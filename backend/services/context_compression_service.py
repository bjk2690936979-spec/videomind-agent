import json
from typing import Any, Dict, List

from backend.core.llm import generate_json
from backend.services.skill_service import load_skill
from backend.tools.context_compressor import compress_chunks
from backend.tools.text_splitter import split_text


def _as_string_list(value: Any) -> List[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _normalize_compressed_context(result: Any, chunk_count: int) -> Dict[str, Any]:
    if not isinstance(result, dict):
        result = {}

    return {
        "global_summary": str(result.get("global_summary", "")).strip(),
        "key_points": _as_string_list(result.get("key_points")),
        "important_terms": _as_string_list(result.get("important_terms")),
        "chunk_count": int(result.get("chunk_count") or chunk_count),
    }


def _summarize_chunk(skill: str, chunk: str, index: int, total: int) -> Dict[str, Any]:
    prompt = (
        f"{skill}\n\n"
        "任务：压缩单个文本分段。\n"
        f"分段序号：{index}/{total}\n\n"
        f"分段内容：\n{chunk}"
    )
    result = generate_json(prompt)
    return _normalize_compressed_context(result, 1)


def compress_text(text: str, chunk_size: int = 2500, overlap: int = 200) -> Dict[str, Any]:
    chunks = split_text(text, chunk_size=chunk_size, overlap=overlap)
    skill = load_skill("context_compress")

    chunk_contexts = [
        _summarize_chunk(skill, chunk, index + 1, len(chunks))
        for index, chunk in enumerate(chunks)
    ]
    chunk_summaries = [
        json.dumps(context, ensure_ascii=False)
        for context in chunk_contexts
    ]

    merged_context = compress_chunks(chunk_summaries)
    final_prompt = (
        f"{skill}\n\n"
        "任务：合并多个分段总结，生成一个全局 compressed_context。\n\n"
        f"分段总结：\n{json.dumps(merged_context, ensure_ascii=False, indent=2)}"
    )
    final_result = generate_json(final_prompt)
    compressed_context = _normalize_compressed_context(final_result, len(chunks))

    if not compressed_context["global_summary"]:
        compressed_context["global_summary"] = str(merged_context["global_summary"])
    if not compressed_context["key_points"]:
        compressed_context["key_points"] = list(merged_context["key_points"])

    compressed_context["chunk_count"] = len(chunks)
    return compressed_context
