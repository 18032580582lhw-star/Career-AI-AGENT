# career-resume-tailor

Canonical host Skill for AI Career Intelligence Suite high-trust resume tailoring.

This Skill only orchestrates the local CLI/Harness. The host may draft proposals,
but the local Career AI workspace, validation harness, confirmation state, and
renderers stay authoritative.

## Workflow

1. prepare
2. host proposal
3. validate
4. confirm/repair
5. render

Use `career-ai-agent prepare` to create the strict request package. Ask the host
model for a JSON proposal that conforms to the provided schema. Use
`career-ai-agent validate-draft` before any confirmation or rendering step.
If validation returns `needs_confirmation`, collect an explicit user decision and
run `career-ai-agent confirm`. If validation returns repairable findings, repair
at most through the local two-repair state policy. Render only accepted runs.

## Natural Language Requests

The Skill supports user requests to generate DOCX/PDF, generate Overleaf .tex,
use the user's own resume.tex, compile a LaTeX PDF, and check the LaTeX
environment. These requests are routed to the CLI commands in
`references/workflow.md` and the rendering policy in `references/rendering.md`.

## Required References

- `references/workflow.md`
- `references/fact-policy.md`
- `references/proposal-contract.md`
- `references/rendering.md`

## Host Neutrality

Codex, Claude Code, and OpenCode must call the same `career-ai-agent` commands
with explicit JSON file arguments. Host differences must not change factual
safety, proposal validation, LaTeX inspection, or rendering policy.
