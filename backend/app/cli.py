"""Comandos de linha de comando: flask --app run <comando>."""

from __future__ import annotations

import click
from flask import Flask

from app.services import session_service


def register_cli(app: Flask) -> None:
    @app.cli.command("cleanup-sessions")
    def cleanup_sessions() -> None:
        """Apaga sessões expiradas do banco (agendar periodicamente em produção)."""
        removed = session_service.delete_expired_sessions()
        click.echo(f"{removed} sessão(ões) expirada(s) removida(s).")
