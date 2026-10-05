from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Enum, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import UserRole, UserStatus, enum_values


if TYPE_CHECKING:
    from app.db.models.system import AuditEvent
    from app.db.models.dataset import Dataset
    from app.db.models.dataset_share import DatasetShare
    from app.db.models.password_reset_token import PasswordResetToken
    from app.db.models.refresh_session import RefreshSession
    from app.db.models.schema_version import SchemaVersion


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    __table_args__ = (
        Index("ix_users_normalized_email", "normalized_email", unique=True),
    )

    email: Mapped[str] = mapped_column(String(320), nullable=False)
    normalized_email: Mapped[str] = mapped_column(String(320), nullable=False)
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=True, validate_strings=True, values_callable=enum_values),
        nullable=False,
        default=UserRole.USER,
        server_default=UserRole.USER.value,
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=True, validate_strings=True, values_callable=enum_values),
        nullable=False,
        default=UserStatus.ACTIVE,
        server_default=UserStatus.ACTIVE.value,
    )
    is_email_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    refresh_sessions: Mapped[list["RefreshSession"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    password_reset_tokens: Mapped[list["PasswordResetToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan", passive_deletes=True
    )
    owned_datasets: Mapped[list["Dataset"]] = relationship(
        back_populates="owner",
        foreign_keys="Dataset.owner_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    dataset_shares: Mapped[list["DatasetShare"]] = relationship(
        back_populates="user",
        foreign_keys="DatasetShare.user_id",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    created_schema_versions: Mapped[list["SchemaVersion"]] = relationship(
        back_populates="created_by_user",
        foreign_keys="SchemaVersion.created_by",
    )
    audit_events: Mapped[list["AuditEvent"]] = relationship(
        back_populates="actor",
        foreign_keys="AuditEvent.actor_id",
    )
