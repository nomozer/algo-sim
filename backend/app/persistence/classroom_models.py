"""Bảng cho tầng TÀI KHOẢN + LỚP HỌC (M18).

Đặt cạnh `db.py` chứ không nhét vào nó: `db.py` sở hữu ngân hàng bài (cache /
pattern / metric) — một trách nhiệm đã đủ. Cả hai dùng CHUNG `Base` nên Alembic
vẫn thấy một metadata duy nhất; import ở đây chỉ đi MỘT chiều
(`classroom_models` → `db`), không có vòng.

Ranh giới của tầng này (bất biến #27): nó lưu DANH TÍNH, TƯ CÁCH THÀNH VIÊN và
BẰNG CHỨNG THỰC HÀNH CÓ CẤU TRÚC. Nó KHÔNG lưu kết quả đúng/sai do ai đó phán —
engine tất định vẫn là nơi duy nhất biết học sinh trả lời đúng hay chưa.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .db import Base, _now


class User(Base):
    """Tài khoản. `role` là cột SERVER sở hữu — client không bao giờ ghi được.

    `email` là định danh đăng nhập; lưu ở dạng đã chuẩn hoá (thường hoá, cắt
    khoảng trắng) để "An@Truong.edu.vn" và "an@truong.edu.vn" không thành hai
    tài khoản.

    `password_hash` KHÔNG BAO GIỜ rời khỏi tầng này: không lọt vào response,
    không lọt vào log. Khoá bằng `test_auth_api.py`.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(16), index=True)
    #: Tài khoản do giáo viên cấp và học sinh CHƯA đổi mật khẩu lần đầu.
    must_change_password: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AuthSession(Base):
    """Phiên máy chủ — nguồn sự thật DUY NHẤT về "ai đang gọi".

    Cố ý KHÔNG dùng JWT: token đục (opaque) tra trong bảng thì **thu hồi được
    ngay** (đăng xuất là xoá dòng), còn JWT tự chứng thực thì phải dựng thêm
    danh sách đen mới huỷ được — nhiều bộ phận hơn cho cùng một việc.

    Hàng này cũng phục vụ KHÁCH: `user_id` để trống nghĩa là phiên ẩn danh, và
    `guest_trials_used` là nơi đếm lượt dùng thử. Đếm ở SERVER vì một cờ trong
    localStorage thì xoá cache là có lại (bài kiểm tiêm lỗi #1).
    """

    __tablename__ = "auth_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    guest_trials_used: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class LearningHistoryEntry(Base):
    """Lịch sử tự học gắn với từng tài khoản (`user_id`).

    Mỗi hàng là một phiên tự học đã mở (từ Thư viện hoặc từ đề nhập qua Composer).
    Khoá định danh theo bài (`history_key`) kết hợp `user_id` đảm bảo mở lại cùng
    một bài sẽ cập nhật `last_viewed_at`/`last_cursor` chứ không nhân bản bản ghi,
    và dữ liệu của User A tách biệt tuyệt đối với User B.
    """

    __tablename__ = "learning_history_entries"
    __table_args__ = (
        UniqueConstraint("user_id", "history_key", name="uq_learning_history_per_user"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    history_key: Mapped[str] = mapped_column(String(80), index=True)
    sample_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    title: Mapped[str] = mapped_column(String(240))
    simulation_id: Mapped[str] = mapped_column(String(80))
    domain: Mapped[str] = mapped_column(String(40), default="geometry")
    envelope_json: Mapped[str] = mapped_column(Text)
    original_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_cursor: Mapped[int] = mapped_column(Integer, default=0)
    step_count: Mapped[int] = mapped_column(Integer, default=0)
    visual_mode: Mapped[str] = mapped_column(String(8), default="3d")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_viewed_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class UserAccountMeta(Base):
    """Siêu dữ liệu hồ sơ, trạng thái quản trị và hạn mức AI theo ngày của tài khoản (`users.id`)."""

    __tablename__ = "user_account_meta"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, index=True
    )
    status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    school: Mapped[str] = mapped_column(String(200), default="")
    grade: Mapped[str] = mapped_column(String(64), default="")
    class_name: Mapped[str] = mapped_column(String(64), default="")
    workplace: Mapped[str] = mapped_column(String(200), default="")
    subject: Mapped[str] = mapped_column(
        String(120), default="Toán Hình học không gian"
    )
    admin_note: Mapped[str] = mapped_column(Text, default="")
    custom_daily_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)
    token_cap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bonus_quota_today: Mapped[int] = mapped_column(Integer, default=0)
    used_today: Mapped[int] = mapped_column(Integer, default=0)
    usage_date: Mapped[str] = mapped_column(String(16), default="")
    password_reset_requested_at: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AdminSystemSetting(Base):
    """Cấu hình toàn hệ thống lưu bền vững trong SQLite qua các lần khởi động lại backend."""

    __tablename__ = "admin_system_settings"

    key: Mapped[str] = mapped_column(String(64), primary_key=True)
    value_json: Mapped[str] = mapped_column(Text, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AdminAuditLogEntry(Base):
    """Nhật ký thao tác quản trị hệ thống lưu bền vững trong SQLite."""

    __tablename__ = "admin_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    audit_key: Mapped[str] = mapped_column(String(64), index=True)
    timestamp_display: Mapped[str] = mapped_column(String(64))
    time_ts: Mapped[int] = mapped_column(Integer, index=True)
    actor: Mapped[str] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(160))
    target: Mapped[str] = mapped_column(String(200))
    detail: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(32), default="info")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)


