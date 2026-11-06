"""Cost of the usage ledger per /api/analyze attempt: reserve + finalize on a temp SQLite DB (0 model calls).

Usage (from backend/): PYTHONPATH=. python <this> — median/p95 ms over 200 attempts for a guest and a student session.
"""
import json
import secrets
import statistics
import tempfile
import time
import uuid
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.accounts.router as router
from app.accounts import service
from app.accounts.policy import Role
from app.persistence import classroom_models  # noqa: F401  (registers the tables)
from app.persistence.db import Base

engine = create_engine(f"sqlite:///{Path(tempfile.mkdtemp()) / 'ledger.db'}", connect_args={"check_same_thread": False})
Base.metadata.create_all(engine)
router.SessionLocal = sessionmaker(bind=engine, autoflush=False)

with router.SessionLocal() as s:
    guest = service.new_session(s).token
    user = service.create_user(s, email="bench@algosim.test", display_name="Bench",
                               password="b" + secrets.token_hex(8), role=Role.STUDENT)
    s.flush()
    student = service.new_session(s, user_id=user.id).token
    s.commit()


def measure(token: str, n: int = 200) -> dict:
    times = []
    for _ in range(n):
        t = time.perf_counter()
        r = router.reserve_analysis_usage(token, "a" + uuid.uuid4().hex)
        assert not isinstance(r, tuple), r
        router.finalize_analysis_usage(r, served=False)    # release + refund keeps the counter free for the next round
        times.append((time.perf_counter() - t) * 1000)
    times.sort()
    return {"attempts": n, "median_ms": round(statistics.median(times), 2), "p95_ms": round(times[int(0.95 * n)], 2)}


print(json.dumps({"guest": measure(guest), "student": measure(student)}))
