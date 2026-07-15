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
