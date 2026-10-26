# -*- coding: utf-8 -*-
"""Hybrid V2: distance between a line and a plane, and between two planes (run `hybrid-v2-nl-certificates-e2e`).

`/2` `distance` goals `{line, plane}` and `{plane1, plane2}` reach the registry asks `ask_distance_line_plane` /
`ask_distance_planes` (route B / `/4` only, `provider_offered=False`: route A's model surface is unchanged). The kernel
already measured both exactly (0 when the objects meet, also when the line lies in the plane); the engine cross-checks the
value with an independent Gram-determinant formula (`_kc2_duong_mat`, `_kc2_mat_mat`).

Closed-form oracles from the stated facts only (no engine coordinates):

- pyramid S.ABCD, square base of side s, SA ⊥ (ABCD), SA = h: AB ∥ (SCD) (AB ∥ CD), CD ⊥ (SAD) ⇒
  d²(AB, (SCD)) = d²(A, SD) = h²s²/(h²+s²), likewise d(AD, (SBC)) = d(A, SB); BC ∥ (SAD) and AB ⊥ (SAD) ⇒
  d(BC, (SAD)) = s, and CD ∥ (SAB) with AD ⊥ (SAB) ⇒ d(CD, (SAB)) = s; AB meets (SAD) at A ⇒ 0;
  (SAB) and (SCD) meet along the line through S parallel to AB ⇒ 0.
- right prism ABC.A'B'C' (right angle at A, AB = x, AC = y, AA' = h): d((ABC), (A'B'C')) = h;
  AA' ∥ (BCC'B') ⇒ d²(AA', (BCC'B')) = x²y²/(x²+y²); BB' ∥ (ACC'A') and AB ⊥ (ACC'A') ⇒ d(BB', (ACC'A')) = x.
- cuboid ABCD.A'B'C'D' (AB = a, AD = b, AA' = c): d((ABCD), (A'B'C'D')) = c, d((ABB'A'), (DCC'D')) = b,
  d((ADD'A'), (BCC'B')) = a, d(AA', (BCC'B')) = a, d(AB, (DCC'D')) = b.

Authored DEV cases by the implementing agent — not a holdout, not an extraction measurement, no provider call.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _square
from tests.geometry.test_typed_fact_next_v2_named_plane import _cuboid, _prism_goal, _pyramid

Q_LP = "Tính khoảng cách giữa đường thẳng {l} và mặt phẳng ({p})."
Q_PP = "Tính khoảng cách giữa hai mặt phẳng ({p}) và ({q})."


def _d2(p) -> F:
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "SERVED", (r.code, r.reason)
    return _square(r)


def _cub(target: dict, quote: str, **dims) -> dict:
    """A cuboid payload asking `target` by `quote` (the shared builder only words point/angle questions)."""
    p = _cuboid("angle", {"u": ["A", "B"], "v": ["A", "D"]}, **dims)
    old = p["math_goals"][0]["quote"]
    p["problem_text"] = p["problem_text"].replace(old, quote)
    p["math_goals"][0].update(goal_type="distance", target=target, quote=quote)
    return p


def _refused(p) -> str:
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "REFUSED", (r.status, r.answers)
    return r.code


# ── pyramid S.ABCD, SA ⊥ base ────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("s,h", [(4, 3), (6, 8), (5, 12), (2, 1)])
def test_pyramid_line_parallel_to_a_lateral_face(s, h):
    t = {"line": ["A", "B"], "plane": ["S", "C", "D"]}
    assert _d2(_pyramid("distance", t, s=s, h=h, quote=Q_LP.format(l="AB", p="SCD"))) == F(h * h * s * s, h * h + s * s)


@pytest.mark.parametrize("line,plane,d2", [
    (["C", "D"], ["S", "A", "B"], lambda s, h: F(s * s)),                               # CD ∥ (SAB), AD ⊥ (SAB)
    (["B", "C"], ["S", "A", "D"], lambda s, h: F(s * s)),                               # BC ∥ (SAD), AB ⊥ (SAD)
    (["A", "D"], ["S", "B", "C"], lambda s, h: F(h * h * s * s, h * h + s * s)),
    (["A", "B"], ["S", "A", "D"], lambda s, h: F(0)),                                   # AB meets (SAD) at A
    (["A", "B"], ["S", "A", "B"], lambda s, h: F(0)),                                   # AB lies in (SAB)
    (["S", "A"], ["A", "B", "C", "D"], lambda s, h: F(0)),                              # SA meets the base at A
])
def test_pyramid_line_plane_oracles(line, plane, d2):
    s, h = 4, 3
    q = Q_LP.format(l="".join(line), p="".join(plane))
    assert _d2(_pyramid("distance", {"line": line, "plane": plane}, s=s, h=h, quote=q)) == d2(s, h)


def test_pyramid_two_planes_meet_so_distance_is_zero():
    t = {"plane1": ["S", "A", "B"], "plane2": ["S", "C", "D"]}
    assert _d2(_pyramid("distance", t, quote=Q_PP.format(p="SAB", q="SCD"))) == 0


@pytest.mark.parametrize("labels", ["PKLMN", "OPQRT", "SABCD"])
def test_renamed_labels_follow_the_formula(labels):
    S, A, B, C, D = labels
    t = {"line": [A, B], "plane": [S, C, D]}
    assert _d2(_pyramid("distance", t, labels=labels, quote=Q_LP.format(l=A + B, p=S + C + D))) == F(9 * 16, 25)


@pytest.mark.parametrize("quote,target", [
    ("Tính khoảng cách giữa đường thẳng AB và mặt phẳng (SCD).", {"line": ["A", "B"], "plane": ["S", "C", "D"]}),
    ("Tính khoảng cách giữa AB và (SCD).", {"line": ["A", "B"], "plane": ["S", "C", "D"]}),
    ("Tính khoảng cách từ đường thẳng AB đến mặt phẳng (SCD).", {"line": ["A", "B"], "plane": ["S", "C", "D"]}),
    ("Tìm khoảng cách giữa AB và mp(SCD).", {"line": ["A", "B"], "plane": ["S", "C", "D"]}),
    ("Khoảng cách giữa đường thẳng AB và mặt phẳng (SCD) bằng bao nhiêu?", {"line": ["A", "B"], "plane": ["S", "C", "D"]}),
    ("Tính khoảng cách giữa mặt phẳng (SCD) và đường thẳng AB.", {"line": ["A", "B"], "plane": ["S", "C", "D"]}),
    ("Tính khoảng cách giữa đường thẳng BA và mặt phẳng (DSC).", {"line": ["A", "B"], "plane": ["S", "C", "D"]}),   # orders
])
def test_question_wordings_of_one_goal_agree(quote, target):
    assert _d2(_pyramid("distance", target, quote=quote)) == F(144, 25)


# ── right prism and cuboid ───────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("x,y,h", [(6, 8, 12), (3, 4, 5), (12, 16, 7)])
def test_prism_parallel_bases_and_lateral_edges(x, y, h):
    base = _prism_goal("distance", {"plane1": ["A", "B", "C"], "plane2": ["A'", "B'", "C'"]},
                       quote=Q_PP.format(p="ABC", q="A'B'C'"), x=x, y=y, h=h)
    assert _d2(base) == h * h
    edge = _prism_goal("distance", {"line": ["A", "A'"], "plane": ["B", "C", "C'", "B'"]},
                       quote="Tính khoảng cách giữa đường thẳng AA' và mặt phẳng (BCC'B').", x=x, y=y, h=h)
    assert _d2(edge) == F(x * x * y * y, x * x + y * y)
    other = _prism_goal("distance", {"line": ["B", "B'"], "plane": ["A", "C", "C'", "A'"]},
                        quote="Tính khoảng cách giữa đường thẳng BB' và mặt phẳng (ACC'A').", x=x, y=y, h=h)
    assert _d2(other) == x * x


@pytest.mark.parametrize("a,b,c", [(3, 4, 12), (5, 12, 7), (2, 2, 9)])
def test_cuboid_oracles(a, b, c):
    cases = [
        ({"plane1": ["A", "B", "C", "D"], "plane2": ["A'", "B'", "C'", "D'"]}, "Tính khoảng cách giữa hai mặt phẳng (ABCD) và (A'B'C'D').", c * c),
        ({"plane1": ["A", "B", "B'", "A'"], "plane2": ["D", "C", "C'", "D'"]}, "Tính khoảng cách giữa hai mặt phẳng (ABB'A') và (DCC'D').", b * b),
        ({"plane1": ["A", "D", "D'", "A'"], "plane2": ["B", "C", "C'", "B'"]}, "Tính khoảng cách giữa hai mặt phẳng (ADD'A') và (BCC'B').", a * a),
        ({"line": ["A", "A'"], "plane": ["B", "C", "C'", "B'"]}, "Tính khoảng cách giữa đường thẳng AA' và mặt phẳng (BCC'B').", a * a),
        ({"line": ["A", "B"], "plane": ["D", "C", "C'", "D'"]}, "Tính khoảng cách giữa đường thẳng AB và mặt phẳng (DCC'D').", b * b),
        ({"line": ["A'", "B'"], "plane": ["A", "B", "C", "D"]}, "Tính khoảng cách giữa đường thẳng A'B' và mặt phẳng (ABCD).", c * c),
        ({"line": ["A", "C"], "plane": ["A'", "B'", "C'", "D'"]}, "Tính khoảng cách giữa đường thẳng AC và mặt phẳng (A'B'C'D').", c * c),
    ]
    for target, quote, d2 in cases:
        assert _d2(_cub(target, quote, a=a, b=b, c=c)) == d2, quote


def test_scaling_the_pyramid_scales_the_squared_distance_by_four():
    t = {"line": ["A", "B"], "plane": ["S", "C", "D"]}
    q = Q_LP.format(l="AB", p="SCD")
    assert _d2(_pyramid("distance", t, s=8, h=6, quote=q)) == 4 * _d2(_pyramid("distance", t, s=4, h=3, quote=q))


# ── refusals: nothing is served for a different object, a clause that is not a question, or a malformed operand ─────────

@pytest.mark.parametrize("target,code", [
    ({"line": ["A", "D"], "plane": ["S", "C", "D"]}, "SOURCE_OBJECT_MISMATCH"),      # another line than the quote names
    ({"line": ["A", "B"], "plane": ["S", "B", "C"]}, "SOURCE_OBJECT_MISMATCH"),      # another plane than the quote names
    ({"line": ["A", "B", "C"], "plane": ["S", "C", "D"]}, "INVALID_MATH_GOAL"),      # a line is exactly two labels
    ({"line": ["A", "B"], "plane": ["S", "C"]}, "INVALID_MATH_GOAL"),                # a plane is three labels or more
    ({"line": ["A", "A"], "plane": ["S", "C", "D"]}, "INVALID_MATH_GOAL"),           # a repeated label
])
def test_wrong_object_or_operand_is_refused_with_its_code(target, code):
    assert _refused(_pyramid("distance", target, quote=Q_LP.format(l="AB", p="SCD"))) == code


def test_a_label_that_names_no_point_is_refused():
    t = {"line": ["A", "B"], "plane": ["S", "C", "X"]}
    assert _refused(_pyramid("distance", t, quote=Q_LP.format(l="AB", p="SCX"))) == "UNDERDETERMINED_POINT"


@pytest.mark.parametrize("quote,code", [
    ("Chứng minh rằng khoảng cách giữa đường thẳng AB và mặt phẳng (SCD) bằng 12/5.", "NOT_ASKED_IN_SOURCE"),
    ("Nếu khoảng cách giữa đường thẳng AB và mặt phẳng (SCD) bằng 12/5 thì SA = 3.", "NOT_ASKED_IN_SOURCE"),
    ("Khoảng cách giữa đường thẳng AB và mặt phẳng (SCD) bằng 12/5.", "NOT_ASKED_IN_SOURCE"),   # an assertion
    ("Khoảng cách giữa đường thẳng AB và mặt phẳng (SCD) không bằng 3.", "NOT_ASKED_IN_SOURCE"),
    ("Làm tròn khoảng cách giữa đường thẳng AB và mặt phẳng (SCD).", "NOT_ASKED_IN_SOURCE"),
    ("Tính bình phương khoảng cách giữa AB và (SCD).", "NOT_ASKED_IN_SOURCE"),             # another quantity
    ("Tính khoảng cách giữa AB và (SCD) và (SAD).", "NOT_ASKED_IN_SOURCE"),                # a second, unread object
    ("Tính khoảng cách giữa AB và (SCD) rồi nhân đôi.", "QUESTION_CONTEXT_UNSUPPORTED"),   # a changed request
])
def test_not_a_question_clause_is_refused_with_its_code(quote, code):
    assert _refused(_pyramid("distance", {"line": ["A", "B"], "plane": ["S", "C", "D"]}, quote=quote)) == code


def test_a_fourth_label_off_the_plane_is_refused():
    t = {"line": ["A", "B"], "plane": ["S", "C", "D", "A"]}
    assert _refused(_pyramid("distance", t, quote="Tính khoảng cách giữa đường thẳng AB và mặt phẳng (SCDA).")) == "SOURCE_OBJECT_MISMATCH"


def test_collinear_plane_labels_are_refused():
    p = _cub({"line": ["C", "D"], "plane": ["A", "B", "A"]}, "Tính khoảng cách giữa đường thẳng CD và mặt phẳng (ABA).")
    assert _refused(p) == "INVALID_MATH_GOAL"                                  # repeated label: not a plane
    p = _cub({"line": ["C", "D"], "plane": ["A", "B", "C", "D", "A'"]},
             "Tính khoảng cách giữa đường thẳng CD và mặt phẳng (ABCDA').")
    assert _refused(p) == "SOURCE_OBJECT_MISMATCH"                             # A' is off the plane ABCD


def test_route_a_provider_surface_is_unchanged():
    """New asks are route B only: they are not offered to the route A provider."""
    from app.simulation.geometry_functions import function_declarations
    names = {d["name"] for d in function_declarations()}
    assert "ask_distance_line_plane" not in names and "ask_distance_planes" not in names


# ── fault injection: the engine cross-check and the kernel must agree, or nothing is served ─────────────────────────

def test_kernel_value_that_disagrees_with_the_gram_check_is_refused(monkeypatch):
    from app.simulation.geometry import measure as M
    from app.simulation.semantic_program import geometry_exec as GE

    real = M.distance_sq_line_plane
    monkeypatch.setattr(GE.M, "distance_sq_line_plane", lambda a, b: real(a, b) + 1)
    r = run_typed_fact_next_v2_route(_pyramid("distance", {"line": ["A", "B"], "plane": ["S", "C", "D"]}, quote=Q_LP.format(l="AB", p="SCD")))
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED", (r.status, r.code)


def test_plane_plane_kernel_fault_is_refused(monkeypatch):
    from app.simulation.semantic_program import geometry_exec as GE

    real = GE.M.distance_sq_planes
    monkeypatch.setattr(GE.M, "distance_sq_planes", lambda a, b: real(a, b) + 1)
    p = _prism_goal("distance", {"plane1": ["A", "B", "C"], "plane2": ["A'", "B'", "C'"]}, quote=Q_PP.format(p="ABC", q="A'B'C'"))
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED", (r.status, r.code)


def test_gram_check_fault_is_caught_by_disagreement(monkeypatch):
    from app.simulation.geometry_functions import engine as E

    monkeypatch.setattr(E._Dung, "_kc2_duong_mat", lambda self, line, mp: F(-1))
    r = run_typed_fact_next_v2_route(_pyramid("distance", {"line": ["A", "B"], "plane": ["S", "C", "D"]}, quote=Q_LP.format(l="AB", p="SCD")))
    assert r.status == "REFUSED" and r.code == "ENGINE_SELF_CHECK_FAILED"
