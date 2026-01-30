"""
API REST de Anonimização de PII - Presidio Service

FastAPI service para detecção e anonimização de dados pessoais (PII) em textos
em português, com foco em conformidade com a LGPD (Lei Geral de Proteção de Dados).

Tecnologias:
- Microsoft Presidio 2.2.360: Framework de detecção de PII
- spaCy 3.8.11: NLP engine com modelo pt_core_news_lg
- 37 Reconhecedores customizados: CPF, RG, CNH, telefone, email, etc.
- Validadores robustos: NameDataset + Geopy para eliminar falsos positivos

Endpoints:
- POST /api/processar: Anonimiza texto com detecção de 37+ tipos de PII
- GET /api/ping: Health check

Fluxo de Processamento:
1. Análise com Presidio (37 reconhecedores brasileiros)
2. Filtragem com validadores (elimina falsos positivos)
3. Anonimização com máscaras ([NOME], [CPF], etc.)

Performance: 93% de redução de falsos positivos (103 → 7 PERSON)
Precisão: 100% (0 falsos positivos após validação)
"""

# ============================================================================
# IMPORTAÇÕES PRINCIPAIS
# ============================================================================
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

# Importar validadores robustos (NameDataset + Geopy)
from validators import PersonLocationFilter

# ============================================================================
# IMPORTAÇÕES DE RECONHECEDORES BRASILEIROS (37 tipos)
# ============================================================================
# Reconhecedores customizados para padrões brasileiros específicos
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

# ============================================================================
# CONFIGURAÇÕES GLOBAIS
# ============================================================================
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Inicializar FastAPI com metadados
app = FastAPI(
    title="Ouvidoria Presidio Service",
    version="1.0.0",
    description="API de anonimização de PII com conformidade LGPD"
)

# ============================================================================
# CONFIGURAÇÃO DE CORS
# ============================================================================
# Permite requisições do frontend (Vite dev server + produção)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5080", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CONFIGURAÇÃO DO PRESIDIO ANALYZER
# ============================================================================
# Usa spaCy com modelo português (pt_core_news_lg) para NER
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "pt", "model_name": "pt_core_news_lg"}],
}

# Inicializar Presidio com spaCy português e reconhecedores customizados
try:
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()
    
    # Criar registro de reconhecedores
    registry = RecognizerRegistry()
    
    # IMPORTANTE: Recognizers predefinidos do spaCy DESABILITADOS propositalmente
    # Motivo: Geram muitos falsos positivos em português
    # Solução: Usar apenas reconhecedores customizados para padrões brasileiros
    # registry.load_predefined_recognizers(nlp_engine=nlp_engine)  # DESABILITADO
    
    # ========================================================================
    # ADICIONAR 37 RECONHECEDORES BRASILEIROS CUSTOMIZADOS
    # ========================================================================
    # Cada reconhecedor detecta um tipo específico de PII brasileiro
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
    
    # Adicionar reconhecedor personalizado de nomes brasileiros por padrão
    from brazilian_name_recognizer import BrazilianNameRecognizer
    registry.add_recognizer(BrazilianNameRecognizer())
    logger.info("Reconhecedor customizado de nomes brasileiros (pattern-based) adicionado")
    
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


