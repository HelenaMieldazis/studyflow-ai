"""Instâncias de extensões Flask compartilhadas.

Criadas sem aplicação e ligadas em `create_app()` (padrão application factory),
evitando importações circulares entre modelos, rotas e serviços.
"""

from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, event
from sqlalchemy.engine import Engine

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

# Rate limiting. Padrão: chave = endereço IP de origem.
# Atrás de um proxy reverso será necessário configurar ProxyFix (Etapa 8),
# caso contrário todos os clientes compartilharão o IP do proxy.
limiter = Limiter(key_func=get_remote_address)


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record):
    """O SQLite ignora chaves estrangeiras por padrão; liga-as (usado nos testes).

    O PostgreSQL sempre aplica as restrições, então nada muda nele.
    """
    module = type(dbapi_connection).__module__
    if module.startswith("sqlite3"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
