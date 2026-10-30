from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, APIRouter, HTTPException, Query, Request, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload

from app.api.deps import (
    CurrentUser,
    DbSession,
    Pagination,
    require_any_permission,
    require_permission,
)
from app.config import settings
from app.core.crypto import CredentialDecryptionError, encrypt_secret
from app.enums import (
    ConnectionMethod,
    FindingStatus,
    LogResult,
    ServerStatus,
    Severity,
)
from app.models import (
    AuditProfile,
    AuditRun,
    CisBenchmark,
    Finding,
    Server,
    ServerCredential,
    User,
)
from app.reference_data import ensure_default_profile
from app.schemas.common import Page
from app.schemas.servers import (
    AuthorizationRequest,
    ConnectionTestResult,
    ServerCreate,
    ServerCredentialIn,
    ServerDetail,
    ServerOut,
    ServerUpdate,
)
from app.services.audit_log import record_audit
from app.services.ssh_connector import AuditConnectionError, connector_for_server

router = APIRouter(prefix="/servers", tags=["Servidores"])


def _get_server(db: Session, server_id: UUID, organization_id: UUID) -> Server:
    server = db.scalar(
        select(Server)
        .where(Server.id == server_id, Server.organization_id == organization_id)
        .options(
            selectinload(Server.credential),
            joinedload(Server.default_profile),
        )
    )
    if server is None:
        raise HTTPException(status_code=404, detail="Servidor no encontrado.")
    return server


def _profile_for_org(db: Session, profile_id: UUID | None, organization_id: UUID, user_id: UUID):
    if profile_id is None:
        profile = ensure_default_profile(db, organization_id, user_id)
    else:
        profile = db.scalar(
            select(AuditProfile).where(
                AuditProfile.id == profile_id,
                AuditProfile.organization_id == organization_id,
                AuditProfile.is_active.is_(True),
            )
        )
        if profile is None:
            raise HTTPException(
                status_code=422,
                detail={"code": "invalid_profile", "message": "Perfil de auditoría inválido."},
            )
    benchmark = db.get(CisBenchmark, profile.benchmark_id)
    if benchmark is None:
        raise HTTPException(status_code=422, detail="El perfil no tiene benchmark asociado.")
    return profile, benchmark


def _validate_os_compatibility(server_os: str, benchmark_os: str) -> None:
    if benchmark_os == "linux":
        return
    if server_os.strip().lower() != benchmark_os.strip().lower():
        raise HTTPException(
            status_code=422,
            detail={
                "code": "os_mismatch",
                "message": (
                    f"El perfil corresponde a {benchmark_os}, pero el servidor es {server_os}. "
                    "Seleccione un perfil compatible."
                ),
            },
        )


def _last_score(db: Session, server_id: UUID) -> float | None:
    value = db.scalar(
        select(AuditRun.score)
        .where(AuditRun.server_id == server_id, AuditRun.score.is_not(None))
        .order_by(AuditRun.created_at.desc())
        .limit(1)
    )
    return float(value) if value is not None else None


def _active_findings(db: Session, server_id: UUID) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Finding)
            .where(
                Finding.server_id == server_id,
                Finding.status.notin_([FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE]),
            )
        )
        or 0
    )


def _server_out(db: Session, server: Server) -> ServerOut:
    return ServerOut(
        **{
            column.name: getattr(server, column.name)
            for column in Server.__table__.columns
        },
        credential_configured=server.credential is not None,
        credential_updated_at=server.credential.updated_at if server.credential else None,
        default_profile_name=server.default_profile.name if server.default_profile else None,
        last_score=_last_score(db, server.id),
        active_findings=_active_findings(db, server.id),
    )


