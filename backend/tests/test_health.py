"""Testes do endpoint /api/health."""

from unittest.mock import patch

from sqlalchemy.exc import OperationalError


def test_health_returns_ok_when_database_is_reachable(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json() == {
        "status": "ok",
        "service": "studyflow-api",
        "checks": {"database": "ok"},
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_health_returns_503_without_leaking_details_when_database_fails(client):
    secret_detail = 'connection to server at "db.internal" (10.0.0.5), user "admin" failed'
    error = OperationalError("SELECT 1", {}, Exception(secret_detail))

    with patch("app.services.health_service.db.session.execute", side_effect=error):
        response = client.get("/api/health")

    assert response.status_code == 503
    body = response.get_json()
    assert body["status"] == "degraded"
    assert body["checks"]["database"] == "unavailable"
    raw = response.get_data(as_text=True)
    for leaked in ("db.internal", "10.0.0.5", "admin", "OperationalError"):
        assert leaked not in raw


def test_health_rejects_unsupported_method(client):
    response = client.post("/api/health")

    assert response.status_code == 405
    assert response.get_json()["error"]["code"] == "method_not_allowed"
    assert "GET" in response.headers["Allow"]


def test_health_returns_503_with_real_unreachable_postgres():
    """Integração real com o driver psycopg: porta sem servidor → 503, sem detalhes."""
    from app import create_app

    unreachable = "postgresql+psycopg://user:senha-secreta@127.0.0.1:1/inexistente"
    app = create_app(
        "testing",
        {
            "SQLALCHEMY_DATABASE_URI": unreachable,
            "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"connect_timeout": 2}},
        },
    )
    response = app.test_client().get("/api/health")

    assert response.status_code == 503
    raw = response.get_data(as_text=True)
    assert "senha-secreta" not in raw
    assert "127.0.0.1" not in raw
