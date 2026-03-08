---
status: pending
priority: p1
issue_id: "002"
tags: [code-review, security, reliability, backend, provider]
dependencies: []
---

# Harden Provider Failure Handling

## Problem Statement

Backpack upstream failures currently leak raw payloads to clients and do not consistently translate transport failures into stable API errors.

## Findings

- `_provider_fetch()` returns `detail={"message": str(exc), "payload": exc.payload}` in [main.py](/app/ai-code/trader/backend/app/main.py#L244).
- `BackpackClient._request()` in [client.py](/app/ai-code/trader/backend/app/backpack/client.py#L220) does not wrap `httpx` transport exceptions.
- Unexpected payload shapes are normalized into placeholder “success-like” rows instead of failing loudly according to reviewer findings in [backpack.py](/app/ai-code/trader/backend/app/providers/backpack.py#L38).
- This creates both information leakage and ambiguous runtime behavior during exchange incidents.

## Proposed Solutions

### Option 1: Sanitize + translate all upstream failures

**Approach:** Catch `httpx.HTTPError`, convert to provider-level exceptions, log upstream payloads server-side only, and return normalized error bodies to clients.

**Pros:**
- Fixes both leak and contract instability
- Minimal surface change

**Cons:**
- Requires consistent logging strategy
- Needs careful test coverage

**Effort:** Medium

**Risk:** Low

---

### Option 2: Full provider result envelope

**Approach:** Introduce a strict result/error envelope for provider calls and reject unsupported payload shapes centrally.

**Pros:**
- Stronger long-term contract
- Easier future provider swaps

**Cons:**
- Larger refactor
- More code churn

**Effort:** Large

**Risk:** Medium

## Recommended Action

## Technical Details

**Affected files:**
- [main.py](/app/ai-code/trader/backend/app/main.py)
- [client.py](/app/ai-code/trader/backend/app/backpack/client.py)
- [backpack.py](/app/ai-code/trader/backend/app/providers/backpack.py)

## Resources

- Review context: current directory review, not a PR diff

## Acceptance Criteria

- [ ] Raw upstream payloads are not returned to clients
- [ ] Transport failures return stable 502/503 style responses
- [ ] Unsupported upstream payload shapes fail closed
- [ ] Provider error behavior is covered by tests or reproducible fixtures

## Work Log

### 2026-03-08 - Initial Review Finding

**By:** Codex

**Actions:**
- Reviewed provider fetch error mapping
- Checked Backpack HTTP client transport handling
- Consolidated security and Python reviewer findings

**Learnings:**
- Failure-path normalization currently undermines the provider abstraction

