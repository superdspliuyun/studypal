"""analytics-deploy: learning_events table

Revision ID: 0003_learning_event
Revises: 0002_ai_chat
Create Date: 2026-09-19

"""
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "0003_learning_event"
down_revision: str | None = "0002_ai_chat"
branch_labels: str | None = None
depends_on: str | None = None


def upgrade() -> None:
    op.create_table(
        "learning_events",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "kind", sa.String(length=32), nullable=False, server_default="chat"
        ),
        sa.Column("minutes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_learning_events_user_id",
            ondelete="CASCADE",
        ),
    )
    op.create_index("ix_learning_events_user_id", "learning_events", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_learning_events_user_id", table_name="learning_events")
    op.drop_table("learning_events")