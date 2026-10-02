# Agent instructions

LeaseFlow AI turns lease PDFs into verified, approved lease records with a FastAPI backend and a Next.js review console.

## Where the instructions live

| File | Purpose |
|------|---------|
| `.cursor/rules/guardrails.mdc` | Always applied: git, secrets, trust-model, scope, and dependency guardrails |
| `.cursor/rules/backend.mdc` | Attached for `backend/**` and `samples/**` |
| `.cursor/rules/frontend.mdc` | Attached for `frontend/**` |
| `.cursor/skills/leaseflow-backend/SKILL.md` | Backend architecture map, invariants, change rules, verification |
| `.cursor/skills/leaseflow-frontend/SKILL.md` | Frontend architecture map, UI rules, test conventions, verification |
| `.cursorignore` | Keeps secrets, local databases, uploads, and build output out of AI context |

## Ground rules

- Never push, force push, or merge without the developer's approval.
- Do not weaken the trust model: evidence before data, one approval path, fail closed.
- Run the verification commands from the relevant skill before reporting a change as done.
