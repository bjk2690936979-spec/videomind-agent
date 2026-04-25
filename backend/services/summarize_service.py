from typing import Any, Dict, List

from backend.core.llm import generate_json
from backend.services.skill_service import load_skill


def _as_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def summarize_text(text: str) -> Dict[str, Any]:
    skill = load_skill("summary")
    prompt = f"{skill}\n\n学习材料：\n{text}"

    result = generate_json(prompt)
    if not isinstance(result, dict):
        result = {}

    # 对模型输出做轻量归一化，保证 API 返回结构稳定。
    return {
        "one_sentence": str(result.get("one_sentence", "")).strip(),
        "key_points": _as_string_list(result.get("key_points")),
    }
