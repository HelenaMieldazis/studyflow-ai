"""Registro central dos blueprints da API (todos sob o prefixo /api)."""

from flask import Flask

API_PREFIX = "/api"


def register_blueprints(app: Flask) -> None:
    from app.routes.health import health_bp

    app.register_blueprint(health_bp, url_prefix=API_PREFIX)
