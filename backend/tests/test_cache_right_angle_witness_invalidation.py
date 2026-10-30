# -*- coding: utf-8 -*-
"""CACHE_VERSION 129 -> 130: right-angle witnesses and assign-built geometry (run `scene3d-to-hybrid-v2-replacement`).

The default LLM_ONLY route's SERVED envelope changes content: a point → line/plane distance witness carries `u_to`
(the named point its in-plane side points to), a geometric object built by `assign` (cylinder, cone, circle/ellipse
of intersection) is a construction step whose narration no longer prints an internal `CurvedSolid(…)`/`Ellipse3(…)`
repr. `/api/analyze` returns a cache hit's `envelope_json` as is, so the genuine v129 rows below — written by the clean
v129 tree `11188e7a` through the same endpoint (`runs/scene3d-to-hybrid-v2-replacement/cache/cache_probe.py`) — would
keep serving the old scene. The bump must make them a MISS; the `cube` control must come back byte-identical.
0 model calls: the replay cases re-run recorded provider output offline; the control stubs both LLM stages.
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
from tests.test_photo_problem_live_runner import RNB

LEGACY = json.loads((Path(__file__).resolve().parents[2] / "docs/evaluation/geometry/runs"
                     / "scene3d-to-hybrid-v2-replacement/cache/legacy-v129-rows.json").read_text(encoding="utf-8"))
#: case → the only kind of path allowed to differ between the v129 row and the fresh v130 envelope.
CASES = {
    # + later bump 130 -> 131 (geometry-generalization-and-pedagogical-construction): its section edges now also carry an
    #   exactly verified "why" (`justification_text`, `details.justification`) — tested in test_section_edge_justification.py.
    "p1_chop_thiet_dien_khoang_cach": ("annotation", "witness", "marker", "justification", "justification_text"),
    "p4_hinh_tru_the_tich_va_xung_quanh": ("events", "formation"),
    "cube": None,
}


def _canon(env: dict) -> dict:
    return {k: v for k, v in env.items() if k not in ("cached", "source")}


def _diff(a, b, path=()):
    if isinstance(a, dict) and isinstance(b, dict):
        return [d for k in sorted(set(a) | set(b)) for d in _diff(a.get(k, "<absent>"), b.get(k, "<absent>"), path + (k,))]
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
        monkeypatch.setattr(PL, "call_gemini", RNB.ProviderPhatLaiTheoThuTu({**RNB.doc_raw_theo_thu_tu(ca)}))
        return RNB.doc_de_bai()[ca]
    return install


def test_cache_version_is_130():
    assert main_module.CACHE_VERSION == "131"  # later bump: geometry-generalization-and-pedagogical-construction
    assert LEGACY["written_by_cache_version"] == "129"


@pytest.mark.parametrize("ca", sorted(CASES))
def test_legacy_v129_row_misses_and_only_the_registered_paths_change(ca, llm):
    text = llm(ca)
    legacy = LEGACY["rows"][ca]
    key = _cache_key(text)
    assert legacy["key"] == key and legacy["text"] == text and legacy["policy_version"] == "129"
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
        assert _cache_lookup(s, key, ident) is None                     # the genuine v129 row is not a valid hit
    assert ident == "131"

    client = TestClient(app)
    fresh = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
    assert fresh.status_code == 200, fresh.text
    fresh = fresh.json()
    assert (fresh["status"], fresh.get("cached", False), fresh["source"]) == ("ok", False, "semantic_program")
    changes = _diff(_canon(legacy_env), _canon(fresh))
    if CASES[ca] is None:
        assert changes == []
    else:
        assert changes, f"{ca} must change"
        for path, _old, _new in changes:
            assert any(seg in CASES[ca] for seg in path), path
        assert "CurvedSolid(" not in json.dumps(fresh["scene3d"]["events"], ensure_ascii=False)

    with SessionLocal() as s:
        rows = s.query(SimulationCache).filter_by(key=key).all()
        assert [r.policy_version for r in rows] == ["131"]               # overwritten in place, no duplicate
    hit = client.post("/api/analyze", json={"input": {"type": "text", "content": text}}).json()
    assert (hit["cached"], hit["source"]) == (True, "exact_cache")
    assert _canon(hit) == _canon(fresh)
