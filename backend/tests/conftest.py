from __future__ import annotations

import os
import shutil
import subprocess
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus

import psycopg
import pytest
from cryptography.fernet import Fernet
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from psycopg import sql

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_ENV = dotenv_values(BACKEND_DIR.parent / ".env")

DB_HOST = os.getenv("TEST_DB_HOST", ROOT_ENV.get("DB_HOST", "localhost"))
DB_PORT = os.getenv("TEST_DB_PORT", ROOT_ENV.get("DB_PORT", "5432"))
DB_USER = os.getenv("TEST_DB_USER", ROOT_ENV.get("DB_USER", "postgres"))
DB_PASSWORD = os.getenv("TEST_DB_PASSWORD", ROOT_ENV.get("DB_PASSWORD", ""))
TEST_DB_NAME = os.getenv("TEST_DB_NAME", "27auditoria_test")
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    f"postgresql+psycopg://{quote_plus(DB_USER)}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{TEST_DB_NAME}",
)
ADMIN_DSN = f"host={DB_HOST} port={DB_PORT} user={DB_USER} password={DB_PASSWORD} dbname=postgres"

os.environ["DATABASE_URL_OVERRIDE"] = TEST_DATABASE_URL
os.environ["ENVIRONMENT"] = "test"
os.environ["DEBUG"] = "false"
os.environ["SECRET_KEY"] = "test-" + "x" * 48
os.environ["FERNET_KEY"] = Fernet.generate_key().decode()
os.environ["COOKIE_SECURE"] = "false"
os.environ["ENABLE_SIMULATED_CONNECTOR"] = "true"
os.environ["AUDIT_ALLOW_PRIVATE_TARGETS"] = "false"
os.environ["AI_ENABLED"] = "false"
os.environ["ALLOWED_HOSTS"] = "testserver,localhost,127.0.0.1"
os.environ["CORS_ORIGINS"] = "http://testserver"
os.environ["ARTIFACT_STORAGE_DIR"] = "generated_test"
os.environ["LOGIN_RATE_MAX_REQUESTS"] = "100"
os.environ["LOGIN_MAX_ATTEMPTS"] = "5"

ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Auditoria!2026-Segura"


@dataclass
class ApiContext:
    client: TestClient
    token: str
    headers: dict[str, str]
    profile_id: str
    organization_id: str
    user_id: str


@pytest.fixture(scope="session", autouse=True)
def database() -> None:
    with psycopg.connect(ADMIN_DSN, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(
                    sql.Identifier(TEST_DB_NAME)
                )
            )
            cur.execute(
                sql.SQL("CREATE DATABASE {}").format(sql.Identifier(TEST_DB_NAME))
            )
    env = os.environ.copy()
    env["PYTHONPATH"] = str(BACKEND_DIR)
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Migraciones fallaron:\n{result.stdout}\n{result.stderr}")
    storage = BACKEND_DIR / "generated_test"
    shutil.rmtree(storage, ignore_errors=True)
    yield
    shutil.rmtree(storage, ignore_errors=True)


def _truncate() -> None:
    from app.database import SessionLocal
    from sqlalchemy import text

    tables = (
        "audit_logs, refresh_sessions, reports, remediation_reviews, "
        "remediation_recommendations, finding_events, findings, hardening_checks, "
        "scheduled_audits, audit_runs, server_credentials, servers, "
        "audit_profile_controls, audit_profiles, api_tokens, user_roles, users, organizations"
    )
    with SessionLocal() as db:
        db.execute(text(f"TRUNCATE TABLE {tables} RESTART IDENTITY CASCADE"))
        db.commit()


@pytest.fixture(scope="function")
def api(database) -> ApiContext:
    from app.api.v1.auth import ip_login_limiter, login_limiter
    from app.api.v1.setup import setup_limiter
    from app.main import app

    _truncate()
    login_limiter._events.clear()
    ip_login_limiter._events.clear()
    setup_limiter._events.clear()

    with TestClient(app) as client:
        response = client.post(
            "/api/v1/setup/initialize",
            json={
                "organization_name": "Organización de Pruebas",
                "organization_slug": f"test-{uuid.uuid4().hex[:8]}",
                "admin_full_name": "Admin de Pruebas",
                "admin_email": ADMIN_EMAIL,
                "admin_password": ADMIN_PASSWORD,
            },
        )
        assert response.status_code == 201, response.text
        payload = response.json()
        token = payload["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        profiles = client.get("/api/v1/profiles", headers=headers)
        assert profiles.status_code == 200
        profile_id = profiles.json()[0]["id"]
        yield ApiContext(
            client=client,
            token=token,
            headers=headers,
            profile_id=profile_id,
            organization_id=payload["user"]["organization_id"],
            user_id=payload["user"]["id"],
        )


def create_simulated_server(
    api: ApiContext,
    *,
    name: str = "Servidor Simulado",
    authorized: bool = True,
) -> dict:
    response = api.client.post(
        "/api/v1/servers",
        headers=api.headers,
        json={
            "name": name,
            "hostname": f"{name.lower().replace(' ', '-')}.test",
            "ip_address": "10.20.30.40",
            "os_family": "ubuntu",
            "os_version": "22.04",
            "environment": "production",
            "connection_method": "simulated",
            "port": 22,
            "auth_method": "key",
            "default_profile_id": api.profile_id,
            "authorization_confirmed": authorized,
            "notes": "Servidor simulado de pruebas; no representa infraestructura real.",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
