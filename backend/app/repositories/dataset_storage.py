from collections.abc import Sequence
from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Dataset, DatasetShare, SharePermission

class DatasetAccessRepository:
    def __init__(self, session: AsyncSession): self.session = session

    async def get_accessible(self, dataset_id: UUID, user_id: UUID) -> tuple[Dataset | None, SharePermission | None]:
        row = (await self.session.execute(
            select(Dataset, DatasetShare.permission)
            .outerjoin(DatasetShare, (DatasetShare.dataset_id == Dataset.id) & (DatasetShare.user_id == user_id))
            .where(Dataset.id == dataset_id, or_(Dataset.owner_id == user_id, DatasetShare.user_id == user_id))
        )).first()
        return (row[0], row[1]) if row else (None, None)

    async def list_accessible(self, user_id: UUID, offset: int, limit: int) -> Sequence[tuple[Dataset, SharePermission | None]]:
        return (await self.session.execute(
            select(Dataset, DatasetShare.permission)
            .outerjoin(DatasetShare, (DatasetShare.dataset_id == Dataset.id) & (DatasetShare.user_id == user_id))
            .where(or_(Dataset.owner_id == user_id, DatasetShare.user_id == user_id))
            .order_by(Dataset.updated_at.desc()).offset(offset).limit(limit)
        )).all()
