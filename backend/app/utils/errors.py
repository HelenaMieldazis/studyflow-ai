"""Tratamento centralizado de erros.

Toda resposta de erro segue o formato:
    {"error": {"code": "not_found", "message": "Recurso não encontrado."}}

Nunca expõe stack traces, mensagens de exceção ou detalhes internos ao cliente.
"""

import logging

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)

# Mensagens públicas, em português, por status HTTP.
_PUBLIC_MESSAGES: dict[int, tuple[str, str]] = {
    400: ("bad_request", "Requisição inválida."),
    401: ("unauthorized", "Autenticação necessária."),
    403: ("forbidden", "Acesso negado."),
    404: ("not_found", "Recurso não encontrado."),
    405: ("method_not_allowed", "Método não permitido para este recurso."),
    409: ("conflict", "Conflito com o estado atual do recurso."),
    413: ("payload_too_large", "A requisição excede o tamanho máximo permitido."),
    415: ("unsupported_media_type", "Tipo de conteúdo não suportado."),
    422: ("unprocessable_entity", "Os dados enviados são inválidos."),
    429: ("too_many_requests", "Muitas requisições. Tente novamente em instantes."),
    500: ("internal_error", "Erro interno. Tente novamente mais tarde."),
    503: ("service_unavailable", "Serviço temporariamente indisponível."),
}


class ApiError(Exception):
    """Erro de negócio com resposta pública controlada.

    Use para erros esperados (credenciais inválidas, conflito, validação). A
    mensagem é exibida ao usuário, então nunca inclua detalhes internos nela.
    """

    def __init__(
        self,
        status: int,
        code: str | None = None,
        message: str | None = None,
        fields: list[dict[str, str]] | None = None,
    ) -> None:
        super().__init__(code or str(status))
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields


def error_response(
    status: int,
    code: str | None = None,
    message: str | None = None,
    fields: list[dict[str, str]] | None = None,
):
    default_code, default_message = _PUBLIC_MESSAGES.get(status, ("error", "Erro."))
    error: dict = {"code": code or default_code, "message": message or default_message}
    if fields:
        error["fields"] = fields
    return jsonify({"error": error}), status


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ApiError)
    def handle_api_error(exc: ApiError):
        return error_response(exc.status, exc.code, exc.message, exc.fields)

    @app.errorhandler(HTTPException)
    def handle_http_exception(exc: HTTPException):
        status = exc.code or 500
        response, status = error_response(status)
        # Preserva headers relevantes (ex.: "Allow" em 405).
        for header, value in exc.get_headers():
            if header.lower() != "content-type":
                response.headers[header] = value
        return response, status

    @app.errorhandler(Exception)
    def handle_unexpected_exception(exc: Exception):
        # logger.exception registra o stack trace somente no servidor.
        logger.exception("Erro não tratado: %s", type(exc).__name__)
        return error_response(500)
