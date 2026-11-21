# -*- coding: utf-8 -*-
"""verified-section-intersection-dihedral-local — sections, intersection lines and altitudes on the LOCAL route.

Vietnamese text → local parser → TypedFactNext/2 → bridge → Source Gate → planner → engine → Scene3D, no AI call.
Section polygons are checked against the INDEPENDENT oracle of `test_hybrid4_three_point_plane_sections` (hand
coordinates, edge–plane intersections, cross-sum area — it never reads engine output). Intersection lines and altitudes
are checked by exact arithmetic written here. Counterexamples must stay unserved.
"""
from __future__ import annotations

import os
from fractions import Fraction as F

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.simulation.geometry.exact import Vec3
from app.simulation.semantic_program import quantity_annotations as QA
from tests.geometry.test_hybrid4_three_point_plane_sections import oracle_section, prism_edges, pyramid_edges

os.environ.setdefault("ALLOW_LIVE_AI", "0")
P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
CUBE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. "
PYR = {"A": (0, 0, 0), "B": (1, 0, 0), "C": (1, 1, 0), "D": (0, 1, 0), "S": (0, 0, 1)}
CUB = {"A": (0, 0, 0), "B": (1, 0, 0), "C": (1, 1, 0), "D": (0, 1, 0),
       "A_prime": (0, 0, 1), "B_prime": (1, 0, 1), "C_prime": (1, 1, 1), "D_prime": (0, 1, 1)}


def _serve(text):
    r = route_text_input(text, allow_live_ai=False).response
    return (r.get("route_d") or {}), r


def _mid(a, b):
    return tuple(F(x + y, 2) for x, y in zip(a, b))


@pytest.mark.parametrize("text,coords,edges,plane", [
    (CUBE + "Gọi M, N lần lượt là trung điểm của AB và AD. Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (MNC').",
     CUB, prism_edges(["A", "B", "C", "D"], ["A_prime", "B_prime", "C_prime", "D_prime"]),
     (_mid(CUB["A"], CUB["B"]), _mid(CUB["A"], CUB["D"]), CUB["C_prime"])),
    (P + "Gọi M là trung điểm của SC. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (ABM).",
     PYR, pyramid_edges("S", "ABCD"), (PYR["A"], PYR["B"], _mid(PYR["S"], PYR["C"]))),
    (CUBE + "Xác định thiết diện của hình lập phương cắt bởi mặt phẳng (A'BD).",
     CUB, prism_edges(["A", "B", "C", "D"], ["A_prime", "B_prime", "C_prime", "D_prime"]), (CUB["A_prime"], CUB["B"], CUB["D"])),
    (CUBE + "Gọi M, N, P lần lượt là trung điểm của AB, BC và CC'. Tìm thiết diện của hình lập phương cắt bởi mặt phẳng (MNP).",
     CUB, prism_edges(["A", "B", "C", "D"], ["A_prime", "B_prime", "C_prime", "D_prime"]),
     (_mid(CUB["A"], CUB["B"]), _mid(CUB["B"], CUB["C"]), _mid(CUB["C"], CUB["C_prime"]))),
])
def test_section_from_local_text_matches_the_independent_oracle(text, coords, edges, plane):
    rd, r = _serve(text)
    assert rd.get("status") == "SERVED"
    sec = next(o for o in r["envelope"]["scene3d"]["objects"] if o["type"] == "section")
    poly = [tuple(F(x) for x in p) for p in sec["polygon"]]
    want = oracle_section(coords, edges, plane)
    assert len(poly) == want["vertices"] and len(set(poly)) == len(poly)
    s = (F(0), F(0), F(0))
    for i in range(len(poly)):          # same cross-sum area as the oracle ⇒ same vertex set in a simple cyclic order
        a, b = poly[i], poly[(i + 1) % len(poly)]
        s = tuple(x + y for x, y in zip(s, (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])))
    assert sum(x * x for x in s) / 4 == want["area2"]


def test_section_area_goal_is_read_once_and_matches_the_hand_value():
    rd, _ = _serve(P + "Gọi M là trung điểm của SC. Tính diện tích thiết diện của hình chóp cắt bởi mặt phẳng (ABM).")
    assert rd["status"] == "SERVED" and rd["answers"] == {"q1": "3a²√2/8"}      # right trapezoid (a + a/2)/2 · a√2/2


