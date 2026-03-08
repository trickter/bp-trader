---
status: complete
priority: p1
issue_id: "012"
tags: [code-review, security, critical]
dependencies: []
---

# Security: Hardcoded Production Credentials

## Problem Statement

The `.env` file contains real production credentials that should never be stored in a configuration file:
- ADMIN_API_TOKEN=gntl10mg2xw9g1oa9UlueEFW0rIMtub7
- BACKPACK_API_KEY and BACKPACK_PRIVATE_KEY exposed
- DATABASE_URL with password exposed

This is a CRITICAL security vulnerability.

## Findings

- File: `/app/ai-code/trader/.env`
- Credentials are committed to git history
- Full access to Backpack exchange account exposed
- Admin API token exposed

## Proposed Solutions

### Option 1: Rotate Credentials Immediately

**Approach:** Rotate all exposed credentials and use secrets manager.

**Effort:** 1 hour | **Risk:** High

---

### Option 2: Git History Cleanup

**Approach:** Remove .env from git history using BFG Repo-Cleaner.

**Effort:** 2 hours | **Risk:** Medium

## Recommended Action

## Technical Details

**Affected files:**
- `.env`

## Acceptance Criteria

- [ ] All exposed credentials rotated
- [ ] .env file excluded from git
- [ ] Secrets use environment-specific management

## Work Log

### 2026-03-08 - Review Finding

**By:** Code Review

**Actions:**
- Identified critical credential exposure

