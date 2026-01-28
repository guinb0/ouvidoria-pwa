from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from typing import List, Dict, Any
import logging
import re

# Importar validadores robustos
from validators import PersonLocationFilter

# Pré-processador temporariamente desabilitado - focando em Flair para recall
# from text_preprocessor import TextPreprocessor

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
    # Reconhecedores auxiliares
    BrazilGenericPhoneRecognizer,
    BrazilNameRecognizer,
    # Documentos adicionais
    BrazilVoterIdRecognizer,
    BrazilWorkCardRecognizer,
    BrazilDriverLicenseRecognizer,
    BrazilPisPasepRecognizer,
    BrazilCnsRecognizer,
    BrazilPassportRecognizer,
    BrazilReservistaRecognizer,
    BrazilProfessionalRegistryRecognizer,
    BrazilPixKeyRecognizer,
    BrazilRenavamRecognizer,
    BrazilSchoolRegistrationRecognizer,
    BrazilBenefitNumberRecognizer,
)

# Importar otimizador ensemble
from ensemble_optimizer import (
    ThresholdOptimizer,
    EnsembleVoter,
    calculate_confidence_boost
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
logging.basicConfig(level=logging.DEBUG)
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
    "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}],
}

# Tentar carregar Stanza transformer NER  
# DESABILITADO: modelo não descompacta corretamente
stanza_nlp = None
# if STANZA_AVAILABLE:
#     try:
#         logger.info("Baixando modelo Stanza português (primeira vez pode demorar)...")
#         stanza.download('pt', logging_level='ERROR')
#         stanza_nlp = stanza.Pipeline('pt', processors='tokenize,ner', logging_level='ERROR')
#         logger.info("✅ Stanza transformer NER português carregado - máxima precisão!")
#     except Exception as e:
#         logger.warning(f"❌ Falha ao carregar Stanza: {e}")
#         stanza_nlp = None

# Inicializar Flair se disponível
flair_tagger = None
if FLAIR_AVAILABLE:
    try:
        logger.info("Carregando modelo Flair NER multilingue (suporta português)...")
        flair_tagger = SequenceTagger.load('ner-multi')
        logger.info("✅ Flair NER multilingue carregado - melhora recall de PERSON/LOCATION")
    except Exception as e:
        logger.warning(f"❌ Falha ao carregar Flair: {e}")
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
    registry.add_recognizer(BrazilGenericPhoneRecognizer())  # Telefones genéricos
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
    registry.add_recognizer(BrazilNameRecognizer())  # Nomes brasileiros
    registry.add_recognizer(BrazilVoterIdRecognizer())  # Título de Eleitor
    registry.add_recognizer(BrazilWorkCardRecognizer())  # CTPS
    registry.add_recognizer(BrazilDriverLicenseRecognizer())  # CNH
    registry.add_recognizer(BrazilPisPasepRecognizer())  # PIS/PASEP
    registry.add_recognizer(BrazilCnsRecognizer())  # CNS (Cartão Nacional de Saúde)
    registry.add_recognizer(BrazilPassportRecognizer())  # Passaporte
    registry.add_recognizer(BrazilReservistaRecognizer())  # Certificado de Reservista
    registry.add_recognizer(BrazilProfessionalRegistryRecognizer())  # Registros profissionais
    registry.add_recognizer(BrazilPixKeyRecognizer())  # Chave PIX
    registry.add_recognizer(BrazilRenavamRecognizer())  # RENAVAM
    registry.add_recognizer(BrazilSchoolRegistrationRecognizer())  # Matrícula escolar
    registry.add_recognizer(BrazilBenefitNumberRecognizer())  # Número de benefício
    logger.info("Reconhecedores brasileiros adicionados: 37 tipos (CPF, RG, CEP, Telefone, CNPJ, Email + 31 incluindo Título Eleitor, CTPS, CNH, PIS, CNS, Passaporte, Reservista, Registros Profissionais, PIX, RENAVAM, Matrícula Escolar, Número Benefício)")
    
    # Inicializar engines do Presidio
    analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
    anonymizer = AnonymizerEngine()
    
    # Inicializar filtro robusto de PERSON/LOCATION
    person_location_filter = PersonLocationFilter()
    logger.info("Filtro robusto Person/Location inicializado com NameDataset + Geopy")
    
    # Pré-processador desabilitado temporariamente
    # text_preprocessor = TextPreprocessor()
    # logger.info("Pré-processador de texto inicializado - normalização de quebras e contexto")
    
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
        person_location_filter = PersonLocationFilter()
        logger.info("Presidio inicializado com spaCy portugues (sm) + Reconhecedores BR + Validadores Robustos")
    except Exception as e2:
        logger.warning(f"Falha ao carregar modelo portugues sm: {e2}")
        logger.info("Inicializando com modelo ingles como fallback")
        analyzer = AnalyzerEngine()
        anonymizer = AnonymizerEngine()
        person_location_filter = PersonLocationFilter()
        logger.info("Filtro robusto inicializado mesmo no fallback")


