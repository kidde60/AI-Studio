from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class SubtitleCue(BaseModel):
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    text: str = Field(min_length=1)


class SceneSubtitleResponse(BaseModel):
    scene_id: UUID
    cues: list[SubtitleCue]
    srt_text: str


class GenerateSubtitlesRequest(BaseModel):
    force: bool = False


class MusicSettingsRequest(BaseModel):
    volume: float = Field(default=0.15, ge=0, le=1)
    fade_in_seconds: float = Field(default=1, ge=0, le=30)
    fade_out_seconds: float = Field(default=1, ge=0, le=30)


class ProjectMusicResponse(BaseModel):
    project_id: UUID
    has_music: bool
    file_name: str | None = None
    volume: float | None = None
    fade_in_seconds: float | None = None
    fade_out_seconds: float | None = None


class RenderRequest(BaseModel):
    storyboard_id: UUID
    width: int = Field(default=1080, ge=320, le=1920)
    height: int = Field(default=1920, ge=320, le=1920)
    fps: int = Field(default=30, ge=24, le=60)


class RenderJobResponse(BaseModel):
    id: UUID
    project_id: UUID
    status: str
    output_url: str | None = None
    error_message: str | None = None
    model_config = {"from_attributes": True}
