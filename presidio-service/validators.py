"""
Validadores robustos para entidades usando bibliotecas especializadas
Evita falsos positivos usando datasets reais de nomes e localizações
"""
import logging
from typing import Optional, Set
from functools import lru_cache

# Importar biblioteca de nomes
try:
    from names_dataset import NameDataset
    NAMES_DATASET_AVAILABLE = True
except ImportError:
    NAMES_DATASET_AVAILABLE = False

# Importar biblioteca de geocoding
try:
    from geopy.geocoders import Nominatim
    from geopy.exc import GeocoderTimedOut, GeocoderServiceError
    GEOPY_AVAILABLE = True
except ImportError:
    GEOPY_AVAILABLE = False

# Importar biblioteca de países/localidades
try:
    import pycountry
    PYCOUNTRY_AVAILABLE = True
except ImportError:
    PYCOUNTRY_AVAILABLE = False

logger = logging.getLogger(__name__)

# Inicializar NameDataset globalmente (carrega uma vez)
if NAMES_DATASET_AVAILABLE:
    try:
        name_dataset = NameDataset()
        logger.info("NameDataset carregado com sucesso - validação robusta de nomes ativada")
    except Exception as e:
        logger.warning(f"Erro ao carregar NameDataset: {e}")
        NAMES_DATASET_AVAILABLE = False
        name_dataset = None
else:
    name_dataset = None
    logger.warning("names-dataset não instalado - validação de nomes limitada")

# Inicializar Nominatim para geocoding
if GEOPY_AVAILABLE:
    try:
        geolocator = Nominatim(user_agent="ouvidoria-pwa-presidio", timeout=2)
        logger.info("Geopy carregado com sucesso - validação robusta de localizações ativada")
    except Exception as e:
        logger.warning(f"Erro ao inicializar Geopy: {e}")
        GEOPY_AVAILABLE = False
        geolocator = None
else:
    geolocator = None
    logger.warning("geopy não instalado - validação de localizações limitada")


