"""Conector SSH de solo lectura con verificación de huella y timeouts."""

from __future__ import annotations

import base64
import hashlib
import hmac
import io
import socket
import time
from dataclasses import dataclass
from typing import Protocol

import paramiko
from paramiko.ssh_exception import AuthenticationException, BadHostKeyException, SSHException

from app.config import settings
from app.core.crypto import decrypt_secret
from app.enums import AuthMethod, ConnectionMethod
from app.models import Server
from app.services.network_policy import TargetNotAllowedError, validate_audit_target

MAX_EVIDENCE_BYTES = settings.ssh_max_output_bytes


class AuditConnectionError(Exception):
    """Error controlado de conexión; su mensaje se muestra sin stack trace."""


class HostKeyMismatch(AuditConnectionError):
    pass


class CommandExecutionError(AuditConnectionError):
    pass


@dataclass
class CommandResult:
    exit_status: int
    stdout: str
    stderr: str
    duration_ms: int
    truncated: bool = False


@dataclass
class ConnectionTest:
    reachable: bool
    latency_ms: int
    fingerprint: str | None
    simulated: bool = False


class AuditConnector(Protocol):
    def test(self) -> ConnectionTest: ...
    def run_command(self, command: str, check_key: str | None = None) -> CommandResult: ...
    def close(self) -> None: ...


def canonical_fingerprint(value: str) -> str:
    value = value.strip()
    if not value.startswith("SHA256:"):
        return value
    body = value.split(":", 1)[1].rstrip("=")
    return "SHA256:" + body


def key_fingerprint(key: paramiko.PKey) -> str:
    digest = hashlib.sha256(key.asbytes()).digest()
    return "SHA256:" + base64.b64encode(digest).decode("ascii").rstrip("=")


class PinnedFingerprintPolicy(paramiko.MissingHostKeyPolicy):
    def __init__(self, expected: str) -> None:
        self.expected = canonical_fingerprint(expected)

    def missing_host_key(self, client, hostname, key) -> None:  # type: ignore[no-untyped-def]
        actual = key_fingerprint(key)
        if not hmac.compare_digest(actual, self.expected):
            raise HostKeyMismatch(
                "La huella del host SSH no coincide con la registrada. "
                "Conexión rechazada; verifique el servidor antes de actualizar la huella."
            )
        client.get_host_keys().add(hostname, key.get_name(), key)


def _load_private_key(secret: str) -> paramiko.PKey:
    errors: list[str] = []
    for key_class in (paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.RSAKey):
        try:
            return key_class.from_private_key(io.StringIO(secret))
        except (SSHException, ValueError) as exc:
            errors.append(type(exc).__name__)
    raise AuditConnectionError(
        "No se pudo interpretar la clave privada. Formatos soportados: Ed25519, ECDSA o RSA "
        "sin passphrase."
    )


