# Inkylens — Project Requirements (SRS v0.2)

**Status:** Phase 1 scope approved by the project owner on 26 October 2026. No code, prototype, deployment, user research, or testing is claimed as completed at the time of this update.
**Event timing record:** The project owner reports a Round 2 deadline of **27 October 2026, 10:00 PM IST**. The official organiser source and full build-window dates have not been independently verified. This is a user-provided planning record, not proof of event eligibility or an official schedule.
**Purpose:** Round 2 functional MVP for an AI-assisted brand-governance platform.
**Development approach:** Solo developer; work incrementally, one file at a time, with instructions and verification.

## 1. Problem and objective
Teams publish content across channels, creating risk of inconsistent tone, terminology, facts, promotional claims, and brand presentation. Manual review is slow and hard to audit. Inkylens will check content *before publication* against organisation-provided approved guidance and explain possible issues. Final editorial decisions remain with humans.

## 2. Users
- **Content creator:** submits copy, reviews issues, revises and resubmits.
- **Brand manager/reviewer:** maintains approved brand guidance and makes review decisions.
- **Demo judge:** can explore a seeded example end-to-end without developer assistance.

For Round 2, roles are represented in one anonymous demo workspace. There is no authentication, identity verification, multi-user isolation, or enterprise RBAC. Do not imply those capabilities are implemented.

## 3. Core MVP journey (must work end to end)
1. Open deployed app and access a clearly labelled demo brand or create a brand profile.
2. Enter/edit brand rules: tone, preferred/forbidden terms, approved facts and claim restrictions.
3. Paste text content for review (text first; file/image analysis is deferred unless capacity permits).
4. Run deterministic rules plus LLM-assisted checks against the supplied brand context.
5. See findings with severity, category, explanation, reference to applicable rule/fact, and suggested correction. Do not claim unverified statements are false; flag as unsupported pending review.
6. Edit content, recheck, and record the result/history.
7. Human reviewer can accept, dismiss, or mark issues resolved, with a visible final review status (basic workflow).

### Round 2 scope boundary

**Included:** a seeded demo brand; editable brand guidelines; pasted text; deterministic terminology checks; backend-only LLM-assisted analysis; explainable findings; review revisions/history; per-finding human decisions; persistence; error states; a public demo flow; and a privacy disclosure.

**Excluded:** document uploads and extraction, image/logo analysis, user accounts, invitations, comments, approval routing, publishing/CMS integrations, analytics dashboards, automatic content replacement, and legal or factual adjudication.

## 4. Functional requirements
| ID | Priority | Requirement | Acceptance criterion |
|---|---|---|---|
| FR-01 | Must | Manage one or more brand profiles and guidelines in an anonymous workspace | A seeded profile can be edited; a saved profile and its rules persist after refresh |
| FR-02 | Must | Store approved terminology, prohibited terms, tone rules, approved facts and claim constraints | Rules persist and can be shown alongside findings |
| FR-03 | Must | Submit pasted text for checking | Valid content is accepted; empty content produces clear validation |
| FR-04 | Must | Deterministic terminology/rule checks | Known forbidden phrase triggers a reproducible finding |
| FR-05 | Must | LLM-assisted tone/messaging/claim analysis | Backend validates structured results before display, or the UI shows a clear recoverable error; never fabricate success |
| FR-06 | Must | Ground findings in supplied rules | Each guideline-based finding identifies its source rule; unsupported claims explicitly labelled |
| FR-07 | Must | Explain findings and propose editable corrections | User can see explanation and suggestion without automatic silent replacement |
| FR-08 | Must | Revision/recheck and persistence | A revised submission can be rechecked and prior review remains accessible |
| FR-09 | Must | Human review decisions | Reviewer can mark a finding open, resolved, dismissed, or accepted as an editorial exception; the decision persists |
| FR-10 | Must | Judge-ready demo | A first-time user can complete the journey using sample data and on-screen guidance |
| FR-11 | Should | Basic accessibility checks for text | Detect selected deterministic issues such as excessive all-caps or ambiguous link text, with limitations noted |
| FR-12 | Could | PDF/DOCX extraction | Only if core journey is stable and file handling is tested |
| FR-13 | Deferred | Image/logo/visual compliance analysis | Round 3 candidate |
| FR-14 | Deferred | Multi-user roles, comments and approval routing | Round 3 candidate |
| FR-15 | Deferred | Analytics and external publishing integrations | Round 3 candidate |

