# API Reference

默认后端地址：

```text
http://127.0.0.1:8000
```

## GET /health

### 功能说明

健康检查接口，用于确认 FastAPI 后端是否启动。

### 请求参数

无。

### 示例请求

```bash
curl http://127.0.0.1:8000/health
```

### 示例响应

```json
{
  "status": "ok",
  "service": "videomind-agent"
}
```

### 可能的错误情况

- 服务未启动：连接失败
- 端口被占用或地址错误：连接失败

## POST /digest/text

### 功能说明

输入学习文本，生成一句话总结、核心要点、关键术语解释、复习题和 Mermaid 思维导图。长文本会先进入切分和上下文压缩流程。

### 请求参数

请求体为 JSON：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| text | string | 是 | 需要消化的学习材料，最小长度为 1 |

### 示例请求

```bash
curl -X POST http://127.0.0.1:8000/digest/text \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"FastAPI 适合快速构建 Python API，LangGraph 可以编排多步骤 Agent 工作流。\"}"
```

### 示例响应

```json
{
  "trace_id": "9f2f4f5d7f8e4f1b9b6a8c7d6e5f4a3b",
  "one_sentence": "这段材料介绍了 FastAPI 和 LangGraph 在 Agent 项目中的作用。",
  "key_points": [
    "FastAPI 用于提供后端 API",
    "LangGraph 用于编排多步骤工作流"
  ],
  "terms": [
    {
      "term": "LangGraph",
      "simple_explain": "用于编排 Agent 状态图的框架。",
      "project_context": "在项目中串联 route、split、summary、quiz 等节点。",
      "interview_answer": "LangGraph 让多步骤 Agent 流程更清晰，也方便后续扩展分支和 trace。"
    }
  ],
  "quiz": [
    {
      "question": "为什么这个项目使用 LangGraph？",
      "answer": "因为它需要编排多个有状态节点，而不是只做一次模型调用。"
    }
  ],
  "mindmap": "mindmap\n  root((VideoMind Agent))\n    FastAPI\n    LangGraph"
}
```

### 可能的错误情况

- `422 Unprocessable Entity`：`text` 缺失或为空字符串
- `500 Internal Server Error`：LLM 配置缺失、LLM 返回无法解析、workflow 节点异常等

## POST /digest/video-url

### 功能说明

输入视频链接，后端先尝试提取平台字幕；如果字幕不可用，再尝试下载音频并使用 faster-whisper 转写。拿到 transcript 后复用文本 digest workflow。

### 请求参数

请求体为 JSON：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| url | string | 是 | 需要解析的视频链接，最小长度为 1 |

### 示例请求

```bash
curl -X POST http://127.0.0.1:8000/digest/video-url \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://example.com/video\"}"
```

### 示例响应：字幕或 Whisper 成功

```json
{
  "trace_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "input_type": "video_url",
  "transcript_source": "subtitle",
  "fallback_needed": false,
  "fallback_used": false,
  "one_sentence": "视频内容已经被整理成学习摘要。",
  "key_points": [
    "优先提取字幕",
    "复用文本 digest workflow"
  ],
  "terms": [],
  "quiz": [],
  "mindmap": "mindmap\n  root((Video))",
  "error": null
}
```

### 示例响应：字幕和 Whisper 都失败

视频转写失败时，当前接口仍保持 `200`，并通过响应体的 `error` 字段和 trace 暴露失败原因，方便前端展示 fallback 状态。

```json
{
  "trace_id": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
  "input_type": "video_url",
  "transcript_source": "none",
  "fallback_needed": true,
  "fallback_used": false,
  "one_sentence": "",
  "key_points": [],
  "terms": [],
  "quiz": [],
  "mindmap": "",
  "error": "Whisper fallback failed: model error"
}
```

### 可能的错误情况

- `422 Unprocessable Entity`：`url` 缺失或为空字符串
- `200` 且 `error` 不为空：字幕提取失败、视频不可访问、音频下载失败、faster-whisper 未安装、模型加载失败、转写结果为空
- `500 Internal Server Error`：拿到 transcript 后，文本 workflow 或 LLM 调用异常

## GET /trace/{trace_id}

### 功能说明

根据 `trace_id` 查询一次请求的 trace 日志。trace 文件保存在 `backend/storage/traces/{trace_id}.json`。

### 请求参数

路径参数：

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| trace_id | string | 是 | 32 位 uuid hex 字符串 |

### 示例请求

```bash
curl http://127.0.0.1:8000/trace/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
```

### 示例响应

```json
{
  "trace_id": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "input_type": "video_url",
  "tools_called": [
    "extract_subtitle",
    "route",
    "split",
    "summary",
    "term_explain",
    "quiz",
    "mindmap",
    "trace"
  ],
  "latency_ms": 1234,
  "input_length": 800,
  "chunk_count": 1,
  "compression_used": false,
  "compressed_length": 800,
  "route": "subtitle_first_whisper_fallback",
  "video_url": "https://example.com/video",
  "transcript_source": "subtitle",
  "fallback_needed": false,
  "fallback_used": false,
  "audio_downloaded": false,
  "whisper_model_size": null,
  "transcript_length": 800,
  "error": null,
  "output_path": "backend/storage/outputs/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.json"
}
```

### 可能的错误情况

- `400 Bad Request`：`trace_id` 不是 32 位十六进制字符串
- `404 Not Found`：对应 trace 文件不存在
- 服务未启动或 storage 挂载错误：连接失败或读取不到 trace
