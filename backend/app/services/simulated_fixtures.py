"""Salidas simuladas para pruebas y generación de ejemplos.

Nunca se cargan en producción: el conector exige ENABLE_SIMULATED_CONNECTOR=true
y el servidor debe estar marcado explícitamente como simulado.
"""

from __future__ import annotations

GOOD: dict[str, str] = {
    "ssh_root_login": "__SSHD__=1\npermitrootlogin no\n",
    "ssh_max_auth_tries": "__SSHD__=1\nmaxauthtries 4\n",
    "ssh_permit_empty_passwords": "__SSHD__=1\npermitemptypasswords no\n",
    "ssh_password_authentication": (
        "__SSHD__=1\npasswordauthentication no\npubkeyauthentication yes\n"
    ),
    "password_quality": (
        "__PWCONF__=1\nminlen = 14\nminclass = 3\n"
        "password requisite pam_pwquality.so retry=3\n"
    ),
    "account_lockout": (
        "auth required pam_faillock.so preauth\n"
        "account required pam_faillock.so\n"
        "deny = 5\nunlock_time = 900\n"
    ),
    "firewall_enabled": "__UFW__=1\nenabled\nactive\nENABLED=yes\n",
    "firewall_default_deny": (
        "__UFW__=1\nDEFAULT_INPUT_POLICY=\"DROP\"\nDEFAULT_FORWARD_POLICY=\"DROP\"\n"
    ),
    "pending_updates": "__PENDING__=0\n",
    "shadow_permissions": (
        "640 root shadow /etc/shadow\n640 root shadow /etc/shadow-\n"
        "640 root shadow /etc/gshadow\n"
    ),
    "logging_enabled": "enabled\nactive\n/usr/sbin/rsyslogd\n",
    "auditd_enabled": "enabled\nactive\n/sbin/auditctl\n",
    "aslr_enabled": "2\n",
    "unnecessary_services": (
        "ssh.service enabled\ncron.service enabled\nsystemd-timesyncd.service enabled\n"
        "ssh.socket enabled\n"
    ),
}

BAD: dict[str, str] = {
    "ssh_root_login": "__SSHD__=1\npermitrootlogin yes\n",
    "ssh_max_auth_tries": "__SSHD__=1\nmaxauthtries 6\n",
    "ssh_permit_empty_passwords": "__SSHD__=1\npermitemptypasswords no\n",
    "ssh_password_authentication": (
        "__SSHD__=1\npasswordauthentication yes\npubkeyauthentication yes\n"
    ),
    "password_quality": (
        "__PWCONF__=1\nminlen = 8\nminclass = 1\n"
        "password requisite pam_pwquality.so retry=3\n"
    ),
    "account_lockout": "auth required pam_unix.so\naccount required pam_unix.so\n",
    "firewall_enabled": "__UFW__=1\nenabled\nactive\nENABLED=yes\n",
    "firewall_default_deny": (
        "__UFW__=1\nDEFAULT_INPUT_POLICY=\"ACCEPT\"\nDEFAULT_FORWARD_POLICY=\"DROP\"\n"
    ),
    "pending_updates": "__PENDING__=3\n",
    "shadow_permissions": (
        "640 root shadow /etc/shadow\n644 root shadow /etc/shadow-\n"
        "644 root shadow /etc/gshadow\n"
    ),
    "logging_enabled": "enabled\nactive\n/usr/sbin/rsyslogd\n",
    "auditd_enabled": "disabled\ninactive\n",
    "aslr_enabled": "2\n",
    "unnecessary_services": (
        "ssh.service enabled\ncron.service enabled\n"
        "avahi-daemon.service enabled\nvsftpd.service enabled\n"
    ),
}


def fixture_for(check_key: str, good: bool) -> tuple[str, int]:
    data = GOOD if good else BAD
    if check_key not in data:
        return "", 0
    return data[check_key], 0
