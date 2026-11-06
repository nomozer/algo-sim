# -*- coding: utf-8 -*-
"""Axo history / admin tables on REAL PostgreSQL (opt-in: `pytest -m postgres`; throw-away container, no volume).

Upgrade from main's head (`a1c7e4b90d52`) with a user already present → Axo head (`d5f9b82c3a14`): the user survives,
the history table carries its unique (user_id, history_key) constraint and its FK to users; the HTTP history API on
Postgres keeps two accounts apart, keeps view order strict when writes share one clock tick, and survives concurrent
upserts of one key; downgrade to main's head drops exactly the Axo tables and keeps the user; re-upgrade and
`alembic check` are clean. Never touches a developer database.
"""
from __future__ import annotations

import threading
from datetime import datetime as real_dt, timezone as tz

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from tests.test_postgres_integration import _alembic, pg_container  # noqa: F401 — shared throw-away container

pytestmark = pytest.mark.postgres
MAIN_HEAD, AXO_HEAD = "a1c7e4b90d52", "d5f9b82c3a14"
AXO_TABLES = {"learning_history_entries", "user_account_meta", "admin_system_settings", "admin_audit_logs",
              "admin_analysis_telemetry"}


def _payload(key: str, title: str) -> dict:
    return {"id": key, "sampleId": None, "title": title, "simulationId": "generic.semantic_program", "domain": "geometry",
            "envelope": {"status": "ok", "simulation_id": "generic.semantic_program", "title": title},
            "originalInput": title, "lastCursor": 1, "stepCount": 3, "visualMode": "3d"}


def _tables(engine) -> set[str]:
    with engine.connect() as c:
        return {r[0] for r in c.execute(text("select tablename from pg_tables where schemaname = 'public'"))}


def test_axo_migrations_and_history_api_on_postgres(pg_container, monkeypatch):  # noqa: F811
    url = pg_container["url"]
    up = _alembic(["upgrade", MAIN_HEAD], url)
    assert up.returncode == 0, up.stderr
    engine = create_engine(url, pool_pre_ping=True)
    with engine.begin() as c:
        c.execute(text("insert into users (email, display_name, password_hash, role, must_change_password, created_at) "
                       "values ('seed@algosim.edu.vn', 'Seed', 'x', 'student', false, now())"))
    assert not (AXO_TABLES & _tables(engine))

    up = _alembic(["upgrade", "head"], url)
    assert up.returncode == 0, up.stderr
    with engine.connect() as c:
        assert c.execute(text("select version_num from alembic_version")).scalar_one() == AXO_HEAD
        assert c.execute(text("select count(*) from users where email = 'seed@algosim.edu.vn'")).scalar_one() == 1
        cons = {r[0]: r[1] for r in c.execute(text(
            "select conname, contype from pg_constraint where conrelid = 'learning_history_entries'::regclass"))}
        idx = {r[0] for r in c.execute(text("select indexname from pg_indexes where tablename = 'learning_history_entries'"))}
    assert AXO_TABLES <= _tables(engine)
    assert cons.get("uq_learning_history_per_user") == "u" and "f" in cons.values(), cons
    assert {"ix_learning_history_entries_user_id", "ix_learning_history_entries_history_key"} <= idx, idx

    # ── HTTP API on Postgres ──
    import app.accounts.router as router_mod
    import app.main as main_mod
    from fastapi.testclient import TestClient
    from tests.conftest_classroom import TEST_PASSWORD

    PgSession = sessionmaker(bind=engine, autoflush=False)
    monkeypatch.setattr(router_mod, "SessionLocal", PgSession)
    monkeypatch.setattr(main_mod, "SessionLocal", PgSession)
    with TestClient(main_mod.app) as a, TestClient(main_mod.app) as b:
        for client, email in ((a, "a@algosim.edu.vn"), (b, "b@algosim.edu.vn")):
            r = client.post("/api/auth/register", json={"email": email, "displayName": email[0], "password": TEST_PASSWORD})
            assert r.status_code == 200, r.text
        assert a.post("/api/history", json=_payload("k-shared", "A")).status_code == 200
        assert b.get("/api/history").json()["items"] == []
        assert b.patch("/api/history/k-shared", json={"lastCursor": 2}).status_code == 404
        assert b.delete("/api/history/k-shared").status_code == 404
        assert b.post("/api/history", json=_payload("k-shared", "B")).status_code == 200   # same key, other account
        assert [x["title"] for x in a.get("/api/history").json()["items"]] == ["A"]

        # one clock tick for several writes: order must stay strict
        frozen = real_dt(2026, 11, 6, 12, 0, 0, tzinfo=tz.utc)

        class _Frozen(real_dt):
            @classmethod
            def now(cls, tz=None):  # noqa: ARG003
                return frozen

        monkeypatch.setattr(router_mod, "datetime", _Frozen)
        for k in ("t1", "t2", "t3"):
            assert a.post("/api/history", json=_payload(k, k)).status_code == 200
        assert a.patch("/api/history/t1", json={"lastCursor": 2}).status_code == 200
        assert [x["id"] for x in a.get("/api/history").json()["items"]][:3] == ["t1", "t3", "t2"]
        monkeypatch.setattr(router_mod, "datetime", real_dt)

        # concurrent upserts of ONE key by one account: never a 5xx, exactly one row
        codes: list[int] = []

        def put():
            codes.append(a.post("/api/history", json=_payload("k-race", "race")).status_code)

        ts = [threading.Thread(target=put) for _ in range(6)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        with engine.connect() as c:
            n = c.execute(text("select count(*) from learning_history_entries where history_key = 'k-race'")).scalar_one()
        assert n == 1 and all(code < 500 for code in codes), codes

    down = _alembic(["downgrade", MAIN_HEAD], url)
    assert down.returncode == 0, down.stderr
    assert not (AXO_TABLES & _tables(engine))
    with engine.connect() as c:
        assert c.execute(text("select count(*) from users where email = 'seed@algosim.edu.vn'")).scalar_one() == 1
    assert _alembic(["upgrade", "head"], url).returncode == 0
    check = _alembic(["check"], url)
    assert check.returncode == 0, check.stdout + check.stderr
    engine.dispose()
