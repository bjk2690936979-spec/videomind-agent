# MCP 预留设计

本阶段不实现真正的 MCP Server，只保留设计说明和适配方向。

## 为什么先做 Tool Registry

VideoMind Agent 当前已经有字幕提取、Whisper 转写、文本切分、上下文压缩、总结、关键词解释、复习题和思维导图生成等能力。先把这些能力注册到本地 Tool Registry，可以让工具的名称、输入、输出和 handler 形成统一描述。

这样后续接 MCP Server 时，不需要重新梳理工具边界，只需要把 registry 中的 ToolDefinition 包装成 MCP tools。

## 后续 MCP 适配方式

计划新增 MCP adapter，读取 Tool Registry：

1. 遍历 `registry.list_tools()`。
2. 将 `input_schema` 和 `output_schema` 映射为 MCP tool schema。
3. 将 `handler` 包装成 MCP tool call。
4. 保留 timeout、retry_count 等执行元信息。

## 计划暴露的 MCP Tools

- extract_subtitle
- whisper_fallback
- split_text
- compress_context
- generate_summary
- generate_keywords
- generate_quiz
- generate_mindmap

## 为什么 MVP 不直接实现 MCP Server

MVP 阶段的重点是跑通视频学习内容消化主链路。直接实现 MCP Server 会引入协议适配、鉴权、工具 schema 兼容和部署复杂度。当前先实现本地 Tool Registry，既能提升可维护性，也能为后续 MCP 接入预留清晰边界。

面试表达：我在项目中先实现本地 Tool Registry，把字幕提取、Whisper 转写、长文本压缩、总结、关键词、复习题和思维导图生成等能力统一注册。后续可以把这些工具通过 MCP Server 暴露给其他 Agent 或客户端调用。
