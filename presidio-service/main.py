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
    # Dados pessoais básicos
    BrazilDateOfBirthRecognizer,
    BrazilAgeRecognizer,
    BrazilProfessionRecognizer,
    BrazilMaritalStatusRecognizer,
    BrazilNationalityRecognizer,
    # Dados financeiros
    BrazilBankAccountRecognizer,
    BrazilContractNumberRecognizer,
    # Dados de localização
    BrazilVehiclePlateRecognizer,
    BrazilGeolocationRecognizer,
    BrazilUsernameRecognizer,
    BrazilIpAddressRecognizer,
    # Dados sensíveis LGPD
    BrazilEthnicityRecognizer,
    BrazilReligionRecognizer,
    BrazilPoliticalOpinionRecognizer,
    BrazilUnionMembershipRecognizer,
    BrazilHealthDataRecognizer,
    BrazilSexualOrientationRecognizer,
)

# Importar otimizador ensemble
from ensemble_optimizer import (
    ThresholdOptimizer,
    EnsembleVoter,
    calculate_confidence_boost
)

# Tentar importar Flair para NER de alta precisão
# DESABILITADO: Causando problemas de carregamento
# try:
#     from flair.data import Sentence
#     from flair.models import SequenceTagger
#     FLAIR_AVAILABLE = True
# except ImportError:
#     FLAIR_AVAILABLE = False
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
        logger.info("Baixando modelo Flair portugues large (pode demorar na primeira vez)...")
        # Carregar modelo português específico (melhor que multilíngue para PT-BR)
        try:
            flair_tagger = SequenceTagger.load('flair/ner-portuguese-large')
            logger.info("Modelo Flair português large carregado com sucesso")
        except Exception:
            # Fallback para multilíngue se português não disponível
            flair_tagger = SequenceTagger.load('ner-multi')
            logger.info("Modelo Flair multilingue carregado (fallback)")
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
    # Dados pessoais básicos
    registry.add_recognizer(BrazilDateOfBirthRecognizer())
    registry.add_recognizer(BrazilAgeRecognizer())
    registry.add_recognizer(BrazilProfessionRecognizer())
    registry.add_recognizer(BrazilMaritalStatusRecognizer())
    registry.add_recognizer(BrazilNationalityRecognizer())
    # Dados financeiros
    registry.add_recognizer(BrazilBankAccountRecognizer())
    registry.add_recognizer(BrazilContractNumberRecognizer())
    # Dados de localização
    registry.add_recognizer(BrazilVehiclePlateRecognizer())
    registry.add_recognizer(BrazilGeolocationRecognizer())
    registry.add_recognizer(BrazilUsernameRecognizer())
    registry.add_recognizer(BrazilIpAddressRecognizer())
    # Dados sensíveis LGPD
    registry.add_recognizer(BrazilEthnicityRecognizer())
    registry.add_recognizer(BrazilReligionRecognizer())
    registry.add_recognizer(BrazilPoliticalOpinionRecognizer())
    registry.add_recognizer(BrazilUnionMembershipRecognizer())
    registry.add_recognizer(BrazilHealthDataRecognizer())
    registry.add_recognizer(BrazilSexualOrientationRecognizer())
    logger.info("Reconhecedores brasileiros adicionados: 22 tipos (CPF, RG, CEP, Telefone, CNPJ, Email + 16 LGPD)")
    
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
            # Entidades básicas Presidio
            "PERSON",           # Nomes de pessoas
            "EMAIL_ADDRESS",    # E-mails
            "PHONE_NUMBER",     # Telefones
            "LOCATION",         # Localizações
            "CREDIT_CARD",      # Cartões de crédito
            "IBAN_CODE",        # Códigos bancários
            "IP_ADDRESS",       # Endereços IP
            "NRP",              # CPF (Portugal/Brasil)
            "US_SSN",           # Similar a CPF
            # Reconhecedores brasileiros básicos
            "BR_CPF",           # CPF brasileiro
            "BR_RG",            # RG brasileiro
            "BR_CEP",           # CEP brasileiro
            "BR_CNPJ",          # CNPJ brasileiro
            "BR_PHONE",         # Telefone brasileiro
            # Dados pessoais básicos
            "BR_DATE_OF_BIRTH", # Data de nascimento
            "BR_AGE",           # Idade
            "BR_PROFESSION",    # Profissão
            "BR_MARITAL_STATUS",# Estado civil
            "BR_NATIONALITY",   # Nacionalidade
            # Dados financeiros
            "BR_BANK_ACCOUNT",  # Dados bancários
            "BR_CONTRACT_NUMBER", # Número de contrato/protocolo
            # Dados de localização
            "BR_VEHICLE_PLATE", # Placa de veículo
            "BR_GEOLOCATION",   # Coordenadas GPS
            "BR_USERNAME",      # Nome de usuário
            "BR_IP_EXPLICIT",   # IP explicitamente mencionado
            # Dados sensíveis LGPD
            "BR_ETHNICITY",     # Origem étnica
            "BR_RELIGION",      # Religião
            "BR_POLITICAL_OPINION", # Opinião política
            "BR_UNION_MEMBERSHIP",  # Filiação sindical
            "BR_HEALTH_DATA",   # Dados de saúde
            "BR_SEXUAL_ORIENTATION", # Orientação sexual
        ]
        
        # Analisar texto com limiar de confiança mínimo
        results = analyzer.analyze(
            text=request.texto,
            language=request.language,
            entities=entities,
            score_threshold=0.50  # Threshold base (será refinado se necessário)
        )
        
        # DESABILITADO: Ensemble optimizer estava reduzindo recall
        # threshold_optimizer = ThresholdOptimizer()
        # optimized_results = []
        # 
        # for r in results:
        #     confidence_boost = calculate_confidence_boost(
        #         request.texto, r.entity_type, r.start, r.end
        #     )
        #     boosted_score = min(r.score * confidence_boost, 1.0)
        #     
        #     if threshold_optimizer.should_accept(r.entity_type, boosted_score):
        #         from presidio_analyzer import RecognizerResult
        #         optimized_r = RecognizerResult(
        #             entity_type=r.entity_type,
        #             start=r.start,
        #             end=r.end,
        #             score=boosted_score
        #         )
        #         optimized_results.append(optimized_r)
        # 
        # results = optimized_results
        
        # Filtrar PERSON com score baixo e verificar se não é apenas uma palavra
        filtered_results = []
        
        # Criar índice de spans para detectar sobreposições
        entity_spans = {}
        for r in results:
            key = (r.start, r.end)
            if key not in entity_spans:
                entity_spans[key] = []
            entity_spans[key].append(r)
        
        # LEXICONS CUSTOMIZADOS (Técnica Reddit: +2-4% F1)
        # Palavras que não devem ser detectadas como PERSON
        person_blacklist = [
            # Documentos e processos
            "documento", "protocolo", "email", "cpf", "rg", "cnpj", "cep", 
            "processo", "lei", "artigo", "inciso", "paragrafo", "decreto",
            # Termos jurídicos
            "sentenca", "acordao", "decisao", "despacho", "parecer",
            "recurso", "agravo", "apelacao", "embargos",
            # Órgãos e cargos genéricos
            "secretaria", "ministerio", "tribunal", "conselho", "comissao",
            "presidente", "ministro", "juiz", "desembargador", "procurador",
            # Conectivos e preposições comuns
            "sobre", "para", "com", "sem", "por", "sob", "ante"
        ]
        
        # Palavras que não devem ser detectadas como LOCATION
        location_blacklist = [
            # Comunicação e documentos
            "fixo", "celular", "email", "tel", "fone", "telefone", "documento", "protocolo",
            # Termos técnicos
            "sistema", "portal", "plataforma", "aplicativo", "site",
            # Status e estados
            "aberto", "fechado", "pendente", "concluido", "em andamento"
        ]
        
        # Contextos governamentais brasileiros (não são PII)
        gov_context_blacklist = [
            "processo", "protocolo", "artigo", "lei", "decreto", "portaria", 
            "resolucao", "instrucao normativa", "parecer", "despacho",
            "edital", "licitacao", "contrato", "convenio", "termo",
            "oficio", "memorando", "comunicacao", "nota tecnica"
        ]
        
        # Padrões de nomes brasileiros válidos (para melhorar precisão)
        # Se tem sobrenome comum brasileiro e mais de 1 palavra, aumentar confiança
        sobrenomes_brasileiros = [
            "silva", "santos", "oliveira", "souza", "rodrigues", "ferreira", 
            "alves", "pereira", "lima", "gomes", "costa", "ribeiro", "martins",
            "carvalho", "rocha", "almeida", "nascimento", "araujo", "melo", "barbosa"
        ]
        
        for r in results:
            skip = False
            
            # Para PERSON
            if r.entity_type == "PERSON":
                texto_detectado = request.texto[r.start:r.end].lower()
                texto_original = request.texto[r.start:r.end]
                palavras = texto_detectado.split()
                
                # Verificar blacklist (exact match ou substring)
                if any(palavra == texto_detectado for palavra in person_blacklist):
                    skip = True
                elif any(black in texto_detectado for black in ["@", "protocolo", "processo"]):
                    skip = True
                
                # Se sobrepõe com EMAIL_ADDRESS, priorizar EMAIL
                span_key = (r.start, r.end)
                if span_key in entity_spans:
                    for other in entity_spans[span_key]:
                        if other.entity_type == "EMAIL_ADDRESS":
                            skip = True
                            break
                
                # Boost: Se tem sobrenome brasileiro comum, reduzir threshold
                has_brazilian_surname = any(sobrenome in palavras for sobrenome in sobrenomes_brasileiros)
                min_score = 0.70 if has_brazilian_surname else 0.75
                
                # Verificar se é um nome válido (pelo menos 2 palavras ou tem ponto)
                if not skip:
                    has_space = " " in texto_original
                    has_dot = "." in texto_original and len(palavras) >= 2
                    
                    if (has_space or has_dot) and r.score >= min_score:
                        filtered_results.append(r)
                    
            # Para LOCATION
            elif r.entity_type == "LOCATION":
                texto_detectado = request.texto[r.start:r.end].lower()
                texto_original = request.texto[r.start:r.end]
                
                # Verificar blacklist (exact match)
                if texto_detectado in location_blacklist:
                    skip = True
                
                # Verificar se contém palavras suspeitas
                if any(palavra in texto_detectado for palavra in ["email", "telefone", "documento"]):
                    skip = True
                
                # Filtrar siglas muito curtas (2-4 letras maiúsculas) SEM espaços e SEM contexto
                if len(texto_original) <= 4 and texto_original.isupper() and " " not in texto_original:
                    # Verificar se tem contexto de localização nas palavras próximas
                    context_window = 30
                    start_context = max(0, r.start - context_window)
                    end_context = min(len(request.texto), r.end + context_window)
                    context = request.texto[start_context:end_context].lower()
                    
                    location_keywords = ["rua", "avenida", "cidade", "estado", "municipio", "bairro", 
                                        "endereco", "local", "residencia", "domicilio"]
                    has_location_context = any(keyword in context for keyword in location_keywords)
                    
                    if not has_location_context:
                        skip = True
                
                # Threshold otimizado para LOCATION (0.70 via ThresholdOptimizer)
                if not skip:
                    filtered_results.append(r)
                    
            # Para BR_CPF e BR_PHONE - remover duplicatas e aplicar validação
            elif r.entity_type in ["BR_CPF", "BR_PHONE"]:
                # Se mesmo span tem CPF e PHONE, priorizar CPF (score mais alto)
                span_key = (r.start, r.end)
                if span_key in entity_spans and len(entity_spans[span_key]) > 1:
                    # Pegar entidade com maior score
                    max_score_entity = max(entity_spans[span_key], key=lambda x: x.score)
                    if r == max_score_entity:
                        # Validação adicional já aplicada via validate_result()
                        filtered_results.append(r)
                else:
                    # Threshold otimizado para BR_PHONE (0.70 via ThresholdOptimizer)
                    filtered_results.append(r)
                    
            # Outras entidades mantém threshold de 55%
            else:
                filtered_results.append(r)
        
        results = filtered_results
        logger.info(f"Encontradas {len(results)} entidades no texto")
        
        # Configurar operadores de anonimização
        operators = {
            # Entidades básicas
            "PERSON": OperatorConfig("replace", {"new_value": "[NOME]"}),
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "(XX) XXXXX-XXXX"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "[LOCAL]"}),
            "CREDIT_CARD": OperatorConfig("mask", {"masking_char": "X", "chars_to_mask": 12, "from_end": False}),
            "IBAN_CODE": OperatorConfig("mask", {"masking_char": "X", "chars_to_mask": 10, "from_end": False}),
            "IP_ADDRESS": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX.XXX"}),
            "NRP": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX-XX"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX-XX"}),
            # Reconhecedores brasileiros básicos
            "BR_CPF": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX-XX"}),
            "BR_RG": OperatorConfig("replace", {"new_value": "XX.XXX.XXX-X"}),
            "BR_CEP": OperatorConfig("replace", {"new_value": "XXXXX-XXX"}),
            "BR_PHONE": OperatorConfig("replace", {"new_value": "(XX) XXXXX-XXXX"}),
            "BR_CNPJ": OperatorConfig("replace", {"new_value": "XX.XXX.XXX/XXXX-XX"}),
            # Dados pessoais básicos
            "BR_DATE_OF_BIRTH": OperatorConfig("replace", {"new_value": "DD/MM/AAAA"}),
            "BR_AGE": OperatorConfig("replace", {"new_value": "[IDADE]"}),
            "BR_PROFESSION": OperatorConfig("replace", {"new_value": "[PROFISSÃO]"}),
            "BR_MARITAL_STATUS": OperatorConfig("replace", {"new_value": "[ESTADO_CIVIL]"}),
            "BR_NATIONALITY": OperatorConfig("replace", {"new_value": "[NACIONALIDADE]"}),
            # Dados financeiros
            "BR_BANK_ACCOUNT": OperatorConfig("replace", {"new_value": "[DADOS_BANCÁRIOS]"}),
            "BR_CONTRACT_NUMBER": OperatorConfig("replace", {"new_value": "[CONTRATO/PROTOCOLO]"}),
            # Dados de localização
            "BR_VEHICLE_PLATE": OperatorConfig("replace", {"new_value": "XXX-XXXX"}),
            "BR_GEOLOCATION": OperatorConfig("replace", {"new_value": "[COORDENADAS]"}),
            "BR_USERNAME": OperatorConfig("replace", {"new_value": "[USUÁRIO]"}),
            "BR_IP_EXPLICIT": OperatorConfig("replace", {"new_value": "IP XXX.XXX.XXX.XXX"}),
            # Dados sensíveis LGPD
            "BR_ETHNICITY": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
            "BR_RELIGION": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
            "BR_POLITICAL_OPINION": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
            "BR_UNION_MEMBERSHIP": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
            "BR_HEALTH_DATA": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
            "BR_SEXUAL_ORIENTATION": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
            # Default
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
    """Retorna lista de entidades suportadas (33 tipos LGPD-compliant)"""
    return {
        "entidades": [
            # Básicas
            "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "CREDIT_CARD", "IP_ADDRESS", "IBAN_CODE",
            # Documentos BR
            "BR_CPF", "BR_RG", "BR_CEP", "BR_PHONE", "BR_CNPJ",
            # Dados pessoais
            "BR_DATE_OF_BIRTH", "BR_AGE", "BR_PROFESSION", "BR_MARITAL_STATUS", "BR_NATIONALITY",
            # Dados financeiros
            "BR_BANK_ACCOUNT", "BR_CONTRACT_NUMBER",
            # Localização
            "BR_VEHICLE_PLATE", "BR_GEOLOCATION", "BR_USERNAME", "BR_IP_EXPLICIT",
            # Dados sensíveis LGPD (Art. 5º, II)
            "BR_ETHNICITY", "BR_RELIGION", "BR_POLITICAL_OPINION", "BR_UNION_MEMBERSHIP",
            "BR_HEALTH_DATA", "BR_SEXUAL_ORIENTATION",
        ],
        "total": 33,
        "lgpd_compliant": True
    }


if __name__ == "__main__":
    import uvicorn
    logger.info("Iniciando servidor Presidio Service na porta 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
