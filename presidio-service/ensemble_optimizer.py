"""
Ensemble Voting + Threshold Optimization para F1 >95%
Combina Flair + spaCy + Presidio com voting ponderado
"""
import numpy as np
from typing import List, Dict, Tuple
from dataclasses import dataclass
from presidio_analyzer import RecognizerResult

@dataclass
class EntityPrediction:
    """Predição de entidade com score de múltiplos modelos"""
    entity_type: str
    start: int
    end: int
    text: str
    presidio_score: float = 0.0
    spacy_score: float = 0.0
    flair_score: float = 0.0
    
    def ensemble_score(self, weights: Dict[str, float] = None) -> float:
        """Calcula score ensemble com soft voting ponderado"""
        if weights is None:
            # Pesos otimizados empiricamente
            weights = {
                'presidio': 0.5,  # Presidio base (patterns + NER)
                'spacy': 0.3,     # spaCy NER
                'flair': 0.2      # Flair NER (mais conservador)
            }
        
        score = (
            self.presidio_score * weights['presidio'] +
            self.spacy_score * weights['spacy'] +
            self.flair_score * weights['flair']
        )
        return score


class ThresholdOptimizer:
    """
    Otimização de threshold por tipo de entidade
    Baseado em análise de falsos positivos/negativos
    """
    
    # Thresholds otimizados para cada tipo (baseado em F1 atual)
    OPTIMIZED_THRESHOLDS = {
        # Documentos brasileiros (100% F1) - manter threshold baixo
        'BR_CPF': 0.50,      # Checksum validation previne FP
        'BR_RG': 0.50,       # Pattern bem definido
        'BR_CEP': 0.50,      # Pattern bem definido
        'BR_CNPJ': 0.50,     # Checksum validation previne FP
        'EMAIL_ADDRESS': 0.50,  # Validação email-validator
        
        # Telefones (90% F1) - manter moderado
        'BR_PHONE': 0.60,    # Validação DDD previne FP
        
        # Localização (90% F1) - manter moderado
        'LOCATION': 0.65,    # Blacklist + contexto previne FP
        
        # Pessoa (93% F1) - manter moderado
        'PERSON': 0.70,      # Blacklist + contexto previne FP
    }
    
    @classmethod
    def should_accept(cls, entity_type: str, score: float, 
                     has_context: bool = False) -> bool:
        """
        Decide se aceitar entidade baseado em threshold otimizado
        
        Args:
            entity_type: Tipo da entidade
            score: Score da predição
            has_context: Se tem contexto relevante próximo
        """
        threshold = cls.OPTIMIZED_THRESHOLDS.get(entity_type, 0.55)
        
        # Boost: reduzir threshold se tem contexto forte
        if has_context:
            threshold *= 0.9  # -10% no threshold
        
        return score >= threshold
    
    @classmethod
    def optimize_thresholds_from_results(cls, results: List[Dict]) -> Dict[str, float]:
        """
        Otimiza thresholds baseado em resultados de teste
        Retorna novos thresholds que maximizam F1
        """
        # Análise de distribuição de scores por entidade
        entity_scores = {}
        
        for result in results:
            entity_type = result.get('entity_type')
            score = result.get('score', 0.0)
            is_true_positive = result.get('is_tp', True)
            
            if entity_type not in entity_scores:
                entity_scores[entity_type] = {'tp_scores': [], 'fp_scores': []}
            
            if is_true_positive:
                entity_scores[entity_type]['tp_scores'].append(score)
            else:
                entity_scores[entity_type]['fp_scores'].append(score)
        
        # Calcular threshold ótimo por entidade
        optimized = {}
        for entity_type, scores in entity_scores.items():
            tp_scores = np.array(scores['tp_scores'])
            fp_scores = np.array(scores['fp_scores'])
            
            if len(tp_scores) == 0:
                continue
            
            # Threshold ótimo = minimize FP mantendo TP
            # Usa percentil 25 dos TP como piso
            min_threshold = np.percentile(tp_scores, 25) if len(tp_scores) > 0 else 0.5
            
            # Se tem FP, usa max(FP) + margem como threshold
            if len(fp_scores) > 0:
                max_fp_score = np.max(fp_scores)
                suggested_threshold = max(min_threshold, max_fp_score + 0.05)
            else:
                suggested_threshold = min_threshold
            
            optimized[entity_type] = min(suggested_threshold, 0.85)  # Cap em 0.85
        
        return optimized


