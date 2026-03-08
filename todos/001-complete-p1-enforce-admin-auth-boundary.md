---
status: complete
priority: p1
issue_id: "001"
tags: [code-review, security, architecture, frontend, backend, auth]
dependencies: []
---

# Enforce Admin Auth Boundary Across Frontend and Backend

## Problem Statement

The project is documented as an admin-only console, but neither the React app nor the FastAPI API actually enforce an admin boundary. Any caller that can reach the frontend or backend can access the admin surface today.

## Findings

- Frontend routes mount the admin shell directly with no auth gate, session bootstrap, or role check in `/app/ai-code/trader/src/App.tsx:15` and `/app/ai-code/trader/src/components/dashboard-layout.tsx:50`.
- Backend routes under `/api/*` expose profile, positions, alerts, settings, and backtest creation with no auth dependency in `/app/ai-code/trader/backend/app/main.py:83`, `/app/ai-code/trader/backend/app/main.py:141`, and `/app/ai-code/trader/backend/app/main.py:224`.
- The only auth-looking setting, `admin_api_token`, is defined but unused in `/app/ai-code/trader/backend/app/config.py:9`.
- This violates the repository’s stated Admin/Public separation and would expose real account data in `BACKPACK_MODE=live`.

## Proposed Solutions

### Option 1: Header-Based Admin Token Gate

**Approach:** Add a FastAPI dependency that validates `ADMIN_API_TOKEN` on every admin endpoint, and add a frontend bootstrap/auth guard that requires the same credential before rendering routes.

**Pros:**
- Smallest change from current code
- Enforces server-side protection immediately

**Cons:**
- Primitive auth model
- Weak fit for future multi-user/admin role expansion

**Effort:** 3-5 hours

**Risk:** Medium

---

### Option 2: Session-Based Admin Auth

**Approach:** Introduce explicit admin session validation on the backend and a frontend route guard that checks session state before rendering the dashboard.

**Pros:**
- Correct long-term shape
- Extends cleanly to multiple admins and RBAC

**Cons:**
- More implementation work now
- Requires auth/session storage decisions

**Effort:** 1-2 days

**Risk:** Medium

---

### Option 3: Network-Only Mitigation

**Approach:** Rely on private network placement and reverse-proxy controls, leaving application code unchanged.

**Pros:**
- Lowest implementation effort

**Cons:**
- Does not satisfy the project’s own admin/public constraint
- Fragile and unsafe for local misconfiguration or future deployment drift

**Effort:** 1 hour

**Risk:** High

## Recommended Action

Implement the smallest enforceable admin boundary now:
- protect every `/api/*` route with a shared FastAPI dependency that validates `X-Admin-Token` against `ADMIN_API_TOKEN`
- keep `/healthz` public so container and local health checks still work without privileged credentials
- block the React admin shell until a token is entered, store it only in `sessionStorage`, and attach it to each API request
- document the header contract and add focused backend tests for missing, invalid, and valid tokens

## Technical Details

**Affected files:**
- `/app/ai-code/trader/src/App.tsx`
- `/app/ai-code/trader/src/components/dashboard-layout.tsx`
- `/app/ai-code/trader/backend/app/main.py`
- `/app/ai-code/trader/backend/app/config.py`
- `/app/ai-code/trader/docker-compose.yml`

**Related components:**
- React route tree
- FastAPI dependency layer
- Admin API configuration

**Database changes:**
- No

## Resources

- `/app/ai-code/trader/README.md`
- `/app/ai-code/trader/compound-engineering.local.md`

## Acceptance Criteria

- [x] Every admin API route requires authenticated admin access on the server
- [x] Frontend admin routes are gated before rendering privileged screens
- [x] Unauthorized requests return explicit 401/403 responses
- [x] The auth mechanism is documented in `README.md`
- [x] `BACKPACK_MODE=live` no longer exposes account data without auth

## Work Log

### 2026-03-08 - Review Finding Created

**By:** Codex

**Actions:**
- Reviewed route mounting in `/app/ai-code/trader/src/App.tsx`
- Reviewed admin API handlers in `/app/ai-code/trader/backend/app/main.py`
- Confirmed `admin_api_token` is dead config in `/app/ai-code/trader/backend/app/config.py`
- Consolidated overlapping frontend, backend, security, and architecture reviewer findings

**Learnings:**
- The repository states an admin-only access model, but the implementation currently has no enforcement layer
- This is the highest-risk issue because it invalidates the project’s basic trust boundary

### 2026-03-08 - Header Token Gate Implemented

**By:** Codex

**Actions:**
- Added a shared FastAPI auth dependency in `/app/ai-code/worktrees/trader-auth/backend/app/auth.py`
- Moved `/api/*` handlers onto a router with global auth dependency in `/app/ai-code/worktrees/trader-auth/backend/app/main.py`
- Added a frontend session token store and invalid-token reset flow in `/app/ai-code/worktrees/trader-auth/src/lib/admin-token.ts` and `/app/ai-code/worktrees/trader-auth/src/lib/api.ts`
- Added an admin login gate and logout path in `/app/ai-code/worktrees/trader-auth/src/App.tsx`, `/app/ai-code/worktrees/trader-auth/src/components/admin-token-gate.tsx`, and `/app/ai-code/worktrees/trader-auth/src/components/dashboard-layout.tsx`
- Documented the `X-Admin-Token` contract in `/app/ai-code/worktrees/trader-auth/README.md`
- Added focused backend coverage in `/app/ai-code/worktrees/trader-auth/backend/tests/test_admin_auth.py`

**Learnings:**
- A router-level FastAPI dependency is enough to enforce the boundary consistently without touching each handler body
- Session-scoped storage keeps the frontend gate minimal while still preventing the admin shell from rendering by default

## Notes

- This issue blocks safe live-mode usage.
