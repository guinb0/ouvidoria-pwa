from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import List, Dict, Any
import logging

# Importar reconhecedores brasileiros customizados
from brazilian_recognizers import (
    BrazilCpfRecognizer,
    BrazilRgRecognizer,
    BrazilCepRecognizer,
    BrazilPhoneRecognizer,
    BrazilCnpjRecognizer,
    BrazilEmailRecognizer,
)

# Tentar importar Flair para NER de alta precisão
try:
    from flair.data import Sentence
    from flair.models import SequenceTagger
    FLAIR_AVAILABLE = True
except ImportError:
    FLAIR_AVAILABLE = False

# Tentar importar Stanza para NER transformer
try:
    import stanza
    STANZA_AVAILABLE = True
except ImportError:
    STANZA_AVAILABLE = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if FLAIR_AVAILABLE:
    logger.info("Flair disponivel para NER de alta precisao")
else:
    logger.warning("Flair nao instalado, usando apenas spaCy")

if STANZA_AVAILABLE:
    logger.info("Stanza disponivel para NER transformer")
else:
    logger.warning("Stanza nao instalado")

app = FastAPI(title="Ouvidoria Presidio Service", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inicializar Presidio
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "pt", "model_name": "pt_core_news_sm"}],
}

# Tentar carregar stanza como alternativa (DESABILITADO - muito lento)
stanza_nlp = None
# if STANZA_AVAILABLE:
#     try:
#         logger.info("Baixando modelo Stanza portugues (pode demorar na primeira vez)...")
#         stanza.download('pt', logging_level='ERROR')
#         stanza_nlp = stanza.Pipeline('pt', processors='tokenize,ner', logging_level='ERROR')
#         logger.info("Modelo Stanza carregado com sucesso (transformer NER)")
#     except Exception as e:
#         logger.warning(f"Falha ao carregar Stanza: {e}")
#         stanza_nlp = None

# Inicializar Flair se disponível
flair_tagger = None
if FLAIR_AVAILABLE:
    try:
        logger.info("Baixando modelo Flair multilingue (pode demorar na primeira vez)...")
        # Carregar modelo multilingue do Flair (inclui portugues)
        flair_tagger = SequenceTagger.load('ner-multi')
        logger.info("Modelo Flair carregado com sucesso (multilingue)")
    except Exception as e:
        logger.warning(f"Falha ao carregar modelo Flair: {e}")
        flair_tagger = None

# Inicializar Presidio com spaCy e reconhecedores customizados
try:
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    
    # Criar registro de reconhecedores
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=nlp_engine)
    
    # Adicionar reconhecedores brasileiros customizados
    registry.add_recognizer(BrazilCpfRecognizer())
    registry.add_recognizer(BrazilRgRecognizer())
    registry.add_recognizer(BrazilCepRecognizer())
    registry.add_recognizer(BrazilPhoneRecognizer())
    registry.add_recognizer(BrazilCnpjRecognizer())
    registry.add_recognizer(BrazilEmailRecognizer())
    logger.info("Reconhecedores brasileiros adicionados (CPF, RG, CEP, Telefone, CNPJ, Email)")
    
    # Inicializar engines do Presidio
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
    anonymizer = AnonymizerEngine()
    
    if flair_tagger:
        logger.info("Presidio inicializado com spaCy portugues (lg) + Flair + Reconhecedores BR")
    elif stanza_nlp:
        logger.info("Presidio inicializado com spaCy portugues (lg) + Stanza + Reconhecedores BR")
    else:
        logger.info("Presidio inicializado com spaCy portugues (lg) + Reconhecedores BR")
