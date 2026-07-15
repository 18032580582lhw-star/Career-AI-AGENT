# Task 3 Evidence - CLI Happy Path

## Scope

Plan: `.omo/plans/debug-stabilization.md`

Task: `3. Local CLI Harness Debug`

Scenario: CLI happy path

## Environment

Temp venv:

```text
$env:TEMP\career-agent-cli-20260715-1202\.venv
```

Setup:

```powershell
python -m venv $cliVenv
& $cliPython -m pip install --upgrade pip
& $cliPython -m pip install -e .
```

Non-fatal stderr during venv creation:

```text
Actual environment location may have moved due to redirects, links or junctions.
Requested location: "C:\Users\SHERLO~1\AppData\Local\Temp\career-agent-cli-20260715-1202\.venv\Scripts\python.exe"
Actual location:    "C:\Users\Sherlock Lee\AppData\Local\Temp\career-agent-cli-20260715-1202\.venv\Scripts\python.exe"
```

## Commands And Results

### doctor

Command:

```powershell
& $cliExe doctor
```

Exit code: `0`

Key stdout:

```text
Provider: fake
Model: local-fake
HTML renderer: available
Workspace: PASS
Tectonic: FAIL
XeLaTeX: FAIL
Skill version: PASS
```

### analyze

Command:

```powershell
& $cliExe analyze --resume-text "Product analyst using Python SQL Streamlit dashboards." --jd-text "Role: AI Product Analyst. Requires Python, SQL, Streamlit, LLM evaluation."
```

Exit code: `0`

Key stdout:

```text
Mode: deterministic fallback
Role: AI Product Analyst. Requires Python, SQL, Streamlit, LLM evaluation.
Match score: 57
Quality: PASS
Trace: ce54e829-1d22-44f9-a957-e2c3e4c37c6c
Failed checks: none
```

### eval

Command:

```powershell
& $cliExe eval --case-dir evals\career_cases --prompt-dir prompts
```

Exit code: `0`

Key stdout:

```text
Total cases: 3
Passed cases: 3
Failed cases: 0
- sample_product_analyst: PASS
```

### eval-matrix

Command:

```powershell
& $cliExe eval-matrix --case-dir evals\career_cases --prompt-dir prompts
```

Exit code: `0`

Key stdout:

```text
Total rows: 1
Passed rows: 1
Failed rows: 0
Unsupported capabilities: 0
- fake-default: fake/local-fake status=passed passed=3 failed=0
```

## Interpretation

The installed CLI public surface works in a clean temp venv with the fake provider baseline. Optional LaTeX engines are not present, and `doctor` reports that honestly.

## Cleanup

```text
CLI_ROOT_EXISTS_AFTER_CLEANUP=False
```

## Adversarial Classes

- Malformed input: deferred to Task 5 bad eval boundary.
- Prompt injection: not applicable; deterministic fake provider and fixed sample text.
- Cancel/resume: Boulder and ledger active.
- Stale state: temp venv installed current local checkout.
- Dirty worktree: no repo-local `.venv` used.
- Hung or long commands: bounded timeout completed.
- Flaky tests: eval/eval-matrix each passed once.
- Misleading success output: exit codes and key stdout captured; a possible zero-case eval issue is deferred to Task 5.
- Repeated interruptions: evidence file and ledger provide restart anchor.
