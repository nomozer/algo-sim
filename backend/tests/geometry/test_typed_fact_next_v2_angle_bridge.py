# -*- coding: utf-8 -*-
"""Hybrid V2 (`scene3d-to-hybrid-v2-replacement`): canonical `measurement` goals with `goal_type: "angle"` reach the ONE
planner/engine through the `/4` bridge — before this, every angle goal was `BRIDGE_UNSUPPORTED_MEASUREMENT`.

Target keys: `{line, plane}` and `{line1, line2}` (what `adapter3_simulation` reads) plus `{plane1, plane2}` (the
planner's dihedral question). The answer is cos² — exact. Closed-form oracles from the stated facts of a triangular prism
ABC.A'B'C' with a right angle at A, AB = x, AC = y (independent of engine layout):

- right prism, AA' = h: cos²(A'C, (ABC)) = y²/(y²+h²); cos²(AA', BC) = 0; cos²((A'BC), (ABC)) = d²/(d²+h²),
  d² = x²y²/(x²+y²) (the base altitude from A);
- oblique prism, A' over the midpoint H of BC, AA' = l: cos²(AA', (ABC)) = ((x²+y²)/4)/l².

Authored development cases — not a holdout, not an extraction-quality measurement.
"""
from __future__ import annotations

from fractions import Fraction as F

import pytest

from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
from tests.geometry.test_typed_fact_next_v2_distance_bridge import _prism


def _ten(v) -> str:
    return "".join(v) if len(v) == 2 else "(" + "".join(v) + ")"


def _angle(target, *prism_args, **prism_kw):
    """A prism whose ONLY question is this angle. The question must NAME its objects — the Source Gate refuses an
    anonymous "tính góc" and a problem whose other question is left unanswered."""
    quote = "Tính góc giữa " + " và ".join(
        ("đường thẳng " if len(v) == 2 else "mặt phẳng ") + _ten(v) for v in target.values()) + "."
    p = _prism(*prism_args, ask=(quote, target), **prism_kw)
    p["math_goals"][0]["goal_type"] = "angle"
    return p


def _cos2(p) -> F:
    r = run_typed_fact_next_v2_route(p)
    assert r.status == "SERVED", (r.code, r.reason)
    return F(r.exec_result.final_memory["kq_q"])


@pytest.mark.parametrize("labels,x,y,h", [("ABC", 6, 8, 12), ("DEF", 3, 4, 5), ("KLM", 12, 16, 7)])
def test_line_plane_angle_of_a_right_prism(labels, x, y, h):
    a, b, c = labels
    p = _angle({"line": [a + "'", c], "plane": [a, b, c]}, labels, x, y, h)
    assert _cos2(p) == F(y * y, y * y + h * h)


def test_lateral_edge_and_base_edge_are_perpendicular_lines():
    assert _cos2(_angle({"line1": ["A", "A'"], "line2": ["B", "C"]})) == 0


def test_dihedral_angle_along_the_base_edge():
    x, y, h = 6, 8, 12
    d2 = F(x * x * y * y, x * x + y * y)
    assert _cos2(_angle({"plane1": ["A'", "B", "C"], "plane2": ["A", "B", "C"]}, x=x, y=y, h=h)) == d2 / (d2 + h * h)


@pytest.mark.parametrize("labels,x,y,h", [("ABC", 6, 8, 12), ("DEF", 12, 16, 24)])
def test_oblique_lateral_edge_angle_uses_the_true_foot(labels, x, y, h):
    a, b, c = labels
    p = _angle({"line": [a, a + "'"], "plane": [a, b, c]}, labels, x, y, h, oblique=True)
    l2 = F(h * h) + F(x * x + y * y, 4)
    assert _cos2(p) == F(x * x + y * y, 4) / l2


def test_operand_order_of_line_and_plane_does_not_matter():
    a = _cos2(_angle({"line": ["A'", "C"], "plane": ["A", "B", "C"]}))
    b = _cos2(_angle({"line": ["C", "A'"], "plane": ["C", "A", "B"]}))
    assert a == b == F(64, 64 + 144)


def test_angle_is_scale_invariant():
    assert _cos2(_angle({"line": ["A'", "C"], "plane": ["A", "B", "C"]}, x=12, y=16, h=24)) == \
        _cos2(_angle({"line": ["A'", "C"], "plane": ["A", "B", "C"]}, x=6, y=8, h=12))


@pytest.mark.parametrize("target", [
    {"line": ["A", "A"], "plane": ["A", "B", "C"]},                 # degenerate line [A, A]
    {"line": ["A'", "C"], "plane": ["A", "B", "C", "A"]},           # repeated / four-label plane — never truncated
    {"line": ["A'", "C"], "plane": ["A", "B", "C", "B'"]},          # a non-coplanar fourth label is not silently dropped
    {"line": ["A'"], "plane": ["A", "B", "C"]},                     # one-point line
    {"line1": ["A", "A'"]},                                          # missing operand
    {"segment": ["A", "B"]},                                         # a distance key on an angle goal
])
def test_malformed_angle_targets_are_refused_with_a_code(target):
    r = run_typed_fact_next_v2_route(_angle(target))
    assert (r.status, r.code) == ("REFUSED", "INVALID_MATH_GOAL")


def test_angle_on_a_line_lying_in_the_plane_is_served_as_cos2_1():
    """AB lies in (ABC): the angle is 0, cos² = 1 — a true answer, not a refusal."""
    assert _cos2(_angle({"line": ["A", "B"], "plane": ["A", "B", "C"]})) == 1


def test_adapter4_envelope_is_served_for_an_angle_goal():
    p = _angle({"line": ["A'", "C"], "plane": ["A", "B", "C"]})
    rd = build_adapter4_response(run_typed_fact_next_v2_route(p), p["problem_text"])["route_d"]
    assert rd["status"] == "SERVED", rd
    prov = next(x for x in rd["source_provenance"] if x["id"] == "q")
    assert (prov["fn"], prov["args"]) == ("ask_angle_line_plane", {"line": ["A'", "C"], "plane": ["A", "B", "C"]})
