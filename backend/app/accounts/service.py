"""Thao tác trên tài khoản/phiên — tầng giữa hàm thuần (`policy.py`) và HTTP.

Router chỉ được gọi xuống đây; nó KHÔNG tự viết truy vấn. Nhờ vậy luật "ai đang
gọi" có đúng một nơi để đọc, và test không cần dựng FastAPI mới kiểm được.
"""

from __future__ import annotations

import hmac
import os
import re
import secrets
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, select

from ..persistence.classroom_models import AuthSession, User, UserAccountMeta
from .passwords import hash_password, verify_password
from .policy import Role

_USERNAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{0,63}$")

#: Phiên sống 30 ngày, gia hạn mỗi lần gặp lại. Đủ dài để học sinh không phải
#: đăng nhập lại giữa hai tiết, đủ ngắn để một máy phòng máy không mở mãi.
SESSION_TTL = timedelta(days=30)
SESSION_COOKIE = "algosim_session"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(dt: datetime) -> datetime:
    """SQLite trả `datetime` KHÔNG mang tzinfo; so nó với `now()` có tz là
    TypeError. Chuẩn hoá về UTC-aware trước mọi phép so."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


# ── PHIÊN ────────────────────────────────────────────────────────────────────

def new_session(session, *, user_id: int | None = None) -> AuthSession:
    """Mở phiên mới. Token 32 byte ngẫu nhiên mật mã, không đoán được."""
    row = AuthSession(
        token=secrets.token_urlsafe(32)[:64],
        user_id=user_id,
        guest_trials_used=0,
        expires_at=_now() + SESSION_TTL,
    )
    session.add(row)
    session.flush()
    return row


def load_session(session, token: str | None) -> AuthSession | None:
    """Tra phiên còn hạn. Hết hạn ⇒ `None` (và dọn luôn dòng chết)."""
    if not token:
        return None
    row = session.execute(
        select(AuthSession).where(AuthSession.token == token)
    ).scalar_one_or_none()
    if row is None:
        return None
    if _aware(row.expires_at) <= _now():
        session.delete(row)
        return None
    row.last_seen_at = _now()
    return row


def attach_user(session, auth: AuthSession, user: User) -> None:
    """Gắn danh tính vào phiên ĐANG CÓ thay vì mở phiên mới.

    Vì sao quan trọng: `guest_trials_used` nằm trên chính hàng này. Mở phiên
    mới lúc đăng nhập sẽ vứt bỏ lượt thử đã dùng, và một người chỉ cần đăng
    nhập rồi đăng xuất là lại có lượt mới (đúng lỗ mà bài kiểm tiêm lỗi #1
    canh). Giữ hàng, đổi chủ.
    """
    auth.user_id = user.id
    auth.expires_at = _now() + SESSION_TTL
    auth.last_seen_at = _now()


def end_session(session, token: str | None) -> None:
    """Đăng xuất = XOÁ hàng phiên. Token đục nên thu hồi là tức thì."""
    if not token:
        return
    row = session.execute(
        select(AuthSession).where(AuthSession.token == token)
    ).scalar_one_or_none()
    if row is not None:
        session.delete(row)


def consume_guest_trial(session, auth: AuthSession) -> None:
    """Ghi nhận khách vừa dùng một lượt. Chỉ có nghĩa với phiên chưa đăng nhập."""
    if auth.user_id is None:
        auth.guest_trials_used += 1


# ── TÀI KHOẢN ────────────────────────────────────────────────────────────────

def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def create_user(session, *, email: str, display_name: str, password: str,
                role: Role, must_change_password: bool = False) -> User:
    """Tạo tài khoản. Ném `ValueError` khi email đã tồn tại hoặc mật khẩu yếu."""
    norm = normalize_email(email)
    if not norm or "@" not in norm:
        raise ValueError("Email không hợp lệ.")
    if not (display_name or "").strip():
        raise ValueError("Cần nhập tên hiển thị.")
    existing = session.execute(select(User).where(User.email == norm)).scalar_one_or_none()
    if existing is not None:
        raise ValueError("Email này đã có tài khoản.")
    user = User(
        email=norm,
        display_name=display_name.strip()[:120],
        password_hash=hash_password(password),  # ném WeakPasswordError nếu yếu
        role=role.value,
        must_change_password=must_change_password,
    )
    session.add(user)
    session.flush()
    return user


def configured_admin_username() -> str:
    """Tên đăng nhập hợp lệ cho tài khoản Admin (mặc định `admin`).

    Chỉ là bí danh định danh ánh xạ tới tài khoản `role == "admin"` ĐÃ TỒN TẠI
    trong bảng `users` — KHÔNG BAO GIỜ tự cấp quyền admin từ chuỗi nhập vào.
    """
    raw = os.getenv("ADMIN_USERNAME")
    if raw is None:
        return "admin"
    norm = raw.strip().lower()
    if not norm or "@" in norm or not _USERNAME_RE.match(norm):
        return ""
    return norm


def configured_admin_email() -> str | None:
    """Email Admin tuỳ chọn từ môi trường để gỡ nhập nhằng nếu có nhiều bản ghi admin."""
    raw = os.getenv("ADMIN_EMAIL", "").strip().lower()
    if not raw or "@" not in raw:
        return None
    return raw


def resolve_admin_user(session, *, email: str | None = None) -> User | None:
    """Tìm DUY NHẤT tài khoản `role == 'admin'` hiện có để ánh xạ bí danh `ADMIN_USERNAME`.

    Fail-closed nếu không có admin hoặc nhập nhằng giữa nhiều tài khoản admin mà
    không có `ADMIN_EMAIL` chỉ rõ.
    """
    explicit_email = normalize_email(email) if email else None
    target_email = explicit_email or configured_admin_email()
    if target_email:
        match = session.execute(
            select(User).where(User.role == "admin", User.email == target_email)
        ).scalar_one_or_none()
        if match is not None or explicit_email:
            return match
        # `ADMIN_EMAIL` trong môi trường lệch với email Admin đã lưu (đổi email trong .env mà chưa chạy
        # `manage_admin.py --apply`): vẫn ánh xạ bí danh tới Admin DUY NHẤT thay vì khoá ngoài Admin.

    admins = (
        session.execute(
            select(User).where(User.role == "admin").order_by(User.id.asc())
        )
        .scalars()
        .all()
    )
    if len(admins) == 1:
        return admins[0]
    if len(admins) > 1:
        alias = configured_admin_username()
        local_matches = [
            u for u in admins if u.email and u.email.split("@", 1)[0].lower() == alias
        ]
        if len(local_matches) == 1:
            return local_matches[0]
    return None


def authenticate(
    session,
    *,
    email: str | None = None,
    password: str,
    identifier: str | None = None,
) -> User | None:
    """Xác thực bằng email hoặc `ADMIN_USERNAME` (chỉ ánh xạ tới tài khoản `role == 'admin'`).

    Sai định danh và sai mật khẩu trả CÙNG một kết quả `None` (chống dò tài khoản).
    """
    raw = identifier if identifier is not None else (email or "")
    ident = normalize_email(raw)
    if not ident:
        return None

    user: User | None
    if "@" in ident:
        user = session.execute(
            select(User).where(User.email == ident)
        ).scalar_one_or_none()
    else:
        admin_alias = configured_admin_username()
        if admin_alias and hmac.compare_digest(ident, admin_alias):
            user = resolve_admin_user(session)
        else:
            user = None

    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def upsert_or_rotate_admin_credentials(
    session,
    *,
    password: str,
    email: str | None = None,
    display_name: str | None = None,
    create_if_missing: bool = False,
) -> tuple[User, str, int]:
    """Cập nhật có kiểm soát (hoặc tạo duy nhất nếu chưa có & được phép) tài khoản Admin.

    - Không bao giờ tạo bản ghi Admin trùng lặp khi đã có Admin hiện hữu.
    - Giữ nguyên `id`, lịch sử và các tài khoản khác.
    - Đổi mật khẩu bằng `hash_password` (PBKDF2-HMAC-SHA256) và thu hồi toàn bộ
      phiên đăng nhập cũ của tài khoản Admin đó để tránh phiên cũ tồn tại sau khi xoay khóa.
    Trả `(user, action, revoked_sessions)` với `action` là `"updated"` hoặc `"created"`.
    """
    target_email = normalize_email(email) if email else None
    if target_email is not None and (not target_email or "@" not in target_email):
        raise ValueError("Email Admin không hợp lệ.")

    existing = resolve_admin_user(session, email=target_email)
    if existing is None:
        admins = (
            session.execute(
                select(User).where(User.role == "admin").order_by(User.id.asc())
            )
            .scalars()
            .all()
        )
        if len(admins) == 1:
            existing = admins[0]
        elif len(admins) > 1:
            raise ValueError(
                f"Phát hiện nhiều tài khoản Admin ({len(admins)}); vui lòng truyền đúng --email hoặc ADMIN_EMAIL của tài khoản Admin cần cập nhật."
            )

    if existing is not None:
        if target_email and target_email != existing.email:
            clash = session.execute(
                select(User).where(User.email == target_email, User.id != existing.id)
            ).scalar_one_or_none()
            if clash is not None:
                raise ValueError(f"Email '{target_email}' đang thuộc về một tài khoản khác.")
            existing.email = target_email
            # Token gửi tới địa chỉ cũ không còn giá trị với địa chỉ mới.
            from .tokens import revoke_user_tokens

            revoke_user_tokens(session, existing.id)
        if display_name and display_name.strip():
            existing.display_name = display_name.strip()[:120]
        set_password(session, existing, password)
        revoked = session.execute(
            delete(AuthSession).where(AuthSession.user_id == existing.id)
        ).rowcount or 0
        session.flush()
        return existing, "updated", int(revoked)

    if not create_if_missing:
        raise ValueError(
            "Không tìm thấy tài khoản Admin hiện có trong cơ sở dữ liệu. "
            "Truyền --create-if-missing nếu bạn chủ động muốn khởi tạo một tài khoản Admin mới."
        )

    final_email = target_email or configured_admin_email() or "admin@axo.edu.vn"
    clash = session.execute(
        select(User).where(User.email == final_email)
    ).scalar_one_or_none()
    if clash is not None:
        raise ValueError(
            f"Email '{final_email}' đã tồn tại với vai trò '{clash.role}'. "
            "Không tự động nâng quyền tài khoản có sẵn."
        )

    user = create_user(
        session,
        email=final_email,
        display_name=(display_name or "Quản trị viên Axo").strip()[:120],
        password=password,
        role=Role.TEACHER,
        must_change_password=False,
    )
    user.role = "admin"
    session.flush()
    meta = session.execute(
        select(UserAccountMeta).where(UserAccountMeta.user_id == user.id)
    ).scalar_one_or_none()
    if meta is None:
        session.add(
            UserAccountMeta(
                user_id=user.id,
                status="active",
                school="Hệ thống Axo",
                workplace="Hệ thống Axo",
                subject="Quản trị hệ thống",
            )
        )
        session.flush()
    return user, "created", 0


def set_password(session, user: User, new_password: str) -> None:
    """Đổi mật khẩu và gỡ cờ bắt-buộc-đổi."""
    user.password_hash = hash_password(new_password)
    user.must_change_password = False


def teacher_signup_code() -> str | None:
    """Mã mời tài khoản giáo viên, đọc từ môi trường lúc GỌI (không cache).

    Đọc mỗi lần để test đặt biến rồi gọi là thấy ngay, và để đổi mã lúc vận
    hành không phải khởi động lại tiến trình.
    """
    code = os.getenv("ALGOSIM_TEACHER_SIGNUP_CODE", "").strip()
    return code or None
