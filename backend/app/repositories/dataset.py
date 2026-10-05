from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Dataset, DatasetStatus
from app.repositories.base import AsyncRepository


class DatasetRepository(AsyncRepository[Dataset]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Dataset)

    async def get_owned(self, dataset_id: UUID, owner_id: UUID) -> Dataset | None:
        statement = select(Dataset).where(
            Dataset.id == dataset_id,
            Dataset.owner_id == owner_id,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_for_owner(
        self,
        owner_id: UUID,
        *,
        status: DatasetStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[Dataset]:
        statement = select(Dataset).where(Dataset.owner_id == owner_id)
        if status is not None:
            statement = statement.where(Dataset.status == status)
        statement = (
            statement
            .order_by(Dataset.updated_at.desc(), Dataset.id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()
