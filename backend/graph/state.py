from typing import Any, Dict, List, Optional, TypedDict

from backend.schemas import QuizItem, TermItem


class AgentState(TypedDict, total=False):
    # LangGraph 节点按需返回部分字段，total=False 让状态增量更新更自然。
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
    usage: List[Dict[str, Any]]
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def append_tool(state: AgentState, tool_name: str) -> List[str]:
    # 返回新列表，避免节点之间共享并意外修改原始 tools_called。
    tools = list(state.get("tools_called", []))
    tools.append(tool_name)
    return tools
