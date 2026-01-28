"""
Pré-processador de texto para melhorar detecção de nomes
Foca em normalização estrutural, não em blacklists
"""
import re
from typing import List, Tuple

class TextPreprocessor:
    """
    Normaliza texto para melhorar NER, mantendo mapeamento de posições originais
    """
    
    def __init__(self):
        # Padrões de tratamento que indicam nome a seguir
        self.tratamentos = [
            r'\bSr\.\s*',
            r'\bSra\.\s*',
            r'\bDr\.\s*',
            r'\bDra\.\s*',
            r'\bProf\.\s*',
            r'\bAt\.te\s*',
            r'\bAtt\s*',
            r'\bAtenciosamente\s*',
        ]
        
        # Padrões de saudação que precedem nomes
        self.saudacoes = [
            r'\bOlá\s+',
            r'\bBom\s+dia\s+',
            r'\bBoa\s+tarde\s+',
            r'\bBoa\s+noite\s+',
            r'\bMe\s+chamo\s+',
            r'\bMeu\s+nome\s+é\s+',
            r'\bSou\s+',
        ]
    
    def normalizar_quebras_em_nomes(self, texto: str) -> Tuple[str, List[Tuple[int, int, str]]]:
        """
        Detecta e normaliza quebras de linha que fragmentam nomes próprios
        Retorna: (texto_normalizado, mapeamento_de_mudancas)
        """
        linhas = texto.split('\n')
        texto_normalizado = []
        mudancas = []
        posicao_atual = 0
        
        i = 0
        while i < len(linhas):
            linha = linhas[i]
            
            # Se linha termina com padrão de nome incompleto e próxima linha começa com continuação
            if i < len(linhas) - 1:
                proxima = linhas[i + 1].strip()
                
                # Padrão: linha termina com nome/sobrenome E próxima linha tem conectores ou sobrenome
                if (self._linha_termina_com_nome(linha) and 
                    self._linha_e_continuacao_nome(proxima)):
                    
                    # Juntar as linhas com espaço simples
                    linha_completa = linha.rstrip() + ' ' + proxima
                    texto_normalizado.append(linha_completa)
                    
                    # Registrar mudança
                    mudancas.append((
                        posicao_atual,
                        posicao_atual + len(linha) + 1 + len(proxima),
                        f"Juntou '{linha.strip()[-30:]}' com '{proxima[:30]}'"
                    ))
                    
                    posicao_atual += len(linha_completa) + 1
                    i += 2  # Pular próxima linha já processada
                    continue
            
            texto_normalizado.append(linha)
            posicao_atual += len(linha) + 1
            i += 1
        
        return '\n'.join(texto_normalizado), mudancas
    
    def _linha_termina_com_nome(self, linha: str) -> bool:
        """Verifica se linha termina com padrão de nome (palavra capitalizada)"""
        palavras = linha.strip().split()
        if not palavras:
            return False
        
        ultima = palavras[-1]
        # Nome típico: começa com maiúscula, tem pelo menos 3 letras
        return (len(ultima) >= 3 and 
                ultima[0].isupper() and 
                ultima.isalpha() and
                not self._e_palavra_comum(ultima))
    
    def _linha_e_continuacao_nome(self, linha: str) -> bool:
        """Verifica se linha é continuação de nome (conectores ou sobrenome)"""
        linha = linha.strip()
        if not linha:
            return False
        
        palavras = linha.split()
        primeira = palavras[0]
        
        # Conectores de nome (da, de, dos, etc)
        conectores = {'da', 'de', 'do', 'dos', 'das', 'e'}
        if primeira.lower() in conectores:
            return True
        
        # Sobrenome (palavra capitalizada, 3+ letras)
        return (len(primeira) >= 3 and 
                primeira[0].isupper() and 
                primeira.isalpha() and
                not self._e_palavra_comum(primeira))
    
    def _e_palavra_comum(self, palavra: str) -> bool:
        """Verifica se é palavra comum (não nome)"""
        comuns = {
            'Assim', 'Dessa', 'Desta', 'Deste', 'Diante', 'Essa', 'Foram',
            'Isto', 'Neste', 'Nossa', 'Porem', 'Qualquer', 'Unidade',
            'Além', 'Bom', 'Boa', 'Olá', 'Me', 'Eu', 'Ele', 'Ela'
        }
        return palavra in comuns
    
    def adicionar_marcadores_contextuais(self, texto: str) -> str:
        """
        Adiciona marcadores invisíveis para ajudar NER a identificar contexto
        Ex: "At.te João" -> "At.te [PESSOA_ESPERADA]João"
        """
        texto_marcado = texto
        
        # Marcar nomes após tratamentos
        for padrao in self.tratamentos:
            # Substituir "Sr. NOME" por "Sr. [CTX:TRATAMENTO]NOME"
            texto_marcado = re.sub(
                padrao + r'(\w+)',
                lambda m: m.group(0).replace(m.group(1), f'[CTX:NOME]{m.group(1)}'),
                texto_marcado,
                flags=re.IGNORECASE
            )
        
        # Marcar nomes após saudações
        for padrao in self.saudacoes:
            texto_marcado = re.sub(
                padrao + r'(\w+)',
                lambda m: m.group(0).replace(m.group(1), f'[CTX:NOME]{m.group(1)}'),
                texto_marcado,
                flags=re.IGNORECASE
            )
        
        return texto_marcado
    
    def extrair_nomes_contextuais(self, texto: str) -> List[Tuple[int, int, str]]:
        """
        Extrai nomes baseado em contexto forte (tratamentos, saudações)
        Retorna: [(start, end, nome), ...]
        """
        nomes_contextuais = []
        
        # Padrão: Tratamento + Nome(s)
        # Ex: "Sr. Antonio Vasconcelos" ou "At.te Gustavo"
        padrao_tratamento = r'\b(Sr\.|Sra\.|Dr\.|Dra\.|Prof\.|At\.te|Att)\s+([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+(?:\s+[A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+)*)'
        
        for match in re.finditer(padrao_tratamento, texto):
            nome = match.group(2)
            # Validar que não é palavra comum
            if not self._e_palavra_comum(nome.split()[0]):
                nomes_contextuais.append((
                    match.start(2),
                    match.end(2),
                    nome
                ))
        
        # Padrão: Saudação + Nome
        # Ex: "Me chamo Thiago" ou "Olá, Gustavo"
        padrao_saudacao = r'\b(Me\s+chamo|Meu\s+nome\s+é|Sou|Olá,?)\s+([A-ZÀÁÂÃÉÊÍÓÔÕÚÇ][a-zàáâãéêíóôõúç]+)'
        
        for match in re.finditer(padrao_saudacao, texto, re.IGNORECASE):
            nome = match.group(2)
            if not self._e_palavra_comum(nome):
                nomes_contextuais.append((
                    match.start(2),
                    match.end(2),
                    nome
                ))
        
        return nomes_contextuais
    
    def processar(self, texto: str) -> Tuple[str, List[Tuple[int, int, str]]]:
        """
        Pipeline completo de pré-processamento
        Retorna: (texto_processado, nomes_contextuais_encontrados)
        """
        # 1. Normalizar quebras de linha em nomes
        texto_normalizado, mudancas = self.normalizar_quebras_em_nomes(texto)
        
        # 2. Extrair nomes baseados em contexto forte
        nomes_contextuais = self.extrair_nomes_contextuais(texto_normalizado)
        
        return texto_normalizado, nomes_contextuais
