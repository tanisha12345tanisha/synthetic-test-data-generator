from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import SharePermission, enum_values


if TYPE_CHECKING:
    from app.db.models.dataset import Dataset
    from app.db.models.user import User


class DatasetShare(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "dataset_shares"
    __table_args__ = (
        UniqueConstraint("dataset_id", "user_id", name="uq_dataset_shares_dataset_user"),
        Index("ix_dataset_shares_user_id", "user_id"),
        Index("ix_dataset_shares_dataset_id", "dataset_id"),
    )

    dataset_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    granted_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    permission: Mapped[SharePermission] = mapped_column(
        Enum(SharePermission, name="share_permission", native_enum=True, values_callable=enum_values),
        nullable=False,
    )

    dataset: Mapped["Dataset"] = relationship(back_populates="shares")
    user: Mapped["User"] = relationship(
        back_populates="dataset_shares", foreign_keys=[user_id]
    )
    granted_by_user: Mapped["User"] = relationship(foreign_keys=[granted_by])
