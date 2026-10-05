import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import (
    Base,
    NAMING_CONVENTION,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.db.session import (
    AsyncSessionFactory,
    close_database_engine,
    database_engine,
    get_database_session,
)


def test_base_has_expected_naming_convention():
    naming_convention = Base.metadata.naming_convention

    assert naming_convention["pk"] == "pk_%(table_name)s"
    assert naming_convention["uq"] == (
        "uq_%(table_name)s_%(column_0_name)s"
    )
    assert naming_convention["ix"] == "ix_%(column_0_label)s"
    assert naming_convention["fk"] == (
        "fk_%(table_name)s_%(column_0_name)s_"
        "%(referred_table_name)s"
    )
    assert naming_convention == NAMING_CONVENTION


def test_uuid_primary_key_mixin_declares_id():
    assert hasattr(UUIDPrimaryKeyMixin, "__annotations__")
    assert "id" in UUIDPrimaryKeyMixin.__annotations__


def test_timestamp_mixin_declares_timestamps():
    annotations = TimestampMixin.__annotations__

    assert "created_at" in annotations
    assert "updated_at" in annotations


def test_database_engine_uses_configured_url():
    assert str(database_engine.url).startswith(
        "postgresql+asyncpg://"
    )


def test_async_session_factory_is_configured():
    assert AsyncSessionFactory is not None


@pytest.mark.asyncio
async def test_database_session_dependency_yields_session():
    session_generator = get_database_session()
    session = await anext(session_generator)

    try:
        assert isinstance(session, AsyncSession)
    finally:
        await session_generator.aclose()


@pytest.mark.asyncio
async def test_close_database_engine():
    await close_database_engine()
