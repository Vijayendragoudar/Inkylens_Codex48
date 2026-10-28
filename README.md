# Inkylens

Inkylens is an AI-assisted, human-reviewed brand-governance MVP. It helps a reviewer check pasted copy against organisation-supplied guidance before publication. It is an anonymous demonstration workspace, not a production compliance system or a legal/factual authority.

## Current status

**Last locally verified: 28 October 2026 (IST).**

- Backend tests: **passed** — `8 passed in 0.94s` using the checked-in `.venv`.
- Frontend production build: **passed** — TypeScript check and Vite build completed after a clean `npm ci`; 30 modules transformed in 1.10 seconds.
- Dependency manifest: **fixed and checked** — `python-dotenv` is now declared; `pip check` reports no broken requirements.
- Local in-process API smoke test: **passed** — `GET /api/health` returned HTTP 200 with `{"status":"ok","database":"ok","ai_configured":false}`; `GET /` returned HTTP 200 HTML from the compiled frontend.
- AI provider: **not configured or live-tested** in this verification. Deterministic checks continue when no key is present.
- Browser end-to-end walkthrough: **not yet verified** in a fresh browser during this audit.
- Public deployment, public Git remote, updated submission PDF, and Round 2 submission: **not verified**. The local Git repository has no commits or configured remote. A Vercel deployment entry point and build configuration are prepared, but no hosting account is connected yet.

The supplied event record says the Round 2 deadline was **27 October 2026, 10:00 PM IST**. This repository does not establish an extension, eligibility, or a submission.

## What the application does

1. Loads a seeded fictional brand or creates an anonymous brand profile.
2. Lets a reviewer edit and persist organisation-supplied guidelines.
3. Reviews pasted text with deterministic terminology, claim-restriction, and all-caps readability checks.
4. Optionally requests server-side AI analysis for tone, messaging, and claim issues when `OPENAI_API_KEY` is configured.
5. Shows rule-linked findings with severity, explanation, excerpt, and suggested correction.
6. Labels governed claim issues as **unsupported/unverified**, not false.
7. Saves each recheck as a separate revision and preserves previous review history.
8. Persists human finding decisions: open, resolved, dismissed, or accepted exception.

The seeded brand, `Cinder & Coast — fictional sample brand`, is sample data only. Do not enter confidential customer or organisation content.

## Architecture

```text
React + TypeScript + Vite
        |
        | JSON /api requests
        v
FastAPI
  ├─ deterministic rule engine
  ├─ optional server-side OpenAI Responses adapter
  └─ SQLAlchemy persistence
        |
        v
SQLite for local development
```

In a production-style local run, FastAPI serves `frontend/dist` from `/`. During frontend development, Vite proxies `/api` to FastAPI on port 8000.

### Deployment behaviour

`api/index.py` exposes the existing FastAPI app to Vercel and `vercel.json` builds the React bundle before deployment. Set `INKYLENS_DATABASE_URL` to a persistent, host-supported database before publishing a judge-facing app. If that variable is omitted on Vercel, Inkylens deliberately uses `/tmp/inkylens.db` so the demo can start, but its data can disappear when the serverless instance is replaced. Do not present that fallback as durable persistence.

## Repository map

| Path | Purpose |
|---|---|
| `backend/app/main.py` | FastAPI routes, database initialisation, static frontend serving |
| `backend/app/rules.py` | Deterministic, independently testable rule checks |
| `backend/app/ai.py` | Optional server-side structured AI analysis and output validation |
| `backend/app/models.py` / `schemas.py` | SQLite/SQLAlchemy entities and validated API shapes |
| `backend/app/seed.py` | Fictional demo brand and sample guidance |
| `backend/tests/` | Rules, AI safety, and persisted-review workflow tests |
| `frontend/src/` | React interface, typed API client, and responsive styles |
| `api/index.py` / `vercel.json` | Vercel entry point and frontend production-build configuration |
| `ARCHITECTURE.md` | Design and API contract |
| `PROJECT_REQUIREMENTS.md` | Product requirements and acceptance criteria |
| `DEVELOPMENT_PLAN.md` | Intended phase gates; not a record of completed work |

## Windows setup

Prerequisites: Python 3.11+ and Node.js/npm. From the repository root in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Copy-Item .env.example .env

Set-Location frontend
npm.cmd install
Set-Location ..
```

Never commit `.env` or real provider keys.

## Configuration

Copy `.env.example` to `.env` and keep secrets on the backend only.

| Variable | Local default | Meaning |
|---|---|---|
| `INKYLENS_DATABASE_URL` | `sqlite:///./inkylens.db` | Local SQLite database URL |
| `OPENAI_API_KEY` | empty | Enables optional server-side AI analysis when set |
| `INKYLENS_OPENAI_MODEL` | `gpt-4o-mini` | AI model name used by the adapter |
| `INKYLENS_AI_TIMEOUT_SECONDS` | `20` | Provider request timeout in seconds |

