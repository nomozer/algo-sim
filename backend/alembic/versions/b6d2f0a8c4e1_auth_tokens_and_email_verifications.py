"""auth tokens and email verifications

Additive tables for account recovery (run `authentication-account-recovery`):

- `auth_tokens`: single-use, purpose-bound tokens (email verification / password reset). Only the SHA-256 digest
  of a token is stored (`token_hash`), never the raw token. Consumption is one atomic conditional UPDATE.
- `email_verifications`: proof that an account controls its email address (valid while `email == users.email`).

No existing table, column or row changes. Downgrade drops only these two new tables.

Revision ID: b6d2f0a8c4e1
Revises: f8a2c41d9e05
Create Date: 2026-11-28 00:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b6d2f0a8c4e1"
down_revision: Union[str, Sequence[str], None] = "f8a2c41d9e05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create `auth_tokens` and `email_verifications` (additive only)."""
    op.create_table(
        "auth_tokens",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("purpose", sa.String(length=32), nullable=False),
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("consumed_at", sa.DateTime(), nullable=True),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("auth_tokens", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_auth_tokens_expires_at"), ["expires_at"], unique=False)
        batch_op.create_index(batch_op.f("ix_auth_tokens_purpose"), ["purpose"], unique=False)
        batch_op.create_index(batch_op.f("ix_auth_tokens_token_hash"), ["token_hash"], unique=True)
        batch_op.create_index(batch_op.f("ix_auth_tokens_user_id"), ["user_id"], unique=False)

    op.create_table(
        "email_verifications",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=254), nullable=False),
        sa.Column("method", sa.String(length=32), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("email_verifications", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_email_verifications_user_id"), ["user_id"], unique=True)


def downgrade() -> None:
    """Drop only the two tables created by this revision."""
    with op.batch_alter_table("email_verifications", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_email_verifications_user_id"))
    op.drop_table("email_verifications")

    with op.batch_alter_table("auth_tokens", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_auth_tokens_user_id"))
        batch_op.drop_index(batch_op.f("ix_auth_tokens_token_hash"))
        batch_op.drop_index(batch_op.f("ix_auth_tokens_purpose"))
        batch_op.drop_index(batch_op.f("ix_auth_tokens_expires_at"))
    op.drop_table("auth_tokens")
