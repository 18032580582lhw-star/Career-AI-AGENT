# High-Trust Debug Skill Distillation Plan

## TL;DR

> **Summary**: Distill the `F:\AGENT` project's hard-won debugging and release-hardening lessons into a separate Codex Skill for evidence-first diagnosis, minimal repairs, and honest verification.
> **Deliverables**: project error taxonomy, correction-process summary, reusable Skill folder, evidence templates, gate commands, validation notes.
> **Effort**: Short
> **Parallel**: NO
> **Critical Path**: Taxonomy -> Skill scope -> references/templates -> validation -> forward test

## Context

### Original Request

The user asked: "总结一下该项目中所出现的所有错误以及改正过程，结合其结果，给我做一个蒸馏出Skill的计划".

### Evidence Basis

- `.omo/plans/high-trust-resume-skill-latex.md`: completed high-trust roadmap tasks and F1-F4 verification.
- `.omo/plans/debug-stabilization.md`: completed install/CLI/Skill/render/Streamlit/package debugging campaign.
- `.omo/evidence/*`: task-level command evidence, root causes, fixes, and verification output.
- `docs/worklogs/2026-07-08` through `2026-07-15`: daily Chinese worklog trail.
- `.omo/start-work/ledger.jsonl`: compact execution state and adversarial-class evidence.
- `src/career_ai/skills/career_resume_tailor/*`: existing runtime Skill to keep separate from the proposed debug Skill.

### Assumptions

- "All errors" means significant project defects, blockers, known failures, and boundary failures recorded in durable artifacts, not every transient shell typo.
- The new Skill should not replace `career-resume-tailor`; it should teach Codex how to debug and harden this class of local-first, high-trust agent projects.
- Start with a repo-packaged draft Skill first. Install globally only after one forward test passes.

### Metis Review

Metis found no contradiction in the core direction, but identified several guardrails now incorporated:

- This turn produces the written summary/plan only. It does not implement the Skill files.
- "All errors" means durable project-significant errors recorded in plans, evidence, ledger, worklogs, or memory; one-off command typos are excluded.
- Historical blockers must be labelled by date and not confused with current state. Example: generic host proposals were not render-ready during the debug run, then structured packages fixed the public render-ready path on 2026-07-15.
- Release results must be chronological: 2026-07-14 had 348 passed in release verification; 2026-07-15 later reached 355 passed after structured host package repair.
- The Skill must stay focused on evidence-first debugging/release stabilization and must not become another runtime resume-tailoring Skill.
- Skill language decision: `SKILL.md` can be English for trigger/runtime clarity; user-facing summaries and project references should preserve Chinese explanations where useful.

## Work Objectives

### Core Objective

Create a reusable Skill that turns this project's error history into a repeatable debugging workflow:

1. discover the true checkpoint;
2. reproduce the visible failure;
3. classify the error family;
4. add focused evidence/regression;
5. patch minimally;
6. run proportionate gates;
7. keep known environment limitations visible;
8. update the durable trail.

### Deliverables

- `SKILL.md` for `high-trust-debug-stabilization`.
- `references/error-taxonomy.md` with symptom/cause/fix/verification patterns.
- `references/checkpoint-and-evidence.md` with `.omo`/worklog/ledger discovery rules.
- `references/verification-gates.md` with repo commands and when to use each.
- `templates/evidence.md` for per-task evidence capture.
- Optional `scripts/run_project_gates.ps1` only if repeated gate execution proves script-worthy.

### Definition of Done

- Skill passes `quick_validate.py`.
- Skill body stays concise and routes details to references.
- At least one realistic forward test can use only the Skill plus repo artifacts to produce the right diagnosis workflow.
- No business code is changed as part of Skill creation unless a separate user request authorizes it.

### Must Have

- Explicit Windows/PowerShell-first command notes.
- "Known failure is still evidence" rule for LaTeX engines and eval signals.
- Failing-first or evidence-first repair loop.
- Durable checkpoint rule: plan checkbox -> `.omo/boulder.json` -> `.omo/start-work/ledger.jsonl` -> `.omo/evidence` -> worklog.
- Guardrail against trusting host/model output before local validation.

### Must NOT Have

- Do not invent new product capabilities.
- Do not bury project history in `SKILL.md`.
- Do not merge runtime resume-tailoring instructions into the debug Skill except as a reference target.
- Do not create a giant all-purpose debugging framework.

## Error Summary to Distill

