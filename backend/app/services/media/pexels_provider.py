from typing import Any

import httpx

from .base import MediaProvider


class PexelsMediaProvider(MediaProvider):
    BASE_URL = "https://api.pexels.com"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(self, query: str, media_type: str = "video", per_page: int = 5) -> list[dict[str, Any]]:
        if not self.api_key:
            return []

        endpoint = "/videos/search" if media_type == "video" else "/v1/search"
        params = {"query": query, "per_page": min(max(per_page, 1), 80)}

        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(
                f"{self.BASE_URL}{endpoint}",
                params=params,
                headers={"Authorization": self.api_key},
            )
            response.raise_for_status()
            data = response.json()

        if media_type == "video":
            return [
                {
                    "provider": "pexels",
                    "id": str(item.get("id")),
                    "type": "video",
                    "url": item.get("url"),
                    "thumbnail": item.get("image"),
                    "duration": item.get("duration"),
                    "width": item.get("width"),
                    "height": item.get("height"),
                    "title": "",
                    "description": "",
                    "source": "Pexels",
                    "files": [
                        {
                            "quality": f.get("quality"),
                            "width": f.get("width"),
                            "height": f.get("height"),
                            "url": f.get("link"),
                        }
                        for f in item.get("video_files", [])
                        if f.get("link")
                    ],
                }
                for item in data.get("videos", [])
            ]

        return [
            {
                "provider": "pexels",
                "id": str(item.get("id")),
                "type": "image",
                "url": item.get("url"),
                "thumbnail": item.get("src", {}).get("medium"),
                "width": item.get("width"),
                "height": item.get("height"),
                "title": "",
                "description": item.get("alt", ""),
                "source": "Pexels",
            }
            for item in data.get("photos", [])
        ]
