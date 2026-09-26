# Testing

## Backend

Pytest covers health, schema creation, uploads, extraction, evidence, validation, concurrency, approval, export, and failure handling. External LLM calls are mocked. Tests use a temporary SQLite file and do not need an API key.

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

Cases include dashboard empty and error states, upload validation, processing status, field/evidence/issue rendering, save, approval controls, export availability, and keyboard focus on labeled inputs.

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

## Quality commands

```powershell
cd backend
python -m ruff check .

cd ../frontend
npm run lint
npm run typecheck
npm run build
```
