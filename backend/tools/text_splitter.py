from typing import List


def split_text(text: str, chunk_size: int = 2500, overlap: int = 200) -> List[str]:
    if not text or not text.strip():
        raise ValueError("text must not be empty.")
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than 0.")
    if overlap < 0:
        raise ValueError("overlap must not be negative.")
    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size.")

    text = text.strip()
    chunks: List[str] = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        # 下一段回退 overlap 个字符，保留上下文连续性。
        start = end - overlap

    return chunks
