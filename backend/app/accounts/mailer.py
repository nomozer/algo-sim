"""Gửi thư giao dịch: xác minh email, đặt lại mật khẩu, thông báo đổi mật khẩu.

Nhà cung cấp chính thức là Resend (REST `POST https://api.resend.com/emails`, gọi bằng `httpx` có sẵn — không thêm
SDK). SMTP cũ (`ALGOSIM_SMTP_*`) vẫn được giữ cho cấu hình đã có. Không có cấu hình hợp lệ thì tính năng ở trạng
thái KHÔNG KHẢ DỤNG: không gửi, không giả vờ đã gửi, không chặn đăng nhập hay phân tích hình học.

Kết quả gửi chỉ có nghĩa "nhà cung cấp đã NHẬN yêu cầu" (`accepted`), không phải "người nhận đã nhận thư".
Nhật ký không bao giờ chứa khoá API, token, nội dung thư hay địa chỉ đầy đủ (chỉ tên miền người nhận).
"""

from __future__ import annotations

import logging
import os
import re
import smtplib
import threading
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import parseaddr
from urllib.parse import urlsplit

import httpx

_log = logging.getLogger("algosim.email")

RESEND_API_URL = "https://api.resend.com/emails"
_HTTP_TIMEOUT = httpx.Timeout(10.0, connect=5.0)
_DEFAULT_PUBLIC_APP_URL = "http://localhost:3000"


@dataclass(frozen=True)
class OutgoingEmail:
    to: str
    subject: str
    html: str
    text: str
    #: `verify_email` | `password_reset` | `password_changed` | `smoke_test` — chỉ để ghi nhật ký/kiểm thử.
    category: str
    idempotency_key: str | None = None


@dataclass(frozen=True)
class SendResult:
    #: `accepted` | `failed` | `unavailable` | `throttled`
    status: str
    provider_id: str | None = None
    #: Mã máy cho nhật ký/kiểm thử — KHÔNG hiển thị cho người dùng.
    reason: str | None = None


Transport = Callable[[OutgoingEmail], SendResult]
_TEST_TRANSPORT: Transport | None = None


def set_email_transport(transport: Transport | None) -> None:
    """Gắn kênh gửi giả cho kiểm thử (không bao giờ gọi Resend thật trong pytest/CI)."""
    global _TEST_TRANSPORT
    _TEST_TRANSPORT = transport


def _env(name: str) -> str:
    return os.getenv(name, "").strip()


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in ("1", "true", "yes", "on")


def email_provider() -> str:
    raw = _env("EMAIL_PROVIDER").lower()
    if raw:
        return raw
    # Tương thích ngược: cấu hình SMTP cũ không khai EMAIL_PROVIDER.
    return "smtp" if _env("ALGOSIM_SMTP_HOST") else "resend"


def public_app_url() -> str | None:
    """Nguồn gốc frontend cố định do vận hành cấu hình — KHÔNG bao giờ lấy từ Host header của yêu cầu."""
    raw = _env("ALGOSIM_PUBLIC_APP_URL") or _DEFAULT_PUBLIC_APP_URL
    parts = urlsplit(raw)
    if parts.scheme not in ("http", "https") or not parts.netloc or parts.query or parts.fragment:
        return None
    if parts.path not in ("", "/"):
        return None
    return f"{parts.scheme}://{parts.netloc}"


def _sender() -> str:
    if email_provider() == "smtp":
        return _env("EMAIL_FROM") or _env("ALGOSIM_SMTP_FROM")
    return _env("EMAIL_FROM")


def _sender_valid(sender: str) -> bool:
    _, addr = parseaddr(sender)
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", addr or ""))


def readiness() -> dict:
    """Trạng thái cấu hình — chỉ boolean và mã lỗi, không có giá trị bí mật."""
    provider = email_provider()
    sender = _sender()
    app_url = public_app_url()
    issues: list[str] = []
    if _TEST_TRANSPORT is not None:
        return {"provider": "test", "enabled": True, "available": True, "issues": [], "publicAppUrl": app_url}
    if provider == "resend":
        enabled = _truthy(_env("EMAIL_ENABLED"))
        if not enabled:
            issues.append("EMAIL_DISABLED")
        if not _env("RESEND_API_KEY"):
            issues.append("RESEND_API_KEY_MISSING")
    elif provider == "smtp":
        enabled_raw = _env("EMAIL_ENABLED")
        enabled = _truthy(enabled_raw) if enabled_raw else True
        if not enabled:
            issues.append("EMAIL_DISABLED")
        if not _env("ALGOSIM_SMTP_HOST"):
            issues.append("SMTP_HOST_MISSING")
    else:
        enabled = False
        issues.append("EMAIL_PROVIDER_UNSUPPORTED")
    if not _sender_valid(sender):
        issues.append("EMAIL_FROM_INVALID")
    if app_url is None:
        issues.append("PUBLIC_APP_URL_INVALID")
    _, sender_addr = parseaddr(sender)
    return {
        "provider": provider,
        "enabled": enabled,
        "available": not issues,
        "issues": issues,
        "senderDomain": sender_addr.split("@", 1)[1] if "@" in sender_addr else None,
        "publicAppUrl": app_url,
    }


def email_available() -> bool:
    return bool(readiness()["available"])


