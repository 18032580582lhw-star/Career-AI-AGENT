<!-- WORKLOG-SUMMARY:START -->
## 当日总结

已修复 OMO 验收复核指出的 `jd_fetcher.py` 阻塞问题：DNS 解析失败现在返回结构化 `FetchFailure`，JD URL 抓取改为“先解析并校验地址，再连接到该已校验 IP”的 pinned-resolution 流程，避免 DNS 校验与实际连接之间的二次解析风险。为满足 250 行上限，已将 fetch Pydantic models、公共入口和底层 HTTP 客户端拆分到独立模块。最新验证结果为 `pytest` 19 passed、`ruff` 通过、`basedpyright` 0 errors，Streamlit 健康检查 HTTP 200。
<!-- WORKLOG-SUMMARY:END -->

## 工作记录

### 2026-07-09 - 修复 OMO 验收阻塞项

- 目标：按 OMO 复核结论修复正式验收失败项。
- 主要变更：
  - `src/career_ai/jd_fetcher.py`：
    - 将 JD URL 公共入口保留为兼容导入点。
    - `FetchSuccess` / `FetchFailure` 改为 Pydantic frozen models。
    - `data:` URL 增加大小限制，并避免把完整 data payload 暴露为 `source_url`。
  - `src/career_ai/jd_http_client.py`：
    - 新增 pinned-resolution HTTP/HTTPS 获取流程。
    - 每一跳 redirect 都先解析 host，阻断 localhost、private、loopback、link-local、reserved、multicast、unspecified 等地址。
    - 实际连接使用已校验 IP，HTTP 保留原始 `Host` header，HTTPS 使用原始 hostname 做 SNI。
    - DNS 解析失败返回 `FetchFailure(reason="network_error", ...)`，避免 Streamlit 崩溃。
    - HTTP 响应读取增加大小限制。
  - `src/career_ai/fetch_models.py`：
    - 拆出 fetch 相关 Pydantic models 和 union 类型，避免 `jd_fetcher.py` 超过 250 行。
  - `app.py`：
    - 上传处理不再使用用户提供的文件名；改为根据文件字节头推断安全临时文件名。
    - 新增 `safe_resume_upload_path`，确保上传路径保持在临时目录内。
    - 补齐 Streamlit 调用返回值处理，使 `app.py` 可被 basedpyright 严格检查。
  - `src/career_ai/analysis.py`：
    - bullet 改写只使用当前 bullet 中已经出现的 JD 关键词，不再从整份简历其他 bullet 借用事实。
  - `src/career_ai/__init__.py`：
    - 从包根导出计划中列出的公共 API。
  - `pyproject.toml`：
    - 将 `app.py` 纳入 basedpyright include。
  - `tests/`：
    - 新增/更新 SSRF、DNS 失败、pinned connection、大小限制、Pydantic fetch result、上传路径、公共 API 导出、basedpyright include、bullet fact-preservation 回归测试。
- 验证结果：
  - `.\.venv\Scripts\python.exe -m pytest`：19 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings。
  - `.\.venv\Scripts\basedpyright.exe app.py`：0 errors, 0 warnings。
  - `streamlit run app.py --server.headless=true --server.port=8504` 后访问 `/_stcore/health`：HTTP 200，body `ok`。
- 备注：
  - 当前工作区仍不是 git repository，无法记录提交哈希。
  - `src/career_ai/jd_http_client.py` 当前 232 纯代码行，低于 250 行上限。

### 2026-07-09 - 初始化 Git 基线
- 目标：按用户要求将 `F:\AGENT` 初始化为 Git 仓库并创建一次基线提交。
- 主要变更：
  - 新增 `.gitignore`，排除 `.venv/`、`__pycache__/`、`.pytest_cache/`、`.ruff_cache/`、`*.egg-info/`、构建产物和本地环境变量文件。
  - 新增 `.gitattributes`，将仓库文本文件统一为 LF 行尾，降低 Windows 本地开发中的换行漂移。
  - 将现有源码、测试、提示词、设计文档、README、项目配置和工作日志纳入 Git 基线。
