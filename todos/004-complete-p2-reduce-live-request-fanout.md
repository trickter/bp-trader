---
status: complete
priority: p2
issue_id: "004"
tags: [code-review, performance, backend, frontend, live-mode]
dependencies: [001, 002]
---

# Reduce Live Request Fanout

## Problem Statement

One profile screen load triggers duplicate account snapshot rebuilds. Market pulse fetches unused klines. Current live-mode behavior will scale poorly even before mutations are introduced.

## Findings

- Profile page makes multiple parallel/sequential fetches for similar data
- Market pulse endpoint fetches klines even when not needed by caller
- Independent upstream requests inside provider fetch could run concurrently

## Proposed Solutions

### Fix: Deduplicate and Parallelize

- Cache account snapshot within request scope
- Add optional parameters to skip unnecessary fetches
- Use `asyncio.gather` for independent upstream calls

**Effort:** 3-5 hours | **Risk:** Low

## Acceptance Criteria

- [ ] One profile screen load does not trigger duplicate account snapshot rebuilds
- [ ] Market pulse does not fetch unused klines
- [ ] Independent upstream requests inside a provider fetch run concurrently where safe
- [ ] Live-mode latency/rate-limit behavior is measurably improved

## Work Log

### 2026-03-08 - Completed

- Added short-lived live profile snapshot caching in [backend/app/main.py](/app/ai-code/trader/backend/app/main.py).
- Parallelized independent Backpack upstream calls with `asyncio.gather` in [backend/app/providers/backpack.py](/app/ai-code/trader/backend/app/providers/backpack.py).
- Stopped fetching klines from `market pulse` unless explicitly requested.
- Added backend regression coverage in [backend/tests/providers/test_backpack_provider.py](/app/ai-code/trader/backend/tests/providers/test_backpack_provider.py) and [backend/tests/test_main_api.py](/app/ai-code/trader/backend/tests/test_main_api.py).
