#!/usr/local/bin/python3
"""Genera el dataset ejecutando el motor REAL de CIS Hardening Auditor (checks.py + scoring.py)
contra una flota de hosts de prueba materializados como archivos de /etc reales (overlayfs).

Uso: PYTHONPATH=<proyecto>/backend python3 build_dataset.py <dir_salida>
"""
from __future__ import annotations

import csv
import json
import os
import random
import shutil
import stat
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "x" * 48)
os.environ.setdefault("FERNET_KEY", "MDEyMzQ1Njc4OWFiY2RlZjAxMjM0NTY3ODlhYmNkZWY=")

from app.enums import CheckStatus  # noqa: E402
from app.reference_data import CONTROLS  # noqa: E402
from app.services.checks import run_check  # noqa: E402
from app.services.scoring import calculate_score  # noqa: E402
from app.services.ssh_connector import AuditConnectionError, CommandResult  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1]).resolve()
SEED = 20261104
N_HOSTS = 40
N_ROUNDS = 6
P_OFFLINE = 0.03     # prob. de que un host no responda en una ronda
P_TIMEOUT = 0.005    # prob. de timeout de un comando individual
CMD_TIMEOUT = 20

rng = random.Random(SEED)
RISKY = ["telnet.socket", "rsh.socket", "rlogin.socket", "rexec.socket", "vsftpd.service",
         "xinetd.service", "tftp.socket", "avahi-daemon.service", "cups.service"]
BENIGN = ["ssh.service", "cron.service", "systemd-resolved.service",
          "cups.path", "cups-browsed.service", "snapd.socket", "apparmor.service", "unattended-upgrades.service"]
CODES = [c["code"] for c in CONTROLS]
BY_CODE = {c["code"]: c for c in CONTROLS}

ORGS = ["Finanzas", "Operaciones", "Soporte TI", "Comercial"]
ENVS = ["production", "staging", "development"]
ARCHETYPES = {  # prob. base de que un control esté en cumplimiento
    "hardened": 0.90, "partial": 0.55, "default_install": 0.30, "neglected": 0.12,
}
ARCH_W = [0.20, 0.30, 0.30, 0.20]
FIX_RATE = {"production": 0.30, "staging": 0.20, "development": 0.10}
REGRESS = 0.03


