from typing import Dict, List


def compress_chunks(chunks: List[str]) -> Dict[str, object]:
    if not chunks:
        raise ValueError("chunks must not be empty.")

    cleaned_chunks = [chunk.strip() for chunk in chunks if chunk and chunk.strip()]
    if not cleaned_chunks:
        raise ValueError("chunks must contain non-empty text.")

    # 这里做确定性合并，LLM 压缩逻辑放在 service 层统一编排。
    return {
        "global_summary": "\n".join(cleaned_chunks),
        "key_points": cleaned_chunks,
        "important_terms": [],
        "chunk_count": len(cleaned_chunks),
    }
