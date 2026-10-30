"""Orquestación de generación y almacenamiento seguro de reportes."""

from __future__ import annotations

import hashlib
import re
import uuid
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import settings
from app.enums import ReportFormat, ReportType
from app.models import AuditRun, Organization, Report, Server, User
from app.schemas.reports import ReportCreate
from app.services.report_data import executive_report_data, technical_report_data
from app.services.report_renderers import render_docx, render_pdf, render_xlsx

MIME_TYPES = {
    ReportFormat.PDF: "application/pdf",
    ReportFormat.DOCX: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ReportFormat.XLSX: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}
RENDERERS = {
    ReportFormat.PDF: render_pdf,
    ReportFormat.DOCX: render_docx,
    ReportFormat.XLSX: render_xlsx,
}
SAFE_SLUG = re.compile(r"[^a-z0-9]+")


def _slug(value: str, fallback: str = "servidor") -> str:
    result = SAFE_SLUG.sub("-", value.lower()).strip("-")
    return (result or fallback)[:40]


def _file_name(
    report_type: ReportType,
    server: Server | None,
    day: datetime,
    ext: str,
    simulated: bool = False,
) -> str:
    prefix = "simulado_" if simulated else ""
    prefix += "tecnico" if report_type == ReportType.TECHNICAL else "ejecutivo"
    if server is not None:
        prefix += "_" + _slug(server.name)
    return f"{prefix}_{day.strftime('%Y%m%d')}.{ext}"


def create_report(db: Session, user: User, payload: ReportCreate) -> Report:
    organization = db.get(Organization, user.organization_id)
    if organization is None:
        raise ValueError("Organización no encontrada.")

    server: Server | None = None
    run: AuditRun | None = None
    if payload.report_type == ReportType.TECHNICAL:
        run = db.scalar(
            select(AuditRun).where(
                AuditRun.id == payload.audit_run_id,
                AuditRun.organization_id == user.organization_id,
            )
        )
        if run is None:
            raise ValueError("Auditoría no encontrada.")
        data = technical_report_data(db, user.organization_id, run.id, user)
        server = data["server"]
        period_start = run.started_at or run.created_at
        period_end = run.finished_at or run.created_at
        parameters = {"audit_run_id": str(run.id)}
    else:
        if payload.server_id:
            server = db.scalar(
                select(Server).where(
                    Server.id == payload.server_id,
                    Server.organization_id == user.organization_id,
                )
            )
            if server is None:
                raise ValueError("Servidor no encontrado.")
        data = executive_report_data(
            db,
            user.organization_id,
            user,
            payload.period_start.date() if payload.period_start else None,
            payload.period_end.date() if payload.period_end else None,
            server.id if server else None,
        )
        period_start = datetime.combine(data["period_start"], time.min, tzinfo=timezone.utc)
        period_end = datetime.combine(data["period_end"], time.max, tzinfo=timezone.utc)
        if (period_end - period_start).days > settings.reports_max_period_days:
            raise ValueError(
                f"El periodo no puede superar {settings.reports_max_period_days} días."
            )
        parameters = {
            "server_id": str(server.id) if server else None,
            "period_start": data["period_start"].isoformat(),
            "period_end": data["period_end"].isoformat(),
        }

    report_id = uuid.uuid4()
    extension = payload.format.value
    simulated = bool(data.get("is_simulated") or data.get("has_simulated"))
    display_name = _file_name(payload.report_type, server, period_end, extension, simulated)
    target_dir = settings.reports_path / str(user.organization_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / f"{report_id}.{extension}"
    renderer = RENDERERS[payload.format]
    try:
        renderer(data, path)
        content = path.read_bytes()
    except Exception:
        path.unlink(missing_ok=True)
        raise
    digest = hashlib.sha256(content).hexdigest()
    relative = path.relative_to(settings.reports_path).as_posix()
    report = Report(
        id=report_id,
        organization_id=user.organization_id,
        report_type=payload.report_type,
        format=payload.format,
        server_id=server.id if server else None,
        audit_run_id=run.id if run else None,
        period_start=period_start,
        period_end=period_end,
        parameters=parameters,
        file_name=display_name,
        storage_path=relative,
        mime_type=MIME_TYPES[payload.format],
        size_bytes=len(content),
        sha256=digest,
        generated_by_id=user.id,
    )
    db.add(report)
    try:
        db.commit()
    except Exception:
        db.rollback()
        path.unlink(missing_ok=True)
        raise
    return report


def resolve_report_path(report: Report) -> Path:
    base = settings.reports_path.resolve()
    path = (settings.reports_path / report.storage_path).resolve()
    if not path.is_relative_to(base):
        raise ValueError("Ruta de reporte inválida.")
    return path
