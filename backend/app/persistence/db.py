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


def _now() -> datetime:
    return datetime.now(timezone.utc)


class SimulationCache(Base):
    """Exact validated cache (M7.13B tầng 1) — thay bảng `problems` cũ.

    Version để ở CỘT (không nướng vào key như trước): row cũ vẫn nhìn thấy
    được để dọn/thống kê, lookup lọc theo version → version lệch = miss,
    không dùng mù. Chỉ lưu envelope status == "ok" (M7.8).
    Bảng `problems` cũ thành orphan vô hại trong volume hiện có — KHÔNG tự
    xóa volume; muốn dọn hẳn thì `docker compose down -v` thủ công.
    """

    __tablename__ = "simulation_cache"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # SHA-256 của đề đã chuẩn hóa (thường hóa chữ, gộp khoảng trắng)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    problem_text: Mapped[str] = mapped_column(Text)
    simulation_id: Mapped[str] = mapped_column(String(80))
    envelope_json: Mapped[str] = mapped_column(Text)
    dsl_version: Mapped[str] = mapped_column(String(16))
    policy_version: Mapped[str] = mapped_column(String(16))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    last_used_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    hit_count: Mapped[int] = mapped_column(Integer, default=0)


class SimulationPattern(Base):
    """Validated reusable pattern (M7.13B tầng 2) — template spec tổng quát
    với slot tham số, identity = pattern_key (hash chữ ký cấu trúc gồm
    scene_mode/roles/object types/rule types+ops/process types/interaction
    types+target types). status: candidate|validated|verified|deprecated —
    chỉ verified/validated được auto-reuse, verified ưu tiên trước."""

    __tablename__ = "simulation_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    pattern_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(160))
    signature_json: Mapped[str] = mapped_column(Text)
    scene_mode: Mapped[str] = mapped_column(String(16), index=True)
    semantic_roles: Mapped[str] = mapped_column(String(200), index=True)  # roles sorted, nối bằng ","
    template_json: Mapped[str] = mapped_column(Text)
    parameter_schema_json: Mapped[str] = mapped_column(Text)
    dsl_version: Mapped[str] = mapped_column(String(16))
    policy_version: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="candidate")
    usage_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_now)


class ReuseMetric(Base):
    """Counter nhẹ chứng minh reuse giảm số call LLM (M7.13B §metrics)."""

    __tablename__ = "reuse_metrics"

    name: Mapped[str] = mapped_column(String(64), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, default=0)


def bump_metric(session, name: str, delta: int = 1) -> None:
    row = session.get(ReuseMetric, name)
    if row is None:
        session.add(ReuseMetric(name=name, count=delta))
    else:
        row.count += delta


def read_metrics(session) -> dict[str, int]:
    return {r.name: r.count for r in session.query(ReuseMetric).all()}


def init_db() -> None:
    Base.metadata.create_all(engine)


def db_dialect() -> str:
    return engine.dialect.name
