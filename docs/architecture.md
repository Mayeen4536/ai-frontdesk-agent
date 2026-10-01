# Architecture

Status: initial design, pre-implementation. This document describes intent and will change as the system is built. Significant changes should be recorded here with the reason.

## 1. Engineering principles

These seven principles decide where every piece of logic lives. They take precedence over convenience.

### 1.1 Deterministic first

> Use deterministic software for deterministic problems and AI only where probabilistic reasoning or language understanding adds value.

| Problem | Approach | Why |
|---|---|---|
| Is this time slot free? | Deterministic code and SQL | There is one correct answer. |
| Is this user allowed to see this record? | Deterministic code | Security cannot be probabilistic. |
| Does this booking request satisfy business rules? | Deterministic validation | Rules are explicit and testable. |
| Which tenant does this request belong to? | Authenticated context | Never inferred by the model. |
| What does the user want ("move my cleaning to Friday")? | LLM | Free-form language understanding. |
| Which stored passages answer the question? | Embeddings plus retrieval | Semantic similarity is probabilistic. |
| How should the answer be phrased, and in what tone? | LLM | Language generation. |
| Should a human take over? | Rules first, LLM signal as one input | Safety-relevant, so rules have the final say. |

When in doubt, start with code. Move a decision to the model only when code cannot reasonably express it.

### 1.2 The LLM proposes, application logic validates

The model never acts. It produces a proposal, such as "book a cleaning on Friday at 9:00". The proposal is expressed as structured output (a typed schema), then parsed and validated by application code: schema validity, business rules, parameter ranges, and current system state. An invalid or implausible proposal is rejected or sent back to the model with the error. Free text from the model is never executed or interpreted as a command.

### 1.3 Authorization determines whether an action is permitted

Whether an action is allowed is a property of who is asking and which tenant they belong to. It is decided by an authorization layer using authenticated context. Nothing the model says, and nothing a user types in chat, can grant permission. A well-formed, valid proposal can still be refused.

### 1.4 Tools execute approved actions

Tools are the only code that changes state or reads live data on the model's behalf. A tool runs only after the proposal has been validated (1.2) and authorized (1.3). Tools have typed inputs and outputs, narrow scope, and receive tenant context from the system, not from the model.

### 1.5 Audit logs record important actions

Important actions are written to an audit log: who or what requested the action, the tenant, the proposal, the validation and authorization outcome, and the result. This covers executed actions and refused ones. The audit log is append-only from the application's point of view and is separate from debug traces.

### 1.6 Live state comes from live sources, not from RAG

Dynamic transactional state, such as appointment availability, existing bookings, and whether a slot is still open, must come from the live database or an API at the moment of the request. It must never be answered from RAG. Embedded documents are snapshots. They go stale, and a retrieved "Friday 9:00 is open" is a bug waiting to happen.

### 1.7 RAG provides stable business knowledge

RAG is for relatively stable, text-based business knowledge: services offered, policies, business hours, insurance information, FAQs, and pre- and post-visit instructions. It answers "what does the clinic say about X". It does not answer "what is true right now".

### How the principles combine

For "Can I get a cleaning Friday morning?":

1. The LLM interprets intent and proposes an availability check (1.1, 1.2).
2. Application logic validates the arguments (1.2) and authorization confirms the caller may do this for this tenant (1.3).
3. The Appointment Tool queries live availability from the database (1.4, 1.6).
4. The LLM phrases the result. If the user asks "how long does a cleaning take?", that comes from RAG (1.7).
5. If the user confirms, the booking goes through the same propose, validate, authorize, execute path, and the outcome is audit-logged (1.5).

## 2. System overview

```
User
 -> Web / Chat UI
 -> FastAPI
 -> AI Orchestrator
      |-- Knowledge / RAG
      |-- Appointment Tool
      |-- Lead Tool
      |-- Human Escalation

Persistent storage
 - PostgreSQL
 - pgvector (where semantic retrieval is needed)
```

## 3. Components

### 3.1 Web / Chat UI

