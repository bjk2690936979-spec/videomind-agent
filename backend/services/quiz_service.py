from typing import Any, List

from backend.core.llm import generate_json
from backend.schemas import QuizItem
from backend.services.skill_service import load_skill


def generate_quiz(text: str) -> List[QuizItem]:
    skill = load_skill("quiz")
    prompt = f"{skill}\n\n学习材料：\n{text}"

    result = generate_json(prompt)
    # 兼容模型直接返回数组，或包一层 {"quiz": [...]} 的情况。
    items = result.get("quiz", result) if isinstance(result, dict) else result
    if not isinstance(items, list):
        return []

    quiz: List[QuizItem] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        quiz.append(
            QuizItem(
                question=str(item.get("question", "")).strip(),
                answer=str(item.get("answer", "")).strip(),
            )
        )

    return [item for item in quiz if item.question]
