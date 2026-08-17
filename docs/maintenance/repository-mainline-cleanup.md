# Repository Mainline Cleanup — Receipt and Recovery Index

> Durable record of the 2026-08-17 slim-main cleanup. Historical task evidence and completed
> plans are preserved in Git refs, not in the active tree.

## Summary

The repository was reduced to one canonical development branch (`main`) plus one archive branch
and one immutable pre-cleanup tag. Historical OMO process artifacts and old worklogs left `main`
only after being preserved in recoverable Git refs. The fully-merged `codex/harness-first-roadmap`
feature branch was deleted locally and remotely.

## Ref record

| Ref | State |
|---|---|
| `HEAD` / `main` / `origin/main` (before) | `9e372508e086987f8bf15b5c5a37f5e09bc99240` |
| `HEAD` / `main` / `origin/main` (after) | `6ca63914fd45e2c428d1920adecc85b085402ead` |
| `pre-slim-main-2026-08-17` (annotated tag) | peels to `9e372508e086987f8bf15b5c5a37f5e09bc99240` |
| `archive/pre-slim-main-2026-08-17` (branch) | tip `168ad77f5b75a636d8e1f7963e84fddae76e0f96` (includes `archive/personal-plans/`) |
| `codex/harness-first-roadmap` | deleted (was fully merged at `9e37250`) |

Preconditions verified before any mutation: all four development refs equal; `git branch
--no-merged main` empty; single worktree; no pre-existing tags.

## Archive refs

- Immutable tag: `pre-slim-main-2026-08-17` → `9e37250...` (full pre-cleanup tree).
- Browsable branch: `archive/pre-slim-main-2026-08-17` → `168ad77...`.
- Personal plans: `archive/personal-plans/` — three files plus `MANIFEST.md` with SHA-256 hashes.

## Removed from `main` (allowlist)

- `.omo/evidence/**` (62 tracked files) — historical task verification evidence.
- `.omo/plans/debug-stabilization.md` — completed plan.
- `.omo/plans/high-trust-resume-skill-latex.md` — completed plan.
- `.omo/start-work/ledger.jsonl` — historical contents replaced by one compact checkpoint record.
- `docs/worklogs/2026-07-08_*` through `2026-07-15_*` (8 files) — historical worklogs.

## Kept on `main`

- `.omo/boulder.json`
- `.omo/plans/skill-first-harness-core-migration.md` (active plan)
- `.omo/start-work/ledger.jsonl` (compact checkpoint naming Task 5 as next work)
- `docs/worklogs/2026-08-17_*` (current worklog)
- All product source, tests, eval fixtures, fonts, prompts, static assets, and package data.

## Recovery / rollback

```bash
# Recreate the deleted feature branch
git branch codex/harness-first-roadmap pre-slim-main-2026-08-17
git push origin codex/harness-first-roadmap

# Restore any archived file to main (no history rewrite)
git restore --source archive/pre-slim-main-2026-08-17 -- <path>
git commit -m "restore: <path> from pre-slim-main archive"

# Revert the slim-main cleanup (never reset/force-push published main)
git revert <cleanup-commit-sha>   # find via: git log --oneline -3

# Recover personal plans and verify against their manifest
git restore --source archive/pre-slim-main-2026-08-17 -- archive/personal-plans/
```

## Verification results (2026-08-17)

- `python -m pytest -q` → 368 passed (includes packaging smoke).
- `python -m ruff check .` → 3 pre-existing errors: RUF100 in `src/career_ai/host_proposal_cli.py`
  and 2× I001 import order in `tests/test_llm_client.py` and `tests/test_workflow_factual_boundary.py`.
  These exist in the pre-cleanup baseline `9e37250`, are surfaced by the current ruff 0.15.20, and are
  unrelated to this cleanup (no `.py` file was modified; see scope fidelity below).
- `python -m basedpyright` → 0 errors, 0 warnings, 0 notes.
- `career-ai-agent doctor` → HTML renderer, Skill, and no-API checks PASS; Tectonic/XeLaTeX FAIL (no LaTeX engine installed).
- `career-ai-agent eval` → 3 passed, 0 failed.
- `career-ai-agent analyze --output json` → valid `CareerFitRunResult` JSON (workflow/quality/run_record).
- `git diff --check` → clean.
- Wheel contents → no `.omo`/worklog/evidence entries; fonts and Skill assets present.

## Scope fidelity

`git diff --name-status 9e37250 HEAD` touches only the allowlisted paths: `.omo/evidence/**`, the two
completed `.omo/plans/`, the historical ledger, eight old worklogs, the two READMEs, the active
migration plan, and the two new `docs/maintenance/` files. No `.py`, `.toml`, `src/`, `tests/`,
font, `.career_ai/`, or `.venv/` path was modified — source and tests are byte-identical to `9e37250`.

## Re-run gates

```powershell
python -m pytest
ruff check .
basedpyright
career-ai-agent doctor
career-ai-agent eval --case-dir evals/career_cases --prompt-dir prompts
git diff --check
```

See `docs/maintenance/repository-policy.md` for branch and artifact retention rules.
