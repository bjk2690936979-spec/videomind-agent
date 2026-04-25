from backend.graph.state import AgentState, append_tool
from backend.services import mindmap_service


def mindmap_node(state: AgentState) -> AgentState:
    mindmap = mindmap_service.generate_mindmap(str(state.get("text") or ""))

    return {
        "mindmap": mindmap,
        "tools_called": append_tool(state, "mindmap"),
    }
