from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PasswordResetToken, RefreshSession
from app.repositories.base import AsyncRepository


class RefreshSessionRepository(AsyncRepository[RefreshSession]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, RefreshSession)

    async def get_by_hash(self, token_hash: str) -> RefreshSession | None:
        result = await self.session.execute(
            select(RefreshSession).where(RefreshSession.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def revoke_all(self, user_id: UUID) -> None:
        await self.session.execute(
            update(RefreshSession)
            .where(RefreshSession.user_id == user_id, RefreshSession.revoked_at.is_(None))
            .values(revoked_at=datetime.now(UTC))
        )


class PasswordResetTokenRepository(AsyncRepository[PasswordResetToken]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, PasswordResetToken)

    async def get_by_hash(self, token_hash: str) -> PasswordResetToken | None:
        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()
