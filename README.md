# VideoMind Agent

VideoMind Agent 是一个面向学习视频和长文本资料的 AI 学习内容消化项目。它把视频链接或文本输入转成结构化学习材料，包括一句话总结、核心要点、关键术语解释、复习题和 Mermaid 思维导图，同时记录 trace 方便排查每一步链路。

当前项目定位是简历展示和面试讲解型 MVP：后端链路已经跑通，前端提供 Streamlit 演示页，评测脚本用于做接口可用性和字段完整性回归。数据库、异步任务、用户系统、对象存储等属于后续优化。

## 项目背景

日常学习长视频时，直接看完再整理笔记成本很高。VideoMind Agent 试图把“提取内容 -> 压缩上下文 -> 生成学习材料 -> 留下可追踪日志”做成一条可复现的工程链路。

这个项目重点不只是调用大模型生成摘要，而是展示 Agent 项目里更重要的工程能力：

- 多步骤 workflow 编排
- 视频字幕优先和语音识别兜底
- 长文本上下文压缩
- Prompt 文件化管理
- Tool Registry 能力注册
- Trace 日志和评测回归

## 项目功能

- 文本学习内容生成：`POST /digest/text`
- 视频链接学习内容生成：`POST /digest/video-url`
- 健康检查：`GET /health`
- Trace 查询：`GET /trace/{trace_id}`
- Streamlit 前端演示：支持文本输入、视频链接输入、结果展示和 trace 查询
- Eval 回归脚本：检查接口可用性、字段完整性、trace_id、latency 和 error

## 技术栈

- 后端：FastAPI、Pydantic、Uvicorn
- Agent 编排：LangGraph
- LLM 调用：OpenAI Python SDK，支持 OpenAI 兼容网关
- 视频字幕和下载：yt-dlp、requests
- 语音转写兜底：faster-whisper
- 前端演示：Streamlit
- 测试和评测：pytest、requests、JSONL eval cases
- 部署复现：Docker、docker-compose

## 目录结构

```text
.
├── backend/
│   ├── api/                 # FastAPI 路由
│   ├── core/                # LLM 封装、异常、日志
│   ├── graph/               # LangGraph workflow 和节点
│   ├── services/            # 业务服务层
│   ├── skills/              # Prompt skill 文件
│   ├── tools/               # 字幕、Whisper、切分、压缩、registry
│   ├── storage/             # 运行产物，Docker 挂载，不进镜像
│   ├── config.py            # 环境变量配置
│   ├── main.py              # FastAPI 入口
│   └── schemas.py           # 请求和响应模型
├── docs/
│   ├── api.md
│   ├── architecture.md
│   ├── bad_cases.md
│   ├── interview_qa.md
│   └── roadmap.md
├── eval/
│   ├── eval_cases.jsonl
│   ├── eval_report.md
│   └── run_eval.py
├── frontend/
│   ├── app.py
│   └── README.md
├── tests/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## 核心流程

文本输入流程：

```text
用户文本
-> FastAPI /digest/text
-> LangGraph text digest workflow
-> 文本切分和长文本压缩
-> 总结、术语解释、复习题、思维导图
-> 保存 output 和 trace
-> 返回结构化学习内容
```

视频链接流程：

```text
视频 URL
-> FastAPI /digest/video-url
-> subtitle-first 字幕提取
-> 没有字幕时 Whisper fallback
-> transcript 复用文本 workflow
-> 补充视频 trace 元信息
-> 返回结构化学习内容
```

## LangGraph 工作流

当前文本 digest 使用 LangGraph 串联节点：

```text
route -> split -> summary -> keyword -> quiz -> mindmap -> trace
```

- `route`：校验和归一化文本输入
- `split`：判断是否长文本，必要时切分并压缩
- `summary`：生成一句话总结和核心要点
- `keyword`：生成关键术语解释、项目语境和面试回答
- `quiz`：生成复习题和答案
- `mindmap`：生成 Mermaid mindmap 文本
- `trace`：保存输出和 trace 文件

## subtitle-first + Whisper fallback

视频接口采用 subtitle-first 设计：

1. 先用 yt-dlp 读取平台字幕和自动字幕。
2. 优先选择中文，其次英文；格式优先级为 `vtt`、`srt`、`json3`。
3. 如果字幕存在且能解析出文本，直接进入文本 digest workflow。
4. 如果没有字幕或字幕为空，再下载音频并使用 faster-whisper 转写。
5. 如果 Whisper 也失败，接口保持稳定返回，并在响应和 trace 中写入 error。

这样做的原因是：已有字幕通常更快、更便宜、更稳定；Whisper 是兜底能力，适合没有字幕的场景，但成本和耗时更高。

## 长文本压缩策略

当前长文本阈值是 `6000` 字符。超过阈值后：

- 使用 `split_text` 按默认 `chunk_size=2500`、`overlap=200` 切分
- 对每个 chunk 使用 `context_compress` skill 做局部压缩
- 再合并成全局 `compressed_context`
- 后续 summary、keyword、quiz、mindmap 统一使用压缩后的上下文
- trace 记录 `input_length`、`chunk_count`、`compression_used`、`compressed_length`

`overlap` 用来减少切分边界造成的信息断裂。当前实现按字符长度切分，后续可以优化为按句子、字幕时间段或 token 切分。

## Skills Prompt

Prompt 文件放在 `backend/skills/`，由 `backend/services/skill_service.py` 读取。这样做的好处是：

- Prompt 和 Python 业务代码解耦
- 每个任务有独立 skill，例如 summary、quiz、mindmap、context_compress
- 面试时可以清楚解释“能力定义”和“执行逻辑”的边界
- 后续可以接入版本管理、AB 测试或按场景切换 Prompt

## Tool Registry

`backend/tools/registry.py` 定义了 Tool Registry，统一描述工具的：

- name
- description
- input_schema
- output_schema
- handler
- timeout
- retry_count

当前 registry 已注册字幕提取、Whisper fallback、文本切分、上下文压缩、总结、关键词、复习题和思维导图工具。现阶段主链路没有强制全部从 registry 调用，registry 主要作为工具元数据、测试和后续 MCP Server 改造的基础。

## Trace 日志

Trace 存储在 `backend/storage/traces/{trace_id}.json`，输出结果存储在 `backend/storage/outputs/{trace_id}.json`。

Trace 主要记录：

- `trace_id`
- `input_type`
- `tools_called`
- `latency_ms`
- `input_length`
- `chunk_count`
- `compression_used`
- `compressed_length`
- `route`
- `video_url`
- `transcript_source`
- `fallback_needed`
- `fallback_used`
- `audio_downloaded`
- `whisper_model_size`
- `transcript_length`
- `error`
- `output_path`

它的作用是让 Agent 链路可复盘：知道调用了哪些节点、是否压缩、是否用了 Whisper、失败在哪里、输出保存在哪里。

## 本地运行方式

建议使用 Python 3.11。

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

在 `.env` 中配置大模型：

```text
LLM_API_KEY=your_api_key
LLM_BASE_URL=
LLM_MODEL=your_model
```

启动后端：

```bash
uvicorn backend.main:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

