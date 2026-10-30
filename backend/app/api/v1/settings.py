from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException, Request, status
from sqlalchemy import select

from app.api.deps import CurrentUser, DbSession, require_permission
from app.config import settings
from app.core.security import new_api_token, utcnow
from app.models import ApiToken, User
from app.schemas.auth import ApiTokenCreate, ApiTokenCreated, ApiTokenOut
from app.schemas.common import Message
from app.schemas.logs import SystemInfo
from app.services.ai_service import ai_health
from app.services.audit_log import record_audit

router = APIRouter(prefix="/settings", tags=["Configuración"])


def _token_out(token: ApiToken) -> ApiTokenOut:
    return ApiTokenOut.model_validate(token)


@router.get("", response_model=SystemInfo)
def system_info(
    user: CurrentUser,
    _: User = Depends(require_permission("settings:manage")),
) -> SystemInfo:
    return SystemInfo(
        product=settings.app_name,
        version=settings.app_version,
        environment=settings.environment,
        ai=ai_health(),
        simulated_connector_enabled=settings.enable_simulated_connector,
        private_targets_enabled=settings.audit_allow_private_targets,
        reports_storage=str(settings.reports_path),
        audit_max_concurrent_runs=settings.audit_max_concurrent_runs,
    )


@router.get("/api-tokens", response_model=list[ApiTokenOut])
def list_api_tokens(
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("settings:manage")),
) -> list[ApiTokenOut]:
    tokens = db.scalars(
        select(ApiToken)
        .where(ApiToken.organization_id == user.organization_id)
        .order_by(ApiToken.created_at.desc())
    ).all()
    return [_token_out(token) for token in tokens]


@router.post(
    "/api-tokens", response_model=ApiTokenCreated, status_code=status.HTTP_201_CREATED
)
def create_api_token(
    payload: ApiTokenCreate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("settings:manage")),
) -> ApiTokenCreated:
    raw, prefix, hashed = new_api_token()
    token = ApiToken(
        organization_id=user.organization_id,
        name=payload.name.strip(),
        token_prefix=prefix,
        token_hash=hashed,
        scopes=payload.scopes,
        created_by_id=user.id,
        expires_at=utcnow() + timedelta(days=payload.expires_in_days),
    )
    db.add(token)
    db.flush()
    record_audit(
        db,
        action="settings.api_token.create",
        module="settings",
        organization_id=user.organization_id,
        user=user,
        resource_type="api_token",
        resource_id=str(token.id),
        request=request,
        changes={"name": token.name, "scopes": payload.scopes},
    )
    db.commit()
    return ApiTokenCreated(
        **_token_out(token).model_dump(),
        token=raw,
    )


@router.delete("/api-tokens/{token_id}", response_model=Message)
def revoke_api_token(
    token_id: UUID,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("settings:manage")),
) -> Message:
    token = db.scalar(
        select(ApiToken).where(
            ApiToken.id == token_id, ApiToken.organization_id == user.organization_id
        )
    )
    if token is None:
        raise HTTPException(status_code=404, detail="Token no encontrado.")
    if token.revoked_at is None:
        token.revoked_at = utcnow()
        record_audit(
            db,
            action="settings.api_token.revoke",
            module="settings",
            organization_id=user.organization_id,
            user=user,
            resource_type="api_token",
            resource_id=str(token.id),
            request=request,
        )
        db.commit()
    return Message(message="Token revocado.")
