# Summary Skill

## Scenario

用于把学习材料压缩成适合复习和面试表达的结构化总结。

## Input

- 学习材料文本，通常由调用方追加到 prompt 末尾。

## Output

只返回 JSON：

{
  "one_sentence": "一句话总结",
  "key_points": [
    "关键点 1",
    "关键点 2",
    "关键点 3"
  ]
}

## Rules

- 不要返回 Markdown。
- one_sentence 用一句中文概括材料核心。
- key_points 提取 3 到 6 条，每条尽量简洁。

## Example

{
  "one_sentence": "FastAPI 适合快速构建类型清晰的 API 服务。",
  "key_points": [
    "使用类型注解描述请求和响应",
    "路由层负责接收请求",
    "服务层负责业务逻辑"
  ]
}
