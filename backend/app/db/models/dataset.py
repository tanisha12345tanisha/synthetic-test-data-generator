from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import DatasetStatus, DatasetType, InputMode, enum_values


if TYPE_CHECKING:
    from app.db.models.dataset_share import DatasetShare
    from app.db.models.generation import GenerationRun
    from app.db.models.schema_version import SchemaVersion
    from app.db.models.user import User


class Dataset(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "datasets"
    __table_args__ = (
        Index("ix_datasets_owner_id", "owner_id"),
        Index("ix_datasets_owner_name", "owner_id", "name"),
        Index("ix_datasets_status", "status"),
    )

    owner_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    dataset_type: Mapped[DatasetType] = mapped_column(
        Enum(DatasetType, name="dataset_type", native_enum=True, values_callable=enum_values),
        nullable=False,
        default=DatasetType.SINGLE_TABLE,
        server_default=DatasetType.SINGLE_TABLE.value,
    )
    input_mode: Mapped[InputMode] = mapped_column(
        Enum(InputMode, name="input_mode", native_enum=True, values_callable=enum_values),
        nullable=False,
        default=InputMode.MANUAL,
        server_default=InputMode.MANUAL.value,
    )
    status: Mapped[DatasetStatus] = mapped_column(
        Enum(DatasetStatus, name="dataset_status", native_enum=True, values_callable=enum_values),
        nullable=False,
        default=DatasetStatus.DRAFT,
        server_default=DatasetStatus.DRAFT.value,
    )
    current_draft_revision: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default="0"
    )

    owner: Mapped["User"] = relationship(
        back_populates="owned_datasets", foreign_keys=[owner_id]
    )
    shares: Mapped[list["DatasetShare"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan", passive_deletes=True
    )
    schema_versions: Mapped[list["SchemaVersion"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan", passive_deletes=True
    )
    generation_runs: Mapped[list["GenerationRun"]] = relationship(
        back_populates="dataset", cascade="all, delete-orphan", passive_deletes=True
    )
