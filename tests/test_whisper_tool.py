from pathlib import Path
from types import SimpleNamespace

from backend.tools import whisper_tool


class FakeYDL:
    def __init__(self, audio_dir: Path, error=None) -> None:
        self.audio_dir = audio_dir
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def extract_info(self, video_url, download=True):
        if self.error:
            raise self.error
        audio_path = self.audio_dir / "mock-audio.m4a"
        audio_path.write_text("audio", encoding="utf-8")
        return {"requested_downloads": [{"filepath": str(audio_path)}]}


class FakeSegment:
    def __init__(self, text: str) -> None:
        self.text = text


class FakeWhisperModel:
    def __init__(self, model_size, device="cpu", compute_type="int8") -> None:
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type

    def transcribe(self, audio_path):
        return [FakeSegment("hello"), FakeSegment("world")], None


class FailingWhisperModel(FakeWhisperModel):
    def transcribe(self, audio_path):
        raise RuntimeError("model error")


def _settings(tmp_path):
    return SimpleNamespace(
        audio_storage_dir=tmp_path,
        whisper_model_size="base",
        whisper_device="cpu",
        whisper_compute_type="int8",
    )


def test_download_audio_success(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(whisper_tool, "get_settings", lambda: _settings(tmp_path))
    monkeypatch.setattr(
        whisper_tool.yt_dlp,
        "YoutubeDL",
        lambda options: FakeYDL(tmp_path),
    )

    result = whisper_tool.download_audio("https://youtu.be/demo")

    assert result["success"] is True
    assert result["error"] is None
    assert Path(result["audio_path"]).exists()


def test_download_audio_failure(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(whisper_tool, "get_settings", lambda: _settings(tmp_path))
    monkeypatch.setattr(
        whisper_tool.yt_dlp,
        "YoutubeDL",
        lambda options: FakeYDL(tmp_path, error=RuntimeError("download error")),
    )

    result = whisper_tool.download_audio("https://youtu.be/demo")

    assert result["success"] is False
    assert "Audio download failed" in result["error"]


def test_transcribe_audio_success(tmp_path, monkeypatch) -> None:
    audio_path = tmp_path / "audio.m4a"
    audio_path.write_text("audio", encoding="utf-8")
    monkeypatch.setattr(whisper_tool, "get_settings", lambda: _settings(tmp_path))
    monkeypatch.setattr(whisper_tool, "WhisperModel", FakeWhisperModel)

    result = whisper_tool.transcribe_audio(str(audio_path))

    assert result["success"] is True
    assert result["transcript"] == "hello world"
    assert result["model_size"] == "base"


def test_transcribe_audio_failure(tmp_path, monkeypatch) -> None:
    audio_path = tmp_path / "audio.m4a"
    audio_path.write_text("audio", encoding="utf-8")
    monkeypatch.setattr(whisper_tool, "get_settings", lambda: _settings(tmp_path))
    monkeypatch.setattr(whisper_tool, "WhisperModel", FailingWhisperModel)

    result = whisper_tool.transcribe_audio(str(audio_path))

    assert result["success"] is False
    assert "Whisper transcription failed" in result["error"]


def test_fallback_to_whisper_success(tmp_path, monkeypatch) -> None:
    audio_path = tmp_path / "audio.m4a"
    audio_path.write_text("audio", encoding="utf-8")
    monkeypatch.setattr(whisper_tool, "get_settings", lambda: _settings(tmp_path))
    monkeypatch.setattr(
        whisper_tool,
        "download_audio",
        lambda video_url: {"success": True, "audio_path": str(audio_path), "error": None},
    )
    monkeypatch.setattr(
        whisper_tool,
        "transcribe_audio",
        lambda path: {
            "success": True,
            "transcript": "fallback transcript",
            "model_size": "base",
            "error": None,
        },
    )

    result = whisper_tool.fallback_to_whisper("https://youtu.be/demo")

    assert result["success"] is True
    assert result["source"] == "whisper"
    assert result["fallback_used"] is True
    assert result["audio_downloaded"] is True
    assert result["transcript"] == "fallback transcript"
