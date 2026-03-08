---
status: pending
priority: p2
issue_id: "004"
tags: [code-review, performance, backend, api]
dependencies: []
---

# Reduce Live Request Fan-Out and Sequential Provider Awaits

## Problem Statement

Live-mode page loads currently amplify upstream Backpack traffic and serialize independent requests. This hurts latency, increases rate-limit pressure, and can produce internally inconsistent snapshots.

## Findings

- `/api/profile/summary`, `/api/profile/assets`, and `/api/profile/positions` each call `fetch_account_snapshot()` in `/app/ai-code/trader/backend/app/main.py:83`, `/app/ai-code/trader/backend/app/main.py:96`, and `/app/ai-code/trader/backend/app/main.py:109`.
- `fetch_account_snapshot()` performs four upstream requests sequentially in `/app/ai-code/trader/backend/app/providers/backpack.py:38`.
- A single Profile screen load can therefore trigger 12 upstream exchange requests before account events are fetched.
- `fetch_market_pulse()` also awaits independent provider calls sequentially and fetches klines even though `/api/markets/pulse` discards them in `/app/ai-code/trader/backend/app/providers/backpack.py:88` and `/app/ai-code/trader/backend/app/main.py:169`.

## Proposed Solutions

### Option 1: Add Shared Snapshot Endpoints and Request-Scoped Caching

**Approach:** Expose one profile snapshot endpoint for summary/assets/positions, and cache provider results within a request or page-load boundary.

**Pros:**
- Largest immediate latency win
- Prevents inconsistent cross-section data

**Cons:**
- Requires client contract change

**Effort:** 1 day

**Risk:** Medium

---

### Option 2: Keep Existing Endpoints but Cache Internally

**Approach:** Maintain current API shape while memoizing `fetch_account_snapshot()` per request context and removing unused pulse fetches.

**Pros:**
- Smaller client impact
- Improves live-mode performance fast

**Cons:**
- Existing fragmented API shape remains

**Effort:** 4-8 hours

**Risk:** Low

---

### Option 3: Parallelize Provider Calls Only

**Approach:** Use `asyncio.gather()` inside provider methods and leave route/API shape intact.

**Pros:**
- Straightforward backend optimization

**Cons:**
- Does not solve duplicate page-level snapshot fetches

**Effort:** 3-5 hours

**Risk:** Low

## Recommended Action

## Technical Details

**Affected files:**
- `/app/ai-code/trader/backend/app/main.py`
- `/app/ai-code/trader/backend/app/providers/backpack.py`
- `/app/ai-code/trader/src/pages/profile-page.tsx`
- `/app/ai-code/trader/src/pages/market-pulse-page.tsx`

**Related components:**
- Profile data-loading flow
- Market pulse flow
- Backpack provider latency characteristics

**Database changes:**
- No

## Resources

- `/app/ai-code/trader/src/lib/api.ts`

## Acceptance Criteria

- [ ] Profile page no longer triggers redundant snapshot fetches in live mode
- [ ] Independent Backpack requests run concurrently where safe
- [ ] `/api/markets/pulse` does not fetch unused klines
- [ ] Live-mode latency and request count are measured before/after the change

## Work Log

### 2026-03-08 - Review Finding Created

**By:** Codex

**Actions:**
- Traced frontend profile loads to backend handlers
- Reviewed provider request patterns and pulse assembly
- Consolidated performance and python findings

**Learnings:**
- The current mock-friendly API shape becomes expensive immediately in live mode

## Notes

- This should land before production-like load testing.
