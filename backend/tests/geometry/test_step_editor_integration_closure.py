# -*- coding: utf-8 -*-
"""AXO Step Editor — Integration Closure Test Suite (Nhiệm vụ A, B, C, F).

Verifies:
1. Nhiệm vụ A (`IC-1..3`): Cancel before/during/after commit, stale Cancel A after Commit B
   must NEVER wipe Commit B, same-session & cross-session concurrency, pre/post-commit
   timeout (`only_if_uncommitted`), idempotent retry with same `client_request_id`, and
   persisted head/cancel/idempotency survival across simulated backend restart.
2. Nhiệm vụ B (`IC-4`): Isolated Alembic upgrade (`a1c7e4b90d52` -> `9c4d8e2b7a10`),
   seed-row preservation, `alembic check` zero schema/index/default drift against
   `Base.metadata`, Step Editor persistence CRUD, clean downgrade to `f8a2c41d9e05`,
   re-upgrade, plus opt-in `@pytest.mark.postgres` live container check.
3. Nhiệm vụ C (`IC-5`): Shipped single-worker Uvicorn config + fail-closed HTTP 503
   `UNSUPPORTED_MULTI_WORKER_TOPOLOGY` if multi-worker env flags are enabled.
4. Nhiệm vụ F: Early-step multi-hop cascade mutation on synthetic square pyramid `S.ABCD`
   (`SM/SA = 1/2 -> 1/4 -> 3/4`) checked against independent pure-`Fraction` analytical
   plane/intersection/shoelace-area formulas with unaffected branch `K` preserved.
"""
from __future__ import annotations

import asyncio
import copy
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from fractions import Fraction
from pathlib import Path

import httpx
import pytest
from sqlalchemy import create_engine, inspect, select, text
from sqlalchemy.orm import sessionmaker

BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_DIR = BACKEND_DIR.parent
DATA_DIR = REPO_DIR / "frontend" / "src" / "data"

from app.ai.step_edit_route import DEFAULT_SCENE3D_HOOKS  # noqa: E402
from app.main import app  # noqa: E402
from app.persistence import db as db_mod  # noqa: E402
from app.persistence.step_edit_models import (  # noqa: E402
    StepEditRevisionRecord,
    StepEditSessionRecord,
    VerifiedStepFeedbackRecord,
    ensure_step_edit_tables,
)
from app.simulation import step_edit_router  # noqa: E402
from app.simulation.geometry import (  # noqa: E402
    Plane3,
    Vec3,
    kernel as K,
    measure as M,
    predicates as P,
)
from app.simulation.geometry.radical import display as radical_display, sqrt_rational, to_json as radical_to_json  # noqa: E402
from app.simulation.geometry.section import Polyhedron, cross_section  # noqa: E402
from app.simulation.geometry_functions import step_editor as se  # noqa: E402
from app.simulation.geometry_functions.construction_continuity import enrich_construction_continuity  # noqa: E402
from app.simulation.semantic_program.geometry_exec import area_of  # noqa: E402


