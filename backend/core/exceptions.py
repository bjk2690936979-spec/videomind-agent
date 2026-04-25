class VideoMindError(Exception):
    """Base exception for VideoMind Agent."""


class MissingConfigurationError(VideoMindError):
    """Raised when required runtime configuration is missing."""
