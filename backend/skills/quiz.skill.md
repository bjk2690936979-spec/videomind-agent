# Quiz Skill

## Scenario

用于根据学习材料生成复习题，帮助用户检查理解程度。

## Input

- 学习材料文本、总结文本或压缩后的上下文。

## Output

只返回 JSON：

{
  "quiz": [
    {
      "question": "问题",
      "answer": "答案"
    }
  ]
}

## Rules

- 不要返回 Markdown。
- 生成 3 到 5 道题。
- 题目优先覆盖核心概念、实现思路和容易混淆的点。
- answer 要简洁但完整。

## Example

{
  "quiz": [
    {
      "question": "为什么要把路由层和服务层分开？",
      "answer": "路由层负责请求响应，服务层负责业务逻辑，分层后更容易测试和维护。"
    }
  ]
}
