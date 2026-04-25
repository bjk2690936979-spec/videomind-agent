from backend.graph.state import AgentState, append_tool
from backend.services import context_compression_service, summarize_service
from backend.tools.text_splitter import split_text


def split_node(state: AgentState) -> AgentState:
    text = str(state.get("text") or state.get("raw_input") or "")

    if len(text) <= summarize_service.LONG_TEXT_THRESHOLD:
        return {
            "chunks": [text],
            "compressed_context": None,
            "compression_used": False,
            "chunk_count": 1,
            "compressed_length": len(text),
            "tools_called": append_tool(state, "split"),
        }

    chunks = split_text(text)
    compressed_context = context_compression_service.compress_text(text)
    digest_source = summarize_service.format_compressed_context(compressed_context)

    # 长文本压缩后，后续节点统一读取 state["text"]。
    return {
        "text": digest_source,
        "chunks": chunks,
        "compressed_context": compressed_context,
        "compression_used": True,
        "chunk_count": len(chunks),
        "compressed_length": len(digest_source),
        "tools_called": append_tool(state, "split"),
    }
