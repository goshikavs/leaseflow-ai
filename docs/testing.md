# Testing

## Backend

Pytest covers the original extraction/review/export slice plus RAG chunking, real vector similarity, organization isolation, MCP discovery and tool calls, LangGraph specialist aggregation, feature-flag precedence including lease-type agent toggles, fail-closed policy, and the Property A/B/C scenarios.

Fixture matching is asserted against verified hashes and explicit `sample_key` values. A PDF named `sample_lease.pdf` with an unknown hash must not receive fixture fields. Policy auto-approval and human approval both persist through `apply_approval` and write `approval_source` on the `lease_approved` audit event.

External LLM calls are not required. Tests use a temporary SQLite file.

```powershell
cd backend
python -m pytest
```

Coverage is emitted on the terminal and as `coverage.xml`.

## Frontend

Vitest and React Testing Library mock `fetch` at the network boundary.

```powershell
cd frontend
npm test
```

Cases include dashboard empty and error states, upload validation, processing status, field/evidence/issue rendering, save, approval controls, export availability, keyboard focus on labeled inputs, and Agent settings save for commercial versus residential specialists.

## End-to-end

Playwright starts the backend in fixture mode and the Next.js dev server, then:

1. Uploads the valid synthetic sample
2. Confirms extracted tenant values
3. Approves and inspects export JSON
4. Uploads the missing-fields sample and confirms approval stays disabled until corrections

```powershell
cd frontend
npx playwright install chromium
npm run e2e
```

CI runs the same job on Ubuntu. If browsers cannot be installed in an environment, that blocker is recorded rather than replaced with a mocked unit test.

Manual reviewer steps for both the human-review and agentic flows: [reviewer-verification.md](reviewer-verification.md).

## Quality commands

```powershell
cd backend
python -m ruff check .

cd ../frontend
npm run lint
npm run typecheck
npm run build
```
