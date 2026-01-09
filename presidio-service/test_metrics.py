"""
Script de Teste e Avaliação de Métricas - VERSÃO AVANÇADA
Calcula Precisão, Recall e F1-Score com análise por tipo de entidade

Uso:
    python test_metrics.py
"""
import json
from typing import List, Dict, Tuple
from collections import defaultdict
import requests

# Dataset de teste sofisticado com casos complexos e edge cases
TEST_CASES = [
    {
        "nome": "Caso 1: Dados pessoais completos",
        "texto": "Meu nome é João Silva e meu CPF é 123.456.789-00. Meu telefone é (11) 98765-4321.",
        "entidades_esperadas": [
            {"tipo": "PERSON", "texto": "João Silva"},
            {"tipo": "BR_CPF", "texto": "123.456.789-00"},
            {"tipo": "BR_PHONE", "texto": "(11) 98765-4321"},
        ]
    },
    {
        "nome": "Caso 2: Email e documentos",
        "texto": "Email: maria.santos@example.com RG: 12.345.678-9 CEP: 01310-100",
        "entidades_esperadas": [
            {"tipo": "EMAIL_ADDRESS", "texto": "maria.santos@example.com"},
            {"tipo": "BR_RG", "texto": "12.345.678-9"},
            {"tipo": "BR_CEP", "texto": "01310-100"},
        ]
    },
    {
        "nome": "Caso 3: Localização e email",
        "texto": "Resido na Rua das Flores, 123, São Paulo. Contato: jose@gmail.com",
        "entidades_esperadas": [
            {"tipo": "LOCATION", "texto": "Rua das Flores"},
            {"tipo": "LOCATION", "texto": "São Paulo"},
            {"tipo": "EMAIL_ADDRESS", "texto": "jose@gmail.com"},
        ]
    },
    {
        "nome": "Caso 4: Documentos sem formatação",
        "texto": "Documento CPF 98765432100 sem pontuação e telefone 11987654321",
        "entidades_esperadas": [
            {"tipo": "BR_CPF", "texto": "98765432100"},
            {"tipo": "BR_PHONE", "texto": "11987654321"},
        ]
    },
    {
        "nome": "Caso 5: Nome completo e CEP",
        "texto": "Protocolo 2023-001 solicitado por Pedro Oliveira em 15/01/2023 CEP 70040-020",
        "entidades_esperadas": [
            {"tipo": "PERSON", "texto": "Pedro Oliveira"},
            {"tipo": "BR_CEP", "texto": "70040-020"},
        ]
    },
    {
        "nome": "Caso 6: CNPJ e razão social",
        "texto": "Empresa XYZ Ltda CNPJ 12.345.678/0001-90 contato comercial@empresa.com.br",
        "entidades_esperadas": [
            {"tipo": "BR_CNPJ", "texto": "12.345.678/0001-90"},
            {"tipo": "EMAIL_ADDRESS", "texto": "comercial@empresa.com.br"},
        ]
    },
    {
        "nome": "Caso 7: Múltiplas pessoas",
        "texto": "Reunião entre Ana Costa, Carlos Mendes e Beatriz Souza sobre o projeto",
        "entidades_esperadas": [
            {"tipo": "PERSON", "texto": "Ana Costa"},
            {"tipo": "PERSON", "texto": "Carlos Mendes"},
            {"tipo": "PERSON", "texto": "Beatriz Souza"},
        ]
    },
    {
        "nome": "Caso 8: Edge case - Números similares a CPF",
        "texto": "O protocolo 12345678901 não é CPF mas o número 111.222.333-44 é CPF válido",
        "entidades_esperadas": [
            {"tipo": "BR_CPF", "texto": "111.222.333-44"},
        ]
    },
    {
        "nome": "Caso 9: Telefones variados",
        "texto": "Fixo (11) 3456-7890 e celular (21) 99876-5432 para contato urgente",
        "entidades_esperadas": [
            {"tipo": "BR_PHONE", "texto": "(11) 3456-7890"},
            {"tipo": "BR_PHONE", "texto": "(21) 99876-5432"},
        ]
    },
    {
        "nome": "Caso 10: Mix complexo",
        "texto": "Denúncia anônima: Roberto Alves CPF 987.654.321-00 mora em Brasília DF CEP 70000-000 tel 61999887766",
        "entidades_esperadas": [
            {"tipo": "PERSON", "texto": "Roberto Alves"},
            {"tipo": "BR_CPF", "texto": "987.654.321-00"},
            {"tipo": "LOCATION", "texto": "Brasília"},
            {"tipo": "BR_CEP", "texto": "70000-000"},
            {"tipo": "BR_PHONE", "texto": "61999887766"},
        ]
    },
    {
        "nome": "Caso 11: Email institucional e RG",
        "texto": "Servidor público João.Santos@gov.br portador do RG 1234567 lotado na SEJUS",
        "entidades_esperadas": [
            {"tipo": "PERSON", "texto": "João Santos"},
            {"tipo": "EMAIL_ADDRESS", "texto": "João.Santos@gov.br"},
            {"tipo": "BR_RG", "texto": "1234567"},
        ]
    },
    {
        "nome": "Caso 12: Endereço completo",
        "texto": "Reside na Avenida Paulista número 1000 apto 501 São Paulo SP",
        "entidades_esperadas": [
            {"tipo": "LOCATION", "texto": "Avenida Paulista"},
            {"tipo": "LOCATION", "texto": "São Paulo"},
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
    """Testa o Presidio e calcula métricas detalhadas"""
    print("🧪 Iniciando testes avançados do sistema de anonimização...")
    print(f"📡 URL do serviço: {url}/api/processar")
    print(f"📋 Total de casos de teste: {len(TEST_CASES)}\n")
    
    vp_total = 0  # Verdadeiros Positivos
    fp_total = 0  # Falsos Positivos
    fn_total = 0  # Falsos Negativos
    
    # Métricas por tipo de entidade
    metricas_por_tipo = defaultdict(lambda: {"vp": 0, "fp": 0, "fn": 0})
    
    resultados_detalhados = []
    
    for i, caso in enumerate(TEST_CASES, 1):
        print(f"📝 {caso['nome']}")
        print(f"   {caso['texto'][:90]}{'...' if len(caso['texto']) > 90 else ''}")
        
        try:
            response = requests.post(
                f"{url}/api/processar",
                json={"texto": caso["texto"]},
                timeout=10
            )
            response.raise_for_status()
            resultado = response.json()
            
            entidades_detectadas = resultado.get("entidadesEncontradas", [])
            
            # Contar VP, FP, FN por tipo
            tipos_esperados = [e["tipo"] for e in caso["entidades_esperadas"]]
            tipos_detectados = [e["tipo"] for e in entidades_detectadas]
            
            # Criar contadores para cada tipo
            esperados_count = defaultdict(int)
            detectados_count = defaultdict(int)
            
            for tipo in tipos_esperados:
                esperados_count[tipo] += 1
            
            for tipo in tipos_detectados:
                detectados_count[tipo] += 1
            
            # Calcular VP, FP, FN
            vp_caso = 0
            fp_caso = 0
            fn_caso = 0
            
            # Para cada tipo esperado
            for tipo, count_esperado in esperados_count.items():
                count_detectado = detectados_count.get(tipo, 0)
                vp = min(count_esperado, count_detectado)
                fn = max(0, count_esperado - count_detectado)
                
                vp_caso += vp
                fn_caso += fn
                
                metricas_por_tipo[tipo]["vp"] += vp
                metricas_por_tipo[tipo]["fn"] += fn
            
            # Para cada tipo detectado que não era esperado
            for tipo, count_detectado in detectados_count.items():
                count_esperado = esperados_count.get(tipo, 0)
                fp = max(0, count_detectado - count_esperado)
                
                fp_caso += fp
                metricas_por_tipo[tipo]["fp"] += fp
            
            vp_total += vp_caso
            fp_total += fp_caso
            fn_total += fn_caso
            
            status = "✅" if fn_caso == 0 and fp_caso == 0 else "⚠️" if fn_caso > 0 else "🔸"
            print(f"   {status} VP: {vp_caso} | FP: {fp_caso} | FN: {fn_caso} | Detectado: {len(entidades_detectadas)}")
            
            if fp_caso > 0 or fn_caso > 0:
                if fn_caso > 0:
                    print(f"      ⚠️ Não detectado: {fn_caso} entidade(s)")
                if fp_caso > 0:
                    print(f"      🔸 Falso positivo: {fp_caso} entidade(s)")
            
            resultados_detalhados.append({
                "caso": i,
                "nome": caso["nome"],
                "vp": vp_caso,
                "fp": fp_caso,
                "fn": fn_caso,
                "entidades_detectadas": entidades_detectadas
            })
            
        except Exception as e:
            print(f"   ❌ Erro: {str(e)}")
            fn_total += len(caso["entidades_esperadas"])
            for entidade in caso["entidades_esperadas"]:
                metricas_por_tipo[entidade["tipo"]]["fn"] += 1
        
        print()
    
    # Calcular métricas finais
    precisao, recall, f1 = calcular_metricas(vp_total, fp_total, fn_total)
    
    print("=" * 70)
    print("📊 RESULTADOS FINAIS")
    print("=" * 70)
    print(f"Verdadeiros Positivos (VP): {vp_total}")
    print(f"Falsos Positivos (FP):      {fp_total}")
    print(f"Falsos Negativos (FN):      {fn_total}")
    print()
    print(f"🎯 Precisão: {precisao:.2%} ({precisao:.4f})")
    print(f"🎯 Recall:   {recall:.2%} ({recall:.4f})")
    print(f"🎯 F1-Score: {f1:.2%} ({f1:.4f})")
    print("=" * 70)
    
    # Métricas por tipo de entidade
    print("\n📊 MÉTRICAS POR TIPO DE ENTIDADE")
    print("=" * 70)
    
    metricas_detalhadas_por_tipo = {}
    for tipo in sorted(metricas_por_tipo.keys()):
        stats = metricas_por_tipo[tipo]
        p, r, f = calcular_metricas(stats["vp"], stats["fp"], stats["fn"])
        metricas_detalhadas_por_tipo[tipo] = {
            "precisao": p,
            "recall": r,
            "f1_score": f,
            "vp": stats["vp"],
            "fp": stats["fp"],
            "fn": stats["fn"]
        }
        
        print(f"{tipo:20} | P: {p:5.1%} | R: {r:5.1%} | F1: {f:5.1%} | VP:{stats['vp']:2} FP:{stats['fp']:2} FN:{stats['fn']:2}")
    
    print("=" * 70)
    
    # Estimativa de pontuação P1
    p1_score = f1
    print(f"\n📈 Pontuação P1 Estimada: {p1_score:.4f} ({p1_score:.2%})")
    
    if f1 >= 0.95:
        print("🏆 EXCELENTE! Nível competitivo para 1º lugar (F1 ≥ 0.95)")
    elif f1 >= 0.90:
        print("🥈 MUITO BOM! Competitivo para Top 3 (F1 ≥ 0.90)")
    elif f1 >= 0.85:
        print("🥉 BOM! Pode competir, mas melhorias aumentam chances (F1 ≥ 0.85)")
    elif f1 >= 0.80:
        print("⚠️ REGULAR. Precisa melhorias para ser competitivo")
    else:
        print("❌ BAIXO. Necessário otimização urgente")
    
    return {
        "metricas": {
            "precisao": precisao,
            "recall": recall,
            "f1_score": f1,
            "vp": vp_total,
            "fp": fp_total,
            "fn": fn_total,
        },
        "metricas_por_tipo": metricas_detalhadas_por_tipo,
        "resultados_detalhados": resultados_detalhados,
        "p1_estimado": p1_score,
        "total_casos_teste": len(TEST_CASES)
    }


def salvar_resultados(resultados: Dict, arquivo: str = "test_results.json"):
    """Salva resultados em arquivo JSON"""
    with open(arquivo, 'w', encoding='utf-8') as f:
        json.dump(resultados, f, indent=2, ensure_ascii=False)
    print(f"\n💾 Resultados salvos em: {arquivo}")


if __name__ == "__main__":
    print("🚀 Sistema de Avaliação Avançado - Ouvidoria PII Detection")
    print("=" * 70)
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
    
    print("\n✅ Avaliação avançada concluída!")
