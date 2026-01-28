#!/usr/bin/env python3
"""Teste RAW do spaCy para ver o que ele detecta ANTES dos filtros"""

import requests

# Texto com nomes que não estão sendo detectados
texto_teste = """
Prezados,

Meu nome é Antonio Costa e trabalho com Júlio Cesar Alves da Rosa.
Também conheço Lúcio Miguel e Antonio Vasconcelos.
A Carolina Alves de Freitas Valle e Edson Henrique da Costa Camargo são colegas.
Lima Tavares também faz parte da equipe.

Gostaria de saber mais informações.
Conceição Sampaio solicitou acesso.
Me chamo Thiago e preciso de ajuda.
Pablo Souza Ramos é o professor.

Atenciosamente,
Teste
"""

# POST para API
response = requests.post(
    'http://localhost:8000/api/processar',
    json={'texto': texto_teste}
)

if response.status_code == 200:
    resultado = response.json()
    
    print("=" * 80)
    print("ENTIDADES DETECTADAS PELO SPACY (antes de filtros):")
    print("=" * 80)
    
    # Agrupar por tipo
    by_type = {}
    for ent in resultado.get('entidades', []):
        tipo = ent['tipo']
        if tipo not in by_type:
            by_type[tipo] = []
        
        # Extrair texto usando índices
        inicio = ent['inicio']
        fim = ent['fim']
        texto_ent = texto_teste[inicio:fim]
        by_type[tipo].append(texto_ent)
    
    for tipo, textos in sorted(by_type.items()):
        print(f"\n{tipo} ({len(textos)}):")
        for t in textos:
            print(f"  • {t}")
    
    print("\n" + "=" * 80)
    print(f"Total: {len(resultado.get('entidades', []))} entidades")
else:
    print(f"❌ Erro: {response.status_code}")
    print(response.text)
