#!/usr/bin/env python3
"""Debug do NameValidator para entender porque nomes não são detectados"""

from validators import NameValidator

validator = NameValidator()

# Nomes que NÃO estão sendo detectados
nomes_faltando = [
    "Júlio Cesar Alves da Rosa",
    "Antonio Costa",
    "Lúcio Miguel",
    "Antonio Vasconcelos",
    "Carolina Alves de Freitas Valle",
    "Edson Henrique da Costa Camargo",
    "Lima Tavares"
]

# Falsos positivos que NÃO deveriam ser detectados
falsos_positivos = [
    "Grata Meu nome",
    "Prezados Senhores",
    "Olá",
    "Me chamo Thiago",
    "Grata Conceição Sampaio",
    "do professor Pablo Souza Ramos",
    "Instituto Brasileiro de Ensino",
    "Escola de Políticas Públicas e Governo",
    "Contrato"
]

print("=" * 80)
print("TESTANDO NOMES QUE DEVERIAM SER VÁLIDOS:")
print("=" * 80)
for nome in nomes_faltando:
    resultado = validator.is_valid_name(nome)
    print(f"{'✅' if resultado else '❌'} {nome}: {resultado}")

print("\n" + "=" * 80)
print("TESTANDO FALSOS POSITIVOS QUE DEVERIAM SER REJEITADOS:")
print("=" * 80)
for frase in falsos_positivos:
    resultado = validator.is_valid_name(frase)
    print(f"{'❌' if resultado else '✅'} {frase}: {resultado}")
