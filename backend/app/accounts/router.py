"""HTTP cho tài khoản / lớp học / bài thực hành.

Router MỎNG có chủ đích: nó dịch HTTP ↔ miền và không chứa luật. Mọi phán quyết
quyền nằm ở `policy.py` (hàm thuần, test được không cần FastAPI); mọi truy vấn
nằm ở `service.py`.

Ba luật xuyên suốt file này:

1. **Vai trò do server sở hữu.** Không handler nào đọc `role` từ body để quyết
   quyền — nó đọc từ `User.role` tra bằng token phiên.
2. **Từ chối là 403/404 có chữ tiếng Việt**, không phải im lặng trả rỗng.
3. **Không rò dữ liệu ngoài lớp.** Giáo viên chỉ thấy lớp mình sở hữu; học sinh
   chỉ thấy lớp mình đã vào (`§23`).
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import secrets
import smtplib
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Any

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel, Field
import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import case, delete, func, literal, select, update
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from ..persistence.classroom_models import (
    AdminAnalysisTelemetry,
    AdminAuditLogEntry,
    AnalysisUsageLedger,
    AdminSystemSetting,
    Assignment,
    AuthSession,
    ClassMembership,
    Classroom,
    LearningHistoryEntry,
    PracticeSession,
    User,
    UserAccountMeta,
)
from ..persistence.db import Base, SessionLocal, SimulationCache
from .passwords import WeakPasswordError
from . import policy
from .policy import (
    Role,
    RoleEscalationError,
    can_observe_class,
    entitlement_for,
    resolve_signup_role,
)
from . import service

router = APIRouter(prefix="/api", tags=["accounts"])

#: Cookie phiên. `httponly` để JavaScript của trang không đọc được (giảm hậu quả
#: khi có XSS); `samesite=lax` chặn CSRF cho mọi request đổi trạng thái đến từ
#: site khác mà vẫn cho điều hướng thường hoạt động.
_COOKIE_KW = {"httponly": True, "samesite": "lax", "path": "/"}

#: Giá trị cấu hình hệ thống mặc định (nguồn chân lý thực tế nằm tại bảng `admin_system_settings`).
_DEFAULT_SYSTEM_SETTINGS: dict[str, Any] = {
    "studentDailyLimit": 15,
    "teacherDailyLimit": 80,
    "studentTokenLimit": 45000,
    "teacherTokenLimit": 240000,
    "studentRpmLimit": 4,
    "teacherRpmLimit": 10,
    "monthlyBudgetVnd": 3000000,
    "vndBudgetRaw": "3.000.000",
    "autoCutoffEnabled": True,
    "budgetCapMode": "chặn yêu cầu mới & thông báo Quản trị viên",
    "guestTrialLimit": 3,
    "teacherVerifyMode": "cần Quản trị viên duyệt trước khi kích hoạt",
    "maintenanceMode": False,
    "allowNewRegistrations": True,
    "updatedAt": None,
}
#: Giữ biến mức module để tương thích ngược với fixture kiểm thử cũ; trạng thái thật nằm trong SQLite.
_USER_EXTRA_META: dict[int, dict[str, Any]] = {}
_SYSTEM_SETTINGS: dict[str, Any] = dict(_DEFAULT_SYSTEM_SETTINGS)
_ADMIN_AUDIT_LOGS: list[dict[str, Any]] = []
_ENSURED_ENGINE_IDS: set[int] = set()


def _utc_today_str(now_dt: datetime | None = None) -> str:
    dt = now_dt or datetime.now(timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _ensure_admin_tables(db) -> None:
    """Đảm bảo 4 bảng quản trị bền vững tồn tại trên cả SQLite có sẵn mà không cần migration phá hủy."""
    if db is None:
        return
    bind = db.get_bind()
    if bind is None:
        return
    bind_key = id(bind)
    if bind_key in _ENSURED_ENGINE_IDS:
        return
    Base.metadata.create_all(
        bind=bind,
        tables=[
            UserAccountMeta.__table__,
            AdminSystemSetting.__table__,
            AdminAuditLogEntry.__table__,
            AdminAnalysisTelemetry.__table__,
            AnalysisUsageLedger.__table__,
        ],
        checkfirst=True,
    )
    _ENSURED_ENGINE_IDS.add(bind_key)


def _load_system_settings(db) -> dict[str, Any]:
    out = dict(_DEFAULT_SYSTEM_SETTINGS)
    if db is None:
        return out
    _ensure_admin_tables(db)
    row = db.get(AdminSystemSetting, "global")
    if row is not None and row.value_json:
        try:
            stored = json.loads(row.value_json)
            if isinstance(stored, dict):
                out.update(stored)
        except Exception:
            pass
    return out


def _save_system_settings(db, payload: dict[str, Any]) -> dict[str, Any]:
    _ensure_admin_tables(db)
    merged = dict(_DEFAULT_SYSTEM_SETTINGS)
    merged.update(payload)
    now_dt = datetime.now(timezone.utc)
    raw_json = json.dumps(merged, ensure_ascii=False)
    row = db.get(AdminSystemSetting, "global")
    if row is None:
        row = AdminSystemSetting(key="global", value_json=raw_json, updated_at=now_dt)
        db.add(row)
    else:
        row.value_json = raw_json
        row.updated_at = now_dt
    db.flush()
    _SYSTEM_SETTINGS.clear()
    _SYSTEM_SETTINGS.update(merged)
    return dict(merged)


def _audit_row_to_dict(row: AdminAuditLogEntry) -> dict[str, Any]:
    return {
        "id": row.audit_key,
        "timestamp": row.timestamp_display,
        "timeTs": int(row.time_ts),
        "actor": row.actor,
        "action": row.action,
        "target": row.target,
        "detail": row.detail,
        "severity": row.severity,
    }


def _record_audit_log(
    db,
    *,
    actor: str,
    action: str,
    target: str,
    detail: str,
    severity: str = "info",
) -> dict[str, Any]:
    _ensure_admin_tables(db)
    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%d/%m/%Y · %H:%M")
    existing_count = len(
        db.execute(select(AdminAuditLogEntry.id)).scalars().all()
    )
    seq = existing_count + 1
    audit_key = f"audit-{seq}-{int(now_dt.timestamp())}"
    time_ts = int(now_dt.timestamp() * 1000) * 1000 + seq
    entry = AdminAuditLogEntry(
        audit_key=audit_key,
        timestamp_display=now_str,
        time_ts=time_ts,
        actor=actor[:200],
        action=action[:160],
        target=target[:200],
        detail=detail,
        severity=severity[:32],
        created_at=now_dt,
    )
    db.add(entry)
    db.flush()
    payload = _audit_row_to_dict(entry)
    _ADMIN_AUDIT_LOGS.insert(0, payload)
    return payload


def _list_audit_logs(db) -> list[dict[str, Any]]:
    _ensure_admin_tables(db)
    rows = (
        db.execute(
            select(AdminAuditLogEntry).order_by(
                AdminAuditLogEntry.time_ts.desc(), AdminAuditLogEntry.id.desc()
            )
        )
        .scalars()
        .all()
    )
    return [_audit_row_to_dict(r) for r in rows]


# ── PHỤ THUỘC ────────────────────────────────────────────────────────────────

class Caller:
    """Ai đang gọi. `user is None` ⇒ khách."""

    def __init__(self, db, auth: AuthSession, user: User | None):
        self.db = db
        self.auth = auth
        self.user = user

    @property
    def role(self) -> Role | None:
        if not self.user:
            return None
        try:
            return Role(self.user.role)
        except ValueError:
            return Role.TEACHER

    @property
    def user_id(self) -> int | None:
        return self.user.id if self.user else None

    def require_user(self) -> User:
        if self.user is None:
            raise HTTPException(401, "Em cần đăng nhập để dùng chức năng này.")
        return self.user

    def require_role(self, role: Role) -> User:
        user = self.require_user()
        if self.role is not role:
            # Câu chữ nói ĐÚNG việc bị chặn, không nói "bạn là ai" — không rò vai trò.
            raise HTTPException(403, "Tài khoản của bạn không có quyền thực hiện việc này.")
        return user

    def require_admin(self) -> User:
        user = self.require_user()
        if user.role != "admin":
            raise HTTPException(403, "Tài khoản của bạn không có quyền quản trị hệ thống.")
        return user


def get_caller(algosim_session: str | None = Cookie(default=None)):
    """Mở transaction + giải danh tính. Dùng làm dependency cho mọi endpoint.

    Phiên KHÔNG tự sinh ở đây: tạo phiên là việc của endpoint có `Response` để
    đặt cookie. Không có phiên ⇒ khách với 0 lượt đã dùng.
    """
    db = SessionLocal()
    try:
        _ensure_admin_tables(db)
        auth = service.load_session(db, algosim_session)
        user = db.get(User, auth.user_id) if (auth and auth.user_id) else None
        if user is not None:
            meta_row = _get_user_meta_row(db, user.id)
            if meta_row is not None and meta_row.status == "suspended":
                user = None
        yield Caller(db, auth, user)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def _revoke_user_sessions(db, user_id: int) -> None:
    """Thu hồi ngay mọi phiên đăng nhập đang mở của tài khoản."""
    db.execute(delete(AuthSession).where(AuthSession.user_id == user_id))
    db.flush()


def _ensure_session(db, auth: AuthSession | None, response: Response) -> AuthSession:
    """Có phiên thì dùng lại, chưa có thì mở và đặt cookie."""
    if auth is not None:
        return auth
    fresh = service.new_session(db)
    set_session_cookie(response, fresh.token)
    return fresh


def set_session_cookie(response, token: str) -> None:
    """The one place a session cookie is written (httponly, samesite=lax, server-issued opaque token)."""
    response.set_cookie(service.SESSION_COOKIE, token,
                        max_age=int(service.SESSION_TTL.total_seconds()), **_COOKIE_KW)


#: No valid session ⇒ provider work is refused; the caller issues a fresh guest session so the client's retry counts.
SESSION_REQUIRED: tuple[int, dict[str, Any]] = (401, {
    "error": "Phiên làm việc chưa sẵn sàng. Hệ thống vừa mở phiên mới — hãy gửi lại.",
    "reason_code": "session_required",
})


def issue_guest_session(db) -> str:
    """Open a guest session server-side (never from a client-supplied identity) and return its token."""
    return service.new_session(db).token


def _get_user_meta_row(db, user_id: int) -> UserAccountMeta | None:
    if db is None:
        return None
    _ensure_admin_tables(db)
    return db.execute(
        select(UserAccountMeta).where(UserAccountMeta.user_id == user_id)
    ).scalar_one_or_none()


def _ensure_user_meta_row(db, user_id: int) -> UserAccountMeta:
    _ensure_admin_tables(db)
    row = _get_user_meta_row(db, user_id)
    if row is None:
        row = UserAccountMeta(
            user_id=user_id,
            subject="Toán Hình học không gian",
            usage_date=_utc_today_str(),
        )
        db.add(row)
        db.flush()
    return row


def _user_daily_limit(user: User, db=None, settings: dict[str, Any] | None = None) -> int:
    meta_row = _get_user_meta_row(db, user.id) if db is not None else None
    if meta_row is not None and isinstance(meta_row.custom_daily_limit, int) and meta_row.custom_daily_limit > 0:
        return meta_row.custom_daily_limit
    if user.role == "admin":
        return 500
    eff_settings = settings if settings is not None else _load_system_settings(db)
    if user.role == "teacher":
        return int(eff_settings.get("teacherDailyLimit", 80))
    return int(eff_settings.get("studentDailyLimit", 15))


def _user_public(user: User, db=None) -> dict:
    """Hình chiếu CÔNG KHAI của tài khoản. `password_hash` không có mặt ở đây,
    và `test_auth_api.py` khoá điều đó bằng cách quét toàn bộ response."""
    settings = _load_system_settings(db)
    meta_row = _get_user_meta_row(db, user.id) if db is not None else None
    today_str = _utc_today_str()
    is_same_day = bool(meta_row is not None and meta_row.usage_date == today_str)
    used_today = int(meta_row.used_today) if (meta_row is not None and is_same_day) else 0
    bonus_today = int(meta_row.bonus_quota_today) if (meta_row is not None and is_same_day) else 0
    daily_limit = _user_daily_limit(user, db, settings)
    default_status = (
        "pending_activation"
        if user.must_change_password
        else ("verified" if user.role == "teacher" else "active")
    )
    resolved_status = (
        meta_row.status
        if (meta_row is not None and meta_row.status)
        else default_status
    )
    return {
        "id": user.id,
        "email": user.email,
        "displayName": user.display_name,
        "role": user.role,
        "mustChangePassword": bool(user.must_change_password),
        "school": meta_row.school if meta_row is not None else "",
        "grade": meta_row.grade if meta_row is not None else "",
        "className": meta_row.class_name if meta_row is not None else "",
        "workplace": meta_row.workplace if meta_row is not None else "",
        "subject": (
            meta_row.subject
            if (meta_row is not None and meta_row.subject)
            else "Toán Hình học không gian"
        ),
        "adminNote": meta_row.admin_note if meta_row is not None else "",
        "status": resolved_status,
        "usedToday": used_today,
        "dailyLimit": daily_limit,
        "tokenCap": meta_row.token_cap if meta_row is not None else None,
        "bonusQuotaToday": bonus_today,
        "passwordResetRequestedAt": (
            meta_row.password_reset_requested_at if meta_row is not None else None
        ),
        "createdAt": user.created_at.isoformat() if user.created_at else None,
    }


def check_analyze_quota_and_maintenance(
    db, algosim_session: str | None, *, enforce_quota: bool = True
) -> tuple[int, dict[str, Any]] | None:
    """Kiểm tra chế độ bảo trì và hạn mức dựng hình theo ngày lưu bền vững trên SQLite.

    Trả `(status_code, payload)` nếu yêu cầu bị chặn trước khi chạy pipeline; `None` nếu được phép.
    """
    _ensure_admin_tables(db)
    settings = _load_system_settings(db)
    auth = service.load_session(db, algosim_session)
    user = db.get(User, auth.user_id) if (auth is not None and auth.user_id is not None) else None
    if user is not None:
        meta_row = _get_user_meta_row(db, user.id)
        if meta_row is not None and meta_row.status == "suspended":
            return (
                403,
                {
                    "error": "Tài khoản này đang bị tạm khóa bởi Quản trị viên.",
                    "reason_code": "account_suspended",
                },
            )
    if settings.get("maintenanceMode") and (user is None or user.role != "admin"):
        return (
            503,
            {
                "error": "Hệ thống đang trong chế độ bảo trì. Vui lòng thử lại sau.",
                "reason_code": "maintenance_mode",
            },
        )
    # `/api/analyze` enforces the quota atomically in `reserve_analysis_usage`; this read-only check stays for gates
    # that only look (image extraction).
    if enforce_quota and user is not None and user.role != "admin":
        today_str = _utc_today_str()
        meta_row = _get_user_meta_row(db, user.id)
        used_today = (
            int(meta_row.used_today)
            if (meta_row is not None and meta_row.usage_date == today_str)
            else 0
        )
        bonus_today = (
            int(meta_row.bonus_quota_today)
            if (meta_row is not None and meta_row.usage_date == today_str)
            else 0
        )
        effective_limit = _user_daily_limit(user, db, settings) + bonus_today
        if used_today >= effective_limit:
            return (
                429,
                {
                    "error": (
                        f"Bạn đã sử dụng hết hạn mức {effective_limit} lượt dựng hình hôm nay. "
                        "Bạn vẫn có thể mở bài mẫu trong Thư viện hoặc Lịch sử."
                    ),
                    "reason_code": "daily_quota_exceeded",
                },
            )
    return None


_log = logging.getLogger("algosim.usage")


@dataclass(frozen=True)
class UsageReservation:
    """A counted attempt (its ledger row and the counter it holds)."""

    ledger_id: int | None
    subject: str = ""                 # "user" | "guest"
    subject_id: int = 0
    usage_date: str = ""


def _upd(db, stmt):
    """Execute a bulk UPDATE as one SQL statement (no ORM evaluation of CASE expressions in the session)."""
    return db.execute(stmt.execution_options(synchronize_session=False))


def _reserve_counter(db, subject: str, subject_id: int, limit: int | None, today: str, now: datetime) -> bool:
    """Atomic conditional +1 in ONE statement (no read-modify-write): False when the limit is already reached."""
    if subject == "guest":
        res = _upd(db, update(AuthSession).where(AuthSession.id == subject_id,
                                                 AuthSession.guest_trials_used < int(limit or 0))
                   .values(guest_trials_used=AuthSession.guest_trials_used + 1))
        return res.rowcount == 1
    same_day = UserAccountMeta.usage_date == today
    used = case((same_day, UserAccountMeta.used_today), else_=literal(0))
    bonus = case((same_day, UserAccountMeta.bonus_quota_today), else_=literal(0))
    stmt = update(UserAccountMeta).where(UserAccountMeta.user_id == subject_id)
    if limit is not None:
        stmt = stmt.where(used < literal(limit) + bonus)
    res = _upd(db, stmt.values(used_today=used + 1, bonus_quota_today=bonus, usage_date=today, updated_at=now))
    return res.rowcount == 1


def _refund_counter(db, r: UsageReservation) -> None:
    if r.subject == "guest":
        _upd(db, update(AuthSession).where(AuthSession.id == r.subject_id, AuthSession.guest_trials_used > 0)
             .values(guest_trials_used=AuthSession.guest_trials_used - 1))
    else:                             # a refund never crosses into another day's counter
        _upd(db, update(UserAccountMeta).where(UserAccountMeta.user_id == r.subject_id,
                                               UserAccountMeta.usage_date == r.usage_date,
                                               UserAccountMeta.used_today > 0)
             .values(used_today=UserAccountMeta.used_today - 1))


def reserve_analysis_usage(
    algosim_session: str | None, attempt_key: str | None
) -> UsageReservation | tuple[int, dict[str, Any]]:
    """Gate + reservation of one analysis attempt, BEFORE any provider work, in one transaction.

    Suspension/maintenance answer as before. Then the attempt's ledger row (unique `(scope, attempt_key)`) and the
    counter (guest trial or daily quota) are taken atomically: a conditional UPDATE, so concurrent tabs, accounts or
    workers can neither lose an increment nor overrun the limit. A retry of an attempt that already holds a
    `reserved`/`charged` row is not counted again (also after a restart). A database failure raises — the caller
    answers 503 and runs nothing, so an analysis is never served uncounted.
    """
    today, now = _utc_today_str(), datetime.now(timezone.utc)
    with SessionLocal() as db:
        gate = check_analyze_quota_and_maintenance(db, algosim_session, enforce_quota=False)
        if gate is not None:
            db.commit()
            return gate
        auth = service.load_session(db, algosim_session)
        if auth is None:              # missing, expired or forged cookie: no provider work, a fresh guest session
            token = issue_guest_session(db)
            db.commit()
            return (*SESSION_REQUIRED, token)
        user = db.get(User, auth.user_id) if auth.user_id is not None else None
        if user is not None:
            subject, subject_id = "user", user.id
            try:
                _ensure_user_meta_row(db, user.id)
            except IntegrityError:    # a concurrent first request created it (unique user_id); nothing else pending
                db.rollback()
            limit = None if user.role == "admin" else _user_daily_limit(user, db)
            refused = (429, {"error": "Bạn đã sử dụng hết hạn mức lượt dựng hình hôm nay. Bạn vẫn có thể mở bài mẫu "
                                      "trong Thư viện hoặc Lịch sử.", "reason_code": "daily_quota_exceeded"})
        else:
            subject, subject_id, limit = "guest", auth.id, policy.GUEST_TRIAL_LIMIT
            refused = (402, {"error": "Em đã dùng hết lượt mô phỏng thử. Đăng nhập để tiếp tục thực hành.",
                             "reason_code": "guest_trial_exhausted"})
        scope, key = f"{subject}:{subject_id}", attempt_key or f"unkeyed-{uuid.uuid4().hex}"
        db.commit()

        for _ in range(2):            # the second pass only after losing an insert race on the same attempt
            row = db.execute(select(AnalysisUsageLedger).where(AnalysisUsageLedger.scope == scope,
                                                               AnalysisUsageLedger.attempt_key == key)).scalar_one_or_none()
            if row is not None and row.state in ("reserved", "charged"):
                return UsageReservation(row.id, subject, subject_id, row.usage_date)
            if not _reserve_counter(db, subject, subject_id, limit, today, now):
                db.rollback()
                return refused
            try:
                if row is None:
                    row = AnalysisUsageLedger(scope=scope, attempt_key=key, state="reserved", usage_date=today,
                                              created_at=now, updated_at=now)
                    db.add(row)
                    db.flush()
                elif _upd(db, update(AnalysisUsageLedger).where(AnalysisUsageLedger.id == row.id,
                                                                AnalysisUsageLedger.state == "released")
                          .values(state="reserved", usage_date=today, updated_at=now)).rowcount != 1:
                    db.rollback()
                    continue
                db.commit()
                return UsageReservation(row.id, subject, subject_id, today)
            except IntegrityError:
                db.rollback()         # a concurrent request of the SAME attempt won: reuse its reservation
        raise RuntimeError("usage reservation did not converge")


def finalize_analysis_usage(r: UsageReservation, served: bool) -> None:
    """`reserved` → `charged` when served, else → `released` with the counter refunded, atomically.

    Failure is logged, never silent. It leaves the row `reserved`: a served attempt stays counted (correct); an
    unserved one stays counted too (fail closed — the learner loses at most that one unit, visible in the ledger)."""
    if r.ledger_id is None:
        return
    now = datetime.now(timezone.utc)
    try:
        with SessionLocal() as db:
            moved = _upd(db, update(AnalysisUsageLedger).where(AnalysisUsageLedger.id == r.ledger_id,
                                                               AnalysisUsageLedger.state == "reserved")
                         .values(state="charged" if served else "released", updated_at=now)).rowcount
            if moved == 1 and not served:
                _refund_counter(db, r)
            db.commit()
    except SQLAlchemyError:
        _log.exception("usage ledger finalisation failed (ledger id %s, served=%s); the attempt stays counted",
                       r.ledger_id, served)


def _configured_gemini_model_id() -> str:
    env_override = os.getenv("GEMINI_MODEL", "").strip()
    if env_override:
        return env_override
    try:
        from ..ai import gemini as gemini_mod

        return str(getattr(gemini_mod, "MODEL", "gemini-2.5-flash") or "gemini-2.5-flash")
    except Exception:
        return "gemini-2.5-flash"


def _sum_usage_snapshot(snapshot: dict[str, dict[str, int]] | None) -> dict[str, int]:
    totals = {
        "calls": 0,
        "prompt_tokens": 0,
        "candidates_tokens": 0,
        "thoughts_tokens": 0,
        "total_tokens": 0,
    }
    if not snapshot:
        return totals
    for vals in snapshot.values():
        if not isinstance(vals, dict):
            continue
        for k in totals:
            totals[k] += int(vals.get(k, 0) or 0)
    return totals


def record_analyze_telemetry(
    *,
    algosim_session: str | None,
    status_code: int,
    body_bytes: bytes,
    latency_ms: int,
    usage_before: dict[str, dict[str, int]] | None,
    usage_after: dict[str, dict[str, int]] | None,
) -> None:
    """Lưu số liệu vận hành thực tế của `/api/analyze` mà không chạm pipeline nghiên cứu hay lưu prompt."""
    payload: dict[str, Any] = {}
    if body_bytes:
        try:
            parsed = json.loads(body_bytes.decode("utf-8"))
            if isinstance(parsed, dict):
                payload = parsed
        except Exception:
            payload = {}

    reason_code = str(payload.get("reason_code") or "")
    # Không tính các lượt bị chặn ngay tại cổng phiên/hạn mức/bảo trì làm lượt chạy mô hình
    if status_code in (402, 429) or reason_code in (
        "guest_trial_exhausted",
        "daily_quota_exceeded",
        "maintenance_mode",
        "account_suspended",
    ):
        return

    route_d = payload.get("route_d") if isinstance(payload.get("route_d"), dict) else None
    if status_code == 200 and (
        payload.get("status") == "ok"
        or (route_d is not None and route_d.get("status") == "SERVED")
    ):
        outcome = "succeeded"
    elif status_code == 200 and (
        payload.get("status") == "unsupported"
        or (route_d is not None and route_d.get("status") == "REFUSED")
    ):
        outcome = "refused"
    else:
        outcome = "failed"

    cached = bool(payload.get("cached"))
    before_sum = _sum_usage_snapshot(usage_before)
    after_sum = _sum_usage_snapshot(usage_after)
    calls_delta = max(0, after_sum["calls"] - before_sum["calls"])
    input_tok = max(0, after_sum["prompt_tokens"] - before_sum["prompt_tokens"])
    output_tok = max(0, after_sum["candidates_tokens"] - before_sum["candidates_tokens"])
    thoughts_tok = max(0, after_sum["thoughts_tokens"] - before_sum["thoughts_tokens"])
    total_tok = max(0, after_sum["total_tokens"] - before_sum["total_tokens"])
    tokens_measured = calls_delta > 0

    with SessionLocal() as db:
        _ensure_admin_tables(db)
        auth = service.load_session(db, algosim_session)
        user = db.get(User, auth.user_id) if (auth is not None and auth.user_id is not None) else None
        role_str = user.role if user is not None else "guest"
        now_dt = datetime.now(timezone.utc)

        db.add(
            AdminAnalysisTelemetry(
                user_id=user.id if user is not None else None,
                role=role_str,
                outcome=outcome,
                cached=cached,
                model_id=_configured_gemini_model_id(),
                latency_ms=max(0, int(latency_ms)),
                tokens_measured=tokens_measured,
                input_tokens=input_tok if tokens_measured else 0,
                output_tokens=output_tok if tokens_measured else 0,
                thoughts_tokens=thoughts_tok if tokens_measured else 0,
                total_tokens=total_tok if tokens_measured else 0,
                created_at=now_dt,
            )
        )
        # The daily quota is NOT counted here: it limits access, so `reserve_analysis_usage` /
        # `finalize_analysis_usage` own it (usage ledger). This row is observational only.
        db.commit()


def _me_payload(caller: Caller, auth: AuthSession) -> dict:
    ent = entitlement_for(caller.role, guest_trials_used=auth.guest_trials_used)
    return {
        "user": _user_public(caller.user, caller.db) if caller.user else None,
        "entitlement": {
            "canRunSimulation": ent.can_run_simulation,
            "canPersistHistory": ent.can_persist_history,
            "canJoinClass": ent.can_join_class,
            "canOwnClass": ent.can_own_class,
            "canReceiveAssignment": ent.can_receive_assignment,
            "trialsLeft": ent.trials_left,
        },
    }


# ── DANH TÍNH ────────────────────────────────────────────────────────────────

class RegisterBody(BaseModel):
    email: str
    displayName: str
    password: str
    #: Client GỬI ĐƯỢC, nhưng server KHÔNG TIN — xem `resolve_signup_role`.
    role: str | None = None
    teacherCode: str | None = None
    school: str | None = None
    grade: str | None = None
    className: str | None = None
    workplace: str | None = None
    subject: str | None = None


class LoginBody(BaseModel):
    email: str
    password: str


class PasswordBody(BaseModel):
    currentPassword: str
    newPassword: str


@router.get("/auth/me")
def me(response: Response, caller: Caller = Depends(get_caller)):
    """Danh tính + quyền hiện tại. Luôn 200 — khách cũng là một câu trả lời hợp lệ.

    Đây cũng là nơi phiên KHÁCH ra đời, nên đếm lượt dùng thử có chỗ bám ngay từ
    lần đầu mở trang.
    """
    auth = _ensure_session(caller.db, caller.auth, response)
    return _me_payload(caller, auth)


@router.post("/auth/register")
def register(body: RegisterBody, response: Response, caller: Caller = Depends(get_caller)):
    settings = _load_system_settings(caller.db)
    admin_code = os.getenv("ALGOSIM_ADMIN_SIGNUP_CODE", "ADMIN2026").strip()
    is_verified_admin_signup = (
        body.role == "admin"
        and bool(body.teacherCode)
        and bool(admin_code)
        and body.teacherCode.strip() == admin_code
    )
    if is_verified_admin_signup:
        role = Role.TEACHER
    else:
        if not settings.get("allowNewRegistrations", True):
            raise HTTPException(
                403,
                "Hệ thống hiện đang tạm đóng đăng ký tài khoản mới.",
            )
        if settings.get("maintenanceMode"):
            raise HTTPException(
                503,
                "Hệ thống đang tạm bảo trì. Vui lòng quay lại sau.",
            )
        try:
            role = resolve_signup_role(
                body.role,
                teacher_code=body.teacherCode,
                expected_teacher_code=service.teacher_signup_code(),
            )
        except RoleEscalationError as exc:
            raise HTTPException(403, str(exc)) from exc
    try:
        user = service.create_user(
            caller.db, email=body.email, display_name=body.displayName,
            password=body.password, role=role,
        )
        if is_verified_admin_signup:
            user.role = "admin"
            caller.db.flush()
    except WeakPasswordError as exc:
        raise HTTPException(400, str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc

    meta_row = _ensure_user_meta_row(caller.db, user.id)
    meta_row.status = "verified" if user.role == "teacher" else "active"
    if body.school is not None:
        meta_row.school = body.school.strip()[:160]
    if body.grade is not None:
        meta_row.grade = body.grade.strip()[:40]
    if body.className is not None:
        meta_row.class_name = body.className.strip()[:60]
    if body.workplace is not None:
        meta_row.workplace = body.workplace.strip()[:160]
    if body.subject is not None:
        meta_row.subject = body.subject.strip()[:120]
    caller.db.flush()

    auth = _ensure_session(caller.db, caller.auth, response)
    service.attach_user(caller.db, auth, user)
    caller.user = user
    return _me_payload(caller, auth)


@router.post("/auth/login")
def login(body: LoginBody, response: Response, caller: Caller = Depends(get_caller)):
    user = service.authenticate(caller.db, email=body.email, password=body.password)
    if user is None:
        # MỘT câu cho cả hai ca (email lạ / sai mật khẩu) — không cho dò tài khoản.
        raise HTTPException(401, "Email hoặc mật khẩu không đúng.")
    meta_row = _get_user_meta_row(caller.db, user.id)
    if meta_row is not None and meta_row.status == "suspended":
        raise HTTPException(403, "Tài khoản này đang bị tạm khóa bởi Quản trị viên.")
    settings = _load_system_settings(caller.db)
    if settings.get("maintenanceMode") and user.role != "admin":
        raise HTTPException(
            503,
            "Hệ thống đang trong chế độ bảo trì. Vui lòng quay lại sau.",
        )
    auth = _ensure_session(caller.db, caller.auth, response)
    service.attach_user(caller.db, auth, user)
    caller.user = user
    return _me_payload(caller, auth)


@router.post("/auth/logout")
def logout(response: Response, caller: Caller = Depends(get_caller)):
    service.end_session(caller.db, caller.auth.token if caller.auth else None)
    response.delete_cookie(service.SESSION_COOKIE, path="/")
    return {"ok": True}


@router.post("/auth/password")
def change_password(body: PasswordBody, caller: Caller = Depends(get_caller)):
    user = caller.require_user()
    if service.authenticate(caller.db, email=user.email, password=body.currentPassword) is None:
        raise HTTPException(400, "Mật khẩu hiện tại không đúng.")
    try:
        service.set_password(caller.db, user, body.newPassword)
    except WeakPasswordError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {"ok": True}


# ── LỚP ──────────────────────────────────────────────────────────────────────

class CreateClassBody(BaseModel):
    name: str = Field(min_length=1, max_length=160)


class JoinClassBody(BaseModel):
    code: str


def _class_public(c: Classroom, *, include_code: bool) -> dict:
    """Mã lớp CHỈ hiện cho giáo viên sở hữu. Học sinh đã vào lớp không cần thấy
    mã, và không được thấy — mã là lời mời để phát tiếp, không phải thông tin lớp."""
    out = {
        "id": c.id, "name": c.name, "archived": bool(c.archived),
        "createdAt": c.created_at.isoformat(),
    }
    if include_code:
        out["joinCode"] = c.join_code if c.code_active else None
        out["codeActive"] = bool(c.code_active)
    return out


@router.get("/classes")
def list_classes(caller: Caller = Depends(get_caller)):
    """Lớp của TÔI. Giáo viên: lớp mình sở hữu. Học sinh: lớp mình đã vào."""
    user = caller.require_user()
    if caller.role is Role.TEACHER:
        rows = caller.db.execute(
            select(Classroom).where(Classroom.teacher_id == user.id)
            .order_by(Classroom.created_at.desc())
        ).scalars().all()
        return {"classes": [_class_public(c, include_code=True) for c in rows]}
    rows = caller.db.execute(
        select(Classroom).join(ClassMembership, ClassMembership.classroom_id == Classroom.id)
        .where(ClassMembership.student_id == user.id)
        .order_by(Classroom.created_at.desc())
    ).scalars().all()
    return {"classes": [_class_public(c, include_code=False) for c in rows]}


@router.post("/classes")
def create_class(body: CreateClassBody, caller: Caller = Depends(get_caller)):
    teacher = caller.require_role(Role.TEACHER)
    c = Classroom(
        teacher_id=teacher.id,
        name=body.name.strip()[:160],
        join_code=service.generate_join_code(caller.db),
    )
    caller.db.add(c)
    caller.db.flush()
    return _class_public(c, include_code=True)


@router.post("/classes/{class_id}/code")
def regenerate_code(class_id: int, caller: Caller = Depends(get_caller)):
    """Sinh lại mã. Mã cũ chết ngay — đó là cách xử lý khi mã bị phát tán."""
    teacher = caller.require_role(Role.TEACHER)
    c = caller.db.get(Classroom, class_id)
    if c is None or c.teacher_id != teacher.id:
        raise HTTPException(404, "Không tìm thấy lớp.")
    c.join_code = service.generate_join_code(caller.db)
    c.code_active = True
    return _class_public(c, include_code=True)


@router.delete("/classes/{class_id}/code")
def revoke_code(class_id: int, caller: Caller = Depends(get_caller)):
    teacher = caller.require_role(Role.TEACHER)
    c = caller.db.get(Classroom, class_id)
    if c is None or c.teacher_id != teacher.id:
        raise HTTPException(404, "Không tìm thấy lớp.")
    c.code_active = False
    return _class_public(c, include_code=True)


@router.post("/classes/join")
def join_class(body: JoinClassBody, caller: Caller = Depends(get_caller)):
    """Học sinh vào lớp bằng mã. Bốn ca hỏng đều có câu trả lời riêng (`§14`)."""
    student = caller.require_role(Role.STUDENT)
    code = service.normalize_join_code(body.code)
    if not code:
        raise HTTPException(400, "Em chưa nhập mã lớp.")
    c = caller.db.execute(
        select(Classroom).where(Classroom.join_code == code)
    ).scalar_one_or_none()
    if c is None:
        raise HTTPException(404, "Mã lớp không đúng. Em kiểm tra lại giúp cô/thầy nhé.")
    if not c.code_active:
        raise HTTPException(410, "Mã lớp này đã ngừng sử dụng. Em hỏi giáo viên mã mới.")
    if c.archived:
        raise HTTPException(410, "Lớp này đã đóng.")
    already = caller.db.execute(
        select(ClassMembership).where(
            ClassMembership.classroom_id == c.id, ClassMembership.student_id == student.id)
    ).scalar_one_or_none()
    if already is not None:
        # KHÔNG phải lỗi: nói rõ đã ở trong lớp rồi và trả lớp về như thường.
        return {"classroom": _class_public(c, include_code=False), "alreadyMember": True}
    caller.db.add(ClassMembership(classroom_id=c.id, student_id=student.id))
    return {"classroom": _class_public(c, include_code=False), "alreadyMember": False}


@router.get("/classes/{class_id}/members")
def class_members(class_id: int, caller: Caller = Depends(get_caller)):
    """Danh sách học sinh — CHỈ giáo viên sở hữu lớp."""
    caller.require_user()
    c = caller.db.get(Classroom, class_id)
    if c is None:
        raise HTTPException(404, "Không tìm thấy lớp.")
    if not can_observe_class(viewer_role=caller.role, viewer_id=caller.user_id,
                             class_teacher_id=c.teacher_id):
        raise HTTPException(403, "Bạn không quản lý lớp này.")
    rows = caller.db.execute(
        select(User).join(ClassMembership, ClassMembership.student_id == User.id)
        .where(ClassMembership.classroom_id == class_id)
        .order_by(User.display_name)
    ).scalars().all()
    return {"members": [
        {"id": u.id, "displayName": u.display_name, "email": u.email} for u in rows]}


# ── LỊCH SỬ TỰ HỌC (USER-SCOPED LEARNING HISTORY) ───────────────────────────

_MAX_HISTORY_PER_USER = 30


class UpsertHistoryBody(BaseModel):
    id: str = Field(min_length=1, max_length=80)
    sampleId: str | None = Field(default=None, max_length=80)
    title: str = Field(min_length=1, max_length=240)
    simulationId: str = Field(min_length=1, max_length=80)
    domain: str = Field(default="geometry", max_length=40)
    envelope: dict
    originalInput: str | None = None
    lastCursor: int = Field(default=0, ge=0)
    stepCount: int = Field(default=0, ge=0)
    visualMode: str = Field(default="3d", max_length=8)


class TouchHistoryBody(BaseModel):
    lastCursor: int | None = Field(default=None, ge=0)
    stepCount: int | None = Field(default=None, ge=0)
    visualMode: str | None = Field(default=None, max_length=8)


def _iso_utc(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def _history_public(row: LearningHistoryEntry) -> dict:
    try:
        envelope = json.loads(row.envelope_json)
    except Exception:
        envelope = {}
    return {
        "id": row.history_key,
        "schemaVersion": 1,
        "sampleId": row.sample_id,
        "title": row.title,
        "simulationId": row.simulation_id,
        "domain": row.domain,
        "envelope": envelope,
        "originalInput": row.original_input,
        "lastCursor": row.last_cursor,
        "stepCount": row.step_count,
        "visualMode": "3d" if row.visual_mode == "3d" else "2d",
        "createdAt": _iso_utc(row.created_at),
        "updatedAt": _iso_utc(row.updated_at),
        "lastViewedAt": _iso_utc(row.last_viewed_at),
    }


def _view_time(db, user_id) -> datetime:
    """`now`, strictly after the user's latest `last_viewed_at`: the wall clock can return one value for several writes
    (≈15.6 ms ticks on Windows), and listing/pruning order by that column — a tie would list (or prune) the wrong row."""
    now = datetime.now(timezone.utc)
    latest = db.execute(select(func.max(LearningHistoryEntry.last_viewed_at))
                        .where(LearningHistoryEntry.user_id == user_id)).scalar_one_or_none()
    if latest is not None:
        latest = latest if latest.tzinfo else latest.replace(tzinfo=timezone.utc)
        now = max(now, latest + timedelta(microseconds=1))
    return now


@router.get("/history")
def list_learning_history(caller: Caller = Depends(get_caller)):
    """Danh sách lịch sử tự học của chính người dùng đang đăng nhập."""
    user = caller.require_user()
    rows = (
        caller.db.execute(
            select(LearningHistoryEntry)
            .where(LearningHistoryEntry.user_id == user.id)
            .order_by(
                LearningHistoryEntry.last_viewed_at.desc(),
                LearningHistoryEntry.id.desc(),
            )
        )
        .scalars()
        .all()
    )
    return {"items": [_history_public(r) for r in rows]}


@router.post("/history")
def upsert_learning_history(
    body: UpsertHistoryBody, caller: Caller = Depends(get_caller)
):
    """Ghi hoặc cập nhật một mục lịch sử tự học gắn với tài khoản hiện tại."""
    user = caller.require_user()
    now = _view_time(caller.db, user.id)
    visual_mode = "3d" if body.visualMode == "3d" else "2d"
    env_json = json.dumps(body.envelope, ensure_ascii=False)

    existing = caller.db.execute(
        select(LearningHistoryEntry).where(
            LearningHistoryEntry.user_id == user.id,
            LearningHistoryEntry.history_key == body.id,
        )
    ).scalar_one_or_none()

    if existing is not None:
        existing.title = body.title.strip() or existing.title
        if body.sampleId is not None:
            existing.sample_id = body.sampleId
        existing.simulation_id = body.simulationId
        existing.domain = body.domain
        existing.envelope_json = env_json
        if body.originalInput is not None:
            existing.original_input = body.originalInput
        existing.last_cursor = max(0, body.lastCursor)
        if body.stepCount > 0:
            existing.step_count = body.stepCount
        existing.visual_mode = visual_mode
        existing.updated_at = now
        existing.last_viewed_at = now
        caller.db.flush()
        return {"item": _history_public(existing)}

    row = LearningHistoryEntry(
        user_id=user.id,
        history_key=body.id,
        sample_id=body.sampleId,
        title=body.title.strip(),
        simulation_id=body.simulationId,
        domain=body.domain,
        envelope_json=env_json,
        original_input=body.originalInput,
        last_cursor=max(0, body.lastCursor),
        step_count=max(0, body.stepCount),
        visual_mode=visual_mode,
        created_at=now,
        updated_at=now,
        last_viewed_at=now,
    )
    caller.db.add(row)
    caller.db.flush()

    all_rows = (
        caller.db.execute(
            select(LearningHistoryEntry)
            .where(LearningHistoryEntry.user_id == user.id)
            .order_by(
                LearningHistoryEntry.last_viewed_at.desc(),
                LearningHistoryEntry.id.desc(),
            )
        )
        .scalars()
        .all()
    )
    for overflow in all_rows[_MAX_HISTORY_PER_USER:]:
        caller.db.delete(overflow)

    return {"item": _history_public(row)}


@router.patch("/history/{history_key}")
def touch_learning_history(
    history_key: str,
    body: TouchHistoryBody,
    caller: Caller = Depends(get_caller),
):
    """Cập nhật bước dựng / chế độ xem của một mục lịch sử thuộc người dùng hiện tại."""
    user = caller.require_user()
    row = caller.db.execute(
        select(LearningHistoryEntry).where(
            LearningHistoryEntry.user_id == user.id,
            LearningHistoryEntry.history_key == history_key,
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Không tìm thấy mục lịch sử.")

    now = _view_time(caller.db, user.id)
    if body.lastCursor is not None:
        row.last_cursor = max(0, body.lastCursor)
    if body.stepCount is not None and body.stepCount > 0:
        row.step_count = body.stepCount
    if body.visualMode is not None:
        row.visual_mode = "3d" if body.visualMode == "3d" else "2d"
    row.updated_at = now
    row.last_viewed_at = now
    caller.db.flush()
    return {"item": _history_public(row)}


@router.delete("/history/{history_key}")
def delete_learning_history_item(
    history_key: str, caller: Caller = Depends(get_caller)
):
    """Xóa một mục lịch sử tự học của người dùng hiện tại."""
    user = caller.require_user()
    row = caller.db.execute(
        select(LearningHistoryEntry).where(
            LearningHistoryEntry.user_id == user.id,
            LearningHistoryEntry.history_key == history_key,
        )
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(404, "Không tìm thấy mục lịch sử.")
    caller.db.delete(row)
    return {"ok": True}


@router.delete("/history")
def clear_learning_history(caller: Caller = Depends(get_caller)):
    """Xóa toàn bộ lịch sử tự học của người dùng hiện tại."""
    user = caller.require_user()
    rows = (
        caller.db.execute(
            select(LearningHistoryEntry).where(
                LearningHistoryEntry.user_id == user.id
            )
        )
        .scalars()
        .all()
    )
    count = len(rows)
    for r in rows:
        caller.db.delete(r)
    return {"ok": True, "deleted": count}


# ── HỒ SƠ CÁ NHÂN, KHÔI PHỤC MẬT KHẨU & QUẢN TRỊ HỆ THỐNG (AXO V2.7 PHASE D.1) ──

class UpdateProfileBody(BaseModel):
    displayName: str = Field(min_length=1, max_length=120)
    school: str | None = None
    grade: str | None = None
    className: str | None = None
    workplace: str | None = None
    subject: str | None = None


class ForgotPasswordBody(BaseModel):
    email: str


class ResetPasswordBody(BaseModel):
    token: str | None = None
    email: str | None = None
    newPassword: str


class AdminCreateUserBody(BaseModel):
    email: str
    displayName: str
    password: str | None = None
    role: str = "student"
    school: str | None = None
    grade: str | None = None
    className: str | None = None
    workplace: str | None = None
    subject: str | None = None
    adminNote: str | None = None
    status: str | None = None
    customDailyLimit: int | None = None
    dailyLimit: int | None = None
    tokenCap: int | None = None


class AdminUpdateUserBody(BaseModel):
    displayName: str | None = None
    role: str | None = None
    status: str | None = None
    isSuspended: bool | None = None
    mustChangePassword: bool | None = None
    school: str | None = None
    grade: str | None = None
    className: str | None = None
    workplace: str | None = None
    subject: str | None = None
    adminNote: str | None = None
    customDailyLimit: int | None = None
    dailyLimit: int | None = None
    tokenCap: int | None = None
    bonusQuotaToday: int | None = None


class AdminSystemSettingsBody(BaseModel):
    studentDailyLimit: int | None = Field(default=None, ge=1, le=500)
    teacherDailyLimit: int | None = Field(default=None, ge=1, le=1000)
    studentTokenLimit: int | None = Field(default=None, ge=1000)
    teacherTokenLimit: int | None = Field(default=None, ge=1000)
    studentRpmLimit: int | None = Field(default=None, ge=1, le=120)
    teacherRpmLimit: int | None = Field(default=None, ge=1, le=120)
    monthlyBudgetVnd: int | None = Field(default=None, ge=0)
    budgetCapMode: str | None = None
    guestTrialLimit: int | None = Field(default=None, ge=0, le=20)
    teacherVerifyMode: str | None = None
    maintenanceMode: bool | None = None
    allowNewRegistrations: bool | None = None
    # Các khóa tương thích trực tiếp với giao diện Quản trị V2.7/V2.8
    studentDailyRequests: int | None = Field(default=None, ge=1, le=500)
    teacherDailyRequests: int | None = Field(default=None, ge=1, le=1000)
    studentDailyTokens: int | None = Field(default=None, ge=1000)
    teacherDailyTokens: int | None = Field(default=None, ge=1000)
    studentRatePerMin: int | None = Field(default=None, ge=1, le=120)
    teacherRatePerMin: int | None = Field(default=None, ge=1, le=120)
    vndBudgetRaw: str | None = None
    autoCutoffEnabled: bool | None = None
    settings: dict[str, Any] | None = None


PASSWORD_RESET_TTL = timedelta(minutes=15)
#: Bảng token đặt lại mật khẩu: khóa là SHA-256(raw_token), không bao giờ lưu token thô.
_PASSWORD_RESET_TOKENS: dict[str, dict[str, Any]] = {}
_PASSWORD_RESET_MAIL_SENDER: Callable[[str, str], None] | None = None


def set_password_reset_mail_sender(
    sender: Callable[[str, str], None] | None,
) -> None:
    """Cho phép kiểm thử tích hợp gắn kênh vận chuyển thư mà không hardcode SMTP."""
    global _PASSWORD_RESET_MAIL_SENDER
    _PASSWORD_RESET_MAIL_SENDER = sender


def _hash_reset_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def _smtp_configured() -> bool:
    if _PASSWORD_RESET_MAIL_SENDER is not None:
        return True
    host = os.getenv("ALGOSIM_SMTP_HOST", "").strip()
    sender = os.getenv("ALGOSIM_SMTP_FROM", "").strip()
    return bool(host and sender)


def _send_password_reset_email(recipient: str, raw_token: str) -> None:
    if _PASSWORD_RESET_MAIL_SENDER is not None:
        _PASSWORD_RESET_MAIL_SENDER(recipient, raw_token)
        return
    host = os.getenv("ALGOSIM_SMTP_HOST", "").strip()
    port = int(os.getenv("ALGOSIM_SMTP_PORT", "587").strip() or "587")
    smtp_user = os.getenv("ALGOSIM_SMTP_USER", "").strip()
    smtp_pass = os.getenv("ALGOSIM_SMTP_PASSWORD", "").strip()
    sender = os.getenv("ALGOSIM_SMTP_FROM", "").strip()
    app_url = os.getenv("ALGOSIM_PUBLIC_APP_URL", "http://localhost:3000").rstrip("/")

    msg = EmailMessage()
    msg["Subject"] = "Mã đặt lại mật khẩu tài khoản Axo"
    msg["From"] = sender
    msg["To"] = recipient
    msg.set_content(
        f"Bạn vừa yêu cầu đặt lại mật khẩu trên Axo.\n\n"
        f"Mã khôi phục (có hiệu lực 15 phút, dùng 1 lần): {raw_token}\n"
        f"Hoặc mở liên kết: {app_url}/?reset_token={raw_token}#reset\n\n"
        f"Nếu bạn không thực hiện yêu cầu này, hãy bỏ qua thư này."
    )
    with smtplib.SMTP(host, port, timeout=10) as client:
        if os.getenv("ALGOSIM_SMTP_STARTTLS", "1").strip() != "0":
            client.starttls()
        if smtp_user and smtp_pass:
            client.login(smtp_user, smtp_pass)
        client.send_message(msg)


def _csv_safe_cell(value: Any) -> str:
    text = "" if value is None else str(value)
    if text and text[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + text
    return text


@router.patch("/auth/profile")
def update_profile(
    body: UpdateProfileBody, response: Response, caller: Caller = Depends(get_caller)
):
    user = caller.require_user()
    clean_name = body.displayName.strip()
    if not clean_name:
        raise HTTPException(400, "Tên hiển thị không được để trống.")
    user.display_name = clean_name[:120]
    meta_row = _ensure_user_meta_row(caller.db, user.id)
    if body.school is not None:
        meta_row.school = body.school.strip()[:160]
    if body.grade is not None:
        meta_row.grade = body.grade.strip()[:40]
    if body.className is not None:
        meta_row.class_name = body.className.strip()[:60]
    if body.workplace is not None:
        meta_row.workplace = body.workplace.strip()[:160]
    if body.subject is not None:
        meta_row.subject = body.subject.strip()[:120]
    meta_row.updated_at = datetime.now(timezone.utc)
    caller.db.flush()
    auth = _ensure_session(caller.db, caller.auth, response)
    return _me_payload(caller, auth)


@router.get("/auth/recovery-status")
def recovery_status():
    """Trạng thái khả dụng của kênh gửi email khôi phục mật khẩu (không lộ cấu hình nội bộ)."""
    return {
        "emailRecoveryAvailable": _smtp_configured(),
    }


@router.post("/auth/forgot-password")
def forgot_password(
    body: ForgotPasswordBody, caller: Caller = Depends(get_caller)
):
    clean_email = service.normalize_email(body.email)
    if not clean_email or "@" not in clean_email:
        raise HTTPException(400, "Vui lòng nhập địa chỉ email hợp lệ.")

    if not _smtp_configured():
        return {
            "ok": True,
            "smtpConfigured": False,
            "deliveryStatus": "BLOCKED_EXTERNAL_CONFIGURATION",
            "message": (
                "Tính năng gửi mã khôi phục qua email hiện chưa được bật trên hệ thống này. "
                "Vui lòng liên hệ giáo viên hoặc quản trị viên để được hỗ trợ đặt lại mật khẩu."
            ),
        }

    now = datetime.now(timezone.utc)
    expired_keys = [
        k
        for k, rec in _PASSWORD_RESET_TOKENS.items()
        if rec.get("used") or rec.get("expires_at", now) <= now
    ]
    for k in expired_keys:
        _PASSWORD_RESET_TOKENS.pop(k, None)

    user = caller.db.execute(
        select(User).where(User.email == clean_email)
    ).scalar_one_or_none()

    if user is not None:
        for rec in _PASSWORD_RESET_TOKENS.values():
            if rec.get("user_id") == user.id:
                rec["used"] = True
        raw_token = secrets.token_urlsafe(32)
        token_hash = _hash_reset_token(raw_token)
        _PASSWORD_RESET_TOKENS[token_hash] = {
            "user_id": user.id,
            "expires_at": now + PASSWORD_RESET_TTL,
            "used": False,
        }
        try:
            _send_password_reset_email(clean_email, raw_token)
        except Exception as exc:
            _PASSWORD_RESET_TOKENS.pop(token_hash, None)
            raise HTTPException(
                503,
                "Không thể gửi thư đặt lại mật khẩu lúc này. Vui lòng thử lại sau.",
            ) from exc

    return {
        "ok": True,
        "smtpConfigured": True,
        "deliveryStatus": "SENT",
        "message": (
            "Nếu địa chỉ email đã đăng ký trên Axo, hướng dẫn và mã đặt lại mật khẩu "
            "có hiệu lực 15 phút đã được gửi đến hộp thư của bạn."
        ),
    }


@router.post("/auth/reset-password")
def reset_password(body: ResetPasswordBody, caller: Caller = Depends(get_caller)):
    raw_token = (body.token or "").strip()
    now = datetime.now(timezone.utc)

    if raw_token:
        token_hash = _hash_reset_token(raw_token)
        rec = _PASSWORD_RESET_TOKENS.get(token_hash)
        if (
            rec is None
            or rec.get("used")
            or not isinstance(rec.get("expires_at"), datetime)
            or rec["expires_at"] <= now
        ):
            raise HTTPException(400, "Mã đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.")

        target_user = caller.db.get(User, int(rec["user_id"]))
        if target_user is None:
            rec["used"] = True
            raise HTTPException(400, "Mã đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.")

        try:
            service.set_password(caller.db, target_user, body.newPassword)
        except WeakPasswordError as exc:
            raise HTTPException(400, str(exc)) from exc

        target_user.must_change_password = False
        rec["used"] = True
        _revoke_user_sessions(caller.db, target_user.id)
        return {"ok": True, "updated": True}

    if caller.user is not None and caller.user.must_change_password:
        try:
            service.set_password(caller.db, caller.user, body.newPassword)
        except WeakPasswordError as exc:
            raise HTTPException(400, str(exc)) from exc
        caller.user.must_change_password = False
        caller.db.flush()
        return {"ok": True, "updated": True}

    raise HTTPException(
        400,
        "Vui lòng nhập mã khôi phục hợp lệ để đặt lại mật khẩu.",
    )


@router.get("/admin/overview")
def admin_overview(caller: Caller = Depends(get_caller)):
    caller.require_admin()
    _ensure_admin_tables(caller.db)
    settings = _load_system_settings(caller.db)
    users = caller.db.execute(select(User).order_by(User.created_at.desc())).scalars().all()
    classes = caller.db.execute(select(Classroom)).scalars().all()
    sessions = caller.db.execute(select(PracticeSession)).scalars().all()
    history_rows = caller.db.execute(select(LearningHistoryEntry)).scalars().all()
    cache_rows = caller.db.execute(select(SimulationCache)).scalars().all()
    telemetry_rows = (
        caller.db.execute(
            select(AdminAnalysisTelemetry).order_by(AdminAnalysisTelemetry.created_at.desc())
        )
        .scalars()
        .all()
    )

    user_list = [_user_public(u, caller.db) for u in users]
    active_count = sum(1 for u in user_list if u.get("status") != "suspended")
    suspended_count = len(user_list) - active_count
    student_users = [u for u in user_list if u.get("role") == "student"]
    teacher_users = [u for u in user_list if u.get("role") == "teacher"]
    admin_users = [u for u in user_list if u.get("role") == "admin"]
    student_count = len(student_users)
    teacher_count = len(teacher_users)
    admin_count = len(admin_users)
    ai_configured = bool(os.getenv("GEMINI_API_KEY", "").strip())
    configured_model_id = _configured_gemini_model_id()

    now_utc = datetime.now(timezone.utc)
    today_date = now_utc.date()
    day_keys = [(today_date - timedelta(days=offset)) for offset in range(6, -1, -1)]
    day_iso_set = {d.isoformat() for d in day_keys}

    def _row_date_iso(row: AdminAnalysisTelemetry) -> str:
        dt = row.created_at
        if dt is None:
            return ""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.date().isoformat()

    today_iso = today_date.isoformat()
    today_rows = [r for r in telemetry_rows if _row_date_iso(r) == today_iso]
    rows_7d = [r for r in telemetry_rows if _row_date_iso(r) in day_iso_set]
    measured_all = [r for r in telemetry_rows if bool(r.tokens_measured)]
    measured_today = [r for r in today_rows if bool(r.tokens_measured)]
    measured_7d = [r for r in rows_7d if bool(r.tokens_measured)]

    succeeded_total = sum(1 for r in telemetry_rows if r.outcome == "succeeded")
    refused_total = sum(1 for r in telemetry_rows if r.outcome == "refused")
    failed_total = sum(1 for r in telemetry_rows if r.outcome == "failed")
    succeeded_7d = sum(1 for r in rows_7d if r.outcome == "succeeded")
    refused_7d = sum(1 for r in rows_7d if r.outcome == "refused")
    failed_7d = sum(1 for r in rows_7d if r.outcome == "failed")

    avg_latency_ms = (
        round(sum(max(0, int(r.latency_ms or 0)) for r in telemetry_rows) / len(telemetry_rows))
        if telemetry_rows
        else None
    )
    avg_latency_7d_ms = (
        round(sum(max(0, int(r.latency_ms or 0)) for r in rows_7d) / len(rows_7d))
        if rows_7d
        else None
    )

    daily_breakdown: list[dict[str, Any]] = []
    for d in reversed(day_keys):
        d_iso = d.isoformat()
        d_rows = [r for r in rows_7d if _row_date_iso(r) == d_iso]
        d_meas = [r for r in d_rows if bool(r.tokens_measured)]
        daily_breakdown.append(
            {
                "dateIso": d_iso,
                "dateLabel": d.strftime("%d/%m/%Y"),
                "totalRequests": len(d_rows),
                "succeededRequests": sum(1 for r in d_rows if r.outcome == "succeeded"),
                "refusedRequests": sum(1 for r in d_rows if r.outcome == "refused"),
                "failedRequests": sum(1 for r in d_rows if r.outcome == "failed"),
                "avgLatencyMs": (
                    round(sum(max(0, int(r.latency_ms or 0)) for r in d_rows) / len(d_rows))
                    if d_rows
                    else None
                ),
                "tokensMeasured": bool(d_meas),
                "inputTokens": sum(int(r.input_tokens or 0) for r in d_meas) if d_meas else None,
                "outputTokens": sum(int(r.output_tokens or 0) for r in d_meas) if d_meas else None,
                "thoughtsTokens": sum(int(r.thoughts_tokens or 0) for r in d_meas) if d_meas else None,
                "totalTokens": sum(int(r.total_tokens or 0) for r in d_meas) if d_meas else None,
            }
        )

    return {
        "users": user_list,
        "stats": {
            "totalUsers": len(users),
            "activeUsers": active_count,
            "suspendedUsers": suspended_count,
            "studentCount": student_count,
            "teacherCount": teacher_count,
            "adminCount": admin_count,
            "totalClasses": len(classes),
            "totalSessions": len(sessions),
            "totalHistoryEntries": len(history_rows),
            "configuredModelId": configured_model_id,
            "totalAnalyses": len(telemetry_rows),
            "analysesToday": len(today_rows),
            "analyses7d": len(rows_7d),
            "aiRequestsToday": len(today_rows),
            "succeededRequests": succeeded_total,
            "refusedRequests": refused_total,
            "failedRequests": failed_total,
            "succeeded7d": succeeded_7d,
            "refused7d": refused_7d,
            "failed7d": failed_7d,
            "avgLatencyMs": avg_latency_ms,
            "avgLatency7dMs": avg_latency_7d_ms,
            "tokensMeasured": bool(measured_all),
            "tokensToday": (
                sum(int(r.total_tokens or 0) for r in measured_today)
                if measured_today
                else None
            ),
            "inputTokens7d": (
                sum(int(r.input_tokens or 0) for r in measured_7d)
                if measured_7d
                else None
            ),
            "outputTokens7d": (
                sum(int(r.output_tokens or 0) for r in measured_7d)
                if measured_7d
                else None
            ),
            "thoughtsTokens7d": (
                sum(int(r.thoughts_tokens or 0) for r in measured_7d)
                if measured_7d
                else None
            ),
            "totalTokens7d": (
                sum(int(r.total_tokens or 0) for r in measured_7d)
                if measured_7d
                else None
            ),
            "estimatedCostVnd": None,
            "aiServiceConfigured": ai_configured,
            "cachedProblems": len(cache_rows),
            "dailyBreakdown": daily_breakdown,
            "roleQuotaSummary": {
                "student": {
                    "count": student_count,
                    "usedToday": sum(int(u.get("usedToday", 0)) for u in student_users),
                    "dailyLimitDefault": int(settings.get("studentDailyLimit", 15)),
                },
                "teacher": {
                    "count": teacher_count,
                    "usedToday": sum(int(u.get("usedToday", 0)) for u in teacher_users),
                    "dailyLimitDefault": int(settings.get("teacherDailyLimit", 80)),
                },
                "admin": {
                    "count": admin_count,
                    "usedToday": sum(int(u.get("usedToday", 0)) for u in admin_users),
                    "dailyLimitDefault": 500,
                },
            },
        },
        "settings": settings,
        "auditLogs": _list_audit_logs(caller.db),
    }


@router.post("/admin/users")
def admin_create_user(body: AdminCreateUserBody, caller: Caller = Depends(get_caller)):
    admin_user = caller.require_admin()
    target_role = Role.TEACHER if body.role in ("teacher", "admin") else Role.STUDENT
    has_explicit_password = bool(body.password and body.password.strip())
    effective_password = (
        body.password.strip() if has_explicit_password else secrets.token_urlsafe(24)
    )
    try:
        u = service.create_user(
            caller.db,
            email=body.email,
            display_name=body.displayName,
            password=effective_password,
            role=target_role,
        )
        if body.role == "admin":
            u.role = "admin"
        if not has_explicit_password:
            u.must_change_password = True
        caller.db.flush()
    except (WeakPasswordError, ValueError) as exc:
        raise HTTPException(400, str(exc)) from exc

    meta_row = _ensure_user_meta_row(caller.db, u.id)
    if body.school is not None:
        meta_row.school = body.school.strip()[:160]
    if body.grade is not None:
        meta_row.grade = body.grade.strip()[:40]
    if body.className is not None:
        meta_row.class_name = body.className.strip()[:60]
    if body.workplace is not None:
        meta_row.workplace = body.workplace.strip()[:160]
    if body.subject is not None:
        meta_row.subject = body.subject.strip()[:120]
    if body.adminNote is not None:
        meta_row.admin_note = body.adminNote.strip()[:240]
    if body.status in ("active", "suspended", "pending_activation", "pending_teacher", "verified"):
        meta_row.status = body.status
    elif not has_explicit_password:
        meta_row.status = "pending_activation"
    elif u.role == "teacher":
        meta_row.status = "verified"
    else:
        meta_row.status = "active"
    eff_limit = body.customDailyLimit if body.customDailyLimit is not None else body.dailyLimit
    if eff_limit is not None and eff_limit > 0:
        meta_row.custom_daily_limit = eff_limit
    if body.tokenCap is not None and body.tokenCap >= 1000:
        meta_row.token_cap = body.tokenCap
    meta_row.updated_at = datetime.now(timezone.utc)
    caller.db.flush()

    _record_audit_log(
        caller.db,
        actor=admin_user.email,
        action="Tạo tài khoản mới",
        target=u.email,
        detail=f"Khởi tạo tài khoản vai trò {u.role} ({u.display_name}).",
        severity="info",
    )
    return {"user": _user_public(u, caller.db)}


@router.patch("/admin/users/{user_id}")
def admin_update_user(
    user_id: int, body: AdminUpdateUserBody, caller: Caller = Depends(get_caller)
):
    admin_user = caller.require_admin()
    u = caller.db.get(User, user_id)
    if u is None:
        raise HTTPException(404, "Không tìm thấy người dùng.")
    changes: list[str] = []
    if body.displayName is not None and body.displayName.strip():
        u.display_name = body.displayName.strip()[:120]
        changes.append(f"tên → {u.display_name}")
    role_changed = False
    if body.role in ("student", "teacher", "admin") and body.role != u.role:
        old_role = u.role
        u.role = body.role
        role_changed = True
        changes.append(f"vai trò {old_role} → {body.role}")
    meta_row = _ensure_user_meta_row(caller.db, u.id)

    resolved_status = body.status
    if resolved_status is None and body.isSuspended is not None:
        resolved_status = (
            "suspended"
            if body.isSuspended
            else ("verified" if u.role == "teacher" else "active")
        )
    if resolved_status is None and role_changed:
        current_status = meta_row.status
        if u.role == "teacher" and current_status in (None, "active", "pending_teacher"):
            resolved_status = "verified"
        elif u.role == "student" and current_status in ("verified", "pending_teacher"):
            resolved_status = "active"
    if resolved_status == "locked":
        resolved_status = "suspended"

    if resolved_status in ("active", "suspended", "pending_activation", "pending_teacher", "verified"):
        if resolved_status == "suspended" and u.id == admin_user.id:
            raise HTTPException(400, "Không thể tự khóa tài khoản Quản trị viên đang đăng nhập.")
        meta_row.status = resolved_status
        changes.append(f"trạng thái → {resolved_status}")
        if resolved_status == "suspended":
            _revoke_user_sessions(caller.db, u.id)

    if body.mustChangePassword is not None:
        u.must_change_password = bool(body.mustChangePassword)
        if body.mustChangePassword:
            meta_row.password_reset_requested_at = datetime.now(timezone.utc).strftime("%d/%m/%Y · %H:%M")
            changes.append("yêu cầu đổi mật khẩu")

    if body.school is not None:
        meta_row.school = body.school.strip()[:160]
    if body.grade is not None:
        meta_row.grade = body.grade.strip()[:40]
    if body.className is not None:
        meta_row.class_name = body.className.strip()[:60]
    if body.workplace is not None:
        meta_row.workplace = body.workplace.strip()[:160]
    if body.subject is not None:
        meta_row.subject = body.subject.strip()[:120]
    if body.adminNote is not None:
        meta_row.admin_note = body.adminNote.strip()[:240]

    eff_limit = body.customDailyLimit if body.customDailyLimit is not None else body.dailyLimit
    if eff_limit is not None and eff_limit > 0:
        meta_row.custom_daily_limit = eff_limit
        changes.append(f"hạn mức ngày → {eff_limit} lượt")
    if body.tokenCap is not None and body.tokenCap >= 1000:
        meta_row.token_cap = body.tokenCap
        changes.append(f"trần token → {body.tokenCap}")
    if body.bonusQuotaToday is not None and body.bonusQuotaToday >= 0:
        today_str = _utc_today_str()
        if meta_row.usage_date != today_str:
            meta_row.usage_date = today_str
            meta_row.used_today = 0
        meta_row.bonus_quota_today = body.bonusQuotaToday
        changes.append(f"lượt bổ sung hôm nay → +{body.bonusQuotaToday}")
    meta_row.updated_at = datetime.now(timezone.utc)
    caller.db.flush()

    if changes:
        _record_audit_log(
            caller.db,
            actor=admin_user.email,
            action="Cập nhật tài khoản",
            target=u.email,
            detail="Cập nhật: " + ", ".join(changes) + ".",
            severity="warning" if resolved_status == "suspended" else "info",
        )
    return {"user": _user_public(u, caller.db)}


@router.delete("/admin/users/{user_id}")
def admin_delete_user(user_id: int, caller: Caller = Depends(get_caller)):
    admin_user = caller.require_admin()
    u = caller.db.get(User, user_id)
    if u is None:
        raise HTTPException(404, "Không tìm thấy người dùng.")
    if u.id == admin_user.id:
        raise HTTPException(400, "Không thể tự xóa tài khoản Quản trị viên đang đăng nhập.")
    target_email = u.email
    target_name = u.display_name
    _ensure_admin_tables(caller.db)
    _revoke_user_sessions(caller.db, user_id)
    caller.db.execute(delete(UserAccountMeta).where(UserAccountMeta.user_id == user_id))
    caller.db.execute(delete(LearningHistoryEntry).where(LearningHistoryEntry.user_id == user_id))
    caller.db.delete(u)
    _USER_EXTRA_META.pop(user_id, None)
    caller.db.flush()
    _record_audit_log(
        caller.db,
        actor=admin_user.email,
        action="Xóa tài khoản",
        target=target_email,
        detail=f"Đã xóa tài khoản {target_name} ({target_email}).",
        severity="danger",
    )
    return {"ok": True}


def _parse_budget_vnd(raw_str: str | None, fallback: int) -> int:
    if raw_str is None:
        return fallback
    digits = "".join(ch for ch in str(raw_str) if ch.isdigit())
    return int(digits) if digits else 0


@router.put("/admin/settings")
def admin_update_settings(
    body: AdminSystemSettingsBody, caller: Caller = Depends(get_caller)
):
    admin_user = caller.require_admin()
    current_settings = _load_system_settings(caller.db)
    nested = body.settings if isinstance(body.settings, dict) else {}

    def _pick_int(keys: tuple[str, ...], current_key: str, lo: int, hi: int | None = None) -> int:
        for k in keys:
            val = getattr(body, k, None)
            if val is None and k in nested:
                val = nested[k]
            if val is not None:
                iv = int(val)
                if iv < lo or (hi is not None and iv > hi):
                    raise HTTPException(400, f"Giá trị cấu hình {k} không hợp lệ.")
                return iv
        return int(current_settings.get(current_key, lo))

    def _pick_bool(key: str, default: bool) -> bool:
        val = getattr(body, key, None)
        if val is None and key in nested:
            val = nested[key]
        if val is None:
            return bool(current_settings.get(key, default))
        return bool(val)

    student_daily = _pick_int(("studentDailyLimit", "studentDailyRequests"), "studentDailyLimit", 1, 500)
    teacher_daily = _pick_int(("teacherDailyLimit", "teacherDailyRequests"), "teacherDailyLimit", 1, 1000)
    student_tokens = _pick_int(("studentTokenLimit", "studentDailyTokens"), "studentTokenLimit", 1000)
    teacher_tokens = _pick_int(("teacherTokenLimit", "teacherDailyTokens"), "teacherTokenLimit", 1000)
    student_rpm = _pick_int(("studentRpmLimit", "studentRatePerMin"), "studentRpmLimit", 1, 120)
    teacher_rpm = _pick_int(("teacherRpmLimit", "teacherRatePerMin"), "teacherRpmLimit", 1, 120)
    guest_trial = _pick_int(("guestTrialLimit",), "guestTrialLimit", 0, 20)

    raw_budget_str = body.vndBudgetRaw
    if raw_budget_str is None and "vndBudgetRaw" in nested:
        raw_budget_str = str(nested["vndBudgetRaw"] or "")

    if body.monthlyBudgetVnd is not None:
        monthly_budget = int(body.monthlyBudgetVnd)
    elif "monthlyBudgetVnd" in nested and nested["monthlyBudgetVnd"] is not None:
        monthly_budget = int(nested["monthlyBudgetVnd"])
    elif raw_budget_str is not None:
        monthly_budget = _parse_budget_vnd(raw_budget_str, int(current_settings.get("monthlyBudgetVnd", 0)))
    else:
        monthly_budget = int(current_settings.get("monthlyBudgetVnd", 3000000))

    auto_cutoff = _pick_bool("autoCutoffEnabled", True)
    budget_cap_mode = (
        body.budgetCapMode
        or nested.get("budgetCapMode")
        or (
            "chặn yêu cầu mới & thông báo Quản trị viên"
            if auto_cutoff
            else "chỉ cảnh báo Quản trị viên"
        )
    )
    teacher_verify_mode = (
        body.teacherVerifyMode
        or nested.get("teacherVerifyMode")
        or str(current_settings.get("teacherVerifyMode", "cần Quản trị viên duyệt trước khi kích hoạt"))
    )
    maintenance_mode = _pick_bool("maintenanceMode", False)
    allow_registrations = _pick_bool("allowNewRegistrations", True)
    vnd_budget_display = (
        raw_budget_str.strip()
        if isinstance(raw_budget_str, str)
        else (f"{monthly_budget:,}".replace(",", ".") if monthly_budget > 0 else "")
    )

    now_iso = datetime.now(timezone.utc).isoformat()
    saved_settings = _save_system_settings(
        caller.db,
        {
            "studentDailyLimit": student_daily,
            "teacherDailyLimit": teacher_daily,
            "studentTokenLimit": student_tokens,
            "teacherTokenLimit": teacher_tokens,
            "studentRpmLimit": student_rpm,
            "teacherRpmLimit": teacher_rpm,
            "monthlyBudgetVnd": monthly_budget,
            "vndBudgetRaw": vnd_budget_display,
            "autoCutoffEnabled": auto_cutoff,
            "budgetCapMode": budget_cap_mode,
            "guestTrialLimit": guest_trial,
            "teacherVerifyMode": teacher_verify_mode,
            "maintenanceMode": maintenance_mode,
            "allowNewRegistrations": allow_registrations,
            "updatedAt": now_iso,
        },
    )
    _record_audit_log(
        caller.db,
        actor=admin_user.email,
        action="Cập nhật cài đặt hệ thống",
        target="Cấu hình toàn hệ thống",
        detail=(
            f"Hạn mức HS={student_daily}/ngày, GV={teacher_daily}/ngày, "
            f"Ngân sách dự kiến tháng={monthly_budget:,} VND."
        ),
        severity="info",
    )
    return {"ok": True, "settings": saved_settings}


@router.get("/admin/export/users")
def admin_export_users_csv(caller: Caller = Depends(get_caller)):
    admin_user = caller.require_admin()
    users = caller.db.execute(select(User).order_by(User.created_at.desc())).scalars().all()
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "ID",
            "Họ và tên",
            "Email",
            "Vai trò",
            "Trạng thái",
            "Trường / Đơn vị",
            "Hạn mức ngày",
            "Đã dùng hôm nay",
            "Bắt buộc đổi mật khẩu",
            "Ngày tạo",
        ]
    )
    for u in users:
        pub = _user_public(u, caller.db)
        org = (pub.get("school") or pub.get("workplace") or "").strip()
        writer.writerow(
            [
                _csv_safe_cell(pub["id"]),
                _csv_safe_cell(pub["displayName"]),
                _csv_safe_cell(pub["email"]),
                _csv_safe_cell(pub["role"]),
                _csv_safe_cell(pub["status"]),
                _csv_safe_cell(org),
                _csv_safe_cell(pub["dailyLimit"]),
                _csv_safe_cell(pub["usedToday"]),
                "Có" if pub["mustChangePassword"] else "Không",
                _csv_safe_cell(pub["createdAt"] or ""),
            ]
        )

    _record_audit_log(
        caller.db,
        actor=admin_user.email,
        action="Xuất danh sách tài khoản",
        target=f"{len(users)} tài khoản",
        detail="Xuất tệp CSV danh sách tài khoản người dùng (đã ẩn trường nhạy cảm).",
        severity="info",
    )
    date_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
    csv_bytes = buf.getvalue().encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="axo-danh-sach-tai-khoan-{date_tag}.csv"',
            "Cache-Control": "no-store",
        },
    )


@router.get("/admin/export/audit-logs")
def admin_export_audit_logs_csv(caller: Caller = Depends(get_caller)):
    admin_user = caller.require_admin()
    existing_logs = _list_audit_logs(caller.db)
    _record_audit_log(
        caller.db,
        actor=admin_user.email,
        action="Xuất nhật ký quản trị",
        target=f"{len(existing_logs)} bản ghi",
        detail="Xuất tệp CSV nhật ký thao tác quản trị hệ thống.",
        severity="info",
    )
    logs_for_export = _list_audit_logs(caller.db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "ID",
            "Thời gian",
            "Quản trị viên",
            "Thao tác",
            "Đối tượng",
            "Mức độ",
            "Chi tiết",
        ]
    )
    for item in logs_for_export:
        writer.writerow(
            [
                _csv_safe_cell(item.get("id", "")),
                _csv_safe_cell(item.get("timestamp") or item.get("time") or ""),
                _csv_safe_cell(item.get("actor", "")),
                _csv_safe_cell(item.get("action", "")),
                _csv_safe_cell(item.get("target", "")),
                _csv_safe_cell(item.get("severity", "info")),
                _csv_safe_cell(item.get("detail", "")),
            ]
        )

    date_tag = datetime.now(timezone.utc).strftime("%Y%m%d")
    csv_bytes = buf.getvalue().encode("utf-8-sig")
    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="axo-nhat-ky-quan-tri-{date_tag}.csv"',
            "Cache-Control": "no-store",
        },
    )
