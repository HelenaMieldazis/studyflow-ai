"""Application factory da API do StudyFlow AI."""

from __future__ import annotations

import logging

from flask import Flask

from app.config import BaseConfig, get_config
from app.extensions import cors, db, migrate
from app.utils.errors import register_error_handlers
from app.utils.log_config import configure_logging
from app.utils.security_headers import register_security_headers


def create_app(config_name: str | None = None, config_overrides: dict | None = None) -> Flask:
    """Cria e configura uma instância da aplicação Flask.

    Args:
        config_name: "development", "testing" ou "production". Se omitido, usa APP_ENV.
        config_overrides: valores extras (usado pelos testes).
    """
    config_class: type[BaseConfig] = get_config(config_name)
    config_class.validate()

    app = Flask(__name__)
    app.config.from_object(config_class)
    if config_overrides:
        app.config.update(config_overrides)

    # Mantém a ordem das chaves definida no código nas respostas JSON.
    app.json.sort_keys = False

    configure_logging(app)

    # Extensões
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,  # necessário para cookies de sessão (Etapa 2)
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-CSRF-Token"],
        max_age=600,
        always_send=False,  # só envia headers CORS quando há header Origin
    )

    # Importa os modelos para que o Flask-Migrate os enxergue.
    from app import models  # noqa: F401

    # Rotas
    from app.routes import register_blueprints

    register_blueprints(app)

    register_error_handlers(app)
    register_security_headers(app)

    logging.getLogger(__name__).info("Aplicação iniciada (ambiente=%s)", config_class.__name__)
    return app
