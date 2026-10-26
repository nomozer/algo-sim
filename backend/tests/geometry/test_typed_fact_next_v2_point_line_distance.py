# -*- coding: utf-8 -*-
"""Hybrid V2 point–line distance (`hybrid-v2-backend-generalization`, second slice): a canonical `/2` distance goal
`{point, line}` reaches the planner's existing decomposition — the foot of the perpendicular is constructed on a fresh
auxiliary label by `orthogonal_projection_line`, the engine checks it (foot on the line, segment ⊥ line) and measures the
segment. Before, the bridge refused this target (`INVALID_MATH_GOAL`) although route B already served it.

Closed-form oracles from the stated facts only (no engine coordinates):

- right prism ABC.A'B'C', right angle at A, AB = x, AC = y, AA' = h: d²(A, BC) = x²y²/(x²+y²);
  d²(A', BC) = h² + x²y²/(x²+y²) (three perpendiculars: the foot is the foot of A);
- pyramid S.ABCD, square base of side s, SA ⊥ (ABCD), SA = h: d²(A, SB) = h²s²/(h²+s²); d²(S, BD) = h² + s²/2;
  d²(A, SC) = 2h²s²/(h²+2s²);
- regular pyramid S.ABCD, base side s, lateral edge l: d²(A, SC) = AC²·sin²(ACS) = 2s² − s⁴/l²;
- cuboid ABCD.A'B'C'D', AB = a, AD = b, AA' = c: d²(A', BD) = c² + a²b²/(a²+b²).

Authored development cases — not a holdout, not an extraction-quality measurement, no provider call.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from tests.geometry.test_typed_fact_next_v2_named_plane import (_cuboid, _d2, _prism_goal, _pyramid, _refused, _regular,
                                                                 _served)


def _q(point, line):
    return f"Tính khoảng cách từ {point} đến đường thẳng {''.join(line)}."


def _prism(point, line, **kw):
    return _prism_goal("distance", {"point": point, "line": line}, quote=_q(point, line), **kw)


@pytest.mark.parametrize("labels,x,y,h", [("ABC", 6, 8, 12), ("DEF", 3, 4, 5), ("KLM", 12, 16, 7)])
def test_right_prism_base_altitude(labels, x, y, h):
    a, b, c = labels
    assert _d2(_prism(a, [b, c], labels=labels, x=x, y=y, h=h)) == F(x * x * y * y, x * x + y * y)


@pytest.mark.parametrize("x,y,h", [(6, 8, 12), (3, 4, 5)])
def test_right_prism_three_perpendiculars(x, y, h):
    assert _d2(_prism("A'", ["B", "C"], x=x, y=y, h=h)) == h * h + F(x * x * y * y, x * x + y * y)


def test_line_order_does_not_matter():
    assert _d2(_prism("A'", ["C", "B"])) == _d2(_prism("A'", ["B", "C"]))


def test_scale_multiplies_the_squared_distance_by_four():
    assert _d2(_prism("A'", ["B", "C"], x=12, y=16, h=24)) == 4 * _d2(_prism("A'", ["B", "C"]))


@pytest.mark.parametrize("s,h", [(4, 3), (2, 5)])
def test_pyramid_sa_perpendicular_base(s, h):
    t = lambda p, ln: _pyramid("distance", {"point": p, "line": ln}, s=s, h=h, quote=_q(p, ln))
    assert _d2(t("A", ["S", "B"])) == F(h * h * s * s, h * h + s * s)
    assert _d2(t("S", ["B", "D"])) == h * h + F(s * s, 2)
    assert _d2(t("A", ["S", "C"])) == F(2 * h * h * s * s, h * h + 2 * s * s)


@pytest.mark.parametrize("s,l", [(4, 3), (2, 3)])
def test_regular_pyramid_vertex_to_opposite_lateral_edge(s, l):
    assert _d2(_regular("distance", {"point": "A", "line": ["S", "C"]}, s, l)) == 2 * s * s - F(s ** 4, l * l)


def test_cuboid_top_vertex_to_base_diagonal():
    assert _d2(_cuboid("distance", {"point": "A'", "line": ["B", "D"]}, 3, 4, 12)) == 144 + F(144, 25)


def test_the_foot_is_a_fresh_auxiliary_label_and_the_answer_is_certified():
    r = _served(_prism("A", ["B", "C"]))
    rd = build_adapter4_response(r, _prism("A", ["B", "C"])["problem_text"])["route_d"]
    assert rd["status"] == "SERVED", rd
    feet = [c for c in r.planner["calls"] if c["fn"] == "orthogonal_projection_line"]
    assert len(feet) == 1 and feet[0]["args"]["point"] == "A" and sorted(feet[0]["args"]["line"]) == ["B", "C"]
    assert feet[0]["args"]["image"] not in r.planner["calls"][0].get("args", {}).values()
    assert feet[0]["args"]["image"] not in _prism("A", ["B", "C"])["problem_text"]


def test_a_text_that_already_uses_h_gets_another_foot_label():
    """The oblique prism text names H (midpoint of BC); the foot must not reuse it."""
    r = _served(_prism("A", ["B'", "C'"], oblique=True))
    feet = [c["args"]["image"] for c in r.planner["calls"] if c["fn"] == "orthogonal_projection_line"]
    assert feet and "H" not in feet


# ── refused ────────────────────────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("target", [{"point": "A", "line": ["B", "B"]}, {"point": "A", "line": ["B"]},
                                    {"point": "A", "line": ["B", "C", "C'"]}, {"point": ["A"], "line": ["B", "C"]},
                                    {"point": "A", "line": ["B", "C"], "plane": ["A", "B", "C"]}])
def test_malformed_point_line_targets_stay_invalid(target):
    p = _prism_goal("distance", target, quote="Tính khoảng cách từ A đến đường thẳng BC.")
    assert _refused(p) == "INVALID_MATH_GOAL"


def test_quote_naming_another_line_is_refused():
    p = _prism_goal("distance", {"point": "A", "line": ["B", "C"]}, quote=_q("A", ["B", "C'"]))
    assert _refused(p) == "SOURCE_OBJECT_MISMATCH"


def test_unknown_point_is_refused():
    """X is named only by the question: nothing determines it, so no coordinate is invented."""
    assert _refused(_prism("X", ["B", "C"])) == "UNDERDETERMINED_POINT"


def test_a_point_on_the_line_is_served_as_zero():
    """B lies on BC: the true distance is 0 (same convention as a line lying in a plane: cos² = 1), never positive."""
    assert _d2(_prism("B", ["B", "C"])) == 0
