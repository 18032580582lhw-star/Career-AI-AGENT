# AI Career Intelligence Suite

A local AI-agent-style career intelligence MVP for job seekers. Paste or upload a resume,
provide a job description URL or manual JD text, then generate structured JD analysis,
resume-match scoring, fact-preserving resume suggestions, a tailored resume document,
a cover letter, and a deterministic prompt evaluation harness.

## Why This Project Matters

- Demonstrates AI Agent workflow design around resume, JD, rewrite, and export steps.
- Shows prompt engineering and prompt quality comparison without requiring an API key.
- Applies LLM output quality control through deterministic, fact-preserving checks.
- Frames a practical job-search product workflow with clear business value.

## Run Locally

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\streamlit.exe run app.py
```

Open the local Streamlit URL, use the sample resume/JD, or upload a `.txt`, `.pdf`, or
`.docx` resume.

## Quality Gates

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
```

## Prompt Evaluation Harness

The harness loads markdown prompt strategies from `prompts/`, scores each strategy with
deterministic rubric signals, and reports the strongest strategy. It is designed to make
prompt strategy tradeoffs visible without depending on live LLM calls.

## MVP Scope

Included: local Streamlit app, JD URL/manual input, resume upload/text input, match
analysis, skill gaps, fact-preserving bullet rewrites, `.docx` resume and cover letter
exports, prompt strategy comparison.

Not included in v0.1: authentication, persistence, payments, RAG, deployment, or
multi-user history.
