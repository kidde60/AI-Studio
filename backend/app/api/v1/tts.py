from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.project import Project
from app.models.scene import Scene
from app.models.scene_audio import SceneAudio
from app.models.storyboard import Storyboard
from app.models.user import User
from app.schemas.tts import SceneTTSRequest, SceneTTSResponse, SceneTTSStatusResponse
from app.services.tts.factory import get_tts_provider

router = APIRouter(prefix="/tts", tags=["tts"])
AUDIO_ROOT = Path("storage/audio")
AUDIO_ROOT.mkdir(parents=True, exist_ok=True)


async def _get_user_scene(scene_id: UUID, current_user: User, db: AsyncSession) -> Scene | None:
    result = await db.execute(
        select(Scene)
        .join(Storyboard, Scene.storyboard_id == Storyboard.id)
        .join(Project, Storyboard.project_id == Project.id)
        .where(Scene.id == scene_id, Project.user_id == current_user.id)
    )
    return result.scalar_one_or_none()


@router.post("/scenes/{scene_id}/generate", response_model=SceneTTSResponse)
async def generate_scene_audio(
    scene_id: UUID,
    request: SceneTTSRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scene = await _get_user_scene(scene_id, current_user, db)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found.")
    if not scene.narration or not scene.narration.strip():
        raise HTTPException(status_code=400, detail="This scene has no narration to synthesize.")

    existing = await db.scalar(select(SceneAudio).where(SceneAudio.scene_id == scene.id))
    if existing and not request.force_regenerate and Path(existing.file_path).exists():
        return SceneTTSResponse(
            scene_id=str(scene.id), audio_url=f"/tts/scenes/{scene.id}/audio",
            voice=existing.voice, model=existing.model, duration_seconds=existing.duration_seconds,
        )

    try:
        audio = await get_tts_provider().generate_speech(scene.narration, request.voice)
    except Exception as exc:
        message = str(exc)
        if "429" in message or "RESOURCE_EXHAUSTED" in message or "quota" in message.lower():
            import re
            match = re.search(r"retry in\s+(\d+(?:\.\d+)?)s", message, re.IGNORECASE)
            retry_after = max(1, int(float(match.group(1)))) if match else 30
            raise HTTPException(
                status_code=429,
                detail=f"Gemini voice quota is temporarily full. Please wait about {retry_after} seconds before trying again.",
                headers={"Retry-After": str(retry_after)},
            ) from exc
        raise HTTPException(status_code=502, detail=f"Voice generation failed: {exc}") from exc

    user_dir = AUDIO_ROOT / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    path = user_dir / f"{scene.id}.wav"
    path.write_bytes(audio.audio_bytes)

    existing = await db.scalar(select(SceneAudio).where(SceneAudio.scene_id == scene.id))
    if existing:
        existing.file_path = str(path)
        existing.voice = audio.voice
        existing.model = audio.model
    else:
        db.add(SceneAudio(scene_id=scene.id, file_path=str(path), voice=audio.voice, model=audio.model))
    await db.commit()

    return SceneTTSResponse(
        scene_id=str(scene.id),
        audio_url=f"/tts/scenes/{scene.id}/audio",
        voice=audio.voice,
        model=audio.model,
    )


@router.get("/scenes/{scene_id}", response_model=SceneTTSStatusResponse)
async def get_scene_audio_status(
    scene_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scene = await _get_user_scene(scene_id, current_user, db)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found.")
    audio = await db.scalar(select(SceneAudio).where(SceneAudio.scene_id == scene.id))
    if not audio:
        return SceneTTSStatusResponse(scene_id=str(scene.id), has_audio=False)
    return SceneTTSStatusResponse(
        scene_id=str(scene.id), has_audio=True, audio_url=f"/tts/scenes/{scene.id}/audio",
        voice=audio.voice, model=audio.model, duration_seconds=audio.duration_seconds,
    )


@router.get("/scenes/{scene_id}/audio")
async def get_scene_audio(
    scene_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scene = await _get_user_scene(scene_id, current_user, db)
    if scene is None:
        raise HTTPException(status_code=404, detail="Scene not found.")
    audio = await db.scalar(select(SceneAudio).where(SceneAudio.scene_id == scene.id))
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found.")
    path = Path(audio.file_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Audio file is missing.")
    return FileResponse(path, media_type="audio/wav", filename=path.name)
