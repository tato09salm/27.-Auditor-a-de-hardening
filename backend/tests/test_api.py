from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import func, select, update
from sqlalchemy.exc import DBAPIError

from app.database import SessionLocal
from app.models import AuditLog, Finding, RemediationRecommendation, ScheduledAudit, User
from tests.conftest import ApiContext, create_simulated_server


def test_setup_login_and_rbac(api: ApiContext):
    assert api.client.get("/api/v1/servers").status_code == 401
    response = api.client.post(
        "/api/v1/users",
        headers=api.headers,
        json={
            "email": "observador@example.com",
            "full_name": "Observador de Pruebas",
            "password": "Observa!Seguro2026",
            "role_codes": ["observer"],
            "must_change_password": False,
        },
    )
    assert response.status_code == 201, response.text
    login = api.client.post(
        "/api/v1/auth/login",
        json={"email": "observador@example.com", "password": "Observa!Seguro2026"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert api.client.get("/api/v1/servers", headers=headers).status_code == 200
    create = api.client.post(
        "/api/v1/servers",
        headers=headers,
        json={
            "name": "No permitido",
            "hostname": "no.test",
            "ip_address": "10.0.0.9",
            "os_family": "ubuntu",
            "os_version": "22.04",
            "connection_method": "simulated",
            "authorization_confirmed": True,
        },
    )
    assert create.status_code == 403
    assert api.client.get("/api/v1/audit-logs", headers=headers).status_code == 403
    assert api.client.get("/api/v1/audit-logs", headers=api.headers).status_code == 200


def test_server_requires_explicit_authorization(api: ApiContext):
    server = create_simulated_server(api, name="Servidor No Autorizado", authorized=False)
    assert server["is_simulated"] is True
    run = api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": server["id"], "profile_id": api.profile_id},
    )
    assert run.status_code == 409
    test = api.client.post(
        f"/api/v1/servers/{server['id']}/test-connection", headers=api.headers
    )
    assert test.status_code == 409
    authorized = api.client.post(
        f"/api/v1/servers/{server['id']}/authorize",
        headers=api.headers,
        json={"confirmed": True, "allow_private_target": False},
    )
    assert authorized.status_code == 200
    tested = api.client.post(
        f"/api/v1/servers/{server['id']}/test-connection", headers=api.headers
    )
    assert tested.status_code == 200
    assert tested.json()["reachable"] is True
    assert tested.json()["simulated"] is True


def test_simulated_audit_score_findings_and_history(api: ApiContext):
    server = create_simulated_server(api, name="Servidor Riesgoso")
    response = api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": server["id"], "profile_id": api.profile_id},
    )
    assert response.status_code == 202, response.text
    run_id = response.json()["id"]
    detail = api.client.get(f"/api/v1/audits/{run_id}", headers=api.headers)
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["status"] == "completed"
    assert payload["score"] == 35.71
    assert payload["passed_count"] == 5
    assert payload["failed_count"] == 9
    assert payload["summary"]["coverage"] == 100.0

    findings = api.client.get("/api/v1/findings", headers=api.headers).json()
    assert findings["total"] == 9
    finding_id = findings["items"][0]["id"]
    detail_finding = api.client.get(f"/api/v1/findings/{finding_id}", headers=api.headers)
    assert detail_finding.status_code == 200
    assert detail_finding.json()["evidence"]

    second = api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": server["id"], "profile_id": api.profile_id},
    )
    assert second.status_code == 202, second.text
    second_detail = api.client.get(
        f"/api/v1/audits/{second.json()['id']}", headers=api.headers
    ).json()
    assert second_detail["status"] == "completed"
    findings_after = api.client.get("/api/v1/findings", headers=api.headers).json()
    assert findings_after["total"] == 9
    assert all(item["occurrence_count"] >= 2 for item in findings_after["items"])

    compliant = create_simulated_server(api, name="Servidor Compliant")
    good = api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": compliant["id"], "profile_id": api.profile_id},
    )
    assert good.status_code == 202, good.text
    good_detail = api.client.get(
        f"/api/v1/audits/{good.json()['id']}", headers=api.headers
    ).json()
    assert good_detail["score"] == 100.0
    dashboard = api.client.get("/api/v1/dashboard", headers=api.headers).json()
    assert dashboard["summary"]["audited_servers"] == 2
    assert dashboard["summary"]["average_score"] == 67.86


