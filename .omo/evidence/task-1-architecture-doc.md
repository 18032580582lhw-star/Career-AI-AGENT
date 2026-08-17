# Task 1 Architecture Baseline Evidence

Observed on 2026-08-17 before writing
`docs/architecture/skill-first-harness-core.md`.

## Current seams

- `src/career_ai/cli.py` registers `doctor`, `install-renderer`, `analyze`, `eval`,
  `eval-matrix`, and `failure-to-eval`, then attaches `init` and the host-proposal
  commands. It still imports `career_ai.agent`, `career_ai.llm`, and the
  model-harness matrix directly.
- `src/career_ai/application/tailoring_service.py` is the shared application seam
  for workspace initialization, prepare, validation, confirmation, provider-backed
  tailoring, rendering, LaTeX inspection, and run listing. It delegates state and
  artifact work to the tailoring, workspace, and rendering packages.
- `src/career_ai/skills/career_resume_tailor/SKILL.md` already defines the canonical
  host workflow as prepare, host proposal, validate, confirm/repair, and render. It
  states that the local CLI/Harness remains authoritative and names Codex, Claude
  Code, and OpenCode as neutral hosts.
- `docs/roadmaps/harness-first-roadmap.md` describes the earlier custom-agent and
  provider baseline, including `eval-matrix` and Streamlit. Those are historical
  delivered facts, not proof that the new Skill-first removals have occurred.
- The current host-proposal CLI maps `prepare`, `validate-draft`, `confirm`, `render`,
  and `inspect-latex` to `TailoringApplicationService`. Its `tailor` command either
  validates a host proposal or calls the service's provider-backed generation path.

## Evidence boundary

This task did not run a live Host Agent smoke test and did not verify DeepSeek as a
host. It created documentation only. No processes or temporary directories were
started or left behind, and unrelated dirty-worktree files were not changed.
