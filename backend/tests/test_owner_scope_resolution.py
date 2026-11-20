# -*- coding: utf-8 -*-
"""Option B Classroom retirement, Step Editor end-to-end pipeline, and PG16 parity tests."""
from __future__ import annotations

import asyncio
import copy
import json
import subprocess
import sys
import uuid
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.persistence import db as db_mod
from app.persistence.step_edit_models import (
    StepEditRevisionRecord,
    StepEditSessionRecord,
    ensure_step_edit_tables,
)
from app.simulation import step_edit_router
from tests.conftest_classroom import api, new_client, register  # noqa: F401
from tests.test_database_safety_closure import (
    LEGACY_TABLES,
    _seed_populated_classroom_graph,
    _stage_alembic_workspace,
    _table_digest,
)
from tests.test_postgres_integration import pg_container  # noqa: F401
from tests.test_pre_merge_release_acceptance import _load_sample
from tests.test_pre_merge_risk_closure import (
    _assert_scene_identity_invariants,
    _run_alembic,
    _run_preflight,
)

BACKEND_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_DIR.parent
SEED_CLASSROOM_SCRIPT = BACKEND_DIR / "scripts" / "seed_classroom_fixture.py"
ACCEPT_LIVE_CLASSROOM_SCRIPT = REPO_ROOT / "frontend" / "scripts" / "accept-live-classroom.mjs"

# Exhaustive 18 retired Classroom / Live Session HTTP endpoints under V1 Option B
RETIRED_CLASSROOM_ENDPOINTS: tuple[tuple[str, str, dict | None], ...] = (
    ("GET", "/api/classes", None),
    ("POST", "/api/classes", {"name": "11A1"}),
    ("POST", "/api/classes/1/code", {}),
    ("DELETE", "/api/classes/1/code", None),
    ("POST", "/api/classes/join", {"code": "ABC123"}),
    ("GET", "/api/classes/1/members", None),
    ("POST", "/api/assignments", {"classroomId": 1, "title": "Test"}),
    ("GET", "/api/assignments", None),
    ("GET", "/api/assignments/1", None),
    ("POST", "/api/assignments/1/progress", {"stepIndex": 1}),
    ("GET", "/api/classes/1/observe", None),
    ("POST", "/api/classes/1/session", {"assignmentId": 1}),
    ("GET", "/api/classes/1/session", None),
    ("DELETE", "/api/classes/1/session", None),
    ("POST", "/api/classes/1/session/command", {"action": "sync"}),
    ("POST", "/api/assignments/1/help", {"message": "Help"}),
    ("POST", "/api/classes/1/help/1/clear", {}),
    ("GET", "/api/classes/1/monitor", None),
)


def _mount_isolated_step_edit_db(tmp_path: Path, monkeypatch, name: str = "osr_se.db"):
    db_file = tmp_path / name
    test_eng = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
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
    return test_eng, TestSess


def test_option_b_all_18_classroom_endpoints_404_and_zero_openapi_leaks(api):  # noqa: F811
    """Verify all 18 retired Classroom/Live Session endpoints return 404 across roles with 0 OpenAPI exposure."""
    openapi = api.app.openapi()
    paths = list((openapi.get("paths") or {}).keys())
    leaked = [p for p in paths if p.startswith("/api/classes") or p.startswith("/api/assignments")]
    assert leaked == [], f"Unexpected Classroom paths in OpenAPI: {leaked}"

    health = api.get("/api/health")
    assert health.status_code == 200
    assert health.json().get("ok") is True

    student = new_client(api)
    assert register(student, email="osr.student@algosim.test", name="Student OSR").status_code == 200

    teacher = new_client(api)
    assert (
        register(
            teacher,
            email="osr.teacher@algosim.test",
            name="Teacher OSR",
            role="teacher",
            teacher_code="MA-GIAO-VIEN-TEST",
        ).status_code
        == 200
    )

    for role_name, client in (("anonymous", api), ("student", student), ("teacher", teacher)):
        for method, path, payload in RETIRED_CLASSROOM_ENDPOINTS:
            resp = client.request(method, path, json=payload)
            assert resp.status_code == 404, f"{role_name} {method} {path} returned {resp.status_code}: {resp.text}"
            assert resp.json() == {"detail": "Not Found"}, f"{role_name} {method} {path} body={resp.text}"


