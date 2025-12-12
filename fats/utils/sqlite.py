from pathlib import Path
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from . import log

_sqlite_dir = Path("/") / "var" / "lib" / "fats"
if not _sqlite_dir.exists():
    _sqlite_dir.mkdir(parents=True, exist_ok=True)
_sqlite_path = _sqlite_dir / "fats.db"

_sqlite_uri = "sqlite+aiosqlite:///" + str(_sqlite_path)

async_engine = create_async_engine(_sqlite_uri, echo=False)
log(f"SQLite database path: {_sqlite_uri}")


class Base(MappedAsDataclass, DeclarativeBase):
    pass


AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
)

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
