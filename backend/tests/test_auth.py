"""Cadastro, login, logout, sessão, expiração e CSRF."""

from __future__ import annotations

import hashlib
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.extensions import db
from app.models import User, UserSession
from app.models.base import as_utc, utcnow
from tests.conftest import DEFAULT_PASSWORD, ORIGIN

COOKIE = "sf_session"


def _set_cookie_header(response) -> str:
    return next(v for k, v in response.headers.items() if k == "Set-Cookie" and v.startswith(COOKIE))


def _session_count() -> int:
    return db.session.execute(select(func.count()).select_from(UserSession)).scalar_one()


# --- Cadastro --------------------------------------------------------------------


def test_register_creates_user_session_and_secure_cookie(make_client):
    c = make_client()
    response = c.register(email="  Ana@Example.COM ", display_name="  Ana Souza ")

    assert response.status_code == 201
    body = response.get_json()
    assert body["user"]["email"] == "ana@example.com"  # normalizado
    assert body["user"]["display_name"] == "Ana Souza"
    assert set(body["user"]) == {"id", "email", "display_name", "created_at"}  # nada de hash
    assert len(body["csrf_token"]) == 64

    cookie = _set_cookie_header(response)
    assert "HttpOnly" in cookie
    assert "SameSite=Lax" in cookie
    assert "Path=/" in cookie
    assert response.headers["Cache-Control"] == "no-store"


def test_password_is_stored_as_argon2id_hash(ana):
    user = db.session.execute(select(User)).scalar_one()
    assert user.password_hash.startswith("$argon2id$")
    assert DEFAULT_PASSWORD not in user.password_hash


def test_session_token_is_stored_only_as_hash(make_client):
    c = make_client()
    response = c.register()
    token = _set_cookie_header(response).split(";")[0].split("=", 1)[1]

    stored = db.session.execute(select(UserSession)).scalar_one()
    assert stored.token_hash != token
    assert stored.token_hash == hashlib.sha256(token.encode()).hexdigest()


def test_register_rejects_duplicate_email_case_insensitive(ana, make_client):
    response = make_client().register(email="ANA@example.com")

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "email_unavailable"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({"email": "nao-e-email", "password": DEFAULT_PASSWORD, "display_name": "A"}, "email"),
        ({"email": "a@example.com", "password": "curta", "display_name": "A"}, "password"),
        ({"email": "a@example.com", "password": "x" * 129, "display_name": "A"}, "password"),
        ({"email": "a@example.com", "password": " " * 20, "display_name": "A"}, "password"),
        ({"email": "a@example.com", "password": DEFAULT_PASSWORD, "display_name": "   "}, "display_name"),
        ({"email": "a@example.com", "password": DEFAULT_PASSWORD, "display_name": "x" * 81}, "display_name"),
        ({"email": "a@example.com", "password": DEFAULT_PASSWORD}, "display_name"),
        ({"email": "a@example.com", "password": DEFAULT_PASSWORD, "display_name": 123}, "display_name"),
        ({"email": "a@example.com", "password": DEFAULT_PASSWORD, "display_name": "A", "is_admin": True}, "is_admin"),
    ],
)
def test_register_validates_input(client, payload, field):
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422
    fields = {f["field"] for f in response.get_json()["error"]["fields"]}
    assert field in fields
    assert _session_count() == 0


def test_register_rejects_password_equal_to_email(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "joao.silva.2024@example.com", "password": "joao.silva.2024@example.com", "display_name": "J"},
    )

    assert response.status_code == 422
    assert response.get_json()["error"]["message"] == "A senha não pode ser igual ao e-mail."


def test_register_requires_json_content_type(client):
    response = client.post("/api/auth/register", data="email=a@example.com", content_type="application/x-www-form-urlencoded")
    assert response.status_code == 415


def test_register_rejects_malformed_and_non_object_json(client):
    malformed = client.post("/api/auth/register", data="{nope", content_type="application/json")
    array = client.post("/api/auth/register", json=["a"])

    assert malformed.status_code == 400
    assert array.status_code == 422


# --- Login -------------------------------------------------------------------------


def test_login_succeeds_with_correct_credentials(ana, make_client):
    response = make_client().login(email="ANA@example.com ")

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "ana@example.com"
    assert _set_cookie_header(response)


def test_wrong_password_and_unknown_email_get_identical_responses(ana, make_client):
    wrong_password = make_client().login(password="senha-errada-123456")
    unknown_email = make_client().login(email="ninguem@example.com")

    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.get_json() == unknown_email.get_json() == {
        "error": {"code": "invalid_credentials", "message": "E-mail ou senha incorretos."}
    }
    assert "Set-Cookie" not in wrong_password.headers


