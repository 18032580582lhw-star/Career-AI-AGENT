# AI Career Intelligence Suite

A local model-neutral Career Agent for job seekers. It can run as a Streamlit app or as
the `career-ai-agent` CLI, accepts resume and job-description inputs, then produces
structured JD analysis, resume-match scoring, fact-preserving resume suggestions, a
tailored resume document, a cover letter, and locally validated tailoring strategy outcomes.

## Why This Project Matters

- Demonstrates local Agent workflow design around resume, JD, rewrite, memory summary,
  and export steps.
- Runs without an API key through a deterministic fake provider, while keeping a
  provider adapter boundary for OpenAI-compatible model gateways.
- Compares evidence-only tailoring strategies without requiring an API key.
- Applies LLM output quality control through deterministic, fact-preserving checks.
- Frames a practical job-search product workflow with clear business value.

## Roadmap

This project follows a finalized harness-first roadmap. Evals, traceability, typed tool
contracts, runtime enforcement, privacy-preserving memory, quality checks, and controlled
autonomy come before larger product expansion. The detailed delivery status and operating
limits are in [the human-facing roadmap](docs/roadmaps/harness-first-roadmap.md); the
governing implementation contract is
[`docs/superpowers/plans/2026-07-10-harness-first-roadmap.md`](docs/superpowers/plans/2026-07-10-harness-first-roadmap.md).

The agent is model-neutral. Its local `fake` provider is the deterministic, no-key
baseline, while OpenAI-compatible and DeepSeek-compatible providers use the same typed
capability contract. Before a run, `doctor` reports whether the active provider supports
structured output, tool calls, reasoning mode, streaming, and provider tracing; missing
capabilities select a deterministic fallback or an explicit unsupported result.

## Run Locally

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\streamlit.exe run app.py
```

Open the local Streamlit URL, use the sample resume/JD, or upload a `.txt`, `.pdf`, or
`.docx` resume.

## Run the Local Agent CLI

```powershell
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe analyze `
  --resume-text "Product analyst using Python SQL Streamlit dashboards." `
  --jd-text "Role: AI Product Analyst. Requires Python, SQL, Streamlit, LLM evaluation."
```

Default mode uses the local `fake` provider, so the CLI is runnable immediately after
install. For an OpenAI-compatible model gateway, configure:

```powershell
$env:CAREER_AI_PROVIDER="openai-compatible"
$env:CAREER_AI_BASE_URL="http://localhost:1234/v1"
$env:CAREER_AI_API_KEY="local-or-provider-key"
$env:CAREER_AI_MODEL="your-model-name"
```

The agent runtime keeps planning/model access separate from local tools. If a model lacks
native tool calling, the local executor still runs the deterministic workflow and records
the structured plan. The planner receives a model-visible tool catalog with each tool's
name, description, input schema, output schema, criticality, retryable errors, and safety
rules, so provider-specific models can reason over the same local capabilities.

## Quality Gates

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
```

## Harness Verification

Run the full harness verification suite after changes to prompts, providers, tools,
runtime policy, or agent behavior:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
.\.venv\Scripts\career-ai-agent.exe eval-matrix --case-dir evals\career_cases --prompt-dir prompts
```

The `eval` command reports deterministic, synthetic case outcomes. `eval-matrix` reports
the provider/model/harness configuration for every row and keeps unavailable providers as
skips, so a missing credential cannot masquerade as a model regression. The local `fake`
row is always the runnable baseline.

## Trace, Failure Corpus, and Quality Evidence

Each local agent run produces a privacy-safe trace containing the run ID, provider,
agent mode, planned and executed local tools, recovery status, capability summary,
runtime-enforcement decisions, and compact input counts. It does not retain full resume
or JD text, uploaded file paths, API keys, credentials, or tokens.

Failures can be stored as redacted, reviewed failure-corpus candidates and converted to
synthetic regression-eval drafts with `career-ai-agent failure-to-eval`. The accepted
corpus deliberately stores only the minimum trace, configuration, failure-category, and
expected-behavior evidence needed to prevent recurrences.

Every run also includes a deterministic `CareerQualityReport`: factual consistency, JD
coverage, prompt strategy availability, missing-keyword coverage, and document-export
readiness. An optional model evaluator is advisory only, runs only through the provider
contract, and is capped at two iterations; it never overrides deterministic failures or
rewrites user materials.

The CLI `analyze` command prints mode, quality, completed/skipped tools, best prompt,
memory availability, and trace ID. In Streamlit, the **Trust & Quality** tab shows the
same evidence without inventing an unavailable historical run.

## Runtime Boundaries and Controlled Autonomy

Models can choose only a small allowlisted set of local analysis tools in a bounded plan.
The runtime validates and repairs critical analysis steps, then independently enforces
tool calls, memory writes, URL fetches, exports, and external-action boundaries. Planner
output is never authorization to perform an external action.

The agent cannot read arbitrary local files, modify shell/Git/environment/credential
state, send messages, submit job applications, or use unapproved external services.
Unsafe or external actions are denied or require an explicit policy decision and are
recorded in the trace. Privacy-preserving memory keeps only redacted, high-signal career
profile summaries.

## Tailoring Strategy Harness

The harness generates conservative, ATS-aligned, and impact-narrative proposals from typed
evidence, then grades each with the local Safety, Adequacy, and lifecycle harnesses. The
`prompts/` directory remains a compatibility profile that enables this legacy surface; its
text does not authorize claims or affect local validation.

## LLM Boundary Harness

The LLM boundary harness checks model-generated `CareerFitReport` JSON before it can
enter the agent as trusted output. It rejects invalid JSON, schema mismatches, match
scores outside `0-100`, bullet suggestions that are not anchored to source resume text,
JD keywords that do not come from the job description, and rewritten resumes with obvious
unsupported factual markers such as new years, percentages, technologies, or organization
names. `guard_career_fit_report()` returns the model report only when it passes these
checks; otherwise it returns the deterministic fallback report plus structured violations.

## Product Scope

Included: local Streamlit app, JD URL/manual input, resume upload/text input, match
analysis, skill gaps, fact-preserving bullet rewrites, `.docx` resume and cover letter
exports, prompt strategy comparison, local analysis history replay, shared workflow
entrypoint, model-neutral agent runtime, provider capabilities, evals, traces, failure
corpus conversion, runtime enforcement, private memory, bounded quality evaluation, and
CLI execution.

Not included: authentication, payments, cloud deployment, multi-user database history,
complex RAG, storage/email/calendar/job-board integrations, or automated job applications.
These remain deferred until the harness verification standard is stable.
