"""Verificações de saúde da infraestrutura."""

import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db

logger = logging.getLogger(__name__)


def check_database() -> bool:
    """Executa `SELECT 1` no banco. Retorna True se o banco respondeu.

    Em caso de falha, registra apenas o tipo da exceção no log (a mensagem do
    driver pode conter host, usuário ou nome do banco) e retorna False.
    """
    try:
        db.session.execute(text("SELECT 1"))
        return True
    except SQLAlchemyError as exc:
        logger.warning("Falha na verificação do banco de dados: %s", type(exc).__name__)
        db.session.rollback()
        return False
