# -*- coding: utf-8 -*-
"""CACHE_VERSION 134 → 135 (run `certified-scale-cache-safety`): a scene served before a semantic guard tightened must not
come back from the cache.

The Route D cache key of `/api/analyze` is computed BEFORE the parser runs, from version strings and the text only
(`prepare_local_first_hybrid`). Run `compositional-semantics-simulation-goals` tightened the parser (comma-joined parts
must be read) and the adapter (a drawn angle bound to verified points) without changing any of those strings and kept
`CACHE_VERSION` 134 — so a row written by the earlier code for a text the guard now refuses would still be served,
skipping the guard. The bump retires every row written under `134:route-d`.

The adversarial row below is that case: an envelope that the earlier code served (modelled by the served scene of the
same problem without the extra clause), stored under the old policy, for a text the current parser refuses.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import main as M
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model
from app.main import SUPPORTED_VERSIONS
from app.persistence.db import SessionLocal, SimulationCache, init_db

B4 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a"
CLEAN = (f"{B4}, M là trung điểm của SA, mặt phẳng (P) đi qua M và song song với mặt đáy. "
         "Xác định thiết diện của hình chóp bởi (P).")
NOW_REFUSED = (f"{B4}, M là trung điểm của SA, N thuộc cạnh SB, mặt phẳng (P) đi qua M và song song với mặt đáy. "
               "Xác định thiết diện của hình chóp bởi (P).")


def test_version_pair():
    assert M.CACHE_VERSION == "137" and M.ROUTE_D_CACHE_POLICY == "137:route-d"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("HYBRID_ROUTE_MODE", "local-first")
    monkeypatch.setenv("ALLOW_LIVE_AI", "0")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    from tests.route_client import sign_in
    with TestClient(M.app) as c:
        sign_in(c)
        yield c


def _post(c, text):
    """(HTTP status, route_d status). A local refusal with live AI disabled is HTTP 503 LIVE_AI_DISABLED, never a scene."""
    r = c.post("/api/analyze", json={"input": {"type": "text", "content": text}})
    body = r.json()
    return r.status_code, ((body.get("route_d") or {}).get("status") if isinstance(body, dict) else None)


def test_a_scene_served_under_the_old_policy_is_not_replayed_once_the_guard_refuses_the_text(client):
    r = client.post("/api/analyze", json={"input": {"type": "text", "content": CLEAN}})
    old_served = r.json()
    assert r.status_code == 200 and old_served["route_d"]["status"] == "SERVED"
    key = prepare_local_first_hybrid(NOW_REFUSED, model=resolve_hybrid_gemini_model()).cache_key
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=NOW_REFUSED, simulation_id="generic.semantic_program",
                              envelope_json=json.dumps(old_served, ensure_ascii=False),
                              dsl_version=next(iter(SUPPORTED_VERSIONS)), policy_version="134:route-d"))
        s.commit()
    try:
        code, status = _post(client, NOW_REFUSED)
        assert (code, status) != (200, "SERVED")                                  # the guard decides, not the cache
        # control: the same row under the CURRENT policy is trusted as written (no revalidation on read) — which is
        # exactly why a tightened guard must come with a policy bump
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).update({"policy_version": M.ROUTE_D_CACHE_POLICY})
            s.commit()
        assert _post(client, NOW_REFUSED) == (200, "SERVED")
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
