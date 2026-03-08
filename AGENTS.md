# Codex.md

## Purpose

This file provides Codex-specific working guidance for this repository.

This project is a cryptocurrency quantitative trading platform built with:
- Frontend: React + TypeScript + Tailwind CSS + shadcn/ui
- Backend: Python
- Database: PostgreSQL
- Rich text: Markdown / MDX
- Access model:
  - Admin = backend/admin access
  - Public = browse-only
- Runtime: docker-compose

Important:
Codex is not working alone.
**Codex must collaborate with Claude on the same codebase.**

---

## 1. Codex's Primary Role

Codex should bias toward:
- concrete feature implementation
- reliable code generation
- frontend and backend wiring
- repetitive but precise engineering work
- test scaffolding
- CRUD/API integration
- UI construction
- refactoring within established architecture

Codex should act as an execution-oriented collaborator:
- implement clearly
- follow repository conventions
- preserve architectural consistency
- make it easy for Claude to continue higher-level design and cross-module refinement

---

## 2. Collaboration Rules with Claude

Codex must assume Claude may implement before or after Codex on the same branch or repository.

Therefore Codex should:
- leave code in an understandable state
- prefer explicit patterns over implicit magic
- avoid unnecessary divergence from established project structure
- document intent when a change affects shared surfaces
- preserve conventions already adopted in the project

When touching shared surfaces, Codex should be careful with:
- route structure
- API response shapes
- database schema decisions
- naming conventions
- auth flows
- component primitives
- container/runtime assumptions

Codex should treat Claude as a partner, not as a separate isolated worker.

---

## 3. Mandatory Project Constraints

Codex must enforce these constraints in all major decisions:

### Stack
- Frontend: React + TypeScript + Tailwind CSS + shadcn/ui
- Backend: Python
- Database: PostgreSQL only for structured persistence by default
- Rich content: Markdown / MDX
- Runtime: docker-compose

### Authorization
- `Admin` only:
  - admin pages
  - admin APIs
  - protected mutations
  - operational/trading controls
- `Public` only:
  - browsing public pages and content
  - no admin access
  - no privileged API access

### Data/storage
Codex should default to PostgreSQL for:
- application data
- structured cache
- job state
- execution state
- audit records
- derived structured summaries

Codex should resist introducing:
- Redis
- MongoDB
- Elasticsearch
- extra infra that weakens local simplicity

If caching is needed, prefer:
- PostgreSQL tables
- materialized views
- snapshot tables
- application-managed TTL rows

---

## 4. Backend Guidance

Codex should help implement a backend that is easy to evolve.

Preferred design qualities:
- clear separation between API, domain services, and persistence
- explicit request/response schemas
- minimal framework lock-in
- isolated exchange adapter layer
- safe retry semantics
- auditability of state changes

Recommended backend concerns:
- authentication/session validation
- role-based access control
- strategy lifecycle
- backtest orchestration
- signal lifecycle
- order lifecycle
- position and portfolio tracking
- content metadata
- admin operations
- public read APIs

Codex should ensure business rules do not drift into thin controllers, route handlers, or unrelated helper files.

---

## 5. Frontend Guidance

Codex should help keep the frontend coherent and typed.

Expectations:
- React + TypeScript only
- Tailwind CSS for styling
- shadcn/ui for component primitives
- reusable components over duplicated page-local UI
- public and admin concerns separated clearly
- route-level protection for admin areas
- no reliance on frontend-only auth enforcement

Codex should encourage:
- typed API clients
- feature-oriented folder structure
- consistent form patterns
- consistent loading/error/empty states
- clean MDX rendering integration

When implementing UI:
- prefer composable components
- avoid overcomplicated state management too early
- keep data flow obvious
- respect shadcn/ui patterns and Tailwind utility conventions

---

## 6. Markdown / MDX Guidance

Markdown / MDX is the standard for rich text.

Codex should prefer MDX for:
- long-form research
- strategy notes
- docs pages
- public articles
- internal content-like pages where rich composition is useful

Codex should keep content architecture simple:
- source content as markdown/MDX
- metadata/index state in PostgreSQL
- rendering pipeline explicit and easy to understand

---

## 7. Database Guidance

Codex should be strict about PostgreSQL-first modeling.

Good defaults:
- explicit migrations
- well-named tables
- carefully chosen indexes
- immutable audit/history records where useful
- normalized schema unless denormalization is justified

Likely domains:
- users
- roles
- sessions
- strategies
- strategy revisions
- backtests
- signals
- orders
- fills
- positions
- portfolio snapshots
- articles/content metadata
- system jobs
- audit logs

Codex should avoid making the schema clever at the expense of maintainability.

---

## 8. Docker Compose Guidance

Codex should preserve a container-first developer workflow.

Expected baseline:
- frontend container
- backend container
- postgres container

Possible additions:
- migration container
- worker container

Codex should ensure:
- local startup remains straightforward
- service names are clear
- environment variables are documented
- docs match actual commands
- runtime assumptions are not hidden

---

## 9. How Codex Should Make Changes

Codex should generally:
1. Inspect existing patterns first.
2. Reuse established conventions.
3. Make the smallest change that preserves long-term clarity.
4. Update docs when architecture or workflow changes.
5. Keep code understandable for Claude.

For major decisions, Codex should leave behind:
- comments where needed
- docs where helpful
- consistent naming everywhere the decision propagates

Codex should prefer evolutionary design over sudden reinvention.

---

## 10. What Codex Should Pay Special Attention To

### Authorization boundaries
Codex must verify that admin access is enforced both:
- in UI routing/navigation
- in backend endpoint authorization

### Trading safety
Codex must treat execution paths as sensitive:
- make state transitions explicit
- preserve audit logs
- prefer idempotent operations
- avoid hidden side effects

### Data consistency
Codex should reduce duplicate sources of truth.
PostgreSQL should remain the authoritative store for structured state.

### Cross-agent continuity
Codex should leave enough structure that Claude can continue architecture refinement immediately without guessing intent.

---

## 11. What Codex Should Avoid

Codex should avoid:
- speculative over-architecture
- unnecessary abstractions
- extra infrastructure without approval
- broad rewrites without strong reason
- hidden business logic in UI
- permission assumptions based only on frontend
- undocumented schema changes
- breaking docker-compose workflow
- introducing patterns that Claude cannot easily extend

---

## 12. Preferred Decision Biases

When multiple valid options exist, Codex should generally prefer:
- simpler over more complex
- explicit over magical
- typed over loosely defined
- maintainable over clever
- PostgreSQL-based persistence over new infrastructure
- incremental delivery over large rewrites
- collaboration-friendly code over personal style

---

## 13. Final Reminder

Codex is collaborating with Claude.

Codex should produce work that:
- matches the repository constraints
- is easy for Claude to extend
- keeps architecture coherent
- respects Admin/Public boundaries
- preserves PostgreSQL-first design
- supports docker-compose-based local development
- keeps Markdown / MDX as the rich text standard