# ── Giới hạn khối lượng (chống dội thư và bảo vệ hạn mức nhà cung cấp) ─────────────────────────────────────────────
# Lưu trong bộ nhớ tiến trình (mỗi worker uvicorn một bộ đếm, đặt lại khi khởi động lại) — KHÔNG phải giới hạn phân
# tán. Đủ cho mô hình VPS một worker; nhiều worker cần lớp giới hạn dùng chung.
_VOLUME_LOCK = threading.Lock()
_RECIPIENT_SENDS: dict[str, deque[float]] = {}
_GLOBAL_SENDS: deque[float] = deque()
_WINDOW_S = 3600.0


def _int_env(name: str, default: int, low: int, high: int) -> int:
    try:
        return min(high, max(low, int(_env(name) or default)))
    except ValueError:
        return default


def reset_volume_limits() -> None:
    with _VOLUME_LOCK:
        _RECIPIENT_SENDS.clear()
        _GLOBAL_SENDS.clear()


def _reserve_volume(recipient: str) -> bool:
    per_recipient = _int_env("EMAIL_MAX_PER_RECIPIENT_PER_HOUR", 5, 1, 50)
    global_cap = _int_env("EMAIL_MAX_PER_HOUR", 200, 1, 10000)
    now = time.monotonic()
    cutoff = now - _WINDOW_S
    key = recipient.strip().lower()
    with _VOLUME_LOCK:
        while _GLOBAL_SENDS and _GLOBAL_SENDS[0] <= cutoff:
            _GLOBAL_SENDS.popleft()
        dq = _RECIPIENT_SENDS.setdefault(key, deque())
        while dq and dq[0] <= cutoff:
            dq.popleft()
        if len(dq) >= per_recipient or len(_GLOBAL_SENDS) >= global_cap:
            return False
        dq.append(now)
        _GLOBAL_SENDS.append(now)
        if len(_RECIPIENT_SENDS) > 4096:
            for stale in [k for k, v in _RECIPIENT_SENDS.items() if not v or v[-1] <= cutoff]:
                _RECIPIENT_SENDS.pop(stale, None)
        return True


# ── Kênh gửi ────────────────────────────────────────────────────────────────────────────────────────────────────────

def _resend_transport(msg: OutgoingEmail) -> SendResult:
    headers = {
        "Authorization": f"Bearer {_env('RESEND_API_KEY')}",
        "Content-Type": "application/json",
        "User-Agent": "axo-backend",
    }
    if msg.idempotency_key:
        headers["Idempotency-Key"] = msg.idempotency_key[:256]
    payload = {"from": _sender(), "to": [msg.to], "subject": msg.subject, "html": msg.html, "text": msg.text}
    try:
        resp = httpx.post(RESEND_API_URL, json=payload, headers=headers, timeout=_HTTP_TIMEOUT)
    except httpx.TimeoutException:
        return SendResult("failed", reason="PROVIDER_TIMEOUT")
    except httpx.HTTPError:
        return SendResult("failed", reason="PROVIDER_NETWORK_ERROR")
    if resp.status_code == 429:
        return SendResult("failed", reason="PROVIDER_RATE_LIMITED")
    if 200 <= resp.status_code < 300:
        try:
            provider_id = str(resp.json().get("id") or "") or None
        except ValueError:
            provider_id = None
        return SendResult("accepted", provider_id=provider_id)
    return SendResult("failed", reason=f"PROVIDER_HTTP_{resp.status_code}")


def _smtp_transport(msg: OutgoingEmail) -> SendResult:
    em = EmailMessage()
    em["Subject"] = msg.subject
    em["From"] = _sender()
    em["To"] = msg.to
    em.set_content(msg.text)
    em.add_alternative(msg.html, subtype="html")
    port = _int_env("ALGOSIM_SMTP_PORT", 587, 1, 65535)
    try:
        with smtplib.SMTP(_env("ALGOSIM_SMTP_HOST"), port, timeout=10) as client:
            if _env("ALGOSIM_SMTP_STARTTLS") != "0":
                client.starttls()
            user, password = _env("ALGOSIM_SMTP_USER"), _env("ALGOSIM_SMTP_PASSWORD")
            if user and password:
                client.login(user, password)
            client.send_message(em)
    except (OSError, smtplib.SMTPException):
        return SendResult("failed", reason="SMTP_ERROR")
    return SendResult("accepted")


def send_email(msg: OutgoingEmail) -> SendResult:
    """Một lần thử, có timeout, không thử lại vô hạn. Không bao giờ ném lỗi ra ngoài."""
    if not email_available():
        result = SendResult("unavailable", reason="EMAIL_NOT_CONFIGURED")
    elif not _reserve_volume(msg.to):
        result = SendResult("throttled", reason="EMAIL_VOLUME_LIMIT")
    else:
        transport = _TEST_TRANSPORT or (_smtp_transport if email_provider() == "smtp" else _resend_transport)
        try:
            result = transport(msg)
        except Exception:  # noqa: BLE001 — kênh gửi lỗi không được làm hỏng yêu cầu HTTP
            result = SendResult("failed", reason="TRANSPORT_EXCEPTION")
    domain = msg.to.rsplit("@", 1)[-1].lower() if "@" in msg.to else "?"
    log_fn = _log.info if result.status == "accepted" else _log.warning
    log_fn(
        "email category=%s status=%s reason=%s provider_id=%s recipient_domain=%s",
        msg.category, result.status, result.reason, result.provider_id, domain,
    )
    return result
