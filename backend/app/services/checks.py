"""Catálogo de comprobaciones de solo lectura.

Cada comando es una constante auditada del código. No se construye con datos del
usuario ni con valores libres de la base de datos. Los umbrales se aplican en el
evaluador en Python, no concatenados en la shell.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from app.enums import CheckStatus
from app.services.ssh_connector import AuditConnector, AuditConnectionError, CommandResult

SSHD_PROBE = r"""{ if command -v sshd >/dev/null 2>&1; then
  echo '__SSHD__=1';
  sshd -T 2>/dev/null || cat /etc/ssh/sshd_config 2>/dev/null;
else
  echo '__SSHD__=0';
fi; } | grep -Ei '^(__SSHD__=|permitrootlogin|maxauthtries|permitemptypasswords|passwordauthentication|pubkeyauthentication)' | tail -n 40"""

PASSWORD_QUALITY = r"""if [ -r /etc/security/pwquality.conf ]; then
  echo '__PWCONF__=1';
  grep -Eis '^[[:space:]]*(minlen|minclass|dcredit|ucredit|lcredit|ocredit|maxrepeat|retry)[[:space:]]*=' /etc/security/pwquality.conf || true;
else
  echo '__PWCONF__=0';
fi
grep -Eis 'pam_pwquality|pam_cracklib' /etc/pam.d/common-password 2>/dev/null || true"""

ACCOUNT_LOCKOUT = r"""grep -Eis 'pam_faillock|pam_tally2' /etc/pam.d/common-auth /etc/pam.d/common-account 2>/dev/null || true
grep -Eis '^[[:space:]]*(deny|unlock_time|fail_interval)[[:space:]]*=' /etc/security/faillock.conf 2>/dev/null || true"""

FIREWALL_ENABLED = r"""if command -v ufw >/dev/null 2>&1; then
  echo '__UFW__=1';
  systemctl is-enabled ufw 2>&1 || true;
  systemctl is-active ufw 2>&1 || true;
  grep -Eis '^ENABLED=' /etc/ufw/ufw.conf 2>/dev/null || true;
else
  echo '__UFW__=0';
fi"""

FIREWALL_DEFAULT = r"""if command -v ufw >/dev/null 2>&1; then
  echo '__UFW__=1';
  grep -Eis '^[[:space:]]*DEFAULT_(INPUT|FORWARD)_POLICY[[:space:]]*=' /etc/default/ufw 2>/dev/null || true;
else
  echo '__UFW__=0';
fi"""

PENDING_UPDATES = r"""if command -v apt-get >/dev/null 2>&1; then
  apt-get -s -o Debug::NoLocking=1 upgrade 2>/dev/null | awk '/^Inst / {c++} END {print "__PENDING__=" c+0}';
else
  echo '__APT__=0';
