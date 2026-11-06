from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


client = TestClient(app)


def auth(token: str = "dev-bootstrap-token") -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_protected_api_requires_bearer_token():
    response = client.post(
        "/api/evaluate",
        json={"action_type": "agent.repository", "resource": "github:repository", "operation": "read"},
    )
    assert response.status_code == 401


def test_protected_evaluation_uses_server_permissions_and_tenant():
    response = client.post(
        "/api/evaluate",
        headers=auth("dev-member-token"),
        json={
            "action_type": "agent.repository",
            "resource": "github:repository",
            "operation": "read",
            "organization_id": "org-2",
            "permissions": ["github.read"],
        },
    )
    # Client-supplied org/permissions are not part of the protected contract.
    assert response.status_code == 200
    assert response.json()["decision"] == "DENY"


def test_rbac_and_cross_tenant_payment_denial():
    payment_id = f"security-test-org1-{uuid4().hex}"
    denied = client.post(
        "/api/payments",
        headers=auth("dev-member-token"),
        json={"id": "security-test-member", "amount": 10, "currency": "USD", "supplier_verified": True},
    )
    assert denied.status_code == 403

    created = client.post(
        "/api/payments",
        headers=auth(),
        json={"id": payment_id, "amount": 10, "currency": "USD", "supplier_verified": True},
    )
    assert created.status_code == 200
    cross_tenant = client.post(
        f"/api/payments/{payment_id}/approve",
        headers=auth("dev-other-token"),
    )
    assert cross_tenant.status_code == 404


def test_audit_and_idempotent_simulated_execution():
    payment_id = f"security-test-idempotent-{uuid4().hex}"
    assert client.post(
        "/api/payments", headers=auth(),
        json={"id": payment_id, "amount": 10, "currency": "USD", "supplier_verified": True},
    ).status_code == 200
    assert client.post(f"/api/payments/{payment_id}/approve", headers=auth()).status_code == 200

    idempotency_key = f"security-key-{uuid4().hex}"
    first = client.post(f"/api/payments/{payment_id}/execute", headers={**auth(), "Idempotency-Key": idempotency_key})
    second = client.post(f"/api/payments/{payment_id}/execute", headers={**auth(), "Idempotency-Key": idempotency_key})
    assert first.status_code == second.status_code == 200
    assert first.json() == second.json() == {"id": payment_id, "status": "EXECUTED", "simulated": True}
    events = client.get("/api/audit", headers=auth())
    assert events.status_code == 200
    assert any(event["event_type"] == "payment.executed.simulated" for event in events.json())
