
from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.content import router as content_router
from app.api.v1.media import router as media_router
from app.api.v1.projects import router as projects_router
from app.api.v1.storyboards import router as storyboards_router
from app.api.v1.tts import router as tts_router
from app.api.v1.production import router as production_router
from app.api.v1.assets import router as assets_router
from app.api.v1.production_assets import router as production_assets_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(content_router)
api_router.include_router(projects_router)
api_router.include_router(storyboards_router)
api_router.include_router(media_router)
api_router.include_router(tts_router)
api_router.include_router(production_router)
api_router.include_router(assets_router)
api_router.include_router(production_assets_router)
