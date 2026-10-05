from sqlalchemy import Enum, inspect

from app.db.base import Base
from app.db.models import (
    PasswordResetToken,
    RefreshSession,
    User,
    UserRole,
    UserStatus,
)


def get_column(model, column_name):
    mapper = inspect(model)
    return mapper.columns[column_name]


def test_identity_tables_are_registered():
    expected_tables = {
        "users",
        "refresh_sessions",
        "password_reset_tokens",
    }
    assert expected_tables.issubset(Base.metadata.tables.keys())


def test_user_table_name():
    assert User.__tablename__ == "users"


def test_user_email_columns_are_required():
    email_column = get_column(User, "email")
    normalized_email_column = get_column(User, "normalized_email")
    assert email_column.nullable is False
    assert normalized_email_column.nullable is False
    assert email_column.type.length == 320
    assert normalized_email_column.type.length == 320


def test_user_normalized_email_has_unique_index():
    normalized_email_index = next(
        index
        for index in User.__table__.indexes
        if index.name == "ix_users_normalized_email"
    )
    assert normalized_email_index.unique is True


def test_user_password_hash_is_required():
    password_hash_column = get_column(User, "password_hash")
    assert password_hash_column.nullable is False
    assert password_hash_column.type.length == 512


def test_user_role_is_enum():
    role_column = get_column(User, "role")
    assert isinstance(role_column.type, Enum)
    assert set(role_column.type.enums) == {
        UserRole.USER.value,
        UserRole.ADMIN.value,
    }


def test_user_status_is_enum():
    status_column = get_column(User, "status")
    assert isinstance(status_column.type, Enum)
    assert set(status_column.type.enums) == {
        UserStatus.ACTIVE.value,
        UserStatus.DISABLED.value,
    }


def test_user_email_verification_defaults_false():
    verification_column = get_column(User, "is_email_verified")
    assert verification_column.nullable is False
    assert verification_column.server_default is not None


def test_refresh_session_references_user():
    user_id_column = get_column(RefreshSession, "user_id")
    foreign_key = next(iter(user_id_column.foreign_keys))
    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"


def test_refresh_token_hash_has_unique_index():
    token_index = next(
        index
        for index in RefreshSession.__table__.indexes
        if index.name == "ix_refresh_sessions_token_hash"
    )
    assert token_index.unique is True


def test_password_reset_token_references_user():
    user_id_column = get_column(PasswordResetToken, "user_id")
    foreign_key = next(iter(user_id_column.foreign_keys))
    assert foreign_key.target_fullname == "users.id"
    assert foreign_key.ondelete == "CASCADE"


def test_password_reset_hash_has_unique_index():
    token_index = next(
        index
        for index in PasswordResetToken.__table__.indexes
        if index.name == "ix_password_reset_tokens_token_hash"
    )
    assert token_index.unique is True


def test_refresh_session_revocation_property():
    session = RefreshSession()
    assert session.is_revoked is False


def test_password_reset_used_property():
    reset_token = PasswordResetToken()
    assert reset_token.is_used is False


def test_user_relationships_are_configured():
    relationship_names = {
        relationship.key
        for relationship in inspect(User).relationships
    }
    assert {
        "refresh_sessions",
        "password_reset_tokens",
        "owned_datasets",
        "dataset_shares",
        "created_schema_versions",
        "audit_events",
    }.issubset(relationship_names)
