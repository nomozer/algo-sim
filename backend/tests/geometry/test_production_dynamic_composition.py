# -*- coding: utf-8 -*-
"""Production Dynamic Function Composition verification suite (Phase 1).

Covers:
- Test Family A: Sequential multi-step production composition (depth 3 and depth 4 chains).
- Test Family B: Shared intermediates across multiple goals without duplicate construction.
- Test Family C: Composition across distinct geometric structures (pyramid with ratio point, right triangular prism, line/plane projections).
- Test Family D: Negative/adversarial fail-closed refusals (Source Gate, depth/kind boundaries, collinearity, depth cap, certificate forgery).
- Section VII Ablation Study: Explicit intermediate premises vs dynamic search discovery + contract-level ablations.
"""
from __future__ import annotations

import copy
from dataclasses import replace
from fractions import Fraction

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import ReplayExtractor
from app.simulation.geometry.radical import Radical
from app.simulation.geometry_functions import planner, registry
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})


def _run(text: str, payload: dict):
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    route = out.response["route_d"]
    answers = (
        {k: v.get("coef") for k, v in (route.get("answer_exact") or {}).items()}
        if route["status"] == "SERVED"
        else None
    )
    return route, out.response["envelope"], answers, out.receipt


def _pyramid_base_premises(side: str = "2", height: str = "3") -> tuple[str, list[dict]]:
    base_text = (
        f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {side}, "
        f"SA vuông góc với mặt phẳng (ABCD) và SA = {height}. "
    )
    premises = [
        {
            "kind": "regular_polygon",
            "args": {"vertices": ["A", "B", "C", "D"], "side": side},
            "quote": f"đáy ABCD là hình vuông cạnh {side}",
            "solid_id": "s1",
        },
        {
            "kind": "perpendicular_line_plane",
            "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
            "quote": "SA vuông góc với mặt phẳng (ABCD)",
            "solid_id": "s1",
        },
        {
            "kind": "segment_length",
            "args": {"segment": ["S", "A"], "value": height},
            "quote": f"SA = {height}",
            "solid_id": "s1",
        },
    ]
    return base_text, premises


# ── Independent exact Euclidean coordinate oracle (no planner/engine calls) ──────────────────────────────────────────

def _oracle_centroid(p1, p2, p3):
    return tuple((p1[i] + p2[i] + p3[i]) / Fraction(3) for i in range(3))


def _oracle_divide_segment(p1, p2, num: int, den: int):
    p, q = Fraction(num), Fraction(den)
    return tuple((q * p1[i] + p * p2[i]) / (p + q) for i in range(3))


def _oracle_proj_z0(pt):
    return (pt[0], pt[1], Fraction(0))


def _oracle_dist_sq(p1, p2) -> Fraction:
    return sum((p1[i] - p2[i]) ** 2 for i in range(3))


# ── Test Family A: Sequential Production Composition ─────────────────────────────────────────────────────────────────

def test_family_a1_sequential_centroid_to_plane_projection_to_plane_distance():
    """3-step sequential composition: centroid(SBC) -> orthogonal_projection((ABCD)) -> ask_distance_point_plane((SAD))."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    )
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["S", "B", "C"],
                "quote": "trọng tâm của tam giác SBC",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@g1",
                "plane": ["A", "B", "C", "D"],
                "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "plane": ["S", "A", "D"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "4/3"}

    # Independent Euclidean Fraction oracle check:
    S = (Fraction(0), Fraction(0), Fraction(3))
    B = (Fraction(2), Fraction(0), Fraction(0))
    C = (Fraction(2), Fraction(2), Fraction(0))
    G_oracle = _oracle_centroid(S, B, C)
    H_oracle = _oracle_proj_z0(G_oracle)
    assert H_oracle == (Fraction(4, 3), Fraction(2, 3), Fraction(0))
    assert H_oracle[0] == Fraction(4, 3)  # distance to plane (SAD) where x = 0

    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
    assert tel["search_generated_steps"] == ["q1_aux2"]
    assert tel["search_depth"] == 3

    cert = next(d for d in route["planner"]["auxiliary"] if d.get("rule") == "effect-chain")
    assert [e["fn"] for e in cert["chain"]] == ["centroid", "orthogonal_projection", "ask_distance_point_plane"]
    assert cert["operand"]["descriptor"] == "orthogonal_projection"
    assert cert["operand"]["nested"]["descriptor"] == "centroid"
    assert validate_construction_continuity(env["scene3d"]) == []


def test_family_a2_four_step_centroid_to_plane_projection_to_line_foot_distance():
    """4-step sequential composition (depth 4):
    centroid(SBC) -> orthogonal_projection((ABCD)) -> orthogonal_projection_line(AB) -> ask_length."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD) đến đường thẳng AB"
    )
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["S", "B", "C"],
                "quote": "trọng tâm của tam giác SBC",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@g1",
                "plane": ["A", "B", "C", "D"],
                "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "line": ["A", "B"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "2/3"}

    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
    assert tel["search_generated_steps"] == ["q1_aux2"]
    assert tel["search_depth"] == 3

    cert = next(d for d in route["planner"]["auxiliary"] if d.get("rule") == "effect-chain")
    assert [e["fn"] for e in cert["chain"]] == [
        "centroid",
        "orthogonal_projection",
        "orthogonal_projection_line",
        "ask_length",
    ]
    assert validate_construction_continuity(env["scene3d"]) == []


