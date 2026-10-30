from __future__ import annotations

from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException, Request, status
from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import CurrentUser, DbSession, require_permission
from app.models import (
    AuditProfile,
    AuditProfileControl,
    CisBenchmark,
    CisControl,
    User,
)
from app.schemas.common import Message
from app.schemas.profiles import (
    BenchmarkOut,
    ControlOut,
    ProfileCreate,
    ProfileDetail,
    ProfileOut,
    ProfileUpdate,
)
from app.services.audit_log import record_audit

router = APIRouter(tags=["Perfiles CIS"])


def _profile_query(db: Session, profile_id: UUID, organization_id: UUID) -> AuditProfile:
    profile = db.scalar(
        select(AuditProfile)
        .where(
            AuditProfile.id == profile_id,
            AuditProfile.organization_id == organization_id,
        )
        .options(joinedload(AuditProfile.benchmark), selectinload(AuditProfile.controls))
    )
    if profile is None:
        raise HTTPException(status_code=404, detail="Perfil no encontrado.")
    return profile


def _profile_out(db: Session, profile: AuditProfile) -> ProfileOut:
    total = int(
        db.scalar(
            select(func.count())
            .select_from(AuditProfileControl)
            .where(AuditProfileControl.profile_id == profile.id)
        )
        or 0
    )
    enabled = int(
        db.scalar(
            select(func.count())
            .select_from(AuditProfileControl)
            .where(
                AuditProfileControl.profile_id == profile.id,
                AuditProfileControl.enabled.is_(True),
            )
        )
        or 0
    )
    return ProfileOut(
        **{column.name: getattr(profile, column.name) for column in AuditProfile.__table__.columns},
        benchmark_name=profile.benchmark.name if profile.benchmark else None,
        benchmark_version=profile.benchmark.version if profile.benchmark else None,
        control_count=total,
        enabled_control_count=enabled,
    )


def _set_default(db: Session, organization_id: UUID, profile_id: UUID) -> None:
    db.execute(
        update(AuditProfile)
        .where(
            AuditProfile.organization_id == organization_id,
            AuditProfile.id != profile_id,
            AuditProfile.is_default.is_(True),
        )
        .values(is_default=False)
    )


@router.get("/benchmarks", response_model=list[BenchmarkOut])
def list_benchmarks(
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("profiles:read")),
) -> list[BenchmarkOut]:
    benchmarks = db.scalars(select(CisBenchmark).order_by(CisBenchmark.name)).all()
    return [BenchmarkOut.model_validate(item) for item in benchmarks]


@router.get("/benchmarks/{benchmark_id}/controls", response_model=list[ControlOut])
def list_controls(
    benchmark_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("profiles:read")),
) -> list[ControlOut]:
    benchmark = db.get(CisBenchmark, benchmark_id)
    if benchmark is None:
        raise HTTPException(status_code=404, detail="Benchmark no encontrado.")
    controls = db.scalars(
        select(CisControl)
        .where(CisControl.benchmark_id == benchmark_id, CisControl.is_active.is_(True))
        .order_by(CisControl.code)
    ).all()
    return [ControlOut.model_validate(item) for item in controls]


@router.get("/profiles", response_model=list[ProfileOut])
def list_profiles(
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("profiles:read")),
) -> list[ProfileOut]:
    profiles = db.scalars(
        select(AuditProfile)
        .where(
            AuditProfile.organization_id == user.organization_id,
            AuditProfile.is_active.is_(True),
        )
        .options(joinedload(AuditProfile.benchmark))
        .order_by(AuditProfile.is_default.desc(), AuditProfile.name)
    ).all()
    return [_profile_out(db, profile) for profile in profiles]


