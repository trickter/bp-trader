---
status: pending
priority: p3
issue_id: "007"
tags: [code-review, architecture, agent-native, planning]
dependencies: []
---

# Add an Agent-Native Parity Plan

## Problem Statement

The application exposes human UI workflows, but there is no agent tool layer, runtime prompt context, or shared workspace contract.

## Findings

- The agent-native review found 0/8 core visible capabilities are agent-accessible.
- UI capabilities exist across [dashboard-layout.tsx](/app/ai-code/trader/src/components/dashboard-layout.tsx), [profile-page.tsx](/app/ai-code/trader/src/pages/profile-page.tsx), and other screens, but there is no equivalent tool surface.
- No system prompt or capability manifest exists in the repository.
- This is not a merge blocker for the current local app, but it is a clear architecture gap relative to the requested review workflow and the broader agent-native direction.

## Proposed Solutions

### Option 1: Read-only agent primitives first

**Approach:** Add tool equivalents for normalized read endpoints and a lightweight capability manifest.

**Pros:**
- Smallest useful slice
- Reuses current API nouns

**Cons:**
- Does not address mutations yet

**Effort:** Medium

**Risk:** Low

---

### Option 2: Full agent-native architecture pass

**Approach:** Add tools, prompt injection, and shared mutation/update model together.

**Pros:**
- Cleaner long-term system

**Cons:**
- Too large for a small follow-up

**Effort:** Large

**Risk:** Medium

## Recommended Action

## Technical Details

**Affected files:**
- [dashboard-layout.tsx](/app/ai-code/trader/src/components/dashboard-layout.tsx)
- [main.py](/app/ai-code/trader/backend/app/main.py)
- Future prompt/tool integration surfaces

## Acceptance Criteria

- [ ] A capability map exists for user-visible actions
- [ ] At least core read-only admin capabilities have agent equivalents
- [ ] Agent context can discover available resources and allowed actions

## Work Log

### 2026-03-08 - Initial Review Finding

**By:** Codex

**Actions:**
- Incorporated the dedicated agent-native reviewer output into the review synthesis

**Learnings:**
- The backend’s normalized domain model is a good base, but there is currently no agent layer at all

