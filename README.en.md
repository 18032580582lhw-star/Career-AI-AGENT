# AI Career Intelligence Suite

> Last updated: 2026-08-17. Skill-first / Harness-core migration Tasks 1–4 are complete.

## Overview

AI Career Intelligence Suite is a local-first, model-neutral career workflow toolkit. The
agent is the host runtime—initially Codex and Claude Code, with DeepSeek Harness planned—
while this repository provides the reusable Skill and the deterministic local Harness that
holds validation and rendering authority. The host reasons and drafts proposals, the Skill
defines the workflow, and the local Harness enforces factual validation, state gates, and
rendering. Streamlit is currently frozen as an optional demo surface, not the core runtime.

The default `fake` provider keeps the project runnable without an API key. OpenAI-
compatible, DeepSeek-compatible, or other compatible gateways must go through the same
typed provider capability contract, local harnesses, and safety boundaries.

## Current Status

As of 2026-08-17, migration Tasks 1–4 are complete:

- Architecture responsibility is fixed as Host Agent → Skill → deterministic Harness →
  domain/workspace/rendering.
- The canonical Agent Skill installs to `.agents/skills/` for Codex and `.claude/skills/`
  for Claude Code without overwriting differing user-owned files.
- Host validation returns typed evidence: state, finding codes, relative artifacts, and the
  next machine instruction.
- `analyze` and deterministic evals share `CareerFitApplicationService` instead of the old
  Agent executor. Quality, factual boundaries, and privacy-safe run records now have neutral ownership.
- `analyze --output json` returns the complete `CareerFitRunResult` schema while removing
  source bodies, credentials, and absolute paths.

Latest release verification:

- non-packaging test suite -> `367 passed`
- wheel packaging smoke -> `1 passed`
- `ruff check .` -> passed
- `basedpyright` -> `0 errors, 0 warnings, 0 notes`
- `career-ai-agent doctor` -> HTML renderer, Skill, and no-API checks pass
- `career-ai-agent eval` -> `3 passed, 0 failed`
- `git diff --check` -> passed

Environment note: Tectonic and XeLaTeX are not currently found on this machine. `.tex`,
DOCX, and HTML-PDF outputs work, while `latex-pdf` correctly reports `latex_no_engine`
until a LaTeX engine is installed.

## Included

- Packaged Skill for agent hosts, plus a deterministic `career-ai-agent` Harness CLI
- Optional local Streamlit UI for demonstration and manual inspection
- Resume/JD analysis, match scoring, missing keywords, fact-preserving rewrites, cover letters
- Deterministic application service, quality checks, factual boundary, and privacy-safe run record
- Provider doctor, deterministic evals, and a compatibility-period model-harness matrix
- Redacted failure-to-eval feedback with an accepted-before-convert gate
- Runtime enforcement for tools, memory, network fetches, exports, and external actions
- High-trust tailoring workspace with source hashes, proposal hashes, validation lifecycle, and render gates
- DOCX, HTML, HTML-PDF, system LaTeX `.tex`, and user-template LaTeX inspection/patching
- Render manifests, live hash revalidation, stale artifact blocking
- Packaged `career-resume-tailor` Skill for Codex and Claude Code
- Read-only compatibility for legacy `.career_ai/history.json`

## Not Included

Authentication, payments, cloud deployment, multi-user database history, private-document
RAG, job-board scanning, application tracking, auto-apply, external messaging, email,
calendar, storage integrations, and model-authorized rendering without local validation.

## Quick Start

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\streamlit.exe run app.py --server.headless=true --server.port=8508
```

Streamlit remains available for demos and manual inspection, but the recommended path is
for Codex or Claude Code to invoke the Skill and CLI directly.

To let Codex or Claude Code install the local Skill from a GitHub project
URL, use the [Agent Install Guide](docs/agent-install.md).

## Common CLI Commands

Basic Harness analysis:

```powershell
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe analyze `
  --resume-text "Product analyst using Python SQL Streamlit dashboards." `
  --jd-text "Role: AI Product Analyst. Requires Python, SQL, Streamlit, LLM evaluation."
.\.venv\Scripts\career-ai-agent.exe analyze `
  --resume-text "Built typed Python workflows." `
  --jd-text "Role: Python Engineer" `
  --output json
```

Harness verification:

```powershell
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
.\.venv\Scripts\career-ai-agent.exe eval-matrix --case-dir evals\career_cases --prompt-dir prompts
```

High-trust resume tailoring workflow:

```powershell
.\.venv\Scripts\career-ai-agent.exe init --workspace . --agent all
.\.venv\Scripts\career-ai-agent.exe prepare --workspace . --resume-file resume.txt --jd-file jd.txt
.\.venv\Scripts\career-ai-agent.exe validate-draft --workspace . --run-id <run-id> --proposal-file proposal.json
.\.venv\Scripts\career-ai-agent.exe confirm --workspace . --run-id <run-id> --confirmation-file confirmation.json
.\.venv\Scripts\career-ai-agent.exe render --workspace . --run-id <run-id> --format all
```

Output modes:

- `analyze` defaults to a human-readable summary.
- `analyze --output json` emits a complete, schema-valid `CareerFitRunResult` with source bodies removed.
- Host-proposal commands retain their own `result` / `process` / `json` protocol.

Renderer installation checks:

```powershell
.\.venv\Scripts\career-ai-agent.exe install-renderer --html
.\.venv\Scripts\career-ai-agent.exe install-renderer --latex
```

`--html` installs Playwright Chromium. `--latex` does not silently install system TeX;
it checks Tectonic/XeLaTeX and prints platform-specific installation guidance.

## Development Verification

After changing prompts, providers, tool catalog, runtime policy, tailoring harnesses,
renderers, or UI, run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
.\.venv\Scripts\career-ai-agent.exe eval-matrix --case-dir evals\career_cases --prompt-dir prompts
```

For documentation-only changes, run at least:

```powershell
git diff --check
```

## Architecture Map

The host agent interprets intent and drafts proposals. The Skill defines the workflow;
the local Harness owns source ingestion, validation, confirmation, and rendering. The CLI
and Streamlit app are adapters over that Harness, not separate autonomous agents.

- `app.py`: Streamlit entrypoint, delegated to `career_ai.streamlit_app`
- `src/career_ai/cli.py`: Typer CLI root
- `src/career_ai/workflows/`: career-fit workflow, deterministic quality, factual boundary, run record
- `src/career_ai/application/`: shared career-fit and tailoring application services
- `src/career_ai/agent/`: migration compatibility code, not the `analyze` / deterministic eval path
- `src/career_ai/evals/`: eval cases, graders, deterministic runner, failure corpus
- `src/career_ai/workspace/`: versioned workspace, source ingestion, safe storage
- `src/career_ai/tailoring/`: high-trust contracts, extraction, safety, adequacy, state machine
- `src/career_ai/rendering/`: DOCX, HTML, HTML-PDF, LaTeX renderers, and renderer registry
- `src/career_ai/skills/career_resume_tailor/`: packaged cross-host Skill
- `docs/architecture/skill-first-harness-core.md`: current architecture and migration boundaries
- `docs/roadmaps/harness-first-roadmap.md`: human-facing harness-first delivery status
- `docs/superpowers/plans/2026-07-10-harness-first-roadmap.md`: canonical harness contract
- `docs/maintenance/repository-mainline-cleanup.md`: repository maintenance receipt and archive index

Historical task evidence and completed plans are archived in immutable tag
`pre-slim-main-2026-08-17` and branch `archive/pre-slim-main-2026-08-17`; see the maintenance doc.
