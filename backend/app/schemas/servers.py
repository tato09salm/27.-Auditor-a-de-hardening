from __future__ import annotations

import ipaddress
import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from app.enums import AuthMethod, ConnectionMethod, Environment, ServerStatus
from app.schemas.common import ORMModel

HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))*$"
)
FINGERPRINT_RE = re.compile(r"^SHA256:[A-Za-z0-9+/]{43}=?$")


def normalize_ip(value: str) -> str:
    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError as exc:
        raise ValueError("La dirección IP no es válida.") from exc


class ServerCredentialIn(BaseModel):
    secret: str = Field(min_length=8, max_length=32768)
    # No se permite un campo adicional que pudiera terminar en logs.
    model_config = {"extra": "forbid"}


class ServerBase(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    hostname: str = Field(min_length=1, max_length=255)
    ip_address: str
    os_family: str = Field(min_length=2, max_length=50)
    os_version: str = Field(min_length=1, max_length=50)
    environment: Environment = Environment.PRODUCTION
    owner_area: str | None = Field(default=None, max_length=150)
    connection_method: ConnectionMethod = ConnectionMethod.SSH
    port: int = Field(default=22, ge=1, le=65535)
    username: str | None = Field(default=None, max_length=100)
    auth_method: AuthMethod = AuthMethod.KEY
    host_key_fingerprint: str | None = Field(default=None, max_length=200)
    default_profile_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=4000)
    authorization_confirmed: bool = False
    allow_private_target: bool = False

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, value: str) -> str:
        value = value.strip().lower()
        if not HOSTNAME_RE.match(value):
            raise ValueError("Hostname inválido.")
        return value

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str) -> str:
        return normalize_ip(value)

    @field_validator("host_key_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not FINGERPRINT_RE.match(value):
            raise ValueError(
                "La huella debe usar SHA256 en formato SHA256:<base64>. No se aceptan MD5."
            )
        return value

    @model_validator(mode="after")
    def validate_ssh_fields(self):
        if self.connection_method == ConnectionMethod.SSH:
            if not self.username:
                raise ValueError("El usuario técnico es obligatorio para SSH.")
            if not self.host_key_fingerprint:
                raise ValueError("La huella de host SSH es obligatoria.")
        return self


class ServerCreate(ServerBase):
    credential: ServerCredentialIn | None = None

    @model_validator(mode="after")
    def validate_credential(self):
        if self.connection_method == ConnectionMethod.SSH and self.credential is None:
            raise ValueError("Debe registrar una credencial SSH cifrada.")
        return self


class ServerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    hostname: str | None = Field(default=None, min_length=1, max_length=255)
    ip_address: str | None = None
    os_family: str | None = Field(default=None, min_length=2, max_length=50)
    os_version: str | None = Field(default=None, min_length=1, max_length=50)
    environment: Environment | None = None
    owner_area: str | None = Field(default=None, max_length=150)
    port: int | None = Field(default=None, ge=1, le=65535)
    username: str | None = Field(default=None, max_length=100)
    auth_method: AuthMethod | None = None
    host_key_fingerprint: str | None = Field(default=None, max_length=200)
    default_profile_id: UUID | None = None
    notes: str | None = Field(default=None, max_length=4000)
    allow_private_target: bool | None = None
    is_active: bool | None = None

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip().lower()
        if not HOSTNAME_RE.match(value):
            raise ValueError("Hostname inválido.")
        return value

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        return normalize_ip(value) if value else None

    @field_validator("host_key_fingerprint")
    @classmethod
    def validate_fingerprint(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not FINGERPRINT_RE.match(value):
            raise ValueError("La huella debe usar SHA256 en formato SHA256:<base64>.")
        return value


class AuthorizationRequest(BaseModel):
    confirmed: bool
    allow_private_target: bool = False
    comment: str | None = Field(default=None, max_length=500)


class ServerOut(ORMModel):
    id: UUID
    name: str
    hostname: str
    ip_address: str
    os_family: str
    os_version: str
    environment: Environment
    owner_area: str | None
    connection_method: ConnectionMethod
    port: int
    username: str | None
    auth_method: AuthMethod
    host_key_fingerprint: str | None
    default_profile_id: UUID | None
    status: ServerStatus
    connectivity_status: str | None
    last_connectivity_check_at: datetime | None
    last_audit_at: datetime | None
    is_active: bool
    is_simulated: bool
    authorization_confirmed: bool
    authorized_at: datetime | None
    allow_private_target: bool
    notes: str | None
    created_at: datetime
    updated_at: datetime
    credential_configured: bool = False
    credential_updated_at: datetime | None = None
    default_profile_name: str | None = None
    last_score: float | None = None
    active_findings: int = 0


class ServerDetail(ServerOut):
    total_audits: int = 0
    last_run_id: UUID | None = None
    open_findings_by_severity: dict[str, int] = Field(default_factory=dict)


class ConnectionTestResult(BaseModel):
    reachable: bool
    message: str
    status: ServerStatus
    latency_ms: int | None = None
    host_identity_verified: bool = False
    simulated: bool = False
    tested_at: datetime
