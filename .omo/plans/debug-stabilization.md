# Debug Stabilization Plan

## TL;DR
> **Summary**: Build a repeatable, evidence-backed debugging campaign for the project’s highest-risk real runtime paths: install, CLI, Skill adapters, tailoring/rendering, Streamlit, and release consistency.
> **Deliverables**:
> - Fresh-install debug evidence for PowerShell and Git Bash/raw GitHub paths.
> - CLI and Skill adapter smoke/debug evidence.
> - High-trust tailoring/rendering debug evidence including no-engine LaTeX boundary.
> - Streamlit browser QA evidence.
> - Packaging/release consistency evidence and final audit.
> **Effort**: Medium
> **Parallel**: YES - 3 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 4 -> Task 6 -> Final Verification Wave

## Context
### Original Request
User asked: “做一个debug调试计划”.

### Interview Summary
No extra interview is required. The request follows a real debugging session that already found and fixed two installer bugs:
- PowerShell installer hardened against Windows PowerShell 5.1 native stderr handling.
- Bash installer skips unusable `python3` PATH stubs and falls back to working `python`.

### Metis Review (gaps addressed)
Gap-analysis review incorporated these corrections:
- Task 1 is now a foundation wave, because every later task depends on the evidence harness.
- Streamlit QA targets the current `Prepare` / `Generate with API` / `Validate host proposal` / `Render` workflow, not the legacy `Analyze` UI.
- GitHub raw validation must happen after any discovered fixes are pushed, otherwise it may test stale `main`.
- Git Bash validation must use `curl` inside Git Bash and must explicitly avoid WSL `bash`.
- Installer checks must verify the selected Python is `>=3.12`, not only that a `python` command exists.

Current defaults:
- Use fake/local provider only.
- Treat missing Tectonic/XeLaTeX as expected if `latex_no_engine` is explicit.
- Use isolated temp directories and `.omo/evidence/` artifacts for all runtime proof.

## Work Objectives
### Core Objective
Create a complete, repeatable debugging route that proves the project can be installed, initialized, evaluated, used from CLI/Streamlit, and packaged from a clean environment without hidden local-state assumptions.

### Deliverables
- `.omo/evidence/task-*.md` or `.json` evidence files with exact commands, exit codes, key stdout/stderr lines, and cleanup notes.
- Any minimal fixes discovered by the debug tasks, each with failing-first evidence and post-fix verification.
- Updated docs only if runtime behavior contradicts current docs.

### Definition of Done
- `git status -sb` shows only intentional fix/docs changes during execution, and is clean after final commit/push if the user asks to publish.
- `python -m pytest -q` or a temp-venv equivalent reports all tests passing.
- `career-ai-agent doctor`, `eval`, and `eval-matrix` pass from a clean installed environment.
- PowerShell and Git Bash GitHub raw install paths complete from isolated temp directories.
- Streamlit starts locally and a browser-visible smoke path is verified.
- All debug artifacts outside intended evidence files are removed.

### Must Have
- Runtime truth over code reading.
- Fresh temp workspace per install/debug scenario.
- Evidence files under `.omo/evidence/`.
- Red/green or failure/pass toggle for every fix.
- Commands usable from Windows/PowerShell first; Git Bash where relevant.

### Must NOT Have
- No new product features.
- No cloud deployment or external model dependency.
- No hiding known optional dependency failures.
- No editing user-owned resume/source files.
- No committing `.debug-journal.md`, temp logs, venvs, or local history.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: TDD for discovered bugs; tests-after only for pure environment harness where a unit seam does not exist.
- QA policy: Every task has agent-executed happy and failure/edge scenarios.
- Evidence: `.omo/evidence/task-{N}-{slug}.md` unless JSON is more appropriate.

## Execution Strategy
### Parallel Execution Waves
Wave 1: Task 1
Wave 2: Task 2, Task 3, Task 8
Wave 3: Task 4, Task 5, Task 6, Task 7

