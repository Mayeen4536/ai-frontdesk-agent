# October Day 1

## What is an LLM?

A Large Language Model is a probabilistic language and reasoning component. It can understand and generate natural language. Examples: GPT, Claude, Gemini.

In our architecture the LLM is **one component** of the larger AI agent system, not the whole system. It interprets messy human input and phrases replies. Everything else (rules, data, permissions, actions) is normal software.

**Key limitation:** LLMs can misunderstand, hallucinate, or give inconsistent outputs. So they should not directly control critical business operations.

## What is RAG?

Retrieval-Augmented Generation: give the LLM relevant external knowledge at question time so its answer is grounded in that knowledge instead of its memory.

```
User question
-> retrieve relevant external/business knowledge
-> provide retrieved information to the LLM
-> generate a grounded response
```

Good fits for our product (stable knowledge):

- clinic opening hours
- services
- policies
- insurance information
- FAQs

**RAG is not live transactional data.** Appointment availability, live inventory, balances and any rapidly changing state should normally come from databases or APIs, not from RAG. Embedded documents are snapshots and go stale.

## What is an embedding?

An embedding converts text (or other information) into a numerical vector that represents its semantic meaning. Similar meanings end up close together, so we can find conceptually related content even when the exact words differ.

Example: "dental implant" and "replacement tooth" are semantically related despite different wording.

- Keyword search = lexical similarity (matching words)
- Embedding search = semantic similarity (matching meaning)

## What is a vector database?

A vector-capable database stores embeddings and supports similarity search.

```
Document
-> chunk
-> embedding
-> vector storage
-> similarity search
-> retrieve relevant content
```

Our project may start with **PostgreSQL + pgvector** instead of a separate vector database. We already need PostgreSQL, and pgvector covers our needs, with tenant filtering in ordinary SQL. Adding another system now would be unnecessary. This is **YAGNI** (You Aren't Gonna Need It): add infrastructure when a real requirement appears.

## What is structured output?

Structured output means making the LLM return information in a predictable schema instead of arbitrary free-form text.

```json
{
  "intent": "book_appointment",
  "date": "2026-10-03",
  "time_preference": "afternoon",
  "reason": "broken tooth"
}
```

Why it matters:

```
Natural language
-> AI understanding
-> structured data
-> deterministic application logic
```

Structured output makes downstream systems easier to validate, test and automate.

## What is tool calling?

Tool calling lets the LLM/agent **request** that the application run a controlled function. The model does not run anything itself. Examples:

- `check_available_slots()`
- `create_lead()`
- `book_appointment()`
- `search_knowledge()`
- `escalate_to_human()`

The LLM should never manipulate databases directly.

```
LLM proposes
-> Application validates
-> Authorization permits
-> Tool executes
-> Audit log records
```

Tools may **read state**, **perform actions**, or **update state**.

## What is an AI agent?

An AI agent is a larger system that uses an LLM together with tools, state/memory, rules and an execution loop to pursue a goal.

```
Observe
-> Understand/Reason
-> Choose Action
-> Execute Tool
-> Observe Result
-> Continue or Stop
```

**Chatbot vs agent:** a chatbot mainly responds with text. An agent can understand a goal, choose actions, call tools, inspect results and change system state.

**Use the least autonomous system that solves the problem.** When a process is predictable, a deterministic workflow is often better than an agent.

## Our architecture

```
User
-> Web / Chat UI
-> FastAPI
-> Input Validation
-> AI Orchestrator
```

The AI Orchestrator may use:

- Knowledge / RAG
- Appointment Tool
- Lead Tool
- Human Escalation
- Persistent State / Memory

Persistent systems:

- PostgreSQL
- pgvector where semantic retrieval is needed

Cross-cutting concerns: authentication, authorization, validation, security, testing, AI evaluation, logs, metrics, traces, audit logs.

**Architecture rules**

1. Use deterministic software for deterministic problems.
2. Use AI where language understanding or probabilistic reasoning adds value.
3. Dynamic transactional state belongs in databases/APIs rather than RAG.
4. The LLM proposes actions, but deterministic application code controls whether they can happen.
5. Critical actions require validation and authorization.
6. Tool results are the source of truth for whether an action succeeded.
7. The AI must not claim an action succeeded if the tool/API reports failure.
8. Avoid unnecessary infrastructure until scale or requirements justify it.

## Biggest thing I learned today

Modern AI systems should not give an LLM unrestricted control.

The strongest architecture separates:

- probabilistic reasoning
- deterministic business rules
- authorization
- tool execution
- persistent state
- observability

The LLM helps understand ambiguous human input and propose actions, while normal software keeps the system safe and reliable.

## Thing I still don't understand

Topics to study later:

- how embeddings are mathematically created
- how similarity scores work
- how RAG chunking and retrieval quality are optimized
- how agent memory differs from normal database state
- how LangGraph manages agent execution
- how MCP standardizes tool access
- how production AI systems are evaluated
- how to test probabilistic systems reliably

## Day 1 Quick Recall

- LLM = probabilistic language/reasoning component
- RAG = retrieve relevant knowledge before generation
- Embedding = numerical representation of semantic meaning
- Vector search = search by meaning/similarity
- Structured output = predictable machine-readable AI response
- Tool calling = model requests controlled application functions
- Agent = LLM + tools + state + rules + execution loop
- RAG is for knowledge; live transactional state comes from databases/APIs
- LLM proposes; application validates and controls execution
