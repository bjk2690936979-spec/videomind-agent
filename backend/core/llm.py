import json
from typing import Any

from openai import OpenAI

from backend.config import get_settings
from backend.core.exceptions import LLMJSONParseError, MissingConfigurationError


def get_llm_client() -> OpenAI:
    settings = get_settings()
    if not settings.llm_api_key:
        raise MissingConfigurationError("LLM_API_KEY is required to create an LLM client.")

    client_kwargs = {"api_key": settings.llm_api_key}
    if settings.llm_base_url:
        client_kwargs["base_url"] = settings.llm_base_url

    return OpenAI(**client_kwargs)


def _strip_json_fence(content: str) -> str:
    content = content.strip()
    if content.startswith("```"):
        lines = content.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        return "\n".join(lines).strip()
    return content


def _extract_json_content(content: str) -> str:
    # 兼容模型返回 Markdown 代码块或少量解释文字的情况。
    content = _strip_json_fence(content)
    try:
        json.loads(content)
        return content
    except json.JSONDecodeError:
        pass

    object_start = content.find("{")
    array_start = content.find("[")
    starts = [index for index in (object_start, array_start) if index != -1]
    if not starts:
        raise LLMJSONParseError("LLM response does not contain JSON content.")

    start = min(starts)
    end_char = "}" if content[start] == "{" else "]"
    end = content.rfind(end_char)
    if end == -1 or end <= start:
        raise LLMJSONParseError("LLM response contains incomplete JSON content.")

    return content[start : end + 1]


def parse_json_response(content: str) -> Any:
    try:
        return json.loads(_extract_json_content(content))
    except json.JSONDecodeError as exc:
        raise LLMJSONParseError(f"Failed to parse LLM JSON response: {exc}") from exc


def generate_json(prompt: str) -> Any:
    settings = get_settings()
    if not settings.llm_model:
        raise MissingConfigurationError("LLM_MODEL is required to generate content.")

    client = get_llm_client()
    response = client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {
                "role": "system",
                "content": "你是 VideoMind Agent，只返回合法 JSON，不要输出 Markdown 或解释文字。",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.2,
    )

    content = response.choices[0].message.content
    if not content:
        raise LLMJSONParseError("LLM response is empty.")

    return parse_json_response(content)
