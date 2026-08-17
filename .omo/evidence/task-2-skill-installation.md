# Task 2 Skill and installation evidence

## Result

- Canonical `SKILL.md` has only `name` and `description` frontmatter, a concise
  authority rule, five workflow steps, stop conditions, and four direct references.
- `agents/openai.yaml` uses the accepted `interface` metadata shape.
- Supported selectors are exactly `codex`, `claude`, and `all`.
- Codex installs at `.agents/skills/career-resume-tailor`; Claude installs at
  `.claude/skills/career-resume-tailor`. OpenCode and Claude plugin paths are absent.
- Installation records use `format: agent-skill`, host, target, status, and bundle hash.
- Both standalone installers consume and verify the machine-readable two-host result.

## Verification

- Temporary clean Python 3.12 environment: `pytest tests/test_skill_init.py
  tests/test_packaging_smoke.py -q`: `8 passed in 28.80s`.
- BasedPyright with the temporary interpreter: `0 errors, 0 warnings, 0 notes`.
- Repository Ruff version on the focused files: passed.
- `check-no-excuse-rules.py`: no violations.
- Official Skill Creator `quick_validate.py`: `Skill is valid!`.
- PowerShell parser and Git Bash `bash -n`: passed (see installer evidence).
- Manual `career-ai-agent init --workspace <temp> --agent all`: exactly two
  `agent-skill` results; Codex and Claude hashes were identical.
- Stale-path scan and `git diff --check`: passed.

## Adversarial and cleanup

- Tests cover repeated initialization, differing user-owned files for both hosts,
  exact persisted-record equality, extra/legacy host rejection, and wheel discovery.
- Install scripts fail closed on malformed JSON, wrong host count, or unexpected targets.
- No DeepSeek path or host-specific duplicate Skill was added.
- The original broken `.venv` was not changed. The temporary Python environment,
  wheel/pytest directories, and install-smoke workspace were removed. An elevated
  pytest directory required elevated cleanup because it inherited elevated ownership;
  removal was verified.