- 状态：
  - Git 初始化与基线提交已完成，提交哈希以 `git log` 结果为准。

### 2026-07-09 - Streamlit 运行与浏览器级验收
- 目标：按用户要求运行并打开 Streamlit UI，完成浏览器级验收。
- 运行结果：
  - 已启动 `.\.venv\Scripts\streamlit.exe run app.py --server.headless=true --server.port=8508 --browser.gatherUsageStats=false`。
  - 本地访问地址：`http://127.0.0.1:8508`。
  - `/_stcore/health` 返回 HTTP 200，body `ok`。
- 浏览器验收：
  - 首屏显示 `AI Career Intelligence Suite`，侧边栏包含 `Resume file`、`Resume text`、`JD URL`、`Job description` 和 `Analyze`。
  - 点击 `Analyze` 后渲染 `JD Analysis`、`Match Score`、`Resume Suggestions`、`Cover Letter`、`Prompt Evaluation`、`Export` 六个页签。
  - `JD Analysis` 显示 `AI Product Analyst` 与 `Seniority: Mid-level`。
  - `Match Score` 显示匹配分 `73`，并展示 matched/missing 关键词。
  - `Resume Suggestions` 显示 original/improved bullet。
  - `Cover Letter` 文本框包含 `Dear Hiring Team`、`AI Product Analyst` 和 `Candidate`。
  - `Prompt Evaluation` 显示 `baseline: 80`、`structured-agent: 95`、`fact-preserving-rewriter: 100`，最佳策略为 `fact-preserving-rewriter`。
  - `Export` 显示 `Download tailored resume` 和 `Download cover letter`。
  - 浏览器控制台 error 日志为空。
- 状态：
  - Streamlit 服务保持运行，便于继续人工查看。

### 2026-07-09 - Streamlit 输入区双栏布局调整
- 目标：根据用户反馈，移除侧边栏输入界面，将输入流程改为主画布排版。
- 主要变更：
  - `app.py` 不再使用 `st.sidebar` 放置输入控件。
  - 主画布改为左右双栏：左侧 `Resume` 包含文件上传和简历文本，右侧 `Job Description` 包含 JD URL 和 JD 文本。
  - `Analyze` 主按钮放在双栏输入区下方，分析结果继续使用原有 tabs。
  - 新增 `tests/test_app_layout.py`，回归保护“输入区使用主画布双栏而不是 sidebar”。
- 验证结果：
  - 先运行 `.\.venv\Scripts\python.exe -m pytest tests\test_app_layout.py`，确认新增测试在旧 sidebar 布局下失败。
  - 修改后 `.\.venv\Scripts\python.exe -m pytest tests\test_app_layout.py` 通过。
  - `.\.venv\Scripts\python.exe -m pytest`：20 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings。
  - 浏览器刷新 `http://127.0.0.1:8508` 后确认首屏无 `Inputs` 侧栏标题，主画布显示 `Resume` 与 `Job Description` 双栏输入。
  - 点击 `Analyze` 后，`JD Analysis`、`Match Score`、`Resume Suggestions`、`Cover Letter`、`Prompt Evaluation`、`Export` 页签仍正常渲染。
  - 浏览器控制台 error 日志为空。
- 状态：
  - Streamlit 服务继续保持运行，便于查看新布局。

### 2026-07-09 - Streamlit 简约动效视觉主题
- 目标：根据用户反馈，为页面增加简约、顺滑、富有设计感的视觉主题与动效。
- 主要变更：
  - 新增 `static/app_theme.css`，集中维护 Streamlit 视觉样式。
  - `app.py` 启动时注入主题 CSS。
  - 页面背景改为浅米色渐变底纹，并增加缓慢 `soft-sheen` 背景过渡动效。
  - 输入窗口、tabs 和指标区域使用浅灰/白色表面、柔和阴影和圆角。
  - 主按钮、下载按钮和上传按钮使用黑白配色、999px 圆角、仿立体阴影、hover/active 过渡。
  - 新增 `tests/test_app_theme.py`，回归保护主题 CSS 文件和关键视觉 token。
