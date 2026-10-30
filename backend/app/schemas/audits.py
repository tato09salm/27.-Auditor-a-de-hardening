from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.enums import CheckStatus, RunStatus, Severity, TriggerType
from app.schemas.common import ORMModel


class AuditRunCreate(BaseModel):
    server_id: UUID
    profile_id: UUID | None = None


class CheckOut(ORMModel):
    id: UUID
    control_id: UUID
    status: CheckStatus
    severity: Severity
    observed_value: str | None
    evidence: dict[str, Any]
    command_executed: str | None
    duration_ms: int | None
    error_message: str | None
    evaluated_at: datetime | None
    control_code: str | None = None
    cis_reference: str | None = None
    control_title: str | None = None
    category: str | None = None
    remediation_guidance: str | None = None
    is_official_mapping: bool = False
    mapping_notes: str | None = None


class AuditRunOut(ORMModel):
    id: UUID
    organization_id: UUID
    server_id: UUID
    profile_id: UUID
    benchmark_id: UUID
    benchmark_version: str
    status: RunStatus
    trigger_type: TriggerType
    started_at: datetime | None
    finished_at: datetime | None
    total_controls: int
    applicable_count: int
    passed_count: int
    failed_count: int
    not_applicable_count: int
    not_evaluated_count: int
    score: float | None
    summary: dict[str, Any]
    error_message: str | None
    is_simulated: bool
    created_at: datetime
    server_name: str | None = None
    server_hostname: str | None = None
    profile_name: str | None = None
    triggered_by_name: str | None = None


class AuditRunDetail(AuditRunOut):
    checks: list[CheckOut] = Field(default_factory=list)
    findings_created: int = 0
    findings_resolved: int = 0


class ScheduledAuditCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    server_id: UUID
    profile_id: UUID
    cron_expression: str = Field(min_length=9, max_length=100)
    timezone: str = Field(default="America/Lima", max_length=60)
    is_enabled: bool = True

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, value: str) -> str:
        parts = value.split()
        if len(parts) != 5:
            raise ValueError("El cron debe tener cinco campos (minuto hora día mes día-semana).")
        allowed = set("0123456789*/,-?LW#")
        if any(char not in allowed for part in parts for char in part):
            raise ValueError("El cron contiene caracteres no permitidos.")
        return value


class ScheduledAuditUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    cron_expression: str | None = Field(default=None, min_length=9, max_length=100)
    timezone: str | None = Field(default=None, max_length=60)
    is_enabled: bool | None = None
    profile_id: UUID | None = None

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, value: str | None) -> str | None:
        if value is None:
            return None
        if len(value.split()) != 5:
            raise ValueError("El cron debe tener cinco campos.")
        allowed = set("0123456789*/,-?LW#")
        if any(char not in allowed for part in value.split() for char in part):
            raise ValueError("El cron contiene caracteres no permitidos.")
        return value


class ScheduledAuditOut(ORMModel):
    id: UUID
    organization_id: UUID
    name: str
    server_id: UUID
    profile_id: UUID
    cron_expression: str
    timezone: str
    is_enabled: bool
    next_run_at: datetime | None
    last_run_at: datetime | None
    last_run_id: UUID | None
    created_at: datetime
    updated_at: datetime
    server_name: str | None = None
    profile_name: str | None = None


class ScoreBreakdown(BaseModel):
    applicable: int
    passed: int
    failed: int
    not_applicable: int
    not_evaluated: int
    score: float | None
    coverage: float
