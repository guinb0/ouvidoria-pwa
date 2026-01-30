"""
Stage B - Classificador de PII por Combinação e Proximidade
Implementa regras de linkage para determinar se entidades detectadas
pelo Presidio realmente constituem dados pessoais identificáveis.
"""
from typing import List, Dict, Any


class PIIClassifier:
    """
    Classifica se um conjunto de entidades representa PII identificável
    baseado em regras de combinação e proximidade.
    """
    
    # Entidades que são "âncoras de pessoa" - indicam possível identificação
    PERSON_ANCHORS = {'PERSON'}
    
    # Identificadores fortes - quando combinados com PERSON, identificam alguém
    STRONG_IDENTIFIERS = {
        'BR_CPF', 'BR_RG', 'BR_CNPJ',
        'EMAIL_ADDRESS', 
        'PHONE_NUMBER', 'BR_PHONE',
        'BR_DRIVER_LICENSE', 'BR_VOTER_ID',
        'BR_WORK_CARD',
        'CREDIT_CARD', 'IBAN_CODE',
        'US_SSN', 'NRP'
    }
    
    # Entidades que sozinhas OU sem pessoa próxima NÃO são PII identificável
    WEAK_ENTITIES = {
        'LOCATION',           # Cidades, bairros, órgãos
        'BR_CEP',            # CEP sem pessoa
        'BR_DATE_OF_BIRTH',  # Datas genéricas
        'DATE_TIME',
        'BR_PROFESSION',     # Cargo/profissão genérica
        'BR_NATIONALITY',
        'BR_MARITAL_STATUS',
        'BR_AGE',
        'BR_RELIGION',
        'BR_ETHNICITY',
        'BR_SCHOOL_REGISTRATION',
        'BR_GEOLOCATION',
        'BR_USERNAME',       # Username genérico
        'BR_IP_EXPLICIT',
        'IP_ADDRESS'
    }
    
    # Identificadores médios - podem ser PII se houver contexto forte
    MEDIUM_IDENTIFIERS = {
        'BR_HEALTH_DATA',
        'BR_POLITICAL_OPINION',
        'BR_SEXUAL_ORIENTATION',
        'BR_UNION_MEMBERSHIP',
        'BR_BANK_ACCOUNT',
        'BR_CONTRACT_NUMBER',
        'BR_VEHICLE_PLATE'
    }
    
    def __init__(self, proximity_window: int = 100, strict_window: int = 50):
        """
        Args:
            proximity_window: Distância máxima em caracteres para considerar
                            entidades como "próximas" (default: 100 chars)
            strict_window: Janela mais restrita para casos duvidosos (default: 50 chars)
        """
        self.proximity_window = proximity_window
        self.strict_window = strict_window
        
        # Keywords que indicam contexto de PII real (inspirado em Contextual Privacy IBM)
        self.pii_context_keywords = {
            'cpf', 'rg', 'telefone', 'tel', 'email', 'e-mail', 
            'contato', 'solicitante', 'requerente', 'interessado',
            'cidadão', 'cidadã', 'contribuinte', 'endereço',
            'telefone:', 'cpf:', 'email:', 'nome:', 'rg:'
        }
        
        # Padrões de números de processo detectados erroneamente como RG
        self.process_patterns = [
            r'^\d{5}-\d{8,}/\d{4}-\d{2}$',  # Formato SEI: 00015-01009853/2026-01
            r'^\d{5}-\d{8}/\d{4}-\d{2}$',   # Formato sem /
        ]
    
    def _is_valid_entity(self, entity: Dict[str, Any]) -> bool:
        """
        Valida se uma entidade é legítima - filtra apenas casos óbvios de erro.
        Inspirado em Contextual Privacy - remove entidades vazias e números de processo.
        """
        import re
        
        # Extrai texto da entidade
        text = entity.get('text', '')
        
        # FILTRO 1: Remove entidades completamente vazias
        if not text or text.strip() == '':
            return False
        
        # Extrai tipo
        entity_type = entity.get('entity_type') or entity.get('tipo', 'UNKNOWN')
        
        # FILTRO 2: Para RG/documentos, verifica se não é número de processo SEI
        # (Contextual Privacy: números de processo não são dados pessoais)
        if entity_type in {'BR_RG', 'BR_WORK_CARD', 'BR_DRIVER_LICENSE'}:
            for pattern in self.process_patterns:
                if re.match(pattern, text.strip()):
                    return False
        
        # Aceita todas as outras entidades (não filtra por score)
        return True
    
    def classify(self, entities: List[Dict[str, Any]], text: str = "") -> Dict[str, Any]:
        """
        Classifica se as entidades detectadas constituem PII identificável.
        
        Args:
            entities: Lista de entidades retornadas pelo Presidio
            text: Texto original (opcional, para análise de proximidade)
        
        Returns:
            Dict com:
                - is_pii: bool - Se contém PII identificável
                - reason: str - Razão da classificação
                - relevant_entities: List - Entidades consideradas PII
                - dismissed_entities: List - Entidades descartadas
        """
        if not entities:
            return {
                'is_pii': False,
                'reason': 'Nenhuma entidade detectada',
                'relevant_entities': [],
                'dismissed_entities': []
            }
        
        # Agrupa entidades por tipo (sem filtros - aceita todas as entidades do Presidio)
        by_type = {}
        for ent in entities:
            # Suporta ambos formatos: 'entity_type' (Presidio) e 'tipo' (API)
            entity_type = ent.get('entity_type') or ent.get('tipo', 'UNKNOWN')
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(ent)
        
        # Verifica identificadores fortes (CPF, email, telefone)
        has_strong_id = any(t in by_type for t in self.STRONG_IDENTIFIERS)
        
        # Verifica âncora de pessoa
        has_person = 'PERSON' in by_type
        
        # Regra 1: Identificador forte SOZINHO já é PII
        # (CPF, email, telefone mesmo sem nome próximo)
        strong_alone = []
        for strong_type in self.STRONG_IDENTIFIERS:
            if strong_type in by_type:
                strong_alone.extend(by_type[strong_type])
        
        if strong_alone:
            entity_types = set((e.get('entity_type') or e.get('tipo')) for e in strong_alone)
            return {
                'is_pii': True,
                'reason': f'Identificador forte detectado: {", ".join(entity_types)}',
                'relevant_entities': strong_alone,
                'dismissed_entities': self._get_weak_entities(entities, strong_alone)
            }
        
        # Regra 2: PERSON + identificador médio próximo = PII
        # Inspirado em Contextual Privacy: usa janela restrita
        if has_person:
            person_entities = by_type['PERSON']
            
            if person_entities:
                medium_ids = []
                for medium_type in self.MEDIUM_IDENTIFIERS:
                    if medium_type in by_type:
                        medium_ids.extend(by_type[medium_type])
                
                if medium_ids:
                    # Usa janela RESTRITA (50 chars) para ser mais seletivo
                    close_pairs = self._find_close_entities(
                        person_entities, 
                        medium_ids, 
                        self.strict_window  # 50 chars ao invés de 100
                    )
                    
                    if close_pairs:
                        relevant = person_entities + medium_ids
                        return {
                            'is_pii': True,
                            'reason': f'PERSON (confiável) + identificador médio muito próximos ({len(close_pairs)} combinações)',
                            'relevant_entities': relevant,
                            'dismissed_entities': self._get_weak_entities(entities, relevant)
                        }
        
        # Regra 3: PERSON com múltiplas entidades fracas próximas pode ser PII
        # Inspirado em Contextual Privacy: verifica contexto e keywords
        if has_person and len(entities) >= 4:
            person_entities = by_type['PERSON']
            
            if person_entities:
                # Verifica se há pelo menos 3 entidades fracas próximas (aumentado de 2)
                weak_near_person = []
                for ent in entities:
                    ent_type = ent.get('entity_type') or ent.get('tipo')
                    if ent_type in self.WEAK_ENTITIES:
                        if self._is_near(person_entities, [ent], self.strict_window):
                            weak_near_person.append(ent)
                
                # Se tiver nome + pelo menos 3 entidades complementares, pode ser PII
                if len(weak_near_person) >= 3:
                    # Filtra apenas contextos mais específicos (não apenas LOCATION)
                    specific_context = [
                        e for e in weak_near_person 
                        if (e.get('entity_type') or e.get('tipo')) not in {'LOCATION', 'BR_PROFESSION'}
                    ]
                    
                    # Verifica se há keywords de contexto PII próximas
                    has_pii_context = text and self._has_pii_keywords_near(person_entities, text)
                    
                    if specific_context and (len(specific_context) >= 2 or has_pii_context):
                        relevant = person_entities + specific_context
                        return {
                            'is_pii': True,
                            'reason': f'PERSON + {len(specific_context)} atributos contextuais + keywords PII',
                            'relevant_entities': relevant,
                            'dismissed_entities': self._get_weak_entities(entities, relevant)
                        }
        
        # Regra 4: Apenas entidades fracas = NÃO é PII identificável
        only_weak = all(
            (e.get('entity_type') or e.get('tipo')) in self.WEAK_ENTITIES 
            for e in entities
        )
        if only_weak:
            return {
                'is_pii': False,
                'reason': f'Apenas entidades fracas detectadas: {set((e.get("entity_type") or e.get("tipo")) for e in entities)}',
                'relevant_entities': [],
                'dismissed_entities': entities
            }
        
        # Regra 5: Se sobrou algo sem combinação clara, NÃO considera PII
        # (mudamos de "por precaução aceita" para "por precaução rejeita" para reduzir FP)
        return {
            'is_pii': False,
            'reason': f'Entidades sem combinação identificável: {set((e.get("entity_type") or e.get("tipo")) for e in entities)}',
            'relevant_entities': [],
            'dismissed_entities': entities
        }
    
    def _find_close_entities(
        self, 
        group_a: List[Dict], 
        group_b: List[Dict], 
        max_distance: int
    ) -> List[tuple]:
        """Encontra pares de entidades próximas entre dois grupos."""
        close_pairs = []
        for ent_a in group_a:
            for ent_b in group_b:
                # Suporta ambos formatos de posição
                start_a = ent_a.get('start') or ent_a.get('inicio', 0)
                start_b = ent_b.get('start') or ent_b.get('inicio', 0)
                distance = abs(start_a - start_b)
                if distance <= max_distance:
                    close_pairs.append((ent_a, ent_b))
        return close_pairs
    
    def _is_near(
        self, 
        group_a: List[Dict], 
        group_b: List[Dict], 
        max_distance: int
    ) -> bool:
        """Verifica se há alguma entidade de group_b próxima de group_a."""
        for ent_a in group_a:
            for ent_b in group_b:
                # Suporta ambos formatos de posição
                start_a = ent_a.get('start') or ent_a.get('inicio', 0)
                start_b = ent_b.get('start') or ent_b.get('inicio', 0)
                distance = abs(start_a - start_b)
                if distance <= max_distance:
                    return True
        return False
    
    def _get_weak_entities(
        self, 
        all_entities: List[Dict], 
        relevant: List[Dict]
    ) -> List[Dict]:
        """Retorna entidades que foram descartadas (não relevantes)."""
        relevant_ids = {id(e) for e in relevant}
        return [e for e in all_entities if id(e) not in relevant_ids]
    
    def _has_pii_keywords_near(
        self,
        person_entities: List[Dict],
        text: str,
        window: int = 50
    ) -> bool:
        """
        Verifica se há keywords de contexto PII próximas às entidades PERSON.
        Inspirado em Contextual Privacy da IBM.
        """
        if not text:
            return False
        
        text_lower = text.lower()
        
        for person in person_entities:
            start = person.get('start') or person.get('inicio', 0)
            end = person.get('end') or person.get('fim', start + 10)
            
            # Extrai janela de texto ao redor do PERSON
            window_start = max(0, start - window)
            window_end = min(len(text), end + window)
            context_window = text_lower[window_start:window_end]
            
            # Verifica se alguma keyword está na janela
            for keyword in self.pii_context_keywords:
                if keyword in context_window:
                    return True
        
        return False


