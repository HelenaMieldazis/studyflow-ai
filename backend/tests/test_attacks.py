"""Tentativas de ataque: injeção de SQL, XSS, força bruta, payloads grandes."""

from __future__ import annotations

import pytest
from sqlalchemy import func, select

from app import create_app
from app.extensions import db, limiter
from app.models import User
from tests.conftest import DEFAULT_PASSWORD, ORIGIN, AuthClient

SQL_PAYLOADS = [
    "' OR '1'='1",
    "' OR 1=1 --",
    "admin'--",
    "'; DROP TABLE users; --",
    "\" OR \"\"=\"",
    "' UNION SELECT id, email, password_hash FROM users --",
]


# --- Injeção de SQL ---------------------------------------------------------------------


@pytest.mark.parametrize("payload", SQL_PAYLOADS)
def test_sql_injection_in_login_password_does_not_authenticate(ana, make_client, payload):
    response = make_client().login(password=payload)

    assert response.status_code in (401, 422)
    assert "Set-Cookie" not in response.headers


@pytest.mark.parametrize("payload", SQL_PAYLOADS)
def test_sql_injection_in_login_email_is_rejected(ana, make_client, payload):
    response = make_client().login(email=payload)

    assert response.status_code == 422  # não é um e-mail válido
    assert db.session.execute(select(func.count()).select_from(User)).scalar_one() == 1


def test_sql_payload_in_text_field_is_stored_literally(ana):
    payload = "Robert'); DROP TABLE users;--"
    response = ana.request("PATCH", "/api/users/me", json={"display_name": payload})

    assert response.status_code == 200
    assert response.get_json()["user"]["display_name"] == payload
    assert db.session.execute(select(func.count()).select_from(User)).scalar_one() == 1


# --- XSS ---------------------------------------------------------------------------------


def test_xss_payload_is_returned_as_json_data_never_as_html(ana):
    payload = '<script>alert("xss")</script><img src=x onerror=alert(1)>'
    response = ana.request("PATCH", "/api/users/me", json={"display_name": payload})

    assert response.status_code == 200
    assert response.mimetype == "application/json"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]
    # O valor é dado: guardado e devolvido como texto; quem escapa na exibição é o React.
    assert response.get_json()["user"]["display_name"] == payload


@pytest.mark.parametrize("name", ["Ana‮eman", "Ana\x00", "Ana\x1b[31m", "Ana\r\nSet-Cookie: x=y"])
def test_control_and_bidi_characters_are_rejected(ana, name):
    response = ana.request("PATCH", "/api/users/me", json={"display_name": name})
    assert response.status_code == 422


# --- Rate limiting / força bruta / credential stuffing --------------------------------------------


@pytest.fixture()
def limited_app():
    app = create_app("testing", {"RATELIMIT_ENABLED": True})
    with app.app_context():
        db.drop_all()
        db.create_all()
        limiter.reset()
        yield app
        db.session.remove()
        db.drop_all()
        db.engine.dispose()
        limiter.reset()


def test_login_is_rate_limited_per_account(limited_app):
    c = AuthClient(limited_app.test_client())
    c.register()

    statuses = [c.login(password=f"tentativa-errada-{i:03d}").status_code for i in range(6)]

    assert statuses[:5] == [401] * 5
    assert statuses[5] == 429
    # Mesmo a senha correta é bloqueada durante a janela (contra força bruta).
    blocked = c.login()
    assert blocked.status_code == 429
    assert blocked.get_json()["error"]["code"] == "too_many_requests"
    assert "Retry-After" in blocked.headers


def test_login_is_rate_limited_per_ip_across_many_accounts(limited_app):
    """Credential stuffing: muitas contas diferentes a partir do mesmo IP."""
    client = limited_app.test_client()
    statuses = [
        client.post(
            "/api/auth/login",
            json={"email": f"vitima{i}@example.com", "password": DEFAULT_PASSWORD},
            headers={"Origin": ORIGIN},
        ).status_code
        for i in range(11)
    ]

    assert statuses[:10] == [401] * 10
    assert statuses[10] == 429


def test_registration_is_rate_limited_per_ip(limited_app):
    c = AuthClient(limited_app.test_client())
    statuses = [c.register(email=f"user{i}@example.com").status_code for i in range(6)]

    assert statuses[:5] == [201] * 5
    assert statuses[5] == 429


def test_rate_limit_headers_are_sent(limited_app):
    response = limited_app.test_client().get("/api/health")
    assert "X-RateLimit-Limit" in response.headers


# --- Tamanho de requisição ---------------------------------------------------------------------


def test_oversized_registration_payload_is_rejected(client):
    response = client.post(
        "/api/auth/register",
        json={"email": "a@example.com", "password": DEFAULT_PASSWORD, "display_name": "x" * 2_000_000},
    )
    assert response.status_code == 413
