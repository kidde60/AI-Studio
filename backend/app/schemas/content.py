from uuid import UUID
from pydantic import BaseModel, Field


class ContentGenerationRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=500)
    style: str = Field(min_length=2, max_length=50)
    platform: str = Field(min_length=2, max_length=50)
    duration: int = Field(ge=15, le=180)
    target_audience: str = Field(min_length=2, max_length=300)


class GeneratedContentResponse(ContentGenerationRequest):
    id: UUID
    title: str
    hook: str
    script: str
    caption: str
    hashtags: list[str]
    cta: str
    content_ideas: list[str]

    model_config = {"from_attributes": True}

