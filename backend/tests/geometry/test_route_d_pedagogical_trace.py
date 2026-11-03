# -*- coding: utf-8 -*-
"""Pedagogical construction trace preconditions/postconditions export on Route D (/4)."""
from __future__ import annotations

import importlib.util
from pathlib import Path

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor

_P = (
    Path(__file__).resolve().parents[3]
    / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools/curved_section_probe.py"
)
_spec = importlib.util.spec_from_file_location("curved_section_probe_trace", _P)
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)


def _symbolic_section_payload() -> dict:
    text = (
        "Cho hình chóp tứ giác đều S.ABCD có đáy ABCD là hình vuông cạnh 6a, chiều cao bằng 4a. "
        "Lấy điểm M trên cạnh SA sao cho SM = 1/3 SA. "
        "Gọi (P) là mặt phẳng đi qua điểm M và song song với mặt phẳng (ABC). "
        "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P)."
    )
    return {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "a",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "pyramid",
                "notation": "S.ABCD",
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
            }
        ],
        "premises": [
            {
                "kind": "regular_pyramid",
                "args": {"apex": "S", "base": ["A", "B", "C", "D"]},
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
                "solid_id": "s1",
            },
            {
                "kind": "regular_polygon",
                "args": {"vertices": ["A", "B", "C", "D"], "side": "6a"},
                "quote": "có đáy ABCD là hình vuông cạnh 6a",
                "solid_id": "s1",
            },
            {
                "kind": "height",
                "args": {"value": "4a", "solid": "s1"},
                "quote": "chiều cao bằng 4a",
                "solid_id": "s1",
            },
            {
                "kind": "divide_segment",
                "args": {"point": "M", "segment": ["S", "A"], "ratio": "1/3"},
                "quote": "Lấy điểm M trên cạnh SA sao cho SM = 1/3 SA",
                "solid_id": "s1",
            },
        ],
        "derived_sections": [
            {
                "section_id": "sec",
                "plane_name": "P",
                "target_solid_id": "s1",
                "plane_kind": "through_point_parallel_plane",
                "through_point": "M",
                "parallel_plane": ["A", "B", "C"],
                "stated_intersections": [],
                "quote": "Gọi (P) là mặt phẳng đi qua điểm M và song song với mặt phẳng (ABC)",
            }
        ],
        "relations": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình chóp tứ giác đều S.ABCD",
            }
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "area",
                "solid_id": "s1",
                "target": {"section_id": "sec"},
                "quote": "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P)",
            }
        ],
    }


def test_polyhedral_route_d_trace_exports_verified_pre_and_postconditions() -> None:
    payload = _symbolic_section_payload()
    out = run_hybrid_offline(
        payload["problem_text"],
        ReplayExtractor({payload["problem_text"]: payload}),
        policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}),
    )
    assert out.response["route_d"]["status"] == "SERVED"
    trace = out.response["route_d"]["construction_trace"]
    assert trace
    for step in trace:
        assert isinstance(step.get("preconditions"), list) and step["preconditions"], step
        assert isinstance(step.get("postconditions"), list) and step["postconditions"], step

    unit_step = next(s for s in trace if s["step"] == "choose_unit")
    assert "homogeneous_symbolic_lengths" in unit_step["preconditions"]
    assert "unit_scale(a==1)" in unit_step["postconditions"]

    m_step = next(s for s in trace if s["step"] == "place_point" and s["object"] == "M")
    assert "placed(S)" in m_step["preconditions"] and "placed(A)" in m_step["preconditions"]
    assert "coords_exact(M)" in m_step["postconditions"]
    assert "kernel_point_matched" in m_step["postconditions"]

    plane_step = next(s for s in trace if s["step"] == "construct_plane")
    assert "not_solid_face" in plane_step["preconditions"]
    assert "relation_verified" in plane_step["postconditions"]

    sec_step = next(s for s in trace if s["step"] == "construct_section")
    assert "closed_section_verified" in sec_step["postconditions"]


