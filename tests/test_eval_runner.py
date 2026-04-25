from pathlib import Path

from eval import run_eval


class FakeResponse:
    # requests.Response 的最小替身，只覆盖 eval runner 读取的属性。
    def __init__(self, payload, status_code=200) -> None:
        self._payload = payload
        self.status_code = status_code

    def json(self):
        return self._payload


def test_load_cases_reads_jsonl() -> None:
    cases = run_eval.load_cases()

    assert len(cases) >= 10
    assert cases[0]["id"] == "case_001"
    assert "expected_outputs" in cases[0]


def test_missing_outputs_detects_absent_fields() -> None:
    data = {
        "one_sentence": "一句话总结",
        "key_points": ["要点"],
    }

    missing = run_eval.missing_outputs(
        data,
        ["one_sentence", "key_points", "terms", "quiz"],
        error=None,
    )

    assert missing == ["terms", "quiz"]


def test_missing_outputs_treats_error_as_field() -> None:
    # 失败用例可以把 error 当作预期输出字段。
    missing = run_eval.missing_outputs(
        {"trace_id": "abc"},
        ["error"],
        error="No subtitle found.",
    )

    assert missing == []


def test_call_case_uses_text_endpoint(monkeypatch) -> None:
    calls = []

    def fake_post(url, json, timeout):
        calls.append((url, json, timeout))
        return FakeResponse(
            {
                "trace_id": "trace_001",
                "one_sentence": "总结",
                "key_points": ["要点"],
            }
        )

    monkeypatch.setattr(run_eval.requests, "post", fake_post)

    result = run_eval.call_case(
        {
            "id": "case_test",
            "input_type": "text",
            "input": "hello",
            "expected_route": "text_digest",
            "expected_outputs": ["one_sentence", "key_points"],
        },
        "http://127.0.0.1:8000",
    )

    assert calls[0][0] == "http://127.0.0.1:8000/digest/text"
    assert calls[0][1] == {"text": "hello"}
    assert result["success"] is True
    assert result["trace_id"] == "trace_001"


def test_call_case_records_missing_outputs(monkeypatch) -> None:
    monkeypatch.setattr(
        run_eval.requests,
        "post",
        lambda url, json, timeout: FakeResponse({"trace_id": "trace_002"}),
    )

    result = run_eval.call_case(
        {
            "id": "case_missing",
            "input_type": "video_url",
            "input": "https://example.com/video",
            "expected_route": "video_subtitle",
            "expected_outputs": ["one_sentence", "mindmap"],
        },
        "http://127.0.0.1:8000",
    )

    assert result["success"] is False
    assert result["missing_outputs"] == ["one_sentence", "mindmap"]


def test_write_report_generates_markdown(tmp_path) -> None:
    report_path = Path(tmp_path, "eval_report.md")
    results = [
        {
            "case_id": "case_001",
            "input_type": "text",
            "expected_route": "text_digest",
            "success": True,
            "missing_outputs": [],
            "trace_id": "trace_001",
            "latency_ms": 12,
            "error": None,
        },
        {
            "case_id": "case_002",
            "input_type": "text",
            "expected_route": "text_digest",
            "success": False,
            "missing_outputs": ["quiz"],
            "trace_id": None,
            "latency_ms": 20,
            "error": "missing field",
        },
    ]

    run_eval.write_report(results, report_path)

    content = report_path.read_text(encoding="utf-8")
    assert "# Eval Report" in content
    assert "| Total Cases | 2 |" in content
    assert "case_002" in content
    assert "quiz" in content
