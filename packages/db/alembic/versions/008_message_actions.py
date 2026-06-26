"""Add message actions table

Revision ID: 008_message_actions
Revises: 007_file_versions
Create Date: 2026-06-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_message_actions"
down_revision: str | None = "007_file_versions"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "message_actions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("value", sa.String(length=256), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_message_actions_task_created", "message_actions", ["task_id", "created_at"])
    op.create_index(
        "ix_message_actions_message_user_action",
        "message_actions",
        ["message_id", "user_id", "action"],
    )


def downgrade() -> None:
    op.drop_index("ix_message_actions_message_user_action", table_name="message_actions")
    op.drop_index("ix_message_actions_task_created", table_name="message_actions")
    op.drop_table("message_actions")
