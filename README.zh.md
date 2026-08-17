# AI Career Intelligence Suite

[![Python](https://img.shields.io/badge/python-3.12+-blue)](https://www.python.org/)
[![Hosts](https://img.shields.io/badge/hosts-Codex%20%7C%20Claude%20Code-8A2BE2)](#)

本地优先、宿主原生的职业工作流工具包：可复用 Agent Skill + 确定性校验与渲染 Harness CLI。

> 最后更新：2026-08-17。Skill-first / Harness-core 迁移已全部完成（Task 1–9）。

## 项目概览

AI Career Intelligence Suite 是一个本地优先、宿主原生的职业工作流工具包。真正的
推理 Agent 是宿主运行时——当前为 Codex 与 Claude Code，并已定义 DeepSeek Harness
adapter seam——本仓库提供可复用的 Skill 与确定性的本地 Harness，后者掌握验证、
确认、状态与渲染的最终权威。

宿主负责理解意图并起草一份严格 JSON proposal；Skill 规定工作流；本地 Harness 负责
事实校验、状态门禁与渲染，仅渲染已接受的 structured package。仓库内没有内嵌模型
provider，也没有进程内 Agent 循环：推理由宿主所有，Harness 保持模型中立。

## 当前状态

截至 2026-08-17，九个迁移任务已全部完成：

- 架构职责固定为 Host Agent → Skill → deterministic Harness → domain/workspace/rendering。
- canonical Skill 安装到 `.agents/skills/`（Codex）与 `.claude/skills/`（Claude Code），
  不会覆盖用户已有的不同文件。
- 自定义 Agent 运行时、内嵌 provider 层、fake model matrix 已全部移除。
- Streamlit 与所有纯 UI 状态已退役；包不再导入或分发网页 UI。
- host proposal 是唯一的模型边界：宿主写严格 JSON，本地 Harness 负责验证。
- `analyze` 与 deterministic eval 共用 `CareerFitApplicationService`；quality、factual
  boundary 与 privacy-safe run record 归属中性。
- DeepSeek harness adapter seam 已记录于 `docs/integrations/deepseek-harness.md`。

最终验证记录：

- 完整测试套件 -> `313 passed`
- `ruff check .` -> passed
- `basedpyright` -> `0 errors, 0 warnings, 0 notes`
- `career-ai-agent doctor` -> 渲染器、Skill 与 host-owned provider 检查通过
- `career-ai-agent eval` -> `3 passed, 0 failed`
- `git diff --check` -> passed

环境诚实状态：本机未安装 Tectonic 或 XeLaTeX。`.tex`、DOCX、HTML-PDF 可生成，而
`latex-pdf` 会返回明确的 `latex_no_engine`，直到本机安装 LaTeX engine。

## 能力范围

已包含：

- 面向 Agent 宿主的跨主机 Skill，以及确定性的 `career-ai-agent` Harness CLI
- 简历/JD 分析、匹配分数、缺口关键词、事实保持型 bullet rewrite、cover letter
- 确定性 application service、quality checks、factual boundary、privacy-safe run record
- 确定性 eval，以及脱敏 failure-to-eval 反馈回路（强制 accepted-before-convert）
- 高可信 resume tailoring workspace、source hashes、proposal hashes、validation lifecycle
- DOCX、HTML、HTML-PDF、system LaTeX `.tex`、user-template LaTeX 检查/修补
- Render manifest、live hash revalidation、stale artifact blocking
- DeepSeek harness adapter seam（设计指引）与宿主 smoke runbook

明确不包含：

- 登录、支付、云部署、多用户数据库
- 私有文档 RAG、职位网站扫描、申请追踪、自动投递
- 邮件、日历、网盘、Notion 等外部操作集成
- 内嵌模型 provider、进程内 Agent 循环、网页 UI
- 在未经本地 validation 的情况下让模型直接改写或渲染用户材料

## 用 Agent 安装

把下面这段提示词复制给 Codex 或 Claude Code，让 Agent 直接安装本项目：

```text
安装这个项目：https://github.com/18032580582lhw-star/Career-AI-AGENT

阅读 docs/agent-install.md，然后创建 Python 3.12 虚拟环境，
pip install -e .，并运行：career-ai-agent doctor、
career-ai-agent init --workspace . --agent all、
career-ai-agent eval --case-dir evals/career_cases --prompt-dir prompts。
逐字报告 doctor 与 eval 的结果。
```

或者自己运行已审查的安装脚本：

```powershell
# Windows
irm https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.ps1 -OutFile install-agent.ps1
.\install-agent.ps1 -RepoUrl "https://github.com/18032580582lhw-star/Career-AI-AGENT.git" -Agent all
```

```bash
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/scripts/install-agent.sh -o install-agent.sh
bash install-agent.sh --repo-url "https://github.com/18032580582lhw-star/Career-AI-AGENT.git" --agent all
```

完整手动步骤：[Agent 安装指南](docs/agent-install.md)。

## 快速开始

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\career-ai-agent.exe doctor
```

Codex / Claude Code 直接调用已安装的 Skill 与 CLI。若要让宿主从 GitHub 项目链接自动
安装本地 Skill，请参阅 [Agent 安装指南](docs/agent-install.md)。

## CLI 常用命令

基础 Harness 分析：

```powershell
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe analyze `
  --resume-text "Product analyst using Python SQL Streamlit dashboards." `
  --jd-text "Role: AI Product Analyst. Requires Python, SQL, Streamlit, LLM evaluation."
.\.venv\Scripts\career-ai-agent.exe analyze `
  --resume-text "Built typed Python workflows." `
  --jd-text "Role: Python Engineer" `
  --output json
```

确定性 eval：

```powershell
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
```

高可信简历定制工作流：

```powershell
.\.venv\Scripts\career-ai-agent.exe init --workspace . --agent all
.\.venv\Scripts\career-ai-agent.exe prepare --workspace . --resume-file resume.txt --jd-file jd.txt
.\.venv\Scripts\career-ai-agent.exe validate-draft --workspace . --run-id <run-id> --proposal-file proposal.json
.\.venv\Scripts\career-ai-agent.exe confirm --workspace . --run-id <run-id> --confirmation-file confirmation.json
.\.venv\Scripts\career-ai-agent.exe render --workspace . --run-id <run-id> --format all
```

输出模式：

- `analyze` 默认为人类可读摘要。
- `analyze --output json` 返回完整、可校验且移除来源正文的 `CareerFitRunResult` JSON。
- host proposal 命令继续支持其各自的 `result` / `process` / `json` 输出协议。

Renderer 安装检查：

```powershell
.\.venv\Scripts\career-ai-agent.exe install-renderer --html
.\.venv\Scripts\career-ai-agent.exe install-renderer --latex
```

`--html` 会安装 Playwright Chromium。`--latex` 不会静默安装系统 TeX，只会检查
Tectonic/XeLaTeX 并输出平台安装指引。

## 开发验证标准

修改 prompts、tailoring harness、renderer、CLI 或 Skill 后，运行：

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
```

文档和 Markdown-only 变更至少运行：

```powershell
git diff --check
```

## 架构导览

宿主 Agent 负责理解意图并起草 proposal；Skill 定义工作流；本地 Harness 掌握 source
ingestion、validation、confirmation 与 rendering 的最终权威。CLI 是 Harness 的适配器，
仓库内没有内嵌 Agent 或 provider。

- `src/career_ai/cli.py`：Typer CLI 根入口
- `src/career_ai/workflows/`：career-fit workflow、确定性 quality、factual boundary、run record
- `src/career_ai/application/`：CLI/宿主共用的 career-fit 与 tailoring application services
- `src/career_ai/evals/`：eval cases、graders、deterministic runner、failure corpus
- `src/career_ai/workspace/`：versioned workspace、source ingestion、safe storage
- `src/career_ai/tailoring/`：高可信 tailoring contracts、extraction、safety、adequacy、state machine
- `src/career_ai/rendering/`：DOCX、HTML、HTML-PDF、LaTeX renderers 和 renderer registry
- `src/career_ai/skills/career_resume_tailor/`：打包的跨主机 Skill
- `docs/architecture/skill-first-harness-core.md`：当前正式架构与迁移边界
- `docs/integrations/deepseek-harness.md`：DeepSeek harness adapter seam
- `docs/verification/host-skill-smoke.md`：真实宿主 smoke runbook
- `docs/maintenance/repository-mainline-cleanup.md`：仓库维护收据与历史归档索引

历史任务证据与已完成计划已归档至不可变 tag `pre-slim-main-2026-08-17` 与分支
`archive/pre-slim-main-2026-08-17`，详见维护文档。