The user-facing chat interface, embedded in a clinic's website. It sends messages to the API and renders replies. It holds no business logic. Built later with React / Next.js; until then the API is exercised through tests and simple HTTP clients.

### 3.2 FastAPI (API layer)

Responsibilities:

- Authenticate the request and resolve the tenant.
- Validate and parse input (schemas).
- Hand the message and conversation context to the orchestrator.
- Return the response.

The API layer contains no LLM logic and no business rules beyond request handling. Keeping it thin means the orchestrator and tools can be tested without HTTP.

### 3.3 AI Orchestrator

The core of the system and the only component that calls the LLM.

Responsibilities:

- Build the prompt from system instructions, conversation history and tenant configuration.
- Call the LLM with the set of tools it may use and, where a typed result is needed, a structured output schema.
- Run the tool-calling loop: the model proposes a tool call, the orchestrator validates it, checks authorization, runs the tool, and returns the result to the model.
- Enforce limits (maximum tool-call iterations, timeouts, token budgets).
- Decide, using rules plus model signals, when to escalate.
- Record a trace of each turn (prompt, retrieved context, proposals, outcomes).

Written as plain Python initially. An agent framework will only be introduced if a concrete need appears that plain code handles poorly. The model provider is accessed through a thin internal interface so it can be swapped and so tests can substitute a fake.

### 3.4 Structured outputs

Wherever the application needs to act on model output, the model is asked to return data conforming to a typed schema (for example a Pydantic model) rather than free text. Tool-call arguments, intent classification and escalation signals are all structured. Output that fails schema validation is treated as a failed proposal: retried with the error, or escalated. Schemas live in `backend/app/schemas` and are shared between the orchestrator and tools so there is one definition of each contract.

### 3.5 Tools

Every capability that touches the outside world is a tool (see 1.4).

**Knowledge / RAG**
Retrieves tenant-specific stable knowledge (see 1.7) relevant to a question. Uses pgvector for semantic search, scoped to the tenant. Answers are grounded in retrieved passages. If nothing relevant is found, the agent says so and offers a human.

**Appointment Tool**
Operations: check availability, book, reschedule, cancel. Availability and validation are deterministic and read live from the database (see 1.6). The model supplies intent and parameters (for example a date range and service type); the tool decides what is actually possible. Bookings are transactional and idempotent where feasible. State-changing operations are audit-logged.

**Lead Tool**
Captures prospective-patient details (name, contact, service of interest) for the clinic to follow up. Input is validated and only needed fields are collected.

**Human Escalation**
Flags the conversation for staff with a summary and reason, and tells the user what happens next. Triggers include: explicit user request, clinical or urgent symptoms, repeated failure to resolve, low-confidence retrieval, tool errors, and out-of-scope topics.

### 3.6 Authorization and audit

**Authorization** (`backend/app/auth`) answers "is this principal allowed to perform this action on this tenant's data". It runs before every tool execution and is independent of the model.

**Audit logging** records important actions (see 1.5) to a dedicated PostgreSQL table. Where exactly the audit writer lives (`auth` versus `db`) is deferred until the data model phase.

### 3.7 Persistent storage

**PostgreSQL** is the system of record: tenants, contacts, appointments, leads, conversations and messages, knowledge documents, audit logs and agent traces.

**pgvector** stores embeddings in PostgreSQL for the knowledge base, used only where semantic retrieval is needed. Keeping vectors in the same database avoids a second system, allows tenant filtering with ordinary SQL, and keeps transactions simple. A dedicated vector store is only worth considering if scale demands it.

## 4. Request flow

1. The user sends a message from the chat UI.
2. FastAPI authenticates, resolves the tenant, and validates the payload.
3. The orchestrator loads conversation history and tenant configuration.
4. The orchestrator calls the LLM with the available tools and output schemas.
5. If the model proposes a tool call: the orchestrator validates the arguments (schema and business rules), authorization checks permission, the tool executes with tenant context supplied by the system, and the result goes back to the model. This repeats up to a fixed limit.
6. Important actions, including refused ones, are written to the audit log.
7. The model produces a final reply, or the orchestrator triggers escalation.
8. The turn is persisted with its trace, and the reply is returned to the UI.

