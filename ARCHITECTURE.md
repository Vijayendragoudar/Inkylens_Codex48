# Inkylens — Architecture and API Contract (v0.1)

**Status:** Design selected on 26 October 2026; no implementation or deployment is claimed by this document.

## 1. Design goal

Deliver one public, judge-friendly web application that demonstrates the complete Round 2 journey while keeping policy decisions explainable and external AI credentials off the browser.

## 2. Chosen architecture

```text
React + TypeScript browser app
        |
        | JSON over HTTPS
        v
FastAPI application
  ├── deterministic rule engine
  ├── optional LLM adapter (server-side only)
  └── SQLAlchemy persistence layer
        |
        v
SQLite for local development / DATABASE_URL-compatible database for deployment
```

The FastAPI application will serve the compiled React application in production. This gives the judge one URL and keeps API keys server-side. Local development uses SQLite. A deployment must use a persistence provider appropriate to its host; an ephemeral host disk must not be presented as durable storage.

## 3. Privacy and AI boundary

- The browser displays a disclosure before a review sends text to the backend.
- The backend sends only the submitted text and necessary approved guidelines to the configured AI provider.
- `OPENAI_API_KEY` (or a future provider-specific equivalent) exists only in server environment variables.
- If no key is configured, the provider fails, the request times out, or the output is malformed, the review remains honest: deterministic findings are returned and the AI status is `unavailable` or `failed`.
- No automated decision constitutes legal, factual, or compliance approval.

## 4. Data model

| Entity | Responsibility |
|---|---|
| Brand | Named anonymous-workspace profile containing guidelines. |
| GuidelineRule | Stable rule key, type, title, content, and optional preferred replacement. |
| Submission | Immutable text supplied for a review. |
| Review | A timestamped review of one submission, including AI availability state. |
| Finding | A deterministic or AI-assisted issue with severity, explanation, suggestion, and rule references. |
| FindingDecision | Persisted human state and optional note for a finding. |

Relationships: `Brand → GuidelineRule`; `Brand → Submission → Review → Finding → FindingDecision`.

## 5. Rule and finding contract

Supported guideline types are `forbidden_term`, `preferred_term`, `tone`, `approved_fact`, and `claim_constraint`.

Every guideline has a human-readable stable key such as `TERM-001`. Deterministic findings must cite a configured key. AI findings may cite only supplied keys; unknown references are rejected. An ungrounded promotional/factual statement is a `claim` finding with the explicit label **unsupported/unverified**, never “false.”

Finding severity is `low`, `medium`, or `high`. A human decision is `open`, `resolved`, `dismissed`, or `accepted_exception`.

## 6. API contract

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/api/health` | Service and database health check. |
| `GET` | `/api/brands` | List available brands, including the seeded demo. |
| `POST` | `/api/brands` | Create a brand in the anonymous demo workspace. |
| `GET` | `/api/brands/{brand_id}` | Read one brand and its guidelines. |
| `PUT` | `/api/brands/{brand_id}` | Update brand details and its complete guideline set. |
| `POST` | `/api/reviews` | Validate text, create a submission/review, run deterministic checks, and attempt AI analysis. |
| `GET` | `/api/reviews/{review_id}` | Retrieve review, findings, decisions, and AI state. |
| `GET` | `/api/brands/{brand_id}/reviews` | Retrieve review history for a brand. |
| `PATCH` | `/api/findings/{finding_id}/decision` | Persist a human decision and optional note. |

All JSON inputs and provider outputs are validated. Client-visible errors use a stable `detail` message and an appropriate HTTP status. No endpoint returns a secret.

## 7. Review execution

1. Validate that the submitted text is not blank and the brand exists.
2. Persist the submission and review skeleton.
3. Run deterministic forbidden-term, preferred-term, and selected accessibility checks.
4. Attempt structured AI analysis with a bounded timeout.
5. Validate findings, reject unsupported rule identifiers, persist valid results, and return a truthful AI state.
6. Preserve previous reviews; a recheck creates a new review rather than overwriting history.

## 8. Verification strategy

- Unit tests: deterministic rule matching, rule references, input validation, and provider-output validation.
- API tests: empty input, persistence, review history, decision persistence, malformed AI output, and AI failure fallback.
- Browser smoke test: seeded demo, edit/save, review, revise/recheck, decision, refresh, keyboard navigation, and disclosure.
- Deployment smoke test: fresh browser, public URL, server-side environment variables, and real provider behavior if a key is configured.

## 9. Deferred decisions and limits

Provider choice, budget limits, hosting account, production database, retention period, and a public URL require the project owner's service accounts or credentials. These will be selected before deployment and documented truthfully. The user-provided deadline is 27 October 2026, 10:00 PM IST; the official event schedule remains unverified.