### Dependency Matrix
| Task | Depends On | Blocks |
| --- | --- | --- |
| 1. Debug Evidence Harness | none | 2, 3, 4, 5, 6, 7, 8 |
| 2. GitHub Raw Install Debug | 1 | 7, F3 |
| 3. Local CLI Harness Debug | 1 | 4, 5, F3 |
| 4. Skill Adapter Debug | 1, 3 | 6, F3 |
| 5. Eval And Quality Debug | 1, 3 | F3 |
| 6. Tailoring Render Debug | 1, 3, 4 | F3 |
| 7. Streamlit Browser Debug | 1, 2, 3 | F3 |
| 8. Packaging Release Debug | 1, 2, 3 | F1, F2, F4 |

## TODOs

- [x] 1. Debug Evidence Harness

  **What to do**: Establish the reusable debug discipline for this campaign. Create per-task evidence files under `.omo/evidence/`, use temp directories outside the repo for fresh installs, and record exact commands, exit codes, and key stdout/stderr. For any discovered bug, create `.debug-journal.md` locally and exclude it through `.git/info/exclude`, then remove it during cleanup.
  **Must NOT do**: Do not commit `.debug-journal.md`, temp logs, `.venv`, downloaded scripts, or raw user data.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: 2, 3, 4, 5, 6, 7, 8 | Blocked By: none

  **References**:
  - Pattern: `docs/agent-install.md` - documents the expected end-to-end install checks.
  - Pattern: `scripts/install-agent.ps1` - PowerShell install path to debug.
  - Pattern: `scripts/install-agent.sh` - Bash/Git Bash install path to debug.
  - Test infra: `pyproject.toml` - pytest, Ruff, BasedPyright configuration.

  **Acceptance Criteria**:
  - [ ] `.omo/evidence/task-1-debug-evidence-harness.md` exists and lists evidence format, temp root naming convention, cleanup checklist, and command capture rules.
  - [ ] Evidence format includes command, cwd, environment, exit code, key stdout, key stderr, interpretation, cleanup state.
  - [ ] `git status -sb` after task shows only the intended evidence file.

  **QA Scenarios**:
  ```text
  Scenario: Happy path evidence template
    Tool: powershell
    Steps: Create one evidence file with a dry-run command such as `git status -sb`.
    Expected: Evidence captures command, exit code 0, and current branch.
    Evidence: .omo/evidence/task-1-debug-evidence-harness.md

  Scenario: Cleanup checklist prevents artifact leakage
    Tool: powershell
    Steps: Create then remove a temp directory under $env:TEMP and record both checks.
    Expected: Evidence states temp path no longer exists.
    Evidence: .omo/evidence/task-1-debug-evidence-harness.md
  ```

  **Commit**: CONDITIONAL | Message: `docs: add debug evidence harness` | Files: `.omo/evidence/task-1-debug-evidence-harness.md`

