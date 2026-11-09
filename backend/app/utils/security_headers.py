"""Headers HTTP de segurança aplicados a todas as respostas da API.

A API devolve apenas JSON, então a Content-Security-Policy pode ser a mais
restritiva possível. A CSP do frontend será definida no servidor que publicar
os arquivos estáticos (Etapa 8).
"""

from flask import Flask, Response

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "Cross-Origin-Resource-Policy": "same-site",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
}


def register_security_headers(app: Flask) -> None:
    @app.after_request
    def apply_security_headers(response: Response) -> Response:
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        # HSTS só faz sentido sob HTTPS (produção).
        if not app.debug and not app.testing:
            response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        return response
