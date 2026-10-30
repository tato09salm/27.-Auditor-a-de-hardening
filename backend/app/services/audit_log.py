"""Registro centralizado de operaciones (append-only en PostgreSQL)."""

from __future__ import annotations

import ipaddress
from typing import Any
from uuid import UUID

from fastapi import Request
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import LogResult
from app.models import ApiToken, AuditLog, User

SENSITIVE_KEYS = {
    "password",
    "current_password",
    "new_password",
    "secret",
    "secret_value",
    "private_key",
    "token",
    "access_token",
    "refresh_token",
    "authorization",
    "api_key",
    "ciphertext",
    "credential",
    "host_key_fingerprint",
}


def redact(value: Any, depth: int = 0) -> Any:
    if depth > 6:
        return "[recortado]"
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key.lower() in SENSITIVE_KEYS:
                result[key] = "[redactado]"
            else:
                result[key] = redact(item, depth + 1)
        return result
    if isinstance(value, list):
        return [redact(item, depth + 1) for item in value[:100]]
    if isinstance(value, str):
        return value[:1000]
    if isinstance(value, (UUID,)):
        return str(value)
    return value


def _is_trusted_proxy(address: str | None) -> bool:
    if not address:
        return False
    try:
        parsed = ipaddress.ip_address(address)
    except ValueError:
        return False
    for entry in settings.trusted_proxy_list:
        try:
            if "/" in entry:
                if parsed in ipaddress.ip_network(entry, strict=False):
                    return True
            elif parsed == ipaddress.ip_address(entry):
                return True
        except ValueError:
            continue
    return False


def client_ip(request: Request | None) -> str | None:
    if request is None:
        return None
    direct = request.client.host if request.client else None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded and _is_trusted_proxy(direct):
        candidate = forwarded.split(",", 1)[0].strip()
        try:
            return str(ipaddress.ip_address(candidate))[:45]
        except ValueError:
            pass
    return direct[:45] if direct else None


def record_audit(
    db: Session,
    *,
    action: str,
    module: str,
    organization_id: UUID | None = None,
    user: User | None = None,
    api_token: ApiToken | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    result: LogResult = LogResult.SUCCESS,
    request: Request | None = None,
    changes: dict[str, Any] | None = None,
) -> AuditLog:
    entry = AuditLog(
        organization_id=organization_id,
        user_id=user.id if user else None,
        api_token_id=api_token.id if api_token else None,
        action=action,
        module=module,
        resource_type=resource_type,
        resource_id=str(resource_id) if resource_id is not None else None,
        result=result,
        ip_address=client_ip(request),
        request_id=getattr(request.state, "request_id", None) if request else None,
        user_agent=(request.headers.get("user-agent", "")[:300] if request else None),
        changes=redact(changes or {}),
    )
    db.add(entry)
    return entry
