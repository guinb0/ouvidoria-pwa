"""
Análise completa de Falsos Positivos e Falsos Negativos
"""
import sys
import re
from collections import defaultdict
import json
sys.path.insert(0, 'C:\\Users\\User\\Downloads\\ouvidoria-pwa\\presidio-service')

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from brazilian_recognizers import *

print("=" * 80)
print("ANÁLISE DE FALSOS POSITIVOS E FALSOS NEGATIVOS")
print("=" * 80)
print()

# Inicializar Presidio
print("🔧 Inicializando...")
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "pt", "model_name": "pt_core_news_sm"}],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()
registry = RecognizerRegistry()
registry.load_predefined_recognizers(nlp_engine=nlp_engine)

# Adicionar todos os reconhecedores
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

# Ler textos
with open("../AMOSTRA_e-SIC.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

textos = []
texto_atual = []
id_atual = None

for line in lines[1:]:
    line = line.strip()
    if not line:
        continue
    
    match = re.match(r'^(\d+)\s+(.+)', line)
    if match:
        if texto_atual:
            textos.append({'id': id_atual, 'texto': ' '.join(texto_atual).strip()})
            texto_atual = []
        id_atual = int(match.group(1))
        texto_atual.append(match.group(2))
    else:
        texto_atual.append(line)

if texto_atual:
    textos.append({'id': id_atual, 'texto': ' '.join(texto_atual).strip()})

print(f"✅ {len(textos)} textos carregados")
print()

# Padrões sensíveis conhecidos (ground truth)
patterns_ground_truth = {
    "CPF": r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    "Telefone": r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
    "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "Nome Completo": r'\b[A-Z][a-z]+\s+(?:[A-Z][a-z]+\s+){1,3}[A-Z][a-z]+\b',
    "Processo SEI": r'\b\d{5}-\d{8}/\d{4}-\d{2}\b',
}

# Padrões que NÃO devem ser detectados (palavras comuns)
palavras_comuns = [
    "Distrito Federal", "Governo", "Prefeitura", "Ministério", "Secretaria",
    "Brasil", "Brasília", "Estado", "Municipal", "Federal",
    "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo",
    "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

print("🔍 Analisando textos...")
print()

falsos_negativos = []  # Deveria detectar mas não detectou
falsos_positivos = []  # Detectou mas não deveria

total_ground_truth = 0
total_detectado = 0

for item in textos:
    texto = item['texto']
    
    # 1. Ground truth (o que deveria ser detectado)
    padroes_esperados = {}
    for nome, regex in patterns_ground_truth.items():
        matches = list(set(re.findall(regex, texto)))
        if matches:
            padroes_esperados[nome] = matches
            total_ground_truth += len(matches)
    
    # 2. O que o Presidio detectou
    results = analyzer.analyze(
        text=texto,
        language="pt",
        entities=entities,
        score_threshold=0.40
    )
    
    total_detectado += len(results)
    
    anonymized_result = anonymizer.anonymize(
        text=texto,
        analyzer_results=results,
        operators=operators
    )
    
    texto_anonimizado = anonymized_result.text
    
    # 3. Verificar FALSOS NEGATIVOS (esperado mas não detectado)
    for tipo, matches in padroes_esperados.items():
        for match in matches:
            if match in texto_anonimizado:
                # Ainda está no texto = NÃO FOI DETECTADO
                falsos_negativos.append({
                    "id": item['id'],
                    "tipo": tipo,
                    "valor": match,
                    "contexto": texto[max(0, texto.find(match)-40):texto.find(match)+len(match)+40]
                })
    
    # 4. Verificar FALSOS POSITIVOS (detectou mas não deveria)
    for result in results:
        valor_detectado = texto[result.start:result.end]
        
        # Verificar se é palavra comum (não deveria ser mascarada)
        if result.entity_type == "PERSON":
            # Verificar se é palavra comum que não deveria ser detectada
            if valor_detectado in palavras_comuns:
                falsos_positivos.append({
                    "id": item['id'],
                    "tipo": result.entity_type,
                    "valor": valor_detectado,
                    "score": result.score,
                    "motivo": "Palavra comum (não é nome pessoal)"
                })
            
            # Verificar se é apenas 1 palavra (provavelmente não é nome completo)
            elif " " not in valor_detectado and "." not in valor_detectado:
                # Verificar se não está nos padrões esperados
                if not any(valor_detectado in matches for matches in padroes_esperados.values()):
                    falsos_positivos.append({
                        "id": item['id'],
                        "tipo": result.entity_type,
                        "valor": valor_detectado,
                        "score": result.score,
                        "motivo": "Nome incompleto/palavra solta"
                    })
        
        # Detectar se mascarou números que não são telefones/CPF
        if result.entity_type in ["BR_PHONE", "PHONE_NUMBER"]:
            # Verificar se é número de processo, protocolo, etc
            if re.match(r'\b\d{5}-\d{8}/\d{4}-\d{2}\b', valor_detectado):
                # É processo SEI, está correto
                pass
            elif len(re.findall(r'\d', valor_detectado)) < 10:
                # Muito curto para ser telefone
                falsos_positivos.append({
                    "id": item['id'],
                    "tipo": result.entity_type,
                    "valor": valor_detectado,
                    "score": result.score,
                    "motivo": "Número muito curto para telefone"
                })

print("=" * 80)
print("📊 RESULTADOS DA ANÁLISE")
print("=" * 80)
print()

print(f"Total de padrões esperados (ground truth): {total_ground_truth}")
print(f"Total de entidades detectadas pelo Presidio: {total_detectado}")
print()

# Métricas
verdadeiros_positivos = total_ground_truth - len(falsos_negativos)
precisao = (verdadeiros_positivos / total_detectado * 100) if total_detectado > 0 else 0
recall = (verdadeiros_positivos / total_ground_truth * 100) if total_ground_truth > 0 else 0
f1_score = (2 * precisao * recall / (precisao + recall)) if (precisao + recall) > 0 else 0

print(f"✅ Verdadeiros Positivos: {verdadeiros_positivos}")
print(f"❌ Falsos Negativos: {len(falsos_negativos)}")
print(f"⚠️  Falsos Positivos: {len(falsos_positivos)}")
print()
print(f"📈 Precisão (Precision): {precisao:.2f}%")
print(f"📈 Recall (Sensibilidade): {recall:.2f}%")
print(f"📈 F1-Score: {f1_score:.2f}%")
print()

# Detalhes dos falsos negativos
if falsos_negativos:
    print("=" * 80)
    print("❌ FALSOS NEGATIVOS (deveria detectar mas não detectou)")
    print("=" * 80)
    print()
    
    fn_por_tipo = defaultdict(list)
    for fn in falsos_negativos:
        fn_por_tipo[fn['tipo']].append(fn)
    
    for tipo, items in sorted(fn_por_tipo.items()):
        print(f"  {tipo}: {len(items)} ocorrências")
        for item in items[:3]:  # Mostrar até 3 exemplos
            print(f"    - ID {item['id']}: '{item['valor']}'")
            print(f"      Contexto: ...{item['contexto']}...")
        if len(items) > 3:
            print(f"    ... e mais {len(items)-3}")
        print()

# Detalhes dos falsos positivos
if falsos_positivos:
    print("=" * 80)
    print("⚠️  FALSOS POSITIVOS (detectou mas não deveria)")
    print("=" * 80)
    print()
    
    fp_por_tipo = defaultdict(list)
    for fp in falsos_positivos:
        fp_por_tipo[fp['tipo']].append(fp)
    
    for tipo, items in sorted(fp_por_tipo.items()):
        print(f"  {tipo}: {len(items)} ocorrências")
        for item in items[:5]:  # Mostrar até 5 exemplos
            print(f"    - ID {item['id']}: '{item['valor']}' (score: {item['score']:.2f})")
            print(f"      Motivo: {item['motivo']}")
        if len(items) > 5:
            print(f"    ... e mais {len(items)-5}")
        print()

# Salvar em JSON
relatorio = {
    "metricas": {
        "total_ground_truth": total_ground_truth,
        "total_detectado": total_detectado,
        "verdadeiros_positivos": verdadeiros_positivos,
        "falsos_negativos": len(falsos_negativos),
        "falsos_positivos": len(falsos_positivos),
        "precisao": f"{precisao:.2f}%",
        "recall": f"{recall:.2f}%",
        "f1_score": f"{f1_score:.2f}%"
    },
    "falsos_negativos": falsos_negativos,
    "falsos_positivos": falsos_positivos
}

with open("analise_fp_fn.json", "w", encoding="utf-8") as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)

print("=" * 80)
print("✅ Análise salva em: analise_fp_fn.json")
print("=" * 80)

# Recomendações
if falsos_negativos or falsos_positivos:
    print()
    print("🔧 RECOMENDAÇÕES:")
    print()
    
    if falsos_negativos:
        print("  Para reduzir FALSOS NEGATIVOS:")
        print("  - Reduzir thresholds dos reconhecedores")
        print("  - Adicionar mais padrões de regex")
        print("  - Expandir contextos dos reconhecedores")
        print()
    
    if falsos_positivos:
        print("  Para reduzir FALSOS POSITIVOS:")
        print("  - Aumentar thresholds seletivamente")
        print("  - Adicionar blacklist mais completa")
        print("  - Melhorar validação de contexto")
        print()
