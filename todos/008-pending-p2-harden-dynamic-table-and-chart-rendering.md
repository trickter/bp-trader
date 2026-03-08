---
status: pending
priority: p2
issue_id: "008"
tags: [code-review, frontend, quality, performance]
dependencies: []
---

# Harden Dynamic Table and Chart Rendering

## Problem Statement

Two reusable UI primitives are brittle under live data: tables key rows by array index, and the candlestick chart assumes non-empty candle data while doing avoidable per-render work.

## Findings

- `DataTable` uses `rowIndex` as the React key in `/app/ai-code/trader/src/components/data-table.tsx:50`, which can misrender reordered or prepended live rows such as alerts, events, and positions.
- `CandlestickChart` computes bounds from `Math.min(...prices)` and `Math.max(...prices)` without guarding empty arrays in `/app/ai-code/trader/src/components/candlestick-chart.tsx:7`.
- `CandlestickChart` also does `findIndex()` for every trade marker in `/app/ai-code/trader/src/components/candlestick-chart.tsx:84`, which grows poorly with larger backtests.

## Proposed Solutions

### Option 1: Add Explicit Row Identity and Empty-State Guards

**Approach:** Extend `DataTable` with a `getRowKey` prop and add an explicit empty/error render path in `CandlestickChart`.

**Pros:**
- Correctness improvement first
- Small, targeted change

**Cons:**
- Minor API change to table component

**Effort:** 2-4 hours

**Risk:** Low

---

### Option 2: Memoize Chart Derivations Too

**Approach:** Add key/guard fixes plus precomputed timestamp-to-index maps and memoized chart math.

**Pros:**
- Handles both correctness and scaling

**Cons:**
- Slightly more implementation work

**Effort:** 4-6 hours

**Risk:** Low

## Recommended Action

## Technical Details

**Affected files:**
- `/app/ai-code/trader/src/components/data-table.tsx`
- `/app/ai-code/trader/src/components/candlestick-chart.tsx`

**Related components:**
- Profile page
- Alerts page
- Backtests page

**Database changes:**
- No

## Resources

- `/app/ai-code/trader/src/lib/types.ts`

## Acceptance Criteria

- [ ] Dynamic lists no longer use array index as row identity
- [ ] Charts render a controlled state when candle data is empty
- [ ] Marker lookup in `CandlestickChart` is not O(markers × candles)
- [ ] Backtest and list components behave correctly with live updates

## Work Log

### 2026-03-08 - Review Finding Created

**By:** Codex

**Actions:**
- Reviewed `DataTable` and `CandlestickChart` primitives
- Consolidated TypeScript and performance reviewer findings

**Learnings:**
- These components are fine against small fixtures but become correctness and scaling issues under live or larger datasets

## Notes

- This is a strong candidate for a small follow-up cleanup PR.
