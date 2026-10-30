from __future__ import annotations

import re
from datetime import datetime
from uuid import UUID

from fastapi import Depends, APIRouter, BackgroundTasks, Header, HTTPException, Query, Request, Response, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import CurrentUser, DbSession, Pagination, require_permission
from app.enums import RunStatus, TriggerType
from app.models import (
    AuditProfile,
    AuditProfileControl,
    AuditRun,
    CisBenchmark,
    CisControl,
    HardeningCheck,
    ScheduledAudit,
    Server,
    User,
)
from app.schemas.audits import (
    AuditRunCreate,
    AuditRunDetail,
    AuditRunOut,
    CheckOut,
    ScheduledAuditCreate,
    ScheduledAuditOut,
    ScheduledAuditUpdate,
)
from app.schemas.common import Message, Page
from app.services.audit_log import record_audit
from app.services.audit_runner import execute_audit_run
from app.services.schedules import ScheduleError, next_run

router = APIRouter(tags=["Auditorías"])
IDEMPOTENCY_RE = re.compile(r"^[A-Za-z0-9._:-]{8,100}$")


def _run_out(db: Session, run: AuditRun) -> AuditRunOut:
    triggered_by = db.get(User, run.triggered_by_id) if run.triggered_by_id else None
    return AuditRunOut(
        **{column.name: getattr(run, column.name) for column in AuditRun.__table__.columns},
        server_name=run.server.name if run.server else None,
        server_hostname=run.server.hostname if run.server else None,
        profile_name=run.profile.name if run.profile else None,
        triggered_by_name=triggered_by.full_name if isinstance(triggered_by, User) else None,
    )


def _next_run(cron_expression: str, timezone_name: str) -> datetime:
    try:
        return next_run(cron_expression, timezone_name)
    except ScheduleError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "invalid_cron", "message": str(exc)},
        ) from exc


def _validate_profile_for_server(
    db: Session, profile_id: UUID, server: Server, organization_id: UUID
) -> AuditProfile:
    profile = db.scalar(
        select(AuditProfile)
        .where(
            AuditProfile.id == profile_id,
            AuditProfile.organization_id == organization_id,
            AuditProfile.is_active.is_(True),
        )
        .options(joinedload(AuditProfile.benchmark))
    )
    if profile is None:
        raise HTTPException(status_code=422, detail="Perfil inválido.")
    benchmark = profile.benchmark
    if benchmark is None:
        raise HTTPException(status_code=422, detail="Perfil sin benchmark.")
    if benchmark.os_family != "linux" and benchmark.os_family != server.os_family.lower():
        raise HTTPException(
            status_code=422,
            detail={
                "code": "os_mismatch",
                "message": f"El perfil es para {benchmark.os_family} y el servidor es {server.os_family}.",
            },
        )
    control_count = int(
        db.scalar(
            select(func.count())
            .select_from(AuditProfileControl)
            .join(CisControl, CisControl.id == AuditProfileControl.control_id)
            .where(
                AuditProfileControl.profile_id == profile.id,
                AuditProfileControl.enabled.is_(True),
                CisControl.is_active.is_(True),
            )
        )
        or 0
    )
    if control_count == 0:
        raise HTTPException(status_code=422, detail="El perfil no tiene controles activos.")
    return profile


