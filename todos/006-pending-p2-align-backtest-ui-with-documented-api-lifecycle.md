---
status: pending
priority: p2
issue_id: "006"
tags: [code-review, architecture, frontend, backend, api]
dependencies: []
---

# Align Backtest UI With Documented API Lifecycle

## Problem Statement

The frontend bypasses the documented backtest creation flow and hardcodes a demo retrieval shortcut. That creates a contract mismatch that will make real backtest execution and history harder to add.

## Findings

- The README documents `POST /api/strategies/templates/:template_id/backtests`, `POST /api/strategies/scripts/:strategy_id/backtests`, and `GET /api/backtests/:id` in `/app/ai-code/trader/README.md:61`.
- The frontend instead calls a singleton demo getter in `/app/ai-code/trader/src/lib/api.ts:24`.
- The page consumes that shortcut directly in `/app/ai-code/trader/src/pages/backtests-page.tsx:10`.
- This bypasses creation, polling, ownership, and persisted run semantics before they even exist.

## Proposed Solutions

### Option 1: Model Real Backtest Lifecycle Now

**Approach:** Add client calls for backtest creation and retrieval, even if the backend still returns demo data internally.

**Pros:**
- Keeps frontend aligned with intended API contract
- Easier to extend later

**Cons:**
- Slightly more client complexity now

**Effort:** 4-6 hours

**Risk:** Low

---

### Option 2: Update Docs to Match Demo Shortcut

**Approach:** Re-document the current API as demo-only and defer lifecycle work.

**Pros:**
- Low immediate effort

**Cons:**
- Accepts architectural debt
- Moves mismatch into documentation instead of code

**Effort:** 1-2 hours

**Risk:** Medium

## Recommended Action

## Technical Details

**Affected files:**
- `/app/ai-code/trader/src/lib/api.ts`
- `/app/ai-code/trader/src/pages/backtests-page.tsx`
- `/app/ai-code/trader/backend/app/main.py`
- `/app/ai-code/trader/README.md`

**Related components:**
- Strategy workflows
- Backtest execution model

**Database changes:**
- No immediate change required

## Resources

- `/app/ai-code/trader/backend/sql/001_initial_schema.sql`

## Acceptance Criteria

- [ ] Frontend backtest flow matches the documented API contract
- [ ] Demo mode does not require hardcoded singleton assumptions
- [ ] Backtest creation/retrieval semantics are explicit in code and docs

## Work Log

### 2026-03-08 - Review Finding Created

**By:** Codex

**Actions:**
- Compared `README.md` API surface against frontend API client usage
- Consolidated architecture reviewer findings

**Learnings:**
- The current shortcut is fine for demos, but it already conflicts with the intended backtest lifecycle

## Notes

- This is best fixed before introducing real backtest creation UI.
