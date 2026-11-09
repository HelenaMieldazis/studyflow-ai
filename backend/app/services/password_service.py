"""Hash e verificação de senhas com Argon2id (argon2-cffi).

Parâmetros: perfil padrão da biblioteca (RFC 9106, "low memory"): 64 MiB de
memória, 3 iterações, 4 threads. Cada hash tem salt aleatório próprio.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()  # tipo padrão: Argon2id

# Hash de uma senha aleatória, usado quando o e-mail não existe: verificar contra
# ele custa o mesmo tempo que uma verificação real, então o tempo de resposta não
# revela se a conta existe (proteção contra enumeração por tempo).
_DUMMY_HASH = _hasher.hash("studyflow-dummy-password-for-timing-equalization")


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str | None, password: str) -> bool:
    """Retorna True se a senha confere. Nunca lança exceção para senha errada."""
    try:
        return _hasher.verify(password_hash or _DUMMY_HASH, password) and password_hash is not None
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(password_hash: str) -> bool:
    """True se o hash foi gerado com parâmetros mais fracos que os atuais."""
    return _hasher.check_needs_rehash(password_hash)
