---
status: complete
priority: p2
issue_id: "016"
tags: [code-review, frontend, typescript]
dependencies: []
---

# TypeScript: TradeMarker Duplicate Property

## Problem Statement

The TradeMarker interface has duplicate properties `action` and `type` that are identical.

## Findings

- File: `/app/ai-code/trader/src/lib/types.ts` (lines 71-83)
- `action` and `type` are the same type: `"open" | "add" | "reduce" | "close" | "stop" | "take_profit"`

## Proposed Solutions

### Option 1: Remove Duplicate

**Approach:** Remove `type` property and keep only `action`.

**Effort:** 10 minutes | **Risk:** Low

## Recommended Action

## Acceptance Criteria

- [ ] TradeMarker has single action property
- [ ] All usages updated

## Work Log

### 2026-03-08 - Review Finding

**By:** TypeScript Review
