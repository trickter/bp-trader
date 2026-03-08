---
status: complete
priority: p2
issue_id: "009"
tags: [code-review, architecture, agent-native, backend, frontend]
dependencies: []
---

# Establish Agent Native Surface

## Problem Statement

No agent surface exists yet. The backend normalization work is a good base, but there's no way for agents to interact with the system.

## Findings

- Runtime agent context does not include account mode or available capabilities
- Agent actions do not use the same underlying data space the UI uses
- No capability discovery is documented for agents

## Proposed Solutions

### Fix: Add Agent API Layer

- Define capability map for user-visible actions
- Create agent endpoints using same data layer as UI
- Document capability discovery for agents

**Effort:** 4-6 hours | **Risk:** Medium

## Acceptance Criteria

- [ ] Runtime agent context includes account mode, available capabilities, and domain vocabulary
- [ ] Agent actions use the same underlying data space the UI uses
- [ ] Capability discovery is documented for both users and agents

## Work Log

### 2026-03-08 - Completed

- Added capability discovery and agent context endpoints in [backend/app/main.py](/app/ai-code/trader/backend/app/main.py).
- Surfaced the same normalized resources used by the admin UI through `/api/agent/capabilities` and `/api/agent/context`.
- Exposed the agent-native surface in settings UI via [src/pages/settings-page.tsx](/app/ai-code/trader/src/pages/settings-page.tsx) and documented it in [README.md](/app/ai-code/trader/README.md).
