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
