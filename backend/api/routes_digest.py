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

    try:
        summary = summarize_service.summarize_text(request.text)
        tools_called.append("summary")

        terms = keyword_service.explain_terms(request.text)
        tools_called.append("term_explain")

        quiz = quiz_service.generate_quiz(request.text)
        tools_called.append("quiz")

        mindmap = mindmap_service.generate_mindmap(request.text)
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

        # trace 记录本次 Agent 执行链路，后续可扩展节点耗时和中间结果。
        trace = TraceInfo(
            trace_id=trace_id,
            input_type="text",
            tools_called=tools_called,
            latency_ms=int((perf_counter() - started_at) * 1000),
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
            error=str(exc),
            output_path=output_path,
        )
        save_trace(trace)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
