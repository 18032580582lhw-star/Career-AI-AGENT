<!-- WORKLOG-SUMMARY:START -->
## 当日总结

尚未执行“总结日志”指令。
<!-- WORKLOG-SUMMARY:END -->

## 工作记录

### GitHub URL Agent 自动安装入口

<!-- WORKLOG-ENTRY:agent-install-docs-and-scripts-2026-07-15 -->
- 状态：已完成但未提交。
- 工作内容：按用户要求先提供马上可用的 `docs/agent-install.md`，再将同一安装流程固化为 Windows PowerShell 和 macOS/Linux/Git Bash 脚本。
- 变更情况：新增 `docs/agent-install.md`、`scripts/install-agent.ps1`、`scripts/install-agent.sh`；更新 `README.md`、`README.zh.md`、`README.en.md`，加入 Agent install guide 链接。
- 安装流程：脚本接收 GitHub repo URL，clone 或复用现有 checkout，创建 `.venv`，执行 `pip install -e .`，运行 `career-ai-agent doctor`，执行 `career-ai-agent init --workspace <checkout> --agent all`，默认继续运行 `eval` 和 `eval-matrix`。
- 安全边界：默认不更新已有 checkout；只有显式传入 `-Update` 或 `--update` 时才执行 `git pull --ff-only`。已有同名 Skill 文件仍由现有 `init` 逻辑报告 `exists-different`，不覆盖用户文件。
- 验证结果：PowerShell 语法解析通过；Git Bash `bash -n scripts/install-agent.sh` 通过；`git diff --check` 通过。PowerShell 直接调用 `bash` 时命中了本机不可用的 WSL `/bin/bash`，已改用 Git Bash MCP 验证并通过。
