from abc import ABC, abstractmethod

from app.schemas.content import ContentGenerationRequest


class AIContentProvider(ABC):
    @abstractmethod
    async def generate_content(self, request: ContentGenerationRequest) -> dict:
        raise NotImplementedError


class AIStoryboardProvider(ABC):
    @abstractmethod
    async def generate_storyboard(self, content: dict) -> dict:
        """Generate a storyboard from previously generated short-form content."""
        raise NotImplementedError
