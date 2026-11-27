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
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

def _app_deps():
    from app.accounts import service as accounts_service
    from app.accounts.passwords import WeakPasswordError
    from app.persistence.classroom_models import User
    from app.persistence.db import Base, sqlite_owns_schema

    return accounts_service, WeakPasswordError, User, Base, sqlite_owns_schema


def _load_admin_dotenv(*, env_file: Path | None = None, no_dotenv: bool = False) -> None:
    if no_dotenv or os.getenv("ALGOSIM_MANAGE_ADMIN_NO_DOTENV", "").strip() == "1":
        # Neo trước các khóa nhạy cảm để `app.persistence.db` (`load_dotenv(..., override=False)`) không nạp nhầm backend/.env cục bộ.
        os.environ.setdefault("ADMIN_PASSWORD", "")
        os.environ.setdefault("ADMIN_EMAIL", "")
        os.environ.setdefault("ADMIN_USERNAME", "admin")
        return
    if env_file is not None:
        if not env_file.is_file():
            raise FileNotFoundError(f"Không tìm thấy tệp môi trường: {env_file}")
        load_dotenv(env_file, override=False)
        os.environ.setdefault("ADMIN_PASSWORD", "")
        os.environ.setdefault("ADMIN_EMAIL", "")
        os.environ.setdefault("ADMIN_USERNAME", "admin")
        return
    load_dotenv(BACKEND_ROOT / ".env", override=False)


def _resolve_db_url(
    explicit_url: str | None,
    *,
    env_file: Path | None = None,
    no_dotenv: bool = False,
) -> str:
    isolated = bool(no_dotenv or env_file is not None or os.getenv("ALGOSIM_MANAGE_ADMIN_NO_DOTENV", "").strip() == "1")
    if explicit_url and explicit_url.strip():
        resolved = explicit_url.strip()
        if isolated:
            os.environ.setdefault("DATABASE_URL", resolved)
        return resolved
    _load_admin_dotenv(env_file=env_file, no_dotenv=no_dotenv)
    env_url = os.getenv("DATABASE_URL", "").strip()
    resolved = env_url if env_url else f"sqlite:///{(BACKEND_ROOT / 'algosim.db').as_posix()}"
    if isolated:
        os.environ.setdefault("DATABASE_URL", resolved)
    return resolved


def _make_engine(db_url: str):
    _, _, _, Base, sqlite_owns_schema = _app_deps()
    kwargs = {"connect_args": {"check_same_thread": False}} if db_url.startswith("sqlite") else {"pool_pre_ping": True}
    eng = create_engine(db_url, future=True, **kwargs)
    if sqlite_owns_schema(eng):
        Base.metadata.create_all(eng)
    return eng


def _mask_email(email: str | None) -> str | None:
    """Che bớt email khi in chẩn đoán (đủ để nhận diện, không lộ toàn bộ địa chỉ trong log/terminal chia sẻ)."""
    if not email or "@" not in email:
        return None
    local, domain = email.split("@", 1)
    return f"{local[:2]}***@{domain}"


def _database_target(db_url: str) -> dict[str, object]:
    """Mô tả CSDL đích KHÔNG kèm thông tin đăng nhập."""
    url = make_url(db_url)
    if url.get_backend_name() == "sqlite":
        return {"dialect": "sqlite", "database": Path(url.database or "").name or ":memory:"}
    return {"dialect": url.get_backend_name(), "host": url.host, "port": url.port, "database": url.database}


