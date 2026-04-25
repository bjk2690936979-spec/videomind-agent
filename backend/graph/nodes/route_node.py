from backend.graph.state import AgentState, append_tool


def route_node(state: AgentState) -> AgentState:
    raw_input = str(state.get("raw_input") or state.get("text") or "")
    if not raw_input.strip():
        raise ValueError("text input must not be empty.")

    # 当前阶段只支持 text，后续视频输入再扩展这里。
    return {
        "input_type": "text",
        "raw_input": raw_input,
        "text": raw_input,
        "input_length": len(raw_input),
        "tools_called": append_tool(state, "route"),
    }
