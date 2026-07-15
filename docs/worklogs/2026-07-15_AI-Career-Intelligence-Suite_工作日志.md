<!-- WORKLOG-SUMMARY:START -->
## 当日总结

尚未执行“总结日志”指令。
<!-- WORKLOG-SUMMARY:END -->

## 工作记录

### GitHub URL Agent 自动安装入口

<!-- WORKLOG-ENTRY:agent-install-docs-and-scripts-2026-07-15 -->
- 状态：已完成并已提交本地 commit。
- 工作内容：按用户要求先提供马上可用的 `docs/agent-install.md`，再将同一安装流程固化为 Windows PowerShell 与 macOS/Linux/Git Bash 脚本。
- 变更情况：新增 `docs/agent-install.md`、`scripts/install-agent.ps1`、`scripts/install-agent.sh`；更新 `README.md`、`README.zh.md`、`README.en.md`，加入 Agent install guide 链接。
- 安装流程：脚本接收 GitHub repo URL，clone 或复用现有 checkout，创建 `.venv`，执行 `pip install -e .`，运行 `career-ai-agent doctor`，执行 `career-ai-agent init --workspace <checkout> --agent all`，默认继续运行 `eval` 和 `eval-matrix`。
- 安全边界：默认不更新已有 checkout；只有显式传入 `-Update` 或 `--update` 时才执行 `git pull --ff-only`。已有同名 Skill 文件仍由现有 `init` 逻辑报告 `exists-different`，不覆盖用户文件。
- 验证结果：PowerShell 语法解析通过；Git Bash `bash -n scripts/install-agent.sh` 通过；`git diff --check` 通过。PowerShell 直接调用 `bash` 时命中了本机不可用的 WSL `/bin/bash`，已改用 Git Bash MCP 验证并通过。

### GitHub 发布与真实安装 URL 固化

<!-- WORKLOG-ENTRY:github-publish-url-fix-2026-07-15 -->
- 状态：已发布到 GitHub `main`。
- 工作内容：用户提供真实仓库 `https://github.com/18032580582lhw-star/Career-AI-AGENT` 后，将 `docs/agent-install.md` 中的 `<OWNER>/<REPO>`、`<GITHUB_PROJECT_URL>` 等占位符替换为可直接访问的 GitHub 与 raw.githubusercontent.com URL。
- 目标效果：Codex、Claude Code、OpenCode 或人工只需要读取 `https://raw.githubusercontent.com/18032580582lhw-star/Career-AI-AGENT/main/docs/agent-install.md`，即可按文档下载脚本、克隆仓库、安装本地 agent 并执行 `doctor`、`init`、`eval`、`eval-matrix` 验证。
- 发布结果：已配置 remote `origin` 指向 `https://github.com/18032580582lhw-star/Career-AI-AGENT.git`，并将本地 `codex/harness-first-roadmap` 分支推送到远端 `main`。
### Debug Stabilization 调试计划执行

<!-- WORKLOG-ENTRY:debug-stabilization-execution-2026-07-15 -->
- 状态：已完成调试计划执行和 F1-F4 最终验证，尚未提交本轮新增修复与证据。
- 计划与证据：新增 `.omo/plans/debug-stabilization.md`，并在 `.omo/evidence/` 写入 Task 1-8、F1-F4 的调试证据；`.omo/boulder.json` 状态已标记为 `completed`，`.omo/start-work/ledger.jsonl` 已记录任务执行链路。
- 真实修复：修复 `career-ai-agent eval` / `eval-matrix` 在缺失或空 case 目录时错误显示 `Total cases: 0` 且 exit 0 的 silent success；新增 `EvalCaseLoadError`，CLI 现在输出明确错误并 exit 2。
- 回归测试：新增 loader 与 CLI bad-input 测试；全量 `pytest` 通过 `352 passed`，`ruff check .` 通过，`basedpyright` 为 `0 errors, 0 warnings`，`git diff --check` 无空白错误。
- 真实 QA：GitHub raw PowerShell fresh install 通过；Streamlit 由 Playwright 真浏览器完成可见控件、Prepare、Generate with API、Safety/Adequacy 状态检查，且无 traceback、无 page error、端口释放正常。
- 重要发现：Tailoring/render 公开流程仍有后续 blocker：generic host proposal 即使 accepted，也缺少 render 所需的 structured proposal、`draft.json` 与 `candidate-facts.json`；renderer 本身在 accepted fixture 路径下可正常生成 DOCX/HTML-PDF/TEX，并正确报告 `latex_no_engine` 与 stale template。

### Tailoring/render structured package 修复

<!-- WORKLOG-ENTRY:structured-host-package-render-ready-2026-07-15 -->
- 状态：已完成实现与全量验证，尚未提交本轮新增修复。
- 修复内容：新增 `HostStructuredProposalPackage`，让公开 `tailor --host-proposal` 流程可接收包含 `ResumeDocumentDraft` 与 `StructuredResumeTailoringProposal` 的 render-ready package；`prepare` 返回的 `proposal_schema` 已改为同时暴露 `HostStructuredProposalPackage` 与 `ResumeTailoringProposal` 的 union schema。
- 持久化结果：structured package 必须先通过本地 safety/adequacy 校验，并在 validate 阶段通过 `accept_resume_document` 文档接受门，才会写入 `draft.json`、structured `proposal.json`、`validation.json` 与 trusted local `candidate-facts.json`；generic `ResumeTailoringProposal` 保持 validation-only，不伪装成可渲染产物。
- 安全边界：`candidate-facts.json` 来自本地 `prepare` 生成的 trusted context，而不是 host package 自带事实，避免 host 侧扩权注入事实；篡改 draft 或 rejected structured package 都不会落 `draft.json`。
- 文档更新：更新 `src/career_ai/skills/career_resume_tailor/references/proposal-contract.md` 与 `workflow.md`，明确 generic proposal 是 validation-only，structured package 才是 render-ready 候选。
- 回归测试：新增并拆分到 `tests/test_host_structured_package_cli_render.py`，覆盖真实 CLI 链路 `prepare -> tailor --host-proposal structured-package -> render --format all --disable-latex-engines`，并增加篡改 draft 与 rejected structured package 的安全回归。
- 验证结果：structured package 测试 `3 passed`；相关 CLI/service/render 测试 `11 passed`；全量 `pytest` 为 `355 passed`；`ruff check .` 通过；`basedpyright` 为 `0 errors, 0 warnings, 0 notes`；`git diff --check` 无空白错误，仅提示既有 `.omo/boulder.json` 与 `.omo/start-work/ledger.jsonl` CRLF 归一化 warning。