def aplicar_ner_complementar(texto: str, results_spacy: List):
    """
    Aplica Flair e Stanza para detectar entidades adicionais não capturadas pelo spaCy
    """
    from presidio_analyzer import RecognizerResult
    
    resultados_extras = []
    
    # Aplicar Flair NER
    if flair_tagger:
        try:
            sentence = Sentence(texto)
            flair_tagger.predict(sentence)
            
            for entity in sentence.get_spans('ner'):
                # Mapear tags do Flair para Presidio
                flair_type = entity.tag
                presidio_type = None
                
                if flair_type in ['PER', 'B-PER', 'I-PER', 'E-PER', 'S-PER']:
                    presidio_type = 'PERSON'
                elif flair_type in ['LOC', 'B-LOC', 'I-LOC', 'E-LOC', 'S-LOC']:
                    presidio_type = 'LOCATION'
                elif flair_type in ['ORG', 'B-ORG', 'I-ORG', 'E-ORG', 'S-ORG']:
                    presidio_type = 'PERSON'  # Tratamos ORG como PERSON para validação posterior
                
                if presidio_type:
                    # Verificar se já foi detectado pelo spaCy
                    start_pos = entity.start_position
                    end_pos = entity.end_position
                    
                    ja_existe = any(
                        r.start == start_pos and r.end == end_pos 
                        for r in results_spacy
                    )
                    
                    if not ja_existe:
                        resultados_extras.append(RecognizerResult(
                            entity_type=presidio_type,
                            start=start_pos,
                            end=end_pos,
                            score=entity.score
                        ))
                        logger.debug(f"✨ Flair detectou: '{texto[start_pos:end_pos]}' ({presidio_type})")
        except Exception as e:
            logger.warning(f"Erro ao aplicar Flair: {e}")
    
    # Aplicar Stanza NER
    if stanza_nlp:
        try:
            doc = stanza_nlp(texto)
            
            for ent in doc.entities:
                # Mapear tags do Stanza para Presidio
                stanza_type = ent.type
                presidio_type = None
                
                if stanza_type == 'PER':
                    presidio_type = 'PERSON'
                elif stanza_type == 'LOC':
                    presidio_type = 'LOCATION'
                elif stanza_type == 'ORG':
                    presidio_type = 'PERSON'  # Tratamos ORG como PERSON
                
                if presidio_type:
                    # Encontrar posições no texto original
                    start_pos = ent.start_char
                    end_pos = ent.end_char
                    
                    # Verificar se já foi detectado
                    ja_existe = any(
                        r.start == start_pos and r.end == end_pos 
                        for r in results_spacy + resultados_extras
                    )
                    
                    if not ja_existe:
                        resultados_extras.append(RecognizerResult(
                            entity_type=presidio_type,
                            start=start_pos,
                            end=end_pos,
                            score=0.85  # Stanza geralmente tem alta precisão
                        ))
                        logger.debug(f"🌟 Stanza detectou: '{texto[start_pos:end_pos]}' ({presidio_type})")
        except Exception as e:
            logger.warning(f"Erro ao aplicar Stanza: {e}")
    
    return resultados_extras


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
            # Documentos adicionais
            "BR_VOTER_ID",      # Título de Eleitor
            "BR_WORK_CARD",     # CTPS (Carteira de Trabalho)
            "BR_DRIVER_LICENSE", # CNH
            "BR_PIS_PASEP",     # PIS/PASEP
            "BR_CNS",           # CNS (Cartão Nacional de Saúde)
            "BR_PASSPORT",      # Passaporte
            "BR_RESERVISTA",    # Certificado de Reservista
            "BR_PROFESSIONAL_REGISTRY", # Registros profissionais (OAB, CRM, CREA, etc)
            "BR_PIX_KEY",       # Chave PIX
            "BR_RENAVAM",       # RENAVAM
            "BR_SCHOOL_REGISTRATION", # Matrícula escolar
            "BR_BENEFIT_NUMBER", # Número de benefício (INSS, etc)
        ]
        
        # Analisar texto com limiar de confiança mínimo
        results = analyzer.analyze(
            text=request.texto,
            language=request.language,
            entities=entities,
            score_threshold=0.40  # Threshold reduzido para capturar mais (filtros específicos aplicados depois)
        )
        
        # Aplicar NER complementar (Flair + Stanza)
        logger.debug(f"spaCy detectou {len(results)} entidades")
        resultados_extras = aplicar_ner_complementar(request.texto, results)
        logger.debug(f"Flair+Stanza adicionaram {len(resultados_extras)} entidades extras")
        
        # Combinar resultados
        results = results + resultados_extras
        logger.info(f"Total após ensemble: {len(results)} entidades")
        
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
        
        # Filtrar PERSON e LOCATION usando validadores robustos
        filtered_results = []
        
        # Criar índice de spans para detectar sobreposições
        entity_spans = {}
        for r in results:
            key = (r.start, r.end)
            if key not in entity_spans:
                entity_spans[key] = []
            entity_spans[key].append(r)
        
        for r in results:
            skip = False
            
            # Para PERSON - usar validador robusto
            if r.entity_type == "PERSON":
                texto_original = request.texto[r.start:r.end]
                logger.debug(f"🔍 spaCy detectou PERSON: '{texto_original}' (score: {r.score:.2f})")
                
                # Extrair contexto ao redor
                context_window = 50
                start_ctx = max(0, r.start - context_window)
                end_ctx = min(len(request.texto), r.end + context_window)
                context = request.texto[start_ctx:end_ctx]
                
                # Usar validador robusto com NameDataset
                is_valid = person_location_filter.should_keep_as_person(texto_original, context, r.score)
                logger.debug(f"✅ PERSON '{texto_original}' - Validador: {is_valid} (score: {r.score:.2f})")
                
                if is_valid:
                    # Validar sobreposição com outros tipos
                    span_key = (r.start, r.end)
                    if span_key in entity_spans:
                        for other in entity_spans[span_key]:
                            if other.entity_type == "EMAIL_ADDRESS":
                                skip = True
                                break
                    
                    if not skip:
                        filtered_results.append(r)
                # else: rejeitar (validador retornou False)
                    
            # Para LOCATION - usar validador robusto
            elif r.entity_type == "LOCATION":
                texto_original = request.texto[r.start:r.end]
                
                # Extrair contexto ao redor
                context_window = 50
                start_ctx = max(0, r.start - context_window)
                end_ctx = min(len(request.texto), r.end + context_window)
                context = request.texto[start_ctx:end_ctx]
                
                # Usar validador robusto com Geopy + PyCountry
                is_valid = person_location_filter.should_keep_as_location(texto_original, context, r.score)
                logger.debug(f"LOCATION '{texto_original}' - Validador: {is_valid} (score: {r.score:.2f})")
                
                if is_valid:
                    filtered_results.append(r)
                # else: rejeitar (validador retornou False)
                    
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
            # Documentos adicionais
            "BR_VOTER_ID": OperatorConfig("replace", {"new_value": "[TÍTULO_ELEITOR]"}),
            "BR_WORK_CARD": OperatorConfig("replace", {"new_value": "[CTPS]"}),
            "BR_DRIVER_LICENSE": OperatorConfig("replace", {"new_value": "[CNH]"}),
            "BR_PIS_PASEP": OperatorConfig("replace", {"new_value": "[PIS/PASEP]"}),
            "BR_CNS": OperatorConfig("replace", {"new_value": "[CNS]"}),
            "BR_PASSPORT": OperatorConfig("replace", {"new_value": "[PASSAPORTE]"}),
            "BR_RESERVISTA": OperatorConfig("replace", {"new_value": "[CERTIFICADO_RESERVISTA]"}),
            "BR_PROFESSIONAL_REGISTRY": OperatorConfig("replace", {"new_value": "[REGISTRO_PROFISSIONAL]"}),
            "BR_PIX_KEY": OperatorConfig("replace", {"new_value": "[CHAVE_PIX]"}),
            "BR_RENAVAM": OperatorConfig("replace", {"new_value": "[RENAVAM]"}),
            "BR_SCHOOL_REGISTRATION": OperatorConfig("replace", {"new_value": "[MATRÍCULA_ESCOLAR]"}),
            "BR_BENEFIT_NUMBER": OperatorConfig("replace", {"new_value": "[NÚMERO_BENEFÍCIO]"}),
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
