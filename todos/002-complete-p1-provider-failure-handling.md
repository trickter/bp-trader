---
status: complete
priority: p1
issue_id: "002"
tags: [code-review, security, reliability, backend, provider]
dependencies: [001]
---

# Provider Failure Handling

## Problem Statement

Backpack upstream failures currently leak raw payloads to clients and do not consistently translate transport failures into stable API errors.

## Findings

- `_provider_fetch()` returned raw vendor payloads in API error details.
- `BackpackClient._request()` did not wrap `httpx` transport exceptions.
- Error semantics were inconsistent across provider init, auth, transport, and upstream failure paths.

## Resolution

Implemented stable provider failure sanitization:

- `httpx.TransportError` is now converted into client-safe `BackpackRequestError`
- upstream HTTP failures now expose a stable error shape with `code`, `provider`, `retryable`, and optional `upstreamStatus`
- raw Backpack payloads are no longer returned to API clients
- `_provider_fetch()` now returns normalized `502/503` error bodies instead of leaking internals

## Acceptance Criteria

- [x] Raw upstream payloads are not returned to clients
- [x] Transport failures return stable 502/503 style responses
- [x] Unsupported upstream failure paths return a normalized error shape
- [x] Provider error behavior is covered by tests

## Work Log

### 2026-03-08 - Failure Sanitization Implemented

**By:** Codex

**Actions:**
- Hardened `backend/app/backpack/client.py` transport and upstream error translation
- Expanded `backend/app/backpack/exceptions.py` with a client-safe response detail model
- Normalized API-side provider error responses in `backend/app/main.py`
- Added regression coverage in `backend/tests/backpack/test_client_failures.py`
- Added API contract tests in `backend/tests/test_main_provider_errors.py`

**Verification:**
- `PYTHONPATH=/app/ai-code/trader/backend /tmp/trader-backend-venv/bin/python -m pytest backend/tests/backpack/test_client_failures.py backend/tests/test_main_provider_errors.py`

