from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest

from app.core.auth_exceptions import InvalidTokenError
from app.core.config import get_settings
from app.core.security import (
    JWT_ALGORITHM,
    create_access_token,
    create_opaque_token,
    create_password_reset_token,
    create_refresh_token,
    decode_access_token,
    hash_opaque_token,
    hash_password,
    token_hash_matches,
    verify_password,
)
from app.db.models import UserRole


def test_password_hash_is_not_plaintext_and_verifies():
    password = "StrongPassword#2026"
    password_hash = hash_password(password)

    assert password_hash != password
    assert verify_password(password, password_hash) is True
    assert verify_password("wrong-password", password_hash) is False


def test_empty_password_is_rejected():
    with pytest.raises(ValueError, match="Password cannot be empty"):
        hash_password("")


def test_invalid_password_hash_returns_false():
    assert verify_password("password", "not-a-valid-hash") is False
    assert verify_password("", "hash") is False


def test_opaque_token_hash_is_deterministic_and_not_raw_token():
    token = "sample-token"
    token_hash = hash_opaque_token(token)

    assert token_hash != token
    assert len(token_hash) == 64
    assert token_hash_matches(token, token_hash) is True
    assert token_hash_matches("different-token", token_hash) is False


def test_empty_opaque_token_is_rejected():
    with pytest.raises(ValueError, match="Token cannot be empty"):
        hash_opaque_token("")


def test_opaque_tokens_are_random_and_future_dated():
    first = create_opaque_token(expires_delta=timedelta(minutes=5))
    second = create_opaque_token(expires_delta=timedelta(minutes=5))

    assert first.value != second.value
    assert first.token_hash != second.token_hash
    assert first.expires_at > datetime.now(UTC)


def test_non_positive_opaque_token_expiry_is_rejected():
    with pytest.raises(ValueError, match="Token expiry must be in the future"):
        create_opaque_token(expires_delta=timedelta(0))


def test_refresh_and_reset_tokens_use_configured_expiry():
    now = datetime.now(UTC)
    refresh_token = create_refresh_token()
    reset_token = create_password_reset_token()

    assert refresh_token.expires_at > now
    assert reset_token.expires_at > now
    assert token_hash_matches(refresh_token.value, refresh_token.token_hash)
    assert token_hash_matches(reset_token.value, reset_token.token_hash)


def test_access_token_round_trip():
    user_id = uuid4()
    issued_at = datetime.now(UTC).replace(microsecond=0)
    token = create_access_token(
        user_id=user_id,
        role=UserRole.ADMIN,
        now=issued_at,
    )

    payload = decode_access_token(token)

    assert payload["sub"] == str(user_id)
    assert payload["role"] == UserRole.ADMIN.value
    assert payload["type"] == "access"
    assert payload["jti"]


def test_access_token_has_configured_expiry():
    settings = get_settings()
    issued_at = datetime.now(UTC).replace(microsecond=0)
    token = create_access_token(
        user_id=uuid4(),
        role=UserRole.USER,
        now=issued_at,
    )
    payload = jwt.decode(
        token,
        settings.access_token_secret,
        algorithms=[JWT_ALGORITHM],
    )

    assert payload["exp"] - payload["iat"] == (
        settings.access_token_expiry_minutes * 60
    )


def test_decode_rejects_wrong_secret():
    settings = get_settings()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "role": "user",
            "type": "access",
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        "incorrect-secret-that-is-at-least-32-bytes",
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_decode_rejects_expired_token():
    settings = get_settings()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "role": "user",
            "type": "access",
            "jti": str(uuid4()),
            "iat": now - timedelta(minutes=10),
            "exp": now - timedelta(minutes=5),
        },
        settings.access_token_secret,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_decode_rejects_wrong_token_type():
    settings = get_settings()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": str(uuid4()),
            "role": "user",
            "type": "refresh",
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.access_token_secret,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)


def test_decode_rejects_invalid_role_and_subject():
    settings = get_settings()
    now = datetime.now(UTC)
    token = jwt.encode(
        {
            "sub": "not-a-uuid",
            "role": "superuser",
            "type": "access",
            "jti": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=5),
        },
        settings.access_token_secret,
        algorithm=JWT_ALGORITHM,
    )

    with pytest.raises(InvalidTokenError):
        decode_access_token(token)
