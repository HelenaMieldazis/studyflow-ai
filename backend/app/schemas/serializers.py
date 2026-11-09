"""Conversão de modelos para JSON público.

Lista explícita de campos: nada é exposto por acidente (ex.: password_hash).
"""

from __future__ import annotations

from app.models import User
from app.models.base import as_utc


def serialize_user(user: User) -> dict:
    return {
        "id": str(user.id),
        "email": user.email,
        "display_name": user.display_name,
        "created_at": as_utc(user.created_at).isoformat(),
    }
