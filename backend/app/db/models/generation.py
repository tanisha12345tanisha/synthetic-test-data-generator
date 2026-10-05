from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Enum, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from app.db.models.enums import GenerationStatus, OutputFormat, enum_values


if TYPE_CHECKING:
    from app.db.models.dataset import Dataset
    from app.db.models.schema_version import SchemaVersion
    from app.db.models.user import User


class GenerationRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generation_runs"
    __table_args__ = (
        Index("ix_generation_runs_dataset_id", "dataset_id"),
        Index("ix_generation_runs_requested_by", "requested_by"),
        Index("ix_generation_runs_status", "status"),
    )

    dataset_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False
    )
    schema_version_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("schema_versions.id", ondelete="RESTRICT"), nullable=False
    )
    requested_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    seed: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    status: Mapped[GenerationStatus] = mapped_column(
        Enum(GenerationStatus, name="generation_status", native_enum=True, values_callable=enum_values),
        nullable=False,
        default=GenerationStatus.QUEUED,
        server_default=GenerationStatus.QUEUED.value,
    )
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    requested_row_total: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_row_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    failure_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    dataset: Mapped["Dataset"] = relationship(back_populates="generation_runs")
    schema_version: Mapped["SchemaVersion"] = relationship(back_populates="generation_runs")
    requested_by_user: Mapped["User"] = relationship(foreign_keys=[requested_by])
    outputs: Mapped[list["GenerationOutput"]] = relationship(
        back_populates="generation_run", cascade="all, delete-orphan", passive_deletes=True
    )
    quality_report: Mapped["QualityReport | None"] = relationship(
        back_populates="generation_run", cascade="all, delete-orphan", passive_deletes=True, uselist=False
    )


class GenerationOutput(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "generation_outputs"
    __table_args__ = (Index("ix_generation_outputs_generation_id", "generation_id"),)

    generation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True), ForeignKey("generation_runs.id", ondelete="CASCADE"), nullable=False
    )
    object_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    output_format: Mapped[OutputFormat] = mapped_column(
        Enum(OutputFormat, name="output_format", native_enum=True, values_callable=enum_values), nullable=False
    )
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    checksum_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    generation_run: Mapped["GenerationRun"] = relationship(back_populates="outputs")


class QualityReport(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "quality_reports"

    generation_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("generation_runs.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    report_document: Mapped[dict] = mapped_column(JSONB, nullable=False)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)

    generation_run: Mapped["GenerationRun"] = relationship(back_populates="quality_report")
