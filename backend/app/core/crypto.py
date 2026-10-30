"""Cifrado de credenciales de servidores.

Las credenciales nunca se guardan en texto plano ni se incluyen en respuestas o
logs. Se cifran con Fernet (AES-128-CBC + HMAC-SHA256) usando una clave externa
al repositorio. Para rotación futura se almacena ``key_version``.
"""

from __future__ import annotations

import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

_fernet = Fernet(settings.fernet_key.encode("ascii"))
CURRENT_KEY_VERSION = 1


class CredentialDecryptionError(Exception):
    pass


def encrypt_secret(secret: str) -> tuple[str, str]:
    if not secret:
        raise ValueError("El secreto no puede estar vacío.")
    ciphertext = _fernet.encrypt(secret.encode("utf-8")).decode("ascii")
    fingerprint = hashlib.sha256(secret.encode("utf-8")).hexdigest()
    return ciphertext, fingerprint


def decrypt_secret(ciphertext: str) -> str:
    try:
        return _fernet.decrypt(ciphertext.encode("ascii")).decode("utf-8")
    except (InvalidToken, ValueError) as exc:
        raise CredentialDecryptionError(
            "No fue posible descifrar la credencial. Verifique FERNET_KEY."
        ) from exc
