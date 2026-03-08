---
status: pending
priority: p2
issue_id: "003"
tags: [code-review, performance, backend, frontend, live-mode]
dependencies: []
---

# Reduce Live Request Fanout and Snapshot Drift

## Problem Statement

The Profile and Market Pulse surfaces perform avoidable duplicate upstream calls in live mode, increasing latency, rate-limit risk, and data inconsistency.

## Findings

- The Profile page calls three endpoints in parallel in [profile-page.tsx](/app/ai-code/trader/src/pages/profile-page.tsx#L11).
- Each backend handler independently rebuilds `fetch_account_snapshot()` in [main.py](/app/ai-code/trader/backend/app/main.py#L83), [main.py](/app/ai-code/trader/backend/app/main.py#L96), and [main.py](/app/ai-code/trader/backend/app/main.py#L109).
- `fetch_account_snapshot()` performs four sequential Backpack requests in [backpack.py](/app/ai-code/trader/backend/app/providers/backpack.py#L38).
- `fetch_market_pulse()` fetches klines in [backpack.py](/app/ai-code/trader/backend/app/providers/backpack.py#L88), but `/api/markets/pulse` discards that payload in [main.py](/app/ai-code/trader/backend/app/main.py#L169).

## Proposed Solutions

### Option 1: Add aggregated endpoints and request-scoped caching

**Approach:** Expose a single profile snapshot endpoint and reuse one provider fetch per request path.

**Pros:**
- Direct latency improvement
- Preserves data consistency across summary/assets/positions

**Cons:**
- Requires frontend contract change

**Effort:** Medium

**Risk:** Low

---

### Option 2: Keep endpoints, cache provider calls internally

**Approach:** Add request-scoped or short-TTL caching at the backend provider/service layer.

**Pros:**
- Smaller frontend churn
- Helps multiple consumers

**Cons:**
- Still leaves fragmented API shape
- Cache invalidation decisions needed

**Effort:** Medium

**Risk:** Medium

## Recommended Action

## Technical Details

**Affected files:**
- [profile-page.tsx](/app/ai-code/trader/src/pages/profile-page.tsx)
- [main.py](/app/ai-code/trader/backend/app/main.py)
- [backpack.py](/app/ai-code/trader/backend/app/providers/backpack.py)

## Acceptance Criteria

- [ ] One profile screen load does not trigger duplicate account snapshot rebuilds
- [ ] Market pulse does not fetch unused klines
- [ ] Independent upstream requests inside a provider fetch run concurrently where safe
- [ ] Live-mode latency/rate-limit behavior is measurably improved

## Work Log

### 2026-03-08 - Initial Review Finding

**By:** Codex

**Actions:**
- Traced frontend fetch pattern for the Profile page
- Followed provider call graph into Backpack client usage
- Consolidated Python and performance reviewer notes

**Learnings:**
- Current live-mode behavior will scale poorly even before mutations are introduced