- 验证结果：
  - 先运行 `.\.venv\Scripts\python.exe -m pytest tests\test_app_theme.py`，确认新增主题测试在 CSS/加载逻辑缺失时失败。
  - 修改后 `.\.venv\Scripts\python.exe -m pytest tests\test_app_theme.py` 通过。
  - `.\.venv\Scripts\python.exe -m pytest`：22 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings。
  - 浏览器刷新 `http://127.0.0.1:8508` 后确认浅米色渐变背景、黑色白字圆角立体按钮、白色输入框与浅灰 tabs 生效。
  - 点击 `Analyze` 后结果区仍正常渲染，浏览器控制台 error 日志为空。
- 状态：
  - Streamlit 服务继续保持运行，便于查看新视觉主题。

### 2026-07-09 - 修复按钮文字对比度
- 目标：修复黑色立体按钮中文字被 Streamlit 内部 `span` 样式覆盖后看不清的问题。
- 根因：
  - 按钮本身已设置 `color: #ffffff`，但 Streamlit 将按钮文字包在内部 `SPAN` 中，且主题 CSS 的全局 `span` 颜色覆盖了按钮文字。
- 主要变更：
  - `static/app_theme.css` 增加按钮内部子元素颜色规则，默认状态强制白色，hover 状态跟随白底按钮切换为黑色。
  - `tests/test_app_theme.py` 增加按钮内部文字对比度回归测试。
- 验证结果：
  - 先运行 `.\.venv\Scripts\python.exe -m pytest tests\test_app_theme.py`，确认新增测试在缺少子元素颜色规则时失败。
  - 修改后 `.\.venv\Scripts\python.exe -m pytest tests\test_app_theme.py`：3 passed。
  - `.\.venv\Scripts\python.exe -m pytest`：23 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings。
  - 浏览器刷新 `http://127.0.0.1:8508` 后确认 `Analyze` 按钮本身和内部 `SPAN` 计算颜色均为 `rgb(255, 255, 255)`。

### 2026-07-09 - 页面调试巡检
- 目标：按用户要求调试改完后的 Streamlit 页面，确认视觉主题与核心流程没有隐藏问题。
- 调试假设：
  - CSS 层级仍可能存在文字/背景对比问题。
  - 视觉主题可能破坏 `Analyze` 后的结果区渲染。
  - 浏览器控制台或 Streamlit 运行日志可能存在静默错误。
- 运行态证据：
  - 浏览器计算样式显示 `Analyze` 按钮本身与内部 `SPAN` 文字颜色均为 `rgb(255, 255, 255)`，按钮背景为黑色渐变，圆角为 `999px`。
  - 页面背景存在浅米色渐变与 `soft-sheen` 动效。
  - 点击 `Analyze` 后，`JD Analysis`、`Match Score`、`Resume Suggestions`、`Cover Letter`、`Prompt Evaluation`、`Export` 均正常；匹配分 `73`、cover letter、prompt best strategy 和下载按钮均可见。
  - 浏览器控制台 error 日志为空。
  - Streamlit stdout/stderr 未出现 traceback，stderr 仅有 Uvicorn 启动日志。
- 验证结果：
  - `.\.venv\Scripts\python.exe -m pytest`：23 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings。
- 状态：
  - 本次调试未发现需要额外修复的页面阻塞问题。
  - Streamlit 服务继续保持运行，访问地址仍为 `http://127.0.0.1:8508`。

