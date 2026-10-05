from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
)
from sqlalchemy.dialects.postgresql import (
    JSONB,
    UUID as PostgreSQLUUID,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.db.base import (
    Base,
    TimestampMixin,
    UUIDPrimaryKeyMixin,
)
from app.db.models.enums import (
    AuditResult,
    enum_values,
)


if TYPE_CHECKING:
    from app.db.models.user import User


class SystemLimit(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "system_limits"

    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )

    value: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    unit: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    effective_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    updated_by: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
    )

    updated_by_user: Mapped["User"] = relationship(
        foreign_keys=[updated_by],
    )


class AuditEvent(
    UUIDPrimaryKeyMixin,
    Base,
):
    __tablename__ = "audit_events"

    __table_args__ = (
        Index(
            "ix_audit_events_actor_id",
            "actor_id",
        ),
        Index(
            "ix_audit_events_target",
            "target_type",
            "target_id",
        ),
        Index(
            "ix_audit_events_timestamp",
            "timestamp",
        ),
    )

    actor_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    action: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    target_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    target_id: Mapped[UUID | None] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        nullable=True,
    )

    result: Mapped[AuditResult] = mapped_column(
        Enum(
            AuditResult,
            name="audit_result",
            native_enum=True,
            values_callable=enum_values,
        ),
        nullable=False,
    )

    safe_metadata: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    actor: Mapped["User | None"] = relationship(
        back_populates="audit_events",
        foreign_keys=[actor_id],
    )