@router.post("/audits", response_model=AuditRunOut, status_code=status.HTTP_202_ACCEPTED)
def create_audit_run(
    payload: AuditRunCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    response: Response,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("audits:execute")),
    idempotency_key: str | None = Header(default=None, alias="X-Idempotency-Key"),
) -> AuditRunOut:
    if idempotency_key is not None and not IDEMPOTENCY_RE.match(idempotency_key):
        raise HTTPException(
            status_code=422,
            detail={
                "code": "invalid_idempotency_key",
                "message": "X-Idempotency-Key debe tener entre 8 y 100 caracteres seguros.",
            },
        )
    if idempotency_key:
        existing = db.scalar(
            select(AuditRun)
            .where(
                AuditRun.organization_id == user.organization_id,
                AuditRun.idempotency_key == idempotency_key,
            )
            .options(joinedload(AuditRun.server), joinedload(AuditRun.profile))
        )
        if existing:
            response.status_code = status.HTTP_200_OK
            return _run_out(db, existing)

    server = db.scalar(
        select(Server)
        .where(Server.id == payload.server_id, Server.organization_id == user.organization_id)
        .options(selectinload(Server.credential), joinedload(Server.default_profile))
    )
    if server is None:
        raise HTTPException(status_code=404, detail="Servidor no encontrado.")
    if not server.is_active:
        raise HTTPException(status_code=409, detail="El servidor está desactivado.")
    if not server.authorization_confirmed:
        raise HTTPException(
            status_code=409,
            detail={"code": "not_authorized", "message": "El servidor no está autorizado para auditoría."},
        )
    profile_id = payload.profile_id or server.default_profile_id
    if profile_id is None:
        raise HTTPException(status_code=422, detail="Seleccione un perfil de auditoría.")
    profile = _validate_profile_for_server(db, profile_id, server, user.organization_id)
    benchmark = db.get(CisBenchmark, profile.benchmark_id)
    if benchmark is None:
        raise HTTPException(status_code=422, detail="Benchmark no encontrado.")

    active = db.scalar(
        select(AuditRun).where(
            AuditRun.server_id == server.id,
            AuditRun.status.in_([RunStatus.QUEUED, RunStatus.RUNNING]),
        )
    )
    if active is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "code": "audit_in_progress",
                "message": "Ya existe una auditoría en curso para este servidor.",
                "run_id": str(active.id),
            },
        )

    run = AuditRun(
        organization_id=user.organization_id,
        server_id=server.id,
        profile_id=profile.id,
        benchmark_id=benchmark.id,
        benchmark_version=benchmark.version,
        status=RunStatus.QUEUED,
        trigger_type=TriggerType.MANUAL,
        triggered_by_id=user.id,
        idempotency_key=idempotency_key,
        request_id=getattr(request.state, "request_id", None),
        is_simulated=server.is_simulated,
    )
    db.add(run)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail={"code": "audit_in_progress", "message": "Ya existe una auditoría en curso."},
        ) from exc

    record_audit(
        db,
        action="audits.run.requested",
        module="audits",
        organization_id=user.organization_id,
        user=user,
        resource_type="audit_run",
        resource_id=str(run.id),
        request=request,
        changes={
            "server_id": str(server.id),
            "profile_id": str(profile.id),
            "simulated": server.is_simulated,
        },
    )
    db.commit()
    background_tasks.add_task(execute_audit_run, run.id)
    return _run_out(db, run)


@router.get("/audits", response_model=Page[AuditRunOut])
def list_audit_runs(
    user: CurrentUser,
    db: DbSession,
    page_params: Pagination,
    _: User = Depends(require_permission("audits:read")),
    server_id: UUID | None = None,
    run_status: str | None = Query(default=None, alias="status", max_length=20),
    date_from: datetime | None = None,
    date_to: datetime | None = None,
) -> Page[AuditRunOut]:
    page, page_size = page_params
    conditions = [AuditRun.organization_id == user.organization_id]
    if server_id:
        conditions.append(AuditRun.server_id == server_id)
    if run_status:
        conditions.append(AuditRun.status == run_status)
    if date_from:
        conditions.append(AuditRun.created_at >= date_from)
    if date_to:
        conditions.append(AuditRun.created_at <= date_to)
    total = int(db.scalar(select(func.count()).select_from(AuditRun).where(*conditions)) or 0)
    runs = db.scalars(
        select(AuditRun)
        .where(*conditions)
        .options(joinedload(AuditRun.server), joinedload(AuditRun.profile))
        .order_by(AuditRun.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[_run_out(db, run) for run in runs],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/audits/{run_id}", response_model=AuditRunDetail)
def get_audit_run(
    run_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("audits:read")),
) -> AuditRunDetail:
    run = db.scalar(
        select(AuditRun)
        .where(AuditRun.id == run_id, AuditRun.organization_id == user.organization_id)
        .options(
            joinedload(AuditRun.server),
            joinedload(AuditRun.profile),
            selectinload(AuditRun.checks).joinedload(HardeningCheck.control),
        )
    )
    if run is None:
        raise HTTPException(status_code=404, detail="Auditoría no encontrada.")
    base = _run_out(db, run)
    checks = []
    for check in sorted(run.checks, key=lambda item: item.control.code):
        checks.append(
            CheckOut(
                **{column.name: getattr(check, column.name) for column in HardeningCheck.__table__.columns},
                control_code=check.control.code,
                cis_reference=check.control.cis_reference,
                control_title=check.control.title,
                category=check.control.category,
                remediation_guidance=check.control.remediation_guidance,
                is_official_mapping=check.control.is_official_mapping,
                mapping_notes=check.control.mapping_notes,
            )
        )
    summary = run.summary or {}
    return AuditRunDetail(
        **base.model_dump(),
        checks=checks,
        findings_created=int(summary.get("findings_created", 0)),
        findings_resolved=int(summary.get("findings_resolved", 0)),
    )


@router.get("/schedules", response_model=list[ScheduledAuditOut])
def list_schedules(
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("audits:read")),
) -> list[ScheduledAuditOut]:
    schedules = db.scalars(
        select(ScheduledAudit)
        .where(ScheduledAudit.organization_id == user.organization_id)
        .order_by(ScheduledAudit.created_at.desc())
    ).all()
    return [
        ScheduledAuditOut(
            **{column.name: getattr(item, column.name) for column in ScheduledAudit.__table__.columns},
            server_name=item.server.name if item.server else None,
            profile_name=item.profile.name if item.profile else None,
        )
        for item in schedules
    ]


