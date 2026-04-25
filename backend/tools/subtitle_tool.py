import html
import json
import re
from typing import Any, Dict, Iterable, Optional

import requests
import yt_dlp

from backend.tools.ytdlp_options import build_ytdlp_options


SUBTITLE_EXT_PRIORITY = ("vtt", "srt", "json3")
# 先选中文，再选英文；没有命中时仍会遍历平台返回的其它语言。
LANGUAGE_PRIORITY = (
    "zh-Hans",
    "zh-CN",
    "zh",
    "zh-TW",
    "en",
    "en-US",
)


def _result(
    subtitle_found: bool,
    transcript: str = "",
    fallback_needed: bool = True,
    source: str = "none",
    error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "subtitle_found": subtitle_found,
        "transcript": transcript,
        "fallback_needed": fallback_needed,
        "source": source,
        "error": error,
    }


def _iter_language_keys(captions: Dict[str, Any]) -> Iterable[str]:
    used = set()
    for language in LANGUAGE_PRIORITY:
        if language in captions:
            used.add(language)
            yield language
    for language in captions:
        if language not in used:
            yield language


def _select_caption(captions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    # 同一种语言下优先选更容易解析的字幕格式。
    for language in _iter_language_keys(captions):
        formats = captions.get(language) or []
        for ext in SUBTITLE_EXT_PRIORITY:
            for item in formats:
                if item.get("ext") == ext and item.get("url"):
                    return item
    return None


def _strip_caption_tags(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_json3(content: str) -> str:
    payload = json.loads(content)
    lines = []
    for event in payload.get("events", []):
        # json3 的一句字幕可能拆在多个 segs 里，需要先拼回完整行。
        segments = event.get("segs") or []
        line = "".join(segment.get("utf8", "") for segment in segments)
        line = _strip_caption_tags(line)
        if line:
            lines.append(line)
    return " ".join(lines).strip()


def _parse_vtt_or_srt(content: str) -> str:
    lines = []
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.upper().startswith(("WEBVTT", "NOTE", "STYLE", "REGION")):
            continue
        if line.isdigit():
            continue
        if "-->" in line:
            continue

        cleaned = _strip_caption_tags(line)
        if cleaned:
            lines.append(cleaned)

    # 去掉相邻重复行，减少自动字幕常见的重复片段。
    deduped = []
    for line in lines:
        if not deduped or deduped[-1] != line:
            deduped.append(line)
    return " ".join(deduped).strip()


def _subtitle_to_text(content: str, ext: str) -> str:
    if ext == "json3":
        return _parse_json3(content)
    return _parse_vtt_or_srt(content)


def _download_subtitle_text(caption: Dict[str, Any]) -> str:
    response = requests.get(caption["url"], timeout=20)
    response.raise_for_status()
    return response.text


def extract_subtitle(video_url: str) -> Dict[str, Any]:
    if not video_url or not video_url.strip():
        return _result(False, error="video_url must not be empty.")

    options = build_ytdlp_options(
        {
            "skip_download": True,
            "quiet": True,
            "no_warnings": True,
        }
    )

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(video_url, download=False)
    except Exception as exc:
        return _result(False, error=f"yt-dlp failed: {exc}")

    # 优先人工字幕，其次自动字幕，成功后就无需 Whisper fallback。
    subtitles = info.get("subtitles") or {}
    automatic_captions = info.get("automatic_captions") or {}
    caption = _select_caption(subtitles) or _select_caption(automatic_captions)
    if not caption:
        return _result(False, error="No subtitle found.")

    try:
        content = _download_subtitle_text(caption)
        transcript = _subtitle_to_text(content, str(caption.get("ext") or "vtt"))
    except Exception as exc:
        return _result(False, error=f"Failed to read subtitle: {exc}")

    if not transcript:
        return _result(False, error="Subtitle content is empty.")

    # 本阶段只要成功拿到字幕，就进入已有文本消化工作流。
    return _result(
        True,
        transcript=transcript,
        fallback_needed=False,
        source="subtitle",
        error=None,
    )
