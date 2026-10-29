
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select

from app.api.ai_errors import ai_failure
from app.api.dependencies import DBSession, get_current_user
from app.models.user_asset import UserAsset
from app.schemas.assets import UserAssetSceneSelectRequest
from app.schemas.storyboard import (
    SceneCreateRequest,
    SceneMediaSearchResponse,
    SceneMediaSelectRequest,
    SceneMediaSelectResponse,
    SceneResponse,
    StoryboardCreateRequest,
    StoryboardGenerateRequest,
    StoryboardResponse,
)
from app.services.media.factory import get_media_providers
from app.services.storyboard_service import (
    add_scene,
    attach_scene_media,
    attach_user_asset,
    create_storyboard,
    generate_storyboard_from_content,
    get_scene,
    get_storyboard,
    get_user_content,
    get_user_project,
    list_storyboards,
)

router = APIRouter(prefix="/storyboards", tags=["Storyboards"])


@router.post("/projects/{project_id}", response_model=StoryboardResponse, status_code=status.HTTP_201_CREATED)
async def create(project_id: UUID, request: StoryboardCreateRequest, db: DBSession, current_user=Depends(get_current_user)):
    project = await get_user_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return await create_storyboard(db, project, request)


@router.post("/projects/{project_id}/generate", response_model=StoryboardResponse, status_code=status.HTTP_201_CREATED)
async def generate(project_id: UUID, request: StoryboardGenerateRequest, db: DBSession, current_user=Depends(get_current_user)):
    project = await get_user_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    content = await get_user_content(db, current_user.id, request.content_id)
    if not content:
        raise HTTPException(status_code=404, detail="Generated content not found.")
    try:
        return await generate_storyboard_from_content(db, project, content)
    except Exception as exc:
        raise ai_failure(exc) from exc


@router.get("/projects/{project_id}", response_model=list[StoryboardResponse])
async def list_all(project_id: UUID, db: DBSession, current_user=Depends(get_current_user)):
    project = await get_user_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return await list_storyboards(db, current_user.id, project_id)


@router.get("/{storyboard_id}", response_model=StoryboardResponse)
async def get_one(storyboard_id: UUID, db: DBSession, current_user=Depends(get_current_user)):
    storyboard = await get_storyboard(db, current_user.id, storyboard_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found.")
    return storyboard


@router.post("/{storyboard_id}/scenes", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(storyboard_id: UUID, request: SceneCreateRequest, db: DBSession, current_user=Depends(get_current_user)):
    storyboard = await get_storyboard(db, current_user.id, storyboard_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found.")
    return await add_scene(db, storyboard, request)


@router.post("/{storyboard_id}/scenes/{scene_id}/media/search", response_model=SceneMediaSearchResponse)
async def search_scene_media(storyboard_id: UUID, scene_id: UUID, db: DBSession, current_user=Depends(get_current_user)):
    storyboard = await get_storyboard(db, current_user.id, storyboard_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found.")
    scene = await get_scene(db, current_user.id, scene_id)
    if not scene or scene.storyboard_id != storyboard.id:
        raise HTTPException(status_code=404, detail="Scene not found.")
    query = (scene.visual_description or scene.title).strip()
    if not query:
        raise HTTPException(status_code=400, detail="This scene has no visual description to search.")

    providers = get_media_providers()
    if not providers:
        raise HTTPException(status_code=503, detail="No stock media provider is configured. Add PEXELS_API_KEY or PIXABAY_API_KEY to backend/.env.")

    results = []
    last_error = None
    for provider in providers:
        try:
            results.extend(await provider.search(query, "video", 6))
            if len(results) >= 6:
                break
        except Exception as exc:
            last_error = exc
    if not results and last_error:
        raise HTTPException(status_code=502, detail="Stock media search failed.")
    return SceneMediaSearchResponse(scene_id=scene.id, query=query, media_type="video", results=results[:6])


@router.post("/{storyboard_id}/scenes/{scene_id}/media/select", response_model=SceneMediaSelectResponse)
async def select_scene_media(storyboard_id: UUID, scene_id: UUID, request: SceneMediaSelectRequest, db: DBSession, current_user=Depends(get_current_user)):
    storyboard = await get_storyboard(db, current_user.id, storyboard_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found.")
    scene = await get_scene(db, current_user.id, scene_id)
    if not scene or scene.storyboard_id != storyboard.id:
        raise HTTPException(status_code=404, detail="Scene not found.")
    media = dict(request.media)
    media["selection_source"] = "stock_manual"
    media["manual_selection"] = True
    updated = await attach_scene_media(db, scene, media)
    return SceneMediaSelectResponse(scene=updated)


@router.post("/{storyboard_id}/scenes/{scene_id}/media/user-select", response_model=SceneMediaSelectResponse)
async def select_user_asset(
    storyboard_id: UUID,
    scene_id: UUID,
    request: UserAssetSceneSelectRequest,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    storyboard = await get_storyboard(db, current_user.id, storyboard_id)
    if not storyboard:
        raise HTTPException(status_code=404, detail="Storyboard not found.")
    scene = await get_scene(db, current_user.id, scene_id)
    if not scene or scene.storyboard_id != storyboard.id:
        raise HTTPException(status_code=404, detail="Scene not found.")

    asset = await db.scalar(
        select(UserAsset).where(
            UserAsset.id == request.asset_id,
            UserAsset.user_id == current_user.id,
        )
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Uploaded asset not found.")

    media = {
        "id": str(asset.id),
        "type": asset.asset_type,
        "source": "user_upload",
        "provider": "user",
        "description": asset.file_name,
        "file_path": asset.file_path,
        "url": f"/assets/{asset.id}/file",
        "selection_source": "user_selected",
        "manual_selection": True,
    }
    updated = await attach_user_asset(db, scene, media)
    return SceneMediaSelectResponse(scene=updated)
