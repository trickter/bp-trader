---
status: pending
priority: p1
issue_id: "003"
tags: [code-review, backend, data-integrity, reliability]
dependencies: []
---

# Fail Closed on Unknown Backpack Payload Shapes

## Problem Statement

The Backpack normalization layer currently fabricates plausible-looking records when it encounters unsupported payload shapes. In a trading admin surface, silent fake success is worse than a hard failure.

## Findings

- `_unwrap_list()` falls back to `[payload]` for mappings that do not expose known list containers, which allows error objects or wrapper objects to masquerade as data rows in `/app/ai-code/trader/backend/app/providers/backpack.py:202`.
- Downstream normalizers default missing fields to placeholders such as `UNKNOWN`, `0.0`, and empty timestamps around `/app/ai-code/trader/backend/app/providers/backpack.py:227`, `/app/ai-code/trader/backend/app/providers/backpack.py:241`, and related normalizer sections cited by the Python reviewer.
- The result is that malformed or drifted vendor responses can become phantom assets, positions, or events instead of surfacing a provider error.

## Proposed Solutions

### Option 1: Strict Schema Validation

**Approach:** Validate provider payloads before normalization and raise `ProviderError` when required fields or expected containers are missing.

**Pros:**
- Strongest correctness guarantee
- Makes vendor drift obvious immediately

**Cons:**
- Requires explicit validation rules for each endpoint

**Effort:** 4-8 hours

**Risk:** Medium

---

### Option 2: Warning Threshold with Hard Fail

**Approach:** Keep tolerant parsing for minor field drift, but fail when container shape or critical fields are missing.

**Pros:**
- More flexible with vendor evolution
- Lower rewrite cost

**Cons:**
- More nuanced logic to maintain

**Effort:** 3-6 hours

**Risk:** Medium

---

### Option 3: Leave Placeholder Parsing

**Approach:** Keep current tolerant behavior and rely on UI warnings.

**Pros:**
- No immediate implementation cost

**Cons:**
- Dangerous data integrity posture
- Operators can act on fabricated records

**Effort:** 0 hours

**Risk:** High

## Recommended Action

## Technical Details

**Affected files:**
- `/app/ai-code/trader/backend/app/providers/backpack.py`

**Related components:**
- Provider normalization helpers
- FastAPI live-mode responses

**Database changes:**
- No

## Resources

- `/app/ai-code/trader/backend/app/providers/base.py`

## Acceptance Criteria

- [ ] Unknown provider container shapes fail with a provider error instead of fabricating records
- [ ] Required fields for positions, assets, events, and metrics are explicitly validated
- [ ] Placeholder defaults are limited to non-critical optional fields only
- [ ] Tests cover malformed Backpack payloads and vendor drift cases

## Work Log

### 2026-03-08 - Review Finding Created

**By:** Codex

**Actions:**
- Reviewed provider normalization flow and list/object unwrapping behavior
- Consolidated Python reviewer data-integrity concerns into a single actionable finding

**Learnings:**
- The current normalization layer is optimized for happy-path flexibility, but that makes failure semantics unsafe for an admin trading console

## Notes

- This issue is especially important before onboarding more Backpack endpoints.
