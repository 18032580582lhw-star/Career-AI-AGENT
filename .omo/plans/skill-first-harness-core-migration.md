# Skill-First / Harness-Core Migration Plan

## TL;DR

> **Goal**: turn the repository into a host-native Career Agent: Codex or Claude Code owns reasoning and interaction, a concise Agent Skill teaches the workflow, and the local Python Harness remains authoritative for facts, state, validation, confirmation, rendering, and evals.
>
> **Deliverables**:
> - Valid, discoverable Codex and Claude Code Skill installations using one canonical policy bundle.
> - A stable machine-readable CLI/Harness contract with trust evidence and deterministic `analyze`/`eval` behavior.
> - Host conformance fixtures for Codex, Claude Code, and a future DeepSeek harness.
> - Removal of the custom planner/executor/tool/recovery runtime and in-project model-provider loop.
> - Streamlit retirement after host/CLI parity.
> - Durable documentation outside `.omo`, followed by tracked OMO process-artifact cleanup.
>
> **Estimated effort**: large, but mostly deletion and boundary consolidation rather than a rewrite.
> **Execution**: four waves, with Tasks 2 and 3 parallel after Task 1.
> **Critical path**: 1 -> 3 -> 4 -> 5 -> 7 -> 8 -> 9.

---

## Context

### Current state

- The shipped console entrypoint is `career-ai-agent = career_ai.cli:app` (`pyproject.toml:25-26`).
- `career-ai-agent analyze` still invokes the custom runtime through `run_career_agent` (`src/career_ai/cli.py:92-128`).
- Deterministic evals also invoke that runtime (`src/career_ai/evals/runner.py:21-36`).
- Failure-corpus conversion imports trace DTOs from the Agent namespace (`src/career_ai/evals/failure_corpus.py:8-13`).
- The high-trust proposal lifecycle is already independent: `TailoringApplicationService` owns prepare, validate, confirm, render, and workspace replay (`src/career_ai/application/tailoring_service.py:53-176`).
- The canonical Skill already states the right authority split: the host drafts, while local validation/state/rendering remain authoritative (`src/career_ai/skills/career_resume_tailor/SKILL.md:3-22`).
- The installer currently supports Codex, Claude, OpenCode, and `all`, but writes Claude content to `.claude/plugins/...` (`src/career_ai/skills/installation.py:20-27,109-124`). Current Claude Code project Skills instead live at `.claude/skills/<skill-name>/SKILL.md`; a real plugin would require a plugin manifest and `skills/` nesting.
- DeepSeek is represented only by a stale provider capability profile (`src/career_ai/llm/capabilities.py:110-156`). It is not a proven host adapter.
- Streamlit is already a UI adapter over the application service (`src/career_ai/streamlit_app/main.py:41-189`), but package metadata, tests, and docs still ship it (`pyproject.toml:8,21`; `tests/test_app_layout.py:8-97`).
- `.omo` has no production imports. Current references are documentation/worklog evidence rather than runtime dependencies.

### Target architecture

```text
Codex / Claude Code / future DeepSeek harness
                    |
          career-resume-tailor Skill
                    |
      career-ai-agent machine CLI contract
                    |
  application + tailoring + workspace + rendering
                    |
       typed artifacts, hashes, evals, manifests
```

Ownership is explicit:

| Layer | Owns | Must not own |
|---|---|---|
| Host Agent | Reasoning, planning, asking the user, choosing when to call commands | Factual authorization, acceptance, renderer trust |
| Skill | Discovery metadata, workflow order, command/file protocol, stop/repair rules | Business logic, provider SDK code, duplicated validation |
| CLI/Harness | Strict parsing, source binding, state transitions, confirmation, rendering, audits, evals | Autonomous planning or simulated tool orchestration |
| UI | Nothing unique | Any rule required for a valid run |

### Decisions already made

- Brand the product as **a host-native Career Agent powered by a Skill and local deterministic Harness**. Do not describe the CLI itself as autonomous.
- Keep `career-ai-agent` as the compatibility command name.
- Preserve `analyze` as a deterministic career-fit command, but remove Agent-mode/tool/retry/memory theater.
- Keep `doctor`, `install-renderer`, `analyze`, `eval`, `failure-to-eval`, `init`, `prepare`, `validate-draft`, `confirm`, `render`, and `inspect-latex`.
- Remove the API-only `tailor` branch and fake-provider-only `eval-matrix` after replacements land.
- Codex and Claude Code are the supported hosts now. Remove OpenCode from the supported-host claim and installer matrix.
- DeepSeek milestone one is no-network protocol conformance plus adapter requirements, not a claimed live installation.
- Freeze Streamlit immediately; retire it in this migration only after CLI and both current hosts meet the same artifact contract.
- TDD applies to behavior and contract changes. Mechanical deletion occurs only after replacement coverage is green.

### Scope

**Included**

- Skill metadata, references, installation layout, and packaging.
- Deterministic CLI/application seams.
- Typed host-result evidence and conformance fixtures.
- Neutral audit/failure-corpus ownership.
- Removal of custom Agent runtime and direct model-provider execution.
- Codex/Claude fresh-session smoke verification.
- DeepSeek future-adapter contract.
- Streamlit and tracked `.omo` retirement.
- Bilingual README/install/architecture updates and clean-wheel verification.

**Excluded**

- Public SaaS, authentication, billing, cloud state, multi-user database history.
- Job submission, email/calendar/storage integrations, and browser form automation.
- A new web UI, TUI, desktop shell, or speculative multi-agent orchestration.
- A live DeepSeek API adapter or invented DeepSeek Skill directory.
- Concurrent writers mutating one `run_id`; the supported rule is one writer per run and isolated run IDs per host invocation.

---

## Objectives and definition of done

