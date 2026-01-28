"""
Teste dos validadores robustos com textos reais da ouvidoria
"""
import requests
import json

API_URL = "http://localhost:8000/api/processar"

# Texto 1: Termo de Cooperação
texto1 = """Venho solicitar acesso externo ao processo nº 00256-25631478/2022-34 referente ao Termo de Acordo de Cooperação 25/2022 - AC 25/2022 firmado entre a Secretaria de Estado de Obras e Infraestrutura – SO/DF e a Sistema de Cooperativas Financeiras do Brasil - SICOOB. Segue anexo procuração em meu nome para representar a SICOOB junto à SO/DF, e Termo de Acordo de Concordância. Segue também cópia da CNH digital e comprovante de endereço"""

# Texto 2: Questionário IA e Letramento Digital
texto2 = """Inteligência Artificial e Letramento Digital no Setor Público

Prezado(a) servidor(a),

Este questionário tem como objetivo mapear as percepções sobre habilidades relacionadas ao letramento digital e ao uso de Inteligência Artificial Generativa no setor público. Dividido em três seções – Perfil Demográfico e Profissional, Letramento Digital e Inteligência Artificial Generativa – o estudo oferece insights valiosos para que governos identifiquem desafios e oportunidades na busca por inovação e transformação digital.

Os benefícios são significativos, pois os participantes podem identificar suas necessidades de capacitação, enquanto os governos utilizam os resultados para mapear lacunas e desenvolver estratégias mais eficazes para promover a inclusão digital, superando os obstáculos associados à adoção de novas tecnologias.

Solicita-se, portanto, ampla divulgação nos órgãos do Governo do Distrito Federal, a fim de garantir resultados robustos e relevantes.

O tempo estimado para responder é de 5 a 10 minutos. Todas as respostas são confidenciais, pois nenhum dado que identifique o participante será coletado, garantindo sua privacidade e anonimato.

As informações serão utilizadas exclusivamente para fins de pesquisa no âmbito do Mestrado da Escola de Políticas Públicas e Governo do Instituto Brasileiro de Ensino, Desenvolvimento e Pesquisa.

Acesse o questionário pelo link: https://bit.ly/4gkOtWa

A sua opinião importa! Contamos com a sua participação.

Desde já, agradecemos a sua colaboração.

Cordialmente,

Carolina Guimarães Neves: Atividade de Defesa do Consumidor e Fiscal de Defesa do Consumidor. Pesquisadora do Instituto Brasileiro de Ensino, Desenvolvimento e Pesquisa.

Orientador: Profª. Doutorª. Fátima Lima"""


def verificar_saude():
    """Verifica se a API está rodando"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def testar_texto(texto, descricao):
    """Testa processamento de texto"""
    print(f"\n{'='*80}")
    print(f"TESTANDO: {descricao}")
    print(f"{'='*80}\n")
    print(f"TEXTO ORIGINAL:\n{texto[:200]}...\n")
    
    try:
        response = requests.post(
            API_URL,
            json={"texto": texto},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            resultado = response.json()
            print(f"TEXTO TARJADO:\n{resultado['textoTarjado'][:300]}...\n")
            print(f"\nDADOS OCULTADOS: {resultado['dadosOcultados']}")
            print(f"\nENTIDADES ENCONTRADAS:")
            
            # Agrupar por tipo
            entidades_por_tipo = {}
            for ent in resultado['entidadesEncontradas']:
                tipo = ent['tipo']
                if tipo not in entidades_por_tipo:
                    entidades_por_tipo[tipo] = []
                entidades_por_tipo[tipo].append(ent['texto'])
            
            for tipo, valores in sorted(entidades_por_tipo.items()):
                print(f"  {tipo}: {valores}")
            
            # Verificações específicas
            texto_tarjado = resultado['textoTarjado']
            print(f"\n{'='*80}")
            print("VERIFICAÇÕES:")
            print(f"{'='*80}")
            
            if descricao == "Termo de Cooperação":
                if "[LOCAL]" in texto_tarjado and "Termo de Acordo" in texto_tarjado:
                    print("✅ CORRETO: 'Termo' NÃO foi tarjado como [LOCAL]")
                elif "[LOCAL]" not in texto_tarjado:
                    print("✅ CORRETO: Nenhum falso positivo de [LOCAL]")
                else:
                    print("❌ ERRO: 'Termo' foi incorretamente tarjado")
            
            elif descricao == "Questionário IA":
                erros = []
                if "Inteligência Artificial" not in texto_tarjado:
                    erros.append("'Inteligência Artificial' foi incorretamente tarjado")
                if "Letramento Digital" not in texto_tarjado:
                    erros.append("'Letramento Digital' foi incorretamente tarjado")
                if "Perfil Demográfico" not in texto_tarjado:
                    erros.append("'Perfil Demográfico' foi incorretamente tarjado")
                if "[NOME]" not in texto_tarjado or "Carolina Guimarães Neves" in texto_tarjado:
                    erros.append("'Carolina Guimarães Neves' NÃO foi tarjado")
                if "Fátima Lima" in texto_tarjado:
                    erros.append("'Fátima Lima' NÃO foi tarjado")
                
                if erros:
                    print("❌ ERROS ENCONTRADOS:")
                    for erro in erros:
                        print(f"  - {erro}")
                else:
                    print("✅ TODOS OS TESTES PASSARAM!")
                    print("  - Nomes detectados corretamente")
                    print("  - Termos técnicos NÃO tarjados incorretamente")
        else:
            print(f"ERRO: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERRO na requisição: {e}")


if __name__ == "__main__":
    print("Verificando se API está rodando...")
    if not verificar_saude():
        print("❌ API não está rodando!")
        print("Execute: python main.py")
        exit(1)
    
    print("✅ API está rodando\n")
    
    # Testar os dois textos
    testar_texto(texto1, "Termo de Cooperação")
    testar_texto(texto2, "Questionário IA")
    
    print(f"\n{'='*80}")
    print("TESTES CONCLUÍDOS")
    print(f"{'='*80}")