When AI is configured, the submitted copy and the necessary approved guidance are sent to the configured provider. The UI requires a disclosure acknowledgement before review. Without a key, the API returns an explicit `unavailable` AI status and deterministic checks still run.

## Run locally

Build the frontend first:

```powershell
Set-Location frontend
npm.cmd run build
Set-Location ..
```

Then start the backend from the repository root:

```powershell
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. The health endpoint is <http://127.0.0.1:8000/api/health>.

For frontend-only development, run the backend command above in one terminal and the following in another:

```powershell
Set-Location frontend
npm.cmd run dev
```

Then open <http://127.0.0.1:5173>. Vite proxies API requests to port 8000.

If PowerShell permits the `npm` command directly, `npm run build` and `npm run dev` are equivalent. `npm.cmd` avoids the local execution-policy block encountered during this audit.

## Test and build

```powershell
.\.venv\Scripts\python.exe -m pytest backend/tests -q

Set-Location frontend
npm.cmd run build
```

Verified on 28 October 2026:

```text
........                                                                 [100%]
8 passed in 0.94s

✓ 30 modules transformed.
✓ built in 1.10s

No broken requirements found.
```

The automated suite covers deterministic rule behaviour, truthful no-key AI fallback, malformed AI output, invented rule-reference rejection, persisted revisions, review history, and human decision persistence. It does not replace a fresh-browser end-to-end accessibility or usability check.

## Implementation checklist

Status meanings: **planned**, **in progress**, **implemented**, **tested**, **deployed**. “Tested” below means a current automated or smoke check exists; it does not mean public deployment or complete acceptance testing.

| Area | Status | Evidence / current limitation |
|---|---|---|
| Requirements and scope | in progress | The SRS records Phase 1 as approved, while the development plan still says awaiting sign-off. Reconcile this documentation conflict before claiming phase-gate completion. |
| Architecture and API contract | implemented | `ARCHITECTURE.md` and the FastAPI/React/SQLite implementation align at a high level. |
| Seeded anonymous demo workspace | implemented | Fictional Cinder & Coast brand is seeded on database initialisation. |
| Editable brand guidelines | implemented | Brand create/read/update endpoints and UI guideline editor are present. |
| Deterministic rule engine | tested | Rules are source-linked and independently covered by backend tests. |
| Unsupported-claim wording | tested | Claim restrictions produce `unsupported/unverified`, not a falsehood assertion. |
| Optional AI-assisted review | tested | No-key, malformed-output, and unknown-rule-reference paths are tested; no live provider request was run. |
| Revision history and human decisions | tested | Persisted workflow test covers two revisions, history, and a resolved decision. |
| React workflow and production bundle | tested | Production build passes; a fresh-browser journey remains unverified. |
| Local API and compiled homepage | tested | In-process FastAPI smoke check passed with AI unconfigured. |
| Reproducible Python dependencies | tested | `python-dotenv` is declared and `pip check` passes. |
| Accessibility review | in progress | Focus styles, labelled controls, live regions, and responsive CSS exist; no manual keyboard/screen-reader audit was performed. |
| Public deployment | planned | No deployed URL or durable production database is recorded. |
| Vercel deployment package | implemented | Hosting entry point and build configuration are present and locally checked; account connection and deployment verification remain outstanding. |
| Git history and public repository | planned | Repository currently has no commits and no configured remote. |
| Submission PDF and Round 2 submission | planned | Neither is present or verified in this repository. |

## Important limitations

- This is an anonymous demo workspace. It has no authentication, role isolation, invitations, comments, approval routing, or enterprise RBAC.
- It accepts pasted text only. File extraction, image/logo analysis, publishing integrations, dashboards, and analytics are out of scope.
- AI output is advisory, validated, and rule-constrained; it is not an automated compliance, legal, or factual decision.
- SQLite is suitable for the verified local workflow. A public deployment needs an explicitly chosen persistent database and retention policy.
- The source tree and handoff describe the intended judge journey, but this audit did not perform the complete journey in a fresh browser or test live AI.

## Proposed Round 3 improvements

These are proposals, not implemented features.

1. Visual brand-compliance analysis for logos, colours, layouts, and other creative assets.
2. Collaborative approvals with authenticated roles, assignments, comments, and audit trails.
3. Publishing integrations and trend analytics for recurring governance issues.

## Next smallest safe task

Run and record a fresh-browser judge walkthrough: select or create a brand, edit and save a rule, submit the sample copy, inspect rule-linked findings, revise and recheck, record a decision, refresh, and reopen the saved history. Then update this checklist with the observed result.

## Project guidance

Read `CODEX_CONTINUATION_PROMPT.md` first when continuing work, then consult `AGENTS.md`, `PROJECT_REQUIREMENTS.md`, `DEVELOPMENT_PLAN.md`, and `ARCHITECTURE.md`. Work one file at a time, preserve the distinction between verified behaviour and plans, and never send sensitive customer content to an external AI provider without clear disclosure.
