# -*- coding: utf-8 -*-
"""DB-HARDEN-2 — cổng chống trôi schema (Alembic drift gate).

Chứng minh: `Base.metadata` (model SQLAlchemy) ↔ head migration Alembic KHÔNG
lệch. Tương đương `alembic check`, nhưng CHẠY TỰ ĐỘNG trong suite offline mặc
định — dev đổi model mà quên tạo migration thì test này ĐỎ, không cần nhớ lệnh.

Cô lập & offline:
- Chạy trên **SQLite tạm** trong tmp_path (KHÔNG đụng DB dev/pgdata).
- SQLite đủ để so metadata↔migration (drift là khác biệt cấu trúc, không phụ
  thuộc dialect). Độ tin cậy dialect Postgres do test_postgres_integration lo.
- Không mạng, không AI, deterministic.

Proof cổng bắt được lỗi (fault injection) đã chạy tay: thêm một cột vào model
mà không tạo migration → `alembic check` exit != 0 → revert → sạch lại. Không
commit lỗi tiêm.
"""

import subprocess
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]


def _run_alembic(args: list[str], db_url: str) -> subprocess.CompletedProcess:
    """Chạy alembic trong tiến trình con với DATABASE_URL cô lập.

    Đặt DATABASE_URL tường minh trong env con; `load_dotenv(override=False)`
    trong db.py sẽ KHÔNG ghi đè → URL tạm này thắng.
    """
    import os

    env = {**os.environ, "DATABASE_URL": db_url}
    return subprocess.run(
        [sys.executable, "-m", "alembic", *args],
        cwd=BACKEND_DIR,
        env=env,
        capture_output=True,
        text=True,
    )


def test_model_and_migration_head_have_no_drift(tmp_path):
    """`alembic check` sạch sau khi upgrade tới head trên SQLite tạm."""
    db_url = f"sqlite:///{(tmp_path / 'drift.db').as_posix()}"

    upgrade = _run_alembic(["upgrade", "head"], db_url)
    assert upgrade.returncode == 0, f"upgrade head lỗi:\n{upgrade.stderr}"

    check = _run_alembic(["check"], db_url)
    assert check.returncode == 0, (
        "PHÁT HIỆN TRÔI SCHEMA: model SQLAlchemy khác head migration.\n"
        "Đổi model thì phải tạo migration: "
        "`alembic revision --autogenerate -m \"...\"` rồi `alembic upgrade head`.\n"
        f"stdout:\n{check.stdout}\nstderr:\n{check.stderr}"
    )
    assert "No new upgrade operations detected" in (check.stdout + check.stderr)


def test_repeated_upgrade_at_head_is_noop(tmp_path):
    """Chạy `upgrade head` lần hai trên DB đã ở head là an toàn (no-op)."""
    db_url = f"sqlite:///{(tmp_path / 'noop.db').as_posix()}"

    first = _run_alembic(["upgrade", "head"], db_url)
    assert first.returncode == 0, first.stderr

    second = _run_alembic(["upgrade", "head"], db_url)
    assert second.returncode == 0, second.stderr
    # head đã áp dụng → lần hai không phát sinh migration nào nữa
    assert "Running upgrade" not in (second.stdout + second.stderr)