The migration is complete only when all statements below are true:

- A fresh wheel installs the CLI and canonical Skill assets without Streamlit or provider-SDK configuration dependencies.
- `init --agent codex`, `init --agent claude`, and `init --agent all` install discoverable project Skills at the correct locations, are idempotent, and never overwrite differing user files.
- The canonical `SKILL.md` has valid YAML frontmatter, concise host-neutral instructions, and one-level references.
- A fixed resume/JD plus four proposal cases (accepted, needs-confirmation, unsupported claim, stale/tampered) produce identical local decisions regardless of host label.
- `analyze` and `eval` no longer import `career_ai.agent` or build an LLM client.
- Failure-to-eval uses neutral privacy-safe run records and never stores resume/JD bodies, credentials, or absolute paths.
- No production import references `career_ai.agent`, `career_ai.llm`, or `streamlit`.
- The custom Agent package, direct provider client/settings/capabilities, `eval-matrix`, Streamlit code/dependency, and obsolete tests are removed.
- README and architecture docs explain the final host/Skill/Harness split without depending on `.omo` evidence.
- Full tests, Ruff, BasedPyright, deterministic eval, host conformance, clean-wheel smoke, and git diff checks pass.
- One redacted Codex smoke and one redacted Claude Code smoke have been run from fresh temporary workspaces; if a host binary/auth is unavailable, the migration is not called fully verified.

### Non-negotiable safety properties

- Host output is untrusted data until strict JSON parsing, source/hash binding, Safety, Adequacy, and state-machine validation pass.
- Only an accepted, current proposal may render.
- Confirmation is explicit and scoped to the requested fact; it cannot authorize unrelated claims.
- Source files and user templates are never modified in place.
- Audit and conformance output contains counts, states, codes, hashes, and relative artifact references—not personal document bodies or credentials.
- No hidden provider/network call occurs in host-proposal mode or deterministic evals.

---

## Verification strategy

### Test policy

1. Add or update a failing test for every changed public boundary.
2. Implement the smallest change that makes it pass.
3. Run the focused suite for that task.
4. Run the full local gate before each deletion wave.
5. Delete obsolete tests only when a replacement test covers the same user-visible or safety contract at an equal or higher boundary.

### Canonical local gate

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
git diff --check
```

The final gate additionally builds a wheel, installs it into a fresh temporary virtual environment, runs `doctor`, installs both host Skills, and runs the host-conformance fixtures.

### Host parity cases

| Case | Expected result | Required negative proof |
|---|---|---|
| Accepted structured proposal | `accepted`, then DOCX render with manifest and SHA-256 | no provider/network client is built |
| Reasonable unsupported inference | `needs_confirmation` | no render before explicit confirmation |
| Invented/JD-only claim | `rejected` with stable finding code | no accepted document or rendered artifact |
| Tampered source/proposal/template hash | `stale` or typed rejection | prior acceptance cannot be replayed |

### Required trust evidence

- Prepare: run ID, relative request artifact, source hashes, template type/hash, proposal schema, next action.
- Validate: source, state, proposal/validation hashes, relative validation artifact, finding count/codes, next action.
- Render: format, status, backend, typed code, relative output artifact/media type/SHA-256, relative render-manifest path.
- Render manifest: engine/version, font bundle, page size, accepted-document hash, proposal hash, validation hash, output hashes.

---

## Execution waves

### Wave 1 — lock the architecture and host contract

- Task 1: write the migration contract and boundary tests.
- Task 2: make the Skill valid and install it at correct Codex/Claude paths.
- Task 3: make host outputs and conformance fixtures sufficient to replace the UI trust panel.

### Wave 2 — replace runtime consumers

- Task 4: create the deterministic career-fit service and neutral audit ownership.
- Task 5: prove Codex/Claude Skill execution and document the DeepSeek adapter contract.
- Task 6: remove in-core API generation and provider assumptions from the high-trust lifecycle.

### Wave 3 — delete redundant products

- Task 7: delete the custom Agent runtime and obsolete LLM/matrix surfaces.
- Task 8: retire Streamlit and UI-only assets/dependencies.

### Wave 4 — package, document, and remove process bloat

- Task 9: clean packaging/docs, migrate durable OMO knowledge, remove tracked OMO artifacts, and run release verification.

### Dependency matrix

| Task | Depends on | Blocks |
|---|---|---|
| 1 | — | 2, 3, 4 |
| 2 | 1 | 5, 9 |
| 3 | 1 | 5, 6, 8 |
| 4 | 1 | 6, 7 |
| 5 | 2, 3 | 7, 8, 9 |
| 6 | 3, 4 | 7 |
| 7 | 4, 5, 6 | 8, 9 |
| 8 | 3, 5, 7 | 9 |
| 9 | 2, 5, 7, 8 | Final verification |

---

## TODOs

- [x] Task 1 — Establish the final architecture contract and migration guardrails

### Task 1 — Establish the final architecture contract and migration guardrails

**Files**

- Create: `docs/architecture/skill-first-harness-core.md`
- Create: `tests/test_architecture_boundaries.py`
- Modify: `README.en.md`
- Modify: `README.zh.md`
- Reference: `src/career_ai/cli.py:37-248`
- Reference: `src/career_ai/application/tailoring_service.py:53-176`
- Reference: `src/career_ai/skills/career_resume_tailor/SKILL.md:3-42`
- Reference: `docs/roadmaps/harness-first-roadmap.md:47-64`

**Work**

1. Write the final ownership table and supported command list from this plan into the architecture document.
2. Mark Streamlit frozen and describe the one-writer-per-run rule; different host invocations must call `prepare` separately and receive isolated run IDs.
3. Add an explicit deprecation table: keep, replace, remove, and the test that unlocks each removal.
4. Add architectural tests that initially pin allowed dependencies and are tightened as later tasks land:
   - Skill/Harness modules must not import Streamlit.
   - `tailoring`, `workspace`, and `rendering` must not import `career_ai.agent`.
   - the final form of `application`, `evals`, and CLI must not import `career_ai.agent` or `career_ai.llm`.
5. Update README positioning only enough to stop calling the web app or CLI an autonomous Agent; leave detailed command cleanup for Task 9.

**Must not**

- Do not move or delete runtime code in this task.
- Do not claim Codex/Claude live execution before Task 5.
- Do not rewrite historical worklogs.

**Acceptance criteria**

- The architecture doc names every retained public command and every planned removal.
- Initial boundary tests pass for modules that are already clean. Each later task adds its stricter assertion as a failing red test immediately before removing that dependency; no long-lived `xfail` is used.
- README clearly says host runtime = Agent, Skill = workflow, local CLI = authority.
- No production behavior changes.

**QA scenarios**

- Happy: given the architecture doc, a reviewer can map `prepare`, `validate-draft`, `confirm`, and `render` to `TailoringApplicationService` without consulting `.omo`.
- Failure: an added `streamlit` import in `career_ai.tailoring` makes `tests/test_architecture_boundaries.py` fail with the offending file path.

**Verification**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_architecture_boundaries.py -q
git diff --check
```