def test_option_b_retired_cli_scripts_fail_closed():
    """Retired Classroom scripts exit 0 on --help and fail closed (exit 2) without mutating DBs or docs."""
    py_help = subprocess.run(
        [sys.executable, "-X", "utf8", str(SEED_CLASSROOM_SCRIPT), "--help"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert py_help.returncode == 0

    py_json = subprocess.run(
        [sys.executable, "-X", "utf8", str(SEED_CLASSROOM_SCRIPT), "--json"],
        cwd=BACKEND_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert py_json.returncode == 2
    assert json.loads(py_json.stdout)["status"] == "CLASSROOM_FEATURE_RETIRED"

    node_help = subprocess.run(
        ["node", str(ACCEPT_LIVE_CLASSROOM_SCRIPT), "--help"],
        cwd=REPO_ROOT / "frontend",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert node_help.returncode == 0

    node_json = subprocess.run(
        ["node", str(ACCEPT_LIVE_CLASSROOM_SCRIPT), "--json"],
        cwd=REPO_ROOT / "frontend",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert node_json.returncode == 2
    assert json.loads(node_json.stdout)["status"] == "CLASSROOM_FEATURE_RETIRED"


def test_step_editor_end_to_end_pipeline_persistence_and_conflicts(tmp_path: Path, monkeypatch):
    """Trace HTTP edit -> validation -> dep rebuild -> Scene3D/events/steps -> persistence -> 422/409/restart."""
    test_eng, TestSess = _mount_isolated_step_edit_db(tmp_path, monkeypatch)
    s11 = _load_sample("chop-mat-cau-ngoai-tiep")
    ev11 = next(e for e in s11["events"] if e.get("object") == "mp_tt_AB")

    s2 = _load_sample("chop-thiet-dien-ba-diem")
    ev2_plane = next(e for e in s2["events"] if e.get("object") == "mp_MNP")
    ev2_m = next(e for e in s2["events"] if e.get("object") == "M")

    sid_a = f"osr-s11-{uuid.uuid4().hex[:8]}"
    sid_b = f"osr-s2-{uuid.uuid4().hex[:8]}"
    hdr = {"X-Axo-Client-Session": "osr-e2e-owner"}

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            # 1. chop-mat-cau-ngoai-tiep: (α) -> (P) & AB -> SB
            r_a1 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid_a,
                    "problem_key": "sample:chop-mat-cau-ngoai-tiep",
                    "step_id": "mp_tt_AB",
                    "step_index": ev11["step_index"],
                    "previous_instruction": ev11.get("learner_text") or "",
                    "edited_instruction": "Dựng mặt phẳng trung trực (P) của cạnh SB.",
                    "target_ids": ["mp_tt_AB"],
                    "absorbed_ids": ["M_AB"],
                    "scene3d": copy.deepcopy(s11),
                    "client_request_id": "osr-req-a1",
                    "client_seq": 1,
                    "expected_committed_version": 0,
                },
            )
            assert r_a1.status_code == 200, r_a1.text
            b_a1 = r_a1.json()
            assert b_a1["status"] == "committed"
            assert b_a1["committed_version"] == 1
            sc_a1 = b_a1["scene3d"]
            _assert_scene_identity_invariants(sc_a1)

            objs_a1 = {o["id"]: o for o in sc_a1["objects"]}
            assert objs_a1["I"]["xyz"] == ["2", "2", "2"]
            assert objs_a1["R"]["value"] == "2√3"
            assert objs_a1["V_cau"]["value"] == "32π√3"
            ev_truc = next(e for e in sc_a1["events"] if e.get("object") == "truc_day")
            assert ev_truc["learner_text"] == "Dựng giao tuyến của (P) và (β)."

            # Zero stale "(α)" anywhere across rebuilt Scene3D objects, events, or formation.steps
            for collection_name, items in (
                ("objects", sc_a1.get("objects") or ()),
                ("events", sc_a1.get("events") or ()),
                ("formation.steps", (sc_a1.get("formation") or {}).get("steps") or ()),
            ):
                blob = json.dumps(items, ensure_ascii=False)
                assert "(α)" not in blob, f"Stale (α) leaked in {collection_name}"
                assert "(P)" in blob, f"Missing (P) in {collection_name}"

            st_a = await ac.get(f"/api/simulation/sessions/{sid_a}/state", headers=hdr)
            assert st_a.status_code == 200
            st_a_json = st_a.json()
            assert st_a_json["found"] is True
            assert st_a_json["committed_version"] == 1
            assert st_a_json["latest_client_seq"] == 1
            assert len(st_a_json["revisions"]) == 1

            # 2. chop-thiet-dien-ba-diem: (MNP) -> (Q) via M, B, P -> repeat S, A, C -> upstream M=1/3
            r_b1 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid_b,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "mp_MNP",
                    "step_index": ev2_plane["step_index"],
                    "previous_instruction": ev2_plane.get("learner_text") or "Dựng (MNP).",
                    "edited_instruction": "Dựng mặt phẳng (Q) đi qua ba điểm M, B, P.",
                    "target_ids": ["mp_MNP"],
                    "absorbed_ids": [],
                    "scene3d": copy.deepcopy(s2),
                    "client_request_id": "osr-req-b1",
                    "client_seq": 10,
                    "expected_committed_version": 0,
                },
            )
            assert r_b1.status_code == 200, r_b1.text
            b_b1 = r_b1.json()
            _assert_scene_identity_invariants(b_b1["scene3d"])
            objs_b1 = {o["id"]: o for o in b_b1["scene3d"]["objects"]}
            assert objs_b1["mp_MNP"]["label"] == "(Q)"
            assert objs_b1["thiet_dien"]["label"] == "Thiết diện MBPF"
            assert objs_b1["S_td"]["value"] == "4√109/3"

            r_b2 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid_b,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "mp_MNP",
                    "step_index": ev2_plane["step_index"],
                    "previous_instruction": b_b1["step_overrides"]["mp_MNP"],
                    "edited_instruction": "Dựng mặt phẳng (Q) đi qua ba điểm S, A, C.",
                    "target_ids": ["mp_MNP"],
                    "absorbed_ids": [],
                    "scene3d": b_b1["scene3d"],
                    "client_request_id": "osr-req-b2",
                    "client_seq": 11,
                    "expected_committed_version": 1,
                },
            )
            assert r_b2.status_code == 200, r_b2.text
            b_b2 = r_b2.json()
            _assert_scene_identity_invariants(b_b2["scene3d"])
            objs_b2 = {o["id"]: o for o in b_b2["scene3d"]["objects"]}
            assert objs_b2["E"]["xyz"] == ["0", "0", "6"]
            assert objs_b2["F"]["xyz"] == ["0", "0", "6"]
            assert objs_b2["thiet_dien"]["label"] == "Thiết diện ACS"
            assert objs_b2["S_td"]["value"] == "12√2"

            # Upstream ratio edit M -> SM/SA = 1/3
            r_b3 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid_b,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": ev2_m["step_index"],
                    "previous_instruction": ev2_m.get("learner_text") or "Dựng M.",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": b_b2["scene3d"],
                    "client_request_id": "osr-req-b3",
                    "client_seq": 12,
                    "expected_committed_version": 2,
                },
            )
            assert r_b3.status_code == 200, r_b3.text
            b_b3 = r_b3.json()
            assert b_b3["committed_version"] == 3
            _assert_scene_identity_invariants(b_b3["scene3d"])
            assert {o["id"]: o for o in b_b3["scene3d"]["objects"]}["M"]["xyz"] == ["0", "0", "4"]

            # 3. Invalid inputs -> fail-closed 422 without advancing committed_version or mutating scene
            for seq_422, (bad_instr, expected_code) in enumerate(
                (
                    ("Dựng mặt phẳng trung trực (P) của cạnh SZ.", "MISSING_DEPENDENCY"),
                    ("Dựng mặt phẳng (Q) đi qua ba điểm A, O, C.", "COLLINEAR_POINTS"),
                    ("Vẽ parabol bất kỳ qua M.", "UNSUPPORTED_STEP_SYNTAX"),
                ),
                start=15,
            ):
                r_bad = await ac.post(
                    "/api/simulation/steps/edit",
                    headers=hdr,
                    json={
                        "session_id": sid_b,
                        "problem_key": "sample:chop-thiet-dien-ba-diem",
                        "step_id": "mp_MNP",
                        "step_index": ev2_plane["step_index"],
                        "previous_instruction": b_b3["step_overrides"]["mp_MNP"],
                        "edited_instruction": bad_instr,
                        "target_ids": ["mp_MNP"],
                        "absorbed_ids": [],
                        "scene3d": b_b3["scene3d"],
                        "client_request_id": f"osr-req-bad-{expected_code}",
                        "client_seq": seq_422,
                        "expected_committed_version": 3,
                    },
                )
                assert r_bad.status_code == 422, r_bad.text
                assert r_bad.json()["error_code"] == expected_code

            st_after_422 = await ac.get(f"/api/simulation/sessions/{sid_b}/state", headers=hdr)
            assert st_after_422.json()["committed_version"] == 3
            assert {o["id"]: o for o in st_after_422.json()["committed_scene"]["objects"]}["S_td"]["value"] == "12√2"

            # 4. 409 STALE_REVISION_CONFLICT + simulated backend restart + 409 EDIT_SUPERSEDED + recovery
            r_stale_ver = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid_b,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": ev2_m["step_index"],
                    "previous_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": b_b3["scene3d"],
                    "client_request_id": "osr-req-stale-ver",
                    "client_seq": 20,
                    "expected_committed_version": 0,
                },
            )
            assert r_stale_ver.status_code == 409
            assert r_stale_ver.json()["error_code"] == "STALE_REVISION_CONFLICT"

            # Simulate worker restart clearing in-memory _LATEST_CLIENT_SEQ
            with step_edit_router._SESSION_LOCKS_GUARD:
                step_edit_router._LATEST_CLIENT_SEQ.clear()
                step_edit_router._SESSION_LOCKS.clear()

            st_rec = await ac.get(f"/api/simulation/sessions/{sid_b}/state", headers=hdr)
            assert st_rec.status_code == 200
            rec_json = st_rec.json()
            assert rec_json["committed_version"] == 3
            assert rec_json["latest_client_seq"] >= 12

            r_superseded = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid_b,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": ev2_m["step_index"],
                    "previous_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": rec_json["committed_scene"],
                    "client_request_id": "osr-req-superseded",
                    "client_seq": 1,
                    "expected_committed_version": 3,
                },
            )
            assert r_superseded.status_code == 409
            assert r_superseded.json()["error_code"] == "EDIT_SUPERSEDED"

            r_b4 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdr,
                json={
                    "session_id": sid_b,
                    "problem_key": "sample:chop-thiet-dien-ba-diem",
                    "step_id": "M",
                    "step_index": ev2_m["step_index"],
                    "previous_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/3",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "scene3d": rec_json["committed_scene"],
                    "client_request_id": "osr-req-b4",
                    "client_seq": rec_json["latest_client_seq"] + 1,
                    "expected_committed_version": 3,
                },
            )
            assert r_b4.status_code == 200, r_b4.text
            assert r_b4.json()["committed_version"] == 4
            m_xyz = {o["id"]: o for o in r_b4.json()["scene3d"]["objects"]}["M"]["xyz"]
            assert m_xyz in (["0", "0", "9/2"], ["0", "0", "4.5"])

    asyncio.run(_run())

    with TestSess() as db:
        sess_b = db.query(StepEditSessionRecord).filter_by(session_id=sid_b).one()
        revs_b = db.query(StepEditRevisionRecord).filter_by(session_id=sid_b).all()
        committed_revs = [r for r in revs_b if r.execution_status == "COMMITTED"]
        assert len(committed_revs) == 4
        assert sess_b.revision_count == len(revs_b) >= 4
        persisted_objs = {o["id"]: o for o in json.loads(sess_b.committed_scene_json)["objects"]}
        assert persisted_objs["M"]["xyz"] in (["0", "0", "9/2"], ["0", "0", "4.5"])
    test_eng.dispose()


