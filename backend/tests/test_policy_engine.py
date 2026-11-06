import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def request(**overrides):
    payload = {
        "organization_id": "org-1",
        "actor_type": "agent",
        "actor_id": "agent-1",
        "action_type": "agent.repository",
        "resource": "github:repository",
        "operation": "read",
        "permissions": ["github.read"],
    }
    payload.update(overrides)
    return payload


def test_allows_authorized_agent_action():
    response = client.post("/evaluate", json=request())

    assert response.status_code == 200
    assert response.json()["decision"] == "ALLOW"


def test_denies_agent_without_permission():
    response = client.post("/evaluate", json=request(permissions=[]))

    assert response.status_code == 200
    assert response.json()["decision"] == "DENY"
    assert response.json()["risk_level"] == "HIGH"


def test_denies_destructive_agent_action_even_with_permission():
    response = client.post(
        "/evaluate",
        json=request(operation="delete", permissions=["github.delete"]),
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "DENY"
    assert response.json()["risk_level"] == "CRITICAL"


def test_requires_two_approvals_for_large_verified_payment():
    response = client.post(
        "/evaluate",
        json=request(
            action_type="finance.payment",
            resource="finance:payment",
            operation="execute",
            amount=5001,
            currency="zmw",
            supplier_verified=True,
            approvals=1,
        ),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["decision"] == "REQUIRE_APPROVAL"
    assert body["approval_count_required"] == 2


def test_denies_finance_action_without_positive_supplier_verification():
    response = client.post(
        "/evaluate",
        json=request(
            action_type="finance.payment",
            resource="finance:payment",
            operation="prepare",
            amount=10,
            supplier_verified=None,
        ),
    )

    assert response.status_code == 200
    assert response.json()["decision"] == "DENY"


@pytest.mark.parametrize(
    "field,value",
    [("amount", -1), ("approvals", -1), ("actor_type", "service"), ("operation", "")],
)
def test_rejects_invalid_input(field, value):
    response = client.post("/evaluate", json=request(**{field: value}))

    assert response.status_code == 422


def test_denies_inconsistent_approval_state():
    response = client.post("/evaluate", json=request(approvals=2, required_approvals=1))

    assert response.status_code == 200
    assert response.json()["decision"] == "DENY"
    assert response.json()["reason"] == "Approval state is inconsistent"