### 2026-07-09 - 方案 A：侧边栏历史记录与本地持久化
- 目标：按用户选择的方案 A，把侧边栏恢复为“历史记录”区域，同时保持简历和 JD 输入区在主画布双栏布局中。
- 主要变更：
  - 新增 `src/career_ai/history.py`，用 Pydantic frozen model 表达 `HistoryEntry`，提供 `load_history`、`append_history_entry` 和 `build_history_entry`。
  - 历史记录落盘到 `.career_ai/history.json`，每次点击 `Analyze` 后追加最新分析，并限制保存数量。
  - 历史记录只保存角色、匹配分、缺口关键词和简历/JD 短预览，不保存完整简历或完整 JD。
  - `.gitignore` 新增 `.career_ai/`，避免本地历史输入痕迹进入 Git。
  - `app.py` 保持主画布双栏输入，同时在 `st.sidebar` 渲染 `History`，空状态显示 `No analyses yet.`。
  - `static/app_theme.css` 增加侧边栏和历史折叠项的浅灰、白色、柔和阴影样式，使其与现有浅米色主题一致。
  - 新增 `tests/test_history.py`，并更新 `tests/test_app_layout.py`，锁定“输入在主画布、侧栏只承载历史”的契约。
- 验证结果：
  - 先运行 `.\.venv\Scripts\python.exe -m pytest tests\test_history.py tests\test_app_layout.py`，确认新增历史模块不存在时测试红灯。
  - 实现后目标测试通过：5 passed。
  - 全量 `.\.venv\Scripts\python.exe -m pytest`：27 passed。
  - `.\.venv\Scripts\python.exe -m ruff check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings。
  - 浏览器刷新 `http://127.0.0.1:8508` 后确认侧栏显示 `History`，主画布仍显示 `Resume` 与 `Job Description` 双栏输入。
  - 点击 `Analyze` 后侧栏出现 `AI Product Analyst - 73` 历史条目，页面结果 tabs 正常，浏览器 console error 日志为空。
  - 刷新页面后历史条目仍可从 `.career_ai/history.json` 重新加载，且 `git check-ignore -v .career_ai/history.json` 确认该文件被 `.gitignore` 命中。

### 2026-07-09 - 历史记录结果回放
- 目标：按用户要求，点击侧栏历史记录后，主内容区显示该次历史会话生成的完整分析结果，而不是只在侧栏展示摘要。
- 主要变更：
  - `src/career_ai/history.py` 的 `HistoryEntry` 增加可选 `report` 与 `prompt_result` 字段，新生成的历史记录会保存完整结构化分析结果和 prompt 评估结果。
  - 保持旧版摘要历史兼容：缺少 `report` / `prompt_result` 的本地历史仍可加载并展示摘要，但不会提供回放按钮。
  - `app.py` 将历史条目改为可点击的 `View result`，点击后通过 `st.session_state["selected_history_index"]` 选中对应历史。
  - 新分析完成后会写入历史并自动选中最新条目；主内容区统一通过选中历史渲染，避免即时结果和历史回放重复渲染。
  - `README.md` 更新 MVP 范围，补充本地历史回放，并移除“没有 persistence”的过时描述。
  - `tests/test_history.py` 增加完整结果落盘与旧摘要历史兼容测试；`tests/test_app_layout.py` 增加结果只通过选中历史渲染一次的回归测试。
- 调试记录：
  - 浏览器验收先发现 Streamlit 热重载没有重新加载已导入的 `history.py` 模型，导致旧进程抛出 `AttributeError: 'HistoryEntry' object has no attribute 'report'`；已重启 8508 端口 Streamlit 服务后确认消失。
  - 新分析后又发现同一轮 run 中重复渲染 `_render_report`，触发 `StreamlitDuplicateElementId`；已通过回归测试锁定并移除直接渲染路径。
- 验证结果：
  - `.\.venv\Scripts\python.exe -m pytest tests\test_app_layout.py tests\test_history.py`：7 passed。
  - `.\.venv\Scripts\python.exe -m pytest`：29 passed。
  - `.\.venv\Scripts\python.exe -m ruff check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings。
  - 浏览器刷新 `http://127.0.0.1:8508` 后点击 `Analyze`，主内容区显示 `Viewing saved analysis from ...` 和完整结果 tabs。
  - 点击侧栏 `View result` 后，主内容区继续显示该历史条目的 `JD Analysis`、`Match Score`、`Prompt Evaluation` 等结果，浏览器 console error 为空，页面无 traceback。
