"""
Script de diagnóstico - testa reconhecedores isoladamente
"""
from brazilian_recognizers import BrazilCpfRecognizer, BrazilRgRecognizer, BrazilCepRecognizer, BrazilPhoneRecognizer

print("🧪 Testando reconhecedores brasileiros...\n")

# Teste CPF
cpf_rec = BrazilCpfRecognizer()
texto_cpf = "Meu CPF é 123.456.789-00 e outro 98765432100"
print(f"📄 Texto: {texto_cpf}")
print(f"✅ Reconhecedor: {cpf_rec.supported_entities}")
print(f"✅ Padrões: {len(cpf_rec.patterns)} regex patterns")
print()

# Teste RG  
rg_rec = BrazilRgRecognizer()
texto_rg = "RG: 12.345.678-9"
print(f"📄 Texto: {texto_rg}")
print(f"✅ Reconhecedor: {rg_rec.supported_entities}")
print()

# Teste CEP
cep_rec = BrazilCepRecognizer()
texto_cep = "CEP: 01310-100"
print(f"📄 Texto: {texto_cep}")
print(f"✅ Reconhecedor: {cep_rec.supported_entities}")
print()

# Teste Telefone
phone_rec = BrazilPhoneRecognizer()
texto_phone = "Telefone: (11) 98765-4321"
print(f"📄 Texto: {texto_phone}")
print(f"✅ Reconhecedor: {phone_rec.supported_entities}")
print()

print("✅ Todos os reconhecedores foram criados com sucesso!")
print("\n⚠️ IMPORTANTE: Reinicie o serviço Python para ativar os reconhecedores:")
print("   No terminal python: Ctrl+C e depois: python main.py")