| Error family | Representative symptom | Correction pattern | Result |
| --- | --- | --- | --- |
| Fetch/DNS boundary | JD URL failures or DNS rebinding risk could crash or fetch the wrong host. | Return structured `FetchFailure`; validate URL/IP before connecting to the pinned address; add SSRF/DNS regression tests. | Fetch failures became safe, typed, and UI-tolerable. |
| Streamlit runtime/UI | Hot reload caused `AttributeError`; duplicate render path caused `StreamlitDuplicateElementId`; CSS span override hid button text. | Restart stale server when model shape changes; remove duplicate render path; add layout/theme/history regression tests and browser QA. | UI smoke path reached healthy page state with no console errors. |
| DOCX ingestion | Malformed DOCX could leak raw `BadZipFile`. | Catch `BadZipFile` at typed ingestion boundary and map to `SOURCE_READ_FAILED`; add focused regression. | Source ingestion became stable and diagnosable. |
| Fact/adequacy trust | Loose token overlap or caller-trusted labels could make adequacy look better than it was. | Require evidence-backed joins, exact threshold math, negation scope, and metric ownership handling; add adversarial tests. | Adequacy became a trust harness rather than a display metric. |
| Lifecycle precedence | Confirmation warnings could hide rejection; stale artifacts could still appear renderable. | Enforce `stale > rejection > needs_confirmation > accepted`; gate `render_allowed` on accepted current-hash proposals. | Rendering is blocked unless state is accepted and current. |
| Provider/host proposal trust | Prompt-text scoring, forged/mixed provenance, or Markdown-fenced JSON could be over-trusted. | Use typed strategies/packages; reject code fences; strict JSON only; local validation remains authoritative. | Host/model outputs became proposals, not authority. |
| Render provenance | Generic `pdf` backend and missing engine identity were too vague; source/template drift risked stale output. | Require exact `RenderManifest` backend/engine/hash fields; rehash before render; fail stale before side effects. | DOCX/HTML-PDF/.tex stay trustworthy; stale render is rejected. |
| LaTeX environment | Missing Tectonic/XeLaTeX could be misread as product failure or hidden behind green output. | Report engine failure honestly in `doctor`; keep `.tex`, DOCX, HTML-PDF available; return `latex_no_engine` for LaTeX PDF. | Optional dependency limits are visible without blocking supported outputs. |
| Eval silent success | Missing/empty case directory reported zero cases and exit 0. | Add typed `EvalCaseLoadError`; CLI exits 2 with clear message; add loader/CLI bad-input tests. | Eval cannot pass silently with no cases. |
| Render-ready host package | Generic accepted host proposal lacked `draft.json` and `candidate-facts.json`, so render was not ready. | Add `HostStructuredProposalPackage`; validation persists render-ready artifacts only after local acceptance; generic proposals remain validation-only. | Public host path can render when structured and accepted. |
| Render-before-validation | Prepared but non-validated run leaked `FileNotFoundError`. | Return stable `HostRunError` with user-facing next step. | CLI failure became controlled and actionable. |
| Installer/runtime | PowerShell 5.1 stderr handling and Git Bash unusable `python3` stubs broke fresh install. | Harden installer capture; verify Python >=3.12; skip unusable candidates; validate raw GitHub path after push. | Fresh PowerShell/Git Bash install path passed. |
| Tool Catalog v2 | Schema was updated in one path but prompt renderer still assumed old fields; refactor tripped import/file-size rules. | Update typed contract and prompt renderer together; split models/defaults; keep imports top-level. | Tool catalog contract stayed planner-visible and lint-clean. |

## Verification Strategy

- Test decision: TDD for concrete bugs; evidence-after for pure environment probes.
- QA policy: every fix gets a happy-path and failure/edge scenario.
- Core gates:
  - `python -m pytest -q`
  - `ruff check .`
  - `basedpyright`
  - `git diff --check`
  - `career-ai-agent doctor`
  - `career-ai-agent eval --case-dir evals\career_cases --prompt-dir prompts`
  - `career-ai-agent eval-matrix --case-dir evals\career_cases --prompt-dir prompts`
- Environment limitation rule: record missing Tectonic/XeLaTeX as an honest boundary, not a hidden failure.

## TODOs

