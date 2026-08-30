"""live classroom session + semantic focus

Revision ID: a1c7e4b90d52
Revises: f32f9b107b77
Create Date: 2026-08-30

VIẾT TAY, không autogenerate: DB dev cục bộ đã có bảng do `create_all` của test
tạo ra mà chưa được stamp, nên autogenerate ở đó so với một cây schema không
phải cây thật và sinh ra diff sai. Phép kiểm thật là
`tests/test_migration_drift.py` — nó so migration với MODEL, không với một file
sqlite tình cờ nằm trên máy ai đó.

HAI thay đổi, hai vòng đời khác nhau:

  ① `practice_sessions` mọc thêm TIÊU ĐIỂM NGỮ NGHĨA + TRỢ GIÚP. Mở rộng bảng
     đã có thay vì dựng `student_observation_state` riêng: nó vốn đã là bản ghi
     "một học sinh đang ở đâu trong một bài", và hai bảng cùng khoá
     `(bài, học sinh)` sẽ có hai `updated_at` lệch nhau.

  ② `classroom_sessions` là bảng MỚI — trạng thái điều phối sống trong một
     tiết. Không trộn vào `classrooms` (danh tính bền): trộn thì mỗi lần giáo
     viên bấm một nút là ghi lại chính danh tính lớp.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c7e4b90d52"
down_revision: Union[str, Sequence[str], None] = "f32f9b107b77"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ① Tiêu điểm ngữ nghĩa + trợ giúp cho bản ghi thực hành đã có.
    #
    # `server_default` cho hai cột BOOLEAN/NOT NULL: bảng có thể đã có dữ liệu,
    # và ALTER thêm một cột NOT NULL không mặc định sẽ nổ trên hàng cũ. Cột
    # nullable thì không cần.
    op.add_column("practice_sessions",
                  sa.Column("selected_id", sa.String(length=160), nullable=True))
    op.add_column("practice_sessions",
                  sa.Column("last_action", sa.String(length=32), nullable=True))
    op.add_column("practice_sessions",
                  sa.Column("help_requested", sa.Boolean(), nullable=False,
                            server_default=sa.false()))
    op.add_column("practice_sessions",
                  sa.Column("help_requested_at", sa.DateTime(), nullable=True))

    # ② Phiên dạy — MỘT hàng sống cho mỗi lớp.
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
        # MỘT phiên sống cho mỗi lớp. Hai phiên cùng sống thì không ai trả lời
        # được câu "lớp đang ở đâu" — ràng buộc này là chỗ luật ấy có hiệu lực.
        sa.UniqueConstraint("classroom_id", name="uq_session_per_class"),
    )
    op.create_index(op.f("ix_classroom_sessions_classroom_id"),
                    "classroom_sessions", ["classroom_id"], unique=False)
    op.create_index(op.f("ix_classroom_sessions_teacher_id"),
                    "classroom_sessions", ["teacher_id"], unique=False)
    op.create_index(op.f("ix_classroom_sessions_round_id"),
                    "classroom_sessions", ["round_id"], unique=False)
    op.create_index(op.f("ix_classroom_sessions_assignment_id"),
                    "classroom_sessions", ["assignment_id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_classroom_sessions_assignment_id"),
                  table_name="classroom_sessions")
    op.drop_index(op.f("ix_classroom_sessions_round_id"),
                  table_name="classroom_sessions")
    op.drop_index(op.f("ix_classroom_sessions_teacher_id"),
                  table_name="classroom_sessions")
    op.drop_index(op.f("ix_classroom_sessions_classroom_id"),
                  table_name="classroom_sessions")
    op.drop_table("classroom_sessions")
    op.drop_column("practice_sessions", "help_requested_at")
    op.drop_column("practice_sessions", "help_requested")
    op.drop_column("practice_sessions", "last_action")
    op.drop_column("practice_sessions", "selected_id")
