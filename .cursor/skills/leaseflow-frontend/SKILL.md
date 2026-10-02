---
name: leaseflow-frontend
description: Conventions, UI rules, and verification steps for the LeaseFlow AI Next.js review console (upload, review, approval, export, knowledge search, agent settings). Use when changing or reviewing anything under frontend/.
---

# LeaseFlow AI frontend

The review console lets a reviewer upload a lease, check each extracted field against its evidence, correct values, approve, and export. The backend owns all business rules; the frontend displays them and never decides approval on its own.

Stack: Next.js 15 App Router, React 19, TypeScript, Tailwind CSS 3. Tests use Vitest with React Testing Library, and Playwright for end-to-end.

## Architecture map

| Area | Location |
|------|----------|
| Routes (thin wrappers) | `frontend/app/` (`page.tsx`, `upload/`, `leases/[id]/`, `leases/[id]/approved/`, `knowledge/`, `settings/`) |
| Page components | `frontend/components/*Page.tsx` |
| Shared UI | `frontend/components/AppShell.tsx`, `Alert.tsx`, `StatusBadge.tsx`, `LeaseIntelligence.tsx` |
| API client | `frontend/lib/api.ts` |
| API types | `frontend/lib/types.ts` |
| Unit tests and fixtures | `frontend/tests/`, `frontend/tests/test-utils.tsx` |
| End-to-end tests | `frontend/e2e/`, `frontend/playwright.config.ts` |

## Rules

1. **Routes stay thin.** Files in `app/` read route params and render a component from `components/`. Put state, effects, and data fetching in the component.
2. **All HTTP goes through `lib/api.ts`.** Use the `api` object and `request` helper; do not call `fetch` from components. The base URL comes from `NEXT_PUBLIC_API_URL`.
3. **Types mirror the backend contract.** Response shapes live in `lib/types.ts`. When the backend changes a response, update the types in the same change.
4. **Surface backend errors.** `request` throws `ApiRequestError` with `status` and the backend's stable `code`. Show the message in `Alert`; do not swallow errors or replace them with generic text.
5. **The backend decides.** Approval, policy outcome, validation issues, and flag restrictions come from the API. The UI may disable a button based on API state, but must not compute approval eligibility itself.
6. **Show evidence with every field.** Extracted values are displayed next to their evidence passage, page, and confidence status so the reviewer can verify them.
7. **Optimistic locking.** Saves and approvals send the lease `version` the reviewer loaded. On a version conflict, show the backend error; never retry with a newer version automatically, because that would overwrite another reviewer's change.
8. **Accessibility.** Inputs have labels, interactive elements are reachable by keyboard, and status is not conveyed by color alone (`StatusBadge` includes text).
9. **Fixture mode is visible.** When the backend reports a fixture provider, keep the label in the UI so demo output is not mistaken for live extraction.

## Making a change

1. Read the page component and its test in `frontend/tests/` before editing.
2. New API calls are added to `api` in `lib/api.ts` with types in `lib/types.ts`.
3. Every UI change needs a Vitest test that mocks `fetch` at the network boundary using `jsonResponse` from `tests/test-utils.tsx`. Cover loading, empty, error, and success states.
4. Query elements by role and label (`getByRole`, `getByLabelText`), not by CSS class.
5. Changes to the upload, review, approve, or export path should keep `e2e/smoke.spec.ts` passing.

## Verification

Run the same checks as the CI frontend job (`.github/workflows/ci.yml`):

```bash
cd frontend
npm ci
npm run lint
npm run typecheck
npm test
npm run build
```

End-to-end, which starts the backend in fixture mode and the Next.js dev server:

```bash
cd frontend
npx playwright install chromium
npm run e2e
```

## Commit style

One logical change per commit, with a sentence-style message describing the behavior change.
