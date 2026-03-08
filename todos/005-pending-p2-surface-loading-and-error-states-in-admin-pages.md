---
status: pending
priority: p2
issue_id: "005"
tags: [code-review, frontend, reliability, ux]
dependencies: []
---

# Surface Loading and Error States in Admin Pages

## Problem Statement

The dashboard’s data hooks track loading and error state, but the pages ignore them and render empty-looking views. That makes outages and API regressions look like valid business zero states.

## Findings

- `useDashboardData()` returns `{ data, loading, error }` in `/app/ai-code/trader/src/hooks/use-dashboard-data.ts:38`.
- Pages consume only `.data` in `/app/ai-code/trader/src/pages/profile-page.tsx:11`, `/app/ai-code/trader/src/pages/alerts-page.tsx:8`, `/app/ai-code/trader/src/pages/market-pulse-page.tsx:8`, `/app/ai-code/trader/src/pages/settings-page.tsx:9`, `/app/ai-code/trader/src/pages/strategies-page.tsx:9`, and `/app/ai-code/trader/src/pages/backtests-page.tsx:10`.
- In failure cases, tables and cards therefore render as if the system simply has no data.

## Proposed Solutions

### Option 1: Per-Page Loading/Error Panels

**Approach:** Add explicit loading, error, and empty-state rendering on each page using existing hook outputs.

**Pros:**
- Clear operator feedback
- Minimal API changes

**Cons:**
- Repetition unless abstracted carefully

**Effort:** 3-5 hours

**Risk:** Low

---

### Option 2: Shared Query State Wrapper

**Approach:** Introduce a reusable page-level state component around `useDashboardData()` results.

**Pros:**
- Consistent UX
- Less repeated page code

**Cons:**
- Slight abstraction cost

**Effort:** 4-6 hours

**Risk:** Low

## Recommended Action

## Technical Details

**Affected files:**
- `/app/ai-code/trader/src/hooks/use-dashboard-data.ts`
- `/app/ai-code/trader/src/pages/profile-page.tsx`
- `/app/ai-code/trader/src/pages/backtests-page.tsx`
- `/app/ai-code/trader/src/pages/alerts-page.tsx`
- `/app/ai-code/trader/src/pages/market-pulse-page.tsx`
- `/app/ai-code/trader/src/pages/settings-page.tsx`
- `/app/ai-code/trader/src/pages/strategies-page.tsx`

**Related components:**
- Cards
- Data tables
- Admin operator workflows

**Database changes:**
- No

## Resources

- `/app/ai-code/trader/src/components/data-table.tsx`

## Acceptance Criteria

- [ ] Every async page distinguishes loading, error, empty, and success states
- [ ] API failure does not render as a false “no data” state
- [ ] Error states include enough context for admin troubleshooting
- [ ] UX remains consistent across all dashboard sections

## Work Log

### 2026-03-08 - Review Finding Created

**By:** Codex

**Actions:**
- Reviewed data hook API and page usage
- Consolidated frontend reliability review findings

**Learnings:**
- This is a reliability problem, not just a cosmetic UX improvement, because operators can misread outages as true empty state

## Notes

- This should be fixed before using live market/account data operationally.