@router.get("", response_model=Page[ServerOut])
def list_servers(
    user: CurrentUser,
    db: DbSession,
    page_params: Pagination,
    _: User = Depends(require_permission("servers:read")),
    search: str | None = Query(default=None, max_length=100),
    environment: str | None = Query(default=None, max_length=30),
    os_family: str | None = Query(default=None, max_length=50),
    server_status: str | None = Query(default=None, alias="status", max_length=30),
    is_active: bool | None = None,
) -> Page[ServerOut]:
    page, page_size = page_params
    conditions = [Server.organization_id == user.organization_id]
    if search:
        pattern = f"%{search.strip()}%"
        conditions.append(
            or_(Server.name.ilike(pattern), Server.hostname.ilike(pattern), Server.ip_address.ilike(pattern))
        )
    if environment:
        conditions.append(Server.environment == environment)
    if os_family:
        conditions.append(Server.os_family == os_family)
    if server_status:
        conditions.append(Server.status == server_status)
    if is_active is not None:
        conditions.append(Server.is_active.is_(is_active))
    total = int(db.scalar(select(func.count()).select_from(Server).where(*conditions)) or 0)
    servers = db.scalars(
        select(Server)
        .where(*conditions)
        .options(selectinload(Server.credential), joinedload(Server.default_profile))
        .order_by(Server.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return Page(
        items=[_server_out(db, server) for server in servers],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=ServerOut, status_code=status.HTTP_201_CREATED)
def create_server(
    payload: ServerCreate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("servers:manage")),
) -> ServerOut:
    if payload.connection_method == ConnectionMethod.SIMULATED:
        if not settings.enable_simulated_connector or settings.environment == "production":
            raise HTTPException(
                status_code=403,
                detail={
                    "code": "simulated_disabled",
                    "message": "El conector simulado está deshabilitado en este entorno.",
                },
            )
    else:
        if not payload.authorization_confirmed:
            raise HTTPException(
                status_code=422,
                detail={
                    "code": "authorization_required",
                    "message": "Debe confirmar la autorización explícita para auditar el servidor.",
                },
            )
        if payload.credential is None:
            raise HTTPException(
                status_code=422,
                detail={"code": "credential_required", "message": "La credencial SSH es obligatoria."},
            )

    profile, benchmark = _profile_for_org(
        db, payload.default_profile_id, user.organization_id, user.id
    )
    _validate_os_compatibility(payload.os_family, benchmark.os_family)

    server = Server(
        organization_id=user.organization_id,
        name=payload.name.strip(),
        hostname=payload.hostname,
        ip_address=payload.ip_address,
        os_family=payload.os_family.strip().lower(),
        os_version=payload.os_version.strip(),
        environment=payload.environment,
        owner_area=payload.owner_area,
        connection_method=payload.connection_method,
        port=payload.port,
        username=payload.username,
        auth_method=payload.auth_method,
        host_key_fingerprint=payload.host_key_fingerprint,
        default_profile_id=profile.id,
        status=(
            ServerStatus.ONLINE
            if payload.connection_method == ConnectionMethod.SIMULATED
            else ServerStatus.PENDING
        ),
        is_active=True,
        is_simulated=payload.connection_method == ConnectionMethod.SIMULATED,
        authorization_confirmed=payload.authorization_confirmed,
        authorized_by_id=user.id if payload.authorization_confirmed else None,
        authorized_at=datetime.now(timezone.utc) if payload.authorization_confirmed else None,
        allow_private_target=payload.allow_private_target,
        notes=payload.notes,
        created_by_id=user.id,
    )
    if payload.connection_method == ConnectionMethod.SSH and payload.credential:
        ciphertext, fingerprint = encrypt_secret(payload.credential.secret)
        server.credential = ServerCredential(
            secret_ciphertext=ciphertext,
            secret_fingerprint=fingerprint,
            updated_by_id=user.id,
        )
    db.add(server)
    try:
        db.flush()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "duplicate_server", "message": "Ya existe un servidor con ese nombre."},
        ) from exc

    record_audit(
        db,
        action="servers.create",
        module="servers",
        organization_id=user.organization_id,
        user=user,
        resource_type="server",
        resource_id=str(server.id),
        request=request,
        changes={
            "name": server.name,
            "hostname": server.hostname,
            "ip_address": server.ip_address,
            "environment": server.environment,
            "connection_method": server.connection_method,
            "authorized": server.authorization_confirmed,
            "simulated": server.is_simulated,
        },
    )
    db.commit()
    return _server_out(db, server)


