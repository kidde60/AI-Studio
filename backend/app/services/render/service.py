import asyncio
import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.db.session import AsyncSessionLocal
from app.models.project_music import ProjectMusic
from app.models.render_job import RenderJob
from app.models.scene_audio import SceneAudio
from app.models.scene_subtitle import SceneSubtitle
from app.models.scene import Scene
from app.models.storyboard import Storyboard
from app.services.subtitles.service import build_cues, cues_to_srt, srt_timestamp
from sqlalchemy import select
from sqlalchemy.orm import selectinload

settings = get_settings()
RENDER_ROOT = Path("storage/renders")
ASSET_ROOT = Path("storage/render_assets")


def _ffmpeg() -> str:
    candidates = [shutil.which("ffmpeg")]
    # Homebrew's regular ffmpeg formula omits libass, while ffmpeg-full
    # includes the ASS subtitle filter used by the renderer.
    candidates.extend(
        str(path)
        for path in (
            Path("/opt/homebrew/opt/ffmpeg-full/bin/ffmpeg"),
            Path("/usr/local/opt/ffmpeg-full/bin/ffmpeg"),
        )
        if path.exists()
    )

    for candidate in dict.fromkeys(path for path in candidates if path):
        filters = subprocess.run(
            [candidate, "-hide_banner", "-filters"],
            capture_output=True,
            text=True,
            check=False,
        )
        if re.search(r"^\s*\S*\s+ass\s", filters.stdout, re.MULTILINE):
            return candidate

    if candidates:
        raise RuntimeError(
            "FFmpeg is installed, but it does not include the ASS subtitle filter. "
            "Install/use a libass-enabled build (on Homebrew: brew install ffmpeg-full), "
            "then restart the backend."
        )
    raise RuntimeError("FFmpeg is not installed or is not available on the backend PATH.")


def _ass_filter(ass_path: Path) -> str:
    filename = str(ass_path.resolve()).replace("\\", "/")
    filename = filename.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")
    return f"ass=filename='{filename}'"