**Commit**: `docs(architecture): define skill-first harness-core boundary`

---

- [x] Task 2 — Make the canonical Skill valid and fix Codex/Claude discovery

### Task 2 — Make the canonical Skill valid and fix Codex/Claude discovery

**Files**

- Modify: `src/career_ai/skills/career_resume_tailor/SKILL.md`
- Modify: `src/career_ai/skills/career_resume_tailor/agents/openai.yaml`
- Modify: `src/career_ai/skills/career_resume_tailor/references/workflow.md`
- Modify: `src/career_ai/skills/installation.py:20-193`
- Modify: `src/career_ai/host_init_cli.py:17-37`
- Modify: `scripts/install-agent.ps1:108-186`
- Modify: `scripts/install-agent.sh:112-185`
- Modify: `tests/test_skill_init.py:18-129`
- Modify: `tests/test_packaging_smoke.py:9-41`

**Work**

1. Add YAML frontmatter with a stable `name` and a specific `description` that states what the Skill does and when it should trigger.
2. Keep `SKILL.md` as a concise index: authority rule, five-step workflow, stop conditions, and direct links to the four one-level references. Remove generic explanation the host already knows.
3. Validate or regenerate `agents/openai.yaml` against the current Codex Skill metadata format; do not preserve the custom `protocol: openai-agents` field if it is not part of the accepted schema.
4. Reduce `HostAgent` to `codex`, `claude`, and `all`.
5. Install paths:
   - Codex: `.agents/skills/career-resume-tailor/`
   - Claude Code: `.claude/skills/career-resume-tailor/`
6. Replace misleading `protocol`/`template` installation metadata with one accurate Agent-Skill format marker plus host and target. Update the installation-record schema atomically.
7. Preserve idempotence, canonical bundle hashing, and `exists-different` behavior. Never overwrite a differing user-owned file.
8. Update both installers to install only the two supported hosts and to consume the machine-readable init result.
9. Add tests for valid frontmatter, correct discovery paths, identical policy/reference bytes, no OpenCode result, idempotence, user-file preservation, and clean-wheel resource discovery.

**Must not**

- Do not create a Claude plugin manifest or call this a plugin.
- Do not add a DeepSeek installation path.
- Do not duplicate the Skill body for each host.

**Acceptance criteria**

- `init --agent all` returns exactly two installations.
- Codex and Claude copies have identical `SKILL.md` and reference files.
- `.claude/plugins/career-resume-tailor` is no longer produced or documented.
- Existing differing Skill content remains byte-identical and reports `exists-different`.
- The canonical Skill passes the local Skill validator and package smoke test.

**QA scenarios**

- Happy: in a fresh temporary workspace, `init --agent all` creates both official project Skill paths and a stable installation record.
- Failure: when `.claude/skills/career-resume-tailor/SKILL.md` already contains user text, init reports a conflict and does not change the file.