except Exception as e:
    logger.warning(f"Falha ao carregar modelo portugues pt_core_news_lg: {e}")
    logger.info("Tentando fallback para pt_core_news_sm")
    try:
        configuration["models"] = [{"lang_code": "pt", "model_name": "pt_core_news_sm"}]
        provider = NlpEngineProvider(nlp_configuration=configuration)
        nlp_engine = provider.create_engine()
        registry = RecognizerRegistry()
        registry.load_predefined_recognizers(nlp_engine=nlp_engine)
        registry.add_recognizer(BrazilCpfRecognizer())
        registry.add_recognizer(BrazilRgRecognizer())
        registry.add_recognizer(BrazilCepRecognizer())
        registry.add_recognizer(BrazilPhoneRecognizer())
        registry.add_recognizer(BrazilCnpjRecognizer())
        registry.add_recognizer(BrazilEmailRecognizer())
        analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
        anonymizer = AnonymizerEngine()
        logger.info("Presidio inicializado com spaCy portugues (sm) + Reconhecedores BR")
    except Exception as e2:
        logger.warning(f"Falha ao carregar modelo portugues sm: {e2}")
        logger.info("Inicializando com modelo ingles como fallback")
        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()


class ProcessamentoRequest(BaseModel):
    texto: str
    language: str = "pt"
    entities: List[str] = None


class ProcessamentoResponse(BaseModel):
    textoOriginal: str
    textoTarjado: str
    dadosOcultados: int
    entidadesEncontradas: List[Dict[str, Any]]


