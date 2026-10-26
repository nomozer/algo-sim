# -*- coding: utf-8 -*-
"""CACHE_VERSION 128 -> 129: the plane cutting a curved solid is a cutting object (run `sphere-sample-source-authority`).

The plane whose intersection with a cylinder/cone/sphere is the asked ellipse/circle now carries
`CONSTRUCT_CUTTING_OBJECT` (as for a polyhedral section) instead of `CONSTRUCT_AUXILIARY_GEOMETRY`, so Scene3D stops
hiding it once the intersection exists. `/api/analyze` returns a cache hit's `envelope_json` as is, so the genuine v128
row below — written by the clean v128 tree de49c592 through the same endpoint
(`runs/sphere-sample-source-authority/cache/cache_probe.py`) — would keep serving the hidden plane. The bump must make it
a MISS and the re-analysis may change nothing but those roles. The `cube` control must come back byte-identical.
0 model calls: the curved case replays recorded provider output offline; the control stubs both LLM stages.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.ai import pipeline as PL
from app.main import _cache_key, _cache_lookup, _policy_identity, app
from app.persistence.db import SessionLocal, SimulationCache, init_db
from tests.geometry import route_cases as W
from tests.test_photo_problem_live_runner import CA_P6, RNB

LEGACY = json.loads((Path(__file__).resolve().parents[2] / "docs/evaluation/geometry/runs"
                     / "sphere-sample-source-authority/cache/legacy-v128-rows.json").read_text(encoding="utf-8"))
CASES = {"p6_ellipse_section_of_cylinder": True, "cube": False}


def _canon(env: dict) -> dict:
    return {k: v for k, v in env.items() if k not in ("cached", "source")}


def _diff(a, b, path=()):
    if isinstance(a, dict) and isinstance(b, dict) and a.keys() == b.keys():
        return [d for k in a for d in _diff(a[k], b[k], path + (k,))]
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b) and not all(isinstance(x, str) for x in a + b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in _diff(x, y, path + (i,))]
    return [] if a == b else [(path, a, b)]


@pytest.fixture
def llm(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)

    def install(ca):
        if ca == "cube":
            text, contract = W.lap_phuong()
            spec = W.spec_cua(W.chuong_trinh(contract))

            async def analyze(*_a, **_k):
                return contract, None

            async def program(*_a, **_k):
                return spec, None

            monkeypatch.setattr(PL, "stage_semantic_analyze", analyze)
            monkeypatch.setattr(PL, "stage_semantic_program", program)
            return text
        monkeypatch.setattr(PL, "call_gemini", RNB.ProviderPhatLaiTheoThuTu({**RNB.doc_raw_theo_thu_tu(CA_P6)}))
        return RNB.doc_de_bai()[CA_P6]
    return install


def test_cache_version_is_current():
    assert main_module.CACHE_VERSION == "130"
    assert LEGACY["written_by_cache_version"] == "128"


@pytest.mark.parametrize("ca", sorted(CASES))
def test_legacy_v128_row_misses_and_only_the_cutting_plane_role_changes(ca, llm):
    text = llm(ca)
    legacy = LEGACY["rows"][ca]
    key = _cache_key(text)
    assert legacy["key"] == key and legacy["text"] == text and legacy["policy_version"] == "128"
    legacy_env = json.loads(legacy["envelope_json"])
    assert legacy_env["status"] == "ok"

    init_db()
    ident = _policy_identity(main_module.route_policy_snapshot())
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=text, simulation_id=legacy["simulation_id"],
                              envelope_json=legacy["envelope_json"], dsl_version=legacy["dsl_version"],
                              policy_version=legacy["policy_version"]))
        s.commit()
        assert _cache_lookup(s, key, ident) is None                     # the genuine v128 row is not a valid hit
    assert ident == "130"

    client = TestClient(app)
    fresh = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
    assert fresh.status_code == 200, fresh.text
    fresh = fresh.json()
    assert (fresh["status"], fresh.get("cached", False), fresh["source"]) == ("ok", False, "semantic_program")
    changes = _diff(_canon(legacy_env), _canon(fresh))
    if CASES[ca]:
        assert changes, "the curved case must change"
        for path, old, new in changes:                                  # nothing but the cutting plane's role moved
            if path[-1] == "explanation":                               # 129 -> 130: no internal repr in narration
                assert "Ellipse3(" in old and "Ellipse3(" not in new, path
                continue
            assert path[-1] == "formation_roles", path
            assert (old, new) == (["CONSTRUCT_AUXILIARY_GEOMETRY"], ["CONSTRUCT_CUTTING_OBJECT"]), path
        plane = [o for o in fresh["scene3d"]["objects"] if o["type"] == "plane3"]
        assert [o["formation_roles"] for o in plane] == [["CONSTRUCT_CUTTING_OBJECT"]]
    else:
        assert changes == []

    with SessionLocal() as s:
        rows = s.query(SimulationCache).filter_by(key=key).all()
        assert [r.policy_version for r in rows] == ["130"]               # overwritten in place, no duplicate
    hit = client.post("/api/analyze", json={"input": {"type": "text", "content": text}}).json()
    assert (hit["cached"], hit["source"]) == (True, "exact_cache")
    assert _canon(hit) == _canon(fresh)
