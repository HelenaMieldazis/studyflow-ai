"""Rotas de autenticação: /api/auth/*."""

from __future__ import annotations

from flask import Blueprint, g, jsonify

from app.extensions import db, limiter
from app.schemas.auth import LoginRequest, RegisterRequest
from app.schemas.serializers import serialize_user
from app.services import auth_service, session_service
from app.utils.auth import (
    clear_session_cookie,
    current_user,
    get_session_token,
    login_required,
    set_session_cookie,
)
from app.utils.rate_limit import account_key, limit_from_config
from app.utils.validation import parse_json_body

auth_bp = Blueprint("auth", __name__)


def _session_response(user, token: str, status: int = 200):
    """Resposta padrão de login: dados públicos do usuário + token CSRF. Define o cookie."""
    response = jsonify({"user": serialize_user(user), "csrf_token": session_service.csrf_token_for(token)})
    set_session_cookie(response, token)
    return response, status


@auth_bp.post("/register")
@limiter.limit(limit_from_config("RATE_LIMIT_REGISTER_IP"))
def register():
    data = parse_json_body(RegisterRequest)
    user, token = auth_service.register(data.email, data.password, data.display_name)
    return _session_response(user, token, 201)


@auth_bp.post("/login")
@limiter.limit(limit_from_config("RATE_LIMIT_LOGIN_IP"))
@limiter.limit(limit_from_config("RATE_LIMIT_LOGIN_ACCOUNT"), key_func=account_key)
def login():
    data = parse_json_body(LoginRequest)
    user, token = auth_service.login(data.email, data.password, previous_token=get_session_token())
    return _session_response(user, token)


@auth_bp.post("/logout")
@login_required
def logout():
    session_service.revoke_session(g.auth_session)
    db.session.commit()
    response = jsonify({"message": "Sessão encerrada."})
    clear_session_cookie(response)
    return response


@auth_bp.get("/me")
@login_required
def me():
    """Retorna o usuário da sessão atual e o token CSRF (usado ao recarregar a página)."""
    return jsonify({"user": serialize_user(current_user()), "csrf_token": session_service.csrf_token_for(g.session_token)})
