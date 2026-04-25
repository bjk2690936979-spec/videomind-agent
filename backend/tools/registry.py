from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from backend.services import keyword_service, mindmap_service, quiz_service, summarize_service
from backend.tools import context_compressor, subtitle_tool, text_splitter, whisper_tool


@dataclass
class ToolDefinition:
    name: str
    description: str
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    handler: Optional[Callable[..., Any]] = None
    timeout: int = 60
    retry_count: int = 0


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition) -> None:
        if not tool.name:
            raise ValueError("Tool name must not be empty.")
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> ToolDefinition:
        try:
            return self._tools[name]
        except KeyError as exc:
            raise KeyError(f"Tool not registered: {name}") from exc

    def list_tools(self) -> List[ToolDefinition]:
        return [self._tools[name] for name in sorted(self._tools)]

    def call_tool(self, name: str, **kwargs: Any) -> Any:
        tool = self.get_tool(name)
        if tool.handler is None:
            raise RuntimeError(f"Tool has no handler: {name}")
        # registry 只做分发，不吞掉工具内部异常，方便调用方记录 trace。
        return tool.handler(**kwargs)


def _wrap_split_text(text: str, chunk_size: int = 2500, overlap: int = 200) -> Dict[str, Any]:
    return {"chunks": text_splitter.split_text(text, chunk_size=chunk_size, overlap=overlap)}


def _wrap_compress_context(chunks: List[str]) -> Dict[str, Any]:
    return {"compressed_context": context_compressor.compress_chunks(chunks)}


def _wrap_generate_summary(text: str) -> Dict[str, Any]:
    return summarize_service.summarize_digest_source(text)


def _wrap_generate_keywords(text: str) -> Dict[str, Any]:
    return {"terms": keyword_service.explain_terms(text)}


def _wrap_generate_quiz(text: str) -> Dict[str, Any]:
    return {"quiz": quiz_service.generate_quiz(text)}


def _wrap_generate_mindmap(text: str) -> Dict[str, Any]:
    return {"mindmap": mindmap_service.generate_mindmap(text)}


def create_default_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(
        ToolDefinition(
            name="extract_subtitle",
            description="从视频链接中提取平台已有字幕。",
            input_schema={"video_url": "str"},
            output_schema={
                "subtitle_found": "bool",
                "transcript": "str",
                "fallback_needed": "bool",
                "source": "str",
                "error": "str | null",
            },
            handler=subtitle_tool.extract_subtitle,
            timeout=60,
            retry_count=1,
        )
    )
    registry.register(
        ToolDefinition(
            name="whisper_fallback",
            description="字幕缺失时下载音频并使用 faster-whisper 转写。",
            input_schema={"video_url": "str"},
            output_schema={
                "transcript": "str",
                "source": "str",
                "fallback_used": "bool",
                "success": "bool",
                "error": "str | null",
            },
            handler=whisper_tool.fallback_to_whisper,
            timeout=900,
            retry_count=0,
        )
    )
    registry.register(
        ToolDefinition(
            name="split_text",
            description="将长文本切分成带 overlap 的 chunks。",
            input_schema={"text": "str", "chunk_size": "int", "overlap": "int"},
            output_schema={"chunks": "list[str]"},
            handler=_wrap_split_text,
            timeout=10,
            retry_count=0,
        )
    )
    registry.register(
        ToolDefinition(
            name="compress_context",
            description="对长文本 chunk summaries 进行上下文压缩合并。",
            input_schema={"chunks": "list[str]"},
            output_schema={"compressed_context": "dict"},
            handler=_wrap_compress_context,
            timeout=60,
            retry_count=0,
        )
    )
    registry.register(
        ToolDefinition(
            name="generate_summary",
            description="生成一句话总结和核心要点。",
            input_schema={"text": "str"},
            output_schema={"one_sentence": "str", "key_points": "list[str]"},
            handler=_wrap_generate_summary,
            timeout=120,
            retry_count=1,
        )
    )
    registry.register(
        ToolDefinition(
            name="generate_keywords",
            description="生成关键词解释、项目语境和面试回答。",
            input_schema={"text": "str"},
            output_schema={"terms": "list[TermItem]"},
            handler=_wrap_generate_keywords,
            timeout=120,
            retry_count=1,
        )
    )
    registry.register(
        ToolDefinition(
            name="generate_quiz",
            description="生成复习题和答案。",
            input_schema={"text": "str"},
            output_schema={"quiz": "list[QuizItem]"},
            handler=_wrap_generate_quiz,
            timeout=120,
            retry_count=1,
        )
    )
    registry.register(
        ToolDefinition(
            name="generate_mindmap",
            description="生成 Mermaid mindmap。",
            input_schema={"text": "str"},
            output_schema={"mindmap": "str"},
            handler=_wrap_generate_mindmap,
            timeout=120,
            retry_count=1,
        )
    )
    return registry


default_registry = create_default_registry()
