from time import perf_counter
from typing import List

from fastapi import APIRouter, HTTPException

from backend.schemas import DigestResponse, TextDigestRequest, TraceInfo
from backend.services import keyword_service, mindmap_service, quiz_service, summarize_service
from backend.services.trace_service import create_trace_id, save_output, save_trace


router = APIRouter(prefix="/digest", tags=["digest"])


@router.post("/text", response_model=DigestResponse)
async def digest_text(request: TextDigestRequest) -> DigestResponse:
    trace_id = create_trace_id()
    started_at = perf_counter()
    tools_called: List[str] = []
    output_path = None
    input_length = len(request.text)
    chunk_count = 1
    compression_used = False
    compressed_length = input_length

    try:
        summary = summarize_service.summarize_text(request.text)
        tools_called.append("summary")
        digest_source = str(summary.get("digest_source") or request.text)
        chunk_count = int(summary.get("chunk_count", 1))
        compression_used = bool(summary.get("compression_used", False))
        compressed_length = int(summary.get("compressed_length", len(digest_source)))

        terms = keyword_service.explain_terms(digest_source)
        tools_called.append("term_explain")

        quiz = quiz_service.generate_quiz(digest_source)
        tools_called.append("quiz")

        mindmap = mindmap_service.generate_mindmap(digest_source)
        tools_called.append("mindmap")

        response = DigestResponse(
            trace_id=trace_id,
            one_sentence=summary["one_sentence"],
            key_points=summary["key_points"],
            terms=terms,
            quiz=quiz,
            mindmap=mindmap,
        )
        output_path = str(save_output(trace_id, response))

        # 记录本次执行链路，后续可以继续扩展节点耗时和中间结果。
        trace = TraceInfo(
            trace_id=trace_id,
            input_type="text",
            tools_called=tools_called,
            latency_ms=int((perf_counter() - started_at) * 1000),
            input_length=input_length,
            chunk_count=chunk_count,
            compression_used=compression_used,
            compressed_length=compressed_length,
            error=None,
            output_path=output_path,
        )
        save_trace(trace)
        return response
    except Exception as exc:
        trace = TraceInfo(
            trace_id=trace_id,
            input_type="text",
            tools_called=tools_called,
            latency_ms=int((perf_counter() - started_at) * 1000),
            input_length=input_length,
            chunk_count=chunk_count,
            compression_used=compression_used,
            compressed_length=compressed_length,
            error=str(exc),
            output_path=output_path,
        )
        save_trace(trace)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
