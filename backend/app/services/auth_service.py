from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_exceptions import InvalidCredentialsError, InvalidTokenError
from app.core.config import get_settings
from app.core.security import (
    create_access_token,
    create_password_reset_token,
    create_refresh_token,
    hash_opaque_token,
    hash_password,
    verify_password,
)
from app.db.models import (
    AuditEvent,
    AuditResult,
    PasswordResetToken,
    RefreshSession,
    User,
    UserRole,
    UserStatus,
)
from app.repositories.auth import PasswordResetTokenRepository, RefreshSessionRepository
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegistrationRequest, ResetPasswordRequest, TokenResponse
from app.services.email_service import send_password_reset_email


GENERIC_AUTH_ERROR = "Invalid email or password."


class AuthService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.sessions = RefreshSessionRepository(session)
        self.reset_tokens = PasswordResetTokenRepository(session)

    def _audit(self, *, actor_id, action: str, result: AuditResult, metadata=None) -> None:
        self.session.add(AuditEvent(
            actor_id=actor_id,
            action=action,
            result=result,
            safe_metadata=metadata,
            timestamp=datetime.now(UTC),
        ))

    def _response(self, user: User, access_token: str, refresh_token: str) -> TokenResponse:
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=get_settings().access_token_expiry_minutes * 60,
            user=user,
        )

    async def register(self, request: RegistrationRequest) -> TokenResponse:
        normalized = self.users.normalize_email(str(request.email))
        if await self.users.get_by_email(normalized):
            raise InvalidCredentialsError("An account with this email already exists.")
        user = User(
            email=str(request.email).strip(),
            normalized_email=normalized,
            display_name=request.display_name.strip(),
            password_hash=hash_password(request.password),
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        await self.users.add(user)
        opaque = create_refresh_token()
        self.session.add(RefreshSession(
            user_id=user.id,
            token_hash=opaque.token_hash,
            expires_at=opaque.expires_at,
        ))
        self._audit(actor_id=user.id, action="auth.registration.success", result=AuditResult.SUCCESS)
        await self.session.commit()
        await self.session.refresh(user)
        access = create_access_token(user_id=user.id, role=user.role)
        return self._response(user, access, opaque.value)

    async def login(self, request: LoginRequest, *, client_ip=None, user_agent=None) -> TokenResponse:
        user = await self.users.get_by_email(str(request.email))
        if not user or not verify_password(request.password, user.password_hash):
            self._audit(actor_id=None, action="auth.login.failure", result=AuditResult.FAILURE)
            await self.session.commit()
            raise InvalidCredentialsError(GENERIC_AUTH_ERROR)
        if user.status != UserStatus.ACTIVE:
            self._audit(actor_id=user.id, action="auth.login.failure", result=AuditResult.FAILURE)
            await self.session.commit()
            raise InvalidCredentialsError(GENERIC_AUTH_ERROR)
        opaque = create_refresh_token()
        self.session.add(RefreshSession(
            user_id=user.id,
            token_hash=opaque.token_hash,
            expires_at=opaque.expires_at,
            client_ip=client_ip,
            user_agent=user_agent,
        ))
        user.last_login_at = datetime.now(UTC)
        self._audit(actor_id=user.id, action="auth.login.success", result=AuditResult.SUCCESS)
        await self.session.commit()
        access = create_access_token(user_id=user.id, role=user.role)
        return self._response(user, access, opaque.value)

    async def refresh(self, raw_token: str) -> TokenResponse:
        stored = await self.sessions.get_by_hash(hash_opaque_token(raw_token))
        now = datetime.now(UTC)
        if not stored or stored.revoked_at or stored.expires_at <= now:
            raise InvalidTokenError("Invalid refresh token.")
        user = await self.users.get(stored.user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise InvalidTokenError("Invalid refresh token.")
        stored.revoked_at = now
        opaque = create_refresh_token()
        self.session.add(RefreshSession(
            user_id=user.id,
            token_hash=opaque.token_hash,
            expires_at=opaque.expires_at,
            client_ip=stored.client_ip,
            user_agent=stored.user_agent,
        ))
        self._audit(actor_id=user.id, action="auth.refresh.success", result=AuditResult.SUCCESS)
        await self.session.commit()
        access = create_access_token(user_id=user.id, role=user.role)
        return self._response(user, access, opaque.value)

    async def logout(self, raw_token: str) -> None:
        stored = await self.sessions.get_by_hash(hash_opaque_token(raw_token))
        if stored and stored.revoked_at is None:
            stored.revoked_at = datetime.now(UTC)
            self._audit(actor_id=stored.user_id, action="auth.logout", result=AuditResult.SUCCESS)
            await self.session.commit()

    async def forgot_password(self, email: str, *, client_ip=None, user_agent=None) -> None:
        user = await self.users.get_by_email(email)
        if not user or user.status != UserStatus.ACTIVE:
            return
        opaque = create_password_reset_token()
        self.session.add(PasswordResetToken(
            user_id=user.id,
            token_hash=opaque.token_hash,
            expires_at=opaque.expires_at,
            requested_ip=client_ip,
            user_agent=user_agent,
        ))
        self._audit(actor_id=user.id, action="auth.password_reset.requested", result=AuditResult.SUCCESS)
        await self.session.commit()
        await send_password_reset_email(user.email, opaque.value)

    async def reset_password(self, request: ResetPasswordRequest) -> None:
        stored = await self.reset_tokens.get_by_hash(hash_opaque_token(request.token))
        now = datetime.now(UTC)
        if not stored or stored.used_at or stored.expires_at <= now:
            raise InvalidTokenError("Invalid or expired password reset token.")
        user = await self.users.get(stored.user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise InvalidTokenError("Invalid or expired password reset token.")
        user.password_hash = hash_password(request.password)
        stored.used_at = now
        await self.sessions.revoke_all(user.id)
        self._audit(actor_id=user.id, action="auth.password_reset.completed", result=AuditResult.SUCCESS)
        await self.session.commit()
