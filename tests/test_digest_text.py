from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.main import app
from backend.services import (
    context_compression_service,
    keyword_service,
    mindmap_service,
    quiz_service,
    summarize_service,
    trace_service,
)


def test_digest_text_creates_output_and_trace(tmp_path, monkeypatch) -> None:
    # 用固定 LLM 输出隔离外部模型依赖，只验证 API、workflow 和 trace 落盘。
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
    assert trace["tools_called"] == [
        "route",
        "split",
        "summary",
        "term_explain",
        "quiz",
        "mindmap",
        "trace",
    ]
    assert trace["input_length"] == len("FastAPI 学习材料")
    assert trace["chunk_count"] == 1
    assert trace["compression_used"] is False
    assert trace["compressed_length"] == len("FastAPI 学习材料")
    assert trace["error"] is None
    assert Path(trace["output_path"]).exists()


def test_digest_text_uses_compression_for_long_input(tmp_path, monkeypatch) -> None:
    # 长文本用例验证 split/compress 标记会写入 trace。
    monkeypatch.setattr(
        trace_service,
        "get_settings",
        lambda: SimpleNamespace(storage_dir=tmp_path),
    )
    monkeypatch.setattr(
        context_compression_service,
        "generate_json",
        lambda prompt: {
            "global_summary": "长文本压缩总结",
            "key_points": ["分段总结", "上下文压缩"],
            "important_terms": ["chunk", "compression"],
            "chunk_count": 4,
        },
    )
    monkeypatch.setattr(
        summarize_service,
        "generate_json",
        lambda prompt: {
            "one_sentence": "长文本已经先压缩再总结。",
            "key_points": ["先切分", "再压缩", "后总结"],
        },
    )
    monkeypatch.setattr(
        keyword_service,
        "generate_json",
        lambda prompt: {
            "terms": [
                {
                    "term": "上下文压缩",
                    "simple_explain": "把长内容变短但保留重点。",
                    "project_context": "用于处理超长 transcript。",
                    "interview_answer": "先分段总结，再合并成可供后续任务使用的上下文。",
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
                    "question": "为什么要做上下文压缩？",
                    "answer": "避免长文本超过模型上下文限制。",
                }
            ]
        },
    )
    monkeypatch.setattr(
        mindmap_service,
        "generate_json",
        lambda prompt: {"mindmap": "mindmap\n  root((长文本压缩))\n    split\n    compress"},
    )

    client = TestClient(app)
    long_text = "长文本学习材料。" * 1100

    response = client.post("/digest/text", json={"text": long_text})

    assert response.status_code == 200
    data = response.json()
    assert data["one_sentence"] == "长文本已经先压缩再总结。"

    trace = client.get(f"/trace/{data['trace_id']}").json()
    assert trace["tools_called"] == [
        "route",
        "split",
        "summary",
        "term_explain",
        "quiz",
        "mindmap",
        "trace",
    ]
    assert trace["input_length"] == len(long_text)
    assert trace["compression_used"] is True
    assert trace["chunk_count"] > 1
    assert trace["compressed_length"] < trace["input_length"]
