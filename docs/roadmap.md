# Roadmap

## 1. MCP Server

为什么需要：当前 Tool Registry 已经有工具元数据，但还只能在项目内部使用。如果改造成 MCP Server，就可以把字幕提取、Whisper fallback、文本压缩、总结等能力暴露给其他 Agent 或 IDE 客户端。

落地方式：从 `backend/tools/registry.py` 读取工具定义，把 `input_schema`、`output_schema` 和 handler 包装成 MCP tool call，并复用 timeout、retry_count 等元信息。

## 2. 数据库

为什么需要：当前 trace 和 output 以 JSON 文件保存在 storage，适合 MVP，但不适合多用户查询、筛选、统计和生产运维。

落地方式：引入 PostgreSQL 或 SQLite，建立 users、tasks、traces、outputs、eval_runs 等表；文件型大对象仍可留在对象存储，只在数据库保存元数据和路径。

## 3. 异步任务队列

为什么需要：视频下载、Whisper 转写和 LLM 调用耗时较长，同步 HTTP 请求容易超时，前端体验也不稳定。

落地方式：使用 Celery、RQ、Dramatiq 或 FastAPI BackgroundTasks 的轻量版本。接口先创建任务并返回 task_id，前端轮询任务状态，worker 异步执行视频处理和 digest workflow。

## 4. 前端可视化

为什么需要：当前 Streamlit 前端能展示结果，但 Mermaid mindmap 还只是文本，trace 也没有流程图或时间线，面向用户的可读性还不够。

落地方式：渲染 Mermaid 图，增加 workflow 节点状态、tools_called 时间线、压缩前后长度对比、fallback 状态提示和错误定位面板。

## 5. RAG

为什么需要：当前系统主要生成摘要和复习材料，不能围绕视频内容做多轮问答，也不能精准引用原文片段。

落地方式：保存 transcript chunks，生成 embedding，接入向量数据库或本地索引。用户提问时先召回相关 chunk，再把上下文交给 LLM 回答，并返回引用片段。

## 6. 用户系统

为什么需要：生产环境需要区分不同用户的数据、任务、配额和权限，不能所有 trace 和输出都混在同一个 storage 目录中。

落地方式：增加登录、用户表、token 鉴权和任务归属字段。API 层按用户过滤 trace、output 和任务状态，storage 路径也按 user_id 隔离。

## 7. 对象存储

为什么需要：音频、字幕、输出 JSON 和未来的视频片段都可能变大，本地磁盘不适合扩容、备份和多实例部署。

落地方式：接入 S3、MinIO 或云厂商对象存储。后端只保存对象 key 和元数据，下载音频、字幕文件、输出结果统一写入 bucket。

## 8. 成本统计

为什么需要：Agent 应用的成本来自 LLM token、Whisper 转写、下载耗时和存储。没有成本统计，就难以做限流、套餐和优化决策。

落地方式：在 LLM 封装层记录模型、token、调用耗时和错误；在 Whisper 链路记录音频时长、模型大小和转写耗时；按 task_id、user_id 汇总成本报表。
