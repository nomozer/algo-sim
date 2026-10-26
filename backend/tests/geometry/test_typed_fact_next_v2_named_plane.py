# -*- coding: utf-8 -*-
"""Hybrid V2 named planes (`hybrid-v2-backend-generalization`): a canonical `/2` distance or angle goal may name its plane
by ALL of its vertices — (ABCD), (BCC'B') — as the premises already may. Before, every plane operand had to be exactly
three labels (`INVALID_MATH_GOAL`) because the planner cut the point–plane distance plane to its first three labels, so a
non-coplanar fourth label was never checked (review I-1 of the B3 slice).

Now every label reaches the engine, which checks exactly that the labels lie in one plane (`SOURCE_OBJECT_MISMATCH`
otherwise, also when every point is collinear), measures through the first non-collinear triple of the WHOLE group
(`chon_ba_mat`, so label order never causes a refusal) and shows the plane under the full written name. Closed-form
oracles from the stated facts only (no engine coordinates):

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


_M_ON_BC = [("Gọi M là trung điểm của BC.", {"kind": "midpoint", "args": {"point": "M", "segment": ["B", "C"]}})]
#: A' projects onto A in a right prism: H and A are two labels of ONE point.
_H_IS_A = [("Hình chiếu vuông góc của A' lên (ABC) là H.",
            {"kind": "orthogonal_projection", "args": {"point": "A'", "image": "H", "plane": ["A", "B", "C"]}})]


@pytest.mark.parametrize("plane", [["B", "M", "C", "C'"], ["M", "B", "C", "C'", "B'"], ["C'", "B", "M", "C"]])
def test_collinear_leading_labels_still_name_a_plane(plane):
    """B, M, C are collinear (M midpoint of BC) but the group also holds C' off that line, so it names exactly the face
    (BCC'B'). The engine measures through the first NON-collinear triple of the whole group (`chon_ba_mat`), never
    refuses because of the order the labels were written in (Owner, 2026-10-26)."""
    assert _d2(_prism_goal("distance", {"point": "A", "plane": plane}, extra=_M_ON_BC)) == F(36 * 64, 36 + 64)


def test_collinear_leading_labels_in_an_angle_plane():
    # w = B - A' = (x, 0, -h) against the face normal ∝ (y, x, 0): sin² = (xy)² / ((x²+h²)(x²+y²)) = 2304/18000
    p = _prism_goal("angle", {"line": ["A'", "B"], "plane": ["B", "M", "C", "C'"]}, extra=_M_ON_BC)
    assert _cos2(p) == 1 - F(36 * 64, (36 + 144) * (36 + 64))


def test_a_label_coinciding_with_another_point_is_skipped_for_the_witness():
    """H = A (projection of A' in a right prism): triples (H, A, ·) are degenerate, (H, B, C) is not."""
    assert _d2(_prism_goal("distance", {"point": "A'", "plane": ["H", "A", "B", "C"]}, extra=_H_IS_A)) == 144


@pytest.mark.parametrize("plane", [["B", "M", "C"], ["B", "M", "C", "H"]])
def test_a_group_whose_points_are_all_collinear_is_refused(plane):
    extra = _M_ON_BC + ([("Gọi H là trung điểm của BM.", {"kind": "midpoint", "args": {"point": "H",
                                                                                 "segment": ["B", "M"]}})]
                        if "H" in plane else [])
    assert _refused(_prism_goal("distance", {"point": "A", "plane": plane}, extra=extra)) == "SOURCE_OBJECT_MISMATCH"


def test_an_unknown_label_in_the_plane_is_refused():
    p = _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "X"]})
    assert _refused(p) in ("UNKNOWN_LABEL", "SOURCE_OBJECT_MISMATCH", "UNKNOWN_VERTEX_REF")


# ── learner-facing identity: the plane is shown under the name the problem wrote ───────────────────────────

@pytest.mark.parametrize("p,name", [
    (lambda: _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "B'"]}), "(BCC′B′)"),
    (lambda: _pyramid("angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}), "(ABCD)"),
    (lambda: _prism_goal("distance", {"point": "A", "plane": ["B", "M", "C", "C'"]}, extra=_M_ON_BC), "(BMCC′)"),
])
def test_the_scene_shows_the_full_plane_name_not_the_witness_triple(p, name):
    obj = next(o for o in _served(p()).scene3d["objects"] if o["id"] == "mp_q")
    assert (obj["label"], obj["notation"], obj["reference"]) == (name, name, name)


def test_a_three_label_plane_keeps_its_previous_display():
    obj = next(o for o in _served(_prism_goal("distance", {"point": "A'", "plane": ["A", "B", "C"]})).scene3d["objects"]
               if o["id"] == "mp_q")
    assert obj["notation"] == "(ABC)"


# ── the same code on more families: #4 regular pyramid, #11 cuboid, #13 oblique prism ────────────────────────