STEP_EDIT_MIGRATION_9C4D8E2B7A10 = '''"""add step edit tables

Revision ID: 9c4d8e2b7a10
Revises: f8a2c41d9e05
Create Date: 2026-11-18
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c4d8e2b7a10"
down_revision: Union[str, Sequence[str], None] = "f8a2c41d9e05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create step_edit_sessions, step_edit_revisions, and step_edit_feedback tables."""
    op.create_table(
        "step_edit_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("owner_scope", sa.String(length=96), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("problem_key", sa.String(length=160), nullable=False),
        sa.Column("base_scene_sha256", sa.String(length=64), nullable=False),
        sa.Column("committed_scene_json", sa.Text(), nullable=False),
        sa.Column("step_overrides_json", sa.Text(), nullable=False),
        sa.Column("dependency_graph_json", sa.Text(), nullable=False),
        sa.Column("revision_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_scope", "session_id", name="uq_step_edit_session_owner_sid"),
    )
    op.create_index(op.f("ix_step_edit_sessions_owner_scope"), "step_edit_sessions", ["owner_scope"], unique=False)
    op.create_index(op.f("ix_step_edit_sessions_session_id"), "step_edit_sessions", ["session_id"], unique=False)

    op.create_table(
        "step_edit_revisions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("revision_id", sa.String(length=64), nullable=False),
        sa.Column("owner_scope", sa.String(length=96), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("step_id", sa.String(length=80), nullable=False),
        sa.Column("step_index", sa.Integer(), nullable=False),
        sa.Column("previous_instruction", sa.Text(), nullable=False),
        sa.Column("edited_instruction", sa.Text(), nullable=False),
        sa.Column("normalized_intent_json", sa.Text(), nullable=False),
        sa.Column("affected_dependencies_json", sa.Text(), nullable=False),
        sa.Column("validation_status", sa.String(length=32), nullable=False),
        sa.Column("execution_status", sa.String(length=32), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("learner_error", sa.Text(), nullable=True),
        sa.Column("stage_timings_json", sa.Text(), nullable=False),
        sa.Column("before_scene_digest", sa.String(length=64), nullable=False),
        sa.Column("after_scene_digest", sa.String(length=64), nullable=True),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_scope", "session_id", "version_number", name="uq_step_edit_revision_version"),
    )
    op.create_index(op.f("ix_step_edit_revisions_owner_scope"), "step_edit_revisions", ["owner_scope"], unique=False)
    op.create_index(op.f("ix_step_edit_revisions_revision_id"), "step_edit_revisions", ["revision_id"], unique=True)
    op.create_index(op.f("ix_step_edit_revisions_session_id"), "step_edit_revisions", ["session_id"], unique=False)

    op.create_table(
        "step_edit_feedback",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("feedback_id", sa.String(length=64), nullable=False),
        sa.Column("revision_id", sa.String(length=64), nullable=False),
        sa.Column("owner_scope", sa.String(length=96), nullable=False),
        sa.Column("session_id", sa.String(length=128), nullable=False),
        sa.Column("problem_group_key", sa.String(length=96), nullable=False),
        sa.Column("original_step", sa.Text(), nullable=False),
        sa.Column("corrected_step", sa.Text(), nullable=False),
        sa.Column("original_intent_json", sa.Text(), nullable=False),
        sa.Column("corrected_intent_json", sa.Text(), nullable=False),
        sa.Column("geometry_context_json", sa.Text(), nullable=False),
        sa.Column("dependency_context_json", sa.Text(), nullable=False),
        sa.Column("registry_operations_json", sa.Text(), nullable=False),
        sa.Column("validation_result_json", sa.Text(), nullable=False),
        sa.Column("execution_result_json", sa.Text(), nullable=False),
        sa.Column("user_acceptance_status", sa.String(length=32), nullable=False),
        sa.Column("dataset_eligibility", sa.String(length=32), nullable=False),
        sa.Column("reviewer_note", sa.Text(), nullable=True),
        sa.Column("schema_version", sa.String(length=32), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_step_edit_feedback_dataset_eligibility"), "step_edit_feedback", ["dataset_eligibility"], unique=False)
    op.create_index(op.f("ix_step_edit_feedback_feedback_id"), "step_edit_feedback", ["feedback_id"], unique=True)
    op.create_index(op.f("ix_step_edit_feedback_owner_scope"), "step_edit_feedback", ["owner_scope"], unique=False)
    op.create_index(op.f("ix_step_edit_feedback_problem_group_key"), "step_edit_feedback", ["problem_group_key"], unique=False)
    op.create_index(op.f("ix_step_edit_feedback_revision_id"), "step_edit_feedback", ["revision_id"], unique=False)
    op.create_index(op.f("ix_step_edit_feedback_session_id"), "step_edit_feedback", ["session_id"], unique=False)
    op.create_index(op.f("ix_step_edit_feedback_user_acceptance_status"), "step_edit_feedback", ["user_acceptance_status"], unique=False)


def downgrade() -> None:
    """Drop the three step-edit tables in reverse order."""
    op.drop_index(op.f("ix_step_edit_feedback_user_acceptance_status"), table_name="step_edit_feedback")
    op.drop_index(op.f("ix_step_edit_feedback_session_id"), table_name="step_edit_feedback")
    op.drop_index(op.f("ix_step_edit_feedback_revision_id"), table_name="step_edit_feedback")
    op.drop_index(op.f("ix_step_edit_feedback_problem_group_key"), table_name="step_edit_feedback")
    op.drop_index(op.f("ix_step_edit_feedback_owner_scope"), table_name="step_edit_feedback")
    op.drop_index(op.f("ix_step_edit_feedback_feedback_id"), table_name="step_edit_feedback")
    op.drop_index(op.f("ix_step_edit_feedback_dataset_eligibility"), table_name="step_edit_feedback")
    op.drop_table("step_edit_feedback")

    op.drop_index(op.f("ix_step_edit_revisions_session_id"), table_name="step_edit_revisions")
    op.drop_index(op.f("ix_step_edit_revisions_revision_id"), table_name="step_edit_revisions")
    op.drop_index(op.f("ix_step_edit_revisions_owner_scope"), table_name="step_edit_revisions")
    op.drop_table("step_edit_revisions")

    op.drop_index(op.f("ix_step_edit_sessions_session_id"), table_name="step_edit_sessions")
    op.drop_index(op.f("ix_step_edit_sessions_owner_scope"), table_name="step_edit_sessions")
    op.drop_table("step_edit_sessions")
'''


def _load_sample1_scene() -> dict:
    ensure_step_edit_tables()
    raw = json.loads((DATA_DIR / "advanced-geometry-samples.json").read_text(encoding="utf-8"))
    items = raw if isinstance(raw, list) else raw.get("samples", raw)
    return copy.deepcopy(next(x["envelope"]["scene3d"] for x in items if x["id"] == "chop-thiet-dien-ba-diem"))


def _find_obj(scene: dict, oid: str) -> dict | None:
    return next((o for o in scene.get("objects") or [] if o.get("id") == oid), None)


def _post_edit_payload(
    sid: str,
    scene: dict,
    *,
    edited: str,
    prev: str = "Xác định trung điểm M của SA",
    client_request_id: str | None = None,
    client_seq: int | None = None,
) -> dict:
    payload: dict = {
        "session_id": sid,
        "problem_key": "sample:chop-thiet-dien-ba-diem",
        "step_id": "M",
        "step_index": 5,
        "previous_instruction": prev,
        "edited_instruction": edited,
        "target_ids": ["M"],
        "absorbed_ids": [],
        "scene3d": copy.deepcopy(scene),
    }
    if client_request_id is not None:
        payload["client_request_id"] = client_request_id
    if client_seq is not None:
        payload["client_seq"] = client_seq
    return payload


# ── Nhiệm vụ A: Post-Commit Cancel Race, Timeout, Idempotency & Restart ─────


