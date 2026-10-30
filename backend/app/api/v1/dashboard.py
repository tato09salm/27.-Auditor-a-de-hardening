from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from uuid import UUID

from fastapi import Depends, APIRouter, Query
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import CurrentUser, DbSession, require_permission
from app.config import settings
from app.enums import FindingStatus, RecommendationStatus, RunStatus, Severity
from app.models import (
    AuditRun,
    CisControl,
    Finding,
    HardeningCheck,
    RemediationRecommendation,
    Server,
    User,
)
from app.schemas.dashboard import (
    DashboardResponse,
    DashboardSummary,
    RecentRun,
    ServerRisk,
    TopFailure,
    TrendPoint,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _range(date_from: date | None, date_to: date | None) -> tuple[datetime, datetime]:
    today = datetime.now(timezone.utc).date()
    start_date = date_from or (today - timedelta(days=30))
    end_date = date_to or today
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    if (end_date - start_date).days > settings.reports_max_period_days:
        start_date = end_date - timedelta(days=settings.reports_max_period_days)
    start = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return start, end


def _week_start(value: datetime) -> date:
    d = value.date()
    return d - timedelta(days=d.weekday())


@router.get("", response_model=DashboardResponse)
def dashboard(
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("dashboard:read")),
    date_from: date | None = None,
    date_to: date | None = None,
    server_id: UUID | None = None,
    os_family: str | None = Query(default=None, max_length=50),
    environment: str | None = Query(default=None, max_length=30),
    profile_id: UUID | None = None,
    severity: str | None = Query(default=None, max_length=20),
) -> DashboardResponse:
    start, end = _range(date_from, date_to)

    server_conditions = [Server.organization_id == user.organization_id]
    if server_id:
        server_conditions.append(Server.id == server_id)
    if os_family:
        server_conditions.append(Server.os_family == os_family)
    if environment:
        server_conditions.append(Server.environment == environment)
    servers = db.scalars(
        select(Server).where(*server_conditions).order_by(Server.name)
    ).all()
    server_ids = [server.id for server in servers]
    active_server_ids = [server.id for server in servers if server.is_active]

    run_conditions = [
        AuditRun.organization_id == user.organization_id,
        AuditRun.created_at.between(start, end),
        AuditRun.status == RunStatus.COMPLETED,
    ]
    if server_ids:
        run_conditions.append(AuditRun.server_id.in_(server_ids))
    else:
        run_conditions.append(AuditRun.server_id.in_([]))
    if profile_id:
        run_conditions.append(AuditRun.profile_id == profile_id)
    runs = db.scalars(
        select(AuditRun)
        .where(*run_conditions)
        .options(joinedload(AuditRun.server))
        .order_by(AuditRun.created_at.desc())
    ).all()

    latest_by_server: dict[UUID, AuditRun] = {}
    for run in runs:
        latest_by_server.setdefault(run.server_id, run)
    latest = [run for run in latest_by_server.values() if run.score is not None]
    average_score = (
        round(sum(float(run.score) for run in latest) / len(latest), 2) if latest else None
    )
    total_applicable = sum(run.applicable_count for run in latest)
    total_controls = sum(run.total_controls for run in latest)
    coverage = round(total_applicable / total_controls * 100, 2) if total_controls else 0.0

    finding_conditions = [
        Finding.organization_id == user.organization_id,
        Finding.status.notin_([FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE]),
    ]
    if server_ids:
        finding_conditions.append(Finding.server_id.in_(server_ids))
    else:
        finding_conditions.append(Finding.server_id.in_([]))
    if severity:
        finding_conditions.append(Finding.severity == severity)
    severity_rows = db.execute(
        select(Finding.severity, func.count())
        .where(*finding_conditions)
        .group_by(Finding.severity)
    ).all()
    counts = {item.value: 0 for item in Severity}
    for key, count in severity_rows:
        counts[key.value if hasattr(key, "value") else str(key)] = count
    active_findings = sum(counts.values())

    finding_ids = db.scalars(
        select(Finding.id).where(*finding_conditions)
    ).all() if active_findings else []
    pending_recommendations = int(
        db.scalar(
            select(func.count())
            .select_from(RemediationRecommendation)
            .where(
                RemediationRecommendation.organization_id == user.organization_id,
                RemediationRecommendation.status == RecommendationStatus.PENDING_REVIEW,
                RemediationRecommendation.finding_id.in_(finding_ids)
                if finding_ids
                else False,
            )
        )
        or 0
    )

    # Tendencia semanal
    buckets: dict[date, list[float]] = defaultdict(list)
    audit_counts: dict[date, int] = defaultdict(int)
    for run in runs:
        bucket = _week_start(run.created_at)
        audit_counts[bucket] += 1
        if run.score is not None:
            buckets[bucket].append(float(run.score))
    trend = [
        TrendPoint(
            period=bucket,
            average_score=round(sum(values) / len(values), 2) if values else None,
            audits=audit_counts[bucket],
        )
        for bucket, values in sorted(buckets.items())
    ]

    failure_query = (
        select(
            CisControl.id,
            CisControl.code,
            CisControl.cis_reference,
            CisControl.title,
            CisControl.severity,
            func.count(HardeningCheck.id).label("failure_count"),
            func.count(distinct(AuditRun.server_id)).label("affected_servers"),
        )
        .join(HardeningCheck, HardeningCheck.control_id == CisControl.id)
        .join(AuditRun, AuditRun.id == HardeningCheck.run_id)
        .where(
            AuditRun.organization_id == user.organization_id,
            AuditRun.created_at.between(start, end),
            HardeningCheck.status == "failed",
        )
    )
    if server_ids:
        failure_query = failure_query.where(AuditRun.server_id.in_(server_ids))
    if profile_id:
        failure_query = failure_query.where(AuditRun.profile_id == profile_id)
    failure_rows = db.execute(
        failure_query.group_by(CisControl.id)
        .order_by(func.count(HardeningCheck.id).desc())
        .limit(8)
    ).all()
    top_failures = [
        TopFailure(
            control_id=row.id,
            control_code=row.code,
            cis_reference=row.cis_reference,
            title=row.title,
            severity=row.severity.value if hasattr(row.severity, "value") else str(row.severity),
            failure_count=row.failure_count,
            affected_servers=row.affected_servers,
        )
        for row in failure_rows
    ]

    recent_runs = [
        RecentRun(
            id=run.id,
            server_id=run.server_id,
            server_name=run.server.name,
            status=run.status.value,
            score=float(run.score) if run.score is not None else None,
            failed_count=run.failed_count,
            created_at=run.created_at,
            is_simulated=run.is_simulated,
        )
        for run in runs[:8]
    ]

    risk_rows = db.execute(
        select(Finding.server_id, func.count())
        .where(
            *finding_conditions,
            Finding.severity.in_([Severity.CRITICAL, Severity.HIGH]),
        )
        .group_by(Finding.server_id)
    ).all()
    risk_counts = {row[0]: row[1] for row in risk_rows}
    riskiest: list[ServerRisk] = []
    for server in servers:
        if not server.is_active:
            continue
        latest_run = latest_by_server.get(server.id)
        severity_total = risk_counts.get(server.id, 0)
        if latest_run is None and severity_total == 0:
            continue
        critical = int(
            db.scalar(
                select(func.count())
                .select_from(Finding)
                .where(
                    Finding.server_id == server.id,
                    Finding.status.notin_([FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE]),
                    Finding.severity == Severity.CRITICAL,
                )
            )
            or 0
        )
        high = int(
            db.scalar(
                select(func.count())
                .select_from(Finding)
                .where(
                    Finding.server_id == server.id,
                    Finding.status.notin_([FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE]),
                    Finding.severity == Severity.HIGH,
                )
            )
            or 0
        )
        score = float(latest_run.score) if latest_run and latest_run.score is not None else None
        riskiest.append(
            ServerRisk(
                id=server.id,
                name=server.name,
                hostname=server.hostname,
                environment=server.environment.value,
                score=score,
                critical_findings=critical,
                high_findings=high,
                last_audit_at=server.last_audit_at,
                status=server.status.value,
            )
        )
    riskiest.sort(
        key=lambda item: (
            item.critical_findings * 10 + item.high_findings * 3 + (100 - (item.score or 0)) / 10
        ),
        reverse=True,
    )

    last_audit = max((run.created_at for run in runs), default=None)
    summary = DashboardSummary(
        total_servers=len(servers),
        active_servers=len(active_server_ids),
        audited_servers=len(latest_by_server),
        pending_servers=max(len(active_server_ids) - len(latest_by_server), 0),
        average_score=average_score,
        evaluation_coverage=coverage,
        findings_critical=counts["critical"],
        findings_high=counts["high"],
        findings_medium=counts["medium"],
        findings_low=counts["low"],
        findings_info=counts["info"],
        audits_in_period=len(runs),
        pending_recommendations=pending_recommendations,
        last_audit_at=last_audit,
    )
    return DashboardResponse(
        summary=summary,
        trend=trend,
        top_failures=top_failures,
        recent_runs=recent_runs,
        riskiest_servers=riskiest[:6],
        generated_at=datetime.now(timezone.utc),
        filters={
            "date_from": start.date().isoformat(),
            "date_to": end.date().isoformat(),
            "server_id": str(server_id) if server_id else None,
            "os_family": os_family,
            "environment": environment,
            "profile_id": str(profile_id) if profile_id else None,
            "severity": severity,
        },
    )
