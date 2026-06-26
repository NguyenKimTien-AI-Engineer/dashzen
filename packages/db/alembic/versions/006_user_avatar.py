"""Add user avatar storage key

Revision ID: 006_user_avatar
Revises: 005_projects
Create Date: 2026-06-24

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "006_user_avatar"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("avatar_key", sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "avatar_key")
