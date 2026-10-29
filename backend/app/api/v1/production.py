from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.api.dependencies import DBSession, get_current_user
from app.db.session import AsyncSessionLocal
from app.models.project import Project
from app.models.project_music import ProjectMusic
from app.models.render_job import RenderJob
from app.models.scene import Scene
from app.models.scene_subtitle import SceneSubtitle
from app.models.storyboard import Storyboard
from app.models.user import User
from app.schemas.production import (
    GenerateSubtitlesRequest,
    MusicSettingsRequest,
    ProjectMusicResponse,
    RenderJobResponse,
    RenderRequest,
    SceneSubtitleResponse,
)
from app.services.render.service import run_render_job
from app.services.subtitles.service import build_cues, cues_to_srt

router = APIRouter(prefix="/production", tags=["Production"])
MUSIC_ROOT = Path("storage/music")


async def _user_project(db: DBSession, user_id: UUID, project_id: UUID) -> Project | None:
    return await db.scalar(select(Project).where(Project.id == project_id, Project.user_id == user_id))


async def _user_scene(db: DBSession, user_id: UUID, scene_id: UUID) -> Scene | None:
    result = await db.execute(
        select(Scene).join(Storyboard, Storyboard.id == Scene.storyboard_id)
        .join(Project, Project.id == Storyboard.project_id)
        .where(Scene.id == scene_id, Project.user_id == user_id)
    )
    return result.scalar_one_or_none()


