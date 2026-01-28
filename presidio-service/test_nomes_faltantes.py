"""
Teste focado nos 5 nomes que não estão sendo detectados
"""
import requests

API_URL = "http://localhost:8000/api/processar"

# Textos com os 5 nomes problemáticos
CASOS_TESTE = [
    {
        "nome": "Júlio Cesar Alves da Rosa",
        "texto": "Júlio Cesar Alves\n    da Rosa, no período de 12/2002"
    },
    {
        "nome": "Antonio Vasconcelos", 
        "texto": "O servidor responsável pelo projeto era o Sr. Antonio\n     Vasconcelos. Com todas essas informações"
    },
    {
        "nome": "Conceição Sampaio",
        "texto": "pesquisa de mestrado e gostaria de fazer essa comparação antes da pandemia. Grata Conceição Sampaio"
    },
    {
        "nome": "Carolina Alves de Freitas Valle",
        "texto": "minha filha Carolina Alves de\n   Freitas Valle Carolina Pois ele estava com o pai"
    },
    {
        "nome": "Gustavo",
        "texto": "At.te\n   Gustavo\ncastração gratuita para gatos"
    }
]

def processar_texto(texto: str):
    """Processa texto via API"""
    response = requests.post(API_URL, json={"texto": texto})
    if response.status_code == 200:
        return response.json()
    else:
        print(f"❌ Erro {response.status_code}: {response.text}")
        return None

def extrair_nomes_detectados(resultado):
    """Extrai lista de nomes detectados do resultado"""
    if not resultado:
        return []
    
    # API retorna entidadesEncontradas com tipo/inicio/fim
    texto_original = resultado.get('textoOriginal', '')
    entidades = resultado.get('entidadesEncontradas', [])
    
    nomes = []
    for ent in entidades:
        if ent.get('tipo') == 'PERSON':
            inicio = ent.get('inicio', 0)
            fim = ent.get('fim', 0)
            nome = texto_original[inicio:fim]
            nomes.append(nome)
    return nomes

def main():
    print("\n" + "="*100)
    print("TESTE DOS 5 NOMES FALTANTES")
    print("="*100 + "\n")
    
    for i, caso in enumerate(CASOS_TESTE, 1):
        print(f"\n{'='*80}")
        print(f"CASO {i}: {caso['nome']}")
        print(f"{'='*80}")
        print(f"\nTexto original:")
        print(f"```\n{caso['texto']}\n```")
        
        resultado = processar_texto(caso['texto'])
        
        if resultado:
            nomes_detectados = extrair_nomes_detectados(resultado)
            print(f"\nNomes detectados ({len(nomes_detectados)}):")
            for nome in nomes_detectados:
                print(f"  • {nome}")
            
            # Verificar se o nome esperado foi detectado
            nome_esperado = caso['nome']
            encontrado = False
            
            # Verificar match exato
            if nome_esperado in nomes_detectados:
                print(f"\n✅ DETECTADO COMPLETO: '{nome_esperado}'")
                encontrado = True
            else:
                # Verificar matches parciais
                palavras_esperadas = set(nome_esperado.split())
                for nome_det in nomes_detectados:
                    palavras_det = set(nome_det.split())
                    if palavras_det & palavras_esperadas:  # Interseção
                        print(f"\n⚠️ DETECTADO PARCIAL: '{nome_det}'")
                        print(f"   Esperado: '{nome_esperado}'")
                        print(f"   Palavras faltando: {palavras_esperadas - palavras_det}")
                        encontrado = True
                
                if not encontrado:
                    print(f"\n❌ NÃO DETECTADO: '{nome_esperado}'")
                    print(f"   Nomes detectados no texto: {nomes_detectados}")
        else:
            print("\n❌ Falha ao processar")

if __name__ == "__main__":
    main()