# Função de conveniência para usar no endpoint
def classify_pii(entities: List[Dict[str, Any]], text: str = "") -> bool:
    """
    Função simplificada que retorna apenas se é PII ou não.
    
    Args:
        entities: Lista de entidades do Presidio
        text: Texto original
    
    Returns:
        bool: True se for PII identificável, False caso contrário
    """
    classifier = PIIClassifier(proximity_window=100)
    result = classifier.classify(entities, text)
    return result['is_pii']


# Para testes
if __name__ == "__main__":
    # Teste 1: CPF sozinho = PII
    entities_cpf = [
        {'entity_type': 'BR_CPF', 'start': 50, 'end': 64, 'text': '123.456.789-00', 'score': 1.0}
    ]
    classifier = PIIClassifier()
    result = classifier.classify(entities_cpf)
    print(f"Teste CPF sozinho: {result['is_pii']} - {result['reason']}")
    
    # Teste 2: Apenas LOCATION = NÃO é PII
    entities_location = [
        {'entity_type': 'LOCATION', 'start': 10, 'end': 18, 'text': 'Brasília', 'score': 0.9}
    ]
    result = classifier.classify(entities_location)
    print(f"Teste LOCATION sozinha: {result['is_pii']} - {result['reason']}")
    
    # Teste 3: PERSON + EMAIL próximos = PII
    entities_person_email = [
        {'entity_type': 'PERSON', 'start': 0, 'end': 10, 'text': 'João Silva', 'score': 0.95},
        {'entity_type': 'EMAIL_ADDRESS', 'start': 20, 'end': 35, 'text': 'joao@email.com', 'score': 1.0}
    ]
    result = classifier.classify(entities_person_email)
    print(f"Teste PERSON + EMAIL: {result['is_pii']} - {result['reason']}")
    
    # Teste 4: PERSON + LOCATION distantes = NÃO é PII
    entities_person_location = [
        {'entity_type': 'PERSON', 'start': 0, 'end': 10, 'text': 'Secretário', 'score': 0.6},
        {'entity_type': 'LOCATION', 'start': 200, 'end': 210, 'text': 'São Paulo', 'score': 0.9}
    ]
    result = classifier.classify(entities_person_location)
    print(f"Teste PERSON + LOCATION longe: {result['is_pii']} - {result['reason']}")
