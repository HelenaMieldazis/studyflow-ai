"""Configuração de logs.

Regra do projeto: nunca registrar senhas, tokens, cookies, corpo de
requisições ou dados pessoais. Os logs devem conter apenas eventos técnicos.
"""

import logging
import os

from flask import Flask


def configure_logging(app: Flask) -> None:
    level_name = os.getenv("LOG_LEVEL", "DEBUG" if app.debug else "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    app.logger.setLevel(level)
    # O log de acesso do servidor de desenvolvimento inclui query strings,
    # que podem conter dados sensíveis no futuro; mantido em INFO apenas em dev.
    logging.getLogger("werkzeug").setLevel(logging.INFO if app.debug else logging.WARNING)
