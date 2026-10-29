from abc import ABC, abstractmethod
from typing import Any


class MediaProvider(ABC):
    @abstractmethod
    async def search(self, query: str, media_type: str = "video", per_page: int = 5) -> list[dict[str, Any]]:
        """Search stock media and return normalized results."""
        raise NotImplementedError
