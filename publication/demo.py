"""Dataset sintético reproducible para el anexo editorial.

No representa infraestructura real ni resultados empíricos. Se genera con una
semilla fija, la misma fórmula de scoring del producto y el catálogo real de 14
controles, de modo que las tablas y figuras puedan auditarse y regenerarse.
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from publication.model import Dataset

DATA_DIR = Path(__file__).resolve().parent / "data"
CONTROLS_CSV = DATA_DIR / "controls.csv"
SEED = 20261103
RUN_DATES = ["2026-07-15", "2026-08-19", "2026-09-23"]

SERVER_SPECS = [
    {
        "server_id": "SRV-WEB-01",
        "name": "Portal de clientes",
        "hostname": "web-prod-01.nexo.local",
        "ip_address": "10.20.10.15",
        "environment": "production",
        "owner_area": "Aplicaciones",
        "auth_method": "key",
        "base": 0.46,
        "trend": 0.12,
    },
    {
        "server_id": "SRV-API-01",
        "name": "API de pagos",
        "hostname": "api-pagos-01.nexo.local",
        "ip_address": "10.20.10.22",
        "environment": "production",
        "owner_area": "Pagos y fraude",
        "auth_method": "key",
        "base": 0.61,
        "trend": 0.10,
    },
    {
        "server_id": "SRV-DB-01",
        "name": "Base de datos de clientes",
        "hostname": "db-clientes-01.nexo.local",
        "ip_address": "10.20.20.11",
        "environment": "production",
        "owner_area": "Datos",
        "auth_method": "key",
        "base": 0.44,
        "trend": 0.13,
    },
    {
        "server_id": "SRV-BKP-01",
        "name": "Nodo de respaldo",
        "hostname": "backup-01.nexo.local",
        "ip_address": "10.20.30.40",
        "environment": "staging",
        "owner_area": "Infraestructura",
        "auth_method": "key",
        "base": 0.79,
        "trend": 0.06,
    },
    {
        "server_id": "SRV-MON-01",
        "name": "Observabilidad",
        "hostname": "monitor-01.nexo.local",
        "ip_address": "10.20.30.55",
        "environment": "production",
        "owner_area": "Operaciones",
        "auth_method": "key",
        "base": 0.67,
        "trend": 0.08,
    },
    {
        "server_id": "SRV-DEV-01",
        "name": "Herramientas de desarrollo",
        "hostname": "devtools-01.nexo.local",
        "ip_address": "10.20.40.18",
        "environment": "development",
        "owner_area": "Desarrollo",
        "auth_method": "password",
        "base": 0.35,
        "trend": 0.12,
    },
    {
        "server_id": "SRV-DNS-01",
        "name": "DNS interno",
        "hostname": "dns-01.nexo.local",
        "ip_address": "10.20.50.5",
        "environment": "production",
        "owner_area": "Redes",
        "auth_method": "key",
        "base": 0.72,
        "trend": 0.09,
    },
    {
        "server_id": "SRV-ERP-01",
        "name": "ERP heredado",
        "hostname": "erp-legacy-01.nexo.local",
        "ip_address": "10.20.60.9",
        "environment": "production",
        "owner_area": "ERP",
        "auth_method": "password",
        "base": 0.30,
        "trend": 0.10,
    },
]

CONTROL_BIAS = {
    "SSH-ROOT": -0.06,
    "SSH-MAXAUTH": 0.04,
    "SSH-EMPTY": 0.20,
    "SSH-KEYONLY": -0.14,
    "AUTH-PWQUALITY": -0.02,
    "AUTH-FAILLOCK": -0.08,
    "FW-ENABLED": 0.10,
    "FW-DEFAULT": 0.05,
    "UPDATES": -0.18,
    "SHADOW-PERMS": 0.16,
    "LOGGING": 0.18,
    "AUDITD": -0.05,
    "ASLR": 0.12,
    "SERVICES": -0.16,
}
NE_RATE = {
    "AUDITD": 0.09,
    "UPDATES": 0.08,
    "SERVICES": 0.06,
    "LOGGING": 0.03,
    "AUTH-FAILLOCK": 0.03,
}
PRIORITY = {"critical": 1, "high": 2, "medium": 3, "low": 4, "info": 5}
DUE_DAYS = {"critical": 7, "high": 30, "medium": 60, "low": 90, "info": 180}


def _load_controls() -> pd.DataFrame:
    controls = pd.read_csv(CONTROLS_CSV, encoding="utf-8-sig")
    controls["official"] = controls["official"].astype(str).str.lower().eq("true")
    return controls


def _pick_finding_status(severity: str, rng: random.Random) -> str:
    weights = {
        "critical": [
            ("in_review", 0.32),
            ("correction_planned", 0.34),
            ("fixed_pending_validation", 0.12),
            ("detected", 0.12),
            ("risk_accepted", 0.08),
            ("false_positive", 0.02),
        ],
        "high": [
            ("in_review", 0.27),
            ("correction_planned", 0.30),
            ("fixed_pending_validation", 0.14),
            ("detected", 0.16),
            ("risk_accepted", 0.09),
            ("false_positive", 0.04),
        ],
        "medium": [
            ("detected", 0.24),
            ("in_review", 0.22),
            ("correction_planned", 0.22),
            ("fixed_pending_validation", 0.10),
            ("risk_accepted", 0.16),
            ("false_positive", 0.06),
        ],
        "low": [
            ("detected", 0.26),
            ("in_review", 0.18),
            ("correction_planned", 0.15),
            ("risk_accepted", 0.25),
            ("false_positive", 0.16),
        ],
        "info": [
            ("detected", 0.30),
            ("risk_accepted", 0.30),
            ("false_positive", 0.20),
            ("in_review", 0.20),
        ],
    }[severity]
    names = [item[0] for item in weights]
    probs = [item[1] for item in weights]
    return rng.choices(names, weights=probs, k=1)[0]


def build_demo_dataset() -> Dataset:
    rng = random.Random(SEED)
    controls = _load_controls()
    control_rows = controls.set_index("code").to_dict("index")
    servers_rows: list[dict] = []
    runs_rows: list[dict] = []
    checks_rows: list[dict] = []

    for server_index, spec in enumerate(SERVER_SPECS):
        servers_rows.append(
            {
                "server_id": spec["server_id"],
                "name": spec["name"],
                "hostname": spec["hostname"],
                "ip_address": spec["ip_address"],
                "os_family": "Ubuntu",
                "os_version": "22.04 LTS",
                "environment": spec["environment"],
                "owner_area": spec["owner_area"],
                "connection_method": "SSH",
                "auth_method": "Clave SSH" if spec["auth_method"] == "key" else "Contraseña",
                "profile_name": "Línea base CIS Ubuntu 22.04",
                "is_simulated": True,
            }
        )
        for run_index, date_text in enumerate(RUN_DATES):
            run_date = datetime.strptime(date_text, "%Y-%m-%d") + timedelta(hours=3 + server_index % 2)
            run_id = f"RUN-{server_index + 1:02d}-{run_index + 1:02d}"
            statuses: list[str] = []
            durations: list[int] = []
            for _, control in controls.iterrows():
                code = control["code"]
                proficiency = spec["base"] + spec["trend"] * run_index
                probability = proficiency + CONTROL_BIAS.get(code, 0.0) + rng.uniform(-0.10, 0.10)
                probability = max(0.04, min(0.97, probability))
                na_rate = 0.025 if code == "FW-DEFAULT" else 0.008
                ne_rate = NE_RATE.get(code, 0.018)
                roll = rng.random()
                if roll < na_rate:
                    status = "not_applicable"
                elif roll < na_rate + ne_rate:
                    status = "not_evaluated"
                elif rng.random() < probability:
                    status = "passed"
                else:
                    status = "failed"
                statuses.append(status)
                duration = int(rng.uniform(160, 820))
                if code in {"UPDATES", "AUDITD", "SERVICES"}:
                    duration += int(rng.uniform(350, 1100))
                durations.append(duration)
                observed = {
                    "passed": "Criterio verificado en la evidencia recopilada.",
                    "failed": "El parámetro observado no satisface el criterio del control.",
                    "not_applicable": "El requisito no aplica al rol del servidor en la muestra.",
                    "not_evaluated": "No fue posible obtener evidencia suficiente para evaluar.",
                }[status]
                checks_rows.append(
                    {
                        "run_id": run_id,
                        "server_id": spec["server_id"],
                        "server_name": spec["name"],
                        "run_date": run_date,
                        "control_code": code,
                        "control_title": control["title"],
                        "category": control["category"],
                        "severity": control["severity"],
                        "cis_reference": control["cis_reference"] or "",
                        "official": bool(control["official"]),
                        "status": status,
                        "duration_ms": duration,
                        "observed_value": observed,
                    }
                )
            passed = statuses.count("passed")
            failed = statuses.count("failed")
            na = statuses.count("not_applicable")
            ne = statuses.count("not_evaluated")
            applicable = passed + failed
            score = round(100 * passed / applicable, 2) if applicable else None
            coverage = round(100 * applicable / len(statuses), 2)
            runs_rows.append(
                {
                    "run_id": run_id,
                    "server_id": spec["server_id"],
                    "server_name": spec["name"],
                    "run_date": run_date,
                    "profile_name": "Línea base CIS Ubuntu 22.04",
                    "benchmark_version": "1.0.0",
                    "status": "completed",
                    "trigger_type": ["manual", "schedule", "automation"][run_index],
                    "total_controls": len(statuses),
                    "passed": passed,
                    "failed": failed,
                    "not_applicable": na,
                    "not_evaluated": ne,
                    "applicable": applicable,
                    "score": score,
                    "coverage": coverage,
                    "duration_seconds": round(1.4 + sum(durations) / 1000 + rng.uniform(0.2, 0.9), 2),
                    "is_simulated": True,
                }
            )

    checks = pd.DataFrame(checks_rows)
    runs = pd.DataFrame(runs_rows)

    finding_rows: list[dict] = []
    for spec in SERVER_SPECS:
        for _, control in controls.iterrows():
            subset = checks[
                (checks["server_id"] == spec["server_id"])
                & (checks["control_code"] == control["code"])
            ].sort_values("run_date")
            failures = subset[subset["status"] == "failed"]
            if failures.empty:
                continue
            first = failures.iloc[0]
            last_failure = failures.iloc[-1]
            latest = subset.iloc[-1]
            occurrence = int(len(failures))
            resolved = latest["status"] == "passed"
            if resolved:
                status = "resolved"
                resolved_at = latest["run_date"]
            else:
                status = _pick_finding_status(control["severity"], rng)
                if (len(finding_rows) + 1) % 23 == 0 and control["severity"] in {"high", "medium"}:
                    status = "false_positive"
                resolved_at = None
            finding_rows.append(
                {
                    "finding_id": f"F-{len(finding_rows) + 1:04d}",
                    "server_id": spec["server_id"],
                    "server_name": spec["name"],
                    "control_code": control["code"],
                    "control_title": control["title"],
                    "category": control["category"],
                    "severity": control["severity"],
                    "status": status,
                    "priority": PRIORITY[control["severity"]],
                    "occurrence_count": occurrence,
                    "first_seen_at": first["run_date"],
                    "last_seen_at": last_failure["run_date"],
                    "resolved_at": resolved_at,
                    "due_date": first["run_date"]
                    + timedelta(days=DUE_DAYS[control["severity"]]),
                    "owner_area": spec["owner_area"],
                }
            )
    findings = pd.DataFrame(finding_rows)

    latest_by_server = (
        runs.sort_values("run_date").groupby("server_id", as_index=False).tail(1).set_index("server_id")
    )
    active_findings = findings[~findings["status"].isin(["resolved", "false_positive"])]
    active_by_server = active_findings.groupby("server_id").size().to_dict()
    for row in servers_rows:
        latest = latest_by_server.loc[row["server_id"]]
        row["audit_count"] = int((runs["server_id"] == row["server_id"]).sum())
        row["last_audit_at"] = latest["run_date"]
        row["latest_score"] = latest["score"]
        row["latest_coverage"] = latest["coverage"]
        row["active_findings"] = int(active_by_server.get(row["server_id"], 0))
        row["status"] = "online"

    servers = pd.DataFrame(servers_rows)
    return Dataset(
        source_type="synthetic",
        source_key="demo-v1",
        source_label="Dataset sintético reproducible",
        source_note=(
            "Datos sintéticos generados con semilla 20261103: 8 servidores, 3 ejecuciones "
            "por servidor y 14 controles. No son mediciones empíricas ni infraestructura real."
        ),
        organization="Organización sintética de demostración",
        generated_at=datetime.now().replace(microsecond=0),
        servers=servers,
        runs=runs,
        checks=checks,
        controls=controls,
        findings=findings,
        metadata={
            "seed": SEED,
            "servers": len(servers),
            "runs": len(runs),
            "controls": len(controls),
            "checks": len(checks),
            "findings": len(findings),
            "period": f"{RUN_DATES[0]} a {RUN_DATES[-1]}",
            "formula": "score = aprobados / (aprobados + incumplidos) × 100",
            "warning": "DATOS SIMULADOS: no usar como resultados empíricos.",
        },
    )
