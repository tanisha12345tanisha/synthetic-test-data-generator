from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, require_admin
from app.core.auth_exceptions import InvalidCredentialsError, InvalidTokenError
from app.db.models import User
from app.db.session import get_database_session
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    MessageResponse,
    RefreshRequest,
    RegistrationRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["authentication"])


def client_data(request: Request) -> tuple[str | None, str | None]:
    ip = request.client.host if request.client else None
    return ip, request.headers.get("user-agent")


@router.post("/register", response_model=TokenResponse, status_code=201)
async def register(payload: RegistrationRequest, session: Annotated[AsyncSession, Depends(get_database_session)]):
    try:
        return await AuthService(session).register(payload)
    except InvalidCredentialsError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, request: Request, session: Annotated[AsyncSession, Depends(get_database_session)]):
    ip, agent = client_data(request)
    try:
        return await AuthService(session).login(payload, client_ip=ip, user_agent=agent)
    except InvalidCredentialsError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


@router.post("/refresh", response_model=TokenResponse)
async def refresh(payload: RefreshRequest, session: Annotated[AsyncSession, Depends(get_database_session)]):
    try:
        return await AuthService(session).refresh(payload.refresh_token)
    except InvalidTokenError as error:
        raise HTTPException(status_code=401, detail=str(error)) from error


@router.post("/logout", response_model=MessageResponse)
async def logout(payload: LogoutRequest, session: Annotated[AsyncSession, Depends(get_database_session)]):
    await AuthService(session).logout(payload.refresh_token)
    return MessageResponse(message="Logged out successfully.")


@router.get("/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(get_current_user)]):
    return user


@router.get("/admin-check", response_model=UserResponse)
async def admin_check(user: Annotated[User, Depends(require_admin)]):
    return user


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(payload: ForgotPasswordRequest, request: Request, session: Annotated[AsyncSession, Depends(get_database_session)]):
    ip, agent = client_data(request)
    await AuthService(session).forgot_password(str(payload.email), client_ip=ip, user_agent=agent)
    return MessageResponse(message="If the account exists, password reset instructions have been sent.")


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(payload: ResetPasswordRequest, session: Annotated[AsyncSession, Depends(get_database_session)]):
    try:
        await AuthService(session).reset_password(payload)
    except InvalidTokenError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return MessageResponse(message="Password reset successfully. Please sign in again.")
