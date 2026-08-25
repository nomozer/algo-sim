# -*- coding: utf-8 -*-
"""DB-HARDEN-2 — quyền sở hữu schema theo dialect.

Bất biến: `create_all()` CHỈ dành cho SQLite ephemeral (test/dev nhanh).
PostgreSQL bền → Alembic sở hữu tạo & tiến hoá schema; runtime KHÔNG được
lặng lẽ `create_all()` trên Postgres (nếu thiếu bảng thì phải là do chưa
`alembic upgrade head`, không được app tự vá bằng create_all).

Quyết định dựa trên metadata dialect thật của engine (`engine.dialect.name`),
KHÔNG string-check URL.
"""

from types import SimpleNamespace

from app.persistence import db


class _Spy:
    def __init__(self) -> None:
        self.calls: list = []

    def __call__(self, *args, **kwargs) -> None:
        self.calls.append((args, kwargs))


def test_sqlite_init_db_creates_schema(monkeypatch):
    """SQLite: init_db() vẫn dùng create_all() (zero-friction cho test/dev)."""
    spy = _Spy()
    monkeypatch.setattr(db.Base.metadata, "create_all", spy)

    assert db.engine.dialect.name == "sqlite"  # engine mặc định trong test
    db.init_db()

    assert len(spy.calls) == 1  # create_all được gọi đúng một lần cho SQLite


def test_postgres_init_db_does_not_create_all(monkeypatch):
    """PostgreSQL: init_db() KHÔNG create_all — Alembic sở hữu schema."""
    spy = _Spy()
    monkeypatch.setattr(db.Base.metadata, "create_all", spy)

    fake_pg = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))
    db.init_db(fake_pg)

    assert spy.calls == []  # Postgres: KHÔNG được tự tạo bảng


def test_schema_owner_decision_uses_dialect():
    """Quyết định chủ sở hữu schema dựa trên dialect, không phải URL string."""
    sqlite_eng = SimpleNamespace(dialect=SimpleNamespace(name="sqlite"))
    pg_eng = SimpleNamespace(dialect=SimpleNamespace(name="postgresql"))

    assert db.sqlite_owns_schema(sqlite_eng) is True
    assert db.sqlite_owns_schema(pg_eng) is False


def test_sqlite_engine_kwargs_has_no_pool_options(monkeypatch):
    """SQLite: chỉ check_same_thread, KHÔNG nhận pool option của Postgres."""
    monkeypatch.setattr(db, "IS_SQLITE", True)
    kwargs = db._engine_kwargs()

    assert kwargs == {"connect_args": {"check_same_thread": False}}
    for pg_only in ("pool_pre_ping", "pool_recycle", "pool_size", "max_overflow"):
        assert pg_only not in kwargs


def test_postgres_engine_kwargs_has_durable_pool(monkeypatch):
    """PostgreSQL: pool bền (pre_ping/recycle/size/overflow), KHÔNG check_same_thread."""
    monkeypatch.setattr(db, "IS_SQLITE", False)
    kwargs = db._engine_kwargs()

    assert kwargs["pool_pre_ping"] is True
    assert set(kwargs) == {"pool_pre_ping", "pool_recycle", "pool_size", "max_overflow"}
    assert "connect_args" not in kwargs


# ── SUITE CHẠY TRÊN DB RIÊNG, KHÔNG PHẢI DB CỦA DEV ────────────────────────
#
# ĐO ĐƯỢC 2026-08-25: một lượt `pytest` full treo quá 600 giây, trong khi lượt
# ngay trước đó mất 27 giây. Không phải test nào chậm — có BỐN tiến trình pytest
# cùng chạy (hai phiên làm việc song song) và cả bốn tranh nhau đúng một file
# `backend/algosim.db`. CPU gần như bằng không: chúng nằm chờ khoá SQLite.
#
# Hình dạng của lỗi mới là chỗ đắt: nó trông y hệt một test treo, nên người ta
# đi tìm test có lỗi. Không có thông báo, không có timeout, không có gì chỉ sang
# tiến trình kia.
#
# Cùng file dùng chung còn đẻ một lớp lỗi thứ hai đã cắn kho này rồi: trạng thái
# RÒ RỈ giữa các lượt chạy. `test_api.py` ghi lại một lỗi câm suốt nhiều lần bump
# `CACHE_VERSION` vì "test luôn chạy trên DB sạch", và nó chỉ lộ ra ở bump 36→37
# khi DB test còn hàng của lượt trước.
#
# Hai test dưới khoá hai nửa của cùng một tính chất: KHÔNG đụng DB của dev, và
# MỖI LƯỢT một file.


def test_suite_KHONG_chay_tren_DB_dung_chung_cua_dev():
    """Suite không được ghi vào `backend/algosim.db` — đó là DB của người dùng."""
    assert "algosim.db" not in db.DATABASE_URL, (
        f"pytest đang chạy trên DB dùng chung: {db.DATABASE_URL}"
    )


def test_hai_luot_pytest_SONG_SONG_khong_dung_chung_file():
    """Đường dẫn dẫn xuất từ PID, nên hai tiến trình không bao giờ đụng nhau."""
    import conftest

    assert conftest.duong_dan_db_test(111) != conftest.duong_dan_db_test(222)
