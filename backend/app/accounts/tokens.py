"""Token dùng một lần (xác minh email, đặt lại mật khẩu) và trạng thái xác minh email.

Token thô chỉ tồn tại trong thư gửi đi; CSDL giữ SHA-256 của nó. Tiêu thụ token là MỘT câu `UPDATE … WHERE
consumed_at IS NULL AND revoked_at IS NULL AND expires_at > now`: hai yêu cầu đồng thời dùng cùng token thì
nhiều nhất một yêu cầu thấy `rowcount == 1`.
"""

from __future__ import annotations

import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_, select, update

from ..persistence.classroom_models import AuthToken, EmailVerification, User

PURPOSE_EMAIL_VERIFICATION = "email_verification"
PURPOSE_PASSWORD_RESET = "password_reset"
_PURPOSES = frozenset({PURPOSE_EMAIL_VERIFICATION, PURPOSE_PASSWORD_RESET})

#: Giới hạn hợp lệ của TTL (phút) đọc từ môi trường; ngoài khoảng thì kẹp lại, sai cú pháp thì dùng mặc định.
_TTL_BOUNDS = {
    PURPOSE_EMAIL_VERIFICATION: ("EMAIL_VERIFICATION_TOKEN_TTL_MINUTES", 1440, 15, 10080),
    PURPOSE_PASSWORD_RESET: ("PASSWORD_RESET_TOKEN_TTL_MINUTES", 15, 5, 60),
}
#: Token đã dùng/thu hồi/hết hạn được dọn sau khoảng này (giữ ngắn hạn để điều tra sự cố).
_RETENTION = timedelta(days=7)


def utcnow() -> datetime:
    """UTC không kèm múi giờ — cùng một cách so sánh trên SQLite và PostgreSQL `timestamp without time zone`."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def token_ttl(purpose: str) -> timedelta:
    env_name, default, low, high = _TTL_BOUNDS[purpose]
    raw = os.getenv(env_name, "").strip()
    try:
        minutes = int(raw) if raw else default
    except ValueError:
        minutes = default
    return timedelta(minutes=min(high, max(low, minutes)))


def digest(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def issue_token(session, *, user: User, purpose: str) -> str:
    """Phát hành token mới (32 byte ngẫu nhiên) và thu hồi các token còn hiệu lực cùng mục đích của tài khoản."""
    if purpose not in _PURPOSES:
        raise ValueError("unknown token purpose")
    now = utcnow()
    revoke_user_tokens(session, user.id, purpose=purpose, now=now)
    session.execute(
        delete(AuthToken).where(
            or_(AuthToken.expires_at <= now - _RETENTION, AuthToken.consumed_at <= now - _RETENTION,
                AuthToken.revoked_at <= now - _RETENTION)
        )
    )
    raw = secrets.token_urlsafe(32)
    session.add(
        AuthToken(
            user_id=user.id,
            purpose=purpose,
            token_hash=digest(raw),
            email=user.email,
            created_at=now,
            expires_at=now + token_ttl(purpose),
        )
    )
    session.flush()
    return raw


def consume_token(session, raw_token: str, *, purpose: str) -> AuthToken | None:
    """Tiêu thụ nguyên tử: trả bản ghi nếu yêu cầu này là yêu cầu DUY NHẤT tiêu thụ được token còn hiệu lực."""
    raw = (raw_token or "").strip()
    if not raw or len(raw) > 256 or purpose not in _PURPOSES:
        return None
    token_hash = digest(raw)
    now = utcnow()
    result = session.execute(
        update(AuthToken)
        .where(
            AuthToken.token_hash == token_hash,
            AuthToken.purpose == purpose,
            AuthToken.consumed_at.is_(None),
            AuthToken.revoked_at.is_(None),
            AuthToken.expires_at > now,
        )
        .values(consumed_at=now)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        return None
    return session.execute(select(AuthToken).where(AuthToken.token_hash == token_hash)).scalar_one()


def revoke_user_tokens(session, user_id: int, *, purpose: str | None = None, now: datetime | None = None) -> int:
    stmt = update(AuthToken).where(
        AuthToken.user_id == user_id,
        AuthToken.consumed_at.is_(None),
        AuthToken.revoked_at.is_(None),
    )
    if purpose is not None:
        stmt = stmt.where(AuthToken.purpose == purpose)
    result = session.execute(stmt.values(revoked_at=now or utcnow()).execution_options(synchronize_session=False))
    return int(result.rowcount or 0)


def delete_user_auth_records(session, user_id: int) -> None:
    """Gỡ token và bằng chứng xác minh trước khi xoá tài khoản (khoá ngoại tới `users`)."""
    session.execute(delete(AuthToken).where(AuthToken.user_id == user_id))
    session.execute(delete(EmailVerification).where(EmailVerification.user_id == user_id))


def is_email_verified(session, user: User) -> bool:
    row = session.execute(
        select(EmailVerification).where(EmailVerification.user_id == user.id)
    ).scalar_one_or_none()
    return bool(row is not None and row.email == user.email)


def mark_email_verified(session, user: User, *, method: str) -> None:
    row = session.execute(
        select(EmailVerification).where(EmailVerification.user_id == user.id)
    ).scalar_one_or_none()
    now = utcnow()
    if row is None:
        session.add(EmailVerification(user_id=user.id, email=user.email, method=method[:32], verified_at=now))
    else:
        row.email = user.email
        row.method = method[:32]
        row.verified_at = now
    session.flush()
