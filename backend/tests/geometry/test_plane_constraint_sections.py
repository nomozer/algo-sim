# -*- coding: utf-8 -*-
"""Constraint-defined planes on the local route (run `independent-geometry-plane-constraints`).

Every served section is checked against a vertex set written here by hand as combinations of the scene's own labelled
points (midpoints, vertices) — never read from the product's section code. Refusals: degenerate, underdetermined and
contradictory definitions, an undefined plane name, coincident vs parallel planes, and a dihedral question substituted
into a plane–plane angle payload.
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction as F

import pytest

from app.ai.adaptive_input_router import route_text_input
from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.local_geometry_parser import parse_geometry_problem_locally
from app.simulation.geometry_functions import registry as R

P = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với mặt phẳng đáy và SA = a. "
REN = "Cho hình chóp T.MNPQ có đáy MNPQ là hình vuông cạnh a, TM vuông góc với mặt phẳng đáy và TM = a. "
CUBE = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a. "
SEC = "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (P)."


def _serve(text):
    r = route_text_input(text, allow_live_ai=False).response
    return r.get("route_d") or {}, r


def _section(text):
    rd, r = _serve(text)
    assert rd.get("status") == "SERVED", (rd.get("refusal"), r.get("reason_code"))
    sc = r["envelope"]["scene3d"]
    pts = {o["id"].replace("_prime", "'"): tuple(F(x) for x in o["xyz"]) for o in sc["objects"] if o["type"] == "point3"}
    secs = [o for o in sc["objects"] if o["type"] == "section"]
    assert len(secs) == 1
    return {tuple(F(x) for x in q) for q in secs[0]["polygon"]}, pts, sc


def _mid(pts, *labels):
    return tuple(sum(pts[x][i] for x in labels) / len(labels) for i in range(3))


@pytest.mark.parametrize("text,expected", [
    # ∥ base through the midpoint of SA: the four lateral-edge midpoints
    (P + "Gọi M là trung điểm của SA. Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). " + SEC,
     lambda p: {_mid(p, "S", x) for x in "ABCD"}),
    (P + "Gọi M là trung điểm của SA. Mặt phẳng (P) qua M và song song với mặt đáy. Tìm thiết diện của hình chóp với mặt phẳng (P).",
     lambda p: {_mid(p, "S", x) for x in "ABCD"}),
    (P + "Gọi M là trung điểm của SA. Qua M dựng mặt phẳng (α) song song với (ABCD). Tìm thiết diện của hình chóp cắt bởi (α).",
     lambda p: {_mid(p, "S", x) for x in "ABCD"}),
    # ∥ (SAB) through the midpoint of AD: midpoints of AD, BC, SD, SC
    (P + "Gọi M là trung điểm của AD. Mặt phẳng (P) đi qua M và song song với mặt phẳng (SAB). " + SEC,
     lambda p: {_mid(p, "A", "D"), _mid(p, "B", "C"), _mid(p, "S", "D"), _mid(p, "S", "C")}),
    # ⊥ SA through its midpoint (SA ⊥ base): the same mid-height square
    (P + "Gọi M là trung điểm của SA. Mặt phẳng (P) qua M và vuông góc với SA. " + SEC,
     lambda p: {_mid(p, "S", x) for x in "ABCD"}),
    # cube: through B ⊥ AC' is (A'BD)
    (CUBE + "Mặt phẳng (P) đi qua B và vuông góc với đường thẳng AC'. Tìm thiết diện của hình lập phương cắt bởi (P).",
     lambda p: {p["A'"], p["B"], p["D"]}),
    # cube: through the midpoint of AA' ∥ (A'BD): midpoints of AA', AB, AD
    (CUBE + "Gọi M là trung điểm của AA'. Mặt phẳng (P) qua M và song song với mặt phẳng (A'BD). Tìm thiết diện của hình lập phương cắt bởi (P).",
     lambda p: {_mid(p, "A", "A'"), _mid(p, "A", "B"), _mid(p, "A", "D")}),
    # a line and a point: (ABM), M midpoint of SC, cuts SD at its midpoint
    (P + "Gọi M là trung điểm của SC. Mặt phẳng (P) chứa AB và đi qua M. " + SEC,
     lambda p: {p["A"], p["B"], _mid(p, "S", "C"), _mid(p, "S", "D")}),
    (P + "Gọi M là trung điểm của SC. Mặt phẳng (P) đi qua M và chứa đường thẳng AB. " + SEC,
     lambda p: {p["A"], p["B"], _mid(p, "S", "C"), _mid(p, "S", "D")}),
    # two lines through A: (AB'D')
    (CUBE + "Mặt phẳng (P) chứa hai đường thẳng cắt nhau AB' và AD'. Tìm thiết diện của hình lập phương cắt bởi (P).",
     lambda p: {p["A"], p["B'"], p["D'"]}),
    # compound: contains BD and ∥ SC ⇒ x + y + 2z = 1 ⇒ B, D and the midpoint of SA
    (P + "Mặt phẳng (P) chứa BD và song song với SC. " + SEC, lambda p: {p["B"], p["D"], _mid(p, "S", "A")}),
    # compound: contains AB and ⊥ (SCD) ⇒ z = y ⇒ A, B and the midpoints of SC, SD
    (P + "Mặt phẳng (P) chứa AB và vuông góc với mặt phẳng (SCD). " + SEC,
     lambda p: {p["A"], p["B"], _mid(p, "S", "C"), _mid(p, "S", "D")}),
])
def test_constraint_defined_plane_sections_match_hand_computed_vertices(text, expected):
    got, pts, _sc = _section(text)
    assert got == expected(pts)


def test_renamed_vertices_give_the_same_section():
    a, pa, _ = _section(P + "Gọi M là trung điểm của SA. Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). " + SEC)
    b, pb, _ = _section(REN + "Gọi K là trung điểm của TM. Mặt phẳng (P) đi qua K và song song với mặt phẳng (MNPQ). " + SEC)
    assert a == {_mid(pa, "S", x) for x in "ABCD"} and b == {_mid(pb, "T", x) for x in "MNPQ"}


@pytest.mark.parametrize("text,code", [
    (P + "Mặt phẳng (P) đi qua A và song song với mặt phẳng (ABCD). " + SEC, "DERIVED_PLANE_IS_REFERENCE"),
    (P + "Gọi M là trung điểm của AB. Mặt phẳng (P) chứa AB và đi qua M. " + SEC, "COLLINEAR_POINTS"),
    (P + "Mặt phẳng (P) chứa AB và song song với CD. " + SEC, "PLANE_NOT_UNIQUE"),
    (P + "Mặt phẳng (P) chứa AB và vuông góc với mặt phẳng (SAB). " + SEC, "SECTION_PLANE_IS_FACE"),
    # underdetermined, contradicted or unverifiable definitions are never read as a plane
    (P + "Gọi M là trung điểm của SA. Mặt phẳng (P) đi qua M và song song với AB. " + SEC, None),
    (P + "Gọi M là trung điểm của SA. Mặt phẳng (P) đi qua M và vuông góc với mặt phẳng (ABCD). " + SEC, None),
    (P + "Mặt phẳng (P) chứa AB. " + SEC, None),
    (CUBE + "Mặt phẳng (P) chứa hai đường thẳng AB và CC'. Tìm thiết diện của hình lập phương cắt bởi (P).", None),
    (CUBE + "Mặt phẳng (P) chứa hai đường thẳng AB và BA. Tìm thiết diện của hình lập phương cắt bởi (P).", None),
    (CUBE + "Mặt phẳng (P) chứa hai đường thẳng song song AB và C'D'. Tìm thiết diện của hình lập phương cắt bởi (P).", None),
    (CUBE + "Mặt phẳng (P) chứa hai đường thẳng cắt nhau AB và C'D'. Tìm thiết diện của hình lập phương cắt bởi (P).", None),
    # the question names a plane the source never defined
    (P + "Gọi M là trung điểm của SA. Mặt phẳng (P) đi qua M và song song với mặt phẳng (ABCD). "
         "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (Q).", None),
])
def test_degenerate_underdetermined_or_unread_planes_are_refused(text, code):
    rd, r = _serve(text)
    assert rd.get("status") != "SERVED"
    if code:
        assert (rd.get("refusal") or {}).get("code") == code, (rd.get("refusal"), r.get("reason_code"))


def test_an_undefined_plane_name_is_never_read_as_a_section_goal():
    r = parse_geometry_problem_locally(P + "Xác định thiết diện của hình chóp cắt bởi mặt phẳng (Q).", use_cache=False)
    assert not any(g.get("kind") == "construct_plane_section" for g in (r.payload or {}).get("simulation_goals", []))


def test_gate_grammar_of_a_plane_defined_by_points():
    d = R._mat_ten_diem(["Mặt phẳng (P) chứa AB và đi qua M", "Mặt phẳng (Q) đi qua N và chứa đường thẳng CD"])
    assert d == {"P": frozenset("ABM"), "Q": frozenset("CDN")}
    assert R._mat_ten_diem(["Mặt phẳng (P) chứa hai đường thẳng cắt nhau AB' và AD'"]) == {"P": frozenset({"A", "B'", "D'"})}
    assert R._mat_ten_diem(["Mặt phẳng (P) chứa hai đường thẳng AB và CD"]) == {}          # no common point: not this grammar
    assert R._mat_ten_diem(["Mặt phẳng (P) chứa hai đường thẳng song song AB và AC"]) == {}  # "song song" is never read
    assert R._mat_ten_diem(["(P) chứa AB và đi qua M", "(P) chứa AB và đi qua N"]) == {}     # defined twice: ambiguous


@pytest.mark.parametrize("text,code", [
    (CUBE + "Xác định giao tuyến của hai mặt phẳng (ABC) và (A'B'C').", "PARALLEL_PLANES"),
    (CUBE + "Xác định giao tuyến của hai mặt phẳng (ABC) và (ACD).", "CONTAINED_INFINITE_INTERSECTION"),
    (P + "Tìm giao tuyến của hai mặt phẳng (ABC) và (ABD).", "CONTAINED_INFINITE_INTERSECTION"),
])
def test_coincident_planes_are_not_called_parallel(text, code):
    rd, _ = _serve(text)
    assert rd.get("status") != "SERVED" and (rd.get("refusal") or {}).get("code") == code


@pytest.mark.parametrize("ask", [
    "Tính số đo của góc nhị diện [B, SC, D].",                                  # 120°: never the 60° plane angle
    "Tính góc nhị diện tạo bởi hai nửa mặt phẳng (SBC) và (SCD) có cạnh chung SC.",
])
def test_a_dihedral_question_is_never_served_as_the_angle_between_two_planes(ask):
    base = P + "Tính góc giữa hai mặt phẳng (SBC) và (SCD)."
    p = parse_geometry_problem_locally(base, use_cache=False).payload
    assert run_typed_fact_next_v2_route(deepcopy(p)).status == "SERVED"      # control: the plane–plane angle serves
    q = deepcopy(p)
    old = "Tính góc giữa hai mặt phẳng (SBC) và (SCD)"
    q["problem_text"] = q["problem_text"].replace(old + ".", ask)
    for g in q["math_goals"]:
        if g["quote"] == old:
            g["quote"] = ask.rstrip(".")
    assert run_typed_fact_next_v2_route(q).status != "SERVED"
    assert _serve(P + ask)[0].get("status") != "SERVED"                       # the local route never reads it either
