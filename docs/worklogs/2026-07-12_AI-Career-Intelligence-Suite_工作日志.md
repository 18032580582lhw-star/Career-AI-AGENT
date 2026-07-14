# 2026-07-12 AI Career Intelligence Suite 工作日志

<!-- WORKLOG-SUMMARY:START -->
## 当日总结

尚未执行“总结日志”指令。
<!-- WORKLOG-SUMMARY:END -->

## 文档信息

- 日期：2026-07-12
- 项目：AI Career Intelligence Suite
- 分支：codex/harness-first-roadmap
- 时区：Asia/Hong_Kong

## 工作记录

### 07:59 — Task 3.3 Optimization Adequacy Harness 完成

<!-- WORKLOG-ENTRY:high-trust-task-3-3-adequacy-complete -->
- 状态：已完成但未提交。
- 工作内容：按审计修正后的契约完成 Adequacy Harness；覆盖增益只接受同一 Change 内由 `EvidenceRequirementMatch` 证明的 fact/requirement join。
- 变更情况：Proposal 新增完整 `rewritten_resume` 并允许安全 no-op；新增 `AdequacyContext`、adequacy 编排/规则/模型，以及拆分后的 typed 测试工厂。实现精确 90% 豁免、低覆盖 10 点增益、双相关事实实质改写、JD 关键词密度和完整输出可读性门。
- 验证情况：相关测试 40 passed；全量 pytest 212 passed；BasedPyright 0 errors；no-excuse 无违规；手工 typed API 验证 50→60 的真实证据化增益并返回 PASS。Ruff import 顺序已机械修复，将与 Task 3.4 一起重跑最终全仓门。
- 证据：`.omo/evidence/task-3-3-optimization-adequacy.txt`；未暂存、提交或推送。

### 01:28 — Task 3.1 版本化 Proposal 协议闭环

<!-- WORKLOG-ENTRY:high-trust-task-3-1-protocol-contracts -->
- 状态：已完成但未提交。
- 工作内容：恢复并闭环已落盘的 Task Package、Proposal、Change、Finding、Decision、Confirmation、Accepted Document 与 Run/Render Manifest typed contracts。
- 变更情况：修正 Pydantic 运行时字段类型、canonical error template、穷尽 enum fallback 及测试 JSON 类型；同时修复两个既有已完成切片的 test-only BasedPyright 遗留项，使全仓静态门恢复。
- 验证情况：聚焦协议测试 15 passed；完整 `pytest -q` 为 187 passed；全仓 Ruff 通过；BasedPyright 为 0 errors/0 warnings/0 notes；no-excuse audit 7 files 无违规；`git diff --check` 通过。手工 API probe 确认 JSON round-trip 与 proposal hash 篡改拒绝。
- 证据：`.omo/evidence/task-3-1-protocol-contracts.txt`、`src/career_ai/tailoring/*contracts.py`、`tests/test_tailoring_protocol_contracts.py`；未暂存、提交或推送。

### 01:02 — Task 2.3 JD provenance 隔离与用户确认

<!-- WORKLOG-ENTRY:high-trust-task-2-3-provenance-boundary -->
- 状态：已完成但未提交。
- 工作内容：将 JD 不能成为候选人事实从注释约定提升为 typed boundary，并为用户明确确认的事实提供稳定 provenance 工厂。
- 变更情况：新增冻结 `ResumeFactSource(role="resume")`；`extract_candidate_facts` 不再接受裸 `SourceArtifactId`；新增 `create_confirmed_candidate_fact`，只生成 `UserConfirmationProvenance`。测试先红后绿。
- 验证情况：相关聚焦测试 26 passed，scoped Ruff、BasedPyright（0 errors）与 no-excuse audit 通过；全量 `pytest -q` 为 187 passed，`git diff --check` 通过。手工 API probe 确认 JD role 被拒绝、中文简历正常提取、确认 provenance 稳定、空确认被拒绝。
- 证据：`.omo/evidence/task-2-3-provenance-boundary.txt`、`src/career_ai/tailoring/candidate_extractor.py`、`extraction_types.py`、`tests/test_candidate_fact_extractor.py`；未暂存、提交或推送。

