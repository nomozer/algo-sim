# -*- coding: utf-8 -*-
"""Hybrid V2 named planes (`hybrid-v2-backend-generalization`): a canonical `/2` distance or angle goal may name its plane
by ALL of its vertices — (ABCD), (BCC'B') — as the premises already may. Before, every plane operand had to be exactly
three labels (`INVALID_MATH_GOAL`) because the planner cut the point–plane distance plane to its first three labels, so a
non-coplanar fourth label was never checked (review I-1 of the B3 slice).

Now every label reaches the engine, which checks exactly that the labels lie in one plane (`SOURCE_OBJECT_MISMATCH`) and
that the three it measures with are not collinear (`COLLINEAR_POINTS`, the kernel's own code). Closed-form oracles from the stated facts only
(no engine coordinates):

- right prism ABC.A'B'C', right angle at A, AB = x, AC = y, AA' = h: d²(A, (BCC'B')) = x²y²/(x²+y²);
  d²(B, (ACC'A')) = x²; cos²(A'B, (ACC'A')) = h²/(x²+h²); cos²((BCC'B'), (ACC'A')) = cos²(ACB) = y²/(x²+y²);
- pyramid S.ABCD, square base of side s, SA ⊥ (ABCD), SA = h: d²(S, (ABCD)) = h²; cos²(SC, (ABCD)) = 2s²/(2s²+h²);
  cos²((SCD), (ABCD)) = cos²(SDA) = s²/(s²+h²).

Authored development cases — not a holdout, not an extraction-quality measurement, no provider call.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism, _square


def _ten(v) -> str:
    return "".join(v) if len(v) == 2 else "(" + "".join(v) + ")"


def _hoi(goal_type: str, target: dict, quote: str | None = None) -> tuple[str, dict, str]:
    if quote is None:
        if goal_type == "distance":
            quote = f"Tính khoảng cách từ {target['point']} đến mặt phẳng {_ten(target['plane'])}."
        else:
            quote = "Tính góc giữa " + " và ".join(
                ("đường thẳng " if len(v) == 2 else "mặt phẳng ") + _ten(v) for v in target.values()) + "."
    return quote, target, goal_type


def _prism_goal(goal_type, target, quote=None, extra=(), **kw):
    quote, target, goal_type = _hoi(goal_type, target, quote)
    p = _prism(ask=(quote, target), **kw)
    p["math_goals"][0]["goal_type"] = goal_type
    for q, prem in extra:                                  # extra premises go BEFORE the question in the text
        p["premises"].append({**prem, "quote": q})
        p["problem_text"] = p["problem_text"].replace(quote, f"{q} {quote}")
    return p


def _pyramid(goal_type, target, s=4, h=3, labels="SABCD", quote=None):
    S, A, B, C, D = labels
    base = [A, B, C, D]
    name = f"{S}.{A}{B}{C}{D}"
    solid, shape = f"Cho hình chóp {name}.", f"Đáy {A}{B}{C}{D} là hình vuông cạnh {s}."
    perp, sa = f"{S}{A} vuông góc với mặt phẳng ({A}{B}{C}{D}).", f"{S}{A} = {h}."
    quote, target, goal_type = _hoi(goal_type, target, quote)
    return {"schema_version": "typed-fact-next/2", "problem_text": " ".join((solid, shape, perp, sa, quote)),
            "length_unit": "1",
            "solids": [{"solid_id": "py", "solid_type": "pyramid", "notation": name, "quote": solid}],
            "premises": [{"kind": "base_is_square", "args": {"vertices": base, "side": str(s)}, "quote": shape},
                         {"kind": "perpendicular_line_plane", "args": {"line": [S, A], "plane": base}, "quote": perp},
                         {"kind": "segment_length", "args": {"segment": [S, A], "value": str(h)}, "quote": sa}],
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "py", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": goal_type, "target": target,
                            "quote": quote}]}


def _served(p):
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "SERVED", (r.code, r.reason)
    return r


def _d2(p) -> F:
    return _square(_served(p))


def _cos2(p) -> F:
    return F(_served(p).exec_result.final_memory["kq_q"])


def _refused(p) -> str:
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "REFUSED", (r.status, r.code)
    return r.code


# ── served: four-label faces of a right prism ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("labels,x,y,h", [("ABC", 6, 8, 12), ("DEF", 3, 4, 5), ("KLM", 12, 16, 7)])
def test_distance_to_a_lateral_face_named_by_its_four_vertices(labels, x, y, h):
    a, b, c = labels
    face = [b, c, c + "'", b + "'"]
    assert _d2(_prism_goal("distance", {"point": a, "plane": face}, labels=labels, x=x, y=y, h=h)) == \
        F(x * x * y * y, x * x + y * y)


def test_distance_from_b_to_the_face_containing_ac_is_ab():
    assert _d2(_prism_goal("distance", {"point": "B", "plane": ["A", "C", "C'", "A'"]})) == 36


@pytest.mark.parametrize("face", [["B", "C", "C'", "B'"], ["B'", "C'", "C", "B"], ["C", "C'", "B'", "B"],
                                  ["B", "C'", "C", "B'"]])
def test_any_order_of_the_same_four_coplanar_labels_is_the_same_plane(face):
    assert _d2(_prism_goal("distance", {"point": "A", "plane": face})) == F(36 * 64, 36 + 64)


def test_four_and_three_label_names_of_one_face_agree():
    four = _d2(_prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "B'"]}))
    three = _d2(_prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'"]},
                            quote="Tính khoảng cách từ A đến mặt phẳng (BCC'B')."))
    assert four == three


@pytest.mark.parametrize("x,y,h", [(6, 8, 12), (3, 4, 5)])
def test_line_to_four_label_face_angle(x, y, h):
    p = _prism_goal("angle", {"line": ["A'", "B"], "plane": ["A", "C", "C'", "A'"]}, x=x, y=y, h=h)
    assert _cos2(p) == F(h * h, x * x + h * h)


@pytest.mark.parametrize("x,y,h", [(6, 8, 12), (3, 4, 5)])
def test_dihedral_angle_between_two_four_label_lateral_faces(x, y, h):
    p = _prism_goal("angle", {"plane1": ["B", "C", "C'", "B'"], "plane2": ["A", "C", "C'", "A'"]}, x=x, y=y, h=h)
    assert _cos2(p) == F(y * y, x * x + y * y)


def test_scaling_the_prism_scales_the_squared_distance_by_four():
    t = {"point": "A", "plane": ["B", "C", "C'", "B'"]}
    assert _d2(_prism_goal("distance", t, x=12, y=16, h=24)) == 4 * _d2(_prism_goal("distance", t))


# ── served: the base (ABCD) of a pyramid with SA ⊥ (ABCD) — reference family #3 ───────────────────────────────

@pytest.mark.parametrize("labels,s,h", [("SABCD", 4, 3), ("PKLMN", 2, 5), ("SABCD", 6, 1)])
def test_angle_between_a_lateral_edge_and_the_square_base(labels, s, h):
    S, A, B, C, D = labels
    assert _cos2(_pyramid("angle", {"line": [S, C], "plane": [A, B, C, D]}, s=s, h=h, labels=labels)) == \
        F(2 * s * s, 2 * s * s + h * h)


def test_dihedral_angle_between_a_lateral_face_and_the_square_base():
    assert _cos2(_pyramid("angle", {"plane1": ["S", "C", "D"], "plane2": ["A", "B", "C", "D"]})) == F(16, 16 + 9)


def test_distance_from_the_apex_to_the_square_base_is_sa():
    assert _d2(_pyramid("distance", {"point": "S", "plane": ["A", "B", "C", "D"]})) == 9


def test_adapter4_envelope_carries_every_label_of_the_named_plane():
    p = _pyramid("angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]})
    rd = build_adapter4_response(run_typed_fact_next_v2_route(p), p["problem_text"])["route_d"]
    assert rd["status"] == "SERVED", rd
    prov = next(x for x in rd["source_provenance"] if x["id"] == "q")
    assert (prov["fn"], prov["args"]) == ("ask_angle_line_plane", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]})


def test_distance_call_keeps_the_three_label_contract_and_the_quote_names_the_face():
    """`ask_distance_point_plane` takes exactly three plane labels (registry contract, part of the function-calling
    surface — unchanged). The provenance reports the call actually made; the fourth label was checked, not dropped
    (`test_a_fourth_label_absent_from_the_quote_is_still_checked`)."""
    p = _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "B'"]})
    rd = build_adapter4_response(run_typed_fact_next_v2_route(p), p["problem_text"])["route_d"]
    assert rd["status"] == "SERVED", rd
    prov = next(x for x in rd["source_provenance"] if x["id"] == "q")
    assert (prov["fn"], prov["args"]) == ("ask_distance_point_plane", {"point": "A", "plane": ["B", "C", "C'"]})
    assert prov["quotes"] == ["Tính khoảng cách từ A đến mặt phẳng (BCC'B')."]


# ── refused: every label is checked, nothing is truncated or guessed ──────────────────────────────────────────

@pytest.mark.parametrize("goal_type,target", [
    ("distance", {"point": "A", "plane": ["B", "C", "C'", "A'"]}),
    ("angle", {"line": ["A'", "B"], "plane": ["A", "B", "C", "B'"]}),
    ("angle", {"plane1": ["B", "C", "C'", "A"], "plane2": ["A", "B", "C"]}),
])
def test_a_non_coplanar_fourth_label_is_refused(goal_type, target):
    assert _refused(_prism_goal(goal_type, target)) == "SOURCE_OBJECT_MISMATCH"


def test_a_fourth_label_absent_from_the_quote_is_still_checked():
    """Review I-1: the question quote names the three-label face (BCC'), the target adds A'. The Source Gate accepts a
    target that contains the quoted plane, so only the engine's check of EVERY call label can refuse it — a planner that
    cut the plane to its first three labels would serve the distance to (BCC')."""
    p = _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "A'"]},
                    quote="Tính khoảng cách từ A đến mặt phẳng (BCC').")
    assert _refused(p) == "SOURCE_OBJECT_MISMATCH"


