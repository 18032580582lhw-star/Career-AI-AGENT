# Repository Policy

## Branches

- `main` is the only long-lived development branch and the GitHub default branch.
- Feature work uses short-lived branches merged into `main`; fully-merged branches are deleted
  locally and remotely after merge.
- Historical snapshots use an `archive/<name>` branch plus an immutable `<name>` tag, both created
  before any destructive tree change.

## Artifact retention

- Runtime package data (`src/career_ai/rendering/assets/fonts/`, packaged Skill files, prompts,
  renderer templates) is tracked and never removed outside an explicit product decision.
- User/runtime state under `.career_ai/`, `.venv/`, and build caches is ignored and must never be
  swept, archived, or treated as disposable.
- OMO process artifacts (`.omo/evidence/`, completed `.omo/plans/`, historical ledgers) leave
  `main` once a milestone is complete; they are preserved in an archive branch/tag first.
- `.omo/` planning state is kept out of the product repository once the active migration finishes.

## Rules

- Recoverability precedes deletion: create and verify archive refs before removing any tracked path.
- No force-push, history rewrite, filter-repo/BFG, or `git reset --hard` on published branches.
- Destructive steps use explicit allowlists and stop on divergence, missing archive refs, or hash
  mismatch.
