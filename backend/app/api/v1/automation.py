"""Endpoints acotados para n8n. Usan API keys con alcance, nunca JWT de usuario."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import ApiPrincipal, DbSession, require_api_scope
from app.enums import (
    CheckStatus,
    FindingStatus,
    LogResult,
    RecommendationSource,
    RecommendationStatus,
    ReportFormat,
    ReportType,
    RunStatus,
    TriggerType,
)
from app.models import (
    AuditProfile,
    AuditProfileControl,
    AuditRun,
    CisBenchmark,
    CisControl,
    Finding,
    HardeningCheck,
    RemediationRecommendation,
    ScheduledAudit,
    Server,
    User,
)
from app.schemas.reports import ReportCreate
from app.services.ai_service import (
    AIInvalidResponseError,
    AIUnavailableError,
    AIContext,
    build_recommendation,
)
from app.services.audit_log import record_audit
from app.services.audit_runner import execute_audit_run
from app.services.reports_service import create_report
from app.services.schedules import ScheduleError, next_run

router = APIRouter(prefix="/automation", tags=["Automatización n8n"])
ACTIVE_FINDING_STATUSES = [
    FindingStatus.DETECTED,
    FindingStatus.IN_REVIEW,
    FindingStatus.CORRECTION_PLANNED,
    FindingStatus.FIXED_PENDING_VALIDATION,
    FindingStatus.RISK_ACCEPTED,
]


class AutomationRunItem(BaseModel):
    schedule_id: UUID | None = None
    run_id: UUID | None = None
    status: str
    message: str | None = None


class AutomationRunsResponse(BaseModel):
    requested_at: datetime
    due_schedules: int
    runs_started: int
    items: list[AutomationRunItem]


class RecommendationRefreshResponse(BaseModel):
    requested_at: datetime
    generated: int
    failed: int
    items: list[dict[str, Any]]


class PersistentFinding(BaseModel):
    id: UUID
    server_name: str
    title: str
    severity: str
    status: str
    days_open: int
    last_seen_at: datetime


class PersistentFindingsResponse(BaseModel):
    requested_at: datetime
    days: int
    total: int
    items: list[PersistentFinding]


class BatchReportRequest(BaseModel):
    format: ReportFormat = ReportFormat.PDF
    period_start: datetime | None = None
    period_end: datetime | None = None
    server_ids: list[UUID] | None = Field(default=None, max_length=20)

    @field_validator("period_end")
    @classmethod
    def validate_period(cls, value: datetime | None) -> datetime | None:
        return value


class BatchReportItem(BaseModel):
    server_id: UUID
    report_id: UUID | None = None
    status: str
    message: str | None = None


class BatchReportResponse(BaseModel):
    generated: int
    failed: int
    items: list[BatchReportItem]


@router.post("/audits/run-due", response_model=AutomationRunsResponse)
def run_due_audits(
    request: Request,
    background_tasks: BackgroundTasks,
    db: DbSession,
    principal: ApiPrincipal = Depends(require_api_scope("automation:execute")),
) -> AutomationRunsResponse:
    now = datetime.now(timezone.utc)
    due_ids = db.scalars(
        select(ScheduledAudit.id)
        .where(
            ScheduledAudit.organization_id == principal.organization_id,
            ScheduledAudit.is_enabled.is_(True),
            ScheduledAudit.next_run_at.is_not(None),
            ScheduledAudit.next_run_at <= now,
        )
        .with_for_update(skip_locked=True)
    ).all()
    schedules = (
        db.scalars(
            select(ScheduledAudit)
            .where(ScheduledAudit.id.in_(due_ids))
            .options(
                joinedload(ScheduledAudit.server).selectinload(Server.credential),
                joinedload(ScheduledAudit.profile).joinedload(AuditProfile.benchmark),
            )
        ).all()
        if due_ids
        else []
    )
    items: list[AutomationRunItem] = []
    started = 0
    for schedule in schedules:
        server = schedule.server
        profile = schedule.profile
        try:
            schedule.next_run_at = next_run(schedule.cron_expression, schedule.timezone)
        except ScheduleError as exc:
            schedule.next_run_at = None
            schedule.is_enabled = False
            items.append(
                AutomationRunItem(
                    schedule_id=schedule.id,
                    status="skipped",
                    message=f"Programación inválida: {exc}",
                )
            )
            continue
        if server is None or not server.is_active:
            items.append(
                AutomationRunItem(
                    schedule_id=schedule.id, status="skipped", message="Servidor inactivo."
                )
            )
            continue
        if not server.authorization_confirmed:
            items.append(
                AutomationRunItem(
                    schedule_id=schedule.id, status="skipped", message="Servidor no autorizado."
                )
            )
            continue
        if profile is None or profile.benchmark is None:
            items.append(
                AutomationRunItem(
                    schedule_id=schedule.id, status="skipped", message="Perfil inválido."
                )
            )
            continue
        if profile.benchmark.os_family not in ("linux", server.os_family.lower()):
            items.append(
                AutomationRunItem(
                    schedule_id=schedule.id,
                    status="skipped",
                    message="Perfil incompatible con el sistema operativo.",
                )
            )
            continue
        active = db.scalar(
            select(AuditRun.id).where(
                AuditRun.server_id == server.id,
                AuditRun.status.in_([RunStatus.QUEUED, RunStatus.RUNNING]),
            )
        )
        if active:
            items.append(
                AutomationRunItem(
                    schedule_id=schedule.id,
                    status="skipped",
                    message="Ya existe una auditoría en curso.",
                )
            )
            continue
        run = AuditRun(
            organization_id=principal.organization_id,
            server_id=server.id,
            profile_id=profile.id,
            benchmark_id=profile.benchmark_id,
            benchmark_version=profile.benchmark.version,
            status=RunStatus.QUEUED,
            trigger_type=TriggerType.SCHEDULE,
            scheduled_audit_id=schedule.id,
            request_id=getattr(request.state, "request_id", None),
            is_simulated=server.is_simulated,
        )
        try:
            with db.begin_nested():
                db.add(run)
                db.flush()
        except IntegrityError:
            items.append(
                AutomationRunItem(
                    schedule_id=schedule.id,
                    status="skipped",
                    message="Ejecución duplicada detectada.",
                )
            )
            continue
        schedule.last_run_id = run.id
        started += 1
        items.append(
            AutomationRunItem(schedule_id=schedule.id, run_id=run.id, status="queued")
        )
    record_audit(
        db,
        action="automation.audits.run_due",
        module="automation",
        organization_id=principal.organization_id,
        api_token=principal.token,
        resource_type="scheduled_audit",
        result=LogResult.SUCCESS,
        request=request,
        changes={"due": len(schedules), "started": started},
    )
    db.commit()
    for item in items:
        if item.run_id and item.status == "queued":
            background_tasks.add_task(execute_audit_run, item.run_id)
    return AutomationRunsResponse(
        requested_at=now,
        due_schedules=len(schedules),
        runs_started=started,
        items=items,
    )


@router.post("/recommendations/refresh", response_model=RecommendationRefreshResponse)
def refresh_recommendations(
    request: Request,
    db: DbSession,
    limit: int = Query(default=2, ge=1, le=5),
    principal: ApiPrincipal = Depends(require_api_scope("automation:recommendations")),
) -> RecommendationRefreshResponse:
    token_creator = db.get(User, principal.token.created_by_id) if principal.token.created_by_id else None
    pending_exists = exists(
        select(RemediationRecommendation.id).where(
            RemediationRecommendation.finding_id == Finding.id,
            RemediationRecommendation.status.in_(
                [RecommendationStatus.PENDING_REVIEW, RecommendationStatus.APPROVED]
            ),
        )
    )
    finding_ids = db.scalars(
        select(Finding.id)
        .where(
            Finding.organization_id == principal.organization_id,
            Finding.status.in_(ACTIVE_FINDING_STATUSES),
            ~pending_exists,
        )
        .order_by(Finding.last_seen_at.desc())
        .limit(limit)
        .with_for_update(skip_locked=True)
    ).all()
    findings = (
        db.scalars(
            select(Finding)
            .where(Finding.id.in_(finding_ids))
            .options(joinedload(Finding.control), joinedload(Finding.server))
        ).all()
        if finding_ids
        else []
    )
    results: list[dict[str, Any]] = []
    generated = 0
    failed = 0
    for finding in findings:
        check = db.scalar(
            select(HardeningCheck).where(
                HardeningCheck.run_id == finding.last_seen_run_id,
                HardeningCheck.control_id == finding.control_id,
            )
        )
        if check is None:
            failed += 1
            results.append(
                {"finding_id": str(finding.id), "status": "failed", "error": "Sin evidencia."}
            )
            continue
        try:
            data = build_recommendation(
                AIContext(
                    finding=finding,
                    control=finding.control,
                    server=finding.server,
                    check=check,
                )
            )
        except (AIUnavailableError, AIInvalidResponseError) as exc:
            failed += 1
            results.append(
                {"finding_id": str(finding.id), "status": "failed", "error": str(exc)}
            )
            continue
        recommendation = RemediationRecommendation(
            organization_id=principal.organization_id,
            finding_id=finding.id,
            check_id=check.id,
            source=RecommendationSource.AI,
            provider=data["provider"],
            model=data["model"],
            status=RecommendationStatus.PENDING_REVIEW,
            payload=data["payload"],
            confidence=Decimal(str(data["confidence"])),
            validation_status=data["validation_status"],
            validation_warnings=data["warnings"],
            flagged_commands=data["flags"],
            created_by_id=token_creator.id if token_creator else None,
        )
        db.add(recommendation)
        db.flush()
        generated += 1
        results.append(
            {
                "finding_id": str(finding.id),
                "recommendation_id": str(recommendation.id),
                "status": "pending_review",
                "validation_status": recommendation.validation_status,
            }
        )
    record_audit(
        db,
        action="automation.recommendations.refresh",
        module="automation",
        organization_id=principal.organization_id,
        api_token=principal.token,
        request=request,
        changes={"generated": generated, "failed": failed},
    )
    db.commit()
    return RecommendationRefreshResponse(
        requested_at=datetime.now(timezone.utc),
        generated=generated,
        failed=failed,
        items=results,
    )


@router.post("/findings/refresh", response_model=PersistentFindingsResponse)
def refresh_findings(
    request: Request,
    db: DbSession,
    days: int = Query(default=30, ge=1, le=365),
    principal: ApiPrincipal = Depends(require_api_scope("automation:execute")),
) -> PersistentFindingsResponse:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=days)
    findings = db.scalars(
        select(Finding)
        .where(
            Finding.organization_id == principal.organization_id,
            Finding.status.in_(ACTIVE_FINDING_STATUSES),
            Finding.first_seen_at <= cutoff,
        )
        .options(joinedload(Finding.server))
        .order_by(Finding.severity.desc(), Finding.first_seen_at.asc())
        .limit(100)
    ).all()
    items = [
        PersistentFinding(
            id=finding.id,
            server_name=finding.server.name if finding.server else "-",
            title=finding.title,
            severity=finding.severity.value,
            status=finding.status.value,
            days_open=max((now - finding.first_seen_at).days, 0),
            last_seen_at=finding.last_seen_at,
        )
        for finding in findings
    ]
    record_audit(
        db,
        action="automation.findings.refresh",
        module="automation",
        organization_id=principal.organization_id,
        api_token=principal.token,
        request=request,
        changes={"persistent": len(items), "days": days},
    )
    db.commit()
    return PersistentFindingsResponse(requested_at=now, days=days, total=len(items), items=items)


@router.post("/reports/batch", response_model=BatchReportResponse)
def batch_reports(
    payload: BatchReportRequest,
    request: Request,
    db: DbSession,
    principal: ApiPrincipal = Depends(require_api_scope("automation:reports")),
) -> BatchReportResponse:
    creator = db.get(User, principal.token.created_by_id) if principal.token.created_by_id else None
    if creator is None:
        raise HTTPException(status_code=422, detail="El token no tiene un usuario creador válido.")
    conditions = [
        Server.organization_id == principal.organization_id,
        Server.is_active.is_(True),
    ]
    if payload.server_ids:
        conditions.append(Server.id.in_(payload.server_ids))
    servers = db.scalars(select(Server).where(*conditions).limit(20)).all()
    items: list[BatchReportItem] = []
    generated = 0
    failed = 0
    for server in servers:
        try:
            report = create_report(
                db,
                creator,
                ReportCreate(
                    report_type=ReportType.EXECUTIVE,
                    format=payload.format,
                    server_id=server.id,
                    period_start=payload.period_start,
                    period_end=payload.period_end,
                ),
            )
            generated += 1
            items.append(
                BatchReportItem(server_id=server.id, report_id=report.id, status="generated")
            )
        except Exception as exc:  # noqa: BLE001
            db.rollback()
            failed += 1
            items.append(
                BatchReportItem(
                    server_id=server.id,
                    status="failed",
                    message=str(exc)[:300] if isinstance(exc, ValueError) else "Error de generación.",
                )
            )
    record_audit(
        db,
        action="automation.reports.batch",
        module="automation",
        organization_id=principal.organization_id,
        api_token=principal.token,
        request=request,
        changes={"generated": generated, "failed": failed},
    )
    db.commit()
    return BatchReportResponse(generated=generated, failed=failed, items=items)
