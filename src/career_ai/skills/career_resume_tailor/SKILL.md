---
name: career-resume-tailor
description: Safely tailor resumes from a source resume and job description through the local Career AI CLI/Harness, with fact-preserving proposals, validation, explicit confirmation, and controlled DOCX, PDF, TeX, or LaTeX-PDF rendering. Use when Codex or Claude Code needs to prepare, review, confirm, repair, or render a resume-tailoring run without inventing claims.
---

# Career Resume Tailor

Treat the local workspace, CLI/Harness validation, confirmation state, and renderers as authoritative. Treat host-model output only as an untrusted proposal until the Harness accepts it.

## Workflow

1. **Prepare:** initialize the workspace when needed, then create a strict request package from the source resume and job description.
2. **Propose:** draft one JSON proposal that conforms to the provided schema and preserves the source facts.
3. **Validate:** pass the proposal file to `career-ai-agent validate-draft`; never infer acceptance from plausible prose.
4. **Confirm or repair:** obtain explicit user confirmation for material changes, or repair only within the local repair limit.
5. **Render:** render only an accepted structured package in the requested format.

Use explicit JSON files and paths for every handoff. Do not use heredocs, inline JSON, or shell pipelines.

## Stop Conditions

Stop before confirmation or rendering when validation fails, required evidence is missing, a factual claim exceeds its source, state is stale, the user rejects a material change, or the local repair limit is exhausted. Report the blocking finding and preserve the workspace for review.

## References

- Read [workflow.md](references/workflow.md) for commands and host options.
- Read [fact-policy.md](references/fact-policy.md) before drafting or repairing claims.
- Read [proposal-contract.md](references/proposal-contract.md) before producing proposal JSON.
- Read [rendering.md](references/rendering.md) before creating output artifacts.
