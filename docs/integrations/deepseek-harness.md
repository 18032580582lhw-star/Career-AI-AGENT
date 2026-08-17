# DeepSeek Harness Adapter Seam

Status: design guidance for a future adapter. Not yet a live, supported integration.

## Positioning

A DeepSeek harness is a **host** in the same sense as Codex or Claude Code: it reasons,
drafts one strict JSON proposal, and drives the local `career-ai-agent` CLI. The local Harness
owns validation, confirmation, state, and rendering — never the model. This document defines the
seam an adapter must satisfy; it does not add model-specific fields to the core contract.

## Canonical contract

The adapter consumes and produces the same protocol as every host. The single source of truth is
the typed schema returned by `career-ai-agent prepare` and defined in
`career_ai.tailoring.proposal_contracts`. Read `references/proposal-contract.md` and
`references/workflow.md` in the packaged Skill for the exact handshake. Do not copy or redefine
the schema fields here; any drift from the typed contracts is detected and rejected by the local
Harness.

## Requirements for any adapter

- **Strict structured proposal output**: the adapter must emit a proposal JSON file that validates
  under the typed schema. If the model's native structured-output mode is unavailable or
  unreliable, the adapter must still produce a file that validates locally before any side effect.
- **State / reasoning replay is an adapter-version capability**: replay or multi-step reasoning
  state is not a core assumption of the contract. The core only needs the final proposal plus the
  run identity and hashes the proposal carries.
- **Unsupported parameters or capabilities fail explicitly**: if the underlying model/API does not
  support a requested mode (for example tool calling on a reasoning model, or a structured output
  flag), the adapter must surface a typed failure instead of silently degrading.
- **No host-specific field may enter the canonical proposal**: model IDs, tool-call capability
  flags, reasoning/replay settings, and adapter version markers stay out-of-band. The local
  Harness rejects unknown fields.
- **Conformance gate**: all four no-network conformance fixtures under `evals/host_skill_cases/`
  (`accepted_structured`, `needs_confirmation`, `rejected_unsupported_claim`, `stale_tampered`)
  must pass before the adapter is called supported. Run
  `pytest tests/test_host_skill_conformance.py` and
  `career-ai-agent eval --case-dir evals/career_cases --prompt-dir prompts`.

## Time-sensitive implementation guidance (verify before relying)

DeepSeek exposes an OpenAI-compatible chat API at `https://api.deepseek.com`. As of this writing:

- Current model IDs are `deepseek-v4-flash` and `deepseek-v4-pro`. The legacy
  `deepseek-chat` / `deepseek-reasoner` names were discontinued on 2026-07-24 and are no longer a
  stable target.
- JSON output uses an OpenAI-style `response_format` (`json_object`). DeepSeek documents that the
  word "json" must appear in the prompt and an example of the desired JSON shape should be
  provided; `max_tokens` must be set high enough to avoid truncation.
- Tool calling is supported, including in thinking mode. A separate structured-output form is
  available through the Responses API, which DeepSeek documents as adapted for Codex.
- Thinking-mode models can emit a separate `reasoning_content` segment; tool-call turns must replay
  that segment or the API rejects the request.

These facts are guidance, not a contract. Re-check the official docs
(<https://api-docs.deepseek.com>) at implementation time; model IDs and tool-call capabilities
must never be hard-coded into the core schema or the local Harness.

## Acceptance for the seam

- A later implementer can build the adapter from this document plus the two Skill references
  without changing the core contracts.
- No committed artifact in this document contains secrets, source document bodies, or absolute
  personal paths.
