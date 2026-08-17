# 2026-08-17 AI-Career-Intelligence-Suite 工作日志

<!-- WORKLOG-SUMMARY:START -->
## 当日总结

尚未执行“总结日志”指令。
<!-- WORKLOG-SUMMARY:END -->

## 文档信息

- 日期：2026-08-17
- 项目：AI-Career-Intelligence-Suite
- 分支：codex/harness-first-roadmap
- 时区：Asia/Hong_Kong

## 工作记录

### 16:16 — 启动 Skill-First / Harness-Core 迁移

<!-- WORKLOG-ENTRY:skill-first-harness-core-migration-start -->
- 状态：进行中
- 工作内容：按既定顺序执行 Skill-First / Harness-Core 迁移计划，当前进入 Task 1 架构契约与迁移边界阶段。
- 变更情况：将迁移计划转换为可勾选的 Start Work 任务，创建新的 Boulder 活跃工作记录；尚未修改生产代码。
- 验证情况：已重新读取完整计划、Start Work、Python 编程和每日工作日志规则；尚未运行 Task 1 测试。
- 证据：`.omo/plans/skill-first-harness-core-migration.md`、`.omo/boulder.json`、`.omo/start-work/ledger.jsonl`

## 变更记载

- 执行状态：新增 `skill-first-harness-core-migration` 活跃工作，保留已完成的 `debug-stabilization` 状态。
- 工作区保护：已识别并保留原有未跟踪 `.omo/drafts/` 与其他计划文件。

## 问题、风险与后续

- 当前计划包含九个迁移任务和四项最终验证；Task 1 完成前不进入宿主安装、运行时删除或 Streamlit 退役。
- 下一步：先建立架构基线测试，再写预期失败的边界测试和最小文档变更。

### 16:34 — 完成 Task 1 架构契约与迁移边界

<!-- WORKLOG-ENTRY:skill-first-harness-core-task-1 -->
- 状态：已完成
- 工作内容：建立 Skill-first / Harness-core 正式架构契约；明确 Host Agent、Skill、CLI/Harness、Application Service、domain/workspace/rendering 的职责；冻结 Streamlit 并定义分阶段删除门槛。
- 变更情况：新增架构文档和静态依赖边界测试；中英文 README 改为“宿主 Agent + Skill + 本地权威 Harness”定位，未修改生产行为。
- 验证情况：边界测试 `3 passed`；Ruff 通过；BasedPyright `0 errors, 0 warnings, 0 notes`；no-excuse 检查和 `git diff --check` 通过。原 `.venv` 绑定的 Python 3.13 已不存在，依赖 `pydantic_core` 的既有 CLI/public API 测试无法在 Codex Python 3.12 下加载，已如实记录为环境阻断而非通过。
- 证据：`.omo/evidence/task-1-architecture-doc.md`、`.omo/evidence/task-1-boundary-tests.md`、`.omo/evidence/task-1-readme-positioning.md`

## 后续执行

- 下一步按顺序进入 Task 2：校正 canonical Skill 与 Codex / Claude Code 的发现和安装路径。

### 16:58 — 完成 Task 2 canonical Skill 与宿主发现路径

<!-- WORKLOG-ENTRY:skill-first-harness-core-task-2 -->
- 状态：已完成
- 工作内容：把 canonical Skill 收敛为标准、精简的 Agent Skill；宿主范围收敛为 Codex 与 Claude Code；Claude 发现路径从 `.claude/plugins` 迁移到 `.claude/skills`。
- 变更情况：更新 Skill frontmatter、Codex UI metadata、workflow reference、类型化安装记录、`init` 帮助、PowerShell/Bash 安装器、双语 README、安装文档及测试。安装器现在验证 machine-readable 两宿主结果后才报告成功。
- 验证情况：临时干净 Python 3.12 环境中聚焦测试 `8 passed`；BasedPyright `0 errors, 0 warnings, 0 notes`；仓库 Ruff、no-excuse、官方 Skill validator、PowerShell/Bash 语法和 `git diff --check` 均通过；真实临时工作区 `init --agent all` 返回两项且 bundle hash 一致。
- 环境与清理：未修改原有失效 `.venv`；临时验证环境、pytest/wheel 目录与安装冒烟工作区均已删除。
- 证据：`.omo/evidence/task-2-red-tests.md`、`.omo/evidence/task-2-install-scripts.md`、`.omo/evidence/task-2-skill-installation.md`

