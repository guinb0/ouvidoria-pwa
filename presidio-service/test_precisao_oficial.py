"""
Teste com amostra oficial e-SIC (formato TXT) - Cálculo de Precisão
"""
import sys
import re
from collections import defaultdict
sys.path.insert(0, 'C:\\Users\\User\\Downloads\\ouvidoria-pwa\\presidio-service')

# Importar Presidio diretamente
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

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
    BrazilHealthDataRecognizer, BrazilSexualOrientationRecognizer,
    BrazilGenericPhoneRecognizer, BrazilNameRecognizer,
)

print("=" * 80)
print("TESTE COM AMOSTRA OFICIAL e-SIC - ANÁLISE DE PRECISÃO")
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

registry = RecognizerRegistry()
registry.load_predefined_recognizers(nlp_engine=nlp_engine)

# Adicionar reconhecedores brasileiros
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
registry.add_recognizer(BrazilNameRecognizer())

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)
anonymizer = AnonymizerEngine()

print("✅ Presidio inicializado (22 reconhecedores brasileiros)")
print()

# Ler arquivo TXT
print("📄 Lendo AMOSTRA_e-SIC.txt...")
with open("../AMOSTRA_e-SIC.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

# Parsear arquivo (formato: ID | Texto)
textos = []
texto_atual = []
id_atual = None

for line in lines[1:]:  # Pular header
    line = line.strip()
    if not line:
        continue
    
    # Tentar extrair ID
    match = re.match(r'^(\d+)\s+(.+)', line)
    if match:
        # Salvar texto anterior
        if texto_atual:
            textos.append({
                'id': id_atual,
                'texto': ' '.join(texto_atual).strip()
            })
            texto_atual = []
        
        id_atual = int(match.group(1))
        texto_atual.append(match.group(2))
    else:
        # Continuação do texto
        texto_atual.append(line)

# Salvar último texto
if texto_atual:
    textos.append({
        'id': id_atual,
        'texto': ' '.join(texto_atual).strip()
    })

print(f"✅ {len(textos)} textos carregados")
print()

# Entidades a detectar
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

# Operadores de anonimização
operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "[NOME]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "(XX) XXXXX-XXXX"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "[LOCAL]"}),
    "CREDIT_CARD": OperatorConfig("mask", {"masking_char": "X", "chars_to_mask": 12, "from_end": False}),
    "BR_CPF": OperatorConfig("replace", {"new_value": "XXX.XXX.XXX-XX"}),
    "BR_RG": OperatorConfig("replace", {"new_value": "XX.XXX.XXX-X"}),
    "BR_CEP": OperatorConfig("replace", {"new_value": "XXXXX-XXX"}),
    "BR_PHONE": OperatorConfig("replace", {"new_value": "(XX) XXXXX-XXXX"}),
    "BR_CONTRACT_NUMBER": OperatorConfig("replace", {"new_value": "[PROCESSO/PROTOCOLO]"}),
    "DEFAULT": OperatorConfig("replace", {"new_value": "[OCULTO]"}),
}

# Padrões sensíveis que DEVEM ser detectados
patterns_check = {
    "CPF": r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    "Telefone": r'\(?\d{2}\)?\s?\d{4,5}-\d{4}',  # Apenas com hífen
    "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "Nome": r'\b[A-Z][a-z]+\s+(?:[A-Z][a-z]+\s+){1,3}[A-Z][a-z]+\b',  # Pelo menos 2 palavras capitalizadas
    "Processo SEI": r'\b\d{5}-\d{8}/\d{4}-\d{2}\b',
}

print("🔍 Processando textos...")
print()

total_padroes_encontrados = 0
total_padroes_mascarados = 0
resultados_detalhados = []
padroes_nao_detectados = defaultdict(int)

for idx, item in enumerate(textos, 1):
    texto = item['texto']
    
    # Detectar padrões no texto original
    padroes_no_texto = {}
    for nome_padrao, regex in patterns_check.items():
        matches = list(set(re.findall(regex, texto)))  # unique
        if matches:
            padroes_no_texto[nome_padrao] = matches
            total_padroes_encontrados += len(matches)
    
    # Processar com Presidio
    try:
        results = analyzer.analyze(
            text=texto,
            language="pt",
            entities=entities,
            score_threshold=0.50
        )
        
        anonymized_result = anonymizer.anonymize(
            text=texto,
            analyzer_results=results,
            operators=operators
        )
        
        texto_anonimizado = anonymized_result.text
        
        # Verificar quais padrões foram mascarados
        padroes_mascarados = 0
        for nome_padrao, matches in padroes_no_texto.items():
            for match in matches:
                if match not in texto_anonimizado:
                    padroes_mascarados += 1
                    total_padroes_mascarados += 1
                else:
                    padroes_nao_detectados[nome_padrao] += 1
        
        resultados_detalhados.append({
            'id': item['id'],
            'entidades_detectadas': len(results),
            'padroes_originais': len(sum([v for v in padroes_no_texto.values()], [])),
            'padroes_mascarados': padroes_mascarados,
        })
        
        if idx % 10 == 0:
            print(f"  Processados: {idx}/{len(textos)} ({idx/len(textos)*100:.1f}%)")
            
    except Exception as e:
        print(f"  ❌ Erro no texto {item['id']}: {str(e)[:50]}")

