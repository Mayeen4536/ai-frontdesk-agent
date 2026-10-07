"""Temporary deterministic message classifier.

This is NOT AI. It is plain keyword matching that exists only to demonstrate
the architecture: route -> service -> typed result. It is deliberately naive
and will be replaced or complemented by an LLM-backed classifier. Callers
depend only on `classify_message` and `IntentResult`, so that swap should not
change the route or the API contract.
"""

import re

from app.schemas.intent import IntentResult

_BOOKING_PATTERN = re.compile(
    r"\b(book|booking|schedule|appointment|reschedule)\b|\bsee (a|the) (dentist|doctor|hygienist)\b",
    re.IGNORECASE,
)
_QUESTION_PATTERN = re.compile(
    r"\b(hours?|open|close[sd]?|insurance|price|prices|pricing|cost|parking|address|location|accept|take)\b",
    re.IGNORECASE,
)
_REASON_PATTERN = re.compile(
    r"\b(cleaning|checkup|check-up|exam|whitening|filling|consultation|x-?rays?|root canal)\b",
    re.IGNORECASE,
)
_DATE_PATTERN = re.compile(
    r"\b(today|tomorrow|next week|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b",
    re.IGNORECASE,
)
_TIME_PATTERN = re.compile(r"\b(morning|afternoon|evening)s?\b", re.IGNORECASE)


def _first_match(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0).lower() if match else None


def classify_message(message: str) -> IntentResult:
    """Classify a message by keyword. Booking wins over business questions."""
    if _BOOKING_PATTERN.search(message):
        time_match = _TIME_PATTERN.search(message)
        return IntentResult(
            intent="book_appointment",
            reason=_first_match(_REASON_PATTERN, message),
            requested_date=_first_match(_DATE_PATTERN, message),
            time_preference=time_match.group(1).lower() if time_match else None,
        )
    if _QUESTION_PATTERN.search(message):
        return IntentResult(intent="business_question")
    return IntentResult(intent="unknown")