class SSHConnector:
    def __init__(self, server: Server, secret: str) -> None:
        self.server = server
        self.secret = secret
        self._client: paramiko.SSHClient | None = None

    def _connect(self) -> paramiko.SSHClient:
        if self._client is not None:
            return self._client
        try:
            decision = validate_audit_target(self.server)
        except TargetNotAllowedError as exc:
            raise AuditConnectionError(str(exc)) from exc
        if not self.server.host_key_fingerprint:
            raise HostKeyMismatch("El servidor no tiene huella SSH registrada.")

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(PinnedFingerprintPolicy(self.server.host_key_fingerprint))
        connect_kwargs: dict[str, object] = {
            "hostname": str(decision.address),
            "port": self.server.port,
            "username": self.server.username,
            "timeout": settings.ssh_connect_timeout_seconds,
            "banner_timeout": settings.ssh_connect_timeout_seconds,
            "auth_timeout": settings.ssh_connect_timeout_seconds,
            "channel_timeout": settings.ssh_command_timeout_seconds,
            "look_for_keys": False,
            "allow_agent": False,
        }
        if self.server.auth_method == AuthMethod.PASSWORD:
            connect_kwargs["password"] = self.secret
        else:
            connect_kwargs["pkey"] = _load_private_key(self.secret)
        try:
            client.connect(**connect_kwargs)  # type: ignore[arg-type]
        except HostKeyMismatch:
            client.close()
            raise
        except AuthenticationException as exc:
            client.close()
            raise AuditConnectionError(
                "Autenticación SSH rechazada. Verifique usuario, credencial y método."
            ) from exc
        except (BadHostKeyException, SSHException, socket.timeout, OSError) as exc:
            client.close()
            raise AuditConnectionError(
                "No fue posible conectar por SSH. Verifique IP, puerto, firewall y conectividad."
            ) from exc
        self._client = client
        return client

    def test(self) -> ConnectionTest:
        started = time.monotonic()
        client = self._connect()
        try:
            stdin, stdout, stderr = client.exec_command(
                "printf 'cis-audit-ok'", timeout=settings.ssh_command_timeout_seconds
            )
            output = stdout.read(64).decode("utf-8", errors="replace")
            if output != "cis-audit-ok":
                raise AuditConnectionError("El servidor no devolvió la respuesta esperada.")
            return ConnectionTest(
                reachable=True,
                latency_ms=int((time.monotonic() - started) * 1000),
                fingerprint=self.server.host_key_fingerprint,
            )
        except (SSHException, socket.timeout, OSError) as exc:
            raise AuditConnectionError("La prueba de ejecución SSH falló.") from exc

    def run_command(self, command: str, check_key: str | None = None) -> CommandResult:
        if "\x00" in command:
            raise CommandExecutionError("Comando inválido.")
        client = self._connect()
        started = time.monotonic()
        try:
            stdin, stdout, stderr = client.exec_command(
                command,
                timeout=settings.ssh_command_timeout_seconds,
                get_pty=False,
            )
            out_bytes = stdout.read(MAX_EVIDENCE_BYTES + 1)
            err_bytes = stderr.read(MAX_EVIDENCE_BYTES + 1)
            exit_status = stdout.channel.recv_exit_status()
        except (SSHException, socket.timeout, OSError) as exc:
            raise CommandExecutionError(
                "La ejecución del control excedió el tiempo o se interrumpió la conexión."
            ) from exc
        truncated = len(out_bytes) > MAX_EVIDENCE_BYTES or len(err_bytes) > MAX_EVIDENCE_BYTES
        return CommandResult(
            exit_status=exit_status,
            stdout=out_bytes[:MAX_EVIDENCE_BYTES].decode("utf-8", errors="replace"),
            stderr=err_bytes[:MAX_EVIDENCE_BYTES].decode("utf-8", errors="replace"),
            duration_ms=int((time.monotonic() - started) * 1000),
            truncated=truncated,
        )

    def close(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None


class SimulatedConnector:
    """Conector de pruebas. Solo se habilita con ENABLE_SIMULATED_CONNECTOR=true."""

    def __init__(self, server: Server) -> None:
        if not settings.enable_simulated_connector:
            raise AuditConnectionError("El conector simulado está deshabilitado.")
        self.server = server
        self.good = any(
            marker in server.name.lower() for marker in ("compliant", "cumplidor", "sano")
        )

    def test(self) -> ConnectionTest:
        return ConnectionTest(reachable=True, latency_ms=3, fingerprint="SHA256:SIMULATED", simulated=True)

    def run_command(self, command: str, check_key: str | None = None) -> CommandResult:
        from app.services.simulated_fixtures import fixture_for

        if not check_key:
            return CommandResult(0, "cis-audit-ok", "", 2)
        output, exit_status = fixture_for(check_key, self.good)
        return CommandResult(exit_status, output, "", 3)

    def close(self) -> None:
        return None


def connector_for_server(server: Server) -> AuditConnector:
    if server.connection_method == ConnectionMethod.SIMULATED:
        if not server.is_simulated:
            raise AuditConnectionError("El servidor no está marcado como simulado.")
        return SimulatedConnector(server)
    if server.connection_method != ConnectionMethod.SSH:
        raise AuditConnectionError("Método de conexión no soportado por el motor actual.")
    if server.credential is None:
        raise AuditConnectionError("El servidor no tiene una credencial configurada.")
    secret = decrypt_secret(server.credential.secret_ciphertext)
    return SSHConnector(server, secret)
