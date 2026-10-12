# Day 2: Python and FastAPI revision notes

Built the first FastAPI skeleton: `GET /health`, `POST /chat`, `POST /lead`.

## Python type hints

Annotations such as `def f(x: int) -> str` and `name: str | None`. Python does not enforce them at runtime. Editors, type checkers and, importantly, Pydantic and FastAPI read them. `str | None` means "a string or nothing"; `dict[str, str]` is a dict with string keys and values.

## Dicts and lists

- `list`: ordered, indexed by position: `["a", "b"]`.
- `dict`: key to value lookup: `{"status": "ok"}`.
- JSON maps directly onto these: JSON object = dict, JSON array = list, `null` = `None`.
- `model.model_dump()` turns a Pydantic model into a plain dict.

## Functions

Take inputs, return a result. Keep them small and single-purpose. Default values (`phone: str | None = None`) make a parameter optional. Prefer returning values over mutating things.

## Classes

A class bundles data and behavior. A Pydantic model is a class whose attributes are the validated fields. Subclassing reuses a contract: `LeadResponse(LeadRequest)` is a lead plus a `status` field. `@classmethod` and decorators like `@field_validator` attach behavior to the class.

## Exceptions

Signal "this cannot proceed". `raise ValueError("...")` stops normal flow; a caller can `try/except` it. Inside a Pydantic validator, raising `ValueError` is how you reject input: Pydantic collects it, and FastAPI turns it into an HTTP 422 response. Do not swallow exceptions silently.

## async / await

`async def` defines a coroutine; `await` pauses it while waiting so the event loop can run other work. One thread can juggle many waiting requests. Our routes are plain `def` today because they do no waiting; FastAPI runs those in a thread pool. Use `async def` once a route awaits something (HTTP call to an LLM, async DB driver).

## I/O-bound vs CPU-bound

- **I/O-bound**: time is spent waiting (network, disk, database, LLM call). `async` helps a lot.
- **CPU-bound**: time is spent computing (parsing huge files, embedding math). `async` does not help; use processes or worker queues.
- Most of this app will be I/O-bound (LLM and database calls).

## Pydantic

Declares data shape with type hints and validates on construction. Wrong type or failed rule gives a clear error instead of bad data flowing deeper. Used here for:

- `field_validator`: rule for one field (message is not blank).
- `model_validator`: rule across fields (phone or email must be present).
- Normalizing input (trimmed names, blank phone becomes `None`).

## FastAPI

Builds the HTTP API from plain functions plus type hints.

- `APIRouter` groups routes; `app.include_router(...)` registers them.
- A parameter typed as a Pydantic model becomes the JSON request body.
- The return type documents and filters the response.
- Invalid input returns 422 automatically, before the route runs.
- `/docs` serves interactive API docs for free.

## API contracts

The agreed shape of requests and responses: field names, types, rules, status codes. Clients depend on it, so changes must be deliberate. In code the contract lives in `app/schemas`, in one place, shared by the route and the tests.

## Why routes stay thin

A route should only translate HTTP to a function call and back. Validation lives in schemas; later, logic lives in the orchestrator and tools. Reasons: logic is testable without HTTP, reusable from other callers (a future MCP server, a CLI), and the architecture rule "API handles requests, orchestrator decides" stays intact.

## Day 2 Quick Recall

1. Do type hints change runtime behavior in plain Python? No. Pydantic and FastAPI read them and act on them.
2. What status code does FastAPI return for a body that fails validation? 422.
3. How do you reject input inside a Pydantic validator? Raise `ValueError`.
4. `field_validator` vs `model_validator`? One field vs the whole model (cross-field rules).
5. When is `async` worth it? I/O-bound work: LLM, database, network. Not CPU-bound work.
6. Why `def` (not `async def`) for today's routes? They never await anything.
7. What does "thin route" mean here? Parse, call, return. No business rules inside.
8. Where do request and response contracts live? `backend/app/schemas`.
9. How do you run the app? `uvicorn app.main:app --reload` from `backend/`.
10. How do you run the tests? `pytest` from `backend/`.