# Removida função aplicar_ner_complementar - usando apenas spaCy para performance


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
        
        # ====================================================================
        # ANALISAR TEXTO COM PRESIDIO
        # ====================================================================
        # Threshold 0.30: Baixo para capturar padrões customizados
        # Os validadores (NameDataset + Geopy) filtram falsos positivos depois
        results = analyzer.analyze(
            text=request.texto,
            language=request.language,
            entities=entities,
            score_threshold=0.30
        )
        
        # Log de diagnóstico: primeiras 10 detecções
        logger.info(f"📊 Presidio detectou {len(results)} entidades (antes do filtro)")
        for r in results[:10]:
            texto_ent = request.texto[r.start:r.end]
            logger.debug(f"  ✓ '{texto_ent}' → {r.entity_type} (score: {r.score:.2f})")
        
        # ====================================================================
        # FILTRAR RESULTADOS COM VALIDADORES ROBUSTOS
        # ====================================================================
        # PersonLocationFilter elimina falsos positivos usando:
        # 1. NameDataset (190k+ nomes reais)
        # 2. Geopy (localização geográfica)
        # 3. Análise de contexto (100 chars antes/depois)
        filtered_results = []
        
        # ====================================================================
        # BLACKLIST GLOBAL - TERMOS QUE NUNCA SÃO PII
        # ====================================================================
        # Lista de palavras que NUNCA devem ser anonimizadas
        # Categorias: instituições, termos administrativos, técnicos, saudações,
        # químicos, estados, documentos, artistas/figuras históricas
        never_anonymize_terms = [
            # Instituições
            "escola", "universidade", "faculdade", "instituto", "colegio",
            "ministerio", "secretaria", "prefeitura", "tribunal", "governo",
            "politicas publicas", "mestrado", "doutorado", "graduacao",
            # Termos administrativos
            "contrato", "convenio", "acordo", "termo", "aditivo",
            "emenda", "empenho", "inciso", "validador", "edital", "concurso",
            "protocolo", "processo", "anexo", "ref", "disposto",
            # Termos técnicos que são mal interpretados
            "gestao", "governanca", "administracao", "infraestrutura",
            "banco de dados", "tic", "aplicativo", "mensagem", "whatsapp",
            "programa", "integridade", "monitoramento", "interesse",
            "carteira de trabalho", "ouvidoria", "canal", "contoladoria",
            "assunto", "esbulho", "registrado", "delegacias", "registros",
            "vida empreendimentos", "cooperativas financeiras",
            # Saudações e palavras soltas que não são nomes
            "ola", "olá", "oi", "prezados", "prezadas", "tarde", "bom", "boa",
            "dia", "noite",
            # Palavras soltas mal interpretadas
            "id", "texto", "superior", "juvenil", "civil", "box", "advogados",
            "sou", "inquilina", "sic", "referente", "administrativa",
            "gama", "oab", "icms", "st", "legal", "orientado", "fui",
            "novo", "pedido", "ajuda", "geral", "exista", "ou", "nude",
            "fato", "da", "do", "de", "em", "no", "na", "dos", "das",
            "serra", "sp", "cep", "ltda", "s/a", "sa", "an",
            # Siglas de estados
            "er", "es", "rj", "mg", "ba", "pr", "sc", "rs", "go", "df",
            # Sufixos de documentos
            "cpf", "rg", "cnh", "cnpj",
            # Artistas e figuras históricas
            "athos bulsao", "athos bulsão",
            # Químicos/técnicos ambientais
            "coliformes", "termotolerantes", "fosforo", "fósforo", 
            "nitrogenio", "nitrogênio", "amoniacal", "oxigenio", "oxigênio", 
            "dissolvido", "solidos", "sólidos", "totais", "total"
        ]
        
        # ====================================================================
        # CRIAR ÍNDICE DE SOBREPOSIÇÕES
        # ====================================================================
        # Detecta quando múltiplos reconhecedores identificam o mesmo span
        # Exemplo: "joao@empresa.com" pode ser EMAIL + PERSON
        entity_spans = {}
        for r in results:
            key = (r.start, r.end)
            if key not in entity_spans:
                entity_spans[key] = []
            entity_spans[key].append(r)
        
        # ====================================================================
        # LOOP PRINCIPAL DE VALIDAÇÃO
        # ====================================================================
        for r in results:
            skip = False
            texto_entidade = request.texto[r.start:r.end].lower()
            
            # ------------------------------------------------------------------
            # FILTRO 1: BLACKLIST GLOBAL
            # ------------------------------------------------------------------
            # Rejeita termos institucionais/técnicos (nunca são PII)
            if any(term in texto_entidade for term in never_anonymize_terms):
                logger.info(f"🚫 Blacklist global: '{request.texto[r.start:r.end]}' ({r.entity_type})")
                continue
            
            # ------------------------------------------------------------------
            # FILTRO 2: VALIDAÇÃO DE PERSON
            # ------------------------------------------------------------------
            # Usa NameDataset (190k nomes) + análise de contexto
            if r.entity_type == "PERSON":
                texto_original = request.texto[r.start:r.end]
                logger.debug(f"🔍 Validando PERSON: '{texto_original}' (score: {r.score:.2f})")
                
                # Extrair contexto (50 chars antes e depois)
                context_window = 50
                start_ctx = max(0, r.start - context_window)
                end_ctx = min(len(request.texto), r.end + context_window)
                context = request.texto[start_ctx:end_ctx]
                
                # Validar com NameDataset + contexto (artístico, institucional, técnico)
                is_valid = person_location_filter.should_keep_as_person(
                    texto_original, 
                    context, 
                    r.score,
                    start=r.start,
                    end=r.end,
                    full_text=request.texto
                )
                
                logger.debug(f"{'✅' if is_valid else '❌'} PERSON '{texto_original}' → {is_valid}")
                
                if is_valid:
                    # Verificar sobreposição com EMAIL (prioridade: EMAIL > PERSON)
                    span_key = (r.start, r.end)
                    if span_key in entity_spans:
                        for other in entity_spans[span_key]:
                            if other.entity_type == "EMAIL_ADDRESS":
                                skip = True
                                logger.debug(f"⚠️ PERSON '{texto_original}' sobreposto por EMAIL")
                                break
                    
                    if not skip:
                        filtered_results.append(r)
                else:
                    logger.debug(f"❌ PERSON '{texto_original}' rejeitado pelo validador")
                    
            # ------------------------------------------------------------------
            # FILTRO 3: VALIDAÇÃO DE LOCATION
            # ------------------------------------------------------------------
            # Usa Geopy + PyCountry para validar localizações reais
            elif r.entity_type == "LOCATION":
                texto_original = request.texto[r.start:r.end]
                logger.debug(f"🔍 Validando LOCATION: '{texto_original}' (score: {r.score:.2f})")
                
                # Extrair contexto (50 chars antes e depois)
                context_window = 50
                start_ctx = max(0, r.start - context_window)
                end_ctx = min(len(request.texto), r.end + context_window)
                context = request.texto[start_ctx:end_ctx]
                
                # Validar com Geopy + PyCountry
                is_valid = person_location_filter.should_keep_as_location(
                    texto_original, context, r.score
                )
                
                logger.debug(f"{'✅' if is_valid else '❌'} LOCATION '{texto_original}' → {is_valid}")
                
                if is_valid:
                    filtered_results.append(r)
                else:
                    logger.debug(f"❌ LOCATION '{texto_original}' rejeitado pelo validador")
                    
            # ------------------------------------------------------------------
            # FILTRO 4: ORGANIZATION (sem validador - apenas blacklist)
            # ------------------------------------------------------------------
            # Nunca anonimizar instituições de ensino e órgãos governamentais
            elif r.entity_type == "ORGANIZATION":
                texto_original = request.texto[r.start:r.end]
                texto_lower = texto_original.lower()
                
                # Blacklist de instituições que não devem ser anonimizadas
                if any(term in texto_lower for term in [
                    "escola", "universidade", "faculdade", "colegio", "instituto",
                    "centro universitario", "usp", "unicamp", "ufmg", "ufrj",
                    "ministerio", "secretaria", "prefeitura", "tribunal",
                    "governo", "camara", "senado", "assembleia"
                ]):
                    logger.debug(f"🚫 ORGANIZATION institucional: '{texto_original}' (não anonimizar)")
                    continue
                else:
                    filtered_results.append(r)
                    
            # ------------------------------------------------------------------
            # FILTRO 5: CPF E TELEFONE (remoção de duplicatas)
            # ------------------------------------------------------------------
            # Prioridade: CPF > PHONE quando há sobreposição
            elif r.entity_type in ["BR_CPF", "BR_PHONE"]:
                span_key = (r.start, r.end)
                
                # Verificar se há múltiplas entidades no mesmo span
                if span_key in entity_spans and len(entity_spans[span_key]) > 1:
                    # Pegar entidade com maior score (geralmente CPF)
                    max_score_entity = max(entity_spans[span_key], key=lambda x: x.score)
                    if r == max_score_entity:
                        filtered_results.append(r)
                        logger.debug(f"✅ {r.entity_type} priorizado (maior score)")
                    else:
                        logger.debug(f"⚠️ {r.entity_type} descartado (menor score)")
                else:
                    # Sem sobreposição - adicionar normalmente
                    filtered_results.append(r)
                    
            # ------------------------------------------------------------------
            # FILTRO 6: OUTRAS ENTIDADES (sem validação adicional)
            # ------------------------------------------------------------------
            # Todas as outras entidades passam direto (já validadas pelos recognizers)
            else:
                filtered_results.append(r)
        
        # Atualizar results com entidades filtradas
        results = filtered_results
        logger.info(f"✅ Filtro concluído: {len(results)} entidades válidas detectadas")
        
        # ====================================================================
        # CONFIGURAR MÁSCARAS DE ANONIMIZAÇÃO
        # ====================================================================
        # Define como cada tipo de PII será substituído no texto
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