### 2026-07-09 - 本地模型无关 Career Agent 升级
- 目标：按用户确认的计划，将现有 Agent-style Career Intelligence MVP 升级为可通过本地命令运行、模型 provider 可替换的 Career Agent 底座。
- 主要变更：
  - 新增 `src/career_ai/workflows/`，把现有职业匹配流程抽为 `run_career_fit_workflow`，供 Streamlit、CLI 和 Agent runtime 共用。
  - 新增 `src/career_ai/llm/`，定义模型无关 `LLMClient` 协议、`LLMSettings`、`FakeLLMClient` 和 `OpenAICompatibleClient`；默认无 API key 时使用 fake provider。
  - 新增 `src/career_ai/agent/`，实现本地 planner/executor/memory summary；运行时会请求结构化 plan，并用本地确定性 workflow 执行分析。
  - 新增 `src/career_ai/cli.py` 和 `career-ai-agent` console script，支持 `doctor` 与 `analyze` 命令。
  - `app.py` 改为调用共享 workflow，保持现有 Streamlit 布局和历史回放不变。
  - `README.md` 补充 CLI、本地 fake provider、OpenAI-compatible provider 环境变量和双入口说明。
  - `pyproject.toml` 增加 `typer`、`rich` 依赖和 CLI 入口。
  - 新增 `tests/test_workflow.py`、`tests/test_llm_client.py`、`tests/test_agent_runtime.py`、`tests/test_cli.py` 覆盖 workflow、模型适配层、Agent runtime 和 CLI。
- 验证结果：
  - `.\.venv\Scripts\python.exe -m pytest`：38 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings, 0 notes。
  - `.\.venv\Scripts\career-ai-agent.exe doctor`：Provider `fake`，Structured output `yes`，Tool calling `no`。
  - `.\.venv\Scripts\career-ai-agent.exe analyze --resume-text ... --jd-text ...`：成功输出 deterministic fallback、角色、匹配分和 best prompt。
  - 纯代码行数检查：所有新/改 Python 文件均低于 250 行，当前最大 `app.py` 为 171 行。
- 状态：
  - 本次升级已完成并通过自动化验证；尚未创建提交。
### 2026-07-09 - Agent Core v1：Tool Registry 与状态机
- 目标：继续推进真正 Agent core，将上一轮“模型生成 plan + 本地直接跑 workflow”升级为“plan 映射工具调用 + Tool Registry 执行 + AgentState 记录状态”的结构。
- 主要变更：
  - 新增 `src/career_ai/agent/tools.py`，定义 `ToolName`、`ToolCall`、`ToolResult`、`ToolRegistry` 和各工具输入模型。
  - 默认注册 `fetch_jd`、`extract_resume`、`analyze_career_fit`、`compare_prompt_strategies`、`export_resume_docx`、`export_cover_letter_docx`、`save_memory_summary` 七个工具。
  - 工具实现复用现有模块：JD 抓取、简历抽取、职业匹配分析、prompt 评估、DOCX 导出和 memory summary 均不重新造业务能力。
  - `src/career_ai/agent/models.py` 新增 `AgentStateStatus`、`AgentStateEvent`、`AgentState`，并让 `AgentRun` 返回完整状态轨迹。
  - `src/career_ai/agent/executor.py` 改为先请求结构化 plan，再映射为 `ToolCall`，由 `ToolRegistry` 执行 `analyze_career_fit` 和 `compare_prompt_strategies`，最后组装 `CareerFitWorkflowResult`。
  - 新增 `tests/test_agent_tools.py`，覆盖默认工具注册、工具执行和参数类型不匹配的 recoverable failure。
  - 更新 `tests/test_agent_runtime.py`，锁定工具驱动步骤和 `initialized -> planned -> running_tool -> tool_completed -> completed` 状态机轨迹。
- 验证结果：
  - `.\.venv\Scripts\python.exe -m pytest`：42 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings, 0 notes。
  - `.\.venv\Scripts\career-ai-agent.exe analyze --resume-text ... --jd-text ...`：成功输出 deterministic fallback、角色、匹配分和 best prompt。
  - 纯代码行数检查：`src/career_ai/agent/tools.py` 为 227 行，低于 250 但已进入警戒区；下一轮继续扩展错误恢复前建议拆分工具模型和工具实现。
