from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_exceptions import InvalidTokenError
from app.core.security import decode_access_token
from app.db.models import User, UserRole, UserStatus
from app.db.session import get_database_session
from app.repositories.user import UserRepository


bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_database_session)],
) -> User:
    unauthorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if credentials is None:
        raise unauthorized
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = UUID(str(payload["sub"]))
    except (InvalidTokenError, ValueError, KeyError) as error:
        raise unauthorized from error
    user = await UserRepository(session).get(user_id)
    if not user or user.status != UserStatus.ACTIVE:
        raise unauthorized
    return user


async def require_admin(user: Annotated[User, Depends(get_current_user)]) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Administrator access required.")
    return user