async def _download(url: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient(timeout=90, follow_redirects=True) as client:
        response = await client.get(url)
        response.raise_for_status()
        path.write_bytes(response.content)


def _media_url(media: dict) -> tuple[str | None, str]:
    # User-uploaded assets are stored locally and include their server-side
    # file path. Prefer it over the browser-facing /assets/... URL so render
    # jobs can copy the file from disk.
    if media.get("file_path"):
        return media["file_path"], media.get("type", "video")

    files = media.get("files") or []
    if files:
        usable = [f for f in files if f.get("url")]
        if usable:
            usable.sort(key=lambda f: (f.get("width") or 0), reverse=True)
            return usable[0]["url"], "video"
    return media.get("thumbnail") or media.get("url"), media.get("type", "video")


def _write_ass(cues: list[dict], path: Path, width: int, height: int) -> None:
    def ass_time(seconds: float) -> str:
        cs = int(round(seconds * 100))
        h, cs = divmod(cs, 360000)
        m, cs = divmod(cs, 6000)
        s, cs = divmod(cs, 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    lines = [
        "[Script Info]", "ScriptType: v4.00+", f"PlayResX: {width}", f"PlayResY: {height}", "",
        "[V4+ Styles]", "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding",
        "Style: Default,Arial,54,&H00FFFFFF,&H00FFFFFF,&H00101010,&H80000000,1,0,0,0,100,100,0,0,1,3,1,2,60,60,110,1", "",
        "[Events]", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text",
    ]
    for cue in cues:
        text = str(cue["text"]).replace("{", "\\{").replace("}", "\\}").replace("\n", "\\N")
        lines.append(f"Dialogue: 0,{ass_time(cue['start'])},{ass_time(cue['end'])},Default,,0,0,0,,{text}")
    path.write_text("\n".join(lines), encoding="utf-8")


def _run(command: list[str]) -> None:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr[-4000:] or "FFmpeg rendering failed.")


def _scene_duration(scene: Scene, audio: SceneAudio | None) -> float:
    # The scene duration is user-controlled. Audio is trimmed or padded to fit
    # it during rendering rather than extending a scene beyond the user's edit.
    return max(0.5, float(scene.duration_seconds or 1))


def render_project_sync(storyboard: Storyboard, scenes: list[Scene], music: ProjectMusic | None, width: int, height: int, fps: int, job_id: UUID) -> Path:
    ffmpeg = _ffmpeg()
    job_dir = ASSET_ROOT / str(job_id)
    job_dir.mkdir(parents=True, exist_ok=True)
    scene_outputs: list[Path] = []

    for index, scene in enumerate(scenes, start=1):
        duration = _scene_duration(scene, scene.audio)
        media = (scene.media_asset_ids or [None])[0]
        media_url, media_type = _media_url(media or {})
        if not media_url:
            raise RuntimeError(f"Scene {index} has no selected media. Attach stock media before rendering.")
        ext = ".jpg" if media_type == "image" else ".mp4"
        media_path = job_dir / f"scene_{index}_media{ext}"
        if media_url.startswith("http://") or media_url.startswith("https://"):
            asyncio.run(_download(media_url, media_path))
        else:
            source = Path(media_url)
            if not source.exists():
                raise RuntimeError(f"Media file for scene {index} could not be found.")
            shutil.copy2(source, media_path)

        subtitle = scene.subtitles
        cues = subtitle.cues if subtitle else build_cues(scene.narration or "", duration)
        ass_path = job_dir / f"scene_{index}.ass"
        _write_ass(cues, ass_path, width, height)
        out = job_dir / f"scene_{index}.mp4"
        command = [ffmpeg, "-y"]
        if media_type == "image":
            command += ["-loop", "1", "-i", str(media_path)]
        else:
            command += ["-stream_loop", "-1", "-i", str(media_path)]
        has_audio = bool(scene.audio and Path(scene.audio.file_path).exists())
        if has_audio:
            command += ["-i", scene.audio.file_path, "-af", "apad"]
        else:
            command += ["-f", "lavfi", "-i", "anullsrc=channel_layout=mono:sample_rate=24000"]
        command += [
            "-t", f"{duration:.3f}",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,setsar=1,{_ass_filter(ass_path)}",
            "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast", "-pix_fmt", "yuv420p",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", str(out),
        ]
        _run(command)
        scene_outputs.append(out)

    concat = job_dir / "concat.txt"
    concat.write_text("\n".join(f"file '{p.resolve().as_posix().replace("'", "'\\''")}'" for p in scene_outputs), encoding="utf-8")
    base = RENDER_ROOT / str(job_id)
    base.parent.mkdir(parents=True, exist_ok=True)
    base.parent.mkdir(parents=True, exist_ok=True)
    assembled = job_dir / "assembled.mp4"
    _run([ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat), "-c", "copy", str(assembled)])

    final = base.with_suffix(".mp4")
    if music and Path(music.file_path).exists():
        duration = sum(_scene_duration(s, s.audio) for s in scenes)
        music_fade_out = min(float(music.fade_out_seconds or 0), max(0, duration - 0.1))
        music_fade_in = min(float(music.fade_in_seconds or 0), max(0, duration - 0.1))
        af = [f"volume={max(0, min(1, music.volume))}"]
        if music_fade_in > 0: af.append(f"afade=t=in:st=0:d={music_fade_in}")
        if music_fade_out > 0: af.append(f"afade=t=out:st={max(0, duration-music_fade_out)}:d={music_fade_out}")
        filter_music = ",".join(af)
        _run([ffmpeg, "-y", "-i", str(assembled), "-stream_loop", "-1", "-i", music.file_path, "-filter_complex", f"[1:a]{filter_music}[m];[0:a][m]amix=inputs=2:duration=first:dropout_transition=2[a]", "-map", "0:v:0", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)])
    else:
        shutil.copy2(assembled, final)
    return final


async def run_render_job(job_id: UUID, storyboard_id: UUID, width: int, height: int, fps: int) -> None:
    async with AsyncSessionLocal() as db:
        job = await db.get(RenderJob, job_id)
        storyboard = await db.scalar(select(Storyboard).where(Storyboard.id == storyboard_id))
        if not job or not storyboard:
            return
        result = await db.execute(select(Scene).where(Scene.storyboard_id == storyboard_id).order_by(Scene.scene_order).options(selectinload(Scene.audio), selectinload(Scene.subtitles)))
        scenes = list(result.scalars().all())
        music = await db.scalar(select(ProjectMusic).where(ProjectMusic.project_id == storyboard.project_id))
        job.status = "rendering"
        await db.commit()
        try:
            output = await asyncio.to_thread(render_project_sync, storyboard, scenes, music, width, height, fps, job_id)
            job.status = "completed"
            job.output_path = str(output)
            job.error_message = None
        except Exception as exc:
            job.status = "failed"
            job.error_message = str(exc)
        await db.commit()
