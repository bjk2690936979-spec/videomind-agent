import re
from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from backend.services.trace_service import load_trace


router = APIRouter(prefix="/trace", tags=["trace"])


@router.get("/{trace_id}")
async def get_trace(trace_id: str) -> Dict[str, Any]:
    # trace_id 只允许 uuid hex 风格，避免路径穿越。
    if not re.fullmatch(r"[a-fA-F0-9]{32}", trace_id):
        raise HTTPException(status_code=400, detail="Invalid trace_id.")

    trace = load_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found.")

    return trace
