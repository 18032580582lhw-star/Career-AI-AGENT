# Task 6 Follow-up: Structured Host Package Render-ready Fix

## Blocker

The public Tailoring/render flow had one remaining real blocker:

- `prepare` created request/context artifacts.
- `tailor --host-proposal` accepted generic `ResumeTailoringProposal` JSON and persisted only `proposal.json` plus `validation.json`.
- `render` requires a structured proposal, `draft.json`, and `candidate-facts.json`.

Result: a generic accepted host proposal could be valid for validation, but still not render-ready.

## Fix

- Added `HostStructuredProposalPackage` as a public host package shape containing:
  - `draft: ResumeDocumentDraft`
  - `proposal: StructuredResumeTailoringProposal`
- Kept generic `ResumeTailoringProposal` behavior validation-only.
- Updated the `prepare` response schema to advertise both public host shapes via
  `HostProposalInput`:
  - `HostStructuredProposalPackage`
  - `ResumeTailoringProposal`
- Updated `validate_host_draft` to accept either generic proposals or structured packages.
- When a structured package is accepted, validation now persists:
  - `draft.json`
  - structured `proposal.json`
  - `validation.json`
  - trusted local `candidate-facts.json`
- Updated `prepare` to persist `candidate-facts.json` from the local generation context.
- Moved the document acceptance gate into validation for accepted structured
  packages. Invalid structured drafts now fail before render-ready artifacts are
  persisted.
- Updated the resume-tailor Skill references to document two modes:
  - generic proposal = validation-only
  - structured package = render-ready only after accepted local validation

Trust boundary: candidate facts still come from the prepared local context, not from the host-authored package.

## Regression Test

Added `test_structured_host_package_makes_public_flow_render_ready` in `tests/test_host_structured_package_cli_render.py`.

The test drives the real public CLI path:

1. `prepare --output json`
2. write a structured host package
3. `tailor --host-proposal <package> --output json`
4. `render --format all --disable-latex-engines --output json`

Expected result:

- DOCX rendered
- HTML/PDF rendered
- TEX rendered
- LaTeX PDF reports `unavailable` with `latex_no_engine`

Security regressions:

- accepted proposal plus tampered draft fails validation before `draft.json` is persisted
- rejected structured package does not persist render-ready `draft.json`

## Verification

- `.venv\Scripts\python.exe -m pytest tests\test_host_structured_package_cli_render.py::test_structured_host_package_makes_public_flow_render_ready -q`
  - passed during focused development
- `.venv\Scripts\python.exe -m pytest tests\test_host_structured_package_cli_render.py -q`
  - `3 passed`
- `.venv\Scripts\python.exe -m pytest tests\test_host_proposal_cli.py tests\test_host_proposal_cli_render.py tests\test_host_structured_package_cli_render.py tests\test_application_service.py -q`
  - `11 passed`
- `.venv\Scripts\python.exe -m pytest -q`
  - `355 passed`
- `.venv\Scripts\ruff.exe check .`
  - passed
- `.venv\Scripts\basedpyright.exe`
  - `0 errors, 0 warnings, 0 notes`
- `git diff --check`
  - no whitespace errors; only existing CRLF normalization warnings for `.omo/boulder.json` and `.omo/start-work/ledger.jsonl`

## Result

The public host workflow now has a discoverable render-ready path when the host supplies a structured package. Generic host proposals remain accepted/rejected by validation only and still do not pretend to be render-ready.
