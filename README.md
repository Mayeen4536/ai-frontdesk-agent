# AI Frontdesk Agent

A multi-tenant AI front-office employee for appointment-based service businesses. The first vertical is dental clinics.

**Status: Phase 1 in progress.** A typed FastAPI backend exists (`/health`, `/chat`, `/lead`) with a service layer and a temporary deterministic message classifier returning structured output. There is no LLM, database or authentication yet. See the design documents for the full plan.

---

## 1. Product problem

Small appointment-based businesses lose revenue at the front desk, mostly in ways nobody measures:

- Calls and messages arrive when staff are busy with patients or the office is closed. Many go unanswered.
- The same questions repeat all day: hours, insurance, pricing, parking, what to do before a procedure.
- Booking, rescheduling and cancelling is manual and error-prone, and it competes with in-person work.
- New leads (a prospective patient asking about a service) are not captured, or are captured inconsistently.
- Hiring dedicated front-desk coverage for every hour of demand is expensive.

Generic chatbots do not fix this. They answer from guesswork, cannot act on the clinic's real schedule, and have no safe path to a human when a conversation needs one.

## 2. Product vision

An AI employee that handles the routine front-office workload end to end, and knows when to hand off to a person.

- It answers questions using the clinic's own approved information, not general knowledge.
- It performs real actions (check availability, book, reschedule, capture a lead) through controlled tools, not free-text promises.
- It escalates to staff whenever it is unsure, the topic is sensitive, or the user asks.
- It is multi-tenant from the start: many businesses, each with isolated data, knowledge and configuration, on one platform.
- It is measurable. Every behavior is covered by automated evaluations so quality can be tracked and regressions caught.

## 3. Initial use case

**Dental clinic front desk, via a web chat widget.**

A patient visits the clinic's site and asks things like:

- "Do you take Delta Dental?"
- "I need a cleaning next week, mornings if possible."
- "Can I move my appointment to Friday?"
- "I have a toothache and it is getting worse."

The agent answers from the clinic's knowledge base, books through the scheduling tool, records interested prospects as leads, and routes anything urgent, clinical or uncertain to a human.

The agent does not give medical advice or diagnoses. This boundary is part of the design, not an afterthought.

## 4. High-level architecture

```
User
 -> Web / Chat UI
 -> FastAPI
 -> AI Orchestrator
      |-- Knowledge / RAG
      |-- Appointment Tool
      |-- Lead Tool
      |-- Human Escalation

Persistent data
 - PostgreSQL
 - pgvector (where semantic retrieval is required)
```

The orchestrator is the only component that talks to the LLM. Everything it can do to the outside world goes through an explicit, typed tool. Full detail is in [docs/architecture.md](docs/architecture.md).

**Engineering principles** (detailed in the architecture document):

1. Use deterministic software for deterministic problems and AI only where probabilistic reasoning or language understanding adds value.
2. The LLM proposes actions, but application logic validates them.
3. Authorization determines whether an action is permitted.
4. Tools execute approved actions.
5. Audit logs record important actions.
6. Dynamic transactional state such as appointment availability comes from live databases or APIs, not from RAG.
7. RAG primarily provides relevant business knowledge such as services, policies, business hours, FAQs, and other relatively stable information.

Availability checks, validation, authorization, tenant isolation and database writes are ordinary code. The model is used for understanding what the user wants and for phrasing responses.

## 5. Planned capabilities

Only the FastAPI foundation and a deterministic structured-output demo exist so far; everything below is still to build. Listed roughly in delivery order.

- Chat endpoint with conversation state
- Tenant-scoped knowledge base with retrieval-augmented answers (RAG) for stable business information
- Structured outputs: typed, validated model responses for intents, tool arguments and escalation signals
- Appointment tool: check availability, book, reschedule, cancel (reads live data, never RAG)
- Authorization checks before every action
- Audit log of important actions
- Lead capture tool
- Human escalation with context handoff
- Evaluation suite for answer quality, tool use correctness and safety behavior
- Admin surface for managing knowledge and reviewing conversations
- Additional channels (voice, SMS) and additional verticals
- MCP server exposure of tools

