"""add dataset draft schema

Revision ID: 9a4f2c8d1e30
Revises: 7de62977a915
"""
from collections.abc import Sequence
from typing import Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
revision: str = "9a4f2c8d1e30"
down_revision: Union[str, Sequence[str], None] = "7de62977a915"
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.add_column(
        "datasets",
        sa.Column(
            "draft_schema_document",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
        ),
    )

def downgrade() -> None:
    op.drop_column("datasets", "draft_schema_document")