- 状态：
  - Agent Core v1 的工具注册、工具执行和状态机记录已完成；尚未创建提交。
### 2026-07-09 - Agent Core v2：错误恢复与真实执行循环
- 目标：在 Agent Core v1 的工具注册和状态机基础上，加入 recoverable failure 的 retry/skip 机制，让 agent executor 具备更接近真实 agent runtime 的执行循环。
- 主要变更：
  - 新增 `src/career_ai/agent/execution_loop.py`，定义 `AgentToolRunner`、`AgentRuntimeOptions` 和 `execute_tool_call`。
  - `execute_tool_call` 现在会按 `AgentExecutionPolicy.max_tool_attempts` 执行工具；recoverable failure 会记录 `failed-recoverable` 和 `recovering` 事件并重试。
  - 非关键工具多次失败后会记录 `tool-skipped`，并为 `compare_prompt_strategies` 生成空的 `PromptHarnessResult` 降级结果，保证主分析流程可以继续完成。
  - `src/career_ai/agent/models.py` 新增 `AgentExecutionPolicy`、`recovering`、`tool-skipped` 和 `completed-with-recovery` 状态。
  - 原 `src/career_ai/agent/tools.py` 已拆分为 `tool_models.py`、`tool_impl.py`、`tool_registry.py`，`tools.py` 保留为兼容导出口，避免工具层继续逼近 250 行上限。
  - `src/career_ai/agent/executor.py` 改为通过执行循环运行 `ToolCall`，并通过 `AgentRuntimeOptions` 支持测试或未来真实 runtime 注入自定义 tool runner 与 execution policy。
  - `tests/test_agent_runtime.py` 新增两条回归：recoverable analyzer failure 可重试恢复；prompt comparison 连续失败后可跳过并以 `completed-with-recovery` 完成。
- 验证结果：
  - `.\.venv\Scripts\python.exe -m pytest tests\test_agent_runtime.py tests\test_agent_tools.py -q`：8 passed。
  - `.\.venv\Scripts\python.exe -m pytest`：44 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings, 0 notes。
  - `.\.venv\Scripts\career-ai-agent.exe analyze --resume-text ... --jd-text ...`：成功输出 deterministic fallback、角色、匹配分和 best prompt。
  - 纯代码行数检查：`executor.py` 157、`execution_loop.py` 168、`tool_impl.py` 146、`tool_models.py` 69、`tool_registry.py` 49、`tools.py` 36，均低于 200。
- 状态：
  - Agent Core v2 的错误恢复和真实执行循环已完成；尚未创建提交。
### 2026-07-09 - Agent Core v3：模型参与恢复决策
- 目标：在 v2 的 retry/skip 本地执行循环基础上，让模型参与工具失败后的恢复决策，形成更接近真实 Agent 的 planner/executor 闭环。
- 主要变更：
  - 新增 `src/career_ai/agent/recovery.py`，定义 `RecoveryAction`、`RecoveryDecision`、`RecoveryDecider`、`ModelRecoveryDecider` 和 `RuleRecoveryDecider`。
  - `ModelRecoveryDecider` 会向当前 `LLMClient` 请求结构化恢复决策，只接受 `retry`、`skip`、`abort` 三种动作；模型输出异常时保守退回 `retry`。
  - `RuleRecoveryDecider` 保留 v2 行为作为无模型或未注入 decider 时的本地兜底。
  - `src/career_ai/agent/execution_loop.py` 现在在工具失败后调用 `recovery_decider.decide(...)`，记录 `recovery-decided` 状态事件，并按模型决策执行 retry、skip 或 abort。
  - `AgentRuntimeOptions` 增加 `recovery_decider` 注入点，方便未来接真实模型、测试替身或更复杂的恢复策略。
  - `src/career_ai/agent/models.py` 新增 `RECOVERY_DECIDED` 状态；`tools.py` 导出恢复相关公共类型。
  - 新增 `tests/test_agent_recovery.py` 覆盖 LLM 恢复决策解析；新增 `tests/test_agent_recovery_runtime.py` 覆盖模型选择 skip 后执行循环停止重试并降级完成；同步更新 v2 runtime 状态机断言。
