# Reviewer verification: human and agentic flows

Use this checklist to verify the whole solution. Both flows share extraction, evidence, validation, `apply_approval`, audit, and export. They differ only in whether LangGraph specialists, MCP, and policy run.

Start the app from the README (fixture mode). Confirm:

- Frontend: http://localhost:3000
- Backend: http://localhost:8000/health
- OpenAPI: http://localhost:8000/docs

If Property A/B/C PDFs are missing from `samples/`, run `python samples/generate_samples.py`. Upload buttons use sample keys; you do not have to pick those files by hand.

| Upload button | File in `samples/` | Property | Graph |
| --- | --- | --- | --- |
| Complete valid lease | `sample_lease.pdf` | `prop-unassigned` | No |
| Missing fields lease | `missing_fields_lease.pdf` | `prop-unassigned` | No |
| Conflicting dates lease | `conflicting_dates_lease.pdf` | `prop-unassigned` | No |
| Property A: Prosper Retail Center | `prosper_retail_lease.pdf` | `prop-prosper-retail` | Yes |
| Property B: Dallas Corporate Plaza | `dallas_plaza_lease.pdf` | `prop-dallas-plaza` | Yes |
| Property C: North Texas Logistics Park | `logistics_park_lease.pdf` | `prop-ntx-logistics` | Yes |
| Property C amendment | `logistics_park_amendment.pdf` | `prop-ntx-logistics` | Yes |

`logistics_park_large.pdf` exists for seed/RAG exhibits and `GET /api/v1/demo/samples`. It is not an Upload button.

A file-picker upload of a catalog PDF matches the live sample bytes or `manifest.json` hash and binds the same property as the corresponding button. An unknown PDF stays unassigned, so specialists will not run. Agents start only when `ENABLE_MULTI_AGENT` is on and the document is bound to a demo property. The uploaded filename is never a fixture selector.

These PDFs are fictional fixture samples, not live LLM results.

## Flow 1 — Human review (original slice)

Goal: extract, show evidence, block bad data, let a person correct and approve, then export. Specialists stay off.

### 1. Happy path

1. Open http://localhost:3000/upload
2. Click **Complete valid lease**
3. On the review page, confirm tenant `Northwind Analytics LLC`, evidence passages, and fixture-mode labeling
4. Confirm there is no specialist workflow (property is unassigned)
5. Click **Approve**
6. Open export and confirm `schema_version` is `"1.0"`

Expected: lease `approved`, `approval_source` is human review, export is allowed.

### 2. Blocking issues

1. On Upload, click **Missing fields lease**
2. Confirm **Approve** is disabled
3. Confirm blocking issues for omitted landlord, property, and/or rent
4. Fill the missing fields and save
5. Confirm an audit event for the correction
6. Approve and export

Expected: approval stays off until blocking issues are resolved. The same `apply_approval` path writes the approved record.

### 3. Validation rule

1. On Upload, click **Conflicting dates lease**
2. Confirm expiration precedes commencement and approval is blocked

Expected: deterministic validators, not an LLM, reject the date range.

## Flow 2 — Agentic (specialists, MCP, policy)

Goal: the same extraction/review record, plus LangGraph specialists, allowlisted MCP tools, and a deterministic policy decision. Policy may request auto-approval; only `apply_approval` writes status. Auto-approval is an internal abstraction only. It never signs a lease or moves funds.

### 1. Agent settings

1. Open http://localhost:3000/settings
2. Confirm **Commercial** and **Residential** columns
3. Commercial default: leasing on, insurance off
4. Residential default: leasing off, insurance on, auto-approval off
5. Residential auto-approval is a policy default, not a checkbox on this page. Confirm it after a residential Property A upload on the review **Approval control** panel
6. Optionally disable a required agent and save. That specialist should skip on the next matching upload, and auto-approval should stay off

### 2. Property A — auto-approval when policy allows

1. On Upload, leave lease type **Commercial**
2. Click **Property A: Prosper Retail Center**
3. Confirm property `prop-prosper-retail` and lease type `commercial` in the review header
4. Confirm **Agent execution** lists document, lease RAG, property, finance, legal, leasing, and risk as SUCCESS (insurance skipped/optional when off). **MCP team servers** shows only the departmental tools.
5. Confirm policy `AUTO_APPROVED` and lease `approved` with `approval_source` from the policy engine
6. Confirm export still uses `schema_version` `"1.0"`
7. A second Approve should be rejected (already approved)

Expected: agents and MCP ran; approval still went through `apply_approval`, not a second workflow.

### 3. Property B — always manual

1. Click **Property B: Dallas Corporate Plaza**
2. Confirm specialists ran
3. Confirm policy `MANUAL_REVIEW_REQUIRED` and lease `awaiting_review`
4. A human can still correct and approve

### 4. Property C and amendment — escalate on conflict

1. Click **Property C: North Texas Logistics Park**
2. Confirm specialists ran and auto-approval is off
3. Click **Property C amendment**
4. Confirm amendment RAG / conflict handling and policy `ESCALATED` or `BLOCKED`
5. Confirm the lease is not auto-approved

### 5. Residential profile

1. On Settings, keep residential leasing off and insurance on
2. On Upload, set lease type **Residential**, then click **Property A**
3. Confirm leasing `SKIPPED` and insurance `SUCCESS`
4. Confirm auto-approval stays off

### 6. Knowledge (optional)

1. Open http://localhost:3000/knowledge
2. Ask a question scoped to Harborpoint and an assigned property
3. Confirm citations or `insufficient_evidence`
4. A mismatched organization should be rejected (403)

## What to look for across both flows

- Extraction output, evidence, validation, approval, audit, and export stay on the original tables
- Agents enrich context; they do not replace the lease row
- Human Approve and policy auto-approval both call `apply_approval`
- Fixture match is content hash (manifest or the live catalog PDF) or explicit sample key, never the uploaded filename
- Disabling a required agent skips that specialist and fail-closes auto-approval

Automated coverage for these paths: `cd backend; python -m pytest` and `cd frontend; npm test`. Playwright covers the human happy path and missing-fields block.
