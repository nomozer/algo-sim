# -*- coding: utf-8 -*-
"""CACHE_VERSION 136 → 137 (run `proof-soundness-generalized-angle-invariance`): a scene served under
`target-invariance-certificate/1` must not come back from the cache.

/1 stated the plane angle as a bare vertex-first triple, was not bound to the asked goal, fixed the triangle's shape at
any vertex and never bound its value to the kernel. /2 adds a structured witness, goal binding, value binding (engine
TI-6) and proof ↔ scene binding (adapter). The Route D key is computed BEFORE the parser from version strings and the
text only, so none of that changes the key: every row written under `136:route-d` must MISS.

The adversarial row is the served envelope of the same text carrying a /1 certificate (what the 136 code wrote).
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

TEXT = ("Cho hình chóp S.ABC có đáy là tam giác vuông tại B, SA vuông góc với đáy và SA = AB. "
        "Tính góc giữa hai mặt phẳng (SBC) và (ABC).")


def test_version_pair():
    assert M.CACHE_VERSION == "142" and M.ROUTE_D_CACHE_POLICY == "142:route-d"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from tests.route_client import sign_in
    with TestClient(M.app) as c:
        sign_in(c)
        yield c


def _schema(body):
    return body["route_d"]["scene_configuration"]["invariance_certificate"]["schema_version"]


def test_a_scene_served_under_the_v1_certificate_is_recomputed(client):
    key = prepare_local_first_hybrid(TEXT, model=resolve_hybrid_gemini_model()).cache_key
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()
    fresh = client.post("/api/analyze", json={"input": {"type": "text", "content": TEXT}}).json()
    assert fresh["route_d"]["status"] == "SERVED" and _schema(fresh) == "target-invariance-certificate/2"
    stale = copy.deepcopy(fresh)
    stale["route_d"]["scene_configuration"]["invariance_certificate"]["schema_version"] = "target-invariance-certificate/1"
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=TEXT, simulation_id="generic.semantic_program",
                              envelope_json=json.dumps(stale, ensure_ascii=False),
                              dsl_version=next(iter(SUPPORTED_VERSIONS)), policy_version="136:route-d"))
        s.commit()
    try:
        again = client.post("/api/analyze", json={"input": {"type": "text", "content": TEXT}}).json()
        assert _schema(again) == "target-invariance-certificate/2"            # recomputed, the 136 row missed
        # control: the same stale row under the CURRENT policy is replayed as written (no revalidation on read)
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.add(SimulationCache(key=key, problem_text=TEXT, simulation_id="generic.semantic_program",
                                  envelope_json=json.dumps(stale, ensure_ascii=False),
                                  dsl_version=next(iter(SUPPORTED_VERSIONS)), policy_version=M.ROUTE_D_CACHE_POLICY))
            s.commit()
        replay = client.post("/api/analyze", json={"input": {"type": "text", "content": TEXT}}).json()
        assert _schema(replay) == "target-invariance-certificate/1"
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
