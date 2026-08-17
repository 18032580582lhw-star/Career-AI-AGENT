# Task 1 README Positioning Evidence

Observed and updated on 2026-08-17.

## Change

- `README.en.md` and `README.zh.md` now identify Codex/Claude Code (and a future
  DeepSeek Harness target) as Host Agents.
- The packaged Skill defines the workflow; the deterministic local Harness owns
  validation, confirmation, and rendering authority.
- Streamlit is described as an optional demonstration/manual-inspection UI, not
  as the product's autonomous agent.
- No CLI command or production behavior was changed in this documentation edit.

## Verification

- `git diff --check`: passed. Git emitted only existing CRLF normalization
  warnings for `.omo/boulder.json` and `.omo/start-work/ledger.jsonl`.
- Manual bilingual diff review: passed; both READMEs state the same ownership
  boundary and retain the existing command examples.
- Existing `tests/test_public_api.py` and `tests/test_cli.py` could not be run on
  this host: `.venv` is bound to a removed Python 3.13 installation. The bundled
  Codex Python can load pure-Python pytest files via `PYTHONPATH`, but cannot load
  the virtual environment's ABI-specific `pydantic_core` extension. This is an
  environment blocker, not a passing or failing behavior result.

## Adversarial and cleanup notes

- Dirty worktree: unrelated untracked drafts and plans were preserved.
- Misleading success: the unavailable regression suite is recorded as blocked,
  never converted to a pass.
- Prompt injection, malformed runtime input, stale run state, cancellation,
  hung commands, and repeated runtime interruption are not exercised by a README
  positioning change. The architecture contract records the relevant safety and
  continuation boundaries.
- No process, temporary directory, credential, network request, or artifact was
  created by the README work.