def test_login_replaces_previous_session_of_same_browser(ana):
    old_token = ana.client.get_cookie(COOKIE).value
    assert ana.login().status_code == 200
    new_token = ana.client.get_cookie(COOKIE).value

    assert new_token != old_token
    assert _session_count() == 1  # a sessão antiga foi revogada (evita fixação de sessão)


# --- Sessão / acesso sem autenticação --------------------------------------------------


def test_me_requires_authentication(client):
    response = client.get("/api/auth/me")

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthenticated"


def test_me_returns_current_user_and_csrf_token(ana):
    response = ana.request("GET", "/api/auth/me")

    assert response.status_code == 200
    assert response.get_json()["user"]["email"] == "ana@example.com"
    assert response.get_json()["csrf_token"] == ana.csrf_token


def test_forged_or_oversized_cookie_is_rejected(client):
    client.set_cookie(COOKIE, "token-inventado")
    assert client.get("/api/auth/me").status_code == 401
    client.set_cookie(COOKIE, "x" * 500)
    assert client.get("/api/auth/me").status_code == 401


# --- Logout --------------------------------------------------------------------------


def test_logout_invalidates_session_on_server(ana, make_client):
    stolen_token = ana.client.get_cookie(COOKIE).value

    response = ana.request("POST", "/api/auth/logout")
    assert response.status_code == 200
    assert "Max-Age=0" in _set_cookie_header(response) or "expires=Thu, 01 Jan 1970" in _set_cookie_header(response)

    # Mesmo que alguém tenha copiado o cookie antes, ele não vale mais.
    attacker = make_client().client
    attacker.set_cookie(COOKIE, stolen_token)
    assert attacker.get("/api/auth/me").status_code == 401
    assert _session_count() == 0


# --- Expiração ------------------------------------------------------------------------


def _only_session() -> UserSession:
    return db.session.execute(select(UserSession)).scalar_one()


def test_session_expires_after_inactivity(ana, app):
    s = _only_session()
    s.last_seen_at = utcnow() - timedelta(minutes=app.config["SESSION_IDLE_TIMEOUT_MINUTES"] + 1)
    db.session.commit()

    response = ana.request("GET", "/api/auth/me")

    assert response.status_code == 401
    assert _session_count() == 0
    assert COOKIE in response.headers.get("Set-Cookie", "")  # cookie vencido é apagado


def test_session_expires_at_absolute_limit_even_if_active(ana):
    s = _only_session()
    s.expires_at = utcnow() - timedelta(seconds=1)
    s.last_seen_at = utcnow()
    db.session.commit()

    assert ana.request("GET", "/api/auth/me").status_code == 401
    assert _session_count() == 0


def test_activity_renews_idle_expiration(ana, app):
    s = _only_session()
    old = utcnow() - timedelta(minutes=30)
    s.last_seen_at = old
    db.session.commit()

    assert ana.request("GET", "/api/auth/me").status_code == 200
    db.session.expire_all()
    assert as_utc(_only_session().last_seen_at) > old


def test_cleanup_command_removes_expired_sessions(ana, make_client, app):
    make_client().register(email="bruno@example.com", display_name="Bruno")
    sessions = db.session.execute(select(UserSession)).scalars().all()
    sessions[0].expires_at = utcnow() - timedelta(hours=1)
    db.session.commit()

    result = app.test_cli_runner().invoke(args=["cleanup-sessions"])

    assert "1 sessão" in result.output
    assert _session_count() == 1


# --- CSRF e origem ----------------------------------------------------------------------


def test_state_changing_request_without_csrf_token_is_rejected(ana):
    response = ana.client.post("/api/auth/logout", headers={"Origin": ORIGIN})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"
    assert _session_count() == 1  # nada foi alterado


def test_csrf_token_from_another_session_is_rejected(ana, make_client):
    bruno = make_client()
    bruno.register(email="bruno@example.com", display_name="Bruno")

    response = ana.request("POST", "/api/auth/logout", headers={"X-CSRF-Token": bruno.csrf_token})

    assert response.status_code == 403


def test_get_requests_do_not_require_csrf(ana):
    assert ana.client.get("/api/auth/me").status_code == 200


@pytest.mark.parametrize("path", ["/api/auth/login", "/api/auth/register", "/api/auth/logout"])
def test_requests_from_untrusted_origin_are_blocked(client, path):
    response = client.post(path, json={}, headers={"Origin": "https://site-malicioso.example"})

    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "origin_not_allowed"


def test_null_origin_is_blocked(client):
    response = client.post("/api/auth/login", json={}, headers={"Origin": "null"})
    assert response.status_code == 403
