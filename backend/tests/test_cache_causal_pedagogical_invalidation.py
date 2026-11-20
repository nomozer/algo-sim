# -*- coding: utf-8 -*-
"""CACHE_VERSION 137 → 138 (run `scene3d-causal-pedagogical-integrity`): a scene that flagged the ASKED intersection line
as an unused auxiliary must not come back from the cache.

The 137 code computed `is_unused_auxiliary` with no goals on Route D, so "Tìm giao tuyến …" served its own answer object
flagged unused (a consumer hiding unused auxiliaries hides the goal). The Route D key is computed before the parser
from version strings and the text only, so the fix does not change the key: every row written under `137:route-d`
must MISS. The adversarial row is the served envelope of the same text with that flag restored.
"""
from __future__ import annotations

import copy
import json

import pytest
from fastapi.testclient import TestClient

from app import main as M
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model
from app.main import SUPPORTED_VERSIONS
from app.persistence.db import SessionLocal, SimulationCache, init_db

TEXT = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
        "Tìm giao tuyến của hai mặt phẳng (SAB) và (SCD).")


def test_version_pair():
    assert M.CACHE_VERSION == "147" and M.ROUTE_D_CACHE_POLICY == "147:route-d"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from tests.route_client import sign_in
    with TestClient(M.app) as c:
        sign_in(c)
        yield c


def _flagged(body):
    return (body.get("envelope") or {}).get("scene3d", {}).get("unused_auxiliary_ids")


def _put(key, body, policy):
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=TEXT, simulation_id="generic.semantic_program",
                              envelope_json=json.dumps(body, ensure_ascii=False),
                              dsl_version=next(iter(SUPPORTED_VERSIONS)), policy_version=policy))
        s.commit()


def test_a_scene_flagging_the_asked_line_unused_is_recomputed(client):
    key = prepare_local_first_hybrid(TEXT, model=resolve_hybrid_gemini_model()).cache_key
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()
    fresh = client.post("/api/analyze", json={"input": {"type": "text", "content": TEXT}}).json()
    assert fresh["route_d"]["status"] == "SERVED" and _flagged(fresh) == []
    stale = copy.deepcopy(fresh)
    stale["envelope"]["scene3d"]["unused_auxiliary_ids"] = ["gt_g_il2"]
    try:
        _put(key, stale, "137:route-d")
        assert _flagged(client.post("/api/analyze", json={"input": {"type": "text", "content": TEXT}}).json()) == []
        _put(key, stale, M.ROUTE_D_CACHE_POLICY)            # control: under the current policy the row is trusted as written
        assert _flagged(client.post("/api/analyze", json={"input": {"type": "text", "content": TEXT}}).json()) == ["gt_g_il2"]
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
