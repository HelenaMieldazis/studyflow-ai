"""Fixtures compartilhadas do Pytest."""

import pytest

from app import create_app
from app.extensions import db


@pytest.fixture()
def app():
    """Aplicação em modo de teste.

    Usa TEST_DATABASE_URL (PostgreSQL) se definida; senão, SQLite em memória.
    Nunca aponta para o banco de desenvolvimento.
    """
    application = create_app("testing")
    with application.app_context():
        yield application
        db.session.remove()
        db.engine.dispose()


@pytest.fixture()
def client(app):
    return app.test_client()
