# Task 1 boundary-test evidence

## Baseline

- `rg -n "career_ai\.agent|streamlit" src/career_ai/tailoring src/career_ai/workspace src/career_ai/rendering`
  returned no matches. The protected core layers were clean before the test file was added.
- The repository `.venv` launcher points to a removed Python 3.13 installation. Verification used
  Codex's bundled Python 3.12 with the existing `.venv` site-packages on `PYTHONPATH`; the environment
  was not rebuilt or changed.

## Automated verification

- Bundled Python + `pytest tests/test_architecture_boundaries.py -q --basetemp
  F:\AGENT\.tmp-task1-pytest -p no:cacheprovider`: `3 passed in 0.23s`.
- `.venv/Scripts/ruff.exe format --check tests/test_architecture_boundaries.py`: passed.
- `.venv/Scripts/ruff.exe check tests/test_architecture_boundaries.py`: passed.
- Bundled Python + `python -m basedpyright tests/test_architecture_boundaries.py`: `0 errors, 0
  warnings, 0 notes`. BasedPyright printed a non-fatal warning when probing the broken `.venv`
  interpreter, then completed successfully.
- `check-no-excuse-rules.py tests/test_architecture_boundaries.py`: no violations.

## Adversarial proof and cleanup

- The synthetic test creates a protected module importing `streamlit` and asserts that the scanner
  reports its exact file, line, and dependency. This rules out a misleading always-success scanner.
- Files are enumerated and sorted, and the test uses pytest's isolated `tmp_path`; there is no clock,
  network, or ordering dependency.
- The explicit pytest base-temp directory was resolved under `F:\AGENT` and removed after the run.
  No process or temporary artifact remains.
- Existing unrelated dirty-worktree files were not modified.
