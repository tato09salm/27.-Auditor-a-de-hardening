from __future__ import annotations

from datetime import timedelta

from fastapi import APIRouter, Cookie, HTTPException, Request, Response, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.api.deps import CurrentUser, DbSession
from app.config import settings
from app.core.rate_limit import SlidingWindowLimiter
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
    token_hash,
    utcnow,
    validate_password_strength,
    verify_password,
)
from app.enums import LogResult
from app.models import Organization, RefreshSession, Role, User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse, UserOut
from app.schemas.common import Message as CommonMessage
from app.services.audit_log import client_ip, record_audit
from app.services.auth_service import (
    clear_refresh_cookie,
    create_refresh_session,
    serialize_user,
    set_refresh_cookie,
)

router = APIRouter(prefix="/auth", tags=["Autenticación"])
login_limiter = SlidingWindowLimiter(
    settings.login_rate_max_requests, settings.login_rate_window_seconds
)
ip_login_limiter = SlidingWindowLimiter(
    settings.login_rate_max_requests * 3, settings.login_rate_window_seconds
)


def _login_failure(
    db: Session,
    request: Request,
    email: str,
    user: User | None,
    result: LogResult = LogResult.FAILURE,
) -> None:
    record_audit(
        db,
        action="auth.login.failed",
        module="auth",
        organization_id=user.organization_id if user else None,
        user=user,
        result=result,
        request=request,
        changes={"email": email},
    )
    db.commit()


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: DbSession,
) -> TokenResponse:
    email = str(payload.email).strip().lower()
    ip = client_ip(request) or "unknown"
    key = f"{ip}:{email}"
    if not ip_login_limiter.check(f"ip:{ip}") or not login_limiter.check(key):
        record_audit(
            db,
            action="auth.login.rate_limited",
            module="auth",
            result=LogResult.DENIED,
            request=request,
            changes={"email": email},
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "code": "rate_limited",
                "message": "Demasiados intentos. Espere unos minutos antes de reintentar.",
            },
        )

    user = db.scalar(
        select(User)
        .where(User.email == email)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    if user is None:
        verify_password(payload.password, DUMMY_PASSWORD_HASH)
        _login_failure(db, request, email, None)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_credentials", "message": "Credenciales inválidas."},
        )

    now = utcnow()
    if not user.is_active or (user.locked_until and user.locked_until > now):
        _login_failure(db, request, email, user, LogResult.DENIED)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_credentials",
                "message": "Credenciales inválidas o cuenta bloqueada temporalmente.",
            },
        )

    if not verify_password(payload.password, user.password_hash):
        user.failed_login_attempts += 1
        if user.failed_login_attempts >= settings.login_max_attempts:
            user.locked_until = now + timedelta(minutes=settings.login_lockout_minutes)
        _login_failure(db, request, email, user)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "invalid_credentials",
                "message": "Credenciales inválidas o cuenta bloqueada temporalmente.",
            },
        )

    org = db.get(Organization, user.organization_id)
    if org is None or not org.is_active:
        _login_failure(db, request, email, user, LogResult.DENIED)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "inactive_organization", "message": "Organización inactiva."},
        )

    user.failed_login_attempts = 0
    user.locked_until = None
    user.last_login_at = now
    access_token, expires_in = create_access_token(str(user.id), str(user.organization_id))
    raw_refresh, _session = create_refresh_session(db, user, request)
    login_limiter.reset(key)
    record_audit(
        db,
        action="auth.login.success",
        module="auth",
        organization_id=user.organization_id,
        user=user,
        request=request,
    )
    db.commit()
    set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=serialize_user(user, org),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    request: Request,
    response: Response,
    db: DbSession,
    refresh_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
) -> TokenResponse:
    if not refresh_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "no_session", "message": "Sesión no encontrada."},
        )
    session = db.scalar(
        select(RefreshSession).where(RefreshSession.token_hash == token_hash(refresh_cookie))
    )
    if session is None:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "invalid_session", "message": "Sesión inválida."},
        )

    now = utcnow()
    if session.revoked_at is not None:
        # Reutilización de un refresh token ya rotado: posible robo. Se revocan
        # todas las sesiones del usuario y se registra el evento.
        db.execute(
            update(RefreshSession)
            .where(
                RefreshSession.user_id == session.user_id,
                RefreshSession.revoked_at.is_(None),
            )
            .values(revoked_at=now)
        )
        record_audit(
            db,
            action="auth.refresh.reuse_detected",
            module="auth",
            result=LogResult.DENIED,
            request=request,
            changes={"user_id": session.user_id},
        )
        db.commit()
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "session_reuse", "message": "Sesión invalidada por seguridad."},
        )

    if session.expires_at <= now:
        session.revoked_at = now
        db.commit()
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "expired_session", "message": "La sesión expiró."},
        )

    user = db.scalar(
        select(User)
        .where(User.id == session.user_id, User.is_active.is_(True))
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    if user is None:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "inactive_user", "message": "Usuario inactivo."},
        )
    org = db.get(Organization, user.organization_id)
    if org is None or not org.is_active:
        clear_refresh_cookie(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "inactive_organization", "message": "Organización inactiva."},
        )

    raw_refresh, new_session = create_refresh_session(db, user, request)
    session.revoked_at = now
    session.last_used_at = now
    session.replaced_by_id = new_session.id
    access_token, expires_in = create_access_token(str(user.id), str(user.organization_id))
    db.commit()
    set_refresh_cookie(response, raw_refresh)
    return TokenResponse(
        access_token=access_token,
        expires_in=expires_in,
        user=serialize_user(user, org),
    )


@router.post("/logout", response_model=CommonMessage)
def logout(
    request: Request,
    response: Response,
    db: DbSession,
    refresh_cookie: str | None = Cookie(default=None, alias=settings.refresh_cookie_name),
) -> CommonMessage:
    if refresh_cookie:
        session = db.scalar(
            select(RefreshSession).where(RefreshSession.token_hash == token_hash(refresh_cookie))
        )
        if session is not None and session.revoked_at is None:
            session.revoked_at = utcnow()
            user = db.get(User, session.user_id)
            record_audit(
                db,
                action="auth.logout",
                module="auth",
                organization_id=user.organization_id if user else None,
                user=user,
                request=request,
            )
            db.commit()
    clear_refresh_cookie(response)
    return CommonMessage(message="Sesión cerrada.")


@router.get("/me", response_model=UserOut)
def me_alias(user: CurrentUser, db: DbSession) -> UserOut:
    org = db.get(Organization, user.organization_id)
    return serialize_user(user, org)


@router.post("/change-password", response_model=CommonMessage)
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    response: Response,
    user: CurrentUser,
    db: DbSession,
) -> CommonMessage:
    if not verify_password(payload.current_password, user.password_hash):
        record_audit(
            db,
            action="auth.password.change_failed",
            module="auth",
            organization_id=user.organization_id,
            user=user,
            result=LogResult.FAILURE,
            request=request,
        )
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "invalid_password", "message": "La contraseña actual no es correcta."},
        )
    try:
        validate_password_strength(payload.new_password, user.email)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "weak_password", "message": str(exc)},
        ) from exc
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "same_password", "message": "La nueva contraseña debe ser diferente."},
        )
    user.password_hash = hash_password(payload.new_password)
    user.password_changed_at = utcnow()
    user.must_change_password = False
    db.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == user.id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    record_audit(
        db,
        action="auth.password.changed",
        module="auth",
        organization_id=user.organization_id,
        user=user,
        request=request,
    )
    db.commit()
    clear_refresh_cookie(response)
    return CommonMessage(message="Contraseña actualizada. Inicie sesión nuevamente.")
