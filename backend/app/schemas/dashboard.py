from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DashboardSummary(BaseModel):
    total_servers: int
    active_servers: int
    audited_servers: int
    pending_servers: int
    average_score: float | None
    evaluation_coverage: float
    findings_critical: int
    findings_high: int
    findings_medium: int
    findings_low: int
    findings_info: int
    audits_in_period: int
    pending_recommendations: int
    last_audit_at: datetime | None


class TrendPoint(BaseModel):
    period: date
    average_score: float | None
    audits: int


class TopFailure(BaseModel):
    control_id: UUID
    control_code: str
    cis_reference: str | None
    title: str
    severity: str
    failure_count: int
    affected_servers: int


class RecentRun(BaseModel):
    id: UUID
    server_id: UUID
    server_name: str
    status: str
    score: float | None
    failed_count: int
    created_at: datetime
    is_simulated: bool


class ServerRisk(BaseModel):
    id: UUID
    name: str
    hostname: str
    environment: str
    score: float | None
    critical_findings: int
    high_findings: int
    last_audit_at: datetime | None
    status: str


class DashboardResponse(BaseModel):
    summary: DashboardSummary
    trend: list[TrendPoint]
    top_failures: list[TopFailure]
    recent_runs: list[RecentRun]
    riskiest_servers: list[ServerRisk]
    generated_at: datetime
    filters: dict[str, str | None] = Field(default_factory=dict)
