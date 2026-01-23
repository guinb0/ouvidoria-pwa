"""
Teste direto dos reconhecedores com a amostra oficial e-SIC
Calcula precisão sem precisar de servidor HTTP
"""
import pandas as pd
import re
import json
import sys
from collections import defaultdict

# Adicionar path
sys.path.insert(0, 'C:\\Users\\User\\Downloads\\ouvidoria-pwa\\presidio-service')

# Importar componentes Presidio
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Importar reconhecedores brasileiros
from brazilian_recognizers import (
    BrazilCpfRecognizer, BrazilRgRecognizer, BrazilCepRecognizer,
    BrazilPhoneRecognizer, BrazilCnpjRecognizer, BrazilEmailRecognizer,
    BrazilDateOfBirthRecognizer, BrazilAgeRecognizer, BrazilProfessionRecognizer,
    BrazilMaritalStatusRecognizer, BrazilNationalityRecognizer,
    BrazilBankAccountRecognizer, BrazilContractNumberRecognizer,
    BrazilVehiclePlateRecognizer, BrazilGeolocationRecognizer,
    BrazilUsernameRecognizer, BrazilIpAddressRecognizer,
    BrazilEthnicityRecognizer, BrazilReligionRecognizer,
    BrazilPoliticalOpinionRecognizer, BrazilUnionMembershipRecognizer,
    BrazilHealthDataRecognizer, BrazilSexualOrientationRecognizer
)

print("=" * 80)
print("TESTE COM AMOSTRA OFICIAL e-SIC - CÁLCULO DE PRECISÃO")
print("=" * 80)
print()

# Inicializar Presidio
print("🔧 Inicializando Presidio...")
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "pt", "model_name": "pt_core_news_sm"}],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()

# Criar registro de reconhecedores
registry = RecognizerRegistry()
registry.load_predefined_recognizers(nlp_engine=nlp_engine)

# Adicionar todos os reconhecedores brasileiros
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

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
anonymizer = AnonymizerEngine()

print("✅ Presidio inicializado com 33 tipos de entidades")
print()

# Ler arquivo Excel
df = pd.read_excel("../AMOSTRA_e-SIC.xlsx")
textos = df["Texto Mascarado"].dropna().astype(str).tolist()

print(f"📊 Total de textos: {len(textos)}")
print()

# Padrões que DEVEM ser detectados
patterns_check = {
    "CPF": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    "Telefone": r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}",
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "CEP_8digitos": r"(?<!\d)\d{8}(?!\d)",
    "CEP_formatado": r"\b\d{5}-\d{3}\b",
    "Processo_SEI": r"\b\d{5}-\d{8}/\d{4}-\d{2}\b",
}

# Definir entidades a detectar
entities = [
    "PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER", "LOCATION", "CREDIT_CARD",
    "IBAN_CODE", "IP_ADDRESS", "NRP", "US_SSN",
    "BR_CPF", "BR_RG", "BR_CEP", "BR_CNPJ", "BR_PHONE",
    "BR_DATE_OF_BIRTH", "BR_AGE", "BR_PROFESSION", "BR_MARITAL_STATUS", "BR_NATIONALITY",
    "BR_BANK_ACCOUNT", "BR_CONTRACT_NUMBER",
    "BR_VEHICLE_PLATE", "BR_GEOLOCATION", "BR_USERNAME", "BR_IP_EXPLICIT",
    "BR_ETHNICITY", "BR_RELIGION", "BR_POLITICAL_OPINION", "BR_UNION_MEMBERSHIP",
    "BR_HEALTH_DATA", "BR_SEXUAL_ORIENTATION",
]

# Operadores de anonimização
operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "[NOME]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "(XX) XXXXX-XXXX"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "[LOCAL]"}),
    "CREDIT_CARD": OperatorConfig("mask", {"masking_char": "X", "chars_to_mask": 12, "from_end": False}),
    "IP_ADDRESS": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX.XXX"}),
    "BR_CPF": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX-XX"}),
    "BR_RG": OperatorConfig("replace", {"new_value": "XX.XXX.XXX-X"}),
    "BR_CEP": OperatorConfig("replace", {"new_value": "XXXXX-XXX"}),
    "BR_PHONE": OperatorConfig("replace", {"new_value": "(XX) XXXXX-XXXX"}),
    "BR_CNPJ": OperatorConfig("replace", {"new_value": "XX.XXX.XXX/XXXX-XX"}),
    "BR_DATE_OF_BIRTH": OperatorConfig("replace", {"new_value": "DD/MM/AAAA"}),
    "BR_BANK_ACCOUNT": OperatorConfig("replace", {"new_value": "[DADOS_BANCÁRIOS]"}),
    "BR_CONTRACT_NUMBER": OperatorConfig("replace", {"new_value": "[CONTRATO/PROTOCOLO]"}),
    "BR_VEHICLE_PLATE": OperatorConfig("replace", {"new_value": "XXX-XXXX"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "[OCULTO]"}),
}

print("🔍 Processando todos os textos...")
print()

# Processar todos os textos
resultados = []
padroes_nao_detectados = defaultdict(int)
padroes_detectados_list = []
total_padroes_esperados = 0
total_padroes_detectados = 0

