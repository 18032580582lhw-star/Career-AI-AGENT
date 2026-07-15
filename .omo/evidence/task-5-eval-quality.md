# Task 5 Evidence - Eval And Quality

## Fix Summary
- Root cause: load_eval_cases() used Path.glob("*.json") directly, so missing or empty directories produced an empty list. un_eval_suite() and eval-matrix then summarized that empty suite as success.
- Fix: added typed EvalCaseLoadError for missing, non-directory, and empty case directories; CLI converts that typed error to exit 2 with a clear message.

## Deterministic Eval Pass
Command: career-ai-agent eval --case-dir evals\career_cases --prompt-dir prompts

`	ext
Total cases: 3
Passed cases: 3
Failed cases: 0
- business_analyst_gap: PASS
- career_content_writer_gap: PASS
- sample_product_analyst: PASS

`

Command: career-ai-agent eval-matrix --case-dir evals\career_cases --prompt-dir prompts

`	ext
Total rows: 1
Passed rows: 1
Failed rows: 0
Skipped rows: 0
Unsupported capabilities: 0
- fake-default: fake/local-fake status=passed passed=3 failed=0

`

## Regression Tests
Command: python -m pytest tests\test_eval_loader.py tests\test_cli.py -q

`	ext
................                                                         [100%]
16 passed in 7.24s

`

Command: python -m pytest -q

`	ext
........................................................................ [ 20%]
........................................................................ [ 40%]
........................................................................ [ 61%]
........................................................................ [ 81%]
................................................................         [100%]
352 passed in 47.42s

`

## failure-to-eval Smoke
Command: career-ai-agent failure-to-eval --record-file <accepted-fixture> --output-file <draft>

`	ext
Wrote eval draft: C:\Users\Sherlock 
Lee\AppData\Local\Temp\career-agent-eval-20260715-1215\eval-draft.json

`

- Draft exists: True
- Draft leaked local path: False
- Draft leaked credential: False

## Interpretation
The deterministic eval suite and model harness matrix still pass with the repository eval bank, while failure-to-eval converts an accepted sanitized candidate into a redacted draft.