## 6. Technology

### Implemented today

| Area | Technology | Where it is used |
|---|---|---|
| Language | Python 3.11+ | Whole backend, fully type-hinted |
| API framework | FastAPI | `GET /health`, `POST /chat`, `POST /lead`, auto-generated OpenAPI and Swagger UI |
| Validation and schemas | Pydantic v2 | Request models, explicit response models, custom validators |
| Testing | pytest, FastAPI `TestClient` | Deterministic endpoint and service tests in `backend/tests` |
| Architecture | Thin routes and a service layer | Routes delegate to `app/services`; no logic in the HTTP layer |

### Planned (not implemented)

Chosen to stay small. Nothing is added until a feature needs it. None of the items below exist in the codebase yet.

| Area | Choice |
|---|---|
| Language | Python |
| API | FastAPI |
| Database | PostgreSQL |
| Vector search | pgvector (inside PostgreSQL, no separate vector store) |
| LLM integration | Direct provider SDK calls behind a thin internal interface |
| Orchestration | Plain Python first; a framework only if a real need appears |
| Structured outputs | Pydantic schemas validating all model output the app acts on |
| Tool calling | Provider-native tool calling with typed schemas |
| Testing | pytest |
| Evaluations | Custom eval harness in `backend/evals`, run in CI |
| Containers | Docker |
| CI | GitHub Actions |
| Frontend (later) | React / Next.js |
| MCP (later) | MCP server exposing the same tools |

## 7. AI reliability philosophy

1. **Deterministic first.** If a problem has a correct answer computable by code, use code. The model never decides what slots are free, who a user is, or what a tenant may access.
2. **The model proposes, software disposes.** Proposals arrive as structured output and are validated against schemas and business rules before anything executes. Invalid output is a failed proposal, not something to guess at.
3. **Ground answers in the right source.** Stable business facts come from retrieved tenant content. Live state such as availability comes from the database. If neither has the answer, the agent says so and offers a human instead of guessing.
4. **Fail toward a human.** Low confidence, out-of-scope requests, clinical questions and errors all route to escalation.
5. **Evaluate, do not eyeball.** Behavior is defined by test cases. Prompt, model or retrieval changes must pass the eval suite before merge.
6. **Observable by default.** Every conversation records the prompts, retrieved context, proposals and outcomes needed to debug a bad answer.
7. **Small blast radius.** Tools do one thing, with narrow inputs and explicit permissions.

## 8. Security principles

- **Tenant isolation is enforced in code and data**, not by prompt. Every query is tenant-scoped, and the tenant is derived from authenticated context, never from model output.
- **Authorization is application logic, not model judgment.** Whether an action is permitted is decided from authenticated identity and tenant, before any tool runs.
- **Least privilege for tools.** Each tool receives only the access it needs.
- **Treat all model input and output as untrusted.** User text, retrieved documents and model responses are validated. Prompt injection is assumed, so the design limits what a manipulated model could do.
- **No secrets in the repo.** Configuration comes from environment variables; `.env` files are git-ignored.
- **Minimize and protect personal data.** Dental interactions may involve health-adjacent information. Collect only what is needed, keep it out of logs where possible, and plan for retention and deletion from the start. Compliance requirements (for example HIPAA in the US) must be assessed before handling real patient data.
- **Auditability.** Important actions, including refused ones, are recorded in an audit log.

## 9. Development roadmap

| Phase | Goal | Status |
|---|---|---|
| 0. Architecture | Repo structure, README, architecture document | Done |
| 1. Foundation | FastAPI skeleton, config, PostgreSQL via Docker, health check, pytest, CI | **In progress** (FastAPI, Pydantic contracts, service layer, structured intent output and pytest done) |
| 2. Data model | Tenants, appointments, leads, conversations, audit log, migrations | Planned |
| 3. Orchestrator v1 | LLM call, structured outputs, conversation state, tool-calling loop | Planned |
| 4. Tools | Appointment tool, lead tool, human escalation | Planned |
| 5. RAG | Document ingestion, pgvector retrieval, grounded answers | Planned |
| 6. Evaluations | Eval harness, baseline datasets, CI gating | Planned |
| 7. Frontend | Chat UI, then admin UI (Next.js) | Planned |
| 8. MCP | Expose tools through an MCP server | Planned |
| 9. Hardening | Observability, auth, rate limits, compliance review | Planned |

