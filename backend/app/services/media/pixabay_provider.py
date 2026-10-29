from typing import Any

import httpx

from .base import MediaProvider


class PixabayMediaProvider(MediaProvider):
    BASE_URL = "https://pixabay.com/api/"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, media_type: str = "video", per_page: int = 5) -> list[dict[str, Any]]:
        if not self.api_key:
            return []

        params = {
            "key": self.api_key,
            "q": query,
            "per_page": min(max(per_page, 3), 200),
        }
        endpoint = self.BASE_URL + ("videos/" if media_type == "video" else "")

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()

        if media_type == "video":
            return [
                {
                    "provider": "pixabay",
                    "id": str(item.get("id")),
                    "type": "video",
                    "url": item.get("pageURL"),
                    "thumbnail": item.get("picture_id"),
                    "duration": item.get("duration"),
                    "width": None,
                    "height": None,
                    "title": "",
                    "description": "",
                    "source": "Pixabay",
                    "files": [
                        {"quality": quality, "url": details.get("url")}
                        for quality, details in item.get("videos", {}).items()
                        if details.get("url")
                    ],
                }
                for item in data.get("hits", [])
            ]

        return [
            {
                "provider": "pixabay",
                "id": str(item.get("id")),
                "type": "image",
                "url": item.get("pageURL"),
                "thumbnail": item.get("webformatURL"),
                "width": item.get("imageWidth"),
                "height": item.get("imageHeight"),
                "title": "",
                "description": item.get("tags", ""),
                "source": "Pixabay",
            }
            for item in data.get("hits", [])
        ]
