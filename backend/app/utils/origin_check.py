"""Verificação de origem para requisições que alteram dados.

Navegadores sempre enviam o header Origin em requisições POST/PUT/PATCH/DELETE.
Se ele estiver presente e não for uma origem autorizada, a requisição é
recusada antes de chegar à rota. Isso protege inclusive as rotas que ainda não
têm sessão (cadastro e login) contra CSRF de login.

Clientes que não são navegadores (curl, testes) não enviam Origin e não são
afetados; eles não carregam cookies da vítima, então não representam risco de CSRF.
"""

from __future__ import annotations

from flask import Flask, request

from app.utils.auth import UNSAFE_METHODS
from app.utils.errors import ApiError


def _allowed_origins(app: Flask) -> set[str]:
    allowed = {origin.rstrip("/") for origin in app.config["CORS_ORIGINS"]}
    # A própria origem da API (quando frontend e API são servidos no mesmo domínio).
    allowed.add(request.host_url.rstrip("/"))
    return allowed


def register_origin_check(app: Flask) -> None:
    @app.before_request
    def verify_origin():
        if request.method not in UNSAFE_METHODS or not request.path.startswith("/api/"):
            return None
        origin = request.headers.get("Origin")
        if origin is None:
            return None
        if origin == "null" or origin.rstrip("/") not in _allowed_origins(app):
            raise ApiError(403, "origin_not_allowed", "Origem da requisição não autorizada.")
        return None
