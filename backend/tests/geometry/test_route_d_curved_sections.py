# -*- coding: utf-8 -*-
"""Curved SECTIONS and the cone volume ratio on Route D /4 (run `hybrid-master-backend-replacement`, sixth continuation;
registry /24, planner /20, engine /16). 0 provider calls.

Hand oracles: `tools/curved_section_probe.py`, written before the implementation (RED: all refused at `9f4f61d2`). One
route: the section is the kernel's `intersect_plane_curved` of the plane z = d (or the polygon through the axis); the
small cone is built by the kernel from the apex and the radius it MEASURES on the section; a ratio is certified by
cross-multiplication, a remaining volume by subtraction; every answer equals an independent similarity certificate.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry.radical import from_json, parse_exact

_P = (Path(__file__).resolve().parents[3]
      / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools/curved_section_probe.py")
_spec = importlib.util.spec_from_file_location("curved_section_probe", _P)
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

NEGATIVE_CODES = {
    "n.cyl.d_above": "CURVED_PLANE_DOES_NOT_CUT", "n.cone.at_apex": "CURVED_PLANE_TANGENT",
    "n.wrong_distance": "UNGROUNDED_VALUE", "n.from_apex": "SOURCE_OBJECT_MISMATCH",
    "n.unread_tail": "SOURCE_OBJECT_MISMATCH", "n.not_parallel": "SOURCE_OBJECT_MISMATCH",
    "n.ratio_inverted": "SOURCE_OBJECT_MISMATCH", "n.volume_of_section": "INVALID_MATH_GOAL",
    "n.sphere_axial": "BRIDGE_UNSUPPORTED_CURVED", "n.section_kind_mismatch": "SOURCE_OBJECT_MISMATCH",
}


@pytest.mark.parametrize("cid,payload,oracle", S.CASES, ids=[c[0] for c in S.CASES])
def test_sections_and_cone_ratios_are_served_exactly(cid, payload, oracle):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(oracle)


@pytest.mark.parametrize("cid,payload,oracle", S.NEGATIVES, ids=[c[0] for c in S.NEGATIVES])
def test_section_negatives_are_refused_for_the_right_reason(cid, payload, oracle):
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED" and not r.answer_exact and r.scene3d is None
    assert r.code == NEGATIVE_CODES[cid], (r.code, r.reason)


def test_the_full_hybrid_path_shows_one_target_with_the_scorer_kind():
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor

    kinds = {"cyl.par.S": "measure.area", "cone.par.r": "measure.radius", "cone.ratio": "assign.volume_ratio",
             "cone.residual": "assign.residual_volume", "cone.ax.S": "measure.area"}
    for cid, p, oracle in (c for c in S.CASES if c[0] in kinds):
        out = run_hybrid_offline(p["problem_text"], ReplayExtractor({p["problem_text"]: p}),
                                 policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}))
        assert out.response["route_d"]["status"] == "SERVED", (cid, out.response["envelope"].get("reason_code"))
        targets = [(o["producer"], from_json(o["exact"])) for o in out.response["envelope"]["scene3d"]["objects"]
                   if o.get("type") == "quantity" and "target" in (o.get("display_group") or [])]
        assert targets == [(kinds[cid], parse_exact(oracle))], cid


def test_the_construction_trace_records_the_dependency_chain():
    (cid, p, _o) = next(c for c in S.CASES if c[0] == "cone.residual")
    r = run_typed_fact_next_v2_route(p)
    steps = [s["step"] for s in r.trace]
    order = ["construct_solid", "construct_section", "derive_dimension", "construct_subsolid", "compose_quantity",
             "certify_answer"]
    assert [x for x in steps if x in order] == order                 # solid → section → k → small cone → V − V' → ✓
    (sub,) = [s for s in r.trace if s["step"] == "construct_subsolid"]
    assert sub["parts"][0].startswith("td_")                          # the small cone REUSES the section circle


def test_a_tampered_section_certificate_is_never_served(monkeypatch):
    from app.simulation.geometry.radical import radical
    from app.simulation.geometry_functions import engine as E

    real = E._dung_phan_cong

    def wrong(*a, **k):
        hoi, cert, muc, kiem = real(*a, **k)
        return hoi, {c: radical(7, 1, 1) for c in cert}, muc, kiem
    monkeypatch.setattr(E, "_dung_phan_cong", wrong)
    (cid, p, _o) = S.CASES[0]
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED"
