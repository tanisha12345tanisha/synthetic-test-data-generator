from collections.abc import Sequence
from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base


ModelType = TypeVar("ModelType", bound=Base)


class AsyncRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model_type: type[ModelType]) -> None:
        self.session = session
        self.model_type = model_type

    async def get(self, entity_id: UUID) -> ModelType | None:
        return await self.session.get(self.model_type, entity_id)

    async def list(self, *, offset: int = 0, limit: int = 100) -> Sequence[ModelType]:
        statement = (
            select(self.model_type)
            .order_by(self.model_type.id)
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(statement)
        return result.scalars().all()

    async def add(self, entity: ModelType, *, refresh: bool = False) -> ModelType:
        self.session.add(entity)
        await self.session.flush()
        if refresh:
            await self.session.refresh(entity)
        return entity

    async def update_fields(
        self,
        entity: ModelType,
        values: dict[str, Any],
        *,
        refresh: bool = False,
    ) -> ModelType:
        protected_fields = {"id", "created_at"}
        unknown_fields = {
            field_name
            for field_name in values
            if field_name in protected_fields or not hasattr(entity, field_name)
        }
        if unknown_fields:
            invalid_names = ", ".join(sorted(unknown_fields))
            raise ValueError(f"Unsupported update fields: {invalid_names}")

        for field_name, value in values.items():
            setattr(entity, field_name, value)

        await self.session.flush()
        if refresh:
            await self.session.refresh(entity)
        return entity

    async def delete(self, entity: ModelType) -> None:
        await self.session.delete(entity)
        await self.session.flush()
