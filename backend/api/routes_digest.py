from time import perf_counter

from fastapi import APIRouter, HTTPException

from backend.graph.workflow import run_text_digest_workflow
from backend.schemas import (
    DigestResponse,
    TextDigestRequest,
    TraceInfo,
    VideoDigestRequest,
    VideoDigestResponse,
)
from backend.services import transcript_service
from backend.services.trace_service import create_trace_id, load_trace, save_trace, save_trace_data


router = APIRouter(prefix="/digest", tags=["digest"])


@router.post("/text", response_model=DigestResponse)
async def digest_text(request: TextDigestRequest) -> DigestResponse:
    try:
        return run_text_digest_workflow(request.text)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/video-url", response_model=VideoDigestResponse)
async def digest_video_url(request: VideoDigestRequest) -> VideoDigestResponse:
    started_at = perf_counter()
    transcript_result = transcript_service.get_transcript_from_video_url(request.url)
    transcript = str(transcript_result.get("transcript") or "")
    transcript_source = str(transcript_result.get("transcript_source") or "none")
    fallback_needed = bool(transcript_result.get("fallback_needed", True))
    fallback_used = bool(transcript_result.get("fallback_used", False))

    if transcript and not fallback_needed:
        digest = run_text_digest_workflow(transcript)
        # 文本 workflow 已保存 trace，这里补上视频来源和字幕/Whisper 元信息。
        trace_data = load_trace(digest.trace_id) or {
            "trace_id": digest.trace_id,
            "tools_called": [],
        }
        text_tools = list(trace_data.get("tools_called", []))
        # tools_called 保留真实执行顺序：先视频转文本，再进入文本消化链路。
        prefix_tools = ["extract_subtitle"]
        if fallback_used:
            prefix_tools.append("whisper_fallback")

        trace_data.update(
            {
                "trace_id": digest.trace_id,
                "input_type": "video_url",
                "route": "subtitle_first_whisper_fallback",
                "video_url": request.url,
                "transcript_source": transcript_source,
                "fallback_needed": False,
                "fallback_used": fallback_used,
                "audio_downloaded": bool(transcript_result.get("audio_downloaded", False)),
                "whisper_model_size": transcript_result.get("whisper_model_size"),
                "transcript_length": len(transcript),
                "tools_called": [*prefix_tools, *text_tools],
                "latency_ms": int((perf_counter() - started_at) * 1000),
                "error": transcript_result.get("error"),
            }
        )
        save_trace_data(digest.trace_id, trace_data)

        return VideoDigestResponse(
            trace_id=digest.trace_id,
            input_type="video_url",
            transcript_source=transcript_source,
            fallback_needed=False,
            fallback_used=fallback_used,
            one_sentence=digest.one_sentence,
            key_points=digest.key_points,
            terms=digest.terms,
            quiz=digest.quiz,
            mindmap=digest.mindmap,
            error=transcript_result.get("error"),
        )

    trace_id = create_trace_id()
    error = str(transcript_result.get("error") or "Transcript extraction failed.")
    # 未进入文本 workflow 时也生成独立 trace，方便前端查询失败细节。
    tools_called = ["extract_subtitle"]
    if transcript_result.get("whisper_model_size") or transcript_result.get("audio_downloaded"):
        tools_called.append("whisper_fallback")

    trace = TraceInfo(
        trace_id=trace_id,
        input_type="video_url",
        tools_called=tools_called,
        latency_ms=int((perf_counter() - started_at) * 1000),
        route="subtitle_first_whisper_fallback",
        video_url=request.url,
        transcript_source="none",
        fallback_needed=True,
        fallback_used=False,
        audio_downloaded=bool(transcript_result.get("audio_downloaded", False)),
        whisper_model_size=transcript_result.get("whisper_model_size"),
        transcript_length=0,
        error=error,
        output_path=None,
    )
    save_trace(trace)

    # 字幕和 Whisper 都失败时返回错误，但接口保持 200，方便前端展示 fallback 状态。
    return VideoDigestResponse(
        trace_id=trace_id,
        input_type="video_url",
        transcript_source="none",
        fallback_needed=True,
        fallback_used=False,
        error=error,
    )
