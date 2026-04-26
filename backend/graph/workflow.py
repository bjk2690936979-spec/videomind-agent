from time import perf_counter
from typing import Any

from langgraph.graph import END, StateGraph

from backend.core.llm import (
    begin_token_usage_tracking,
    finish_token_usage_tracking,
    summarize_token_usage,
)
from backend.graph.nodes.keyword_node import keyword_node
from backend.graph.nodes.mindmap_node import mindmap_node
from backend.graph.nodes.quiz_node import quiz_node
from backend.graph.nodes.route_node import route_node
from backend.graph.nodes.split_node import split_node
from backend.graph.nodes.summary_node import summary_node
from backend.graph.nodes.trace_node import trace_node
from backend.graph.state import AgentState
from backend.schemas import DigestResponse, TraceInfo
from backend.services.trace_service import create_trace_id, save_trace


def build_text_digest_graph() -> Any:
    workflow = StateGraph(AgentState)

    # 当前文本链路是线性 DAG，后续扩展视频/多模态时可在 route 后分支。
    workflow.add_node("route", route_node)
    workflow.add_node("split", split_node)
    workflow.add_node("summary", summary_node)
    workflow.add_node("keyword", keyword_node)
    workflow.add_node("quiz", quiz_node)
    workflow.add_node("mindmap", mindmap_node)
    workflow.add_node("trace", trace_node)

    workflow.set_entry_point("route")
    workflow.add_edge("route", "split")
    workflow.add_edge("split", "summary")
    workflow.add_edge("summary", "keyword")
    workflow.add_edge("keyword", "quiz")
    workflow.add_edge("quiz", "mindmap")
    workflow.add_edge("mindmap", "trace")
    workflow.add_edge("trace", END)

    return workflow.compile()


def run_text_digest_workflow(text: str) -> DigestResponse:
    trace_id = create_trace_id()
    started_at = perf_counter()
    # 初始化所有下游节点会读取的字段，减少节点内的缺省判断。
    initial_state: AgentState = {
        "trace_id": trace_id,
        "input_type": "text",
        "raw_input": text,
        "text": text,
        "transcript": None,
        "chunks": [],
        "compressed_context": None,
        "one_sentence": "",
        "key_points": [],
        "terms": [],
        "quiz": [],
        "mindmap": "",
        "tools_called": [],
        "fallback_used": False,
        "error": None,
        "output_path": None,
        "input_length": len(text),
        "chunk_count": 1,
        "compression_used": False,
        "compressed_length": len(text),
        "latency_ms": 0,
        "started_at": started_at,
        "usage": [],
        "prompt_tokens": 0,
        "completion_tokens": 0,
        "total_tokens": 0,
    }

    graph = build_text_digest_graph()
    usage_token = begin_token_usage_tracking()
    try:
        final_state = graph.invoke(initial_state)
    except Exception as exc:
        usage = finish_token_usage_tracking(usage_token)
        token_totals = summarize_token_usage(usage)
        # 工作流失败时也记录 trace，方便后续排查。
        trace = TraceInfo(
            trace_id=trace_id,
            input_type="text",
            tools_called=list(initial_state.get("tools_called", [])),
            latency_ms=int((perf_counter() - started_at) * 1000),
            input_length=len(text),
            chunk_count=1,
            compression_used=False,
            compressed_length=len(text),
            error=str(exc),
            output_path=None,
            usage=usage,
            **token_totals,
        )
        save_trace(trace)
        raise
    finish_token_usage_tracking(usage_token)

    # trace_node 通常会放入完整 response；兜底构造保持旧调用方可用。
    response = final_state.get("response")
    if isinstance(response, DigestResponse):
        return response

    return DigestResponse(
        trace_id=trace_id,
        one_sentence=str(final_state.get("one_sentence") or ""),
        key_points=list(final_state.get("key_points", [])),
        terms=list(final_state.get("terms", [])),
        quiz=list(final_state.get("quiz", [])),
        mindmap=str(final_state.get("mindmap") or ""),
        latency_ms=int(final_state.get("latency_ms", 0)),
        usage=list(final_state.get("usage", [])),
        prompt_tokens=int(final_state.get("prompt_tokens", 0)),
        completion_tokens=int(final_state.get("completion_tokens", 0)),
        total_tokens=int(final_state.get("total_tokens", 0)),
    )
