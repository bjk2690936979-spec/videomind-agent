from typing import Any, Dict, List

from backend.core.llm import generate_json
from backend.services.context_compression_service import compress_text
from backend.services.skill_service import load_skill


LONG_TEXT_THRESHOLD = 6000


def _as_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return []


def _build_summary(text: str) -> Dict[str, Any]:
    skill = load_skill("summary")
    prompt = f"{skill}\n\n学习材料：\n{text}"

    result = generate_json(prompt)
    if not isinstance(result, dict):
        result = {}

    return {
        "one_sentence": str(result.get("one_sentence", "")).strip(),
        "key_points": _as_string_list(result.get("key_points")),
    }


def _format_compressed_context(compressed_context: Dict[str, Any]) -> str:
    key_points = "\n".join(f"- {item}" for item in compressed_context.get("key_points", []))
    important_terms = "、".join(compressed_context.get("important_terms", []))
    return (
        "压缩后的学习上下文：\n"
        f"全局总结：{compressed_context.get('global_summary', '')}\n"
        f"关键点：\n{key_points}\n"
        f"重要术语：{important_terms}\n"
        f"分段数量：{compressed_context.get('chunk_count', 1)}"
    )


def summarize_text(text: str) -> Dict[str, Any]:
    input_length = len(text)

    if input_length <= LONG_TEXT_THRESHOLD:
        summary = _build_summary(text)
        summary.update(
            {
                "digest_source": text,
                "compression_used": False,
                "chunk_count": 1,
                "compressed_length": input_length,
            }
        )
        return summary

    compressed_context = compress_text(text)
    digest_source = _format_compressed_context(compressed_context)
    summary = _build_summary(digest_source)

    # 长文本后续链路都使用压缩上下文，降低模型上下文压力。
    summary.update(
        {
            "digest_source": digest_source,
            "compressed_context": compressed_context,
            "compression_used": True,
            "chunk_count": int(compressed_context.get("chunk_count", 1)),
            "compressed_length": len(digest_source),
        }
    )
    return summary