def _cuboid(goal_type, target, a=3, b=4, c=12):
    solid, rect = "Cho hình hộp chữ nhật ABCD.A'B'C'D'.", "Đáy ABCD là hình chữ nhật."
    qs = [solid, rect, f"AB = {a}.", f"AD = {b}.", f"AA' = {c}."]
    quote, target, goal_type = _hoi(goal_type, target)
    base, top = ["A", "B", "C", "D"], ["A'", "B'", "C'", "D'"]
    return {"schema_version": "typed-fact-next/2", "problem_text": " ".join([*qs, quote]), "length_unit": "1",
            "solids": [{"solid_id": "h", "solid_type": "prism", "notation": "ABCD.A'B'C'D'", "quote": solid}],
            "premises": [{"kind": "base_is_rectangle", "args": {"vertices": base}, "quote": rect},
                         {"kind": "right_prism", "args": {"base": base, "top": top}, "quote": solid},
                         {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": str(a)}, "quote": qs[2]},
                         {"kind": "segment_length", "args": {"segment": ["A", "D"], "value": str(b)}, "quote": qs[3]},
                         {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": str(c)}, "quote": qs[4]}],
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "h", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": goal_type, "target": target,
                            "quote": quote}]}


def _regular(goal_type, target, s=4, l=3):
    solid, sq, sa = "Cho hình chóp tứ giác đều S.ABCD.", f"Đáy ABCD là hình vuông cạnh {s}.", f"SA = {l}."
    quote, target, goal_type = _hoi(goal_type, target)
    base = ["A", "B", "C", "D"]
    return {"schema_version": "typed-fact-next/2", "problem_text": " ".join([solid, sq, sa, quote]), "length_unit": "1",
            "solids": [{"solid_id": "py", "solid_type": "pyramid", "notation": "S.ABCD", "quote": solid}],
            "premises": [{"kind": "regular_pyramid", "args": {"apex": "S", "base": base}, "quote": solid},
                         {"kind": "base_is_square", "args": {"vertices": base, "side": str(s)}, "quote": sq},
                         {"kind": "segment_length", "args": {"segment": ["S", "A"], "value": str(l)}, "quote": sa}],
            "simulation_goals": [{"goal_id": "draw", "kind": "construct_object", "target_solid_id": "py", "quote": solid}],
            "math_goals": [{"goal_id": "q", "kind": "measurement", "goal_type": goal_type, "target": target,
                            "quote": quote}]}


@pytest.mark.parametrize("x,y,h", [(6, 8, 12), (12, 16, 24)])
def test_oblique_prism_distance_to_a_lateral_face(x, y, h):
    """A' over the midpoint of BC at height h: AA' = (x/2, y/2, h), face normal ∝ (yh, xh, −xy)."""
    p = _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "B'"]}, x=x, y=y, h=h, oblique=True)
    assert _d2(p) == F(x * x * y * y * h * h, y * y * h * h + x * x * h * h + x * x * y * y)


@pytest.mark.parametrize("a,b,c", [(3, 4, 12), (5, 12, 7)])
def test_cuboid_diagonal_plane_distance(a, b, c):
    assert _d2(_cuboid("distance", {"point": "A", "plane": ["B", "D", "D'", "B'"]}, a, b, c)) == F(a * a * b * b,
                                                                                                 a * a + b * b)


@pytest.mark.parametrize("a,b,c", [(3, 4, 12), (5, 12, 7)])
def test_cuboid_space_diagonal_to_the_base(a, b, c):
    assert _cos2(_cuboid("angle", {"line": ["A'", "C"], "plane": ["A", "B", "C", "D"]}, a, b, c)) == \
        F(a * a + b * b, a * a + b * b + c * c)


def test_cuboid_dihedral_between_a_diagonal_plane_and_the_base():
    assert _cos2(_cuboid("angle", {"plane1": ["A'", "B'", "C", "D"], "plane2": ["D", "C", "B", "A"]})) == F(16, 16 + 144)


def test_cuboid_non_coplanar_four_labels_are_refused():
    assert _refused(_cuboid("distance", {"point": "A", "plane": ["B", "D", "D'", "C'"]})) == "SOURCE_OBJECT_MISMATCH"


@pytest.mark.parametrize("s,l", [(4, 3), (2, 3)])
def test_regular_pyramid_lateral_edge_to_the_base(s, l):
    assert _cos2(_regular("angle", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}, s, l)) == F(s * s, 2 * l * l)


@pytest.mark.parametrize("s,l", [(4, 3), (2, 3)])
def test_regular_pyramid_lateral_face_to_the_base(s, l):
    h2 = l * l - F(s * s, 2)
    assert _cos2(_regular("angle", {"plane1": ["S", "C", "D"], "plane2": ["A", "B", "C", "D"]}, s, l)) == \
        F(s * s, 4) / (F(s * s, 4) + h2)


@pytest.mark.parametrize("plane", [["B", "C", "C'", "B"], ["B", "C"], "BCC'B'", ["B", "C", "C'", 7]])
def test_malformed_plane_operands_stay_invalid(plane):
    p = _prism_goal("distance", {"point": "A", "plane": plane}, quote="Tính khoảng cách từ A đến mặt phẳng (BCC'B').")
    assert _refused(p) in ("INVALID_MATH_GOAL", "INVALID_TYPED_FACT_NEXT")


def test_quote_naming_another_face_is_refused():
    p = _prism_goal("distance", {"point": "A", "plane": ["B", "C", "C'", "B'"]},
                    quote="Tính khoảng cách từ A đến mặt phẳng (ACC'A').")
    assert _refused(p) == "SOURCE_OBJECT_MISMATCH"