class AnalysisUsageLedger(Base):
    """One row per analysis ATTEMPT that limits access (guest trial or daily quota) — the usage ledger.

    Separate from `AdminAnalysisTelemetry` (observational, best effort). The unique `(scope, attempt_key)` makes a
    retry of the same attempt — after a lost response, a 502 or a process restart — reuse its row instead of charging
    again. States: `reserved` (counted before the provider runs) → `charged` (served) | `released` (not served,
    counter refunded). A row left `reserved` means the process stopped before finalising: the attempt stays counted.
    """

    __tablename__ = "analysis_usage_ledger"
    __table_args__ = (UniqueConstraint("scope", "attempt_key", name="uq_analysis_usage_attempt"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(80))            # "user:<users.id>" | "guest:<auth_sessions.id>"
    attempt_key: Mapped[str] = mapped_column(String(128))
    state: Mapped[str] = mapped_column(String(16), index=True)
    usage_date: Mapped[str] = mapped_column(String(16), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class AdminAnalysisTelemetry(Base):
    """Số liệu vận hành thực tế của `/api/analyze` (không lưu prompt hay khóa bí mật)."""

    __tablename__ = "admin_analysis_telemetry"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    role: Mapped[str] = mapped_column(String(32), default="guest")
    outcome: Mapped[str] = mapped_column(String(32), index=True)
    cached: Mapped[bool] = mapped_column(Boolean, default=False)
    model_id: Mapped[str] = mapped_column(String(120), default="")
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    tokens_measured: Mapped[bool] = mapped_column(Boolean, default=False)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    thoughts_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now, index=True)


class AuthToken(Base):
    """Token dùng một lần cho xác minh email và đặt lại mật khẩu.

    Chỉ lưu SHA-256 của token (`token_hash`), không bao giờ lưu token thô. `purpose` tách hai loại token để token
    xác minh không đặt lại được mật khẩu và ngược lại; `email` gắn token với địa chỉ tại lúc phát hành, nên đổi email
    làm token cũ vô hiệu. Thời gian lưu dạng UTC không kèm múi giờ (giống nhau trên SQLite và PostgreSQL).
    """

    __tablename__ = "auth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    purpose: Mapped[str] = mapped_column(String(32), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254))
    created_at: Mapped[datetime] = mapped_column(DateTime)
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class EmailVerification(Base):
    """Bằng chứng tài khoản đã chứng minh quyền sở hữu địa chỉ email.

    Bảng riêng (không thêm cột vào `users`) để CSDL SQLite cũ nhận được bằng `create_all` mà không cần ALTER. Một
    tài khoản được coi là đã xác minh khi `email` ở đây trùng `users.email`; đổi email thì tự động mất xác minh.
    """

    __tablename__ = "email_verifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(254))
    method: Mapped[str] = mapped_column(String(32))
    verified_at: Mapped[datetime] = mapped_column(DateTime)

