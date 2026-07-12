"""Ngân hàng bài (R2.3e) trên SQLAlchemy.

Mặc định SQLite (không cần cài gì, demo offline được). Đặt DATABASE_URL trong
backend/.env để chuyển sang PostgreSQL mà không đổi một dòng code nào, ví dụ:
    DATABASE_URL=postgresql+psycopg2://user:password@localhost:5432/algosim
(cần cài thêm: pip install psycopg2-binary)
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

# Nạp backend/.env trước khi đọc biến môi trường
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./algosim.db")

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    pass


class Problem(Base):
    """Một bài toán đã phân tích — đề trùng không gọi lại API (R2.3e)."""

    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # SHA-256 của đề đã chuẩn hóa (thường hóa chữ, gộp khoảng trắng)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    problem_text: Mapped[str] = mapped_column(Text)
    # ValidatedSimulationEnvelope (M3) — đổi tên cột nên cần docker compose down -v một lần
    envelope_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


def init_db() -> None:
    Base.metadata.create_all(engine)


def db_dialect() -> str:
    return engine.dialect.name
