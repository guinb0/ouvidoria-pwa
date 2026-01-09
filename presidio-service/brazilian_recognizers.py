"""
Reconhecedores customizados brasileiros para Microsoft Presidio
Aumenta Recall para CPF, RG, CEP e telefones brasileiros
"""
from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer


class BrazilCpfRecognizer(PatternRecognizer):
    """
    Reconhece CPF brasileiro nos formatos:
    - 000.000.000-00
    - 00000000000
    """
    PATTERNS = [
        Pattern(
            name="cpf_with_dots",
            regex=r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
            score=0.95,
        ),
        Pattern(
            name="cpf_without_dots",
            regex=r"\b\d{11}\b",
            score=0.7,  # Score menor pois pode ser outro número
        ),
    ]

    CONTEXT = ["cpf", "cadastro", "documento", "identificação"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "pt",
        supported_entity: str = "BR_CPF",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )


class BrazilRgRecognizer(PatternRecognizer):
    """
    Reconhece RG brasileiro nos formatos:
    - 00.000.000-0
    - 000000000
    """
    PATTERNS = [
        Pattern(
            name="rg_with_dots",
            regex=r"\b\d{2}\.\d{3}\.\d{3}-\d{1}\b",
            score=0.9,
        ),
        Pattern(
            name="rg_without_dots",
            regex=r"\b[0-9]{8,9}\b",
            score=0.6,
        ),
    ]

    CONTEXT = ["rg", "identidade", "carteira", "documento"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "pt",
        supported_entity: str = "BR_RG",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )


class BrazilCepRecognizer(PatternRecognizer):
    """
    Reconhece CEP brasileiro: 00000-000 ou 00000000
    """
    PATTERNS = [
        Pattern(
            name="cep_with_dash",
            regex=r"\b\d{5}-\d{3}\b",
            score=0.95,
        ),
        Pattern(
            name="cep_without_dash",
            regex=r"\b\d{8}\b",
            score=0.6,
        ),
    ]

    CONTEXT = ["cep", "código postal", "endereço"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "pt",
        supported_entity: str = "BR_CEP",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )


class BrazilPhoneRecognizer(PatternRecognizer):
    """
    Reconhece telefones brasileiros:
    - (00) 0000-0000
    - (00) 00000-0000
    - 00 0000-0000
    - 00 00000-0000
    """
    PATTERNS = [
        Pattern(
            name="phone_with_parentheses",
            regex=r"\(\d{2}\)\s?\d{4,5}-\d{4}",
            score=0.9,
        ),
        Pattern(
            name="phone_without_parentheses",
            regex=r"\b\d{2}\s?\d{4,5}-\d{4}\b",
            score=0.85,
        ),
    ]

    CONTEXT = ["telefone", "celular", "contato", "fone", "tel"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "pt",
        supported_entity: str = "BR_PHONE",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )
