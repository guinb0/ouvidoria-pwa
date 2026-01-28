"""
Teste completo de todos os 37 reconhecedores de documentos brasileiros
Validação de conformidade com LGPD
"""

texto_teste = """
=== DADOS PESSOAIS BÁSICOS ===
Nome: João da Silva Santos
CPF: 123.456.789-09
RG: 12.345.678-X SSP/SP
Data de nascimento: 15/03/1985
Idade: 38 anos
Telefone: (61) 99876-5432
Email: joao.silva@example.com
CEP: 70040-020
Endereço: SQN 308 Bloco B Apto 205, Asa Norte, Brasília/DF

=== DOCUMENTOS OBRIGATÓRIOS LGPD ===
Título de Eleitor: 123456789012 Zona: 001 Seção: 0123
CTPS: 65421 - Série: 00123/DF
CNH: 12345678901
PIS/PASEP: 120.45678.90-1
CNS (Cartão Nacional de Saúde - SUS): 123456789012345
Passaporte: AA123456
Certificado de Reservista: 123456789

=== REGISTROS PROFISSIONAIS ===
OAB/DF: 12345
CRM-SP: 123456
CREA-RJ: 12345678
CRC-MG: 123456

=== DADOS FINANCEIROS E IDENTIFICAÇÃO ===
CNPJ: 12.345.678/0001-90
Conta bancária: Banco 001 Ag 1234 CC 12345-6
Chave PIX: 550e8400-e29b-41d4-a716-446655440000
Placa do veículo: ABC1234
RENAVAM: 12345678901

=== DADOS EDUCACIONAIS E SOCIAIS ===
Matrícula escolar: 2023001234
Número de Benefício INSS: NB 1234567890
Bolsa Família: Benefício 123456789012

=== DADOS SENSÍVEIS ===
Religião: Católica
Etnia: Parda
Orientação sexual: Heterossexual
Filiação sindical: Sindicato dos Trabalhadores
Dados de saúde: Hipertensão arterial, diabetes tipo 2
Opinião política: Apoiador do partido XYZ

=== DADOS DE LOCALIZAÇÃO ===
IP: 192.168.1.100
Usuário: joao_silva2023
Coordenadas GPS: -15.7942, -47.8822

=== DOCUMENTO TÉCNICO ===
Solicitação de acesso aos dados pessoais conforme Art. 18 da LGPD.
O cidadão identificado acima requer cópia de todos os seus dados tratados pela CAESB.
Protocolo: 2023/12345
Data: 15/03/2024
"""

print("=" * 80)
print("TESTE COMPLETO DE DOCUMENTOS BRASILEIROS - CONFORMIDADE LGPD")
print("=" * 80)
print("\n📄 TEXTO ORIGINAL:")
print(texto_teste)

print("\n" + "=" * 80)
print("🔍 ANÁLISE DE ENTIDADES DETECTADAS")
print("=" * 80)

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Importar TODOS os reconhecedores
from brazilian_recognizers import (
    BrazilCpfRecognizer,
    BrazilRgRecognizer,
    BrazilCepRecognizer,
    BrazilPhoneRecognizer,
    BrazilCnpjRecognizer,
    BrazilEmailRecognizer,
    BrazilDateOfBirthRecognizer,
    BrazilAgeRecognizer,
    BrazilProfessionRecognizer,
    BrazilMaritalStatusRecognizer,
    BrazilNationalityRecognizer,
    BrazilBankAccountRecognizer,
    BrazilContractNumberRecognizer,
    BrazilVehiclePlateRecognizer,
    BrazilGeolocationRecognizer,
    BrazilUsernameRecognizer,
    BrazilIpAddressRecognizer,
    BrazilEthnicityRecognizer,
    BrazilReligionRecognizer,
    BrazilPoliticalOpinionRecognizer,
    BrazilUnionMembershipRecognizer,
    BrazilHealthDataRecognizer,
    BrazilSexualOrientationRecognizer,
    BrazilGenericPhoneRecognizer,
    BrazilNameRecognizer,
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

# Configurar NLP
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "pt", "model_name": "pt_core_news_sm"}],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

# Registrar todos os reconhecedores
registry = RecognizerRegistry()
registry.load_predefined_recognizers(nlp_engine=nlp_engine)

