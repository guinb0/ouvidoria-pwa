"""
Teste completo de anonimização LGPD
Testa todos os 33 tipos de dados pessoais e sensíveis conforme Art. 5º da LGPD
"""
import requests
import json

# Texto com TODOS os tipos de dados considerados pela LGPD
TEXTO_TESTE = """Meu nome é Carlos Henrique Almeida dos Santos, nome social Carlos Almeida, sou brasileiro, solteiro, engenheiro civil, nascido em 15/08/1987, atualmente com 38 anos.

Meu CPF é 123.456.789-09 e meu RG é 12.345.678-9 SSP/SP.

Resido na Rua das Acácias, nº 450, Apto 302, Bairro Jardim Primavera, São Paulo/SP, CEP 01234-567.

Meu telefone é (11) 99876-5432, meu e-mail é carlos.almeida87@email.com e meu usuário de login no sistema é calmeida87. O acesso foi realizado a partir do IP 189.45.120.33, estando eu localizado próximo à latitude -23.55052 e longitude -46.633308.

Trabalho atualmente na empresa Construtora Alfa Ltda., onde utilizo o veículo de placa ABC-1D23 para atividades profissionais.

Identifiquei problemas relacionados ao meu contrato nº 2024-OUV-998877, bem como ao protocolo de atendimento 456789123.

Informo ainda que meus dados bancários (Banco 001, agência 1234, conta corrente 56789-0) e meu cartão de crédito nº 4111 1111 1111 1111 foram indevidamente expostos.

Ressalto que sou de origem étnica parda, sigo a religião católica, possuo opinião política de orientação progressista e sou filiado ao Sindicato dos Engenheiros do Estado de São Paulo.

Também houve vazamento de dados de saúde, incluindo histórico de hipertensão arterial, além de informações sobre meus dados biométricos (impressão digital) e dados genéticos coletados em exame laboratorial.

Por fim, foram mencionadas indevidamente informações sobre minha orientação sexual, o que considero extremamente grave.

Anexo a esta reclamação segue minha fotografia, minha assinatura digitalizada e registros internos do sistema contendo meus dados pessoais.

Solicito providências urgentes.

Carlos Henrique Almeida dos Santos"""

# Dados que DEVEM ser mascarados (expectativa)
DADOS_ESPERADOS = {
    "PERSON": ["Carlos Henrique Almeida dos Santos", "Carlos Almeida"],
    "BR_CPF": ["123.456.789-09"],
    "BR_RG": ["12.345.678-9"],
    "BR_CEP": ["01234-567"],
    "BR_PHONE": ["(11) 99876-5432"],
    "EMAIL_ADDRESS": ["carlos.almeida87@email.com"],
    "LOCATION": ["Rua das Acácias", "São Paulo", "SP", "Bairro Jardim Primavera"],
    "BR_DATE_OF_BIRTH": ["15/08/1987"],
    "BR_AGE": ["38 anos"],
    "BR_NATIONALITY": ["brasileiro"],
    "BR_MARITAL_STATUS": ["solteiro"],
    "BR_PROFESSION": ["engenheiro civil"],
    "BR_USERNAME": ["calmeida87"],
    "BR_IP_EXPLICIT": ["IP 189.45.120.33"],
    "BR_GEOLOCATION": ["latitude -23.55052", "longitude -46.633308"],
    "BR_VEHICLE_PLATE": ["ABC-1D23"],
    "BR_CONTRACT_NUMBER": ["contrato nº 2024-OUV-998877", "protocolo de atendimento 456789123"],
    "BR_BANK_ACCOUNT": ["Banco 001", "agência 1234", "conta corrente 56789-0"],
    "CREDIT_CARD": ["4111 1111 1111 1111"],
    "BR_ETHNICITY": ["origem étnica parda"],
    "BR_RELIGION": ["religião católica"],
    "BR_POLITICAL_OPINION": ["opinião política de orientação progressista"],
    "BR_UNION_MEMBERSHIP": ["Sindicato dos Engenheiros do Estado de São Paulo"],
    "BR_HEALTH_DATA": ["hipertensão arterial"],
    "BR_SEXUAL_ORIENTATION": ["orientação sexual"],
}

