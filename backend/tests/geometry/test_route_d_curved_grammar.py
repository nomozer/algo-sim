# -*- coding: utf-8 -*-
"""Base-centre wording, the general apex ratio k and sphere sections on Route D /4 (seventh continuation, registry /25).
0 provider calls.

Hand oracles: `tools/base_center_probe.py` (the wording of the Adapter /3 fixtures /4 refused, plus variants and
negatives) and `tools/apex_ratio_probe.py` (k = SM/SO from the apex, OM/OS from the base converted by the GATE, never by the
model; k³ volume law through the existing similarity certificate), `tools/sphere_section_probe.py` (r'² = R² − d²; d = R is
a tangent point, d > R misses). Each negative carries the exact code it must refuse with.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry.radical import parse_exact

_RUN = Path(__file__).resolve().parents[3] / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, _RUN / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


B, K, S = _load("base_center_probe"), _load("apex_ratio_probe"), _load("sphere_section_probe")
B_POS = [c for c in B.CASES if not c[3].startswith("REFUSE")]
B_NEG = [c for c in B.CASES if c[3].startswith("REFUSE")]


@pytest.mark.parametrize("cid,fig,ask,oracle", B_POS, ids=[c[0] for c in B_POS])
def test_base_centre_wordings_are_served_exactly(cid, fig, ask, oracle):
    r = run_typed_fact_next_v2_route(B.CP.payload(fig, *ask))
    assert r.status == "SERVED", (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(oracle)


@pytest.mark.parametrize("cid,fig,ask,oracle", B_NEG, ids=[c[0] for c in B_NEG])
def test_base_centre_negatives_are_refused_for_the_right_reason(cid, fig, ask, oracle):
    r = run_typed_fact_next_v2_route(B.CP.payload(fig, *ask))
    assert r.status == "REFUSED" and not r.answer_exact and r.code == oracle.split(":", 1)[1], (r.code, r.reason)


@pytest.mark.parametrize("cid,payload,oracle", K.CASES, ids=[c[0] for c in K.CASES])
def test_apex_ratio_sections_and_volumes_are_served_exactly(cid, payload, oracle):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(oracle)


@pytest.mark.parametrize("cid,payload,code", K.NEGATIVES, ids=[c[0] for c in K.NEGATIVES])
def test_apex_ratio_negatives_are_refused_for_the_right_reason(cid, payload, code):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED" and not r.answer_exact and r.code == code, (r.code, r.reason)


def test_a_named_point_on_the_axis_is_the_small_cones_base_centre():
    (cid, p, _o) = next(c for c in K.CASES if c[0] == "k.13.ratio")
    r = run_typed_fact_next_v2_route(p)
    assert r.points.get("M") == (0, 0, parse_exact("8/3"))           # SM/SO = 1/3 of h = 4 ⇒ z = 4 − 4/3 = 8/3
    assert any(s.get("object") == "M" and s.get("provenance") == "SOURCE_NAMED" for s in r.trace)


@pytest.mark.parametrize("cid,payload,oracle", S.CASES, ids=[c[0] for c in S.CASES])
def test_sphere_sections_are_served_exactly(cid, payload, oracle):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(oracle)


@pytest.mark.parametrize("cid,payload,code", S.NEGATIVES, ids=[c[0] for c in S.NEGATIVES])
def test_sphere_section_negatives_are_refused_for_the_right_reason(cid, payload, code):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED" and not r.answer_exact and r.code == code, (r.code, r.reason)


def test_the_sphere_section_is_the_kernels_circle_not_a_formula():
    """The served circle is executed by the kernel (`_giao_cau`): centre = projection of the sphere's centre, r'² = R² − d²."""
    (cid, p, _o) = next(c for c in S.CASES if c[0] == "s.d3.radius")
    r = run_typed_fact_next_v2_route(p)
    assert any(s.get("rule") == "sphere_plane_at_distance" and s.get("plane_distance") == "3" for s in r.trace)
    assert "intersect_plane_curved" in str(r.program["statements"])


def test_a_missing_centre_distance_is_a_contract_error():
    import copy
    (cid, p, _o) = S.CASES[0]
    p = copy.deepcopy(p)
    del p["derived_sections"][0]["distance_from_center"]
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "REFUSED" and not r.answer_exact
