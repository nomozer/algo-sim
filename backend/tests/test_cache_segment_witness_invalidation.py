# -*- coding: utf-8 -*-
"""Cache invalidation across version bumps + exact perpendicular-witness certification on Scene3D.

`/api/analyze` serves Hybrid `/4` responses keyed by `(exact_source, "132:route-d")`.
Legacy `LLM_ONLY` cache rows (`policy_version == "126"`, `"130"`, `"131"`, etc.) never hit under `CACHE_VERSION = "132"`,
and shared `quantity_annotations._gan_chung_chi_vuong_goc_doan` + Route D `/4` continue to emit verified
`segment3.perpendicular_witness` metadata on certified altitudes.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import main as main_module
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.main import _cache_key, _cache_lookup, _policy_identity
from app.persistence.db import SessionLocal, SimulationCache, init_db
from app.simulation.geometry.exact import Vec3
from app.simulation.geometry_functions.certificates import CERTIFICATE_SCHEMA, verify_perpendicular_witness
from app.simulation.semantic_program.quantity_annotations import _gan_chung_chi_vuong_goc_doan

LEGACY = json.loads(
    (
        Path(__file__).resolve().parents[2]
        / "docs/evaluation/geometry/runs/segment-witness-cache-invalidation/cache/legacy-v126-rows.json"
    ).read_text(encoding="utf-8")
)


def test_cache_version_bump_covers_hybrid_cutover():
    assert main_module.CACHE_VERSION == "132"
    assert main_module.ROUTE_D_CACHE_POLICY == "132:route-d"
    assert _policy_identity(main_module.route_policy_snapshot()) == main_module.ROUTE_D_CACHE_POLICY
    assert LEGACY["written_by_cache_version"] == "126"


@pytest.mark.parametrize("ca", sorted(k for k, v in LEGACY["rows"].items() if v is not None))
def test_legacy_v126_row_misses_under_hybrid_cutover_cache_policy(ca):
    legacy = LEGACY["rows"][ca]
    key = legacy["key"]
    init_db()
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(
            SimulationCache(
                key=key,
                problem_text=legacy["text"],
                simulation_id=legacy["simulation_id"],
                envelope_json=legacy["envelope_json"],
                dsl_version=legacy["dsl_version"],
                policy_version=legacy["policy_version"],
            )
        )
        s.commit()
        try:
            assert _cache_lookup(s, key, main_module.ROUTE_D_CACHE_POLICY) is None
            assert _cache_lookup(s, key, main_module.CACHE_VERSION) is None
        finally:
            s.query(SimulationCache).filter_by(key=key).delete()
            s.commit()


def test_hybrid_route_d_emits_verified_segment_perpendicular_witnesses():
    text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3 và AA' = 4. "
        "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."
    )
    solid_quote = "Cho hình hộp chữ nhật ABCD.A'B'C'D'"
    res = run_typed_fact_next_v2_route(
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": text,
            "length_unit": "1",
            "solids": [{"solid_id": "s1", "solid_type": "prism", "notation": "ABCD.A'B'C'D'", "quote": solid_quote}],
            "premises": [
                {"kind": "right_prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"]}, "quote": solid_quote, "solid_id": "s1"},
                {"kind": "rectangle", "args": {"vertices": list("ABCD")}, "quote": solid_quote, "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "AB = 2", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": "3"}, "quote": "AD = 3", "solid_id": "s1"},
                {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "4"}, "quote": "AA' = 4", "solid_id": "s1"},
            ],
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": solid_quote}],
            "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "solid_id": "s1", "target": {"solid_id": "s1"}, "quote": "Tính thể tích khối hộp chữ nhật ABCD.A'B'C'D'."}],
        }
    )
    assert res.status == "SERVED" and res.scene3d is not None
    segs = [o for o in res.scene3d["objects"] if o["type"] == "segment3" and "perpendicular_witness" in o]
    assert len(segs) >= 1
    for o in segs:
        w = o["perpendicular_witness"]
        assert w["certificate"] == CERTIFICATE_SCHEMA and w["status"] == "ENGINE_VERIFIED"
        ok, code = verify_perpendicular_witness(w, res.scene3d, res.scene3d.get("chart_metric"), segment_obj=o)
        assert ok, (o["id"], code)


def test_other_identities_never_share_the_default_row():
    init_db()
    key = _cache_key("Wave 1 cache identity probe: hình chóp S.ABCD")
    with SessionLocal() as s:
        s.query(SimulationCache).filter_by(key=key).delete()
        s.add(
            SimulationCache(
                key=key,
                problem_text="x",
                simulation_id="x",
                envelope_json='{"status":"ok"}',
                dsl_version=main_module.DSL_VERSION,
                policy_version="127:deadbeef",
            )
        )
        s.commit()
        try:
            assert _cache_lookup(s, key, main_module.ROUTE_D_CACHE_POLICY) is None
            assert _cache_lookup(s, key, "127:deadbeef") is not None
        finally:
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
    mem = {"A": Vec3(0, 0, 0), "B": Vec3(4, 0, 0), "C": Vec3(0, 3, 0), "S": top}
    objs = [
        {"id": "day_ABC", "type": "polygon3", "vertex_ids": ["A", "B", "C"], "formation_roles": ["CONSTRUCT_BASE"]},
        {"id": "khoi", "type": "solid", "shape_class": shape_class},
        {"id": "SA", "type": "segment3", "endpoint_ids": ["S", "A"], "formation_roles": [role]},
    ]
    return objs, mem


@pytest.mark.parametrize(
    "shape_class, role, rule",
    [
        ("PYRAMID_LIKE", "CONSTRUCT_HEIGHT", "formation_construct_height"),
        ("PRISM_LIKE", "CONSTRUCT_LATERAL_BOUNDARY", "prism_lateral_altitude"),
    ],
)
def test_an_oblique_height_or_lateral_edge_never_gets_a_marker(shape_class, role, rule):
    objs, mem = _base_and_segment(Vec3(1, 0, 5), shape_class, role)
    _gan_chung_chi_vuong_goc_doan(objs, mem)
    assert "perpendicular_witness" not in objs[2]
    objs, mem = _base_and_segment(Vec3(0, 0, 5), shape_class, role)
    _gan_chung_chi_vuong_goc_doan(objs, mem)
    assert (objs[2]["perpendicular_witness"]["foot_id"], objs[2]["perpendicular_witness"]["rule"]) == ("A", rule)


def test_a_pyramid_lateral_edge_is_never_a_prism_edge():
    objs, mem = _base_and_segment(Vec3(0, 0, 5), "PYRAMID_LIKE", "CONSTRUCT_LATERAL_BOUNDARY")
    _gan_chung_chi_vuong_goc_doan(objs, mem)
    assert "perpendicular_witness" not in objs[2]
