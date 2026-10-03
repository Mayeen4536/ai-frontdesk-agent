from typing import Any

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_lead_email_only_is_accepted() -> None:
    payload = {"name": "Ada", "email": "ada@example.com", "reason": "Cleaning"}
    response = client.post("/lead", json=payload)
    assert response.status_code == 200
    assert response.json() == {
        "name": "Ada",
        "phone": None,
        "email": "ada@example.com",
        "reason": "Cleaning",
        "status": "accepted",
    }


def test_lead_phone_only_is_accepted() -> None:
    payload = {"name": "Ada", "phone": "555-0100", "reason": "Cleaning"}
    response = client.post("/lead", json=payload)
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    assert body["phone"] == "555-0100"
    assert body["email"] is None
    assert body["status"] == "accepted"


def test_lead_missing_phone_and_email_is_rejected() -> None:
    response = client.post("/lead", json={"name": "Ada", "reason": "Cleaning"})
    assert response.status_code == 422


def test_lead_blank_phone_and_email_is_rejected() -> None:
    payload = {"name": "Ada", "phone": " ", "email": "", "reason": "Cleaning"}
    assert client.post("/lead", json=payload).status_code == 422


def test_lead_missing_name_is_rejected() -> None:
    payload = {"email": "ada@example.com", "reason": "Cleaning"}
    assert client.post("/lead", json=payload).status_code == 422


def test_lead_missing_reason_is_rejected() -> None:
    payload = {"name": "Ada", "email": "ada@example.com"}
    assert client.post("/lead", json=payload).status_code == 422