- [ ] 1. Freeze the source taxonomy

  **What to do**: Convert the error summary table into `references/error-taxonomy.md`. Keep each entry as symptom, likely cause, fix pattern, verification evidence, and "do differently next time".
  **Must NOT do**: Do not paste entire worklogs or evidence files into the reference.

  **References**:
  - `.omo/evidence/task-5-eval-quality.md`
  - `.omo/evidence/task-6-structured-host-package-render-ready.md`
  - `.omo/evidence/task-9-10-render-manifest-host-cli.txt`
  - `docs/worklogs/2026-07-15_AI-Career-Intelligence-Suite_工作日志.md`

  **Acceptance Criteria**:
  - [ ] Reference contains all error families in this plan.
  - [ ] Each family has a concrete verification command or artifact pointer.

  **QA Scenarios**:
  ```text
  Scenario: lookup eval silent success
    Tool: powershell
    Steps: Search the reference for "silent success".
    Expected: It gives symptom, root cause, fix, and verification.

  Scenario: avoid history dump
    Tool: powershell
    Steps: Count the file and inspect for copied command logs.
    Expected: Reference stays concise and contains no giant pasted logs.
  ```

- [ ] 2. Define the Skill trigger and workflow

  **What to do**: Create `SKILL.md` with frontmatter name `high-trust-debug-stabilization` and a description that triggers for debugging/hardening local-first agent projects, `.omo` roadmap continuation, release verification, and high-trust resume-tailoring failures.
  **Must NOT do**: Do not make the Skill trigger for ordinary programming questions.

  **References**:
  - Existing runtime Skill: `src/career_ai/skills/career_resume_tailor/SKILL.md`
  - Skill creator guidance: concise body, details in references.

  **Acceptance Criteria**:
  - [ ] `SKILL.md` has only `name` and `description` frontmatter fields.
  - [ ] Body defines the loop: checkpoint -> reproduce -> classify -> regress/evidence -> fix -> verify -> record.

  **QA Scenarios**:
  ```text
  Scenario: intended trigger
    Tool: manual inspection
    Steps: Read description for "debug", "release verification", ".omo", and "high-trust".
    Expected: A future Codex can know when to use it from frontmatter alone.

  Scenario: over-trigger prevention
    Tool: manual inspection
    Steps: Check description for broad generic terms like "any bug".
    Expected: It stays scoped to evidence-backed local-first agent/project debugging.
  ```

- [ ] 3. Add checkpoint and evidence protocol

  **What to do**: Create `references/checkpoint-and-evidence.md` documenting the durable source order, evidence file naming, temp root cleanup, dirty-worktree handling, and when to update worklogs.
  **Must NOT do**: Do not instruct agents to commit, push, or reset unless user authorization is explicit.

  **References**:
  - `.omo/plans/debug-stabilization.md`
  - `.omo/evidence/task-1-debug-evidence-harness.md`
  - `.omo/start-work/ledger.jsonl`

  **Acceptance Criteria**:
  - [ ] The durable checkpoint chain is explicit.
  - [ ] Dirty-worktree and temp-artifact cleanup rules are explicit.

  **QA Scenarios**:
  ```text
  Scenario: resumed roadmap
    Tool: manual inspection
    Steps: Ask what to read before changing code.
    Expected: Plan checkbox, Boulder, ledger, evidence, worklog are listed before source edits.

  Scenario: temp artifacts
    Tool: manual inspection
    Steps: Ask what not to commit.
    Expected: temp logs, local venvs, debug journals, and raw user data are excluded.
  ```

- [ ] 4. Add verification gates reference

  **What to do**: Create `references/verification-gates.md` with focused, full, CLI, eval, renderer, Streamlit, packaging, and install gate groups. Include Windows command forms.
  **Must NOT do**: Do not claim missing optional dependencies must be installed for every run.

  **References**:
  - `pyproject.toml`
  - `docs/agent-install.md`
  - `.omo/evidence/task-13-release-verification.txt`

  **Acceptance Criteria**:
  - [ ] Includes proportional gate selection guidance.
  - [ ] Separates environment-bound warnings from real failures.

  **QA Scenarios**:
  ```text
  Scenario: small loader fix
    Tool: manual inspection
    Steps: Choose gates for eval loader bug.
    Expected: Focused loader/CLI tests first, then full pytest/static gates if source changed.

  Scenario: LaTeX no engine
    Tool: manual inspection
    Steps: Check how to report missing XeLaTeX/Tectonic.
    Expected: Mark as environment limitation while verifying DOCX/HTML-PDF/.tex remain available.
  ```

