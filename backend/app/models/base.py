"""Utilitários compartilhados pelos modelos."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import Mapped, mapped_column


def utcnow() -> datetime:
    """Data/hora atual em UTC, sempre com fuso horário."""
    return datetime.now(UTC)


def as_utc(value: datetime) -> datetime:
    """Garante que a data tenha fuso UTC.

    O PostgreSQL devolve `timestamptz` com fuso; o SQLite (usado como opção nos
    testes) devolve datas sem fuso. Ambas são gravadas em UTC pela aplicação.
    """
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


class TimestampMixin:
    """Adiciona created_at e updated_at, preenchidos automaticamente em UTC."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow
    )
