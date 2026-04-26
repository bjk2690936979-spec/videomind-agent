from time import perf_counter

from backend.core.llm import current_token_usage, summarize_token_usage
from backend.graph.state import AgentState, append_tool
from backend.schemas import DigestResponse, TraceInfo
from backend.services.trace_service import save_output, save_trace


def trace_node(state: AgentState) -> AgentState:
    trace_id = str(state["trace_id"])
    tools_called = append_tool(state, "trace")
    latency_ms = int((perf_counter() - float(state.get("started_at", perf_counter()))) * 1000)
    usage = current_token_usage()
    token_totals = summarize_token_usage(usage)

    response = DigestResponse(
        trace_id=trace_id,
        one_sentence=str(state.get("one_sentence") or ""),
        key_points=list(state.get("key_points", [])),
        terms=list(state.get("terms", [])),
        quiz=list(state.get("quiz", [])),
        mindmap=str(state.get("mindmap") or ""),
        latency_ms=latency_ms,
        usage=usage,
        **token_totals,
    )
    output_path = str(save_output(trace_id, response))

    # trace 落盘放在最后一个节点，记录整条 LangGraph 链路。
    trace = TraceInfo(
        trace_id=trace_id,
        input_type=str(state.get("input_type") or "text"),
        tools_called=tools_called,
        latency_ms=latency_ms,
        input_length=int(state.get("input_length", len(str(state.get("raw_input") or "")))),
        chunk_count=int(state.get("chunk_count", 1)),
        compression_used=bool(state.get("compression_used", False)),
        compressed_length=int(state.get("compressed_length", 0)),
        error=state.get("error"),
        output_path=output_path,
        usage=usage,
        **token_totals,
    )
    save_trace(trace)

    return {
        "response": response,
        "output_path": output_path,
        "latency_ms": latency_ms,
        "tools_called": tools_called,
        "usage": usage,
        **token_totals,
    }
