# Mindmap Skill

## Scenario

用于把学习材料整理成 Mermaid mindmap，便于快速复习。

## Input

- 学习材料文本、总结文本或关键词解释。

## Output

只返回 JSON：

{
  "mindmap": "mindmap\n  root((主题))\n    分支 1\n    分支 2"
}

## Rules

- 不要返回 Markdown。
- mindmap 字段中返回合法 Mermaid mindmap 文本。
- Mermaid 内容必须以 mindmap 开头。
- 层级不要过深，适合快速复习。

## Example

{
  "mindmap": "mindmap\n  root((VideoMind Agent))\n    FastAPI\n    LangGraph\n    Tools"
}
