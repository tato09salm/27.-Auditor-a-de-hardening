"""Modelo relacional de CIS Hardening Auditor.

Separación deliberada:
- cis_controls: definición versionada del control.
- hardening_checks: resultado de ejecutar un control dentro de una auditoría.
- findings: incumplimiento persistente con ciclo de vida.
- remediation_recommendations: propuesta de corrección revisable.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Table,
    Text,
    UniqueConstraint,
    Uuid,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.enums import (
    AuthMethod,
    CheckStatus,
    ConnectionMethod,
    Environment,
    FindingStatus,
    LogResult,
    RecommendationSource,
    RecommendationStatus,
    ReportFormat,
    ReportType,
    RunStatus,
    ServerStatus,
    Severity,
    TriggerType,
)


def enum_type(enum_cls: type, name: str, length: int = 32) -> SAEnum:
    return SAEnum(
        enum_cls,
        native_enum=False,
        length=length,
        name=name,
        values_callable=lambda items: [item.value for item in items],
        validate_strings=True,
        create_constraint=True,
    )


def uuid_pk() -> Mapped[uuid.UUID]:
    return mapped_column(
        Uuid(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Identidad y acceso
# ---------------------------------------------------------------------------
user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True),
)

role_permissions = Table(
    "role_permissions",
    Base.metadata,
    Column("role_id", Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "permission_id", Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    ),
)


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    users: Mapped[list["User"]] = relationship(back_populates="organization")
    servers: Mapped[list["Server"]] = relationship(back_populates="organization")


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    must_change_password: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    failed_login_attempts: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=0, server_default="0"
    )
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    password_changed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    organization: Mapped[Organization] = relationship(back_populates="users")
    roles: Mapped[list["Role"]] = relationship(
        secondary=user_roles, back_populates="users", lazy="selectin"
    )
    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    @property
    def role_codes(self) -> list[str]:
        return [role.code for role in self.roles]


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(300))
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    users: Mapped[list[User]] = relationship(secondary=user_roles, back_populates="roles")
    permissions: Mapped[list["Permission"]] = relationship(
        secondary=role_permissions, back_populates="roles", lazy="selectin"
    )


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(80), nullable=False, unique=True, index=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(300), nullable=False)

    roles: Mapped[list[Role]] = relationship(
        secondary=role_permissions, back_populates="permissions"
    )


class RefreshSession(Base):
    __tablename__ = "refresh_sessions"

    id: Mapped[uuid.UUID] = uuid_pk()
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("refresh_sessions.id", ondelete="SET NULL")
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped[User] = relationship(back_populates="refresh_sessions")


class ApiToken(Base):
    __tablename__ = "api_tokens"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    token_prefix: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    scopes: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list, server_default="[]")
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


# ---------------------------------------------------------------------------
# Servidores y credenciales
# ---------------------------------------------------------------------------
class Server(Base, TimestampMixin):
    __tablename__ = "servers"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_servers_org_name"),
        Index("ix_servers_org_active", "organization_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("organizations.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    hostname: Mapped[str] = mapped_column(String(255), nullable=False)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    os_family: Mapped[str] = mapped_column(String(50), nullable=False)
    os_version: Mapped[str] = mapped_column(String(50), nullable=False)
    environment: Mapped[Environment] = mapped_column(
        enum_type(Environment, "server_environment", 20),
        nullable=False,
        default=Environment.PRODUCTION,
    )
    owner_area: Mapped[str | None] = mapped_column(String(150))
    connection_method: Mapped[ConnectionMethod] = mapped_column(
        enum_type(ConnectionMethod, "server_connection_method", 20),
        nullable=False,
        default=ConnectionMethod.SSH,
    )
    port: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=22, server_default="22")
    username: Mapped[str | None] = mapped_column(String(100))
    auth_method: Mapped[AuthMethod] = mapped_column(
        enum_type(AuthMethod, "server_auth_method", 20),
        nullable=False,
        default=AuthMethod.KEY,
    )
    host_key_fingerprint: Mapped[str | None] = mapped_column(String(200))
    default_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audit_profiles.id", ondelete="SET NULL")
    )
    status: Mapped[ServerStatus] = mapped_column(
        enum_type(ServerStatus, "server_status", 20),
        nullable=False,
        default=ServerStatus.PENDING,
        server_default=ServerStatus.PENDING.value,
    )
    connectivity_status: Mapped[str | None] = mapped_column(String(200))
    last_connectivity_check_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_audit_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    authorization_confirmed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    authorized_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    allow_private_target: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    notes: Mapped[str | None] = mapped_column(Text)
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    organization: Mapped[Organization] = relationship(back_populates="servers")
    credential: Mapped["ServerCredential | None"] = relationship(
        back_populates="server", uselist=False, cascade="all, delete-orphan"
    )
    default_profile: Mapped["AuditProfile | None"] = relationship(foreign_keys=[default_profile_id])


class ServerCredential(Base):
    __tablename__ = "server_credentials"

    id: Mapped[uuid.UUID] = uuid_pk()
    server_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("servers.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    secret_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    secret_fingerprint: Mapped[str] = mapped_column(String(64), nullable=False)
    key_version: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1, server_default="1")
    updated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    server: Mapped[Server] = relationship(back_populates="credential")


# ---------------------------------------------------------------------------
# Catálogo CIS y perfiles
# ---------------------------------------------------------------------------
class CisBenchmark(Base):
    __tablename__ = "cis_benchmarks"

    id: Mapped[uuid.UUID] = uuid_pk()
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    os_family: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(String(500))
    is_official: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    mapping_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="preliminary", server_default="preliminary"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    controls: Mapped[list["CisControl"]] = relationship(
        back_populates="benchmark", order_by="CisControl.code"
    )

    __table_args__ = (
        UniqueConstraint("name", "version", "os_family", name="uq_cis_benchmarks_name_version"),
    )


class CisControl(Base, TimestampMixin):
    __tablename__ = "cis_controls"
    __table_args__ = (
        UniqueConstraint("benchmark_id", "code", name="uq_cis_controls_benchmark_code"),
        Index("ix_cis_controls_benchmark_active", "benchmark_id", "is_active"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    benchmark_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cis_benchmarks.id", ondelete="CASCADE"), nullable=False
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    cis_reference: Mapped[str | None] = mapped_column(String(30))
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    rationale: Mapped[str | None] = mapped_column(Text)
    severity: Mapped[Severity] = mapped_column(
        enum_type(Severity, "control_severity", 20), nullable=False, default=Severity.MEDIUM
    )
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    cis_level: Mapped[str | None] = mapped_column(String(20))
    automated: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    check_key: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    remediation_guidance: Mapped[str] = mapped_column(Text, nullable=False)
    references: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    is_official_mapping: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    mapping_notes: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    benchmark: Mapped[CisBenchmark] = relationship(back_populates="controls")


class AuditProfile(Base, TimestampMixin):
    __tablename__ = "audit_profiles"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_audit_profiles_org_name"),
        Index("ix_audit_profiles_org_default", "organization_id", "is_default"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    benchmark_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cis_benchmarks.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    benchmark: Mapped[CisBenchmark] = relationship()
    controls: Mapped[list["AuditProfileControl"]] = relationship(
        back_populates="profile", cascade="all, delete-orphan", lazy="selectin"
    )


class AuditProfileControl(Base):
    __tablename__ = "audit_profile_controls"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("audit_profiles.id", ondelete="CASCADE"),
        primary_key=True,
    )
    control_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cis_controls.id", ondelete="CASCADE"), primary_key=True
    )
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")

    profile: Mapped[AuditProfile] = relationship(back_populates="controls")
    control: Mapped[CisControl] = relationship(lazy="joined")


# ---------------------------------------------------------------------------
# Ejecución de auditorías
# ---------------------------------------------------------------------------
class ScheduledAudit(Base, TimestampMixin):
    __tablename__ = "scheduled_audits"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_scheduled_audits_org_name"),
        Index("ix_scheduled_audits_due", "is_enabled", "next_run_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    server_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("servers.id", ondelete="CASCADE"), nullable=False
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audit_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    cron_expression: Mapped[str] = mapped_column(String(100), nullable=False)
    timezone: Mapped[str] = mapped_column(String(60), nullable=False, default="America/Lima")
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audit_runs.id", ondelete="SET NULL")
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    server: Mapped["Server"] = relationship(lazy="joined", foreign_keys=[server_id])
    profile: Mapped["AuditProfile"] = relationship(lazy="joined", foreign_keys=[profile_id])


class AuditRun(Base):
    __tablename__ = "audit_runs"
    __table_args__ = (
        Index("ix_audit_runs_org_created", "organization_id", "created_at"),
        Index("ix_audit_runs_server_created", "server_id", "created_at"),
        Index("ix_audit_runs_status", "status"),
        Index(
            "uq_audit_runs_active_server",
            "server_id",
            unique=True,
            postgresql_where=text("status IN ('queued', 'running')"),
        ),
        Index(
            "uq_audit_runs_org_idempotency",
            "organization_id",
            "idempotency_key",
            unique=True,
            postgresql_where=text("idempotency_key IS NOT NULL"),
        ),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("servers.id", ondelete="RESTRICT"), nullable=False
    )
    profile_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audit_profiles.id", ondelete="RESTRICT"), nullable=False
    )
    benchmark_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cis_benchmarks.id", ondelete="RESTRICT"), nullable=False
    )
    benchmark_version: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[RunStatus] = mapped_column(
        enum_type(RunStatus, "run_status", 20),
        nullable=False,
        default=RunStatus.QUEUED,
        server_default=RunStatus.QUEUED.value,
        index=True,
    )
    trigger_type: Mapped[TriggerType] = mapped_column(
        enum_type(TriggerType, "trigger_type", 20),
        nullable=False,
        default=TriggerType.MANUAL,
        server_default=TriggerType.MANUAL.value,
    )
    triggered_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    scheduled_audit_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("scheduled_audits.id", ondelete="SET NULL", use_alter=True),
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(100))
    request_id: Mapped[str | None] = mapped_column(String(80))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    total_controls: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    applicable_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    passed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    not_applicable_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    not_evaluated_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    error_message: Mapped[str | None] = mapped_column(Text)
    is_simulated: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    server: Mapped[Server] = relationship()
    profile: Mapped[AuditProfile] = relationship()
    benchmark: Mapped[CisBenchmark] = relationship()
    checks: Mapped[list["HardeningCheck"]] = relationship(
        back_populates="run", cascade="all, delete-orphan", order_by="HardeningCheck.created_at"
    )


class HardeningCheck(Base):
    __tablename__ = "hardening_checks"
    __table_args__ = (
        UniqueConstraint("run_id", "control_id", name="uq_hardening_checks_run_control"),
        Index("ix_hardening_checks_run_status", "run_id", "status"),
        Index("ix_hardening_checks_control_status", "control_id", "status"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audit_runs.id", ondelete="CASCADE"), nullable=False, index=True
    )
    control_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cis_controls.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[CheckStatus] = mapped_column(
        enum_type(CheckStatus, "check_status", 25), nullable=False
    )
    severity: Mapped[Severity] = mapped_column(enum_type(Severity, "check_severity", 20), nullable=False)
    observed_value: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    command_executed: Mapped[str | None] = mapped_column(Text)
    duration_ms: Mapped[int | None] = mapped_column(Integer)
    error_message: Mapped[str | None] = mapped_column(Text)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    run: Mapped[AuditRun] = relationship(back_populates="checks")
    control: Mapped[CisControl] = relationship(lazy="joined")


# ---------------------------------------------------------------------------
# Hallazgos y recomendaciones
# ---------------------------------------------------------------------------
class Finding(Base, TimestampMixin):
    __tablename__ = "findings"

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    server_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("servers.id", ondelete="RESTRICT"), nullable=False
    )
    control_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("cis_controls.id", ondelete="RESTRICT"), nullable=False
    )
    first_seen_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audit_runs.id", ondelete="RESTRICT"), nullable=False
    )
    last_seen_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audit_runs.id", ondelete="RESTRICT"), nullable=False
    )
    resolved_by_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audit_runs.id", ondelete="SET NULL")
    )
    status: Mapped[FindingStatus] = mapped_column(
        enum_type(FindingStatus, "finding_status", 30),
        nullable=False,
        default=FindingStatus.DETECTED,
        server_default=FindingStatus.DETECTED.value,
        index=True,
    )
    severity: Mapped[Severity] = mapped_column(enum_type(Severity, "finding_severity", 20), nullable=False)
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=3, server_default="3")
    title: Mapped[str] = mapped_column(String(250), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    due_date: Mapped[date | None] = mapped_column(Date)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    resolution_note: Mapped[str | None] = mapped_column(Text)
    risk_acceptance_until: Mapped[date | None] = mapped_column(Date)
    occurrence_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    server: Mapped[Server] = relationship()
    control: Mapped[CisControl] = relationship(lazy="joined")
    events: Mapped[list["FindingEvent"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", order_by="FindingEvent.created_at"
    )
    recommendations: Mapped[list["RemediationRecommendation"]] = relationship(
        back_populates="finding", cascade="all, delete-orphan", order_by="RemediationRecommendation.created_at"
    )

    __table_args__ = (
        CheckConstraint("priority BETWEEN 1 AND 5", name="priority_range"),
        Index(
            "uq_findings_active_server_control",
            "server_id",
            "control_id",
            unique=True,
            postgresql_where=text("status NOT IN ('resolved', 'false_positive')"),
        ),
        Index("ix_findings_org_status_severity", "organization_id", "status", "severity"),
        Index("ix_findings_server_last_seen", "server_id", "last_seen_at"),
    )


class FindingEvent(Base):
    __tablename__ = "finding_events"

    id: Mapped[uuid.UUID] = uuid_pk()
    finding_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False, index=True
    )
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(40))
    to_status: Mapped[str | None] = mapped_column(String(40))
    comment: Mapped[str | None] = mapped_column(Text)
    event_metadata: Mapped[dict[str, Any]] = mapped_column(
        "metadata", JSONB, nullable=False, default=dict, server_default="{}"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    finding: Mapped[Finding] = relationship(back_populates="events")


class RemediationRecommendation(Base):
    __tablename__ = "remediation_recommendations"
    __table_args__ = (
        Index("ix_recommendations_org_status", "organization_id", "status"),
        Index("ix_recommendations_finding_created", "finding_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    finding_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("findings.id", ondelete="CASCADE"), nullable=False
    )
    check_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("hardening_checks.id", ondelete="SET NULL")
    )
    source: Mapped[RecommendationSource] = mapped_column(
        enum_type(RecommendationSource, "recommendation_source", 20),
        nullable=False,
        default=RecommendationSource.AI,
        server_default=RecommendationSource.AI.value,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="ollama")
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[RecommendationStatus] = mapped_column(
        enum_type(RecommendationStatus, "recommendation_status", 30),
        nullable=False,
        default=RecommendationStatus.PENDING_REVIEW,
        server_default=RecommendationStatus.PENDING_REVIEW.value,
        index=True,
    )
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(3, 2))
    validation_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="pending", server_default="pending"
    )
    validation_warnings: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    flagged_commands: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, default=list, server_default="[]"
    )
    created_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    review_note: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    finding: Mapped[Finding] = relationship(back_populates="recommendations")
    reviews: Mapped[list["RemediationReview"]] = relationship(
        back_populates="recommendation", cascade="all, delete-orphan", order_by="RemediationReview.created_at"
    )


class RemediationReview(Base):
    __tablename__ = "remediation_reviews"

    id: Mapped[uuid.UUID] = uuid_pk()
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("remediation_recommendations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    comments: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    recommendation: Mapped[RemediationRecommendation] = relationship(back_populates="reviews")


# ---------------------------------------------------------------------------
# Reportes y bitácora
# ---------------------------------------------------------------------------
class Report(Base):
    __tablename__ = "reports"
    __table_args__ = (Index("ix_reports_org_created", "organization_id", "created_at"),)

    id: Mapped[uuid.UUID] = uuid_pk()
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    report_type: Mapped[ReportType] = mapped_column(
        enum_type(ReportType, "report_type", 20), nullable=False
    )
    format: Mapped[ReportFormat] = mapped_column(
        enum_type(ReportFormat, "report_format", 10), nullable=False
    )
    server_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("servers.id", ondelete="SET NULL")
    )
    audit_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("audit_runs.id", ondelete="SET NULL")
    )
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    parameters: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(120), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_by_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_org_created", "organization_id", "created_at"),
        Index("ix_audit_logs_action_created", "action", "created_at"),
        Index("ix_audit_logs_resource", "resource_type", "resource_id"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    api_token_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("api_tokens.id", ondelete="SET NULL")
    )
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    module: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_type: Mapped[str | None] = mapped_column(String(60))
    resource_id: Mapped[str | None] = mapped_column(String(80))
    result: Mapped[LogResult] = mapped_column(
        enum_type(LogResult, "log_result", 20),
        nullable=False,
        default=LogResult.SUCCESS,
        server_default=LogResult.SUCCESS.value,
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    request_id: Mapped[str | None] = mapped_column(String(80))
    user_agent: Mapped[str | None] = mapped_column(String(300))
    changes: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
