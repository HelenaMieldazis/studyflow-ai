"""Ponto de entrada da API.

Desenvolvimento:  flask --app run run --port 5001   (ou: python run.py)
Produção:         usar um servidor WSGI (ex.: gunicorn "run:app") — Etapa 8.
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    # O servidor embutido do Flask é só para desenvolvimento.
    app.run(
        host=os.getenv("BACKEND_HOST", "127.0.0.1"),
        port=int(os.getenv("BACKEND_PORT", "5001")),
        debug=app.config["DEBUG"],
    )