**Verification**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_skill_init.py tests\test_packaging_smoke.py -q
.\.venv\Scripts\ruff.exe check src\career_ai\skills src\career_ai\host_init_cli.py tests\test_skill_init.py
.\.venv\Scripts\basedpyright.exe src\career_ai\skills src\career_ai\host_init_cli.py tests\test_skill_init.py
```

**Commit**: `fix(skill): install valid Codex and Claude project skills`

---

- [x] Task 3 — Strengthen the host protocol and add deterministic conformance cases

### Task 3 — Strengthen the host protocol and add deterministic conformance cases

**Files**

- Modify: `src/career_ai/tailoring/host_run_models.py:61-108`
- Modify: `src/career_ai/tailoring/host_run_validation.py:61-234`
- Modify: `src/career_ai/tailoring/host_run_render.py:51-245`
- Modify: `src/career_ai/host_proposal_output.py:28-113`
- Modify: `src/career_ai/host_proposal_cli.py:32-206`
- Create: `evals/host_skill_cases/accepted_structured.json`
- Create: `evals/host_skill_cases/needs_confirmation.json`
- Create: `evals/host_skill_cases/rejected_unsupported_claim.json`
- Create: `evals/host_skill_cases/stale_tampered.json`
- Create: `tests/test_host_skill_conformance.py`
- Modify: `tests/test_host_proposal_cli.py:24-181`
- Modify: `tests/test_host_proposal_cli_render.py:28-176`
- Modify: `tests/test_host_structured_package_cli_render.py:35-177`
- Modify: `tests/test_phase9_render_manifest.py`

**Work**

1. Extend `HostValidationResult` with relative `validation_artifact`, `finding_count`, stable `finding_codes`, and `next_machine_instruction` fields.
2. Keep detailed findings in the validation artifact; do not duplicate resume/JD text into CLI summaries.
3. Ensure every `HostRenderItem` provides either rendered artifact+manifest evidence or a typed failure/unavailable/stale code.
4. Build four data-driven conformance cases around one synthetic resume/JD. Bind run IDs and source/template hashes at test runtime rather than checking in forged dynamic identifiers.
5. Execute every case through public CLI commands in a fresh temporary workspace. Assert run isolation, exact states, artifact hashes, no render on non-accepted cases, and no absolute path leakage in JSON output.
6. Preserve current strict-JSON behavior: fenced Markdown, extra fields, tampered hashes, unknown run IDs, and prompt-injection instructions remain data or fail at a typed boundary.
7. Test two independent `prepare` calls create distinct run directories and cannot overwrite one another. Document same-run concurrent mutation as unsupported; do not add a locking subsystem.

**Must not**

- Do not call a model provider in conformance tests.
- Do not make renderer availability look like validation failure.
- Do not loosen existing factual safety, adequacy, confirmation, stale, or render-manifest checks.

**Acceptance criteria**

- Conformance JSON contains every trust-evidence field listed in this plan.
- Accepted case renders DOCX and its content-addressed manifest; negative cases create no rendered output.
- The exact same cases are reusable by Codex, Claude, and a future DeepSeek adapter without host-specific expected decisions.
- Missing/empty case directory is a hard failure, not a zero-case success.

**QA scenarios**

- Happy: accepted structured fixture reaches `accepted`, renders DOCX, and the returned SHA-256 matches the file and render manifest.
- Failure: changing one source hash after acceptance produces `stale`/typed rejection and no new output artifact.

**Verification**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_host_skill_conformance.py tests\test_host_proposal_cli.py tests\test_host_proposal_cli_render.py tests\test_host_structured_package_cli_render.py tests\test_phase9_render_manifest.py -q
.\.venv\Scripts\ruff.exe check src\career_ai\tailoring src\career_ai\host_proposal_cli.py src\career_ai\host_proposal_output.py tests\test_host_skill_conformance.py
.\.venv\Scripts\basedpyright.exe src\career_ai\tailoring src\career_ai\host_proposal_cli.py src\career_ai\host_proposal_output.py tests\test_host_skill_conformance.py
```

**Commit**: `feat(harness): expose host trust evidence and conformance cases`

---

- [x] Task 4 — Replace Agent-backed analysis/evals with a deterministic application service

### Task 4 — Replace Agent-backed analysis/evals with a deterministic application service

**Files**

- Create: `src/career_ai/application/career_fit_service.py`
- Create: `src/career_ai/workflows/quality.py`
- Create: `src/career_ai/workflows/run_record.py`
- Move: `src/career_ai/llm/boundary_harness.py` -> `src/career_ai/workflows/factual_boundary.py`
- Modify: `src/career_ai/application/__init__.py:1-8`
- Modify: `src/career_ai/workflows/career_fit.py:15-32`
- Modify: `src/career_ai/cli.py:92-160`
- Modify: `src/career_ai/evals/runner.py:21-54`
- Modify: `src/career_ai/evals/failure_corpus.py:8-205`
- Replace: `tests/test_agent_quality.py` -> `tests/test_workflow_quality.py` and `tests/test_career_fit_service.py`
- Replace: `tests/test_agent_trace.py` -> `tests/test_workflow_run_record.py`
- Move/update: `tests/test_boundary_harness.py` -> `tests/test_workflow_factual_boundary.py`
- Modify: `tests/test_cli.py:100-173`
- Modify: `tests/test_eval_runner.py`
- Modify: `tests/test_failure_corpus.py`

**Work**

1. Create a small `CareerFitApplicationService` that runs `run_career_fit_workflow`, applies deterministic quality checks, and returns one typed `CareerFitRunResult` containing workflow output, quality, and a privacy-safe run record.
2. Move only deterministic quality checks out of `career_ai.agent.quality`. Do not carry over the optional model evaluator/optimizer.
3. Move the factual boundary out of the misleading `llm` namespace without changing its validation behavior.
4. Define neutral run records around the operation actually performed:
   - run ID and operation name,
   - final status,
   - resume/JD character counts,
   - deterministic workflow step names,
   - quality check names/codes/status,
   - expected behavior.
   Exclude provider, Agent mode, planned tool calls, retry budget, tool catalog, full input, absolute paths, and credentials.
5. Redirect `analyze` to the new service. Human output retains role, match score, best prompt strategy, quality, audit ID, and failed checks. Add `--output json` for the complete typed result.
6. Redirect `run_eval_suite` to the same deterministic service and remove its `LLMClient` parameter.
7. Update failure-corpus conversion to accept the neutral run record and preserve redaction plus accepted-before-convert rules.
8. Keep `failure-to-eval` and its exit behavior. Update its schema/tests rather than deleting the feedback loop.
9. Keep each new pure-Python module below 250 logical lines; split models/helpers only when the measured line count requires it.

**Must not**

- Do not call any model client from `analyze`, `eval`, quality, factual boundary, or failure conversion.
- Do not preserve old output fields merely to simulate autonomy.
- Do not weaken factual checks while moving their module.

**Acceptance criteria**

- `src/career_ai/cli.py`, `src/career_ai/evals/runner.py`, and `src/career_ai/evals/failure_corpus.py` contain no `career_ai.agent` or `career_ai.llm` import.
- `analyze --output json` validates against the new typed result and contains no personal input body or absolute path.
- Existing deterministic eval cases produce the same graded pass/fail outcomes as before the migration.
- Failure-corpus records still remove emails, phones, credentials, and local paths and still refuse unaccepted conversion.
- Old Agent quality/trace tests are removed only after their deterministic/safety assertions exist in the replacement tests.

