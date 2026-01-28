"""
Teste dos validadores robustos usando todos os nomes da AMOSTRA_e-SIC.txt
"""
import requests
import json
import re
from typing import List, Dict

API_URL = "http://localhost:8000/api/processar"

# Nomes esperados na amostra (extração manual)
NOMES_ESPERADOS = [
    "Júlio Cesar Alves da Rosa",
    "Maria Martins Mota Silva",
    "Antonio Costa",
    "Ruth Helena Franco",
    "Cassandra Rodrigues",
    "Ana Cristina Cardoso Ribeiro Sousa",
    "Paulo Roberto Braga Nascimento",
    "José Paulo Lacerda Almeida",
    "Paulo SA AN Martins",
    "Ana Garcia",
    "Roberto Carlos Pereira",
    "Antônio Garcia Soares",
    "AURA Costa Mota",
    "Rafael",
    "Lúcio Miguel",
    "Leonardo Rocha",
    "Jorge Luiz Pereira Vieira",
    "Walter Rodrigues Cruz",
    "Antonio Vasconcelos",
    "Beatriz Oliveira Nunes",
    "Conceição Sampaio",
    "Carolina Alves de Freitas Valle",
    "Braga",
    "Carolina",
    "Thiago",
    "Pablo Souza Ramos",
    "Eduardo",
    "Marcos Henrique da Silva Simoes",
    "Edson Henrique da Costa Camargo",
    "João Lopes Ribeiro",
    "Gabriela Isabel Campos Lima Cruz",
    "João Ribeiro",
    "Eduardo da Costa Barbosa",
    "Pablo da Vitória Simões",
    "Francisco Barbosa Marques",
    "João Campos Cruz",
    "Lima Tavares",
    "Carolina Guimarães Neves",
    "Fátima Lima",
    "Fátima Ferreira Braga",
    "Maria Rodrigues de Araújo",
    "Gustavo",
]

# Palavras que NÃO devem ser detectadas como PERSON ou LOCATION
NAO_DEVEM_SER_DETECTADOS = {
    # Termos administrativos
    "Termo", "Acordo", "Cooperação", "Contrato", "Convênio",
    # Termos técnicos
    "Inteligência Artificial", "Letramento Digital", "Perfil Demográfico",
    "Setor Público", "Inteligência Artificial Generativa",
    # Instituições
    "Governo do Distrito Federal", "Instituto Brasileiro de Ensino",
    "Escola de Políticas Públicas e Governo",
    "Mestrado", "Desenvolvimento", "Pesquisa",
    # Verbos
    "Venho", "Solicito", "Informo",
    # Outras
    "Atividade de Defesa do Consumidor",
}


def verificar_saude():
    """Verifica se a API está rodando"""
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def extrair_nomes_do_resultado(entidades: List[Dict], texto_original: str) -> List[str]:
    """Extrai nomes detectados das entidades usando índices"""
    nomes = []
    for ent in entidades:
        if ent.get('tipo') == 'PERSON':
            inicio = ent.get('inicio', 0)
            fim = ent.get('fim', 0)
            nome = texto_original[inicio:fim]
            nomes.append(nome)
    return nomes


