# -*- coding: utf-8 -*-
"""CACHE_VERSION 145 → 146 (run `axo-hybrid-simulation-intent-generalization-grounded-slm-recovery`).

The Source Gate now accepts a simulation request naming the solid ("Hãy mô phỏng hình chóp S.ABCD."), the local parser
picks the request target by label/kind and covers every clause, and the SLM lowers 0 metric goals for a simulate-only
source. None of that is in the Route D key (`prepare_local_first_hybrid`: version strings + text; the parser version
string is unchanged), so a row written under `145:route-d` for such a text would be replayed instead of the new decision.

Adversarial row: a SERVED envelope carrying a marker object, stored under the old policy for a text the current code
serves. It must MISS (fresh scene, no marker, row rewritten under the current policy); the same row under the current
policy is a HIT (control: no revalidation on read — hence the bump).
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import main as M
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model
from app.persistence.db import SessionLocal, SimulationCache, init_db

TEXT = ("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
        "Hãy mô phỏng hình chóp S.ABCD.")
MARKER = "STALE_145_MARKER"


def test_version_pair():
    from tests.cache_policy import assert_cache_policy_at_least
    assert_cache_policy_at_least(146)


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from tests.route_client import sign_in
    with TestClient(M.app) as c:
        sign_in(c)
        yield c


def _put(key, policy):
    stale = {"schema_version": next(iter(M.SUPPORTED_VERSIONS)),
             "envelope": {"status": "ok", "simulation_id": "generic.semantic_program", "domain": "solid_geometry",
                          "visual_mode": "3d", "scene3d": {"objects": [{"id": MARKER, "type": "point3"}], "events": []}},
             "route_d": {"status": "SERVED", "planner": {"calls": []}}}
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=TEXT, simulation_id="generic.semantic_program",
                              envelope_json=json.dumps(stale, ensure_ascii=False),
                              dsl_version=next(iter(M.SUPPORTED_VERSIONS)), policy_version=policy))
        s.commit()


def _ids(c):
    r = c.post("/api/analyze", json={"input": {"type": "text", "content": TEXT}})
    assert r.status_code == 200
    body = r.json()
    assert body["route_d"]["status"] == "SERVED"
    return {o["id"] for o in body["envelope"]["scene3d"]["objects"]}


def test_a_simulate_only_row_written_under_145_misses_and_is_recomputed(client):
    key = prepare_local_first_hybrid(TEXT, model=resolve_hybrid_gemini_model()).cache_key
    init_db()
    try:
        _put(key, "145:route-d")
        ids = _ids(client)
        assert MARKER not in ids and {"S", "A", "B", "C", "D"} <= ids
        with SessionLocal() as s:
            assert s.query(SimulationCache).filter_by(key=key).first().policy_version == M.ROUTE_D_CACHE_POLICY
        _put(key, M.ROUTE_D_CACHE_POLICY)                       # control: the current policy trusts its own row
        assert MARKER in _ids(client)
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
