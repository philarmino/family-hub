from collections.abc import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from .config import get_settings


class Base(DeclarativeBase):
    pass


_settings = get_settings()
_settings.data_dir.mkdir(parents=True, exist_ok=True)
(_settings.data_dir / "photos").mkdir(parents=True, exist_ok=True)

engine = create_async_engine(
    f"sqlite+aiosqlite:///{_settings.data_dir / 'app.db'}",
    echo=False,
)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with SessionLocal() as session:
        yield session


async def _migrate(conn) -> None:
    result = await conn.execute(text("PRAGMA table_info(week_plan_days)"))
    columns = {row[1] for row in result.fetchall()}
    if columns and "servings" not in columns:
        await conn.execute(
            text("ALTER TABLE week_plan_days ADD COLUMN servings INTEGER NOT NULL DEFAULT 4")
        )


async def init_db() -> None:
    async with engine.begin() as conn:
        from . import models  # noqa: F401

        await conn.run_sync(Base.metadata.create_all)
        await _migrate(conn)
