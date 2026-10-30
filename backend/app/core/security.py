"""Primitivas criptográficas y de autenticación."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import bcrypt
from jose import JWTError, jwt

from app.config import settings

JWT_ISSUER = "cis-hardening-auditor"
JWT_AUDIENCE = "cis-hardening-auditor-web"
COMMON_PASSWORDS = {
    "password",
    "password123",
    "123456789012",
    "qwertyuiop12",
    "administrador",
    "administrator",
    "bienvenido123",
    "cambiar123456",
}


class PasswordPolicyError(ValueError):
    pass


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def validate_password_strength(password: str, email: str | None = None) -> None:
    if len(password) < settings.password_min_length:
        raise PasswordPolicyError(
            f"La contraseña debe tener al menos {settings.password_min_length} caracteres."
        )
    if len(password.encode("utf-8")) > 72:
        raise PasswordPolicyError("La contraseña no puede superar 72 bytes en UTF-8.")
    classes = sum(
        [
            any(char.islower() for char in password),
            any(char.isupper() for char in password),
            any(char.isdigit() for char in password),
            any(not char.isalnum() for char in password),
        ]
    )
    if classes < 3:
        raise PasswordPolicyError(
            "La contraseña debe combinar al menos tres de: minúsculas, mayúsculas, "
            "dígitos y símbolos."
        )
    if password.lower() in COMMON_PASSWORDS:
        raise PasswordPolicyError("La contraseña es demasiado común.")
    if email:
        local = email.split("@", 1)[0].lower()
        if len(local) >= 4 and local in password.lower():
            raise PasswordPolicyError("La contraseña no debe contener el correo del usuario.")


def hash_password(password: str) -> str:
    validate_password_strength(password)
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


# Hash de relleno para reducir diferencias de tiempo cuando el usuario no existe.
DUMMY_PASSWORD_HASH = bcrypt.hashpw(b"not-a-real-password-1234", bcrypt.gensalt(rounds=12)).decode()


def create_access_token(user_id: str, organization_id: str) -> tuple[str, int]:
    now = utcnow()
    expires = now + timedelta(minutes=settings.access_token_minutes)
    payload = {
        "sub": user_id,
        "org": organization_id,
        "type": "access",
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "iat": now.timestamp(),
        "exp": int(expires.timestamp()),
        "jti": uuid4().hex,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)
    return token, settings.access_token_minutes * 60


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
            audience=JWT_AUDIENCE,
            issuer=JWT_ISSUER,
            options={"require_exp": True, "require_sub": True},
        )
    except JWTError as exc:
        raise ValueError("Token inválido o expirado.") from exc
    if payload.get("type") != "access":
        raise ValueError("Tipo de token inválido.")
    return payload


def new_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_api_token() -> tuple[str, str, str]:
    """Devuelve (token_visible_una_vez, prefijo, hash)."""
    prefix = "cisa_" + secrets.token_hex(4)
    raw = f"{prefix}_{secrets.token_urlsafe(32)}"
    return raw, prefix, token_hash(raw)


def constant_time_equals(left: str, right: str) -> bool:
    return secrets.compare_digest(left.encode("utf-8"), right.encode("utf-8"))
