# AI Career Intelligence Suite

> Last updated: 2026-07-14. This summary is based on the repository roadmap,
> `.omo` task ledger, evidence files, and daily worklogs.

## Overview

AI Career Intelligence Suite is a local-first, model-neutral career agent. It started as
a Streamlit resume/JD analysis MVP and has grown into a verified local workflow with
deterministic evals, privacy-safe traces, runtime enforcement, high-trust resume
tailoring, cross-host skills, and DOCX/HTML-PDF/LaTeX rendering.

The default `fake` provider keeps the project runnable without an API key. OpenAI-
compatible, DeepSeek-compatible, or other compatible gateways must go through the same
typed provider capability contract, local harnesses, and safety boundaries.

## Current Status

As of 2026-07-14, the two major roadmap tracks are complete:

- The harness-first career-agent roadmap delivered provider capabilities, evals,
  eval matrix reporting, privacy-safe traces, failure corpus conversion, Tool Catalog v2,
  runtime enforcement, private memory, bounded quality evaluation, controlled autonomy,
  and CLI/Streamlit trust surfaces.
- The high-trust resume-tailoring roadmap delivered versioned workspaces, immutable
  source ingestion, typed evidence extraction, Safety/Adequacy harnesses, proposal
  lifecycle gating, accepted-document rendering, host-proposal CLI commands, render
  manifests, cross-host Skill installation, Streamlit integration, and release checks.

Latest release verification:

- `python -m pytest -q` -> `348 passed`
- `ruff check .` -> passed
- `basedpyright` -> `0 errors, 0 warnings, 0 notes`
- `career-ai-agent doctor` -> HTML renderer, Skill, and no-API checks pass
- `career-ai-agent eval` -> `3 passed, 0 failed`
- `career-ai-agent eval-matrix` -> `fake-default passed=3 failed=0`
- `git diff --check` -> passed

Environment note: Tectonic and XeLaTeX are not currently found on this machine. `.tex`,
DOCX, and HTML-PDF outputs work, while `latex-pdf` correctly reports `latex_no_engine`
until a LaTeX engine is installed.

## Included

- Local Streamlit UI and `career-ai-agent` CLI
- Resume/JD analysis, match scoring, missing keywords, fact-preserving rewrites, cover letters
- Model-neutral runtime with planner, executor, tool registry, recovery, and controlled autonomy
- Provider doctor, deterministic evals, model-harness matrix, traces, failure-to-eval, quality reports
- Runtime enforcement for tools, memory, network fetches, exports, and external actions
- High-trust tailoring workspace with source hashes, proposal hashes, validation lifecycle, and render gates
- DOCX, HTML, HTML-PDF, system LaTeX `.tex`, and user-template LaTeX inspection/patching
- Render manifests, live hash revalidation, stale artifact blocking
- Packaged `career-resume-tailor` Skill for Codex, Claude Code, and OpenCode
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

Open the local Streamlit URL, use the sample data, or upload a `.txt`, `.pdf`, or `.docx`
resume and provide a job description as text or URL.

To let Codex, Claude Code, or OpenCode install the local agent from a GitHub project
URL, use the [Agent Install Guide](docs/agent-install.md).

## Common CLI Commands

Basic agent analysis:

```powershell
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe analyze `
  --resume-text "Product analyst using Python SQL Streamlit dashboards." `
  --jd-text "Role: AI Product Analyst. Requires Python, SQL, Streamlit, LLM evaluation."
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

- `--output result`: default result summary only
- `--output process`: result summary plus process JSON
- `--output json`: machine-readable JSON only

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

- `app.py`: Streamlit entrypoint, delegated to `career_ai.streamlit_app`
- `src/career_ai/cli.py`: Typer CLI root
- `src/career_ai/workflows/`: legacy career-fit workflow
- `src/career_ai/agent/`: planner, executor, tool catalog, trace, quality, memory, policy
- `src/career_ai/evals/`: eval cases, graders, runner, model-harness matrix, failure corpus
- `src/career_ai/workspace/`: versioned workspace, source ingestion, safe storage
- `src/career_ai/tailoring/`: high-trust contracts, extraction, safety, adequacy, state machine
- `src/career_ai/rendering/`: DOCX, HTML, HTML-PDF, LaTeX renderers, and renderer registry
- `src/career_ai/application/`: shared tailoring application service for CLI and UI
- `src/career_ai/skills/career_resume_tailor/`: packaged cross-host Skill
- `docs/roadmaps/harness-first-roadmap.md`: human-facing harness-first delivery status
- `docs/superpowers/plans/2026-07-10-harness-first-roadmap.md`: canonical harness contract
- `.omo/plans/high-trust-resume-skill-latex.md`: high-trust resume tailoring and LaTeX roadmap
- `.omo/evidence/`: task-level verification evidence
