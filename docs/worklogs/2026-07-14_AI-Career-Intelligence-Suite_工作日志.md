# 2026-07-14 AI Career Intelligence Suite 工作日志

<!-- WORKLOG-SUMMARY:START -->
## 当日总结

尚未执行“总结日志”指令。
<!-- WORKLOG-SUMMARY:END -->

## 工作记录

### Phase 9/10 — Render Manifest 防篡改与无 API Host Proposal CLI

- 状态：已完成但未提交。
- 工作内容：完成高可信简历定制路线图 Phase 9 与 Phase 10。Render Manifest 现在记录 run id、proposal/validation/accepted-document/template/output hashes、template type、具体 renderer backend、engine、engine version、font bundle、页面大小和语言；`pdf` 这类笼统 backend 继续被拒绝，必须使用 `html-playwright`、`latex-tectonic` 或 `latex-xelatex` 等具体身份。
- 防篡改：新增 `.career_ai/runs/<run_id>` host-run 协议，持久化 request/context/proposal/validation/draft/candidate-facts/run-manifest/rendered artifacts。render 前会重新计算 source/template/proposal/validation/accepted-document hashes；验证后修改绑定模板会让旧 validation 进入 stale，且不产生新 artifact。
- CLI：新增或扩展 `init`、`prepare`、`validate-draft`、`confirm`、`tailor`、`render`、`inspect-latex`、`install-renderer --latex`。`validate-draft` 只接受严格 JSON，不从 Markdown code fence 猜测；Host Proposal 路径不构建 provider client；API 路径请求三策略 proposal 后仍进入同一组本地 Safety/Adequacy/state harness。
- Renderer：`render --format all` 支持 `docx`、`pdf`、`tex`、`latex-pdf`；缺少 LaTeX engine 时 `.tex`、DOCX、HTML-PDF 不受影响，`latex-pdf` 返回 `latex_no_engine`。
- Doctor/install：`doctor` 扩展 workspace、prompt/schema/template、Chromium、Tectonic、XeLaTeX、font bundle、LaTeX package cache、Skill、重复 Skill 和 no-API provider-call 检查；`install-renderer --latex` 不静默安装系统级 TeX 工具，只给平台安装指导。
- 验证情况：`python -m pytest -q` 为 332 passed；`ruff check .` 通过；`basedpyright` 为 0 errors、0 warnings、0 notes；`career-ai-agent doctor` 报告 HTML renderer available、Tectonic/XeLaTeX FAIL、LaTeX package cache WARN、No-API provider calls PASS；`eval` 和 `eval-matrix` 仍如实保留既有 `sample_product_analyst` 缺少 `dashboard storytelling` 与 `stakeholder communication` 的 missing-keywords 失败；`git diff --check` 通过。
- 证据：`.omo/evidence/task-9-10-render-manifest-host-cli.txt`、`.omo/start-work/ledger.jsonl` 末尾记录、`.omo/plans/high-trust-resume-skill-latex.md` 已勾选 Task 9.1、10.1、10.2。


### Phase 11/12 — Multi-host Skill、idempotent init 与 Streamlit 统一视图

- 状态：已完成但未提交。
- 工作内容：完成高可信简历定制路线图 Phase 11 与 Phase 12。新增 packaged canonical `career-resume-tailor` Skill，包含 `SKILL.md`、`references/workflow.md`、`references/fact-policy.md`、`references/proposal-contract.md`、`references/rendering.md` 与 `agents/openai.yaml`；Skill 只编排 `prepare -> host proposal -> validate -> confirm/repair -> render`，事实安全、确认状态和 LaTeX 安全策略继续由本地 CLI/Harness 执行。
- 宿主适配：新增 `career_ai.skills.installation` 与 `career-ai-agent init --workspace PATH --agent codex|claude|opencode|all`。Codex/OpenCode 共享 `.agents/skills/career-resume-tailor`，Claude 写入 `.claude/plugins/career-resume-tailor`；重复执行不会覆盖同名用户文件，init 输出记录 package、protocol、template、Skill hash 与 package resources。`pyproject.toml` 已纳入 packaged Skill resources。
- 共享服务：新增 `career_ai.application.TailoringApplicationService`，CLI 的 `prepare`、`validate-draft`、`confirm`、`tailor`、`render`、`inspect-latex` 改为经由共享 application service 进入 workspace/tailoring/rendering 逻辑，避免 UI 或宿主适配复制事实、验证、LaTeX patch/compile 逻辑。
- Streamlit：`app.py` 改为薄入口，新增 `src/career_ai/streamlit_app/`。新 UI 支持上传简历、输入 JD/URL、可选上传 `resume.tex`、Prepare、API 或 Host Proposal、Safety/Adequacy 状态、renderer 选择、LaTeX inspect、section mapping/unsafe findings/engine 状态展示、未 accepted 时禁用 render、workspace run replay 与 legacy summary-only replay。
- 验证情况：`.\.venv\Scripts\python.exe -m pytest -q` 通过（338 passed）；`.\.venv\Scripts\ruff.exe check .` 通过；`.\.venv\Scripts\basedpyright.exe` 通过（0 errors, 0 warnings, 0 notes）；`career-ai-agent doctor` 通过并显示 Skill hash，HTML renderer available，Tectonic/XeLaTeX FAIL、LaTeX package cache WARN；`init --agent all` 临时工作区探针首轮 installed/present、二轮全部 present；Streamlit health `http://127.0.0.1:8508/_stcore/health` 返回 `200 ok`。
- 已知失败保持：`career-ai-agent eval` 和 `career-ai-agent eval-matrix` 仍如实报告 `sample_product_analyst` 缺少 `dashboard storytelling` 与 `stakeholder communication` 的 missing-keywords 失败，未将该内容失败包装成全绿。
- 证据：`.omo/evidence/task-11-skill-init.txt`、`.omo/evidence/task-12-streamlit-service-ui.txt`、`.omo/start-work/ledger.jsonl` 末尾记录、`.omo/plans/high-trust-resume-skill-latex.md` 已勾选 Task 11.1、11.2、12.1、12.2。

