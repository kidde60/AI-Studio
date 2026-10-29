
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.ai_errors import ai_failure
from app.api.dependencies import DBSession, get_current_user
from app.models.content_generation import ContentGeneration
from app.models.content_version import ContentVersion
from app.schemas.assets import ContentUpdateRequest, ContentVersionResponse
from app.schemas.content import ContentGenerationRequest, GeneratedContentResponse
from app.services.content_service import generate_and_save_content
from sqlalchemy import func, select

router = APIRouter(prefix="/content", tags=["Content"])


@router.post("/generate", response_model=GeneratedContentResponse)
async def generate_content(
    request: ContentGenerationRequest,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    try:
        return await generate_and_save_content(db, request, current_user.id)
    except Exception as exc:
        await db.rollback()
        raise ai_failure(exc) from exc


@router.patch("/{content_id}", response_model=GeneratedContentResponse)
async def update_content(
    content_id: UUID,
    request: ContentUpdateRequest,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    content = await db.scalar(
        select(ContentGeneration).where(
            ContentGeneration.id == content_id,
            ContentGeneration.user_id == current_user.id,
        )
    )
    if not content:
        raise HTTPException(status_code=404, detail="Generated content not found.")

    snapshot = {
        "id": str(content.id),
        "topic": content.topic,
        "style": content.style,
        "platform": content.platform,
        "duration": content.duration,
        "target_audience": content.target_audience,
        "title": content.title,
        "hook": content.hook,
        "script": content.script,
        "caption": content.caption,
        "hashtags": list(content.hashtags or []),
        "cta": content.cta,
        "content_ideas": list(content.content_ideas or []),
    }
    latest = await db.scalar(
        select(func.max(ContentVersion.version_number)).where(
            ContentVersion.content_id == content.id
        )
    )
    version = ContentVersion(
        content_id=content.id,
        version_number=int(latest or 0) + 1,
        snapshot=snapshot,
    )
    db.add(version)

    changes = request.model_dump(exclude_unset=True)
    for key, value in changes.items():
        setattr(content, key, value)

    await db.commit()
    await db.refresh(content)
    return content


@router.get("/{content_id}/versions", response_model=list[ContentVersionResponse])
async def list_versions(
    content_id: UUID,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    content = await db.scalar(
        select(ContentGeneration).where(
            ContentGeneration.id == content_id,
            ContentGeneration.user_id == current_user.id,
        )
    )
    if not content:
        raise HTTPException(status_code=404, detail="Generated content not found.")
    result = await db.execute(
        select(ContentVersion)
        .where(ContentVersion.content_id == content_id)
        .order_by(ContentVersion.version_number.desc())
    )
    return list(result.scalars().all())