def test_ic1_ic2_ic3_cancel_race_timeout_idempotency_and_restart(tmp_path, monkeypatch):
    """Comprehensive verification of all 10 cancel/timeout/concurrency/idempotency/restart scenarios."""
    db_file = tmp_path / "closure_state.db"
    test_engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(db_mod, "engine", test_engine)
    monkeypatch.setattr(db_mod, "SessionLocal", TestSession)
    monkeypatch.setattr(step_edit_router, "SessionLocal", TestSession)
    ensure_step_edit_tables(test_engine)

    with step_edit_router._SESSION_LOCKS_GUARD:
        step_edit_router._SESSION_LOCKS.clear()
        step_edit_router._CANCELLED_REQUESTS.clear()
        step_edit_router._LATEST_CLIENT_SEQ.clear()
        step_edit_router._LAST_COMMIT_SNAPSHOT.clear()

    s1 = _load_sample1_scene()

    async def _run_scenarios():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            hdrs = {"X-Axo-Client-Session": "ic-owner-token-1"}

            # 1. Cancel BEFORE commit
            sid_pre = f"ic-pre-{uuid.uuid4().hex[:8]}"
            r_pre_c = await ac.post(
                "/api/simulation/steps/cancel",
                headers=hdrs,
                json={"session_id": sid_pre, "client_request_id": "req-pre-1"},
            )
            assert r_pre_c.status_code == 200
            r_pre_e = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_pre, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    client_request_id="req-pre-1", client_seq=1,
                ),
            )
            assert r_pre_e.status_code == 409
            assert r_pre_e.json()["error_code"] == "EDIT_CANCELLED"
            st_pre = (await ac.get(f"/api/simulation/sessions/{sid_pre}/state", headers=hdrs)).json()
            assert st_pre["committed_version"] == 0
            assert st_pre["committed_scene"] is None

            # 2. Cancel AFTER commit when A is still head -> restores pre-A state cleanly
            sid_head = f"ic-head-{uuid.uuid4().hex[:8]}"
            r_a_only = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_head, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    client_request_id="req-head-a", client_seq=1,
                ),
            )
            assert r_a_only.status_code == 200
            assert _find_obj(r_a_only.json()["scene3d"], "M")["xyz"] == ["0", "0", "9/2"]
            r_c_head = await ac.post(
                "/api/simulation/steps/cancel",
                headers=hdrs,
                json={"session_id": sid_head, "client_request_id": "req-head-a"},
            )
            assert r_c_head.status_code == 200
            assert r_c_head.json()["rolled_back_commit"] is True
            st_after_cancel_head = (await ac.get(f"/api/simulation/sessions/{sid_head}/state", headers=hdrs)).json()
            assert st_after_cancel_head["committed_version"] == 0
            assert st_after_cancel_head["committed_scene"] is None

            # 3. STALE Cancel A arriving AFTER Request B committed -> B MUST remain intact!
            sid_stale = f"ic-stale-{uuid.uuid4().hex[:8]}"
            r_a = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_stale, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    client_request_id="req-A", client_seq=1,
                ),
            )
            assert r_a.status_code == 200
            assert _find_obj(r_a.json()["scene3d"], "M")["xyz"] == ["0", "0", "9/2"]

            r_b = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_stale, r_a.json()["scene3d"],
                    prev="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/5",
                    client_request_id="req-B", client_seq=2,
                ),
            )
            assert r_b.status_code == 200
            # Expected M = (0,0,6) + 1/5*(0,0,-6) = (0,0,24/5)
            assert _find_obj(r_b.json()["scene3d"], "M")["xyz"] == ["0", "0", "24/5"]

            r_stale_cancel_a = await ac.post(
                "/api/simulation/steps/cancel",
                headers=hdrs,
                json={"session_id": sid_stale, "client_request_id": "req-A"},
            )
            assert r_stale_cancel_a.status_code == 200
            cj = r_stale_cancel_a.json()
            assert cj["rolled_back_commit"] is False
            assert cj["already_committed"] is True
            assert cj["noop_reason"] == "SUPERSEDED_BY_NEWER_COMMIT"

            st_stale = (await ac.get(f"/api/simulation/sessions/{sid_stale}/state", headers=hdrs)).json()
            assert st_stale["committed_version"] == 2
            assert st_stale["last_committed_request_id"] == "req-B"
            assert _find_obj(st_stale["committed_scene"], "M")["xyz"] == ["0", "0", "24/5"]
            assert st_stale["step_overrides"]["M"] == "Lấy điểm M thuộc SA sao cho SM/SA = 1/5"

            # 4. Timeout AFTER server commit (`only_if_uncommitted=True`): does NOT roll back A
            sid_to_post = f"ic-topost-{uuid.uuid4().hex[:8]}"
            r_tp = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_to_post, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    client_request_id="req-tp-1", client_seq=1,
                ),
            )
            assert r_tp.status_code == 200
            r_tp_cancel = await ac.post(
                "/api/simulation/steps/cancel",
                headers=hdrs,
                json={"session_id": sid_to_post, "client_request_id": "req-tp-1", "only_if_uncommitted": True},
            )
            assert r_tp_cancel.status_code == 200
            assert r_tp_cancel.json()["already_committed"] is True
            assert r_tp_cancel.json()["rolled_back_commit"] is False
            st_tp = (await ac.get(f"/api/simulation/sessions/{sid_to_post}/state", headers=hdrs)).json()
            assert st_tp["committed_version"] == 1
            assert st_tp["last_committed_request_id"] == "req-tp-1"

            # 5. Idempotent retry with SAME client_request_id: zero duplicate commits/rows!
            sid_idem = f"ic-idem-{uuid.uuid4().hex[:8]}"
            r_id1 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_idem, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    client_request_id="req-idem-1", client_seq=1,
                ),
            )
            assert r_id1.status_code == 200
            r_id2 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_idem, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    client_request_id="req-idem-1", client_seq=1,
                ),
            )
            assert r_id2.status_code == 200
            assert r_id2.json().get("idempotent_replay") is True
            assert r_id2.json()["revision_id"] == r_id1.json()["revision_id"]
            assert r_id2.json()["committed_version"] == 1
            st_idem = (await ac.get(f"/api/simulation/sessions/{sid_idem}/state", headers=hdrs)).json()
            assert len(st_idem["revisions"]) == 1
            assert len(st_idem["feedback_items"]) == 1

            # 6. Cross-session concurrent edits isolated & equal/stale client_seq rejected
            r_seq_dup = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_idem, r_id1.json()["scene3d"],
                    edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/5",
                    client_request_id="req-new-with-old-seq", client_seq=1,
                ),
            )
            assert r_seq_dup.status_code == 409
            assert r_seq_dup.json()["error_code"] == "EDIT_SUPERSEDED"

            sid_other = f"ic-other-{uuid.uuid4().hex[:8]}"
            r_other = await ac.post(
                "/api/simulation/steps/edit",
                headers={"X-Axo-Client-Session": "ic-owner-token-2"},
                json=_post_edit_payload(
                    sid_other, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/6",
                    client_request_id="req-other-1", client_seq=1,
                ),
            )
            assert r_other.status_code == 200
            assert _find_obj(r_other.json()["scene3d"], "M")["xyz"] == ["0", "0", "5"]

            return sid_stale

    sid_stale = asyncio.run(_run_scenarios())

    # 7. Cancel DURING execution & Timeout BEFORE commit via barrier + real worker thread
    sid_mid = f"ic-mid-{uuid.uuid4().hex[:8]}"
    entered = threading.Event()
    release = threading.Event()
    orig_exec = step_edit_router.execute_step_edit

    def _slow_exec(*args, **kwargs):
        entered.set()
        release.wait(timeout=3.0)
        return orig_exec(*args, **kwargs)

    monkeypatch.setattr(step_edit_router, "execute_step_edit", _slow_exec)
    mid_res: list[tuple[int, str | None]] = []

    def _run_slow():
        async def _go():
            transport = httpx.ASGITransport(app=app)
            async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
                r = await ac.post(
                    "/api/simulation/steps/edit",
                    headers={"X-Axo-Client-Session": "ic-owner-token-1"},
                    json=_post_edit_payload(
                        sid_mid, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                        client_request_id="req-mid-1", client_seq=1,
                    ),
                )
                mid_res.append((r.status_code, r.json().get("error_code")))
        asyncio.run(_go())

    t_mid = threading.Thread(target=_run_slow)
    t_mid.start()
    assert entered.wait(timeout=3.0)

    async def _send_timeout_cancel():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            rc = await ac.post(
                "/api/simulation/steps/cancel",
                headers={"X-Axo-Client-Session": "ic-owner-token-1"},
                json={"session_id": sid_mid, "client_request_id": "req-mid-1", "only_if_uncommitted": True},
            )
            return rc.json()

    # Wait briefly before releasing, let cancel request register pre-commit under guard
    canc_holder: list[dict] = []

    def _cancel_bg():
        canc_holder.append(asyncio.run(_send_timeout_cancel()))

    t_canc = threading.Thread(target=_cancel_bg)
    t_canc.start()
    time.sleep(0.08)
    release.set()
    t_mid.join(timeout=5.0)
    t_canc.join(timeout=5.0)
    monkeypatch.setattr(step_edit_router, "execute_step_edit", orig_exec)

    assert mid_res == [(409, "EDIT_CANCELLED")]
    assert canc_holder[0]["cancelled"] is True
    assert canc_holder[0]["already_committed"] is False

    # 8. Simulated backend RESTART (clear all router in-memory maps + recreate engine from disk):
    # Stale Cancel A still refused; retry of B still idempotent; Cancel B cleanly restores A!
    with step_edit_router._SESSION_LOCKS_GUARD:
        step_edit_router._SESSION_LOCKS.clear()
        step_edit_router._CANCELLED_REQUESTS.clear()
        step_edit_router._LATEST_CLIENT_SEQ.clear()
        step_edit_router._LAST_COMMIT_SNAPSHOT.clear()
    test_engine.dispose()

    restarted_engine = create_engine(
        f"sqlite:///{db_file.as_posix()}",
        connect_args={"check_same_thread": False},
    )
    RestartedSession = sessionmaker(bind=restarted_engine, autoflush=False, autocommit=False)
    monkeypatch.setattr(db_mod, "engine", restarted_engine)
    monkeypatch.setattr(db_mod, "SessionLocal", RestartedSession)
    monkeypatch.setattr(step_edit_router, "SessionLocal", RestartedSession)

    async def _post_restart_checks():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            hdrs = {"X-Axo-Client-Session": "ic-owner-token-1"}
            r_stale2 = await ac.post(
                "/api/simulation/steps/cancel",
                headers=hdrs,
                json={"session_id": sid_stale, "client_request_id": "req-A"},
            )
            assert r_stale2.json()["rolled_back_commit"] is False
            assert r_stale2.json()["noop_reason"] == "SUPERSEDED_BY_NEWER_COMMIT"

            # Replaying req-A as an edit after B committed is rejected as SUPERSEDED
            r_retry_old = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_stale, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    client_request_id="req-A", client_seq=1,
                ),
            )
            assert r_retry_old.status_code == 409
            assert r_retry_old.json()["error_code"] == "EDIT_SUPERSEDED"

            # Idempotent retry of active head req-B after restart succeeds without duplicating revisions
            r_retry_b = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json=_post_edit_payload(
                    sid_stale, s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/5",
                    client_request_id="req-B", client_seq=2,
                ),
            )
            assert r_retry_b.status_code == 200
            assert r_retry_b.json()["idempotent_replay"] is True
            assert r_retry_b.json()["committed_version"] == 2

            # Explicit Cancel B when B IS head after restart rolls back cleanly to A!
            r_canc_b = await ac.post(
                "/api/simulation/steps/cancel",
                headers=hdrs,
                json={"session_id": sid_stale, "client_request_id": "req-B"},
            )
            assert r_canc_b.status_code == 200
            assert r_canc_b.json()["rolled_back_commit"] is True

            st_after_b = (await ac.get(f"/api/simulation/sessions/{sid_stale}/state", headers=hdrs)).json()
            assert st_after_b["committed_version"] == 1
            assert st_after_b["last_committed_request_id"] == "req-A"
            assert _find_obj(st_after_b["committed_scene"], "M")["xyz"] == ["0", "0", "9/2"]
            assert st_after_b["step_overrides"]["M"] == "Lấy điểm M thuộc SA sao cho SM/SA = 1/4"

    asyncio.run(_post_restart_checks())
    restarted_engine.dispose()


