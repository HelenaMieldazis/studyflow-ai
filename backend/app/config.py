"""Configuração da aplicação por ambiente.

Todos os valores sensíveis vêm de variáveis de ambiente (arquivo `.env` na raiz
do repositório em desenvolvimento). Nenhum segredo fica no código.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Raiz do repositório: studyflow-ai/
REPO_ROOT = Path(__file__).resolve().parents[2]

# Carrega o .env da raiz sem sobrescrever variáveis já definidas no ambiente
# (em produção, variáveis do sistema/orquestrador têm prioridade).
load_dotenv(REPO_ROOT / ".env", override=False)

_INSECURE_SECRET_PLACEHOLDERS = {"", "change-me", "changeme", "dev", "secret"}
_MIN_SECRET_LENGTH = 32


def _split_csv(value: str | None) -> list[str]:
    """Converte "a, b,c" em ["a", "b", "c"], ignorando itens vazios."""
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise RuntimeError(f"A variável de ambiente {name} deve ser um número inteiro.") from exc


class BaseConfig:
    """Valores comuns a todos os ambientes."""

    SECRET_KEY = os.getenv("SECRET_KEY", "")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        # Descarta conexões quebradas antes de usá-las.
        "pool_pre_ping": True,
        # Evita que a aplicação fique presa esperando o banco.
        "connect_args": {"connect_timeout": _int_env("DATABASE_CONNECT_TIMEOUT", 5)},
    }

    # Origens autorizadas a chamar a API pelo navegador (lista explícita, nunca "*").
    CORS_ORIGINS = _split_csv(os.getenv("CORS_ORIGINS", "http://localhost:5173"))

    # Limite global do corpo das requisições (bytes). Requisições maiores recebem 413.
    MAX_CONTENT_LENGTH = _int_env("MAX_CONTENT_LENGTH", 1 * 1024 * 1024)

    DEBUG = False
    TESTING = False

    @classmethod
    def validate(cls) -> None:
        """Validações executadas na inicialização. Sobrescrita por ambiente."""
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise RuntimeError("DATABASE_URL não foi definida. Consulte o .env.example.")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    SECRET_KEY = "test-secret-key-not-for-production-use-0123456789"
    # Os testes usam TEST_DATABASE_URL (PostgreSQL) quando definida;
    # caso contrário, um SQLite em memória isolado.
    SQLALCHEMY_DATABASE_URI = os.getenv("TEST_DATABASE_URL") or "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = (
        {"pool_pre_ping": True}
        if SQLALCHEMY_DATABASE_URI.startswith("sqlite")
        else BaseConfig.SQLALCHEMY_ENGINE_OPTIONS
    )
    CORS_ORIGINS = ["http://localhost:5173"]


class ProductionConfig(BaseConfig):
    DEBUG = False

    @classmethod
    def validate(cls) -> None:
        super().validate()
        if cls.SECRET_KEY.strip().lower() in _INSECURE_SECRET_PLACEHOLDERS or len(cls.SECRET_KEY) < _MIN_SECRET_LENGTH:
            raise RuntimeError(
                f"SECRET_KEY ausente ou fraca. Em produção use um valor aleatório com pelo menos {_MIN_SECRET_LENGTH} caracteres."
            )
        if not cls.CORS_ORIGINS:
            raise RuntimeError("CORS_ORIGINS deve listar as origens autorizadas em produção.")
        if any(origin == "*" for origin in cls.CORS_ORIGINS):
            raise RuntimeError("CORS_ORIGINS não pode conter '*' em produção.")
        if any(not origin.startswith("https://") for origin in cls.CORS_ORIGINS):
            raise RuntimeError("Em produção, todas as origens em CORS_ORIGINS devem usar HTTPS.")


CONFIG_BY_NAME: dict[str, type[BaseConfig]] = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None) -> type[BaseConfig]:
    """Retorna a classe de configuração. Padrão: variável APP_ENV ou 'production'.

    O padrão é 'production' de propósito: se alguém esquecer de definir o
    ambiente, a aplicação falha fechada (exige segredos fortes, sem debug).
    """
    env_name = (name or os.getenv("APP_ENV") or "production").strip().lower()
    try:
        return CONFIG_BY_NAME[env_name]
    except KeyError as exc:
        valid = ", ".join(CONFIG_BY_NAME)
        raise RuntimeError(f"APP_ENV inválido: '{env_name}'. Valores aceitos: {valid}.") from exc
