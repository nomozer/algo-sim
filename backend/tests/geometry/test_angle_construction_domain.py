# -*- coding: utf-8 -*-
"""verified-section-intersection-dihedral-local — the drawn angle must BE the asked angle, not its supplement.

Every supported angle ask (lines, line–plane, planes) is the non-oriented angle in [0°, 90°] (measure.degrees, SGK).
cos² alone cannot tell 60° from 120° (cos² = 1/4 for both): a construction whose rays meet at 120° passed the old
cos²-only check. These tests recompute the SIGNED cosine of the drawn rays independently (Fractions + the envelope's
own Gram matrix) and require it to be ≥ 0 and to square to the measured value.
"""
from __future__ import annotations

import os
from fractions import Fraction

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.simulation.geometry.exact import Line3, Plane3, Vec3
from app.simulation.semantic_program import quantity_annotations as QA

os.environ.setdefault("ALLOW_LIVE_AI", "0")
P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
CUBE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. "


def _signed(text: str) -> tuple[Fraction, Fraction, dict]:
    r = route_text_input(text, allow_live_ai=False).response
    rd = r["route_d"]
    assert rd["status"] == "SERVED", rd.get("refusal")
    sc = r["envelope"]["scene3d"]
    g = [[Fraction(x) for x in row] for row in sc["chart_metric"]]
    q = next(o for o in sc["objects"] if o.get("angle_construction"))
    ac = q["angle_construction"]
    v = [Fraction(x) for x in ac["vertex"]]
    a, b = ([Fraction(x) - y for x, y in zip(arm["to"], v)] for arm in ac["arms"])
    dot = lambda u, w: sum(u[i] * g[i][j] * w[j] for i in range(3) for j in range(3))  # noqa: E731
    cos2 = dot(a, b) ** 2 / (dot(a, a) * dot(b, b))
    return dot(a, b), cos2, ac


@pytest.mark.parametrize("text", [
    P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (SCD).",        # dihedral B-SC-D is 120°, the planes meet at 60°
    P + "Tính góc giữa mặt phẳng (SCD) và mặt phẳng (SBC).",        # plane order swapped
    P + "Tính góc giữa mặt phẳng (SAB) và mặt phẳng (SCD).",
    P + "Tính góc giữa mặt phẳng (SBD) và mặt phẳng (SCD).",
    P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (ABCD).",
    CUBE + "Tính góc giữa mặt phẳng (A'BD) và mặt phẳng (C'BD).",
    CUBE + "Tính góc giữa mặt phẳng (A'BD) và mặt phẳng (ABCD).",
    P + "Tính góc giữa hai đường thẳng SB và SD.",
    P + "Tính góc giữa hai đường thẳng SB và CD.",
    P + "Tính góc giữa hai đường thẳng SC và AD.",
    CUBE + "Tính góc giữa hai đường thẳng AC và DA'.",
    P + "Tính góc giữa đường thẳng SC và mặt phẳng (ABCD).",
])
def test_drawn_angle_is_never_the_obtuse_supplement(text):
    dot, cos2, ac = _signed(text)
    measured = Fraction(route_text_input(text, allow_live_ai=False).response["route_d"]["answers"]["q1"].split("=")[1])
    assert dot >= 0, f"drawn rays meet at an obtuse angle ({ac['relation']})"
    assert cos2 == measured
    assert ac.get("angle_domain") == "[0°, 90°]"


def test_renamed_vertices_keep_the_acute_construction():
    a = _signed(P + "Tính góc giữa mặt phẳng (SBC) và mặt phẳng (SCD).")
    b = _signed("Cho hình chóp T.MNPQ có đáy MNPQ là hình vuông cạnh a, TM vuông góc với mặt phẳng đáy và TM = a. "
                "Tính góc giữa mặt phẳng (TNP) và mặt phẳng (TPQ).")
    assert a[0] >= 0 and b[0] >= 0 and a[1] == b[1] and a[2]["vertex"] == b[2]["vertex"]


# ── synthetic 60° / 120° pair: same cos², opposite sign — the construction must draw the 60° one ────────────────────
def _mem_planes(theta_obtuse: bool):
    """Two half-planes on the x-axis edge: (xy) and a plane at 120° or 60° to it, with one named point in each."""
    o = Vec3.of(0, 0, 0)
    e = Vec3.of(1, 0, 0)
    p1 = Vec3.of(0, 1, 0)                                         # in plane z = 0
    p2 = Vec3.of(0, -1, 1) if theta_obtuse else Vec3.of(0, 1, 1)  # half-plane at 135° or 45° (cos² = 1/2 both)
    mem = {"O": o, "E": o + e, "P1": p1, "P2": p2,
           "m1": Plane3.through(o, o + e, p1), "m2": Plane3.through(o, o + e, p2)}
    return mem, [("O", o), ("E", o + e), ("P1", p1), ("P2", p2)]


@pytest.mark.parametrize("obtuse_named_point", [False, True])
def test_plane_angle_is_acute_even_when_the_named_points_open_an_obtuse_dihedral(obtuse_named_point):
    mem, co_ten = _mem_planes(obtuse_named_point)
    ac = QA._dung_goc("m1", "m2", Fraction(1, 2), mem, {}, co_ten)
    assert isinstance(ac, dict)
    v = Vec3.of(*(Fraction(x) for x in ac["vertex"]))
    a, b = (Vec3.of(*(Fraction(x) for x in arm["to"])) - v for arm in ac["arms"])
    assert a.dot(b) > 0 and a.dot(Vec3.of(1, 0, 0)) == 0 and b.dot(Vec3.of(1, 0, 0)) == 0
    assert mem["m2"].signed_eval(Vec3.of(*(Fraction(x) for x in ac["arms"][1]["to"]))) == 0      # still in plane 2


def test_wrong_cos_sign_is_not_a_valid_construction_value():
    """cos² = 1/4 means 60° here; a construction of 60° must not be accepted for a 1/2 measurement and vice versa."""
    mem, co_ten = _mem_planes(True)
    assert isinstance(QA._dung_goc("m1", "m2", Fraction(1, 4), mem, {}, co_ten), str)


def test_lines_whose_named_points_open_an_obtuse_angle_are_drawn_acute():
    o = Vec3.of(0, 0, 0)
    mem = {"O": o, "A": Vec3.of(1, 0, 0), "B": Vec3.of(-1, 1, 0),        # ∠AOB = 135°, lines meet at 45°
           "l1": Line3.through(o, Vec3.of(1, 0, 0)), "l2": Line3.through(o, Vec3.of(-1, 1, 0))}
    ac = QA._dung_goc("l1", "l2", Fraction(1, 2), mem, {}, [("O", o), ("A", mem["A"]), ("B", mem["B"])])
    v = Vec3.of(*(Fraction(x) for x in ac["vertex"]))
    a, b = (Vec3.of(*(Fraction(x) for x in arm["to"])) - v for arm in ac["arms"])
    assert a.dot(b) > 0 and ac["relation"] == "line_line"


def test_coincident_and_parallel_planes_have_no_construction():
    mem, co_ten = _mem_planes(False)
    mem["m3"] = Plane3.through(Vec3.of(0, 0, 5), Vec3.of(1, 0, 5), Vec3.of(0, 1, 5))   # parallel to m1
    with pytest.raises(Exception):
        QA._dung_goc("m1", "m3", Fraction(1), mem, {}, co_ten)
    with pytest.raises(Exception):
        QA._dung_goc("m1", "m1", Fraction(1), mem, {}, co_ten)