**QA scenarios**

- Happy: deterministic sample input returns a stable role/score/quality result and a run record with only counts, step names, and check codes.
- Failure: a failed quality check becomes a redacted failure candidate and cannot be converted until its review state is `accepted`.

**Verification**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_career_fit_service.py tests\test_workflow_quality.py tests\test_workflow_run_record.py tests\test_workflow_factual_boundary.py tests\test_eval_runner.py tests\test_failure_corpus.py tests\test_cli.py -q
.\.venv\Scripts\ruff.exe check src\career_ai\application src\career_ai\workflows src\career_ai\evals src\career_ai\cli.py
.\.venv\Scripts\basedpyright.exe src\career_ai\application src\career_ai\workflows src\career_ai\evals src\career_ai\cli.py
.\.venv\Scripts\career-ai-agent.exe analyze --resume-text "Built typed Python workflows." --jd-text "Role: Python Engineer" --output json
```

**Commit**: `refactor(harness): replace agent analysis with deterministic service`

---

- [x] Task 5 — Prove Codex/Claude host behavior and define the DeepSeek adapter seam

### Task 5 — Prove Codex/Claude host behavior and define the DeepSeek adapter seam

**Files**

- Create: `docs/verification/host-skill-smoke.md`
- Create: `docs/integrations/deepseek-harness.md`
- Modify: `src/career_ai/skills/career_resume_tailor/references/workflow.md`
- Modify: `src/career_ai/skills/career_resume_tailor/references/proposal-contract.md`
- Modify: `tests/test_host_skill_conformance.py`
- Modify: `tests/test_skill_init.py`
- Reference: `evals/host_skill_cases/*.json`
- Reference: `src/career_ai/tailoring/proposal_contracts.py:75-270`
- Reference: `src/career_ai/tailoring/state_machine.py:34-236`

**Work**

1. Add a host smoke runbook that always starts from a new temporary repository/workspace and a freshly installed wheel.
2. Run two actual fresh-session scenarios per current host when the binaries/auth are available:
   - accepted structured proposal through DOCX render,
   - invented/JD-only claim blocked before rendering.
3. For Codex, install only the `.agents/skills/...` copy and run from that temporary workspace. For Claude Code, install only `.claude/skills/...` and run from its temporary workspace. Do not expose both copies in one smoke.
4. Record a redacted summary: host/version, case ID, commands observed, final state, finding codes, relative artifacts, hashes, and pass/fail. Never commit full resumes, full host transcripts, tokens, or absolute user paths.
5. Require the host to use explicit JSON files—not inline JSON, heredocs, or parsing fenced Markdown—and to obey `needs_confirmation`, repair cap, stale, and render gates.
6. Define the DeepSeek adapter as a producer/consumer of the same task-package and proposal JSON protocol. The document must specify:
   - strict structured proposal output,
   - state/reasoning replay requirements are adapter/version capabilities rather than core assumptions,
   - unsupported parameters/capabilities fail explicitly,
   - no host-specific field may enter the canonical proposal contract,
   - all four no-network conformance cases must pass before any live adapter is called supported.
7. Cite current official DeepSeek behavior as time-sensitive implementation guidance, not a permanent hard-coded model profile. Keep model IDs and tool-call capabilities outside the core schema.
8. Add tests ensuring the Skill references every required command/stop condition and the DeepSeek document points to the canonical schema rather than duplicating it.

**Must not**

- Do not create a fake DeepSeek install result or hard-code a DeepSeek directory.
- Do not treat installation-copy tests as live host proof.
- Do not require multiple collaborating agents; each smoke is one host session using the one Skill.

**Acceptance criteria**

- Codex and Claude each have one redacted happy-path result and one redacted safety-failure result from isolated fresh sessions.
- Both hosts call the same CLI commands and yield the same local states/codes for equivalent inputs.
- The DeepSeek integration document is sufficient for a later adapter implementer to run the four existing fixtures without changing core contracts.
- No committed verification artifact contains secrets, source document bodies, or absolute personal paths.

**QA scenarios**

- Happy: a fresh Claude Code session discovers the project Skill, prepares a run, writes strict proposal JSON, validates it, and renders only after `accepted`.
- Failure: a fresh Codex session is asked to add an unsupported JD-only technology; local validation rejects it and the session does not invoke render.

**Verification**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_skill_init.py tests\test_host_skill_conformance.py -q
```

Fresh temporary workspace setup plus live `codex exec` and `claude -p --output-format json` invocations follow `docs/verification/host-skill-smoke.md`; record only the redacted result fields defined above and never install smoke assets into the source checkout.

**Commit**: `test(hosts): verify Codex Claude and DeepSeek protocol seam`

---

- [x] Task 6 — Remove direct provider generation from the high-trust lifecycle

### Task 6 — Remove direct provider generation from the high-trust lifecycle

**Files**

- Modify: `src/career_ai/application/tailoring_service.py:53-176`
- Modify: `src/career_ai/host_proposal_cli.py:32-206`
- Modify: `src/career_ai/tailoring/generation_workflow.py:58-104`
- Modify: `src/career_ai/tailoring/host_run_validation.py:113-162`
- Modify: `src/career_ai/tailoring/host_run_store.py`
- Modify: `src/career_ai/streamlit_app/main.py:136-178` (freeze-compatible removal only)
- Modify: `tests/test_application_service.py`
- Modify: `tests/test_host_proposal_cli.py:111-149`
- Modify: `tests/test_tailoring_generation.py:37-127`
- Modify: `tests/test_host_structured_package_cli_render.py:35-177`

**Work**

1. Remove `LLMClient` injection and `_resolved_llm_client` from `TailoringApplicationService`.
2. Remove `tailor_with_api` from the service, host-run store, and validation module.
3. Remove `run_api_proposal_workflow`; retain deterministic local strategy generation and host-proposal validation only where they remain used and tested.
4. Remove the `tailor` command's provider mode. Migrate structured-package tests and documentation to `validate-draft`, which already accepts the union proposal schema.
5. If `tailor --host-proposal` is purely an alias after this change, remove the command rather than retaining two names for the same operation.
6. During the Streamlit freeze, remove the API-generation control and keep only host-proposal/workspace review needed until Task 8. Do not redesign the page.
7. Add negative tests that monkeypatch any provider-client builder to fail if invoked during prepare, validate, confirm, render, analyze, or eval.

**Must not**

- Do not delete the entire `llm` package yet; Task 7 removes it after all Agent consumers are gone.
- Do not remove deterministic factual-boundary code moved in Task 4.
- Do not replace provider generation with a hidden subprocess or network call.

**Acceptance criteria**

- The high-trust lifecycle has exactly one proposal authority path: host writes strict JSON; Harness validates it.
- `TailoringApplicationService` constructor takes workspace only.
- Public lifecycle tests pass with no provider settings or API key.
- Structured render-ready packages still reach accepted/rendered state through `validate-draft` and `render`.
- Streamlit, while still present, exposes no API-model generation control.

**QA scenarios**

- Happy: `prepare -> validate-draft <structured-package> -> render` succeeds with provider construction patched to raise.
- Failure: invoking the removed provider form of `tailor` returns a clear unknown-command/deprecation error and performs no network access.

**Verification**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_application_service.py tests\test_host_proposal_cli.py tests\test_host_structured_package_cli_render.py tests\test_tailoring_generation.py -q
.\.venv\Scripts\ruff.exe check src\career_ai\application src\career_ai\tailoring src\career_ai\host_proposal_cli.py
.\.venv\Scripts\basedpyright.exe src\career_ai\application src\career_ai\tailoring src\career_ai\host_proposal_cli.py
```

**Commit**: `refactor(core): make host proposals the only model boundary`

---

- [x] Task 7 — Delete the custom Agent runtime, provider layer, and fake matrix

### Task 7 — Delete the custom Agent runtime, provider layer, and fake matrix

**Files**

- Delete: `src/career_ai/agent/`
- Delete: `src/career_ai/llm/` after `boundary_harness.py` has moved in Task 4
- Delete: `src/career_ai/evals/model_harness_matrix.py`
- Modify: `src/career_ai/evals/__init__.py`
- Modify: `src/career_ai/cli.py:37-248`
- Modify: `src/career_ai/host_doctor_cli.py:16-62`
- Modify: `pyproject.toml:5-67`
- Modify: dependency lock file, if present
- Delete/replace: `tests/test_agent_enforcement.py`
- Delete/replace: `tests/test_agent_memory.py`
- Delete/replace: `tests/test_agent_recovery.py`
- Delete/replace: `tests/test_agent_recovery_runtime.py`
- Delete/replace: `tests/test_agent_runtime.py`
- Delete/replace: `tests/test_agent_tool_catalog.py`
- Delete/replace: `tests/test_agent_tools.py`
- Delete: `tests/test_llm_capabilities.py`
- Delete: `tests/test_llm_client.py`
- Delete: `tests/test_model_harness_matrix.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/test_public_api.py:1-21`

**Work**

1. Confirm by import scan that Tasks 4 and 6 removed every production consumer of planner, executor, tool registry/catalog, execution loop, recovery, enforcement, memory, Agent trace, model client/settings/capabilities, and model matrix.
2. Delete `career_ai.agent` as a package. Do not move Tool Catalog or runtime enforcement into the core; their authority belonged to the removed in-process Agent loop.
3. Delete the direct `career_ai.llm` provider package after the deterministic factual boundary has moved.
4. Delete the fake-only `eval-matrix` command and module. Keep the deterministic `eval` command plus host conformance tests as the meaningful gates.
5. Rewrite `doctor` to report local Harness facts only: package/CLI status, host Skill resource/install status, workspace support, and renderer availability. It must explicitly say embedded model provider is absent/host-owned.
6. Remove provider-only dependencies (`pydantic-settings`, `python-dotenv`, and any now-unused dependency found by import scan). Keep `httpx` if JD fetching still uses it; keep Playwright because HTML/PDF rendering still uses it.
7. Delete implementation-specific tests only after replacement tests from Tasks 3-6 cover:
   - factual and adequacy gates,
   - strict proposal parsing,
   - state/confirmation/stale behavior,
   - privacy-safe run records,
   - deterministic quality/evals,
   - no-provider host lifecycle.
8. Add a hard architecture assertion that no production Python file imports `career_ai.agent` or `career_ai.llm`.

**Must not**

- Do not preserve a fake provider just to make old tests green.
- Do not delete `httpx` or Playwright without checking their non-Agent consumers.
- Do not remove safety tests simply because their old module name included `agent`; move the assertion if the safety property remains relevant.

**Acceptance criteria**

- `rg "career_ai\.(agent|llm)" src tests` has no production hits and only intentional historical/documentation references, if any.
- `career-ai-agent --help` does not list `eval-matrix` or provider-backed `tailor`.
- `doctor` contains no fake/OpenAI/DeepSeek provider profile and clearly reports host-owned reasoning.
- Package imports and public API tests pass without the deleted packages.
- Full test, lint, and type gates pass before proceeding to Streamlit removal.

**QA scenarios**

- Happy: `career-ai-agent analyze` and `eval` run with all provider environment variables unset and produce deterministic results.
- Failure: attempting to invoke `eval-matrix` or import `career_ai.agent` fails clearly; no compatibility shim silently recreates the old runtime.

**Verification**

```powershell
rg -n "career_ai\.(agent|llm)|run_career_agent|eval-matrix|build_llm_client|LLMSettings" src tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
```

**Commit**: `refactor(core): remove embedded agent and model runtime`

---

- [x] Task 8 — Retire Streamlit and all UI-only state

### Task 8 — Retire Streamlit and all UI-only state

**Files**

- Delete: `app.py`
- Delete: `src/career_ai/streamlit_app/`
- Delete: `static/app_theme.css`
- Delete: `src/career_ai/history.py`
- Delete: `src/career_ai/legacy_history.py`
- Delete: `tests/test_app_layout.py`
- Delete: `tests/test_app_theme.py`
- Delete: `tests/test_app_security.py`
- Delete: `tests/test_history.py`
- Delete: `tests/test_legacy_history_adapter.py`
- Modify: `tests/test_workspace.py:25-72`
- Modify: `src/career_ai/application/__init__.py`
- Modify: `src/career_ai/application/tailoring_service.py:1-176`
- Modify: `src/career_ai/skills/installation.py:185-193`
- Modify: `pyproject.toml:8-22,64-67`

**Entry gate**

- Task 3 conformance cases pass.
- Task 5 has one successful and one safety-failure smoke for both Codex and Claude.
- No business rule exists only in Streamlit; source review confirms all accepted/rendered decisions come from `TailoringApplicationService` and typed artifacts.

**Work**

1. Delete the Streamlit launcher, package, CSS theme, and source-string UI tests.
2. Delete UI-only upload/history adapters and their tests. Preserve an existing user `.career_ai/history.json` file on disk; removal means the package stops reading it, not that installation deletes user data.
3. Keep the workspace regression proving workspace initialization does not modify an existing legacy history file.
4. Remove `streamlit` from project dependencies and `app.py` from BasedPyright include configuration.
5. Remove `static/app_theme.css` from packaged Skill/resource declarations. Do not remove renderer HTML/CSS templates or Playwright assets.
6. Update service/package docstrings that still say “CLI, Skills, and Streamlit.”
7. Tighten architecture tests: no source, test, package data, or entrypoint may import/reference Streamlit as a product surface. Domain sample text may still contain the word “Streamlit” as a candidate skill and must not be mechanically rewritten.

**Must not**

- Do not delete `.career_ai/history.json` from any workspace.
- Do not delete Playwright or HTML rendering because Streamlit is removed.
- Do not replace Streamlit with another UI in this migration.

**Acceptance criteria**

- `streamlit` is absent from runtime dependencies and production imports.
- Root `app.py`, UI package, theme, and UI-only tests are gone.
- CLI/Skill prepare, validation, confirmation, rendering, workspace replay, and trust evidence still pass unchanged.
- Wheel contains renderer assets but no Streamlit/UI assets.
- No user data deletion code is introduced.

**QA scenarios**

- Happy: after uninstalling Streamlit from a fresh environment, the wheel installs and all CLI/Skill workflows and DOCX/HTML renderer tests pass.
- Failure: an existing `.career_ai/history.json` remains byte-identical after `init`, `prepare`, and workspace creation even though legacy UI replay code is gone.

**Verification**

```powershell
rg -n "import streamlit|from streamlit|streamlit_app|static/app_theme.css" src tests pyproject.toml
if (Test-Path -LiteralPath app.py) { throw "app.py must be removed" }
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
```

Domain fixture text mentioning Streamlit is not a failure; only product imports, entrypoints, package data, or setup guidance are prohibited.

**Commit**: `refactor(product): retire the Streamlit compatibility UI`

---

- [ ] Task 9 — Finalize packaging/docs and remove tracked OMO process artifacts

### Task 9 — Finalize packaging/docs and remove tracked OMO process artifacts

**Files**

- Modify: `README.md`
- Modify: `README.en.md`
- Modify: `README.zh.md`
- Modify: `docs/agent-install.md`
- Modify: `docs/architecture/skill-first-harness-core.md`
- Modify: `docs/roadmaps/harness-first-roadmap.md`
- Modify: `docs/superpowers/plans/2026-07-10-harness-first-roadmap.md` (superseded notice only)
- Modify: `docs/verification/host-skill-smoke.md`
- Modify: `scripts/install-agent.ps1`
- Modify: `scripts/install-agent.sh`
- Modify: `pyproject.toml`
- Modify: dependency lock file, if present
- Modify: `.gitignore`
- Remove: tracked `.omo/boulder.json`, `.omo/start-work/`, `.omo/evidence/`, completed tracked `.omo/plans/`, and other tracked OMO process files after migration bookkeeping is complete
- Preserve: all unrelated untracked files, including pre-existing untracked `.omo/plans/*.md`

**Work**

1. Update package description and all current docs to the final host-native Skill/Harness architecture.
2. Make install docs lead with Codex and Claude Code paths, the retained commands, local-only authority, and the four conformance cases. Remove Streamlit, OpenCode, fake provider, API key, Tool Catalog, Agent runtime, `tailor`, and `eval-matrix` instructions.
3. Mark the old harness-first roadmap as historical/superseded where it claims permanent authority. Keep truthful historical results, but point current work to the new architecture document.
4. Update both install scripts to run `doctor`, `init --agent all`, deterministic `eval`, and host-conformance tests; remove `eval-matrix` and web startup assumptions.
5. Build wheel/sdist and inspect contents: canonical Skill, four references, valid metadata, schemas, prompts, renderer assets, and CLI entrypoint present; Agent/LLM/Streamlit/OMO process assets absent.
6. Install the wheel into a new temporary virtual environment and run the CLI smoke, both Skill installs, deterministic eval, and conformance suite from outside the source tree.
7. Consolidate only durable OMO knowledge into normal docs:
   - architecture decisions and removal rationale,
   - factual/privacy/render invariants,
   - current command contract,
   - verification commands and known environment limits.
8. Enumerate tracked OMO files with `git ls-files .omo`. Remove only those tracked paths after all plan tasks and release verification are recorded. Do not enumerate broad paths and delete untracked content.
9. Add `.omo/` to `.gitignore` so future planning state remains local and does not re-enter the product repository.
10. Leave historical worklogs intact even when they mention OMO or Streamlit; they are records, not current instructions.

> **Repository cleanup supersession (2026-08-17):** the `repository-mainline-cleanup` work
> executed this task's historical OMO-artifact removal ahead of schedule. The pre-cleanup tree is
> preserved immutably at tag `pre-slim-main-2026-08-17` and browsably at branch
> `archive/pre-slim-main-2026-08-17` (personal plans under `archive/personal-plans/`). Steps 7–9
> now reduce to verifying that tracked `.omo` process artifacts are gone and `.omo/` is ignored,
> rather than repeating the removal. See `docs/maintenance/repository-mainline-cleanup.md`.

**Must not**

- Do not delete untracked user planning files.
- Do not claim live DeepSeek support.
- Do not include host transcripts, credentials, personal source text, or absolute user paths in docs.
- Do not remove the `.omo` plan/state until execution bookkeeping and all release gates are finished.

**Acceptance criteria**

- Current README/install/architecture docs contain no instruction to use `.omo`, Streamlit, OpenCode, fake providers, direct model APIs, `tailor`, or `eval-matrix`.
- Historical worklogs may retain those terms but are clearly not current setup guidance.
- Fresh-wheel CLI and both Skill installs work outside the checkout.
- Wheel inventory contains no `career_ai.agent`, `career_ai.llm`, Streamlit app, or OMO artifacts.
- `git status --short` shows unrelated pre-existing untracked files preserved.
- Tracked `.omo` files are removed only in the final cleanup commit and `.omo/` is ignored afterward.

**QA scenarios**

- Happy: a new user follows only `docs/agent-install.md`, installs the wheel, initializes Codex or Claude, runs eval/conformance, and sees where trust artifacts are stored.
- Failure: if a fresh-wheel run imports from the source checkout, misses Skill references, or writes over an existing user Skill, packaging verification fails and OMO cleanup does not proceed.

**Verification**

```powershell
.\.venv\Scripts\python.exe -m build
.\.venv\Scripts\python.exe -m pytest tests\test_packaging_smoke.py tests\test_skill_init.py tests\test_host_skill_conformance.py -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
git diff --check
git ls-files .omo
git status --short
```

**Commit**: `chore(release): ship the Skill-first Harness-core product`

---

## Final Verification Wave

- [ ] F1 — Architecture and scope audit

### F1 — Architecture and scope audit

- Confirm the final import graph matches the ownership table.
- Confirm no custom reasoning loop, provider client, UI, or OMO process dependency remains.
- Confirm no unrelated feature/refactor was introduced.
- Confirm all pre-existing unrelated worktree changes are still present.

- [ ] F2 — Contract and safety audit

### F2 — Contract and safety audit

- Run accepted, confirmation, rejected, and stale/tampered host cases.
- Inspect request, validation, accepted document, and render manifests for correct hashes and relative paths.
- Confirm strict JSON and prompt-injection tests still fail safely.
- Confirm failure records remain privacy-safe and conversion remains review-gated.

- [ ] F3 — Real host and artifact QA

### F3 — Real host and artifact QA

- Repeat one fresh Codex accepted flow and one fresh Claude accepted flow from isolated workspaces.
- Repeat one unsupported-claim rejection on each host.
- Open the resulting DOCX and at least one PDF/HTML artifact when its renderer is available; report unavailable LaTeX engines honestly rather than treating them as a code failure.
- Compare rendered artifact hashes/manifests with CLI output.

- [ ] F4 — Clean package and repository hygiene

### F4 — Clean package and repository hygiene

- Build and install the wheel outside the checkout.
- Run full tests, Ruff, BasedPyright, doctor, eval, conformance, and `git diff --check`.
- Inspect wheel contents and public command help.
- Verify current docs are self-contained and tracked `.omo` artifacts are gone while unrelated untracked files remain.

---

## Rollback checkpoints

- After Task 3: old runtime and UI still exist; host protocol changes can be reverted without data migration.
- After Task 4: `analyze`, eval, and failure corpus use the new neutral service; old Agent code is still available only for comparison until Task 7.
- After Task 6: high-trust lifecycle is host-only; revert this task alone if a missing provider-dependent contract is discovered.
- Before Task 7: run the full gate and capture the import scan. Do not delete if any production consumer remains.
- Before Task 8: require Codex/Claude live smoke evidence and artifact parity.
- Before OMO cleanup: finish all implementation/review bookkeeping and verify normal docs contain every durable rule.

## Expected final repository shape

```text
src/career_ai/
  application/        # deterministic use-case services
  workflows/          # career-fit workflow, factual boundary, quality, run records
  tailoring/          # proposal contracts, safety, adequacy, state, host lifecycle
  workspace/          # local versioned state and source ingestion
  rendering/          # DOCX/HTML/PDF/LaTeX renderers and manifests
  evals/              # deterministic cases, graders, failure corpus
  skills/             # one canonical career-resume-tailor Skill
  cli.py               # thin command composition
evals/
  career_cases/
  tailoring_cases/
  host_skill_cases/
docs/
  architecture/
  integrations/
  verification/
```

Intentionally absent: `career_ai/agent`, `career_ai/llm`, `career_ai/streamlit_app`, `app.py`, and tracked `.omo` process state.
