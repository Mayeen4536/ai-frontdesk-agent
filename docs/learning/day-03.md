# Day 3: FastAPI structure and structured output (revision notes)

Added a service layer, a Pydantic `IntentResult`, and a deterministic classifier behind `POST /chat`. No LLM.

## FastAPI routes
A route is a Python function bound to an HTTP method and path. `APIRouter` groups routes per file; `main.py` registers them with `include_router`. FastAPI reads the type hints to parse, validate and document.

## Decorators
`@router.post("/chat")` is a function that takes your function and registers it, returning it unchanged. It is how you attach "this handles POST /chat" without changing the function body. Same idea as `@field_validator` and `@classmethod`.

## GET vs POST
- GET: read, no body, safe to repeat and cache (`/health`).
- POST: submit data in a JSON body, may create or change something (`/chat`, `/lead`).

## Pydantic request models
`ChatRequest` declares the body shape. FastAPI builds it from JSON; failed rules never reach the function. Validators (`@field_validator`, `@model_validator`) add business rules such as "not blank" and "needs phone or email".

## Response models
`response_model=ChatResponse` (and the return annotation) fix the output contract, filter extra fields and drive the OpenAPI docs. Nested models (`classification: IntentResult`) compose contracts.

## HTTP status codes
200 OK success. 422 Unprocessable Entity: well-formed JSON that fails validation (FastAPI default). 404 not found, 401/403 auth, 500 server bug. Pick codes by what happened, not by habit.

## Thin routes
Route: parse, call service, return. Service: the logic. Benefits: testable without HTTP, replaceable (keywords now, LLM later), routes stay readable.

## Structured output
Return typed data (`intent: Literal[...]`, optional fields) rather than text. Callers and tests can rely on it. An LLM will later be forced to produce this same schema, and Pydantic will validate it; invalid output = failed proposal.

## Deterministic classification
Keyword regexes, same input always gives same output. Not AI, naive on purpose (booking beats question when both appear). Tests assert exact results. Probabilistic behaviour will need evals, not just unit tests.
