# Draft: High-Trust Debug Skill Distillation

## Requirements confirmed

- User asked to summarize all project errors and correction processes.
- User asked to combine the results into a plan for distilling a reusable Skill.

## Assumptions

- Scope is the current `F:\AGENT` repository, especially `.omo`, `docs/worklogs`, `.omo/evidence`, and the packaged `career-resume-tailor` Skill.
- "All errors" means project-significant defects, blockers, known failures, and high-trust boundary failures recorded in durable evidence, not every transient command typo.
- The new Skill should be separate from `career-resume-tailor`: runtime resume tailoring stays in the existing Skill; debug/release/error-handling workflow becomes a new Skill.

## Research findings

- The project has two major evidence streams: the high-trust roadmap plan and the later debug-stabilization plan.
- Error classes cluster around trust boundaries: ingestion, JD fetch, factual adequacy, lifecycle state, host proposal strictness, render provenance, optional renderer availability, eval correctness, installer/runtime environment, and UI/browser QA.
- Final release evidence shows full gates passed while missing local LaTeX engines remained honestly reported as an environment limitation.

## Skill direction

- Proposed skill name: `high-trust-debug-stabilization`.
- Purpose: guide Codex through evidence-first diagnosis and minimal repair for this project family.
- Core loop: checkpoint discovery -> reproduce -> classify -> write focused regression/evidence -> fix minimally -> verify gates -> update durable trail.

## Open questions

- Whether the Skill should be installed globally under the user Codex skills folder or kept as a repo-packaged skill first.
- Whether to include scripts in the first version or start with references/templates only.

## Scope boundaries

- INCLUDE: debugging workflow, error taxonomy, evidence templates, verification gates, Windows/PowerShell notes, Skill creation validation.
- EXCLUDE: changing business code now, replacing `career-resume-tailor`, adding cloud/provider integrations, inventing new product features.
