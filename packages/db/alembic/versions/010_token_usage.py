"""Token usage tracking

Revision ID: 010_token_usage
Revises: 009_google_oauth
Create Date: 2026-06-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_token_usage"
down_revision: str | None = "009_google_oauth"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "llm_usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("turn_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("agent_name", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["task_id"], ["tasks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_llm_usage_user_id", "llm_usage_events", ["user_id"])
    op.create_index("ix_llm_usage_task_id", "llm_usage_events", ["task_id"])
    op.create_index("ix_llm_usage_turn_id", "llm_usage_events", ["turn_id"])
    op.create_index("ix_llm_usage_user_created", "llm_usage_events", ["user_id", "created_at"])

    op.add_column(
        "users",
        sa.Column("total_input_tokens", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("total_output_tokens", sa.BigInteger(), nullable=False, server_default="0"),
    )

    op.add_column(
        "tasks",
        sa.Column("total_input_tokens", sa.BigInteger(), nullable=False, server_default="0"),
    )
    op.add_column(
        "tasks",
        sa.Column("total_output_tokens", sa.BigInteger(), nullable=False, server_default="0"),
    )

    op.add_column("messages", sa.Column("output_tokens", sa.Integer(), nullable=True))
    op.add_column("messages", sa.Column("turn_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.create_index("ix_messages_turn_id", "messages", ["turn_id"])


def downgrade() -> None:
    op.drop_index("ix_messages_turn_id", table_name="messages")
    op.drop_column("messages", "turn_id")
    op.drop_column("messages", "output_tokens")

    op.drop_column("tasks", "total_output_tokens")
    op.drop_column("tasks", "total_input_tokens")

    op.drop_column("users", "total_output_tokens")
    op.drop_column("users", "total_input_tokens")

    op.drop_index("ix_llm_usage_user_created", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_turn_id", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_task_id", table_name="llm_usage_events")
    op.drop_index("ix_llm_usage_user_id", table_name="llm_usage_events")
    op.drop_table("llm_usage_events")
