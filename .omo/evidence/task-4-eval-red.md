# Task 4 eval/failure/factual-boundary RED evidence

## Baseline

- Command: `.tmp-task4-venv\Scripts\python.exe -m pytest tests/test_boundary_harness.py -q`
- Result: `7 passed, 1 cache warning in 1.25s`.
- Independent parent baseline for unchanged legacy quality/trace/boundary/CLI tests:
  `26 passed, 1 cache warning in 6.39s`.
- Limitation: the temporary environment was not ready before `test_eval_runner.py` and
  `test_failure_corpus.py` were edited, so no pre-edit pass is claimed for those two files.

## RED contract

- Command: `.tmp-task4-venv\Scripts\python.exe -m pytest tests/test_workflow_factual_boundary.py tests/test_eval_runner.py tests/test_failure_corpus.py -q`
- Result: collection stopped on exactly the absent new production modules:
  `career_ai.workflows.factual_boundary` and `career_ai.workflows.run_record`.
- Command: `.tmp-task4-venv\Scripts\python.exe -m pytest tests/test_eval_runner.py -q`
- Result: `2 failed, 1 passed in 2.24s`.
  - `run_eval_suite` still requires the obsolete `llm_client` keyword.
  - `career_ai.evals.runner` still imports `career_ai.agent` / `career_ai.llm`.

These failures lock the intended migration seam rather than an assertion typo: the existing
factual-boundary behavior remains green in its legacy namespace, while the new workflow
namespace, neutral run record, and deterministic eval signature do not exist yet.

## Static test check

- Command: `.tmp-task4-venv\Scripts\ruff.exe check --ignore CPY001 tests/test_workflow_factual_boundary.py tests/test_eval_runner.py tests/test_failure_corpus.py`
- Result: `All checks passed!`.
- `CPY001` is ignored here because the repository's existing tests do not carry copyright
  headers; the Task 4 production verification command does not lint tests.
