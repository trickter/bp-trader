---
status: complete
priority: p2
issue_id: "006"
tags: [code-review, security, docker, config]
dependencies: []
---

# Remove Insecure Dev Defaults

## Problem Statement

Weak secrets are silently used outside explicit local dev mode. Unsafe defaults are often how "dev-only" assumptions become production incidents.

## Findings

- Env defaults and compose fallbacks use weak secrets
- No clear distinction between dev and production configs
- Startup does not fail when secret requirements are not met

## Proposed Solutions

### Fix: Fail Fast on Missing Secrets

- Require explicit env values for production
- Document required env values in compose/runtime docs
- Fail startup loudly when secret requirements are not met

**Effort:** 1-2 hours | **Risk:** Low

## Acceptance Criteria

- [ ] Weak secrets are not silently used outside explicit local dev mode
- [ ] Compose/runtime docs explain required env values
- [ ] Startup fails loudly when secret requirements are not met

## Work Log

### 2026-03-08 - Completed

- Hardened runtime validation in [backend/app/config.py](/app/ai-code/trader/backend/app/config.py).
- Removed compose fallbacks for `DATABASE_URL`, `ADMIN_API_TOKEN`, and `POSTGRES_PASSWORD` in [docker-compose.yml](/app/ai-code/trader/docker-compose.yml).
- Documented explicit local-dev secret behavior in [README.md](/app/ai-code/trader/README.md) and [.env.example](/app/ai-code/trader/.env.example).
- Added validation tests in [backend/tests/test_config.py](/app/ai-code/trader/backend/tests/test_config.py).
