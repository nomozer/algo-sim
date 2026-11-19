# -*- coding: utf-8 -*-
"""Alembic environment — nguồn tiến hoá schema cho DB BỀN (Postgres deploy).

Nguyên tắc chống trôi (drift) + bảo vệ dữ liệu:
- KHÔNG khai URL hay model ở đây. Tất cả lấy TỪ `app.persistence.db` và
  `classroom_models` / `step_edit_models`.
- Cổng an toàn migration (`migration_preflight.py`) chặn migration phá hủy và DB
  chưa đóng dấu `alembic_version` trước mọi `upgrade` / `downgrade` trực tuyến.
- Các bảng Classroom cũ được giữ nguyên an toàn trong cơ sở dữ liệu hiện hữu và
  được loại trừ có chủ đích khỏi phép so drift autogenerate (`include_name`) để
  hệ không sinh lệnh xóa bảng dữ liệu lịch sử.
"""

from __future__ import annotations

import importlib.util
from logging.config import fileConfig
from pathlib import Path

from alembic import context

from app.persistence.db import DATABASE_URL, IS_SQLITE, Base, engine
from app.persistence import classroom_models, step_edit_models  # noqa: F401

_PREFLIGHT_PATH = Path(__file__).resolve().with_name("migration_preflight.py")
_PREFLIGHT_SPEC = importlib.util.spec_from_file_location("_axo_migration_preflight", _PREFLIGHT_PATH)
if _PREFLIGHT_SPEC is None or _PREFLIGHT_SPEC.loader is None:
    raise RuntimeError(f"Cannot load migration_preflight module from {_PREFLIGHT_PATH}")
_preflight = importlib.util.module_from_spec(_PREFLIGHT_SPEC)
_PREFLIGHT_SPEC.loader.exec_module(_preflight)

RETAINED_LEGACY_CLASSROOM_TABLES = _preflight.RETAINED_LEGACY_CLASSROOM_TABLES

config = context.config
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _include_name(name: str | None, type_: str, parent_names: dict) -> bool:
    """Ignore retained legacy Classroom tables during autogenerate / alembic check."""
    if type_ == "table" and name in RETAINED_LEGACY_CLASSROOM_TABLES:
        return False
    return True


def _run_online_preflight(connection) -> None:
    """Enforce migration safety gate right before executing upgrade, downgrade, or stamp."""
    mc = context.get_context()
    fn = mc.opts.get("fn")
    fn_name = getattr(fn, "__name__", "")
    if fn_name not in ("upgrade", "downgrade", "do_stamp"):
        return
    if mc.environment_context is None:
        return
    direction = "stamp" if fn_name == "do_stamp" else fn_name
    raw_dest = mc.environment_context.context_opts.get("destination_rev")
    if isinstance(raw_dest, (tuple, list)):
        target_rev = str(raw_dest[0]) if raw_dest else "head"
    else:
        target_rev = str(raw_dest or "head")
    purge = bool(mc.environment_context.context_opts.get("purge"))
    report = _preflight.evaluate_migration_safety(
        connection,
        config,
        direction=direction,
        target_rev=target_rev,
        purge=purge,
    )
    if not report["allowed"]:
        raise RuntimeError(
            f"MIGRATION_SAFETY_BLOCKED [{report['reason_code']}]: {report['message']}"
        )


def run_migrations_offline() -> None:
    """Sinh SQL không cần kết nối (alembic upgrade --sql)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=IS_SQLITE,
        include_name=_include_name,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Chạy migration qua kết nối thật (dùng chung engine đã cấu hình pool)."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=IS_SQLITE,
            include_name=_include_name,
        )
        _run_online_preflight(connection)
        if connection.in_transaction():
            connection.rollback()
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
