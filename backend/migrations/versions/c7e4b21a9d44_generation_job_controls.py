"""generation job controls
Revision ID: c7e4b21a9d44
Revises: 9a4f2c8d1e30
"""
from alembic import op
import sqlalchemy as sa
revision="c7e4b21a9d44"
down_revision="9a4f2c8d1e30"
branch_labels=None
depends_on=None

def upgrade():
    op.add_column("generation_runs",sa.Column("idempotency_key",sa.String(128),nullable=True))
    op.add_column("generation_runs",sa.Column("current_phase",sa.String(50),server_default="queued",nullable=False))
    op.add_column("generation_runs",sa.Column("cancel_requested",sa.Boolean(),server_default=sa.false(),nullable=False))
    op.execute("UPDATE generation_runs SET idempotency_key = id::text WHERE idempotency_key IS NULL")
    op.alter_column("generation_runs","idempotency_key",nullable=False)
    op.create_unique_constraint("uq_generation_request_idempotency","generation_runs",["requested_by","idempotency_key"])

def downgrade():
    op.drop_constraint("uq_generation_request_idempotency","generation_runs",type_="unique")
    op.drop_column("generation_runs","cancel_requested")
    op.drop_column("generation_runs","current_phase")
    op.drop_column("generation_runs","idempotency_key")
