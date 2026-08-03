"""Async SQLAlchemy database engine and session management."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings


connect_args = {}
engine_args = {
    "echo": False,
}

# Ensure postgresql uses asyncpg if not explicitly specified
db_url = settings.DATABASE_URL
if db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

from sqlalchemy.pool import NullPool

if db_url.startswith("postgresql"):
    engine_args["pool_pre_ping"] = True
    engine_args["poolclass"] = NullPool
    connect_args["statement_cache_size"] = 0
    engine_args["connect_args"] = connect_args
elif db_url.startswith("sqlite"):
    # SQLite needs this to allow multiple async requests to the same file
    connect_args["check_same_thread"] = False
    engine_args["connect_args"] = connect_args

engine = create_async_engine(
    db_url,
    **engine_args
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db():
    """Dependency that provides a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
