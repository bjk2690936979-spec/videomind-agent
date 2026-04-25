from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.api import routes_digest
from backend.main import app
from backend.schemas import DigestResponse, QuizItem, TermItem
from backend.services import trace_service, transcript_service


def _fake_digest_response(trace_id: str = "a" * 32) -> DigestResponse:
    # 视频接口只关心文本 workflow 的合同，这里构造稳定响应。
    return DigestResponse(
        trace_id=trace_id,
        one_sentence="视频内容已经进入文本消化流程。",
        key_points=["提取 transcript", "复用文本 workflow"],
        terms=[
            TermItem(
                term="subtitle-first",
                simple_explain="优先使用平台已有字幕。",
                project_context="减少重复语音识别成本。",
                interview_answer="先查字幕，没字幕再考虑 Whisper fallback。",
            )
        ],
        quiz=[
            QuizItem(
                question="为什么要 subtitle-first？",
                answer="已有字幕更快、更便宜，也更稳定。",
            )
        ],
        mindmap="mindmap\n  root((Video))\n    transcript",
    )


def test_transcript_service_skips_whisper_when_subtitle_exists(monkeypatch) -> None:
    # subtitle-first 命中时，Whisper 不应被调用。
    monkeypatch.setattr(
        transcript_service,
        "extract_subtitle",
        lambda url: {
            "subtitle_found": True,
            "transcript": "已有字幕",
            "fallback_needed": False,
            "source": "subtitle",
            "error": None,
        },
    )
    monkeypatch.setattr(
        transcript_service,
        "fallback_to_whisper",
        lambda url: (_ for _ in ()).throw(AssertionError("whisper should not be called")),
    )

    result = transcript_service.get_transcript_from_video_url("https://youtu.be/has-subtitle")

    assert result["transcript"] == "已有字幕"
    assert result["transcript_source"] == "subtitle"
    assert result["fallback_needed"] is False
    assert result["fallback_used"] is False


def test_digest_video_url_with_subtitle_enters_text_workflow(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        trace_service,
        "get_settings",
        lambda: SimpleNamespace(storage_dir=tmp_path),
    )
    monkeypatch.setattr(
        routes_digest.transcript_service,
        "get_transcript_from_video_url",
        lambda url: {
            "transcript": "这是视频字幕文本",
            "transcript_source": "subtitle",
            "fallback_needed": False,
            "fallback_used": False,
            "audio_downloaded": False,
            "whisper_model_size": None,
            "error": None,
        },
    )

    def fake_workflow(text: str) -> DigestResponse:
        assert text == "这是视频字幕文本"
        return _fake_digest_response()

    monkeypatch.setattr(routes_digest, "run_text_digest_workflow", fake_workflow)

    client = TestClient(app)
    response = client.post("/digest/video-url", json={"url": "https://youtu.be/demo"})

    assert response.status_code == 200
    data = response.json()
    assert data["input_type"] == "video_url"
    assert data["transcript_source"] == "subtitle"
    assert data["fallback_needed"] is False
    assert data["fallback_used"] is False
    assert data["one_sentence"] == "视频内容已经进入文本消化流程。"

    trace_path = Path(tmp_path, "traces", f"{data['trace_id']}.json")
    assert trace_path.exists()
    trace = client.get(f"/trace/{data['trace_id']}").json()
    assert trace["input_type"] == "video_url"
    assert trace["transcript_source"] == "subtitle"
    assert trace["fallback_used"] is False
    assert trace["tools_called"][0] == "extract_subtitle"


def test_digest_video_url_without_subtitle_uses_whisper(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        trace_service,
        "get_settings",
        lambda: SimpleNamespace(storage_dir=tmp_path),
    )
    monkeypatch.setattr(
        routes_digest.transcript_service,
        "get_transcript_from_video_url",
        lambda url: {
            "transcript": "这是 Whisper 转写文本",
            "transcript_source": "whisper",
            "fallback_needed": False,
            "fallback_used": True,
            "audio_downloaded": True,
            "whisper_model_size": "base",
            "error": None,
        },
    )

    def fake_workflow(text: str) -> DigestResponse:
        assert text == "这是 Whisper 转写文本"
        return _fake_digest_response(trace_id="b" * 32)

    monkeypatch.setattr(routes_digest, "run_text_digest_workflow", fake_workflow)

    client = TestClient(app)
    response = client.post("/digest/video-url", json={"url": "https://youtu.be/no-subtitle"})

    assert response.status_code == 200
    data = response.json()
    assert data["transcript_source"] == "whisper"
    assert data["fallback_needed"] is False
    assert data["fallback_used"] is True
    assert data["one_sentence"] == "视频内容已经进入文本消化流程。"

    trace = client.get(f"/trace/{data['trace_id']}").json()
    assert trace["transcript_source"] == "whisper"
    assert trace["fallback_used"] is True
    assert trace["audio_downloaded"] is True
    assert trace["whisper_model_size"] == "base"
    assert trace["transcript_length"] == len("这是 Whisper 转写文本")
    assert trace["tools_called"][:2] == ["extract_subtitle", "whisper_fallback"]


def test_digest_video_url_whisper_failure_does_not_crash(tmp_path, monkeypatch) -> None:
    # 转写失败是可展示状态，接口保持 200 并写入 trace。
    monkeypatch.setattr(
        trace_service,
        "get_settings",
        lambda: SimpleNamespace(storage_dir=tmp_path),
    )
    monkeypatch.setattr(
        routes_digest.transcript_service,
        "get_transcript_from_video_url",
        lambda url: {
            "transcript": "",
            "transcript_source": "none",
            "fallback_needed": True,
            "fallback_used": False,
            "audio_downloaded": False,
            "whisper_model_size": "base",
            "error": "Whisper transcription failed: model error",
        },
    )
    monkeypatch.setattr(
        routes_digest,
        "run_text_digest_workflow",
        lambda text: (_ for _ in ()).throw(AssertionError("workflow should not be called")),
    )

    client = TestClient(app)
    response = client.post("/digest/video-url", json={"url": "https://youtu.be/no-subtitle"})

    assert response.status_code == 200
    data = response.json()
    assert data["input_type"] == "video_url"
    assert data["transcript_source"] == "none"
    assert data["fallback_needed"] is True
    assert data["fallback_used"] is False
    assert "Whisper transcription failed" in data["error"]

    trace = client.get(f"/trace/{data['trace_id']}").json()
    assert trace["input_type"] == "video_url"
    assert trace["transcript_source"] == "none"
    assert trace["fallback_needed"] is True
    assert trace["fallback_used"] is False
    assert trace["tools_called"] == ["extract_subtitle", "whisper_fallback"]


def test_digest_video_url_subtitle_error_does_not_crash(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(
        trace_service,
        "get_settings",
        lambda: SimpleNamespace(storage_dir=tmp_path),
    )
    monkeypatch.setattr(
        routes_digest.transcript_service,
        "get_transcript_from_video_url",
        lambda url: {
            "transcript": "",
            "transcript_source": "none",
            "fallback_needed": True,
            "fallback_used": False,
            "audio_downloaded": False,
            "whisper_model_size": None,
            "error": "yt-dlp failed: invalid url",
        },
    )

    client = TestClient(app)
    response = client.post("/digest/video-url", json={"url": "not-a-real-url"})

    assert response.status_code == 200
    data = response.json()
    assert data["fallback_needed"] is True
    assert data["transcript_source"] == "none"
    assert "yt-dlp failed" in data["error"]
