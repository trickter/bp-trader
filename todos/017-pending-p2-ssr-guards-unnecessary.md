---
status: complete
priority: p2
issue_id: "017"
tags: [code-review, frontend, typescript]
dependencies: []
---

# Frontend: Unnecessary SSR Guards

## Problem Statement

The app uses hasWindow() checks throughout but this is a Vite SPA that never runs on the server.

## Findings

- File: `/app/ai-code/trader/src/lib/admin-token.ts`
- All hasWindow() checks are unnecessary for a client-only SPA
- Adds ~15 lines of dead code

## Proposed Solutions

### Option 1: Remove SSR Guards

**Approach:** Remove hasWindow() function and all its calls.

**Effort:** 10 minutes | **Risk:** Low

## Recommended Action

## Acceptance Criteria

- [ ] hasWindow() removed
- [ ] All usages updated to direct window access
- [ ] No runtime errors

## Work Log

### 2026-03-08 - Review Finding

**By:** Simplification Review
