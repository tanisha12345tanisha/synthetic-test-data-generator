"""create initial application tables

Revision ID: 7de62977a915
Revises:
Create Date: 2026-10-05 11:51:09.261084
"""

from collections.abc import Sequence
from typing import Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "7de62977a915"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply this migration."""
    op.create_table(
        "users",
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("normalized_email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=200), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column(
            "role",
            sa.Enum("user", "admin", name="user_role"),
            server_default="user",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("active", "disabled", name="user_status"),
            server_default="active",
            nullable=False,
        ),
        sa.Column(
            "is_email_verified",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
    )
    op.create_index(
        "ix_users_normalized_email",
        "users",
        ["normalized_email"],
        unique=True,
    )

    op.create_table(
        "audit_events",
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(length=150), nullable=False),
        sa.Column("target_type", sa.String(length=100), nullable=True),
        sa.Column("target_id", sa.UUID(), nullable=True),
        sa.Column(
            "result",
            sa.Enum("success", "failure", name="audit_result"),
            nullable=False,
        ),
        sa.Column(
            "safe_metadata",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_id"],
            ["users.id"],
            name=op.f("fk_audit_events_actor_id_users"),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_audit_events")),
    )
    op.create_index(
        "ix_audit_events_actor_id",
        "audit_events",
        ["actor_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_target",
        "audit_events",
        ["target_type", "target_id"],
        unique=False,
    )
    op.create_index(
        "ix_audit_events_timestamp",
        "audit_events",
        ["timestamp"],
        unique=False,
    )

    op.create_table(
        "datasets",
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "dataset_type",
            sa.Enum(
                "single_table",
                "connected_tables",
                name="dataset_type",
            ),
            server_default="single_table",
            nullable=False,
        ),
        sa.Column(
            "input_mode",
            sa.Enum(
                "manual",
                "csv",
                "database",
                "json",
                "template",
                name="input_mode",
            ),
            server_default="manual",
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.Enum("draft", "active", "archived", name="dataset_status"),
            server_default="draft",
            nullable=False,
        ),
        sa.Column(
            "current_draft_revision",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            name=op.f("fk_datasets_owner_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_datasets")),
    )
    op.create_index("ix_datasets_owner_id", "datasets", ["owner_id"], unique=False)
    op.create_index(
        "ix_datasets_owner_name",
        "datasets",
        ["owner_id", "name"],
        unique=False,
    )
    op.create_index("ix_datasets_status", "datasets", ["status"], unique=False)

    op.create_table(
        "password_reset_tokens",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("requested_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_password_reset_tokens_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_password_reset_tokens")),
    )
    op.create_index(
        "ix_password_reset_tokens_expires_at",
        "password_reset_tokens",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_password_reset_tokens_token_hash",
        "password_reset_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_password_reset_tokens_user_id",
        "password_reset_tokens",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "refresh_sessions",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=512), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("client_ip", sa.String(length=64), nullable=True),
        sa.Column("user_agent", sa.String(length=512), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_refresh_sessions_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_sessions")),
    )
    op.create_index(
        "ix_refresh_sessions_expires_at",
        "refresh_sessions",
        ["expires_at"],
        unique=False,
    )
    op.create_index(
        "ix_refresh_sessions_token_hash",
        "refresh_sessions",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_refresh_sessions_user_id",
        "refresh_sessions",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "system_limits",
        sa.Column("key", sa.String(length=100), nullable=False),
        sa.Column(
            "value",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("effective_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_by", sa.UUID(), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["updated_by"],
            ["users.id"],
            name=op.f("fk_system_limits_updated_by_users"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_system_limits")),
        sa.UniqueConstraint("key", name=op.f("uq_system_limits_key")),
    )

    op.create_table(
        "dataset_shares",
        sa.Column("dataset_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("granted_by", sa.UUID(), nullable=False),
        sa.Column(
            "permission",
            sa.Enum("viewer", "editor", name="share_permission"),
            nullable=False,
        ),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_dataset_shares_dataset_id_datasets"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"],
            ["users.id"],
            name=op.f("fk_dataset_shares_granted_by_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name=op.f("fk_dataset_shares_user_id_users"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dataset_shares")),
        sa.UniqueConstraint(
            "dataset_id",
            "user_id",
            name="uq_dataset_shares_dataset_user",
        ),
    )
    op.create_index(
        "ix_dataset_shares_dataset_id",
        "dataset_shares",
        ["dataset_id"],
        unique=False,
    )
    op.create_index(
        "ix_dataset_shares_user_id",
        "dataset_shares",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "schema_versions",
        sa.Column("dataset_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column(
            "trigger",
            sa.Enum(
                "manual_save",
                "generation",
                "import",
                "restore",
                name="schema_version_trigger",
            ),
            nullable=False,
        ),
        sa.Column(
            "schema_document",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("restored_from_version_id", sa.UUID(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            name=op.f("fk_schema_versions_created_by_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_schema_versions_dataset_id_datasets"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["restored_from_version_id"],
            ["schema_versions.id"],
            name=op.f(
                "fk_schema_versions_restored_from_version_id_schema_versions"
            ),
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_schema_versions")),
        sa.UniqueConstraint(
            "dataset_id",
            "version_number",
            name="uq_schema_versions_dataset_version",
        ),
    )
    op.create_index(
        "ix_schema_versions_dataset_id",
        "schema_versions",
        ["dataset_id"],
        unique=False,
    )

    op.create_table(
        "generation_runs",
        sa.Column("dataset_id", sa.UUID(), nullable=False),
        sa.Column("schema_version_id", sa.UUID(), nullable=False),
        sa.Column("requested_by", sa.UUID(), nullable=False),
        sa.Column("seed", sa.BigInteger(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "queued",
                "running",
                "completed",
                "failed",
                "cancelled",
                name="generation_status",
            ),
            server_default="queued",
            nullable=False,
        ),
        sa.Column(
            "progress_percent",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("requested_row_total", sa.Integer(), nullable=False),
        sa.Column(
            "generated_row_total",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("failure_code", sa.String(length=100), nullable=True),
        sa.Column("failure_message", sa.Text(), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["dataset_id"],
            ["datasets.id"],
            name=op.f("fk_generation_runs_dataset_id_datasets"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["requested_by"],
            ["users.id"],
            name=op.f("fk_generation_runs_requested_by_users"),
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["schema_version_id"],
            ["schema_versions.id"],
            name=op.f("fk_generation_runs_schema_version_id_schema_versions"),
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generation_runs")),
    )
    op.create_index(
        "ix_generation_runs_dataset_id",
        "generation_runs",
        ["dataset_id"],
        unique=False,
    )
    op.create_index(
        "ix_generation_runs_requested_by",
        "generation_runs",
        ["requested_by"],
        unique=False,
    )
    op.create_index(
        "ix_generation_runs_status",
        "generation_runs",
        ["status"],
        unique=False,
    )

    op.create_table(
        "generation_outputs",
        sa.Column("generation_id", sa.UUID(), nullable=False),
        sa.Column("object_path", sa.String(length=1024), nullable=False),
        sa.Column(
            "output_format",
            sa.Enum("csv", "json", "psv", "zip", name="output_format"),
            nullable=False,
        ),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("checksum_sha256", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["generation_id"],
            ["generation_runs.id"],
            name=op.f(
                "fk_generation_outputs_generation_id_generation_runs"
            ),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_generation_outputs")),
    )
    op.create_index(
        "ix_generation_outputs_generation_id",
        "generation_outputs",
        ["generation_id"],
        unique=False,
    )

    op.create_table(
        "quality_reports",
        sa.Column("generation_id", sa.UUID(), nullable=False),
        sa.Column(
            "report_document",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["generation_id"],
            ["generation_runs.id"],
            name=op.f("fk_quality_reports_generation_id_generation_runs"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_quality_reports")),
        sa.UniqueConstraint(
            "generation_id",
            name=op.f("uq_quality_reports_generation_id"),
        ),
    )


def downgrade() -> None:
    """Reverse this migration."""
    op.drop_table("quality_reports")

    op.drop_index(
        "ix_generation_outputs_generation_id",
        table_name="generation_outputs",
    )
    op.drop_table("generation_outputs")

    op.drop_index("ix_generation_runs_status", table_name="generation_runs")
    op.drop_index(
        "ix_generation_runs_requested_by",
        table_name="generation_runs",
    )
    op.drop_index(
        "ix_generation_runs_dataset_id",
        table_name="generation_runs",
    )
    op.drop_table("generation_runs")

    op.drop_index(
        "ix_schema_versions_dataset_id",
        table_name="schema_versions",
    )
    op.drop_table("schema_versions")

    op.drop_index(
        "ix_dataset_shares_user_id",
        table_name="dataset_shares",
    )
    op.drop_index(
        "ix_dataset_shares_dataset_id",
        table_name="dataset_shares",
    )
    op.drop_table("dataset_shares")

    op.drop_table("system_limits")

    op.drop_index(
        "ix_refresh_sessions_user_id",
        table_name="refresh_sessions",
    )
    op.drop_index(
        "ix_refresh_sessions_token_hash",
        table_name="refresh_sessions",
    )
    op.drop_index(
        "ix_refresh_sessions_expires_at",
        table_name="refresh_sessions",
    )
    op.drop_table("refresh_sessions")

    op.drop_index(
        "ix_password_reset_tokens_user_id",
        table_name="password_reset_tokens",
    )
    op.drop_index(
        "ix_password_reset_tokens_token_hash",
        table_name="password_reset_tokens",
    )
    op.drop_index(
        "ix_password_reset_tokens_expires_at",
        table_name="password_reset_tokens",
    )
    op.drop_table("password_reset_tokens")

    op.drop_index("ix_datasets_status", table_name="datasets")
    op.drop_index("ix_datasets_owner_name", table_name="datasets")
    op.drop_index("ix_datasets_owner_id", table_name="datasets")
    op.drop_table("datasets")

    op.drop_index("ix_audit_events_timestamp", table_name="audit_events")
    op.drop_index("ix_audit_events_target", table_name="audit_events")
    op.drop_index("ix_audit_events_actor_id", table_name="audit_events")
    op.drop_table("audit_events")

    op.drop_index("ix_users_normalized_email", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()

    enum_names = [
        "output_format",
        "generation_status",
        "schema_version_trigger",
        "share_permission",
        "dataset_status",
        "input_mode",
        "dataset_type",
        "audit_result",
        "user_status",
        "user_role",
    ]

    for enum_name in enum_names:
        postgresql.ENUM(name=enum_name).drop(
            bind,
            checkfirst=True,
        )
