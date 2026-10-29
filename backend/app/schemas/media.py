from typing import Any, Literal

from pydantic import BaseModel, Field


class MediaSearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=200)
    media_type: Literal["video", "image"] = "video"
    per_page: int = Field(default=6, ge=1, le=20)


class MediaSearchResponse(BaseModel):
    query: str
    media_type: str
    results: list[dict[str, Any]]