def test_ssh_loopback_is_blocked_and_run_fails_closed(api: ApiContext):
    fingerprint = "SHA256:" + "A" * 43
    response = api.client.post(
        "/api/v1/servers",
        headers=api.headers,
        json={
            "name": "Servidor Loopback",
            "hostname": "loopback.test",
            "ip_address": "127.0.0.1",
            "os_family": "ubuntu",
            "os_version": "22.04",
            "environment": "production",
            "connection_method": "ssh",
            "port": 22,
            "username": "auditor",
            "auth_method": "key",
            "host_key_fingerprint": fingerprint,
            "credential": {"secret": "-----BEGIN OPENSSH PRIVATE KEY-----\nfake\n-----END OPENSSH PRIVATE KEY-----"},
            "default_profile_id": api.profile_id,
            "authorization_confirmed": True,
        },
    )
    assert response.status_code == 201, response.text
    server_id = response.json()["id"]
    tested = api.client.post(
        f"/api/v1/servers/{server_id}/test-connection", headers=api.headers
    )
    assert tested.status_code == 200
    assert tested.json()["reachable"] is False
    assert "SSRF" in tested.json()["message"] or "bloqueado" in tested.json()["message"].lower()

    run = api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": server_id, "profile_id": api.profile_id},
    )
    assert run.status_code == 202, run.text
    detail = api.client.get(
        f"/api/v1/audits/{run.json()['id']}", headers=api.headers
    ).json()
    assert detail["status"] == "failed"
    assert detail["score"] is None
    assert detail["not_evaluated_count"] == 14


def test_finding_lifecycle_guard(api: ApiContext):
    server = create_simulated_server(api, name="Servidor Flujo")
    run = api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": server["id"], "profile_id": api.profile_id},
    )
    finding = api.client.get("/api/v1/findings", headers=api.headers).json()["items"][0]
    invalid = api.client.patch(
        f"/api/v1/findings/{finding['id']}",
        headers=api.headers,
        json={"status": "fixed_pending_validation", "comment": "sin plan"},
    )
    assert invalid.status_code == 409
    valid = api.client.patch(
        f"/api/v1/findings/{finding['id']}",
        headers=api.headers,
        json={"status": "in_review", "comment": "Revisión iniciada"},
    )
    assert valid.status_code == 200
    assert valid.json()["status"] == "in_review"


def test_audit_log_is_append_only(api: ApiContext):
    with SessionLocal() as db:
        log = db.scalar(select(AuditLog).limit(1))
        assert log is not None
        with pytest.raises(DBAPIError):
            db.execute(update(AuditLog).where(AuditLog.id == log.id).values(action="tampered"))
            db.commit()
        db.rollback()


def test_ai_unavailable_does_not_break_audit(api: ApiContext):
    server = create_simulated_server(api, name="Servidor IA Apagada")
    api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": server["id"], "profile_id": api.profile_id},
    )
    finding = api.client.get("/api/v1/findings", headers=api.headers).json()["items"][0]
    response = api.client.post(
        f"/api/v1/findings/{finding['id']}/recommendations", headers=api.headers
    )
    assert response.status_code == 503
    assert response.json()["code"] == "ai_unavailable"


def test_recommendation_detail_and_human_review(api: ApiContext):
    server = create_simulated_server(api, name="Servidor Recomendacion")
    run = api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": server["id"], "profile_id": api.profile_id},
    )
    assert run.status_code == 202, run.text
    finding = api.client.get("/api/v1/findings", headers=api.headers).json()["items"][0]
    payload = {
        "problem": "El acceso SSH de root está habilitado.",
        "risk": "Compromiso total del servidor.",
        "recommendation": "Deshabilitar el acceso directo y validar en una ventana controlada.",
        "commands": [
            {
                "command": "sudo sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config",
                "explanation": "Modifica la configuración efectiva.",
                "risk": "Puede bloquear el acceso.",
            }
        ],
        "impact": "Requiere una sesión de rescate.",
        "prerequisites": ["Sesión abierta"],
        "service_interruption_risk": "high",
        "validation": ["Reejecutar el control"],
        "rollback": ["Restaurar el respaldo"],
        "references": ["https://www.cisecurity.org/benchmark/ubuntu_linux"],
        "confidence": 0.8,
        "insufficient_information": False,
    }
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == "admin@example.com"))
        recommendation = RemediationRecommendation(
            organization_id=finding["organization_id"],
            finding_id=finding["id"],
            source="ai",
            provider="ollama",
            model="llama3.1:8b",
            status="pending_review",
            payload=payload,
            confidence=0.8,
            validation_status="warnings",
            validation_warnings=["Puede bloquear el acceso SSH."],
            flagged_commands=[
                {
                    "command": payload["commands"][0]["command"],
                    "pattern": "ssh-config-change",
                    "severity": "high",
                    "reason": "Puede bloquear el acceso SSH.",
                }
            ],
            created_by_id=admin.id,
        )
        db.add(recommendation)
        db.commit()
        recommendation_id = str(recommendation.id)

    detail = api.client.get(f"/api/v1/recommendations/{recommendation_id}", headers=api.headers)
    assert detail.status_code == 200, detail.text
    assert detail.json()["finding_title"] == finding["title"]
    assert detail.json()["server_name"] == "Servidor Recomendacion"

    # La aprobación solo documenta la revisión; no ejecuta comandos.
    review = api.client.post(
        f"/api/v1/recommendations/{recommendation_id}/review",
        headers=api.headers,
        json={
            "decision": "approved",
            "comments": "Revisado con ventana de cambio y plan de reversión aprobado.",
        },
    )
    assert review.status_code == 200, review.text
    assert review.json()["status"] == "approved"
    assert len(review.json()["reviews"]) == 1


