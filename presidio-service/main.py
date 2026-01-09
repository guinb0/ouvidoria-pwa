from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import List, Dict, Any
import logging

# Tentar importar Flair para NER de alta precisão
try:
    from flair.data import Sentence
    from flair.models import SequenceTagger
    FLAIR_AVAILABLE = True
except ImportError:
    FLAIR_AVAILABLE = False

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if FLAIR_AVAILABLE:
    logger.info("✅ Flair disponível para NER de alta precisão")
else:
    logger.warning("⚠️ Flair não instalado, usando apenas spaCy")

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

# Inicializar Flair se disponível
flair_tagger = None
if FLAIR_AVAILABLE:
    try:
        logger.info("📥 Baixando modelo Flair multilíngue (pode demorar na primeira vez)...")
        # Carregar modelo multilíngue do Flair (inclui português)
        flair_tagger = SequenceTagger.load('ner-multi')
        logger.info("✅ Flair NER model loaded successfully (multilingual)")
    except Exception as e:
        logger.warning(f"Failed to load Flair model: {e}")
        flair_tagger = None

try:
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    
    # Criar registro de reconhecedores
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=nlp_engine)
    
    # Inicializar engines
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
    anonymizer = AnonymizerEngine()
    
    if flair_tagger:
        logger.info("Presidio initialized with Portuguese spaCy + Flair NER")
    else:
        logger.info("Presidio initialized with Portuguese spaCy only")
except Exception as e:
    logger.warning(f"Failed to load Portuguese model: {e}")
    logger.info("Initializing with English model as fallback")
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
        # Definir entidades a serem detectadas
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
        ]
        
        # Analisar texto com score threshold mais alto
        results = analyzer.analyze(
            text=request.texto,
            language=request.language,
            entities=entities,
            score_threshold=0.5  # Apenas detectar com confiança >= 50%
        )
        
        # Filtrar PERSON com score baixo e verificar se não é apenas uma palavra
        filtered_results = []
        for r in results:
            # Para PERSON, precisa ter score alto E ter pelo menos 2 palavras (nome completo)
            if r.entity_type == "PERSON":
                texto_detectado = request.texto[r.start:r.end]
                # Só aceita se tem espaço (nome completo) E score >= 70%
                if " " in texto_detectado and r.score >= 0.70:
                    filtered_results.append(r)
            # Para LOCATION, precisa ter score >= 60%
            elif r.entity_type == "LOCATION":
                if r.score >= 0.60:
                    filtered_results.append(r)
            # Outras entidades mantém threshold de 50%
            else:
                filtered_results.append(r)
        
        results = filtered_results
        logger.info(f"Found {len(results)} entities in text")
        
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
        logger.error(f"Error processing text: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro ao processar texto: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Verifica saúde do serviço"""
    return {
        "status": "OK",
        "service": "Presidio Service",
        "engines": {
            "analyzer": "ready",
            "anonymizer": "ready"
        }
    }


@app.get("/api/entities")
async def get_supported_entities():
    """Retorna lista de entidades suportadas"""
    return {
        "entities": [
            "PERSON",
            "EMAIL_ADDRESS",
            "PHONE_NUMBER",
            "LOCATION",
            "CREDIT_CARD",
            "IBAN_CODE",
            "IP_ADDRESS",
            "NRP",
            "US_SSN"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
