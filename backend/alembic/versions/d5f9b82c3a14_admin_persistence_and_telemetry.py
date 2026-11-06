"""admin persistence and telemetry tables

Revision ID: d5f9b82c3a14
Revises: c4e8a91b2f03
Create Date: 2026-10-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d5f9b82c3a14"
down_revision: Union[str, Sequence[str], None] = "c4e8a91b2f03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema (additive & reversible)."""
    op.create_table(
        "user_account_meta",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=True),
        sa.Column("school", sa.String(length=200), nullable=False),
        sa.Column("grade", sa.String(length=64), nullable=False),
        sa.Column("class_name", sa.String(length=64), nullable=False),
        sa.Column("workplace", sa.String(length=200), nullable=False),
        sa.Column("subject", sa.String(length=120), nullable=False),
        sa.Column("admin_note", sa.Text(), nullable=False),
        sa.Column("custom_daily_limit", sa.Integer(), nullable=True),
        sa.Column("token_cap", sa.Integer(), nullable=True),
        sa.Column("bonus_quota_today", sa.Integer(), nullable=False),
        sa.Column("used_today", sa.Integer(), nullable=False),
        sa.Column("usage_date", sa.String(length=16), nullable=False),
        sa.Column("password_reset_requested_at", sa.String(length=64), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_account_meta_user_id"),
        "user_account_meta",
        ["user_id"],
        unique=True,
    )

    op.create_table(
        "admin_system_settings",
        sa.Column("key", sa.String(length=64), nullable=False),
        sa.Column("value_json", sa.Text(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )

    op.create_table(
        "admin_audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("audit_key", sa.String(length=64), nullable=False),
        sa.Column("timestamp_display", sa.String(length=64), nullable=False),
        sa.Column("time_ts", sa.Integer(), nullable=False),
        sa.Column("actor", sa.String(length=200), nullable=False),
        sa.Column("action", sa.String(length=160), nullable=False),
        sa.Column("target", sa.String(length=200), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_admin_audit_logs_audit_key"),
        "admin_audit_logs",
        ["audit_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_audit_logs_time_ts"),
        "admin_audit_logs",
        ["time_ts"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_audit_logs_created_at"),
        "admin_audit_logs",
        ["created_at"],
        unique=False,
    )

    op.create_table(
        "admin_analysis_telemetry",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("cached", sa.Boolean(), nullable=False),
        sa.Column("model_id", sa.String(length=120), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=False),
        sa.Column("tokens_measured", sa.Boolean(), nullable=False),
        sa.Column("input_tokens", sa.Integer(), nullable=False),
        sa.Column("output_tokens", sa.Integer(), nullable=False),
        sa.Column("thoughts_tokens", sa.Integer(), nullable=False),
        sa.Column("total_tokens", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_admin_analysis_telemetry_user_id"),
        "admin_analysis_telemetry",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_analysis_telemetry_outcome"),
        "admin_analysis_telemetry",
        ["outcome"],
        unique=False,
    )
    op.create_index(
        op.f("ix_admin_analysis_telemetry_created_at"),
        "admin_analysis_telemetry",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_admin_analysis_telemetry_created_at"),
        table_name="admin_analysis_telemetry",
    )
    op.drop_index(
        op.f("ix_admin_analysis_telemetry_outcome"),
        table_name="admin_analysis_telemetry",
    )
    op.drop_index(
        op.f("ix_admin_analysis_telemetry_user_id"),
        table_name="admin_analysis_telemetry",
    )
    op.drop_table("admin_analysis_telemetry")

    op.drop_index(
        op.f("ix_admin_audit_logs_created_at"),
        table_name="admin_audit_logs",
    )
    op.drop_index(
        op.f("ix_admin_audit_logs_time_ts"),
        table_name="admin_audit_logs",
    )
    op.drop_index(
        op.f("ix_admin_audit_logs_audit_key"),
        table_name="admin_audit_logs",
    )
    op.drop_table("admin_audit_logs")

    op.drop_table("admin_system_settings")

    op.drop_index(
        op.f("ix_user_account_meta_user_id"),
        table_name="user_account_meta",
    )
    op.drop_table("user_account_meta")