print()
print("=" * 80)
print("📊 RESULTADOS - PRECISÃO DE DETECÇÃO")
print("=" * 80)
print()

# Calcular precisão
if total_padroes_encontrados > 0:
    precisao = (total_padroes_mascarados / total_padroes_encontrados) * 100
else:
    precisao = 100.0

print(f"🎯 Padrões sensíveis encontrados nos textos: {total_padroes_encontrados}")
print(f"✅ Padrões corretamente mascarados: {total_padroes_mascarados}")
print(f"❌ Padrões NÃO mascarados: {total_padroes_encontrados - total_padroes_mascarados}")
print()
print("=" * 80)
print(f"📈 PRECISÃO ATUAL: {precisao:.2f}%")
print(f"🎯 OBJETIVO: 98.00%")
print(f"📉 GAP: {max(0, 98.00 - precisao):.2f}%")
print("=" * 80)
print()

# Salvar análise detalhada em JSON
import json
analise_detalhada = {
    "resumo": {
        "precisao": f"{precisao:.2f}%",
        "total_padroes_encontrados": total_padroes_encontrados,
        "padroes_mascarados": total_padroes_mascarados,
        "padroes_nao_mascarados": total_padroes_encontrados - total_padroes_mascarados,
        "gap_para_98": f"{max(0, 98.00 - precisao):.2f}%"
    },
    "falsos_negativos": {},
    "exemplos_nao_detectados": []
}

# Coletar exemplos específicos de falsos negativos
for idx, item in enumerate(textos, 1):
    texto = item['texto']
    
    padroes_no_texto = {}
    for nome_padrao, regex in patterns_check.items():
        matches = list(set(re.findall(regex, texto)))
        if matches:
            padroes_no_texto[nome_padrao] = matches
    
    if not padroes_no_texto:
        continue
    
    # Processar com Presidio
    results = analyzer.analyze(
        text=texto,
        language="pt",
        entities=entities,
        score_threshold=0.40
    )
    
    anonymized_result = anonymizer.anonymize(
        text=texto,
        analyzer_results=results,
        operators=operators
    )
    
    texto_anonimizado = anonymized_result.text
    
    # Verificar quais padrões NÃO foram mascarados
    for nome_padrao, matches in padroes_no_texto.items():
        for match in matches:
            if match in texto_anonimizado:
                # FALSO NEGATIVO: padrão não foi detectado
                if nome_padrao not in analise_detalhada["falsos_negativos"]:
                    analise_detalhada["falsos_negativos"][nome_padrao] = []
                
                analise_detalhada["exemplos_nao_detectados"].append({
                    "id_texto": item['id'],
                    "tipo": nome_padrao,
                    "valor": match,
                    "contexto": texto[max(0, texto.find(match)-50):texto.find(match)+len(match)+50]
                })
                
                analise_detalhada["falsos_negativos"][nome_padrao].append({
                    "id": item['id'],
                    "valor": match
                })

with open("analise_falsos_negativos.json", "w", encoding="utf-8") as f:
    json.dump(analise_detalhada, f, ensure_ascii=False, indent=2)

print(f"✅ Análise detalhada salva em: analise_falsos_negativos.json")
print()

if padroes_nao_detectados:
    print("⚠️  PADRÕES NÃO DETECTADOS POR TIPO:")
    print()
    for tipo, count in sorted(padroes_nao_detectados.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {tipo}: {count} ocorrências")
    print()

# Estatísticas gerais
total_entidades = sum(r['entidades_detectadas'] for r in resultados_detalhados)
print(f"📊 Total de entidades detectadas: {total_entidades}")
print(f"📊 Média por texto: {total_entidades/len(textos):.1f}")
print()

# Análise de gaps
if precisao < 98:
    print("=" * 80)
    print("🔧 RECOMENDAÇÕES PARA ATINGIR 98%")
    print("=" * 80)
    print()
    
    if padroes_nao_detectados.get("CPF", 0) > 0:
        print("  1. ✏️  Melhorar detecção de CPF")
        print("     - Ajustar threshold de 0.95 para 0.80")
        print("     - Adicionar validação de contexto mais flexível")
        print()
    
    if padroes_nao_detectados.get("Telefone", 0) > 0:
        print("  2. ✏️  Melhorar detecção de telefones")
        print("     - Adicionar padrões sem parênteses e sem espaços")
        print("     - Reduzir score mínimo de 0.60 para 0.50")
        print()
    
    if padroes_nao_detectados.get("Nome", 0) > 0:
        print("  3. ✏️  Melhorar detecção de nomes")
        print("     - Reduzir threshold de PERSON de 0.75 para 0.65")
        print("     - Adicionar lista de nomes brasileiros comuns")
        print()
    
    if padroes_nao_detectados.get("Processo SEI", 0) > 0:
        print("  4. ✏️  Adicionar reconhecedor específico para processos SEI")
        print("     - Padrão: 00015-01009853/2026-01")
        print()
else:
    print("🎉 OBJETIVO ALCANÇADO!")
    print("   Sistema está com precisão >= 98%")

print()
print("✅ Teste concluído!")
