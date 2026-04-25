from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import keyword_service, mindmap_service, quiz_service, summarize_service, trace_service


def test_digest_text_creates_output_and_trace(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        trace_service,
        "get_settings",
        lambda: SimpleNamespace(storage_dir=tmp_path),
    )
    monkeypatch.setattr(
        summarize_service,
        "generate_json",
        lambda prompt: {
            "one_sentence": "FastAPI 用于快速构建 Python Web API。",
            "key_points": ["路由负责接收请求", "服务层负责业务逻辑"],
        },
    )
    monkeypatch.setattr(
        keyword_service,
        "generate_json",
        lambda prompt: {
            "terms": [
                {
                    "term": "FastAPI",
                    "simple_explain": "一个 Python Web 框架。",
                    "project_context": "用于提供 VideoMind Agent 的后端接口。",
                    "interview_answer": "FastAPI 基于类型注解，适合快速构建高性能 API。",
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
                    "question": "routes 层主要负责什么？",
                    "answer": "负责接收请求、调用服务并返回响应。",
                }
            ]
        },
    )
    monkeypatch.setattr(
        mindmap_service,
        "generate_json",
        lambda prompt: {"mindmap": "mindmap\n  root((FastAPI))\n    routes\n    services"},
    )

    client = TestClient(app)

    response = client.post("/digest/text", json={"text": "FastAPI 学习材料"})

    assert response.status_code == 200
    data = response.json()
    assert data["one_sentence"] == "FastAPI 用于快速构建 Python Web API。"
    assert data["key_points"] == ["路由负责接收请求", "服务层负责业务逻辑"]
    assert data["terms"][0]["term"] == "FastAPI"
    assert data["quiz"][0]["question"] == "routes 层主要负责什么？"
    assert data["mindmap"].startswith("mindmap")

    trace_id = data["trace_id"]
    assert Path(tmp_path, "outputs", f"{trace_id}.json").exists()
    assert Path(tmp_path, "traces", f"{trace_id}.json").exists()

    trace_response = client.get(f"/trace/{trace_id}")

    assert trace_response.status_code == 200
    trace = trace_response.json()
    assert trace["trace_id"] == trace_id
    assert trace["input_type"] == "text"
    assert trace["tools_called"] == ["summary", "term_explain", "quiz", "mindmap"]
    assert trace["error"] is None
    assert Path(trace["output_path"]).exists()
