# Archive Manifest — Personal Plans

These files are the user's personal planning artifacts, preserved verbatim from the
pre-slim-main worktree on 2026-08-17. They are NOT product or runtime inputs and are
archived here only for recoverability; they were never part of the tracked repository.

Archive commit: `archive: preserve pre-cleanup personal plans`
Source snapshot: tag `pre-slim-main-2026-08-17` / commit `9e372508e086987f8bf15b5c5a37f5e09bc99240`

## Files

| Original path | Archived path | SHA-256 | Size (bytes) |
|---|---|---|---|
| `.omo/drafts/high-trust-debug-skill-distillation.md` | `omo/drafts/high-trust-debug-skill-distillation.md` | `2C4894C9AC9BEF6CCD884F82AA219D2DA05C59986BCD4794A55FB1B2200287BF` | 2135 |
| `.omo/plans/high-trust-debug-skill-distillation.md` | `omo/plans/high-trust-debug-skill-distillation.md` | `79DEABC739547DE362202CF3C698EB4260DBB6A59FB369B380B6F7B0752EDCA8` | 18504 |
| `.omo/plans/personal-reusable-skill-evolution.md` | `omo/plans/personal-reusable-skill-evolution.md` | `BEAD5B5460C2EE5D300A1375E9D95EA674658B87D2F6E4A5C6366783D48DA3E4` | 8404 |

## Recovery

```bash
git restore --source archive/pre-slim-main-2026-08-17 -- archive/personal-plans/
```

Recompute each file's SHA-256 and compare against the table above before restoring to the
main worktree. These files are not inputs to any build, test, or runtime path.
