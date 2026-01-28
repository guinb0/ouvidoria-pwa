"""
Debug - Identificar exatamente quais telefones não estão sendo detectados
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

# Parsear textos
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

# Inicializar Presidio
configuration = {
    "nlp_engine_name": "spacy",
    "models": [{"lang_code": "pt", "model_name": "pt_core_news_sm"}],
}

provider = NlpEngineProvider(nlp_configuration=configuration)
nlp_engine = provider.create_engine()
registry = RecognizerRegistry()
registry.load_predefined_recognizers(nlp_engine=nlp_engine)

registry.add_recognizer(BrazilPhoneRecognizer())
registry.add_recognizer(BrazilGenericPhoneRecognizer())

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)

# Regex para detectar telefones
phone_pattern = r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}'

print("=" * 80)
print("TELEFONES NÃO DETECTADOS")
print("=" * 80)
print()

for item in textos:
    texto = item['texto']
    
    # Encontrar telefones no texto
    phones_in_text = re.findall(phone_pattern, texto)
    
    if phones_in_text:
        # Analisar com Presidio
        results = analyzer.analyze(
            text=texto,
            language="pt",
            entities=["BR_PHONE", "PHONE_NUMBER"],
            score_threshold=0.40
        )
        
        # Verificar quais não foram detectados
        detected_phones = [texto[r.start:r.end] for r in results if r.entity_type in ["BR_PHONE", "PHONE_NUMBER"]]
        
        for phone in phones_in_text:
            if phone not in ' '.join(detected_phones):
                print(f"ID {item['id']}: '{phone}' NÃO DETECTADO")
                # Contexto
                idx = texto.find(phone)
                context_start = max(0, idx - 50)
                context_end = min(len(texto), idx + len(phone) + 50)
                print(f"  Contexto: ...{texto[context_start:context_end]}...")
                print()
