import pytest

from app.services.classifier import classify_message


@pytest.mark.parametrize(
    ("message", "intent"),
    [
        ("I'd like to book an appointment", "book_appointment"),
        ("Can I reschedule to Friday?", "book_appointment"),
        ("Do you accept Delta Dental insurance?", "business_question"),
        ("Where is parking?", "business_question"),
        ("hello there", "unknown"),
        ("", "unknown"),
    ],
)
def test_classify_message_intent(message: str, intent: str) -> None:
    assert classify_message(message).intent == intent


def test_booking_takes_priority_over_business_question() -> None:
    result = classify_message("Book a cleaning, do you take insurance?")
    assert result.intent == "book_appointment"
    assert result.reason == "cleaning"