- [x] 2. GitHub Raw Install Debug

  **What to do**: Re-run the real GitHub raw install path from isolated temp directories for both Windows PowerShell 5.1 and Git Bash. Use the raw URLs in `docs/agent-install.md`, not local scripts, to verify the public installation path. Capture stdout/stderr separately without letting PowerShell 5.1 native stderr handling contaminate the result. If execution discovers a fix, commit and push first, then repeat raw GitHub validation against `origin/main`.
  **Must NOT do**: Do not reuse repo `.venv`; do not rely on already downloaded scripts; do not count docs-only checks as install success.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 7, F3 | Blocked By: 1

  **References**:
  - Contract: `docs/agent-install.md` - install guide and expected baseline.
  - Script: `scripts/install-agent.ps1` - PowerShell behavior should match raw script.
  - Script: `scripts/install-agent.sh` - Git Bash behavior should match raw script.

  **Acceptance Criteria**:
  - [ ] PowerShell raw installer exits 0 in a clean temp root.
  - [ ] Git Bash raw installer exits 0 in a clean temp root.
  - [ ] PowerShell run uses Windows PowerShell 5.1 (`$PSVersionTable.PSVersion.Major -eq 5`) for native stderr regression coverage.
  - [ ] Git Bash run uses `C:\Program Files\Git\bin\bash.exe` or another verified Git Bash path, not `C:\Windows\system32\bash.exe`.
  - [ ] Git Bash run performs `curl -fsSL ...install-agent.sh` inside Bash, matching `docs/agent-install.md`.
  - [ ] Both installers record the selected Python executable and confirm `python --version` is `>=3.12`.
  - [ ] Both runs show `Passed cases: 3`, `Failed cases: 0`, and `fake-default ... passed=3 failed=0`.
  - [ ] Evidence records any non-fatal stderr, including Git clone progress or Python venv path notices.
  - [ ] All temp install roots are removed after evidence capture.

  **QA Scenarios**:
  ```text
  Scenario: PowerShell raw install
    Tool: powershell
    Steps: Download install-agent.ps1 from raw.githubusercontent.com into a temp root, run with -RepoUrl and -Agent all.
    Expected: exit 0; doctor/init/eval/eval-matrix complete; no Command failed.
    Evidence: .omo/evidence/task-2-github-raw-install-powershell.md

  Scenario: Git Bash raw install
    Tool: powershell + Git Bash Start-Process
    Steps: Start C:\Program Files\Git\bin\bash.exe with a BOM-free runner.sh that runs `curl -fsSL https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.sh -o "$root/install-agent.sh"` inside Bash, then runs `bash "$root/install-agent.sh" --repo-url ... --install-root "$root" --agent all`.
    Expected: exit 0; skipped unusable python candidates do not abort; eval/eval-matrix pass.
    Evidence: .omo/evidence/task-2-github-raw-install-bash.md
  ```

  **Commit**: CONDITIONAL | Message: `test: record raw install debug evidence` | Files: `.omo/evidence/task-2-*`

- [x] 3. Local CLI Harness Debug

  **What to do**: In a clean temp venv or known local dev venv, run CLI commands that represent the main public surface: `doctor`, `analyze`, `eval`, `eval-matrix`, and renderer install checks. Confirm outputs match documented semantics and optional dependency failures remain explicit.
  **Must NOT do**: Do not suppress optional LaTeX engine failures; do not require external API keys.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 4, 5, 6, F3 | Blocked By: 1

  **References**:
  - CLI: `src/career_ai/cli.py` - root Typer commands and output.
  - Tests: `tests/test_cli.py` - expected CLI behavior.
  - Docs: `README.zh.md` and `README.en.md` - user-facing command examples.

  **Acceptance Criteria**:
  - [ ] `career-ai-agent doctor` exits 0 and prints provider/model/render/Skill status.
  - [ ] `career-ai-agent analyze --resume-text ... --jd-text ...` exits 0 and prints quality PASS plus trace id.
  - [ ] `career-ai-agent eval --case-dir evals\career_cases --prompt-dir prompts` exits 0 with 3 passed, 0 failed.
  - [ ] `career-ai-agent eval-matrix ...` exits 0 with fake-default passed.
  - [ ] `career-ai-agent install-renderer --latex` does not pretend missing engines are installed.

  **QA Scenarios**:
  ```text
  Scenario: CLI happy path
    Tool: powershell
    Steps: Run doctor, analyze, eval, eval-matrix from an installed CLI.
    Expected: all exit 0; quality and eval outputs match baseline.
    Evidence: .omo/evidence/task-3-cli-happy-path.md

  Scenario: Optional renderer boundary
    Tool: powershell
    Steps: Run install-renderer --latex and doctor on a host without Tectonic/XeLaTeX.
    Expected: guidance or FAIL status is explicit; command behavior matches current contract.
    Evidence: .omo/evidence/task-3-cli-renderer-boundary.md
  ```

  **Commit**: CONDITIONAL | Message: `test: record cli debug evidence` | Files: `.omo/evidence/task-3-*`

