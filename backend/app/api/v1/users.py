from __future__ import annotations

from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.api.deps import CurrentUser, DbSession, Pagination, require_permission, user_permission_codes
from app.core.security import hash_password, utcnow
from app.enums import LogResult
from app.models import Organization, RefreshSession, Role, User
from app.schemas.auth import (
    AdminPasswordReset,
    OrganizationOut,
    RoleOut,
    UserAdminOut,
    UserCreate,
    UserOut,
    UserUpdate,
)
from app.schemas.common import Message, Page
from app.services.audit_log import record_audit
from app.services.auth_service import serialize_user

router = APIRouter(tags=["Usuarios y roles"])


def _admin_out(db: Session, user: User) -> UserAdminOut:
    org = db.get(Organization, user.organization_id)
    base = serialize_user(user, org)
    return UserAdminOut(
        **base.model_dump(),
        failed_login_attempts=user.failed_login_attempts,
        locked_until=user.locked_until,
    )


def _active_admin_count(db: Session, organization_id: UUID) -> int:
    return int(
        db.scalar(
            select(func.count(func.distinct(User.id)))
            .select_from(User)
            .join(User.roles)
            .where(
                User.organization_id == organization_id,
                User.is_active.is_(True),
                Role.code == "admin",
            )
        )
        or 0
    )


def _resolve_roles(db: Session, codes: list[str]) -> list[Role]:
    roles = db.scalars(select(Role).where(Role.code.in_(codes))).all()
    found = {role.code for role in roles}
    unknown = set(codes) - found
    if unknown:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "invalid_roles", "message": f"Roles inválidos: {', '.join(unknown)}"},
        )
    return list(roles)


@router.get("/users/me", response_model=UserOut)
def get_me(user: CurrentUser, db: DbSession) -> UserOut:
    return serialize_user(user, db.get(Organization, user.organization_id))


@router.get("/organizations/me", response_model=OrganizationOut)
def get_organization(
    user: CurrentUser, db: DbSession, _: User = Depends(require_permission("dashboard:read"))
) -> OrganizationOut:
    org = db.get(Organization, user.organization_id)
    if org is None:
        raise HTTPException(status_code=404, detail="Organización no encontrada.")
    return OrganizationOut.model_validate(org)


@router.get("/roles", response_model=list[RoleOut])
def list_roles(
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("users:read")),
) -> list[RoleOut]:
    roles = db.scalars(select(Role).order_by(Role.id)).all()
    return [RoleOut.model_validate(role) for role in roles]


@router.get("/users", response_model=Page[UserAdminOut])
def list_users(
    user: CurrentUser,
    db: DbSession,
    page_params: Pagination,
    _: User = Depends(require_permission("users:read")),
    search: str | None = Query(default=None, max_length=100),
    role: str | None = Query(default=None, max_length=50),
    is_active: bool | None = None,
) -> Page[UserAdminOut]:
    page, page_size = page_params
    conditions = [User.organization_id == user.organization_id]
    if search:
        pattern = f"%{search.strip()}%"
        conditions.append(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))
    if is_active is not None:
        conditions.append(User.is_active.is_(is_active))
    query = select(User).where(*conditions)
    if role:
        query = query.join(User.roles).where(Role.code == role)
    total = int(
        db.scalar(select(func.count()).select_from(query.order_by(None).subquery())) or 0
    )
    users = db.scalars(
        query.options(selectinload(User.roles).selectinload(Role.permissions))
        .order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[_admin_out(db, item) for item in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/users/{user_id}", response_model=UserAdminOut)
def get_user(
    user_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("users:read")),
) -> UserAdminOut:
    target = db.scalar(
        select(User)
        .where(User.id == user_id, User.organization_id == user.organization_id)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    return _admin_out(db, target)


@router.post("/users", response_model=UserAdminOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("users:manage")),
) -> UserAdminOut:
    email = str(payload.email).strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "email_taken", "message": "Ya existe un usuario con ese correo."},
        )
    roles = _resolve_roles(db, payload.role_codes)
    new_user = User(
        organization_id=user.organization_id,
        email=email,
        full_name=payload.full_name.strip(),
        password_hash=hash_password(payload.password),
        is_active=True,
        must_change_password=payload.must_change_password,
        password_changed_at=utcnow(),
        roles=roles,
    )
    db.add(new_user)
    db.flush()
    record_audit(
        db,
        action="users.create",
        module="users",
        organization_id=user.organization_id,
        user=user,
        resource_type="user",
        resource_id=str(new_user.id),
        request=request,
        changes={"email": email, "roles": payload.role_codes},
    )
    db.commit()
    return _admin_out(db, new_user)


@router.patch("/users/{user_id}", response_model=UserAdminOut)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    request: Request,
    actor: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("users:manage")),
) -> UserAdminOut:
    target = db.scalar(
        select(User)
        .where(User.id == user_id, User.organization_id == actor.organization_id)
        .options(selectinload(User.roles).selectinload(Role.permissions))
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    if target.id == actor.id and payload.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "self_deactivate", "message": "No puede desactivar su propia cuenta."},
        )

    was_admin = "admin" in target.role_codes
    losing_admin = False
    if payload.role_codes is not None:
        new_roles = _resolve_roles(db, payload.role_codes)
        losing_admin = was_admin and "admin" not in {role.code for role in new_roles}
        target.roles = new_roles
    if payload.is_active is False and was_admin:
        losing_admin = True
    if losing_admin and target.is_active and _active_admin_count(db, actor.organization_id) <= 1:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "last_admin",
                "message": "No puede dejar la organización sin un administrador activo.",
            },
        )

    changes = {}
    if payload.full_name is not None:
        target.full_name = payload.full_name.strip()
        changes["full_name"] = target.full_name
    if payload.is_active is not None:
        target.is_active = payload.is_active
        if not payload.is_active:
            db.execute(
                update(RefreshSession)
                .where(
                    RefreshSession.user_id == target.id,
                    RefreshSession.revoked_at.is_(None),
                )
                .values(revoked_at=utcnow())
            )
        changes["is_active"] = payload.is_active
    if payload.role_codes is not None:
        changes["roles"] = payload.role_codes

    record_audit(
        db,
        action="users.update",
        module="users",
        organization_id=actor.organization_id,
        user=actor,
        resource_type="user",
        resource_id=str(target.id),
        request=request,
        changes=changes,
    )
    db.commit()
    return _admin_out(db, target)


@router.post("/users/{user_id}/reset-password", response_model=Message)
def admin_reset_password(
    user_id: UUID,
    payload: AdminPasswordReset,
    request: Request,
    actor: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("users:manage")),
) -> Message:
    target = db.scalar(
        select(User).where(User.id == user_id, User.organization_id == actor.organization_id)
    )
    if target is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado.")
    target.password_hash = hash_password(payload.new_password)
    target.must_change_password = payload.must_change_password
    target.password_changed_at = utcnow()
    target.failed_login_attempts = 0
    target.locked_until = None
    db.execute(
        update(RefreshSession)
        .where(RefreshSession.user_id == target.id, RefreshSession.revoked_at.is_(None))
        .values(revoked_at=utcnow())
    )
    record_audit(
        db,
        action="users.password.reset",
        module="users",
        organization_id=actor.organization_id,
        user=actor,
        resource_type="user",
        resource_id=str(target.id),
        request=request,
        changes={"must_change_password": payload.must_change_password},
    )
    db.commit()
    return Message(message="Contraseña restablecida y sesiones revocadas.")
