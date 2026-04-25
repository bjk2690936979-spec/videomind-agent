from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

import yt_dlp

from backend.config import get_settings
from backend.tools.ytdlp_options import build_ytdlp_options

try:
    from faster_whisper import WhisperModel
except ImportError:  # pragma: no cover - 方便缺少本地模型依赖时返回清晰错误。
    WhisperModel = None


def _result(success: bool, error: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
    payload = {"success": success, "error": error}
    payload.update(kwargs)
    return payload


def download_audio(video_url: str) -> Dict[str, Any]:
    if not video_url or not video_url.strip():
        return _result(False, audio_path="", error="video_url must not be empty.")

    settings = get_settings()
    audio_dir = settings.audio_storage_dir
    audio_dir.mkdir(parents=True, exist_ok=True)
    file_stem = uuid4().hex
    output_template = str(audio_dir / f"{file_stem}.%(ext)s")

    options = build_ytdlp_options(
        {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
        }
    )
    cookiefile = options.get("cookiefile")
    if cookiefile and not Path(str(cookiefile)).exists():
        return _result(
            False,
            audio_path="",
            error=f"Configured YTDLP_COOKIES_FILE does not exist: {cookiefile}",
        )

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            info = ydl.extract_info(video_url, download=True)
    except Exception as exc:
        return _result(False, audio_path="", error=f"Audio download failed: {exc}")

    audio_path = _find_downloaded_audio_path(audio_dir, file_stem, info)
    if not audio_path:
        return _result(False, audio_path="", error="Audio download finished but file was not found.")

    # 只下载音频，不下载视频文件；路径在 storage/audio 下且被 git 忽略。
    return _result(True, audio_path=str(audio_path), error=None)


def _find_downloaded_audio_path(audio_dir: Path, file_stem: str, info: Dict[str, Any]) -> Optional[Path]:
    # yt-dlp 不同版本返回的下载路径字段不同，这里按可信度依次查找。
    for item in info.get("requested_downloads") or []:
        filepath = item.get("filepath")
        if filepath and Path(filepath).exists():
            return Path(filepath)

    filepath = info.get("filepath") or info.get("_filename")
    if filepath and Path(filepath).exists():
        return Path(filepath)

    matches = sorted(audio_dir.glob(f"{file_stem}.*"))
    return matches[0] if matches else None


def transcribe_audio(audio_path: str) -> Dict[str, Any]:
    settings = get_settings()
    if WhisperModel is None:
        return _result(
            False,
            transcript="",
            model_size=settings.whisper_model_size,
            error="faster-whisper is not installed.",
        )
    if not audio_path or not Path(audio_path).exists():
        return _result(
            False,
            transcript="",
            model_size=settings.whisper_model_size,
            error="audio_path does not exist.",
        )

    try:
        model = WhisperModel(
            settings.whisper_model_size,
            device=settings.whisper_device,
            compute_type=settings.whisper_compute_type,
        )
        segments, _info = model.transcribe(audio_path)
        transcript = " ".join(
            str(getattr(segment, "text", "")).strip()
            for segment in segments
            if str(getattr(segment, "text", "")).strip()
        )
    except Exception as exc:
        return _result(
            False,
            transcript="",
            model_size=settings.whisper_model_size,
            error=f"Whisper transcription failed: {exc}",
        )

    if not transcript:
        return _result(
            False,
            transcript="",
            model_size=settings.whisper_model_size,
            error="Whisper transcript is empty.",
        )

    # 将所有 segments 合并成完整 transcript，交给现有文本 workflow。
    return _result(
        True,
        transcript=transcript,
        model_size=settings.whisper_model_size,
        error=None,
    )


def fallback_to_whisper(video_url: str) -> Dict[str, Any]:
    download_result = download_audio(video_url)
    if not download_result.get("success"):
        # 下载失败仍标记 fallback_used，表示确实尝试过 Whisper 路径。
        return {
            "transcript": "",
            "source": "whisper",
            "fallback_used": True,
            "audio_path": download_result.get("audio_path", ""),
            "audio_downloaded": False,
            "success": False,
            "error": download_result.get("error"),
            "model_size": get_settings().whisper_model_size,
        }

    audio_path = str(download_result["audio_path"])
    transcribe_result = transcribe_audio(audio_path)
    return {
        "transcript": str(transcribe_result.get("transcript") or ""),
        "source": "whisper",
        "fallback_used": True,
        "audio_path": audio_path,
        "audio_downloaded": True,
        "success": bool(transcribe_result.get("success")),
        "error": transcribe_result.get("error"),
        "model_size": transcribe_result.get("model_size", get_settings().whisper_model_size),
    }
