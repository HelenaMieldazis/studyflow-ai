"""Endpoint de saúde: GET /api/health."""

from flask import Blueprint, jsonify

from app.services.health_service import check_database

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health():
    """Informa se a API está no ar e se o banco de dados responde.

    - 200: API e banco OK.
    - 503: API no ar, mas banco indisponível.

    A resposta nunca inclui detalhes internos (host, usuário, mensagem do driver).
    """
    database_ok = check_database()
    status_code = 200 if database_ok else 503
    body = {
        "status": "ok" if database_ok else "degraded",
        "service": "studyflow-api",
        "checks": {"database": "ok" if database_ok else "unavailable"},
    }
    response = jsonify(body)
    response.headers["Cache-Control"] = "no-store"
    return response, status_code
