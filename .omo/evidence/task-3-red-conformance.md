# Task 3 RED conformance evidence

- Baseline command attempted: `.venv\Scripts\python.exe -m pytest tests\test_host_proposal_cli.py tests\test_host_structured_package_cli_render.py -q`
- Baseline execution blocker: the relocated virtual environment still points at the missing interpreter `C:\Users\Sherlock Lee\AppData\Local\Programs\Python\Python313\python.exe`, so Windows reports `Unable to create process`.
- Static baseline observable: `HostValidationResult` currently exposes only `run_id`, `source`, `state`, `proposal_hash`, and `validation_hash` in `src/career_ai/tailoring/host_run_models.py`.
- Intended RED observable: each case parses CLI JSON through `ValidationEnvelope`, which additionally requires `validation_artifact`, `finding_count`, `finding_codes`, and `next_machine_instruction`. The current response therefore fails schema validation before the render assertions.
- Case coverage: accepted structured output, confirmation-required inference, unsupported-claim rejection, and stale/tampered source binding.
- Dynamic identity: case JSON contains no run IDs, hashes, or absolute paths; tests bind values after `prepare` inside isolated temporary workspaces.
- Static QA: Ruff passes; Python syntax compilation passes with the Codex bundled Python. Runtime pytest and BasedPyright remain blocked by the missing Python 3.13 interpreter used by `.venv` and its CPython 3.13 extension packages.
