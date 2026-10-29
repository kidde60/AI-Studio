from .base import TTSProvider
from .gemini_provider import GeminiTTSProvider


def get_tts_provider() -> TTSProvider:
    return GeminiTTSProvider()
