from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.db.session import Base, engine
import app.models  # noqa: F401 - registers all SQLAlchemy models


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Development/MVP behavior:
    # create every registered SQLAlchemy table automatically if it does not exist.
    # Later, replace this with Alembic migrations for production deployments.
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    yield

    await engine.dispose()


app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-video-studio-api"}
