# Task 1 Evidence - Debug Evidence Harness

## Scope

Plan: `.omo/plans/debug-stabilization.md`

Task: `1. Debug Evidence Harness`

Goal: Establish a reusable evidence format, temp root naming convention, command capture rules, and cleanup checklist for the debug stabilization campaign.

## Evidence Format

Each task evidence file must record:

- `Command`: exact command or script invocation.
- `Cwd`: working directory.
- `Environment`: shell/runtime versions relevant to the task.
- `Exit code`: exact process exit code where available.
- `Key stdout`: trimmed lines proving the expected behavior.
- `Key stderr`: trimmed lines proving failures, warnings, or explicitly empty stderr.
- `Interpretation`: why the observed output proves or refutes the task.
- `Cleanup`: temp paths, processes, ports, and files removed or intentionally retained.
- `Adversarial classes`: applicable ultraqa classes with observed result, and non-applicable classes with one-line reason.

## Temp Root Naming

Use temp directories outside the repository:

```text
$env:TEMP\career-agent-<task-slug>-<YYYYMMDD-HHmm>
```

Examples:

```text
$env:TEMP\career-agent-raw-install-20260715-1200
$env:TEMP\career-agent-streamlit-20260715-1230
```

## Command Capture Rules

- Windows PowerShell installer regression coverage must use Windows PowerShell 5.1.
- Git Bash regression coverage must use a verified Git Bash path such as `C:\Program Files\Git\bin\bash.exe`, not `C:\Windows\system32\bash.exe`.
- For commands that emit normal stderr, capture stdout/stderr to files through `Start-Process` when PowerShell 5.1 native stderr handling could contaminate results.
- Evidence must include key stdout/stderr lines, not only “passed”.
- If a bug is found, create `.debug-journal.md`, add it to `.git/info/exclude`, and remove both before completion.

## Cleanup Checklist

For each task:

- Remove temp install/workspace directories.
- Stop background processes and verify ports are free.
- Remove downloaded scripts, runner files, screenshots, or traces unless promoted into `.omo/evidence/`.
- Confirm `git status -sb` contains only intended tracked or evidence changes.

## QA Scenario 1 - Happy Path Evidence Template

Command:

```powershell
git status -sb
```

Cwd:

```text
F:\AGENT
```

Environment:

```text
Timestamp: 2026-07-15T11:46:32.0421425+08:00
PowerShell: 5.1.26100.8655
Python: Python 3.13.7
```

Exit code: `0`

Key stdout:

```text
## codex/harness-first-roadmap...origin/main
 M .omo/boulder.json
 M .omo/start-work/ledger.jsonl
?? .omo/plans/debug-stabilization.md
```

Interpretation: Evidence capture includes command, cwd, environment, exit code, stdout, and status context.

## QA Scenario 2 - Cleanup Checklist Prevents Artifact Leakage

Command:

```powershell
$tmp = Join-Path $env:TEMP 'career-agent-evidence-harness-probe'
Remove-Item -Recurse -Force -LiteralPath $tmp -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $tmp | Out-Null
$existsBeforeCleanup = Test-Path -LiteralPath $tmp
Remove-Item -Recurse -Force -LiteralPath $tmp
$existsAfterCleanup = Test-Path -LiteralPath $tmp
```

Exit code: `0`

Observed:

```text
TEMP_PATH=C:\Users\SHERLO~1\AppData\Local\Temp\career-agent-evidence-harness-probe
EXISTS_BEFORE_CLEANUP=True
EXISTS_AFTER_CLEANUP=False
```

Interpretation: The task’s temp artifact was created, removed, and verified absent.

## Adversarial Classes

- Malformed input: not applicable; this task defines evidence protocol, no parser is under test.
- Prompt injection: not applicable; no LLM or prompt input used.
- Cancel/resume: applicable; Boulder state and ledger were initialized before task execution, allowing continuation.
- Stale state: applicable; `git status -sb` captured current branch and existing planned changes.
- Dirty worktree: applicable; evidence notes current intended `.omo` changes.
- Hung or long commands: applicable; all commands used short timeouts and completed.
- Flaky tests: not applicable; no test suite invoked in Task 1.
- Misleading success output: applicable; evidence requires exit code plus key stdout/stderr, not prose-only success.
- Repeated interruptions: applicable; evidence path and ledger provide restart anchors.

## Cleanup Receipt

- Temp directory removed: `C:\Users\SHERLO~1\AppData\Local\Temp\career-agent-evidence-harness-probe`
- Cleanup verification: `EXISTS_AFTER_CLEANUP=False`