class NameValidator:
    """
    Validador robusto de nomes usando NameDataset
    Usa dataset com milhões de nomes reais do mundo todo
    """
    
    def __init__(self):
        self.dataset = name_dataset
        self.available = NAMES_DATASET_AVAILABLE
        
        # Lista expandida de palavras que NUNCA são nomes (blacklist definitiva)
        self.never_names = {
            # Verbos comuns em documentos administrativos
            "venho", "solicito", "requeiro", "peço", "peco", "encaminho", "apresento",
            "informo", "comunico", "manifesto", "declaro", "afirmo", "ratifico",
            "pergunto", "questiono", "indago", "consulto", "verifico", "confirmo",
            "gostaria", "quero", "preciso", "necessito", "desejo", "pretendo",
            # Substantivos genéricos
            "servidor", "servidora", "cidadao", "cidada", "solicitante", "requerente",
            "interessado", "contribuinte", "usuario", "beneficiario", "funcionario",
            # Termos administrativos
            "processo", "protocolo", "documento", "artigo", "lei", "decreto", "portaria",
            "oficio", "memorando", "despacho", "parecer", "termo", "acordo", "contrato",
            "convenio", "convencao", "cooperacao", "parceria", "emenda", "empenho",
            "inciso", "validador", "gerador", "disposto", "edital", "concurso",
            "registrado", "registros", "anexo", "ref", "fato", "destaque",
            # Áreas/setores (detectados incorretamente como PERSON)
            "artificial", "digital", "demografico", "profissional", "publico",
            "generativa", "inteligencia", "letramento", "perfil", "setor",
            "gestao", "governanca", "administracao", "infraestrutura", "tic",
            "banco de dados", "aplicativo", "programa", "integridade", "monitoramento",
            "carteira de trabalho", "interesse", "ajuda", "ouvidoria", "canal",
            "contoladoria", "assunto", "esbulho", "texto", "superior", "juvenil",
            # Palavras compostas técnicas
            "governo", "distrito", "federal", "mestrado", "escola", "politicas",
            "instituto", "brasileiro", "ensino", "desenvolvimento", "pesquisa",
            # Instituições compostas - ÓRGÃOS GOVERNAMENTAIS BRASILEIROS
            "instituto brasileiro de ensino",
            "escola de politicas publicas", "escola de politicas publicas e governo",
            "escola nacional de administracao publica", "enap",
            "governo do distrito federal", "gdf",
            "ministerio", "secretaria de estado", "secretaria estadual", "secretaria municipal",
            "prefeitura", "camara municipal", "assembleia legislativa",
            "tribunal de justica", "tribunal regional", "defensoria publica",
            "procuradoria geral", "controladoria geral",
            "agencia nacional", "banco central", "caixa economica", "receita federal",
            "policia federal", "policia militar", "corpo de bombeiros",
            "inss", "sus", "datasus", "ibge", "ibama", "funai", "incra",
            "anvisa", "anatel", "aneel", "ans", "anac", "anp",
            "supremo tribunal federal", "superior tribunal",
            "congresso nacional", "senado federal", "camara dos deputados",
            "universidade federal", "instituto federal",
            "petrobras", "eletrobras", "correios", "bndes",
            # Instituições de ensino (NUNCA anonimizar)
            "escola", "colegio", "faculdade", "universidade", "instituto",
            "centro universitario", "centro de ensino", "academia",
            "escola municipal", "escola estadual", "escola particular",
            "escola publica", "ensino fundamental", "ensino medio",
            "educacao", "curso", "graduacao", "pos-graduacao",
            # Status e qualificadores
            "aberto", "fechado", "pendente", "concluido", "ativo", "inativo",
            # Cargos/títulos genéricos
            "gerencia", "diretoria", "coordenacao", "assessoria", "secretaria",
            "ministerio", "governador", "prefeito", "diretor", "coordenador",
            # Outros
            "carreira", "gestao", "administracao", "departamento", "divisao",
            "favor", "aluna", "moro", "data", "valor", "identidade", "ola", "oi",
            "prezados", "prezadas", "grato", "grata", "atenciosamente", "cordialmente"
        }
        
        # Primeiros nomes brasileiros muito comuns (lista definitiva)
        # Fonte: IBGE, cartórios brasileiros, dados demográficos
        self.common_brazilian_first_names = {
            # Nomes masculinos muito comuns
            "joao", "jose", "antonio", "antonio", "francisco", "carlos", "paulo", "pedro",
            "lucas", "luiz", "marcos", "luis", "gabriel", "rafael", "daniel", "marcelo",
            "bruno", "eduardo", "felipe", "guilherme", "rodrigo", "fernando", "gustavo",
            "leonardo", "caio", "vitor", "henrique", "thiago", "diego", "ricardo",
            "anderson", "andre", "sergio", "roberto", "alexandre", "renan", "vinicius",
            "julio", "cesar", "adriano", "fabio", "marcio", "leandro", "mauricio",
            "renato", "wallace", "wellington", "matheus", "nicolas", "igor", "otavio",
            "raul", "samuel", "isaac", "theo", "arthur", "miguel", "davi", "heitor",
            "bernardo", "lorenzo", "joao", "enzo", "ryan", "ian", "pietro", "benicio",
            # Nomes femininos muito comuns
            "maria", "ana", "francisca", "antonia", "adriana", "juliana", "marcia",
            "fernanda", "patricia", "aline", "tatiana", "cristina", "leticia", "vanessa",
            "camila", "amanda", "bruna", "carla", "claudia", "daniela", "eliane",
            "fabiana", "gabriela", "helena", "isabela", "jessica", "julia", "larissa",
            "luciana", "michele", "natalia", "paula", "priscila", "renata", "roberta",
            "sabrina", "silvia", "simone", "tania", "viviane", "alice", "beatriz",
            "carolina", "cecilia", "clara", "debora", "eduarda", "emanuela", "fatima",
            "gisele", "giovana", "heloisa", "iris", "jade", "lais", "livia", "lorena",
            "manuela", "marina", "melissa", "nicole", "olivia", "pietra", "rafaela",
            "raquel", "regina", "rosangela", "sandra", "sophia", "valentina", "yasmin",
            "conceicao", "aparecida", "socorro", "penha", "gloria", "graca", "lourdes",
            "conceição",  # Versão com acento
            # Nomes compostos comuns (primeira parte)
            "joao", "jose", "maria", "ana", "paulo", "carlos", "pedro", "luiz",
            "marcos", "antonio", "francisco", "luiza", "clara", "eduarda", "gabriela",
            # Variações e diminutivos
            "beto", "betina", "carlinhos", "duda", "juju", "lulu", "nando", "rafa",
            "tati", "vivi", "gabi", "fabi", "dani", "cris", "mari", "leti", "nath",
            "bia", "carol", "cacá", "zeca", "chico", "binho", "nino", "tito",
            "aura", "ruth", "edson", "walter", "cassandra", "pablo", "lúcio", "lucio",
            "thiago", "conceicao"
        }
        
        # Sobrenomes brasileiros muito comuns (Top 200+ segundo IBGE)
        self.common_brazilian_surnames = {
            # Top 20 (> 1% da população)
            "silva", "santos", "oliveira", "souza", "sousa", "rodrigues", "ferreira", 
            "alves", "pereira", "lima", "gomes", "costa", "ribeiro", "martins",
            "carvalho", "rocha", "almeida", "nascimento", "araujo", "araújo",
            # Top 21-50
            "melo", "barbosa", "cardoso", "reis", "castro", "andrade", "pinto", 
            "moreira", "freitas", "fernandes", "dias", "cavalcanti", "monteiro", 
            "mendes", "barros", "batista", "tavares", "sampaio", "braga", "cruz",
            "simoes", "simões", "mota", "franco", "garcia", "moreira", "miranda",
            "guimaraes", "guimarães", "neves",
            # Top 51-100
            "correa", "corrêa", "teixeira", "pires", "rosa", "nunes", "borges",
            "camargo", "valle", "marques", "vasconcelos", "farias", "ramos", "bezerra",
            "cunha", "santiago", "aguiar", "rezende", "moura", "nogueira", "machado",
            "sales", "azevedo", "duarte", "macedo", "vargas", "jesus", "paiva",
            "magalhaes", "magalhães", "medeiros", "coelho", "xavier", "lourenco",
            "lourenço", "aragao", "aragão", "siqueira", "fonseca", "goncalves", "gonçalves",
            # Top 101-150
            "leite", "brito", "amaral", "bueno", "dantas", "godoy", "barreto",
            "pessoa", "matos", "fogaca", "fogaça", "ramalho", "delgado", "santana",
            "bastos", "viana", "toledo", "avila", "ávila", "porto", "lacerda",
            "salgado", "leal", "menezes", "moraes", "morais", "figueiredo",
            "mesquita", "rangel", "queiroz", "novais", "vaz", "pacheco",
            "furtado", "cardozo", "muniz", "fontes", "rossi", "goulart", "ventura",
            # Top 151-200 e outros muito comuns
            "brandao", "brandão", "medina", "vidal", "nery", "coutinho",
            "domingues", "lemos", "esteves", "serra", "gonzaga", "assuncao",
            "assunção", "silveira", "vilela", "fagundes", "guedes", "arruda",
            "caetano", "carneiro", "bento", "amorim", "guerra", "escobar", "jardim",
            "sequeira", "vale", "felix", "félix", "maia", "lara", "padilha", "torres",
            "serrano", "neto", "filho", "junior", "sobrinho", "segundo", "terceiro",
            "villar", "bispo", "goes", "peixoto", "cabral", "camara", "câmara",
            "vasques", "varela", "espinosa", "horta", "crespo", "bessa",
            "cortes", "cortês", "seabra", "lobato", "portela", "afonso", "saraiva",
            "cordeiro", "barroso", "guerreiro", "nobre", "galvao", "galvão",
            "prado", "pestana", "paredes", "trindade", "bernardes", "gama",
            "lopes", "marques", "borges", "pires", "moura", "cunha", "correa", "campos",
            "teixeira", "vieira", "azevedo", "sales", "xavier", "macedo", "farias", "nunes",
            "ramos", "miranda", "nogueira", "duarte", "pacheco", "medeiros", "amaral", 
            "fonseca", "guimaraes", "soares", "cavalcante", "brito", "siqueira", "moraes",
            "coelho", "vasconcelos", "neves", "cabral", "domingues", "toledo", "lacerda",
            "bezerra", "bastos", "guerra", "brandao", "torres", "santiago", "bueno",
            "sampaio", "tavares", "braga", "cruz", "simoes", "barbosa", "marques", "valle",
            "camargo", "mota", "franco", "garcia", "ribeiro"
        }
    
    def is_valid_name(self, text: str) -> bool:
        """
        Valida se o texto é realmente um nome de pessoa usando NameDataset
        
        Returns:
            True se é um nome válido, False caso contrário
        """
        if not text or not text.strip():
            return False
        
        # NORMALIZAR quebras de linha e espaços múltiplos (para nomes como "Júlio Cesar\n   da Rosa")
        text_normalized = ' '.join(text.split())
        
        text_lower = text_normalized.lower().strip()
        palavras = text_lower.split()
        
        # 1. Blacklist definitiva - NUNCA são nomes
        if text_lower in self.never_names:
            return False
        
        # 1.1. Verificar frases completas de órgãos que podem estar fragmentadas
        # Detectar padrões como "Escola de Políticas Públicas", "Mestrado da Escola"
        institutional_keywords = [
            "escola", "universidade", "faculdade", "colegio", "instituto",
            "centro universitario", "centro de ensino",
            "politicas publicas", "ministerio", "secretaria de",
            "prefeitura", "governo do", "tribunal de",
            "banco de dados", "gestao", "governanca", "administracao",
            "ouvidoria", "contoladoria", "infraestrutura"
        ]
        if any(org in text_lower for org in institutional_keywords):
            return False
        
        # 1.2. Rejeitar palavras únicas que são claramente não-nomes
        single_word_blacklist = {
            "ola", "oi", "id", "texto", "superior", "juvenil", "civil",
            "tarde", "box", "advogados", "sou", "inquilina", "sic",
            "referente", "administrativa", "gama", "oab", "ltda",
            "coliformes", "fosforo", "nitrogenio", "oxigenio", "solidos",
            "empenho", "emenda", "inciso", "validador", "canal", "geral"
        }
        if len(palavras) == 1 and palavras[0] in single_word_blacklist:
            return False
        
        # Verificar cada palavra
        for palavra in palavras:
            if palavra in self.never_names:
                return False
        
        # 2. Rejeitar se contém caracteres especiais inválidos para nomes
        if any(char in text_normalized for char in ['@', '#', '$', '%', '&', '*', '(', ')', '[', ']', '{', '}', '/', '\\']):
            return False
        
        # 3. Rejeitar siglas (todas maiúsculas, 2-8 caracteres, sem espaços)
        if text_normalized.isupper() and 2 <= len(text_normalized) <= 8 and ' ' not in text_normalized:
            # Exceções: siglas que são nomes (raríssimo)
            if text_normalized not in ["JOÃO", "JOSÉ"]:
                return False
        
        # 4. NOVO: Rejeitar frases muito longas (>6 palavras) - não são nomes
        if len(palavras) > 6:
            return False
        
        # 5. NOVO: Rejeitar se contém verbos auxiliares/preposições comuns
        palavras_gramaticais = {'de', 'da', 'do', 'das', 'dos', 'para', 'com', 'que', 'se', 'em', 'no', 'na', 'por', 'como', 'ser', 'uma', 'um', 'os', 'as', 'ao', 'pelo', 'pela'}
        # Se mais de 40% são palavras gramaticais, não é nome
        palavras_gram_count = sum(1 for p in palavras if p in palavras_gramaticais)
        if palavras_gram_count > len(palavras) * 0.4:
            return False
        
        # 5.1. NOVO: Rejeitar se contém verbos ou palavras de ação
        palavras_acao = {'saber', 'entrar', 'contato', 'constar', 'acesso', 'informar', 'fornecer', 'obter', 'solicitar', 'receber', 'possuir', 'ter', 'haver', 'fazer', 'dar', 'pedir', 'enviar', 'apresentar', 'encaminhar', 'chamo'}
        if any(p in palavras_acao for p in palavras):
            return False
        
        # 6. NOVO: Rejeitar se começa com verbo conjugado ou palavra minúscula
        if palavras and palavras[0] in {'gostaria', 'solicito', 'preciso', 'venho', 'quero', 'pedir', 'fazer', 'ter', 'saber', 'informar',
                                         'caso', 'tendo', 'ao', 'em', 'para', 'com', 'de', 'sem', 'por', 'sobre', 'como', 'quando',
                                         'estou', 'sou', 'foi', 'houve', 'possui', 'todas', 'isso', 'favor', 'pelo', 'a', 'o', 'e',
                                         'mas', 'ja', 'ainda', 'apos', 'antes', 'durante', 'pelo', 'pela', 'pelos', 'pelas'}:
            return False
        
        # 6.1. NOVO CRÍTICO: Rejeitar frases com múltiplas palavras min. como "em que contenha meu nome"
        # Apenas para frases com 3+ palavras
        if len(palavras) >= 3:
            # Contar palavras totalmente minúsculas (no texto ORIGINAL normalizado, não no lower)
            palavras_originais = text_normalized.split()
            minusculas_count = sum(1 for p in palavras_originais if p.islower() and p not in {'de', 'da', 'do', 'dos', 'das'})
            # Se >50% são minúsculas (excluindo preposições normais), é frase não nome
            if minusculas_count > len(palavras) * 0.5:
                return False
        
        # 7. NOVO: Rejeitar se não tem estrutura de nome (sem maiúsculas)
        if not any(c.isupper() for c in text_normalized):
            return False
        
        # Se NameDataset não está disponível, usar validação básica
        if not self.available or not self.dataset:
            # Validação básica: pelo menos 1 sobrenome brasileiro comum
            return any(sobrenome in palavras for sobrenome in self.common_brazilian_surnames)
        
        # 9. Validação robusta com NameDataset + Lista de nomes comuns brasileiros
        # Verificar cada palavra contra o dataset e nossa lista
        if len(palavras) == 1:
            # Nome único - deve estar no dataset como primeiro nome OU sobrenome OU na nossa lista
            palavra_lower = palavras[0].lower()
            
            # Verificar se está na lista de nomes brasileiros comuns
            if palavra_lower in self.common_brazilian_first_names:
                return True
            
            search_result = self.dataset.search(palavras[0].capitalize())
            
            # search retorna dict com 'first_name' e 'last_name'
            if search_result and (search_result.get('first_name') or search_result.get('last_name')):
                # Encontrado no dataset
                # Mas verificar se também é sobrenome comum (evitar "Santos" sozinho)
                if palavra_lower in self.common_brazilian_surnames and palavra_lower not in self.common_brazilian_first_names:
                    # É APENAS sobrenome comum (não é nome), exigir contexto ou score alto
                    return False  # Rejeitar palavra solta como "Santos", "Silva" sem contexto
                return True
            return False
        
        elif len(palavras) == 2:
            # Nome simples de 2 palavras - "Antonio Costa", "Fátima Lima", "Júlio Cesar"
            # AJUSTADO: Ser mais permissivo - aceitar se qualquer componente é válido
            palavra1_lower = palavras[0].lower()
            palavra2_lower = palavras[1].lower()
            palavra1_cap = palavras[0].capitalize()
            palavra2_cap = palavras[1].capitalize()
            
            # Verificar lista de nomes comuns primeiro (mais rápido)
            if palavra1_lower in self.common_brazilian_first_names:
                # Primeira é nome brasileiro comum - aceitar se segunda tem 3+ chars
                if palavra2_lower in self.common_brazilian_surnames or palavra2_lower in self.common_brazilian_first_names or len(palavra2_lower) >= 3:
                    return True
            
            # Se segunda palavra é sobrenome comum E primeira tem 3+ caracteres (não é sigla)
            if palavra2_lower in self.common_brazilian_surnames and len(palavra1_lower) >= 3:
                return True
            
            search1 = self.dataset.search(palavra1_cap)
            search2 = self.dataset.search(palavra2_cap)
            
            # Cenário 1: Primeira é first_name, segunda é last_name
            if search1 and search1.get('first_name') and (search2 and search2.get('last_name') or palavra2_lower in self.common_brazilian_surnames):
                return True
            
            # Cenário 2: Ambas aparecem no dataset (uma como nome, outra como sobrenome)
            if search1 and search2:
                return True
            
            # Cenário 3: Segunda palavra é sobrenome brasileiro comum E primeira é válida
            if palavra2_lower in self.common_brazilian_surnames and search1:
                return True
            
            # NOVO: Aceitar se primeira é nome comum no dataset E segunda tem 3+ chars
            if search1 and search1.get('first_name') and len(palavra2_lower) >= 3:
                return True
            
            return False
        
        else:
            # Nome composto (3+ palavras) - "Carolina Guimarães Neves", "Júlio Cesar Alves da Rosa"
            # AJUSTADO: Ser mais permissivo - aceitar se tem pelo menos um nome OU sobrenome válido
            has_first_name = False
            has_last_name = False
            valid_components = 0
            
            for i, palavra in enumerate(palavras):
                palavra_lower = palavra.lower()
                palavra_cap = palavra.capitalize()
                
                # Pular conectivos (de, da, dos, das, do)
                if palavra_lower in ['de', 'da', 'dos', 'das', 'do', 'e']:
                    continue
                
                # Verificar lista de nomes comuns brasileiros primeiro
                if palavra_lower in self.common_brazilian_first_names:
                    has_first_name = True
                    valid_components += 1
                
                if palavra_lower in self.common_brazilian_surnames:
                    has_last_name = True
                    valid_components += 1
                
                # Se ainda não encontrou, buscar no NameDataset
                if not (has_first_name and has_last_name):
                    search_result = self.dataset.search(palavra_cap)
                    
                    if search_result:
                        if search_result.get('first_name'):
                            has_first_name = True
                            valid_components += 1
                        if search_result.get('last_name'):
                            has_last_name = True
                            valid_components += 1
            
            # Nome válido: tem primeiro nome E sobrenome OU tem 2+ componentes válidos
            return (has_first_name and has_last_name) or valid_components >= 2


