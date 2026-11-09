"""Proteção de rotas, cookie de sessão e verificação de CSRF."""

from __future__ import annotations

from functools import wraps
from typing import Callable

from flask import Flask, Response, current_app, g, request

from app.models import User
from app.services import session_service
from app.utils.errors import ApiError

CSRF_HEADER = "X-CSRF-Token"
UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


def get_session_token() -> str | None:
    return request.cookies.get(current_app.config["AUTH_COOKIE_NAME"])


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        current_app.config["AUTH_COOKIE_NAME"],
        token,
        max_age=int(session_service.absolute_timeout().total_seconds()),
        httponly=True,  # inacessível a JavaScript (mitiga roubo via XSS)
        secure=current_app.config["AUTH_COOKIE_SECURE"],  # só HTTPS em produção
        samesite=current_app.config["AUTH_COOKIE_SAMESITE"],  # não enviado em POSTs de outros sites
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        current_app.config["AUTH_COOKIE_NAME"],
        httponly=True,
        secure=current_app.config["AUTH_COOKIE_SECURE"],
        samesite=current_app.config["AUTH_COOKIE_SAMESITE"],
        path="/",
    )


def current_user() -> User:
    """Usuário autenticado da requisição atual (só dentro de rotas com @login_required)."""
    return g.current_user


def login_required(view: Callable) -> Callable:
    """Exige sessão válida. Em métodos que alteram dados, exige também o token CSRF.

    O usuário vem SEMPRE da sessão no servidor, nunca de um id enviado pelo cliente.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        active = session_service.get_active_session(get_session_token())
        if active is None:
            # Se havia um cookie (expirado ou revogado), ele é apagado na resposta.
            g.clear_session_cookie = get_session_token() is not None
            raise ApiError(401, "unauthenticated", "Sua sessão expirou ou você não está conectado.")

        if request.method in UNSAFE_METHODS and not session_service.is_valid_csrf_token(
            active.token, request.headers.get(CSRF_HEADER)
        ):
            raise ApiError(403, "csrf_failed", "Não foi possível validar a requisição. Recarregue a página.")

        g.current_user = active.user
        g.auth_session = active.session
        g.session_token = active.token
        return view(*args, **kwargs)

    return wrapper


def register_auth_hooks(app: Flask) -> None:
    @app.after_request
    def clear_stale_cookie(response: Response) -> Response:
        if g.get("clear_session_cookie"):
            clear_session_cookie(response)
        return response
