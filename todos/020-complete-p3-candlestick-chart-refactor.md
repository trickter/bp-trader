---
status: pending
priority: p3
issue_id: "020"
tags: [code-review, frontend, refactor]
dependencies: []
---

# Frontend: CandlestickChart Too Complex

## Problem Statement

CandlestickChart component is 835 lines with mixing concerns.

## Findings

- File: `/app/ai-code/trader/src/components/candlestick-chart.tsx`
- Handles: SVG rendering, mouse/keyboard, zoom/pan, data transforms, warnings
- 12+ useMemo calls
- Magic numbers throughout

## Proposed Solutions

### Option 1: Extract Sub-components

**Approach:** Split into ChartCanvas, MarkerLayer, EquityOverlay.

**Effort:** 4 hours | **Risk:** Low

## Recommended Action

## Acceptance Criteria

- [ ] Chart calculations extracted
- [ ] Marker logic in separate hook
- [ ] Magic numbers as constants

## Work Log

### 2026-03-08 - Review Finding

**By:** TypeScript Review
