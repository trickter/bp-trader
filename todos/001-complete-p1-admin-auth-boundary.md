---
status: complete
priority: p1
issue_id: "001"
tags: [code-review, security, architecture, frontend, backend, auth]
---

# Enforce Admin Auth Boundary

## Problem Statement

The current implementation does not enforce an admin auth boundary. The `/api/*` surface is accessible without authentication, and the frontend does not gate the admin shell.

## Findings

- `/api/*` handlers are registered without auth dependencies in main.py.
- Frontend routing does not prevent admin shell rendering for unauthenticated users.
- The system lacks a shared authentication dependency between frontend and backend.

## Proposed Solutions

### Fix: Add Shared Auth Dependency

- Create a shared FastAPI auth dependency.
- Add auth requirement to all `/api/*` handlers via router-level dependency.
- Add frontend token store and admin login gate.

**Effort:** 4-6 hours | **Risk:** Medium

## Acceptance Criteria

- [ ] Unauthenticated requests to `/api/*` return 401
- [ ] Admin pages are not accessible without valid token
- [ ] Invalid tokens redirect to login
- [ ] Logout clears session

## Work Log

### 2026-03-08 - Header Token Gate Implemented

**By:** Codex

**Actions:**
- Added a shared FastAPI auth dependency
- Moved `/api/*` handlers onto a router with global auth dependency
- Added a frontend session token store and invalid-token reset flow
- Added an admin login gate and logout path
- Documented the `X-Admin-Token` contract

**Learnings:**
- A router-level FastAPI dependency is enough to enforce the boundary consistently
- Session-scoped storage keeps the frontend gate minimal

## Notes

- This issue blocks safe live-mode usage.
