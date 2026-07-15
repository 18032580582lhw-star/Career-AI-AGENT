# Task 8 Evidence - Packaging Wheel

## Scope

Plan: `.omo/plans/debug-stabilization.md`

Task: `8. Packaging Release Debug`

Scenario: wheel contains runtime assets

## Commands

```powershell
python -m pip wheel . --no-deps --wheel-dir $wheelhouse
python inspect_wheel.py $wheel
python -m venv $wheelVenv
& $wheelPython -m pip install $wheel.FullName
& $wheelCli --help
```

## Result

Wheel build key output:

```text
Processing f:\agent
Created wheel for ai-career-intelligence-suite: filename=ai_career_intelligence_suite-0.1.0-py3-none-any.whl size=18451260
Successfully built ai-career-intelligence-suite
```

Wheel content inspection:

```text
career_ai/skills/career_resume_tailor/SKILL.md=PRESENT
career_ai/skills/career_resume_tailor/references/workflow.md=PRESENT
career_ai/rendering/latex/assets/system_resume.tex=PRESENT
career_ai/rendering/assets/fonts/NotoSans-Regular.woff2=PRESENT
entrypoint=True
```

Wheel install key output:

```text
Successfully installed MarkupSafe-3.0.3 ai-career-intelligence-suite-0.1.0 ... websockets-16.1
WHEEL_CLI_EXISTS=True
```

CLI help key output:

```text
Usage: career-ai-agent [OPTIONS] COMMAND [ARGS]...
Local model-neutral Career Agent.
```

## Interpretation

The wheel carries the CLI entrypoint, Skill files, workflow reference, system LaTeX template, and Noto font assets. Installing the built wheel into a temp venv exposes `career-ai-agent`.

## Cleanup

```text
PKG_ROOT_EXISTS_AFTER_CLEANUP=False
```

## Adversarial Classes

- Malformed input: not applicable to packaging happy path.
- Prompt injection: not applicable.
- Cancel/resume: Boulder and ledger active.
- Stale state: wheel built from current workspace; raw surface separately verifies GitHub `main`.
- Dirty worktree: wheelhouse was outside repo under temp.
- Hung or long commands: bounded timeout completed.
- Flaky tests: not a test suite; deterministic wheel inspection used.
- Misleading success output: inspected wheel contents and CLI existence rather than trusting pip success alone.
- Repeated interruptions: evidence captures exact artifacts and cleanup.
