"""Deterministic keyword classifier. NOT AI, and no longer used by the chat route.

Kept as a free, instant, reproducible baseline: tests use it to pin the expected
`IntentResult` shape, and it can be compared against the LLM extractor later. It is
deliberately naive. It is not a silent fallback: if the LLM fails, the API reports
the failure instead of guessing.
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