### 00:54 — Task 3.3 Adequacy Harness 设计审计

<!-- WORKLOG-ENTRY:high-trust-task-3-3-adequacy-audit -->
- 状态：进行中。
- 工作内容：按顺序进入 Task 3.3；首版实现虽有 5 个聚焦测试通过，但独立审计证明调用者可用任意 fact 与 requirement target 标签伪造覆盖增益，因此未勾选任务。
- 变更情况：撤回未达 high-trust 标准的 adequacy 模块和测试，保存下一轮必须采用 `EvidenceRequirementMatch` join、精确 90% 阈值、相关双事实实质改写、accepted no-op 豁免、readability/keyword-stuffing 稳定规则及 golden adapter 的设计约束。
- 验证情况：撤回 WIP 后全量 pytest 199 passed，Ruff 通过，BasedPyright 0 errors，`git diff --check` 通过；未把“测试绿但可绕过”误报为完成。
- 证据：`.omo/evidence/task-3-3-adequacy-audit.txt`；Task 3.3 仍未勾选，未暂存、提交或推送。

### 00:48 — Task 3.2 事实 Safety Harness

<!-- WORKLOG-ENTRY:high-trust-task-3-2-factual-safety -->
- 状态：已完成但未提交。
- 工作内容：实现纯确定性的事实 Safety Harness；Safety 只给出通过/待确认/拒绝证据，不越权产生 accepted 状态。
- 变更情况：新增 `safety.py`、`safety_rules.py`、`safety_models.py` 与 12 个测试，覆盖稳定 violation codes、未知/重复 fact、技术/责任/资历/指标/通用虚构、确认 provenance、无 claim change 以及 change/claim 引用不一致。finding ID 改为内容哈希，模块按 250 LOC 门拆分。
- 验证情况：三轮红测均按预期暴露缺失实现和绕过；最终聚焦测试 12 passed，全量 pytest 199 passed，全仓 Ruff 与 BasedPyright 通过，no-excuse 无违规，doctor 成功；eval/eval-matrix 如实保留既有 missing-keywords 失败。真实 typed Proposal QA 对无 claim 的 Kubernetes 改写返回 `passed=false`、`unsupported_technology`。
- 证据：`.omo/evidence/task-3-2-factual-safety-harness.txt`、`.omo/start-work/ledger.jsonl`；未暂存、提交或推送。

### 00:42 — Task 2.2 候选人事实与 JD 要求提取闭环

<!-- WORKLOG-ENTRY:high-trust-task-2-2-extraction -->
- 状态：已完成但未提交。
- 工作内容：验证现有中断产物可从简历生成 evidence-backed candidate facts，并从 JD 生成分类、优先级明确的 typed requirements；Task 2.3 的 JD provenance 硬隔离不提前宣告完成。
- 变更情况：未修改提取生产代码；补充 `.omo` 证据、ledger 与计划状态。独立审计指出的 JD-to-candidate 结构性泄漏、注入/垃圾行语义过滤、重复项及细粒度 span 建议已记录并路由至 Task 2.3 或后续 Safety/Adequacy eval。
- 验证情况：聚焦 pytest 7 passed；scoped Ruff、BasedPyright（0 errors）和 no-excuse audit 通过。真实中文输入、原文 offset 映射、稳定 identity、空输入以及 JD-only Kubernetes 不进入隔离简历事实均通过手工 API probe。
- 证据：`.omo/evidence/task-2-2-fact-requirement-extraction.txt`、`tests/test_candidate_fact_extractor.py`、`tests/test_jd_requirement_extractor.py`；未暂存、提交或推送。

### 00:16 — 恢复高可信简历路线并续跑 Task 1.2

