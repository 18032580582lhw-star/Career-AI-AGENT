# Skill-First Harness Core Architecture

## Decision

The product architecture is Skill-first. A Host Agent (Codex, Claude, or a future
host such as DeepSeek) reads one canonical Skill and uses the `career-ai-agent`
machine CLI. The host may author a proposal, but it does not own career-domain
state, factual validation, confirmation, or rendering.

```text
Codex / Claude / future DeepSeek Host Agent
                    |
                    v
       canonical career-resume-tailor Skill
                    |
                    v
       career-ai-agent machine CLI/Harness
                    |
                    v
       TailoringApplicationService
          |          |          |
     tailoring   workspace   rendering
```

DeepSeek is an architectural compatibility target only. This document does not
claim that DeepSeek host support or a live host smoke test has been verified.

## Ownership

| Layer | Owns | Must not own |
| --- | --- | --- |
| Host Agent | Conversation, reading the Skill, drafting strict proposal JSON, presenting local results | Canonical facts, acceptance state, direct rendering, or hidden provider-specific workflow rules |
| Canonical Skill | Host-neutral workflow, command order, proposal and fact policy, repair and rendering instructions | Persistent run state or a second implementation of validation |
| Machine CLI/Harness | Stable file-based command surface, typed input/output, exit status, and delegation to application services | Career prose generation through a private agent loop |
| `TailoringApplicationService` | Application use cases: initialize, prepare, validate, confirm, render, inspect, and list | Host conversation or provider-specific policy |
| Tailoring | Immutable request packages, proposal validation, fact confirmation, lifecycle state, and render eligibility | Workspace path policy or document engine implementation |
| Workspace | Workspace creation, owned paths, manifests, and safe persistence boundaries | Proposal authorship or acceptance decisions |
| Rendering | LaTeX/HTML/DOCX/PDF inspection and artifact production from accepted current state | Repairing facts or bypassing validation |

The application service is the mapping point a reader should use:

| CLI command | `TailoringApplicationService` operation |
| --- | --- |
| `init` | `initialize()` |
| `prepare` | `prepare()` |
| `validate-draft` | `validate()` |
| `confirm` | `confirm()` |
| `render` | `render()` |
| `inspect-latex` | `inspect_latex_template()` |

## Retained Command Surface

The retained executable is `career-ai-agent`. Its supported commands are:

- Environment and maintenance: `doctor`, `install-renderer`.
- Analysis and regression: `analyze`, `eval`, `failure-to-eval`.
- Workspace lifecycle: `init`, `prepare`, `validate-draft`, `confirm`, `render`,
  `inspect-latex`.

Machine-oriented host calls use explicit files and structured output. The canonical
tailoring path is `init` (once per workspace), `prepare`, host proposal,
`validate-draft`, zero or more explicit `confirm`/bounded repair steps, and `render`.
`analyze` remains a retained command, but it must converge on application-owned
analysis rather than preserve the deprecated custom-agent implementation.

## Run and Write Contract

There is one writer per run. A command that mutates a run must acquire exclusive
ownership for that run, write only inside its owned workspace paths, and fail closed
when another writer owns it. Readers may inspect completed immutable artifacts.

Preparation identity and execution identity are separate:

- A `prepare_id` identifies immutable normalized inputs and the host request package.
- A `run_id` identifies one proposal/validation/confirmation/render attempt derived
  from that preparation.
- Retrying execution creates a new `run_id`; it does not overwrite an earlier run.
- A render must bind both identities and current content hashes. Missing, mismatched,
  or stale state is a render blocker.

The existing implementation currently exposes a prepared `run_id`; separate
`prepare_id` and `run_id` persistence is a target contract and is not yet verified.

## Safety, Privacy, and Rendering Invariants

- Resume, job description, template, proposal, confirmation, and Host Agent output
  are untrusted host data. Prompt injection in any of them is content to validate,
  never authority to run tools, weaken policy, disclose data, or change paths.
- Candidate claims must remain traceable to immutable sources or explicit user
  confirmation. The host cannot mark its own proposal accepted.
