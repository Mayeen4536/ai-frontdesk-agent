import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_valid_message_is_received() -> None:
    response = client.post("/chat", json={"message": "Do you take Delta Dental?"})
    assert response.status_code == 200
    body = response.json()
    assert body["message"] == "Do you take Delta Dental?"
    assert body["status"] == "received"
    assert body["classification"]["intent"] == "business_question"


@pytest.mark.parametrize("message", ["", "   ", "\n\t "])
def test_chat_blank_message_is_rejected(message: str) -> None:
    response = client.post("/chat", json={"message": message})
    assert response.status_code == 422


def test_chat_appointment_message_is_classified_with_details() -> None:
    message = "Please book a cleaning next week, mornings if possible"
    response = client.post("/chat", json={"message": message})
    assert response.status_code == 200
    assert response.json()["classification"] == {
        "intent": "book_appointment",
        "reason": "cleaning",
        "requested_date": "next week",
        "time_preference": "morning",
    }


def test_chat_business_question_is_classified() -> None:
    response = client.post("/chat", json={"message": "What are your opening hours?"})
    assert response.status_code == 200
    assert response.json()["classification"] == {
        "intent": "business_question",
        "reason": None,
        "requested_date": None,
        "time_preference": None,
    }


def test_chat_unknown_message_is_classified_unknown() -> None:
    response = client.post("/chat", json={"message": "asdf qwerty"})
    assert response.status_code == 200
    assert response.json()["classification"]["intent"] == "unknown"


def test_chat_missing_message_field_is_rejected() -> None:
    assert client.post("/chat", json={}).status_code == 422