def test_dangerous_recommendation_cannot_be_approved(api: ApiContext):
    server = create_simulated_server(api, name="Servidor Peligroso")
    api.client.post(
        "/api/v1/audits",
        headers=api.headers,
        json={"server_id": server["id"], "profile_id": api.profile_id},
    )
    finding = api.client.get("/api/v1/findings", headers=api.headers).json()["items"][0]
    payload = {
        "problem": "Prueba",
        "risk": "Prueba",
        "recommendation": "No aplicar",
        "commands": [{"command": "rm -rf /", "explanation": "Peligroso", "risk": "Crítico"}],
        "impact": "Destrucción",
        "prerequisites": [],
        "service_interruption_risk": "high",
        "validation": [],
        "rollback": [],
        "references": [],
        "confidence": 0.2,
        "insufficient_information": False,
    }
    with SessionLocal() as db:
        admin = db.scalar(select(User).where(User.email == "admin@example.com"))
        recommendation = RemediationRecommendation(
            organization_id=finding["organization_id"],
            finding_id=finding["id"],
            source="ai",
            provider="ollama",
            model="llama3.1:8b",
            status="pending_review",
            payload=payload,
            confidence=0.2,
            validation_status="dangerous",
            validation_warnings=["Comando destructivo."],
            flagged_commands=[{"command": "rm -rf /", "pattern": "rm", "severity": "critical", "reason": "Destrucción"}],
            created_by_id=admin.id,
        )
        db.add(recommendation)
        db.commit()
        recommendation_id = str(recommendation.id)
    review = api.client.post(
        f"/api/v1/recommendations/{recommendation_id}/review",
        headers=api.headers,
        json={"decision": "approved", "comments": "Intento de aprobación de comando destructivo."},
    )
    assert review.status_code == 422
    assert review.json()["code"] == "dangerous_commands"


def test_temporary_password_must_be_changed_before_api_access(api: ApiContext):
    created = api.client.post(
        "/api/v1/users",
        headers=api.headers,
        json={
            "email": "temporal@example.com",
            "full_name": "Usuario Temporal",
            "password": "Inicial!2026-Segura",
            "role_codes": ["analyst"],
            "must_change_password": True,
        },
    )
    assert created.status_code == 201, created.text
    login = api.client.post(
        "/api/v1/auth/login",
        json={"email": "temporal@example.com", "password": "Inicial!2026-Segura"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    blocked = api.client.get("/api/v1/findings", headers=headers)
    assert blocked.status_code == 403
    assert blocked.json()["code"] == "password_change_required"
    changed = api.client.post(
        "/api/v1/auth/change-password",
        headers=headers,
        json={
            "current_password": "Inicial!2026-Segura",
            "new_password": "Definitiva!2026-Segura",
        },
    )
    assert changed.status_code == 200, changed.text


def test_password_change_revokes_sessions(api: ApiContext):
    response = api.client.post(
        "/api/v1/auth/change-password",
        headers=api.headers,
        json={
            "current_password": "Auditoria!2026-Segura",
            "new_password": "Nueva!Auditoria2026",
        },
    )
    assert response.status_code == 200, response.text
    assert api.client.get("/api/v1/servers", headers=api.headers).status_code == 401
    login = api.client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "Nueva!Auditoria2026"},
    )
    assert login.status_code == 200