def test_a_pyramid_base_with_the_apex_as_fourth_label_is_refused():
    assert _refused(_pyramid("angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "S"]})) == "SOURCE_OBJECT_MISMATCH"


@pytest.mark.parametrize("goal_type,target", [
    ("distance", {"point": "A", "plane": ["B", "M", "C", "C'"]}),
    ("angle", {"line": ["A'", "B"], "plane": ["B", "M", "C", "C'"]}),
])
def test_collinear_leading_labels_are_refused_with_the_kernel_code(goal_type, target):
    """B, M, C are collinear (M midpoint of BC); the four labels still lie in (BCC'B') but the engine measures with the
    first three. The angle call already met the kernel's `COLLINEAR_POINTS`; without the leading-label check the distance
    call (which carries only [B, M, C]) was refused as "(BMC) is not a plane" — fail-closed, but the wrong reason."""
    p = _prism_goal(goal_type, target, extra=[("Gọi M là trung điểm của BC.",
                                               {"kind": "midpoint", "args": {"point": "M", "segment": ["B", "C"]}})])
    assert _refused(p) == "COLLINEAR_POINTS"


@pytest.mark.parametrize("plane", [["B", "C", "C'", "B"], ["B", "C"], "BCC'B'", ["B", "C", "C'", 7]])
def test_malformed_plane_operands_stay_invalid(plane):
    p = _prism_goal("distance", {"point": "A", "plane": plane}, quote="Tính khoảng cách từ A đến mặt phẳng (BCC'B').")
    assert _refused(p) in ("INVALID_MATH_GOAL", "INVALID_TYPED_FACT_NEXT")


def test_quote_naming_another_face_is_refused():
    p = _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "B'"]},
                    quote="Tính khoảng cách từ A đến mặt phẳng (ACC'A').")
    assert _refused(p) == "SOURCE_OBJECT_MISMATCH"
