---
review_agents: [kieran-typescript-reviewer, kieran-python-reviewer, code-simplicity-reviewer, security-sentinel, performance-oracle, architecture-strategist, agent-native-reviewer]
plan_review_agents: [kieran-typescript-reviewer, kieran-python-reviewer, code-simplicity-reviewer]
---

# Review Context

- This repository is a mixed-stack local app: React + TypeScript frontend and Python backend.
- Review for local-path quality rather than PR diff quality because this directory is not a git repository.
- Prioritize correctness of API contracts between frontend and backend, runtime safety, deployment ergonomics, and maintainability.
- Treat files under `docs/plans/` and `docs/solutions/` as protected artifacts if they appear later.