<!-- WORKLOG-ENTRY:high-trust-task-1-2-resume -->
- 状态：已完成但未提交。
- 工作内容：核对附件路线图、`.omo` Boulder 状态、计划 checkbox、ledger、Git 工作树和既有证据；确认上次运行停在 Task 1.2 的实现已落盘但尚未完成验证闭环。
- 变更情况：将当前 Codex 会话追加到 `.omo/boulder.json`；补充畸形 DOCX 的失败测试，并在 `source_extraction.py` 的 DOCX 边界将 `BadZipFile` 映射为稳定的 `source_read_failed`；完成 Task 1.2 计划勾选，并同步上次 ledger 已完成但漏勾的 Task 1.3。保留既有未提交变更，不暂存、不提交、不推送。
- 验证情况：红测确认畸形 DOCX 原先泄漏 `BadZipFile`（1 failed, 9 passed）；修复后聚焦测试 10 passed，scoped Ruff、BasedPyright（0 errors）与 no-excuse audit 通过，全量 `pytest -q` 为 185 passed，`git diff --check` 通过。真实临时 Workspace QA 验证 SHA-256 identity、重复导入、部分记录恢复、源变更保留旧 blob、prompt injection 惰性保存、非法格式拒绝与清理。全仓 Ruff/BasedPyright 仍被其他未完成 tailoring/protocol 文件阻断，未误报为本切片回归。
- 证据：`.omo/evidence/task-1-2-source-ingestion.txt`、`.omo/start-work/ledger.jsonl`、`tests/test_source_ingestion.py`、`src/career_ai/workspace/source_extraction.py`。

## 变更记录

### Task 3.4 validation lifecycle 完成

<!-- WORKLOG-ENTRY:high-trust-task-3-4-validation-state-machine -->
- 状态：已完成但未提交。
- 内容：完成 accepted / needs-confirmation / rejected / stale 聚合、source/template stale、harness-result proposal 绑定、两次 repair 消耗和 accepted-only render guard。
- 安全收口：阻断短/长否定转肯定、普通及 `by N%` 指标归属互换；Adequacy error 优先于 confirmation warning；真实 golden no-op fixture 走通 Safety、Adequacy 与状态机。
- 验证：全仓 pytest 238 passed；Ruff 通过；BasedPyright 0 errors；git diff --check 通过；OMO 五路 review-work 全部 PASS。
- 证据：`.omo/evidence/task-3-4-validation-state-machine.txt`；未暂存、提交或推送。

无。

## 问题、风险与后续

- 当前工作区在续跑前已有大量未提交和未跟踪文件；本次继续严格限制在当前计划切片及其状态/证据/日志文件内。

### Task 4 真实多策略生成与统一提案工作流完成

<!-- WORKLOG-ENTRY:high-trust-task-4-real-multi-strategy-generation -->
- 状态：已完成但未提交。
- 工作内容：完成 Task 4.1/4.2；将旧的提示词文本启发式评分改为 conservative、ATS-aligned、impact-narrative 三种真实 `ResumeTailoringProposal`，并经本地 Safety、Adequacy 与状态机做结果分级；API-provider 与 host proposal 统一进入 `TailoringTaskPackage` 和本地验证路径。
- 变更情况：保留完整基线简历与 legacy profile 入口；补上 fake provider 的安全非接受结果、run/source/template 绑定、伪造目标 requirement 拒绝、提示注入/语义事实拼接拒绝，以及空匹配策略哈希稳定性。`prompts/` 现在仅作为兼容性启用 profile，其文本不再授权任何 claim。
- 验证情况：全仓 `pytest -q` 250 passed、Ruff 通过、BasedPyright 0 errors/0 warnings/0 notes、`git diff --check` 通过；手工 local/host/API probe 分别得到策略生命周期结果和 host/API accepted 100。`doctor` 通过；`eval` 与 `eval-matrix` 如实保留既有 `sample_product_analyst` missing-keywords 失败。
- 证据：`.omo/evidence/task-4-real-multi-strategy-generation.txt`、`.omo/start-work/ledger.jsonl`；未暂存、提交或推送。
