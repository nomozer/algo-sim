# -*- coding: utf-8 -*-
"""Pre-merge final acceptance regression tests:
1. Gate A2 Scenarios 1..8 (including isolated copy of 46-user/66-row unstamped SQLite DB,
   schema drift detection, partial-migration collision, and empty alembic_version guard)
   on both SQLite and real PostgreSQL 16.
2. Root-cause closure for ISSUE-SE-STALE-REVISION-METADATA (`role`, `computational_depends`,
   `visible_prerequisites`, `dependency_edges`, event `display_label`/`explanation`/`details`).
3. Gate E3 independent pure-Fraction geometry oracle + out-of-order async `client_seq` 409 race.
"""
from __future__ import annotations

import asyncio
import copy
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import uuid
from fractions import Fraction
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.ai.step_edit_route import DEFAULT_SCENE3D_HOOKS
from app.main import app
from app.persistence import db as db_mod
from app.persistence.step_edit_models import StepEditRevisionRecord, ensure_step_edit_tables
from app.simulation import step_edit_router
from tests.test_database_safety_closure import (
    LEGACY_TABLES,
    _seed_populated_classroom_graph,
    _stage_alembic_workspace,
    _table_digest,
)
from tests.test_postgres_integration import pg_container  # noqa: F401

BACKEND_DIR = Path(__file__).resolve().parents[1]
WORKTREE_ROOT = BACKEND_DIR.parent
DATA_DIR = WORKTREE_ROOT / "frontend" / "src" / "data"


