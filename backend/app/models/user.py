"""Modelo de usuário (tabela users)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin, utcnow

if TYPE_CHECKING:
    from app.models.user_session import UserSession

EMAIL_MAX_LENGTH = 254  # limite prático de um endereço de e-mail (RFC 5321)
DISPLAY_NAME_MAX_LENGTH = 80


class User(TimestampMixin, db.Model):
    __tablename__ = "users"
    __table_args__ = (
        # O e-mail é sempre gravado normalizado em minúsculas; garante unicidade sem
        # depender de comparação case-insensitive.
        CheckConstraint("email = lower(email)", name="email_lowercase"),
        CheckConstraint("length(display_name) > 0", name="display_name_not_empty"),
    )

    # UUID em vez de inteiro sequencial: não revela quantos usuários existem
    # nem permite adivinhar IDs vizinhos.
    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(EMAIL_MAX_LENGTH), nullable=False, unique=True)
    display_name: Mapped[str] = mapped_column(String(DISPLAY_NAME_MAX_LENGTH), nullable=False)
    # Hash Argon2id (formato PHC: "$argon2id$v=19$m=...,t=...,p=...$salt$hash").
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    password_changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,  # o banco apaga as sessões (ON DELETE CASCADE)
    )

    def __repr__(self) -> str:  # nunca inclui e-mail ou hash
        return f"<User id={self.id}>"
