"""Validação de corpo de requisição com Pydantic.

Uso numa rota:
    data = parse_json_body(LoginRequest)

- Exige Content-Type application/json (415 caso contrário). Isso também obriga
  navegadores de outras origens a fazer preflight CORS, que é bloqueado.
- Rejeita JSON malformado (400) e campos inesperados (422, proteção contra
  mass assignment).
- Converte os erros do Pydantic em mensagens seguras, em português.
"""

from __future__ import annotations

from typing import TypeVar

from flask import request
from pydantic import BaseModel, ValidationError

from app.utils.errors import ApiError

T = TypeVar("T", bound=BaseModel)

_MESSAGES_BY_TYPE: dict[str, str] = {
    "missing": "Campo obrigatório.",
    "extra_forbidden": "Campo não permitido.",
    "string_type": "Deve ser um texto.",
    "string_too_short": "Texto muito curto.",
    "string_too_long": "Texto muito longo.",
    "value_error": "Valor inválido.",
    "model_type": "Formato inválido.",
}


def _field_name(location: tuple) -> str:
    return ".".join(str(part) for part in location) or "body"


def _public_message(error: dict) -> str:
    error_type = error.get("type", "")
    # Mensagens de validadores próprios (ValueError) já estão em português e são seguras.
    if error_type == "value_error":
        ctx_error = (error.get("ctx") or {}).get("error")
        if ctx_error is not None and getattr(ctx_error, "public", False):
            return str(ctx_error)
    if error_type in ("string_too_short", "string_too_long"):
        ctx = error.get("ctx") or {}
        if "min_length" in ctx:
            return f"Use pelo menos {ctx['min_length']} caracteres."
        if "max_length" in ctx:
            return f"Use no máximo {ctx['max_length']} caracteres."
    return _MESSAGES_BY_TYPE.get(error_type, "Valor inválido.")


def parse_json_body(model: type[T]) -> T:
    if not request.is_json:
        raise ApiError(415, message="Envie os dados em formato JSON.")

    payload = request.get_json(silent=True)
    if payload is None:
        raise ApiError(400, message="JSON inválido.")
    if not isinstance(payload, dict):
        raise ApiError(422, message="O corpo da requisição deve ser um objeto JSON.")

    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        fields = [
            {"field": _field_name(err.get("loc", ())), "message": _public_message(err)}
            for err in exc.errors(include_url=False, include_input=False)
        ]
        # Erros que envolvem mais de um campo (ex.: "senha igual ao e-mail") viram a mensagem principal.
        general = next((f["message"] for f in fields if f["field"] == "body"), None)
        raise ApiError(422, message=general or "Verifique os dados informados.", fields=fields) from None


class PublicValueError(ValueError):
    """ValueError cuja mensagem pode ser mostrada ao usuário."""

    public = True
