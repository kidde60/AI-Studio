from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import DBSession, get_current_user
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.project_service import (
    create_project,
    delete_project,
    get_project,
    list_projects,
    update_project,
)


router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create(
    request: ProjectCreateRequest,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    return await create_project(db, current_user.id, request)


@router.get("", response_model=list[ProjectResponse])
async def list_all(
    db: DBSession,
    current_user=Depends(get_current_user),
):
    return await list_projects(db, current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_one(
    project_id: UUID,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    project = await get_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return project


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update(
    project_id: UUID,
    request: ProjectUpdateRequest,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    project = await get_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    return await update_project(db, project, request)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove(
    project_id: UUID,
    db: DBSession,
    current_user=Depends(get_current_user),
):
    project = await get_project(db, current_user.id, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found.")
    await delete_project(db, project)
