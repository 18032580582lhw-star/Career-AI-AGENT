# Task 2 Evidence - GitHub Raw Install, PowerShell

## Scope

Plan: `.omo/plans/debug-stabilization.md`

Task: `2. GitHub Raw Install Debug`

Scenario: PowerShell raw install

## Command

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $env:TEMP\career-agent-raw-ps-20260715-1148\runner.ps1
```

The runner downloaded:

```text
https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.ps1
```

and ran:

```powershell
.\install-agent.ps1 -RepoUrl "https://github.com/18032580582lhw-star/Career-AI-AGENT.git" -InstallRoot "$root" -Agent all
```

## Environment

```text
HOST_PS_VERSION=5.1.26100.8655
HOST_PYTHON_COMMAND=C:\Users\Sherlock Lee\AppData\Local\Programs\Python\Python313\python.exe
Python 3.13.7
```

## Result

Exit code: `0`

Key stdout:

```text
==> Preparing install root
==> Cloning repository
==> Creating virtual environment
==> Installing package
==> Running doctor
Provider: fake
Workspace: PASS
Skill version: PASS
==> Installing host Skill adapters
==> Running eval
Passed cases: 3
Failed cases: 0
==> Running eval-matrix
Failed rows: 0
- fake-default: fake/local-fake status=passed passed=3 failed=0
==> Installed
Python 3.13.7
```

Key stderr:

```text
Cloning into 'C:\Users\Sherlock Lee\AppData\Local\Temp\career-agent-raw-ps-20260715-1148\Career-AI-AGENT'...
Updating files: 100% (682/682), done.
```

Interpretation: Windows PowerShell 5.1 raw installer completed from GitHub with Python `>=3.12`, and normal Git stderr did not trigger a false failure.

## Cleanup

```text
PS_ROOT_EXISTS_AFTER_CLEANUP=False
```

## Adversarial Classes

- Malformed input: not exercised in this scenario; Task 2 focuses on documented happy path install.
- Prompt injection: not applicable; no LLM prompt path.
- Cancel/resume: Boulder and ledger already active from Task 1.
- Stale state: raw URL came from GitHub `main`, not local script files.
- Dirty worktree: install ran in `%TEMP%`, not the repo workspace.
- Hung or long commands: runner used a bounded command timeout and completed.
- Flaky tests: eval and eval-matrix ran once successfully.
- Misleading success output: evidence includes exit code plus key stdout/stderr.
- Repeated interruptions: temp root and evidence path are sufficient to resume or rerun.