@router.post("/scenes/{scene_id}/subtitles", response_model=SceneSubtitleResponse)
async def generate_scene_subtitles(scene_id: UUID, request: GenerateSubtitlesRequest, db: DBSession, current_user: User = Depends(get_current_user)):
    scene = await _user_scene(db, current_user.id, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")
    if not scene.narration or not scene.narration.strip():
        raise HTTPException(status_code=400, detail="This scene has no narration for subtitles.")
    existing = await db.scalar(select(SceneSubtitle).where(SceneSubtitle.scene_id == scene.id))
    if existing and not request.force:
        return SceneSubtitleResponse(scene_id=scene.id, cues=existing.cues, srt_text=existing.srt_text)
    cues = build_cues(scene.narration, float(scene.duration_seconds or 1))
    srt = cues_to_srt(cues)
    if existing:
        existing.cues = cues
        existing.srt_text = srt
    else:
        db.add(SceneSubtitle(scene_id=scene.id, cues=cues, srt_text=srt))
    await db.commit()
    return SceneSubtitleResponse(scene_id=scene.id, cues=cues, srt_text=srt)


@router.get("/scenes/{scene_id}/subtitles", response_model=SceneSubtitleResponse)
async def get_scene_subtitles(scene_id: UUID, db: DBSession, current_user: User = Depends(get_current_user)):
    scene = await _user_scene(db, current_user.id, scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found.")
    subtitle = await db.scalar(select(SceneSubtitle).where(SceneSubtitle.scene_id == scene.id))
    if not subtitle:
        raise HTTPException(status_code=404, detail="Subtitles have not been generated.")
    return SceneSubtitleResponse(scene_id=scene.id, cues=subtitle.cues, srt_text=subtitle.srt_text)


@router.get("/scenes/{scene_id}/subtitles.srt")
async def download_scene_srt(scene_id: UUID, db: DBSession, current_user: User = Depends(get_current_user)):
    data = await get_scene_subtitles(scene_id, db, current_user)
    return Response(content=data.srt_text, media_type="application/x-subrip", headers={"Content-Disposition": f'attachment; filename="scene-{scene_id}.srt"'})


@router.post("/projects/{project_id}/music", response_model=ProjectMusicResponse)
async def upload_project_music(project_id: UUID, db: DBSession, file: UploadFile = File(...), current_user: User = Depends(get_current_user)):
    project = await _user_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    allowed = {"audio/mpeg", "audio/wav", "audio/x-wav", "audio/mp4", "audio/aac", "audio/ogg", "audio/webm"}
    if file.content_type and file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Unsupported music format. Use MP3, WAV, AAC, OGG or WebM audio.")
    MUSIC_ROOT.mkdir(parents=True, exist_ok=True)
    suffix = Path(file.filename or "music.mp3").suffix.lower() or ".mp3"
    path = MUSIC_ROOT / str(current_user.id) / f"{project.id}{suffix}"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(await file.read())
    existing = await db.scalar(select(ProjectMusic).where(ProjectMusic.project_id == project.id))
    if existing:
        existing.file_path = str(path)
        existing.file_name = file.filename or path.name
    else:
        db.add(ProjectMusic(project_id=project.id, file_path=str(path), file_name=file.filename or path.name))
    await db.commit()
    music = await db.scalar(select(ProjectMusic).where(ProjectMusic.project_id == project.id))
    return ProjectMusicResponse(project_id=project.id, has_music=True, file_name=music.file_name, volume=music.volume, fade_in_seconds=music.fade_in_seconds, fade_out_seconds=music.fade_out_seconds)


@router.get("/projects/{project_id}/music", response_model=ProjectMusicResponse)
async def get_project_music(project_id: UUID, db: DBSession, current_user: User = Depends(get_current_user)):
    project = await _user_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    music = await db.scalar(select(ProjectMusic).where(ProjectMusic.project_id == project.id))
    if not music:
        return ProjectMusicResponse(project_id=project.id, has_music=False)
    return ProjectMusicResponse(project_id=project.id, has_music=True, file_name=music.file_name, volume=music.volume, fade_in_seconds=music.fade_in_seconds, fade_out_seconds=music.fade_out_seconds)


@router.patch("/projects/{project_id}/music", response_model=ProjectMusicResponse)
async def update_project_music(project_id: UUID, request: MusicSettingsRequest, db: DBSession, current_user: User = Depends(get_current_user)):
    project = await _user_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    music = await db.scalar(select(ProjectMusic).where(ProjectMusic.project_id == project.id))
    if not music:
        raise HTTPException(status_code=404, detail="Project music has not been uploaded.")
    music.volume = request.volume
    music.fade_in_seconds = request.fade_in_seconds
    music.fade_out_seconds = request.fade_out_seconds
    await db.commit()
    return ProjectMusicResponse(project_id=project.id, has_music=True, file_name=music.file_name, volume=music.volume, fade_in_seconds=music.fade_in_seconds, fade_out_seconds=music.fade_out_seconds)


@router.post("/projects/{project_id}/render", response_model=RenderJobResponse, status_code=202)
async def create_render(project_id: UUID, request: RenderRequest, background_tasks: BackgroundTasks, db: DBSession, current_user: User = Depends(get_current_user)):
    project = await _user_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    storyboard = await db.scalar(select(Storyboard).where(Storyboard.id == request.storyboard_id, Storyboard.project_id == project.id))
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found for this project.")
    scenes = (await db.execute(select(Scene).where(Scene.storyboard_id == storyboard.id).options(selectinload(Scene.audio), selectinload(Scene.subtitles)))).scalars().all()
    if not scenes:
        raise HTTPException(status_code=400, detail="The storyboard has no scenes.")
    missing = [str(s.scene_order) for s in scenes if not s.media_asset_ids]
    if missing:
        raise HTTPException(status_code=400, detail=f"Select media for scene(s): {', '.join(missing)} before rendering.")
    job = RenderJob(project_id=project.id, status="queued")
    db.add(job)
    await db.commit()
    await db.refresh(job)
    background_tasks.add_task(run_render_job, job.id, storyboard.id, request.width, request.height, request.fps)
    return RenderJobResponse(id=job.id, project_id=job.project_id, status=job.status)


@router.get("/render/{job_id}", response_model=RenderJobResponse)
async def get_render_job(job_id: UUID, db: DBSession, current_user: User = Depends(get_current_user)):
    result = await db.execute(select(RenderJob).join(Project, Project.id == RenderJob.project_id).where(RenderJob.id == job_id, Project.user_id == current_user.id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Render job not found.")
    return RenderJobResponse(id=job.id, project_id=job.project_id, status=job.status, output_url=f"/production/render/{job.id}/video" if job.status == "completed" else None, error_message=job.error_message)


@router.get("/render/{job_id}/video")
async def get_render_video(job_id: UUID, db: DBSession, current_user: User = Depends(get_current_user)):
    result = await db.execute(select(RenderJob).join(Project, Project.id == RenderJob.project_id).where(RenderJob.id == job_id, Project.user_id == current_user.id))
    job = result.scalar_one_or_none()
    if not job or job.status != "completed" or not job.output_path:
        raise HTTPException(status_code=404, detail="Rendered video is not available.")
    path = Path(job.output_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Rendered video file is missing.")
    return FileResponse(path, media_type="video/mp4", filename=f"ai-video-{job.id}.mp4")
