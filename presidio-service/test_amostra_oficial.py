"""
Teste com amostra oficial e-SIC e cálculo de precisão
"""
import pandas as pd
import requests
import json
import re
from collections import defaultdict

# Configuração
API_URL = "http://localhost:8000/api/processar"

# Ler arquivo Excel
print("=" * 80)
print("TESTE COM AMOSTRA OFICIAL e-SIC")
print("=" * 80)
print()

df = pd.read_excel("../AMOSTRA_e-SIC.xlsx")
textos = df["Texto Mascarado"].dropna().astype(str).tolist()

print(f"📊 Total de textos: {len(textos)}")
print()

# Verificar se API está ativa
try:
    response = requests.get("http://localhost:8000/api/health", timeout=5)
    if response.status_code != 200:
        print("❌ API não está respondendo. Execute: python main.py")
        exit(1)
    print("✅ API conectada")
except:
    print("❌ API não está acessível na porta 8000")
    print("   Inicie o serviço: python main.py")
    exit(1)

print()
print("🔍 Processando todos os textos...")
print()

# Processar todos os textos
resultados = []
padroes_nao_detectados = defaultdict(int)
total_padroes_esperados = 0

# Padrões que DEVEM ser detectados
patterns_check = {
    "CPF": r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b",
    "Telefone": r"\(?\d{2}\)?\s?\d{4,5}-?\d{4}",
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
    "CEP": r"\b\d{5}-?\d{3}\b",
    "Processo/Protocolo": r"\b\d{5}-\d{8}/\d{4}-\d{2}\b",
}

for i, texto in enumerate(textos, 1):
    # Analisar padrões no texto original
    padroes_no_texto = {}
    for nome_padrao, regex in patterns_check.items():
        matches = re.findall(regex, texto)
        if matches:
            padroes_no_texto[nome_padrao] = matches
            total_padroes_esperados += len(matches)
    
    # Processar com API
    try:
        response = requests.post(API_URL, json={"texto": texto, "language": "pt"}, timeout=30)
        
        if response.status_code == 200:
            resultado = response.json()
            
            # Verificar se todos os padrões foram detectados
            texto_anonimizado = resultado["textoTarjado"]
            
            for nome_padrao, matches_originais in padroes_no_texto.items():
                for match in matches_originais:
                    # Verificar se o padrão ainda aparece no texto anonimizado
                    if match in texto_anonimizado:
                        padroes_nao_detectados[nome_padrao] += 1
            
            resultados.append({
                "id": i,
                "texto_original": texto[:100] + "..." if len(texto) > 100 else texto,
                "total_entidades": resultado["dadosOcultados"],
                "padroes_originais": padroes_no_texto,
                "sucesso": True
            })
            
            if i % 10 == 0:
                print(f"  Processados: {i}/{len(textos)} ({i/len(textos)*100:.1f}%)")
        else:
            resultados.append({
                "id": i,
                "erro": f"Status {response.status_code}",
                "sucesso": False
            })
    except Exception as e:
        resultados.append({
            "id": i,
            "erro": str(e),
            "sucesso": False
        })

print()
print("=" * 80)
print("📊 RESULTADOS DA ANÁLISE")
print("=" * 80)
print()

# Calcular estatísticas
sucessos = [r for r in resultados if r.get("sucesso")]
falhas = [r for r in resultados if not r.get("sucesso")]

print(f"✅ Processados com sucesso: {len(sucessos)}/{len(textos)} ({len(sucessos)/len(textos)*100:.1f}%)")
print(f"❌ Falhas: {len(falhas)}")
print()

# Estatísticas de detecção
total_entidades_detectadas = sum(r.get("total_entidades", 0) for r in sucessos)
print(f"🔍 Total de entidades detectadas: {total_entidades_detectadas}")
print()

# Calcular precisão (padrões que NÃO foram mascarados = falsos negativos)
total_nao_detectados = sum(padroes_nao_detectados.values())
taxa_deteccao = ((total_padroes_esperados - total_nao_detectados) / total_padroes_esperados * 100) if total_padroes_esperados > 0 else 100

