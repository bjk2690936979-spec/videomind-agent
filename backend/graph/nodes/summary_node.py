from backend.graph.state import AgentState, append_tool
from backend.services import summarize_service


def summary_node(state: AgentState) -> AgentState:
    summary = summarize_service.summarize_digest_source(str(state.get("text") or ""))

    return {
        "one_sentence": summary["one_sentence"],
        "key_points": summary["key_points"],
        "tools_called": append_tool(state, "summary"),
    }
