# AI Career Intelligence Suite

> 最后更新：2026-08-17。当前完成 Skill-first / Harness-core 迁移 Task 1–4。

## 项目概览

AI Career Intelligence Suite 是一个本地优先、模型中立的职业工作流工具包。真正的
Agent 是宿主运行时——当前优先支持 Codex 和 Claude Code，后续计划适配 DeepSeek
Harness；本仓库提供可复用 Skill，以及掌握本地校验与渲染权威的确定性 Harness。
它从 Streamlit 简历/JD 分析 MVP 演进为宿主原生工作流：宿主负责推理和起草 proposal，
Skill 规定操作顺序，本地 Harness 负责事实校验、状态门禁和渲染。网页版本目前冻结为可选
演示界面，不是核心运行时。

项目默认使用 `fake` provider，因此无需 API key 即可运行核心流程。接入
OpenAI-compatible、DeepSeek-compatible 或其他兼容网关时，仍然通过同一个 typed
provider capability contract、同一套本地 harness 和同一套安全边界执行。

## 当前状态

截至 2026-08-17，本轮迁移已经完成 Task 1–4：

- 架构职责已固定为 Host Agent → Skill → deterministic Harness → domain/workspace/rendering。
- canonical Skill 符合 Agent Skills 结构，项目级安装目标为 Codex 的 `.agents/skills/` 和
  Claude Code 的 `.claude/skills/`；安装不会覆盖用户已有的不同文件。
- host validation 返回 typed evidence，包括状态、finding codes、相对 artifact 和下一条机器指令。
- `analyze` 与 deterministic eval 共用 `CareerFitApplicationService`，不再经过旧 Agent executor；
  quality、factual boundary 和 privacy-safe run record 已迁到中性 workflow/application 层。
- `analyze --output json` 返回完整 `CareerFitRunResult` schema，但移除来源正文、凭证和绝对路径。

最终验证记录：

- 非打包测试 -> `367 passed`
- wheel packaging smoke -> `1 passed`
- `ruff check .` -> passed
- `basedpyright` -> `0 errors, 0 warnings, 0 notes`
- `career-ai-agent doctor` -> HTML renderer / Skill / no-API checks pass
- `career-ai-agent eval` -> `3 passed, 0 failed`
- `git diff --check` -> passed

环境诚实状态：当前机器未发现 Tectonic 或 XeLaTeX，所以 `.tex`、DOCX 和 HTML-PDF 可以
生成，但 `latex-pdf` 会返回明确的 `latex_no_engine`，直到本机安装 LaTeX engine。

## 能力范围

已包含：

- 面向 Agent 宿主的跨主机 Skill，以及确定性的 `career-ai-agent` Harness CLI
- 用于演示和人工检查的可选 Streamlit 本地 UI
- 简历文本、上传文件、JD 文本和 JD URL 输入
- 职位分析、匹配分数、缺口关键词、事实保持型 bullet rewrite、cover letter
- Prompt strategy compatibility surface，以及本地多策略 tailoring workflow
- 确定性 application service、quality checks、privacy-safe run record 和 factual boundary
- Provider capability doctor、deterministic eval，以及兼容期内保留的 model-harness matrix
- 脱敏 failure-to-eval 反馈回路，并强制 accepted-before-convert
- Runtime enforcement：tool call、memory write、network fetch、export、external action 边界
- 高可信 resume tailoring workspace、source hashes、proposal hashes、validation lifecycle
- Safety Harness、Adequacy Harness、needs-confirmation / rejected / stale / accepted 状态机
- DOCX、HTML、HTML-PDF、system LaTeX `.tex`、user-owned `resume.tex` inspection/patching
- Render manifest、live hash revalidation、stale artifact blocking
- Codex / Claude Code 的 `career-resume-tailor` Skill 安装
- Legacy `.career_ai/history.json` 只读兼容 replay

明确不包含：

- 登录、支付、云部署、多用户数据库
- 私有文档 RAG、职位网站扫描、申请追踪、自动投递
- 邮件、日历、网盘、Notion 等外部操作集成
- 在未经本地 validation 的情况下让模型直接改写或渲染用户材料

## 快速开始

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\streamlit.exe run app.py --server.headless=true --server.port=8508
```

Streamlit 仍可用于演示和人工检查，但当前推荐直接由 Codex / Claude Code 调用 Skill 和 CLI。

如果想让 Codex 或 Claude Code 通过 GitHub 项目链接自动安装本地 Skill，
请使用 [Agent Install Guide](docs/agent-install.md)。

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

Harness 验证：

```powershell
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
.\.venv\Scripts\career-ai-agent.exe eval-matrix --case-dir evals\career_cases --prompt-dir prompts
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
- `analyze --output json`：完整、可校验且移除来源正文的 `CareerFitRunResult` JSON。
- host proposal 命令继续支持其各自的 `result` / `process` / `json` 输出协议。

Renderer 安装检查：

```powershell
.\.venv\Scripts\career-ai-agent.exe install-renderer --html
.\.venv\Scripts\career-ai-agent.exe install-renderer --latex
```

`--html` 会安装 Playwright Chromium。`--latex` 不会静默安装系统 TeX，只会检查
Tectonic/XeLaTeX 并输出平台安装指引。

## 开发验证标准

修改 prompts、provider、tool catalog、runtime policy、tailoring harness、renderer 或 UI
后，运行：

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\ruff.exe check .
.\.venv\Scripts\basedpyright.exe
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe eval --case-dir evals\career_cases --prompt-dir prompts
.\.venv\Scripts\career-ai-agent.exe eval-matrix --case-dir evals\career_cases --prompt-dir prompts
```

文档和 Markdown-only 变更至少运行：

```powershell
git diff --check
```

## 架构导览

宿主 Agent 负责理解意图并起草 proposal；Skill 定义工作流；本地 Harness 掌握 source
ingestion、validation、confirmation 与 rendering 的最终权威。CLI 和 Streamlit 只是
Harness 的适配器，而不是两套独立的自主 Agent。

- `app.py`：Streamlit 入口，委托到 `career_ai.streamlit_app`
- `src/career_ai/cli.py`：Typer CLI 根入口
- `src/career_ai/workflows/`：career-fit workflow、确定性 quality、factual boundary、run record
- `src/career_ai/application/`：CLI/宿主共用的 career-fit 与 tailoring application services
- `src/career_ai/agent/`：迁移期兼容代码；不是 `analyze` / deterministic eval 的主路径
- `src/career_ai/evals/`：eval cases、graders、deterministic runner、failure corpus
- `src/career_ai/workspace/`：versioned workspace、source ingestion、safe storage
- `src/career_ai/tailoring/`：高可信 tailoring contracts、extraction、safety、adequacy、state machine
- `src/career_ai/rendering/`：DOCX、HTML、HTML-PDF、LaTeX renderers 和 renderer registry
- `src/career_ai/skills/career_resume_tailor/`：打包的跨主机 Skill
- `docs/architecture/skill-first-harness-core.md`：当前正式架构与迁移边界
- `docs/roadmaps/harness-first-roadmap.md`：人类可读 harness-first 交付状态
- `docs/superpowers/plans/2026-07-10-harness-first-roadmap.md`：canonical harness contract
- `.omo/plans/high-trust-resume-skill-latex.md`：高可信简历定制与 LaTeX 路线图
- `.omo/evidence/`：每个任务的验证证据
