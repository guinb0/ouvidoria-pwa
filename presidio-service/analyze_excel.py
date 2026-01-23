"""
Análise da amostra oficial e-SIC para otimizar reconhecedores
"""
import pandas as pd
import re
import json
from collections import Counter, defaultdict

# Ler arquivo Excel
df = pd.read_excel("../AMOSTRA_e-SIC.xlsx")

print("=" * 80)
print("ANÁLISE DA AMOSTRA OFICIAL e-SIC")
print("=" * 80)
print()

# Informações básicas
print(f"📊 Total de registros: {len(df)}")
print(f"📊 Total de colunas: {len(df.columns)}")
print()

print("Colunas disponíveis:")
for i, col in enumerate(df.columns, 1):
    print(f"  {i}. {col}")
print()

# Se houver coluna de texto/manifestação
texto_cols = [col for col in df.columns if any(
    keyword in col.lower() 
    for keyword in ['texto', 'descri', 'manifest', 'solicit', 'mensag', 'conteudo']
)]

print(f"🔍 Colunas de texto identificadas: {texto_cols}")
print()

if texto_cols:
    # Analisar primeira coluna de texto
    col_texto = texto_cols[0]
    print(f"📝 Analisando coluna: '{col_texto}'")
    print()
    
    # Remover valores nulos
    textos = df[col_texto].dropna().astype(str).tolist()
    print(f"Total de textos válidos: {len(textos)}")
    print()
    
    # Estatísticas de tamanho
    tamanhos = [len(t) for t in textos]
    print(f"Tamanho médio: {sum(tamanhos)/len(tamanhos):.0f} caracteres")
    print(f"Tamanho mínimo: {min(tamanhos)} caracteres")
    print(f"Tamanho máximo: {max(tamanhos)} caracteres")
    print()
    
    # Análise de padrões (amostra dos primeiros 100 registros)
    print("=" * 80)
    print("🔍 ANÁLISE DE PADRÕES (primeiros 100 registros)")
    print("=" * 80)
    print()
    
    amostra = textos[:100]
    
    # Padrões a detectar
    patterns = {
        "CPF": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
        "Telefone": r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}",
        "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "CEP": r"\b\d{5}-?\d{3}\b",
        "Data": r"\b\d{2}[/-]\d{2}[/-]\d{4}\b",
        "Placa": r"\b[A-Z]{3}-?\d[A-Z0-9]\d{2}\b",
        "IP": r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
        "Números (possíveis protocolos)": r"\b\d{6,}\b",
    }
    
    deteccoes = defaultdict(list)
    
    for texto in amostra:
        for nome, pattern in patterns.items():
            matches = re.findall(pattern, texto)
            if matches:
                deteccoes[nome].extend(matches)
    
    print("Padrões encontrados:")
    for nome, matches in deteccoes.items():
        unique = set(matches)
        print(f"\n  {nome}: {len(matches)} ocorrências ({len(unique)} únicas)")
        if len(unique) <= 10:
            for match in list(unique)[:5]:
                print(f"    - {match}")
        else:
            for match in list(unique)[:3]:
                print(f"    - {match}")
            print(f"    ... (+{len(unique)-3} mais)")
    
    print()
    print("=" * 80)
    print("📋 AMOSTRAS DE TEXTOS")
    print("=" * 80)
    print()
    
    # Mostrar 5 primeiras manifestações
    for i, texto in enumerate(textos[:5], 1):
        print(f"Texto {i}:")
        print("-" * 80)
        # Limitar a 500 caracteres
        if len(texto) > 500:
            print(texto[:500] + "...")
        else:
            print(texto)
        print()
    
    # Salvar amostra para análise manual
    with open("amostra_textos.json", "w", encoding="utf-8") as f:
        json.dump({
            "total_registros": len(df),
            "colunas": list(df.columns),
            "coluna_analisada": col_texto,
            "total_textos": len(textos),
            "padroes_detectados": {k: len(v) for k, v in deteccoes.items()},
            "amostras": textos[:20]  # Primeiros 20 textos
        }, f, ensure_ascii=False, indent=2)
    
    print("=" * 80)
    print("✅ Análise salva em: amostra_textos.json")
    print("=" * 80)

else:
    print("❌ Nenhuma coluna de texto encontrada")
    print()
    print("Primeiras 5 linhas do DataFrame:")
    print(df.head())
