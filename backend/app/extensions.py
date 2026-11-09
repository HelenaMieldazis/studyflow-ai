"""Instâncias de extensões Flask compartilhadas.

Criadas sem aplicação e ligadas em `create_app()` (padrão application factory),
evitando importações circulares entre modelos, rotas e serviços.
"""

from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData

# Convenção de nomes para constraints: garante migrações determinísticas e
# nomes previsíveis para índices, chaves estrangeiras e checks.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

db = SQLAlchemy(metadata=MetaData(naming_convention=NAMING_CONVENTION))
migrate = Migrate()
cors = CORS()
