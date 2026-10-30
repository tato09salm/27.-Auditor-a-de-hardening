"""Dependencias comunes: autenticación, RBAC, API keys y paginación."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.security import decode_access_token, token_hash, utcnow
from app.database import get_db
from app.models import ApiToken, Organization, Role, User

bearer_scheme = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


class AuthError(HTTPException):
    def __init__(self, detail: str = "No autenticado.", code: str = "unauthorized") -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": code, "message": detail},
            headers={"WWW-Authenticate": "Bearer"},
        )


def user_permission_codes(user: User) -> set[str]:
    return {permission.code for role in user.roles for permission in role.permissions}


def user_role_codes(user: User) -> list[str]:
    return sorted(role.code for role in user.roles)


def get_current_user(
    request: Request,
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise AuthError("Debe iniciar sesión.")
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise AuthError(str(exc), "invalid_token") from exc
    try:
        user_id = UUID(payload["sub"])
        org_id = UUID(payload["org"])
    except (KeyError, ValueError) as exc:
        raise AuthError("Token inválido.", "invalid_token") from exc
    user = db.scalar(
        select(User)
        .where(User.id == user_id, User.organization_id == org_id)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    if user is None or not user.is_active:
        raise AuthError("Usuario inactivo o inexistente.", "inactive_user")
    org = db.get(Organization, user.organization_id)
    if org is None or not org.is_active:
        raise AuthError("Organización inactiva.", "inactive_organization")
    now = datetime.now(timezone.utc)
    if user.locked_until and user.locked_until > now:
        raise AuthError("La cuenta está bloqueada temporalmente.", "locked")
    issued_at = payload.get("iat")
    if user.password_changed_at and issued_at:
        if float(issued_at) < user.password_changed_at.timestamp():
            raise AuthError("La sesión expiró por cambio de contraseña.", "stale_session")
    request.state.user = user
    if user.must_change_password:
        allowed_suffixes = (
            "/auth/change-password",
            "/auth/me",
            "/users/me",
        )
        if not request.url.path.endswith(allowed_suffixes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "password_change_required",
                    "message": "Debe cambiar la contraseña temporal antes de continuar.",
                },
            )
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(code: str):
    def dependency(user: CurrentUser) -> User:
        if code not in user_permission_codes(user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "forbidden", "message": "No tiene permiso para esta operación."},
            )
        return user

    return dependency


def require_any_permission(*codes: str):
    def dependency(user: CurrentUser) -> User:
        if not user_permission_codes(user).intersection(codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "forbidden", "message": "No tiene permiso para esta operación."},
            )
        return user

    return dependency


@dataclass
class ApiPrincipal:
    organization_id: UUID
    token: ApiToken
    scopes: set[str]


def require_api_scope(scope: str):
    def dependency(
        db: DbSession,
        request: Request,
        x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    ) -> ApiPrincipal:
        if not x_api_key:
            raise AuthError("Se requiere una API key de automatización.")
        hashed = token_hash(x_api_key)
        token = db.scalar(select(ApiToken).where(ApiToken.token_hash == hashed))
        if token is None or token.revoked_at is not None:
            raise AuthError("API key inválida o revocada.", "invalid_api_key")
        now = utcnow()
        if token.expires_at <= now:
            raise AuthError("API key expirada.", "expired_api_key")
        scopes = set(token.scopes or [])
        if scope not in scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "forbidden", "message": "La API key no posee el alcance requerido."},
            )
        org = db.get(Organization, token.organization_id)
        if org is None or not org.is_active:
            raise AuthError("Organización inactiva.", "inactive_organization")
        token.last_used_at = now
        request.state.api_token = token
        return ApiPrincipal(organization_id=token.organization_id, token=token, scopes=scopes)

    return dependency


def pagination_params(
    page: int = 1,
    page_size: int = 25,
) -> tuple[int, int]:
    from app.config import settings

    page = max(1, page)
    page_size = max(1, min(page_size, settings.max_page_size))
    return page, page_size


Pagination = Annotated[tuple[int, int], Depends(pagination_params)]
