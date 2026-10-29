from pydantic import BaseModel, Field


class SceneTTSRequest(BaseModel):
    voice: str = Field(default="Kore", min_length=1, max_length=100)
    force_regenerate: bool = False


class SceneTTSResponse(BaseModel):
    scene_id: str
    audio_url: str
    voice: str
    model: str
    duration_seconds: float | None = None


class SceneTTSStatusResponse(BaseModel):
    scene_id: str
    has_audio: bool
    audio_url: str | None = None
    voice: str | None = None
    model: str | None = None
    duration_seconds: float | None = None
