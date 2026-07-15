# -*- coding: utf-8 -*-
"""Alembic environment — nguồn tiến hoá schema cho DB BỀN (Postgres deploy).

Nguyên tắc chống trôi (drift): KHÔNG khai URL hay model ở đây. Tất cả lấy TỪ
`app.persistence.db` — cùng một `DATABASE_URL` và cùng `Base.metadata` mà app
dùng lúc chạy. Nhờ vậy `alembic revision --autogenerate` luôn so với đúng model
thật, và migration chạy đúng DB mà app sẽ kết nối.

render_as_batch cho SQLite: SQLite không ALTER trực tiếp được, batch mode tái
tạo bảng để đổi cột — nhờ đó cùng một migration chạy được trên CẢ hai dialect.
"""

from __future__ import annotations

from logging.config import fileConfig

from alembic import context

# Import model + URL của app (db.py tự load_dotenv lúc import)
from app.persistence.db import DATABASE_URL, IS_SQLITE, Base, engine

config = context.config

# Ghi đè URL trong alembic.ini bằng URL thật của app (không hardcode thông tin
# kết nối vào file cấu hình version-controlled).
config.set_main_option("sqlalchemy.url", DATABASE_URL)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Sinh SQL không cần kết nối (alembic upgrade --sql)."""
    context.configure(
        url=DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=IS_SQLITE,
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
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
