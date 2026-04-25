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
