from backend.tools import subtitle_tool


class FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return None


class FakeYDL:
    def __init__(self, info=None, error=None) -> None:
        self.info = info or {}
        self.error = error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        return None

    def extract_info(self, video_url, download=False):
        if self.error:
            raise self.error
        return self.info


def test_extract_subtitle_from_mocked_vtt(monkeypatch) -> None:
    info = {
        "subtitles": {
            "en": [
                {
                    "ext": "vtt",
                    "url": "https://example.com/subtitle.vtt",
                }
            ]
        }
    }
    monkeypatch.setattr(subtitle_tool.yt_dlp, "YoutubeDL", lambda options: FakeYDL(info=info))
    monkeypatch.setattr(
        subtitle_tool.requests,
        "get",
        lambda url, timeout=20: FakeResponse(
            "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello <c>world</c>\n"
        ),
    )

    result = subtitle_tool.extract_subtitle("https://www.youtube.com/watch?v=demo")

    assert result["subtitle_found"] is True
    assert result["fallback_needed"] is False
    assert result["source"] == "subtitle"
    assert result["transcript"] == "Hello world"
    assert result["error"] is None


def test_extract_subtitle_returns_fallback_when_no_subtitle(monkeypatch) -> None:
    monkeypatch.setattr(subtitle_tool.yt_dlp, "YoutubeDL", lambda options: FakeYDL(info={}))

    result = subtitle_tool.extract_subtitle("https://www.youtube.com/watch?v=demo")

    assert result["subtitle_found"] is False
    assert result["fallback_needed"] is True
    assert result["source"] == "none"
    assert result["error"] == "No subtitle found."


def test_extract_subtitle_returns_error_when_ytdlp_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        subtitle_tool.yt_dlp,
        "YoutubeDL",
        lambda options: FakeYDL(error=RuntimeError("invalid video")),
    )

    result = subtitle_tool.extract_subtitle("https://www.youtube.com/watch?v=demo")

    assert result["subtitle_found"] is False
    assert result["fallback_needed"] is True
    assert "yt-dlp failed" in result["error"]
