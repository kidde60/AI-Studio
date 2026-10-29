from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SceneCreateRequest(BaseModel):
    scene_order: int = Field(ge=1)
    title: str = Field(min_length=1, max_length=200)
    narration: str | None = None
    visual_description: str | None = None
    duration_seconds: float = Field(default=5.0, gt=0, le=180)
    transition: str = Field(default="cut", max_length=50)
    media_asset_ids: list[dict[str, Any]] = Field(default_factory=list)


class SceneResponse(SceneCreateRequest):
    id: UUID
    storyboard_id: UUID
    model_config = {"from_attributes": True}


class StoryboardCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)


class StoryboardGenerateRequest(BaseModel):
    content_id: UUID


class StoryboardResponse(StoryboardCreateRequest):
    id: UUID
    project_id: UUID
    status: str
    scenes: list[SceneResponse] = Field(default_factory=list)
    model_config = {"from_attributes": True}


class SceneMediaSearchResponse(BaseModel):
    scene_id: UUID
    query: str
    media_type: str
    results: list[dict[str, Any]]


class SceneMediaSelectRequest(BaseModel):
    media: dict[str, Any]


class SceneMediaSelectResponse(BaseModel):
    scene: SceneResponse
