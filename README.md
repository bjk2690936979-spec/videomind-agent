# VideoMind Agent

VideoMind Agent 是一个基于 FastAPI + LangGraph 的视频学习内容消化 Agent。项目目标是支持文本和视频输入，逐步实现字幕提取、Whisper 兜底转写、长文本总结、关键词解释、复习题生成、思维导图生成和 trace 日志记录。

## 技术栈

- Python
- FastAPI
- LangGraph
- LangChain Core
- OpenAI SDK
- yt-dlp
- faster-whisper
- Streamlit

## 目录结构

```text
videomind-agent/
|-- README.md
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- backend/
|   |-- main.py
|   |-- config.py
|   |-- schemas.py
|   |-- api/
|   |-- core/
|   |-- graph/
|   |   `-- nodes/
|   |-- services/
|   |-- tools/
|   |-- skills/
|   |-- mcp/
|   |-- storage/
|   |   |-- transcripts/
|   |   |-- compressed/
|   |   |-- outputs/
|   |   `-- traces/
|   `-- utils/
|-- frontend/
|-- eval/
|-- docs/
`-- tests/
```

## 本地启动

1. 创建虚拟环境并安装依赖：

```bash
pip install -r requirements.txt
```

2. 按需复制环境变量文件：

```bash
cp .env.example .env
```

3. 启动 FastAPI：

```bash
uvicorn backend.main:app --reload
```

4. 验证健康检查：

```bash
curl http://127.0.0.1:8000/health
```

期望返回：

```json
{"status":"ok","service":"videomind-agent"}
```

## 运行测试

```bash
pytest
```

## LangGraph 文本工作流

当前 `/digest/text` 已接入 LangGraph 工作流，API 层只负责接收请求并调用 workflow，业务逻辑仍保留在 service 层。

流程：

```text
RouteNode
↓
SplitNode
↓
SummaryNode
↓
KeywordNode
↓
QuizNode
↓
MindmapNode
↓
TraceNode
```

其中 `SplitNode` 会判断是否需要长文本压缩，`TraceNode` 会保存最终输出和 trace JSON。

## 视频链接 Subtitle-First + Whisper Fallback

当前 `/digest/video-url` 采用字幕优先提取，字幕缺失时再走 faster-whisper 兜底转写。

流程：

```text
POST /digest/video-url
↓
transcript_service
↓
subtitle_tool.extract_subtitle
↓
如果有字幕：run_text_digest_workflow(transcript)
↓
如果没有字幕：whisper_tool.fallback_to_whisper
↓
Whisper 成功：run_text_digest_workflow(transcript)
↓
Whisper 失败：返回 error 和 trace
```

采用 subtitle-first + Whisper fallback 的原因是：优先提取平台已有字幕，字幕缺失时再调用 faster-whisper 进行语音识别，从而兼顾效率、成本和可用性。

## Tool Registry 与 Skills Prompt

本项目将工具能力统一注册到 Tool Registry 中，并将不同任务的 Prompt 抽离为 Skills Prompt 文件。这样后续新增工具、调整提示词或接入 MCP Server 时，不需要大范围修改业务代码。

当前 Tool Registry 位于：

```text
backend/tools/registry.py
```

已注册的核心工具包括：

- extract_subtitle
- whisper_fallback
- split_text
- compress_context
- generate_summary
- generate_keywords
- generate_quiz
- generate_mindmap

Skills Prompt 位于：

```text
backend/skills/
```

`skill_service` 提供 `load_skill`、`list_skills` 和 `render_skill`，用于统一加载和渲染 prompt。本阶段不是新增用户功能，而是提升工具和 prompt 管理的可维护性。

MCP Server 当前只做预留设计，后续可以把 Tool Registry 中的工具包装成 MCP tools，对外暴露给其他 Agent 或客户端。
