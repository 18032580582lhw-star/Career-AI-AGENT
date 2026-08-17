# AI Career Intelligence Suite

[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/)
[![Hosts](https://img.shields.io/badge/hosts-Codex%20%7C%20Claude%20Code-8A2BE2)](#)

A local-first, host-native career workflow toolkit: a reusable Agent Skill plus a
deterministic validation and rendering Harness CLI.

> Last updated: 2026-08-17. Skill-first / Harness-core migration is complete (Tasks 1–9).

## Overview

AI Career Intelligence Suite is a local-first, host-native career workflow toolkit. The
reasoning agent is the host runtime — Codex and Claude Code today, with a DeepSeek Harness
adapter seam documented — while this repository provides the reusable Skill and the
deterministic local Harness that owns validation, confirmation, state, and rendering.

The host interprets intent and drafts one strict JSON proposal; the Skill defines the workflow;
the local Harness validates facts, enforces state gates, and renders only accepted structured
packages. There is no embedded model provider and no in-process agent loop: reasoning is
host-owned, and the Harness is model-neutral.

## Current Status

As of 2026-08-17, all nine migration tasks are complete:

- Architecture responsibility is fixed as Host Agent → Skill → deterministic Harness →
  domain/workspace/rendering.
- The canonical Skill installs to `.agents/skills/` (Codex) and `.claude/skills/` (Claude Code)
  without overwriting differing user-owned files.
- The custom Agent runtime, embedded provider layer, and fake model matrix are removed.
- Streamlit and all UI-only state are retired; the package no longer imports or ships a web UI.
- Host proposals are the only model boundary: the host writes strict JSON, the local Harness validates it.
- `analyze` and deterministic evals share `CareerFitApplicationService`; quality, factual
  boundaries, and privacy-safe run records have neutral ownership.
- A DeepSeek harness adapter seam is documented in `docs/integrations/deepseek-harness.md`.

Latest release verification:

- full test suite -> `313 passed`
- `ruff check .` -> passed
- `basedpyright` -> `0 errors, 0 warnings, 0 notes`
- `career-ai-agent doctor` -> renderer, Skill, and host-owned-provider checks pass
- `career-ai-agent eval` -> `3 passed, 0 failed`
- `git diff --check` -> passed

Environment note: Tectonic and XeLaTeX are not installed on this machine. `.tex`, DOCX, and
HTML-PDF outputs work, while `latex-pdf` correctly reports `latex_no_engine` until a LaTeX
engine is installed.

## Included

- A packaged cross-host Skill plus a deterministic `career-ai-agent` Harness CLI.
- Resume/JD analysis, match scoring, missing keywords, fact-preserving rewrites, and cover letters.
- Deterministic application service, quality checks, factual boundary, and privacy-safe run records.
- Deterministic evals and a redacted failure-to-eval loop with an accepted-before-convert gate.
- A high-trust tailoring workspace with source hashes, proposal hashes, validation lifecycle, and render gates.
- DOCX, HTML, HTML-PDF, system LaTeX `.tex`, and user-template LaTeX inspection/patching.
- Render manifests, live hash revalidation, and stale-artifact blocking.
- A DeepSeek harness adapter seam (design guidance) and a host smoke runbook.

## Not Included

Authentication, payments, cloud deployment, multi-user databases, private-document RAG,
job-board scanning, application tracking, auto-apply, external messaging/email/calendar/storage
integrations, an embedded model provider, an in-process agent loop, a web UI, and
model-authorized rendering without local validation.

## Install with an agent

Copy this prompt into Codex or Claude Code to have the agent install the project for you:

```text
Install this project: https://github.com/18032580582lhw-star/Career-AI-AGENT

Read docs/agent-install.md, then create a Python 3.12 virtual environment,
pip install -e ., and run: career-ai-agent doctor,
career-ai-agent init --workspace . --agent all, and
career-ai-agent eval --case-dir evals/career_cases --prompt-dir prompts.
Report the doctor and eval results verbatim.
```

Or run the reviewed installer yourself:

```powershell
# Windows
irm https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.ps1 -OutFile install-agent.ps1
.\install-agent.ps1 -RepoUrl "https://github.com/18032580582lhw-star/Career-AI-AGENT.git" -Agent all
```

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.sh -o install-agent.sh
bash install-agent.sh --repo-url "https://github.com/18032580582lhw-star/Career-AI-AGENT.git" --agent all
```

Full manual steps: [Agent Install Guide](docs/agent-install.md).

## Quick Start

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\career-ai-agent.exe doctor
```

Codex and Claude Code invoke the installed Skill and the CLI directly. To let a host install
the local Skill from a GitHub project URL, see the [Agent Install Guide](docs/agent-install.md).

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

Deterministic eval:

```powershell
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
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

`--html` installs Playwright Chromium. `--latex` does not silently install system TeX; it
checks Tectonic/XeLaTeX and prints platform-specific installation guidance.

## Development Verification

After changing prompts, the tailoring harness, renderers, the CLI, or the Skill, run:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
```

For documentation-only changes, run at least:

```powershell
git diff --check
```

## Architecture Map

The host agent interprets intent and drafts proposals. The Skill defines the workflow; the
local Harness owns source ingestion, validation, confirmation, and rendering. The CLI is the
Harness adapter; there is no embedded agent or provider.

- `src/career_ai/cli.py`: Typer CLI root
- `src/career_ai/workflows/`: career-fit workflow, deterministic quality, factual boundary, run record
- `src/career_ai/application/`: shared career-fit and tailoring application services
- `src/career_ai/evals/`: eval cases, graders, deterministic runner, failure corpus
- `src/career_ai/workspace/`: versioned workspace, source ingestion, safe storage
- `src/career_ai/tailoring/`: high-trust contracts, extraction, safety, adequacy, state machine
- `src/career_ai/rendering/`: DOCX, HTML, HTML-PDF, LaTeX renderers, and renderer registry
- `src/career_ai/skills/career_resume_tailor/`: packaged cross-host Skill
- `docs/architecture/skill-first-harness-core.md`: current architecture and migration boundaries
- `docs/integrations/deepseek-harness.md`: DeepSeek harness adapter seam
- `docs/verification/host-skill-smoke.md`: live host smoke runbook
- `docs/maintenance/repository-mainline-cleanup.md`: repository maintenance receipt and archive index
- `llms.txt`: LLM/agent-readable documentation index

Historical task evidence and completed plans are archived in immutable tag
`pre-slim-main-2026-08-17` and branch `archive/pre-slim-main-2026-08-17`; see the maintenance doc.
