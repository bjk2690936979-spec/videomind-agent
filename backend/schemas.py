from typing import List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    service: str


# 输入模型只做轻量校验，业务校验放在 workflow/service 层。
class TextDigestRequest(BaseModel):
    text: str = Field(..., min_length=1, description="需要消化的学习材料")


class VideoDigestRequest(BaseModel):
    url: str = Field(..., min_length=1, description="需要提取字幕的视频链接")


class TermItem(BaseModel):
    term: str
    simple_explain: str
    project_context: str
    interview_answer: str


class QuizItem(BaseModel):
    question: str
    answer: str


# Trace 同时承载文本和视频链路元信息，缺省值保证失败路径也能落盘。
class TraceInfo(BaseModel):
    trace_id: str
    input_type: str
    tools_called: List[str]
    latency_ms: int
    input_length: int = 0
    chunk_count: int = 1
    compression_used: bool = False
    compressed_length: int = 0
    route: Optional[str] = None
    video_url: Optional[str] = None
    transcript_source: Optional[str] = None
    fallback_needed: bool = False
    fallback_used: bool = False
    audio_downloaded: bool = False
    whisper_model_size: Optional[str] = None
    transcript_length: int = 0
    error: Optional[str] = None
    output_path: Optional[str] = None


class DigestResponse(BaseModel):
    trace_id: str
    one_sentence: str
    key_points: List[str]
    terms: List[TermItem]
    quiz: List[QuizItem]
    mindmap: str


# 视频接口在转写失败时仍返回 200，所以学习内容字段需要可为空。
class VideoDigestResponse(BaseModel):
    trace_id: str
    input_type: str
    transcript_source: str
    fallback_needed: bool
    fallback_used: bool = False
    one_sentence: str = ""
    key_points: List[str] = Field(default_factory=list)
    terms: List[TermItem] = Field(default_factory=list)
    quiz: List[QuizItem] = Field(default_factory=list)
    mindmap: str = ""
    error: Optional[str] = None