class EnsembleVoter:
    """
    Combina predições de múltiplos modelos usando soft voting
    """
    
    def __init__(self, weights: Dict[str, float] = None):
        """
        Args:
            weights: Pesos para cada modelo (presidio, spacy, flair)
        """
        self.weights = weights or {
            'presidio': 0.5,
            'spacy': 0.3,
            'flair': 0.2
        }
        self.threshold_optimizer = ThresholdOptimizer()
    
    def merge_predictions(self, 
                         presidio_results: List[RecognizerResult],
                         spacy_entities: List[Tuple[int, int, str, float]] = None,
                         flair_entities: List[Tuple[int, int, str, float]] = None,
                         text: str = "") -> List[EntityPrediction]:
        """
        Merge predições de múltiplos modelos em ensemble
        
        Args:
            presidio_results: Resultados do Presidio
            spacy_entities: Lista de (start, end, label, score) do spaCy
            flair_entities: Lista de (start, end, label, score) do Flair
            text: Texto original
        
        Returns:
            Lista de EntityPrediction com scores ensemble
        """
        # Criar índice de spans
        span_predictions = {}
        
        # Adicionar predições do Presidio
        for r in presidio_results:
            key = (r.start, r.end, r.entity_type)
            if key not in span_predictions:
                span_predictions[key] = EntityPrediction(
                    entity_type=r.entity_type,
                    start=r.start,
                    end=r.end,
                    text=text[r.start:r.end] if text else "",
                    presidio_score=r.score
                )
            else:
                span_predictions[key].presidio_score = max(
                    span_predictions[key].presidio_score, r.score
                )
        
        # Adicionar predições do spaCy (se disponível)
        if spacy_entities:
            for start, end, label, score in spacy_entities:
                # Mapear labels spaCy para Presidio
                mapped_label = self._map_spacy_label(label)
                key = (start, end, mapped_label)
                
                if key not in span_predictions:
                    span_predictions[key] = EntityPrediction(
                        entity_type=mapped_label,
                        start=start,
                        end=end,
                        text=text[start:end] if text else "",
                        spacy_score=score
                    )
                else:
                    span_predictions[key].spacy_score = score
        
        # Adicionar predições do Flair (se disponível)
        if flair_entities:
            for start, end, label, score in flair_entities:
                mapped_label = self._map_flair_label(label)
                key = (start, end, mapped_label)
                
                if key not in span_predictions:
                    span_predictions[key] = EntityPrediction(
                        entity_type=mapped_label,
                        start=start,
                        end=end,
                        text=text[start:end] if text else "",
                        flair_score=score
                    )
                else:
                    span_predictions[key].flair_score = score
        
        # Converter para lista e filtrar por threshold otimizado
        predictions = []
        for pred in span_predictions.values():
            ensemble_score = pred.ensemble_score(self.weights)
            
            # Verificar threshold otimizado
            if self.threshold_optimizer.should_accept(
                pred.entity_type, 
                ensemble_score
            ):
                predictions.append(pred)
        
        return predictions
    
    def _map_spacy_label(self, label: str) -> str:
        """Mapeia labels spaCy para tipos Presidio"""
        mapping = {
            'PER': 'PERSON',
            'PERSON': 'PERSON',
            'LOC': 'LOCATION',
            'LOCATION': 'LOCATION',
            'ORG': 'ORGANIZATION',
            'GPE': 'LOCATION',  # Geopolitical entity
        }
        return mapping.get(label, label)
    
    def _map_flair_label(self, label: str) -> str:
        """Mapeia labels Flair para tipos Presidio"""
        mapping = {
            'PER': 'PERSON',
            'LOC': 'LOCATION',
            'ORG': 'ORGANIZATION',
            'MISC': 'OTHER',
        }
        return mapping.get(label, label)


def calculate_confidence_boost(text: str, entity_type: str, 
                               start: int, end: int) -> float:
    """
    Calcula boost de confiança baseado em contexto
    
    Returns:
        Multiplicador de confiança (1.0 = sem boost, 1.2 = +20%)
    """
    context_window = 30
    context_start = max(0, start - context_window)
    context_end = min(len(text), end + context_window)
    context = text[context_start:context_end].lower()
    
    boost = 1.0
    
    # Contextos que aumentam confiança
    if entity_type == 'BR_PHONE':
        phone_keywords = ['telefone', 'celular', 'contato', 'ligar', 'whatsapp']
        if any(kw in context for kw in phone_keywords):
            boost = 1.15
    
    elif entity_type == 'BR_CPF':
        cpf_keywords = ['cpf', 'cadastro', 'contribuinte', 'documento']
        if any(kw in context for kw in cpf_keywords):
            boost = 1.1
    
    elif entity_type == 'PERSON':
        person_keywords = ['sr', 'sra', 'nome', 'cidadao', 'solicitante']
        if any(kw in context for kw in person_keywords):
            boost = 1.15
    
    elif entity_type == 'LOCATION':
        loc_keywords = ['rua', 'avenida', 'cidade', 'estado', 'endereco', 'bairro']
        if any(kw in context for kw in loc_keywords):
            boost = 1.2
    
    return boost
