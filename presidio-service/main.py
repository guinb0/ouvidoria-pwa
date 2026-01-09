from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import List, Dict, Any
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

try:
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    
    # Criar registro de reconhecedores
    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(nlp_engine=nlp_engine)
    
    # Inicializar engines
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
    anonymizer = AnonymizerEngine()
    
    logger.info("Presidio initialized successfully with Portuguese support")
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
        
        # Analisar texto
        results = analyzer.analyze(
            text=request.texto,
            language=request.language,
            entities=entities
        )
        
        logger.info(f"Found {len(results)} entities in text")
        
        # Configurar operadores de anonimização
        operators = {
            "PERSON": OperatorConfig("replace", {"new_value": "[NOME OCULTO]"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL OCULTO]"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[TELEFONE OCULTO]"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "[ENDEREÇO OCULTO]"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CARTÃO OCULTO]"}),
            "IBAN_CODE": OperatorConfig("replace", {"new_value": "[CÓDIGO BANCÁRIO OCULTO]"}),
            "IP_ADDRESS": OperatorConfig("replace", {"new_value": "[IP OCULTO]"}),
            "NRP": OperatorConfig("replace", {"new_value": "[CPF OCULTO]"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "[CPF OCULTO]"}),
            "DEFAULT": OperatorConfig("replace", {"new_value": "[DADO OCULTO]"}),
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
