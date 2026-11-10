#!/usr/local/bin/python3
"""Emulador mínimo de herramientas que dependen de systemd/apt/sshd en el entorno de pruebas.

Se invoca por enlace simbólico (systemctl, sshd, ufw, rsyslogd, auditctl, apt-get). Lee el
estado del host desde $HOST_STATE (JSON). Los archivos de configuración (/etc/...) NO se
emulan: son archivos reales montados con overlayfs y los lee el comando real del control.
"""
import json
import os
import sys

name = os.path.basename(sys.argv[0])
state = json.load(open(os.environ["HOST_STATE"]))
args = sys.argv[1:]

SSHD_DEFAULTS = {
    "permitrootlogin": "without-password",
    "maxauthtries": "6",
    "permitemptypasswords": "no",
    "passwordauthentication": "yes",
    "pubkeyauthentication": "yes",
}


def unit(u):
    return state["services"].get(u if "." in u else u + ".service")


if name == "sshd":
    if "-T" in args:
        cfg = dict(SSHD_DEFAULTS)
        seen = set()
        try:
            for line in open("/etc/ssh/sshd_config"):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(None, 1)
                if len(parts) == 2:
                    k = parts[0].lower()
                    if k in SSHD_DEFAULTS and k not in seen:  # sshd: gana la primera aparición
                        cfg[k] = parts[1].split()[0].lower()
                        seen.add(k)
        except OSError:
            sys.exit(1)
        for k, v in cfg.items():
            print(f"{k} {v}")
    sys.exit(0)

if name == "systemctl":
    if args and args[0] in ("is-enabled", "is-active"):
        u = unit(args[1])
        if args[0] == "is-enabled":
            if u is None or not u.get("installed"):
                print(f"Failed to get unit file state for {args[1]}.service: No such file or directory")
                sys.exit(1)
            print("enabled" if u["enabled"] else "disabled")
            sys.exit(0 if u["enabled"] else 1)
        else:
            print("active" if (u and u.get("active")) else "inactive")
            sys.exit(0 if (u and u.get("active")) else 3)
    if args and args[0] == "list-unit-files":
        kind = "socket" if "--type=socket" in args else "service"
        for uname in sorted(state["services"]):
            u = state["services"][uname]
            if u.get("installed") and u.get("enabled") and uname.endswith("." + kind):
                print(f"{uname:<40} enabled         enabled")
        sys.exit(0)
    sys.exit(0)

if name == "apt-get":
    if "upgrade" in args:
        for i in range(int(state["pending_updates"])):
            print(f"Inst paquete{i:03d} [1.{i}-0ubuntu1] (1.{i}-0ubuntu1.1 Ubuntu:24.04/noble-updates [amd64])")
        print("Conf paquete000 (1.0-0ubuntu1.1 Ubuntu:24.04/noble-updates [amd64])")
    sys.exit(0)

# ufw, rsyslogd, auditctl: solo su presencia importa a los controles
sys.exit(0)
