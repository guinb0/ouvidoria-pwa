"""
Reconhecedores customizados brasileiros para Microsoft Presidio
Aumenta Recall para CPF, RG, CEP e telefones brasileiros
"""
from typing import List, Optional
from presidio_analyzer import Pattern, PatternRecognizer

try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False
try:
    from email_validator import validate_email, EmailNotValidError
    EMAIL_VALIDATOR_AVAILABLE = True
except ImportError:
    EMAIL_VALIDATOR_AVAILABLE = False


class BrazilCpfRecognizer(PatternRecognizer):
    """
    Reconhece CPF brasileiro nos formatos:
    - 000.000.000-00
    - 00000000000
    Com validacao de contexto para evitar falsos positivos
    """
    PATTERNS = [
        Pattern(
            name="cpf_with_dots",
            regex=r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b",
            score=0.95,
        ),
        Pattern(
            name="cpf_without_dots",
            regex=r"(?<!\d)\d{11}(?!\d)",
            score=0.5,
        ),
    ]

    CONTEXT = ["cpf", "cadastro", "documento", "identificacao", "contribuinte", "titular", "portador"]

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
            regex=r"\b[0-9]{7,9}\b",
            score=0.4,
        ),
    ]

    CONTEXT = ["rg", "identidade", "carteira", "documento", "portador", "registro"]

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
    - 0000000000 (10 digitos)
    - 00000000000 (11 digitos)
    """
    PATTERNS = [
        Pattern(
            name="phone_with_parentheses",
            regex=r"\(\d{2}\)\s?\d{4,5}-\d{4}",
            score=0.95,
        ),
        Pattern(
            name="phone_without_parentheses",
            regex=r"\b\d{2}\s?\d{4,5}-\d{4}\b",
            score=0.9,
        ),
        Pattern(
            name="phone_only_digits_11",
            regex=r"\b\d{11}\b",
            score=0.45,
        ),
        Pattern(
            name="phone_only_digits_10",
            regex=r"\b\d{10}\b",
            score=0.4,
        ),
    ]

    CONTEXT = ["telefone", "celular", "contato", "fone", "tel", "whatsapp", "zap", "ligar", "falar"]

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


class BrazilEmailRecognizer(PatternRecognizer):
    """
    Reconhece emails com validação real usando email-validator
    Melhora detecção e reduz falsos positivos
    """
    PATTERNS = [
        Pattern(
            name="email_pattern",
            regex=r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            score=0.9,
        ),
    ]

    CONTEXT = ["email", "e-mail", "contato", "@"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "pt",
        supported_entity: str = "EMAIL_ADDRESS",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

    def validate_result(self, pattern_text: str) -> bool:
        """Valida se o email é válido usando email-validator"""
        if not EMAIL_VALIDATOR_AVAILABLE:
            return True
        try:
            validate_email(pattern_text, check_deliverability=False)
            return True
        except EmailNotValidError:
            return False
        except Exception:
            return True


class BrazilCnpjRecognizer(PatternRecognizer):
    """
    Reconhece CNPJ brasileiro nos formatos:
    - 00.000.000/0000-00
    - 00000000000000
    """
    PATTERNS = [
        Pattern(
            name="cnpj_with_formatting",
            regex=r"\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b",
            score=0.95,
        ),
        Pattern(
            name="cnpj_without_formatting",
            regex=r"(?<!\d)\d{14}(?!\d)",
            score=0.85,
        ),
    ]

    CONTEXT = ["cnpj", "empresa", "razao social", "cadastro nacional"]

    def __init__(
        self,
        patterns: Optional[List[Pattern]] = None,
        context: Optional[List[str]] = None,
        supported_language: str = "pt",
        supported_entity: str = "BR_CNPJ",
    ):
        patterns = patterns if patterns else self.PATTERNS
        context = context if context else self.CONTEXT
        super().__init__(
            supported_entity=supported_entity,
            patterns=patterns,
            context=context,
            supported_language=supported_language,
        )

