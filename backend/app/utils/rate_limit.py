"""Chaves e limites usados pelo Flask-Limiter."""

from __future__ import annotations

import hashlib

from flask import current_app, request


def account_key() -> str:
    """Limita tentativas de login por conta (contra força bruta distribuída em vários IPs).

    Usa o hash do e-mail normalizado: o armazenamento do limitador nunca guarda
    e-mails em texto puro.
    """
    payload = request.get_json(silent=True)
    email = payload.get("email") if isinstance(payload, dict) else None
    normalized = email.strip().lower() if isinstance(email, str) else ""
    return "login-account:" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def session_key() -> str:
    """Limita operações sensíveis (senha, exclusão) por sessão de login.

    O limitador roda antes da autenticação da rota, então a chave é o hash do
    cookie de sessão (sem cookie, cai para o IP).
    """
    token = request.cookies.get(current_app.config["AUTH_COOKIE_NAME"])
    if token:
        return "session:" + hashlib.sha256(token.encode("utf-8")).hexdigest()
    return f"ip:{request.remote_addr}"


def limit_from_config(name: str):
    """Lê o limite da configuração no momento da requisição (permite ajustar por ambiente)."""
    return lambda: current_app.config[name]
