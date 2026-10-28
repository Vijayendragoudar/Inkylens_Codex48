# Codex Instructions — Inkylens

## Mission
Build Inkylens, a judge-ready AI-assisted brand-governance MVP for Round 2. Prioritize a functioning end-to-end workflow over feature count. Read `PROJECT_REQUIREMENTS.md` and `DEVELOPMENT_PLAN.md` before making changes.

## Critical starting instruction
**Begin at Phase 1: Requirements Engineering.** Review and refine the SRS, ask only essential clarifying questions, and obtain user approval before creating application source code. Do not skip ahead to scaffolding or implementation.

## Working style
- The developer works solo and wants slow, detailed guidance, **one file at a time**.
- For each file: state path, purpose, full content or focused patch, how to run/test it, expected result, and next step.
- Do not make large batches of unreviewed files. Obtain confirmation at phase gates.
- Keep a running implementation checklist with statuses: `planned`, `in progress`, `implemented`, `tested`, `deployed`.
- Never represent planned functionality as working, tested or deployed.
- Prefer simple, maintainable solutions and minimize dependencies.

## Engineering rules
- Treat organisation guidelines as the only authoritative source for brand-specific rules; AI must not invent brand policy.
- Label uncertain factual/promotional claims as **unsupported/unverified**, not necessarily false.
- Provide explainable, rule-linked findings and human override/review.
- Keep AI credentials in backend environment variables; never commit secrets or leak them to frontend.
- Validate request and LLM output schemas; handle malformed AI output, network failure and rate limits.
- Test the deterministic rule engine independently from the LLM.
- Do not silently send sensitive customer content to external services; document provider and disclosure.
- Use clear README instructions, `.env.example` placeholders, and `.gitignore` when implementation starts.
- Commit in small meaningful increments; disclose significant AI assistance, templates, external services and licenses in submissions.

## Mandatory milestone response format
1. Current phase and exact task.
2. Decisions/requirements under review.
3. One concrete deliverable or file change (only when authorized).
4. Verification steps and observed result (distinguish actual tests from proposed tests).
5. Explicit question asking whether to proceed to next task.

## Event integrity
Development must respect the official build window. Confirm it before coding. Do not fabricate research, metrics, interviews, demos, deployment, commits, or completed features. Ensure submission statements match repository and deployed behavior.