## Docker 运行方式

项目提供 `Dockerfile` 和 `docker-compose.yml`。镜像不会复制 `.env`，也不会复制 `backend/storage` 中的音频、cookies、trace、outputs 等运行产物。

使用 Docker Compose 启动：

```bash
docker-compose up --build
```

或使用新版 Docker CLI：

```bash
docker compose up --build
```

后端地址：

```text
http://127.0.0.1:8000
```

`backend/storage` 会挂载到容器内 `/app/backend/storage`，运行产生的 trace、outputs、audio 仍保留在本地目录。

## API 示例

健康检查：

```bash
curl http://127.0.0.1:8000/health
```

文本 digest：

```bash
curl -X POST http://127.0.0.1:8000/digest/text \
  -H "Content-Type: application/json" \
  -d "{\"text\":\"FastAPI 适合快速构建 Python API 服务，LangGraph 可以编排多步骤 Agent 工作流。\"}"
```

视频 URL digest：

```bash
curl -X POST http://127.0.0.1:8000/digest/video-url \
  -H "Content-Type: application/json" \
  -d "{\"url\":\"https://example.com/video\"}"
```

查询 trace：

```bash
curl http://127.0.0.1:8000/trace/{trace_id}
```

完整接口说明见 [docs/api.md](docs/api.md)。

## 前端启动

先启动后端，再运行 Streamlit：

```bash
streamlit run frontend/app.py
```

默认前端地址：

```text
http://localhost:8501
```

前端侧边栏可以修改后端地址，默认是：

```text
http://127.0.0.1:8000
```

## 评测运行

先启动后端并配置好模型环境变量，然后运行：

```bash
python -m eval.run_eval --backend-url http://127.0.0.1:8000
```

评测用例位于 `eval/eval_cases.jsonl`，报告输出到 `eval/eval_report.md`。当前 eval 主要检查接口可用性、字段完整性、trace_id、latency 和 error，不做自动语义质量评分。

## 后续优化方向

- MCP Server：把 Tool Registry 暴露为标准工具协议
- 数据库：持久化用户、任务、trace 和评测结果
- 异步任务队列：处理视频下载、Whisper 和长 LLM 调用
- 前端可视化：渲染 Mermaid、展示 workflow 和 trace 时间线
- RAG：支持基于视频片段和笔记的问答
- 用户系统：隔离不同用户的数据和任务
- 对象存储：保存音频、字幕、输出文件等大对象
- 成本统计：记录模型 token、Whisper 耗时和任务成本

更详细计划见 [docs/roadmap.md](docs/roadmap.md)。
