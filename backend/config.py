import os
from functools import lru_cache
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel


load_dotenv()


class Settings(BaseModel):
    llm_api_key: Optional[str] = None
    llm_base_url: Optional[str] = None
    llm_model: Optional[str] = None
    storage_dir: Path = Path("backend/storage")
    whisper_model_size: str = "base"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    audio_storage_dir: Path = Path("backend/storage/audio")


@lru_cache
def get_settings() -> Settings:
    return Settings(
        llm_api_key=os.getenv("LLM_API_KEY"),
        llm_base_url=os.getenv("LLM_BASE_URL"),
        llm_model=os.getenv("LLM_MODEL"),
        storage_dir=Path(os.getenv("STORAGE_DIR", "backend/storage")),
        whisper_model_size=os.getenv("WHISPER_MODEL_SIZE", "base"),
        whisper_device=os.getenv("WHISPER_DEVICE", "cpu"),
        whisper_compute_type=os.getenv("WHISPER_COMPUTE_TYPE", "int8"),
        audio_storage_dir=Path(os.getenv("AUDIO_STORAGE_DIR", "backend/storage/audio")),
    )