def test_curved_route_d_trace_exports_verified_pre_and_postconditions() -> None:
    (_cid, payload, _oracle) = next(c for c in S.CASES if c[0] == "cone.residual")
    res = run_typed_fact_next_v2_route(payload)
    assert res.status == "SERVED"
    assert res.trace
    for step in res.trace:
        assert isinstance(step.get("preconditions"), list) and step["preconditions"], step
        assert isinstance(step.get("postconditions"), list) and step["postconditions"], step
    cert_step = next(s for s in res.trace if s["step"] == "certify_answer")
    assert any(p.startswith("closed_form_matched(") for p in cert_step["postconditions"])


def test_refused_trace_never_claims_post_execution_kernel_checks() -> None:
    text = (
        "Cho hình chóp tứ giác đều S.ABCD có đáy ABCD là hình vuông cạnh 6, AB = 5, "
        "chiều cao bằng 4. Tính thể tích khối chóp S.ABCD."
    )
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp tứ giác đều S.ABCD"}],
        "premises": [
            {"kind": "regular_pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "quote": "Cho hình chóp tứ giác đều S.ABCD", "solid_id": "s1"},
            {"kind": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": "6"}, "quote": "có đáy ABCD là hình vuông cạnh 6", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "5"}, "quote": "AB = 5", "solid_id": "s1"},
            {"kind": "height", "args": {"value": "4", "solid": "s1"}, "quote": "chiều cao bằng 4", "solid_id": "s1"},
        ],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp tứ giác đều S.ABCD"}],
        "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "solid_id": "s1", "target": {"solid_id": "s1"}, "quote": "Tính thể tích khối chóp S.ABCD"}],
    }
    res = run_typed_fact_next_v2_route(payload)
    assert res.status == "REFUSED" and res.code == "INCONSISTENT_FACTS"
    assert res.trace
    for step in res.trace:
        assert isinstance(step.get("preconditions"), list) and step["preconditions"], step
        assert isinstance(step.get("postconditions"), list) and step["postconditions"], step
        assert "kernel_point_matched" not in step["postconditions"]
        assert "closed_section_verified" not in step["postconditions"]


def test_post_engine_refusal_and_standalone_sphere_pose_trace_invariants() -> None:
    """Round 1 MINOR-1 & MINOR-2: post-engine REFUSED strips kernel_* claims, route_d carries construction_trace,
    and standalone sphere pose uses canonical_origin_center without axis(Oz)."""
    import json
    from app.ai.function_route import run_fact_route

    hold = {
        c["id"]: c
        for c in json.loads(
            (Path(__file__).resolve().parent / "fixtures/hybrid_holdout_cases.json").read_text(encoding="utf-8")
        )["cases"]
    }
    neg_case = hold["H13_NEGATED_RELATION_CONTRADICTS"]
    r_neg = run_fact_route(neg_case["text"], {"facts": neg_case["b_facts"]})
    assert r_neg.status == "REFUSED" and r_neg.code == "NEGATED_CLAUSE"
    assert r_neg.trace
    for step in r_neg.trace:
        assert "kernel_point_matched" not in step["postconditions"]
        assert "kernel_line_matched" not in step["postconditions"]
        assert "closed_section_verified" not in step["postconditions"]

    # Direct run_typed_fact_next_v2_route populates route_d["construction_trace"] on SERVED:
    r_served = run_typed_fact_next_v2_route(_symbolic_section_payload())
    assert r_served.status == "SERVED"
    assert r_served.route_d["construction_trace"] == r_served.trace

    # Standalone sphere pose does not claim axis(Oz):
    sph_text = "Cho mặt cầu (S) tâm O bán kính R = 3. Tính thể tích khối cầu (S)."
    sph_payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": sph_text,
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "sphere",
                "notation": "(S)",
                "center": "O",
                "radius": "3",
                "quote": "Cho mặt cầu (S) tâm O bán kính R = 3.",
            }
        ],
        "premises": [],
        "relations": [],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho mặt cầu (S) tâm O bán kính R = 3."}
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "volume",
                "solid_id": "s1",
                "target": {"solid_id": "s1"},
                "quote": "Tính thể tích khối cầu (S).",
            }
        ],
    }
    r_sph = run_typed_fact_next_v2_route(sph_payload)
    assert r_sph.status == "SERVED"
    pose_step = next(s for s in r_sph.trace if s["step"] == "choose_pose")
    assert pose_step["rule"] == "canonical_origin_center"
    assert "axis(Oz)" not in pose_step["postconditions"]
    assert "center_at_origin" in pose_step["postconditions"]