## 4.1 Operational definitions and user stories

- A **guideline** is organisation-supplied guidance stored with a stable identifier, title, type, and text. Examples: `TERM-001`, `FACT-003`, or `TONE-002`.
- A **finding** has a source (`deterministic` or `AI-assisted`), severity (`low`, `medium`, or `high`), category, explanation, suggested correction, and the related guideline identifier where applicable.
- A claim that lacks support in the supplied approved-facts list is labelled **unsupported/unverified**. Inkylens must not label it false.
- An **accepted editorial exception** records a human decision to retain content despite a finding; it is not an automated approval or compliance certification.
- A **review revision** preserves the submitted text, its findings, timestamps, and decisions so an earlier review remains accessible after rechecking.

User stories:

1. As a content creator, I can open a seeded demo brand, review example copy, and understand the result without developer help.
2. As a brand manager, I can edit guidelines and see those exact guidelines referenced in later findings.
3. As a content creator, I can revise copy and compare the resulting saved review with the earlier one.
4. As a reviewer, I can record a human decision for each finding and see it survive refresh.
5. As a judge, I can see an honest AI failure state while deterministic checks continue to provide useful results.

## 5. Non-functional requirements
- **Reliability:** clear loading, timeout, retry and service-unavailable states; deterministic rules still work if AI is unavailable where feasible.
- **Security:** API keys server-side only; input validation; upload limits if uploads are added; no secrets in Git.
- **Privacy:** disclose external LLM processing; do not send confidential material without explicit user awareness/permission; minimize logs and retained content.
- **Explainability:** show the relevant guideline or approved fact; AI outputs are suggestions, not authoritative legal/factual judgments.
- **Usability:** responsive UI; sample brand and sample copy; plain-language findings; no developer intervention needed.
- **Accessibility:** keyboard operability, labelled inputs, sufficient contrast, readable errors.
- **Performance:** measure real response times on deployment; do not invent latency targets/results.
- **Data integrity:** persist brand rules and review history; avoid mixing records between brands.
- **Public-demo scope:** clearly state that this is an anonymous demonstration workspace, not a multi-user production service.

## 6. Proposed stack (not yet implemented)
- Frontend: React + TypeScript (Vite), CSS.
- Backend: Python + FastAPI.
- Persistence: PostgreSQL (SQLite acceptable for initial local development; choose explicitly during architecture phase).
- AI: configurable LLM API, invoked only from backend, with validated structured output.
- Tooling: VS Code or Codex desktop app, Git/GitHub, API tests (pytest/httpx or equivalent), browser testing.
- Hosting: choose compatible frontend/backend/database providers during deployment planning; do not assert deployment exists.

## 7. Round 2 submission and scoring alignment
| Judging criterion | Points | Evidence to prepare |
|---|---:|---|
| Working core workflow | 30 | Judge can run brand setup → review → findings → revision → saved review |
| Technical depth and reliability | 25 | Architecture, working APIs/data persistence/AI, tests and graceful failures |
| Progress from Round 1 | 20 | Feature mapping and screenshots/commits showing implemented scope |
| Three planned improvements | 15 | Three meaningful Round 3 features with scope and value |
| Usability | 10 | Self-service demo, instructions, sample content, accessible UI |
| **Total** | **100** | |

