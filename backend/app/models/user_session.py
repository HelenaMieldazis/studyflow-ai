"""Sessões de login (tabela user_sessions).

O navegador guarda um token aleatório num cookie HttpOnly. O banco guarda apenas
o hash SHA-256 desse token: quem tiver acesso ao banco não consegue usar as
sessões registradas.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import utcnow

if TYPE_CHECKING:
    from app.models.user import User


class UserSession(db.Model):
    __tablename__ = "user_sessions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # SHA-256 em hexadecimal do token do cookie (64 caracteres).
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)
    # Expiração absoluta, definida no login. Indexada para a limpeza periódica.
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    user: Mapped[User] = relationship(back_populates="sessions")

    def __repr__(self) -> str:  # nunca inclui o hash do token
        return f"<UserSession id={self.id} user_id={self.user_id}>"