def inspect_admin_state(db_url: str) -> dict[str, object]:
    """Chẩn đoán CHỈ ĐỌC: không tạo bảng, không tạo tệp SQLite, không ghi gì vào CSDL."""
    accounts_service, _, User, _, _ = _app_deps()
    from app.accounts.passwords import verify_password

    username = accounts_service.configured_admin_username()
    env_email = accounts_service.configured_admin_email()
    env_password = os.getenv("ADMIN_PASSWORD", "")
    resolved_email: str | None = None
    state: dict[str, object] = {
        "databaseTarget": _database_target(db_url),
        "schemaReady": False,
        "alembicRevision": None,
        "adminCount": 0,
        "ambiguous": False,
        "configuredUsername": username,
        "usernameAliasValid": bool(username),
        "configuredEmailEnv": _mask_email(env_email),
        "envAdminPasswordPresent": bool(env_password.strip()),
        "configuredPasswordMatchesStoredHash": None,
        "resolvedAdmin": None,
        "admins": [],
    }
    url = make_url(db_url)
    if url.get_backend_name() == "sqlite" and url.database and not Path(url.database).is_file():
        state.update(diagnosis="SCHEMA_MISSING", nextStep="Khởi động backend một lần để tạo CSDL, rồi chạy --apply --create-if-missing.")
        return state
    kwargs = {"connect_args": {"check_same_thread": False}} if db_url.startswith("sqlite") else {"pool_pre_ping": True}
    eng = create_engine(db_url, future=True, **kwargs)
    try:
        tables = set(inspect(eng).get_table_names())
        if "alembic_version" in tables:
            with eng.connect() as conn:
                state["alembicRevision"] = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
        if "users" not in tables:
            state.update(diagnosis="SCHEMA_MISSING", nextStep="Chạy migration (alembic upgrade head) hoặc khởi động backend trước.")
            return state
        state["schemaReady"] = True
        Session = sessionmaker(bind=eng, autoflush=False, autocommit=False, future=True)
        with Session() as db:
            admins = db.execute(select(User).where(User.role == "admin").order_by(User.id.asc())).scalars().all()
            resolved = accounts_service.resolve_admin_user(db)
            resolved_email = resolved.email if resolved is not None else None
            state["adminCount"] = len(admins)
            state["ambiguous"] = len(admins) > 1 and resolved is None
            public = lambda u: {"id": u.id, "email": _mask_email(u.email), "displayName": u.display_name, "role": u.role}
            state["admins"] = [public(a) for a in admins]
            state["resolvedAdmin"] = public(resolved) if resolved is not None else None
            if resolved is not None and env_password.strip():
                state["configuredPasswordMatchesStoredHash"] = bool(verify_password(env_password.strip(), resolved.password_hash))
            db.rollback()
    finally:
        eng.dispose()

    if state["adminCount"] == 0:
        diagnosis, hint = "ADMIN_NOT_CREATED", "Chạy: python scripts/manage_admin.py --apply --create-if-missing"
    elif state["ambiguous"]:
        diagnosis, hint = "MULTIPLE_ADMINS", "Có nhiều tài khoản Admin; chỉ định --email của tài khoản cần giữ và rà soát thủ công."
    elif not state["usernameAliasValid"] or (env_email and resolved_email is not None and env_email != resolved_email):
        diagnosis, hint = "ADMIN_CONFIGURATION_MISMATCH", "ADMIN_USERNAME/ADMIN_EMAIL không khớp tài khoản Admin trong CSDL; chạy --apply để đồng bộ."
    elif state["configuredPasswordMatchesStoredHash"] is False:
        diagnosis, hint = "ADMIN_PASSWORD_NOT_SYNCHRONIZED", "ADMIN_PASSWORD trong môi trường khác mật khẩu đã lưu; chạy --apply nếu muốn đồng bộ."
    else:
        diagnosis, hint = "OK", None
    state["diagnosis"] = diagnosis
    state["nextStep"] = hint
    return state


def apply_admin_update(
    db_url: str,
    *,
    password: str,
    email: str | None = None,
    display_name: str | None = None,
    create_if_missing: bool = False,
) -> dict[str, object]:
    accounts_service, _, _, _, _ = _app_deps()
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
    dotenv_group = parser.add_mutually_exclusive_group()
    dotenv_group.add_argument(
        "--no-dotenv",
        action="store_true",
        help="Không tự nạp backend/.env (chỉ đọc biến môi trường tiến trình — dùng cho kiểm thử cô lập/CI).",
    )
    dotenv_group.add_argument(
        "--env-file",
        default=None,
        help="Đường dẫn tới tệp .env chỉ định thay cho backend/.env mặc định.",
    )
    parser.add_argument("--json", action="store_true", help="Xuất kết quả JSON (không bao giờ chứa mật khẩu).")
    args = parser.parse_args(argv)

    env_path = Path(args.env_file).expanduser().resolve() if args.env_file else None
    try:
        _load_admin_dotenv(env_file=env_path, no_dotenv=bool(args.no_dotenv))
        db_url = _resolve_db_url(
            args.database_url,
            env_file=env_path,
            no_dotenv=bool(args.no_dotenv),
        )
    except FileNotFoundError as exc:
        print(f"LỖI: {exc}", file=sys.stderr)
        return 2

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
    _, WeakPasswordError, _, _, _ = _app_deps()
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
