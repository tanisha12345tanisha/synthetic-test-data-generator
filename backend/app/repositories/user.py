from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User
from app.repositories.base import AsyncRepository


class UserRepository(AsyncRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    @staticmethod
    def normalize_email(email: str) -> str:
        return email.strip().lower()

    async def get_by_email(self, email: str) -> User | None:
        normalized_email = self.normalize_email(email)
        statement = select(User).where(User.normalized_email == normalized_email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()
