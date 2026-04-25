from types import SimpleNamespace

from backend.tools import ytdlp_options


def _settings(cookies_file: str = "", cookies_from_browser: str = "", proxy: str = "") -> SimpleNamespace:
    return SimpleNamespace(
        ytdlp_cookies_file=cookies_file,
        ytdlp_cookies_from_browser=cookies_from_browser,
        ytdlp_proxy=proxy,
    )


def _patch_settings(monkeypatch, settings: SimpleNamespace) -> None:
    monkeypatch.setattr(ytdlp_options, "get_settings", lambda: settings)


def test_build_ytdlp_options_without_cookies(monkeypatch) -> None:
    _patch_settings(monkeypatch, _settings())

    options = ytdlp_options.build_ytdlp_options({"quiet": True})

    assert options["quiet"] is True
    assert "cookiefile" not in options
    assert "cookiesfrombrowser" not in options


def test_build_ytdlp_options_uses_cookiefile(monkeypatch) -> None:
    cookiefile = "backend/storage/cookies/youtube_cookies.txt"
    _patch_settings(monkeypatch, _settings(cookies_file=cookiefile))

    options = ytdlp_options.build_ytdlp_options()

    assert options["cookiefile"] == cookiefile
    assert "cookiesfrombrowser" not in options


def test_build_ytdlp_options_prefers_cookiefile_over_browser(monkeypatch) -> None:
    # 显式 cookiefile 比浏览器 cookie 更可复现，应优先使用。
    cookiefile = "backend/storage/cookies/youtube_cookies.txt"
    _patch_settings(
        monkeypatch,
        _settings(cookies_file=cookiefile, cookies_from_browser="edge"),
    )

    options = ytdlp_options.build_ytdlp_options({"cookiesfrombrowser": ("chrome",)})

    assert options["cookiefile"] == cookiefile
    assert "cookiesfrombrowser" not in options


def test_build_ytdlp_options_uses_browser_when_cookiefile_empty(monkeypatch) -> None:
    _patch_settings(monkeypatch, _settings(cookies_from_browser="edge"))

    options = ytdlp_options.build_ytdlp_options()

    assert options["cookiesfrombrowser"] == ("edge",)
    assert "cookiefile" not in options


def test_build_ytdlp_options_uses_proxy(monkeypatch) -> None:
    proxy = "http://127.0.0.1:7890"
    _patch_settings(monkeypatch, _settings(proxy=proxy))

    options = ytdlp_options.build_ytdlp_options()

    assert options["proxy"] == proxy
