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
