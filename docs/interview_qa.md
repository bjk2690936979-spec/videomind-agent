# VideoMind Agent Interview Q&A

## 1. 你的项目是做什么的？

VideoMind Agent 是一个把学习视频或长文本资料转成结构化学习内容的 Agent 项目。用户可以输入文本或视频链接，系统会生成一句话总结、核心要点、关键术语解释、复习题和 Mermaid 思维导图，并保存 trace 方便复盘每一步链路。它不是单纯的摘要 demo，而是包含 FastAPI 接口、LangGraph 工作流、字幕提取、Whisper fallback、长文本压缩、Prompt 管理、Tool Registry 和评测脚本的完整 MVP。

## 2. 为什么用 FastAPI？

我选 FastAPI 是因为这个项目需要清晰的 HTTP API、请求响应模型和自动校验。FastAPI 和 Pydantic 配合后，`/digest/text`、`/digest/video-url`、`/trace/{trace_id}` 这些接口的输入输出结构比较明确，也方便写测试和前端调用。对简历项目来说，它能比较快地把 Agent 能力封装成可复现的服务。

## 3. 为什么用 LangGraph？

这个项目不是一次 LLM 调用，而是有 route、split、summary、keyword、quiz、mindmap、trace 多个步骤。LangGraph 可以把这些步骤表达成状态图，每个节点读取和更新同一个 state。这样比把逻辑都写在一个函数里更容易扩展，比如后续加入视频分支、RAG 节点、人工审核节点或失败重试节点。

## 4. LangGraph 工作流具体怎么走？

文本链路是 `route -> split -> summary -> keyword -> quiz -> mindmap -> trace`。`route` 做输入归一化，`split` 判断是否长文本并可能压缩，后面几个节点分别生成学习内容，最后 `trace` 保存输出和链路元信息。视频链路会先把视频转成 transcript，再复用同一条文本 workflow。

## 5. 为什么 subtitle-first？

因为平台已有字幕通常比重新语音识别更快、更便宜，也更稳定。项目里会先用 yt-dlp 获取人工字幕或自动字幕，优先中文，其次英文。如果拿到有效字幕，就直接进入文本 digest workflow，不再调用 Whisper。这样可以降低延迟、减少本地算力消耗，也避免不必要的音频下载。

## 6. Whisper fallback 怎么做？

当字幕不存在、为空或解析失败时，后端会进入 Whisper fallback：先用 yt-dlp 下载音频到 `backend/storage/audio`，再用 faster-whisper 按环境变量指定的模型大小、设备和 compute_type 转写。成功后把转写文本交给文本 workflow；失败时接口不会崩溃，而是返回稳定结构，并在 trace 里记录 `fallback_used`、`audio_downloaded`、`whisper_model_size` 和 error。

## 7. 长文本怎么处理？

当前阈值是 6000 字符。短文本直接进入总结、术语、复习题和思维导图节点；长文本会先切成多个 chunk，然后逐段压缩，再合并成 `compressed_context`。后续节点使用压缩后的上下文，避免一次性把超长 transcript 塞给模型导致上下文溢出或质量下降。

## 8. chunk size 怎么考虑？

当前默认 `chunk_size=2500`、`overlap=200`，这是一个偏保守的 MVP 参数。chunk 太大容易接近模型上下文上限，太小又会丢失局部语义并增加调用次数。overlap 用来保留段落边界附近的信息，减少切分造成的语义断裂。后续更好的做法是按 token、句子或字幕时间段切分，而不是只按字符长度。

## 9. Skills Prompt 有什么作用？

Skills Prompt 把不同任务的 prompt 放到 `backend/skills/`，例如 summary、quiz、mindmap、context_compress。业务代码只负责加载 skill 和调用模型，不把大段 prompt 写死在 Python 里。这样方便单独迭代 prompt，也能让面试官看到项目把“提示词能力”和“业务流程”做了解耦。

## 10. Tool Registry 有什么作用？

Tool Registry 在 `backend/tools/registry.py`，用于统一描述工具的名称、说明、输入输出 schema、handler、timeout 和 retry_count。当前注册了字幕提取、Whisper fallback、文本切分、上下文压缩、总结、关键词、复习题和思维导图工具。它让工具能力有统一元数据，后续可以很自然地改造成 MCP Server 或供前端展示工具链路。

## 11. trace 记录什么？

trace 记录一次请求的链路元信息，包括 `trace_id`、输入类型、调用过的工具、耗时、输入长度、chunk 数量、是否压缩、压缩后长度、视频 transcript 来源、是否用了 fallback、音频是否下载、Whisper 模型、错误信息和输出文件路径。它的价值是可观测性：当结果不好或接口失败时，可以定位是字幕、Whisper、压缩、LLM 还是存储环节的问题。

## 12. 这个项目和夸克/百度网盘有什么区别？

夸克或百度网盘更像成熟产品，重点是文件管理、在线播放、云端转码、搜索和多端同步。VideoMind Agent 是一个工程学习型 Agent 项目，重点展示如何把视频理解流程拆成可编排、可追踪、可扩展的后端链路。它目前不追求完整网盘能力，而是聚焦视频学习内容消化和 Agent 工程设计。

## 13. 企业落地还需要补什么？

首先要补异步任务队列，因为视频下载、Whisper 和 LLM 调用都可能很慢；其次要补数据库和对象存储，用来管理任务、trace、用户文件和输出结果；还需要用户系统、权限隔离、成本统计、限流、重试、监控告警和更完整的评测体系。生产环境还要考虑模型稳定性、数据安全和内容合规。

## 14. 项目里最能体现工程思考的地方是什么？

我认为有三个点。第一是 subtitle-first + Whisper fallback，用成本更低的路径优先处理，失败才走兜底。第二是长文本压缩，把超长 transcript 先变成可控上下文再交给后续节点。第三是 trace 和 eval，让 Agent 不只是能生成结果，还能被复盘、测试和持续优化。

## 15. 如果模型输出不是合法 JSON 怎么办？

项目在 LLM 封装层做了 JSON 清洗和解析，兼容模型返回 Markdown 代码块或前后带少量解释文字的情况。如果仍然解析失败，会抛出明确异常并写入 trace。后续可以继续加强 schema 校验、自动修复重试和结构化输出能力。

## 16. 你怎么介绍这个项目的后续方向？

我会说当前版本已经完成了“可运行的学习内容消化闭环”，下一步优先做异步任务队列和数据库。异步队列解决视频任务耗时问题，数据库解决 trace、任务和用户数据的持久化问题。再往后可以做 MCP Server、RAG、前端可视化和成本统计，让项目从 MVP 更接近真实生产系统。
