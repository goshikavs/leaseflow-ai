# Prompt 03: testing and fixes

## Observed failures and corrections

These events actually happened during implementation on 2026-09-25/26.

1. **Pydantic 2.11.9 failed to install on Python 3.14.** `pydantic-core==2.33.2` tried to compile from source and needed an MSVC Rust target. Fix: pin `pydantic==2.12.5` (has a `cp314` wheel) and `fastapi==0.128.8`.

2. **Invalid leases could be approved.** `replace_validation_issues` marked old issues resolved and inserted new rows, but `blocking_issues()` still read the in-memory relationship, which no longer contained the new blocking rows. Fix: append created issues onto `lease.issues` and approve from the newly created issue list.

3. **Alembic `upgrade head` failed after `create_all`.** Startup originally created tables without stamping Alembic. A later `alembic upgrade` tried to create `documents` again. Fix: startup now runs Alembic with an absolute `script_location`. Tests no longer pre-create tables.

4. **Ruff E501/I001 on first backend pass.** Auto-fixed import order, raised line length to 120, and wrapped remaining long lines.

5. **Frontend TypeScript: `lease`/`form` possibly null** inside save/approve closures. Fix: capture `currentLease` and `currentForm` after the render guard.

6. **Upload unit test did not see a non-PDF rejection.** `userEvent.upload` plus `accept=".pdf"` never fired `onChange` in jsdom. Fix: `fireEvent.change`. Also added Testing Library `cleanup()` so later tests did not see leftover buttons.

7. **Playwright first assertion was too loose.** `/lease approved/i` matched both the status banner and an audit-event label. A later assertion matched the tenant name in both the definition list and the JSON `<pre>`. Fix: assert `getByRole("status")` and the export `<pre>` only.

## Verified results

- Backend: `python -m ruff check backend` passed; `python -m pytest backend` — **31 passed**, **90% coverage**.
- Frontend: `npm run lint` passed; `npm run typecheck` passed; `npm test` — **11 passed** (3 files).
- Production build: `npm run build` succeeded (Next.js 15.5.26).
- Playwright: `npm run e2e` — **2 passed** (valid approve/export; missing-fields blocking path).
- Docker: `docker` is not installed on the implementation machine. Compose files exist; CI validates `docker compose config`.

## Not claimed

- Live OpenAI extraction was not executed.
- GitHub Actions was not observed to run, because the private remote was not authenticated at implementation time.
