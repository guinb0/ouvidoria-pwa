"""
Script de Teste e Avaliação de Métricas
Calcula Precisão, Recall e F1-Score do sistema de anonimização

Uso:
    python test_metrics.py
"""
import json
from typing import List, Dict, Tuple
import requests

# Dataset de teste com PII anotado
TEST_CASES = [
    {
        "texto": "Meu nome é João Silva e meu CPF é 123.456.789-00. Meu telefone é (11) 98765-4321.",
        "entidades_esperadas": [
            {"tipo": "PERSON", "texto": "João Silva"},
            {"tipo": "BR_CPF", "texto": "123.456.789-00"},
            {"tipo": "BR_PHONE", "texto": "(11) 98765-4321"},
        ]
    },
    {
        "texto": "Email: maria.santos@example.com RG: 12.345.678-9 CEP: 01310-100",
        "entidades_esperadas": [
            {"tipo": "EMAIL_ADDRESS", "texto": "maria.santos@example.com"},
            {"tipo": "BR_RG", "texto": "12.345.678-9"},
            {"tipo": "BR_CEP", "texto": "01310-100"},
        ]
    },
    {
        "texto": "Resido na Rua das Flores, 123, São Paulo. Contato: jose@gmail.com",
        "entidades_esperadas": [
            {"tipo": "LOCATION", "texto": "Rua das Flores"},
            {"tipo": "LOCATION", "texto": "São Paulo"},
            {"tipo": "EMAIL_ADDRESS", "texto": "jose@gmail.com"},
        ]
    },
    {
        "texto": "Documento CPF 98765432100 sem pontuação e telefone 11987654321",
        "entidades_esperadas": [
            {"tipo": "BR_CPF", "texto": "98765432100"},
            {"tipo": "BR_PHONE", "texto": "11987654321"},
        ]
    },
    {
        "texto": "Protocolo 2023-001 solicitado por Pedro Oliveira em 15/01/2023 CEP 70040-020",
        "entidades_esperadas": [
            {"tipo": "PERSON", "texto": "Pedro Oliveira"},
            {"tipo": "BR_CEP", "texto": "70040-020"},
        ]
    },
]


def calcular_metricas(vp: int, fp: int, fn: int) -> Tuple[float, float, float]:
    """Calcula Precisão, Recall e F1-Score"""
    precisao = vp / (vp + fp) if (vp + fp) > 0 else 0
    recall = vp / (vp + fn) if (vp + fn) > 0 else 0
    f1 = 2 * (precisao * recall) / (precisao + recall) if (precisao + recall) > 0 else 0
    return precisao, recall, f1


def testar_presidio(url: str = "http://localhost:8000") -> Dict:
    """Testa o Presidio e calcula métricas"""
    print("🧪 Iniciando testes do sistema de anonimização...")
    print(f"📡 URL do serviço: {url}/api/processar\n")
    
    vp_total = 0  # Verdadeiros Positivos
    fp_total = 0  # Falsos Positivos
    fn_total = 0  # Falsos Negativos
    
    resultados_detalhados = []
    
    for i, caso in enumerate(TEST_CASES, 1):
        print(f"📝 Teste {i}/{len(TEST_CASES)}")
        print(f"Texto: {caso['texto'][:80]}...")
        
        try:
            response = requests.post(
                f"{url}/api/processar",
                json={"texto": caso["texto"]},
                timeout=10
            )
            response.raise_for_status()
            resultado = response.json()
            
            entidades_detectadas = resultado.get("entidadesEncontradas", [])
            
            # Contar VP, FP, FN
            tipos_esperados = [e["tipo"] for e in caso["entidades_esperadas"]]
            tipos_detectados = [e["tipo"] for e in entidades_detectadas]
            
            # Verdadeiros Positivos: detectados corretamente
            vp = len([t for t in tipos_detectados if t in tipos_esperados])
            
            # Falsos Positivos: detectados mas não esperados
            fp = len([t for t in tipos_detectados if t not in tipos_esperados])
            
            # Falsos Negativos: esperados mas não detectados
            fn = len([t for t in tipos_esperados if t not in tipos_detectados])
            
            vp_total += vp
            fp_total += fp
            fn_total += fn
            
            print(f"  ✅ VP: {vp} | ❌ FP: {fp} | ⚠️ FN: {fn}")
            print(f"  Detectado: {len(entidades_detectadas)} entidades")
            
            resultados_detalhados.append({
                "caso": i,
                "vp": vp,
                "fp": fp,
                "fn": fn,
                "entidades_detectadas": entidades_detectadas
            })
            
        except Exception as e:
            print(f"  ❌ Erro: {str(e)}")
            fn_total += len(caso["entidades_esperadas"])
        
        print()
    
    # Calcular métricas finais
    precisao, recall, f1 = calcular_metricas(vp_total, fp_total, fn_total)
    
    print("=" * 60)
    print("📊 RESULTADOS FINAIS")
    print("=" * 60)
    print(f"Verdadeiros Positivos (VP): {vp_total}")
    print(f"Falsos Positivos (FP):      {fp_total}")
    print(f"Falsos Negativos (FN):      {fn_total}")
    print()
    print(f"🎯 Precisão: {precisao:.2%} ({precisao:.4f})")
    print(f"🎯 Recall:   {recall:.2%} ({recall:.4f})")
    print(f"🎯 F1-Score: {f1:.2%} ({f1:.4f})")
    print("=" * 60)
    
    # Estimativa de pontuação P1
    p1_score = f1
    print(f"\n📈 Pontuação P1 Estimada: {p1_score:.2f}/1.0")
    
    if f1 >= 0.90:
        print("🏆 Excelente! Alta chance de premiação (Top 3)")
    elif f1 >= 0.85:
        print("✅ Muito bom! Competitivo para premiação")
    elif f1 >= 0.80:
        print("⚠️ Bom, mas pode melhorar")
    else:
        print("❌ Precisa de melhorias para ser competitivo")
    
    return {
        "metricas": {
            "precisao": precisao,
            "recall": recall,
            "f1_score": f1,
            "vp": vp_total,
            "fp": fp_total,
            "fn": fn_total,
        },
        "resultados_detalhados": resultados_detalhados,
        "p1_estimado": p1_score
    }


def salvar_resultados(resultados: Dict, arquivo: str = "test_results.json"):
    """Salva resultados em arquivo JSON"""
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Resultados salvos em: {arquivo}")


if __name__ == "__main__":
    print("🚀 Sistema de Avaliação - Ouvidoria PII Detection")
    print("=" * 60)
    print()
    
    # Verificar se serviço está rodando
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code == 200:
            print("✅ Presidio Service está rodando\n")
        else:
            print("⚠️ Presidio Service respondeu com erro\n")
    except Exception:
        print("❌ Presidio Service não está rodando!")
        print("Execute: python main.py\n")
        exit(1)
    
    # Executar testes
    resultados = testar_presidio()
    
    # Salvar resultados
    salvar_resultados(resultados)
    
    print("\n✅ Avaliação concluída!")
