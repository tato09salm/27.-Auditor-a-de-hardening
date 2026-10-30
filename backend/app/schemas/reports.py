from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.enums import ReportFormat, ReportType
from app.schemas.common import ORMModel


class ReportCreate(BaseModel):
    report_type: ReportType
    format: ReportFormat
    server_id: UUID | None = None
    audit_run_id: UUID | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None

    @model_validator(mode="after")
    def validate_scope(self):
        if self.report_type == ReportType.TECHNICAL and not self.audit_run_id:
            raise ValueError("El reporte técnico requiere una auditoría (audit_run_id).")
        if self.period_start and self.period_end and self.period_start > self.period_end:
            raise ValueError("El inicio del periodo no puede ser posterior al fin.")
        return self


class ReportOut(ORMModel):
    id: UUID
    organization_id: UUID
    report_type: ReportType
    format: ReportFormat
    server_id: UUID | None
    audit_run_id: UUID | None
    period_start: datetime | None
    period_end: datetime | None
    parameters: dict[str, Any]
    file_name: str
    mime_type: str
    size_bytes: int
    sha256: str
    generated_by_id: UUID | None
    created_at: datetime
    download_url: str | None = None
    server_name: str | None = None
    generated_by_name: str | None = None