## 5. Multi-tenancy

- Every tenant-owned table carries a tenant identifier.
- All queries are scoped by tenant. The tenant comes from authenticated request context and is passed to tools by the system, never by the model.
- Knowledge embeddings are filtered by tenant at query time.
- Row-level security in PostgreSQL is a candidate for defense in depth and will be evaluated in the data model phase.
- Per-tenant configuration (business hours, services, tone, escalation contacts) is data, not code.

## 6. Reliability and evaluation

Two test layers with different purposes:

- **`backend/tests` (pytest, deterministic):** unit and integration tests for the API, tools, availability logic, validation, authorization, tenant isolation and database behavior. They must pass reliably and run on every commit. The LLM is replaced by a fake.
- **`backend/evals` (AI evaluations, probabilistic):** scenario-based evaluations that run real model calls and measure behavior: grounded answers, correct tool selection and arguments, valid structured output, refusal of out-of-scope requests, escalation on sensitive topics, and resistance to prompt injection. Results are tracked as metrics against thresholds rather than strict pass or fail on a single run.

Changes to prompts, models, retrieval settings or chunking are treated like code changes and must be checked against the evals.

## 7. Security considerations

- Tenant isolation enforced in code and data, not in prompts.
- Authorization decided by application logic, never by the model (1.3).
- Tool arguments validated on the server regardless of what the model sends.
- Tools run with least privilege.
- Retrieved documents and user messages are untrusted input that may contain injected instructions. The model can only propose, and every proposal is validated and authorized, which limits the damage a manipulated model can do.
- Secrets come from environment configuration and are never committed.
- Personal and health-adjacent data is minimized, kept out of logs where possible, and subject to retention and deletion policy. A compliance review is required before real patient data is processed.
- Important actions are audit-logged (1.5).

## 8. Repository mapping

| Path | Responsibility |
|---|---|
| `backend/app/api` | FastAPI routes, request and response handling, auth dependencies |
| `backend/app/auth` | Authentication helpers and authorization rules |
| `backend/app/orchestrator` | LLM client interface, prompt construction, tool-calling loop, escalation rules |
| `backend/app/tools` | Appointment, lead and escalation tools |
| `backend/app/rag` | Document ingestion, chunking, embedding, retrieval |
| `backend/app/schemas` | Typed schemas for structured outputs and tool inputs and outputs |
| `backend/app/db` | Models, sessions, migrations |
| `backend/app/core` | Configuration, logging, shared utilities |
| `backend/tests` | Deterministic test suite |
| `backend/evals` | AI evaluation suite |
| `frontend` | React / Next.js application (later) |
| `docs` | Architecture and design documents |
| `docs/learning` | Personal daily learning notes, written by the learner |
| `.github/workflows` | CI pipelines (later) |

Dependencies point inward: `api` depends on `orchestrator`; `orchestrator` depends on `tools`, `auth` and `schemas`; `tools` depend on `rag`, `db` and `schemas`; `core` is shared. Tools never depend on the API layer.

## 9. Deferred decisions

Intentionally not decided yet. Each will be settled when the phase that needs it begins, with the reasoning recorded here.

- LLM provider and model selection
- Embedding model and chunking strategy
- Authentication and tenant resolution mechanism
- ORM and migration tooling
- Audit log schema and where its writer lives
- Conversation memory strategy for long conversations
- Streaming responses
- Observability stack
- MCP server design (the tool layer is designed so the same tools can be exposed over MCP later)
- Voice and SMS channels
- Compliance approach (HIPAA or equivalent) before handling real patient data

## 10. Non-goals for now

- Implementing any of the above
- Autonomous multi-agent systems; a single orchestrator with tools is the starting point
- Clinical advice of any kind
- Replacing the practice management system; integration is a later concern
- Infrastructure beyond a single API service and PostgreSQL (no queues, microservices or orchestration platforms until a concrete need exists)
