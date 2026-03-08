---
status: pending
priority: p2
issue_id: "007"
tags: [code-review, architecture, agent-native, backend, frontend]
dependencies: []
---

# Establish an Agent-Native Surface for User-Visible Capabilities

## Problem Statement

The app exposes clear human-facing dashboard capabilities, but none of them are agent-accessible. There is no tool surface, no runtime context injection, and no shared workspace model for future agent actions.

## Findings

- The agent-native reviewer found 0/8 core user-visible capabilities agent-accessible across navigation, profile data, strategy data, alerts, settings, and backtest preview.
- No system prompt or tool manifest exists in this project.
- The UI is fetch-only, so even future agent mutations would have no shared state invalidation path.

## Proposed Solutions

### Option 1: Read-Only Agent Tool Layer First

**Approach:** Expose agent tools for current read surfaces such as profile summary, assets, positions, alerts, settings, and backtest preview.

**Pros:**
- Smallest viable step toward agent-native parity
- Builds on normalized backend contracts already present

**Cons:**
- Still leaves mutations for later

**Effort:** 1-2 days

**Risk:** Medium

---

### Option 2: Full Agent Runtime Foundation

**Approach:** Add tool primitives, runtime prompt construction, shared state invalidation, and capability discovery together.

**Pros:**
- Coherent long-term foundation

**Cons:**
- Larger initial investment

**Effort:** 3-5 days

**Risk:** Medium

## Recommended Action

## Technical Details

**Affected files:**
- `/app/ai-code/trader/src/components/dashboard-layout.tsx`
- `/app/ai-code/trader/src/pages/profile-page.tsx`
- `/app/ai-code/trader/src/pages/strategies-page.tsx`
- `/app/ai-code/trader/src/pages/backtests-page.tsx`
- `/app/ai-code/trader/src/pages/market-pulse-page.tsx`
- `/app/ai-code/trader/src/pages/alerts-page.tsx`
- `/app/ai-code/trader/src/pages/settings-page.tsx`
- `/app/ai-code/trader/backend/app/main.py`

**Related components:**
- Future assistant/system prompt layer
- Backend tool primitives
- Shared UI invalidation model

**Database changes:**
- No immediate change required

## Resources

- `/app/ai-code/trader/compound-engineering.local.md`

## Acceptance Criteria

- [ ] Every major user-visible read capability has an agent-accessible equivalent
- [ ] Runtime agent context includes account mode, available capabilities, and domain vocabulary
- [ ] Agent actions use the same underlying data space the UI uses
- [ ] Capability discovery is documented for both users and agents

## Work Log

### 2026-03-08 - Review Finding Created

**By:** Codex

**Actions:**
- Reviewed the agent-native capability map
- Consolidated agent-native gaps into one roadmap-level finding

**Learnings:**
- The backend normalization work is a good base for future agent support, but no agent surface exists yet

## Notes

- This is not a release blocker unless agent support is an active product requirement, but the gap is currently total.
