# Inkylens — Phased Development Plan

**Current stage:** Phase 1, not yet signed off. **Implementation status:** not started.

## Phase 1 — Requirements Engineering (start here)
1.1 Confirm event constraints, build window and submission deadline.
1.2 Review problem, stakeholders, users and Round 1 commitments.
1.3 Finalize functional and non-functional requirements and MVP boundaries.
1.4 Specify user stories, detailed acceptance tests and failure cases.
1.5 Approve SRS before any app code is created.
**Exit gate:** user signs off on `PROJECT_REQUIREMENTS.md`.

## Phase 2 — Architecture and Technical Design
Choose architecture, hosting assumptions, DB, LLM provider, privacy posture, guideline schema, review data model, API endpoints and error behavior.
**Exit gate:** agreed architecture/data flow and API contract.

## Phase 3 — UX and Interaction Design
Map screens and judge journey: demo landing, brand setup, content submission, findings, revision/history and review decision. Design empty/loading/error states.
**Exit gate:** approved wireframes and user flow.

## Phase 4 — Backend and Persistence Foundation
Create minimal backend one file at a time; implement guideline storage, content/review persistence, validation and tests. Establish migration/setup process.
**Exit gate:** repeatable API tests and persistent records.

## Phase 5 — Governance Analysis Engine
Implement deterministic terminology rules; integrate backend LLM for structured tone, messaging and unsupported-claim analysis; ground explanations in brand rules; test failures.
**Exit gate:** reproducible rules, real AI integration, error handling and test cases.

## Phase 6 — Frontend and End-to-End Integration
Build UI incrementally and wire to backend. Ensure full journey from guidelines to review, revision and history works.
**Exit gate:** complete core workflow on local environment.

## Phase 7 — Testing and Reliability
Run unit, API and end-to-end smoke tests; check edge cases, secrets, privacy notices, usability and accessibility. Capture evidence of actual results.
**Exit gate:** known issues documented and blocking defects fixed.

## Phase 8 — Deployment and Judge Readiness
Deploy frontend, backend and database; set environment variables; seed safe sample data; verify from fresh browser/device; add README and demo instructions.
**Exit gate:** public working URL and repository URL, tested without developer help.

## Phase 9 — Round 2 Submission
Create updated PDF; completed-feature evidence; stack and implementation details; honest Round 1 changes; three substantive Round 3 improvements; source/reuse/AI disclosures.
**Exit gate:** submission checklist fully verified.

## Suggested MVP priority
**Must:** editable guidelines, pasted-text review, deterministic checks, AI-assisted analysis, referenced findings, suggestions, revision/history, human decisions, demo usability.
**Should:** limited accessibility text checks, basic analytics if time permits.
**Defer:** image/logo checks, full multi-user collaboration, external publishing integrations and advanced analytics.

## Phase tracking
| Phase | Status |
|---|---|
| 1 Requirements | In progress (draft prepared, awaiting review) |
| 2 Architecture | Planned |
| 3 UX | Planned |
| 4 Backend | Planned |
| 5 AI engine | Planned |
| 6 Integration | Planned |
| 7 Testing | Planned |
| 8 Deployment | Planned |
| 9 Submission | Planned |

**Important:** This plan describes future tasks, not completed development.