- [x] 4. Skill Adapter Debug

  **What to do**: Verify `career-ai-agent init --workspace <temp> --agent all` installs Codex/OpenCode and Claude adapter files exactly once, preserves user-owned conflicts, and records package resources and skill hash.
  **Must NOT do**: Do not overwrite existing user Skill files; do not mutate real user `$CODEX_HOME` or Claude config outside the temp workspace.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 6, F3 | Blocked By: 1, 3

  **References**:
  - CLI registration: `src/career_ai/host_init_cli.py`
  - Installer: `src/career_ai/skills/installation.py`
  - Tests: `tests/test_skill_init.py`
  - Packaged Skill: `src/career_ai/skills/career_resume_tailor/SKILL.md`

  **Acceptance Criteria**:
  - [ ] Fresh temp workspace has `.agents/skills/career-resume-tailor/SKILL.md`.
  - [ ] Fresh temp workspace has `.claude/plugins/career-resume-tailor/SKILL.md`.
  - [ ] `.career_ai/skill-installations.json` exists and validates as JSON.
  - [ ] Re-running init is idempotent.
  - [ ] Pre-existing conflicting `SKILL.md` is preserved and reports `exists-different`.

  **QA Scenarios**:
  ```text
  Scenario: all-host install
    Tool: powershell
    Steps: Run init twice in a temp workspace with --agent all.
    Expected: first installed/present statuses, second stable; skill hash unchanged.
    Evidence: .omo/evidence/task-4-skill-all-hosts.md

  Scenario: user-owned conflict
    Tool: powershell
    Steps: Pre-create .agents/skills/career-resume-tailor/SKILL.md with custom text, run init --agent codex.
    Expected: file bytes unchanged; JSON reports exists-different.
    Evidence: .omo/evidence/task-4-skill-conflict.md
  ```

  **Commit**: CONDITIONAL | Message: `test: record skill adapter debug evidence` | Files: `.omo/evidence/task-4-*`

- [x] 5. Eval And Quality Debug

  **What to do**: Debug the deterministic eval and quality harness as a first-class runtime path. Capture failing-case details if any case regresses, and prove failure-to-eval conversion still writes redacted drafts.
  **Must NOT do**: Do not hide eval failures; do not change expected cases to make results green.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: F3 | Blocked By: 1, 3

  **References**:
  - Eval runner: `src/career_ai/evals/runner.py`
  - Eval matrix: `src/career_ai/evals/model_harness_matrix.py`
  - Graders: `src/career_ai/evals/graders.py`
  - Cases: `evals/career_cases/*.json`
  - Tests: `tests/test_eval_runner.py`, `tests/test_model_harness_matrix.py`, `tests/test_agent_quality.py`

  **Acceptance Criteria**:
  - [ ] `eval` reports 3 total, 3 passed, 0 failed.
  - [ ] `eval-matrix` reports 1 total row, 1 passed row, 0 failed rows.
  - [ ] If an eval fails, evidence includes exact failed check names and messages.
  - [ ] `failure-to-eval` is smoke-tested with a safe fixture or intentionally skipped with a documented blocker if no accepted fixture exists.

  **QA Scenarios**:
  ```text
  Scenario: deterministic eval pass
    Tool: powershell
    Steps: Run eval and eval-matrix against evals/career_cases and prompts.
    Expected: no failed checks; fake-default passes.
    Evidence: .omo/evidence/task-5-eval-quality.md

  Scenario: bad input boundary
    Tool: powershell
    Steps: Run eval with a missing case directory.
    Expected: non-zero or explicit failure message; no silent success with zero cases.
    Evidence: .omo/evidence/task-5-eval-bad-input.md
  ```

  **Commit**: CONDITIONAL | Message: `test: record eval debug evidence` | Files: `.omo/evidence/task-5-*`

