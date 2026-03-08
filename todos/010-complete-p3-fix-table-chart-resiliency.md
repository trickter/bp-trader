---
status: complete
priority: p3
issue_id: "010"
tags: [code-review, frontend, quality, performance]
dependencies: [007]
---

# Fix Table and Chart Resiliency

## Problem Statement

Tables use unstable row keys for live data. Backtest chart doesn't handle zero candles gracefully. Current mocks hide issues that will surface as data becomes dynamic.

## Findings

- DataTable doesn't use stable keys
- CandlestickChart has no empty state
- No proper handling of dynamic/live data

## Proposed Solutions

### Fix: Add Stability

- Use stable row identifiers in tables
- Add empty state handling to charts
- Handle live updates properly

**Effort:** 2-3 hours | **Risk:** Low

## Acceptance Criteria

- [ ] Tables use stable row keys for live data
- [ ] Backtest chart renders a clear empty state with zero candles
- [ ] Chart marker lookup no longer scans the candle array for every marker

## Work Log

### 2026-03-08 - Completed

- Completed as part of the table/chart hardening pass in [src/components/data-table.tsx](/app/ai-code/trader/src/components/data-table.tsx) and [src/components/candlestick-chart.tsx](/app/ai-code/trader/src/components/candlestick-chart.tsx).
- Verified by [src/test/components.test.tsx](/app/ai-code/trader/src/test/components.test.tsx).
