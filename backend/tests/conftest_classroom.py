# -*- coding: utf-8 -*-
"""Đồ nghề chung cho test tầng tài khoản/lớp học (M18).

MỖI TEST MỘT DATABASE RIÊNG, trong bộ nhớ trên đĩa tạm. Vì sao không dùng chung
`algosim.db` của dev: test tạo tài khoản và lớp, mà `users.email` là UNIQUE —
chạy hai lần trên cùng file sẽ đỏ ở lần thứ hai vì lý do không liên quan đến
điều đang kiểm. Test phải kể cùng một câu chuyện mỗi lần chạy.

KHÔNG có mật khẩu production nào ở đây (`§34`): mọi thông tin đăng nhập là dữ
liệu test sinh tại chỗ.
"""

from __future__ import annotations

import secrets
import tempfile
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Generated per test session: no credential-shaped literal in the repository (publication scan `HARDCODED_PASSWORD`).
TEST_PASSWORD = "t" + secrets.token_hex(8)


@pytest.fixture()
def api(monkeypatch):
    """FastAPI client trên một DB trống hoàn toàn.

    ĐỔI CHỖ `SessionLocal`, KHÔNG nạp lại module. Bản đầu dùng
    `importlib.reload` để `create_engine` ở tầng module đọc `DATABASE_URL` mới,
    và nó hỏng ngay: nạp lại `classroom_models` đăng ký lại `users` lên cùng một
    `MetaData` → `Table 'users' is already defined`. Nạp lại module trong một
    tiến trình đã import chúng là công cụ sai cho việc này.

    Chỉ có HAI nơi mở phiên DB (`app.main` và `app.accounts.router`), nên trỏ
    lại đúng hai cái tên đó là đủ, và nó không đụng gì tới metadata.
    """
    import app.accounts.router as router_mod
    import app.main as main_mod
    import app.persistence.classroom_models  # noqa: F401  (đăng ký bảng)
    from app.persistence import db as db_mod

    tmpdir = Path(tempfile.mkdtemp(prefix="algosim-test-"))
    db_path = tmpdir / f"{uuid.uuid4().hex}.db"
    # Mã giáo viên: cố định trong test để kiểm được cả nhánh đúng lẫn nhánh sai.
    monkeypatch.setenv("ALGOSIM_TEACHER_SIGNUP_CODE", "MA-GIAO-VIEN-TEST")

    # A file DB with the default pool: one connection per thread, like the product engine
    # (`app.persistence.db._engine_kwargs`). `StaticPool` shared ONE sqlite3 connection between the threads of
    # concurrent requests, which interleaved their cursors (FlushError "NULL identity key", IndexError) — the
    # T3 flake of `test_overlapping_analyses_are_charged_only_their_own_tokens` (run
    # axo-final-reliability-premerge-gate).
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    db_mod.Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(router_mod, "SessionLocal", TestSession)
    monkeypatch.setattr(main_mod, "SessionLocal", TestSession)

    with TestClient(main_mod.app) as client:
        yield client
    engine.dispose()


def register(client, *, email: str, name: str, role: str | None = None,
             teacher_code: str | None = None, password: str = TEST_PASSWORD):
    body = {"email": email, "displayName": name, "password": password}
    if role is not None:
        body["role"] = role
    if teacher_code is not None:
        body["teacherCode"] = teacher_code
    return client.post("/api/auth/register", json=body)


def login(client, *, email: str, password: str = TEST_PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def new_client(api) -> TestClient:
    """Một trình duyệt KHÁC (cookie jar riêng) trên cùng ứng dụng.

    Cần cho mọi bài kiểm uỷ quyền: hai vai phải là hai phiên độc lập, nếu dùng
    chung client thì đăng nhập sau ghi đè cookie trước và bài kiểm mất nghĩa.
    """
    return TestClient(api.app)