def testar_anonimizacao():
    """Testa o serviço de anonimização"""
    print("=" * 80)
    print("TESTE COMPLETO DE ANONIMIZAÇÃO LGPD")
    print("=" * 80)
    print()
    
    # Verificar se serviço está ativo
    try:
        response = requests.get("http://localhost:8000/api/health", timeout=5)
        if response.status_code != 200:
            print("❌ Serviço não está respondendo corretamente")
            print("   Certifique-se de iniciar o serviço: python main.py")
            return
    except requests.exceptions.ConnectionError:
        print("❌ Não foi possível conectar ao serviço na porta 8000")
        print("   Inicie o serviço primeiro: python main.py")
        return
    
    print("✅ Serviço de anonimização está ativo")
    print()
    
    # Verificar entidades suportadas
    print("🔍 Consultando entidades suportadas...")
    response = requests.get("http://localhost:8000/api/entities")
    entities_info = response.json()
    print(f"   Total de entidades: {entities_info.get('total', 'N/A')}")
    print(f"   LGPD Compliant: {entities_info.get('lgpd_compliant', False)}")
    print()
    
    # Processar texto
    print("📝 Processando texto de teste...")
    print()
    print("TEXTO ORIGINAL:")
    print("-" * 80)
    print(TEXTO_TESTE)
    print("-" * 80)
    print()
    
    response = requests.post(
        "http://localhost:8000/api/processar",
        json={"texto": TEXTO_TESTE, "language": "pt"}
    )
    
    if response.status_code != 200:
        print(f"❌ Erro ao processar: {response.status_code}")
        print(response.text)
        return
    
    resultado = response.json()
    
    print("TEXTO ANONIMIZADO:")
    print("-" * 80)
    print(resultado["textoTarjado"])
    print("-" * 80)
    print()
    
    # Análise de resultados
    print("📊 ANÁLISE DE DETECÇÃO")
    print("=" * 80)
    print(f"Total de entidades detectadas: {resultado['dadosOcultados']}")
    print()
    
    # Agrupar entidades por tipo
    entidades_por_tipo = {}
    for entidade in resultado["entidadesEncontradas"]:
        tipo = entidade["tipo"]
        if tipo not in entidades_por_tipo:
            entidades_por_tipo[tipo] = []
        
        # Extrair texto da entidade
        inicio = entidade["inicio"]
        fim = entidade["fim"]
        texto_entidade = TEXTO_TESTE[inicio:fim]
        confianca = entidade["confianca"]
        
        entidades_por_tipo[tipo].append({
            "texto": texto_entidade,
            "confianca": confianca
        })
    
    # Exibir por tipo
    print("Entidades detectadas por categoria:")
    print()
    for tipo in sorted(entidades_por_tipo.keys()):
        entidades = entidades_por_tipo[tipo]
        print(f"  {tipo} ({len(entidades)} ocorrência(s)):")
        for ent in entidades:
            print(f"    ✓ '{ent['texto']}' (confiança: {ent['confianca']:.2f})")
        print()
    
    # Análise de cobertura LGPD
    print("=" * 80)
    print("🎯 ANÁLISE DE COBERTURA LGPD")
    print("=" * 80)
    print()
    
    tipos_detectados = set(entidades_por_tipo.keys())
    tipos_lgpd = [
        # Documentos e identificação
        ("PERSON", "Nome completo"),
        ("BR_CPF", "CPF"),
        ("BR_RG", "RG"),
        ("EMAIL_ADDRESS", "E-mail"),
        ("BR_PHONE", "Telefone"),
        ("BR_CEP", "CEP"),
        ("LOCATION", "Localização/Endereço"),
        
        # Dados pessoais
        ("BR_DATE_OF_BIRTH", "Data de nascimento"),
        ("BR_AGE", "Idade"),
        ("BR_NATIONALITY", "Nacionalidade"),
        ("BR_MARITAL_STATUS", "Estado civil"),
        ("BR_PROFESSION", "Profissão"),
        
        # Dados financeiros
        ("BR_BANK_ACCOUNT", "Dados bancários"),
        ("CREDIT_CARD", "Cartão de crédito"),
        ("BR_CONTRACT_NUMBER", "Contrato/Protocolo"),
        
        # Dados de localização
        ("BR_VEHICLE_PLATE", "Placa de veículo"),
        ("BR_GEOLOCATION", "Coordenadas GPS"),
        ("BR_USERNAME", "Nome de usuário"),
        ("BR_IP_EXPLICIT", "Endereço IP"),
        
        # Dados sensíveis LGPD (Art. 5º, II)
        ("BR_ETHNICITY", "Origem étnica"),
        ("BR_RELIGION", "Religião"),
        ("BR_POLITICAL_OPINION", "Opinião política"),
        ("BR_UNION_MEMBERSHIP", "Filiação sindical"),
        ("BR_HEALTH_DATA", "Dados de saúde"),
        ("BR_SEXUAL_ORIENTATION", "Orientação sexual"),
    ]
    
    detectados = 0
    nao_detectados = 0
    
    for tipo, descricao in tipos_lgpd:
        if tipo in tipos_detectados:
            print(f"  ✅ {descricao.ljust(30)} → {tipo}")
            detectados += 1
        else:
            print(f"  ❌ {descricao.ljust(30)} → {tipo} (NÃO DETECTADO)")
            nao_detectados += 1
    
    print()
    print("=" * 80)
    print(f"RESULTADO FINAL: {detectados}/{detectados + nao_detectados} categorias detectadas")
    taxa_sucesso = (detectados / (detectados + nao_detectados)) * 100
    print(f"Taxa de sucesso: {taxa_sucesso:.1f}%")
    print("=" * 80)
    
    # Salvar resultados
    with open("test_results_lgpd_complete.json", "w", encoding="utf-8") as f:
        json.dump({
            "texto_original": TEXTO_TESTE,
            "texto_anonimizado": resultado["textoTarjado"],
            "total_entidades": resultado["dadosOcultados"],
            "entidades_por_tipo": entidades_por_tipo,
            "taxa_deteccao": f"{taxa_sucesso:.1f}%",
            "detectados": detectados,
            "nao_detectados": nao_detectados
        }, f, ensure_ascii=False, indent=2)
    
    print()
    print(f"✅ Resultados salvos em: test_results_lgpd_complete.json")

if __name__ == "__main__":
    testar_anonimizacao()
