# Harness-First Roadmap: Finalized Delivery Status

## Canonical Status

The governing implementation contract is
[`docs/superpowers/plans/2026-07-10-harness-first-roadmap.md`](../superpowers/plans/2026-07-10-harness-first-roadmap.md).
It was finalized on 2026-07-10. This document is the stable, human-facing delivery
summary: future harness work must reference the governing contract or a separate
addendum, and must not weaken its provider, privacy, evaluation, enforcement, or
autonomy requirements.

The product remains a local, model-neutral Career Agent. Its default `fake` provider
keeps the workflow runnable without an API key; OpenAI-compatible and
DeepSeek-compatible providers use the same typed client boundary rather than
provider-specific workflow shortcuts.

## Completed Harness Baseline

| Area | Delivered baseline | User-visible or developer evidence |
| --- | --- | --- |
| Provider contract | Typed capability profiles select tool-calling, structured-plan, or deterministic-fallback behavior. | `career-ai-agent doctor` prints the active provider and capabilities. |
| Eval bank | Synthetic, privacy-safe career cases and deterministic graders cover role extraction, gaps, factual consistency, and prompt-strategy selection. | `career-ai-agent eval --case-dir evals/career_cases --prompt-dir prompts` prints each case result. |
| Model-harness matrix | Results are associated with a provider/model/harness configuration; unavailable provider rows are skipped rather than reported as failures. | `career-ai-agent eval-matrix --case-dir evals/career_cases --prompt-dir prompts` includes the `fake` baseline row. |
| Trace and failure corpus | Every agent run emits a compact trace; reviewed, redacted failure records can become eval drafts. | CLI analysis prints a trace ID; `failure-to-eval` only accepts reviewed candidates. |
| Tool contract | The model-visible catalog supplies names, schemas, examples, response modes, failure categories, retries, and safety annotations. | Planner and tool-catalog tests validate the contract. |
| Runtime enforcement | Tool calls, memory writes, URL fetches, exports, and external actions pass runtime policy hooks and emit trace-compatible decisions. | Enforcement tests prove unsafe paths and external actions are denied or gated. |
| Private memory | Only redacted, high-signal career profile fields are retained; full resume/JD text, contact data, credentials, and local paths are removed. | Memory and failure-corpus tests verify redaction. |
| Quality and recovery | Deterministic quality checks remain the release gate; an optional model evaluator is advisory and capped at two iterations. | Each agent result has a `CareerQualityReport` and recovery evidence. |
| Controlled autonomy | The model may select only allowlisted local tools in a bounded plan; critical analysis tools are repaired into the plan when needed. | Rejected or external actions are recorded as skipped/denied, not executed. |
| Trust surfaces | CLI and Streamlit expose quality, prompt, recovery, memory, mode, and trace evidence. | `analyze` output and the Streamlit **Trust & Quality** tab. |

## Operating Contract

The workflow is deliberately bounded:

- The model may plan within the typed local tool catalog, subject to the active provider
  capabilities and the autonomy allowlist.
- The deterministic workflow remains the fallback when a provider cannot safely supply
  structured planning or tool calls.
- Runtime policy is authoritative. Planner output alone cannot authorize a memory write,
  network fetch, document export, or external action.
- The agent does not read arbitrary local files, alter shell/Git/environment/credential
  state, submit applications, send messages, or invoke unapproved external services.
- Privacy-safe traces and memory contain summaries and metadata only, never full resumes,
  job descriptions, credentials, tokens, or local file paths.

## Verification Standard

Run the full local contract before declaring a harness change complete:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
.\.venv\Scripts\career-ai-agent.exe eval-matrix --case-dir evals\career_cases --prompt-dir prompts
```

The expected baseline is: all tests and Ruff checks pass, BasedPyright reports zero
errors, `doctor` lists provider capabilities, every deterministic eval case is reported,
and the matrix includes the local `fake` provider row. Browser QA additionally verifies
that the Streamlit sample-analysis path renders its report and trust panel without a
traceback.

## Task 12 Verification Record

Task 12 documentation and verification completed on 2026-07-11 (Asia/Hong_Kong):

- `pytest`: 103 passed.
- `ruff check .`: passed.
- `basedpyright`: 0 errors, 0 warnings, 0 notes.
- `doctor`: reported the `fake` / `local-fake` capability profile.
- `eval` and `eval-matrix`: each reported the deterministic
  `sample_product_analyst` missing-keywords failure; the matrix emitted the required
  `fake-default` row. This is recorded as an eval outcome, not masked as a successful
  result.
- Streamlit on port 8508 returned `ok` from `/_stcore/health`; the sample analysis and
  **Trust & Quality** panel rendered without a traceback or browser-console error.

## Deferred Product Work

Authentication, payments, cloud deployment, multi-user database history, complex RAG,
job-board integrations, email/calendar/storage integrations, and automated job
applications remain out of scope. They may be reconsidered only after the verification
standard above remains stable for the intended change.
