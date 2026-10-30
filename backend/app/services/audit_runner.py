"""Ejecutor de auditorías: conecta, evalúa, puntúa, persiste y actualiza hallazgos."""

from __future__ import annotations

import logging
import threading
from datetime import date, datetime, timedelta, timezone
from typing import Iterable
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.config import settings
from app.database import SessionLocal
from app.enums import (
    CheckStatus,
    FindingStatus,
    RecommendationStatus,
    RunStatus,
    ServerStatus,
    Severity,
)
from app.models import (
    AuditProfile,
    AuditProfileControl,
    AuditRun,
    AuditLog,
    CisControl,
    Finding,
    FindingEvent,
    HardeningCheck,
    RemediationRecommendation,
    ScheduledAudit,
    Server,
    User,
)
from app.core.crypto import CredentialDecryptionError
from app.services.audit_log import record_audit
from app.services.checks import CheckOutcome, run_check
from app.services.scoring import calculate_score
from app.services.ssh_connector import AuditConnectionError, connector_for_server

logger = logging.getLogger(__name__)
_semaphore = threading.BoundedSemaphore(max(1, settings.audit_max_concurrent_runs))

PRIORITY_BY_SEVERITY = {
    Severity.CRITICAL: 1,
    Severity.HIGH: 2,
    Severity.MEDIUM: 3,
    Severity.LOW: 4,
    Severity.INFO: 5,
}
DUE_DAYS_BY_SEVERITY = {
    Severity.CRITICAL: 7,
    Severity.HIGH: 30,
    Severity.MEDIUM: 60,
    Severity.LOW: 90,
    Severity.INFO: 180,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _fail_run(
    db: Session,
    run: AuditRun,
    message: str,
    controls: Iterable[CisControl],
    request_id: str | None = None,
) -> None:
    for control in controls:
        db.add(
            HardeningCheck(
                run_id=run.id,
                control_id=control.id,
                status=CheckStatus.NOT_EVALUATED,
                severity=control.severity,
                observed_value="Auditoría no ejecutada.",
                evidence={"error": message},
                error_message=message,
                evaluated_at=_now(),
            )
        )
    run.status = RunStatus.FAILED
    run.finished_at = _now()
    run.error_message = message
    run.total_controls = len(list(controls))
    run.applicable_count = 0
    run.not_evaluated_count = run.total_controls
    run.score = None
    run.summary = {
        "scope": "evaluación no completada",
        "limitations": [
            "No se obtuvieron resultados utilizables; el porcentaje no se calcula.",
        ],
        "error": message,
    }
    if run.server:
        run.server.status = (
            ServerStatus.AUTH_ERROR
            if "Autenticación" in message or "huella" in message.lower()
            else ServerStatus.OFFLINE
        )
        run.server.connectivity_status = message[:200]
        run.server.last_connectivity_check_at = _now()
    entry = record_audit(
        db,
        action="audits.run.failed",
        module="audits",
        organization_id=run.organization_id,
        resource_type="audit_run",
        resource_id=str(run.id),
        changes={"error": message},
    )
    entry.request_id = request_id


def _active_finding(db: Session, server_id: UUID, control_id: UUID) -> Finding | None:
    # La unicidad de ejecución activa por servidor evita carreras; no se usa
    # FOR UPDATE porque la relación eager con cis_controls genera un outer join.
    return db.scalar(
        select(Finding).where(
            Finding.server_id == server_id,
            Finding.control_id == control_id,
            Finding.status.notin_([FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE]),
        )
    )


def _add_event(
    db: Session,
    finding: Finding,
    event_type: str,
    *,
    actor_id: UUID | None,
    from_status: str | None = None,
    to_status: str | None = None,
    comment: str | None = None,
    run_id: UUID | None = None,
) -> None:
    db.add(
        FindingEvent(
            finding_id=finding.id,
            actor_id=actor_id,
            event_type=event_type,
            from_status=from_status,
            to_status=to_status,
            comment=comment,
            event_metadata={"run_id": str(run_id)} if run_id else {},
        )
    )


def _sync_findings(
    db: Session,
    run: AuditRun,
    server: Server,
    control: CisControl,
    outcome: CheckOutcome,
    now: datetime,
) -> tuple[int, int]:
    created = 0
    resolved = 0
    existing = _active_finding(db, server.id, control.id)
    if outcome.status == CheckStatus.FAILED:
        if existing is None:
            due = now.date() + timedelta(days=DUE_DAYS_BY_SEVERITY[control.severity])
            finding = Finding(
                organization_id=run.organization_id,
                server_id=server.id,
                control_id=control.id,
                first_seen_run_id=run.id,
                last_seen_run_id=run.id,
                status=FindingStatus.DETECTED,
                severity=control.severity,
                priority=PRIORITY_BY_SEVERITY[control.severity],
                title=control.title,
                description=control.description,
                due_date=due,
                first_seen_at=now,
                last_seen_at=now,
                occurrence_count=1,
            )
            db.add(finding)
            db.flush()
            _add_event(
                db,
                finding,
                "created",
                actor_id=run.triggered_by_id,
                to_status=FindingStatus.DETECTED.value,
                comment="Hallazgo detectado por auditoría automatizada.",
                run_id=run.id,
            )
            created += 1
        else:
            previous = existing.status
            existing.last_seen_run_id = run.id
            existing.last_seen_at = now
            existing.severity = control.severity
            existing.occurrence_count += 1
            if previous == FindingStatus.FIXED_PENDING_VALIDATION:
                existing.status = FindingStatus.DETECTED
                _add_event(
                    db,
                    existing,
                    "validation_failed",
                    actor_id=run.triggered_by_id,
                    from_status=previous.value,
                    to_status=FindingStatus.DETECTED.value,
                    comment="La nueva comprobación no superó la validación.",
                    run_id=run.id,
                )
            elif (
                previous == FindingStatus.RISK_ACCEPTED
                and existing.risk_acceptance_until
                and existing.risk_acceptance_until < now.date()
            ):
                existing.status = FindingStatus.DETECTED
                existing.risk_acceptance_until = None
                _add_event(
                    db,
                    existing,
                    "risk_acceptance_expired",
                    actor_id=run.triggered_by_id,
                    from_status=previous.value,
                    to_status=FindingStatus.DETECTED.value,
                    comment="La aceptación temporal del riesgo venció.",
                    run_id=run.id,
                )
    elif outcome.status == CheckStatus.PASSED and existing is not None:
        previous = existing.status
        existing.status = FindingStatus.RESOLVED
        existing.resolved_at = now
        existing.resolved_by_run_id = run.id
        existing.last_seen_run_id = run.id
        existing.last_seen_at = now
        existing.resolution_note = (
            "Resuelto automáticamente tras una comprobación satisfactoria. "
            "El cierre queda respaldado por la evidencia de esta auditoría."
        )
        db.execute(
            update(RemediationRecommendation)
            .where(
                RemediationRecommendation.finding_id == existing.id,
                RemediationRecommendation.status.in_(
                    [RecommendationStatus.PENDING_REVIEW, RecommendationStatus.APPROVED]
                ),
            )
            .values(status=RecommendationStatus.SUPERSEDED, updated_at=now)
        )
        _add_event(
            db,
            existing,
            "auto_resolved",
            actor_id=run.triggered_by_id,
            from_status=previous.value,
            to_status=FindingStatus.RESOLVED.value,
            comment="Comprobación posterior satisfactoria.",
            run_id=run.id,
        )
        resolved += 1
    return created, resolved


def _remaining_not_evaluated(
    control: CisControl, run_id: UUID, message: str
) -> HardeningCheck:
    return HardeningCheck(
        run_id=run_id,
        control_id=control.id,
        status=CheckStatus.NOT_EVALUATED,
        severity=control.severity,
        observed_value="No evaluado por interrupción de la conexión.",
        evidence={"error": message},
        error_message=message,
        evaluated_at=_now(),
    )


def execute_audit_run(run_id: UUID) -> None:
    """Punto de entrada del worker. Debe ejecutarse fuera del request."""
    acquired = _semaphore.acquire(timeout=5)
    if not acquired:
        with SessionLocal() as db:
            run = db.get(AuditRun, run_id)
            if run and run.status == RunStatus.QUEUED:
                run.status = RunStatus.FAILED
                run.error_message = "No hay capacidad de ejecución disponible."
                run.finished_at = _now()
                db.commit()
        return
    try:
        _execute(run_id)
    finally:
        _semaphore.release()


def _execute(run_id: UUID) -> None:
    with SessionLocal() as db:
        run = db.scalar(
            select(AuditRun)
            .where(AuditRun.id == run_id)
            .options(joinedload(AuditRun.server).selectinload(Server.credential))
        )
        if run is None or run.status != RunStatus.QUEUED:
            return
        run.status = RunStatus.RUNNING
        run.started_at = _now()
        db.commit()

        controls: list[CisControl] = []
        request_id = run.request_id
        try:
            server = run.server
            if server is None:
                raise AuditConnectionError("Servidor no encontrado.")
            if not server.is_active:
                raise AuditConnectionError("El servidor está desactivado.")
            if not server.authorization_confirmed:
                raise AuditConnectionError("El servidor no está autorizado para auditoría.")

            controls = list(
                db.scalars(
                    select(CisControl)
                    .join(AuditProfileControl, AuditProfileControl.control_id == CisControl.id)
                    .where(
                        AuditProfileControl.profile_id == run.profile_id,
                        AuditProfileControl.enabled.is_(True),
                        CisControl.is_active.is_(True),
                    )
                    .order_by(CisControl.code)
                ).all()
            )
            if not controls:
                raise AuditConnectionError("El perfil no contiene controles activos.")

            run.total_controls = len(controls)
            connector = connector_for_server(server)
            try:
                connection = connector.test()
                server.status = ServerStatus.ONLINE
                server.connectivity_status = "Conectividad verificada"
                server.last_connectivity_check_at = _now()
                db.commit()
                outcomes: list[CheckOutcome] = []
                connection_failed = False
                for index, control in enumerate(controls):
                    outcome = run_check(connector, control)
                    outcomes.append(outcome)
                    if outcome.connection_failed:
                        connection_failed = True
                        for remaining in controls[index + 1 :]:
                            outcomes.append(
                                CheckOutcome(
                                    control_id=remaining.id,
                                    check_key=remaining.check_key,
                                    status=CheckStatus.NOT_EVALUATED,
                                    observed_value="No evaluado por interrupción de la conexión.",
                                    evidence={
                                        "error": outcome.error_message,
                                        "collector": remaining.check_key,
                                    },
                                    command_executed="",
                                    duration_ms=0,
                                    error_message=outcome.error_message,
                                    connection_failed=True,
                                )
                            )
                        break
            finally:
                connector.close()

            for outcome, control in zip(outcomes, controls, strict=True):
                db.add(
                    HardeningCheck(
                        run_id=run.id,
                        control_id=control.id,
                        status=outcome.status,
                        severity=control.severity,
                        observed_value=outcome.observed_value,
                        evidence=outcome.evidence,
                        command_executed=outcome.command_executed,
                        duration_ms=outcome.duration_ms,
                        error_message=outcome.error_message,
                        evaluated_at=_now(),
                    )
                )
            db.flush()

            score = calculate_score(outcome.status for outcome in outcomes)
            now = _now()
            created_total = 0
            resolved_total = 0
            for outcome, control in zip(outcomes, controls, strict=True):
                created, resolved = _sync_findings(db, run, server, control, outcome, now)
                created_total += created
                resolved_total += resolved

            failed_controls = []
            severity_counts = {severity.value: 0 for severity in Severity}
            for outcome, control in zip(outcomes, controls, strict=True):
                if outcome.status == CheckStatus.FAILED:
                    severity_counts[control.severity.value] += 1
                    failed_controls.append(
                        {
                            "control_id": str(control.id),
                            "code": control.code,
                            "cis_reference": control.cis_reference,
                            "title": control.title,
                            "severity": control.severity.value,
                        }
                    )

            run.applicable_count = score.applicable
            run.passed_count = score.passed
            run.failed_count = score.failed
            run.not_applicable_count = score.not_applicable
            run.not_evaluated_count = score.not_evaluated
            run.score = score.score
            run.finished_at = now
            run.summary = {
                "coverage": float(score.coverage),
                "severity_counts": severity_counts,
                "failed_controls": failed_controls,
                "findings_created": created_total,
                "findings_resolved": resolved_total,
                "connection": {
                    "verified": True,
                    "simulated": connection.simulated,
                    "latency_ms": connection.latency_ms,
                },
                "limitations": [
                    "El porcentaje mide únicamente los controles incluidos en el perfil y "
                    "evaluados correctamente; no es una certificación CIS.",
                    "Una configuración conforme no garantiza que el servidor esté libre de "
                    "vulnerabilidades.",
                    "El motor realiza comprobaciones de solo lectura y no corrige el servidor.",
                ],
            }
            if score.not_evaluated == len(outcomes) and outcomes:
                run.status = RunStatus.FAILED
                run.error_message = "Ningún control pudo evaluarse correctamente."
            else:
                run.status = RunStatus.COMPLETED
                if connection_failed:
                    run.error_message = "La conexión se interrumpió; hay controles no evaluados."
            server.last_audit_at = now
            server.status = ServerStatus.ONLINE
            if run.scheduled_audit_id:
                scheduled = db.get(ScheduledAudit, run.scheduled_audit_id)
                if scheduled:
                    scheduled.last_run_at = now
                    scheduled.last_run_id = run.id

            entry = record_audit(
                db,
                action="audits.run.completed" if run.status == RunStatus.COMPLETED else "audits.run.failed",
                module="audits",
                organization_id=run.organization_id,
                resource_type="audit_run",
                resource_id=str(run.id),
                changes={
                    "score": float(score.score) if score.score is not None else None,
                    "failed": score.failed,
                    "not_evaluated": score.not_evaluated,
                    "findings_created": created_total,
                    "findings_resolved": resolved_total,
                },
            )
            entry.request_id = request_id
            db.commit()
        except (AuditConnectionError, CredentialDecryptionError) as exc:
            db.rollback()
            run = db.scalar(
                select(AuditRun)
                .where(AuditRun.id == run_id)
                .options(joinedload(AuditRun.server))
            )
            if run is not None:
                _fail_run(db, run, str(exc), controls, request_id)
                db.commit()
        except Exception:  # noqa: BLE001
            logger.exception("Fallo interno al ejecutar auditoría %s", run_id)
            db.rollback()
            run = db.scalar(
                select(AuditRun)
                .where(AuditRun.id == run_id)
                .options(joinedload(AuditRun.server))
            )
            if run is not None:
                _fail_run(
                    db,
                    run,
                    "Error interno durante la auditoría. Revise la bitácora del backend.",
                    controls,
                    request_id,
                )
                db.commit()


def recover_stale_runs() -> int:
    """Marca ejecuciones huérfanas tras un reinicio; evita bloqueos permanentes."""
    cutoff = _now() - timedelta(hours=2)
    with SessionLocal() as db:
        stale = db.scalars(
            select(AuditRun).where(
                AuditRun.status.in_([RunStatus.QUEUED, RunStatus.RUNNING]),
                AuditRun.created_at < cutoff,
            )
        ).all()
        for run in stale:
            run.status = RunStatus.FAILED
            run.finished_at = _now()
            run.error_message = "Ejecución interrumpida por reinicio o tiempo agotado."
            run.summary = {"error": run.error_message}
        if stale:
            db.commit()
        return len(stale)
