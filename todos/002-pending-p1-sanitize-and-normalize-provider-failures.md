---
status: pending
priority: p1
issue_id: "002"
tags: [code-review, security, backend, api, reliability]
dependencies: []
---

# Sanitize and Normalize Provider Failure Handling

## Problem Statement

The backend leaks raw upstream error payloads to clients and does not consistently translate transport-level failures into stable API responses. This exposes sensitive diagnostics and makes caller behavior unpredictable during exchange outages.

## Findings

- `_provider_fetch()` returns `detail={"message": str(exc), "payload": exc.payload}` for `BackpackRequestError` in `/app/ai-code/trader/backend/app/main.py:244`.
- `exc.payload` comes directly from the Backpack response body created in `/app/ai-code/trader/backend/app/backpack/client.py:235`.
- `BackpackClient._request()` does not catch `httpx.TimeoutException`, `httpx.ConnectError`, or other `httpx.HTTPError` subclasses at `/app/ai-code/trader/backend/app/backpack/client.py:220`.
- As written, callers may see raw vendor payloads in some failure cases and unhandled 500s in others.

## Proposed Solutions

### Option 1: Sanitize at API Boundary

**Approach:** Keep provider internals mostly intact, but change `_provider_fetch()` to log upstream payloads server-side and return a normalized client-safe error shape.

**Pros:**
- Minimal surface-area change
- Removes payload leakage quickly

**Cons:**
- Leaves transport exceptions unstructured unless addressed separately

**Effort:** 2-4 hours

**Risk:** Low

---

### Option 2: Wrap All Provider Errors in Client Layer

**Approach:** Catch `httpx.HTTPError` inside `BackpackClient`, convert them to provider-specific exceptions, and expose only normalized FastAPI error bodies from `_provider_fetch()`.

**Pros:**
- Cleaner abstraction boundary
- Stable external API contract

**Cons:**
- Requires touching both client and route layers

**Effort:** 4-6 hours

**Risk:** Medium

---

### Option 3: Global FastAPI Exception Middleware

**Approach:** Add exception handlers for provider and transport exceptions at the app level.

**Pros:**
- Centralized error presentation

**Cons:**
- Can hide provider abstraction issues if overused
- Still needs route/provider refactor discipline

**Effort:** 3-5 hours

**Risk:** Medium

## Recommended Action

## Technical Details

**Affected files:**
- `/app/ai-code/trader/backend/app/main.py`
- `/app/ai-code/trader/backend/app/backpack/client.py`

**Related components:**
- Backpack provider abstraction
- FastAPI exception contract
- Operational logging

**Database changes:**
- No

## Resources

- `/app/ai-code/trader/backend/app/backpack/exceptions.py`

## Acceptance Criteria

- [ ] Upstream vendor payloads are not returned verbatim to API clients
- [ ] Transport failures are translated into consistent 502/503-style API responses
- [ ] Error responses have a stable documented shape
- [ ] Detailed provider diagnostics are logged server-side only
- [ ] Health and failure behavior is verified in live-mode simulation

## Work Log

### 2026-03-08 - Review Finding Created

**By:** Codex

**Actions:**
- Reviewed provider error translation in `/app/ai-code/trader/backend/app/main.py`
- Reviewed raw request handling in `/app/ai-code/trader/backend/app/backpack/client.py`
- Consolidated overlapping security, python, and architecture findings

**Learnings:**
- The provider abstraction normalizes success paths but currently leaks vendor semantics on failure paths

## Notes

- This should be fixed before adding any more live provider endpoints.
