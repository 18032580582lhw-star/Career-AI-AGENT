# Task 3 host protocol and conformance evidence

## Result

- `HostValidationResult` now reports a relative validation artifact, finding count,
  stable finding codes, and the next machine instruction.
- Four checked-in descriptors cover accepted structured, needs-confirmation,
  rejected prompt-injection/unsupported-claim, and stale/tampered proposals.
- Case execution binds run IDs and hashes at runtime in isolated workspaces.
- Render items contain artifacts plus manifests when rendered, or a typed code when
  failed, unavailable, or stale. A Playwright `OSError` is converted to
  `renderer_output_failed` instead of escaping the CLI.

## TDD and automated verification

- RED: `tests/test_host_skill_conformance.py` initially produced four failures for
  missing `validation_artifact`, `finding_count`, `finding_codes`, and
  `next_machine_instruction`; the run-isolation test passed.
- GREEN: conformance suite `5 passed`.
- Focused host/render regression: `26 passed`.
- Full suite without network permission: `364 passed`, with only the isolated wheel
  build blocked by package-index access.
- The packaging test rerun with network permission: `1 passed`. Combined repository
  result: all 365 tests passed.
- Repository Ruff: passed. BasedPyright: `0 errors, 0 warnings, 0 notes`.
- Python no-excuse audit: no violations. `git diff --check`: passed.

## Manual CLI QA

An accepted structured proposal was prepared in a temporary workspace and driven
through the real `career-ai-agent` executable:

- `validate-draft --output json` returned `state=accepted`, a relative
  `.career_ai/runs/<run-id>/validation.json`, zero findings, and a render instruction.
- `render --format all --disable-latex-engines --output json` returned DOCX and TeX
  artifacts with relative manifest paths, PDF as typed `renderer_output_failed`, and
  LaTeX PDF as typed `latex_no_engine`. No absolute path leaked in machine output.

## Adversarial classes and cleanup

- Malformed input: existing strict-JSON fenced-input regression passed.
- Prompt injection: the unsupported case embeds an instruction to ignore validation
  and render immediately; it remains proposal data and is rejected.
- Cancel/resume: plan, Boulder, ledger, static descriptors, and runtime-generated IDs
  allow continuation without reusing run state.
- Stale state: tampered hashes produce `stale` and no rendered directory.
- Dirty worktree: unrelated user drafts/plans remain untouched.
- Hung/long commands: bounded test and installer commands completed; no service started.
- Flaky tests: descriptors contain no dynamic IDs/hashes and workspaces are isolated.
- Misleading success: missing Playwright and LaTeX engines are typed non-success items.
- Repeated interruptions: every prepare creates a distinct run directory; the ledger
  retained the active Task 3 state across turns.
- All `.tmp-task3-*` environments, pytest directories, and manual workspaces were
  deleted. The elevated packaging directory required and received elevated cleanup.