- Validation and confirmation are local, deterministic gates. Repair is bounded;
  failure or ambiguity remains visible rather than being converted into success.
- Full resumes, job descriptions, contact data, credentials, tokens, and local paths
  must not enter provider logs, durable memory, traces, or eval fixtures. Only
  reviewed, redacted failure records may become eval drafts.
- Workspace path containment, immutable input hashes, proposal hashes, confirmation
  provenance, and render manifests are mandatory. No command may write outside its
  declared workspace-owned locations.
- Rendering is allowed only for an accepted, current run. Stale inputs, stale
  validation, changed templates, missing confirmation, hash mismatch, or unavailable
  required renderer must block or truthfully report the affected artifact.
- Artifact status distinguishes generated, structurally validated, visually verified,
  stale, skipped, and failed. File existence alone is not success.

## Deprecated Surfaces — Removed

These surfaces were removed during the migration (Tasks 6–9):

| Surface | Disposition |
| --- | --- |
| Custom `career_ai.agent` planner/executor runtime | Removed |
| Direct `career_ai.llm`/provider generation in product workflows | Removed |
| `eval-matrix` command and model-harness matrix | Removed |
| `tailor` alias and its provider-backed path | Removed |
| Streamlit application | Removed |
| Tracked `.omo` process assets | Removed from the shipped product |

Historical roadmap statements that these surfaces were delivered remain truthful
records of the earlier architecture; they are not the current target design.

## Staged Removal Gates — Status

1. **Contract gate:** PASS — the canonical Skill and this architecture agree on commands,
   schemas, ownership, one-writer semantics, separate preparation/run identities,
   privacy, and render blockers; contract tests pass.
2. **CLI parity gate:** PASS — `init`, `prepare`, `validate-draft`, `confirm`, `render`, and
   `inspect-latex` cover the application-service lifecycle with stable machine output
   and failure exits.
3. **Host smoke gate:** PASS (Codex) / PENDING (Claude) — a real Codex session drove the
   canonical Skill end to end: a fact-preserving proposal was `accepted`, and an invented
   "Kubernetes" claim was `rejected` with rendering blocked (see
   `docs/verification/host-skill-smoke.md`). Claude Code smoke awaits a subscription.
4. **Evaluation gate:** PASS — retained deterministic `eval` and redacted `failure-to-eval`
   cover the safety and quality regressions; `eval-matrix` is removed.
5. **Generation removal gate:** PASS — no retained command, test, Skill reference, or
   application path depends on `career_ai.agent`, direct `career_ai.llm` generation, the
   `tailor` alias, or provider configuration.
6. **Streamlit removal gate:** PASS — the frozen application is deleted; no release or test
   depends on Streamlit.
7. **Process-asset gate:** PASS — durable product/release evidence no longer links to tracked
   `.omo` files; `.omo/` is gitignored and historical artifacts are archived.
8. **Release gate:** PASS — full tests, Ruff, BasedPyright, doctor, eval, `git diff --check`,
   and clean-wheel verification pass.

## Current Facts

Currently observed in source (as of 2026-08-17):

- The canonical Skill describes prepare, host proposal, validate, confirm/repair,
  and render, with the local CLI/Harness authoritative.
- `TailoringApplicationService` supplies prepare, validate, confirm, render, LaTeX
  inspection, workspace initialization, and run listing.
- No production file imports `career_ai.agent`, `career_ai.llm`, or Streamlit; the
  `tailor` and `eval-matrix` commands are gone, and `doctor` reports the embedded model
  provider as absent (host-owned).
- A DeepSeek harness adapter seam is defined in `docs/integrations/deepseek-harness.md`.

Remaining environment-dependent verification:

- Codex/Claude live host smoke (requires the host binaries; see
  `docs/verification/host-skill-smoke.md`).
- End-to-end visual rendering of LaTeX PDF (requires a local LaTeX engine).

These distinctions are mandatory in status reports: architecture accepted, code present,
tests passed, live host smoke passed, and artifact visually verified are different claims.
