"""Lectura de solo lectura de la base PostgreSQL del proyecto."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg
from dotenv import load_dotenv

from publication.model import Dataset

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


class LiveDataError(RuntimeError):
    pass


def _connection() -> psycopg.Connection:
    dsn = {
        "host": os.getenv("DB_HOST", "localhost"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "27auditoria"),
        "user": os.getenv("DB_USER", "postgres"),
        "password": os.getenv("DB_PASSWORD", ""),
        "options": "-c default_transaction_read_only=on",
        "connect_timeout": 5,
    }
    return psycopg.connect(**dsn)


def _query(conn: psycopg.Connection, sql: str, params: tuple = ()) -> pd.DataFrame:
    with conn.cursor() as cur:
        cur.execute(sql, params)
        if cur.description is None:
            return pd.DataFrame()
        columns = [item.name for item in cur.description]
        rows = cur.fetchall()
    return pd.DataFrame(rows, columns=columns)


def available_organizations() -> pd.DataFrame:
    try:
        with _connection() as conn:
            return _query(
                conn,
                """
                SELECT id::text AS organization_id, name, slug
                FROM organizations
                WHERE is_active
                ORDER BY name
                """,
            )
    except Exception as exc:  # noqa: BLE001
        raise LiveDataError(
            "No se pudo conectar a PostgreSQL en modo lectura. Revise DB_* en .env."
        ) from exc


def dataset_is_available(org_id: str | None = None) -> bool:
    try:
        with _connection() as conn:
            params: tuple = ()
            condition = ""
            if org_id:
                condition = "WHERE organization_id = %s::uuid"
                params = (org_id,)
            row = _query(
                conn,
                f"SELECT count(*) AS n FROM audit_runs {condition}",
                params,
            )
            return bool(row.iloc[0]["n"])
    except Exception:  # noqa: BLE001
        return False


def load_live_dataset(org_id: str) -> Dataset:
    with _connection() as conn:
        organization = _query(
            conn,
            "SELECT id::text AS organization_id, name, slug FROM organizations WHERE id = %s::uuid",
            (org_id,),
        )
        if organization.empty:
            raise LiveDataError("La organización no existe.")
        org_name = organization.iloc[0]["name"]

        controls = _query(
            conn,
            """
            SELECT ct.code,
                   COALESCE(ct.cis_reference, '') AS cis_reference,
                   ct.title,
                   ct.severity,
                   ct.category,
                   COALESCE(ct.cis_level, '') AS cis_level,
                   ct.is_official_mapping AS official,
                   ct.description
            FROM cis_controls ct
            JOIN cis_benchmarks b ON b.id = ct.benchmark_id
            WHERE ct.is_active
            ORDER BY ct.code
            """,
        )
        if controls.empty:
            raise LiveDataError("No hay catálogo de controles en la base.")
        controls["official"] = controls["official"].astype(bool)

        servers = _query(
            conn,
            """
            SELECT s.id::text AS server_id,
                   s.name,
                   s.hostname,
                   s.ip_address,
                   s.os_family,
                   s.os_version,
                   s.environment,
                   COALESCE(s.owner_area, '') AS owner_area,
                   s.connection_method,
                   s.auth_method,
                   s.is_simulated,
                   s.status,
                   COALESCE(p.name, '') AS profile_name
            FROM servers s
            LEFT JOIN audit_profiles p ON p.id = s.default_profile_id
            WHERE s.organization_id = %s::uuid
            ORDER BY s.name
            """,
            (org_id,),
        )
        if servers.empty:
            raise LiveDataError("La organización no tiene servidores registrados.")
        servers["is_simulated"] = servers["is_simulated"].astype(bool)
        servers["connection_method"] = servers["connection_method"].map(
            {"ssh": "SSH", "simulated": "Simulado"}
        ).fillna(servers["connection_method"])
        servers["auth_method"] = servers["auth_method"].map(
            {"key": "Clave SSH", "password": "Contraseña"}
        ).fillna(servers["auth_method"])
        servers["os_family"] = servers["os_family"].str.title()

        runs = _query(
            conn,
            """
            SELECT r.id::text AS run_id,
                   r.server_id::text AS server_id,
                   s.name AS server_name,
                   COALESCE(r.finished_at, r.started_at, r.created_at) AS run_date,
                   COALESCE(p.name, '') AS profile_name,
                   r.benchmark_version,
                   r.status,
                   r.trigger_type,
                   r.total_controls,
                   r.passed_count AS passed,
                   r.failed_count AS failed,
                   r.not_applicable_count AS not_applicable,
                   r.not_evaluated_count AS not_evaluated,
                   r.applicable_count AS applicable,
                   r.score::float AS score,
                   r.is_simulated,
                   CASE
                     WHEN r.started_at IS NOT NULL AND r.finished_at IS NOT NULL
                     THEN EXTRACT(EPOCH FROM (r.finished_at - r.started_at))
                     ELSE NULL
                   END AS duration_seconds
            FROM audit_runs r
            JOIN servers s ON s.id = r.server_id
            LEFT JOIN audit_profiles p ON p.id = r.profile_id
            WHERE r.organization_id = %s::uuid
            ORDER BY r.created_at
            """,
            (org_id,),
        )
        if runs.empty:
            raise LiveDataError("La organización no tiene ejecuciones de auditoría.")
        runs["is_simulated"] = runs["is_simulated"].astype(bool)
        runs["coverage"] = (
            runs["applicable"].astype(float) / runs["total_controls"].replace(0, pd.NA) * 100
        ).round(2)
        runs["duration_seconds"] = runs["duration_seconds"].astype(float).round(2)

        checks = _query(
            conn,
            """
            SELECT c.run_id::text AS run_id,
                   r.server_id::text AS server_id,
                   s.name AS server_name,
                   COALESCE(r.finished_at, r.started_at, r.created_at) AS run_date,
                   ct.code AS control_code,
                   ct.title AS control_title,
                   ct.category,
                   c.severity,
                   COALESCE(ct.cis_reference, '') AS cis_reference,
                   ct.is_official_mapping AS official,
                   c.status,
                   c.duration_ms,
                   COALESCE(c.observed_value, '') AS observed_value
            FROM hardening_checks c
            JOIN audit_runs r ON r.id = c.run_id
            JOIN servers s ON s.id = r.server_id
            JOIN cis_controls ct ON ct.id = c.control_id
            WHERE r.organization_id = %s::uuid
            ORDER BY r.created_at, ct.code
            """,
            (org_id,),
        )
        if checks.empty:
            raise LiveDataError("No hay resultados de controles para la organización.")
        checks["official"] = checks["official"].astype(bool)

        findings = _query(
            conn,
            """
            SELECT f.id::text AS finding_id,
                   f.server_id::text AS server_id,
                   s.name AS server_name,
                   ct.code AS control_code,
                   ct.title AS control_title,
                   ct.category,
                   f.severity,
                   f.status,
                   f.priority,
                   f.occurrence_count,
                   f.first_seen_at,
                   f.last_seen_at,
                   f.resolved_at,
                   f.due_date,
                   COALESCE(s.owner_area, '') AS owner_area
            FROM findings f
            JOIN servers s ON s.id = f.server_id
            JOIN cis_controls ct ON ct.id = f.control_id
            WHERE f.organization_id = %s::uuid
            ORDER BY f.first_seen_at
            """,
            (org_id,),
        )

    latest = (
        runs[runs["status"] == "completed"]
        .sort_values("run_date")
        .groupby("server_id", as_index=False)
        .tail(1)
        .set_index("server_id")
    )
    active = findings[~findings["status"].isin(["resolved", "false_positive"])]
    active_by_server = active.groupby("server_id").size().to_dict() if not active.empty else {}
    servers["audit_count"] = servers["server_id"].map(runs.groupby("server_id").size()).fillna(0).astype(int)
    servers["last_audit_at"] = servers["server_id"].map(
        runs.groupby("server_id")["run_date"].max()
    )
    servers["latest_score"] = servers["server_id"].map(latest["score"]) if not latest.empty else None
    servers["latest_coverage"] = (
        servers["server_id"].map(latest["coverage"]) if not latest.empty else None
    )
    servers["active_findings"] = servers["server_id"].map(active_by_server).fillna(0).astype(int)

    return Dataset(
        source_type="postgresql",
        source_key=f"live-{org_id}",
        source_label=f"PostgreSQL · {org_name}",
        source_note=(
            f"Datos leídos en modo de solo lectura de la base institucional. "
            f"Organización: {org_name}. Ejecuciones: {len(runs)}; controles evaluados: {len(checks)}."
        ),
        organization=org_name,
        generated_at=datetime.now().replace(microsecond=0),
        servers=servers,
        runs=runs,
        checks=checks,
        controls=controls,
        findings=findings,
        metadata={
            "servers": len(servers),
            "runs": len(runs),
            "controls": len(controls),
            "checks": len(checks),
            "findings": len(findings),
            "formula": "score = aprobados / (aprobados + incumplidos) × 100",
            "warning": "Datos institucionales; revise autorización y anonimización antes de publicar.",
        },
    )