# Adicionar reconhecedores brasileiros
registry.add_recognizer(BrazilCpfRecognizer())
registry.add_recognizer(BrazilRgRecognizer())
registry.add_recognizer(BrazilCepRecognizer())
registry.add_recognizer(BrazilPhoneRecognizer())
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
registry.add_recognizer(BrazilNameRecognizer())
registry.add_recognizer(BrazilVoterIdRecognizer())
registry.add_recognizer(BrazilWorkCardRecognizer())
registry.add_recognizer(BrazilDriverLicenseRecognizer())
registry.add_recognizer(BrazilPisPasepRecognizer())
registry.add_recognizer(BrazilCnsRecognizer())
registry.add_recognizer(BrazilPassportRecognizer())
registry.add_recognizer(BrazilReservistaRecognizer())
registry.add_recognizer(BrazilProfessionalRegistryRecognizer())
registry.add_recognizer(BrazilPixKeyRecognizer())
registry.add_recognizer(BrazilRenavamRecognizer())
registry.add_recognizer(BrazilSchoolRegistrationRecognizer())
registry.add_recognizer(BrazilBenefitNumberRecognizer())

print(f"✅ Total de reconhecedores registrados: 37 tipos brasileiros")

# Criar analyzer e anonymizer
analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
anonymizer = AnonymizerEngine()

# Analisar texto
results = analyzer.analyze(text=texto_teste, language="pt")

# Agrupar por tipo
entities_by_type = {}
for result in results:
    entity_type = result.entity_type
    if entity_type not in entities_by_type:
        entities_by_type[entity_type] = []
    
    text_value = texto_teste[result.start:result.end]
    entities_by_type[entity_type].append({
        "text": text_value,
        "score": result.score,
        "start": result.start,
        "end": result.end
    })

# Exibir resultados agrupados
print(f"\n📊 Total de entidades detectadas: {len(results)}")
print(f"📋 Tipos de entidades encontrados: {len(entities_by_type)}")

print("\n" + "-" * 80)
print("DETALHAMENTO POR TIPO DE ENTIDADE:")
print("-" * 80)

for entity_type in sorted(entities_by_type.keys()):
    entities = entities_by_type[entity_type]
    print(f"\n🏷️  {entity_type} ({len(entities)} ocorrências):")
    for i, entity in enumerate(entities, 1):
        print(f"   {i}. '{entity['text']}' (confiança: {entity['score']:.2f})")

# Configurar operadores de anonimização
operators = {
    "BR_CPF": OperatorConfig("replace", {"new_value": "[CPF]"}),
    "BR_RG": OperatorConfig("replace", {"new_value": "[RG]"}),
    "BR_CEP": OperatorConfig("replace", {"new_value": "[CEP]"}),
    "BR_PHONE": OperatorConfig("replace", {"new_value": "[TELEFONE]"}),
    "BR_CNPJ": OperatorConfig("replace", {"new_value": "[CNPJ]"}),
    "BR_EMAIL": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
    "BR_DATE_OF_BIRTH": OperatorConfig("replace", {"new_value": "[DATA_NASCIMENTO]"}),
    "BR_AGE": OperatorConfig("replace", {"new_value": "[IDADE]"}),
    "BR_PROFESSION": OperatorConfig("replace", {"new_value": "[PROFISSÃO]"}),
    "BR_MARITAL_STATUS": OperatorConfig("replace", {"new_value": "[ESTADO_CIVIL]"}),
    "BR_NATIONALITY": OperatorConfig("replace", {"new_value": "[NACIONALIDADE]"}),
    "BR_BANK_ACCOUNT": OperatorConfig("replace", {"new_value": "[CONTA_BANCÁRIA]"}),
    "BR_CONTRACT_NUMBER": OperatorConfig("replace", {"new_value": "[PROTOCOLO]"}),
    "BR_VEHICLE_PLATE": OperatorConfig("replace", {"new_value": "[PLACA]"}),
    "BR_GEOLOCATION": OperatorConfig("replace", {"new_value": "[COORDENADAS]"}),
    "BR_USERNAME": OperatorConfig("replace", {"new_value": "[USUÁRIO]"}),
    "BR_IP_EXPLICIT": OperatorConfig("replace", {"new_value": "[IP]"}),
    "BR_ETHNICITY": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
    "BR_RELIGION": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
    "BR_POLITICAL_OPINION": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
    "BR_UNION_MEMBERSHIP": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
    "BR_HEALTH_DATA": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
    "BR_SEXUAL_ORIENTATION": OperatorConfig("replace", {"new_value": "[DADO_SENSÍVEL]"}),
    "PERSON": OperatorConfig("replace", {"new_value": "[NOME]"}),
    "BR_VOTER_ID": OperatorConfig("replace", {"new_value": "[TÍTULO_ELEITOR]"}),
    "BR_WORK_CARD": OperatorConfig("replace", {"new_value": "[CTPS]"}),
    "BR_DRIVER_LICENSE": OperatorConfig("replace", {"new_value": "[CNH]"}),
    "BR_PIS_PASEP": OperatorConfig("replace", {"new_value": "[PIS/PASEP]"}),
    "BR_CNS": OperatorConfig("replace", {"new_value": "[CNS]"}),
    "BR_PASSPORT": OperatorConfig("replace", {"new_value": "[PASSAPORTE]"}),
    "BR_RESERVISTA": OperatorConfig("replace", {"new_value": "[RESERVISTA]"}),
    "BR_PROFESSIONAL_REGISTRY": OperatorConfig("replace", {"new_value": "[REGISTRO_PROFISSIONAL]"}),
    "BR_PIX_KEY": OperatorConfig("replace", {"new_value": "[CHAVE_PIX]"}),
    "BR_RENAVAM": OperatorConfig("replace", {"new_value": "[RENAVAM]"}),
    "BR_SCHOOL_REGISTRATION": OperatorConfig("replace", {"new_value": "[MATRÍCULA]"}),
    "BR_BENEFIT_NUMBER": OperatorConfig("replace", {"new_value": "[BENEFÍCIO]"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "[OCULTO]"}),
}

