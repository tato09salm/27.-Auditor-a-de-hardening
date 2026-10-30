"""Emisión de sesiones y serialización del usuario autenticado."""

from __future__ import annotations

from datetime import timedelta

from fastapi import Request, Response
from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import new_refresh_token, token_hash, utcnow
from app.models import Organization, RefreshSession, User
from app.schemas.auth import RoleOut, UserOut
from app.services.audit_log import client_ip


def serialize_user(user: User, organization: Organization | None = None) -> UserOut:
    permissions = sorted(
        {permission.code for role in user.roles for permission in role.permissions}
    )
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        is_active=user.is_active,
        must_change_password=user.must_change_password,
        last_login_at=user.last_login_at,
        created_at=user.created_at,
        roles=[RoleOut(code=role.code, name=role.name) for role in user.roles],
        permissions=permissions,
        organization_id=user.organization_id,
        organization_name=organization.name if organization else None,
    )


def create_refresh_session(db: Session, user: User, request: Request) -> tuple[str, RefreshSession]:
    raw_token = new_refresh_token()
    session = RefreshSession(
        user_id=user.id,
        token_hash=token_hash(raw_token),
        expires_at=utcnow() + timedelta(days=settings.refresh_token_days),
        ip_address=client_ip(request),
        user_agent=(request.headers.get("user-agent", "")[:300] or None),
    )
    db.add(session)
    db.flush()
    return raw_token, session


def set_refresh_cookie(response: Response, raw_token: str) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=raw_token,
        max_age=settings.refresh_token_days * 86400,
        httponly=True,
        secure=settings.cookie_secure,
        samesite=settings.cookie_samesite,
        path="/api/v1/auth",
        domain=settings.cookie_domain,
    )


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path="/api/v1/auth",
        domain=settings.cookie_domain,
        secure=settings.cookie_secure,
        httponly=True,
        samesite=settings.cookie_samesite,
    )
