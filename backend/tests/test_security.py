"""Testes da configuração base de segurança (Etapa 1)."""

import pytest
from flask import Blueprint

from app import create_app
from app.config import ProductionConfig

ALLOWED_ORIGIN = "http://localhost:5173"


# --- Tratamento de erros -----------------------------------------------------


def test_unknown_route_returns_json_404(client):
    response = client.get("/api/rota-que-nao-existe")

    assert response.status_code == 404
    assert response.get_json() == {"error": {"code": "not_found", "message": "Recurso não encontrado."}}


def test_unexpected_exception_returns_generic_500_without_stack_trace():
    app = create_app("testing")
    boom = Blueprint("boom", __name__)

    @boom.get("/api/_boom")
    def explode():
        raise RuntimeError("segredo interno: senha=hunter2")

    app.register_blueprint(boom)
    response = app.test_client().get("/api/_boom")

    assert response.status_code == 500
    raw = response.get_data(as_text=True)
    assert "hunter2" not in raw
    assert "Traceback" not in raw
    assert "RuntimeError" not in raw
    assert response.get_json()["error"]["code"] == "internal_error"


def test_request_body_larger_than_limit_is_rejected():
    app = create_app("testing", {"MAX_CONTENT_LENGTH": 10})
    sink = Blueprint("sink", __name__)

    @sink.post("/api/_sink")
    def read_body():
        from flask import request

        return {"size": len(request.get_data())}

    app.register_blueprint(sink)
    response = app.test_client().post("/api/_sink", data=b"x" * 100, content_type="application/octet-stream")

    assert response.status_code == 413
    assert response.get_json()["error"]["code"] == "payload_too_large"


# --- Headers de segurança ------------------------------------------------------


def test_security_headers_are_present(client):
    response = client.get("/api/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]


def test_server_does_not_advertise_debug_mode(client, app):
    assert app.debug is False


# --- CORS ------------------------------------------------------------------------


def test_cors_allows_configured_origin(client):
    response = client.get("/api/health", headers={"Origin": ALLOWED_ORIGIN})

    assert response.headers.get("Access-Control-Allow-Origin") == ALLOWED_ORIGIN
    assert response.headers.get("Access-Control-Allow-Credentials") == "true"


def test_cors_ignores_unknown_origin(client):
    response = client.get("/api/health", headers={"Origin": "https://site-malicioso.example"})

    assert "Access-Control-Allow-Origin" not in response.headers


def test_cors_preflight_from_unknown_origin_is_not_authorized(client):
    response = client.options(
        "/api/health",
        headers={"Origin": "https://site-malicioso.example", "Access-Control-Request-Method": "POST"},
    )

    assert "Access-Control-Allow-Origin" not in response.headers


# --- Configuração de produção -------------------------------------------------


@pytest.mark.parametrize(
    ("secret", "origins", "expected_message"),
    [
        ("", ["https://app.example.com"], "SECRET_KEY"),
        ("change-me", ["https://app.example.com"], "SECRET_KEY"),
        ("curta", ["https://app.example.com"], "SECRET_KEY"),
        ("x" * 64, ["*"], "'*'"),
        ("x" * 64, ["http://app.example.com"], "HTTPS"),
        ("x" * 64, [], "CORS_ORIGINS"),
    ],
)
def test_production_config_refuses_insecure_settings(monkeypatch, secret, origins, expected_message):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", secret)
    monkeypatch.setattr(ProductionConfig, "CORS_ORIGINS", origins)
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "postgresql+psycopg://u:p@localhost/db")

    with pytest.raises(RuntimeError, match=expected_message):
        ProductionConfig.validate()


def test_production_config_requires_database_url(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "x" * 64)
    monkeypatch.setattr(ProductionConfig, "CORS_ORIGINS", ["https://app.example.com"])
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "")

    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        ProductionConfig.validate()


def test_production_config_accepts_secure_settings(monkeypatch):
    monkeypatch.setattr(ProductionConfig, "SECRET_KEY", "x" * 64)
    monkeypatch.setattr(ProductionConfig, "CORS_ORIGINS", ["https://app.example.com"])
    monkeypatch.setattr(ProductionConfig, "SQLALCHEMY_DATABASE_URI", "postgresql+psycopg://u:p@localhost/db")

    ProductionConfig.validate()  # não deve lançar exceção


def test_invalid_app_env_is_rejected():
    with pytest.raises(RuntimeError, match="APP_ENV inválido"):
        create_app("staging-inexistente")
