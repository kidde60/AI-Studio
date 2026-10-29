from app.core.config import get_settings
from app.services.ai.base import AIContentProvider, AIStoryboardProvider
from app.services.ai.mock_provider import MockContentProvider
from app.services.ai.mock_storyboard_provider import MockStoryboardProvider
from app.services.ai.ollama_provider import OllamaProvider


def get_content_provider() -> AIContentProvider:
    provider = get_settings().ai_provider.strip().lower()

    if provider == "ollama":
        return OllamaProvider()

    if provider == "gemini":
        from app.services.ai.gemini_provider import GeminiContentProvider
        return GeminiContentProvider()

    if provider == "openai":
        from app.services.ai.openai_provider import OpenAIContentProvider
        return OpenAIContentProvider()

    if provider == "mock":
        return MockContentProvider()

    raise ValueError(f"Unsupported AI_PROVIDER: {provider}")


def get_storyboard_provider() -> AIStoryboardProvider:
    provider = get_settings().ai_provider.strip().lower()

    if provider == "ollama":
        return OllamaProvider()

    if provider == "gemini":
        from app.services.ai.gemini_provider import GeminiContentProvider
        return GeminiContentProvider()

    if provider in {"openai", "mock"}:
        # OpenAI storyboard generation can be added later without changing routes/services.
        return MockStoryboardProvider()

    raise ValueError(f"Unsupported AI_PROVIDER: {provider}")