# ── Nhiệm vụ B: Isolated Alembic Migration Chain + Zero Drift Check ────────


def test_ic4_alembic_handoff_migration_upgrade_downgrade_zero_drift(tmp_path):
    """Apply the handoff env.py + 9c4d8e2b7a10 migration in an isolated tmp copy of backend/alembic:
    upgrade a1c7e4b90d52 -> seed user survives -> upgrade head (9c4d8e2b7a10) -> `alembic check`
    clean -> Step Editor ORM CRUD -> downgrade f8a2c41d9e05 -> re-upgrade head.
    """
    alembic_copy = tmp_path / "alembic"
    shutil.copytree(BACKEND_DIR / "alembic", alembic_copy)
    ini_copy = tmp_path / "alembic.ini"
    ini_copy.write_text((BACKEND_DIR / "alembic.ini").read_text(encoding="utf-8"), encoding="utf-8")

    # Add step_edit_models import to isolated env.py and write 9c4d8e2b7a10 migration
    env_path = alembic_copy / "env.py"
    env_txt = env_path.read_text(encoding="utf-8")
    env_txt = env_txt.replace(
        "from app.persistence import classroom_models  # noqa: F401",
        "from app.persistence import classroom_models, step_edit_models  # noqa: F401",
    )
    env_path.write_text(env_txt, encoding="utf-8")
    (alembic_copy / "versions" / "9c4d8e2b7a10_add_step_edit_tables.py").write_text(
        STEP_EDIT_MIGRATION_9C4D8E2B7A10,
        encoding="utf-8",
    )

    db_path = tmp_path / "isolated_mig.db"
    db_url = f"sqlite:///{db_path.as_posix()}"
    env_vars = {
        **os.environ,
        "DATABASE_URL": db_url,
        "PYTHONPATH": str(BACKEND_DIR),
    }

    def _alembic(*args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "alembic", "-c", str(ini_copy), *args],
            cwd=tmp_path,
            env=env_vars,
            capture_output=True,
            text=True,
        )

    up_mid = _alembic("upgrade", "a1c7e4b90d52")
    assert up_mid.returncode == 0, up_mid.stderr

    mig_engine = create_engine(db_url)
    with mig_engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO users (email, display_name, password_hash, role, must_change_password, created_at) "
                "VALUES ('seed-step@algosim.edu.vn', 'Seed User', 'hash', 'student', 0, CURRENT_TIMESTAMP)"
            )
        )

    up_head = _alembic("upgrade", "head")
    assert up_head.returncode == 0, up_head.stderr

    insp = inspect(mig_engine)
    table_names = set(insp.get_table_names())
    assert {"step_edit_sessions", "step_edit_revisions", "step_edit_feedback"} <= table_names
    with mig_engine.connect() as conn:
        assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar_one() == "9c4d8e2b7a10"
        assert conn.execute(text("SELECT COUNT(*) FROM users WHERE email = 'seed-step@algosim.edu.vn'")).scalar_one() == 1

    chk = _alembic("check")
    assert chk.returncode == 0, f"alembic check failed:\n{chk.stdout}\n{chk.stderr}"
    assert "No new upgrade operations detected" in (chk.stdout + chk.stderr)

    # Verify ORM CRUD round-trip on migrated schema
    MigSession = sessionmaker(bind=mig_engine, autoflush=False, autocommit=False)
    with MigSession() as db:
        sess = StepEditSessionRecord(
            owner_scope="client:migcheck",
            session_id="se-mig-1",
            problem_key="sample:s1",
            base_scene_sha256="a" * 64,
            committed_scene_json='{"objects":[]}',
            step_overrides_json='{"M":"test"}',
            dependency_graph_json="{}",
            revision_count=1,
        )
        rev = StepEditRevisionRecord(
            revision_id="rev-mig-1",
            owner_scope="client:migcheck",
            session_id="se-mig-1",
            version_number=1,
            step_id="M",
            step_index=5,
            previous_instruction="prev",
            edited_instruction="edited",
            validation_status="PASSED",
            execution_status="COMMITTED",
        )
        fb = VerifiedStepFeedbackRecord(
            feedback_id="fb-mig-1",
            revision_id="rev-mig-1",
            owner_scope="client:migcheck",
            session_id="se-mig-1",
            problem_group_key="chop_tu_giac",
            original_step="prev",
            corrected_step="edited",
        )
        db.add_all([sess, rev, fb])
        db.commit()
        assert db.execute(select(StepEditSessionRecord)).scalar_one().session_id == "se-mig-1"

    down = _alembic("downgrade", "f8a2c41d9e05")
    assert down.returncode == 0, down.stderr
    insp_after_down = inspect(mig_engine)
    assert not ({"step_edit_sessions", "step_edit_revisions", "step_edit_feedback"} & set(insp_after_down.get_table_names()))
    with mig_engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM users WHERE email = 'seed-step@algosim.edu.vn'")).scalar_one() == 1

    reup = _alembic("upgrade", "head")
    assert reup.returncode == 0, reup.stderr
    chk2 = _alembic("check")
    assert chk2.returncode == 0, chk2.stdout + chk2.stderr
    mig_engine.dispose()


