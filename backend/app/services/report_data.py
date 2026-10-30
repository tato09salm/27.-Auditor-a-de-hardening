"""Recopilación de datos verificables para reportes. Nada se inventa en el render."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, time, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.enums import FindingStatus, RecommendationStatus, RunStatus, Severity
from app.models import (
    AuditRun,
    CisControl,
    Finding,
    HardeningCheck,
    Organization,
    RemediationRecommendation,
    Server,
    User,
)

LIMITATIONS = [
    "Este reporte evalúa únicamente los controles incluidos en el perfil y no constituye una certificación CIS.",
    "Una configuración conforme no garantiza la ausencia de vulnerabilidades ni de otros riesgos.",
    "Las comprobaciones son de solo lectura y no modifican la configuración del servidor.",
    "Los controles marcados como internos no son un mapeo oficial de CIS.",
    "La evidencia puede haber sido truncada por límites de tamaño; la evidencia completa está disponible en la plataforma.",
]


def _date_range(start: date | None, end: date | None) -> tuple[datetime, datetime]:
    today = datetime.now(timezone.utc).date()
    start_date = start or (today - timedelta(days=30))
    end_date = end or today
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return start_dt, end_dt


def _severity_counts(findings: list[Finding]) -> dict[str, int]:
    counts = {item.value: 0 for item in Severity}
    for finding in findings:
        counts[finding.severity.value] += 1
    return counts


def technical_report_data(
    db: Session, organization_id: UUID, run_id: UUID, generated_by: User
) -> dict[str, Any]:
    run = db.scalar(
        select(AuditRun)
        .where(AuditRun.id == run_id, AuditRun.organization_id == organization_id)
        .options(
            joinedload(AuditRun.server),
            joinedload(AuditRun.profile),
            joinedload(AuditRun.benchmark),
            selectinload(AuditRun.checks).joinedload(HardeningCheck.control),
        )
    )
    if run is None:
        raise ValueError("Auditoría no encontrada.")
    organization = db.get(Organization, organization_id)
    findings = db.scalars(
        select(Finding)
        .where(
            Finding.organization_id == organization_id,
            Finding.server_id == run.server_id,
        )
        .options(joinedload(Finding.control))
        .order_by(Finding.last_seen_at.desc())
    ).all()
    active_findings = [
        finding
        for finding in findings
        if finding.status not in (FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE)
    ]
    finding_ids = [finding.id for finding in findings]
    recommendations = (
        db.scalars(
            select(RemediationRecommendation)
            .where(
                RemediationRecommendation.finding_id.in_(finding_ids),
                RemediationRecommendation.status == RecommendationStatus.APPROVED,
            )
            .order_by(RemediationRecommendation.reviewed_at.desc())
        ).all()
        if finding_ids
        else []
    )
    checks = []
    for check in sorted(run.checks, key=lambda item: item.control.code):
        control = check.control
        evidence = check.evidence or {}
        checks.append(
            {
                "code": control.code,
                "cis_reference": control.cis_reference,
                "title": control.title,
                "category": control.category,
                "severity": control.severity.value,
                "status": check.status.value,
                "observed": check.observed_value or "",
                "evidence_excerpt": str(evidence.get("stdout", ""))[:1800],
                "error": check.error_message or "",
                "official": control.is_official_mapping,
                "mapping_notes": control.mapping_notes or "",
                "guidance": control.remediation_guidance,
            }
        )
    return {
        "report_type": "technical",
        "generated_at": datetime.now(timezone.utc),
        "generated_by": generated_by.full_name,
        "organization": organization,
        "server": run.server,
        "profile": run.profile,
        "benchmark": run.benchmark,
        "run": run,
        "checks": checks,
        "findings": active_findings,
        "all_findings_count": len(findings),
        "recommendations": recommendations,
        "severity_counts": _severity_counts(active_findings),
        "limitations": LIMITATIONS,
        "score": float(run.score) if run.score is not None else None,
        "is_simulated": run.is_simulated,
    }


def _latest_runs(
    db: Session,
    organization_id: UUID,
    start: datetime,
    end: datetime,
    server_id: UUID | None = None,
) -> list[AuditRun]:
    conditions = [
        AuditRun.organization_id == organization_id,
        AuditRun.created_at.between(start, end),
        AuditRun.status == RunStatus.COMPLETED,
    ]
    if server_id:
        conditions.append(AuditRun.server_id == server_id)
    runs = db.scalars(
        select(AuditRun)
        .where(*conditions)
        .options(joinedload(AuditRun.server))
        .order_by(AuditRun.created_at.desc())
    ).all()
    latest: dict[UUID, AuditRun] = {}
    for run in runs:
        latest.setdefault(run.server_id, run)
    return list(latest.values())


def executive_report_data(
    db: Session,
    organization_id: UUID,
    generated_by: User,
    period_start: date | None,
    period_end: date | None,
    server_id: UUID | None = None,
) -> dict[str, Any]:
    start, end = _date_range(period_start, period_end)
    organization = db.get(Organization, organization_id)
    server = (
        db.scalar(
            select(Server).where(Server.id == server_id, Server.organization_id == organization_id)
        )
        if server_id
        else None
    )
    latest = _latest_runs(db, organization_id, start, end, server_id)
    scored = [run for run in latest if run.score is not None]
    average_score = round(sum(float(run.score) for run in scored) / len(scored), 2) if scored else None
    total_applicable = sum(run.applicable_count for run in latest)
    total_controls = sum(run.total_controls for run in latest)
    coverage = round(total_applicable / total_controls * 100, 2) if total_controls else 0.0

    finding_conditions = [
        Finding.organization_id == organization_id,
        Finding.status.notin_([FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE]),
    ]
    if server_id:
        finding_conditions.append(Finding.server_id == server_id)
    findings = db.scalars(
        select(Finding)
        .where(*finding_conditions)
        .options(joinedload(Finding.server), joinedload(Finding.control))
        .order_by(Finding.last_seen_at.desc())
    ).all()
    severity_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings = sorted(
        findings, key=lambda item: (severity_rank.get(item.severity.value, 9), -item.last_seen_at.timestamp())
    )
    counts = _severity_counts(findings)

    # Comparación con el periodo inmediatamente anterior de igual duración.
    span = end - start
    prev_latest = _latest_runs(db, organization_id, start - span, start - timedelta(microseconds=1), server_id)
    prev_scored = [run for run in prev_latest if run.score is not None]
    prev_average = (
        round(sum(float(run.score) for run in prev_scored) / len(prev_scored), 2)
        if prev_scored
        else None
    )
    delta = (
        round(average_score - prev_average, 2)
        if average_score is not None and prev_average is not None
        else None
    )

    # Tendencia semanal
    all_runs = db.scalars(
        select(AuditRun)
        .where(
            AuditRun.organization_id == organization_id,
            AuditRun.created_at.between(start, end),
            AuditRun.status == RunStatus.COMPLETED,
            AuditRun.server_id == server_id if server_id else True,
        )
        .order_by(AuditRun.created_at)
    ).all()
    buckets: dict[date, list[float]] = defaultdict(list)
    for run in all_runs:
        if run.score is None:
            continue
        d = run.created_at.date()
        week = d - timedelta(days=d.weekday())
        buckets[week].append(float(run.score))
    trend = [
        {"period": week, "average_score": round(sum(values) / len(values), 2)}
        for week, values in sorted(buckets.items())
    ]

    failure_query = (
        select(
            CisControl.code,
            CisControl.cis_reference,
            CisControl.title,
            CisControl.severity,
            func.count(HardeningCheck.id).label("failure_count"),
            func.count(distinct(AuditRun.server_id)).label("servers"),
        )
        .join(HardeningCheck, HardeningCheck.control_id == CisControl.id)
        .join(AuditRun, AuditRun.id == HardeningCheck.run_id)
        .where(
            AuditRun.organization_id == organization_id,
            AuditRun.created_at.between(start, end),
            HardeningCheck.status == "failed",
        )
    )
    if server_id:
        failure_query = failure_query.where(AuditRun.server_id == server_id)
    failure_rows = db.execute(
        failure_query.group_by(CisControl.id)
        .order_by(func.count(HardeningCheck.id).desc())
        .limit(8)
    ).all()
    top_failures = [
        {
            "code": row.code,
            "cis_reference": row.cis_reference,
            "title": row.title,
            "severity": row.severity.value if hasattr(row.severity, "value") else str(row.severity),
            "failure_count": row.failure_count,
            "servers": row.servers,
        }
        for row in failure_rows
    ]

    action_rows = db.execute(
        select(CisControl.title, CisControl.remediation_guidance, func.count(HardeningCheck.id))
        .join(HardeningCheck, HardeningCheck.control_id == CisControl.id)
        .join(AuditRun, AuditRun.id == HardeningCheck.run_id)
        .where(
            AuditRun.organization_id == organization_id,
            AuditRun.created_at.between(start, end),
            HardeningCheck.status == "failed",
        )
        .group_by(CisControl.id)
        .order_by(func.count(HardeningCheck.id).desc())
        .limit(5)
    ).all()
    actions = [
        {"title": row[0], "guidance": row[1], "failures": row[2]} for row in action_rows
    ]

    riskiest = sorted(
        findings,
        key=lambda item: (item.severity.value in ("critical", "high"), item.last_seen_at),
        reverse=True,
    )[:10]

    return {
        "report_type": "executive",
        "generated_at": datetime.now(timezone.utc),
        "generated_by": generated_by.full_name,
        "organization": organization,
        "server_filter": server,
        "period_start": start.date(),
        "period_end": end.date(),
        "latest_runs": latest,
        "average_score": average_score,
        "previous_average": prev_average,
        "delta": delta,
        "coverage": coverage,
        "findings": findings,
        "severity_counts": counts,
        "top_failures": top_failures,
        "actions": actions,
        "riskiest": riskiest,
        "trend": trend,
        "limitations": LIMITATIONS,
        "has_simulated": any(run.is_simulated for run in latest),
    }