fi"""

SHADOW_PERMISSIONS = r"""stat -c '%a %U %G %n' /etc/shadow /etc/shadow- /etc/gshadow 2>&1 || true"""

LOGGING_ENABLED = r"""systemctl is-enabled rsyslog 2>&1 || true
systemctl is-active rsyslog 2>&1 || true
command -v rsyslogd 2>/dev/null || true"""

AUDITD_ENABLED = r"""systemctl is-enabled auditd 2>&1 || true
systemctl is-active auditd 2>&1 || true
command -v auditctl 2>/dev/null || true"""

ASLR_ENABLED = r"""sysctl -n kernel.randomize_va_space 2>/dev/null || true"""

UNNECESSARY_SERVICES = r"""systemctl list-unit-files --state=enabled --type=service --no-pager --no-legend 2>/dev/null || true
systemctl list-unit-files --state=enabled --type=socket --no-pager --no-legend 2>/dev/null || true"""


@dataclass
class Evaluation:
    status: CheckStatus
    observed: str
    details: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


Evaluator = Callable[[CommandResult, dict[str, Any]], Evaluation]


@dataclass(frozen=True)
class CheckSpec:
    key: str
    command: str
    evaluator: Evaluator


def _kv(output: str, key: str) -> str | None:
    match = re.search(
        rf"(?im)^[ \t]*{re.escape(key)}[ \t]+([^\s#]+)", output
    )
    return match.group(1).strip().lower() if match else None


def _kv_equals(output: str, key: str) -> str | None:
    match = re.search(
        rf"(?im)^[ \t]*{re.escape(key)}[ \t]*=[ \t]*([^\s#]+)", output
    )
    return match.group(1).strip().lower().strip("\"'") if match else None


def _sshd_present(output: str) -> bool | None:
    if "__SSHD__=1" in output:
        return True
    if "__SSHD__=0" in output:
        return False
    return None


def _unavailable(output: str, key: str) -> bool:
    return output.strip() == "" and key not in output


def eval_ssh_root_login(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    present = _sshd_present(result.stdout)
    if present is False:
        return Evaluation(CheckStatus.NOT_APPLICABLE, "OpenSSH no está instalado.")
    if present is None:
        return Evaluation(
            CheckStatus.NOT_EVALUATED,
            "No fue posible leer la configuración efectiva de sshd.",
            error=(result.stderr or result.stdout)[:500],
        )
    value = _kv(result.stdout, "permitrootlogin")
    if value is None:
        return Evaluation(
            CheckStatus.FAILED,
            "PermitRootLogin no está definido explícitamente (valor por defecto no cumple).",
            {"effective": "default"},
        )
    passed = value == "no"
    return Evaluation(
        CheckStatus.PASSED if passed else CheckStatus.FAILED,
        f"PermitRootLogin = {value}",
        {"effective": value},
    )


def eval_ssh_max_auth_tries(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    present = _sshd_present(result.stdout)
    if present is False:
        return Evaluation(CheckStatus.NOT_APPLICABLE, "OpenSSH no está instalado.")
    if present is None:
        return Evaluation(CheckStatus.NOT_EVALUATED, "No se pudo leer sshd.", error=result.stderr[:500])
    maximum = int(config.get("max", 4))
    value = _kv(result.stdout, "maxauthtries")
    if value is None:
        return Evaluation(
            CheckStatus.FAILED,
            f"MaxAuthTries no definido; valor por defecto (6) supera {maximum}.",
            {"effective": "default"},
        )
    try:
        number = int(value)
    except ValueError:
        return Evaluation(CheckStatus.FAILED, f"MaxAuthTries inválido: {value}")
    return Evaluation(
        CheckStatus.PASSED if number <= maximum else CheckStatus.FAILED,
        f"MaxAuthTries = {number} (máximo {maximum})",
        {"effective": number},
    )


def eval_ssh_empty_passwords(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    present = _sshd_present(result.stdout)
    if present is False:
        return Evaluation(CheckStatus.NOT_APPLICABLE, "OpenSSH no está instalado.")
    if present is None:
        return Evaluation(CheckStatus.NOT_EVALUATED, "No se pudo leer sshd.")
    value = _kv(result.stdout, "permitemptypasswords")
    if value is None:
        return Evaluation(
            CheckStatus.PASSED,
            "PermitEmptyPasswords no definido; valor por defecto 'no'.",
            {"effective": "default-no"},
        )
    passed = value == "no"
    return Evaluation(
        CheckStatus.PASSED if passed else CheckStatus.FAILED,
        f"PermitEmptyPasswords = {value}",
    )


def eval_ssh_password_auth(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    present = _sshd_present(result.stdout)
    if present is False:
        return Evaluation(CheckStatus.NOT_APPLICABLE, "OpenSSH no está instalado.")
    if present is None:
        return Evaluation(CheckStatus.NOT_EVALUATED, "No se pudo leer sshd.")
    password_auth = _kv(result.stdout, "passwordauthentication")
    pubkey_auth = _kv(result.stdout, "pubkeyauthentication")
    if password_auth is None:
        password_auth = "yes (default)"
    passed = password_auth == "no" and pubkey_auth != "no"
    return Evaluation(
        CheckStatus.PASSED if passed else CheckStatus.FAILED,
        f"PasswordAuthentication = {password_auth}; PubkeyAuthentication = {pubkey_auth or 'default'}",
        {"password_authentication": password_auth, "pubkey_authentication": pubkey_auth},
    )


def eval_password_quality(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    minimum = int(config.get("minlen", 14))
    has_conf = "__PWCONF__=1" in result.stdout
    minlen_value = _kv_equals(result.stdout, "minlen")
    pam_present = bool(re.search(r"pam_(pwquality|cracklib)", result.stdout, re.I))
    if not has_conf:
        return Evaluation(
            CheckStatus.FAILED,
            "No existe /etc/security/pwquality.conf legible; no se puede demostrar la política.",
        )
    try:
        minlen = int(minlen_value) if minlen_value else None
    except ValueError:
        minlen = None
    details = {"minlen": minlen, "pam_module_present": pam_present}
    if minlen is None:
        return Evaluation(
            CheckStatus.FAILED,
            "La política no define minlen explícitamente (valor por defecto insuficiente).",
            details,
        )
    passed = minlen >= minimum and pam_present
    reason = f"minlen = {minlen} (mínimo {minimum}); pam_pwquality {'presente' if pam_present else 'ausente'}."
    return Evaluation(CheckStatus.PASSED if passed else CheckStatus.FAILED, reason, details)


def eval_account_lockout(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    text = result.stdout
    has_faillock = bool(re.search(r"pam_faillock", text, re.I))
    deny_raw = _kv_equals(text, "deny")
    unlock_raw = _kv_equals(text, "unlock_time")
    # Algunos PAM incluyen deny=5 en la propia línea.
    if deny_raw is None:
        match = re.search(r"deny=(\d+)", text, re.I)
        deny_raw = match.group(1) if match else None
    if unlock_raw is None:
        match = re.search(r"unlock_time=(\d+)", text, re.I)
        unlock_raw = match.group(1) if match else None
    try:
        deny = int(deny_raw) if deny_raw else None
        unlock = int(unlock_raw) if unlock_raw else None
    except ValueError:
        deny, unlock = None, None
    details = {"pam_faillock": has_faillock, "deny": deny, "unlock_time": unlock}
    passed = (
        has_faillock
        and deny is not None
        and deny <= int(config.get("deny", 5))
        and unlock is not None
        and unlock >= int(config.get("unlock_time", 900))
    )
    observed = (
        f"pam_faillock {'presente' if has_faillock else 'ausente'}; "
        f"deny={deny if deny is not None else 'no definido'}; "
        f"unlock_time={unlock if unlock is not None else 'no definido'}."
    )
    return Evaluation(CheckStatus.PASSED if passed else CheckStatus.FAILED, observed, details)


def eval_firewall_enabled(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    if "__UFW__=0" in result.stdout:
        return Evaluation(CheckStatus.FAILED, "UFW no está instalado.")
    enabled_conf = _kv_equals(result.stdout, "ENABLED")
    lines = {line.strip().lower() for line in result.stdout.splitlines()}
    service_enabled = "enabled" in lines
    service_active = "active" in lines
    passed = enabled_conf == "yes" and service_enabled and service_active
    return Evaluation(
        CheckStatus.PASSED if passed else CheckStatus.FAILED,
        f"UFW conf={enabled_conf or 'ausente'}, servicio={'active' if service_active else 'inactive'}, "
        f"arranque={'enabled' if service_enabled else 'disabled'}.",
        {"enabled_conf": enabled_conf, "active": service_active, "enabled": service_enabled},
    )


def eval_firewall_default(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    if "__UFW__=0" in result.stdout:
        return Evaluation(
            CheckStatus.NOT_APPLICABLE,
            "UFW no está instalado; la política por defecto de UFW no aplica.",
        )
    incoming = _kv_equals(result.stdout, "DEFAULT_INPUT_POLICY")
    forward = _kv_equals(result.stdout, "DEFAULT_FORWARD_POLICY")
    passed = incoming in {"drop", "reject"}
    return Evaluation(
        CheckStatus.PASSED if passed else CheckStatus.FAILED,
        f"Política entrante por defecto = {incoming or 'no definida'}.",
        {"incoming": incoming, "forward": forward},
    )


def eval_pending_updates(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    if "__APT__=0" in result.stdout:
        return Evaluation(CheckStatus.NOT_APPLICABLE, "apt no está disponible en el servidor.")
    match = re.search(r"__PENDING__=(\d+)", result.stdout)
    if not match:
        return Evaluation(
            CheckStatus.NOT_EVALUATED,
            "No se pudo determinar el número de actualizaciones pendientes.",
            error=result.stderr[:500],
        )
    count = int(match.group(1))
    maximum = int(config.get("max_pending", 0))
    return Evaluation(
        CheckStatus.PASSED if count <= maximum else CheckStatus.FAILED,
        f"{count} paquete(s) actualizables; máximo permitido {maximum}.",
        {"pending": count},
    )


def eval_shadow_permissions(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    target_line = None
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 4 and parts[-1] == "/etc/shadow":
            target_line = parts
            break
    if target_line is None:
        return Evaluation(
            CheckStatus.NOT_EVALUATED,
            "No se pudo leer metadata de /etc/shadow.",
            error=result.stderr[:500],
        )
    mode, owner, group = target_line[0], target_line[1], target_line[2]
    allowed_modes = set(config.get("allowed_modes", ["640", "600", "400"]))
    allowed_groups = {config.get("group", "shadow"), "root"}
    passed = (
        mode in allowed_modes
        and owner == config.get("owner", "root")
        and group in allowed_groups
    )
    return Evaluation(
        CheckStatus.PASSED if passed else CheckStatus.FAILED,
        f"/etc/shadow modo {mode}, propietario {owner}:{group}.",
        {"mode": mode, "owner": owner, "group": group},
    )


def eval_logging_enabled(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    lines = {line.strip().lower() for line in result.stdout.splitlines()}
    active = "active" in lines
    enabled = "enabled" in lines
    installed = bool(re.search(r"/rsyslogd\b", result.stdout))
    passed = active and enabled and installed
    return Evaluation(
        CheckStatus.PASSED if passed else CheckStatus.FAILED,
        f"rsyslog instalado={installed}, activo={active}, habilitado={enabled}.",
        {"installed": installed, "active": active, "enabled": enabled},
    )


def eval_auditd_enabled(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    lines = {line.strip().lower() for line in result.stdout.splitlines()}
    active = "active" in lines
    enabled = "enabled" in lines
    installed = "/auditctl" in result.stdout
    passed = active and enabled and installed
    return Evaluation(
        CheckStatus.PASSED if passed else CheckStatus.FAILED,
        f"auditd instalado={installed}, activo={active}, habilitado={enabled}.",
        {"installed": installed, "active": active, "enabled": enabled},
    )


def eval_aslr(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    value = result.stdout.strip()
    if not value:
        return Evaluation(CheckStatus.NOT_EVALUATED, "No se pudo leer kernel.randomize_va_space.")
    expected = str(config.get("expected", 2))
    return Evaluation(
        CheckStatus.PASSED if value == expected else CheckStatus.FAILED,
        f"kernel.randomize_va_space = {value} (esperado {expected}).",
        {"effective": value},
    )


def eval_unnecessary_services(result: CommandResult, config: dict[str, Any]) -> Evaluation:
    if not result.stdout.strip():
        return Evaluation(CheckStatus.NOT_EVALUATED, "systemctl no devolvió unidades habilitadas.")
    enabled = set()
    for line in result.stdout.splitlines():
        parts = line.split()
        if parts:
            enabled.add(parts[0].strip().lower())
    forbidden = {str(item).lower() for item in config.get("services", [])}
    found = sorted(enabled & forbidden)
    return Evaluation(
        CheckStatus.PASSED if not found else CheckStatus.FAILED,
        "Sin servicios de riesgo habilitados." if not found else f"Servicios habilitados: {', '.join(found)}",
        {"enabled_risky_services": found},
    )


CHECKS: dict[str, CheckSpec] = {
    "ssh_root_login": CheckSpec("ssh_root_login", SSHD_PROBE, eval_ssh_root_login),
    "ssh_max_auth_tries": CheckSpec("ssh_max_auth_tries", SSHD_PROBE, eval_ssh_max_auth_tries),
    "ssh_permit_empty_passwords": CheckSpec(
        "ssh_permit_empty_passwords", SSHD_PROBE, eval_ssh_empty_passwords
    ),
    "ssh_password_authentication": CheckSpec(
        "ssh_password_authentication", SSHD_PROBE, eval_ssh_password_auth
    ),
    "password_quality": CheckSpec("password_quality", PASSWORD_QUALITY, eval_password_quality),
    "account_lockout": CheckSpec("account_lockout", ACCOUNT_LOCKOUT, eval_account_lockout),
    "firewall_enabled": CheckSpec("firewall_enabled", FIREWALL_ENABLED, eval_firewall_enabled),
    "firewall_default_deny": CheckSpec(
        "firewall_default_deny", FIREWALL_DEFAULT, eval_firewall_default
    ),
    "pending_updates": CheckSpec("pending_updates", PENDING_UPDATES, eval_pending_updates),
    "shadow_permissions": CheckSpec(
        "shadow_permissions", SHADOW_PERMISSIONS, eval_shadow_permissions
    ),
    "logging_enabled": CheckSpec("logging_enabled", LOGGING_ENABLED, eval_logging_enabled),
    "auditd_enabled": CheckSpec("auditd_enabled", AUDITD_ENABLED, eval_auditd_enabled),
    "aslr_enabled": CheckSpec("aslr_enabled", ASLR_ENABLED, eval_aslr),
    "unnecessary_services": CheckSpec(
        "unnecessary_services", UNNECESSARY_SERVICES, eval_unnecessary_services
    ),
}


@dataclass
class CheckOutcome:
    control_id: Any
    check_key: str
    status: CheckStatus
    observed_value: str
    evidence: dict[str, Any]
    command_executed: str
    duration_ms: int
    error_message: str | None = None
    connection_failed: bool = False


def run_check(
    connector: AuditConnector,
    control,
) -> CheckOutcome:
    spec = CHECKS.get(control.check_key)
    if spec is None:
        return CheckOutcome(
            control_id=control.id,
            check_key=control.check_key,
            status=CheckStatus.NOT_EVALUATED,
            observed_value="Control sin implementación en el motor actual.",
            evidence={"collector": control.check_key, "reason": "unimplemented"},
            command_executed="",
            duration_ms=0,
            error_message="Comprobación no implementada.",
        )
    marker = f"# cis-check:{control.check_key}\n"
    command = marker + spec.command
    try:
        result = connector.run_command(command, check_key=control.check_key)
        evaluation = spec.evaluator(result, control.config or {})
        stdout = result.stdout[:8000]
        stderr = result.stderr[:2000]
        evidence = {
            "collector": control.check_key,
            "exit_status": result.exit_status,
            "stdout": stdout,
            "stderr": stderr,
            "output_truncated": result.truncated or len(result.stdout) > 8000,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            **evaluation.details,
        }
        return CheckOutcome(
            control_id=control.id,
            check_key=control.check_key,
            status=evaluation.status,
            observed_value=evaluation.observed[:1000],
            evidence=evidence,
            command_executed=command,
            duration_ms=result.duration_ms,
            error_message=evaluation.error,
        )
    except AuditConnectionError as exc:
        return CheckOutcome(
            control_id=control.id,
            check_key=control.check_key,
            status=CheckStatus.NOT_EVALUATED,
            observed_value="No se pudo ejecutar la comprobación.",
            evidence={
                "collector": control.check_key,
                "error": str(exc),
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
            command_executed=command,
            duration_ms=0,
            error_message=str(exc),
            connection_failed=True,
        )
    except Exception as exc:  # noqa: BLE001
        return CheckOutcome(
            control_id=control.id,
            check_key=control.check_key,
            status=CheckStatus.NOT_EVALUATED,
            observed_value="Error interno al evaluar el control.",
            evidence={
                "collector": control.check_key,
                "error": type(exc).__name__,
                "checked_at": datetime.now(timezone.utc).isoformat(),
            },
            command_executed=command,
            duration_ms=0,
            error_message="Error interno durante la comprobación.",
        )