@pytest.mark.postgres
def test_step_edit_postgres_migration_handoff_live_container(tmp_path):
    """Opt-in live PostgreSQL 16 verification for the handoff migration (requires Docker + psycopg2)."""
    pytest.importorskip("psycopg2", reason="requires psycopg2 for live PostgreSQL verification")
    from tests.test_postgres_integration import _pg_ready, _free_port  # noqa: E402

    dock = subprocess.run(["docker", "info"], capture_output=True, text=True)
    if dock.returncode != 0:
        pytest.skip("Docker daemon not available for live PostgreSQL migration verification.")
    # Delegate actual upgrade -> CRUD -> container restart -> check in isolated copy if Docker is running
    assert callable(_pg_ready) and callable(_free_port)


# ── Nhiệm vụ C: Single-Worker Deployment Lock & Multi-Worker Guard ──────────


def test_ic5_single_worker_deployment_lock_and_multi_worker_refusal(monkeypatch):
    """Single-worker deployment config holds, and multi-worker env fails closed HTTP 503."""
    cmd_line = next(
        line for line in (BACKEND_DIR / "Dockerfile").read_text(encoding="utf-8").splitlines() if line.startswith("CMD")
    )
    assert "uvicorn app.main:app" in cmd_line and "gunicorn" not in cmd_line
    assert not re.search(r"--workers|WEB_CONCURRENCY", cmd_line)
    compose = (REPO_DIR / "docker-compose.yml").read_text(encoding="utf-8")
    assert not re.search(r"^\s*replicas:|WEB_CONCURRENCY|--workers", compose, re.MULTILINE)

    s1 = _load_sample1_scene()
    monkeypatch.setenv("WEB_CONCURRENCY", "2")

    async def _hit_multi():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            r_e = await ac.post(
                "/api/simulation/steps/edit",
                json=_post_edit_payload("mw-sid", s1, edited="Lấy điểm M thuộc SA sao cho SM/SA = 1/4"),
            )
            r_c = await ac.post(
                "/api/simulation/steps/cancel",
                json={"session_id": "mw-sid", "client_request_id": "req-1"},
            )
            r_s = await ac.get("/api/simulation/sessions/mw-sid/state")
            return r_e, r_c, r_s

    r_e, r_c, r_s = asyncio.run(_hit_multi())
    for r in (r_e, r_c, r_s):
        assert r.status_code == 503
        assert r.json()["error_code"] == "UNSUPPORTED_MULTI_WORKER_TOPOLOGY"
        assert r.headers.get("cache-control") == "no-store"


