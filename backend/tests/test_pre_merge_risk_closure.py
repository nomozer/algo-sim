# -*- coding: utf-8 -*-
"""Pre-merge risk closure regression tests for P0 §2 (Schema/Stamp) & P0 §3 (Semantic Identity)."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect, text

from app.ai.step_edit_route import DEFAULT_SCENE3D_HOOKS
from app.persistence.db import Base
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity
from app.simulation.geometry_functions.step_editor import StepEditRefusal, execute_step_edit
from tests.test_database_safety_closure import (
    LEGACY_TABLES,
    _seed_populated_classroom_graph,
    _stage_alembic_workspace,
    _table_digest,
)
from tests.test_postgres_integration import pg_container  # noqa: F401
from tests.test_pre_merge_release_acceptance import _fcross, _fdot, _fnorm_sq, _fsub, _fvec, _load_sample

BACKEND_DIR = Path(__file__).resolve().parents[1]


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


def _assert_scene_identity_invariants(scene: dict, *, forbidden_id_in_objs: str | None = None) -> None:
    """Verify object dependencies, events, visible_prerequisites, and inline helpers have zero dangling refs or orphans."""
    by_id = {o["id"]: o for o in scene.get("objects") or () if "id" in o}
    assert len(by_id) == len(scene.get("objects") or ())
    if forbidden_id_in_objs:
        assert forbidden_id_in_objs not in by_id

    for obj in scene.get("objects") or ():
        oid = obj["id"]
        for dep in obj.get("depends") or ():
            assert dep in by_id, f"{oid} has missing depend {dep}"
        if "computational_depends" in obj:
            assert obj["computational_depends"] == obj.get("depends")
        if "visible_prerequisites" in obj:
            for vp in obj["visible_prerequisites"]:
                assert vp in by_id, f"{oid} has missing visible_prerequisite {vp}"

    used_as_dep = {d for o in (scene.get("objects") or ()) for d in (o.get("depends") or ())}
    for obj in scene.get("objects") or ():
        parent = (obj.get("source") or {}).get("inline_step_parent")
        if parent:
            assert obj["id"] in used_as_dep, f"Orphan inline helper {obj['id']} (parent={parent})"

    for idx, ev in enumerate(scene.get("events") or ()):
        ev_obj = ev.get("object")
        if ev_obj and ev_obj != "canh_ben":
            assert ev_obj in by_id, f"Event {idx} references missing object {ev_obj}"
        for dep in ev.get("depends") or ():
            assert dep in by_id, f"Event {idx} ({ev_obj}) references missing depend {dep}"
        for vp in ev.get("visible_prerequisites") or ():
            assert vp in by_id, f"Event {idx} ({ev_obj}) references missing visible_prerequisite {vp}"

    assert validate_construction_continuity(scene) == []


# ── P0 §2: Schema Contract (15 vs 20 Tables), Drift, Partial Legacy & Stamp Safety ──


def test_p0_schema_contract_15_vs_20_tables_valid_states(tmp_path: Path):
    """Prove both 22-table (migrated/fresh alembic) and 17-table (core ORM, no legacy) states are valid at head.

    Counts grew by 2 at `b6d2f0a8c4e1` (auth_tokens, email_verifications — run authentication-account-recovery).
    """
    # 1. Fresh empty DB via alembic upgrade head -> 22 tables (16 core + 5 retained Classroom + alembic_version)
    fresh_url = f"sqlite:///{(tmp_path / 'fresh20.db').as_posix()}"
    work_f, ini_f, env_f = _stage_alembic_workspace(tmp_path, fresh_url, "fresh20_w")
    assert _run_alembic(work_f, ini_f, env_f, "upgrade", "head").returncode == 0
    assert _run_preflight(work_f, ini_f, env_f, "--startup", "--json").returncode == 0
    assert _run_alembic(work_f, ini_f, env_f, "check").returncode == 0
    eng_f = create_engine(fresh_url)
    fresh_tables = {t for t in inspect(eng_f).get_table_names() if t != "sqlite_sequence"}
    assert len(fresh_tables) == 22
    assert fresh_tables - set(LEGACY_TABLES) - {"alembic_version"} == set(Base.metadata.tables.keys())
    eng_f.dispose()

    # 2. Legacy DB upgraded e437149641fa -> head -> identical 22 tables
    leg_url = f"sqlite:///{(tmp_path / 'leg20.db').as_posix()}"
    work_l, ini_l, env_l = _stage_alembic_workspace(tmp_path, leg_url, "leg20_w")
    assert _run_alembic(work_l, ini_l, env_l, "upgrade", "e437149641fa").returncode == 0
    assert _run_alembic(work_l, ini_l, env_l, "upgrade", "head").returncode == 0
    assert _run_preflight(work_l, ini_l, env_l, "--startup", "--json").returncode == 0
    assert _run_alembic(work_l, ini_l, env_l, "check").returncode == 0
    eng_l = create_engine(leg_url)
    leg_tables = {t for t in inspect(eng_l).get_table_names() if t != "sqlite_sequence"}
    assert leg_tables == fresh_tables
    eng_l.dispose()

    # 3. Core-only 17-table DB at head (0 legacy tables) is also contract-valid
    core_url = f"sqlite:///{(tmp_path / 'core15.db').as_posix()}"
    work_c, ini_c, env_c = _stage_alembic_workspace(tmp_path, core_url, "core15_w")
    assert _run_alembic(work_c, ini_c, env_c, "upgrade", "head").returncode == 0
    eng_c = create_engine(core_url)
    with eng_c.begin() as conn:
        for lt in LEGACY_TABLES:
            conn.execute(text(f'DROP TABLE "{lt}"'))
    core_tables = {t for t in inspect(eng_c).get_table_names() if t != "sqlite_sequence"}
    assert len(core_tables) == 17
    assert _run_preflight(work_c, ini_c, env_c, "--startup", "--json").returncode == 0
    assert _run_alembic(work_c, ini_c, env_c, "check").returncode == 0
    eng_c.dispose()


def test_p0_rogue_unexpected_table_detected_as_schema_drift(tmp_path: Path):
    """Any stray/rogue table on a stamped DB must fail closed with SCHEMA_DRIFT_DETECTED."""
    db_url = f"sqlite:///{(tmp_path / 'rogue.db').as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "rogue_w")
    assert _run_alembic(work, ini, env, "upgrade", "e437149641fa").returncode == 0

    eng = create_engine(db_url)
    with eng.begin() as conn:
        conn.execute(text("CREATE TABLE rogue_drift_tbl (id INTEGER PRIMARY KEY)"))

    pre = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre.returncode == 23
    report = json.loads(pre.stdout)
    assert report["reason_code"] == "SCHEMA_DRIFT_DETECTED"
    assert report["drift_details"]["unexpected_tables"] == ["rogue_drift_tbl"]

    up = _run_alembic(work, ini, env, "upgrade", "head")
    assert up.returncode != 0
    assert "SCHEMA_DRIFT_DETECTED" in (up.stdout + up.stderr)
    eng.dispose()


def test_p0_partial_legacy_classroom_tables_rejected_at_f8(tmp_path: Path):
    """Retaining only a partial subset (1..4 of 5) Classroom tables at f8a2c41d9e05 is rejected as drift."""
    db_url = f"sqlite:///{(tmp_path / 'partial_cls.db').as_posix()}"
    work, ini, env = _stage_alembic_workspace(tmp_path, db_url, "partial_cls_w")
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0

    eng = create_engine(db_url)
    with eng.begin() as conn:
        conn.execute(text("DROP TABLE classroom_sessions"))

    pre = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre.returncode == 23
    report = json.loads(pre.stdout)
    assert report["reason_code"] == "SCHEMA_DRIFT_DETECTED"
    assert report["drift_details"]["missing_tables"] == ["classroom_sessions"]
    assert len(report["drift_details"]["partial_legacy_classroom_tables"]) == 4
    eng.dispose()


def test_p0_stamp_safety_blocks_wrong_revision_empty_drifted_and_already_versioned_dbs(tmp_path: Path):
    """Enforce schema parity and version protection on `alembic stamp`."""
    # 1. Brand-new empty DB cannot be blindly stamped to head or e437149641fa
    empty_url = f"sqlite:///{(tmp_path / 'stamp_empty.db').as_posix()}"
    work_e, ini_e, env_e = _stage_alembic_workspace(tmp_path, empty_url, "se_w")
    assert _run_preflight(work_e, ini_e, env_e, "--direction", "stamp", "--target", "head", "--json").returncode == 23
    res_se = _run_alembic(work_e, ini_e, env_e, "stamp", "head")
    assert res_se.returncode != 0
    assert "INVALID_STAMP_SCHEMA_MISMATCH" in (res_se.stdout + res_se.stderr)
    eng_e = create_engine(empty_url)
    assert inspect(eng_e).get_table_names() == []
    eng_e.dispose()

    # 2. Stamped e437149641fa DB cannot be wrongly stamped to head (or stamped with --purge)
    st_url = f"sqlite:///{(tmp_path / 'stamp_wrong.db').as_posix()}"
    work_w, ini_w, env_w = _stage_alembic_workspace(tmp_path, st_url, "sw_w")
    assert _run_alembic(work_w, ini_w, env_w, "upgrade", "e437149641fa").returncode == 0
    bad_stamp = _run_alembic(work_w, ini_w, env_w, "stamp", "head")
    assert bad_stamp.returncode != 0
    assert "STAMP_ON_ALREADY_VERSIONED_DATABASE" in (bad_stamp.stdout + bad_stamp.stderr)
    bad_purge = _run_alembic(work_w, ini_w, env_w, "stamp", "--purge", "head")
    assert bad_purge.returncode != 0
    assert "INVALID_STAMP_SCHEMA_MISMATCH" in (bad_purge.stdout + bad_purge.stderr)

    # 3. Unstamped populated 16-table e437149641fa DB:
    #    - stamp head MUST FAIL (missing step_edit_* tables)
    #    - stamp at startup MUST FAIL
    #    - stamp e437149641fa with rogue column MUST FAIL
    #    - clean stamp e437149641fa MUST SUCCEED & upgrade head preserves 100% rows
    eng_w = create_engine(st_url)
    with eng_w.begin() as conn:
        _seed_populated_classroom_graph(conn, is_postgres=False)
        conn.execute(text("DROP TABLE alembic_version"))
        baseline_cls = _table_digest(conn, "classrooms")
        baseline_usr = _table_digest(conn, "users")

    wrong_unstamped = _run_alembic(work_w, ini_w, env_w, "stamp", "head")
    assert wrong_unstamped.returncode != 0
    assert "INVALID_STAMP_SCHEMA_MISMATCH" in (wrong_unstamped.stdout + wrong_unstamped.stderr)

    startup_stamp = _run_preflight(work_w, ini_w, env_w, "--startup", "--direction", "stamp", "--target", "e437149641fa", "--json")
    assert startup_stamp.returncode == 23
    assert json.loads(startup_stamp.stdout)["reason_code"] == "STAMP_FORBIDDEN_AT_STARTUP"

    with eng_w.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN rogue_s TEXT"))
    drifted_stamp = _run_alembic(work_w, ini_w, env_w, "stamp", "e437149641fa")
    assert drifted_stamp.returncode != 0
    assert "INVALID_STAMP_SCHEMA_MISMATCH" in (drifted_stamp.stdout + drifted_stamp.stderr)

    # Restore exact e437149641fa schema on SQLite by creating clean copy without rogue_s
    clean_url = f"sqlite:///{(tmp_path / 'stamp_valid.db').as_posix()}"
    work_v, ini_v, env_v = _stage_alembic_workspace(tmp_path, clean_url, "sv_w")
    assert _run_alembic(work_v, ini_v, env_v, "upgrade", "e437149641fa").returncode == 0
    eng_v = create_engine(clean_url)
    with eng_v.begin() as conn:
        _seed_populated_classroom_graph(conn, is_postgres=False)
        conn.execute(text("DROP TABLE alembic_version"))
        clean_baseline_cls = _table_digest(conn, "classrooms")
        clean_baseline_usr = _table_digest(conn, "users")
    assert _run_alembic(work_v, ini_v, env_v, "stamp", "e437149641fa").returncode == 0
    assert _run_preflight(work_v, ini_v, env_v, "--startup", "--json").returncode == 0
    assert _run_alembic(work_v, ini_v, env_v, "upgrade", "head").returncode == 0
    assert _run_alembic(work_v, ini_v, env_v, "check").returncode == 0
    with eng_v.connect() as conn:
        assert _table_digest(conn, "classrooms") == clean_baseline_cls
        assert _table_digest(conn, "users") == clean_baseline_usr
    eng_w.dispose()
    eng_v.dispose()


@pytest.mark.postgres
def test_p0_postgres16_stamp_drift_and_schema_catalog_parity(pg_container, tmp_path: Path):
    """Verify PostgreSQL 16 guards against wrong stamp, rogue tables, partial Classroom tables, and preserves parity."""
    pg_url = pg_container["url"]
    work, ini, env = _stage_alembic_workspace(tmp_path, pg_url, "pg_p0_w")
    assert _run_alembic(work, ini, env, "upgrade", "e437149641fa").returncode == 0

    eng = create_engine(pg_url, pool_pre_ping=True)
    with eng.begin() as conn:
        _seed_populated_classroom_graph(conn, is_postgres=True)
        conn.execute(text("CREATE TABLE pg_rogue_tbl (id SERIAL PRIMARY KEY)"))

    pre_r = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre_r.returncode == 23
    assert json.loads(pre_r.stdout)["drift_details"]["unexpected_tables"] == ["pg_rogue_tbl"]
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode != 0

    with eng.begin() as conn:
        conn.execute(text("DROP TABLE pg_rogue_tbl"))
        conn.execute(text("DROP TABLE alembic_version"))
    # Wrong stamp head on e437149641fa schema must block
    bad_st = _run_alembic(work, ini, env, "stamp", "head")
    assert bad_st.returncode != 0
    assert "INVALID_STAMP_SCHEMA_MISMATCH" in (bad_st.stdout + bad_st.stderr)

    # Valid stamp e437149641fa -> upgrade head -> partial Classroom table guard
    assert _run_alembic(work, ini, env, "stamp", "e437149641fa").returncode == 0
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0

    with eng.begin() as conn:
        conn.execute(text("DROP TABLE classroom_sessions"))
    pre_p = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre_p.returncode == 23
    j_p = json.loads(pre_p.stdout)
    assert j_p["reason_code"] == "SCHEMA_DRIFT_DETECTED"
    assert j_p["drift_details"]["missing_tables"] == ["classroom_sessions"]
    assert len(j_p["drift_details"]["partial_legacy_classroom_tables"]) == 4
    eng.dispose()


# ── P0 §3: Geometric Semantic Identity Chains & Independent Fraction Oracle ─────


def test_p0_semantic_identity_multi_edit_chains_and_fraction_oracle():
    """Exercise AB->SB->AD->AB, (α)->(P), compound->bisector retirement, coincidence 422 refusal, and Fraction oracle."""
    s11 = _load_sample("chop-mat-cau-ngoai-tiep")
    ev11 = next(e for e in s11["events"] if e.get("object") == "mp_tt_AB")

    # 1. AB -> SB and (α) -> (P)
    r1 = execute_step_edit(
        scene3d=copy.deepcopy(s11),
        step_id="mp_tt_AB",
        step_index=ev11["step_index"],
        previous_instruction=ev11.get("learner_text") or "",
        edited_instruction="Dựng mặt phẳng trung trực (P) của cạnh SB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
        scene_hooks=DEFAULT_SCENE3D_HOOKS,
    )
    sc1, ov1 = r1["scene3d"], r1["step_overrides"]
    _assert_scene_identity_invariants(sc1)
    objs1 = {o["id"]: o for o in sc1["objects"]}
    assert objs1["M_AB"]["xyz"] == ["2", "0", "2"]
    assert objs1["M_AB"]["label"] == "Trung điểm của S và B"
    assert next(e for e in sc1["events"] if e.get("object") == "M_AB")["learner_text"] == "Dựng trung điểm của S và B."

    # 2. Direct SB -> AD while (β) still bisects AD must fail closed cleanly (planes coincide)
    with pytest.raises(StepEditRefusal) as exc_422:
        execute_step_edit(
            scene3d=copy.deepcopy(sc1),
            step_id="mp_tt_AB",
            step_index=ev11["step_index"],
            previous_instruction=ov1["mp_tt_AB"],
            edited_instruction="Dựng mặt phẳng trung trực (P) của cạnh AD.",
            target_ids=["mp_tt_AB"],
            absorbed_ids=["M_AB"],
            step_overrides=ov1,
            scene_hooks=DEFAULT_SCENE3D_HOOKS,
        )
    assert exc_422.value.error_code == "CONTAINED_INFINITE_INTERSECTION"

    # 3. Retarget (β) AD -> SC so AD becomes free, then move (P): SB -> AD
    ev_beta = next(e for e in sc1["events"] if e.get("object") == "mp_tt_AD")
    r2 = execute_step_edit(
        scene3d=copy.deepcopy(sc1),
        step_id="mp_tt_AD",
        step_index=ev_beta["step_index"],
        previous_instruction=ev_beta.get("learner_text") or "",
        edited_instruction="Dựng mặt phẳng trung trực (β) của cạnh SC.",
        target_ids=["mp_tt_AD"],
        absorbed_ids=["M_AD"],
        step_overrides=ov1,
        scene_hooks=DEFAULT_SCENE3D_HOOKS,
    )
    _assert_scene_identity_invariants(r2["scene3d"])

    r3 = execute_step_edit(
        scene3d=copy.deepcopy(r2["scene3d"]),
        step_id="mp_tt_AB",
        step_index=ev11["step_index"],
        previous_instruction=r2["step_overrides"]["mp_tt_AB"],
        edited_instruction="Dựng mặt phẳng trung trực (P) của cạnh AD.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
        step_overrides=r2["step_overrides"],
        scene_hooks=DEFAULT_SCENE3D_HOOKS,
    )
    sc3, ov3 = r3["scene3d"], r3["step_overrides"]
    _assert_scene_identity_invariants(sc3, forbidden_id_in_objs="line_S_B")
    objs3 = {o["id"]: o for o in sc3["objects"]}
    assert objs3["M_AB"]["xyz"] == ["0", "2", "0"]
    assert objs3["mp_tt_AB"]["depends"] == ["M_AB", "ad"]
    # Independent analytical verification for (P)=AD, (β)=SC, (γ)=SA
    I3 = _fvec(objs3["I"]["xyz"])
    assert _fdot(_fvec(objs3["mp_tt_AB"]["normal"]), _fsub(I3, _fvec(objs3["mp_tt_AB"]["point"]))) == Fraction(0)
    assert _fdot(_fvec(objs3["mp_tt_AD"]["normal"]), _fsub(I3, _fvec(objs3["mp_tt_AD"]["point"]))) == Fraction(0)
    assert _fdot(_fvec(objs3["mp_tt_SA"]["normal"]), _fsub(I3, _fvec(objs3["mp_tt_SA"]["point"]))) == Fraction(0)
    for v in ("A", "B", "C", "D", "S"):
        assert _fnorm_sq(_fsub(_fvec(objs3[v]["xyz"]), I3)) == Fraction(12)

    # 4. AD -> AB and (P) -> (α)
    r4 = execute_step_edit(
        scene3d=copy.deepcopy(sc3),
        step_id="mp_tt_AB",
        step_index=ev11["step_index"],
        previous_instruction=ov3["mp_tt_AB"],
        edited_instruction="Dựng mặt phẳng trung trực (α) của cạnh AB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
        step_overrides=ov3,
        scene_hooks=DEFAULT_SCENE3D_HOOKS,
    )
    sc4, ov4 = r4["scene3d"], r4["step_overrides"]
    _assert_scene_identity_invariants(sc4)
    assert "(P)" not in json.dumps(sc4, ensure_ascii=False)
    objs4 = {o["id"]: o for o in sc4["objects"]}
    assert objs4["M_AB"]["xyz"] == ["2", "0", "0"]
    assert objs4["mp_tt_AB"]["notation"] == "(α)"

    # 5. Compound named point K on SB -> retires M_AB -> then revert back to bisector of AD -> retires K & line_S_B
    r5 = execute_step_edit(
        scene3d=copy.deepcopy(sc4),
        step_id="mp_tt_AB",
        step_index=ev11["step_index"],
        previous_instruction=ov4["mp_tt_AB"],
        edited_instruction="Gọi K là trung điểm của SB; dựng mặt phẳng (Q) qua K và vuông góc với SB.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=["M_AB"],
        step_overrides=ov4,
        scene_hooks=DEFAULT_SCENE3D_HOOKS,
    )
    sc5, ov5 = r5["scene3d"], r5["step_overrides"]
    _assert_scene_identity_invariants(sc5, forbidden_id_in_objs="M_AB")

    r6 = execute_step_edit(
        scene3d=copy.deepcopy(sc5),
        step_id="mp_tt_AB",
        step_index=ev11["step_index"],
        previous_instruction=ov5["mp_tt_AB"],
        edited_instruction="Dựng mặt phẳng trung trực (P) của cạnh AD.",
        target_ids=["mp_tt_AB"],
        absorbed_ids=[],
        step_overrides=ov5,
        scene_hooks=DEFAULT_SCENE3D_HOOKS,
    )
    sc6 = r6["scene3d"]
    _assert_scene_identity_invariants(sc6, forbidden_id_in_objs="K")
    assert "line_S_B" not in {o["id"] for o in sc6["objects"]}
    assert "mid_A_D" in {o["id"] for o in sc6["objects"]}
    ev_mid = next(e for e in sc6["events"] if e.get("object") == "mid_A_D")
    assert "A và D" in ev_mid["learner_text"]

    # 6. Upstream edit cascading across dependent plane & section on chop-thiet-dien-ba-diem
    s1 = _load_sample("chop-thiet-dien-ba-diem")
    ev_m = next(e for e in s1["events"] if e.get("object") == "M")
    r_s1 = execute_step_edit(
        scene3d=copy.deepcopy(s1),
        step_id="M",
        step_index=ev_m["step_index"],
        previous_instruction=ev_m.get("learner_text") or "",
        edited_instruction="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
        target_ids=["M"],
        absorbed_ids=[],
        scene_hooks=DEFAULT_SCENE3D_HOOKS,
    )
    sc_s1 = r_s1["scene3d"]
    _assert_scene_identity_invariants(sc_s1)
    objs_s1 = {o["id"]: o for o in sc_s1["objects"]}
    S0, A0 = _fvec(objs_s1["S"]["xyz"]), _fvec(objs_s1["A"]["xyz"])
    M_exp = tuple(S0[k] + Fraction(1, 4) * (A0[k] - S0[k]) for k in range(3))
    assert _fvec(objs_s1["M"]["xyz"]) == M_exp
    for pt_on_sec in ("M", "N", "P", "E", "F"):
        if pt_on_sec in objs_s1 and "xyz" in objs_s1[pt_on_sec]:
            assert _fdot(
                _fvec(objs_s1["mp_MNP"]["normal"]),
                _fsub(_fvec(objs_s1[pt_on_sec]["xyz"]), _fvec(objs_s1["mp_MNP"]["point"])),
            ) == Fraction(0)


def test_cross_context_state_recovery_exposes_latest_client_seq_across_restart(tmp_path: Path, monkeypatch):
    """ISSUE-SE-CROSS-CONTEXT-CLIENT-SEQ-DESYNC: GET /state and 409 expose persisted latest_client_seq across restarts."""
    import asyncio
    import uuid

    import httpx
    from sqlalchemy.orm import sessionmaker

    from app.main import app
    from app.persistence import db as db_mod
    from app.persistence.step_edit_models import ensure_step_edit_tables
    from app.simulation import step_edit_router

    db_file = tmp_path / "seq_recovery.db"
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
    sid = f"seq-rec-{uuid.uuid4().hex[:8]}"
    hdr = {"X-Axo-Client-Session": "seq-recovery-owner"}

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            st_empty = await ac.get(f"/api/simulation/sessions/{sid}-missing/state", headers=hdr)
            assert st_empty.status_code == 200
            assert st_empty.json()["found"] is False
            assert st_empty.json()["latest_client_seq"] == 0

            r1 = await ac.post(
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
                    "client_request_id": "req-ctx1-20",
                    "client_seq": 20,
                },
            )
            assert r1.status_code == 200
            assert r1.json()["committed_version"] == 1

            # Simulate backend worker restart (in-memory _LATEST_CLIENT_SEQ wiped) + fresh browser context
            with step_edit_router._SESSION_LOCKS_GUARD:
                step_edit_router._LATEST_CLIENT_SEQ.clear()
                step_edit_router._SESSION_LOCKS.clear()

            st = await ac.get(f"/api/simulation/sessions/{sid}/state", headers=hdr)
            assert st.status_code == 200
            st_json = st.json()
            assert st_json["found"] is True
            assert st_json["committed_version"] == 1
            assert st_json["latest_client_seq"] == 20

            # Stale client_seq <= 20 returns 409 EDIT_SUPERSEDED along with server latest_client_seq
            r_stale = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": ev_m["step_index"],
                    "previous_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": st_json["committed_scene"],
                    "client_request_id": "req-ctx2-stale-1",
                    "client_seq": 1,
                },
            )
            assert r_stale.status_code == 409
            assert r_stale.json()["error_code"] == "EDIT_SUPERSEDED"
            assert r_stale.json()["latest_client_seq"] == 20

            # Fresh browser context advancing from server latest_client_seq + 1 succeeds immediately
            r2 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": ev_m["step_index"],
                    "previous_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": st_json["committed_scene"],
                    "client_request_id": "req-ctx2-21",
                    "client_seq": st_json["latest_client_seq"] + 1,
                },
            )
            assert r2.status_code == 200
            assert r2.json()["committed_version"] == 2
            m_obj = next(o for o in r2.json()["scene3d"]["objects"] if o["id"] == "M")
            assert m_obj["xyz"] == ["0", "0", "4"]

    asyncio.run(_run())
    test_eng.dispose()