def test_family_a3_sequential_midpoint_to_line_projection_to_plane_distance():
    """3-step sequential composition with line projection:
    midpoint(SC) -> orthogonal_projection_line(BD) -> ask_distance_point_plane((SAB))."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trung điểm của SC "
        "lên đường thẳng BD đến mặt phẳng (SAB)"
    )
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "m1",
                "kind": "midpoint",
                "segment": ["S", "C"],
                "quote": "trung điểm của SC",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection_line",
                "point": "@m1",
                "line": ["B", "D"],
                "quote": "hình chiếu vuông góc của trung điểm của SC lên đường thẳng BD",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "plane": ["S", "A", "B"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "1"}

    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
    assert tel["search_generated_steps"] == ["q1_aux2"]
    assert tel["search_depth"] == 3
    assert validate_construction_continuity(env["scene3d"]) == []


# ── Test Family B: Shared Intermediates Across Multiple Goals ────────────────────────────────────────────────────────

def test_family_b1_shared_composed_intermediate_across_distance_and_area_goals():
    """Two distinct goals (distance to line AB and area of triangle with S, A) share the 2-step composed point @h1
    without rebuilding either the centroid or its plane projection."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q1_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD) đến đường thẳng AB"
    )
    q2_quote = (
        "Tính diện tích tam giác tạo bởi hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD), S và A"
    )
    text = base_text + q1_quote + ". " + q2_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["S", "B", "C"],
                "quote": "trọng tâm của tam giác SBC",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@g1",
                "plane": ["A", "B", "C", "D"],
                "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "line": ["A", "B"]},
                "quote": q1_quote,
                "solid_id": "s1",
            },
            {
                "goal_id": "q2",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"polygon": ["@h1", "S", "A"]},
                "quote": q2_quote,
                "solid_id": "s1",
            },
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "2/3", "q2": "√5"}

    calls = route["planner"]["calls"]
    assert len([c for c in calls if c["fn"] == "centroid"]) == 1
    assert len([c for c in calls if c["fn"] == "orthogonal_projection"]) == 1

    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
    assert tel["reused_intermediates"] >= 1
    assert tel["search_generated_steps"] == ["q1_aux2"]

    certs = [d for d in route["planner"]["auxiliary"] if d.get("rule") == "effect-chain"]
    assert len(certs) == 2
    assert certs[0]["operand"]["label"] == certs[1]["operand"]["label"]
    assert certs[0]["operand"]["nested"]["label"] == certs[1]["operand"]["nested"]["label"]
    assert validate_construction_continuity(env["scene3d"]) == []


# ── Test Family C: Composition Across Geometric Structures ───────────────────────────────────────────────────────────

