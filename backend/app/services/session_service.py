"""Criação, validação, renovação e revogação de sessões de login.

Modelo:
- O token da sessão é um valor aleatório de 256 bits (secrets.token_urlsafe(32)),
  enviado ao navegador num cookie HttpOnly.
- O banco guarda apenas SHA-256(token). Um hash rápido é adequado aqui porque o
  token tem entropia alta (não é uma senha escolhida por pessoas).
- A sessão expira por inatividade (idle) e por tempo máximo desde o login
  (absoluto). Cada uso renova a expiração por inatividade.
- O token CSRF é derivado do token da sessão via HMAC com a SECRET_KEY: fica
  vinculado à sessão e não precisa ser armazenado.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from dataclasses import dataclass
from datetime import timedelta

from flask import current_app
from sqlalchemy import delete, select

from app.extensions import db
from app.models import User, UserSession
from app.models.base import as_utc, utcnow

# Limite de tamanho do valor do cookie aceito (token_urlsafe(32) tem 43 caracteres).
_MAX_TOKEN_LENGTH = 128


@dataclass(frozen=True)
class ActiveSession:
    session: UserSession
    user: User
    token: str


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _idle_timeout() -> timedelta:
    return timedelta(minutes=current_app.config["SESSION_IDLE_TIMEOUT_MINUTES"])


def absolute_timeout() -> timedelta:
    return timedelta(hours=current_app.config["SESSION_ABSOLUTE_TIMEOUT_HOURS"])


def create_session(user: User) -> str:
    """Cria uma sessão para o usuário e devolve o token (só existe em memória e no cookie)."""
    token = secrets.token_urlsafe(32)
    now = utcnow()
    db.session.add(
        UserSession(
            user_id=user.id,
            token_hash=_hash_token(token),
            created_at=now,
            last_seen_at=now,
            expires_at=now + absolute_timeout(),
        )
    )
    return token


def get_active_session(token: str | None) -> ActiveSession | None:
    """Valida o token do cookie. Sessões expiradas são apagadas e retornam None."""
    if not token or len(token) > _MAX_TOKEN_LENGTH:
        return None

    session = db.session.execute(
        select(UserSession).where(UserSession.token_hash == _hash_token(token))
    ).scalar_one_or_none()
    if session is None:
        return None

    now = utcnow()
    last_seen = as_utc(session.last_seen_at)
    if now >= as_utc(session.expires_at) or now - last_seen >= _idle_timeout():
        db.session.delete(session)
        db.session.commit()
        return None

    # Renovação deslizante: registra o uso, no máximo a cada SESSION_TOUCH_INTERVAL_SECONDS.
    if (now - last_seen).total_seconds() >= current_app.config["SESSION_TOUCH_INTERVAL_SECONDS"]:
        session.last_seen_at = now
        db.session.commit()

    return ActiveSession(session=session, user=session.user, token=token)


def revoke_session(session: UserSession) -> None:
    db.session.delete(session)


def revoke_token(token: str | None) -> None:
    """Revoga a sessão do token informado, se existir (usado para evitar fixação de sessão)."""
    if token and len(token) <= _MAX_TOKEN_LENGTH:
        db.session.execute(delete(UserSession).where(UserSession.token_hash == _hash_token(token)))


def revoke_all_sessions(user_id: uuid.UUID) -> None:
    db.session.execute(delete(UserSession).where(UserSession.user_id == user_id))


def delete_expired_sessions() -> int:
    """Remove sessões vencidas (absolutas ou por inatividade). Retorna quantas foram apagadas."""
    now = utcnow()
    result = db.session.execute(
        delete(UserSession).where(
            (UserSession.expires_at <= now) | (UserSession.last_seen_at <= now - _idle_timeout())
        )
    )
    db.session.commit()
    return result.rowcount or 0


def csrf_token_for(session_token: str) -> str:
    key = current_app.config["SECRET_KEY"].encode("utf-8")
    return hmac.new(key, b"csrf:" + session_token.encode("utf-8"), hashlib.sha256).hexdigest()


def is_valid_csrf_token(session_token: str, provided: str | None) -> bool:
    if not provided:
        return False
    return hmac.compare_digest(csrf_token_for(session_token), provided)