print("=" * 80)
print("🎯 ANÁLISE DE PRECISÃO")
print("=" * 80)
print()
print(f"Total de padrões sensíveis encontrados: {total_padroes_esperados}")
print(f"Padrões corretamente mascarados: {total_padroes_esperados - total_nao_detectados}")
print(f"Padrões NÃO mascarados (falso negativo): {total_nao_detectados}")
print()
print(f"📈 TAXA DE DETECÇÃO: {taxa_deteccao:.2f}%")
print()

if padroes_nao_detectados:
    print("Padrões não detectados por tipo:")
    for nome, count in sorted(padroes_nao_detectados.items(), key=lambda x: x[1], reverse=True):
        print(f"  ❌ {nome}: {count} ocorrências")
    print()

# Distribuição de entidades detectadas
tipo_entidades = defaultdict(int)
for r in sucessos:
    # Processar novamente para obter tipos (já temos o resultado)
    pass

# Exemplos de textos processados
print("=" * 80)
print("📋 EXEMPLOS DE PROCESSAMENTO")
print("=" * 80)
print()

for i, resultado in enumerate(resultados[:3], 1):
    if resultado.get("sucesso"):
        print(f"Exemplo {i}:")
        print(f"  Original: {resultado['texto_original']}")
        print(f"  Entidades detectadas: {resultado['total_entidades']}")
        if resultado['padroes_originais']:
            print(f"  Padrões no texto: {', '.join(resultado['padroes_originais'].keys())}")
        print()

# Salvar relatório
relatorio = {
    "total_textos": len(textos),
    "processados_com_sucesso": len(sucessos),
    "taxa_sucesso": f"{len(sucessos)/len(textos)*100:.2f}%",
    "total_entidades_detectadas": total_entidades_detectadas,
    "total_padroes_esperados": total_padroes_esperados,
    "padroes_nao_detectados": dict(padroes_nao_detectados),
    "taxa_deteccao": f"{taxa_deteccao:.2f}%",
    "precisao_objetivo": "98.00%",
    "gap": f"{98.00 - taxa_deteccao:.2f}%",
}

with open("relatorio_amostra_oficial.json", "w", encoding="utf-8") as f:
    json.dump(relatorio, f, ensure_ascii=False, indent=2)

print("=" * 80)
print(f"✅ Relatório salvo em: relatorio_amostra_oficial.json")
print("=" * 80)
print()

# Análise de gaps
if taxa_deteccao < 98:
    gap = 98 - taxa_deteccao
    print("⚠️  ANÁLISE DE GAPS")
    print("=" * 80)
    print(f"Precisão atual: {taxa_deteccao:.2f}%")
    print(f"Objetivo: 98.00%")
    print(f"Gap: {gap:.2f}%")
    print()
    print("🔧 RECOMENDAÇÕES PARA ATINGIR 98%:")
    print()
    
    if padroes_nao_detectados.get("Processo/Protocolo", 0) > 0:
        print("  1. Melhorar reconhecedor de números de processo SEI")
        print("     - Padrão: 00015-00568900/2016-56")
        print()
    
    if padroes_nao_detectados.get("CPF", 0) > 0:
        print("  2. Ajustar thresholds do reconhecedor de CPF")
        print("     - Reduzir score mínimo de 0.95 para 0.85")
        print()
    
    if padroes_nao_detectados.get("Telefone", 0) > 0:
        print("  3. Melhorar regex de telefones brasileiros")
        print("     - Adicionar variações sem parênteses")
        print()
    
    if padroes_nao_detectados.get("CEP", 0) > 0:
        print("  4. Ajustar reconhecedor de CEP")
        print("     - CEPs sem hífen (8 dígitos seguidos)")
        print()
else:
    print("🎉 OBJETIVO ATINGIDO! Precisão >= 98%")
    print()
