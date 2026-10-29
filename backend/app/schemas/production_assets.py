from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SceneUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    narration: str | None = None
    visual_description: str | None = None
    duration_seconds: float | None = Field(default=None, gt=0, le=180)
    transition: str | None = Field(default=None, max_length=50)


class AutoProductionSceneResult(BaseModel):
    scene_id: UUID
    scene_order: int
    media_attached: bool = False
    voice_attached: bool = False
    subtitles_attached: bool = False
    media: dict[str, Any] | None = None
    voice: dict[str, Any] | None = None
    skipped_media: bool = False
    skipped_voice: bool = False
    skipped_subtitles: bool = False
    error: str | None = None


class AutoProductionResponse(BaseModel):
    storyboard_id: UUID
    scenes: list[AutoProductionSceneResult]


class ProductionReadinessResponse(BaseModel):
    storyboard_id: UUID
    total_scenes: int
    media_ready: int
    voice_ready: int
    subtitles_ready: int
    ready_scenes: int
    missing_scenes: list[dict[str, Any]]
    music_attached: bool
