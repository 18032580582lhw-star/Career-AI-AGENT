# Task 4 — Deterministic application service

## Outcome

- `CareerFitApplicationService` is the shared deterministic entrypoint for `analyze` and evals.
- Deterministic quality, factual-boundary, and privacy-safe run-record contracts live under `workflows`.
- `cli.py`, `evals/runner.py`, and `evals/failure_corpus.py` have no `career_ai.agent` or `career_ai.llm` imports.
- The old Agent quality/trace/boundary tests were removed only after replacement RED tests existed and passed.

## TDD evidence

- Existing quality/trace baseline: `10 passed in 1.34s`.
- Unchanged legacy subset baseline: `26 passed in 6.39s`.
- Service RED: three collection failures for the missing service, quality, and run-record modules.
- Eval RED: `2 failed, 1 passed`; failures were the required `llm_client` argument and forbidden Agent/LLM imports.
- GREEN focused Task 4 privacy/service suite after review hardening: `37 passed`.

## Verification

- Full suite excluding network-isolated wheel build: `367 passed in 19.75s`.
- Final wheel packaging smoke with network permission: `1 passed in 20.68s`.
- Focused Ruff: all checks passed (repository copyright rule excluded consistently with prior task evidence).
- Focused BasedPyright with the temporary Python 3.12 interpreter: `0 errors, 0 warnings, 0 notes`.
- `git diff --check`: passed; only pre-existing line-ending notices were printed.
- New module line counts: service 67, provider status 31, quality 137, run record 50, factual boundary 234.

## Manual CLI QA

- Human `analyze`: role, score, best prompt, quality, audit ID, workflow steps, and failed checks rendered successfully.
- JSON `analyze`: validated as the complete typed `CareerFitRunResult`; no original input body or absolute path.
- `eval`: 3 total, 3 passed, 0 failed.

## Post-implementation review

- Initial review found three real blockers: reduced JSON schema, partial `Role:` disclosure, and incomplete failure-record sanitization.
- Fixes retain the complete `CareerFitRunResult` schema while redacting source-derived free-text bodies, normalize role titles, sanitize every string-bearing failure field, re-sanitize disk-loaded records before conversion, and prevent deterministic CLI startup from eagerly loading Agent/LLM namespaces.
- Five review lanes passed after the fixes: goal contract, hands-on QA, code quality, security/privacy, and repository context.

## Adversarial classes

1. Malformed input: factual-boundary invalid JSON remains rejected with `invalid_json`.
2. Prompt injection/unsupported claims: invented facts remain rejected by the unchanged boundary rules.
3. Cancel/resume: active Boulder plan and RED evidence preserve the restart point.
4. Stale state: failure conversion requires an explicit accepted review state.
5. Dirty worktree: unrelated Task 1–3 and user draft changes were preserved.
6. Hung command: the slow dependency install was polled to completion; no process remains.
7. Flaky behavior: workflow and quality outputs are deterministic; only opaque audit IDs vary.
8. Misleading success: packaging was reported separately after its network-isolated test actually passed.
9. Repeated interruptions: service/eval RED work was independently recorded before implementation.

## Cleanup receipt

- Removed all `F:\AGENT\.tmp-task4-*` verification environments and basetemps.
- The elevated packaging basetemp required and received separate removal permission.
- Preserved the original broken `.venv`; no credentials, services, or external resources remain.
