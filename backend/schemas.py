from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


class TextDigestRequest(BaseModel):
    text: str = Field(..., min_length=1, description="需要消化的学习材料")


class TermItem(BaseModel):
    term: str
    simple_explain: str
    project_context: str
    interview_answer: str


class QuizItem(BaseModel):
    question: str
    answer: str


class TraceInfo(BaseModel):
    trace_id: str
    input_type: str
    tools_called: List[str]
    latency_ms: int
    input_length: int = 0
    chunk_count: int = 1
    compression_used: bool = False
    compressed_length: int = 0
    error: Optional[str] = None
    output_path: Optional[str] = None


class DigestResponse(BaseModel):
    trace_id: str
    one_sentence: str
    key_points: List[str]
    terms: List[TermItem]
    quiz: List[QuizItem]
    mindmap: str
