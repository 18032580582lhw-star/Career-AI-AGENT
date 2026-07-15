# AI Career Intelligence Suite

> 最后更新：2026-07-14。内容依据仓库路线图、`.omo` 任务账本、证据文件和每日工作日志整理。

## 项目概览

AI Career Intelligence Suite 是一个本地优先、模型中立的职业智能代理。它从一个
Streamlit 简历/JD 分析 MVP，演进为带有确定性评测、运行轨迹、运行时安全边界、
高可信简历定制、跨主机 Skill、DOCX/HTML-PDF/LaTeX 渲染链和 CLI 工作流的完整本地
工具。

项目默认使用 `fake` provider，因此无需 API key 即可运行核心流程。接入
OpenAI-compatible、DeepSeek-compatible 或其他兼容网关时，仍然通过同一个 typed
provider capability contract、同一套本地 harness 和同一套安全边界执行。

## 当前状态

截至 2026-07-14，两个主要阶段已经完成：

- Harness-first 职业代理路线图已完成：provider capability、eval bank、eval matrix、
  privacy-safe trace、failure corpus、Tool Catalog v2、runtime enforcement、
  privacy-preserving memory、bounded evaluator、controlled autonomy，以及 CLI/Streamlit
  Trust & Quality 视图。
- 高可信简历定制路线图已完成：versioned workspace、immutable source ingestion、
  candidate fact / JD requirement extraction、Safety/Adequacy harness、proposal lifecycle、
  accepted-document gate、DOCX/HTML-PDF/LaTeX rendering、host proposal CLI、render manifest、
  cross-host Skill installation、Streamlit 统一视图和 release verification。

最终验证记录：

- `python -m pytest -q` -> `348 passed`
- `ruff check .` -> passed
- `basedpyright` -> `0 errors, 0 warnings, 0 notes`
- `career-ai-agent doctor` -> HTML renderer / Skill / no-API checks pass
- `career-ai-agent eval` -> `3 passed, 0 failed`
- `career-ai-agent eval-matrix` -> `fake-default passed=3 failed=0`
- `git diff --check` -> passed

环境诚实状态：当前机器未发现 Tectonic 或 XeLaTeX，所以 `.tex`、DOCX 和 HTML-PDF 可以
生成，但 `latex-pdf` 会返回明确的 `latex_no_engine`，直到本机安装 LaTeX engine。

## 能力范围

已包含：

- Streamlit 本地 UI 和 `career-ai-agent` CLI
- 简历文本、上传文件、JD 文本和 JD URL 输入
- 职位分析、匹配分数、缺口关键词、事实保持型 bullet rewrite、cover letter
- Prompt strategy compatibility surface，以及本地多策略 tailoring workflow
- 模型中立 agent runtime、tool registry、tool catalog、recovery 和 controlled autonomy
- Provider capability doctor、deterministic eval、model-harness eval matrix
- Privacy-safe run trace、failure-to-eval、deterministic quality report
- Runtime enforcement：tool call、memory write、network fetch、export、external action 边界
- 高可信 resume tailoring workspace、source hashes、proposal hashes、validation lifecycle
- Safety Harness、Adequacy Harness、needs-confirmation / rejected / stale / accepted 状态机
- DOCX、HTML、HTML-PDF、system LaTeX `.tex`、user-owned `resume.tex` inspection/patching
- Render manifest、live hash revalidation、stale artifact blocking
- Codex / Claude Code / OpenCode 的 `career-resume-tailor` Skill 安装
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

打开 Streamlit 本地地址后，可以使用示例材料，也可以上传 `.txt`、`.pdf` 或 `.docx`
简历，并输入 JD 文本或 URL。

如果想让 Codex、Claude Code 或 OpenCode 通过 GitHub 项目链接自动安装本地 agent，
请使用 [Agent Install Guide](docs/agent-install.md)。

## CLI 常用命令

基础 agent 分析：

```powershell
.\.venv\Scripts\career-ai-agent.exe doctor
.\.venv\Scripts\career-ai-agent.exe analyze `
  --resume-text "Product analyst using Python SQL Streamlit dashboards." `
  --jd-text "Role: AI Product Analyst. Requires Python, SQL, Streamlit, LLM evaluation."
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

- `--output result`：默认，只显示结果摘要
- `--output process`：显示摘要和过程 JSON
- `--output json`：纯机器可读 JSON

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

- `app.py`：Streamlit 入口，委托到 `career_ai.streamlit_app`
- `src/career_ai/cli.py`：Typer CLI 根入口
- `src/career_ai/workflows/`：传统 career-fit workflow
- `src/career_ai/agent/`：agent planner、executor、tool catalog、trace、quality、memory、policy
- `src/career_ai/evals/`：eval cases、graders、runner、model-harness matrix、failure corpus
- `src/career_ai/workspace/`：versioned workspace、source ingestion、safe storage
- `src/career_ai/tailoring/`：高可信 tailoring contracts、extraction、safety、adequacy、state machine
- `src/career_ai/rendering/`：DOCX、HTML、HTML-PDF、LaTeX renderers 和 renderer registry
- `src/career_ai/application/`：CLI/UI 共用的 tailoring application service
- `src/career_ai/skills/career_resume_tailor/`：打包的跨主机 Skill
- `docs/roadmaps/harness-first-roadmap.md`：人类可读 harness-first 交付状态
- `docs/superpowers/plans/2026-07-10-harness-first-roadmap.md`：canonical harness contract
- `.omo/plans/high-trust-resume-skill-latex.md`：高可信简历定制与 LaTeX 路线图
- `.omo/evidence/`：每个任务的验证证据
