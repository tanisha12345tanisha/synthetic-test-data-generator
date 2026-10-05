from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


EXPECTED_REVISION = "9a4f2c8d1e30"


@pytest_asyncio.fixture
async def integration_engine() -> AsyncIterator[AsyncEngine]:
    settings = get_settings()
    database_url = settings.test_database_url

    if not database_url:
        pytest.skip(
            "TEST_DATABASE_URL is not configured."
        )

    parsed_url = make_url(database_url)
    database_name = parsed_url.database or ""

    if "test" not in database_name.lower():
        pytest.fail(
            "TEST_DATABASE_URL must point to a database "
            "containing 'test' in its name."
        )

    engine = create_async_engine(
        database_url,
        poolclass=NullPool,
    )

    try:
        async with engine.connect() as connection:
            revision = await connection.scalar(
                text(
                    "SELECT version_num "
                    "FROM alembic_version"
                )
            )

            if revision != EXPECTED_REVISION:
                pytest.fail(
                    f"Test database revision is "
                    f"{revision!r}; expected "
                    f"{EXPECTED_REVISION!r}."
                )

        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def db_session(
    integration_engine: AsyncEngine,
) -> AsyncIterator[AsyncSession]:
    async with integration_engine.connect() as connection:
        transaction = await connection.begin()

        session_factory = async_sessionmaker(
            bind=connection,
            expire_on_commit=False,
            autoflush=False,
        )

        session = session_factory()

        try:
            yield session
        finally:
            await session.close()

            if transaction.is_active:
                await transaction.rollback()
