from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import GenerationRun, GenerationStatus
from app.repositories.base import AsyncRepository


class GenerationRunRepository(AsyncRepository[GenerationRun]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, GenerationRun)

    async def list_for_dataset(
        self,
        dataset_id: UUID,
        *,
        status: GenerationStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> Sequence[GenerationRun]:
        statement = select(GenerationRun).where(
            GenerationRun.dataset_id == dataset_id
        )
        if status is not None:
            statement = statement.where(GenerationRun.status == status)
        statement = (
            statement
            .order_by(GenerationRun.created_at.desc(), GenerationRun.id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def get_for_requester(
        self,
        generation_id: UUID,
        requested_by: UUID,
    ) -> GenerationRun | None:
        statement = select(GenerationRun).where(
            GenerationRun.id == generation_id,
            GenerationRun.requested_by == requested_by,
        )
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
