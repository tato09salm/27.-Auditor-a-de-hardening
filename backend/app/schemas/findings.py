from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.enums import (
    FindingStatus,
    RecommendationSource,
    RecommendationStatus,
    Severity,
)
from app.schemas.common import ORMModel


class FindingOut(ORMModel):
    id: UUID
    organization_id: UUID
    server_id: UUID
    control_id: UUID
    first_seen_run_id: UUID
    last_seen_run_id: UUID
    resolved_by_run_id: UUID | None
    status: FindingStatus
    severity: Severity
    priority: int
    title: str
    description: str
    owner_id: UUID | None
    due_date: date | None
    first_seen_at: datetime
    last_seen_at: datetime
    resolved_at: datetime | None
    resolution_note: str | None
    risk_acceptance_until: date | None
    occurrence_count: int
    created_at: datetime
    updated_at: datetime
    server_name: str | None = None
    control_code: str | None = None
    cis_reference: str | None = None
    category: str | None = None
    owner_name: str | None = None
    recommendation_count: int = 0
    latest_recommendation_id: UUID | None = None
    latest_recommendation_status: RecommendationStatus | None = None


class FindingEventOut(ORMModel):
    id: UUID
    event_type: str
    from_status: str | None
    to_status: str | None
    comment: str | None
    actor_id: UUID | None
    created_at: datetime
    actor_name: str | None = None


class FindingDetail(FindingOut):
    evidence: dict[str, Any] = Field(default_factory=dict)
    observed_value: str | None = None
    events: list[FindingEventOut] = Field(default_factory=list)


class FindingUpdate(BaseModel):
    status: FindingStatus | None = None
    owner_id: UUID | None = None
    priority: int | None = Field(default=None, ge=1, le=5)
    due_date: date | None = None
    comment: str | None = Field(default=None, max_length=2000)
    resolution_note: str | None = Field(default=None, max_length=4000)
    risk_acceptance_until: date | None = None

    @model_validator(mode="after")
    def validate_resolution(self):
        if self.status == FindingStatus.RISK_ACCEPTED:
            if not self.risk_acceptance_until:
                raise ValueError("Aceptar un riesgo requiere una fecha límite.")
            if not self.comment:
                raise ValueError("Aceptar un riesgo requiere justificación.")
        if self.status == FindingStatus.FALSE_POSITIVE and not self.resolution_note:
            raise ValueError("Debe documentar por qué es un falso positivo.")
        return self


class RemediationStep(BaseModel):
    command: str = Field(min_length=1, max_length=1000)
    explanation: str = Field(min_length=1, max_length=2000)
    risk: str | None = Field(default=None, max_length=1000)


class RecommendationPayload(BaseModel):
    problem: str = Field(min_length=1, max_length=4000)
    risk: str = Field(min_length=1, max_length=4000)
    recommendation: str = Field(min_length=1, max_length=6000)
    commands: list[RemediationStep] = Field(default_factory=list)
    impact: str = Field(min_length=1, max_length=3000)
    prerequisites: list[str] = Field(default_factory=list)
    service_interruption_risk: Literal["low", "medium", "high", "unknown"] = "unknown"
    validation: list[str] = Field(default_factory=list)
    rollback: list[str] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    insufficient_information: bool = False


class RecommendationOut(ORMModel):
    id: UUID
    organization_id: UUID
    finding_id: UUID
    check_id: UUID | None
    source: RecommendationSource
    provider: str
    model: str
    status: RecommendationStatus
    payload: dict[str, Any]
    confidence: float | None
    validation_status: str
    validation_warnings: list[str]
    flagged_commands: list[dict[str, Any]]
    created_by_id: UUID | None
    reviewed_by_id: UUID | None
    reviewed_at: datetime | None
    review_note: str | None
    created_at: datetime
    updated_at: datetime
    created_by_name: str | None = None
    reviewed_by_name: str | None = None
    finding_title: str | None = None
    server_name: str | None = None
    control_code: str | None = None


class RecommendationReviewIn(BaseModel):
    decision: Literal["approved", "rejected"]
    comments: str = Field(min_length=10, max_length=4000)


class RecommendationReviewOut(ORMModel):
    id: UUID
    recommendation_id: UUID
    reviewer_id: UUID | None
    decision: str
    comments: str
    created_at: datetime
    reviewer_name: str | None = None


class RecommendationDetail(RecommendationOut):
    reviews: list[RecommendationReviewOut] = Field(default_factory=list)
    finding_title: str | None = None
    server_name: str | None = None
    control_code: str | None = None


class GenerateRecommendationResponse(BaseModel):
    recommendation: RecommendationOut
    ai_available: bool
    message: str
