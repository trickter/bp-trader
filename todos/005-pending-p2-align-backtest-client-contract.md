---
status: pending
priority: p2
issue_id: "005"
tags: [code-review, architecture, frontend, backend, api-contract]
dependencies: []
---

# Align Backtest Client Flow with the Documented API Contract

## Problem Statement

The frontend bypasses the documented backtest creation lifecycle and hardcodes a demo fetch path, which will block real backtest orchestration later.

## Findings

- README documents backtest creation endpoints in [README.md](/app/ai-code/trader/README.md#L61).
- The client hardcodes `GET /api/backtests/demo` in [api.ts](/app/ai-code/trader/src/lib/api.ts#L31).
- The Backtests page consumes that singleton fetch directly in [backtests-page.tsx](/app/ai-code/trader/src/pages/backtests-page.tsx#L10).
- Reviewers also flagged that `main.py` currently mixes HTTP routing with mock/live orchestration, making later lifecycle changes more invasive.

## Proposed Solutions

### Option 1: Keep demo mode, but model real lifecycle now

**Approach:** Add a frontend flow that creates a preview backtest via POST and then loads the returned ID through the existing GET endpoint.

**Pros:**
- Matches future backend behavior
- Keeps mock demo support

**Cons:**
- Requires a small UI flow change

**Effort:** Medium

**Risk:** Low

---

### Option 2: Document the demo shortcut as intentionally temporary

**Approach:** If lifecycle work is deferred, isolate the shortcut behind a clearly named demo client and update docs accordingly.

**Pros:**
- Lower immediate code churn

**Cons:**
- Preserves contract mismatch
- Easy to forget and ship

**Effort:** Small

**Risk:** Medium

## Recommended Action

## Technical Details

**Affected files:**
- [README.md](/app/ai-code/trader/README.md)
- [api.ts](/app/ai-code/trader/src/lib/api.ts)
- [backtests-page.tsx](/app/ai-code/trader/src/pages/backtests-page.tsx)
- [main.py](/app/ai-code/trader/backend/app/main.py)

## Acceptance Criteria

- [ ] Frontend backtest flow matches the documented backend lifecycle
- [ ] Demo-only shortcuts are either removed or explicitly isolated/documented
- [ ] Route/controller logic is easier to extend without duplicating mock/live branching

## Work Log

### 2026-03-08 - Initial Review Finding

**By:** Codex

**Actions:**
- Compared README API surface with frontend client usage
- Checked Backtests page against backend endpoints

**Learnings:**
- Contract drift is already present even before persistence and job orchestration arrive

