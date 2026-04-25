from typing import Any, Dict

from backend.tools.subtitle_tool import extract_subtitle
from backend.tools.whisper_tool import fallback_to_whisper


def get_transcript_from_video_url(video_url: str) -> Dict[str, Any]:
    # 视频链路优先复用平台字幕，只有字幕不可用时才走 Whisper 成本更高的 fallback。
    try:
        subtitle_result = extract_subtitle(video_url)
    except Exception as exc:
        return {
            "transcript": "",
            "transcript_source": "none",
            "fallback_needed": True,
            "fallback_used": False,
            "audio_path": "",
            "audio_downloaded": False,
            "whisper_model_size": None,
            "error": f"Subtitle extraction failed: {exc}",
        }

    transcript = str(subtitle_result.get("transcript") or "").strip()
    subtitle_found = bool(subtitle_result.get("subtitle_found")) and bool(transcript)

    if subtitle_found:
        return {
            "transcript": transcript,
            "transcript_source": "subtitle",
            "fallback_needed": False,
            "fallback_used": False,
            "audio_path": "",
            "audio_downloaded": False,
            "whisper_model_size": None,
            "error": subtitle_result.get("error"),
        }

    # 字幕缺失或为空时再下载音频并转写。
    try:
        whisper_result = fallback_to_whisper(video_url)
    except Exception as exc:
        return {
            "transcript": "",
            "transcript_source": "none",
            "fallback_needed": True,
            "fallback_used": False,
            "audio_path": "",
            "audio_downloaded": False,
            "whisper_model_size": None,
            "error": f"Whisper fallback failed: {exc}",
        }

    whisper_transcript = str(whisper_result.get("transcript") or "").strip()
    if whisper_result.get("success") and whisper_transcript:
        return {
            "transcript": whisper_transcript,
            "transcript_source": "whisper",
            "fallback_needed": False,
            "fallback_used": True,
            "audio_path": whisper_result.get("audio_path", ""),
            "audio_downloaded": bool(whisper_result.get("audio_downloaded", False)),
            "whisper_model_size": whisper_result.get("model_size"),
            "error": None,
        }

    # Whisper 失败时仍返回稳定结构，不让接口崩溃。
    return {
        "transcript": "",
        "transcript_source": "none",
        "fallback_needed": True,
        "fallback_used": False,
        "audio_path": whisper_result.get("audio_path", ""),
        "audio_downloaded": bool(whisper_result.get("audio_downloaded", False)),
        "whisper_model_size": whisper_result.get("model_size"),
        "error": whisper_result.get("error") or subtitle_result.get("error") or "Whisper fallback failed.",
    }
