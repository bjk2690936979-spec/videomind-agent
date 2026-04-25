from typing import Any

from backend.core.llm import generate_json
from backend.services.skill_service import load_skill


def generate_mindmap(text: str) -> str:
    skill = load_skill("mindmap")
    prompt = f"{skill}\n\n学习材料：\n{text}"

    result: Any = generate_json(prompt)
    # 非 dict 输出无法定位 mindmap 字段，返回空字符串让接口结构保持稳定。
    if isinstance(result, dict):
        return str(result.get("mindmap", "")).strip()
    return ""
