# Personal Reusable Skill Evolution Plan

## TL;DR

> **Summary**: Build a personal Skill distillation workflow inspired by SkillClaw: real project work becomes reusable, non-project-bound Codex Skills through extraction, abstraction, validation, and iteration.
> **Deliverables**: personal Skill taxonomy, extraction protocol, first Skill candidates seeded from `F:\AGENT`, validation loop, and evolution/maintenance rules.
> **Effort**: Medium
> **Parallel**: NO
> **Critical Path**: Source sessions -> reusable patterns -> candidate Skills -> validation -> personal library.

## Core Reframe

The goal is not to create `F:\AGENT-debug-skill`.

The goal is to create a personal skill-making system:

1. mine real projects for repeated failure/repair patterns;
2. strip away project-specific nouns;
3. preserve the useful decision procedure;
4. package it as a concise Codex Skill;
5. validate it on a different task;
6. keep improving it as new sessions reveal better patterns.

`F:\AGENT` is the first source corpus, not the final target.

## SkillClaw-Inspired Design Principles

- Skills should evolve from real interactions, not imagined best practices.
- A single user can benefit first with a local Skill library; shared/team evolution is optional later.
- Session history must be digested, deduplicated, and verified before becoming a Skill.
- Candidate Skills should be inspected and validated before being published into the everyday library.
- Skill assets should be portable across agents and devices when possible.

## What to Extract from `F:\AGENT`

| Project-specific observation | Reusable personal Skill lesson |
| --- | --- |
| `.omo` plan, Boulder, ledger, evidence, and worklog were needed to resume correctly. | Build a `resume-from-checkpoint` Skill for finding the real continuation point before editing. |
| Silent eval success with zero cases looked green but was wrong. | Build a `truthful-verification` Skill that treats empty tests, known failures, and optional dependency warnings honestly. |
| BadZipFile, FileNotFoundError, stale render, no LaTeX engine, browser errors all needed stable boundaries. | Build a `typed-boundary-debugging` Skill for turning raw crashes into typed, user-facing failure modes. |
| Host/model proposals had to be revalidated locally before rendering. | Build a `local-authority-validation` Skill for workflows where AI output is proposal-only, never authority. |
| Browser-visible Streamlit bugs needed real health/browser/console checks. | Build a `browser-visible-qa` Skill for UI bugs where passing unit tests is insufficient. |
| Installer bugs only appeared in fresh PowerShell/Git Bash/raw GitHub paths. | Build a `fresh-install-release-qa` Skill for package/install/release verification. |
| Worklogs and evidence made later agents much better. | Build a `worklog-to-skill-miner` Skill that turns completed worklogs into reusable lessons. |

## Proposed Personal Skill Set

Start small. Do not create one giant "do everything" Skill.

### 1. `resume-from-checkpoint`

Use when a project has interrupted plans, partial work, dirty worktrees, previous evidence, or user says continue/resume/finish.

Core procedure:

- read plan state;
- read execution ledger/state;
- inspect evidence artifacts;
- check worklog summary;
- only then decide whether to code, verify, document, or ask.

### 2. `truthful-verification`

Use when tests, evals, release gates, doctor checks, or QA output might be misleading.

Core procedure:

- reject empty-green results;
- separate known honest limitations from real regressions;
- preserve visible known failures until fixed;
- require focused proof plus proportional full gates.

### 3. `typed-boundary-debugging`

Use when a raw runtime exception leaks through a user-facing or agent-facing boundary.

Core procedure:

- reproduce the raw failure;
- identify the boundary owner;
- map raw exception to typed/domain error;
- test the bad input path;
- verify the user-facing message and exit/status behavior.

### 4. `local-authority-validation`

Use when AI/model/host output should be treated as a proposal requiring local validation.

Core procedure:

- keep source facts local and immutable;
- require strict machine-readable input;
- reject Markdown-wrapped or schema-drifting payloads;
- gate side effects on accepted current-hash state.

### 5. `fresh-install-release-qa`

Use when a tool/package/repo must work outside the developer's warm local environment.

Core procedure:

- create clean temp root;
- install from published/raw path, not local files;
- verify selected runtime versions;
- run doctor/eval/smoke gates;
- clean temp artifacts and record evidence.

## Skill Architecture

Each Skill should be compact:

```text
skill-name/
  SKILL.md
  references/
    workflow.md
    failure-patterns.md
  templates/
    evidence.md
```

Only add scripts when a repeated command sequence is fragile enough to justify deterministic automation.

## Distillation Workflow

### Step 1. Collect source material

For each completed project slice, collect:

- user request;
- final result;
- errors encountered;
- root causes;
- fix decisions;
- verification commands;
- known limitations;
- what should be done differently next time.

### Step 2. Normalize the lesson

Rewrite each lesson from:

> In `F:\AGENT`, `career-ai-agent eval` silently passed with a missing case directory.

to:

> When a verifier reports success over an empty input set, treat it as a verifier bug. Add an explicit empty/missing input failure path and assert non-zero status.

### Step 3. Cluster lessons

Group lessons by recurring action, not by project:

- checkpoint continuation;
- truthful verification;
- typed error boundaries;
- local validation authority;
- browser-visible QA;
- fresh install/release QA;
- artifact/worklog mining.

### Step 4. Draft candidate Skill

For each cluster, write:

- trigger description;
- 5-8 step workflow;
- hard guardrails;
- evidence template;
- minimal examples.

### Step 5. Validate outside the source project

A Skill is not reusable until it works on a second context.

Example validations:

- apply `truthful-verification` to a different repo with a suspicious green test result;
- apply `typed-boundary-debugging` to a CLI exception outside `F:\AGENT`;
- apply `resume-from-checkpoint` to `F:\CHK` or another interrupted workspace.

### Step 6. Publish to personal library

After validation:

- install under `C:\Users\Sherlock Lee\.codex\skills\<skill-name>`;
- keep source examples in references, not in the main body;
- run `quick_validate.py`;
- optionally sync/evolve later with a SkillClaw-like local library.

## First Implementation Wave

- [ ] 1. Create `worklog-to-skill-miner` as the meta-Skill.
  - Purpose: turn project logs/evidence into reusable personal Skills.
  - Why first: it becomes the factory for all later Skills.

- [ ] 2. Create `truthful-verification`.
  - Seed examples: empty eval success, known LaTeX no-engine boundary, known missing-keywords signal.
  - Validation: apply to one non-`F:\AGENT` verification transcript.

- [ ] 3. Create `resume-from-checkpoint`.
  - Seed examples: `.omo` plan/Boulder/ledger/evidence/worklog chain.
  - Validation: apply to another interrupted roadmap or dirty worktree.

- [ ] 4. Create `typed-boundary-debugging`.
  - Seed examples: `BadZipFile`, render-before-validation `FileNotFoundError`, missing eval directory.
  - Validation: apply to a different CLI/runtime exception.

## Success Criteria

- The first three personal Skills trigger by task pattern, not project name.
- Each Skill is useful even when `F:\AGENT` is never mentioned.
- Each Skill has at least one seed example and one out-of-source validation example.
- Project-specific details live in references/examples; SKILL.md remains short and procedural.
- The personal library becomes cumulative: every serious project can feed future Skill improvements.

## Open Decisions

- Whether to install the first wave directly under `C:\Users\Sherlock Lee\.codex\skills` or keep a staging folder first.
- Whether to install/run SkillClaw locally now, or use its design manually first and adopt the tool after the workflow stabilizes.
- Whether your personal Skills should be Chinese-first, English-first, or bilingual. Recommended: English frontmatter for trigger stability, Chinese explanations/examples where they preserve your thinking style.