# ----------------------------------------------------------------------------- variantes
def make_variant(code: str, ok: bool, r: random.Random) -> dict:
    """Devuelve la configuración intencionada de un control (cumple o no)."""
    if code == "SSH-ROOT":
        return {"v": "no" if ok else r.choice(["yes", "prohibit-password", "unset", "yes"]),
                "decoy": (not ok) and r.random() < 0.3}
    if code == "SSH-MAXAUTH":
        return {"v": r.choice([2, 3, 4]) if ok else r.choice(["unset", 5, 6, 8, 10])}
    if code == "SSH-EMPTY":
        return {"v": r.choice(["no", "unset"]) if ok else "yes"}
    if code == "SSH-KEYONLY":
        return {"pw": "no" if ok else r.choice(["yes", "unset"]),
                "pubkey": "yes" if ok or r.random() < 0.9 else "no"}
    if code == "AUTH-PWQUALITY":
        if ok:
            return {"conf": True, "minlen": r.choice([14, 14, 15, 16]), "pam": True, "pam_commented": False,
                    "minlen_commented": False}
        kind = r.choice(["short", "unset", "nopam", "noconf", "pam_commented", "minlen_commented"])
        return {"conf": kind != "noconf", "minlen": {"short": r.choice([6, 8, 10, 12])}.get(kind),
                "pam": kind != "nopam", "pam_commented": kind == "pam_commented",
                "minlen_commented": kind == "minlen_commented", "kind": kind,
                **({"minlen": 14} if kind in ("pam_commented", "nopam") else {})}
    if code == "AUTH-FAILLOCK":
        where = r.choice(["conf", "conf", "pamline"])
        if ok:
            return {"pam": True, "pam_commented": False, "deny": r.choice([3, 4, 5]),
                    "unlock": r.choice([900, 1200, 1800]), "where": where}
        kind = r.choice(["nopam", "weak_deny", "weak_unlock", "unset", "pam_commented"])
        return {"pam": kind != "nopam", "pam_commented": kind == "pam_commented",
                "deny": 5 if kind in ("pam_commented", "weak_unlock", "nopam") else (10 if kind == "weak_deny" else None),
                "unlock": 900 if kind in ("pam_commented", "weak_deny", "nopam") else (300 if kind == "weak_unlock" else None),
                "where": where, "kind": kind}
    if code == "FW-ENABLED":
        if ok:
            return {"installed": True, "conf": "yes", "enabled": True, "active": True}
        kind = r.choice(["notinstalled", "conf_no", "inactive", "disabled"])
        return {"installed": kind != "notinstalled", "conf": "no" if kind == "conf_no" else "yes",
                "enabled": kind != "disabled", "active": kind not in ("inactive", "conf_no"), "kind": kind}
    if code == "FW-DEFAULT":
        return {"policy": r.choice(["DROP", "REJECT"]) if ok else "ACCEPT"}
    if code == "UPDATES":
        return {"pending": 0 if ok else r.randint(1, 45)}
    if code == "SHADOW-PERMS":
        if ok:
            return {"mode": r.choice(["640", "640", "600", "000"]), "owner": "root", "group": "shadow"}
        return r.choice([{"mode": "644", "owner": "root", "group": "shadow"},
                         {"mode": "666", "owner": "root", "group": "shadow"},
                         {"mode": "640", "owner": "nobody", "group": "shadow"},
                         {"mode": "664", "owner": "root", "group": "root"}])
    if code == "LOGGING":
        if ok:
            return {"installed": True, "enabled": True, "active": True}
        kind = r.choice(["notinstalled", "inactive", "disabled"])
        return {"installed": kind != "notinstalled", "enabled": kind != "disabled", "active": kind == "disabled", "kind": kind}
    if code == "AUDITD":
        if ok:
            return {"installed": True, "enabled": True, "active": True}
        kind = r.choice(["notinstalled", "notinstalled", "inactive", "disabled"])
        return {"installed": kind != "notinstalled", "enabled": kind != "disabled", "active": kind == "disabled", "kind": kind}
    if code == "ASLR":
        return {"v": 2 if ok else r.choice([0, 1])}
    if code == "SERVICES":
        return {"risky": [] if ok else r.sample(RISKY, r.choice([1, 1, 2, 3])),
                "benign": r.sample(BENIGN, r.randint(2, 5))}
    raise KeyError(code)


def ground_truth(code: str, v: dict, ssh_installed: bool, fw_installed: bool = True) -> str:
    """Resultado esperado según el criterio documentado del control (independiente del evaluador)."""
    ssh_codes = {"SSH-ROOT", "SSH-MAXAUTH", "SSH-EMPTY", "SSH-KEYONLY"}
    if code in ssh_codes and not ssh_installed:
        return "not_applicable"
    P, F = "passed", "failed"
    if code == "SSH-ROOT":
        return P if v["v"] == "no" else F
    if code == "SSH-MAXAUTH":
        return P if v["v"] != "unset" and int(v["v"]) <= 4 else F
    if code == "SSH-EMPTY":
        return F if v["v"] == "yes" else P
    if code == "SSH-KEYONLY":
        return P if v["pw"] == "no" and v["pubkey"] != "no" else F
    if code == "AUTH-PWQUALITY":
        ok = v["conf"] and v["minlen"] is not None and not v["minlen_commented"] and v["minlen"] >= 14 \
            and v["pam"] and not v["pam_commented"]
        return P if ok else F
    if code == "AUTH-FAILLOCK":
        ok = v["pam"] and not v["pam_commented"] and v["deny"] is not None and v["deny"] <= 5 \
            and v["unlock"] is not None and v["unlock"] >= 900
        return P if ok else F
    if code == "FW-ENABLED":
        return P if v["installed"] and v["conf"] == "yes" and v["enabled"] and v["active"] else F
    if code == "FW-DEFAULT":
        # El criterio es la política de UFW: sin UFW instalado no hay política que evaluar (N/A).
        # (Corregido tras la corrida piloto: la primera versión asignaba passed/failed sin archivo de política.)
        if not fw_installed:
            return "not_applicable"
        return P if v["policy"] in ("DROP", "REJECT") else F
    if code == "UPDATES":
        return P if v["pending"] == 0 else F
    if code == "SHADOW-PERMS":
        return P if v["mode"] in ("640", "600", "400", "000") and v["owner"] == "root" and v["group"] in ("shadow", "root") else F
    if code in ("LOGGING", "AUDITD"):
        return P if v["installed"] and v["enabled"] and v["active"] else F
    if code == "ASLR":
        return P if v["v"] == 2 else F
    if code == "SERVICES":
        return P if not v["risky"] else F
    raise KeyError(code)


