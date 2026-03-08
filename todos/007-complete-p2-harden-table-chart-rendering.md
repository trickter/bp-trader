---
status: complete
priority: p2
issue_id: "007"
tags: [code-review, frontend, quality, performance]
dependencies: [005]
---

# Harden Dynamic Table and Chart Rendering

## Problem Statement

Tables use unstable row keys for live data. Charts render incorrectly with empty candle data. Marker lookup in CandlestickChart is O(markers × candles).

## Findings

- DataTable components use array index as keys
- CandlestickChart has no empty state handling
- Linear search through candles for every marker is inefficient

## Proposed Solutions

### Fix: Stable Keys + Empty States

- Use stable identifiers for table row keys
- Add controlled empty states for charts
- Pre-index candles by timestamp for marker lookup

**Effort:** 2-3 hours | **Risk:** Low

## Acceptance Criteria

- [ ] Tables use stable row keys for live data
- [ ] Charts render a controlled state when candle data is empty
- [ ] Marker lookup in CandlestickChart is not O(markers × candles)
- [ ] Backtest chart renders a clear empty state with zero candles

## Work Log

### 2026-03-08 - Completed

- `DataTable` now requires caller-supplied stable row keys in [src/components/data-table.tsx](/app/ai-code/trader/src/components/data-table.tsx).
- `CandlestickChart` now renders a controlled zero-candle state and uses timestamp indexing for marker placement in [src/components/candlestick-chart.tsx](/app/ai-code/trader/src/components/candlestick-chart.tsx).
- Regression coverage added in [src/test/components.test.tsx](/app/ai-code/trader/src/test/components.test.tsx).
