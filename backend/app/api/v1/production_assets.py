from pathlib import Path
from uuid import UUID
import wave

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.project_music import ProjectMusic
from app.models.scene import Scene
from app.models.scene_audio import SceneAudio
from app.models.scene_subtitle import SceneSubtitle
from app.models.storyboard import Storyboard
from app.schemas.production_assets import (
    AutoProductionResponse,
    AutoProductionSceneResult,
    ProductionReadinessResponse,
    SceneUpdateRequest,
)
from app.services.media.auto_selector import auto_select_scene_media
from app.services.subtitles.service import build_cues, cues_to_srt
from app.services.tts.factory import get_tts_provider

router = APIRouter(prefix="/production-assets", tags=["production-assets"])
AUDIO_ROOT = Path("storage/audio")


async def _scene_for_user(db: AsyncSession, user_id: UUID, scene_id: UUID) -> Scene | None:
    result = await db.execute(
        select(Scene)
        .join(Storyboard, Scene.storyboard_id == Storyboard.id)
        .join(Project, Storyboard.project_id == Project.id)
        .where(Scene.id == scene_id, Project.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def _storyboard_for_user(db: AsyncSession, user_id: UUID, storyboard_id: UUID):
    result = await db.execute(
        select(Storyboard, Project.platform)
        .join(Project, Project.id == Storyboard.project_id)
        .where(Storyboard.id == storyboard_id, Project.user_id == user_id)
    )
    return result.first()


@router.patch("/scenes/{scene_id}")
async def update_scene(
    scene_id: UUID,
    request: SceneUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    scene = await _scene_for_user(db, current_user.id, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")

    data = request.model_dump(exclude_unset=True)
    narration_changed = "narration" in data and data["narration"] != scene.narration
    duration_changed = "duration_seconds" in data and float(data["duration_seconds"]) != float(scene.duration_seconds)

    for key, value in data.items():
        setattr(scene, key, value)

    # Subtitle timing depends on both narration and scene duration. Invalidate
    # it so the next production pass/render creates timing for the edited scene.
    if narration_changed or duration_changed:
        subtitle = await db.scalar(select(SceneSubtitle).where(SceneSubtitle.scene_id == scene.id))
        if subtitle:
            await db.delete(subtitle)

    # A narration edit makes the existing voice-over invalid. Duration edits do
    # not invalidate audio because the renderer trims/pads audio to the scene.
    if narration_changed:
        audio = await db.scalar(select(SceneAudio).where(SceneAudio.scene_id == scene.id))
        if audio:
            Path(audio.file_path).unlink(missing_ok=True)
            await db.delete(audio)

    await db.commit()
    await db.refresh(scene)
    return scene


async def _ensure_subtitles(db: AsyncSession, scene: Scene) -> bool:
    if not scene.narration or not scene.narration.strip():
        return False
    cues = build_cues(scene.narration, float(scene.duration_seconds or 1))
    srt = cues_to_srt(cues)
    existing = await db.scalar(select(SceneSubtitle).where(SceneSubtitle.scene_id == scene.id))
    if existing:
        existing.cues = cues
        existing.srt_text = srt
    else:
        db.add(SceneSubtitle(scene_id=scene.id, cues=cues, srt_text=srt))
    return True


@router.post("/{storyboard_id}/auto", response_model=AutoProductionResponse)
async def auto_production_assets(
    storyboard_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = await _storyboard_for_user(db, current_user.id, storyboard_id)
    if not row:
        raise HTTPException(status_code=404, detail="Storyboard not found.")
    storyboard, platform = row

    result = await db.execute(
        select(Scene).where(Scene.storyboard_id == storyboard.id).order_by(Scene.scene_order)
    )
    scenes = list(result.scalars().all())
    used_keys: set[str] = set()
    for scene in scenes:
        for media in scene.media_asset_ids or []:
            if media.get("provider") and media.get("id"):
                used_keys.add(f"{media.get('provider')}:{media.get('id')}")

    output: list[AutoProductionSceneResult] = []
    for scene in scenes:
        item = AutoProductionSceneResult(scene_id=scene.id, scene_order=scene.scene_order)
        try:
            current_media = (scene.media_asset_ids or [None])[0]
            if current_media and (
                current_media.get("manual_selection")
                or current_media.get("selection_source") in {"user_selected", "stock_manual"}
            ):
                item.skipped_media = True
                item.media = current_media
            else:
                media = await auto_select_scene_media(scene, platform, used_keys)
                if media:
                    scene.media_asset_ids = [media]
                    if media.get("provider") and media.get("id"):
                        used_keys.add(f"{media.get('provider')}:{media.get('id')}")
                    item.media_attached = True
                    item.media = media
                elif current_media:
                    item.skipped_media = True
                    item.media = current_media

            audio = await db.scalar(select(SceneAudio).where(SceneAudio.scene_id == scene.id))
            if scene.narration and scene.narration.strip() and audio and Path(audio.file_path).exists():
                item.skipped_voice = True
                item.voice = {
                    "voice": audio.voice,
                    "model": audio.model,
                    "duration_seconds": audio.duration_seconds,
                }
            elif scene.narration and scene.narration.strip():
                generated = await get_tts_provider().generate_speech(scene.narration, "Kore")
                user_dir = AUDIO_ROOT / str(current_user.id)
                user_dir.mkdir(parents=True, exist_ok=True)
                path = user_dir / f"{scene.id}.wav"
                path.write_bytes(generated.audio_bytes)
                with wave.open(str(path), "rb") as wav:
                    duration = wav.getnframes() / float(wav.getframerate() or 1)
                if audio:
                    audio.file_path = str(path)
                    audio.voice = generated.voice
                    audio.model = generated.model
                    audio.duration_seconds = duration
                else:
                    db.add(
                        SceneAudio(
                            scene_id=scene.id,
                            file_path=str(path),
                            voice=generated.voice,
                            model=generated.model,
                            duration_seconds=duration,
                        )
                    )
                item.voice_attached = True
                item.voice = {
                    "voice": generated.voice,
                    "model": generated.model,
                    "duration_seconds": duration,
                }

            if await _ensure_subtitles(db, scene):
                item.subtitles_attached = True
            else:
                item.skipped_subtitles = True

        except Exception as exc:
            item.error = str(exc)
        output.append(item)
        await db.commit()

    return AutoProductionResponse(storyboard_id=storyboard.id, scenes=output)


@router.get("/{storyboard_id}/readiness", response_model=ProductionReadinessResponse)
async def production_readiness(
    storyboard_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    row = await _storyboard_for_user(db, current_user.id, storyboard_id)
    if not row:
        raise HTTPException(status_code=404, detail="Storyboard not found.")
    storyboard, _ = row
    result = await db.execute(
        select(Scene)
        .where(Scene.storyboard_id == storyboard.id)
        .options(selectinload(Scene.audio), selectinload(Scene.subtitles))
        .order_by(Scene.scene_order)
    )
    scenes = list(result.scalars().all())
    music = await db.scalar(select(ProjectMusic).where(ProjectMusic.project_id == storyboard.project_id))

    missing = []
    media_ready = voice_ready = subtitles_ready = ready = 0
    for scene in scenes:
        has_media = bool(scene.media_asset_ids)
        has_voice = bool(scene.audio and Path(scene.audio.file_path).exists()) if scene.narration else True
        has_subtitles = bool(scene.subtitles) if scene.narration else True
        media_ready += int(has_media)
        voice_ready += int(has_voice)
        subtitles_ready += int(has_subtitles)
        if has_media and has_voice and has_subtitles:
            ready += 1
        else:
            missing.append({
                "scene_id": str(scene.id),
                "scene_order": scene.scene_order,
                "media": has_media,
                "voice": has_voice,
                "subtitles": has_subtitles,
            })

    return ProductionReadinessResponse(
        storyboard_id=storyboard.id,
        total_scenes=len(scenes),
        media_ready=media_ready,
        voice_ready=voice_ready,
        subtitles_ready=subtitles_ready,
        ready_scenes=ready,
        missing_scenes=missing,
        music_attached=bool(music),
    )
