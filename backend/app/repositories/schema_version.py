from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dataset, SchemaVersion, SchemaVersionTrigger
from app.repositories.base import AsyncRepository


class SchemaVersionRepository(AsyncRepository[SchemaVersion]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SchemaVersion)

    async def list_for_dataset(self, dataset_id: UUID) -> Sequence[SchemaVersion]:
        statement = (
            select(SchemaVersion)
            .where(SchemaVersion.dataset_id == dataset_id)
            .order_by(SchemaVersion.version_number.desc())
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_latest(self, dataset_id: UUID) -> SchemaVersion | None:
        statement = (
            select(SchemaVersion)
            .where(SchemaVersion.dataset_id == dataset_id)
            .order_by(SchemaVersion.version_number.desc())
            .limit(1)
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def create_next(
        self,
        *,
        dataset_id: UUID,
        created_by: UUID,
        trigger: SchemaVersionTrigger,
        schema_document: dict,
        restored_from_version_id: UUID | None = None,
    ) -> SchemaVersion:
        lock_statement = (
            select(Dataset.id)
            .where(Dataset.id == dataset_id)
            .with_for_update()
        )
        locked_dataset = await self.session.scalar(lock_statement)
        if locked_dataset is None:
            raise ValueError("Dataset does not exist.")

        version_statement = select(
            func.coalesce(func.max(SchemaVersion.version_number), 0)
        ).where(SchemaVersion.dataset_id == dataset_id)
        current_version = await self.session.scalar(version_statement)

        version = SchemaVersion(
            dataset_id=dataset_id,
            version_number=int(current_version or 0) + 1,
            trigger=trigger,
            schema_document=schema_document,
            created_by=created_by,
            restored_from_version_id=restored_from_version_id,
        )
        return await self.add(version)