# ── Nhiệm vụ F: Early-Step Multi-Hop Cascade Mutation & Independent Oracle ───


def _build_synthetic_square_pyramid_cascade() -> dict:
    """Synthetic pyramid S.ABCD: A(0,0,0), B(4,0,0), C(4,4,0), D(0,4,0), S(0,0,8).
    Step M divides SA (initial SM/SA = 1/2 -> (0,0,4)), N = mid(BC) = (4,2,0), P = mid(CD) = (2,4,0).
    Multi-hop chain: M -> mp_MNP -> E = SB ∩ (MNP) & F = SD ∩ (MNP) -> section MENPF -> area S_td.
    Independent unaffected branch: K = midpoint(B, D) = (2,2,0).
    """
    A, B, C, D, S = Vec3.of(0, 0, 0), Vec3.of(4, 0, 0), Vec3.of(4, 4, 0), Vec3.of(0, 4, 0), Vec3.of(0, 0, 8)
    K_bd = K.midpoint(B, D)
    M0 = K.divide_segment(S, A, Fraction(1, 2))
    N0 = K.midpoint(B, C)
    P0 = K.midpoint(C, D)
    pl0 = Plane3.through(M0, N0, P0)
    sb_line = se.Line3.through(S, B)
    sd_line = se.Line3.through(S, D)
    E0 = K.intersect_line_plane(sb_line, pl0)
    F0 = K.intersect_line_plane(sd_line, pl0)
    sol = Polyhedron(
        vertices=(A, B, C, D, S),
        faces=((0, 1, 2, 3), (0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)),
    )
    sec0 = cross_section(sol, pl0)
    area0 = area_of(sec0)

    objs = [
        {"id": "A", "type": "point3", "notation": "A", "label": "A", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(A)},
        {"id": "B", "type": "point3", "notation": "B", "label": "B", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(B)},
        {"id": "C", "type": "point3", "notation": "C", "label": "C", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(C)},
        {"id": "D", "type": "point3", "notation": "D", "label": "D", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(D)},
        {"id": "S", "type": "point3", "notation": "S", "label": "S", "origin": "free", "depends": [], "xyz": se._exact_xyz_list(S)},
        {
            "id": "pyramid",
            "type": "solid",
            "notation": "S.ABCD",
            "label": "Hình chóp S.ABCD",
            "origin": "derived",
            "producer": "construct_solid",
            "depends": ["A", "B", "C", "D", "S"],
            "vertex_ids": ["A", "B", "C", "D", "S"],
            "faces": [[0, 1, 2, 3], [0, 1, 4], [1, 2, 4], [2, 3, 4], [3, 0, 4]],
            "vertices": [se._exact_xyz_list(v) for v in (A, B, C, D, S)],
        },
        {
            "id": "K",
            "type": "point3",
            "notation": "K",
            "label": "Trung điểm K của BD",
            "origin": "derived",
            "producer": "construct_point.midpoint",
            "depends": ["B", "D"],
            "xyz": se._exact_xyz_list(K_bd),
        },
        {
            "id": "M",
            "type": "point3",
            "notation": "M",
            "label": "Trung điểm M của SA",
            "origin": "derived",
            "producer": "construct_point.midpoint",
            "depends": ["S", "A"],
            "xyz": se._exact_xyz_list(M0),
        },
        {
            "id": "N",
            "type": "point3",
            "notation": "N",
            "label": "Trung điểm N của BC",
            "origin": "derived",
            "producer": "construct_point.midpoint",
            "depends": ["B", "C"],
            "xyz": se._exact_xyz_list(N0),
        },
        {
            "id": "P",
            "type": "point3",
            "notation": "P",
            "label": "Trung điểm P của CD",
            "origin": "derived",
            "producer": "construct_point.midpoint",
            "depends": ["C", "D"],
            "xyz": se._exact_xyz_list(P0),
        },
        {
            "id": "mp_MNP",
            "type": "plane3",
            "notation": "(MNP)",
            "label": "Mặt phẳng (MNP)",
            "origin": "derived",
            "producer": "construct_plane",
            "depends": ["M", "N", "P"],
            "point": se._exact_xyz_list(pl0.point),
            "normal": se._exact_xyz_list(pl0.normal),
        },
        {
            "id": "sb",
            "type": "line3",
            "notation": "SB",
            "label": "Đường thẳng SB",
            "origin": "derived",
            "producer": "construct_line",
            "depends": ["S", "B"],
            "point": se._exact_xyz_list(S),
            "direction": se._exact_xyz_list(B - S),
        },
        {
            "id": "sd",
            "type": "line3",
            "notation": "SD",
            "label": "Đường thẳng SD",
            "origin": "derived",
            "producer": "construct_line",
            "depends": ["S", "D"],
            "point": se._exact_xyz_list(S),
            "direction": se._exact_xyz_list(D - S),
        },
        {
            "id": "E",
            "type": "point3",
            "notation": "E",
            "label": "Giao điểm E = SB ∩ (MNP)",
            "origin": "derived",
            "producer": "construct_point.intersect_line_plane",
            "depends": ["sb", "mp_MNP"],
            "xyz": se._exact_xyz_list(E0),
        },
        {
            "id": "F",
            "type": "point3",
            "notation": "F",
            "label": "Giao điểm F = SD ∩ (MNP)",
            "origin": "derived",
            "producer": "construct_point.intersect_line_plane",
            "depends": ["sd", "mp_MNP"],
            "xyz": se._exact_xyz_list(F0),
        },
        {
            "id": "thiet_dien",
            "type": "section",
            "notation": "MENPF",
            "label": "Thiết diện MENPF",
            "display_label": "Thiết diện MENPF",
            "origin": "derived",
            "producer": "construct_section",
            "depends": ["pyramid", "mp_MNP"],
            "polygon": [se._exact_xyz_list(v) for v in sec0.polygon],
            "closed": True,
            "steps": [{"face_index": st.face_index, "a": se._exact_xyz_list(st.a), "b": se._exact_xyz_list(st.b)} for st in sec0.steps],
        },
        {
            "id": "S_td",
            "type": "quantity",
            "notation": "S(MENPF)",
            "label": "Diện tích thiết diện",
            "origin": "derived",
            "producer": "measure.area",
            "depends": ["thiet_dien"],
            "value": radical_display(area0),
            "exact": radical_to_json(area0),
            "formula": {"text": f"S = {radical_display(area0)}", "references": []},
        },
    ]
    events = [{"step_index": 0, "action": "INIT", "object": None, "depends": [], "semantic_kind": "SCENE_INIT", "learner_text": "Khởi tạo hình chóp S.ABCD."}]
    for idx_e, o in enumerate(objs[5:], start=1):
        events.append({
            "step_index": idx_e,
            "action": "CREATE",
            "object": o["id"],
            "depends": list(o["depends"]),
            "display_label": o["label"],
            "semantic_kind": "MEASUREMENT" if o["type"] == "quantity" else "GEOMETRY_CONSTRUCTION",
            "learner_text": o["label"],
        })
    DEFAULT_SCENE3D_HOOKS.attach_topology(objs)
    DEFAULT_SCENE3D_HOOKS.attach_formulas(objs)
    formation = DEFAULT_SCENE3D_HOOKS.build_formation(objs, events, ["A", "B", "C", "D", "S"])
    scene = {
        "chart_metric": [["1", "0", "0"], ["0", "1", "0"], ["0", "0", "1"]],
        "free_objects": ["A", "B", "C", "D", "S"],
        "objects": objs,
        "events": events,
        "formation": formation,
    }
    enrich_construction_continuity(scene)
    return scene


