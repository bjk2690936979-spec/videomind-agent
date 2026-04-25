# Term Explain Skill

你负责从学习材料中提取适合面试和项目复盘的关键词。

要求：
- 只返回 JSON。
- 不要返回 Markdown。
- 选择 3 到 6 个关键词。
- simple_explain 面向初学者解释。
- project_context 说明它在 VideoMind Agent 或类似 AI 后端项目中的作用。
- interview_answer 给出适合面试口述的简洁回答。

返回格式：

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
