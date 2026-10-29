
import mimetypes
import re
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import select

from app.api.dependencies import DBSession, get_current_user
from app.core.security import decode_access_token
from app.services.auth_service import get_user_by_id
from app.models.project import Project
from app.models.user_asset import UserAsset
from app.schemas.assets import UserAssetResponse

router = APIRouter(prefix="/assets", tags=["Assets"])

ASSET_ROOT = Path("storage/user_assets")
ALLOWED_TYPES = {"image", "video", "audio"}
MAX_SIZE = 500 * 1024 * 1024


def _asset_type(content_type: str | None, filename: str) -> str:
    value = (content_type or mimetypes.guess_type(filename)[0] or "").lower()
    if value.startswith("image/"):
        return "image"
    if value.startswith("video/"):
        return "video"
    if value.startswith("audio/"):
        return "audio"
    raise HTTPException(status_code=400, detail="Only image, video and audio files are supported.")


def _safe_name(filename: str) -> str:
    name = Path(filename or "upload").name
    return re.sub(r"[^A-Za-z0-9._-]+", "_", name)[:180] or "upload"


def _response(asset: UserAsset) -> UserAssetResponse:
    return UserAssetResponse(
        id=asset.id,
        project_id=asset.project_id,
        file_name=asset.file_name,
        asset_type=asset.asset_type,
        mime_type=asset.mime_type,
        size_bytes=asset.size_bytes,
        file_url=f"/assets/{asset.id}/file",
        created_at=asset.created_at,
    )


@router.post("/upload", response_model=UserAssetResponse, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    db: DBSession,
    file: UploadFile = File(...),
    project_id: UUID | None = Query(default=None),
    current_user=Depends(get_current_user),
):
    asset_type = _asset_type(file.content_type, file.filename or "")
    if project_id:
        project = await db.scalar(
            select(Project).where(Project.id == project_id, Project.user_id == current_user.id)
        )
        if not project:
            raise HTTPException(status_code=404, detail="Project not found.")

    safe_name = _safe_name(file.filename or "upload")
    directory = ASSET_ROOT / str(current_user.id)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{UUID(int=__import__('uuid').uuid4().int)}_{safe_name}"

    size = 0
    try:
        with path.open("wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > MAX_SIZE:
                    raise HTTPException(status_code=413, detail="File is larger than the 500 MB upload limit.")
                output.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    finally:
        await file.close()

    asset = UserAsset(
        user_id=current_user.id,
        project_id=project_id,
        file_name=safe_name,
        asset_type=asset_type,
        mime_type=file.content_type or mimetypes.guess_type(safe_name)[0] or "application/octet-stream",
        file_path=str(path),
        size_bytes=size,
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return _response(asset)


@router.get("", response_model=list[UserAssetResponse])
async def list_assets(
    db: DBSession,
    current_user=Depends(get_current_user),
    asset_type: str | None = Query(default=None),
    project_id: UUID | None = Query(default=None),
):
    query = select(UserAsset).where(UserAsset.user_id == current_user.id)
    if asset_type:
        if asset_type not in ALLOWED_TYPES:
            raise HTTPException(status_code=400, detail="Invalid asset type.")
        query = query.where(UserAsset.asset_type == asset_type)
    if project_id:
        query = query.where(UserAsset.project_id == project_id)
    query = query.order_by(UserAsset.created_at.desc())
    result = await db.execute(query)
    return [_response(asset) for asset in result.scalars().all()]


@router.get("/{asset_id}/file")
async def get_asset_file(
    asset_id: UUID,
    db: DBSession,
    access_token: str | None = Query(default=None),
    current_user=Depends(get_current_user),
):
    # <img>/<video> tags cannot attach Authorization headers, so allow the
    # existing JWT as a short URL query parameter for protected asset previews.
    if access_token:
        try:
            user_id = decode_access_token(access_token)
            current_user = await get_user_by_id(db, user_id)
        except Exception:
            raise HTTPException(status_code=401, detail="Invalid or expired access token.")
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    asset = await db.scalar(
        select(UserAsset).where(UserAsset.id == asset_id, UserAsset.user_id == current_user.id)
    )
    if not asset or not Path(asset.file_path).exists():
        raise HTTPException(status_code=404, detail="Asset not found.")
    return FileResponse(asset.file_path, media_type=asset.mime_type, filename=asset.file_name)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: UUID,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    asset = await db.scalar(
        select(UserAsset).where(UserAsset.id == asset_id, UserAsset.user_id == current_user.id)
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found.")
    Path(asset.file_path).unlink(missing_ok=True)
    await db.delete(asset)
    await db.commit()
