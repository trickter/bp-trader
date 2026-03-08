---
status: complete
priority: p1
issue_id: "003"
tags: [code-review, backend, data-integrity, reliability]
dependencies: [002]
---

# Fail Closed on Unknown Provider Payload Shapes

## Problem Statement

The Backpack normalization layer currently fabricated plausible-looking records when it encountered unsupported payload shapes. Silent fake success is worse than hard failure in a trading admin surface.

## Findings

- Unknown object/list wrapper shapes were tolerated too broadly.
- Missing critical fields could degrade into placeholders like `UNKNOWN`, `0.0`, and empty timestamps.
- Malformed vendor responses could become phantom assets, positions, fills, or candles.

## Resolution

Backpack provider normalization now fails closed for malformed payloads:

- unknown container shapes now raise `ProviderError`
- required IDs, symbols, timestamps, and critical numeric fields are validated explicitly
- unsupported fill event types are rejected instead of being coerced into trade fills
- malformed kline rows and multi-record object wrappers now fail before normalization
- placeholders remain only for non-critical optional fields

## Acceptance Criteria

- [x] Unknown provider container shapes fail with provider error instead of fabricating records
- [x] Required fields for positions, assets, events, and metrics are explicitly validated
- [x] Placeholder defaults are limited to non-critical optional fields only
- [x] Tests cover malformed Backpack payloads and vendor drift cases

## Work Log

### 2026-03-08 - Strict Payload Validation Implemented

**By:** Codex

**Actions:**
- Tightened provider validation in `backend/app/providers/backpack.py`
- Preserved strict object/list unwrap helpers and required field guards
- Added malformed payload and drift coverage in `backend/tests/providers/test_normalization.py`

**Verification:**
- `PYTHONPATH=/app/ai-code/trader/backend /tmp/trader-backend-venv/bin/python -m pytest backend/tests/providers/test_normalization.py`
