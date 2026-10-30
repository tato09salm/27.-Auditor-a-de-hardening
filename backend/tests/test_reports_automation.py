from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from app.database import SessionLocal
from app.models import AuditRun, ScheduledAudit
from tests.conftest import ApiContext, create_simulated_server


def _completed_run(api: ApiContext, server_id: str) -> dict:
    response = api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": server_id, "profile_id": api.profile_id},
    )
    assert response.status_code == 202, response.text
    detail = api.client.get(
        f"/api/v1/audits/{response.json()['id']}", headers=api.headers
    )
    assert detail.status_code == 200
    assert detail.json()["status"] == "completed"
    return detail.json()


def test_three_report_formats_and_executive(api: ApiContext):
    server = create_simulated_server(api, name="Servidor Reportes")
    run = _completed_run(api, server["id"])
    signatures = {"pdf": b"%PDF", "docx": b"PK\x03\x04", "xlsx": b"PK\x03\x04"}
    for fmt, signature in signatures.items():
        response = api.client.post(
            "/api/v1/reports",
            headers=api.headers,
            json={
                "report_type": "technical",
                "format": fmt,
                "audit_run_id": run["id"],
            },
        )
        assert response.status_code == 201, response.text
        assert response.json()["file_name"].startswith("simulado_")
        download = api.client.get(
            f"/api/v1/reports/{response.json()['id']}/download", headers=api.headers
        )
        assert download.status_code == 200
        assert download.content.startswith(signature)
        assert len(download.content) > 1000
    executive = api.client.post(
        "/api/v1/reports",
        headers=api.headers,
        json={"report_type": "executive", "format": "xlsx"},
    )
    assert executive.status_code == 201, executive.text
    assert api.client.get(
        f"/api/v1/reports/{executive.json()['id']}/download", headers=api.headers
    ).status_code == 200
    # El reporte técnico no debe filtrar credenciales.
    assert b"BEGIN OPENSSH" not in api.client.get(
        f"/api/v1/reports/{executive.json()['id']}/download", headers=api.headers
    ).content


def test_automation_api_key_runs_due_schedule(api: ApiContext):
    server = create_simulated_server(api, name="Servidor Programado")
    token_response = api.client.post(
        "/api/v1/settings/api-tokens",
        headers=api.headers,
        json={
            "name": "n8n pruebas",
            "scopes": ["automation:execute"],
            "expires_in_days": 30,
        },
    )
    assert token_response.status_code == 201, token_response.text
    api_key = token_response.json()["token"]
    schedule = api.client.post(
        "/api/v1/schedules",
        headers=api.headers,
        json={
            "name": "Auditoría nocturna",
            "server_id": server["id"],
            "profile_id": api.profile_id,
            "cron_expression": "0 3 * * *",
            "timezone": "America/Lima",
            "is_enabled": True,
        },
    )
    assert schedule.status_code == 201, schedule.text
    with SessionLocal() as db:
        db.execute(
            update(ScheduledAudit)
            .where(ScheduledAudit.id == schedule.json()["id"])
            .values(next_run_at=datetime.now(timezone.utc) - timedelta(minutes=1))
        )
        db.commit()
    run_due = api.client.post(
        "/api/v1/automation/audits/run-due",
        headers={"X-API-Key": api_key},
    )
    assert run_due.status_code == 200, run_due.text
    assert run_due.json()["runs_started"] == 1
    with SessionLocal() as db:
        run = db.scalar(
            select(AuditRun).where(AuditRun.scheduled_audit_id == schedule.json()["id"])
        )
        assert run is not None
        assert run.trigger_type.value == "schedule"
        schedule_db = db.get(ScheduledAudit, schedule.json()["id"])
        assert schedule_db.next_run_at is not None
    # Repetir no debe duplicar mientras no venza el siguiente intervalo.
    repeat = api.client.post(
        "/api/v1/automation/audits/run-due",
        headers={"X-API-Key": api_key},
    )
    assert repeat.status_code == 200
    assert repeat.json()["runs_started"] == 0
