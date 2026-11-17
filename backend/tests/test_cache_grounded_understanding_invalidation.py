# -*- coding: utf-8 -*-
"""CACHE_VERSION 138 → 139 (run `grounded-vietnamese-geometry-understanding`): the local parser and the Source Gate now
decide differently on the same text (unnamed base bound by clause order, lateral-edge angle of a regular pyramid,
undotted prism notation, derived isosceles legs, unnamed base area) and a premise value no quote reads is never
COMPLETE. The Route D key is computed before the parser from version strings and the text only, so a row written under
`138:route-d` for a text the new guard refuses would skip it: every such row must MISS.

The adversarial row is a served envelope stored under the old policy for a text whose "chu vi đáy bằng 8" no item reads.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app import main as M
from app.ai.hybrid_offline import prepare_local_first_hybrid, resolve_hybrid_gemini_model
from app.main import SUPPORTED_VERSIONS
from app.persistence.db import SessionLocal, SimulationCache, init_db

SERVED_TEXT = ("Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3 và diện tích đáy bằng 4. "
               "Tính thể tích khối chóp S.ABCD.")
NOW_REFUSED = ("Cho hình chóp tứ giác đều S.ABCD có cạnh bên bằng 3 và chu vi đáy bằng 8. "
               "Tính thể tích khối chóp S.ABCD.")


def test_version_pair():
    assert M.CACHE_VERSION == "145" and M.ROUTE_D_CACHE_POLICY == "145:route-d"


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
    r = c.post("/api/analyze", json={"input": {"type": "text", "content": text}})
    body = r.json()
    return r.status_code, ((body.get("route_d") or {}).get("status") if isinstance(body, dict) else None)


def _put(key, body, policy):
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=NOW_REFUSED, simulation_id="generic.semantic_program",
                              envelope_json=json.dumps(body, ensure_ascii=False),
                              dsl_version=next(iter(SUPPORTED_VERSIONS)), policy_version=policy))
        s.commit()


def test_a_scene_served_under_the_old_policy_is_not_replayed_once_the_parser_refuses_the_text(client):
    r = client.post("/api/analyze", json={"input": {"type": "text", "content": SERVED_TEXT}})
    old_served = r.json()
    assert r.status_code == 200 and old_served["route_d"]["status"] == "SERVED"
    key = prepare_local_first_hybrid(NOW_REFUSED, model=resolve_hybrid_gemini_model()).cache_key
    init_db()
    try:
        _put(key, old_served, "138:route-d")
        assert _post(client, NOW_REFUSED) != (200, "SERVED")                     # the parser decides, not the cache
        _put(key, old_served, M.ROUTE_D_CACHE_POLICY)                           # control: the current policy trusts it
        assert _post(client, NOW_REFUSED) == (200, "SERVED")
    finally:
        with SessionLocal() as s:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()
