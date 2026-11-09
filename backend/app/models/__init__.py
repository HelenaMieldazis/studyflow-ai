"""Modelos SQLAlchemy.

Cada entidade fica em seu próprio módulo e é importada aqui para que o
Flask-Migrate a detecte ao gerar migrações.
"""

from app.models.user import User
from app.models.user_session import UserSession

__all__ = ["User", "UserSession"]
