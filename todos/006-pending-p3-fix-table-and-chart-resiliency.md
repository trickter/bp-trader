---
status: pending
priority: p3
issue_id: "006"
tags: [code-review, frontend, quality, performance]
dependencies: []
---

# Fix Table and Chart Resiliency Gaps

## Problem Statement

Some reusable frontend primitives will behave incorrectly once live data starts reordering or arriving empty.

## Findings

- `DataTable` uses `rowIndex` as the row key in [data-table.tsx](/app/ai-code/trader/src/components/data-table.tsx#L50).
- `CandlestickChart` computes `Math.min(...prices)` and `Math.max(...prices)` without guarding empty candles in [candlestick-chart.tsx](/app/ai-code/trader/src/components/candlestick-chart.tsx#L7).
- Trade marker rendering does an O(markers × candles) `findIndex()` loop in [candlestick-chart.tsx](/app/ai-code/trader/src/components/candlestick-chart.tsx#L84).

## Proposed Solutions

### Option 1: Add stable row keys and empty-state guards

**Approach:** Extend `DataTable` with an optional `getRowKey`, and early-return an empty chart state when no candles exist.

**Pros:**
- Directly fixes correctness issues
- Minimal design churn

**Cons:**
- Slight API change to `DataTable`

**Effort:** Small

**Risk:** Low

---

### Option 2: Precompute chart lookup maps

**Approach:** Build a timestamp index map for trade markers and reuse it during render.

**Pros:**
- Removes avoidable hot path

**Cons:**
- Secondary compared with correctness fixes

**Effort:** Small

**Risk:** Low

## Recommended Action

## Technical Details

**Affected files:**
- [data-table.tsx](/app/ai-code/trader/src/components/data-table.tsx)
- [candlestick-chart.tsx](/app/ai-code/trader/src/components/candlestick-chart.tsx)

## Acceptance Criteria

- [ ] Tables use stable row keys for live data
- [ ] Backtest chart renders a clear empty state with zero candles
- [ ] Chart marker lookup no longer scans the candle array for every marker

## Work Log

### 2026-03-08 - Initial Review Finding

**By:** Codex

**Actions:**
- Reviewed reusable table and chart components
- Validated list-key and empty-data assumptions against likely live behavior

**Learnings:**
- Current mocks hide issues that will surface as soon as data becomes dynamic