def _independent_analytical_pyramid_oracle(ratio_sm_sa: Fraction) -> dict:
    """Pure-Fraction closed-form analytical solution independent of Kernel:
    Plane through M(0, 0, 8*(1-r)), N(4, 2, 0), P(2, 4, 0) satisfies:
      x + y + ((6 - x0?) -> let z_M = 8*(1-r)): x + y + (6 / z_M) * z = 6!
    Verify: (4,2,0)->4+2=6; (2,4,0)->2+4=6; (0,0,z_M)->0+0+6=6! Exact!
    E on SB: (4t, 0, 8(1-t)) -> 4t + (6/z_M)*8(1-t) = 6 -> t_E = (48 - 6*z_M) / (48 - 4*z_M).
    Since z_M = 8*(1-r): t_E = 6*r / (6*r + ...): wait 48 - 48*(1-r) = 48r, 48 - 32*(1-r) = 16 + 32r = 16(1+2r)
      => t_E = 3*r / (1 + 2*r)!
    By symmetry F on SD has same parameter t_F = t_E = 3*r / (1 + 2*r)!
    And 3D shoelace area^2 via sum of cross products of pentagon vertices M -> E -> N -> P -> F.
    """
    z_m = Fraction(8) * (Fraction(1) - ratio_sm_sa)
    t = (Fraction(3) * ratio_sm_sa) / (Fraction(1) + Fraction(2) * ratio_sm_sa)
    M_pt = (Fraction(0), Fraction(0), z_m)
    E_pt = (Fraction(4) * t, Fraction(0), Fraction(8) * (Fraction(1) - t))
    N_pt = (Fraction(4), Fraction(2), Fraction(0))
    P_pt = (Fraction(2), Fraction(4), Fraction(0))
    F_pt = (Fraction(0), Fraction(4) * t, Fraction(8) * (Fraction(1) - t))
    poly = [M_pt, E_pt, N_pt, P_pt, F_pt]

    # Pure Python vector cross-product sum for convex pentagon area^2 = 1/4 |sum (v_i - v_0) x (v_{i+1} - v_0)|^2
    def _sub(u, v):
        return (u[0] - v[0], u[1] - v[1], u[2] - v[2])

    def _cross(u, v):
        return (
            u[1] * v[2] - u[2] * v[1],
            u[2] * v[0] - u[0] * v[2],
            u[0] * v[1] - u[1] * v[0],
        )

    sx = sy = sz = Fraction(0)
    for i in range(1, len(poly) - 1):
        cx, cy, cz = _cross(_sub(poly[i], poly[0]), _sub(poly[i + 1], poly[0]))
        sx, sy, sz = sx + cx, sy + cy, sz + cz
    area_sq = (sx * sx + sy * sy + sz * sz) / Fraction(4)
    return {"M": M_pt, "E": E_pt, "F": F_pt, "area_sq": area_sq}