@app.post("/api/processar", response_model=ProcessamentoResponse)
async def processar_texto(request: ProcessamentoRequest):
    """
    Analisa e anonimiza texto usando Microsoft Presidio
    """
    try:
        # Definir entidades a serem detectadas (incluindo brasileiras)
        entities = request.entities or [
            "PERSON",           # Nomes de pessoas
            "EMAIL_ADDRESS",    # E-mails
            "PHONE_NUMBER",     # Telefones
            "LOCATION",         # Localizações
            "CREDIT_CARD",      # Cartões de crédito
            "IBAN_CODE",        # Códigos bancários
            "IP_ADDRESS",       # Endereços IP
            "NRP",              # CPF (Portugal/Brasil)
            "US_SSN",           # Similar a CPF
            "BR_CPF",           # CPF brasileiro (custom)
            "BR_RG",            # RG brasileiro (custom)
            "BR_CEP",           # CEP brasileiro (custom)
            "BR_CNPJ",          # CNPJ brasileiro (custom)
            "BR_PHONE",         # Telefone brasileiro (custom)
        ]
        
        # Analisar texto com limiar de confiança mínimo
        results = analyzer.analyze(
            text=request.texto,
            language=request.language,
            entities=entities,
            score_threshold=0.55  # Só detecta com confiança >= 55%
        )
        
        # Filtrar PERSON com score baixo e verificar se não é apenas uma palavra
        filtered_results = []
        
        # Criar índice de spans para detectar sobreposições
        entity_spans = {}
        for r in results:
            key = (r.start, r.end)
            if key not in entity_spans:
                entity_spans[key] = []
            entity_spans[key].append(r)
        
        # Palavras que não devem ser detectadas como PERSON
        person_blacklist = ["documento", "protocolo", "email", "cpf", "rg", "cnpj", "cep"]
        
        # Palavras que não devem ser detectadas como LOCATION
        location_blacklist = ["fixo", "celular", "email", "tel", "fone", "documento", "protocolo", "reside", "resido"]
        
        for r in results:
            skip = False
            
            # Para PERSON
            if r.entity_type == "PERSON":
                texto_detectado = request.texto[r.start:r.end].lower()
                
                # Verificar blacklist
                if any(palavra in texto_detectado for palavra in person_blacklist):
                    skip = True
                
                # Se sobrepõe com EMAIL_ADDRESS, priorizar EMAIL
                span_key = (r.start, r.end)
                if span_key in entity_spans:
                    for other in entity_spans[span_key]:
                        if other.entity_type == "EMAIL_ADDRESS":
                            skip = True
                            break
                
                # Verificar se é um nome válido (espaço ou ponto) e score >= 75%
                if not skip and (" " in request.texto[r.start:r.end] or "." in request.texto[r.start:r.end]) and r.score >= 0.75:
                    filtered_results.append(r)
                    
            # Para LOCATION
            elif r.entity_type == "LOCATION":
                texto_detectado = request.texto[r.start:r.end].lower()
                
                # Verificar blacklist
                if any(palavra == texto_detectado for palavra in location_blacklist):
                    skip = True
                
                # Filtrar siglas curtas (2-5 letras maiúsculas)
                texto_original = request.texto[r.start:r.end]
                if len(texto_original) <= 5 and texto_original.isupper():
                    skip = True
                
                if not skip and r.score >= 0.70:
                    filtered_results.append(r)
                    
            # Para BR_CPF e BR_PHONE - remover duplicatas
            elif r.entity_type in ["BR_CPF", "BR_PHONE"]:
                # Se mesmo span tem CPF e PHONE, priorizar CPF (score mais alto)
                span_key = (r.start, r.end)
                if span_key in entity_spans and len(entity_spans[span_key]) > 1:
                    # Pegar entidade com maior score
                    max_score_entity = max(entity_spans[span_key], key=lambda x: x.score)
                    if r == max_score_entity:
                        filtered_results.append(r)
                else:
                    filtered_results.append(r)
                    
            # Outras entidades mantém threshold de 55%
            else:
                filtered_results.append(r)
        
        results = filtered_results
        logger.info(f"Encontradas {len(results)} entidades no texto")
        
        # Configurar operadores de anonimização
        operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "[NOME]"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "(XX) XXXXX-XXXX"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "[LOCAL]"}),
            "CREDIT_CARD": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 12, "from_end": False}),
            "IBAN_CODE": OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 10, "from_end": False}),
            "IP_ADDRESS": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX.XXX"}),
            "NRP": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX-XX"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX-XX"}),
            "BR_CPF": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX-XX"}),
            "BR_RG": OperatorConfig("replace", {"new_value": "XX.XXX.XXX-X"}),
            "BR_CEP": OperatorConfig("replace", {"new_value": "XXXXX-XXX"}),
            "BR_PHONE": OperatorConfig("replace", {"new_value": "(XX) XXXXX-XXXX"}),
            "BR_CNPJ": OperatorConfig("replace", {"new_value": "XX.XXX.XXX/XXXX-XX"}),
            "DEFAULT": OperatorConfig("replace", {"new_value": "[OCULTO]"}),
        }
        
        # Anonimizar texto
        anonymized_result = anonymizer.anonymize(
            text=request.texto,
            analyzer_results=results,
            operators=operators
        )
        
        # Preparar lista de entidades encontradas
        entidades_encontradas = [
            {
                "tipo": result.entity_type,
                "inicio": result.start,
                "fim": result.end,
                "confianca": result.score
            }
            for result in results
        ]
        
        return ProcessamentoResponse(
            textoOriginal=request.texto,
            textoTarjado=anonymized_result.text,
            dadosOcultados=len(results),
            entidadesEncontradas=entidades_encontradas
        )
        
    except Exception as e:
        logger.error(f"Erro ao processar texto: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar texto: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Verifica saude do servico"""
    return {
        "status": "OK",
        "servico": "Presidio Service",
        "motores": {
            "analisador": "pronto",
            "anonimizador": "pronto"
        }
    }


@app.get("/api/entities")
async def get_supported_entities():
    """Retorna lista de entidades suportadas"""
    return {
        "entidades": [
            "PERSON",           # Nomes de pessoas
            "EMAIL_ADDRESS",    # E-mails
            "PHONE_NUMBER",     # Telefones
            "LOCATION",         # Localizações
            "CREDIT_CARD",      # Cartões de crédito
            "BR_CPF",          # CPF brasileiro
            "BR_RG",           # RG brasileiro
            "BR_CEP",          # CEP brasileiro
            "BR_PHONE",        # Telefone brasileiro
            "IP_ADDRESS",      # Endereços IP
            "IBAN_CODE",       # Códigos bancários
        ]
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor Presidio Service na porta 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
