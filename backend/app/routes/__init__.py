"""Registro central dos blueprints da API (todos sob o prefixo /api)."""

from flask import Flask

API_PREFIX = "/api"


def register_blueprints(app: Flask) -> None:
    from app.routes.auth import auth_bp
    from app.routes.health import health_bp
    from app.routes.users import users_bp

    app.register_blueprint(health_bp, url_prefix=API_PREFIX)
    app.register_blueprint(auth_bp, url_prefix=f"{API_PREFIX}/auth")
    app.register_blueprint(users_bp, url_prefix=f"{API_PREFIX}/users")
