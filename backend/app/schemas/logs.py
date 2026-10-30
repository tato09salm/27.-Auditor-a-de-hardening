from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.enums import LogResult
from app.schemas.common import ORMModel


class AuditLogOut(ORMModel):
    id: int
    organization_id: UUID | None
    user_id: UUID | None
    api_token_id: UUID | None
    action: str
    module: str
    resource_type: str | None
    resource_id: str | None
    result: LogResult
    ip_address: str | None
    request_id: str | None
    user_agent: str | None
    changes: dict[str, Any]
    created_at: datetime
    user_name: str | None = None


class SystemInfo(BaseModel):
    product: str
    version: str
    environment: str
    ai: dict[str, Any]
    simulated_connector_enabled: bool
    private_targets_enabled: bool
    reports_storage: str
    audit_max_concurrent_runs: int