### Eval / eval-matrix sample_product_analyst missing-keywords 修复

- 状态：已完成但未提交。
- 根因：`SKILL_TERMS` 缺少短语级 `dashboard storytelling` 与 `stakeholder communication`，JD 提取时只保留了 `dashboard` / `stakeholder` 单词，导致 golden eval 的 required missing phrases 无法在报告中出现。
- 变更：`src/career_ai/text_processing.py` 增加两个短语词项；`tests/test_text_processing.py` 增加短语提取回归；同步 eval runner、agent memory、matrix、CLI 与 runtime 测试期望，使通过条件绑定真实 missing-keywords 内容。
- 内容抽查：`sample_product_analyst` 当前 missing keywords 为 `ai, dashboard storytelling, data analysis, evaluation, stakeholder communication`，required missing phrases 均存在。
- 验证：`python -m pytest -q` 通过（339 passed）；`ruff check .` 通过；`basedpyright` 通过（0 errors, 0 warnings, 0 notes）；`career-ai-agent eval` 通过（1 passed, 0 failed）；`career-ai-agent eval-matrix` 通过（1 passed row, 0 failed rows）；`git diff --check` 通过。

### 输出过程显示模式可选化

- 状态：已完成但未提交。
- Streamlit：新增 `Output detail` 单选项，默认 `Result only`，用户选择 `Result + process` 时才展示 prepare/generate/validate/render/replay 的原始 JSON 或 render manifest；默认结果视图只显示摘要和最终状态。
- CLI：`prepare`、`validate-draft`、`confirm`、`tailor`、`render`、`inspect-latex` 新增 `--output result|process|json`。默认 `result` 只显示终端摘要；`process` 显示摘要加过程 JSON；`json` 保持纯机器可读输出供脚本和测试使用。
- 重构：新增 `src/career_ai/host_proposal_output.py` 承担 CLI 输出格式化，`host_proposal_cli.py` 只保留 Typer 命令注册；新增 `tests/test_host_proposal_cli_output.py` 与 `tests/test_host_proposal_cli_render.py` 拆分 CLI 输出和 render 测试，所有修改文件均低于 250 pure LOC。
- 验证：`python -m pytest -q` 通过（341 passed）；`ruff check .` 通过；`basedpyright` 通过（0 errors, 0 warnings, 0 notes）；`git diff --check` 通过；手动抽查 `career-ai-agent prepare` 默认只输出摘要，`--output process` 输出摘要后附带 JSON。

### Phase 13 — Release verification 与覆盖扩展

- 状态：已完成但未提交。
- 工作内容：扩展 release eval bank 至 3 个 deterministic fake-provider cases；新增 clean wheel packaging smoke；补齐 packaged Skill resources、cross-host policy parity、renderer security 与 LaTeX scanner 覆盖。
- 兼容修复：`render` 在 prepared/rejected/not render-ready run 上不再泄漏 `FileNotFoundError` traceback，统一返回稳定的 `HostRunError`，提示先 validate 并 accept proposal。
- 手工验收：临时 workspace 执行 `init --agent all` 后，`render --format all --disable-latex-engines` 输出 DOCX/PDF/TEX 成功，LaTeX-PDF 如实返回 `latex_no_engine`；临时 workspace 已清理；Streamlit health `http://127.0.0.1:8508/_stcore/health` 返回 `200 ok`。
- 验证：`python -m pytest -q` 通过（348 passed）；`ruff check .` 通过；`basedpyright` 通过（0 errors, 0 warnings, 0 notes）；`career-ai-agent doctor` 仍如实报告 Tectonic/XeLaTeX FAIL 与 LaTeX package cache WARN；`career-ai-agent eval` 通过（3 passed, 0 failed）；`career-ai-agent eval-matrix` 通过（fake-default passed=3 failed=0）；`git diff --check` 通过。
- 证据：`.omo/evidence/task-13-release-verification.txt`、`.omo/start-work/ledger.jsonl` 末尾记录、`.omo/plans/high-trust-resume-skill-latex.md` 已勾选 Task 13.1、13.2 与 F1-F4。
