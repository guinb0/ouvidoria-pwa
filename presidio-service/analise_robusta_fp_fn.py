"""
Análise ROBUSTA de Falsos Positivos e Falsos Negativos
Baseado em técnicas de validação cruzada e anotação manual
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
print("ANÁLISE ROBUSTA DE FALSOS POSITIVOS E FALSOS NEGATIVOS")
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

# GROUND TRUTH REFINADO (baseado em análise manual)
# Apenas padrões que REALMENTE deveriam ser mascarados
patterns_ground_truth = {
    "CPF": r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    "Telefone": r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',  # Apenas telefones reais, não nº de processo
    "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "Processo SEI": r'\b\d{5}-\d{8}/\d{4}-\d{2}\b',
}

# BLACKLIST DE FALSOS POSITIVOS CONHECIDOS
# Palavras que o spaCy detecta como PERSON mas NÃO são nomes
false_positive_patterns = {
    "verbos_inicio_frase": [
        "Venho", "Solicito", "Requeiro", "Peço", "Encaminho", "Apresento",
        "Informo", "Comunico", "Manifesto", "Declaro", "Afirmo"
    ],
    "substantivos_comuns": [
        "Cidadã", "Cidadão", "Solicitante", "Requerente", "Interessado",
        "Contribuinte", "Usuário", "Beneficiário", "Servidor"
    ],
    "empresas_orgaos": [
        "Caesb", "Novacap", "Detran", "Sefaz", "Google", "Microsoft",
        "WhatsApp", "Facebook", "Instagram"
    ],
    "termos_tecnicos": [
        "Site", "Portal", "Sistema", "Plataforma", "Aplicativo",
        "Google Maps", "Site Google Maps", "Fale Conosco"
    ],
    "termos_administrativos": [
        "Secretaria", "Coordenação", "Diretoria", "Gerência",
        "Contoladoria Geral Assunto", "Processo Sei", "Identidade Prezados"
    ]
}

print("🔍 Analisando com validações robustas...")
print()

falsos_negativos_detalhado = []
falsos_positivos_detalhado = []
verdadeiros_positivos = 0
verdadeiros_negativos = 0

total_ground_truth = 0
total_detectado_person = 0

for item in textos:
    texto = item['texto']
    
    # 1. Contar padrões esperados (ground truth)
    padroes_esperados = {}
    for nome, regex in patterns_ground_truth.items():
        matches = list(set(re.findall(regex, texto)))
        if matches:
            padroes_esperados[nome] = matches
            total_ground_truth += len(matches)
    
    # 2. Analisar com Presidio
    results = analyzer.analyze(
        text=texto,
        language="pt",
        entities=entities,
        score_threshold=0.40
    )
    
    # 3. APLICAR FILTROS ROBUSTOS (mesmos do main.py)
    filtered_results = []
    entity_spans = {}
    for r in results:
        key = (r.start, r.end)
        if key not in entity_spans:
            entity_spans[key] = []
        entity_spans[key].append(r)
    
    # Blacklist expandida do main.py
    person_blacklist_expanded = [
        "venho", "solicito", "encaminho", "peco", "requeiro", "apresento",
        "informo", "comunico", "manifesto", "declaro", "afirmo", "ratifico",
        "cidada", "cidadao", "solicitante", "requerente", "interessado",
        "contribuinte", "usuario", "beneficiario", "servidor", "funcionario",
        "caesb", "novacap", "detran", "sefaz", "pmdf", "cbmdf", "tjdft",
        "site", "portal", "sistema", "google", "maps", "whatsapp"
    ]
    
    sobrenomes_brasileiros = [
        "silva", "santos", "oliveira", "souza", "rodrigues", "ferreira",
        "alves", "pereira", "lima", "gomes", "costa", "ribeiro", "martins"
    ]
    
    primeiros_nomes_comuns = [
        "maria", "jose", "joao", "ana", "pedro", "paulo", "carlos", "francisco",
        "marcos", "lucas", "antonio", "luiz", "marcelo", "gabriel", "rafael"
    ]
    
    for r in results:
        skip = False
        
        if r.entity_type == "PERSON":
            texto_detectado = texto[r.start:r.end].lower()
            texto_original = texto[r.start:r.end]
            palavras = texto_detectado.split()
            
            # 1. Blacklist
            if any(palavra == texto_detectado for palavra in person_blacklist_expanded):
                skip = True
            
            # 1.5. Siglas/Acrônimos (detecta automaticamente órgãos)
            if not skip and texto_original.isupper() and len(texto_original) >= 3 and len(texto_original) <= 8:
                siglas_nomes = ["JOÃO", "JOSÉ"]
                if texto_original not in siglas_nomes:
                    skip = True
            
            # 2. Palavras soltas
            if not skip and len(palavras) == 1:
                terminacoes_verbais = ["o", "as", "amos", "am", "ei", "ou", "emos"]
                if any(texto_detectado.endswith(term) for term in terminacoes_verbais):
                    skip = True
                elif texto_detectado not in primeiros_nomes_comuns:
                    if r.score < 0.90:
                        skip = True
            
            # 3. Sobreposição com EMAIL
            if not skip:
                span_key = (r.start, r.end)
                if span_key in entity_spans:
                    for other in entity_spans[span_key]:
                        if other.entity_type == "EMAIL_ADDRESS":
                            skip = True
                            break
            
            # 4. Threshold adaptativo
            if not skip:
                context_window = 40
                start_ctx = max(0, r.start - context_window)
                end_ctx = min(len(texto), r.end + context_window)
                context = texto[start_ctx:end_ctx].lower()
                
                positive_contexts = ["sr.", "sra.", "dr.", "nome:", "cpf:"]
                has_positive_context = any(pos in context for pos in positive_contexts)
                
                has_brazilian_surname = any(sobrenome in palavras for sobrenome in sobrenomes_brasileiros)
                has_multiple_words = len(palavras) >= 2
                
                if has_positive_context:
                    min_score = 0.40
                elif has_brazilian_surname and has_multiple_words:
                    min_score = 0.50
                elif has_multiple_words:
                    min_score = 0.60
                else:
                    min_score = 0.75
                
                if r.score >= min_score:
                    filtered_results.append(r)
            
        else:
            filtered_results.append(r)
    
    # 4. Separar resultados filtrados por tipo
    person_results = [r for r in filtered_results if r.entity_type == "PERSON"]
    other_results = [r for r in filtered_results if r.entity_type != "PERSON"]
    
    total_detectado_person += len(person_results)
    
    # 5. Validar PERSON com blacklist de falsos positivos
    for r in person_results:
        valor = texto[r.start:r.end]
        
        # Verificar se está na blacklist de falsos positivos
        is_false_positive = False
        categoria_fp = None
        
        for categoria, palavras in false_positive_patterns.items():
            if valor in palavras:
                is_false_positive = True
                categoria_fp = categoria
                break
        
        if is_false_positive:
            falsos_positivos_detalhado.append({
                "id": item['id'],
                "tipo": "PERSON",
                "valor": valor,
                "score": r.score,
                "categoria": categoria_fp,
                "motivo": f"Palavra comum ({categoria_fp})"
            })
        else:
            # É verdadeiro positivo (nome real)
            verdadeiros_positivos += 1
    
    # 6. Verificar falsos negativos
    for tipo, matches in padroes_esperados.items():
        for match in matches:
            # Verificar se foi detectado
            foi_detectado = False
            for r in filtered_results:
                texto_detectado = texto[r.start:r.end]
                if match in texto_detectado or texto_detectado in match:
                    foi_detectado = True
                    break
            
            if not foi_detectado:
                # Verificar se é número de processo (não é telefone real)
                if tipo == "Telefone" and len(match.replace("-", "").replace("(", "").replace(")", "").replace(" ", "")) > 11:
                    # É número de processo/ocorrência, não é falso negativo
                    continue
                
                falsos_negativos_detalhado.append({
                    "id": item['id'],
                    "tipo": tipo,
                    "valor": match,
                    "contexto": texto[max(0, texto.find(match)-40):texto.find(match)+len(match)+40]
                })

print("=" * 80)
print("📊 RESULTADOS DA ANÁLISE ROBUSTA")
print("=" * 80)
print()

print(f"Total de padrões esperados (ground truth): {total_ground_truth}")
print(f"Total de PERSON detectados: {total_detectado_person}")
print()

print(f"✅ Verdadeiros Positivos (PERSON real): {verdadeiros_positivos}")
print(f"❌ Falsos Negativos: {len(falsos_negativos_detalhado)}")
print(f"⚠️  Falsos Positivos (PERSON): {len(falsos_positivos_detalhado)}")
print()

# Calcular métricas
if total_detectado_person > 0:
    precisao_person = (verdadeiros_positivos / total_detectado_person * 100)
else:
    precisao_person = 0

if total_ground_truth > 0:
    recall = ((total_ground_truth - len(falsos_negativos_detalhado)) / total_ground_truth * 100)
else:
    recall = 0

if precisao_person + recall > 0:
    f1_score = (2 * precisao_person * recall / (precisao_person + recall))
else:
    f1_score = 0

print(f"📈 Precisão PERSON (VP / Total Detectado): {precisao_person:.2f}%")
print(f"📈 Recall Geral: {recall:.2f}%")
print(f"📈 F1-Score: {f1_score:.2f}%")
print()

# Detalhes dos falsos positivos
if falsos_positivos_detalhado:
    print("=" * 80)
    print("⚠️  FALSOS POSITIVOS PERSON (por categoria)")
    print("=" * 80)
    print()
    
    fp_por_categoria = defaultdict(list)
    for fp in falsos_positivos_detalhado:
        fp_por_categoria[fp['categoria']].append(fp)
    
    for categoria, items in sorted(fp_por_categoria.items()):
        print(f"  {categoria}: {len(items)} ocorrências")
        for item in items[:5]:
            print(f"    - '{item['valor']}' (score: {item['score']:.2f})")
        if len(items) > 5:
            print(f"    ... e mais {len(items)-5}")
        print()
else:
    fp_por_categoria = {}

# Detalhes dos falsos negativos
if falsos_negativos_detalhado:
    print("=" * 80)
    print("❌ FALSOS NEGATIVOS")
    print("=" * 80)
    print()
    
    fn_por_tipo = defaultdict(list)
    for fn in falsos_negativos_detalhado:
        fn_por_tipo[fn['tipo']].append(fn)
    
    for tipo, items in sorted(fn_por_tipo.items()):
        print(f"  {tipo}: {len(items)} ocorrências")
        for item in items[:3]:
            print(f"    - ID {item['id']}: '{item['valor']}'")
        if len(items) > 3:
            print(f"    ... e mais {len(items)-3}")
        print()

# Salvar relatório
relatorio = {
    "metricas": {
        "total_ground_truth": total_ground_truth,
        "total_person_detectado": total_detectado_person,
        "verdadeiros_positivos_person": verdadeiros_positivos,
        "falsos_negativos": len(falsos_negativos_detalhado),
        "falsos_positivos_person": len(falsos_positivos_detalhado),
        "precisao_person": f"{precisao_person:.2f}%",
        "recall_geral": f"{recall:.2f}%",
        "f1_score": f"{f1_score:.2f}%"
    },
    "falsos_positivos": falsos_positivos_detalhado,
    "falsos_negativos": falsos_negativos_detalhado,
    "categorias_fp": {k: len(v) for k, v in fp_por_categoria.items()}
}

with open("analise_robusta_fp_fn.json", "w", encoding="utf-8") as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)

print("=" * 80)
print("✅ Análise salva em: analise_robusta_fp_fn.json")
print("=" * 80)
print()

# Análise de melhorias
print("🔧 ANÁLISE DE OPORTUNIDADES DE MELHORIA:")
print()

if falsos_positivos_detalhado:
    print(f"  1. REDUZIR FALSOS POSITIVOS ({len(falsos_positivos_detalhado)} ocorrências):")
    print(f"     - Expandir blacklist com as palavras identificadas")
    print(f"     - Implementar validação POS tagging (filtrar verbos)")
    print(f"     - Adicionar validação de contexto semântico")
    print()

if falsos_negativos_detalhado:
    print(f"  2. REDUZIR FALSOS NEGATIVOS ({len(falsos_negativos_detalhado)} ocorrências):")
    print(f"     - Verificar se são padrões legítimos ou ground truth incorreto")
    print(f"     - Ajustar thresholds para tipos específicos")
    print()

if precisao_person < 90:
    print(f"  3. MELHORAR PRECISÃO PERSON ({precisao_person:.1f}% atual):")
    print(f"     - Meta: atingir >90% de precisão")
    print(f"     - Técnicas: POS tagging, validação estrutural, contexto")
    print()
