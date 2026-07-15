# Proposal Contract

Proposals are strict JSON files conforming to the schema returned by
`career-ai-agent prepare`. Do not wrap proposals in Markdown fences.

The returned schema accepts two host-authored shapes:

- `ResumeTailoringProposal`: validation-only. Use this when the host proposes
  text changes but is not producing renderer-neutral document structure. Even if
  accepted, this shape is not render-ready by itself.
- `HostStructuredProposalPackage`: render-ready candidate. Use this when the
  host supplies both `draft` (`ResumeDocumentDraft`) and `proposal`
  (`StructuredResumeTailoringProposal`). If accepted by the local harness, the
  CLI persists `draft.json`, structured `proposal.json`, `validation.json`, and
  trusted local `candidate-facts.json` for rendering.

The proposal must describe facts and, for render-ready packages, document
structure. It must not include raw LaTeX commands, shell commands, renderer
invocations, or file-system operations. The host writes a proposal file; the
local CLI validates, confirms, accepts, and renders only accepted structured
packages.

The host should preserve run id, source hashes, template hash, and output
language from the prepare package. Any mismatch is treated as stale or invalid.
Candidate facts are owned by the local prepared run; do not add candidate facts
to the host package.
