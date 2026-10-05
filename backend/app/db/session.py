from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings


settings = get_settings()


def create_database_engine() -> AsyncEngine:
    engine_options: dict[str, object] = {
        "echo": settings.database_echo,
        "pool_pre_ping": True,
    }

    if settings.database_url.startswith(
        "postgresql+asyncpg://"
    ):
        engine_options.update(
            {
                "pool_size": settings.database_pool_size,
                "max_overflow": settings.database_max_overflow,
                "pool_timeout": (
                    settings.database_pool_timeout_seconds
                ),
                "pool_recycle": (
                    settings.database_pool_recycle_seconds
                ),
            }
        )

    return create_async_engine(
        settings.database_url,
        **engine_options,
    )


database_engine = create_database_engine()


AsyncSessionFactory = async_sessionmaker(
    bind=database_engine,
    class_=AsyncSession,
    autoflush=False,
    expire_on_commit=False,
)


async def get_database_session() -> AsyncIterator[AsyncSession]:
    async with AsyncSessionFactory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def close_database_engine() -> None:
    await database_engine.dispose()
