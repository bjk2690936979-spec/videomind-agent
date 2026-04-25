from typing import Any, Dict, List, Optional, TypedDict

from backend.schemas import QuizItem, TermItem


class AgentState(TypedDict, total=False):
    trace_id: str
    input_type: str
    raw_input: str
    text: str
    transcript: Optional[str]
    chunks: List[str]
    compressed_context: Optional[Dict[str, Any]]
    one_sentence: str
    key_points: List[str]
    terms: List[TermItem]
    quiz: List[QuizItem]
    mindmap: str
    tools_called: List[str]
    fallback_used: bool
    error: Optional[str]
    output_path: Optional[str]
    input_length: int
    chunk_count: int
    compression_used: bool
    compressed_length: int
    latency_ms: int
    started_at: float
    response: Any


def append_tool(state: AgentState, tool_name: str) -> List[str]:
    tools = list(state.get("tools_called", []))
    tools.append(tool_name)
    return tools
