# High-Trust Resume Tailoring, Multi-Host Skills, and LaTeX

## TODOs

- [x] Task 0.1 Record and verify the existing harness baseline without touching unrelated changes.
- [x] Task 0.2 Add release-quality golden fixtures for factual safety, adequacy, and rendering.
- [x] Task 1.1 Implement versioned workspace manifest, safe path resolution, and atomic JSON writes.
- [x] Task 1.2 Implement immutable resume, JD, and LaTeX source ingestion with SHA-256 identity.
- [x] Task 1.3 Preserve legacy `.career_ai/history.json` as read-only compatibility data.
- [x] Task 2.1 Add typed evidence, candidate-fact, JD-requirement, and match contracts.
- [x] Task 2.2 Extract evidence-backed candidate facts and typed JD requirements.
- [x] Task 2.3 Remove JD-as-candidate-fact leakage and add confirmation-aware provenance.
- [x] Task 3.1 Add versioned tailoring task, proposal, change, finding, and decision contracts.
- [x] Task 3.2 Implement factual Safety Harness with stable violation codes.
- [x] Task 3.3 Implement optimization Adequacy Harness and acceptance thresholds.
- [x] Task 3.4 Implement accepted/needs-confirmation/rejected/stale state transitions and two-repair cap.
- [x] Task 4.1 Replace prompt-text scoring with three real proposal strategies and outcome grading.
- [x] Task 4.2 Integrate API-provider and host-proposal paths through one tailoring workflow.
- [x] Task 5.1 Add AcceptedResumeDocument, ATS normalization, and renderer registry.
- [x] Task 6.1 Upgrade DOCX rendering and add production HTML/Playwright PDF rendering.
- [x] Task 6.2 Implement HTML/CSS PDF rendering with Playwright Chromium, bundled Noto fonts, and CJK-safe mixed-language output.
- [x] Task 6.3 Implement HTML renderer installation checks, Chromium installer, and doctor coverage for browser/template/fonts/write permission.
- [x] Task 7.1 Add safe system LaTeX template, escaping, Tectonic-first compilation, and CJK support.
- [x] Task 8.1 Add user-owned `resume.tex` inspection, section mapping, safe patching, and compilation.
- [x] Task 9.1 Add render manifests, backend identity, hashes, and stale-artifact enforcement.
- [x] Task 10.1 Add machine-readable init/prepare/tailor/validate/confirm/inspect-latex/render/install-renderer CLI commands.
- [x] Task 10.2 Extend doctor for workspace, renderer, LaTeX engine, fonts, Skill, and no-API checks.
- [x] Task 11.1 Add canonical career-resume-tailor Skill and Codex/OpenCode/Claude adapters.
- [x] Task 11.2 Add idempotent host initialization and wheel/pipx package resources.
- [x] Task 12.1 Move Streamlit onto shared workspace/tailoring/rendering services.
- [x] Task 12.2 Add confirmation, trust evidence, renderer selection, LaTeX inspection, and legacy replay UI.
- [x] Task 13.1 Expand eval bank, packaging smoke tests, cross-host fixtures, and renderer security coverage.
- [x] Task 13.2 Complete final compatibility, security, manual UI, clean-install, and release verification.

## Final Verification Wave

- [x] F1 Plan compliance and scope-fidelity audit.
- [x] F2 Full pytest, Ruff, BasedPyright, doctor, eval, and eval-matrix verification.
- [x] F3 Real CLI, DOCX, HTML-PDF, LaTeX, and user-template manual QA with cleanup evidence.
- [x] F4 Codex, Claude Code, OpenCode, Streamlit, legacy-history, and clean-wheel acceptance review.

## Guardrails

- Keep the current `career-ai-agent`, `CareerFitReport`, fake provider, history replay, and trust surfaces compatible.
- Original resume, JD, and user LaTeX sources are immutable; only supported or confirmed facts authorize claims.
- Skill and host models produce proposals only; local typed validation remains authoritative.
- Render only accepted, current-hash artifacts. Never use shell escape or modify user-owned `.tex` in place.
- Exclude OCR, job-board scanning, application tracking, auto-apply, external messaging, auth, cloud, payments, multi-user storage, plugin marketplace, and full updater/rollback.
- Do not stage, commit, push, reset, or overwrite unrelated dirty-worktree changes.

## Verification Standard

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
.\.venv\Scripts\career-ai-agent.exe eval-matrix --case-dir evals\career_cases --prompt-dir prompts
```
