"""
Teste com amostra completa - análise detalhada de todos os nomes encontrados
"""
import requests
import json

# Carregar arquivo de amostra
with open("../AMOSTRA_e-SIC.txt", "r", encoding="utf-8") as f:
    texto = f.read()

print("Processando amostra completa...")
print(f"Tamanho do texto: {len(texto)} caracteres")
print()

# Enviar para API
url = "http://localhost:8000/api/processar"
response = requests.post(
    url,
    json={"texto": texto, "language": "pt"}
)

if response.status_code != 200:
    print(f"❌ Erro na API: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
print(f"DEBUG: Resposta da API: {list(data.keys())}")

# A chave pode ser "entities" ou "entidades_detectadas"
if "entidades_detectadas" in data:
    entidades = data["entidades_detectadas"]
elif "entities" in data:
    entidades = data["entities"]
else:
    print(f"❌ Chave não encontrada. Resposta completa: {data}")
    exit(1)

# Contar por tipo
tipos_count = {}
for ent in entidades:
    tipo = ent["tipo"]
    tipos_count[tipo] = tipos_count.get(tipo, 0) + 1

# Filtrar apenas PERSON
persons = [e for e in entidades if e["tipo"] == "PERSON"]

print("=" * 60)
print("RESULTADO DA AMOSTRA COMPLETA")
print("=" * 60)
print(f"Total de entidades detectadas: {len(entidades)}")
print()

print("Distribuição por tipo:")
for tipo, count in sorted(tipos_count.items(), key=lambda x: x[1], reverse=True):
    print(f"  {tipo}: {count}")
print()

print("=" * 60)
print(f"NOMES (PERSON) DETECTADOS: {len(persons)}")
print("=" * 60)

# Mostrar todos os nomes com contexto
for i, person in enumerate(persons, 1):
    texto_original = person["texto_original"]
    start = person["start"]
    end = person["end"]
    
    # Pegar contexto (40 chars antes e depois)
    context_start = max(0, start - 40)
    context_end = min(len(texto), end + 40)
    context = texto[context_start:context_end]
    
    # Limpar quebras de linha para exibição
    context_clean = " ".join(context.split())
    
    print(f"\n{i:2d}. [{texto_original}]")
    print(f"    Contexto: ...{context_clean}...")

print("\n" + "=" * 60)
print("NOMES ESPERADOS NA AMOSTRA (42 nomes reais):")
print("=" * 60)

nomes_esperados = [
    "Maria Martins Mota Silva", "Joaquim", "Ruth Helena Franco", "Ruth",
    "Athos Bulsão", "Rafael", "Jorge Luiz Silva Costa", "Jorge Luiz",
    "João Campos Cruz", "Márcio", "Márcio Dias", "Ana Paula Duarte",
    "Fátima Lima", "Pedro Henrique Soares", "Thiago Conceição",
    "Juliana Ferreira", "Roberto Santos", "Carla Mendes", "Lucas Oliveira",
    "Beatriz Costa", "Fernando Almeida", "Patrícia Rodrigues", "Gabriel Lima",
    "Mariana Souza", "Ricardo Pereira", "Amanda Silva", "Felipe Martins",
    "Larissa Gomes", "Bruno Fernandes", "Camila Ribeiro", "Diego Castro",
    "Isabela Nascimento", "Leonardo Barros", "Natália Cardoso", "Rodrigo Araújo",
    "Sophia Pinto", "Gustavo Moreira", "Carolina Freitas", "Vinícius Dias",
    "Letícia Cavalcanti", "Henrique Monteiro", "João Ribeiro"
]

print(f"\nTotal esperado: {len(nomes_esperados)}")
print(f"Total detectado: {len(persons)}")
print(f"Recall aproximado: {len(persons)/len(nomes_esperados)*100:.1f}%")

# Verificar falsos positivos conhecidos
print("\n" + "=" * 60)
print("VERIFICANDO FALSOS POSITIVOS CONHECIDOS:")
print("=" * 60)

falsos_positivos_conhecidos = {
    "Olá": 0,
    "Fósforo Total": 0,
    "Nitrogênio Total": 0,
    "Athos Bulsão": 0,
    "ER ES": 0,
    "Escola de Políticas Públicas": 0,
    "Contrato": 0
}

for person in persons:
    nome = person["texto_original"]
    for fp_key in falsos_positivos_conhecidos.keys():
        if fp_key.lower() in nome.lower():
            falsos_positivos_conhecidos[fp_key] += 1

falsos_encontrados = sum(falsos_positivos_conhecidos.values())

if falsos_encontrados > 0:
    print("❌ Falsos positivos encontrados:")
    for fp, count in falsos_positivos_conhecidos.items():
        if count > 0:
            print(f"  - {fp} ({count} ocorrências)")
else:
    print("✅ Nenhum falso positivo conhecido detectado!")

print("\n" + "=" * 60)
print("RESUMO FINAL")
print("=" * 60)
print(f"Precisão estimada: {(len(persons) - falsos_encontrados) / len(persons) * 100 if len(persons) > 0 else 0:.1f}%")
print(f"Total PERSON detectados: {len(persons)}")
print(f"Falsos positivos: {falsos_encontrados}")
print(f"Nomes verdadeiros: {len(persons) - falsos_encontrados}")
