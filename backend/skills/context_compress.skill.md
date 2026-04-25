# Context Compress Skill

## Scenario

用于把长学习材料压缩成适合后续总结、关键词解释、复习题和思维导图生成的上下文。

## Input

- 单个文本分段。
- 多个分段总结。

## Output

只返回 JSON：

{
  "global_summary": "全局压缩总结",
  "key_points": [
    "关键点 1",
    "关键点 2"
  ],
  "important_terms": [
    "术语 1",
    "术语 2"
  ],
  "chunk_count": 1
}

## Rules

- 不要返回 Markdown。
- 保留核心概念、因果关系、实现步骤和适合面试表达的内容。
- 删除重复、口水话和无关细节。
- key_points 输出 3 到 8 条。
- important_terms 输出 3 到 8 个术语。

## Example

{
  "global_summary": "这段材料介绍了长文本如何先切分再压缩。",
  "key_points": [
    "按字符切分文本",
    "逐段总结",
    "合并为全局上下文"
  ],
  "important_terms": [
    "chunk",
    "compression"
  ],
  "chunk_count": 3
}
