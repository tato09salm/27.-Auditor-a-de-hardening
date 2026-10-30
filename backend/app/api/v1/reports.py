from __future__ import annotations

from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException, Query, Request, status
from fastapi.responses import FileResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import CurrentUser, DbSession, Pagination, require_permission
from app.config import settings
from app.models import Report, Server, User
from app.schemas.common import Page
from app.schemas.reports import ReportCreate, ReportOut
from app.services.audit_log import record_audit
from app.services.reports_service import create_report, resolve_report_path

router = APIRouter(prefix="/reports", tags=["Reportes"])


def _report_out(db: Session, report: Report) -> ReportOut:
    server = db.get(Server, report.server_id) if report.server_id else None
    user = db.get(User, report.generated_by_id) if report.generated_by_id else None
    return ReportOut(
        **{column.name: getattr(report, column.name) for column in Report.__table__.columns},
        download_url=f"{settings.api_v1_prefix}/reports/{report.id}/download",
        server_name=server.name if server else None,
        generated_by_name=user.full_name if user else None,
    )


@router.post("", response_model=ReportOut, status_code=status.HTTP_201_CREATED)
def generate_report(
    payload: ReportCreate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("reports:generate")),
) -> ReportOut:
    try:
        report = create_report(db, user, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"code": "report_error", "message": str(exc)},
        ) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": "render_error", "message": "No fue posible generar el reporte."},
        ) from exc
    record_audit(
        db,
        action="reports.generate",
        module="reports",
        organization_id=user.organization_id,
        user=user,
        resource_type="report",
        resource_id=str(report.id),
        request=request,
        changes={
            "type": report.report_type.value,
            "format": report.format.value,
            "server_id": str(report.server_id) if report.server_id else None,
        },
    )
    db.commit()
    return _report_out(db, report)


@router.get("", response_model=Page[ReportOut])
def list_reports(
    user: CurrentUser,
    db: DbSession,
    page_params: Pagination,
    _: User = Depends(require_permission("reports:read")),
    report_type: str | None = Query(default=None, alias="type", max_length=20),
    report_format: str | None = Query(default=None, alias="format", max_length=10),
    server_id: UUID | None = None,
) -> Page[ReportOut]:
    page, page_size = page_params
    conditions = [Report.organization_id == user.organization_id]
    if report_type:
        conditions.append(Report.report_type == report_type)
    if report_format:
        conditions.append(Report.format == report_format)
    if server_id:
        conditions.append(Report.server_id == server_id)
    total = int(db.scalar(select(func.count()).select_from(Report).where(*conditions)) or 0)
    reports = db.scalars(
        select(Report)
        .where(*conditions)
        .order_by(Report.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[_report_out(db, report) for report in reports],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{report_id}/download", response_class=FileResponse)
def download_report(
    report_id: UUID,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("reports:read")),
) -> FileResponse:
    report = db.scalar(
        select(Report).where(
            Report.id == report_id, Report.organization_id == user.organization_id
        )
    )
    if report is None:
        raise HTTPException(status_code=404, detail="Reporte no encontrado.")
    try:
        path = resolve_report_path(report)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Ruta de reporte inválida.") from exc
    if not path.is_file():
        raise HTTPException(status_code=410, detail="El archivo del reporte ya no está disponible.")
    record_audit(
        db,
        action="reports.download",
        module="reports",
        organization_id=user.organization_id,
        user=user,
        resource_type="report",
        resource_id=str(report.id),
        request=request,
    )
    db.commit()
    return FileResponse(
        path=str(path),
        media_type=report.mime_type,
        filename=report.file_name,
        headers={"X-Checksum-SHA256": report.sha256},
    )
