# Day 4: First real LLM integration (revision notes)

`POST /chat` now asks Claude Haiku 4.5 for a structured `IntentResult`. Route -> service -> `IntentExtractor` -> Anthropic client.

## How LLM APIs work
You send an HTTPS request with a model name, instructions and messages. The model generates text token by token and the response comes back with usage numbers. It is stateless: nothing is remembered unless you resend it. The SDK wraps this (auth, retries, timeouts, typed errors).

## System vs user instructions
- **System**: the rules and job description, written by us (`INTENT_SYSTEM_PROMPT`).
- **User**: the end user's text. It is untrusted data and may try to give orders ("ignore your rules"). The system prompt says to classify it, not obey it.
- Keep the job narrow: classify only, never claim bookings, availability, policies or diagnoses.

## Tokens
Models read and write tokens (word pieces), not characters. You pay per input and output token, and `max_tokens` caps the output. Our result is tiny, so `max_tokens=256` is plenty and cheap. Haiku is the cheap tier, which fits a simple classification job.

## Temperature
Controls randomness. 0 means the most likely token each time: the best choice for classification and extraction. Higher values suit creative text. Even at 0, output is not guaranteed identical, so it is still probabilistic.

## Structured output
`messages.parse(..., output_format=IntentResult)` sends the Pydantic JSON schema to the API, which constrains generation to match it, then the SDK parses it into the model. No regex on free text. `intent` is a `Literal`, so only the three allowed values can appear.

## Why validate model output anyway
Constrained output can still be wrong in content, refused, cut off by `max_tokens`, or the call can fail. So: Pydantic validates, `parsed_output is None` becomes `LLMOutputError`, and we never guess. Treat model output as a proposal from an untrusted source.

## Provider abstraction
`IntentExtractor` is a `Protocol` (an interface). The route depends on that, injected with `Depends(get_intent_extractor)`. Only `app/llm/anthropic_client.py` knows about Anthropic. To switch provider, write one new class. In tests, `app.dependency_overrides` swaps in a fake, so no network or cost.

## Async LLM calls
The model call takes hundreds of milliseconds to seconds of waiting (I/O-bound). `async def` plus `await client.messages.parse(...)` lets the server handle other requests during the wait. Only this path is async; `/health` and `/lead` stay plain `def` because they never wait.

## AI must not claim tool actions succeeded
The model cannot book anything. If it said "your appointment is booked", that would be a lie the patient acts on. Only real tool code, after validation and authorization, may report success. For now the model only labels intent; later, tools will perform actions and the app, not the model, reports results.

## Failure handling
- Provider error or timeout -> `LLMProviderError` -> HTTP 502.
- Invalid or missing structured output -> `LLMOutputError` -> 502.
- No API key -> 503. Checked at call time so a blank message still gets 422.
- No silent fallback to keywords: a hidden fallback would report guesses as if the AI had understood.

## Deterministic vs probabilistic boundary
- Deterministic (ordinary code, unit tested): request validation, schema validation, routing, error mapping, config.
- Probabilistic (the model): deciding which intent a message expresses.
- Rule: probabilistic output only enters the app through a validated schema. Later, AI quality will be measured with evals (datasets and scoring), not unit tests. Unit tests here only prove our code handles each outcome correctly.

## Secrets
API key lives in an environment variable (`ANTHROPIC_API_KEY`), locally in `backend/.env` which is git-ignored. `.env.example` has placeholders only. Never print or commit the key.
