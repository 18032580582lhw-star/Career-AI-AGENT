# Task 2 Evidence - GitHub Raw Install, Git Bash

## Scope

Plan: `.omo/plans/debug-stabilization.md`

Task: `2. GitHub Raw Install Debug`

Scenario: Git Bash raw install

## Command

```powershell
Start-Process -FilePath "C:\Program Files\Git\bin\bash.exe" -ArgumentList @($runnerForBash) -Wait -PassThru -RedirectStandardOutput stdout.txt -RedirectStandardError stderr.txt
```

The BOM-free Git Bash runner executed `curl` inside Bash:

```bash
curl -fsSL 'https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.sh' -o "$root/install-agent.sh"
bash "$root/install-agent.sh" --repo-url 'https://github.com/18032580582lhw-star/Career-AI-AGENT.git' --install-root "$root" --agent all
```

## Environment

```text
BASH_PATH=/usr/bin/bash
PYTHON_COMMAND=/c/Users/Sherlock Lee/AppData/Local/Programs/Python/Python313/python
PYTHON_VERSION=Python 3.13.7
PYTHON3_COMMAND=/c/Users/Sherlock Lee/AppData/Local/Microsoft/WindowsApps/python3
PYTHON3_EXIT=49
```

## Result

Exit code: `0`

Key stdout:

```text
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
Project: /tmp/career-agent-raw-bash-20260715-1148/Career-AI-AGENT
Python 3.13.7
```

Key stderr:

```text
Cloning into 'C:/Users/SHERLO~1/AppData/Local/Temp/career-agent-raw-bash-20260715-1148/Career-AI-AGENT'...
Actual environment location may have moved due to redirects, links or junctions.
  Requested location: "C:\Users\SHERLO~1\AppData\Local\Temp\career-agent-raw-bash-20260715-1148\Career-AI-AGENT\.venv\Scripts\python.exe"
  Actual location:    "C:\Users\Sherlock Lee\AppData\Local\Temp\career-agent-raw-bash-20260715-1148\Career-AI-AGENT\.venv\Scripts\python.exe"
```

Interpretation: Git Bash raw installer skipped the unusable WindowsApps `python3` candidate, selected working Python 3.13.7, and completed the full install/eval flow. The venv path notice is non-fatal; the script exited `0`.

## Cleanup

```text
BASH_ROOT_EXISTS_AFTER_CLEANUP=False
```

## Adversarial Classes

- Malformed input: not exercised in this scenario; Task 2 focuses on documented happy path install.
- Prompt injection: not applicable; no LLM prompt path.
- Cancel/resume: Boulder and ledger already active from Task 1.
- Stale state: raw URL came from GitHub `main`, not local script files.
- Dirty worktree: install ran in `%TEMP%`, not the repo workspace.
- Hung or long commands: runner used a bounded command timeout and completed.
- Flaky tests: eval and eval-matrix ran once successfully.
- Misleading success output: evidence includes exit code plus key stdout/stderr, including non-fatal stderr.
- Repeated interruptions: temp root and evidence path are sufficient to resume or rerun.
