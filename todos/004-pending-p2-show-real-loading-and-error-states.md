---
status: pending
priority: p2
issue_id: "004"
tags: [code-review, quality, frontend, ux, reliability]
dependencies: []
---

# Show Real Loading and Error States in Admin Screens

## Problem Statement

Dashboard screens currently treat failed API requests like valid empty data, which can mislead operators during outages.

## Findings

- `useDashboardData()` exposes `loading` and `error` in [use-dashboard-data.ts](/app/ai-code/trader/src/hooks/use-dashboard-data.ts#L3).
- Pages consume only `.data`, including [profile-page.tsx](/app/ai-code/trader/src/pages/profile-page.tsx#L11), [backtests-page.tsx](/app/ai-code/trader/src/pages/backtests-page.tsx#L10), and other screens found during review.
- Result: a broken backend can render as “no alerts”, “no positions”, or zeroed metrics instead of an operational error.

## Proposed Solutions

### Option 1: Per-page loading/error/empty states

**Approach:** Add explicit branches in each page using the existing hook contract.

**Pros:**
- Smallest fix
- Keeps current hook

**Cons:**
- Repeated page boilerplate

**Effort:** Medium

**Risk:** Low

---

### Option 2: Shared async state component pattern

**Approach:** Introduce reusable async-state wrappers for section/page rendering.

**Pros:**
- More consistent UI
- Less repetition across screens

**Cons:**
- Slightly more abstraction

**Effort:** Medium

**Risk:** Low

## Recommended Action

## Technical Details

**Affected files:**
- [use-dashboard-data.ts](/app/ai-code/trader/src/hooks/use-dashboard-data.ts)
- [profile-page.tsx](/app/ai-code/trader/src/pages/profile-page.tsx)
- [backtests-page.tsx](/app/ai-code/trader/src/pages/backtests-page.tsx)
- Other page files under [src/pages](/app/ai-code/trader/src/pages)

## Acceptance Criteria

- [ ] Every screen distinguishes loading, error, empty, and success states
- [ ] Backend failures are visible to operators
- [ ] Zero-state tables are not used as outage fallbacks

## Work Log

### 2026-03-08 - Initial Review Finding

**By:** Codex

**Actions:**
- Reviewed hook output and screen usage
- Confirmed error state is calculated but ignored

**Learnings:**
- Reliability issues in admin UIs often come from treating “missing data” and “failed fetch” as the same state