@router.get("/profiles/{profile_id}", response_model=ProfileDetail)
def get_profile(
    profile_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("profiles:read")),
) -> ProfileDetail:
    profile = _profile_query(db, profile_id, user.organization_id)
    base = _profile_out(db, profile)
    rows = db.execute(
        select(CisControl, AuditProfileControl.enabled)
        .join(AuditProfileControl, AuditProfileControl.control_id == CisControl.id)
        .where(AuditProfileControl.profile_id == profile.id)
        .order_by(CisControl.code)
    ).all()
    controls = [
        ControlOut.model_validate(control).model_copy(update={"enabled": enabled})
        for control, enabled in rows
    ]
    return ProfileDetail(**base.model_dump(), controls=controls)


@router.post("/profiles", response_model=ProfileDetail, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("profiles:manage")),
) -> ProfileDetail:
    benchmark = db.get(CisBenchmark, payload.benchmark_id)
    if benchmark is None:
        raise HTTPException(status_code=422, detail="Benchmark inválido.")
    if payload.control_ids is None:
        control_ids = list(
            db.scalars(
                select(CisControl.id).where(
                    CisControl.benchmark_id == benchmark.id, CisControl.is_active.is_(True)
                )
            ).all()
        )
    else:
        control_ids = payload.control_ids
    controls = db.scalars(
        select(CisControl).where(
            CisControl.id.in_(control_ids),
            CisControl.benchmark_id == benchmark.id,
            CisControl.is_active.is_(True),
        )
    ).all()
    if len(controls) != len(control_ids):
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_controls", "message": "Algún control no pertenece al benchmark."},
        )
    if payload.is_default:
        _set_default(db, user.organization_id, UUID(int=0))
    profile = AuditProfile(
        organization_id=user.organization_id,
        benchmark_id=benchmark.id,
        name=payload.name.strip(),
        description=payload.description,
        is_default=payload.is_default,
        is_active=True,
        created_by_id=user.id,
    )
    db.add(profile)
    db.flush()
    for control in controls:
        db.add(AuditProfileControl(profile_id=profile.id, control_id=control.id, enabled=True))
    if payload.is_default:
        _set_default(db, user.organization_id, profile.id)
    record_audit(
        db,
        action="profiles.create",
        module="profiles",
        organization_id=user.organization_id,
        user=user,
        resource_type="audit_profile",
        resource_id=str(profile.id),
        request=request,
        changes={"name": profile.name, "benchmark": benchmark.name, "controls": len(controls)},
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "duplicate_profile", "message": "Ya existe un perfil con ese nombre."},
        ) from exc
    return get_profile(profile.id, user, db, user)


@router.patch("/profiles/{profile_id}", response_model=ProfileDetail)
def update_profile(
    profile_id: UUID,
    payload: ProfileUpdate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("profiles:manage")),
) -> ProfileDetail:
    profile = _profile_query(db, profile_id, user.organization_id)
    changes = {}
    if payload.name is not None:
        profile.name = payload.name.strip()
        changes["name"] = profile.name
    if payload.description is not None:
        profile.description = payload.description
    if payload.is_default is not None:
        profile.is_default = payload.is_default
        if payload.is_default:
            _set_default(db, user.organization_id, profile.id)
        changes["is_default"] = payload.is_default
    if payload.control_ids is not None:
        controls = db.scalars(
            select(CisControl).where(
                CisControl.id.in_(payload.control_ids),
                CisControl.benchmark_id == profile.benchmark_id,
                CisControl.is_active.is_(True),
            )
        ).all()
        if len(controls) != len(payload.control_ids):
            raise HTTPException(status_code=422, detail="Algún control no pertenece al benchmark.")
        db.execute(
            AuditProfileControl.__table__.delete().where(
                AuditProfileControl.profile_id == profile.id
            )
        )
        db.flush()
        for control in controls:
            db.add(
                AuditProfileControl(
                    profile_id=profile.id, control_id=control.id, enabled=True
                )
            )
        changes["controls"] = len(controls)
    record_audit(
        db,
        action="profiles.update",
        module="profiles",
        organization_id=user.organization_id,
        user=user,
        resource_type="audit_profile",
        resource_id=str(profile.id),
        request=request,
        changes=changes,
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "duplicate_profile", "message": "Ya existe un perfil con ese nombre."},
        ) from exc
    return get_profile(profile.id, user, db, user)
