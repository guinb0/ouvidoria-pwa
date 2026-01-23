"""
Teste rápido com um texto simples
"""
from fastapi.testclient import TestClient
import sys
sys.path.insert(0, 'C:\\Users\\User\\Downloads\\ouvidoria-pwa\\presidio-service')

from main import app

client = TestClient(app)

# Teste simples
texto = "Meu CPF é 123.456.789-09 e meu telefone é (11) 99876-5432"

print("Testando API localmente...")
response = client.post("/api/processar", json={"texto": texto})

if response.status_code == 200:
    result = response.json()
    print(f"✅ Sucesso!")
    print(f"Original: {result['textoOriginal']}")
    print(f"Anonimizado: {result['textoTarjado']}")
    print(f"Entidades: {result['dadosOcultados']}")
else:
    print(f"❌ Erro: {response.status_code}")
    print(response.text)
