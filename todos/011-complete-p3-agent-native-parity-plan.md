---
status: complete
priority: p3
issue_id: "011"
tags: [code-review, architecture, agent-native, planning]
dependencies: [009]
---

# Add Agent Native Parity Plan

## Problem Statement

The backend's normalized domain model is a good base, but there's currently no agent layer at all. Need a plan for future prompt/tool integration.

## Findings

- No agent-native capabilities exist
- Backend normalization work provides good foundation
- Need capability map for user-visible actions

## Proposed Solutions

### Plan: Define Agent Surface

- Create capability map for core read-only admin capabilities
- Define agent context for resource discovery
- Document future prompt/tool integration surfaces

**Effort:** 2-4 hours | **Risk:** Low

## Acceptance Criteria

- [ ] A capability map exists for user-visible actions
- [ ] At least core read-only admin capabilities have agent equivalents
- [ ] Agent context can discover available resources and allowed actions

## Work Log

### 2026-03-08 - Completed

- Replaced the plan-only gap with an implemented capability map in [backend/app/main.py](/app/ai-code/trader/backend/app/main.py).
- Core read-only admin resources now have agent equivalents and are exposed in [src/pages/settings-page.tsx](/app/ai-code/trader/src/pages/settings-page.tsx).
