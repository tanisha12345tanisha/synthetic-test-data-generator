from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.db.models import Dataset, SchemaVersionTrigger, User
from app.repositories import (
    AsyncRepository,
    DatasetRepository,
    SchemaVersionRepository,
    UserRepository,
    transactional_session,
)


def scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def sequence_result(values):
    scalars = MagicMock()
    scalars.all.return_value = values
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


@pytest.mark.asyncio
async def test_base_repository_get_uses_session_get():
    entity_id = uuid4()
    user = User()
    session = AsyncMock()
    session.get.return_value = user
    repository = AsyncRepository(session, User)

    result = await repository.get(entity_id)

    assert result is user
    session.get.assert_awaited_once_with(User, entity_id)


@pytest.mark.asyncio
async def test_base_repository_add_flushes_entity():
    session = AsyncMock()
    session.add = MagicMock()
    repository = AsyncRepository(session, User)
    user = User()

    result = await repository.add(user)

    assert result is user
    session.add.assert_called_once_with(user)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_base_repository_rejects_protected_update_fields():
    session = AsyncMock()
    repository = AsyncRepository(session, User)

    with pytest.raises(ValueError, match="Unsupported update fields: id"):
        await repository.update_fields(User(), {"id": uuid4()})


@pytest.mark.asyncio
async def test_base_repository_delete_flushes():
    session = AsyncMock()
    repository = AsyncRepository(session, User)
    user = User()

    await repository.delete(user)

    session.delete.assert_awaited_once_with(user)
    session.flush.assert_awaited_once()


def test_user_repository_normalizes_email():
    assert UserRepository.normalize_email("  USER@Example.COM  ") == "user@example.com"


@pytest.mark.asyncio
async def test_user_repository_get_by_email_returns_user():
    user = User()
    session = AsyncMock()
    session.execute.return_value = scalar_result(user)
    repository = UserRepository(session)

    result = await repository.get_by_email("USER@Example.COM")

    assert result is user
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_dataset_repository_get_owned_returns_dataset():
    dataset = Dataset()
    session = AsyncMock()
    session.execute.return_value = scalar_result(dataset)
    repository = DatasetRepository(session)

    result = await repository.get_owned(uuid4(), uuid4())

    assert result is dataset


@pytest.mark.asyncio
async def test_dataset_repository_lists_owner_datasets():
    datasets = [Dataset(), Dataset()]
    session = AsyncMock()
    session.execute.return_value = sequence_result(datasets)
    repository = DatasetRepository(session)

    result = await repository.list_for_owner(uuid4())

    assert result == datasets


@pytest.mark.asyncio
async def test_schema_version_create_next_locks_dataset_and_increments():
    session = AsyncMock()
    session.add = MagicMock()
    session.scalar.side_effect = [uuid4(), 3]
    repository = SchemaVersionRepository(session)

    version = await repository.create_next(
        dataset_id=uuid4(),
        created_by=uuid4(),
        trigger=SchemaVersionTrigger.MANUAL_SAVE,
        schema_document={"tables": []},
    )

    assert version.version_number == 4
    assert version.schema_document == {"tables": []}
    assert session.scalar.await_count == 2
    session.add.assert_called_once_with(version)
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_schema_version_create_next_rejects_missing_dataset():
    session = AsyncMock()
    session.scalar.return_value = None
    repository = SchemaVersionRepository(session)

    with pytest.raises(ValueError, match="Dataset does not exist"):
        await repository.create_next(
            dataset_id=uuid4(),
            created_by=uuid4(),
            trigger=SchemaVersionTrigger.MANUAL_SAVE,
            schema_document={},
        )


@pytest.mark.asyncio
async def test_transactional_session_uses_session_transaction():
    session = AsyncMock()

    @asynccontextmanager
    async def session_context():
        yield session

    session_factory = MagicMock(return_value=session_context())

    transaction_context = AsyncMock()
    transaction_context.__aenter__.return_value = None
    transaction_context.__aexit__.return_value = None
    session.begin = MagicMock(return_value=transaction_context)

    async with transactional_session(session_factory) as yielded_session:
        assert yielded_session is session

    session.begin.assert_called_once_with()
    transaction_context.__aenter__.assert_awaited_once()
    transaction_context.__aexit__.assert_awaited_once()
