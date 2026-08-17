# Host Skill Smoke Runbook

Prove that a fresh host session (Codex CLI or Claude Code) can drive the
`career-resume-tailor` Skill end to end using only the installed Skill and the
`career-ai-agent` CLI. This is a **live-host** check; installation-copy tests do not
substitute for it.

## Preconditions

- A fresh temporary workspace directory, never the source checkout.
- A fresh wheel installed into a clean virtualenv (`career-ai-agent` from the wheel, not the dev `.venv`).
- Exactly one host Skill installed for the host under test:
  - Codex: `.agents/skills/career-resume-tailor`
  - Claude Code: `.claude/skills/career-resume-tailor`
- A synthetic resume and JD (no real personal data, credentials, or absolute user paths).

## Rules observed by every smoke

- Every host handoff uses an explicit JSON file path — never heredocs, inline JSON, or fenced Markdown.
- The host obeys `needs_confirmation`, the local repair cap, `stale`, and render gates.
- One smoke = one host session using the one installed Skill; no multi-agent collaboration.
- Record only the redacted summary below; never commit full resumes, full host transcripts, tokens, or absolute paths.

## Scenarios (run both, per host, in isolated fresh sessions)

### S1 — Accepted structured proposal through DOCX render (happy path)

1. `career-ai-agent init --workspace <ws> --agent <codex|claude>`
2. `career-ai-agent prepare --workspace <ws> --resume-file resume.txt --jd-file jd.txt`
3. The host writes a `HostStructuredProposalPackage` JSON file (render-ready: `draft` + `proposal`).
4. `career-ai-agent validate-draft --workspace <ws> --run-id <run-id> --proposal-file proposal.json`
5. `career-ai-agent confirm --workspace <ws> --run-id <run-id> --confirmation-file confirmation.json` (only if validation requires it)
6. `career-ai-agent render --workspace <ws> --run-id <run-id> --format docx`

Expected: final state `accepted`, relative validation/manifest artifacts, a DOCX artifact with a render manifest.

### S2 — Invented / JD-only claim blocked before render (safety)

1. Same `init` + `prepare` as S1.
2. The host writes a proposal that asserts a technology or title present in neither the resume facts nor the JD.
3. `career-ai-agent validate-draft ...`

Expected: final state `rejected` (or `needs_confirmation` for inferred material), finding code
`unsupported_claim` (or `inference_requires_confirmation`), and **no** render artifacts produced.

## Redacted summary template

| Field | Value |
|---|---|
| host / version | e.g. `codex <version>` |
| case id | `s1-accepted-docx` / `s2-unsupported-claim` |
| commands observed | `init`, `prepare`, `validate-draft`, `confirm`?, `render`? |
| final state | `accepted` / `rejected` / `needs_confirmation` / `stale` |
| finding codes | e.g. `unsupported_claim` |
| relative artifacts | relative paths only |
| hashes | proposal/validation/source/template hashes |
| pass / fail | boolean |

## Gates

- `needs_confirmation`, `rejected`, and `stale` never reach `render`.
- The local repair limit is enforced; a third repair transition is refused.
- Rendering succeeds only for an accepted structured package.

The same four no-network conformance fixtures under `evals/host_skill_cases/` (`accepted_structured`,
`needs_confirmation`, `rejected_unsupported_claim`, `stale_tampered`) are the deterministic
regression for these scenarios and must pass before any live adapter is called supported.

## Recorded results

### Codex (codex-cli 0.147.0) — 2026-08-17

| Case | State | Finding codes | Render | Proposal hash |
|---|---|---|---|---|
| S1 accepted (conservative, no-op) | `accepted` | `[]` | n/a (validation-only) | `13e4aa233d430b6fa547fadb4081392b76e319d11d673ea5b0106d6b1b5118dd` |
| S2 invented "Kubernetes" claim | `rejected` | `unsupported_technology`, `inference_requires_confirmation` | blocked | `0651cb827ba54a09ea86074f8fc94812c4d8a4adec547912086ac4c7f691ff99` |

Observations: the host read the Skill and run inputs, produced strict JSON with a correct
canonical proposal hash, and the local Harness accepted the fact-preserving proposal and
rejected the invented claim before rendering.

### Claude Code — pending

No Claude Code subscription is available in this environment, so its two scenarios remain
unexecuted until a plan is attached. The Codex run above exercises the same host-neutral
Skill and CLI contract.
