class VideoMindError(Exception):
    """Base exception for VideoMind Agent."""


class MissingConfigurationError(VideoMindError):
    """Raised when required runtime configuration is missing."""


class LLMJSONParseError(VideoMindError):
    """Raised when the LLM response cannot be parsed as JSON."""