## 后续执行（Task 2 后）

- 下一步进入 Task 3：加强宿主协议结果字段并建立四类确定性 conformance case。

### 17:10 — 完成 Task 3 宿主协议与确定性 conformance cases

<!-- WORKLOG-ENTRY:skill-first-harness-core-task-3 -->
- 状态：已完成
- 工作内容：扩展 validation machine envelope，新增 accepted、needs-confirmation、rejected prompt-injection/unsupported claim、stale/tampered 四类数据驱动场景；所有动态 run ID 与 hash 均在运行时绑定。
- 变更情况：validation 输出新增相对 artifact、finding count/codes 和 next instruction；render 输出保证成功项有 artifact+manifest，非成功项有 typed code；Playwright `OSError` 改为 `renderer_output_failed`。
- 验证情况：RED 阶段 4 个用例因缺少新字段而失败；GREEN conformance `5 passed`；聚焦 host/render 回归 `26 passed`；完整套件其余 `364 passed`，需要联网隔离构建的 packaging 测试单独 `1 passed`，合计 365 项全部通过。Ruff、BasedPyright、no-excuse 和 `git diff --check` 通过。
- 人工 QA：真实 CLI accepted 流程返回相对 validation/manifest 路径；DOCX/TEX 正常生成，缺失 Playwright/LaTeX engine 分别返回 typed `renderer_output_failed`/`latex_no_engine`，未伪装成功。
- 清理：所有 `.tmp-task3-*` 环境、测试目录和手工工作区均已删除。
- 证据：`.omo/evidence/task-3-red-conformance.md`、`.omo/evidence/task-3-host-conformance.md`

## 后续执行（Task 3 后）

- 下一步进入 Task 4：把保留的确定性 Harness 契约移出旧 `career_ai.agent` 命名空间。

### 17:35 — 完成 Task 4 确定性 application service 迁移

<!-- WORKLOG-ENTRY:skill-first-harness-core-task-4 -->
- 状态：已完成
- 工作内容：新增 `CareerFitApplicationService`，将确定性 quality、factual boundary 和中性 run record 迁到 application/workflows；`analyze`、eval runner 与 failure corpus 不再走旧 Agent/LLM 主路径。
- 变更情况：`analyze` 保留 human 输出并新增完整 typed `CareerFitRunResult` JSON 输出；eval 与 CLI 共用同一服务；failure corpus 改接中性 run record，继续执行脱敏和 accepted-before-convert 闸门；旧 quality/trace/boundary 测试在替代契约就绪后删除。
- 验证情况：Task 4 聚焦隐私/服务套件 `37 passed`；完整非打包套件 `367 passed`；联网 wheel 冒烟 `1 passed`；Ruff 通过；BasedPyright `0 errors, 0 warnings, 0 notes`；真实 CLI analyze human/JSON 与 eval 3/3 均通过。五路实现后审查发现并修复完整 JSON schema、Role 注入、failure-record 全字段脱敏和 CLI eager-load Agent/LLM 命名空间问题，五路复审全部通过。
- 清理：所有 `.tmp-task4-*` 临时环境和 basetemp 已删除，原失效 `.venv` 保留。
- 证据：`.omo/evidence/task-4-service-red.md`、`.omo/evidence/task-4-eval-red.md`、`.omo/evidence/task-4-deterministic-service.md`

## 后续执行（Task 4 后）

- 下一步进入 Task 5：验证 Codex / Claude Code 的真实宿主行为并定义 DeepSeek adapter seam。
