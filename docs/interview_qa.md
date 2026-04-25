# Interview Q&A：Eval 与 Bad Case

## 1. 你为什么要做 eval？

我做 eval 是为了让 Agent 项目具备可回归、可复盘、可优化的能力。每次改 workflow、prompt 或工具时，可以快速检查接口是否可用、字段是否完整、trace 是否生成。

## 2. 你评测哪些指标？

第一版主要评测接口可用性、字段完整性、trace_id、latency、error 和 expected_outputs 是否存在。暂时不做语义质量自动评分。

## 3. 你的 eval_cases.jsonl 里怎么设计 case？

我按输入类型和风险路径设计：短文本、长文本、技术概念、学习笔记、视频有字幕、视频 Whisper fallback、非法 URL、空文本和极短文本。

## 4. Agent 项目为什么不能只看最终答案？

因为 Agent 是多步骤链路，最终答案失败可能来自字幕、Whisper、压缩、LLM JSON、prompt 或存储。只看答案无法定位是哪一步出问题。

## 5. trace 和 eval 有什么关系？

eval 负责发现 case 是否成功，trace 负责解释为什么成功或失败。trace_id 可以把某条 eval case 关联到具体工具调用、耗时和错误信息。

## 6. 你怎么分析 bad case？

我会先看输入类型和 expected_route，再看 trace 中的 tools_called、latency_ms、error 和输出路径，判断问题出在工具层、服务层、LLM 输出还是外部网络。

## 7. 如果 LLM 输出格式不稳定怎么办？

我会先加强 prompt 约束，只允许返回 JSON；然后在 LLM 封装层做 JSON 解析兜底；后续可以增加 schema 校验、自动修复和重试。

## 8. 如果视频处理超时怎么办？

MVP 先用同步接口跑通链路。后续会引入异步任务队列，把视频下载、Whisper 转写和 LLM 处理拆成任务，并提供任务状态查询。

## 9. 如果长文本压缩丢信息怎么办？

我会检查 chunk_count、compressed_length 和 compression_used，再优化 chunk_size、overlap 和 map-reduce prompt。后续可以保留 chunk 级摘要，并做二次召回。

## 10. 这个 eval 和 RAGAS / LangSmith 有什么区别？

当前 eval 是轻量回归测试，主要检查链路可用性和字段完整性。RAGAS 和 LangSmith 更适合做语义质量、链路观测和大规模实验管理，可以作为后续增强。
