# -*- coding: utf-8 -*-
"""Khởi tạo hoặc đặt lại cơ sở dữ liệu trình diễn Axo với đúng 3 tài khoản đại diện.

Nguyên tắc an toàn dữ liệu (§8.3):
- Tuyệt đối KHÔNG hardcode mật khẩu hoặc thông tin bí mật trong mã nguồn được commit.
- Mật khẩu đọc từ biến môi trường (`AXO_DEMO_ADMIN_PASSWORD`, `AXO_DEMO_TEACHER_PASSWORD`,
  `AXO_DEMO_STUDENT_PASSWORD`) hoặc tự sinh ngẫu nhiên an toàn bằng `secrets.token_urlsafe`.
- Khi truyền `--receipt-out <path>`, biên nhận cục bộ (nằm ngoài vùng commit) ghi lại thông tin
  đăng nhập vừa sinh để phục vụ kiểm thử E2E/trình diễn mà không lưu vào kho Git.
- Từ chối ghi đè nếu cơ sở dữ liệu chứa tài khoản không phải dữ liệu seed/kiểm thử trừ khi
  truyền cờ tường minh `--reset-demo-db` sau khi đã sao lưu.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.accounts import service as accounts_service  # noqa: E402
from app.accounts.policy import Role  # noqa: E402
from app.persistence.classroom_models import (  # noqa: E402
    AdminAnalysisTelemetry,
    AdminAuditLogEntry,
    AdminSystemSetting,
    Assignment,
    AuthSession,
    ClassMembership,
    Classroom,
    ClassroomSession,
    LearningHistoryEntry,
    PracticeSession,
    User,
    UserAccountMeta,
)
from app.persistence.db import Base  # noqa: E402

REPRESENTATIVE_ACCOUNTS: tuple[dict[str, str], ...] = (
    {
        "slot": "admin",
        "env_email": "AXO_DEMO_ADMIN_EMAIL",
        "default_email": "admin@axo.edu.vn",
        "env_password": "AXO_DEMO_ADMIN_PASSWORD",
        "display_name": "Quản trị viên Axo",
        "role": "admin",
        "status": "active",
        "school": "Hệ thống Axo",
        "workplace": "Hệ thống Axo",
        "subject": "Quản trị hệ thống",
    },
    {
        "slot": "teacher",
        "env_email": "AXO_DEMO_TEACHER_EMAIL",
        "default_email": "giaovien@axo.edu.vn",
        "env_password": "AXO_DEMO_TEACHER_PASSWORD",
        "display_name": "Cô Nguyễn Thu Hà",
        "role": "teacher",
        "status": "verified",
        "school": "THPT Chu Văn An",
        "workplace": "THPT Chu Văn An",
        "subject": "Toán Hình học không gian",
    },
    {
        "slot": "student",
        "env_email": "AXO_DEMO_STUDENT_EMAIL",
        "default_email": "hocsinh@axo.edu.vn",
        "env_password": "AXO_DEMO_STUDENT_PASSWORD",
        "display_name": "Trần Minh Khoa",
        "role": "student",
        "status": "active",
        "school": "THPT Chu Văn An",
        "grade": "Lớp 11",
        "class_name": "11A1",
        "subject": "Toán Hình học không gian",
    },
)

KNOWN_EPHEMERAL_EMAIL_DOMAINS: tuple[str, ...] = (
    "@axo.edu.vn",
    "@truong.edu.vn",
    "@example.com",
    "@test.local",
)


def _generate_runtime_password() -> str:
    return f"Axo-{secrets.token_urlsafe(12)}"


def _is_known_seed_or_test_email(email: str) -> bool:
    lower = email.strip().lower()
    return any(lower.endswith(dom) for dom in KNOWN_EPHEMERAL_EMAIL_DOMAINS)


def seed_three_demo_accounts(
    db_path: Path,
    *,
    reset_demo_db: bool = False,
    receipt_out: Path | None = None,
) -> list[dict[str, str]]:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path.as_posix()}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

    issued: list[dict[str, str]] = []
    now_dt = datetime.now(timezone.utc)

    with Session() as db:
        existing_users = db.execute(select(User)).scalars().all()
        unknown_users = [
            u.email for u in existing_users if not _is_known_seed_or_test_email(u.email)
        ]
        if unknown_users and not reset_demo_db:
            raise RuntimeError(
                "Phát hiện tài khoản không thuộc tập kiểm thử/seed đã xác minh: "
                + ", ".join(unknown_users)
                + ". Dừng an toàn để không xóa nhầm dữ liệu thật."
            )

        # Dọn sạch các bảng phụ thuộc theo đúng thứ tự khóa ngoại trước khi ghi 3 tài khoản đại diện
        for model in (
            PracticeSession,
            ClassroomSession,
            Assignment,
            ClassMembership,
            Classroom,
            LearningHistoryEntry,
            AuthSession,
            UserAccountMeta,
            AdminAnalysisTelemetry,
            AdminAuditLogEntry,
            AdminSystemSetting,
            User,
        ):
            db.execute(delete(model))
        db.flush()

        for spec in REPRESENTATIVE_ACCOUNTS:
            email = os.getenv(spec["env_email"], spec["default_email"]).strip().lower()
            raw_pw = os.getenv(spec["env_password"], "").strip() or _generate_runtime_password()
            base_role = Role.TEACHER if spec["role"] in ("teacher", "admin") else Role.STUDENT
            user = accounts_service.create_user(
                db,
                email=email,
                display_name=spec["display_name"],
                password=raw_pw,
                role=base_role,
            )
            if spec["role"] == "admin":
                user.role = "admin"
            user.must_change_password = False
            db.flush()

            db.add(
                UserAccountMeta(
                    user_id=user.id,
                    status=spec["status"],
                    school=spec.get("school", ""),
                    grade=spec.get("grade", ""),
                    class_name=spec.get("class_name", ""),
                    workplace=spec.get("workplace", ""),
                    subject=spec.get("subject", "Toán Hình học không gian"),
                    usage_date=now_dt.strftime("%Y-%m-%d"),
                    used_today=0,
                    bonus_quota_today=0,
                    updated_at=now_dt,
                )
            )
            issued.append(
                {
                    "slot": spec["slot"],
                    "id": str(user.id),
                    "email": user.email,
                    "displayName": user.display_name,
                    "role": user.role,
                    "status": spec["status"],
                    "password": raw_pw,
                }
            )

        db.add(
            AdminAuditLogEntry(
                audit_key=f"audit-1-{int(now_dt.timestamp())}",
                timestamp_display=now_dt.strftime("%d/%m/%Y · %H:%M"),
                time_ts=int(now_dt.timestamp() * 1000) * 1000 + 1,
                actor="system@axo.edu.vn",
                action="Khởi tạo dữ liệu trình diễn",
                target="3 tài khoản đại diện",
                detail="Khởi tạo sạch 1 Quản trị viên, 1 Giáo viên và 1 Học sinh.",
                severity="info",
                created_at=now_dt,
            )
        )
        db.commit()

    engine.dispose()

    if receipt_out is not None:
        receipt_out.parent.mkdir(parents=True, exist_ok=True)
        receipt_out.write_text(
            json.dumps(
                {
                    "dbPath": str(db_path),
                    "seededAtUtc": now_dt.isoformat(),
                    "accountCount": len(issued),
                    "accounts": issued,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    return issued


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(
        description="Khởi tạo cơ sở dữ liệu trình diễn Axo với đúng 3 tài khoản đại diện."
    )
    parser.add_argument(
        "--db-path",
        type=Path,
        default=BACKEND_ROOT / "algosim.db",
        help="Đường dẫn tệp SQLite cần khởi tạo.",
    )
    parser.add_argument(
        "--reset-demo-db",
        action="store_true",
        help="Xác nhận đặt lại cơ sở dữ liệu trình diễn sau khi đã sao lưu.",
    )
    parser.add_argument(
        "--receipt-out",
        type=Path,
        default=None,
        help="Đường dẫn biên nhận cục bộ (ngoài Git) để lưu thông tin đăng nhập sinh ngẫu nhiên.",
    )
    args = parser.parse_args()
    accounts = seed_three_demo_accounts(
        args.db_path.resolve(),
        reset_demo_db=args.reset_demo_db,
        receipt_out=args.receipt_out.resolve() if args.receipt_out else None,
    )
    summary = [
        {"id": a["id"], "role": a["role"], "email": a["email"], "displayName": a["displayName"]}
        for a in accounts
    ]
    print(json.dumps({"ok": True, "count": len(summary), "accounts": summary}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