for i, texto in enumerate(textos, 1):
    # Contar padrões sensíveis no texto original
    padroes_no_texto = {}
    for nome_padrao, regex in patterns_check.items():
        matches = re.findall(regex, texto)
        if matches:
            padroes_no_texto[nome_padrao] = matches
            total_padroes_esperados += len(matches)
    
    # Analisar texto
    try:
        results = analyzer.analyze(
            text=texto,
            language="pt",
            entities=entities,
            score_threshold=0.45  # Threshold mais baixo para aumentar recall
        )
        
        # Anonimizar
        anonymized_result = anonymizer.anonymize(
            text=texto,
            analyzer_results=results,
            operators=operators
        )
        
        texto_anonimizado = anonymized_result.text
        
        # Verificar se padrões ainda aparecem no texto anonimizado
        padroes_ainda_visiveis = {}
        for nome_padrao, matches_originais in padroes_no_texto.items():
            ainda_visiveis = []
            for match in matches_originais:
                if match in texto_anonimizado:
                    padroes_nao_detectados[nome_padrao] += 1
                    ainda_visiveis.append(match)
                else:
                    total_padroes_detectados += 1
            
            if ainda_visiveis:
                padroes_ainda_visiveis[nome_padrao] = ainda_visiveis
        
        resultados.append({
            "id": i,
            "entidades_detectadas": len(results),
            "padroes_originais": padroes_no_texto,
            "padroes_nao_mascarados": padroes_ainda_visiveis,
        })
        
    except Exception as e:
        print(f"❌ Erro no texto {i}: {str(e)}")
        resultados.append({"id": i, "erro": str(e)})
    
    if i % 20 == 0:
        print(f"  Processados: {i}/{len(textos)} ({i/len(textos)*100:.1f}%)")

print()
print("=" * 80)
print("📊 RESULTADOS FINAIS")
print("=" * 80)
print()

# Calcular métricas
taxa_deteccao = (total_padroes_detectados / total_padroes_esperados * 100) if total_padroes_esperados > 0 else 100

print(f"Total de padrões sensíveis encontrados: {total_padroes_esperados}")
print(f"Padrões corretamente mascarados: {total_padroes_detectados}")
print(f"Padrões NÃO mascarados (falso negativo): {total_padroes_esperados - total_padroes_detectados}")
print()
print("=" * 80)
print(f"📈 TAXA DE DETECÇÃO: {taxa_deteccao:.2f}%")
print("=" * 80)
print()

if padroes_nao_detectados:
    print("⚠️  Padrões não detectados por tipo:")
    for nome, count in sorted(padroes_nao_detectados.items(), key=lambda x: x[1], reverse=True):
        print(f"  ❌ {nome}: {count} ocorrências não mascaradas")
    print()

# Mostrar exemplos
print("=" * 80)
print("📋 EXEMPLOS DE FALSOS NEGATIVOS")
print("=" * 80)
print()

exemplos_mostrados = 0
for r in resultados:
    if r.get("padroes_nao_mascarados") and exemplos_mostrados < 5:
        print(f"Texto {r['id']}:")
        for tipo, matches in r['padroes_nao_mascarados'].items():
            print(f"  {tipo}: {matches}")
        print()
        exemplos_mostrados += 1

# Salvar relatório
relatorio = {
    "total_textos": len(textos),
    "total_padroes_esperados": total_padroes_esperados,
    "padroes_detectados": total_padroes_detectados,
    "padroes_nao_detectados_totais": total_padroes_esperados - total_padroes_detectados,
    "taxa_deteccao": f"{taxa_deteccao:.2f}%",
    "precisao_objetivo": "98.00%",
    "gap": f"{max(0, 98.00 - taxa_deteccao):.2f}%",
    "breakdown_falsos_negativos": dict(padroes_nao_detectados),
}

with open("relatorio_precisao_oficial.json", "w", encoding="utf-8") as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)

print("✅ Relatório salvo em: relatorio_precisao_oficial.json")
print()

# Recomendações
if taxa_deteccao < 98:
    print("🔧 RECOMENDAÇÕES PARA ATINGIR 98%:")
    print("=" * 80)
    
    if padroes_nao_detectados.get("CEP_8digitos", 0) > 0:
        print(f"  1. CEP sem hífen: {padroes_nao_detectados['CEP_8digitos']} não detectados")
        print("     → Ajustar threshold do BrazilCepRecognizer")
        print()
    
    if padroes_nao_detectados.get("CPF", 0) > 0:
        print(f"  2. CPF: {padroes_nao_detectados['CPF']} não detectados")
        print("     → Reduzir score threshold de 0.55 para 0.45")
        print()
    
    if padroes_nao_detectados.get("Telefone", 0) > 0:
        print(f"  3. Telefone: {padroes_nao_detectados['Telefone']} não detectados")
        print("     → Melhorar regex para variações sem parênteses")
        print()
    
    if padroes_nao_detectados.get("Processo_SEI", 0) > 0:
        print(f"  4. Processo SEI: {padroes_nao_detectados['Processo_SEI']} não detectados")
        print("     → Adicionar pattern específico para processos SEI")
        print()
else:
    print("🎉 OBJETIVO ATINGIDO!")
    print("=" * 80)
    print(f"Taxa de detecção: {taxa_deteccao:.2f}% >= 98.00%")
