---
status: pending
priority: p2
issue_id: "008"
tags: [code-review, security, docker, config]
dependencies: []
---

# Remove Insecure Default Credentials from Networked Services

## Problem Statement

The repository ships weak default credentials and publishes services on host ports, which is too easy to misuse outside a strictly local environment.

## Findings

- Weak defaults are defined in [.env.example](/app/ai-code/trader/.env.example#L8) and [.env.example](/app/ai-code/trader/.env.example#L27).
- Compose falls back to `postgres/postgres` and `dev-admin-token` in [docker-compose.yml](/app/ai-code/trader/docker-compose.yml#L5) and [docker-compose.yml](/app/ai-code/trader/docker-compose.yml#L21).
- Backend config also defaults `admin_api_token` in [config.py](/app/ai-code/trader/backend/app/config.py#L9).
- This is not the primary auth bug, but it compounds exposure whenever the stack is run on a shared machine or poorly isolated host.

## Proposed Solutions

### Option 1: Require explicit secrets outside local dev

**Approach:** Keep dev convenience only when `APP_ENV=development`; otherwise fail fast if secrets are missing.

**Pros:**
- Retains local usability
- Reduces accidental exposure

**Cons:**
- Requires slightly better env documentation

**Effort:** Small

**Risk:** Low

---

### Option 2: Remove all fallbacks and require `.env`

**Approach:** Make secrets mandatory for every startup path.

**Pros:**
- Strongest safety posture

**Cons:**
- More friction for first-time local setup

**Effort:** Small

**Risk:** Low

## Recommended Action

## Technical Details

**Affected files:**
- [.env.example](/app/ai-code/trader/.env.example)
- [docker-compose.yml](/app/ai-code/trader/docker-compose.yml)
- [config.py](/app/ai-code/trader/backend/app/config.py)

## Acceptance Criteria

- [ ] Weak secrets are not silently used outside explicit local dev mode
- [ ] Compose/runtime docs explain required env values
- [ ] Startup fails loudly when secret requirements are not met

## Work Log

### 2026-03-08 - Initial Review Finding

**By:** Codex

**Actions:**
- Reviewed env defaults and compose fallbacks
- Consolidated security reviewer findings that were distinct from the missing auth boundary itself

**Learnings:**
- Unsafe defaults are often how “dev-only” assumptions become production incidents