def _file_sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _run_preflight(work: Path, ini_path: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-X", "utf8", str(work / "alembic" / "migration_preflight.py"), "--alembic-ini", str(ini_path), *args],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _run_alembic(work: Path, ini_path: Path, env: dict[str, str], *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "alembic", "-c", str(ini_path), *args],
        cwd=work,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _load_sample(sample_id: str) -> dict:
    raw = json.loads((DATA_DIR / "advanced-geometry-samples.json").read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("samples", raw)
    return copy.deepcopy(next(x["envelope"]["scene3d"] for x in items if x["id"] == sample_id))


# ── Pure-Python Fraction Analytical Geometry Oracle (Independent of app.simulation.geometry) ──


def _fvec(xs: list[str]) -> tuple[Fraction, Fraction, Fraction]:
    return (Fraction(xs[0]), Fraction(xs[1]), Fraction(xs[2]))


def _fsub(a: tuple[Fraction, Fraction, Fraction], b: tuple[Fraction, Fraction, Fraction]):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _fdot(a, b) -> Fraction:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _fcross(a, b):
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _fnorm_sq(a) -> Fraction:
    return _fdot(a, a)


# ── Gate A2: Preflight Partial Migration, Drift & Unstamped 46-User SQLite Copy ─


def test_gate_a2_schema_drift_and_partial_migration_blocked_sqlite(tmp_path: Path):
    # Scenario 6a: Empty alembic_version table
    empty_ver_db = tmp_path / "empty_ver.db"
    db_url_ev = f"sqlite:///{empty_ver_db.as_posix()}"
    work_ev, ini_ev, env_ev = _stage_alembic_workspace(tmp_path, db_url_ev, "ev_w")
    eng_ev = create_engine(db_url_ev)
    with eng_ev.begin() as conn:
        conn.execute(text("CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL)"))
    r_ev = _run_preflight(work_ev, ini_ev, env_ev, "--startup", "--json")
    assert r_ev.returncode == 23
    assert json.loads(r_ev.stdout)["reason_code"] == "EMPTY_ALEMBIC_VERSION_TABLE"
    assert _run_alembic(work_ev, ini_ev, env_ev, "upgrade", "head").returncode != 0
    eng_ev.dispose()

    # Scenario 6b: Schema drift (missing table & unexpected column on stamped DB)
    drift_db = tmp_path / "drift.db"
    db_url_dr = f"sqlite:///{drift_db.as_posix()}"
    work_dr, ini_dr, env_dr = _stage_alembic_workspace(tmp_path, db_url_dr, "dr_w")
    assert _run_alembic(work_dr, ini_dr, env_dr, "upgrade", "e437149641fa").returncode == 0
    eng_dr = create_engine(db_url_dr)
    with eng_dr.begin() as conn:
        conn.execute(text("ALTER TABLE analysis_usage_ledger ADD COLUMN rogue_col TEXT"))
    r_col = _run_preflight(work_dr, ini_dr, env_dr, "--startup", "--json")
    assert r_col.returncode == 23
    j_col = json.loads(r_col.stdout)
    assert j_col["reason_code"] == "SCHEMA_DRIFT_DETECTED"
    assert j_col["drift_details"]["unexpected_columns"]["analysis_usage_ledger"] == ["rogue_col"]
    assert _run_alembic(work_dr, ini_dr, env_dr, "upgrade", "head").returncode != 0

    with eng_dr.begin() as conn:
        conn.execute(text("DROP TABLE reuse_metrics"))
    r_tbl = _run_preflight(work_dr, ini_dr, env_dr, "--startup", "--json")
    assert r_tbl.returncode == 23
    assert "reuse_metrics" in json.loads(r_tbl.stdout)["drift_details"]["missing_tables"]
    eng_dr.dispose()

    # Scenario 7: Partial/interrupted migration collision (e437149641fa + pre-existing step_edit_sessions)
    part_db = tmp_path / "partial.db"
    db_url_pt = f"sqlite:///{part_db.as_posix()}"
    work_pt, ini_pt, env_pt = _stage_alembic_workspace(tmp_path, db_url_pt, "pt_w")
    assert _run_alembic(work_pt, ini_pt, env_pt, "upgrade", "e437149641fa").returncode == 0
    eng_pt = create_engine(db_url_pt)
    with eng_pt.begin() as conn:
        conn.execute(text("CREATE TABLE step_edit_sessions (id INTEGER PRIMARY KEY)"))
    r_pt = _run_preflight(work_pt, ini_pt, env_pt, "--startup", "--json")
    assert r_pt.returncode == 23
    j_pt = json.loads(r_pt.stdout)
    assert j_pt["reason_code"] == "PARTIAL_MIGRATION_PRE_EXISTING_OBJECT"
    assert "step_edit_sessions" in j_pt["colliding_tables"]
    up_pt = _run_alembic(work_pt, ini_pt, env_pt, "upgrade", "head")
    assert up_pt.returncode != 0
    assert "PARTIAL_MIGRATION_PRE_EXISTING_OBJECT" in (up_pt.stdout + up_pt.stderr)
    eng_pt.dispose()


def test_gate_a2_isolated_copy_of_46_user_66_classroom_sqlite_db_safe_upgrade(tmp_path: Path):
    """Build deterministic unstamped e437149641fa SQLite DB with 46 users & 66 Classroom rows;
    verify automatic startup blocks cleanly (0 bytes changed) and controlled operator stamp+upgrade preserves 100% rows."""
    iso_db = tmp_path / "unstamped_46u_66c.db"
    db_url = f"sqlite:///{iso_db.as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "root_copy_w")
    assert _run_alembic(work, ini, env, "upgrade", "e437149641fa").returncode == 0

    eng_seed = create_engine(db_url)
    with eng_seed.begin() as conn:
        user_ids: list[int] = []
        for idx in range(46):
            role = "teacher" if idx < 12 else "student"
            conn.execute(
                text(
                    "INSERT INTO users (email, display_name, password_hash, role, must_change_password, created_at) "
                    "VALUES (:email, :name, 'h', :role, 0, CURRENT_TIMESTAMP)"
                ),
                {"email": f"u{idx}@algosim.local", "name": f"User {idx}", "role": role},
            )
            uid = conn.execute(text("SELECT id FROM users WHERE email = :email"), {"email": f"u{idx}@algosim.local"}).scalar_one()
            user_ids.append(int(uid))

        cls_ids: list[int] = []
        for cidx in range(12):
            code = f"CLS{cidx:02d}"
            conn.execute(
                text(
                    "INSERT INTO classrooms (teacher_id, name, join_code, code_active, archived, created_at) "
                    "VALUES (:tid, :cname, :code, 1, 0, CURRENT_TIMESTAMP)"
                ),
                {"tid": user_ids[cidx], "cname": f"Class {cidx}", "code": code},
            )
            cid = conn.execute(text("SELECT id FROM classrooms WHERE join_code = :code"), {"code": code}).scalar_one()
            cls_ids.append(int(cid))

        for midx in range(20):
            conn.execute(
                text("INSERT INTO class_memberships (classroom_id, student_id, joined_at) VALUES (:cid, :sid, CURRENT_TIMESTAMP)"),
                {"cid": cls_ids[midx % 12], "sid": user_ids[12 + (midx % 34)]},
            )

        asg_ids: list[int] = []
        for aidx in range(10):
            title = f"Assignment {aidx}"
            cid = cls_ids[aidx % 12]
            tid = user_ids[aidx % 12]
            conn.execute(
                text(
                    "INSERT INTO assignments (classroom_id, created_by, title, instruction, simulation_id, envelope_json, closed, created_at) "
                    "VALUES (:cid, :tid, :title, 'Dung hinh', 'sim.sec', :env_json, 0, CURRENT_TIMESTAMP)"
                ),
                {"cid": cid, "tid": tid, "title": title, "env_json": '{"ok":true}'},
            )
            aid = conn.execute(text("SELECT id FROM assignments WHERE title = :title"), {"title": title}).scalar_one()
            asg_ids.append(int(aid))

        for pidx in range(16):
            conn.execute(
                text(
                    "INSERT INTO practice_sessions (assignment_id, student_id, simulation_id, cursor, step_count, "
                    "explore_open, challenge_open, action_count, commitment_count, completed, started_at, updated_at, help_requested) "
                    "VALUES (:aid, :sid, 'sim.sec', 1, 4, 1, 0, 2, 1, 0, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 0)"
                ),
                {"aid": asg_ids[pidx % 10], "sid": user_ids[12 + (pidx % 34)]},
            )

        for sidx in range(8):
            cid = cls_ids[sidx % 12]
            tid = user_ids[sidx % 12]
            conn.execute(
                text(
                    "INSERT INTO classroom_sessions (classroom_id, teacher_id, round_id, cmd_id, mode, assignment_id, "
                    "simulation_id, current_step, isolated_ids, exploded_groups, sync_cmd_id, active, started_at, updated_at) "
                    "VALUES (:cid, :tid, :rnd, 1, 'follow', :aid, 'sim.sec', 0, '[]', '[]', 1, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"
                ),
                {"cid": cid, "tid": tid, "rnd": f"rnd-{sidx}", "aid": asg_ids[sidx % 10]},
            )

        conn.execute(text("DROP TABLE alembic_version"))
    eng_seed.dispose()

    pre_copy_sha = _file_sha256(iso_db)

    # 1) Automatic startup MUST refuse before DDL with UNSTAMPED_EXISTING_DATABASE
    pre_auto = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre_auto.returncode == 23
    j_auto = json.loads(pre_auto.stdout)
    assert j_auto["reason_code"] == "UNSTAMPED_EXISTING_DATABASE"
    assert j_auto["existing_table_row_counts"]["users"] == 46
    assert j_auto["existing_table_row_counts"]["classrooms"] == 12
    up_blocked = _run_alembic(work, ini, env, "upgrade", "head")
    assert up_blocked.returncode != 0
    assert _file_sha256(iso_db) == pre_copy_sha, "Blocked upgrade modified the SQLite file!"

    # Record baseline digests for every table before operator stamp+upgrade
    eng = create_engine(db_url)
    with eng.connect() as conn:
        baseline = {
            tbl: _table_digest(conn, tbl)
            for tbl in ("users", "auth_sessions", "user_account_meta", *LEGACY_TABLES)
        }
    assert baseline["users"][0] == 46
    assert sum(baseline[t][0] for t in LEGACY_TABLES) == 66

    # 2) Controlled operator procedure: stamp e437149641fa -> preflight --startup PASS -> upgrade head -> check
    assert _run_alembic(work, ini, env, "stamp", "e437149641fa").returncode == 0
    pre_ok = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre_ok.returncode == 0, pre_ok.stdout + pre_ok.stderr
    assert json.loads(pre_ok.stdout)["reason_code"] == "SAFE_NO_DESTRUCTIVE_OPERATIONS"
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0

    with eng.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "f8a2c41d9e05"
        for tbl, exp in baseline.items():
            assert _table_digest(conn, tbl) == exp, f"{tbl} changed after upgrade!"
        assert {"step_edit_sessions", "step_edit_revisions", "step_edit_feedback"} <= set(inspect(eng).get_table_names())
    eng.dispose()


@pytest.mark.postgres
def test_gate_a2_postgres16_drift_and_partial_migration_guards(pg_container, tmp_path: Path):
    pg_url = pg_container["url"]
    work, ini, env = _stage_alembic_workspace(tmp_path, pg_url, "pg_drift_w")
    assert _run_alembic(work, ini, env, "upgrade", "e437149641fa").returncode == 0

    eng = create_engine(pg_url, pool_pre_ping=True)
    with eng.begin() as conn:
        _seed_populated_classroom_graph(conn, is_postgres=True)
        # Inject schema drift: rogue column on users
        conn.execute(text("ALTER TABLE users ADD COLUMN rogue_pg_col TEXT"))

    pre_dr = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre_dr.returncode == 23
    j_dr = json.loads(pre_dr.stdout)
    assert j_dr["reason_code"] == "SCHEMA_DRIFT_DETECTED"
    assert j_dr["drift_details"]["unexpected_columns"]["users"] == ["rogue_pg_col"]
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode != 0

    # Repair drift -> simulate partial 9c4d8e2b7a10 table left behind -> verify PARTIAL_MIGRATION_PRE_EXISTING_OBJECT
    with eng.begin() as conn:
        conn.execute(text("ALTER TABLE users DROP COLUMN rogue_pg_col"))
        conn.execute(text("CREATE TABLE step_edit_sessions (id SERIAL PRIMARY KEY)"))
    pre_pt = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre_pt.returncode == 23
    assert json.loads(pre_pt.stdout)["reason_code"] == "PARTIAL_MIGRATION_PRE_EXISTING_OBJECT"

    with eng.begin() as conn:
        conn.execute(text("DROP TABLE step_edit_sessions"))
    assert _run_preflight(work, ini, env, "--startup", "--json").returncode == 0
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0
    eng.dispose()


# ── Gate E1 & E3: Stale Revision Metadata Fix + Independent Pure-Fraction Oracle ─


def test_step_editor_clears_stale_revision_role_prereqs_and_event_details():
    """Verify ISSUE-SE-STALE-REVISION-METADATA closure on chop-mat-cau-ngoai-tiep."""
    s11 = _load_sample("chop-mat-cau-ngoai-tiep")
    ev_alpha = next(e for e in s11["events"] if e.get("object") == "mp_tt_AB")

    res = DEFAULT_SCENE3D_HOOKS  # ensure imported
    from app.simulation.geometry_functions import step_editor as se

    # 1) Rename (α) -> (P) AND redirect AB -> SB
    out = se.execute_step_edit(
        scene3d=copy.deepcopy(s11),
        step_id="mp_tt_AB",
        step_index=ev_alpha["step_index"],
        previous_instruction=ev_alpha.get("learner_text") or "",
        edited_instruction="Dựng mặt phẳng trung trực (P) của cạnh SB",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
        scene_hooks=res,
    )
    sc = out["scene3d"]
    objs = {o["id"]: o for o in sc["objects"]}

    # Zero stale (α) anywhere in objects or events (including I["role"] and I["annotation"])
    assert "α" not in (objs["I"].get("role") or "")
    assert "(P)" in (objs["I"].get("role") or "")
    for o in sc["objects"]:
        for fk in ("notation", "label", "display_label", "reference", "role"):
            if isinstance(o.get(fk), str):
                assert "α" not in o[fk], f"Stale (α) remained in {o['id']}.{fk}: {o[fk]!r}"
    for ev in sc["events"]:
        for fk in ("learner_text", "display_label", "explanation", "title"):
            if isinstance(ev.get(fk), str):
                assert "α" not in ev[fk], f"Stale (α) remained in ev[{ev.get('step_index')}].{fk}: {ev[fk]!r}"

    # Synchronized dependency mirrors on mp_tt_AB & M_AB
    mp = objs["mp_tt_AB"]
    assert mp["depends"] == ["M_AB", "line_S_B"]
    assert mp["computational_depends"] == ["M_AB", "line_S_B"]
    assert mp["visible_prerequisites"] == ["M_AB", "line_S_B"]
    assert mp["dependency_edges"] == [
        {"source_id": "M_AB", "relation": "topological"},
        {"source_id": "line_S_B", "relation": "topological"},
    ]
    assert objs["M_AB"]["depends"] == ["S", "B"]
    assert objs["M_AB"]["computational_depends"] == ["S", "B"]
    assert objs["M_AB"]["visible_prerequisites"] == ["S", "B"]

    # Event metadata (visible_prerequisites, display_label, explanation, details.value) matches new revision
    ev_mp = next(e for e in sc["events"] if e.get("object") == "mp_tt_AB")
    assert ev_mp["visible_prerequisites"] == ["M_AB", "line_S_B"]
    assert ev_mp["display_label"] == mp["display_label"]
    assert ev_mp["explanation"] == "Dựng mặt phẳng trung trực (P) của cạnh SB"
    assert ev_mp["details"]["value"] == {"kind": "plane3", "point": ["2", "0", "2"], "normal": ["4", "0", "-4"]}

    ev_truc = next(e for e in sc["events"] if e.get("object") == "truc_day")
    assert "(P)" in ev_truc["display_label"] and "α" not in ev_truc["display_label"]
    assert ev_truc["details"]["value"]["point"] == objs["truc_day"]["point"]
    assert ev_truc["details"]["value"]["direction"] == objs["truc_day"]["direction"]

    # Independent analytical Fraction verification of (P), truc_day, and I:
    S = _fvec(objs["S"]["xyz"])
    B = _fvec(objs["B"]["xyz"])
    SB = _fsub(B, S)
    M_sb = tuple((S[k] + B[k]) / 2 for k in range(3))
    pl_pt = _fvec(mp["point"])
    pl_n = _fvec(mp["normal"])
    assert _fcross(pl_n, SB) == (Fraction(0), Fraction(0), Fraction(0))
    assert _fdot(pl_n, _fsub(pl_pt, M_sb)) == Fraction(0)
    tr_pt = _fvec(objs["truc_day"]["point"])
    tr_dir = _fvec(objs["truc_day"]["direction"])
    # truc_day must lie in both (P) and (β), so tr_dir ⟂ pl_n & ad_n, and both planes contain tr_pt
    assert _fdot(pl_n, _fsub(tr_pt, pl_pt)) == Fraction(0)
    assert _fdot(pl_n, tr_dir) == Fraction(0)
    ad_pt = _fvec(objs["mp_tt_AD"]["point"])
    ad_n = _fvec(objs["mp_tt_AD"]["normal"])
    assert _fdot(ad_n, _fsub(tr_pt, ad_pt)) == Fraction(0)
    assert _fdot(ad_n, tr_dir) == Fraction(0)
    I_pt = _fvec(objs["I"]["xyz"])
    # Distance squared from I to all 5 vertices must equal 12
    for vid in ("A", "B", "C", "D", "S"):
        assert _fnorm_sq(_fsub(_fvec(objs[vid]["xyz"]), I_pt)) == Fraction(12)


def test_gate_e2_out_of_order_client_seq_race_and_draft_preservation(tmp_path: Path, monkeypatch):
    """Verify slow/stale HTTP request with lower client_seq returns 409 EDIT_SUPERSEDED and cannot overwrite newer revision."""
    db_file = tmp_path / "ooo_race.db"
    test_eng = create_engine(f"sqlite:///{db_file.as_posix()}", connect_args={"check_same_thread": False})
    TestSess = sessionmaker(bind=test_eng, autoflush=False, autocommit=False)
    monkeypatch.setattr(db_mod, "engine", test_eng)
    monkeypatch.setattr(db_mod, "SessionLocal", TestSess)
    monkeypatch.setattr(step_edit_router, "SessionLocal", TestSess)
    ensure_step_edit_tables(test_eng)
    with step_edit_router._SESSION_LOCKS_GUARD:
        step_edit_router._SESSION_LOCKS.clear()
        step_edit_router._CANCELLED_REQUESTS.clear()
        step_edit_router._LATEST_CLIENT_SEQ.clear()
        step_edit_router._LAST_COMMIT_SNAPSHOT.clear()

    s1 = _load_sample("chop-thiet-dien-ba-diem")
    ev_m = next(e for e in s1["events"] if e.get("object") == "M")
    sid = f"ooo-{uuid.uuid4().hex[:8]}"
    hdr = {"X-Axo-Client-Session": "ooo-owner-1"}

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            r_newer = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": ev_m["step_index"],
                    "previous_instruction": ev_m.get("learner_text") or "Dựng M.",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": copy.deepcopy(s1),
                    "client_request_id": "req-seq-5",
                    "client_seq": 5,
                    "expected_committed_version": 0,
                },
            )
            assert r_newer.status_code == 200
            assert r_newer.json()["committed_version"] == 1

            r_older = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": ev_m["step_index"],
                    "previous_instruction": ev_m.get("learner_text") or "Dựng M.",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 3/4",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": copy.deepcopy(s1),
                    "client_request_id": "req-seq-2",
                    "client_seq": 2,
                    "expected_committed_version": 0,
                },
            )
            assert r_older.status_code == 409
            assert r_older.json()["error_code"] == "EDIT_SUPERSEDED"

            st = (await ac.get(f"/api/simulation/sessions/{sid}/state", headers=hdr)).json()
            assert st["committed_version"] == 1
            m_obj = next(o for o in st["committed_scene"]["objects"] if o["id"] == "M")
            assert m_obj["xyz"] == ["0", "0", "9/2"]

    asyncio.run(_run())
    test_eng.dispose()


def test_conftest_ephemeral_db_prevents_windows_pid_reuse_and_disposes_engine() -> None:
    """ISSUE-TEST-WINDOWS-PID-DB-REUSE: isolate ephemeral SQLite DB by session nonce & verify cleanup."""
    import conftest

    p_same = conftest.duong_dan_db_test()
    assert p_same == conftest.duong_dan_db_test()
    assert "algosim.db" not in p_same
    assert conftest.duong_dan_db_test(111) != conftest.duong_dan_db_test(222)
    assert conftest.duong_dan_db_test(111, "aaa") != conftest.duong_dan_db_test(111, "bbb")
