from pathlib import Path
from types import SimpleNamespace

from backend.graph.workflow import run_text_digest_workflow
from backend.services import keyword_service, mindmap_service, quiz_service, summarize_service, trace_service


def test_run_text_digest_workflow_returns_digest_response(tmp_path, monkeypatch) -> None:
    # 固定各节点的 LLM 响应，专注验证 LangGraph 串联和 trace 输出。
    monkeypatch.setattr(
        trace_service,
        "get_settings",
        lambda: SimpleNamespace(storage_dir=tmp_path),
    )
    monkeypatch.setattr(
        summarize_service,
        "generate_json",
        lambda prompt: {
            "one_sentence": "LangGraph 串起了文本学习消化流程。",
            "key_points": ["RouteNode 识别输入", "TraceNode 保存结果"],
        },
    )
    monkeypatch.setattr(
        keyword_service,
        "generate_json",
        lambda prompt: {
            "terms": [
                {
                    "term": "LangGraph",
                    "simple_explain": "用于编排 Agent 工作流。",
                    "project_context": "串联 VideoMind Agent 的文本消化节点。",
                    "interview_answer": "LangGraph 可以把多步骤 Agent 流程表达成状态图。",
                }
            ]
        },
    )
    monkeypatch.setattr(
        quiz_service,
        "generate_json",
        lambda prompt: {
            "quiz": [
                {
                    "question": "TraceNode 的作用是什么？",
                    "answer": "保存输出和 trace，方便排查链路。",
                }
            ]
        },
    )
    monkeypatch.setattr(
        mindmap_service,
        "generate_json",
        lambda prompt: {"mindmap": "mindmap\n  root((LangGraph))\n    RouteNode\n    TraceNode"},
    )

    response = run_text_digest_workflow("LangGraph 文本工作流学习材料")

    assert response.one_sentence == "LangGraph 串起了文本学习消化流程。"
    assert response.terms[0].term == "LangGraph"
    assert Path(tmp_path, "outputs", f"{response.trace_id}.json").exists()
    assert Path(tmp_path, "traces", f"{response.trace_id}.json").exists()
