"""
Debug do reconhecedor de CPF
"""
import re

cpf_texto = "129.180.122-6"

# Padrões do recognizer
pattern1 = r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b"
pattern2 = r"(?<!\d)\d{11}(?!\d)"

match1 = re.search(pattern1, cpf_texto)
match2 = re.search(pattern2, cpf_texto.replace(".", "").replace("-", ""))

print(f"Texto: {cpf_texto}")
print(f"Pattern 1 (com pontos): {pattern1}")
print(f"  Match: {match1.group() if match1 else 'NENHUM'}")
print()
print(f"Pattern 2 (sem pontos): {pattern2}")
print(f"  Match: {match2.group() if match2 else 'NENHUM'}")
print()

# Testar validação de checksum
try:
    from validate_docbr import CPF
    cpf_validator = CPF()
    cpf_limpo = cpf_texto.replace(".", "").replace("-", "")
    print(f"CPF limpo: {cpf_limpo}")
    print(f"Validação: {cpf_validator.validate(cpf_limpo)}")
    print(f"É CPF válido: {cpf_validator.validate(cpf_limpo)}")
except Exception as e:
    print(f"Erro na validação: {e}")
