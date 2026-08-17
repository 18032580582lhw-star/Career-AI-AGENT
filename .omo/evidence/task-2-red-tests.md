# Task 2 red-test evidence

## Scope

- Changed only `tests/test_skill_init.py` and `tests/test_packaging_smoke.py`.
- Production code, packaged Skill files, installers, documentation, and work state were not changed.

## Expected contract failures against current production

1. `SKILL.md` has no YAML frontmatter with exactly `name` and `description`.
2. `agents/openai.yaml` still contains the custom `protocol` and `commands` fields.
3. `HostAgent` still exposes `opencode`.
4. `init --agent all` still returns three installations.
5. Claude still installs under `.claude/plugins/` rather than `.claude/skills/`.
6. Installation metadata still exposes `protocol` and `template`, not `format: agent-skill`.

## Verification

- `ruff check tests/test_skill_init.py tests/test_packaging_smoke.py`: PASS.
- Pytest collection with bundled Python and the existing `.venv` site-packages: BLOCKED before tests by `ModuleNotFoundError: pydantic_core._pydantic_core` (ABI-dependent extension unavailable).
- BasedPyright launcher: BLOCKED because it delegates to the broken `.venv/Scripts/python.exe`.

The contract is intentionally RED against the inspected current implementation. The environment failure is separate from those source-level mismatches.
