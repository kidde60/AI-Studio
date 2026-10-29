from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_generation import ContentGeneration
from app.schemas.content import ContentGenerationRequest
from app.services.ai.factory import get_content_provider


async def generate_and_save_content(
    db: AsyncSession,
    request: ContentGenerationRequest,
    user_id,
) -> ContentGeneration:
    provider = get_content_provider()
    generated = await provider.generate_content(request)

    record = ContentGeneration(
        user_id=user_id,
        topic=request.topic,
        style=request.style,
        platform=request.platform,
        duration=request.duration,
        target_audience=request.target_audience,
        **generated,
    )

    db.add(record)
    await db.commit()
    await db.refresh(record)

    return record