# ----------------------------------------------------------------------------- materialización
def whiteout(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        path.unlink()
    os.mknod(path, 0o600 | stat.S_IFCHR, os.makedev(0, 0))


def put(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() or path.is_symlink():
        path.unlink()
    path.write_text(text)


def render_host(hdir: Path, st: dict) -> None:
    up = hdir / "up"
    if up.exists():
        shutil.rmtree(up)
    (hdir / "wk").mkdir(exist_ok=True)
    v = st["v"]
    # --- sshd_config
    if st["ssh_installed"]:
        lines = ["# /etc/ssh/sshd_config (host de prueba)", "Include /etc/ssh/sshd_config.d/*.conf",
                 "KbdInteractiveAuthentication no", "UsePAM yes", "X11Forwarding yes",
                 "Subsystem sftp /usr/lib/openssh/sftp-server"]
        r = v["SSH-ROOT"]
        if r["v"] != "unset":
            lines.append(f"PermitRootLogin {r['v']}")
        elif r.get("decoy"):
            lines.append("#PermitRootLogin no")
        if r.get("decoy") and r["v"] != "unset":
            lines.append("#PermitRootLogin no")
        m = v["SSH-MAXAUTH"]["v"]
        lines.append("#MaxAuthTries 6" if m == "unset" else f"MaxAuthTries {m}")
        e = v["SSH-EMPTY"]["v"]
        lines.append("#PermitEmptyPasswords no" if e == "unset" else f"PermitEmptyPasswords {e}")
        k = v["SSH-KEYONLY"]
        lines.append("#PasswordAuthentication yes" if k["pw"] == "unset" else f"PasswordAuthentication {k['pw']}")
        lines.append(f"PubkeyAuthentication {k['pubkey']}")
        put(up / "ssh/sshd_config", "\n".join(lines) + "\n")
    # --- pwquality
    p = v["AUTH-PWQUALITY"]
    if p["conf"]:
        txt = ["# /etc/security/pwquality.conf", "# difok = 1", "# minlen = 8"]
        if p["minlen_commented"]:
            txt.append("# minlen = 14")
        elif p["minlen"] is not None:
            txt.append(f"minlen = {p['minlen']}")
        txt += ["minclass = 3", "retry = 3"]
        put(up / "security/pwquality.conf", "\n".join(txt) + "\n")
    else:
        whiteout(up / "security/pwquality.conf")
    pamline = "password\trequisite\t\t\tpam_pwquality.so retry=3"
    cp = ["# /etc/pam.d/common-password"]
    if p["pam"]:
        cp.append(("# " if p["pam_commented"] else "") + pamline)
    cp.append("password\t[success=1 default=ignore]\tpam_unix.so obscure use_authtok try_first_pass yescrypt")
    put(up / "pam.d/common-password", "\n".join(cp) + "\n")
    # --- faillock
    f = v["AUTH-FAILLOCK"]
    auth = ["# /etc/pam.d/common-auth"]
    fconf = ["# /etc/security/faillock.conf", "# deny = 3", "# unlock_time = 600"]
    if f["pam"]:
        extra = ""
        if f["where"] == "pamline":
            if f["deny"] is not None:
                extra += f" deny={f['deny']}"
            if f["unlock"] is not None:
                extra += f" unlock_time={f['unlock']}"
        auth.append(("# " if f["pam_commented"] else "") + "auth\trequired\t\t\tpam_faillock.so preauth" + extra)
    if f["where"] == "conf":
        if f["deny"] is not None:
            fconf.append(f"deny = {f['deny']}")
        if f["unlock"] is not None:
            fconf.append(f"unlock_time = {f['unlock']}")
    auth.append("auth\t[success=1 default=ignore]\tpam_unix.so nullok")
    put(up / "pam.d/common-auth", "\n".join(auth) + "\n")
    put(up / "security/faillock.conf", "\n".join(fconf) + "\n")
    put(up / "pam.d/common-account", "account\t[success=1 new_authtok_reqd=done default=ignore]\tpam_unix.so\n")
    # --- ufw
    fw = v["FW-ENABLED"]
    if fw["installed"]:
        put(up / "ufw/ufw.conf", f"# /etc/ufw/ufw.conf\nENABLED={fw['conf']}\nLOGLEVEL=low\n")
        put(up / "default/ufw", f"# /etc/default/ufw\nIPV6=yes\nDEFAULT_INPUT_POLICY=\"{v['FW-DEFAULT']['policy']}\"\n"
                                "DEFAULT_OUTPUT_POLICY=\"ACCEPT\"\nDEFAULT_FORWARD_POLICY=\"DROP\"\n")
    # --- shadow (archivo real con modo/propietario/grupo del host)
    sh = v["SHADOW-PERMS"]
    sp = up / "shadow"
    put(sp, "root:*:19000:0:99999:7:::\n")
    os.chmod(sp, int(sh["mode"], 8))
    import grp
    import pwd
    try:
        uid = pwd.getpwnam(sh["owner"]).pw_uid
    except KeyError:
        uid = 65534
    os.chown(sp, uid, grp.getgrnam(sh["group"]).gr_gid)
    # --- sysctl ASLR
    put(hdir / "aslr", f"{v['ASLR']['v']}\n")
    # --- estado para shims
    services = {}
    for s in v["SERVICES"]["benign"]:
        services[s] = {"installed": True, "enabled": True, "active": True}
    for s in v["SERVICES"]["risky"]:
        services[s] = {"installed": True, "enabled": True, "active": True}
    for unit_name, key in (("rsyslog.service", "LOGGING"), ("auditd.service", "AUDITD")):
        x = v[key]
        services[unit_name] = {"installed": x["installed"], "enabled": x["enabled"], "active": x["active"]}
    services["ufw.service"] = {"installed": fw["installed"], "enabled": fw["enabled"], "active": fw["active"]}
    (hdir / "state.json").write_text(json.dumps({"services": services, "pending_updates": v["UPDATES"]["pending"]}))
    # --- binarios presentes en el host
    hb = hdir / "bin"
    hb.mkdir(exist_ok=True)
    for f_ in hb.iterdir():
        f_.unlink()
    present = ["systemctl", "apt-get"]
    if st["ssh_installed"]:
        present.append("sshd")
    if fw["installed"]:
        present.append("ufw")
    if v["LOGGING"]["installed"]:
        present.append("rsyslogd")
    if v["AUDITD"]["installed"]:
        present.append("auditctl")
    for b in present:
        (hb / b).symlink_to(HERE / "shim.py")


class NamespaceConnector:
    """Implementa el protocolo AuditConnector (run_command) ejecutando en un mount namespace aislado
    con el /etc del host de prueba superpuesto (overlayfs). El resto del motor es el real."""

    SETUP = (
        'mount --make-rprivate / && '
        'mount -t overlay overlay -o lowerdir=/etc,upperdir="$HD/up",workdir="$HD/wk" /etc && '
        'mount --bind "$HD/aslr" /proc/sys/kernel/randomize_va_space && '
        'export PATH="$HD/bin:$PATH" HOST_STATE="$HD/state.json" && exec bash -c "$CHECK_CMD"'
    )

    def __init__(self, hdir: Path, offline: bool, timeout_keys: set[str]) -> None:
        self.hdir, self.offline, self.timeout_keys = hdir, offline, timeout_keys

    def run_command(self, command: str, check_key: str | None = None) -> CommandResult:
        if self.offline:
            raise AuditConnectionError("No fue posible conectar por SSH. Verifique IP, puerto, firewall y conectividad.")
        if check_key in self.timeout_keys:
            raise AuditConnectionError("La comprobación excedió el tiempo máximo de ejecución.")
        env = {"PATH": os.environ["PATH"], "HD": str(self.hdir), "CHECK_CMD": command}
        t0 = time.perf_counter()
        p = subprocess.run(["unshare", "-m", "bash", "-c", self.SETUP], env=env, capture_output=True,
                           text=True, timeout=CMD_TIMEOUT)
        ms = int((time.perf_counter() - t0) * 1000)
        return CommandResult(p.returncode, p.stdout, p.stderr, ms)

    def test(self):  # pragma: no cover
        raise NotImplementedError

    def close(self) -> None:
        pass


# ----------------------------------------------------------------------------- flota
def build_fleet() -> list[dict]:
    fleet = []
    for i in range(1, N_HOSTS + 1):
        arch = rng.choices(list(ARCHETYPES), ARCH_W)[0]
        env = rng.choices(ENVS, [0.4, 0.3, 0.3])[0]
        org = rng.choice(ORGS)
        ssh_installed = rng.random() > 0.05
        pbase = ARCHETYPES[arch]
        v = {}
        for code in CODES:
            # los controles de mayor esfuerzo (auditd, firewall, actualizaciones) cumplen menos
            adj = {"AUDITD": -0.25, "UPDATES": -0.20, "FW-DEFAULT": -0.05, "ASLR": +0.35,
                   "SHADOW-PERMS": +0.30, "SSH-EMPTY": +0.30, "LOGGING": +0.20}.get(code, 0)
            ok = rng.random() < min(max(pbase + adj, 0.03), 0.97)
            v[code] = make_variant(code, ok, rng)
        # coherencia: ufw no instalado => política por defecto irrelevante pero se mantiene el valor
        fleet.append({
            "host_id": f"H{i:03d}", "hostname": f"srv-{org.split()[0].lower()}-{env[:4]}-{i:02d}",
            "organization": org, "environment": env, "os": "Ubuntu 24.04 LTS", "archetype": arch,
            "ssh_installed": ssh_installed, "v": v,
        })
    return fleet


def evolve(st: dict, r: random.Random) -> None:
    v = st["v"]
    for code in CODES:
        truth = ground_truth(code, v[code], st["ssh_installed"], v["FW-ENABLED"]["installed"])
        sev_boost = 1.3 if BY_CODE[code]["severity"].value == "high" else 1.0
        if truth == "failed" and r.random() < FIX_RATE[st["environment"]] * sev_boost:
            v[code] = make_variant(code, True, r)
        elif truth == "passed" and code != "UPDATES" and r.random() < REGRESS:
            v[code] = make_variant(code, False, r)
    # parches y nuevas actualizaciones
    if r.random() < {"production": 0.40, "staging": 0.30, "development": 0.15}[st["environment"]]:
        v["UPDATES"]["pending"] = r.randint(0, 2)
    else:
        v["UPDATES"]["pending"] += r.randint(1, 8)


def audit_host_round(st: dict, rnd: int, work: Path, hrng: random.Random):
    hdir = work / st["host_id"]
    hdir.mkdir(parents=True, exist_ok=True)
    render_host(hdir, st)
    offline = hrng.random() < P_OFFLINE
    timeouts = {c["check_key"] for c in CONTROLS if hrng.random() < P_TIMEOUT}
    conn = NamespaceConnector(hdir, offline, timeouts)
    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    rows = []
    for c in CONTROLS:
        ctrl = SimpleNamespace(id=c["code"], check_key=c["check_key"], config=c["config"])
        out = run_check(conn, ctrl)
        gt = ground_truth(c["code"], st["v"][c["code"]], st["ssh_installed"], st["v"]["FW-ENABLED"]["installed"])
        fault = "host_offline" if offline else ("command_timeout" if c["check_key"] in timeouts else "")
        if fault:
            gt = "not_evaluated"
        rows.append({
            "host_id": st["host_id"], "round": rnd, "control_code": c["code"], "check_key": c["check_key"],
            "status": out.status.value, "observed_value": out.observed_value,
            "duration_ms": out.duration_ms, "ground_truth": gt, "injected_fault": fault,
            "error_message": out.error_message or "",
            "evidence": {k: out.evidence.get(k) for k in ("exit_status", "stdout", "stderr", "checked_at")},
        })
    total_ms = int((time.perf_counter() - t0) * 1000)
    return rows, started, total_ms


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    work = Path(os.environ.get("HOSTS_WORK", "/tmp/cis_hosts_work"))
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    fleet = build_fleet()
    all_rows, runs = [], []
    for rnd in range(1, N_ROUNDS + 1):
        if rnd > 1:
            for st in fleet:
                evolve(st, random.Random(f"{SEED}-evo-{st['host_id']}-{rnd}"))
        def job(st):
            return st, audit_host_round(st, rnd, work, random.Random(f"{SEED}-run-{st['host_id']}-{rnd}"))
        with ThreadPoolExecutor(max_workers=4) as ex:
            results = list(ex.map(job, fleet))
        for st, (rows, started, total_ms) in results:
            sc = calculate_score([r["status"] for r in rows])
            run_id = f"R{rnd}-{st['host_id']}"
            for r in rows:
                r["run_id"] = run_id
            all_rows += rows
            d = sc.as_dict()
            sev = {"high": 0, "medium": 0}
            for r in rows:
                if r["status"] == "failed":
                    sev[BY_CODE[r["control_code"]]["severity"].value] += 1
            runs.append({"run_id": run_id, "host_id": st["host_id"], "round": rnd,
                         "executed_at_utc": started.isoformat(timespec="seconds"), "total_duration_ms": total_ms,
                         "total_controls": d["total"], "passed": d["passed"], "failed": d["failed"],
                         "not_applicable": d["not_applicable"], "not_evaluated": d["not_evaluated"],
                         "compliance_pct": "" if d["score"] is None else d["score"], "coverage_pct": d["coverage"],
                         "failed_high": sev["high"], "failed_medium": sev["medium"],
                         "run_outcome": "unreachable" if d["not_evaluated"] == d["total"] else "completed"})
        print(f"ronda {rnd}/{N_ROUNDS} lista", flush=True)

    # ---- escritura
    def w(name, rows, fields):
        with open(OUT / name, "w", newline="", encoding="utf-8") as fh:
            wr = csv.DictWriter(fh, fieldnames=fields)
            wr.writeheader()
            wr.writerows(rows)

    w("servers.csv", [{k: s[k] for k in ("host_id", "hostname", "organization", "environment", "os", "archetype")}
                      | {"openssh_installed": s["ssh_installed"]} for s in fleet],
      ["host_id", "hostname", "organization", "environment", "os", "archetype", "openssh_installed"])
    w("controls.csv", [{"control_code": c["code"], "cis_reference": c["cis_reference"] or "",
                        "official_cis_mapping": c["is_official_mapping"], "title": c["title"],
                        "severity": c["severity"].value, "category": c["category"], "check_key": c["check_key"]}
                       for c in CONTROLS],
      ["control_code", "cis_reference", "official_cis_mapping", "title", "severity", "category", "check_key"])
    w("audit_runs.csv", runs, list(runs[0].keys()))
    sevmap = {c["code"]: c["severity"].value for c in CONTROLS}
    catmap = {c["code"]: c["category"] for c in CONTROLS}
    flat = []
    for r in all_rows:
        flat.append({"run_id": r["run_id"], "host_id": r["host_id"], "round": r["round"],
                     "control_code": r["control_code"], "severity": sevmap[r["control_code"]],
                     "category": catmap[r["control_code"]], "status": r["status"],
                     "ground_truth": r["ground_truth"], "match": r["status"] == r["ground_truth"],
                     "injected_fault": r["injected_fault"], "duration_ms": r["duration_ms"],
                     "observed_value": r["observed_value"], "error_message": r["error_message"]})
    w("check_results.csv", flat, list(flat[0].keys()))
    with open(OUT / "evidence.jsonl", "w", encoding="utf-8") as fh:
        for r in all_rows:
            fh.write(json.dumps({"run_id": r["run_id"], "control_code": r["control_code"],
                                 "status": r["status"], **r["evidence"]}, ensure_ascii=False) + "\n")

    # ---- hallazgos (ciclo de vida derivado de resultados reales)
    findings = []
    key = lambda r: (r["host_id"], r["control_code"])
    by = {}
    for r in sorted(all_rows, key=lambda x: x["round"]):
        by.setdefault(key(r), []).append(r)
    fid = 0
    for (h, c), seq in by.items():
        cur = None
        for r in seq:
            if r["status"] == "failed" and cur is None:
                fid += 1
                cur = {"finding_id": f"F{fid:04d}", "host_id": h, "control_code": c, "severity": sevmap[c],
                       "first_detected_round": r["round"], "resolved_round": "", "rounds_open": 1, "reopened": False}
                if any(x["status"] == "passed" for x in seq if x["round"] < r["round"]):
                    cur["reopened"] = True  # regresión
                findings.append(cur)
            elif r["status"] == "failed" and cur is not None:
                cur["rounds_open"] += 1
            elif r["status"] == "passed" and cur is not None:
                cur["resolved_round"] = r["round"]
                cur = None
    for f in findings:
        f["status"] = "resolved" if f["resolved_round"] != "" else "open"
    w("findings.csv", findings, list(findings[0].keys()))
    print("filas:", len(flat), "runs:", len(runs), "hallazgos:", len(findings))


if __name__ == "__main__":
    main()
