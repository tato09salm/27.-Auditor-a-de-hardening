"""Datos de referencia versionados: permisos, roles y catálogo CIS inicial.

Los identificadores CIS fueron contrastados con el PDF oficial
"CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0". Cuando el benchmark marca un
control como manual, la automatización es una comprobación propia y así se
documenta en ``mapping_notes``. Los controles sin referencia CIS se identifican
como internos.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.enums import Severity
from app.models import (
    AuditProfile,
    AuditProfileControl,
    CisBenchmark,
    CisControl,
    Permission,
    Role,
)

BENCHMARK_NAME = "CIS Ubuntu Linux 22.04 LTS Benchmark"
BENCHMARK_VERSION = "1.0.0"
BENCHMARK_OS = "ubuntu"
CIS_SOURCE = "https://www.cisecurity.org/benchmark/ubuntu_linux"


PERMISSIONS: list[tuple[str, str, str]] = [
    ("dashboard:read", "dashboard", "Consultar dashboard e indicadores"),
    ("servers:read", "servers", "Consultar inventario de servidores"),
    ("servers:manage", "servers", "Registrar, editar, autorizar y desactivar servidores"),
    ("profiles:read", "profiles", "Consultar perfiles y controles CIS"),
    ("profiles:manage", "profiles", "Crear y modificar perfiles de auditoría"),
    ("audits:read", "audits", "Consultar auditorías, resultados y evidencias"),
    ("audits:execute", "audits", "Ejecutar auditorías autorizadas"),
    ("findings:read", "findings", "Consultar hallazgos"),
    ("findings:manage", "findings", "Gestionar el ciclo de vida de hallazgos"),
    ("recommendations:read", "recommendations", "Consultar recomendaciones"),
    ("recommendations:generate", "recommendations", "Solicitar recomendaciones asistidas por IA"),
    ("recommendations:review", "recommendations", "Aprobar o rechazar recomendaciones"),
    ("reports:read", "reports", "Consultar y descargar reportes"),
    ("reports:generate", "reports", "Generar reportes técnicos y ejecutivos"),
    ("schedules:manage", "schedules", "Programar auditorías periódicas"),
    ("users:read", "users", "Consultar usuarios y roles"),
    ("users:manage", "users", "Crear, modificar y desactivar usuarios"),
    ("logs:read", "logs", "Consultar la bitácora de auditoría"),
    ("settings:manage", "settings", "Gestionar tokens de automatización y configuración"),
]

ROLE_DEFINITIONS: dict[str, tuple[str, str, list[str]]] = {
    "admin": (
        "Administrador",
        "Administra usuarios, servidores, perfiles, automatización y configuración.",
        [code for code, _, _ in PERMISSIONS],
    ),
    "auditor": (
        "Auditor",
        "Configura perfiles, ejecuta auditorías, revisa recomendaciones y genera informes.",
        [
            "dashboard:read",
            "servers:read",
            "profiles:read",
            "profiles:manage",
            "audits:read",
            "audits:execute",
            "findings:read",
            "recommendations:read",
            "recommendations:review",
            "reports:read",
            "reports:generate",
            "schedules:manage",
            "logs:read",
        ],
    ),
    "analyst": (
        "Analista",
        "Analiza incumplimientos, gestiona hallazgos y propone acciones correctivas.",
        [
            "dashboard:read",
            "servers:read",
            "profiles:read",
            "audits:read",
            "findings:read",
            "findings:manage",
            "recommendations:read",
            "recommendations:generate",
            "reports:read",
            "reports:generate",
        ],
    ),
    "observer": (
        "Observador",
        "Consulta dashboards, resultados e informes sin modificar configuraciones.",
        [
            "dashboard:read",
            "servers:read",
            "profiles:read",
            "audits:read",
            "findings:read",
            "recommendations:read",
            "reports:read",
        ],
    ),
}


def _ref(title: str, url: str) -> dict[str, str]:
    return {"title": title, "url": url}


CONTROLS: list[dict[str, Any]] = [
    {
        "code": "SSH-ROOT",
        "cis_reference": "5.2.7",
        "title": "Acceso SSH directo de root deshabilitado",
        "description": (
            "El servicio SSH no debe permitir autenticación directa del usuario root. "
            "La administración debe realizarse con cuentas nominativas y escalada controlada."
        ),
        "rationale": (
            "Elimina un objetivo predecible y obliga a usar trazabilidad por usuario. "
            "Reduce el impacto de ataques de fuerza bruta contra root."
        ),
        "severity": Severity.HIGH,
        "category": "Acceso remoto",
        "cis_level": "Level 1 - Server",
        "check_key": "ssh_root_login",
        "config": {"expected": "no"},
        "remediation_guidance": (
            "Establecer 'PermitRootLogin no' en /etc/ssh/sshd_config (o en un archivo "
            "incluido), validar con 'sshd -t', conservar una sesión SSH abierta y recargar "
            "el servicio. Verificar el acceso con un usuario no root antes de cerrar la sesión."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 5.2.7", CIS_SOURCE),
            _ref(
                "Ubuntu Server: OpenSSH",
                "https://documentation.ubuntu.com/server/how-to/security/openssh-server/",
            ),
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado en el benchmark v1.0.0.",
    },
    {
        "code": "SSH-MAXAUTH",
        "cis_reference": "5.2.18",
        "title": "SSH limita los intentos de autenticación",
        "description": "MaxAuthTries debe ser 4 o menos para limitar intentos fallidos por conexión.",
        "rationale": "Reduce la ventana de fuerza bruta y el ruido de autenticación.",
        "severity": Severity.MEDIUM,
        "category": "Acceso remoto",
        "cis_level": "Level 1 - Server",
        "check_key": "ssh_max_auth_tries",
        "config": {"max": 4},
        "remediation_guidance": (
            "Configurar 'MaxAuthTries 4' en sshd_config, validar la sintaxis y recargar SSH."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 5.2.18", CIS_SOURCE)
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado en el benchmark v1.0.0.",
    },
    {
        "code": "SSH-EMPTY",
        "cis_reference": "5.2.9",
        "title": "SSH rechaza contraseñas vacías",
        "description": "PermitEmptyPasswords debe estar deshabilitado.",
        "rationale": "Evita el acceso con cuentas sin contraseña.",
        "severity": Severity.HIGH,
        "category": "Acceso remoto",
        "cis_level": "Level 1 - Server",
        "check_key": "ssh_permit_empty_passwords",
        "config": {"expected": "no"},
        "remediation_guidance": (
            "Establecer 'PermitEmptyPasswords no'. Antes de aplicar, verificar que ninguna "
            "cuenta habilitada tenga contraseña vacía."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 5.2.9", CIS_SOURCE)
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado en el benchmark v1.0.0.",
    },
    {
        "code": "SSH-KEYONLY",
        "cis_reference": None,
        "title": "SSH prefiere autenticación por clave pública",
        "description": (
            "Control interno inspirado en buenas prácticas: PasswordAuthentication debería "
            "estar deshabilitado cuando exista un despliegue de claves gestionado."
        ),
        "rationale": "Reduce exposición a fuerza bruta y a reutilización de contraseñas.",
        "severity": Severity.MEDIUM,
        "category": "Acceso remoto",
        "cis_level": None,
        "check_key": "ssh_password_authentication",
        "config": {"expected": "no"},
        "remediation_guidance": (
            "No es un requisito universal de CIS. Antes de establecer "
            "'PasswordAuthentication no', distribuir y probar claves por usuario, mantener una "
            "sesión de emergencia y definir un procedimiento de recuperación."
        ),
        "references": [
            _ref("CIS Controls v8.1: 4.5", "https://www.cisecurity.org/controls"),
            _ref(
                "Ubuntu Server: OpenSSH",
                "https://documentation.ubuntu.com/server/how-to/security/openssh-server/",
            ),
        ],
        "is_official_mapping": False,
        "mapping_notes": "Control interno; CIS no exige deshabilitar contraseñas en todos los perfiles.",
    },
    {
        "code": "AUTH-PWQUALITY",
        "cis_reference": "5.4.1",
        "title": "Requisitos de complejidad de contraseñas",
        "description": (
            "La política de creación de contraseñas debe exigir al menos 14 caracteres y "
            "complejidad razonable mediante pam_pwquality."
        ),
        "rationale": "Dificulta ataques de diccionario y fuerza bruta sobre cuentas locales.",
        "severity": Severity.HIGH,
        "category": "Autenticación",
        "cis_level": "Level 1 - Server",
        "check_key": "password_quality",
        "config": {"minlen": 14},
        "remediation_guidance": (
            "Configurar pam_pwquality con minlen=14 y al menos una clase de caracteres; "
            "probar el cambio con una cuenta de prueba antes de generalizarlo."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 5.4.1", CIS_SOURCE),
            _ref("pam_pwquality(8)", "https://manpages.ubuntu.com/manpages/jammy/man8/pam_pwquality.8.html"),
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado. Se evalúa minlen y presencia de pam_pwquality.",
    },
    {
        "code": "AUTH-FAILLOCK",
        "cis_reference": "5.4.2",
        "title": "Bloqueo de cuentas por intentos fallidos",
        "description": (
            "Debe existir una política de bloqueo temporal tras intentos fallidos "
            "(pam_faillock o mecanismo equivalente)."
        ),
        "rationale": "Limita la fuerza bruta contra cuentas locales.",
        "severity": Severity.HIGH,
        "category": "Autenticación",
        "cis_level": "Level 1 - Server",
        "check_key": "account_lockout",
        "config": {"deny": 5, "unlock_time": 900},
        "remediation_guidance": (
            "Configurar pam_faillock en /etc/pam.d/common-auth y common-account con "
            "deny<=5 y unlock_time>=900. Probar en una cuenta no privilegiada."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 5.4.2", CIS_SOURCE),
            _ref("pam_faillock(8)", "https://manpages.ubuntu.com/manpages/jammy/man8/pam_faillock.8.html"),
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado. El parser es conservador ante PAM personalizado.",
    },
    {
        "code": "FW-ENABLED",
        "cis_reference": "3.5.1.3",
        "title": "Firewall UFW habilitado",
        "description": "El servicio UFW debe estar habilitado y activo.",
        "rationale": "Reduce la superficie de red expuesta.",
        "severity": Severity.HIGH,
        "category": "Firewall",
        "cis_level": "Level 1 - Server",
        "check_key": "firewall_enabled",
        "config": {"service": "ufw"},
        "remediation_guidance": (
            "Revisar reglas antes de habilitar; conservar acceso SSH y ejecutar "
            "'ufw --force enable'. Validar la conectividad desde otra sesión."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 3.5.1.3", CIS_SOURCE),
            _ref("UFW", "https://help.ubuntu.com/community/UFW"),
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado en el benchmark v1.0.0.",
    },
    {
        "code": "FW-DEFAULT",
        "cis_reference": "3.5.1.7",
        "title": "Política por defecto del firewall: denegar entrada",
        "description": "UFW debe aplicar una política por defecto de denegación para tráfico entrante.",
        "rationale": "Una política deny reduce servicios alcanzables por error.",
        "severity": Severity.HIGH,
        "category": "Firewall",
        "cis_level": "Level 1 - Server",
        "check_key": "firewall_default_deny",
        "config": {"incoming": "deny"},
        "remediation_guidance": (
            "Establecer 'ufw default deny incoming' y 'ufw default allow outgoing' "
            "después de revisar las reglas explícitas de servicios."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 3.5.1.7", CIS_SOURCE)
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado en el benchmark v1.0.0.",
    },
    {
        "code": "UPDATES",
        "cis_reference": "1.9",
        "title": "Actualizaciones y parches de seguridad instalados",
        "description": (
            "No deben existir actualizaciones pendientes en el sistema auditado. "
            "La comprobación automatizada revisa paquetes actualizables."
        ),
        "rationale": "Los parches corrigen vulnerabilidades conocidas explotables.",
        "severity": Severity.HIGH,
        "category": "Actualizaciones",
        "cis_level": "Level 1 - Server",
        "check_key": "pending_updates",
        "config": {"max_pending": 0},
        "remediation_guidance": (
            "Revisar 'apt list --upgradable', programar ventana de mantenimiento, aplicar "
            "actualizaciones y reiniciar si el kernel lo requiere. No aplicar a ciegas en producción."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 1.9", CIS_SOURCE)
        ],
        "is_official_mapping": True,
        "mapping_notes": (
            "El benchmark marca 1.9 como Manual. La comprobación es una automatización propia "
            "basada en paquetes pendientes; no sustituye la revisión de ciclo de parcheo."
        ),
    },
    {
        "code": "SHADOW-PERMS",
        "cis_reference": "6.1.5",
        "title": "Permisos restrictivos sobre /etc/shadow",
        "description": "El archivo /etc/shadow debe pertenecer a root:shadow y tener modo 640 o más restrictivo.",
        "rationale": "Protege hashes de contraseñas frente a lectura por usuarios no privilegiados.",
        "severity": Severity.HIGH,
        "category": "Permisos de archivos",
        "cis_level": "Level 1 - Server",
        "check_key": "shadow_permissions",
        "config": {"allowed_modes": ["640", "600", "400", "000"], "owner": "root", "group": "shadow"},
        "remediation_guidance": (
            "Ejecutar 'chown root:shadow /etc/shadow' y 'chmod 640 /etc/shadow'. "
            "Validar el acceso con 'getent shadow root' desde root."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 6.1.5", CIS_SOURCE)
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado en el benchmark v1.0.0.",
    },
    {
        "code": "LOGGING",
        "cis_reference": "4.2.2.2",
        "title": "Servicio de registro rsyslog habilitado",
        "description": "rsyslog debe estar instalado y su servicio habilitado/activo.",
        "rationale": "Sin registro local persistente se pierden evidencias de incidentes.",
        "severity": Severity.MEDIUM,
        "category": "Registro de eventos",
        "cis_level": "Level 1 - Server",
        "check_key": "logging_enabled",
        "config": {"service": "rsyslog"},
        "remediation_guidance": (
            "Instalar rsyslog si falta y ejecutar 'systemctl enable --now rsyslog'. "
            "Validar que /var/log/syslog recibe eventos."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 4.2.2.2", CIS_SOURCE)
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado en el benchmark v1.0.0.",
    },
    {
        "code": "AUDITD",
        "cis_reference": "4.1.1.2",
        "title": "auditd habilitado y activo",
        "description": "El servicio auditd debe estar habilitado y en ejecución.",
        "rationale": "Proporciona trazas de auditoría del sistema para investigación forense.",
        "severity": Severity.MEDIUM,
        "category": "Registro de eventos",
        "cis_level": "Level 2 - Server",
        "check_key": "auditd_enabled",
        "config": {"service": "auditd"},
        "remediation_guidance": (
            "Instalar auditd y ejecutar 'systemctl enable --now auditd'. Revisar las reglas "
            "antes de un despliegue masivo."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 4.1.1.2", CIS_SOURCE)
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado en el benchmark v1.0.0.",
    },
    {
        "code": "ASLR",
        "cis_reference": "1.5.1",
        "title": "Aleatorización del espacio de direcciones (ASLR)",
        "description": "kernel.randomize_va_space debe valer 2.",
        "rationale": "Dificulta la explotación de vulnerabilidades de memoria.",
        "severity": Severity.MEDIUM,
        "category": "Hardening del kernel",
        "cis_level": "Level 1 - Server",
        "check_key": "aslr_enabled",
        "config": {"expected": 2},
        "remediation_guidance": (
            "Establecer 'kernel.randomize_va_space=2' en un archivo de /etc/sysctl.d/, "
            "aplicar con 'sysctl --system' y verificar el valor."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, control 1.5.1", CIS_SOURCE)
        ],
        "is_official_mapping": True,
        "mapping_notes": "Identificador verificado en el benchmark v1.0.0.",
    },
    {
        "code": "SERVICES",
        "cis_reference": None,
        "title": "Servicios de red innecesarios deshabilitados",
        "description": (
            "Control interno: revisar servicios heredados o de compartición que no correspondan "
            "al propósito del servidor (telnet, rsh, xinetd, tftp, etc.)."
        ),
        "rationale": "Cada servicio expuesto amplía la superficie de ataque.",
        "severity": Severity.MEDIUM,
        "category": "Servicios",
        "cis_level": None,
        "check_key": "unnecessary_services",
        "config": {
            "services": [
                "telnet.socket",
                "rsh.socket",
                "rlogin.socket",
                "rexec.socket",
                "vsftpd.service",
                "xinetd.service",
                "tftp.socket",
                "avahi-daemon.service",
                "cups.service",
            ]
        },
        "remediation_guidance": (
            "Confirmar con el propietario del servidor que el servicio no es necesario. "
            "Luego deshabilitarlo/maskearlo y documentar el cambio. No detener servicios a ciegas."
        ),
        "references": [
            _ref("CIS Ubuntu Linux 22.04 LTS Benchmark v1.0.0, sección 2.4 (Manual)", CIS_SOURCE),
            _ref("CIS Controls v8.1: 4.8", "https://www.cisecurity.org/controls"),
        ],
        "is_official_mapping": False,
        "mapping_notes": (
            "Control interno inspirado en CIS 2.4; CIS no publica una lista universal de "
            "servicios innecesarios para cada servidor."
        ),
    },
]


def seed_reference_data(session: Session) -> CisBenchmark:
    """Inserta/actualiza permisos, roles y catálogo. Es idempotente."""
    perms_by_code: dict[str, Permission] = {}
    for code, module, description in PERMISSIONS:
        permission = session.scalar(select(Permission).where(Permission.code == code))
        if permission is None:
            permission = Permission(code=code, module=module, description=description)
            session.add(permission)
        else:
            permission.module = module
            permission.description = description
        perms_by_code[code] = permission
    session.flush()

    for role_code, (name, description, perm_codes) in ROLE_DEFINITIONS.items():
        role = session.scalar(select(Role).where(Role.code == role_code))
        if role is None:
            role = Role(code=role_code, name=name, description=description, is_system=True)
            session.add(role)
        else:
            role.name = name
            role.description = description
        role.permissions = [perms_by_code[code] for code in perm_codes]
    session.flush()

    benchmark = session.scalar(
        select(CisBenchmark).where(
            CisBenchmark.name == BENCHMARK_NAME,
            CisBenchmark.version == BENCHMARK_VERSION,
            CisBenchmark.os_family == BENCHMARK_OS,
        )
    )
    if benchmark is None:
        benchmark = CisBenchmark(
            name=BENCHMARK_NAME,
            version=BENCHMARK_VERSION,
            os_family=BENCHMARK_OS,
            description=(
                "Catálogo inicial de controles Linux. Los identificadores CIS se contrastaron "
                "con el benchmark v1.0.0; los controles internos están marcados como tales. "
                "El alcance soportado del motor es Ubuntu 22.04/24.04 con OpenSSH y APT."
            ),
            source_url=CIS_SOURCE,
            is_official=True,
            mapping_status="verified_partial",
        )
        session.add(benchmark)
        session.flush()

    existing = {
        control.code: control
        for control in session.scalars(
            select(CisControl).where(CisControl.benchmark_id == benchmark.id)
        )
    }
    for item in CONTROLS:
        control = existing.get(item["code"])
        if control is None:
            control = CisControl(benchmark_id=benchmark.id, code=item["code"])
            session.add(control)
        for field in (
            "cis_reference",
            "title",
            "description",
            "rationale",
            "severity",
            "category",
            "cis_level",
            "check_key",
            "config",
            "remediation_guidance",
            "references",
            "is_official_mapping",
            "mapping_notes",
        ):
            setattr(control, field, item[field])
        control.automated = True
        control.is_active = True
    session.flush()
    return benchmark


def ensure_default_profile(session: Session, organization_id, user_id=None) -> AuditProfile:
    """Crea el perfil por defecto de una organización si no existe."""
    profile = session.scalar(
        select(AuditProfile).where(
            AuditProfile.organization_id == organization_id,
            AuditProfile.is_default.is_(True),
        )
    )
    if profile is not None:
        return profile
    benchmark = session.scalar(
        select(CisBenchmark).where(
            CisBenchmark.name == BENCHMARK_NAME,
            CisBenchmark.version == BENCHMARK_VERSION,
            CisBenchmark.os_family == BENCHMARK_OS,
        )
    )
    if benchmark is None:
        benchmark = seed_reference_data(session)
    profile = AuditProfile(
        organization_id=organization_id,
        benchmark_id=benchmark.id,
        name="Línea base CIS Ubuntu 22.04",
        description=(
            "Perfil inicial con todos los controles automatizados del catálogo. "
            "Los controles internos están identificados como tales."
        ),
        is_default=True,
        created_by_id=user_id,
    )
    session.add(profile)
    session.flush()
    controls = session.scalars(
        select(CisControl).where(
            CisControl.benchmark_id == benchmark.id, CisControl.is_active.is_(True)
        )
    ).all()
    for control in controls:
        session.add(
            AuditProfileControl(profile_id=profile.id, control_id=control.id, enabled=True)
        )
    session.flush()
    return profile
