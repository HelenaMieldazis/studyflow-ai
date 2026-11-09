"""Regras de negócio de contas: cadastro, login, perfil, senha e exclusão."""

from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models import User
from app.models.base import utcnow
from app.services import password_service, session_service
from app.utils.errors import ApiError

logger = logging.getLogger(__name__)

INVALID_CREDENTIALS = ApiError(401, "invalid_credentials", "E-mail ou senha incorretos.")


def _email_unavailable() -> ApiError:
    return ApiError(409, "email_unavailable", "Não foi possível usar este e-mail. Verifique-o ou faça login.")


def _find_by_email(email: str) -> User | None:
    # Consulta parametrizada pelo SQLAlchemy: o valor nunca é concatenado ao SQL.
    return db.session.execute(select(User).where(User.email == email)).scalar_one_or_none()


def register(email: str, password: str, display_name: str) -> tuple[User, str]:
    """Cria a conta e já inicia uma sessão. Retorna (usuário, token da sessão)."""
    if _find_by_email(email) is not None:
        raise _email_unavailable()

    user = User(email=email, display_name=display_name, password_hash=password_service.hash_password(password))
    db.session.add(user)
    try:
        db.session.flush()  # obtém o id e detecta e-mail duplicado (cadastro simultâneo)
    except IntegrityError:
        db.session.rollback()
        raise _email_unavailable() from None

    token = session_service.create_session(user)
    db.session.commit()
    logger.info("auth.register user_id=%s", user.id)
    return user, token


def login(email: str, password: str, previous_token: str | None = None) -> tuple[User, str]:
    """Autentica e cria uma nova sessão. A mesma resposta para e-mail inexistente e senha errada."""
    user = _find_by_email(email)
    # Sempre executa a verificação do hash (mesmo sem usuário) para igualar o tempo de resposta.
    if not password_service.verify_password(user.password_hash if user else None, password) or user is None:
        logger.info("auth.login_failed")
        raise INVALID_CREDENTIALS

    if password_service.needs_rehash(user.password_hash):
        user.password_hash = password_service.hash_password(password)

    # Descarta a sessão anterior deste navegador (evita fixação de sessão).
    session_service.revoke_token(previous_token)
    token = session_service.create_session(user)
    db.session.commit()
    logger.info("auth.login_succeeded user_id=%s", user.id)
    return user, token


def _require_password(user: User, password: str) -> None:
    if not password_service.verify_password(user.password_hash, password):
        raise ApiError(403, "invalid_password", "Senha atual incorreta.")


def update_profile(user: User, display_name: str | None, email: str | None, current_password: str | None) -> User:
    if email is not None and email != user.email:
        _require_password(user, current_password or "")
        if _find_by_email(email) is not None:
            raise _email_unavailable()
        user.email = email
    if display_name is not None:
        user.display_name = display_name
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise _email_unavailable() from None
    logger.info("account.profile_updated user_id=%s", user.id)
    return user


def change_password(user: User, current_password: str, new_password: str) -> str:
    """Troca a senha, encerra TODAS as sessões (inclusive em outros dispositivos) e abre uma nova."""
    _require_password(user, current_password)
    user.password_hash = password_service.hash_password(new_password)
    user.password_changed_at = utcnow()
    session_service.revoke_all_sessions(user.id)
    token = session_service.create_session(user)
    db.session.commit()
    logger.info("account.password_changed user_id=%s", user.id)
    return token


def delete_account(user: User, password: str) -> None:
    """Exclui a conta. As sessões (e, nas próximas etapas, todos os dados) são apagadas em cascata."""
    _require_password(user, password)
    user_id = user.id
    db.session.delete(user)
    db.session.commit()
    logger.info("account.deleted user_id=%s", user_id)