## 10. Current project status

**Phase 1 (Foundation) in progress.**

- Repository structure defined
- README and architecture document written, including the seven engineering principles
- Learning journal started in `docs/learning` (written by the learner, not generated)
- FastAPI app with `GET /health`, `POST /chat` and `POST /lead` (validates only, no storage)
- `POST /chat` validates the request, classifies the message through a service and returns structured output
- Classification is **temporary deterministic keyword logic, not AI**. It exists to establish the architecture and the output contract that an LLM-backed classifier will later fulfil
- pytest suite (22 tests) covering endpoints and the classifier
- No LLM, database, Docker setup, CI or authentication yet

### API at a glance

| Endpoint | Purpose | Success | Invalid input |
|---|---|---|---|
| `GET /health` | Liveness check | 200 `{"status": "ok"}` | n/a |
| `POST /chat` | Validate a message, return it with a structured intent | 200 `ChatResponse` | 422 (empty or whitespace message) |
| `POST /lead` | Validate a prospective-patient lead (no storage yet) | 200 `LeadResponse` | 422 (missing name/reason, or no phone and no email) |

Example `POST /chat`:

```json
// request
{"message": "Please book a cleaning tomorrow afternoon"}

// response
{
  "message": "Please book a cleaning tomorrow afternoon",
  "status": "received",
  "classification": {
    "intent": "book_appointment",
    "reason": "cleaning",
    "requested_date": "tomorrow",
    "time_preference": "afternoon"
  }
}
```

### Engineering concepts demonstrated

- **HTTP API design**: correct verbs (GET for reads, POST for submissions), meaningful status codes (200 and 422), a consistent JSON contract.
- **API contracts**: explicit request and response models on every route (`response_model`), so the OpenAPI schema at `/docs` is the contract and cannot silently drift from the code.
- **Structured data validation**: Pydantic models reject malformed input at the boundary (blank messages, missing lead fields, leads with no contact method) before any logic runs.
- **Structured output**: the classifier returns a typed `IntentResult` (`intent` constrained to a fixed set of values, plus optional `reason`, `requested_date`, `time_preference`) instead of free text. This is the same shape an LLM will be required to produce later, validated the same way.
- **Thin routes, service layer**: routes handle HTTP only; classification lives in `app/services/classifier.py` behind a single function, so the implementation can change without touching the route or the contract.
- **Deterministic testing**: unit tests for the service and API tests through `TestClient`, all repeatable with no network or model calls.
- **Honest scoping**: placeholder logic is labelled as such in code and docs, and no capability is claimed before it exists.

### Running the backend

```
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows; use source .venv/bin/activate elsewhere
pip install -e ".[dev]"
uvicorn app.main:app --reload   # http://localhost:8000/docs
pytest
```

## Repository layout

```
backend/
  app/
    main.py         FastAPI app factory
    api/            HTTP layer (thin FastAPI routes)
    services/       Business logic (temporary deterministic classifier)
    auth/           Authentication and authorization
    orchestrator/   LLM interaction and agent loop
    tools/          Appointment, lead and escalation tools
    rag/            Ingestion and retrieval
    schemas/        Pydantic request, response and structured-output models
    db/             Models, sessions, migrations
    core/           Config, logging, shared utilities
  pyproject.toml    Python project and dependencies
  tests/            pytest suite (deterministic)
  evals/            AI evaluation suite (probabilistic behavior)
frontend/           React / Next.js app (later)
docs/
  architecture.md   Architecture and engineering principles
  learning/         Daily learning notes
.github/workflows/  GitHub Actions (later)
```

Empty directories hold a `.gitkeep` file so Git tracks them. Remove it when real files are added.
