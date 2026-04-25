from backend.graph.state import AgentState, append_tool
from backend.services import quiz_service


def quiz_node(state: AgentState) -> AgentState:
    quiz = quiz_service.generate_quiz(str(state.get("text") or ""))

    return {
        "quiz": quiz,
        "tools_called": append_tool(state, "quiz"),
    }