- 验证结果：
  - `.\.venv\Scripts\python.exe -m pytest tests\test_agent_recovery.py tests\test_agent_recovery_runtime.py tests\test_agent_runtime.py -q`：7 passed。
  - `.\.venv\Scripts\python.exe -m pytest`：46 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings, 0 notes。
  - `.\.venv\Scripts\career-ai-agent.exe analyze --resume-text ... --jd-text ...`：成功输出 deterministic fallback、角色、匹配分和 best prompt。
  - 纯代码行数检查：`recovery.py` 101、`execution_loop.py` 198、`models.py` 59、`tools.py` 48、`test_agent_recovery.py` 63、`test_agent_recovery_runtime.py` 82、`test_agent_runtime.py` 166，均低于 200。
- 状态：
  - Agent Core v3 的模型恢复决策已完成；尚未创建提交。
### 2026-07-09 - Agent Core v4：Tool Catalog 与模型可见工具 Schema
- 目标：让模型在规划阶段看到本地 Career Agent 的工具目录、参数 schema、关键性、错误恢复提示和安全约束，为后续更真实的 tool-call 生成打基础。
- 主要变更：
  - 新增 `src/career_ai/agent/tool_catalog.py`，定义 `ToolInputField`、`ToolSpec`、`ToolCatalog` 和 `ToolSpecNotFoundError`。
  - `default_tool_catalog()` 现在描述七个本地工具：`fetch_jd`、`extract_resume`、`analyze_career_fit`、`compare_prompt_strategies`、`export_resume_docx`、`export_cover_letter_docx`、`save_memory_summary`。
  - 每个工具 spec 包含名称、说明、输入字段、输出字段、是否关键、可重试错误和安全规则；其中 `analyze_career_fit` 被标记为关键工具，并明确包含“不编造简历事实”的安全约束。
  - 新增 `render_tool_catalog_for_prompt()`，将强类型工具目录渲染成紧凑的模型可读文本。
  - `src/career_ai/agent/planner.py` 的 `request_agent_plan()` 现在会把 tool catalog 注入 user prompt，并要求模型只基于目录中的工具规划步骤。
  - `AgentRuntimeOptions` 增加 `tool_catalog` 注入点，未来可以为不同运行模式替换模型可见工具目录。
  - `ToolRegistry` 现在持有 `ToolCatalog`，`names()` 由目录稳定派生；`tools.py` 导出 catalog 相关公共 API。
  - `README.md` 补充模型可见工具目录说明。
  - 新增 `tests/test_agent_tool_catalog.py`，并更新 `tests/test_agent_runtime.py`，锁定工具目录内容和 planner prompt 注入行为。
- 验证结果：
  - `.\.venv\Scripts\python.exe -m pytest tests\test_agent_tool_catalog.py tests\test_agent_runtime.py -q`：7 passed。
  - `.\.venv\Scripts\python.exe -m pytest`：48 passed。
  - `.\.venv\Scripts\ruff.exe check .`：All checks passed。
  - `.\.venv\Scripts\basedpyright.exe`：0 errors, 0 warnings, 0 notes。
  - `.\.venv\Scripts\career-ai-agent.exe analyze --resume-text ... --jd-text ...`：成功输出 deterministic fallback、角色、匹配分和 best prompt。
  - 纯代码行数检查：`tool_catalog.py` 196、`planner.py` 57、`executor.py` 158、`execution_loop.py` 200、`tool_registry.py` 43、`tools.py` 60、`test_agent_tool_catalog.py` 19、`test_agent_runtime.py` 169，均未进入 200 行以上警戒区。
- 状态：
  - Agent Core v4 的模型可见工具目录与工具 schema 已完成；尚未创建提交。
