"""
Debug - Identificar nomes não detectados
"""
import sys
import re
sys.path.insert(0, 'C:\\Users\\User\\Downloads\\ouvidoria-pwa\\presidio-service')

from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from brazilian_recognizers import *

# Ler arquivo
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

# Inicializar
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "pt", "model_name": "pt_core_news_sm"}],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()
registry = RecognizerRegistry()
registry.load_predefined_recognizers(nlp_engine=nlp_engine)
registry.add_recognizer(BrazilNameRecognizer())

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)

# Regex para nomes
name_pattern = r'\b[A-Z][a-z]+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'

print("=" * 80)
print("NOMES NÃO DETECTADOS")
print("=" * 80)
print()

nomes_nao_detectados = []

for item in textos:
    texto = item['texto']
    
    # Encontrar nomes no texto
    names_in_text = re.findall(name_pattern, texto)
    
    if names_in_text:
        # Analisar com Presidio
        results = analyzer.analyze(
            text=texto,
            language="pt",
            entities=["PERSON"],
            score_threshold=0.40
        )
        
        # Verificar quais não foram detectados
        detected = set()
        for r in results:
            detected.add(texto[r.start:r.end])
        
        for name in names_in_text:
            if name not in detected and name not in ' '.join(detected):
                nomes_nao_detectados.append(name)
                print(f"ID {item['id']}: '{name}' NÃO DETECTADO")

print()
print(f"Total de nomes únicos não detectados: {len(set(nomes_nao_detectados))}")
print()
print("Nomes únicos:")
for name in sorted(set(nomes_nao_detectados)):
    print(f"  - {name}")