**Mandatory submission:** working project URL, source repository URL, updated PDF, completed feature list, technologies and implementation details, changes from Round 1, and three major Round 3 improvements. Only list genuinely implemented/tested features as completed.

## 8. Round 3 improvement proposals (subject to revision)
1. **Visual brand-compliance engine:** inspect uploaded images for logo usage, palette and visual-guideline deviations with explainable evidence.
2. **Collaborative approval workflow:** real user accounts/roles, assignments, comments, approvals and audit trails.
3. **Cross-channel integration and analytics:** ingest content from publishing tools/CMS, detect recurring violations and report trends.

These are substantial *planned* improvements, not Round 2 functionality unless actually built.

## 8.1 Phase 1 acceptance-test matrix

The following are future acceptance tests. They are requirements, not completed test results.

| ID | Scenario | Pass condition |
|---|---|---|
| AT-01 | Fresh judge visit | A user opens the deployed URL, sees the demo guidance, and can start a seeded review without credentials or developer intervention. |
| AT-02 | Guideline persistence | Edit a guideline, save it, refresh the browser, and see the same value and stable rule identifier. |
| AT-03 | Empty content | Submit blank or whitespace-only text and receive a clear, accessible validation message; no review is falsely created. |
| AT-04 | Deterministic finding | Submit a known forbidden phrase and receive the same rule-linked finding on every run. |
| AT-05 | Grounded claim handling | Submit a claim absent from approved facts and see it labelled `unsupported/unverified`, never false. |
| AT-06 | AI success | Validated AI output is displayed only with its category, explanation, suggestion, and cited supplied rule/fact where applicable. |
| AT-07 | AI failure | A timeout, rate limit, malformed response, or provider outage produces clear retry guidance; deterministic findings remain available where feasible. |
| AT-08 | Revision history | Revise content and recheck it; the earlier review remains accessible with its original content, findings, and decisions. |
| AT-09 | Human decision | Mark a finding resolved, dismissed, or accepted as an editorial exception; refresh and confirm the decision remains visible. |
| AT-10 | Accessibility/privacy smoke test | Keyboard users can reach labelled inputs and errors; the UI displays an LLM-processing disclosure before review submission. |

## 8.2 Required failure behaviour

- Missing brand, guideline, or review identifiers return understandable not-found feedback; the client does not display stale success data.
- Invalid requests are rejected with field-level validation where possible.
- The backend validates LLM output against a defined schema and discards malformed output rather than displaying it as a finding.
- Network failures, timeouts, and rate limits display a recoverable error and retry action; they do not erase the user's submitted text.
- Persistence failures clearly state that saving did not complete and do not claim a saved review exists.
- The LLM must receive only the text and approved guidance necessary for the review, after a visible disclosure. The demo must not invite users to submit sensitive customer material.

## 9. Research, validation and open decisions
- No interviews, surveys, production user validation or working implementation are claimed.
- Validate key assumptions with quick user feedback if possible; record methods and actual findings only.
- Approved Round 2 scope decisions: anonymous demo workspace; seeded demo data; pasted text only; no authentication/RBAC; no uploads; no visual analysis; no publishing integrations; no analytics.
- Decide during architecture: persistence choice; AI provider/model/cost; demo quota; hosting; retention policy; request/response schema; and the exact guideline storage model.
- Build-window status: the user-provided deadline is recorded at the top of this document. The official rules/build window remain unverified and must not be represented as externally confirmed.
- Round 1 evidence status: no baseline repository, submission artefact, or feature inventory has yet been supplied. Before submission, create an honest mapping from actual Round 1 material to implemented Round 2 work; do not invent progress claims.

## 10. Definition of done for Round 2
Deployed URL opens; judge can use seeded demo without credentials they do not have; the core journey passes manual smoke test; errors are understandable; API keys are not exposed; repo README explains setup; implementation evidence and limitations are honest; required PDF and three Round 3 improvements are prepared.