def testar_arquivo_completo():
    """Testa o arquivo completo AMOSTRA_e-SIC.txt"""
    print("="*80)
    print("TESTE COMPLETO: AMOSTRA_e-SIC.txt")
    print("="*80)
    
    # Ler arquivo
    with open("../AMOSTRA_e-SIC.txt", "r", encoding="utf-8") as f:
        texto_completo = f.read()
    
    print(f"\nTamanho do texto: {len(texto_completo)} caracteres")
    print(f"Processando...")
    
    try:
        response = requests.post(
            API_URL,
            json={"texto": texto_completo},
            headers={"Content-Type": "application/json"},
            timeout=300  # 5 minutos para ensemble de 3 modelos (spaCy + Flair + Stanza)
        )
        
        if response.status_code == 200:
            resultado = response.json()
            
            print(f"\n✅ Processamento concluído!")
            print(f"Dados ocultados: {resultado.get('dadosOcultados', 0)}")
            
            # Extrair nomes detectados
            nomes_detectados = extrair_nomes_do_resultado(resultado.get('entidadesEncontradas', []), texto_completo)
            
            print(f"\n{'='*80}")
            print(f"NOMES DETECTADOS ({len(nomes_detectados)}):")
            print(f"{'='*80}")
            for nome in sorted(set(nomes_detectados)):
                print(f"  ✓ {nome}")
            
            # Verificar recall (quantos dos nomes esperados foram encontrados)
            print(f"\n{'='*80}")
            print(f"ANÁLISE DE RECALL (Nomes Esperados vs Detectados)")
            print(f"{'='*80}")
            
            nomes_detectados_lower = [n.lower() for n in nomes_detectados]
            encontrados = 0
            nao_encontrados = []
            
            for nome_esperado in NOMES_ESPERADOS:
                # Verificar se nome esperado está nos detectados
                encontrado = any(nome_esperado.lower() in nd for nd in nomes_detectados_lower)
                
                if encontrado:
                    encontrados += 1
                    print(f"  ✅ {nome_esperado}")
                else:
                    nao_encontrados.append(nome_esperado)
                    print(f"  ❌ {nome_esperado} - NÃO DETECTADO")
            
            recall = (encontrados / len(NOMES_ESPERADOS)) * 100 if NOMES_ESPERADOS else 0
            print(f"\n📊 RECALL: {encontrados}/{len(NOMES_ESPERADOS)} = {recall:.1f}%")
            
            # Verificar precision (falsos positivos)
            print(f"\n{'='*80}")
            print(f"ANÁLISE DE PRECISION (Falsos Positivos)")
            print(f"{'='*80}")
            
            texto_tarjado = resultado.get('textoTarjado', '')
            falsos_positivos = []
            
            # Verificar se termos que não devem ser tarjados foram mantidos
            for termo in NAO_DEVEM_SER_DETECTADOS:
                if termo not in texto_tarjado:
                    falsos_positivos.append(termo)
                    print(f"  ❌ '{termo}' foi incorretamente tarjado")
                else:
                    print(f"  ✅ '{termo}' mantido (correto)")
            
            # Verificar LOCATION especificamente
            print(f"\n{'='*80}")
            print(f"LOCALIZAÇÕES DETECTADAS:")
            print(f"{'='*80}")
            locations = [texto_completo[ent.get('inicio', 0):ent.get('fim', 0)] 
                        for ent in resultado.get('entidadesEncontradas', []) 
                        if ent.get('tipo') == 'LOCATION']
            for loc in sorted(set(locations)):
                print(f"  • {loc}")
            
            # Resumo final
            print(f"\n{'='*80}")
            print(f"RESUMO FINAL")
            print(f"{'='*80}")
            print(f"✅ Recall de Nomes: {recall:.1f}%")
            print(f"❌ Falsos Positivos: {len(falsos_positivos)}")
            print(f"📊 Total de Entidades: {resultado.get('dadosOcultados', 0)}")
            
            if recall >= 95 and len(falsos_positivos) <= 2:
                print(f"\n🎉 QUALIDADE EXCELENTE!")
            elif recall >= 85 and len(falsos_positivos) <= 5:
                print(f"\n✅ QUALIDADE BOA")
            else:
                print(f"\n⚠️ PRECISA MELHORAR")
            
            # Salvar resultado para análise
            with open("test_amostra_resultado.json", "w", encoding="utf-8") as f:
                json.dump({
                    "nomes_detectados": nomes_detectados,
                    "nomes_esperados": NOMES_ESPERADOS,
                    "nao_encontrados": nao_encontrados,
                    "falsos_positivos": falsos_positivos,
                    "recall": recall,
                    "total_entidades": resultado.get('dadosOcultados', 0),
                    "entidades_por_tipo": {
                        tipo: [e.get('texto', '') for e in resultado.get('entidadesEncontradas', []) if e.get('tipo') == tipo]
                        for tipo in set(e.get('tipo', '') for e in resultado.get('entidadesEncontradas', []))
                    }
                }, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Resultado salvo em: test_amostra_resultado.json")
            
        else:
            print(f"❌ ERRO: Status {response.status_code}")
            print(response.text)
    
    except Exception as e:
        print(f"❌ ERRO na requisição: {e}")


if __name__ == "__main__":
    print("Verificando se API está rodando...")
    if not verificar_saude():
        print("❌ API não está rodando!")
        print("Execute no terminal python: python main.py")
        exit(1)
    
    print("✅ API está rodando\n")
    
    testar_arquivo_completo()
