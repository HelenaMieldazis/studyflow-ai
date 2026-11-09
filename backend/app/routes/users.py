"""Rotas da conta do usuário autenticado: /api/users/me*.

Não existe rota com id de usuário na URL: cada pessoa só consegue ler e alterar
a própria conta, identificada pela sessão no servidor (proteção contra IDOR).
"""

from __future__ import annotations

from flask import Blueprint, jsonify

from app.extensions import limiter
from app.schemas.auth import ChangePasswordRequest, DeleteAccountRequest, UpdateProfileRequest
from app.schemas.serializers import serialize_user
from app.services import auth_service, session_service
from app.utils.auth import clear_session_cookie, current_user, login_required, set_session_cookie
from app.utils.rate_limit import limit_from_config, session_key
from app.utils.validation import parse_json_body

users_bp = Blueprint("users", __name__)


@users_bp.get("/me")
@login_required
def get_profile():
    return jsonify({"user": serialize_user(current_user())})


@users_bp.patch("/me")
@login_required
def update_profile():
    data = parse_json_body(UpdateProfileRequest)
    user = auth_service.update_profile(current_user(), data.display_name, data.email, data.current_password)
    return jsonify({"user": serialize_user(user)})


@users_bp.put("/me/password")
@limiter.limit(limit_from_config("RATE_LIMIT_SENSITIVE_USER"), key_func=session_key)
@login_required
def change_password():
    data = parse_json_body(ChangePasswordRequest)
    user = current_user()
    token = auth_service.change_password(user, data.current_password, data.new_password)
    # A sessão antiga foi revogada; o navegador recebe um novo cookie e um novo token CSRF.
    response = jsonify(
        {
            "user": serialize_user(user),
            "csrf_token": session_service.csrf_token_for(token),
            "message": "Senha alterada. As outras sessões foram encerradas.",
        }
    )
    set_session_cookie(response, token)
    return response


@users_bp.delete("/me")
@limiter.limit(limit_from_config("RATE_LIMIT_SENSITIVE_USER"), key_func=session_key)
@login_required
def delete_account():
    data = parse_json_body(DeleteAccountRequest)
    auth_service.delete_account(current_user(), data.password)
    response = jsonify({"message": "Conta excluída."})
    clear_session_cookie(response)
    return response
