from uuid import UUID

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    platform: str = Field(default="TikTok", max_length=50)
    duration: int = Field(default=45, ge=15, le=180)


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    platform: str | None = Field(default=None, max_length=50)
    duration: int | None = Field(default=None, ge=15, le=180)
    status: str | None = Field(default=None, max_length=30)


class ProjectResponse(ProjectCreateRequest):
    id: UUID
    user_id: UUID
    status: str

    model_config = {"from_attributes": True}
