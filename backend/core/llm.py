from openai import OpenAI

from backend.config import get_settings
from backend.core.exceptions import MissingConfigurationError


def get_llm_client() -> OpenAI:
    settings = get_settings()
    if not settings.llm_api_key:
        raise MissingConfigurationError("LLM_API_KEY is required to create an LLM client.")

    client_kwargs = {"api_key": settings.llm_api_key}
    if settings.llm_base_url:
        client_kwargs["base_url"] = settings.llm_base_url

    return OpenAI(**client_kwargs)
