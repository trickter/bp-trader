---
status: complete
priority: p2
issue_id: "005"
tags: [code-review, quality, frontend, ux, reliability]
dependencies: [001, 002]
---

# Show Real Loading and Error States

## Problem Statement

Every screen should distinguish loading, error, empty, and success states. Backend failures are currently invisible to operators. Zero-state tables are used as outage fallbacks.

## Findings

- Error state is calculated but ignored in many hooks
- "Missing data" and "failed fetch" are treated as the same state
- Reliability issues in admin UIs come from treating outage as true empty state

## Proposed Solutions

### Fix: Explicit State Handling

- Surface error states from hooks to components
- Add loading skeletons for async data
- Distinguish "no data" from "failed to load"

**Effort:** 2-4 hours | **Risk:** Low

## Acceptance Criteria

- [ ] Every screen distinguishes loading, error, empty, and success states
- [ ] Backend failures are visible to operators
- [ ] Zero-state tables are not used as outage fallbacks
- [ ] API failure does not render as a false "no data" state

## Work Log

### 2026-03-08 - Completed

- Added shared async state primitives in [src/components/async-state.tsx](/app/ai-code/trader/src/components/async-state.tsx).
- Extended [src/hooks/use-dashboard-data.ts](/app/ai-code/trader/src/hooks/use-dashboard-data.ts) to expose explicit `loading | error | empty | success`.
- Updated admin pages to render real loading/error/empty states instead of falling back to empty tables.
- Added frontend coverage in [src/test/components.test.tsx](/app/ai-code/trader/src/test/components.test.tsx).
