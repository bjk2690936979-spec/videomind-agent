from backend.graph.state import AgentState, append_tool
from backend.services import keyword_service


def keyword_node(state: AgentState) -> AgentState:
    terms = keyword_service.explain_terms(str(state.get("text") or ""))

    return {
        "terms": terms,
        "tools_called": append_tool(state, "term_explain"),
    }