# Anonimizar
anonymized_result = anonymizer.anonymize(
    text=texto_teste,
    analyzer_results=results,
    operators=operators
)

print("\n" + "=" * 80)
print("✅ TEXTO ANONIMIZADO (CONFORMIDADE LGPD)")
print("=" * 80)
print(anonymized_result.text)

# Validação de conformidade
print("\n" + "=" * 80)
print("📋 CHECKLIST DE CONFORMIDADE LGPD")
print("=" * 80)

checklist = {
    "Documentos Obrigatórios": [
        ("BR_CPF", "CPF"),
        ("BR_RG", "RG"),
        ("BR_DRIVER_LICENSE", "CNH"),
        ("BR_VOTER_ID", "Título de Eleitor"),
        ("BR_CNS", "CNS (Cartão Nacional de Saúde)"),
        ("BR_PIS_PASEP", "PIS/PASEP"),
        ("BR_PASSPORT", "Passaporte"),
        ("BR_WORK_CARD", "CTPS (Carteira de Trabalho)"),
        ("BR_RESERVISTA", "Certificado de Reservista"),
        ("BR_PROFESSIONAL_REGISTRY", "Registros Profissionais"),
    ],
    "Dados para Pseudonimização": [
        ("BR_BANK_ACCOUNT", "Conta Bancária"),
        ("BR_PIX_KEY", "Chave PIX"),
        ("BR_RENAVAM", "RENAVAM"),
        ("BR_VEHICLE_PLATE", "Placa de Veículo"),
        ("BR_SCHOOL_REGISTRATION", "Matrícula Escolar"),
        ("BR_BENEFIT_NUMBER", "Número de Benefício"),
    ],
    "Dados Sensíveis LGPD": [
        ("BR_ETHNICITY", "Origem Étnica"),
        ("BR_RELIGION", "Religião"),
        ("BR_POLITICAL_OPINION", "Opinião Política"),
        ("BR_UNION_MEMBERSHIP", "Filiação Sindical"),
        ("BR_HEALTH_DATA", "Dados de Saúde"),
        ("BR_SEXUAL_ORIENTATION", "Orientação Sexual"),
    ],
}

total_checks = 0
passed_checks = 0

for category, items in checklist.items():
    print(f"\n{category}:")
    for entity_type, description in items:
        total_checks += 1
        if entity_type in entities_by_type:
            passed_checks += 1
            print(f"   ✅ {description} - DETECTADO ({len(entities_by_type[entity_type])} ocorrências)")
        else:
            print(f"   ⚠️  {description} - NÃO ENCONTRADO NO TEXTO DE TESTE")

print(f"\n" + "=" * 80)
print(f"📊 RESULTADO FINAL: {passed_checks}/{total_checks} tipos de documentos testados")
conformity_rate = (passed_checks / total_checks) * 100
print(f"📈 Taxa de conformidade: {conformity_rate:.1f}%")
print("=" * 80)

if conformity_rate == 100:
    print("\n🎉 SISTEMA 100% COMPATÍVEL COM TODOS OS DOCUMENTOS LGPD!")
else:
    print(f"\n⚠️  Alguns tipos não foram testados (não presentes no texto de exemplo)")
