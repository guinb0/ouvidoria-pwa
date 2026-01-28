#!/usr/bin/env python3
"""Debug: ver o que o Analyzer retorna ANTES de qualquer filtro"""

import sys
sys.path.insert(0, 'C:/Users/User/Downloads/ouvidoria-pwa/presidio-service')

# Importar engine
from presidio_analyzer import AnalyzerEngine

# Carregar analyzer
print("Carregando analyzer...")
analyzer = AnalyzerEngine()

texto = """
Prezados,

Meu nome é Antonio Costa e trabalho com Júlio Cesar Alves da Rosa.
Também conheço Lúcio Miguel e Antonio Vasconcelos.
A Carolina Alves de Freitas Valle e Edson Henrique da Costa Camargo são colegas.
Lima Tavares também faz parte da equipe.

Conceição Sampaio solicitou.
"""

print("\nAnalisando texto...")
results = analyzer.analyze(text=texto, language='pt')

print(f"\n{'='*80}")
print(f"RESULTADOS BRUTOS DO ANALYZER (Total: {len(results)})")
print(f"{'='*80}\n")

for r in results:
    texto_detectado = texto[r.start:r.end]
    print(f"• {r.entity_type:15} | Score: {r.score:.2f} | '{texto_detectado}'")