- [x] 6. Tailoring Render Debug

  **What to do**: Exercise the high-trust proposal flow in a temp workspace: prepare, generate/validate a proposal, render all supported formats with live hash revalidation, and verify stale/unsafe/no-engine boundaries. For accepted happy path, use the fake-provider API path so no hand-authored proposal schema guessing is required: `career-ai-agent prepare --workspace <tmp> --resume-file <resume.txt> --jd-file <jd.txt> --output json`, parse `run_id`, then `career-ai-agent tailor --workspace <tmp> --run-id <run_id> --output json`, then `career-ai-agent render --workspace <tmp> --run-id <run_id> --format all --disable-latex-engines --output json`.
  **Must NOT do**: Do not use real personal resume data; do not patch source resume/template files; do not claim local LaTeX PDF success when engines are absent.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: F3 | Blocked By: 1, 3, 4

  **References**:
  - CLI: `src/career_ai/host_proposal_cli.py`
  - Service: `src/career_ai/application/tailoring_service.py`
  - Store/render: `src/career_ai/tailoring/host_run_store.py`, `src/career_ai/tailoring/host_run_render.py`
  - Rendering: `src/career_ai/rendering/`
  - Fixtures: `evals/tailoring_cases/*.json`
  - Tests: `tests/test_tailoring_golden_integration.py`, `tests/test_document_renderers.py`, `tests/test_user_latex_template.py`

  **Acceptance Criteria**:
  - [ ] Temp resume/JD prepare command creates a run id.
  - [ ] Fake-provider `tailor` path reaches accepted or explicit non-accepted state with full local validation details; accepted path is required for render happy path.
  - [ ] `render --format all --disable-latex-engines` produces DOCX/HTML-PDF/TEX where expected and explicit `latex_no_engine` for LaTeX PDF.
  - [ ] Stale artifact or hash mismatch blocks render with a non-zero/known exit code.
  - [ ] Malicious LaTeX fixture is blocked before engine execution.

  **QA Scenarios**:
  ```text
  Scenario: accepted render happy path
    Tool: powershell
    Steps: Use synthetic resume/JD, run prepare --output json, parse run_id, run tailor --output json with fake provider, then render all with --disable-latex-engines.
    Expected: accepted state, render manifest, output hashes, explicit no-engine boundary.
    Evidence: .omo/evidence/task-6-tailoring-render-happy.md

  Scenario: stale or unsafe render boundary
    Tool: powershell
    Steps: Mutate source hash or use malicious_latex fixture, then attempt render.
    Expected: render blocked with clear stale/unsafe code; no output artifact is trusted.
    Evidence: .omo/evidence/task-6-tailoring-render-boundary.md
  ```

  **Commit**: CONDITIONAL | Message: `test: record tailoring render debug evidence` | Files: `.omo/evidence/task-6-*`

- [x] 7. Streamlit Browser Debug

  **What to do**: Start Streamlit locally from an isolated temp working directory and verify the current user-visible tailoring workflow in a real browser path. Check page loads; `Resume file`, `Resume text`, `JD URL`, `Job description`, `resume.tex template`, `Prepare`, `Generate with API`, `Validate host proposal`, `Output format`, `Render`, and `Safety/Adequacy` surfaces exist. Use fake-provider generation for the accepted path where possible.
  **Must NOT do**: Do not rely only on `/_stcore/health`; do not skip browser interaction; do not use fake screenshots without opening the app.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: F3 | Blocked By: 1, 2, 3

  **References**:
  - Entry: `app.py`
  - App: `src/career_ai/streamlit_app/main.py`
  - History panel: `src/career_ai/streamlit_app/history_panel.py`
  - Tests: `tests/test_app_security.py`, `tests/test_app_layout.py`, `tests/test_history.py`

  **Acceptance Criteria**:
  - [ ] Streamlit process starts on a free local port and `/_stcore/health` returns healthy.
  - [ ] Browser-visible controls include current Prepare/Proposal/Render workflow controls.
  - [ ] Running sample prepare flow produces `Prepared run <run_id>` and no visible exception.
  - [ ] Generate with API or host proposal validation updates Safety/Adequacy state; if accepted, Render button becomes enabled.
  - [ ] QA captures screenshot or DOM-visible evidence of current workflow controls and no traceback.
  - [ ] Process is stopped and port is released.

  **QA Scenarios**:
  ```text
  Scenario: browser-visible tailoring workflow
    Tool: Playwright or in-app browser control
    Steps: Launch Streamlit from a temp cwd, open URL, fill Resume text and Job description, click Prepare, then exercise Generate with API or Validate host proposal.
    Expected: prepared run appears; Safety/Adequacy panel updates; no uncaught Streamlit error or traceback.
    Evidence: .omo/evidence/task-7-streamlit-browser.md

  Scenario: startup/teardown hygiene
    Tool: powershell
    Steps: Start Streamlit on selected port, query health, stop process, confirm no listener remains.
    Expected: health success while running; port free after teardown.
    Evidence: .omo/evidence/task-7-streamlit-teardown.md
  ```

  **Commit**: CONDITIONAL | Message: `test: record streamlit debug evidence` | Files: `.omo/evidence/task-7-*`

