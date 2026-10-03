import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_chat_valid_message_is_received() -> None:
    response = client.post("/chat", json={"message": "Do you take Delta Dental?"})
    assert response.status_code == 200
    assert response.json() == {"message": "Do you take Delta Dental?", "status": "received"}


@pytest.mark.parametrize("message", ["", "   ", "\n\t "])
def test_chat_blank_message_is_rejected(message: str) -> None:
    response = client.post("/chat", json={"message": message})
    assert response.status_code == 422