- [ ] 5. Add reusable evidence template

  **What to do**: Create `templates/evidence.md` with fields for failure, hypothesis, repro command, fix, focused test, full gate, known limitations, cleanup, and final result.
  **Must NOT do**: Do not require screenshots for non-UI bugs.

  **References**:
  - `.omo/evidence/task-5-eval-bad-input.md`
  - `.omo/evidence/task-7-streamlit-browser.md`
  - `.omo/evidence/f1-plan-compliance-audit.md`

  **Acceptance Criteria**:
  - [ ] Template supports both command-line and browser-visible bugs.
  - [ ] Template has an explicit "known honest failure" section.

  **QA Scenarios**:
  ```text
  Scenario: command bug evidence
    Tool: manual inspection
    Steps: Fill mentally for missing eval case directory.
    Expected: Template captures original failure, exit code, fix, and post-fix command.

  Scenario: browser QA evidence
    Tool: manual inspection
    Steps: Fill mentally for Streamlit browser smoke.
    Expected: Template captures URL, visible checks, console/page errors, and teardown.
  ```

- [ ] 6. Decide whether a script belongs in v1

  **What to do**: Evaluate whether `scripts/run_project_gates.ps1` is worth adding. Add it only if it reduces repeated error-prone command rewriting without hiding failures.
  **Must NOT do**: Do not add a script that mutates repo state, installs dependencies silently, or normalizes failures into green output.

  **References**:
  - `docs/agent-install.md`
  - `.omo/plans/debug-stabilization.md`

  **Acceptance Criteria**:
  - [ ] Decision is recorded: include script in v1 or defer.
  - [ ] If included, the script returns non-zero on real gate failure and prints optional dependency boundaries honestly.

  **QA Scenarios**:
  ```text
  Scenario: no script needed
    Tool: manual inspection
    Steps: Compare reference commands with likely Skill usage.
    Expected: If commands are short enough, defer script and keep Skill lean.

  Scenario: script included
    Tool: powershell
    Steps: Run script with a deliberately missing eval dir option, if such option exists.
    Expected: It fails loudly and does not summarize zero cases as success.
  ```

- [ ] 7. Validate the Skill folder

  **What to do**: Run the Skill Creator validation script against the completed Skill folder and fix frontmatter/naming/resource errors.
  **Must NOT do**: Do not create extra README, changelog, or install guide files inside the Skill.

  **References**:
  - `C:\Users\Sherlock Lee\.codex\skills\.system\skill-creator\scripts\quick_validate.py`

  **Acceptance Criteria**:
  - [ ] `quick_validate.py <skill-folder>` passes.
  - [ ] `agents/openai.yaml` exists if the Skill should appear cleanly in UI lists.

  **QA Scenarios**:
  ```text
  Scenario: validation pass
    Tool: powershell
    Steps: Run quick_validate.py against the Skill folder.
    Expected: exit 0.

  Scenario: no auxiliary clutter
    Tool: powershell
    Steps: List files in the Skill folder.
    Expected: Only SKILL.md, agents metadata, references, templates, and optional scripts exist.
  ```

- [ ] 8. Forward-test on one real historical bug

  **What to do**: Use a fresh context to ask Codex to diagnose one historical bug with the new Skill. Recommended test case: missing eval case directory silent success, because it has clear symptom/cause/fix/verification evidence.
  **Must NOT do**: Do not pass the expected answer to the tester; pass the Skill and raw artifact pointers only.

  **References**:
  - `.omo/evidence/task-5-eval-bad-input.md`
  - `.omo/evidence/task-5-eval-quality.md`

  **Acceptance Criteria**:
  - [ ] Tester identifies the correct checkpoint/evidence sources.
  - [ ] Tester recommends typed load error plus CLI non-zero handling, not superficial output wording.
  - [ ] Tester selects focused loader/CLI tests before full gates.

  **QA Scenarios**:
  ```text
  Scenario: independent diagnosis
    Tool: subagent or fresh thread
    Steps: Ask for diagnosis of eval missing-dir silent success using the Skill.
    Expected: Correct root cause and verification path are recovered without leaked conclusions.

  Scenario: scope fidelity
    Tool: manual review
    Steps: Review tester output for unrelated refactors.
    Expected: No unrelated cleanup or new feature proposals.
  ```

## Commit Strategy

- Commit only if the user asks to create the Skill artifacts.
- Suggested commit after implementation: `docs(skill): add high-trust debug stabilization skill`.

## Success Criteria

- The project error history is summarized into a taxonomy, not buried as raw logs.
- The resulting Skill gives future Codex runs a repeatable debugging spine.
- The Skill preserves the project's core lesson: local evidence and typed validation beat model confidence and pretty green output.
