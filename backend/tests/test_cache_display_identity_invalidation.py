# -*- coding: utf-8 -*-
"""CACHE_VERSION 127 -> 128: backend display identity on the default LLM_ONLY route (run `visual-hybrid-final-corrections`).

A plane the problem names "(P)" (declared by exactly one plane) is now shown as "(P)", not by the name composed from
its points. `/api/analyze` returns a cache hit's `envelope_json` as is, so the genuine v127 row below — written by the
clean v127 tree b99afd32 through the same endpoint (`runs/visual-hybrid-final-corrections/cache/cache_probe.py`) —
would keep serving "(AB′D′)". The bump must make it a MISS, and the re-analysis may change nothing but that name. The
`cube` control must come back byte-identical. 0 model calls (both LLM stages are stubs).
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
from tests.geometry import test_cuboid_cube_production_route as CC

LEGACY = json.loads((Path(__file__).resolve().parents[2] / "docs/evaluation/geometry/runs"
                     / "visual-hybrid-final-corrections/cache/legacy-v127-rows.json").read_text(encoding="utf-8"))


def _cube():
    text, payload = CC._cube_p01_payload()
    contract = W.hop_dong(text, payload)
    return text, contract, W.chuong_trinh(contract)


def _cube_named_plane_p():
    text, payload = CC._cube_p01_payload()
    text = f"{text} Mặt phẳng (P) đi qua ba điểm A, B′, D′."
    contract = W.hop_dong(text, payload)
    prog = W.chuong_trinh(contract)
    prog["memory_declarations"].append({"name": "P", "type": "plane3"})
    prog["statements"].append({"kind": "construct_plane", "target_var": "P", "label": "(P)",
                               "through": ["A", "B_prime", "D_prime"]})
    return text, contract, prog


#: case -> (builder, old name, new name). `None` = control: the envelope must not change at all.
CASES = {"cube_named_plane_P": (_cube_named_plane_p, "(AB′D′)", "(P)"), "cube": (_cube, None, None)}


def _canon(env: dict) -> str:
    return json.dumps({k: v for k, v in env.items() if k not in ("cached", "source")}, ensure_ascii=False, sort_keys=True)


@pytest.fixture
def stub_llm(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "khoa-gia")
    monkeypatch.delenv("GEOMETRY_COMPILER_MODE", raising=False)
    calls = {"analyze": 0, "program": 0}

    def install(contract, sp):
        async def analyze(*_a, **_k):
            calls["analyze"] += 1
            return contract, None

        async def program(*_a, **_k):
            calls["program"] += 1
            return sp, None

        monkeypatch.setattr(PL, "stage_semantic_analyze", analyze)
        monkeypatch.setattr(PL, "stage_semantic_program", program)
        return calls

    return install


def test_cache_version_is_128():
    assert main_module.CACHE_VERSION == "128"
    assert LEGACY["written_by_cache_version"] == "127"


@pytest.mark.parametrize("ca", sorted(CASES))
def test_legacy_v127_row_misses_and_only_the_name_changes(ca, stub_llm):
    make, cu, moi = CASES[ca]
    text, contract, prog = make()
    legacy = LEGACY["rows"][ca]
    key = _cache_key(text)
    assert legacy["key"] == key and legacy["text"] == text and legacy["policy_version"] == "127"
    legacy_env = json.loads(legacy["envelope_json"])
    assert legacy_env["status"] == "ok"
    if cu:
        mat = {o["id"]: o for o in legacy_env["scene3d"]["objects"]}["P"]
        assert mat["notation"] == cu                                    # the stale name a v127 hit would serve

    init_db()
    ident = _policy_identity(main_module.route_policy_snapshot())
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=text, simulation_id=legacy["simulation_id"],
                              envelope_json=legacy["envelope_json"], dsl_version=legacy["dsl_version"],
                              policy_version=legacy["policy_version"]))
        s.commit()
        assert _cache_lookup(s, key, ident) is None                     # the genuine v127 row is not a valid hit
    assert ident == "128"

    calls = stub_llm(contract, W.spec_cua(prog))
    client = TestClient(app)
    fresh = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
    assert fresh.status_code == 200, fresh.text
    fresh = fresh.json()
    assert (fresh["status"], fresh.get("cached", False), fresh["source"]) == ("ok", False, "semantic_program")
    assert calls == {"analyze": 1, "program": 1}
    if cu:
        assert {o["id"]: o for o in fresh["scene3d"]["objects"]}["P"]["notation"] == moi
        # Nothing but the plane's name moved: ids, coordinates, answers, provenance, steps are the v127 bytes.
        assert _canon(fresh) == _canon(legacy_env).replace(cu, moi)
    else:
        assert _canon(fresh) == _canon(legacy_env)

    with SessionLocal() as s:
        rows = s.query(SimulationCache).filter_by(key=key).all()
        assert [r.policy_version for r in rows] == ["128"]               # overwritten in place, no duplicate
    hit = client.post("/api/analyze", json={"input": {"type": "text", "content": text}}).json()
    assert (hit["cached"], hit["source"]) == (True, "exact_cache")
    assert calls == {"analyze": 1, "program": 1}
    assert _canon(hit) == _canon(fresh)

    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()
