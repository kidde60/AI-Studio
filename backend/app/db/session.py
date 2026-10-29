from collections.abc import AsyncGenerator

from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


settings = get_settings()
database_url = make_url(settings.database_url)
connect_args: dict[str, object] = {}

if database_url.drivername == "postgresql+asyncpg":
    query = dict(database_url.query)
    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    database_url = database_url.set(query=query)
    if sslmode:
        connect_args["ssl"] = sslmode

engine = create_async_engine(
    database_url,
    connect_args=connect_args,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

