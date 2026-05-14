from collections.abc import AsyncGenerator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings
from app.db.base import Base

_engine = None
async_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.database_url
        _engine = create_async_engine(
            url,
            echo=False,
            connect_args={"check_same_thread": False},
        )
    return _engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    global async_session_maker
    if async_session_maker is None:
        async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return async_session_maker


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_session_maker()
    async with session_maker() as session:
        yield session


async def init_db() -> None:
    import app.models  # noqa: F401 — register ORM metadata

    settings = get_settings()
    path = Path(settings.database_url.removeprefix("sqlite+aiosqlite:///"))
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
