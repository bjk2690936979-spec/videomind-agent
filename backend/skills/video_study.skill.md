# Video Study Skill

## Scenario

用于规划视频学习材料的消化流程，当前阶段支持字幕和 Whisper 转写后的文本消化。

## Input

- 视频字幕 transcript。
- Whisper fallback 转写文本。

## Output

输出应面向学习复盘，保留适合项目实践和面试表达的内容。

## Rules

- 优先保留核心概念、实现步骤和容易复习的结构。
- 不把无关细节放进最终结果。
- 后续可以配合 summary、term_explain、quiz、mindmap 等 skill 使用。

## Example

视频 transcript 会先转成文本上下文，再进入文本 digest workflow。
