# Term Explain Skill

## Scenario

用于从学习材料中提取适合项目复盘和面试表达的关键词。

## Input

- 学习材料文本或压缩后的上下文。

## Output

只返回 JSON：

{
  "terms": [
    {
      "term": "关键词",
      "simple_explain": "通俗解释",
      "project_context": "项目语境",
      "interview_answer": "面试回答"
    }
  ]
}

## Rules

- 不要返回 Markdown。
- 选择 3 到 6 个关键词。
- simple_explain 面向初学者解释。
- project_context 说明它在 VideoMind Agent 或类似 AI 后端项目中的作用。
- interview_answer 给出适合面试口述的简洁回答。

## Example

{
  "terms": [
    {
      "term": "LangGraph",
      "simple_explain": "一个用于编排 Agent 多步骤流程的图工作流框架。",
      "project_context": "用于串联文本消化的 route、split、summary、quiz 等节点。",
      "interview_answer": "我用 LangGraph 把 Agent 流程拆成状态节点，便于维护和扩展。"
    }
  ]
}
