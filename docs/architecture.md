# VideoMind Agent Architecture

## Overall Flow

```text
用户 / 前端
↓
FastAPI routes
↓
LangGraph workflow
↓
Graph nodes
↓
Services
↓
Tools / Skills / LLM
↓
Storage / Trace
```

FastAPI 负责 HTTP 接口，LangGraph 负责编排文本 digest 节点，services 保留业务逻辑，tools 放具体工具能力，skills 保存 prompt 文件，storage 保存输出和 trace。

## Tool Registry

Tool Registry 位于 `backend/tools/registry.py`，用于统一注册工具能力。每个工具包含：

- name
- description
- input_schema
- output_schema
- handler
- timeout
- retry_count

当前已注册字幕提取、Whisper fallback、文本切分、上下文压缩、总结、关键词、复习题和思维导图生成工具。现有 workflow 暂时不强制改成 registry 调用，避免为了基础设施优化破坏已经跑通的主链路。

## Skills Prompt

Skills Prompt 位于 `backend/skills/`，不同任务的 prompt 不写死在 Python 代码里。`backend/services/skill_service.py` 负责：

- `load_skill(skill_name)`
- `list_skills()`
- `render_skill(skill_name, variables)`

这种设计方便后续单独调整 prompt、增加新的任务 skill，或者针对不同场景切换 prompt。

## MCP Server Reserved Design

MVP 阶段不直接实现 MCP Server。当前先保留 `backend/mcp/` 和 Tool Registry，后续可以把 registry 中的工具转换为 MCP tools：

1. 从 registry 读取工具元信息。
2. 将 input_schema/output_schema 转换为 MCP schema。
3. 将 handler 包装成 MCP tool call。
4. 统一复用 timeout 和 retry_count 等执行信息。

这样可以在不重写业务逻辑的情况下，把 VideoMind Agent 的能力暴露给其他 Agent 或客户端。