@router.get("/{server_id}", response_model=ServerDetail)
def get_server(
    server_id: UUID,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("servers:read")),
) -> ServerDetail:
    server = _get_server(db, server_id, user.organization_id)
    base = _server_out(db, server)
    total_audits = int(
        db.scalar(select(func.count()).select_from(AuditRun).where(AuditRun.server_id == server.id))
        or 0
    )
    last_run_id = db.scalar(
        select(AuditRun.id)
        .where(AuditRun.server_id == server.id)
        .order_by(AuditRun.created_at.desc())
        .limit(1)
    )
    rows = db.execute(
        select(Finding.severity, func.count())
        .where(
            Finding.server_id == server.id,
            Finding.status.notin_([FindingStatus.RESOLVED, FindingStatus.FALSE_POSITIVE]),
        )
        .group_by(Finding.severity)
    ).all()
    counts = {severity.value: 0 for severity in Severity}
    for severity, count in rows:
        counts[severity.value if hasattr(severity, "value") else str(severity)] = count
    return ServerDetail(
        **base.model_dump(),
        total_audits=total_audits,
        last_run_id=last_run_id,
        open_findings_by_severity=counts,
    )


@router.patch("/{server_id}", response_model=ServerOut)
def update_server(
    server_id: UUID,
    payload: ServerUpdate,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("servers:manage")),
) -> ServerOut:
    server = _get_server(db, server_id, user.organization_id)
    data = payload.model_dump(exclude_unset=True)

    if "default_profile_id" in data:
        profile, benchmark = _profile_for_org(
            db, data["default_profile_id"], user.organization_id, user.id
        )
        _validate_os_compatibility(
            data.get("os_family", server.os_family), benchmark.os_family
        )
        server.default_profile_id = profile.id
    if "os_family" in data:
        profile = db.get(AuditProfile, server.default_profile_id) if server.default_profile_id else None
        if profile:
            benchmark = db.get(CisBenchmark, profile.benchmark_id)
            if benchmark:
                _validate_os_compatibility(data["os_family"], benchmark.os_family)

    target_fields = {"ip_address", "hostname", "port", "username", "auth_method", "host_key_fingerprint"}
    requires_reauthorization = bool(target_fields.intersection(data))
    for field in ("name", "hostname", "ip_address", "os_family", "os_version", "owner_area", "notes"):
        if field in data:
            setattr(server, field, data[field].strip() if isinstance(data[field], str) else data[field])
    if "environment" in data:
        server.environment = data["environment"]
    if "port" in data:
        server.port = data["port"]
    if "username" in data:
        server.username = data["username"]
    if "auth_method" in data:
        server.auth_method = data["auth_method"]
    if "host_key_fingerprint" in data:
        server.host_key_fingerprint = data["host_key_fingerprint"]
    if "allow_private_target" in data:
        server.allow_private_target = data["allow_private_target"]
    if "is_active" in data:
        server.is_active = data["is_active"]
        server.status = ServerStatus.PENDING if data["is_active"] else ServerStatus.DISABLED
        if not data["is_active"]:
            requires_reauthorization = True

    if requires_reauthorization:
        server.authorization_confirmed = False
        server.authorized_by_id = None
        server.authorized_at = None
        server.status = ServerStatus.PENDING if server.is_active else ServerStatus.DISABLED

    record_audit(
        db,
        action="servers.update",
        module="servers",
        organization_id=user.organization_id,
        user=user,
        resource_type="server",
        resource_id=str(server.id),
        request=request,
        changes={
            "fields": sorted(data),
            "reauthorization_required": requires_reauthorization,
        },
    )
    db.commit()
    return _server_out(db, server)


@router.post("/{server_id}/authorize", response_model=ServerOut)
def authorize_server(
    server_id: UUID,
    payload: AuthorizationRequest,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("servers:manage")),
) -> ServerOut:
    server = _get_server(db, server_id, user.organization_id)
    if payload.confirmed:
        if not server.is_active:
            raise HTTPException(status_code=409, detail="No se puede autorizar un servidor inactivo.")
        if not server.is_simulated and server.credential is None:
            raise HTTPException(
                status_code=409,
                detail="Configure la credencial SSH antes de autorizar el servidor.",
            )
        server.authorization_confirmed = True
        server.authorized_by_id = user.id
        server.authorized_at = datetime.now(timezone.utc)
        server.allow_private_target = payload.allow_private_target
        server.status = ServerStatus.PENDING
    else:
        server.authorization_confirmed = False
        server.authorized_by_id = None
        server.authorized_at = None
        server.status = ServerStatus.PENDING if server.is_active else ServerStatus.DISABLED

    record_audit(
        db,
        action="servers.authorize" if payload.confirmed else "servers.revoke_authorization",
        module="servers",
        organization_id=user.organization_id,
        user=user,
        resource_type="server",
        resource_id=str(server.id),
        request=request,
        changes={
            "confirmed": payload.confirmed,
            "allow_private_target": payload.allow_private_target,
            "comment": payload.comment,
        },
    )
    db.commit()
    return _server_out(db, server)