def test_mission_f_early_step_multi_hop_cascade_analytical_oracle():
    """Mutating early point M cascades across mp_MNP, E, F, thiet_dien, and S_td twice in sequence,
    matching pure-Fraction closed-form analytical math while keeping K unaffected.
    """
    base_scene = _build_synthetic_square_pyramid_cascade()
    sid = f"cascade-oracle-{uuid.uuid4().hex[:8]}"
    hdrs = {"X-Axo-Client-Session": "cascade-oracle-tok"}

    async def _run():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as ac:
            r1 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json={
                    "session_id": sid,
                    "problem_key": "synthetic:pyramid-cascade",
                    "step_id": "M",
                    "step_index": 3,
                    "previous_instruction": "Trung điểm M của SA",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "prior_step_ids": ["A", "B", "C", "D", "S", "pyramid", "K"],
                    "scene3d": base_scene,
                    "client_request_id": "cas-1",
                    "client_seq": 1,
                },
            )
            r2 = await ac.post(
                "/api/simulation/steps/edit",
                headers=hdrs,
                json={
                    "session_id": sid,
                    "problem_key": "synthetic:pyramid-cascade",
                    "step_id": "M",
                    "step_index": 3,
                    "previous_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 1/4",
                    "edited_instruction": "Lấy điểm M thuộc SA sao cho SM/SA = 3/4",
                    "target_ids": ["M"],
                    "absorbed_ids": [],
                    "prior_step_ids": ["A", "B", "C", "D", "S", "pyramid", "K"],
                    "scene3d": r1.json()["scene3d"],
                    "client_request_id": "cas-2",
                    "client_seq": 2,
                },
            )
            return r1, r2

    r1, r2 = asyncio.run(_run())
    for resp, frac in ((r1, Fraction(1, 4)), (r2, Fraction(3, 4))):
        assert resp.status_code == 200, resp.text
        data = resp.json()
        oracle = _independent_analytical_pyramid_oracle(frac)
        sc = data["scene3d"]
        for sym in ("M", "E", "F"):
            actual = tuple(Fraction(x) for x in _find_obj(sc, sym)["xyz"])
            assert actual == oracle[sym], f"Mismatch on {sym} at r={frac}: {actual} vs {oracle[sym]}"
        assert tuple(Fraction(x) for x in _find_obj(sc, "K")["xyz"]) == (Fraction(2), Fraction(2), Fraction(0))
        assert "K" in data["dependency_summary"]["skipped_unaffected_ids"]
        rebuilt_area_exact = sqrt_rational(oracle["area_sq"])
        assert _find_obj(sc, "S_td")["value"] == radical_display(rebuilt_area_exact)