def test_family_c1_pyramid_with_ratio_point_centroid_to_plane_projection_multi_goal():
    """Pyramid S.ABCD with ratio point E on SC (SE = 2EC, t = 2/3) -> centroid(EAB) -> orthogonal_projection((ABCD)) -> distance + segment length."""
    base_text, premises = _pyramid_base_premises("3", "3")
    e_quote = "Gọi E là điểm thuộc cạnh SC sao cho SE = 2EC"
    q1_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác EAB "
        "lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    )
    q2_quote = (
        "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của trọng tâm của tam giác EAB "
        "lên mặt phẳng (ABCD) với A"
    )
    text = base_text + e_quote + ". " + q1_quote + ". " + q2_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises + [
            {
                "kind": "divide_segment",
                "args": {"point": "E", "segment": ["S", "C"], "ratio": "2/3"},
                "quote": e_quote,
                "solid_id": "s1",
            }
        ],
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["E", "A", "B"],
                "quote": "trọng tâm của tam giác EAB",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@g1",
                "plane": ["A", "B", "C", "D"],
                "quote": "hình chiếu vuông góc của trọng tâm của tam giác EAB lên mặt phẳng (ABCD)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "plane": ["S", "A", "D"]},
                "quote": q1_quote,
                "solid_id": "s1",
            },
            {
                "goal_id": "q2",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"segment": ["@h1", "A"]},
                "quote": q2_quote,
                "solid_id": "s1",
            },
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")

    # Oracle check: S=(0,0,3), C=(3,3,0), SE/SC = 2/3 => E=(2,2,1); A=(0,0,0), B=(3,0,0) => G_EAB=(5/3, 2/3, 1/3) => H=(5/3, 2/3, 0)
    S = (Fraction(0), Fraction(0), Fraction(3))
    C = (Fraction(3), Fraction(3), Fraction(0))
    A = (Fraction(0), Fraction(0), Fraction(0))
    B = (Fraction(3), Fraction(0), Fraction(0))
    E_oracle = _oracle_divide_segment(S, C, 2, 1)
    H_oracle = _oracle_proj_z0(_oracle_centroid(E_oracle, A, B))
    assert H_oracle == (Fraction(5, 3), Fraction(2, 3), Fraction(0))
    assert _oracle_dist_sq(H_oracle, A) == Fraction(29, 9)
    assert answers == {"q1": "5/3", "q2": "√29/3"}

    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
    assert tel["reused_intermediates"] >= 1
    assert validate_construction_continuity(env["scene3d"]) == []


def test_family_c2_right_triangular_prism_four_step_composition_and_shared_intermediate():
    """Right triangular prism ABC.A'B'C': midpoint(B'C') -> orthogonal_projection((ABC)) -> orthogonal_projection_line(AC) -> ask_length,
    plus shared intermediate distance to (ABB')."""
    base_text = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, "
        "AB = 2, AC = 2, AA' = 3. "
    )
    q1_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trung điểm của B'C' "
        "lên mặt phẳng (ABC) đến đường thẳng AC"
    )
    q2_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trung điểm của B'C' "
        "lên mặt phẳng (ABC) đến mặt phẳng (ABB')"
    )
    text = base_text + q1_quote + ". " + q2_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [
            {
                "solid_id": "s1",
                "solid_type": "prism",
                "notation": "ABC.A'B'C'",
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
            }
        ],
        "premises": [
            {
                "kind": "right_prism",
                "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
                "solid_id": "s1",
            },
            {
                "kind": "right_angle",
                "args": {"vertices": ["A", "B", "C"], "right_at": "A"},
                "quote": "đáy ABC là tam giác vuông tại A",
                "solid_id": "s1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "B"], "value": "2"},
                "quote": "AB = 2",
                "solid_id": "s1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "C"], "value": "2"},
                "quote": "AC = 2",
                "solid_id": "s1",
            },
            {
                "kind": "segment_length",
                "args": {"segment": ["A", "A'"], "value": "3"},
                "quote": "AA' = 3",
                "solid_id": "s1",
            },
        ],
        "relations": [],
        "described_points": [
            {
                "described_id": "m1",
                "kind": "midpoint",
                "segment": ["B'", "C'"],
                "quote": "trung điểm của B'C'",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@m1",
                "plane": ["A", "B", "C"],
                "quote": "hình chiếu vuông góc của trung điểm của B'C' lên mặt phẳng (ABC)",
            },
        ],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}
        ],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "line": ["A", "C"]},
                "quote": q1_quote,
                "solid_id": "s1",
            },
            {
                "goal_id": "q2",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "plane": ["A", "B", "B'"]},
                "quote": q2_quote,
                "solid_id": "s1",
            },
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "1", "q2": "1"}

    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
    assert tel["search_depth"] == 3
    assert tel["reused_intermediates"] >= 1
    assert validate_construction_continuity(env["scene3d"]) == []


# ── Test Family D: Negative / Adversarial & Fail-Closed Boundaries ──────────────────────────────────────────────────

