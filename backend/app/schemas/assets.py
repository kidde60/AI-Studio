
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class UserAssetResponse(BaseModel):
    id: UUID
    project_id: UUID | None
    file_name: str
    asset_type: str
    mime_type: str
    size_bytes: int
    file_url: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ContentUpdateRequest(BaseModel):
    title: str | None = None
    hook: str | None = None
    script: str | None = None
    caption: str | None = None
    hashtags: list[str] | None = None
    cta: str | None = None
    content_ideas: list[str] | None = None


class ContentVersionResponse(BaseModel):
    id: UUID
    content_id: UUID
    version_number: int
    snapshot: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class UserAssetSceneSelectRequest(BaseModel):
    asset_id: UUID
