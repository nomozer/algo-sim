"""learning history entries per user

Revision ID: c4e8a91b2f03
Revises: a1c7e4b90d52
Create Date: 2026-10-27
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e8a91b2f03"
down_revision: Union[str, Sequence[str], None] = "a1c7e4b90d52"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "learning_history_entries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("history_key", sa.String(length=80), nullable=False),
        sa.Column("sample_id", sa.String(length=80), nullable=True),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("simulation_id", sa.String(length=80), nullable=False),
        sa.Column("domain", sa.String(length=40), nullable=False),
        sa.Column("envelope_json", sa.Text(), nullable=False),
        sa.Column("original_input", sa.Text(), nullable=True),
        sa.Column("last_cursor", sa.Integer(), nullable=False),
        sa.Column("step_count", sa.Integer(), nullable=False),
        sa.Column("visual_mode", sa.String(length=8), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_viewed_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "history_key", name="uq_learning_history_per_user"),
    )
    op.create_index(
        op.f("ix_learning_history_entries_user_id"),
        "learning_history_entries",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_learning_history_entries_history_key"),
        "learning_history_entries",
        ["history_key"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_learning_history_entries_history_key"),
        table_name="learning_history_entries",
    )
    op.drop_index(
        op.f("ix_learning_history_entries_user_id"),
        table_name="learning_history_entries",
    )
    op.drop_table("learning_history_entries")