def test_family_d1_source_gate_rejects_mismatched_inner_or_outer_quote():
    """If the inner described point's quote mismatches its polygon, the pipeline refuses fail-closed with SOURCE_OBJECT_MISMATCH."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    )
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["S", "C", "D"],
                "quote": "trọng tâm của tam giác SBC",  # claims SBC in quote, but polygon is SCD!
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@g1",
                "plane": ["A", "B", "C", "D"],
                "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "plane": ["S", "A", "D"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "REFUSED" and answers is None
    assert env["reason_code"] == "SOURCE_OBJECT_MISMATCH"


def test_family_d2_nested_orthocenter_projection_distance_is_served_exactly():
    """Nested DescribedPointSpec through a POINT_DEFINITIONS point (`orthocenter(SBC) -> orthogonal_projection((ABCD)) -> distance((SAD))`) is dynamically planned and served exactly (2)."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trực tâm của tam giác SBC "
        "lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    )
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "o1",
                "kind": "orthocenter",
                "polygon": ["S", "B", "C"],
                "quote": "trực tâm của tam giác SBC",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@o1",
                "plane": ["A", "B", "C", "D"],
                "quote": "hình chiếu vuông góc của trực tâm của tam giác SBC lên mặt phẳng (ABCD)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "plane": ["S", "A", "D"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "SERVED", env.get("reason_code")
    assert answers == {"q1": "2"}
    assert validate_construction_continuity(env["scene3d"]) == []
    tel = route["planner"]["search_telemetry"]
    assert tel["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"


def test_family_d2b_quadrilateral_area_with_described_point_refuses_fail_closed():
    """Negative boundary: quadrilateral area goal with `@id` fails closed with BRIDGE_UNSUPPORTED_DESCRIBED_POINT."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = "Tính diện tích tứ giác tạo bởi trọng tâm của tam giác SBC và A, B, D"
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["S", "B", "C"],
                "quote": "trọng tâm của tam giác SBC",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "area",
                "target": {"polygon": ["@g1", "A", "B", "D"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "REFUSED" and answers is None
    assert env["reason_code"] == "BRIDGE_UNSUPPORTED_DESCRIBED_POINT"


def test_family_d3_collinear_inner_triangle_refuses_fail_closed():
    """If the inner centroid's polygon (A, B, M where M is midpoint of AB) is collinear, the engine refuses with COLLINEAR_POINTS."""
    base_text, premises = _pyramid_base_premises("2", "3")
    m_quote = "Gọi M là trung điểm của AB"
    q_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác ABM "
        "lên mặt phẳng (SBC) đến mặt phẳng (SAD)"
    )
    text = base_text + m_quote + ". " + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises + [
            {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": m_quote, "solid_id": "s1"}
        ],
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["A", "B", "M"],
                "quote": "trọng tâm của tam giác ABM",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@g1",
                "plane": ["S", "B", "C"],
                "quote": "hình chiếu vuông góc của trọng tâm của tam giác ABM lên mặt phẳng (SBC)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "plane": ["S", "A", "D"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }
    route, env, answers, _receipt = _run(text, payload)
    assert route["status"] == "REFUSED" and answers is None
    assert env["reason_code"] == "COLLINEAR_POINTS"


def test_family_d4_search_budget_and_tampered_nested_certificate_refuse_fail_closed(monkeypatch):
    """Search depth cap refuses with PLAN_TOO_LARGE; tampered inner nested certificate refuses with AUXILIARY_RULE_MISMATCH."""
    base_text, premises = _pyramid_base_premises("2", "3")
    q_quote = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD) đến đường thẳng AB"
    )
    text = base_text + q_quote + "."
    payload = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["S", "B", "C"],
                "quote": "trọng tâm của tam giác SBC",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@g1",
                "plane": ["A", "B", "C", "D"],
                "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "line": ["A", "B"]},
                "quote": q_quote,
                "solid_id": "s1",
            }
        ],
    }

    with monkeypatch.context() as m:
        m.setattr(planner, "MAX_EFFECT_DEPTH", 2)
        route, env, answers, _ = _run(text, payload)
        assert route["status"] == "REFUSED" and answers is None
        assert env["reason_code"] == "PLAN_TOO_LARGE"

    real_plan = planner.lap_ke_hoach

    def _forged_nested(*a, **k):
        plan = real_plan(*a, **k)
        for cert in plan.auxiliary:
            if cert.get("rule") == "effect-chain" and cert.get("operand", {}).get("nested"):
                cert["operand"]["nested"]["points"] = ["S", "C", "D"]
        return plan

    with monkeypatch.context() as m:
        m.setattr(planner, "lap_ke_hoach", _forged_nested)
        r = run_typed_fact_next_v2_route(payload)
        assert r.status == "REFUSED" and r.code in ("AUXILIARY_RULE_MISMATCH", "SOURCE_OBJECT_MISMATCH")


