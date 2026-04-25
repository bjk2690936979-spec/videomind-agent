import json
from pathlib import Path
from typing import Any, Dict, Optional
from uuid import uuid4

from backend.config import get_settings
from backend.schemas import DigestResponse, TraceInfo


def create_trace_id() -> str:
    return uuid4().hex


def _storage_path(*parts: str) -> Path:
    return get_settings().storage_dir.joinpath(*parts)


def _model_to_dict(model: Any) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


def save_output(trace_id: str, output: DigestResponse) -> Path:
    output_dir = _storage_path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{trace_id}.json"

    # 最终学习消化结果单独落盘，便于后续复查和前端读取。
    output_path.write_text(
        json.dumps(_model_to_dict(output), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def save_trace(trace: TraceInfo) -> Path:
    trace_dir = _storage_path("traces")
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / f"{trace.trace_id}.json"

    trace_path.write_text(
        json.dumps(_model_to_dict(trace), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return trace_path


def load_trace(trace_id: str) -> Optional[Dict[str, Any]]:
    trace_path = _storage_path("traces", f"{trace_id}.json")
    if not trace_path.exists():
        return None
    return json.loads(trace_path.read_text(encoding="utf-8"))
