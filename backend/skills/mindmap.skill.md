# Mindmap Skill

你负责把学习材料整理成 Mermaid mindmap。

要求：
- 只返回 JSON。
- 不要返回 Markdown。
- mindmap 字段中返回合法 Mermaid mindmap 文本。
- Mermaid 内容必须以 mindmap 开头。
- 层级不要过深，适合快速复习。

返回格式：

{
  "mindmap": "mindmap\n  root((主题))\n    分支 1\n    分支 2"
}
