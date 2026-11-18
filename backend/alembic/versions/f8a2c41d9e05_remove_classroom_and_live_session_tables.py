"""remove classroom and live session tables

Drops the five legacy classroom / assignment / practice-session / live-session
tables (`classroom_sessions`, `practice_sessions`, `assignments`,
`class_memberships`, `classrooms`) in foreign-key dependency order while
preserving all user account, auth session, learning history, admin, usage
ledger, and simulation cache tables and rows.

Revision ID: f8a2c41d9e05
Revises: 9c4d8e2b7a10
Create Date: 2026-11-11 22:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "f8a2c41d9e05"
down_revision: Union[str, Sequence[str], None] = "9c4d8e2b7a10"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop classroom, assignment, practice session, and live session tables in FK order."""
    # 1. classroom_sessions (FK -> assignments.id, classrooms.id, users.id)
    with op.batch_alter_table("classroom_sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_classroom_sessions_assignment_id"))
        batch_op.drop_index(batch_op.f("ix_classroom_sessions_round_id"))
        batch_op.drop_index(batch_op.f("ix_classroom_sessions_teacher_id"))
        batch_op.drop_index(batch_op.f("ix_classroom_sessions_classroom_id"))
    op.drop_table("classroom_sessions")

    # 2. practice_sessions (FK -> assignments.id, users.id)
    with op.batch_alter_table("practice_sessions", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_practice_sessions_student_id"))
        batch_op.drop_index(batch_op.f("ix_practice_sessions_assignment_id"))
    op.drop_table("practice_sessions")

    # 3. assignments (FK -> classrooms.id, users.id)
    with op.batch_alter_table("assignments", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_assignments_simulation_id"))
        batch_op.drop_index(batch_op.f("ix_assignments_created_by"))
        batch_op.drop_index(batch_op.f("ix_assignments_classroom_id"))
    op.drop_table("assignments")

    # 4. class_memberships (FK -> classrooms.id, users.id)
    with op.batch_alter_table("class_memberships", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_class_memberships_student_id"))
        batch_op.drop_index(batch_op.f("ix_class_memberships_classroom_id"))
    op.drop_table("class_memberships")

    # 5. classrooms (FK -> users.id)
    with op.batch_alter_table("classrooms", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_classrooms_teacher_id"))
        batch_op.drop_index(batch_op.f("ix_classrooms_join_code"))
    op.drop_table("classrooms")


def downgrade() -> None:
    """Recreate classrooms, class_memberships, assignments, practice_sessions, and classroom_sessions."""
    op.create_table(
        "classrooms",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("join_code", sa.String(length=12), nullable=False),
        sa.Column("code_active", sa.Boolean(), nullable=False),
        sa.Column("archived", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("classrooms", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_classrooms_join_code"), ["join_code"], unique=True)
        batch_op.create_index(batch_op.f("ix_classrooms_teacher_id"), ["teacher_id"], unique=False)

    op.create_table(
        "class_memberships",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("classroom_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("classroom_id", "student_id", name="uq_class_student"),
    )
    with op.batch_alter_table("class_memberships", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_class_memberships_classroom_id"), ["classroom_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_class_memberships_student_id"), ["student_id"], unique=False)

    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("classroom_id", sa.Integer(), nullable=False),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("instruction", sa.Text(), nullable=False),
        sa.Column("simulation_id", sa.String(length=80), nullable=False),
        sa.Column("envelope_json", sa.Text(), nullable=False),
        sa.Column("closed", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("assignments", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_assignments_classroom_id"), ["classroom_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_assignments_created_by"), ["created_by"], unique=False)
        batch_op.create_index(batch_op.f("ix_assignments_simulation_id"), ["simulation_id"], unique=False)

    op.create_table(
        "practice_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=False),
        sa.Column("student_id", sa.Integer(), nullable=False),
        sa.Column("simulation_id", sa.String(length=80), nullable=False),
        sa.Column("cursor", sa.Integer(), nullable=False),
        sa.Column("step_count", sa.Integer(), nullable=False),
        sa.Column("explore_open", sa.Boolean(), nullable=False),
        sa.Column("challenge_open", sa.Boolean(), nullable=False),
        sa.Column("action_count", sa.Integer(), nullable=False),
        sa.Column("commitment_count", sa.Integer(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("selected_id", sa.String(length=160), nullable=True),
        sa.Column("last_action", sa.String(length=32), nullable=True),
        sa.Column("help_requested", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("help_requested_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"]),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("assignment_id", "student_id", name="uq_practice_once"),
    )
    with op.batch_alter_table("practice_sessions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_practice_sessions_assignment_id"), ["assignment_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_practice_sessions_student_id"), ["student_id"], unique=False)

    op.create_table(
        "classroom_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("classroom_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=False),
        sa.Column("round_id", sa.String(length=40), nullable=False),
        sa.Column("cmd_id", sa.Integer(), nullable=False),
        sa.Column("mode", sa.String(length=8), nullable=False),
        sa.Column("assignment_id", sa.Integer(), nullable=True),
        sa.Column("simulation_id", sa.String(length=80), nullable=True),
        sa.Column("current_step", sa.Integer(), nullable=False),
        sa.Column("selected_id", sa.String(length=160), nullable=True),
        sa.Column("isolated_ids", sa.Text(), nullable=False),
        sa.Column("exploded_groups", sa.Text(), nullable=False),
        sa.Column("sync_cmd_id", sa.Integer(), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["assignment_id"], ["assignments.id"]),
        sa.ForeignKeyConstraint(["classroom_id"], ["classrooms.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("classroom_id", name="uq_session_per_class"),
    )
    with op.batch_alter_table("classroom_sessions", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_classroom_sessions_classroom_id"), ["classroom_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_classroom_sessions_teacher_id"), ["teacher_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_classroom_sessions_round_id"), ["round_id"], unique=False)
        batch_op.create_index(batch_op.f("ix_classroom_sessions_assignment_id"), ["assignment_id"], unique=False)
