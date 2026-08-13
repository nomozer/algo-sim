"""Thao tác trên tài khoản/phiên — tầng giữa hàm thuần (`policy.py`) và HTTP.

Router chỉ được gọi xuống đây; nó KHÔNG tự viết truy vấn. Nhờ vậy luật "ai đang
gọi" có đúng một nơi để đọc, và test không cần dựng FastAPI mới kiểm được.
"""

from __future__ import annotations

import os
import secrets
import string
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from ..persistence.classroom_models import AuthSession, ClassMembership, Classroom, User
from .passwords import hash_password, verify_password
from .policy import Role

#: Phiên sống 30 ngày, gia hạn mỗi lần gặp lại. Đủ dài để học sinh không phải
#: đăng nhập lại giữa hai tiết, đủ ngắn để một máy phòng máy không mở mãi.
SESSION_TTL = timedelta(days=30)
SESSION_COOKIE = "algosim_session"

#: Bảng chữ cái của MÃ LỚP: bỏ 0/O/1/I/L để đọc-đọc-lại trên bảng không nhầm.
#: Học sinh gõ tay mã này, nên cặp ký tự dễ lẫn là lỗi dùng thật, không phải lý thuyết.
_CODE_ALPHABET = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 6


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


def authenticate(session, *, email: str, password: str) -> User | None:
    """Xác thực. Sai email và sai mật khẩu trả CÙNG một kết quả `None`.

    Có chủ ý: phân biệt hai ca cho phép người ngoài dò xem email nào có tài
    khoản. Câu lỗi hiển thị cũng phải chung một chữ.
    """
    user = session.execute(
        select(User).where(User.email == normalize_email(email))
    ).scalar_one_or_none()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


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


# ── LỚP ──────────────────────────────────────────────────────────────────────

def generate_join_code(session) -> str:
    """Mã lớp duy nhất. Thử lại khi đụng — không gắn số thứ tự lớp vào mã.

    Vì sao không dùng id lớp: mã đoán được thì bất kỳ ai cũng vào được lớp bất
    kỳ. Ngẫu nhiên mật mã trong bảng chữ cái không-mơ-hồ.
    """
    for _ in range(20):
        code = "".join(secrets.choice(_CODE_ALPHABET) for _ in range(_CODE_LENGTH))
        clash = session.execute(
            select(Classroom).where(Classroom.join_code == code)
        ).scalar_one_or_none()
        if clash is None:
            return code
    raise RuntimeError("Không sinh được mã lớp duy nhất.")


def normalize_join_code(raw: str) -> str:
    """Học sinh gõ mã: bỏ khoảng trắng, hoa hết. "abc 123" ≡ "ABC123"."""
    return "".join((raw or "").split()).upper()


def member_ids(session, classroom_id: int) -> frozenset[int]:
    rows = session.execute(
        select(ClassMembership.student_id).where(ClassMembership.classroom_id == classroom_id)
    ).scalars().all()
    return frozenset(rows)
