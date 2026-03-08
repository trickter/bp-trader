---
status: complete
priority: p2
issue_id: "008"
tags: [code-review, architecture, frontend, backend, api-contract]
dependencies: [001]
---

# Align Backtest Client Contract

## Problem Statement

Frontend backtest flow does not match the documented backend lifecycle. Demo-only shortcuts conflict with the intended backtest lifecycle. Route/controller logic is hard to extend.

## Findings

- README API surface differs from frontend client usage
- Demo mode requires hardcoded singleton assumptions
- Backtest creation/retrieval semantics are not explicit

## Proposed Solutions

### Fix: Match Contract

- Align frontend flow with documented backend lifecycle
- Remove or isolate demo-only shortcuts
- Make backtest creation/retrieval semantics explicit

**Effort:** 3-4 hours | **Risk:** Medium

## Acceptance Criteria

- [ ] Frontend backtest flow matches the documented backend lifecycle
- [ ] Demo-only shortcuts are either removed or explicitly isolated/documented
- [ ] Route/controller logic is easier to extend without duplicating mock/live branching
- [ ] Backtest creation/retrieval semantics are explicit in code and docs

## Work Log

### 2026-03-08 - Completed

- Frontend now uses an explicit create-then-read lifecycle in [src/hooks/use-backtest-run.ts](/app/ai-code/trader/src/hooks/use-backtest-run.ts) and [src/pages/backtests-page.tsx](/app/ai-code/trader/src/pages/backtests-page.tsx).
- Backend exposes accepted-run semantics and durable lookup by id in [backend/app/main.py](/app/ai-code/trader/backend/app/main.py).
- Types and API client were aligned in [src/lib/types.ts](/app/ai-code/trader/src/lib/types.ts) and [src/lib/api.ts](/app/ai-code/trader/src/lib/api.ts).
