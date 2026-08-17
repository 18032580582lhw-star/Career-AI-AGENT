# Task 2 installer evidence

## Scope

- Updated only `scripts/install-agent.ps1` and `scripts/install-agent.sh`.
- Both installers now invoke `init --agent all` and validate the machine-readable JSON before reporting success.
- Validation requires exactly one `codex` installation and one `claude` installation at the two project Skill discovery paths.
- Removed the installer-level single-host selector because these installers provision the complete supported host set.

## Static verification

- PowerShell parser: PASS.
- Git for Windows Bash `-n`: PASS.
- Stale `opencode`, `.claude/plugins`, `--agent NAME`, and `Codex/OpenCode` wording scan: PASS (no matches).
- `git diff --check -- scripts/install-agent.ps1 scripts/install-agent.sh`: PASS.

## Adversarial behavior

- Malformed JSON fails in `ConvertFrom-Json` or `json.load`.
- Missing, duplicate, extra, or renamed installation entries fail the exact-count and exact-host checks.
- Unexpected target paths fail before the installer prints its final success summary.
- No `jq` or new external dependency was added; the scripts use PowerShell JSON support or the already-created virtualenv Python.

## Cleanup

- No processes, temporary directories, or generated installation trees were created during static verification.
