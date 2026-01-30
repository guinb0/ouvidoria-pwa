"""
Reconhecedor customizado de nomes brasileiros usando listas de nomes comuns
"""
import re
from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer

class BrazilianNameRecognizer(PatternRecognizer):
    """
    Detecta nomes próprios brasileiros usando lista de nomes e sobrenomes comuns
    """
    
    # Lista de primeiros nomes brasileiros comuns (masculinos e femininos)
    FIRST_NAMES = {
        # Masculinos
        "joão", "jose", "antonio", "francisco", "carlos", "paulo", "pedro", "lucas", "matheus", 
        "gabriel", "rafael", "felipe", "bruno", "gustavo", "leonardo", "rodrigo", "daniel", 
        "marcelo", "fernando", "ricardo", "thiago", "julio", "cesar", "diego", "vitor", 
        "andre", "jorge", "eduardo", "marcos", "lucio", "lúcio", "miguel", "henrique", "fabio",
        "roberto", "sergio", "alexandre", "joaquim", "walter", "edson", "pablo", "vinicius",
        "joão", "júlio",
        # Femininos
        "maria", "ana", "francisca", "antonia", "adriana", "juliana", "fernanda", "patricia",
        "aline", "mariana", "amanda", "jessica", "camila", "leticia", "raquel", "monica",
        "sandra", "carolina", "beatriz", "larissa", "vanessa", "simone", "claudia", "silvia",
        "cristina", "julia", "isabela", "gabriela", "debora", "renata", "tatiana", "paula",
        "fatima", "fátima", "rita", "conceicao", "conceição", "aparecida", "lucia", "lúcia", 
        "ruth", "aura", "cassandra",
    }
    
    # Lista completa de sobrenomes brasileiros (Top 200+ mais comuns segundo IBGE)
    LAST_NAMES = {
        # Top 20 (> 1% da população)
        "silva", "santos", "oliveira", "souza", "sousa", "rodrigues", "ferreira", "alves",
        "pereira", "lima", "gomes", "costa", "ribeiro", "martins", "carvalho", "almeida",
        "lopes", "soares", "fernandes", "vieira",
        # Top 21-50
        "barbosa", "rocha", "dias", "nascimento", "araujo", "araújo", "melo", "campos",
        "cardoso", "reis", "freitas", "monteiro", "mendes", "castro", "cavalcanti", "andrade",
        "tavares", "sampaio", "braga", "cruz", "simoes", "simões", "mota", "franco",
        "garcia", "moreira", "miranda", "pinto", "guimaraes", "guimarães",
        # Top 51-100
        "neves", "correa", "corrêa", "teixeira", "pires", "rosa", "nunes", "borges",
        "camargo", "valle", "marques", "vasconcelos", "farias", "ramos", "bezerra",
        "cunha", "santiago", "aguiar", "rezende", "moura", "nogueira", "machado",
        "sales", "azevedo", "duarte", "macedo", "vargas", "jesus", "paiva", "silva",
        "magalhaes", "magalhães", "medeiros", "coelho", "xavier", "batista", "lourenco",
        "lourenço", "aragao", "aragão", "siqueira", "fonseca", "goncalves", "gonçalves",
        # Top 101-150
        "leite", "brito", "amaral", "bueno", "barros", "dantas", "godoy", "barreto",
        "pessoa", "matos", "correa", "fogaca", "fogaça", "ramalho", "delgado", "santana",
        "bastos", "viana", "Toledo", "toledo", "avila", "ávila", "Porto", "porto",
        "lacerda", "salgado", "leal", "menezes", "moraes", "morais", "figueiredo",
        "mesquita", "rangel", "pessoa", "queiroz", "novais", "vaz", "pacheco",
        "furtado", "cardozo", "muniz", "fontes", "rossi", "goulart", "ventura",
        # Top 151-200 e outros muito comuns
        "ferreira", "brandao", "brandão", "medina", "vidal", "nery", "coutinho",
        "domingues", "lemos", "esteves", "serra", "gonzaga", "amaral", "assuncao",
        "assunção", "silveira", "vilela", "fagundes", "pacheco", "guedes", "arruda",
        "caetano", "carneiro", "bento", "amorim", "guerra", "escobar", "jardim",
        "sequeira", "vale", "felix", "félix", "maia", "lara", "padilha", "torres",
        "serrano", "neto", "filho", "junior", "sobrinho", "segundo", "terceiro",
        "villar", "sales", "bispo", "Goes", "goes", "peixoto", "cabral", "camara",
        "câmara", "vasques", "varela", "espinosa", "horta", "crespo", "bessa",
        "cortes", "cortês", "seabra", "lobato", "portela", "afonso", "saraiva",
        "brandao", "cordeiro", "maia", "barroso", "guerreiro", "nobre", "galvao",
        "galvão", "prado", "pestana", "paredes", "trindade", "bernardes", "gama"
    }
    
    SUPPORTED_ENTITY = "PERSON"
    
    def __init__(self):
        patterns = []
        
        # Padrão 0: Nome único comum (ex: Thiago, Gustavo, Rafael) - com contexto forte
        # Apenas nomes muito comuns em contextos claros
        common_single_names = [
            "thiago", "gustavo", "rafael", "bruno", "lucas", "gabriel", "matheus", "felipe",
            "leonardo", "rodrigo", "diego", "fernando", "ricardo", "marcelo", "daniel",
            "eduardo", "marcos", "vinicius", "carolina", "beatriz", "larissa", "vanessa",
            "juliana", "fernanda", "amanda", "jessica", "camila", "mariana", "gabriela"
        ]
        single_names_pattern = "|".join([f"{name.capitalize()}" for name in common_single_names])
        patterns.append(Pattern(
            name="common_single_name",
            regex=rf"\b({single_names_pattern})\b",
            score=0.50  # Score alto para nomes únicos comuns
        ))
        
        # Padrão 1: Nome + Sobrenome (ex: João Silva, Maria Santos)
        # Suporta quebras de linha entre nome e sobrenome
        first_names_pattern = "|".join(self.FIRST_NAMES)
        last_names_pattern = "|".join(self.LAST_NAMES)
        
        patterns.append(Pattern(
            name="first_last_name",
            regex=rf"\b([A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][a-zàáâãçéêíóôõú]+)[\s\n]+([A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][a-zàáâãçéêíóôõú]+)\b",
            score=0.55  # Score médio-alto, validação determina aceite final
        ))
        
        # Padrão 2: Nome composto (ex: João Paulo, Maria Clara, Ana Cristina)
        # Suporta quebras de linha
        patterns.append(Pattern(
            name="compound_first_name",
            regex=rf"\b([A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][a-zàáâãçéêíóôõú]+)[\s\n]+([A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][a-zàáâãçéêíóôõú]+)[\s\n]+([A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][a-zàáâãçéêíóôõú]+)\b",
            score=0.60  # Score ligeiramente maior para nomes compostos
        ))
        
        # Padrão 3: Nome completo com conectivos (ex: João da Silva, Maria de Souza)
        # Suporta quebras de linha e múltiplos conectores
        patterns.append(Pattern(
            name="full_name_with_connectors",
            regex=rf"\b([A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][a-zàáâãçéêíóôõú]+)([\s\n]+(da|das|de|do|dos|e)[\s\n]+[A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][a-zàáâãçéêíóôõú]+)+\b",
            score=0.70  # Score alto para nomes com conectores
        ))
        
        # Padrão 4: Nomes com 4-6 palavras (nomes muito longos)
        patterns.append(Pattern(
            name="very_long_names",
            regex=rf"\b([A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][a-zàáâãçéêíóôõú]+[\s\n]+){{3,5}}([A-ZÀÁÂÃÇÉÊÍÓÔÕÚ][a-zàáâãçéêíóôõú]+)\b",
            score=0.65
        ))
        
        super().__init__(
            supported_entity=self.SUPPORTED_ENTITY,
            patterns=patterns,
            supported_language="pt",
            context=["sr", "sra", "dr", "dra", "prof", "nome", "senhor", "senhora", 
                     "atenciosamente", "cordialmente", "att", "grata", "grato",
                     "chamo", "sou", "assina", "assinado", "responsavel", "responsável"]
        )
    
    def validate_result(self, pattern_text: str) -> Optional[bool]:
        """
        Valida se o texto detectado é realmente um nome brasileiro
        """
        # Normalizar para lowercase
        text_lower = pattern_text.lower()
        
        # Dividir em palavras
        words = [w for w in re.split(r'\s+', text_lower) if w not in ['da', 'das', 'de', 'do', 'dos', 'e']]
        
        if not words:
            return False
        
        # Verificar se pelo menos uma palavra é nome comum OU sobrenome comum
        has_first_name = any(w in self.FIRST_NAMES for w in words)
        has_last_name = any(w in self.LAST_NAMES for w in words)
        
        # Aceitar se tem pelo menos um nome ou sobrenome comum
        if has_first_name or has_last_name:
            return True
        
        # Rejeitar nomes muito curtos sem match
        if len(words) == 1 and len(words[0]) < 4:
            return False
        
        return None  # Deixar outros validadores decidirem
