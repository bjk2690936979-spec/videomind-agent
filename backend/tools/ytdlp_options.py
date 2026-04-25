from typing import Any

from backend.config import get_settings


def _settings_value(settings: Any, name: str) -> str:
    value = getattr(settings, name, "") or ""
    return str(value).strip()


def build_ytdlp_options(base_options: dict | None = None) -> dict:
    settings = get_settings()
    options = dict(base_options or {})

    # 鉴权参数统一由环境配置覆盖，避免调用方传入旧 cookie 导致行为不一致。
    options.pop("cookiefile", None)
    options.pop("cookiesfrombrowser", None)

    cookies_file = _settings_value(settings, "ytdlp_cookies_file")
    cookies_from_browser = _settings_value(settings, "ytdlp_cookies_from_browser")
    proxy = _settings_value(settings, "ytdlp_proxy")

    if cookies_file:
        options["cookiefile"] = cookies_file
    elif cookies_from_browser:
        options["cookiesfrombrowser"] = (cookies_from_browser,)

    if proxy:
        options["proxy"] = proxy

    return options


def apply_ytdlp_auth_options(options: dict) -> dict:
    return build_ytdlp_options(options)
