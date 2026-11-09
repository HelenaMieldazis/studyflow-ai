"""Fixtures compartilhadas do Pytest."""

from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db, limiter

ORIGIN = "http://localhost:5173"
DEFAULT_PASSWORD = "uma-senha-bem-longa-123"


@pytest.fixture()
def app():
    """Aplicação em modo de teste com banco limpo a cada teste.

    Usa TEST_DATABASE_URL (PostgreSQL) se definida; senão, SQLite em memória.
    Nunca aponta para o banco de desenvolvimento.
    """
    application = create_app("testing")
    with application.app_context():
        db.drop_all()
        db.create_all()
        if application.config["RATELIMIT_ENABLED"]:
            limiter.reset()
        yield application
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()


class AuthClient:
    """Cliente de teste que se comporta como o frontend: guarda o token CSRF da última resposta."""

    def __init__(self, client):
        self.client = client
        self.csrf_token: str | None = None

    def _capture(self, response):
        body = response.get_json(silent=True) or {}
        if isinstance(body, dict) and body.get("csrf_token"):
            self.csrf_token = body["csrf_token"]
        return response

    def _headers(self, extra=None):
        headers = {"Origin": ORIGIN}
        if self.csrf_token:
            headers["X-CSRF-Token"] = self.csrf_token
        headers.update(extra or {})
        return headers

    def register(self, email="ana@example.com", password=DEFAULT_PASSWORD, display_name="Ana"):
        return self._capture(
            self.client.post(
                "/api/auth/register",
                json={"email": email, "password": password, "display_name": display_name},
                headers=self._headers(),
            )
        )

    def login(self, email="ana@example.com", password=DEFAULT_PASSWORD):
        return self._capture(
            self.client.post("/api/auth/login", json={"email": email, "password": password}, headers=self._headers())
        )

    def request(self, method, path, json=None, headers=None):
        return self._capture(self.client.open(path, method=method, json=json, headers=self._headers(headers)))


@pytest.fixture()
def make_client(app):
    """Fábrica de clientes independentes (cada um com seus próprios cookies)."""

    def factory() -> AuthClient:
        return AuthClient(app.test_client())

    return factory


@pytest.fixture()
def ana(make_client) -> AuthClient:
    c = make_client()
    assert c.register().status_code == 201
    return c
