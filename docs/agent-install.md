# Agent Install Guide

This guide lets Codex, Claude Code, OpenCode, or a human install the AI Career
Intelligence Suite local agent from a GitHub project URL.

Use the raw version of this file when asking an agent to install the project:

```text
https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/docs/agent-install.md
```

## Agent Prompt

Give this prompt to Codex, Claude Code, or OpenCode:

```text
Install the local AI Career Intelligence Suite agent from this GitHub project:

https://github.com/18032580582lhw-star/Career-AI-AGENT

First read the full raw install guide:
https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/docs/agent-install.md

Do not rely on a summarized web page. Follow the guide, run the installer or
manual commands, then verify with doctor, init, eval, and eval-matrix. If a
dependency is missing, stop and report the exact repair command.
```

This guide is configured for:

```text
https://github.com/18032580582lhw-star/Career-AI-AGENT
```

## What Gets Installed

The installer:

1. Clones the GitHub repository, or reuses an existing checkout.
2. Creates `.venv` inside the checkout.
3. Installs the package in editable mode.
4. Runs `career-ai-agent doctor`.
5. Runs `career-ai-agent init --workspace <checkout> --agent all`.
6. Runs deterministic `eval` and `eval-matrix` unless explicitly skipped.

The host Skill is installed into:

```text
.agents/skills/career-resume-tailor
.claude/plugins/career-resume-tailor
.career_ai/skill-installations.json
```

Codex and OpenCode share `.agents/skills/career-resume-tailor`. Claude Code uses
`.claude/plugins/career-resume-tailor`.

## Windows / PowerShell Installer

Safer reviewed-script flow:

```powershell
irm https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.ps1 -OutFile install-agent.ps1
Get-Content .\install-agent.ps1
.\install-agent.ps1 -RepoUrl "https://github.com/18032580582lhw-star/Career-AI-AGENT.git" -Agent all
```

Useful options:

```powershell
.\install-agent.ps1 `
  -RepoUrl "https://github.com/18032580582lhw-star/Career-AI-AGENT.git" `
  -InstallRoot "$HOME\career-agents" `
  -Agent all `
  -SkipEval
```

Use `-Update` only when you want the script to run `git pull --ff-only` in an
existing checkout.

## macOS / Linux / Git Bash Installer

Safer reviewed-script flow:

```bash
curl -fsSL https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.sh -o install-agent.sh
sed -n '1,220p' install-agent.sh
bash install-agent.sh --repo-url "https://github.com/18032580582lhw-star/Career-AI-AGENT.git" --agent all
```

Useful options:

```bash
bash install-agent.sh \
  --repo-url "https://github.com/18032580582lhw-star/Career-AI-AGENT.git" \
  --install-root "$HOME/career-agents" \
  --agent all \
  --skip-eval
```

Use `--update` only when you want the script to run `git pull --ff-only` in an
existing checkout.

## Manual Install

If an agent cannot run the installer script, use these steps.

Windows / PowerShell:

```powershell
git clone https://github.com/18032580582lhw-star/Career-AI-AGENT.git
cd Career-AI-AGENT
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe init --workspace . --agent all
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
.\.venv\Scripts\career-ai-agent.exe eval-matrix --case-dir evals\career_cases --prompt-dir prompts
```

macOS / Linux:

```bash
git clone https://github.com/18032580582lhw-star/Career-AI-AGENT.git
cd Career-AI-AGENT
python3.12 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -e .
./.venv/bin/career-ai-agent doctor
./.venv/bin/career-ai-agent init --workspace . --agent all
./.venv/bin/career-ai-agent eval --case-dir evals/career_cases --prompt-dir prompts
./.venv/bin/career-ai-agent eval-matrix --case-dir evals/career_cases --prompt-dir prompts
```

If `python3.12` is unavailable, install Python 3.12 first. The project requires
Python `>=3.12`.

## Verification Checklist

Installation is complete when all of these pass:

```powershell
career-ai-agent doctor
career-ai-agent init --workspace . --agent all
career-ai-agent eval --case-dir evals\career_cases --prompt-dir prompts
career-ai-agent eval-matrix --case-dir evals\career_cases --prompt-dir prompts
```

Expected release baseline:

```text
eval: 3 passed, 0 failed
eval-matrix: fake-default passed=3 failed=0
```

Known environment boundary: if Tectonic or XeLaTeX is not installed, `doctor`
must report that honestly. DOCX, HTML-PDF, and `.tex` generation can still work,
while `latex-pdf` should return `latex_no_engine`.

## Troubleshooting

- Missing Git: install Git, then rerun the installer.
- Missing Python 3.12: install Python 3.12, then rerun the installer.
- Existing checkout with local changes: rerun without update, or inspect and run
  `git pull --ff-only` manually.
- Existing Skill file differs: `init` reports `exists-different` and does not
  overwrite user-owned files.
- HTML renderer unavailable: run `career-ai-agent install-renderer --html`.
- LaTeX PDF unavailable: install Tectonic or XeLaTeX, or keep using `.tex`,
  DOCX, and HTML-PDF outputs.
