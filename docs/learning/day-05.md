# Day 5: PostgreSQL persistence (revision notes)

`POST /lead` now saves a row. Route -> lead service -> LeadRepository -> SQLAlchemy -> PostgreSQL.

## Vocabulary
- **Table**: a named set of rows with the same shape (`leads`).
- **Row**: one record (one lead). **Column**: one field of every row (`email`).
- **Primary key**: the column that uniquely identifies a row (`id`). The database generates it, so the API returns the real id only after the insert.
- **Foreign key**: a column pointing at another table's primary key (later: `appointments.patient_id`). The database refuses orphan references.
- **CRUD**: Create (INSERT), Read (SELECT), Update, Delete. Today we only do Create.
- **Index**: a lookup structure that makes searches on a column fast, at the cost of slower writes and extra space. The primary key already has one. Add others only for real queries (for example email lookup).
- **Transaction**: a group of changes that all succeed or all vanish. Our insert is one: commit on success, rollback on error. No half-saved lead.
- **Normalization**: store each fact once and link by key, instead of copying it into many rows (a clinic's details live in a `clinics` table, not repeated on every lead).
- **PostgreSQL**: a relational database server. Strong consistency, constraints, transactions, and later pgvector for embeddings in the same database.

## Why SQLAlchemy
It maps Python classes to tables, manages sessions and transactions, and works with Alembic later. A bare driver means hand-written SQL and manual mapping. We use the sync ORM because `/lead` is a plain `def` route; only the LLM call needs async.

## Service vs repository
- **Repository**: knows how to store and fetch (SQL, sessions, commit/rollback). Nothing about HTTP or business rules.
- **Service**: knows what the application does (save this lead). Calls the repository.
- **Route**: HTTP only: validate, call service, map errors to status codes.
Benefit: swap or fake the storage in tests without touching the route.

## Database vs RAG
- **Database**: exact, current, transactional facts: leads, appointments, availability. Query returns the truth.
- **RAG**: finds relevant passages of stable text (policies, FAQs) by meaning, to give the model context. Approximate, never the source of truth for state.

## Why persistence success is the source of truth
"Saved" must mean the database committed. So: build the response from the stored row, and if the commit fails return 503. Telling a patient "we got your details" when nothing was stored loses a real lead silently. Same principle as Day 4 (never fake an AI success).

## Things I should remember
- `create_all` only creates missing tables; it cannot change existing ones. Real schema changes need Alembic migrations (next step).
- "phone or email" is checked in Pydantic, not in the database yet. A CHECK constraint would also protect against writes that bypass the API.
- Tests use in-memory SQLite for speed; real PostgreSQL behaviour was verified by hand. A CI job with real Postgres comes later.
- Secrets: `DATABASE_URL` lives only in the gitignored `.env`. Settings hide it from `repr`. Logs record the error type, never the lead's data.
- On Windows use `127.0.0.1` not `localhost` if connections hang for ~10s (IPv6 tried first).
- The old venv was 32-bit Python, which psycopg has no wheels for. Rebuilt it with 64-bit Python 3.11.
