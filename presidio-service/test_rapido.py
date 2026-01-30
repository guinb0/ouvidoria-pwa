import requests
import json

# Ler arquivo
with open('../AMOSTRA_e-SIC.txt', encoding='utf-8') as f:
    texto = f.read()

# Processar
print("Processando...")
r = requests.post('http://localhost:8000/api/processar', json={'texto': texto})
result = r.json()

# Contar entidades
total = len(result['entidadesEncontradas'])
persons = [e for e in result['entidadesEncontradas'] if e['tipo'] == 'PERSON']

print(f"\n{'='*60}")
print(f"RESULTADO DO TESTE")
print(f"{'='*60}")
print(f"Total de entidades detectadas: {total}")
print(f"Entidades PERSON: {len(persons)}")
print(f"\n{'='*60}")
print(f"PRIMEIRAS 50 DETECÇÕES DE PERSON:")
print(f"{'='*60}")

for i, e in enumerate(persons[:50], 1):
    texto_detectado = texto[e['inicio']:e['fim']]
    # Normalizar quebras de linha para exibição
    texto_display = ' '.join(texto_detectado.split())
    print(f"{i:2}. {texto_display}")

# Verificar se nomes problemáticos ainda aparecem
print(f"\n{'='*60}")
print(f"VERIFICANDO FALSOS POSITIVOS:")
print(f"{'='*60}")

falsos_positivos_esperados = [
    "Olá", "ID", "Texto", "Gestão", "Governança", "Empenho", "Emenda",
    "Inciso", "Validador", "Juvenil", "Superior", "Box", "Advogados",
    "Coliformes", "Fósforo", "Nitrogênio", "Oxigênio", "Sólidos"
]

encontrados = []
for fp in falsos_positivos_esperados:
    for e in persons:
        texto_detectado = texto[e['inicio']:e['fim']]
        if fp.lower() in texto_detectado.lower():
            encontrados.append(texto_detectado)
            
if encontrados:
    print(f"⚠️  Ainda detectando {len(encontrados)} falsos positivos:")
    for fp in set(encontrados):
        print(f"  - {fp}")
else:
    print("✅ Nenhum falso positivo conhecido detectado!")

print(f"\n{'='*60}")
print(f"ESTATÍSTICAS:")
print(f"{'='*60}")
print(f"Redução de entidades PERSON: {103 - len(persons)} (antes: 103)")
print(f"Taxa de melhoria: {((103 - len(persons)) / 103 * 100):.1f}%")
