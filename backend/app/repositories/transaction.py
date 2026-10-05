from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionFactory


SessionFactory = Callable[[], AsyncSession]


@asynccontextmanager
async def transactional_session(
    session_factory: SessionFactory = AsyncSessionFactory,
) -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        async with session.begin():
            yield session
