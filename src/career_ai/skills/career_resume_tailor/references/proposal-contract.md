# Proposal Contract

Proposals are strict JSON files conforming to the schema returned by
`career-ai-agent prepare`. Do not wrap proposals in Markdown fences.

The proposal must describe facts and document structure. It must not include raw
LaTeX commands, shell commands, renderer invocations, or file-system operations.
The host writes a proposal file; the local CLI validates, confirms, accepts, and
renders.

The host should preserve run id, source hashes, template hash, and output
language from the prepare package. Any mismatch is treated as stale or invalid.
