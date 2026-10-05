from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    Dataset,
    DatasetType,
    GenerationOutput,
    GenerationRun,
    GenerationStatus,
    InputMode,
    OutputFormat,
    QualityReport,
    SchemaVersionTrigger,
    User,
)
from app.repositories import (
    DatasetRepository,
    GenerationRunRepository,
    SchemaVersionRepository,
    UserRepository,
)

pytestmark = pytest.mark.integration


async def create_user(session, email: str) -> User:
    user = User(
        email=email,
        normalized_email=email.strip().lower(),
        display_name="Integration User",
        password_hash="test-password-hash",
    )
    session.add(user)
    await session.flush()
    return user


async def create_dataset(session, owner: User, name: str = "Test Dataset") -> Dataset:
    dataset = Dataset(
        owner_id=owner.id,
        name=name,
        dataset_type=DatasetType.SINGLE_TABLE,
        input_mode=InputMode.MANUAL,
    )
    session.add(dataset)
    await session.flush()
    return dataset


@pytest.mark.asyncio
async def test_user_repository_round_trip(db_session):
    repository = UserRepository(db_session)
    user = await repository.add(
        User(
            email="Repository@Test.example",
            normalized_email="repository@test.example",
            display_name="Repository User",
            password_hash="hash",
        ),
        refresh=True,
    )

    loaded = await repository.get_by_email("  REPOSITORY@test.example ")

    assert loaded is not None
    assert loaded.id == user.id
    assert loaded.normalized_email == "repository@test.example"


@pytest.mark.asyncio
async def test_normalized_email_uniqueness_is_enforced(db_session):
    await create_user(db_session, "unique@test.example")

    with pytest.raises(IntegrityError):
        async with db_session.begin_nested():
            duplicate = User(
                email="UNIQUE@test.example",
                normalized_email="unique@test.example",
                display_name="Duplicate",
                password_hash="hash",
            )
            db_session.add(duplicate)
            await db_session.flush()


@pytest.mark.asyncio
async def test_dataset_repository_is_owner_scoped(db_session):
    owner = await create_user(db_session, "owner@test.example")
    another_user = await create_user(db_session, "other@test.example")
    dataset = await create_dataset(db_session, owner)
    repository = DatasetRepository(db_session)

    assert await repository.get_owned(dataset.id, owner.id) is not None
    assert await repository.get_owned(dataset.id, another_user.id) is None
    assert list(await repository.list_for_owner(owner.id)) == [dataset]


@pytest.mark.asyncio
async def test_schema_versions_increment_and_remain_distinct(db_session):
    owner = await create_user(db_session, "versions@test.example")
    dataset = await create_dataset(db_session, owner)
    repository = SchemaVersionRepository(db_session)

    first = await repository.create_next(
        dataset_id=dataset.id,
        created_by=owner.id,
        trigger=SchemaVersionTrigger.MANUAL_SAVE,
        schema_document={"version": 1},
    )
    second = await repository.create_next(
        dataset_id=dataset.id,
        created_by=owner.id,
        trigger=SchemaVersionTrigger.GENERATION,
        schema_document={"version": 2},
    )

    assert first.version_number == 1
    assert second.version_number == 2
    latest = await repository.get_latest(dataset.id)
    assert latest is not None
    assert latest.id == second.id


@pytest.mark.asyncio
async def test_user_delete_cascades_owned_dataset(db_session):
    owner = await create_user(db_session, "cascade@test.example")
    dataset = await create_dataset(db_session, owner)
    dataset_id = dataset.id

    await db_session.execute(delete(User).where(User.id == owner.id))
    await db_session.flush()

    assert await db_session.scalar(
        select(Dataset.id).where(Dataset.id == dataset_id)
    ) is None


@pytest.mark.asyncio
async def test_generation_metadata_persists(db_session):
    owner = await create_user(db_session, "generation@test.example")
    dataset = await create_dataset(db_session, owner)
    schema_repository = SchemaVersionRepository(db_session)
    schema_version = await schema_repository.create_next(
        dataset_id=dataset.id,
        created_by=owner.id,
        trigger=SchemaVersionTrigger.GENERATION,
        schema_document={"tables": [{"name": "customers"}]},
    )

    run = GenerationRun(
        dataset_id=dataset.id,
        schema_version_id=schema_version.id,
        requested_by=owner.id,
        seed=42,
        status=GenerationStatus.COMPLETED,
        progress_percent=100,
        requested_row_total=10,
        generated_row_total=10,
        started_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )
    db_session.add(run)
    await db_session.flush()

    output = GenerationOutput(
        generation_id=run.id,
        object_path="tests/outputs/result.csv",
        output_format=OutputFormat.CSV,
        size_bytes=128,
        checksum_sha256="a" * 64,
        expires_at=datetime.now(UTC) + timedelta(hours=1),
    )
    report = QualityReport(
        generation_id=run.id,
        report_document={"rules_checked": 3},
        score=100.0,
        status="pass",
    )
    db_session.add_all([output, report])
    await db_session.flush()

    loaded = await GenerationRunRepository(db_session).get_for_requester(
        run.id,
        owner.id,
    )
    assert loaded is not None
    assert loaded.generated_row_total == 10
    assert await db_session.scalar(
        select(GenerationOutput.id).where(GenerationOutput.generation_id == run.id)
    ) == output.id
    assert await db_session.scalar(
        select(QualityReport.id).where(QualityReport.generation_id == run.id)
    ) == report.id
