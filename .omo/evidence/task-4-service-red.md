# Task 4 application service RED evidence

## Baseline characterization

Command:

```powershell
F:\AGENT\.tmp-task4-venv\Scripts\python.exe -m pytest tests/test_agent_quality.py tests/test_agent_trace.py -q -p no:cacheprovider
```

Result: `10 passed in 1.34s`.

This confirms the pre-migration deterministic quality and Agent trace behavior remained green before the Task 4 production migration.

## New contract RED

Command:

```powershell
F:\AGENT\.tmp-task4-venv\Scripts\python.exe -m pytest tests/test_workflow_quality.py tests/test_career_fit_service.py tests/test_workflow_run_record.py -q -p no:cacheprovider
```

Result: collection stopped with three expected errors:

- `ModuleNotFoundError: No module named 'career_ai.workflows.quality'`
- `ModuleNotFoundError: No module named 'career_ai.application.career_fit_service'`
- `ModuleNotFoundError: No module named 'career_ai.workflows.run_record'`

These failures are the intended RED boundary: deterministic quality, the application service, and the neutral privacy-safe run record do not exist yet. No production code or legacy tests were changed or removed by this subtask.