@pytest.mark.parametrize("text,code", [
    (P + "Gọi M là trung điểm của AC. Xác định thiết diện của hình chóp cắt bởi mặt phẳng (AMC).", "COLLINEAR_POINTS"),
    (P + "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (XYZ).", None),
    (P + "Xác định thiết diện của hình chóp T.ABCD cắt bởi mặt phẳng (SAB).", None),   # not the declared solid
    (P + "Gọi M là trung điểm của SC. Mặt phẳng (ABM) cắt hình chóp theo thiết diện là hình gì?", None),  # goal-as-premise
])
def test_section_counterexamples_are_not_served(text, code):
    rd, r = _serve(text)
    assert rd.get("status") != "SERVED"
    if code:
        assert (rd.get("refusal") or {}).get("code") == code


def test_renamed_section_problem_gives_the_same_polygon():
    a = _serve(P + "Gọi M là trung điểm của SC. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (ABM).")[1]
    b = _serve("Cho hình chóp T.MNPQ có đáy MNPQ là hình vuông cạnh a, TM vuông góc với mặt phẳng đáy và TM = a. "
               "Gọi K là trung điểm của TP. Dựng thiết diện của hình chóp cắt bởi mặt phẳng (MNK).")[1]
    pa, pb = ([o for o in x["envelope"]["scene3d"]["objects"] if o["type"] == "section"][0]["polygon"] for x in (a, b))
    assert pa == pb


# ── intersection lines ────────────────────────────────────────────────────────────────────────────────────────────────
def _line(text):
    rd, r = _serve(text)
    assert rd.get("status") == "SERVED", rd.get("refusal")
    ln = next(o for o in r["envelope"]["scene3d"]["objects"] if o.get("producer") == "intersect_plane_plane")
    return Vec3.of(*(F(x) for x in ln["point"])), Vec3.of(*(F(x) for x in ln["direction"]))


def _in_plane(p, a, b, c):
    n = (b - a).cross(c - a)
    return n.dot(p - a) == 0


@pytest.mark.parametrize("text,pa,pb", [
    (P + "Xác định giao tuyến của hai mặt phẳng (SAB) và (SCD).", "SAB", "SCD"),
    (P + "Tìm giao tuyến của hai mặt phẳng (SAC) và (SBD).", "SAC", "SBD"),
    (P + "Gọi d là giao tuyến của (SAB) và (SCD).", "SAB", "SCD"),
    (P + "Dựng giao tuyến của mặt phẳng (SAD) và mặt phẳng (SBC).", "SAD", "SBC"),
])
def test_intersection_line_lies_in_both_planes(text, pa, pb):
    p0, d = _line(text)
    v = {k: Vec3.of(*x) for k, x in PYR.items()}
    for name in (pa, pb):
        a, b, c = (v[x] for x in name)
        assert _in_plane(p0, a, b, c) and _in_plane(p0 + d, a, b, c)       # a point and the direction lie in the plane
    assert not d.is_zero()


@pytest.mark.parametrize("text,code", [
    (CUBE + "Xác định giao tuyến của hai mặt phẳng (ABC) và (A'B'C').", "PARALLEL_PLANES"),
    (CUBE + "Xác định giao tuyến của hai mặt phẳng (ABC) và (ACD).", None),       # the same plane: no line
])
def test_parallel_or_coincident_planes_have_no_intersection_line(text, code):
    rd, _ = _serve(text)
    assert rd.get("status") != "SERVED"
    if code:
        assert (rd.get("refusal") or {}).get("code") == code


def test_intersection_goal_is_never_a_premise_and_needs_two_distinct_planes():
    r = parse_geometry_problem_locally(P + "Xác định giao tuyến của hai mặt phẳng (SAB) và (SBA).", use_cache=False)
    assert not any(g.get("kind") == "construct_intersection_line" for g in (r.payload or {}).get("simulation_goals", []))
    r = parse_geometry_problem_locally(P + "Xác định giao tuyến của hai mặt phẳng (SAB) và (SCD).", use_cache=False)
    goals = [g for g in r.payload["simulation_goals"] if g["kind"] == "construct_intersection_line"]
    assert len(goals) == 1 and not any("giao tuyến" in p["quote"] for p in r.payload["premises"])