# ── Section VII: Production Ablation Study ───────────────────────────────────────────────────────────────────────────

def test_section_vii_ablation_explicit_premises_vs_dynamic_composition_and_contract_ablation(monkeypatch):
    """Section VII Ablation Proof:
    1. Control (explicit intermediate premises G and H): solved as REGISTERED_DECOMPOSITION (search_generated_steps == []).
    2. Ablated intermediate premises (only the composed goal is stated): Planner dynamically discovers the 4-step chain
       centroid -> orthogonal_projection -> orthogonal_projection_line -> ask_length (DISCOVERED_FUNCTION_COMPOSITION,
       search_generated_steps == ['q1_aux2']), yielding the exact same answer 2/3 and verified Scene3D.
    3. Contract ablation: removing orthogonal_projection.planning or centroid.planning from REGISTRY causes the same
       case to fail closed with UNSUPPORTED_CAPABILITY.
    """
    base_text, premises = _pyramid_base_premises("2", "3")

    # 1. Control with explicit intermediate premises G and H
    g_quote = "Gọi G là trọng tâm của tam giác SBC"
    h_quote = "Gọi H là hình chiếu vuông góc của G lên mặt phẳng (ABCD)"
    q_explicit = "Tính khoảng cách từ H đến đường thẳng AB"
    text_explicit = base_text + g_quote + ". " + h_quote + ". " + q_explicit + "."
    payload_explicit = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text_explicit,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises + [
            {"kind": "centroid", "args": {"point": "G", "polygon": ["S", "B", "C"]}, "quote": g_quote, "solid_id": "s1"},
            {
                "kind": "orthogonal_projection",
                "args": {"point": "G", "plane": ["A", "B", "C", "D"], "image": "H"},
                "quote": h_quote,
                "solid_id": "s1",
            },
        ],
        "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "H", "line": ["A", "B"]},
                "quote": q_explicit,
                "solid_id": "s1",
            }
        ],
    }
    route_ctrl, _env_ctrl, ans_ctrl, _ = _run(text_explicit, payload_explicit)
    assert route_ctrl["status"] == "SERVED" and ans_ctrl == {"q1": "2/3"}
    assert route_ctrl["planner"]["search_telemetry"]["classification"] == "REGISTERED_DECOMPOSITION"
    assert route_ctrl["planner"]["search_telemetry"]["search_generated_steps"] == []

    # 2. Ablated intermediate premises (dynamic multi-step search discovery)
    q_composed = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD) đến đường thẳng AB"
    )
    text_composed = base_text + q_composed + "."
    payload_composed = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text_composed,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises,
        "relations": [],
        "described_points": [
            {
                "described_id": "g1",
                "kind": "centroid",
                "polygon": ["S", "B", "C"],
                "quote": "trọng tâm của tam giác SBC",
            },
            {
                "described_id": "h1",
                "kind": "orthogonal_projection",
                "point": "@g1",
                "plane": ["A", "B", "C", "D"],
                "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)",
            },
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {
                "goal_id": "q1",
                "kind": "measurement",
                "goal_type": "distance",
                "target": {"point": "@h1", "line": ["A", "B"]},
                "quote": q_composed,
                "solid_id": "s1",
            }
        ],
    }
    route_dyn, env_dyn, ans_dyn, _ = _run(text_composed, payload_composed)
    assert route_dyn["status"] == "SERVED" and ans_dyn == ans_ctrl == {"q1": "2/3"}
    tel_dyn = route_dyn["planner"]["search_telemetry"]
    assert tel_dyn["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
    assert tel_dyn["search_generated_steps"] == ["q1_aux2"]
    assert tel_dyn["search_depth"] == 3
    assert validate_construction_continuity(env_dyn["scene3d"]) == []

    # 3. Contract Ablation: ablating orthogonal_projection.planning or centroid.planning fails closed
    for fn_name in ("orthogonal_projection", "centroid"):
        with monkeypatch.context() as m:
            spec = registry.REGISTRY[fn_name]
            m.setitem(registry.REGISTRY, fn_name, replace(spec, planning=None))
            r_abl, env_abl, ans_abl, _ = _run(text_composed, copy.deepcopy(payload_composed))
            assert r_abl["status"] == "REFUSED" and ans_abl is None
            assert env_abl["reason_code"] in ("UNSUPPORTED_CAPABILITY", "BRIDGE_UNSUPPORTED_DESCRIBED_POINT")