class LocationValidator:
    """
    Validador robusto de localizações usando Geopy e PyCountry
    Valida contra bases de dados geográficas reais
    """
    
    def __init__(self):
        self.geolocator = geolocator
        self.available = GEOPY_AVAILABLE
        
        # Cache de validações para evitar chamadas repetidas à API
        self._location_cache: dict = {}
        
        # Blacklist definitiva de palavras que NUNCA são localizações
        self.never_locations = {
            # Saudações/fechamentos
            "at.te", "atenciosamente", "cordialmente", "respeitosamente", "grata", "grato",
            # Verbos
            "venho", "solicito", "requeiro", "peço", "peco", "encaminho", "apresento",
            "informo", "comunico", "manifesto", "declaro", "afirmo", "ratifico",
            # Termos técnicos/abstratos
            "inteligencia", "artificial", "digital", "letramento", "generativa",
            "demografico", "profissional", "publico", "setor", "perfil",
            # Termos administrativos
            "termo", "acordo", "contrato", "convenio", "cooperacao", "parceria",
            "protocolo", "processo", "documento", "oficio", "memorando",
            # Órgãos/entidades (siglas)
            "gdf", "sefaz", "detran", "pmdf", "cbmdf", "tjdft", "mpdft",
            "caesb", "novacap", "terracap", "codhab", "dftrans",
            # Conceitos abstratos
            "mestrado", "escola", "instituto", "atividade", "fiscal",
            "consumidor", "defesa", "orientador", "pesquisador", "pesquisadora",
            # Palavras técnicas em contexto educacional/profissional
            "ensino", "desenvolvimento", "pesquisa", "politicas", "governo"
        }
        
        # Lista de cidades e estados brasileiros (backup caso geopy falhe)
        self.brazilian_states = {
            "acre", "alagoas", "amapa", "amazonas", "bahia", "ceara", "distrito federal",
            "espirito santo", "goias", "maranhao", "mato grosso", "mato grosso do sul",
            "minas gerais", "para", "paraiba", "parana", "pernambuco", "piaui",
            "rio de janeiro", "rio grande do norte", "rio grande do sul", "rondonia",
            "roraima", "santa catarina", "sao paulo", "sergipe", "tocantins",
            # Siglas
            "ac", "al", "ap", "am", "ba", "ce", "df", "es", "go", "ma", "mt", "ms",
            "mg", "pa", "pb", "pr", "pe", "pi", "rj", "rn", "rs", "ro", "rr", "sc", "sp", "se", "to"
        }
        
        # Cidades brasileiras mais comuns (top 200)
        self.brazilian_cities = self._load_brazilian_cities()
        
        # Indicadores de localização genuína
        self.location_indicators = {
            "rua", "avenida", "av", "alameda", "travessa", "praca", "rodovia",
            "cidade", "estado", "municipio", "bairro", "quadra", "lote", "conjunto",
            "endereco", "cep", "residencia", "domicilio", "logradouro"
        }
    
    def _load_brazilian_cities(self) -> Set[str]:
        """Carrega lista de cidades brasileiras principais"""
        # Top cidades brasileiras (expandível via arquivo JSON)
        return {
            "sao paulo", "rio de janeiro", "brasilia", "salvador", "fortaleza",
            "belo horizonte", "manaus", "curitiba", "recife", "goiania",
            "porto alegre", "belem", "guarulhos", "campinas", "sao luis",
            "sao goncalo", "maceio", "duque de caxias", "natal", "teresina",
            "campo grande", "nova iguacu", "sao bernardo do campo", "joao pessoa",
            "santo andre", "osasco", "jaboatao dos guararapes", "sao jose dos campos",
            "ribeirao preto", "uberlandia", "contagem", "sorocaba", "aracaju",
            "feira de santana", "cuiaba", "joinville", "juiz de fora", "londrina",
            "aparecida de goiania", "porto velho", "niteroi", "ananindeua", "serra",
            "campos dos goytacazes", "caxias do sul", "maua", "betim", "diadema",
            "jundiai", "carapicuiba", "piracicaba", "olinda", "bauru", "itaquaquecetuba",
            "sao vicente", "franca", "canoas", "cascavel", "petropolis", "vitoria",
            "ponta grossa", "blumenau", "limeira", "uberaba", "paulista", "suzano"
        }
    
    @lru_cache(maxsize=1000)
    def is_valid_location(self, text: str, context: str = "") -> bool:
        """
        Valida se o texto é realmente uma localização usando múltiplas estratégias
        
        Args:
            text: Texto detectado como localização
            context: Contexto ao redor (janela de palavras)
            
        Returns:
            True se é uma localização válida, False caso contrário
        """
        if not text or not text.strip():
            return False
        
        text_lower = text.lower().strip()
        palavras = text_lower.split()
        
        # 1. BLACKLIST DEFINITIVA - NUNCA são localizações
        if text_lower in self.never_locations:
            return False
        
        # Verificar cada palavra
        for palavra in palavras:
            if palavra in self.never_locations:
                return False
        
        # 2. REJEITAR frases muito longas (>5 palavras) - provavelmente conceitos/títulos
        if len(palavras) > 5:
            return False
        
        # 3. REJEITAR se contém apenas palavras abstratas/técnicas
        palavras_abstratas = {
            "artificial", "digital", "inteligencia", "letramento", "generativa",
            "politicas", "publicas", "privacidade", "seguranca", "tecnologia"
        }
        if all(palavra in palavras_abstratas for palavra in palavras):
            return False
        
        # 4. VALIDAÇÃO ROBUSTA: Verificar se é estado ou cidade brasileira conhecida
        if text_lower in self.brazilian_states or text_lower in self.brazilian_cities:
            return True
        
        # 5. VALIDAÇÃO COM CONTEXTO: Se tem indicadores de localização próximos, aceitar
        context_lower = context.lower() if context else ""
        has_location_indicator = any(indicator in context_lower for indicator in self.location_indicators)
        
        if has_location_indicator:
            # Tem contexto forte de localização (ex: "Rua X", "Cidade Y")
            # Validar se parece com nome de lugar
            if self._looks_like_place_name(text):
                return True
        
        # 6. VALIDAÇÃO COM PYCOUNTRY: Verificar se é país/subdivisão conhecida
        if PYCOUNTRY_AVAILABLE:
            try:
                # Verificar países
                try:
                    pycountry.countries.search_fuzzy(text)
                    return True
                except LookupError:
                    pass
                
                # Verificar subdivisões (estados, províncias)
                for subdivision in pycountry.subdivisions:
                    if text_lower in subdivision.name.lower():
                        return True
            except Exception:
                pass
        
        # 7. VALIDAÇÃO COM GEOPY (última tentativa - pode ser lenta)
        # DESABILITADO por padrão para evitar latência
        # if self.available and self.geolocator and has_location_indicator:
        #     try:
        #         location = self.geolocator.geocode(text, language='pt')
        #         return location is not None
        #     except (GeocoderTimedOut, GeocoderServiceError):
        #         pass
        
        # 8. FALLBACK: Rejeitar se não passou em nenhuma validação
        return False
    
    def _looks_like_place_name(self, text: str) -> bool:
        """Verifica se o texto parece com um nome de lugar válido"""
        # Nome de lugar geralmente:
        # - Começa com maiúscula
        # - Pode ter conectivos (de, da, do, dos, das)
        # - Não contém números (exceto "São Paulo 2" etc.)
        # - Não é palavra abstrata/técnica
        
        if not text[0].isupper():
            return False
        
        palavras = text.lower().split()
        
        # Rejeitar se tem muitas palavras abstratas
        abstract_count = sum(1 for p in palavras if p in self.never_locations)
        if abstract_count > len(palavras) * 0.5:  # Mais de 50% abstratas
            return False
        
        # Aceitar se parece com estrutura de lugar
        return True


class PersonLocationFilter:
    """
    Filtro inteligente que distingue entre PERSON e LOCATION
    Evita confusões comuns do spaCy
    """
    
    def __init__(self):
        self.name_validator = NameValidator()
        self.location_validator = LocationValidator()
    
    def should_keep_as_person(self, text: str, context: str = "", score: float = 0.0) -> bool:
        """
        Decide se uma detecção de PERSON deve ser mantida
        
        Args:
            text: Texto detectado
            context: Contexto ao redor
            score: Score de confiança do modelo
            
        Returns:
            True se deve manter como PERSON, False para rejeitar
        """
        # Usar validador robusto de nomes
        return self.name_validator.is_valid_name(text)
    
    def should_keep_as_location(self, text: str, context: str = "", score: float = 0.0) -> bool:
        """
        Decide se uma detecção de LOCATION deve ser mantida
        
        Args:
            text: Texto detectado
            context: Contexto ao redor
            score: Score de confiança do modelo
            
        Returns:
            True se deve manter como LOCATION, False para rejeitar
        """
        # Usar validador robusto de localizações
        return self.location_validator.is_valid_location(text, context)