# ── altitude from a lateral face perpendicular to the base ────────────────────────────────────────────────────────────
def _altitude(text):
    rd, r = _serve(text)
    assert rd["status"] == "SERVED"
    sc = r["envelope"]["scene3d"]
    q = next(o for o in sc["objects"] if o["type"] == "quantity" and "target" in (o.get("display_group") or []))
    g = [[F(x) for x in row] for row in sc["chart_metric"]]
    pts = {o["id"]: [F(x) for x in o["xyz"]] for o in sc["objects"] if o["type"] == "point3"}
    return q.get("altitude_construction"), g, pts


def _gdot(g, u, w):
    return sum(u[i] * g[i][j] * w[j] for i in range(3) for j in range(3))


def test_face_perpendicular_base_altitude_foot_is_the_projection_on_the_common_line():
    ac, g, pts = _altitude("Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, tam giác SAB đều và nằm trong mặt phẳng "
                           "vuông góc với mặt phẳng đáy. Tính thể tích khối chóp S.ABCD.")
    assert ac and ac["base_edge"] == ["A", "B"] and ac["foot_on_edge_segment"] is True
    h, s = [F(x) for x in ac["foot"]], [F(x) for x in ac["from"]]
    leg = [x - y for x, y in zip(s, h)]
    for e in (("A", "B"), ("A", "D")):                                     # SH ⟂ base in the frame metric
        assert _gdot(g, leg, [x - y for x, y in zip(pts[e[1]], pts[e[0]])]) == 0
    ab = [x - y for x, y in zip(pts["B"], pts["A"])]
    ah = [x - y for x, y in zip(h, pts["A"])]
    assert ab[0] * ah[1] - ab[1] * ah[0] == 0 and ab[1] * ah[2] - ab[2] * ah[1] == 0          # H on line AB
    assert h == [(a + b) / 2 for a, b in zip(pts["A"], pts["B"])]           # SA = SB (equilateral) ⇒ midpoint, derived


@pytest.mark.parametrize("text", [
    P + "Tính thể tích khối chóp S.ABCD.",                                  # SA is already the drawn altitude
    "Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, hình chiếu vuông góc của S lên mặt phẳng (ABC) trùng với "
    "trọng tâm G của tam giác ABC, SA = 2a. Tính thể tích khối chóp S.ABC.",  # SG is already drawn
])
def test_no_second_altitude_when_one_is_already_drawn(text):
    ac, _, _ = _altitude(text)
    assert ac is None


def test_altitude_foot_outside_the_edge_segment_is_kept_on_the_line():
    mem = {"A": Vec3.of(0, 0, 0), "B": Vec3.of(1, 0, 0), "C": Vec3.of(1, 1, 0), "D": Vec3.of(0, 1, 0), "S": Vec3.of(-1, 0, 2)}
    ac = QA._dung_duong_cao("S", ["A", "B", "C", "D"], "day", mem, {k: v for k, v in mem.items()})
    assert ac["base_edge"] == ["A", "B"] and ac["foot_on_edge_segment"] is False and ac["foot"] == ["-1", "0", "0"]


def test_non_perpendicular_face_gives_a_plain_altitude_without_a_face_claim():
    mem = {"A": Vec3.of(0, 0, 0), "B": Vec3.of(2, 0, 0), "C": Vec3.of(2, 2, 0), "D": Vec3.of(0, 2, 0), "S": Vec3.of(1, 1, 3)}
    ac = QA._dung_duong_cao("S", ["A", "B", "C", "D"], "day", mem, dict(mem))
    assert "base_edge" not in ac and "face_perpendicular_to_base" not in ac["checks"] and ac["foot"] == ["1", "1", "0"]


def test_apex_in_the_base_plane_has_no_altitude():
    mem = {"A": Vec3.of(0, 0, 0), "B": Vec3.of(2, 0, 0), "C": Vec3.of(2, 2, 0), "D": Vec3.of(0, 2, 0), "S": Vec3.of(1, 1, 0)}
    assert isinstance(QA._dung_duong_cao("S", ["A", "B", "C", "D"], "day", mem, dict(mem)), str)
