# -*- coding: utf-8 -*-
"""CACHE_VERSION 126 -> 127: Wave 1 adds `segment3.perpendicular_witness` to SERVED Path A scenes.

`/api/analyze` returns a cache hit's `envelope_json` as is, without rebuilding the scene. The legacy rows below are the
genuine rows that `main` f0560449 (v126) wrote for the same requests through the same endpoint
(`runs/segment-witness-cache-invalidation/cache/cache_probe.py`); they carry no segment witness, so a v126 hit would keep
serving a scene without the right-angle marker. The bump must make every such row a MISS, the re-analysis must store a
v127 row that keeps the witness through the JSON round trip, and nothing but the witness may change: answers,
provenance, formation steps and refusals stay byte-identical. The expected witnesses are written by hand from the
problem statements (altitude of a regular pyramid, a given SA ⟂ base, every lateral edge of a right prism / cuboid /
cube), never derived from the output. 0 model calls (both LLM stages are stubs).
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
from app.simulation.geometry.exact import Vec3
from app.simulation.geometry_functions.certificates import CERTIFICATE_SCHEMA, verify_perpendicular_witness
from app.simulation.semantic_program.quantity_annotations import _gan_chung_chi_vuong_goc_doan
from tests.geometry import route_cases as W
from tests.geometry import test_regular_square_pyramid as RSP

LEGACY = json.loads((Path(__file__).resolve().parents[2] / "docs/evaluation/geometry/runs"
                     / "segment-witness-cache-invalidation/cache/legacy-v126-rows.json").read_text(encoding="utf-8"))


def _rsp(ca):
    contract, prog = RSP.CA[ca]()
    return RSP.NHAN[ca]["text"], contract, prog


def _compiled(text, contract):
    return text, contract, W.chuong_trinh(contract)


_PYR, _PRISM = "formation_construct_height", "prism_lateral_altitude"
_HOP = {"A_prime": "A", "B_prime": "B", "C_prime": "C", "D_prime": "D"}  # ABCD.A'B'C'D': top vertex -> base foot

#: case -> (builder, rule, {top/apex endpoint: foot}). EXACTLY these segments carry a witness; every other segment3
#: (oblique lateral edges SB/SC/SD, base and top edges) must carry none.
SERVED = {
    "S1_side_height_volume": (lambda: _rsp("S1_side_height_volume"), _PYR, {"S": "O"}),
    "S6_renamed_vertices": (lambda: _rsp("S6_renamed_vertices"), _PYR, {"S": "O"}),
    "S7_named_centre": (lambda: _rsp("S7_named_centre"), _PYR, {"S": "O"}),
    # Not regular, A is not the base centre: SA ⊥ (ABC) / (ABCD) is GIVEN; the other lateral edges are oblique.
    "SA_given_right_triangle_pyramid": (lambda: _compiled(*W.chop_tam_giac()), _PYR, {"S": "A"}),
    "SA_given_rectangular_pyramid": (lambda: _compiled(*W.chop_chu_nhat()), _PYR, {"S": "A"}),
    # "lăng trụ đứng ABC.DEF": lateral edges AD, BE, CF.
    "right_triangular_prism": (lambda: _compiled(*W.lang_tru_tam_giac()), _PRISM, {"D": "A", "E": "B", "F": "C"}),
    "cuboid": (lambda: _compiled(*W.hop_chu_nhat()), _PRISM, _HOP),
    "cube": (lambda: _compiled(*W.lap_phuong()), _PRISM, _HOP),
    "square_prism": (lambda: _compiled(*W.lang_tru_day_vuong()), _PRISM, _HOP),
}


def _seg_witnesses(env: dict) -> list[dict]:
    return [o for o in env["scene3d"]["objects"] if o["type"] == "segment3" and "perpendicular_witness" in o]


def _strip(env: dict) -> str:
    env = json.loads(json.dumps(env))
    for k in ("cached", "source"):
        env.pop(k, None)
    for o in env["scene3d"]["objects"]:
        if o["type"] == "segment3":
            o.pop("perpendicular_witness", None)
    return json.dumps(env, ensure_ascii=False, sort_keys=True)


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


def test_cache_version_is_127():
    # 126 -> 127 (hybrid-architecture-wave1-exact-certificates-planner): served Path A scenes gain
    # segment3.perpendicular_witness; v126 rows were written without it and a hit returns them as is.
    # 127 -> 128 (visual-hybrid-final-corrections, display names): a v126 row still misses; the fresh row is v128.
    # 128 -> 129 (sphere-sample-source-authority, curved cutting plane role): a v126 row still misses; the fresh row is v129.
    # 129 -> 130 (scene3d-to-hybrid-v2-replacement, right-angle witness / assign-built geometry): a v126 row still misses; the fresh row is v130.
    assert main_module.CACHE_VERSION == "131"  # later bump: geometry-generalization-and-pedagogical-construction
    assert LEGACY["written_by_cache_version"] == "126"


@pytest.mark.parametrize("ca", sorted(SERVED))
def test_legacy_v126_row_misses_and_v127_row_keeps_the_witness(ca, stub_llm):
    make, rule, expected = SERVED[ca]
    text, contract, prog = make()
    legacy = LEGACY["rows"][ca]
    key = _cache_key(text)
    assert legacy["key"] == key and legacy["text"] == text and legacy["policy_version"] == "126"
    legacy_env = json.loads(legacy["envelope_json"])
    assert legacy_env["status"] == "ok" and _seg_witnesses(legacy_env) == []  # the stale scene: no segment marker

    init_db()
    ident = _policy_identity(main_module.route_policy_snapshot())
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text=text, simulation_id=legacy["simulation_id"],
                              envelope_json=legacy["envelope_json"], dsl_version=legacy["dsl_version"],
                              policy_version=legacy["policy_version"]))
        s.commit()
        assert _cache_lookup(s, key, ident) is None  # A: the genuine v126 row is not a valid hit
    assert ident == main_module.CACHE_VERSION  # default LLM_ONLY identity

    calls = stub_llm(contract, W.spec_cua(prog))
    client = TestClient(app)
    fresh = client.post("/api/analyze", json={"input": {"type": "text", "content": text}})
    assert fresh.status_code == 200, fresh.text
    fresh = fresh.json()
    assert (fresh["status"], fresh.get("cached", False), fresh["source"]) == ("ok", False, "semantic_program")
    assert calls == {"analyze": 1, "program": 1}

    # B: exactly the expected segments carry a certified witness (none on oblique, base or top edges), each verified
    # independently; provenance says only what was checked (formation role + exact Gram orthogonality).
    sc = fresh["scene3d"]
    segs = _seg_witnesses(fresh)
    got = {o["perpendicular_witness"]["from"]: o["perpendicular_witness"]["foot_id"] for o in segs}
    assert got == expected and len(segs) == len(expected)
    for o in segs:
        w = o["perpendicular_witness"]
        assert set(o["endpoint_ids"]) == {w["from"], w["foot_id"]}
        assert (w["certificate"], w["rule"], w["status"]) == (CERTIFICATE_SCHEMA, rule, "ENGINE_VERIFIED")
        ok, code = verify_perpendicular_witness(w, sc, sc.get("chart_metric"), segment_obj=o)
        assert ok, (o["id"], code)
    # C: nothing but the witness changed — answers, provenance, steps identical to the genuine v126 envelope.
    assert _strip(fresh) == _strip(legacy_env)

    with SessionLocal() as s:
        rows = s.query(SimulationCache).filter_by(key=key).all()
        assert [r.policy_version for r in rows] == [main_module.CACHE_VERSION]  # overwritten in place, no duplicate
        assert _seg_witnesses(json.loads(rows[0].envelope_json))

    hit = client.post("/api/analyze", json={"input": {"type": "text", "content": text}}).json()
    assert (hit["cached"], hit["source"]) == (True, "exact_cache")
    assert calls == {"analyze": 1, "program": 1}  # the hit made no stage call
    assert {k: v for k, v in hit.items() if k not in ("cached", "source")} == \
        {k: v for k, v in fresh.items() if k not in ("cached", "source")}

    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()


def test_refusal_stays_refused_and_uncached(stub_llm):
    text, contract, prog = W.LANG_TRU_XIEN_TEXT, *W.ca_lang_tru_xien()
    assert LEGACY["rows"]["REFUSED_oblique_prism"] is None  # v126 never cached it either
    init_db()
    calls = stub_llm(contract, W.spec_cua(prog))
    env = TestClient(app).post("/api/analyze", json={"input": {"type": "text", "content": text}}).json()
    assert env["status"] != "ok" and not env.get("scene3d") and calls["analyze"] == 1
    with SessionLocal() as s:
        assert s.query(SimulationCache).filter_by(key=_cache_key(text)).first() is None


def test_other_identities_never_share_the_default_row():
    init_db()
    key = _cache_key("Wave 1 cache identity probe: hình chóp S.ABCD")
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(SimulationCache(key=key, problem_text="x", simulation_id="x", envelope_json='{"status":"ok"}',
                              dsl_version=main_module.DSL_VERSION, policy_version="127:deadbeef"))
        s.commit()
        assert _cache_lookup(s, key, "127") is None          # another route mode's row is not a default hit
        assert _cache_lookup(s, key, "127:deadbeef") is not None
        s.query(SimulationCache).filter_by(key=key).delete()
        s.commit()


def test_hybrid_preview_never_reaches_the_product_cache():
    class _Preview:
        hybrid_preview_enabled = True

        def fingerprint(self):
            return None

    with pytest.raises(ValueError):
        _policy_identity(_Preview())


def _base_and_segment(top: Vec3, shape_class: str, role: str) -> tuple[list[dict], dict]:
    # Same fields as a real Path A scene: the solid's class is `shape_class` (formation), not any other key.
    mem = {"A": Vec3(0, 0, 0), "B": Vec3(4, 0, 0), "C": Vec3(0, 3, 0), "S": top}
    objs = [{"id": "day_ABC", "type": "polygon3", "vertex_ids": ["A", "B", "C"], "formation_roles": ["CONSTRUCT_BASE"]},
            {"id": "khoi", "type": "solid", "shape_class": shape_class},
            {"id": "SA", "type": "segment3", "endpoint_ids": ["S", "A"], "formation_roles": [role]}]
    return objs, mem


@pytest.mark.parametrize("shape_class, role, rule", [
    ("PYRAMID_LIKE", "CONSTRUCT_HEIGHT", "formation_construct_height"),
    ("PRISM_LIKE", "CONSTRUCT_LATERAL_BOUNDARY", "prism_lateral_altitude"),
])
def test_an_oblique_height_or_lateral_edge_never_gets_a_marker(shape_class, role, rule):
    objs, mem = _base_and_segment(Vec3(1, 0, 5), shape_class, role)  # role says "height"/"lateral", coordinates oblique
    _gan_chung_chi_vuong_goc_doan(objs, mem)
    assert "perpendicular_witness" not in objs[2]
    objs, mem = _base_and_segment(Vec3(0, 0, 5), shape_class, role)  # injected fault reversed: exactly perpendicular
    _gan_chung_chi_vuong_goc_doan(objs, mem)
    assert (objs[2]["perpendicular_witness"]["foot_id"], objs[2]["perpendicular_witness"]["rule"]) == ("A", rule)


def test_a_pyramid_lateral_edge_is_never_a_prism_edge():
    objs, mem = _base_and_segment(Vec3(0, 0, 5), "PYRAMID_LIKE", "CONSTRUCT_LATERAL_BOUNDARY")
    _gan_chung_chi_vuong_goc_doan(objs, mem)
    assert "perpendicular_witness" not in objs[2]  # only CONSTRUCT_HEIGHT qualifies on a pyramid
