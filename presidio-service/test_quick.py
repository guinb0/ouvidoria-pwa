"""
Teste rápido direto com Presidio (sem API)
"""
import sys
sys.path.insert(0, 'C:\\Users\\User\\Downloads\\ouvidoria-pwa\\presidio-service')

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from brazilian_recognizers import *

# Inicializar
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "pt", "model_name": "pt_core_news_sm"}],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()
registry = RecognizerRegistry()
registry.load_predefined_recognizers(nlp_engine=nlp_engine)

registry.add_recognizer(BrazilCpfRecognizer())
registry.add_recognizer(BrazilRgRecognizer())
registry.add_recognizer(BrazilCepRecognizer())
registry.add_recognizer(BrazilPhoneRecognizer())
registry.add_recognizer(BrazilGenericPhoneRecognizer())
registry.add_recognizer(BrazilCnpjRecognizer())
registry.add_recognizer(BrazilEmailRecognizer())
registry.add_recognizer(BrazilDateOfBirthRecognizer())
registry.add_recognizer(BrazilAgeRecognizer())
registry.add_recognizer(BrazilProfessionRecognizer())
registry.add_recognizer(BrazilMaritalStatusRecognizer())
registry.add_recognizer(BrazilNationalityRecognizer())
registry.add_recognizer(BrazilBankAccountRecognizer())
registry.add_recognizer(BrazilContractNumberRecognizer())
registry.add_recognizer(BrazilVehiclePlateRecognizer())
registry.add_recognizer(BrazilGeolocationRecognizer())
registry.add_recognizer(BrazilUsernameRecognizer())
registry.add_recognizer(BrazilIpAddressRecognizer())
registry.add_recognizer(BrazilEthnicityRecognizer())
registry.add_recognizer(BrazilReligionRecognizer())
registry.add_recognizer(BrazilPoliticalOpinionRecognizer())
registry.add_recognizer(BrazilUnionMembershipRecognizer())
registry.add_recognizer(BrazilHealthDataRecognizer())
registry.add_recognizer(BrazilSexualOrientationRecognizer())

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
anonymizer = AnonymizerEngine()

entities = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "CREDIT_CARD",
    "IBAN_CODE", "IP_ADDRESS", "NRP", "US_SSN",
    "BR_CPF", "BR_RG", "BR_CEP", "BR_PHONE", "BR_CNPJ",
    "BR_DATE_OF_BIRTH", "BR_AGE", "BR_PROFESSION", "BR_MARITAL_STATUS", "BR_NATIONALITY",
    "BR_BANK_ACCOUNT", "BR_CONTRACT_NUMBER",
    "BR_VEHICLE_PLATE", "BR_GEOLOCATION", "BR_USERNAME", "BR_IP_EXPLICIT",
    "BR_ETHNICITY", "BR_RELIGION", "BR_POLITICAL_OPINION", "BR_UNION_MEMBERSHIP",
    "BR_HEALTH_DATA", "BR_SEXUAL_ORIENTATION",
]

operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "[NOME]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "[LOCAL]"}),
    "BR_CPF": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX-XX"}),
    "BR_CONTRACT_NUMBER": OperatorConfig("replace", {"new_value": "[PROCESSO/PROTOCOLO]"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "[OCULTO]"}),
}

# Teste simples
texto = """Segundo o item 15.4.1 do Edital, solicito esclarecimentos da CGDF-DF se existe alguma ilegalidade ou impedimento para recebimento da ajuda financeira por candidatos que sejam servidores efetivos de outros entes federativos (União, Estados ou Municípios), que estejam em gozo de férias ou licença não remunerada para participar do curso de formação profissional do referido certame. Além disso, havendo impedimento legal, solicito orientação da CGDF-DF sobre como proceder durante a matrícula no curso de formação, para dirimir as dúvidas dos candidatos que se encontram nessa situação.

Diante dessa resposta emitida pela SEEC, encaminho para a CGDF-DF novo pedido de informações a respeito do questionamento em tela, visto que o cargo para o qual concorro no certame (Auditor de Controle Interno) faz parte da estrutura desta secretaria."""

print("=" * 80)
print("Testando detecção...")
print("=" * 80)
print(f"\nTexto original:\n{texto}\n")

# Analisar
results = analyzer.analyze(
    text=texto,
    language="pt",
    entities=entities,
    score_threshold=0.40
)

# APLICAR FILTROS (mesmos do main.py)
filtered_results = []
entity_spans = {}
for r in results:
    key = (r.start, r.end)
    if key not in entity_spans:
        entity_spans[key] = []
    entity_spans[key].append(r)

location_blacklist = [
    "fixo", "celular", "email", "tel", "fone", "telefone", "documento", "protocolo",
    "sistema", "portal", "plataforma", "aplicativo", "site",
    "aberto", "fechado", "pendente", "concluido", "em andamento"
]

for r in results:
    skip = False
    
    if r.entity_type == "LOCATION":
        texto_detectado = texto[r.start:r.end].lower()
        texto_original = texto[r.start:r.end]
        palavras_loc = texto_detectado.split()
        
        # 1. Blacklist
        if texto_detectado in location_blacklist:
            skip = True
        
        # 2. Filtrar verbos
        if not skip:
            terminacoes_verbais = ["o", "as", "amos", "am", "ei", "ou", "emos", "aram", "ito", "ido"]
            if len(palavras_loc) == 1 and any(texto_detectado.endswith(term) for term in terminacoes_verbais):
                verbos_comuns = [
                    "solicito", "informo", "comunico", "declaro", "afirmo", "venho",
                    "encaminho", "requeiro", "peco", "apresento", "manifesto", "ratifico"
                ]
                if texto_detectado in verbos_comuns:
                    skip = True
        
        # 3. POS tagging
        if not skip and len(palavras_loc) == 1:
            try:
                doc = nlp_engine.process_text(texto_original, "pt")
                if hasattr(doc, 'tokens'):
                    pos_tags = [token.pos_ for token in doc.tokens if hasattr(token, 'pos_')]
                    if any(pos in ['VERB', 'AUX', 'ADP', 'DET'] for pos in pos_tags):
                        skip = True
            except:
                pass
    
    if not skip:
        filtered_results.append(r)

results = filtered_results

print(f"Entidades detectadas: {len(results)}\n")
for r in results:
    valor = texto[r.start:r.end]
    print(f"  - {r.entity_type}: '{valor}' (score: {r.score:.2f})")

# Anonimizar
anonymized_result = anonymizer.anonymize(
    text=texto,
    analyzer_results=results,
    operators=operators
)

print(f"\n{'=' * 80}")
print(f"Texto anonimizado:\n{anonymized_result.text}")
print("=" * 80)
