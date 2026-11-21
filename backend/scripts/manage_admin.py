# -*- coding: utf-8 -*-
"""Công cụ vận hành có kiểm soát để kiểm tra hoặc xoay thông tin tài khoản Admin Axo.

Nguyên tắc an toàn:
- KHÔNG tự động chạy khi backend khởi động.
- KHÔNG chứa mật khẩu mặc định hay mật khẩu hardcode.
- KHÔNG in mật khẩu thô hoặc password_hash ra màn hình / log.
- Bảo toàn tuyệt đối dữ liệu các tài khoản khác, lịch sử và nhật ký quản trị;
  tái sử dụng đúng 1 tài khoản `role == 'admin'` hiện có (không tạo bản ghi trùng lặp).
- Khi đổi mật khẩu thành công, tự động thu hồi mọi phiên đăng nhập cũ của Admin đó.
- An toàn khi chạy lặp lại (idempotent).

Cách sử dụng:
  1. Kiểm tra trạng thái tài khoản Admin hiện tại (chỉ đọc):
       python scripts/manage_admin.py --check
  2. Cập nhật mật khẩu/email cho tài khoản Admin hiện có (đọc từ ADMIN_PASSWORD / ADMIN_EMAIL
     trong backend/.env hoặc môi trường, hoặc nhập tương tác an toàn qua getpass):
       python scripts/manage_admin.py --apply
  3. Khởi tạo mới duy nhất 1 Admin trên DB hoàn toàn trống (khi chưa có tài khoản Admin nào):
       python scripts/manage_admin.py --apply --create-if-missing
  4. Kiểm thử trên một DB cô lập (không chạm DB chính):
       python scripts/manage_admin.py --database-url sqlite:///path/to/test.db --apply --create-if-missing
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from app.accounts import service as accounts_service  # noqa: E402
from app.accounts.passwords import WeakPasswordError  # noqa: E402
from app.persistence.classroom_models import User  # noqa: E402
from app.persistence.db import Base, sqlite_owns_schema  # noqa: E402


def _resolve_db_url(explicit_url: str | None) -> str:
    if explicit_url and explicit_url.strip():
        return explicit_url.strip()
    load_dotenv(BACKEND_ROOT / ".env", override=False)
    env_url = os.getenv("DATABASE_URL", "").strip()
    if env_url:
        return env_url
    return f"sqlite:///{(BACKEND_ROOT / 'algosim.db').as_posix()}"


def _make_engine(db_url: str):
    kwargs = {"connect_args": {"check_same_thread": False}} if db_url.startswith("sqlite") else {"pool_pre_ping": True}
    eng = create_engine(db_url, future=True, **kwargs)
    if sqlite_owns_schema(eng):
        Base.metadata.create_all(eng)
    return eng


def inspect_admin_state(db_url: str) -> dict[str, object]:
    eng = _make_engine(db_url)
    Session = sessionmaker(bind=eng, autoflush=False, autocommit=False, future=True)
    try:
        with Session() as db:
            admins = (
                db.execute(select(User).where(User.role == "admin").order_by(User.id.asc()))
                .scalars()
                .all()
            )
            resolved = accounts_service.resolve_admin_user(db)
            return {
                "adminCount": len(admins),
                "ambiguous": len(admins) > 1 and resolved is None,
                "configuredUsername": accounts_service.configured_admin_username(),
                "configuredEmailEnv": accounts_service.configured_admin_email(),
                "resolvedAdmin": (
                    {
                        "id": resolved.id,
                        "email": resolved.email,
                        "displayName": resolved.display_name,
                        "role": resolved.role,
                    }
                    if resolved is not None
                    else None
                ),
                "admins": [
                    {
                        "id": a.id,
                        "email": a.email,
                        "displayName": a.display_name,
                        "role": a.role,
                    }
                    for a in admins
                ],
            }
    finally:
        eng.dispose()


def apply_admin_update(
    db_url: str,
    *,
    password: str,
    email: str | None = None,
    display_name: str | None = None,
    create_if_missing: bool = False,
) -> dict[str, object]:
    eng = _make_engine(db_url)
    Session = sessionmaker(bind=eng, autoflush=False, autocommit=False, future=True)
    try:
        with Session() as db:
            user, action, revoked = accounts_service.upsert_or_rotate_admin_credentials(
                db,
                password=password,
                email=email,
                display_name=display_name,
                create_if_missing=create_if_missing,
            )
            db.commit()
            return {
                "ok": True,
                "action": action,
                "adminId": user.id,
                "email": user.email,
                "username": accounts_service.configured_admin_username(),
                "role": user.role,
                "revokedSessions": revoked,
            }
    finally:
        eng.dispose()


def _is_interactive_stdin() -> bool:
    """Trả True chỉ khi stdin thực sự là terminal tương tác (không bị kẹt với NUL/DEVNULL trên Windows)."""
    if sys.stdin is None or getattr(sys.stdin, "closed", False):
        return False
    try:
        if not sys.stdin.isatty():
            return False
    except Exception:
        return False
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes

            handle = ctypes.windll.kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
            mode = wintypes.DWORD()
            return bool(ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)))
        except Exception:
            return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Kiểm tra hoặc cập nhật có kiểm soát tài khoản Admin Axo (không lưu mật khẩu hardcode)."
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true", help="Chỉ đọc và hiển thị trạng thái tài khoản Admin.")
    mode.add_argument("--apply", action="store_true", help="Cập nhật (hoặc khởi tạo) mật khẩu/email Admin.")
    parser.add_argument("--database-url", default=None, help="DATABASE_URL đích (mặc định đọc từ backend/.env hoặc SQLite cục bộ).")
    parser.add_argument("--email", default=None, help="Email Admin cần gán/chỉ định (mặc định đọc từ ADMIN_EMAIL nếu có).")
    parser.add_argument("--display-name", default=None, help="Tên hiển thị mới tuỳ chọn cho tài khoản Admin.")
    parser.add_argument(
        "--create-if-missing",
        action="store_true",
        help="Chỉ tạo duy nhất 1 tài khoản Admin mới khi DB hiện chưa có tài khoản Admin nào.",
    )
    parser.add_argument("--json", action="store_true", help="Xuất kết quả JSON (không bao giờ chứa mật khẩu).")
    args = parser.parse_args(argv)

    load_dotenv(BACKEND_ROOT / ".env", override=False)
    db_url = _resolve_db_url(args.database_url)

    if args.check:
        state = inspect_admin_state(db_url)
        print(json.dumps(state, ensure_ascii=False, indent=2))
        return 0

    raw_pw = os.getenv("ADMIN_PASSWORD", "").strip()
    if not raw_pw:
        if args.json or not _is_interactive_stdin():
            print(
                "LỖI: Chưa đặt biến môi trường ADMIN_PASSWORD và không có terminal tương tác để nhập mật khẩu.",
                file=sys.stderr,
            )
            return 2
        p1 = getpass.getpass("Nhập mật khẩu Admin mới (tối thiểu 8 ký tự): ")
        p2 = getpass.getpass("Xác nhận mật khẩu Admin mới: ")
        if p1 != p2:
            print("LỖI: Mật khẩu xác nhận không khớp.", file=sys.stderr)
            return 2
        raw_pw = p1

    target_email = args.email or os.getenv("ADMIN_EMAIL", "").strip() or None
    try:
        result = apply_admin_update(
            db_url,
            password=raw_pw,
            email=target_email,
            display_name=args.display_name,
            create_if_missing=bool(args.create_if_missing),
        )
    except (WeakPasswordError, ValueError) as exc:
        print(f"LỖI: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(
            f"[OK] action={result['action']} id={result['adminId']} "
            f"username={result['username']} email={result['email']} "
            f"revoked_sessions={result['revokedSessions']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
