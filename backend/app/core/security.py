from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
import hashlib
import hmac
import secrets
from uuid import UUID, uuid4

import jwt
from jwt import InvalidTokenError as PyJWTInvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from app.core.auth_exceptions import InvalidTokenError
from app.core.config import get_settings
from app.db.models import UserRole


JWT_ALGORITHM = "HS256"
_password_hash = PasswordHash.recommended()


@dataclass(frozen=True)
class OpaqueToken:
    value: str
    token_hash: str
    expires_at: datetime


def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")
    return _password_hash.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    if not password or not password_hash:
        return False
    try:
        return _password_hash.verify(password, password_hash)
    except (TypeError, ValueError, UnknownHashError):
        return False


def hash_opaque_token(token: str) -> str:
    if not token:
        raise ValueError("Token cannot be empty.")
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def token_hash_matches(token: str, expected_hash: str) -> bool:
    if not token or not expected_hash:
        return False
    actual_hash = hash_opaque_token(token)
    return hmac.compare_digest(actual_hash, expected_hash)


def create_opaque_token(*, expires_delta: timedelta) -> OpaqueToken:
    if expires_delta <= timedelta(0):
        raise ValueError("Token expiry must be in the future.")

    value = secrets.token_urlsafe(64)
    return OpaqueToken(
        value=value,
        token_hash=hash_opaque_token(value),
        expires_at=datetime.now(UTC) + expires_delta,
    )


def create_refresh_token() -> OpaqueToken:
    settings = get_settings()
    return create_opaque_token(
        expires_delta=timedelta(days=settings.refresh_token_expiry_days)
    )


def create_password_reset_token() -> OpaqueToken:
    settings = get_settings()
    return create_opaque_token(
        expires_delta=timedelta(
            minutes=settings.password_reset_token_expiry_minutes
        )
    )


def create_access_token(
    *,
    user_id: UUID,
    role: UserRole,
    now: datetime | None = None,
) -> str:
    settings = get_settings()
    issued_at = now or datetime.now(UTC)
    expires_at = issued_at + timedelta(
        minutes=settings.access_token_expiry_minutes
    )
    payload = {
        "sub": str(user_id),
        "role": role.value,
        "type": "access",
        "jti": str(uuid4()),
        "iat": issued_at,
        "exp": expires_at,
    }
    return jwt.encode(
        payload,
        settings.access_token_secret,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict[str, object]:
    settings = get_settings()
    if not token:
        raise InvalidTokenError("Invalid authentication token.")

    try:
        payload = jwt.decode(
            token,
            settings.access_token_secret,
            algorithms=[JWT_ALGORITHM],
            options={"require": ["sub", "role", "type", "jti", "iat", "exp"]},
        )
    except PyJWTInvalidTokenError as error:
        raise InvalidTokenError("Invalid authentication token.") from error

    if payload.get("type") != "access":
        raise InvalidTokenError("Invalid authentication token.")

    try:
        UUID(str(payload["sub"]))
        UserRole(str(payload["role"]))
        UUID(str(payload["jti"]))
    except (KeyError, TypeError, ValueError) as error:
        raise InvalidTokenError("Invalid authentication token.") from error

    return payload
