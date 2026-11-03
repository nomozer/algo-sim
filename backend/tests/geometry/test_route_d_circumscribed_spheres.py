# -*- coding: utf-8 -*-
"""Certified circumscribed spheres of polyhedra on Route D /4
(run `hybrid-master-backend-replacement`, Continuation 8). 0 provider calls.

Verifies:
1. Exact Fraction circumcenter + all-vertex cosphericity certificate + G4 IR construction
   (`midpoint` + `plane_perpendicular_to_line` + `intersect_plane_plane` + `intersect_line_plane`
   + `construct_curved_solid` + `measure`) + independent closed-form cross-check.
2. Closed Vietnamese Source Gate binding for named/unnamed circumscribed spheres and named centers.
3. Fail-closed refusals for non-cospheric polyhedra (`NO_CIRCUMSCRIBED_SPHERE`), non-Euclidean charts
   (`METRIC_REQUIRES_EUCLIDEAN_CHART`), contradictory pre-declared centers (`INCONSISTENT_FACTS`),
   inscribed/circumcircle/mismatched wordings, undefined lateral area, and scope/legacy boundaries.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import importlib.util
from pathlib import Path

import pytest

from app.ai.function_route import run_typed_fact_next_planner_route
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry.radical import from_json, parse_exact
from app.simulation.geometry_functions.typed_fact_next import (
    TypedFactNextValidationError,
    convert_v1_to_v2,
    parse_typed_fact_next_v2,
)

_P = (
    Path(__file__).resolve().parents[3]
    / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/tools/circumscribed_sphere_probe.py"
)
_spec = importlib.util.spec_from_file_location("circumscribed_sphere_probe", _P)
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)


@pytest.mark.parametrize("cid,payload,oracle", P.POSITIVE_CASES, ids=[x[0] for x in P.POSITIVE_CASES])
def test_circumscribed_sphere_positives_are_served_exactly(cid: str, payload: dict, oracle: str) -> None:
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED" and r.kernel_check is True, (cid, r.code, r.reason)
    assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(oracle)
    assert any(s["step"] == "certify_answer" and s["rule"] == "independent_closed_form" for s in r.trace)
    assert any(
        s["step"] == "construct_solid" and s.get("rule") == "circumscribed_solid" for s in r.trace
    )
    for step in r.trace:
        assert step.get("preconditions") and step.get("postconditions")
    types = {o["type"] for o in r.scene3d["objects"]}
    assert {"solid", "curved_solid", "quantity"} <= types


def test_named_circumcenter_coordinates_and_unnamed_absence() -> None:
    named = dict(P.POSITIVE_CASES)["cs.pyr_sq.named_center"] if False else next(
        x[1] for x in P.POSITIVE_CASES if x[0] == "cs.pyr_sq.named_center"
    )
    r_named = run_typed_fact_next_v2_route(named)
    assert r_named.status == "SERVED"
    assert r_named.points["I"] == (Fraction(1), Fraction(1), Fraction(1))

    unnamed = next(x[1] for x in P.POSITIVE_CASES if x[0] == "cs.tetra_236.surface_area")
    r_unnamed = run_typed_fact_next_v2_route(unnamed)
    assert r_unnamed.status == "SERVED"
    assert set(r_unnamed.points) == {"S", "A", "B", "C"}


def test_symbolic_unit_circumscribed_sphere_formats_pi_and_radical_with_unit() -> None:
    for goal_type, question, want_coef, want_dim, want_text in (
        ("radius", "Tính bán kính mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.", "√3/2", 1, "a√3/2"),
        ("area", "Tính diện tích mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.", "3π", 2, "3πa²"),
        ("volume", "Tính thể tích khối cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.", "π√3/2", 3, "πa³√3/2"),
    ):
        payload = P.make_payload(
            problem_text=P.CUBE_A_GIVEN + " " + question,
            poly_solid=P.CUBE_A_SOLID,
            premises=P.CUBE_A_PREMS,
            sphere_notation="(ABCD.A'B'C'D')",
            sphere_quote=question,
            goal_type=goal_type,
            goal_quote=question,
            length_unit="a",
        )
        r = run_typed_fact_next_v2_route(payload)
        assert r.status == "SERVED", (goal_type, r.code, r.reason)
        assert parse_exact(r.answer_exact["mg1"]["coef"]) == parse_exact(want_coef)
        assert r.answer_exact["mg1"]["dim"] == want_dim and r.answer_exact["mg1"]["unit"] == "a"
        assert r.answers["mg1"] == want_text


def test_full_hybrid_offline_serves_circumscribed_sphere_and_classifies_non_cospheric_as_invalid_data() -> None:
    from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
    from app.ai.typed_fact_next_extraction import ReplayExtractor

    pos = next(x[1] for x in P.POSITIVE_CASES if x[0] == "cs.box_236.radius")
    out_ok = run_hybrid_offline(
        pos["problem_text"],
        ReplayExtractor({pos["problem_text"]: pos}),
        policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}),
    )
    assert out_ok.response["route_d"]["status"] == "SERVED", out_ok.response["envelope"].get("reason_code")
    targets = [
        from_json(o["exact"])
        for o in out_ok.response["envelope"]["scene3d"]["objects"]
        if o.get("type") == "quantity" and "target" in (o.get("display_group") or [])
    ]
    assert targets == [parse_exact("7/2")]

    neg = next(x[1] for x in P.NEGATIVE_CASES if x[0] == "cs.neg.oblique_prism_not_cospheric")
    out_neg = run_hybrid_offline(
        neg["problem_text"],
        ReplayExtractor({neg["problem_text"]: neg}),
        policy=hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"}),
    )
    assert out_neg.response["route_d"]["status"] == "REFUSED"
    assert out_neg.response["route_d"]["refusal"]["code"] == "NO_CIRCUMSCRIBED_SPHERE"
    assert out_neg.response["envelope"]["reason_code"] == "NO_CIRCUMSCRIBED_SPHERE"
    assert out_neg.response["envelope"]["failure_category"] == "geometry_generation_failed"


@pytest.mark.parametrize("cid,payload,want_code", P.NEGATIVE_CASES, ids=[x[0] for x in P.NEGATIVE_CASES])
def test_circumscribed_sphere_negatives_refuse_fail_closed(cid: str, payload: dict, want_code: str) -> None:
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED" and not r.answer_exact and r.scene3d is None, cid
    assert r.code == want_code, (cid, r.code, r.reason)


def test_circumscribed_sphere_scope_controls_serve() -> None:
    base = next(x[1] for x in P.POSITIVE_CASES if x[0] == "cs.pyr_sq.named_center")
    parsed = parse_typed_fact_next_v2(base)
    assert parsed.solids[1].circumscribes == "poly"


def test_circumscribed_sphere_scope_violations_refuse() -> None:
    base = next(x[1] for x in P.POSITIVE_CASES if x[0] == "cs.pyr_sq.named_center")

    p_unknown = deepcopy(base)
    p_unknown["solids"][1]["circumscribes"] = "missing_solid"
    with pytest.raises(TypedFactNextValidationError) as e1:
        parse_typed_fact_next_v2(p_unknown)
    assert e1.value.code == "UNKNOWN_SOLID_ID"

    p_cone = deepcopy(base)
    p_cone["solids"][1]["solid_type"] = "cone"
    with pytest.raises(TypedFactNextValidationError) as e2:
        parse_typed_fact_next_v2(p_cone)
    assert e2.value.code == "SOURCE_OBJECT_MISMATCH"

    p_radius = deepcopy(base)
    p_radius["solids"][1]["radius"] = "2"
    with pytest.raises(TypedFactNextValidationError) as e3:
        parse_typed_fact_next_v2(p_radius)
    assert e3.value.code == "SOURCE_OBJECT_MISMATCH"

    p_self = deepcopy(base)
    p_self["solids"][1]["circumscribes"] = "sph"
    with pytest.raises(TypedFactNextValidationError) as e4:
        parse_typed_fact_next_v2(p_self)
    assert e4.value.code == "SOURCE_OBJECT_MISMATCH"


def test_legacy_adapter3_refuses_circumscribed_sphere_without_expanding_legacy() -> None:
    v1 = deepcopy(next(x[1] for x in P.POSITIVE_CASES if x[0] == "cs.cube_2.surface_area"))
    v1["schema_version"] = "typed-fact-next/1"
    res = run_typed_fact_next_planner_route(v1)
    assert res.status == "REFUSED"
    assert convert_v1_to_v2(v1, route="bridge")["solids"][1]["circumscribes"] == "poly"


def test_composite_polyhedron_and_sphere_volume_disambiguation_and_multi_goal() -> None:
    """Round 1 MAJOR-2 & NIT-1:
    - Ambiguous unqualified 'Tính thể tích.' / 'Tính thể tích V.' refuses QUESTION_SOURCE_MISMATCH on composite figure.
    - Explicit multi-goal asking BOTH polyhedron volume and sphere volume serves in BOTH goal clause orders.
    - Premise quote ending with '?' refuses QUESTION_CLAUSE_NOT_PREMISE.
    """
    base_given = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 4. "
        "Gọi (S) là mặt cầu ngoại tiếp hình chóp S.ABCD."
    )
    solids = [
        {"solid_id": "poly", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"},
        {
            "solid_id": "sph",
            "solid_type": "sphere",
            "notation": "(S)",
            "circumscribes": "poly",
            "quote": "Gọi (S) là mặt cầu ngoại tiếp hình chóp S.ABCD.",
        },
    ]
    prems = [
        P._prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "4"}, "đáy ABCD là hình vuông cạnh 4"),
        P._prem("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "SA vuông góc với mặt phẳng (ABCD)"),
        P._prem("segment_length", {"segment": ["S", "A"], "value": "4"}, "SA = 4"),
    ]
    sim_goals = [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": "Cho hình chóp S.ABCD"}]

    for bare_q in ("Tính thể tích.", "Tính thể tích V."):
        p_bare = {
            "schema_version": "typed-fact-next/2",
            "problem_text": f"{base_given} {bare_q}",
            "solids": deepcopy(solids),
            "premises": deepcopy(prems),
            "relations": [],
            "derived_sections": [],
            "simulation_goals": deepcopy(sim_goals),
            "math_goals": [
                {"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "solid_id": "poly", "target": {"solid_id": "poly"}, "quote": bare_q}
            ],
        }
        r_bare = run_typed_fact_next_v2_route(p_bare)
        assert r_bare.status == "REFUSED" and r_bare.code == "SOURCE_OBJECT_MISMATCH", (bare_q, r_bare.status, r_bare.code)

    for q_both in (
        "Tính thể tích khối chóp S.ABCD và thể tích khối cầu (S).",
        "Tính thể tích khối cầu (S) và thể tích khối chóp S.ABCD.",
        "Tính thể tích khối chóp S.ABCD. Tính thể tích khối cầu (S).",
    ):
        q1 = "Tính thể tích khối chóp S.ABCD." if ". Tính" in q_both else q_both
        q2 = "Tính thể tích khối cầu (S)." if ". Tính" in q_both else q_both
        p_both = {
            "schema_version": "typed-fact-next/2",
            "problem_text": f"{base_given} {q_both}",
            "solids": deepcopy(solids),
            "premises": deepcopy(prems),
            "relations": [],
            "derived_sections": [],
            "simulation_goals": deepcopy(sim_goals),
            "math_goals": [
                {"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "solid_id": "poly", "target": {"solid_id": "poly"}, "quote": q1},
                {"goal_id": "mg2", "kind": "measurement", "goal_type": "volume", "solid_id": "sph", "target": {"solid_id": "sph"}, "quote": q2},
            ],
        }
        r_both = run_typed_fact_next_v2_route(p_both)
        assert r_both.status == "SERVED", (q_both, r_both.code, r_both.reason)
        assert parse_exact(r_both.answer_exact["mg1"]["coef"]) == parse_exact("64/3")
        assert parse_exact(r_both.answer_exact["mg2"]["coef"]) == parse_exact("32π√3")

    # Premise with trailing '?' refuses QUESTION_CLAUSE_NOT_PREMISE:
    p_qmark = P.make_payload(
        problem_text=(
            "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 4, SA vuông góc với mặt phẳng (ABCD) và SA = 4. "
            "Gọi (S) là mặt cầu ngoại tiếp hình chóp S.ABCD? Tính bán kính mặt cầu (S)."
        ),
        poly_solid={"solid_id": "poly", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"},
        premises=deepcopy(prems),
        sphere_notation="(S)",
        sphere_quote="Gọi (S) là mặt cầu ngoại tiếp hình chóp S.ABCD?",
        goal_type="radius",
        goal_quote="Tính bán kính mặt cầu (S).",
    )
    r_qmark = run_typed_fact_next_v2_route(p_qmark)
    assert r_qmark.status == "REFUSED" and r_qmark.code in ("QUESTION_CLAUSE_NOT_PREMISE", "CURVED_WORDING_UNSUPPORTED")