@router.put("/{server_id}/credential", response_model=ServerOut)
def set_credential(
    server_id: UUID,
    payload: ServerCredentialIn,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_permission("servers:manage")),
) -> ServerOut:
    server = _get_server(db, server_id, user.organization_id)
    if server.connection_method == ConnectionMethod.SIMULATED:
        raise HTTPException(status_code=422, detail="Un servidor simulado no usa credenciales.")
    ciphertext, fingerprint = encrypt_secret(payload.secret)
    if server.credential is None:
        server.credential = ServerCredential(
            secret_ciphertext=ciphertext,
            secret_fingerprint=fingerprint,
            updated_by_id=user.id,
        )
    else:
        server.credential.secret_ciphertext = ciphertext
        server.credential.secret_fingerprint = fingerprint
        server.credential.updated_by_id = user.id
    server.status = ServerStatus.PENDING
    record_audit(
        db,
        action="servers.credential.update",
        module="servers",
        organization_id=user.organization_id,
        user=user,
        resource_type="server",
        resource_id=str(server.id),
        request=request,
        changes={"credential_configured": True},
    )
    db.commit()
    return _server_out(db, server)


@router.post("/{server_id}/test-connection", response_model=ConnectionTestResult)
def test_connection(
    server_id: UUID,
    request: Request,
    user: CurrentUser,
    db: DbSession,
    _: User = Depends(require_any_permission("audits:execute", "servers:manage")),
) -> ConnectionTestResult:
    server = _get_server(db, server_id, user.organization_id)
    tested_at = datetime.now(timezone.utc)
    if not server.is_active:
        raise HTTPException(status_code=409, detail="El servidor está desactivado.")
    if not server.authorization_confirmed:
        raise HTTPException(
            status_code=409,
            detail={"code": "not_authorized", "message": "El servidor no está autorizado."},
        )
    try:
        connector = connector_for_server(server)
        try:
            result = connector.test()
        finally:
            connector.close()
        server.status = ServerStatus.ONLINE
        server.connectivity_status = "Conectividad verificada"
        server.last_connectivity_check_at = tested_at
        record_audit(
            db,
            action="servers.connection_test",
            module="servers",
            organization_id=user.organization_id,
            user=user,
            resource_type="server",
            resource_id=str(server.id),
            request=request,
            changes={"reachable": True, "simulated": result.simulated},
        )
        db.commit()
        return ConnectionTestResult(
            reachable=True,
            message="Conexión verificada e identidad del host validada."
            if not result.simulated
            else "Conector simulado: no se contactó infraestructura real.",
            status=ServerStatus.ONLINE,
            latency_ms=result.latency_ms,
            host_identity_verified=not result.simulated,
            simulated=result.simulated,
            tested_at=tested_at,
        )
    except (AuditConnectionError, CredentialDecryptionError) as exc:
        message = str(exc)
        server.status = (
            ServerStatus.AUTH_ERROR
            if "Autenticación" in message or "huella" in message.lower() or "credencial" in message.lower()
            else ServerStatus.OFFLINE
        )
        server.connectivity_status = message[:200]
        server.last_connectivity_check_at = tested_at
        record_audit(
            db,
            action="servers.connection_test",
            module="servers",
            organization_id=user.organization_id,
            user=user,
            resource_type="server",
            resource_id=str(server.id),
            result=LogResult.FAILURE,
            request=request,
            changes={"reachable": False, "error": message},
        )
        db.commit()
        return ConnectionTestResult(
            reachable=False,
            message=message,
            status=server.status,
            host_identity_verified=False,
            simulated=server.is_simulated,
            tested_at=tested_at,
        )
