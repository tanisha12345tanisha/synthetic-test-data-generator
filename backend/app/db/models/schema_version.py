from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import SchemaVersionTrigger, enum_values


if TYPE_CHECKING:
    from app.db.models.dataset import Dataset
    from app.db.models.generation import GenerationRun
    from app.db.models.user import User


class SchemaVersion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "schema_versions"
    __table_args__ = (
        UniqueConstraint("dataset_id", "version_number", name="uq_schema_versions_dataset_version"),
        Index("ix_schema_versions_dataset_id", "dataset_id"),
    )

    dataset_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    trigger: Mapped[SchemaVersionTrigger] = mapped_column(
        Enum(SchemaVersionTrigger, name="schema_version_trigger", native_enum=True, values_callable=enum_values),
        nullable=False,
    )
    schema_document: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
    )
    restored_from_version_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("schema_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    dataset: Mapped["Dataset"] = relationship(back_populates="schema_versions")
    created_by_user: Mapped["User"] = relationship(
        back_populates="created_schema_versions", foreign_keys=[created_by]
    )
    restored_from_version: Mapped["SchemaVersion | None"] = relationship(
        remote_side="SchemaVersion.id", foreign_keys=[restored_from_version_id]
    )
    generation_runs: Mapped[list["GenerationRun"]] = relationship(
        back_populates="schema_version"
    )
