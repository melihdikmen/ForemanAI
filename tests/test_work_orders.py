"""Tests for the work-order (human-in-the-loop) endpoints."""

from __future__ import annotations

from typing import Any

from fastapi.testclient import TestClient

from tests.conftest import FOREMAN_HEADERS, TECHNICIAN_HEADERS

# A realistic draft, shaped like the output of the draft_work_order tool.
SAMPLE_DRAFT: dict[str, Any] = {
    "machine_code": "PRES-3",
    "title": "Hidrolik yağ sızıntısı kontrolü",
    "description": "E-204 alarmı sonrası silindir altında yağ izi görüldü.",
    "proposed_actions": "LOTO uygula, conta ve hortum bağlantılarını kontrol et.",
    "priority": "high",
}


def test_submit_creates_pending_work_order(client: TestClient) -> None:
    """A submitted draft is stored as PENDING, attributed to the submitting user."""
    response = client.post("/work-orders", json=SAMPLE_DRAFT, headers=TECHNICIAN_HEADERS)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["created_by"] == TECHNICIAN_HEADERS["X-User"]
    assert body["machine_code"] == "PRES-3"
    assert body["reviewed_by"] is None


def test_submit_requires_identity(client: TestClient) -> None:
    """Without identity headers the request is rejected with 401."""
    response = client.post("/work-orders", json=SAMPLE_DRAFT)
    assert response.status_code == 401


def test_submit_unknown_machine_returns_404(client: TestClient) -> None:
    """A draft for a machine that does not exist is rejected."""
    bad_draft = {**SAMPLE_DRAFT, "machine_code": "NOPE-99"}
    response = client.post("/work-orders", json=bad_draft, headers=TECHNICIAN_HEADERS)
    assert response.status_code == 404


def test_list_filters_by_status(client: TestClient) -> None:
    """?status=pending returns the submitted order; ?status=approved does not."""
    created = client.post("/work-orders", json=SAMPLE_DRAFT, headers=TECHNICIAN_HEADERS)
    created_id = created.json()["id"]

    pending = client.get("/work-orders?status=pending", headers=TECHNICIAN_HEADERS).json()
    approved = client.get("/work-orders?status=approved", headers=TECHNICIAN_HEADERS).json()

    assert created_id in [order["id"] for order in pending]
    assert created_id not in [order["id"] for order in approved]


def submit_sample(client: TestClient) -> int:
    """Submit SAMPLE_DRAFT as a technician and return the new work order id."""
    response = client.post("/work-orders", json=SAMPLE_DRAFT, headers=TECHNICIAN_HEADERS)
    return response.json()["id"]


def test_foreman_can_approve(client: TestClient) -> None:
    """Approval moves PENDING -> APPROVED and records who approved it."""
    work_order_id = submit_sample(client)

    response = client.post(f"/work-orders/{work_order_id}/approve", headers=FOREMAN_HEADERS)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "approved"
    assert body["reviewed_by"] == FOREMAN_HEADERS["X-User"]
    assert body["reviewed_at"] is not None


def test_technician_cannot_approve(client: TestClient) -> None:
    """Done criterion: nobody but a foreman can approve; the order stays PENDING."""
    work_order_id = submit_sample(client)

    response = client.post(f"/work-orders/{work_order_id}/approve", headers=TECHNICIAN_HEADERS)

    assert response.status_code == 403
    pending = client.get("/work-orders?status=pending", headers=FOREMAN_HEADERS).json()
    assert work_order_id in [order["id"] for order in pending]


def test_approve_without_identity_returns_401(client: TestClient) -> None:
    """No identity headers -> 401 (not 403): we don't know who you are."""
    work_order_id = submit_sample(client)
    response = client.post(f"/work-orders/{work_order_id}/approve")
    assert response.status_code == 401


def test_foreman_can_reject_with_reason(client: TestClient) -> None:
    """Rejection stores the reason so the technician can see why."""
    work_order_id = submit_sample(client)

    response = client.post(
        f"/work-orders/{work_order_id}/reject",
        json={"reason": "Önce yağ seviyesini ölç, sonra tekrar gönder."},
        headers=FOREMAN_HEADERS,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"
    assert body["rejection_reason"].startswith("Önce yağ")


def test_reject_requires_reason(client: TestClient) -> None:
    """An empty/too-short reason is a validation error (422)."""
    work_order_id = submit_sample(client)
    response = client.post(
        f"/work-orders/{work_order_id}/reject", json={"reason": ""}, headers=FOREMAN_HEADERS
    )
    assert response.status_code == 422


def test_cannot_review_twice(client: TestClient) -> None:
    """Once decided, an order cannot be re-decided (approved then rejected) -> 409."""
    work_order_id = submit_sample(client)
    client.post(f"/work-orders/{work_order_id}/approve", headers=FOREMAN_HEADERS)

    response = client.post(
        f"/work-orders/{work_order_id}/reject",
        json={"reason": "fikrimi değiştirdim"},
        headers=FOREMAN_HEADERS,
    )

    assert response.status_code == 409


def test_review_unknown_work_order_returns_404(client: TestClient) -> None:
    """Reviewing an id that does not exist returns 404."""
    response = client.post("/work-orders/999999/approve", headers=FOREMAN_HEADERS)
    assert response.status_code == 404
