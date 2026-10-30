from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.enums import Severity
from app.schemas.common import ORMModel


class BenchmarkOut(ORMModel):
    id: UUID
    name: str
    version: str
    os_family: str
    description: str | None
    source_url: str | None
    is_official: bool
    mapping_status: str


class ControlOut(ORMModel):
    id: UUID
    benchmark_id: UUID
    code: str
    cis_reference: str | None
    title: str
    description: str
    rationale: str | None
    severity: Severity
    category: str
    cis_level: str | None
    automated: bool
    check_key: str
    config: dict[str, Any]
    remediation_guidance: str
    references: list[dict[str, Any]]
    is_official_mapping: bool
    mapping_notes: str | None
    is_active: bool
    enabled: bool | None = None


class ProfileOut(ORMModel):
    id: UUID
    organization_id: UUID
    benchmark_id: UUID
    name: str
    description: str | None
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
    benchmark_name: str | None = None
    benchmark_version: str | None = None
    control_count: int = 0
    enabled_control_count: int = 0


class ProfileDetail(ProfileOut):
    controls: list[ControlOut] = Field(default_factory=list)


class ProfileCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    benchmark_id: UUID
    control_ids: list[UUID] | None = None
    is_default: bool = False

    @field_validator("control_ids")
    @classmethod
    def dedupe_controls(cls, value: list[UUID] | None) -> list[UUID] | None:
        if value is None:
            return None
        if not value:
            raise ValueError("Seleccione al menos un control.")
        return list(dict.fromkeys(value))


class ProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    control_ids: list[UUID] | None = None
    is_default: bool | None = None

    @field_validator("control_ids")
    @classmethod
    def dedupe_controls(cls, value: list[UUID] | None) -> list[UUID] | None:
        if value is None:
            return None
        if not value:
            raise ValueError("Seleccione al menos un control.")
        return list(dict.fromkeys(value))
