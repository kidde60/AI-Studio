
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.content_generation import ContentGeneration
from app.models.project import Project
from app.models.scene import Scene
from app.models.storyboard import Storyboard
from app.schemas.storyboard import SceneCreateRequest, StoryboardCreateRequest
from app.services.ai.factory import get_storyboard_provider


async def get_user_project(db: AsyncSession, user_id: UUID, project_id: UUID) -> Project | None:
    result = await db.execute(
        select(Project).where(Project.id == project_id, Project.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_content(db: AsyncSession, user_id: UUID, content_id: UUID) -> ContentGeneration | None:
    result = await db.execute(
        select(ContentGeneration).where(
            ContentGeneration.id == content_id,
            ContentGeneration.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def create_storyboard(db: AsyncSession, project: Project, request: StoryboardCreateRequest) -> Storyboard:
    storyboard = Storyboard(project_id=project.id, **request.model_dump())
    db.add(storyboard)
    await db.commit()
    return await get_storyboard(db, project.user_id, storyboard.id)


async def generate_storyboard_from_content(db: AsyncSession, project: Project, content: ContentGeneration) -> Storyboard:
    provider = get_storyboard_provider()
    generated = await provider.generate_storyboard({
        "topic": content.topic,
        "title": content.title,
        "hook": content.hook,
        "script": content.script,
        "cta": content.cta,
        "style": content.style,
        "platform": content.platform,
        "duration": content.duration,
        "target_audience": content.target_audience,
    })

    storyboard = Storyboard(
        project_id=project.id,
        title=generated["title"][:200],
        description=generated.get("description"),
        status="generated",
    )
    db.add(storyboard)
    await db.flush()

    for item in generated["scenes"]:
        db.add(Scene(
            storyboard_id=storyboard.id,
            scene_order=item["scene_order"],
            title=item["title"][:200],
            narration=item.get("narration"),
            visual_description=item.get("visual_description"),
            duration_seconds=item.get("duration_seconds", 5.0),
            transition=item.get("transition", "cut")[:50],
            media_asset_ids=[],
        ))

    await db.commit()
    return await get_storyboard(db, project.user_id, storyboard.id)


async def get_storyboard(db: AsyncSession, user_id: UUID, storyboard_id: UUID) -> Storyboard | None:
    result = await db.execute(
        select(Storyboard)
        .join(Project, Project.id == Storyboard.project_id)
        .where(Storyboard.id == storyboard_id, Project.user_id == user_id)
        .options(selectinload(Storyboard.scenes))
    )
    return result.scalar_one_or_none()


async def list_storyboards(db: AsyncSession, user_id: UUID, project_id: UUID) -> list[Storyboard]:
    result = await db.execute(
        select(Storyboard)
        .join(Project, Project.id == Storyboard.project_id)
        .where(Storyboard.project_id == project_id, Project.user_id == user_id)
        .options(selectinload(Storyboard.scenes))
        .order_by(Storyboard.created_at.desc())
    )
    return list(result.scalars().unique().all())


async def add_scene(db: AsyncSession, storyboard: Storyboard, request: SceneCreateRequest) -> Scene:
    scene = Scene(storyboard_id=storyboard.id, **request.model_dump())
    db.add(scene)
    await db.commit()
    await db.refresh(scene)
    return scene


async def get_scene(db: AsyncSession, user_id: UUID, scene_id: UUID) -> Scene | None:
    result = await db.execute(
        select(Scene)
        .join(Storyboard, Storyboard.id == Scene.storyboard_id)
        .join(Project, Project.id == Storyboard.project_id)
        .where(Scene.id == scene_id, Project.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def attach_scene_media(db: AsyncSession, scene: Scene, media: dict) -> Scene:
    scene.media_asset_ids = [media]
    await db.commit()
    await db.refresh(scene)
    return scene


async def attach_user_asset(db: AsyncSession, scene: Scene, media: dict) -> Scene:
    scene.media_asset_ids = [media]
    await db.commit()
    await db.refresh(scene)
    return scene
