from typing import Any, List

from backend.core.llm import generate_json
from backend.schemas import TermItem
from backend.services.skill_service import load_skill


def explain_terms(text: str) -> List[TermItem]:
    skill = load_skill("term_explain")
    prompt = f"{skill}\n\n学习材料：\n{text}"

    result = generate_json(prompt)
    # 兼容模型直接返回数组，或包一层 {"terms": [...]} 的情况。
    items = result.get("terms", result) if isinstance(result, dict) else result
    if not isinstance(items, list):
        return []

    terms: List[TermItem] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        terms.append(
            TermItem(
                term=str(item.get("term", "")).strip(),
                simple_explain=str(item.get("simple_explain", "")).strip(),
                project_context=str(item.get("project_context", "")).strip(),
                interview_answer=str(item.get("interview_answer", "")).strip(),
            )
        )

    return [term for term in terms if term.term]