@router.post("/schedules", response_model=ScheduledAuditOut, status_code=status.HTTP_201_CREATED)
def create_schedule(
    payload: ScheduledAuditCreate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("schedules:manage")),
) -> ScheduledAuditOut:
    server = db.scalar(
        select(Server).where(
            Server.id == payload.server_id, Server.organization_id == user.organization_id
        )
    )
    if server is None:
        raise HTTPException(status_code=404, detail="Servidor no encontrado.")
    _validate_profile_for_server(db, payload.profile_id, server, user.organization_id)
    schedule = ScheduledAudit(
        organization_id=user.organization_id,
        name=payload.name.strip(),
        server_id=server.id,
        profile_id=payload.profile_id,
        cron_expression=payload.cron_expression,
        timezone=payload.timezone,
        is_enabled=payload.is_enabled,
        next_run_at=_next_run(payload.cron_expression, payload.timezone) if payload.is_enabled else None,
        created_by_id=user.id,
    )
    db.add(schedule)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="Ya existe una programación con ese nombre.") from exc
    record_audit(
        db,
        action="schedules.create",
        module="schedules",
        organization_id=user.organization_id,
        user=user,
        resource_type="scheduled_audit",
        resource_id=str(schedule.id),
        request=request,
        changes={"server_id": str(server.id), "cron": schedule.cron_expression},
    )
    db.commit()
    db.refresh(schedule)
    return ScheduledAuditOut(
        **{column.name: getattr(schedule, column.name) for column in ScheduledAudit.__table__.columns},
        server_name=schedule.server.name if schedule.server else None,
        profile_name=schedule.profile.name if schedule.profile else None,
    )


@router.patch("/schedules/{schedule_id}", response_model=ScheduledAuditOut)
def update_schedule(
    schedule_id: UUID,
    payload: ScheduledAuditUpdate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("schedules:manage")),
) -> ScheduledAuditOut:
    schedule = db.scalar(
        select(ScheduledAudit).where(
            ScheduledAudit.id == schedule_id,
            ScheduledAudit.organization_id == user.organization_id,
        )
    )
    if schedule is None:
        raise HTTPException(status_code=404, detail="Programación no encontrada.")
    if payload.profile_id is not None:
        _validate_profile_for_server(db, payload.profile_id, schedule.server, user.organization_id)
        schedule.profile_id = payload.profile_id
    if payload.name is not None:
        schedule.name = payload.name.strip()
    if payload.cron_expression is not None:
        schedule.cron_expression = payload.cron_expression
    if payload.timezone is not None:
        schedule.timezone = payload.timezone
    if payload.is_enabled is not None:
        schedule.is_enabled = payload.is_enabled
    schedule.next_run_at = (
        _next_run(schedule.cron_expression, schedule.timezone) if schedule.is_enabled else None
    )
    record_audit(
        db,
        action="schedules.update",
        module="schedules",
        organization_id=user.organization_id,
        user=user,
        resource_type="scheduled_audit",
        resource_id=str(schedule.id),
        request=request,
        changes=payload.model_dump(exclude_unset=True),
    )
    db.commit()
    return ScheduledAuditOut(
        **{column.name: getattr(schedule, column.name) for column in ScheduledAudit.__table__.columns},
        server_name=schedule.server.name if schedule.server else None,
        profile_name=schedule.profile.name if schedule.profile else None,
    )


@router.delete("/schedules/{schedule_id}", response_model=Message)
def disable_schedule(
    schedule_id: UUID,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("schedules:manage")),
) -> Message:
    schedule = db.scalar(
        select(ScheduledAudit).where(
            ScheduledAudit.id == schedule_id,
            ScheduledAudit.organization_id == user.organization_id,
        )
    )
    if schedule is None:
        raise HTTPException(status_code=404, detail="Programación no encontrada.")
    schedule.is_enabled = False
    schedule.next_run_at = None
    record_audit(
        db,
        action="schedules.disable",
        module="schedules",
        organization_id=user.organization_id,
        user=user,
        resource_type="scheduled_audit",
        resource_id=str(schedule.id),
        request=request,
    )
    db.commit()
    return Message(message="Programación deshabilitada.")