- [x] 8. Packaging Release Debug

  **What to do**: Verify a clean wheel/source install contains runtime package data, CLI entrypoint, skills, LaTeX templates, and fonts. Cross-check GitHub raw docs and scripts after any fixes are pushed, and verify raw content contains the expected current fix or commit-specific marker rather than merely returning HTTP 200.
  **Must NOT do**: Do not assume editable install proves wheel install; do not forget binary package data.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: F1, F2, F4 | Blocked By: 1, 2, 3

  **References**:
  - Packaging: `pyproject.toml`
  - Test: `tests/test_packaging_smoke.py`
  - Runtime assets: `src/career_ai/rendering/assets/fonts/`, `src/career_ai/rendering/latex/assets/system_resume.tex`
  - Skill assets: `src/career_ai/skills/career_resume_tailor/`
  - GitHub docs: `docs/agent-install.md`

  **Acceptance Criteria**:
  - [ ] `python -m pip wheel . --no-deps` succeeds in an isolated temp wheelhouse.
  - [ ] Wheel contains CLI entrypoint, Skill files, workflow references, system LaTeX template, and Noto font assets.
  - [ ] Installing the wheel into a temp venv exposes `career-ai-agent`.
  - [ ] GitHub raw install guide and both scripts return HTTP 200.
  - [ ] Raw `install-agent.ps1` contains `Invoke-Native`.
  - [ ] Raw `install-agent.sh` contains guarded `if "$candidate" --version >/dev/null 2>&1; then`.

  **QA Scenarios**:
  ```text
  Scenario: wheel contains runtime assets
    Tool: powershell
    Steps: Build wheel and inspect zip names.
    Expected: required skill/render/font assets present.
    Evidence: .omo/evidence/task-8-packaging-wheel.md

  Scenario: raw release surface
    Tool: powershell
    Steps: HEAD/GET README, docs/agent-install.md, install-agent.ps1, install-agent.sh from GitHub raw.
    Expected: all return 200 and contain current expected install logic, including the two installer hardening fixes.
    Evidence: .omo/evidence/task-8-github-raw-surface.md
  ```

  **Commit**: CONDITIONAL | Message: `test: record packaging release debug evidence` | Files: `.omo/evidence/task-8-*`

## Final Verification Wave
> ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [x] F1. Plan Compliance Audit
  - Verify every task produced evidence, cleaned temp artifacts, and either made no code changes or included a fix with red/green proof.
  - Command: `git status -sb; git diff --stat`

- [x] F2. Code Quality Review
  - Run static and test gates after all fixes.
  - Commands: `python -m pytest -q`, `ruff check .`, `basedpyright`, `git diff --check`, `git status -sb`

- [x] F3. Real Manual QA
  - Re-run at least one fresh GitHub install path and one Streamlit browser path after all changes.
  - Evidence: `.omo/evidence/f3-real-manual-qa.md`

- [x] F4. Scope Fidelity Check
  - Confirm changes stayed inside debug/fix/evidence scope and did not add product features or external dependencies.
  - Evidence: `.omo/evidence/f4-scope-fidelity.md`

## Commit Strategy
- Commit after each independent fix or evidence batch only when the user has asked to publish or the execution handoff explicitly allows commits.
- Use explicit path staging only.
- Suggested commit messages:
  - `test: record install debug evidence`
  - `fix: harden <specific runtime path>`
  - `test: record streamlit debug evidence`
  - `docs: update debug findings`

## Success Criteria
- All TODOs checked.
- All evidence files present.
- No temp/debug artifacts remain.
- Full gates pass or any environment-bound failure is documented honestly.
- GitHub raw install path remains usable by Codex, Claude Code, OpenCode, and a human.
