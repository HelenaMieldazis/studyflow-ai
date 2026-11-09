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


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    value = raw.strip().lower()
    if value in {"1", "true", "yes", "on"}:
        return True
    if value in {"0", "false", "no", "off"}:
        return False
    raise RuntimeError(f"A variável de ambiente {name} deve ser true ou false.")


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

    # --- Sessões de autenticação (cookie HttpOnly + registro no banco) ---------
    # Em produção o cookie usa o prefixo __Host- (exige Secure, Path=/ e sem Domain).
    AUTH_COOKIE_SECURE = _bool_env("AUTH_COOKIE_SECURE", True)
    AUTH_COOKIE_NAME = "__Host-sf_session" if AUTH_COOKIE_SECURE else "sf_session"
    AUTH_COOKIE_SAMESITE = "Lax"
    # Sessão expira após este tempo sem uso (renovada automaticamente enquanto houver uso)...
    SESSION_IDLE_TIMEOUT_MINUTES = _int_env("SESSION_IDLE_TIMEOUT_MINUTES", 120)
    # ...e nunca dura mais que isto desde o login, mesmo com uso contínuo.
    SESSION_ABSOLUTE_TIMEOUT_HOURS = _int_env("SESSION_ABSOLUTE_TIMEOUT_HOURS", 168)
    # Intervalo mínimo entre atualizações de "último uso" (evita uma escrita por requisição).
    SESSION_TOUCH_INTERVAL_SECONDS = 300

    # --- Limitação de requisições (Flask-Limiter) -------------------------------
    RATELIMIT_ENABLED = True
    # memory:// funciona para um único processo. Com vários workers, use Redis (Etapa 8).
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_HEADERS_ENABLED = True
    RATELIMIT_DEFAULT = "300 per minute"
    RATELIMIT_KEY_PREFIX = "studyflow"
    # Limites específicos (por IP e por conta).
    RATE_LIMIT_LOGIN_IP = "10 per minute; 50 per hour"
    RATE_LIMIT_LOGIN_ACCOUNT = "5 per 15 minutes; 20 per day"
    RATE_LIMIT_REGISTER_IP = "5 per hour"
    RATE_LIMIT_SENSITIVE_USER = "10 per hour"

    DEBUG = False
    TESTING = False

    @classmethod
    def validate(cls) -> None:
        """Validações executadas na inicialização. Sobrescrita por ambiente."""
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise RuntimeError("DATABASE_URL não foi definida. Consulte o .env.example.")
        if not cls.SECRET_KEY.strip():
            raise RuntimeError("SECRET_KEY não foi definida. Consulte o .env.example.")


class DevelopmentConfig(BaseConfig):
    DEBUG = True
    # Em desenvolvimento local (http://localhost) o cookie não pode ser Secure.
    AUTH_COOKIE_SECURE = _bool_env("AUTH_COOKIE_SECURE", False)
    AUTH_COOKIE_NAME = "__Host-sf_session" if AUTH_COOKIE_SECURE else "sf_session"


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
    AUTH_COOKIE_SECURE = False
    AUTH_COOKIE_NAME = "sf_session"
    SESSION_IDLE_TIMEOUT_MINUTES = 120
    SESSION_ABSOLUTE_TIMEOUT_HOURS = 168
    # Desligado por padrão para que os testes não interfiram uns nos outros;
    # os testes de rate limiting o ligam explicitamente.
    RATELIMIT_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"


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
        if not cls.AUTH_COOKIE_SECURE:
            raise RuntimeError("Em produção, AUTH_COOKIE_SECURE deve ser true (cookies só via HTTPS).")


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
