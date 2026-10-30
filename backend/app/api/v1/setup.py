from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request, Response, status
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from app.api.deps import DbSession
from app.config import settings
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import create_access_token, hash_password, utcnow
from app.enums import LogResult
from app.models import Organization, Role, User
from app.reference_data import ensure_default_profile, seed_reference_data
from app.schemas.auth import SetupRequest, SetupStatus, TokenResponse
from app.services.audit_log import record_audit
from app.services.auth_service import (
    create_refresh_session,
    serialize_user,
    set_refresh_cookie,
)

router = APIRouter(prefix="/setup", tags=["Instalación inicial"])
setup_limiter = SlidingWindowLimiter(5, 600)


def _user_count(db: Session) -> int:
    return int(db.scalar(select(func.count()).select_from(User)) or 0)


@router.get("/status", response_model=SetupStatus)
def setup_status(db: DbSession) -> SetupStatus:
    count = _user_count(db)
    return SetupStatus(
        initialized=count > 0,
        organization_name=None,
        product_name=settings.app_name,
        version=settings.app_version,
    )


@router.post("/initialize", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def initialize(
    payload: SetupRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> TokenResponse:
    ip = request.client.host if request.client else "unknown"
    if not setup_limiter.check(ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"code": "rate_limited", "message": "Demasiados intentos de instalación."},
        )

    # Bloqueo transaccional para evitar dos administradores iniciales en carrera.
    db.execute(text("SELECT pg_advisory_xact_lock(918273645)"))
    if _user_count(db) > 0:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "already_initialized",
                "message": "La plataforma ya fue inicializada.",
            },
        )

    existing_slug = db.scalar(
        select(Organization).where(Organization.slug == payload.organization_slug)
    )
    if existing_slug is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "slug_taken", "message": "El identificador de organización ya existe."},
        )

    organization = Organization(name=payload.organization_name, slug=payload.organization_slug)
    db.add(organization)
    db.flush()

    admin_role = db.scalar(select(Role).where(Role.code == "admin"))
    if admin_role is None:
        seed_reference_data(db)
        admin_role = db.scalar(select(Role).where(Role.code == "admin"))
    if admin_role is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "seed_missing", "message": "No se pudo inicializar el catálogo de roles."},
        )

    user = User(
        organization_id=organization.id,
        email=str(payload.admin_email).strip().lower(),
        full_name=payload.admin_full_name.strip(),
        password_hash=hash_password(payload.admin_password),
        is_active=True,
        must_change_password=False,
        password_changed_at=utcnow(),
        roles=[admin_role],
    )
    db.add(user)
    db.flush()

    ensure_default_profile(db, organization.id, user.id)
    access_token, expires_in = create_access_token(str(user.id), str(organization.id))
    raw_refresh, _session = create_refresh_session(db, user, request)
    record_audit(
        db,
        action="setup.initialize",
        module="setup",
        organization_id=organization.id,
        user=user,
        resource_type="organization",
        resource_id=str(organization.id),
        request=request,
        changes={"organization_name": organization.name, "admin_email": user.email},
    )
    db.commit()
    set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=serialize_user(user, organization),
    )
