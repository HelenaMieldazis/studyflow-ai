"""Tipos de campo reutilizáveis com normalização e validação."""

from __future__ import annotations

import unicodedata
from typing import Annotated

from email_validator import EmailNotValidError, validate_email
from pydantic import AfterValidator, BeforeValidator, Field

from app.models.user import DISPLAY_NAME_MAX_LENGTH, EMAIL_MAX_LENGTH
from app.utils.validation import PublicValueError

PASSWORD_MIN_LENGTH = 12
# Limite superior evita uso de senhas gigantes para sobrecarregar o hash (DoS).
PASSWORD_MAX_LENGTH = 128

# Caracteres de controle de direção de texto (podem disfarçar o conteúdo exibido).
_BIDI_CONTROLS = {chr(c) for c in (*range(0x202A, 0x202F), *range(0x2066, 0x206A))}


def _strip_if_str(value: object) -> object:
    return value.strip() if isinstance(value, str) else value


def _normalize_email(value: str) -> str:
    try:
        result = validate_email(value, check_deliverability=False)
    except EmailNotValidError:
        raise PublicValueError("Informe um e-mail válido.") from None
    return result.normalized.lower()


def _clean_display_name(value: str) -> str:
    value = unicodedata.normalize("NFC", value)
    if any(unicodedata.category(ch) == "Cc" or ch in _BIDI_CONTROLS for ch in value):
        raise PublicValueError("O nome contém caracteres não permitidos.")
    if not value:
        raise PublicValueError("Informe um nome.")
    return value


def _check_password(value: str) -> str:
    if value.strip() == "":
        raise PublicValueError("A senha não pode ser composta apenas por espaços.")
    return value


Email = Annotated[
    str,
    BeforeValidator(_strip_if_str),
    Field(min_length=3, max_length=EMAIL_MAX_LENGTH),
    AfterValidator(_normalize_email),
]

DisplayName = Annotated[
    str,
    BeforeValidator(_strip_if_str),
    Field(min_length=1, max_length=DISPLAY_NAME_MAX_LENGTH),
    AfterValidator(_clean_display_name),
]

# Senha nova: aplica a política. Espaços são permitidos (frases-senha) e NÃO são removidos.
NewPassword = Annotated[
    str,
    Field(min_length=PASSWORD_MIN_LENGTH, max_length=PASSWORD_MAX_LENGTH),
    AfterValidator(_check_password),
]

# Senha atual/de login: só limites de tamanho (a política pode ter mudado desde o cadastro).
CurrentPassword = Annotated[str, Field(min_length=1, max_length=PASSWORD_MAX_LENGTH)]
