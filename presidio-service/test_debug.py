"""
Debug - Testar detecção de nomes e telefones específicos
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
registry.add_recognizer(BrazilPhoneRecognizer())

analyzer = AnalyzerEngine(nlp_engine=nlp_engine, registry=registry)

# Textos problema
textos_teste = [
    "Meus dados: Ruth Helena Franco CPF: 110.100.179-87 Tel. (54)99199-1000",
    "Antonio Costa Controladoria-Geral Tel: 21-1205-1999",
    "Júlio Cesar Alves da Rosa, CPF: 129.180.122-6",
    "Maria Martins Mota Silva, CPF: 210.201.140-24",
    "Dr Joaquim fui orientada",
]

entities = ["PERSON", "BR_CPF", "BR_PHONE", "PHONE_NUMBER"]

print("=" * 80)
print("DEBUG - DETECÇÃO DE NOMES E TELEFONES")
print("=" * 80)
print()

for texto in textos_teste:
    print(f"Texto: {texto}")
    print("-" * 80)
    
    results = analyzer.analyze(
        text=texto,
        language="pt",
        entities=entities,
        score_threshold=0.40
    )
    
    if results:
        for r in results:
            palavra = texto[r.start:r.end]
            print(f"  ✓ {r.entity_type}: '{palavra}' (score: {r.score:.2f})")
    else:
        print("  ❌ Nenhuma entidade detectada")
    
    print()