@pytest.mark.postgres
def test_option_b_postgres16_20_table_legacy_retention_and_step_edit_isolation(pg_container, tmp_path: Path, monkeypatch):
    """Verify PostgreSQL 16 preserves all 5 populated Classroom tables across upgrade + Step Edit commits (20 tables total)."""
    pg_url = pg_container["url"]
    work, ini, env = _stage_alembic_workspace(tmp_path, pg_url, "osr_pg_w")
    assert _run_alembic(work, ini, env, "upgrade", "e437149641fa").returncode == 0

    eng = create_engine(pg_url, pool_pre_ping=True)
    with eng.begin() as conn:
        _seed_populated_classroom_graph(conn, is_postgres=True)
        baseline = {tbl: _table_digest(conn, tbl) for tbl in LEGACY_TABLES}
        baseline_users = _table_digest(conn, "users")

    pre = _run_preflight(work, ini, env, "--startup", "--json")
    assert pre.returncode == 0, pre.stdout + pre.stderr
    assert _run_alembic(work, ini, env, "upgrade", "head").returncode == 0
    assert _run_alembic(work, ini, env, "check").returncode == 0

    tables = set(inspect(eng).get_table_names())
    assert len(tables) == 20, f"Expected 20 tables (15 active + 5 legacy), got {len(tables)}: {sorted(tables)}"
    for tbl in LEGACY_TABLES:
        assert tbl in tables

    with eng.connect() as conn:
        for tbl in LEGACY_TABLES:
            assert _table_digest(conn, tbl) == baseline[tbl], f"Table {tbl} mutated during upgrade"
        assert _table_digest(conn, "users") == baseline_users

    # Execute Step Editor HTTP commit against PG16 and confirm legacy Classroom tables remain untouched
    PgSess = sessionmaker(bind=eng, autoflush=False, autocommit=False)
    monkeypatch.setattr(db_mod, "engine", eng)
    monkeypatch.setattr(db_mod, "SessionLocal", PgSess)
    monkeypatch.setattr(step_edit_router, "SessionLocal", PgSess)
    with step_edit_router._SESSION_LOCKS_GUARD:
        step_edit_router._SESSION_LOCKS.clear()
        step_edit_router._CANCELLED_REQUESTS.clear()
        step_edit_router._LATEST_CLIENT_SEQ.clear()
        step_edit_router._LAST_COMMIT_SNAPSHOT.clear()

    s11 = _load_sample("chop-mat-cau-ngoai-tiep")
    ev11 = next(e for e in s11["events"] if e.get("object") == "mp_tt_AB")
    sid = f"osr-pg-{uuid.uuid4().hex[:8]}"

    async def _run_pg():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            r = await ac.post(
                "/api/simulation/steps/edit",
                headers={"X-Axo-Client-Session": "osr-pg-owner"},
                json={
                    "session_id": sid,
                    "problem_key": "sample:chop-mat-cau-ngoai-tiep",
                    "step_id": "mp_tt_AB",
                    "step_index": ev11["step_index"],
                    "previous_instruction": ev11.get("learner_text") or "",
                    "edited_instruction": "Dựng mặt phẳng trung trực (P) của cạnh SB.",
                    "target_ids": ["mp_tt_AB"],
                    "absorbed_ids": ["M_AB"],
                    "scene3d": copy.deepcopy(s11),
                    "client_request_id": "osr-pg-req-1",
                    "client_seq": 1,
                    "expected_committed_version": 0,
                },
            )
            assert r.status_code == 200, r.text
            assert r.json()["committed_version"] == 1

    asyncio.run(_run_pg())

    with eng.connect() as conn:
        for tbl in LEGACY_TABLES:
            assert _table_digest(conn, tbl) == baseline[tbl], f"Table {tbl} mutated after Step Edit commit"
        assert _table_digest(conn, "users") == baseline_users
        sess_count = conn.execute(
            text("SELECT count(*) FROM step_edit_sessions WHERE session_id = :sid"),
            {"sid": sid},
        ).scalar_one()
        assert sess_count == 1
    eng.dispose()
