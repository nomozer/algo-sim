# -*- coding: utf-8 -*-
"""Continuation 11 (§3.1 & §3.2): Semantic shape-kind invariants (PE-2) and unanswered/incomplete request audit.

Covers:
1. PE-2 (`ISSUE-ARCH-ROUTE-D-SOLID-CLASS-WORD-UNCERTIFIED`) across Route D (/4), Route B (`run_fact_route`), and Route A (`run_function_route`):
   - "Cho hình lập phương ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 2, AD = 3, AA' = 4." -> REFUSED (INCONSISTENT_FACTS)
   - SL-1 openers ("Vẽ hình lập phương ...", "Vẽ lập phương ...") -> REFUSED (INCONSISTENT_FACTS)
   - Valid mathematical consequence ("Cho hình lập phương ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 2, AD = 2, AA' = 2.") -> SERVED (V = 8)
2. All solid shape assertions: cube, cuboid, right prism, oblique prism, regular prism, regular pyramid, regular tetrahedron.
3. Special polygon/triangle assertions: equilateral, right, isosceles, right-isosceles triangles; square, rectangle,
   rhombus, regular hexagon, right trapezoid; renamed vertices and permuted premises; GOAL/CONDITIONAL/QUESTION/negated exemptions.
4. Post-PE-1 unanswered / incomplete request audit ("Vẽ hình rồi tính.", "Tìm.", "Tính.", "Xác định.", "Dựng mp(SBC).",
   partial multi-goal refusal, clarification envelope, and SL-1 positive controls).
"""
from __future__ import annotations

import re

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.ai.function_route import run_fact_route, run_function_route


def _p(kind: str, quote: str, solid_id: str | None = "s1", **args) -> dict:
    d = {"kind": kind, "args": args, "quote": quote}
    if solid_id is not None:
        d["solid_id"] = solid_id
    return d


def _split_tokens(s: str) -> list[str]:
    return re.findall(r"[A-Z][0-9]*'?", s)


def _v2_payload(
    text: str,
    *,
    solid_type: str,
    notation: str,
    solid_quote: str,
    premises: list[dict],
    math_goals: list[dict] | None = None,
    sim_quote: str | None = None,
    unresolved: list[dict] | None = None,
) -> dict:
    extra_solid_premises: list[dict] = []
    if solid_type == "right_prism":
        b, t = notation.split(".")
        extra_solid_premises.append(
            _p("right_prism", solid_quote, base=_split_tokens(b), top=_split_tokens(t))
        )
        raw_solid_type = "prism"
    elif solid_type == "regular_pyramid":
        ap, b = notation.split(".")
        extra_solid_premises.append(
            _p("regular_pyramid", solid_quote, apex=ap, base=_split_tokens(b))
        )
        raw_solid_type = "pyramid"
    else:
        raw_solid_type = solid_type
    d = {
        "schema_version": "typed-fact-next/2",
        "problem_text": text,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": raw_solid_type, "notation": notation, "quote": solid_quote}],
        "premises": [*extra_solid_premises, *premises],
        "derived_sections": [],
        "relations": [],
        "simulation_goals": [
            {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": sim_quote or solid_quote}
        ],
        "math_goals": list(math_goals or ()),
    }
    if unresolved is not None:
        d["unresolved"] = list(unresolved)
    return d


def _vol_goal(quote: str) -> dict:
    return {
        "goal_id": "mg1",
        "kind": "measurement",
        "goal_type": "volume",
        "target": {"solid_id": "s1"},
        "quote": quote,
        "solid_id": "s1",
    }


# ── 1. PE-2: Cube assertion vs unequal dimensions across Route D, Route B, Route A, and SL-1 ─────────────────────────


@pytest.mark.parametrize(
    "opener,solid_quote",
    [
        ("Cho hình lập phương ABCD.A'B'C'D'", "Cho hình lập phương ABCD.A'B'C'D'"),
        ("Vẽ hình lập phương ABCD.A'B'C'D'", "hình lập phương ABCD.A'B'C'D'"),
        ("Vẽ lập phương ABCD.A'B'C'D'", "lập phương ABCD.A'B'C'D'"),
    ],
)
def test_pe2_cube_with_unequal_rectangle_dimensions_refused_route_d(opener: str, solid_quote: str) -> None:
    text = f"{opener} có đáy ABCD là hình chữ nhật, AB = 2, AD = 3, AA' = 4."
    payload = _v2_payload(
        text,
        solid_type="right_prism",
        notation="ABCD.A'B'C'D'",
        solid_quote=solid_quote,
        sim_quote=opener,
        premises=[
            _p("rectangle", "đáy ABCD là hình chữ nhật", vertices=list("ABCD")),
            _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
            _p("segment_length", "AD = 3", segment=["A", "D"], value="3"),
            _p("segment_length", "AA' = 4", segment=["A", "A'"], value="4"),
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED"
    assert r.code == "INCONSISTENT_FACTS"


def test_pe2_cube_with_unequal_dimensions_refused_route_b_and_route_a() -> None:
    text = (
        "Cho hình lập phương ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, "
        "AB = 2, AD = 3, AA' = 4. Tính thể tích khối lập phương ABCD.A'B'C'D'."
    )
    raw_b = {
        "facts": [
            {"id": "f1", "kind": "solid", "role": "premise", "solid": "ABCD.A'B'C'D'", "solid_type": "prism",
             "right": True, "quotes": ["Cho hình lập phương ABCD.A'B'C'D'"]},
            {"id": "f2", "kind": "polygon_shape", "role": "premise", "points": list("ABCD"), "shape": "rectangle",
             "quotes": ["đáy ABCD là hình chữ nhật"]},
            {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "2",
             "quotes": ["AB = 2"]},
            {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "3",
             "quotes": ["AD = 3"]},
            {"id": "f5", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "A'"], "value": "4",
             "quotes": ["AA' = 4"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "ABCD.A'B'C'D'",
             "quotes": ["Tính thể tích khối lập phương ABCD.A'B'C'D'"]},
        ]
    }
    rb = run_fact_route(text, raw_b)
    assert rb.status == "REFUSED"
    assert rb.code in ("INCONSISTENT_FACTS", "SOURCE_OBJECT_MISMATCH")

    # Direct Route A call list (no math goal needed)
    text_a = "Cho hình lập phương ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 2, AD = 3, AA' = 4."
    ra = run_function_route(
        text_a,
        {
            "calls": [
                {"id": "c1", "fn": "prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"], "right": True},
                 "source": {"quotes": ["Cho hình lập phương ABCD.A'B'C'D'"]}},
                {"id": "c2", "fn": "rectangle", "args": {"vertices": list("ABCD")},
                 "source": {"quotes": ["đáy ABCD là hình chữ nhật"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "2"},
                 "source": {"quotes": ["AB = 2"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "D"], "value": "3"},
                 "source": {"quotes": ["AD = 3"]}},
                {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "4"},
                 "source": {"quotes": ["AA' = 4"]}},
            ]
        },
    )
    assert ra.status == "REFUSED"
    assert ra.code == "INCONSISTENT_FACTS"


def test_pe2_state2_valid_mathematical_consequence_cube_with_equal_rectangle_sides_served() -> None:
    """Every square is a rectangle: AB = AD = AA' = 2 satisfies all cube invariants and MUST be SERVED (V = 8)."""
    text = (
        "Cho hình lập phương ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, "
        "AB = 2, AD = 2, AA' = 2. Tính thể tích khối lập phương ABCD.A'B'C'D'."
    )
    payload = _v2_payload(
        text,
        solid_type="right_prism",
        notation="ABCD.A'B'C'D'",
        solid_quote="Cho hình lập phương ABCD.A'B'C'D'",
        premises=[
            _p("rectangle", "đáy ABCD là hình chữ nhật", vertices=list("ABCD")),
            _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
            _p("segment_length", "AD = 2", segment=["A", "D"], value="2"),
            _p("segment_length", "AA' = 2", segment=["A", "A'"], value="2"),
        ],
        math_goals=[_vol_goal("Tính thể tích khối lập phương ABCD.A'B'C'D'")],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "SERVED", r.reason
    assert r.answer_exact["mg1"]["coef"] == "8"


def test_pe2_cube_with_square_base_but_unequal_height_refused_even_after_vertex_renaming_and_permutation() -> None:
    text = "Cho hình lập phương MNPQ.M'N'P'Q' có MM' = 5, đáy MNPQ là hình vuông cạnh 2."
    payload = _v2_payload(
        text,
        solid_type="right_prism",
        notation="MNPQ.M'N'P'Q'",
        solid_quote="Cho hình lập phương MNPQ.M'N'P'Q'",
        premises=[
            _p("segment_length", "MM' = 5", segment=["M", "M'"], value="5"),
            _p("regular_polygon", "đáy MNPQ là hình vuông cạnh 2", vertices=list("MNPQ"), side="2"),
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED"
    assert r.code == "INCONSISTENT_FACTS"


# ── 2. Sibling Solid Classes: cuboid, right prism, oblique prism, regular prism, regular pyramid, regular tetrahedron ─


def test_cuboid_with_right_trapezoid_base_refused() -> None:
    text = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy ABCD là hình thang vuông tại A và B, "
        "AB = 2, AD = 2, BC = 4, AA' = 3."
    )
    payload = _v2_payload(
        text,
        solid_type="right_prism",
        notation="ABCD.A'B'C'D'",
        solid_quote="Cho hình hộp chữ nhật ABCD.A'B'C'D'",
        premises=[
            _p("right_angle", "hình thang vuông tại A và B", vertex="A", rays=["B", "D"]),
            _p("right_angle", "hình thang vuông tại A và B", vertex="B", rays=["A", "C"]),
            _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
            _p("segment_length", "AD = 2", segment=["A", "D"], value="2"),
            _p("segment_length", "BC = 4", segment=["B", "C"], value="4"),
            _p("segment_length", "AA' = 3", segment=["A", "A'"], value="3"),
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED"
    assert r.code == "INCONSISTENT_FACTS"


def test_right_prism_claim_with_oblique_lateral_edge_refused() -> None:
    text = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2, "
        "hình chiếu vuông góc của A' lên mặt phẳng (ABC) trùng với B, A'B = 3."
    )
    payload = _v2_payload(
        text,
        solid_type="prism",
        notation="ABC.A'B'C'",
        solid_quote="Cho hình lăng trụ đứng ABC.A'B'C'",
        premises=[
            _p("regular_polygon", "đáy ABC là tam giác đều cạnh 2", vertices=list("ABC"), side="2"),
            _p("orthogonal_projection", "hình chiếu vuông góc của A' lên mặt phẳng (ABC) trùng với B",
               point="A'", plane=list("ABC"), image="B"),
            _p("segment_length", "A'B = 3", segment=["A'", "B"], value="3"),
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED"
    assert r.code == "INCONSISTENT_FACTS"


def test_oblique_prism_claim_with_perpendicular_lateral_edge_refused_and_true_oblique_served() -> None:
    bad_text = (
        "Cho hình lăng trụ xiên ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2, "
        "AA' vuông góc với mặt phẳng (ABC), AA' = 3."
    )
    bad = _v2_payload(
        bad_text,
        solid_type="prism",
        notation="ABC.A'B'C'",
        solid_quote="Cho hình lăng trụ xiên ABC.A'B'C'",
        premises=[
            _p("regular_polygon", "đáy ABC là tam giác đều cạnh 2", vertices=list("ABC"), side="2"),
            _p("perpendicular_line_plane", "AA' vuông góc với mặt phẳng (ABC)", line=["A", "A'"], plane=list("ABC")),
            _p("segment_length", "AA' = 3", segment=["A", "A'"], value="3"),
        ],
    )
    r_bad = run_typed_fact_next_v2_route(bad)
    assert r_bad.status == "REFUSED"
    assert r_bad.code == "INCONSISTENT_FACTS"

    ok_text = (
        "Cho hình lăng trụ xiên ABC.A'B'C' có đáy ABC là tam giác đều cạnh 2, "
        "hình chiếu vuông góc của A' lên mặt phẳng (ABC) trùng với B, A'B = 3. "
        "Tính thể tích khối lăng trụ ABC.A'B'C'."
    )
    ok = _v2_payload(
        ok_text,
        solid_type="prism",
        notation="ABC.A'B'C'",
        solid_quote="Cho hình lăng trụ xiên ABC.A'B'C'",
        premises=[
            _p("regular_polygon", "đáy ABC là tam giác đều cạnh 2", vertices=list("ABC"), side="2"),
            _p("orthogonal_projection", "hình chiếu vuông góc của A' lên mặt phẳng (ABC) trùng với B",
               point="A'", plane=list("ABC"), image="B"),
            _p("segment_length", "A'B = 3", segment=["A'", "B"], value="3"),
        ],
        math_goals=[_vol_goal("Tính thể tích khối lăng trụ ABC.A'B'C'")],
    )
    r_ok = run_typed_fact_next_v2_route(ok)
    assert r_ok.status == "SERVED", r_ok.reason
    assert r_ok.answer_exact["mg1"]["coef"] == "3√3"


def test_regular_prism_with_scalene_base_refused() -> None:
    text = "Cho hình lăng trụ tam giác đều ABC.A'B'C' có AB = 2, BC = 3, AC = 4, AA' = 5."
    payload = _v2_payload(
        text,
        solid_type="right_prism",
        notation="ABC.A'B'C'",
        solid_quote="Cho hình lăng trụ tam giác đều ABC.A'B'C'",
        premises=[
            _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
            _p("segment_length", "BC = 3", segment=["B", "C"], value="3"),
            _p("segment_length", "AC = 4", segment=["A", "C"], value="4"),
            _p("segment_length", "AA' = 5", segment=["A", "A'"], value="5"),
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED"
    assert r.code == "INCONSISTENT_FACTS"


def test_regular_pyramid_omitted_by_extractor_with_corner_perpendicular_edge_refused() -> None:
    text = "Cho hình chóp đều S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD), SA = 2."
    payload = _v2_payload(
        text,
        solid_type="pyramid",
        notation="S.ABCD",
        solid_quote="Cho hình chóp đều S.ABCD",
        premises=[
            _p("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=list("ABCD"), side="2"),
            _p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABCD)", line=["S", "A"], plane=list("ABCD")),
            _p("segment_length", "SA = 2", segment=["S", "A"], value="2"),
        ],
    )
    r = run_typed_fact_next_v2_route(payload)
    assert r.status == "REFUSED"
    assert r.code == "INCONSISTENT_FACTS"


def test_regular_tetrahedron_unequal_lateral_edge_refused_and_equal_served() -> None:
    bad_text = "Cho tứ diện đều ABCD có AB = 2, DA = 3."
    bad = _v2_payload(
        bad_text,
        solid_type="regular_pyramid",
        notation="D.ABC",
        solid_quote="Cho tứ diện đều ABCD",
        premises=[
            _p("regular_polygon", "Cho tứ diện đều ABCD", vertices=list("ABC")),
            _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
            _p("segment_length", "DA = 3", segment=["D", "A"], value="3"),
        ],
    )
    r_bad = run_typed_fact_next_v2_route(bad)
    assert r_bad.status == "REFUSED"
    assert r_bad.code == "INCONSISTENT_FACTS"

    ok_text = "Cho tứ diện đều ABCD có AB = 2, DA = 2. Tính thể tích khối tứ diện ABCD."
    ok = _v2_payload(
        ok_text,
        solid_type="regular_pyramid",
        notation="D.ABC",
        solid_quote="Cho tứ diện đều ABCD",
        premises=[
            _p("regular_polygon", "Cho tứ diện đều ABCD", vertices=list("ABC")),
            _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
            _p("segment_length", "DA = 2", segment=["D", "A"], value="2"),
        ],
        math_goals=[_vol_goal("Tính thể tích khối tứ diện ABCD")],
    )
    r_ok = run_typed_fact_next_v2_route(ok)
    assert r_ok.status == "SERVED", r_ok.reason
    assert r_ok.answer_exact["mg1"]["coef"] == "2√2/3"


# ── 3. Special Triangles & Polygons (equilateral, right, isosceles, right-isosceles, rhombus, hexagon, trapezoid) ─────


def test_equilateral_face_claim_blanketed_by_face_perp_base_checked_on_coordinates() -> None:
    bad_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "mặt bên SAB là tam giác đều và nằm trong mặt phẳng vuông góc với đáy, SA = 3, SB = 3."
    )
    bad = _v2_payload(
        bad_text,
        solid_type="pyramid",
        notation="S.ABCD",
        solid_quote="Cho hình chóp S.ABCD",
        premises=[
            _p("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=list("ABCD"), side="2"),
            _p("face_perpendicular_base", "mặt bên SAB là tam giác đều và nằm trong mặt phẳng vuông góc với đáy",
               face=["S", "A", "B"], base=list("ABCD")),
            _p("segment_length", "SA = 3", segment=["S", "A"], value="3"),
            _p("segment_length", "SB = 3", segment=["S", "B"], value="3"),
        ],
    )
    r_bad = run_typed_fact_next_v2_route(bad)
    assert r_bad.status == "REFUSED"
    assert r_bad.code == "INCONSISTENT_FACTS"

    ok_text = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "mặt bên SAB là tam giác đều và nằm trong mặt phẳng vuông góc với đáy, SA = 2, SB = 2."
    )
    ok = _v2_payload(
        ok_text,
        solid_type="pyramid",
        notation="S.ABCD",
        solid_quote="Cho hình chóp S.ABCD",
        premises=[
            _p("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=list("ABCD"), side="2"),
            _p("face_perpendicular_base", "mặt bên SAB là tam giác đều và nằm trong mặt phẳng vuông góc với đáy",
               face=["S", "A", "B"], base=list("ABCD")),
            _p("segment_length", "SA = 2", segment=["S", "A"], value="2"),
            _p("segment_length", "SB = 2", segment=["S", "B"], value="2"),
        ],
    )
    r_ok = run_typed_fact_next_v2_route(ok)
    assert r_ok.status == "SERVED", r_ok.reason


def test_isosceles_and_right_isosceles_and_pythagorean_right_triangle_assertions() -> None:
    # Isosceles at S contradicted by SA = 2, SB = 3
    iso_bad = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, "
        "mặt bên SAB là tam giác cân tại S và nằm trong mặt phẳng vuông góc với đáy, SA = 2, SB = 3."
    )
    r_iso = run_typed_fact_next_v2_route(
        _v2_payload(
            iso_bad,
            solid_type="pyramid",
            notation="S.ABCD",
            solid_quote="Cho hình chóp S.ABCD",
            premises=[
                _p("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=list("ABCD"), side="2"),
                _p("face_perpendicular_base", "mặt bên SAB là tam giác cân tại S và nằm trong mặt phẳng vuông góc với đáy",
                   face=["S", "A", "B"], base=list("ABCD")),
                _p("segment_length", "SA = 2", segment=["S", "A"], value="2"),
                _p("segment_length", "SB = 3", segment=["S", "B"], value="3"),
            ],
        )
    )
    assert (r_iso.status, r_iso.code) == ("REFUSED", "INCONSISTENT_FACTS")

    # Right-isosceles at A contradicted by AB = 2, AC = 3
    riso_bad = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A, AB = 2, AC = 3, "
        "SA vuông góc với mặt phẳng (ABC), SA = 2."
    )
    r_riso = run_typed_fact_next_v2_route(
        _v2_payload(
            riso_bad,
            solid_type="pyramid",
            notation="S.ABC",
            solid_quote="Cho hình chóp S.ABC",
            premises=[
                _p("right_angle", "đáy ABC là tam giác vuông cân tại A", vertex="A", rays=["B", "C"]),
                _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
                _p("segment_length", "AC = 3", segment=["A", "C"], value="3"),
                _p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABC)", line=["S", "A"], plane=list("ABC")),
                _p("segment_length", "SA = 2", segment=["S", "A"], value="2"),
            ],
        )
    )
    assert (r_riso.status, r_riso.code) == ("REFUSED", "INCONSISTENT_FACTS")

    # Right-isosceles positive control (AB = 2, AC = 2) -> SERVED
    riso_ok = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A, AB = 2, AC = 2, "
        "SA vuông góc với mặt phẳng (ABC), SA = 3. Tính thể tích khối chóp S.ABC."
    )
    r_riso_ok = run_typed_fact_next_v2_route(
        _v2_payload(
            riso_ok,
            solid_type="pyramid",
            notation="S.ABC",
            solid_quote="Cho hình chóp S.ABC",
            premises=[
                _p("right_angle", "đáy ABC là tam giác vuông cân tại A", vertex="A", rays=["B", "C"]),
                _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
                _p("segment_length", "AC = 2", segment=["A", "C"], value="2"),
                _p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABC)", line=["S", "A"], plane=list("ABC")),
                _p("segment_length", "SA = 3", segment=["S", "A"], value="3"),
            ],
            math_goals=[_vol_goal("Tính thể tích khối chóp S.ABC")],
        )
    )
    assert r_riso_ok.status == "SERVED", r_riso_ok.reason
    assert r_riso_ok.answer_exact["mg1"]["coef"] == "2"

    # Right triangle specified at A contradicted by 3-4-5 right at B (even if blanketed in solid quote)
    rt_wrong_vertex = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, BC = 4, AC = 5, "
        "SA vuông góc với mặt phẳng (ABC), SA = 2."
    )
    r_rt_bad = run_typed_fact_next_v2_route(
        _v2_payload(
            rt_wrong_vertex,
            solid_type="pyramid",
            notation="S.ABC",
            solid_quote="Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A",
            premises=[
                _p("segment_length", "AB = 3", segment=["A", "B"], value="3"),
                _p("segment_length", "BC = 4", segment=["B", "C"], value="4"),
                _p("segment_length", "AC = 5", segment=["A", "C"], value="5"),
                _p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABC)", line=["S", "A"], plane=list("ABC")),
                _p("segment_length", "SA = 2", segment=["S", "A"], value="2"),
            ],
        )
    )
    assert r_rt_bad.status == "REFUSED"
    assert r_rt_bad.code == "INCONSISTENT_FACTS"


def test_rhombus_and_right_trapezoid_and_regular_hexagon_shape_assertions() -> None:
    # Route A when rectangle(ABCD) is constructed with AB=2, AD=3 under a rhombus claim -> INCONSISTENT_FACTS
    text_rhom = (
        "Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, đáy ABCD là hình thoi, "
        "AB = 2, AD = 3, AA' = 4."
    )
    ra_rhom = run_function_route(
        text_rhom,
        {
            "calls": [
                {"id": "c1", "fn": "prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"], "right": True},
                 "source": {"quotes": ["Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, đáy ABCD là hình thoi"]}},
                {"id": "c2", "fn": "rectangle", "args": {"vertices": list("ABCD")},
                 "source": {"quotes": ["đáy ABCD là hình chữ nhật"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "2"},
                 "source": {"quotes": ["AB = 2"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "D"], "value": "3"},
                 "source": {"quotes": ["AD = 3"]}},
                {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "4"},
                 "source": {"quotes": ["AA' = 4"]}},
            ]
        },
    )
    assert (ra_rhom.status, ra_rhom.code) == ("REFUSED", "INCONSISTENT_FACTS")

    # Rhombus positive mathematical-consequence control: square AB = 2, AD = 2 IS a rhombus -> SERVED
    text_rhom_ok = (
        "Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, đáy ABCD là hình thoi, "
        "AB = 2, AD = 2, AA' = 4."
    )
    ra_rhom_ok = run_function_route(
        text_rhom_ok,
        {
            "calls": [
                {"id": "c1", "fn": "prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"], "right": True},
                 "source": {"quotes": ["Cho hình lăng trụ đứng ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, đáy ABCD là hình thoi"]}},
                {"id": "c2", "fn": "rectangle", "args": {"vertices": list("ABCD")},
                 "source": {"quotes": ["đáy ABCD là hình chữ nhật"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "2"},
                 "source": {"quotes": ["AB = 2"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "D"], "value": "2"},
                 "source": {"quotes": ["AD = 2"]}},
                {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "4"},
                 "source": {"quotes": ["AA' = 4"]}},
            ]
        },
    )
    assert ra_rhom_ok.status == "SERVED", ra_rhom_ok.reason

    # Regular hexagon positive control -> SERVED
    hex_ok = (
        "Cho hình chóp đều S.ABCDEF có đáy ABCDEF là lục giác đều cạnh 2, SA = 4. "
        "Tính thể tích khối chóp S.ABCDEF."
    )
    r_hex = run_typed_fact_next_v2_route(
        _v2_payload(
            hex_ok,
            solid_type="regular_pyramid",
            notation="S.ABCDEF",
            solid_quote="Cho hình chóp đều S.ABCDEF",
            premises=[
                _p("regular_polygon", "đáy ABCDEF là lục giác đều cạnh 2", vertices=list("ABCDEF"), side="2"),
                _p("segment_length", "SA = 4", segment=["S", "A"], value="4"),
            ],
            math_goals=[_vol_goal("Tính thể tích khối chóp S.ABCDEF")],
        )
    )
    assert r_hex.status == "SERVED", r_hex.reason

    # Right trapezoid positive control -> SERVED
    trap_ok = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và B, AB = 2, AD = 2, BC = 4, "
        "SA vuông góc với mặt phẳng (ABCD), SA = 3. Tính thể tích khối chóp S.ABCD."
    )
    r_trap = run_typed_fact_next_v2_route(
        _v2_payload(
            trap_ok,
            solid_type="pyramid",
            notation="S.ABCD",
            solid_quote="Cho hình chóp S.ABCD",
            premises=[
                _p("right_angle", "hình thang vuông tại A và B", vertex="A", rays=["B", "D"]),
                _p("right_angle", "hình thang vuông tại A và B", vertex="B", rays=["A", "C"]),
                _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
                _p("segment_length", "AD = 2", segment=["A", "D"], value="2"),
                _p("segment_length", "BC = 4", segment=["B", "C"], value="4"),
                _p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABCD)", line=["S", "A"], plane=list("ABCD")),
                _p("segment_length", "SA = 3", segment=["S", "A"], value="3"),
            ],
            math_goals=[_vol_goal("Tính thể tích khối chóp S.ABCD")],
        )
    )
    assert r_trap.status == "SERVED", r_trap.reason
    assert r_trap.answer_exact["mg1"]["coef"] == "6"

    # Right trapezoid with wrong right-angle vertices (tại A và C when right angles are at A and B, AD != BC) -> REFUSED
    trap_bad = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và C, góc DAB vuông, góc ABC vuông, "
        "AB = 2, AD = 2, BC = 4, SA vuông góc với mặt phẳng (ABCD), SA = 3."
    )
    r_trap_bad = run_typed_fact_next_v2_route(
        _v2_payload(
            trap_bad,
            solid_type="pyramid",
            notation="S.ABCD",
            solid_quote="Cho hình chóp S.ABCD có đáy ABCD là hình thang vuông tại A và C",
            premises=[
                _p("right_angle", "góc DAB vuông", vertex="A", rays=["B", "D"]),
                _p("right_angle", "góc ABC vuông", vertex="B", rays=["A", "C"]),
                _p("segment_length", "AB = 2", segment=["A", "B"], value="2"),
                _p("segment_length", "AD = 2", segment=["A", "D"], value="2"),
                _p("segment_length", "BC = 4", segment=["B", "C"], value="4"),
                _p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABCD)", line=["S", "A"], plane=list("ABCD")),
                _p("segment_length", "SA = 3", segment=["S", "A"], value="3"),
            ],
        )
    )
    assert (r_trap_bad.status, r_trap_bad.code) == ("REFUSED", "INCONSISTENT_FACTS")


def test_goal_clause_shape_claim_is_exempt_from_premise_shape_obligation() -> None:
    """State 3: a shape predicate inside a GOAL clause ('Chứng minh BC vuông góc với (SAB)') or GOAL shape claim is exempt."""
    text = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, "
        "SA vuông góc với mặt phẳng (ABC), SA = 2. "
        "Tính thể tích khối chóp S.ABC, rồi chứng minh BC vuông góc với (SAB)."
    )
    r = run_typed_fact_next_v2_route(
        _v2_payload(
            text,
            solid_type="pyramid",
            notation="S.ABC",
            solid_quote="Cho hình chóp S.ABC",
            premises=[
                _p("right_angle", "đáy ABC là tam giác vuông tại B", vertex="B", rays=["A", "C"]),
                _p("segment_length", "AB = 3", segment=["A", "B"], value="3"),
                _p("segment_length", "BC = 4", segment=["B", "C"], value="4"),
                _p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABC)", line=["S", "A"], plane=list("ABC")),
                _p("segment_length", "SA = 2", segment=["S", "A"], value="2"),
            ],
            math_goals=[_vol_goal("Tính thể tích khối chóp S.ABC")],
        )
    )
    assert r.status == "SERVED", r.reason
    assert r.answer_exact["mg1"]["coef"] == "4"


# ── 4. §3.2 Post-PE-1 Unanswered / Incomplete Request Audit ──────────────────────────────────────────────────────────


BASE_PYR = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2."


def _base_pyr_payload(tail: str, goals: list[dict] | None = None, sim_quote: str = "Cho hình chóp S.ABCD",
                      unresolved: list[dict] | None = None) -> dict:
    return _v2_payload(
        f"{BASE_PYR} {tail}",
        solid_type="pyramid",
        notation="S.ABCD",
        solid_quote="Cho hình chóp S.ABCD",
        sim_quote=sim_quote,
        premises=[
            _p("regular_polygon", "đáy ABCD là hình vuông cạnh 2", vertices=list("ABCD"), side="2"),
            _p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABCD)", line=["S", "A"], plane=list("ABCD")),
            _p("segment_length", "SA = 2", segment=["S", "A"], value="2"),
        ],
        math_goals=goals,
        unresolved=unresolved,
    )


@pytest.mark.parametrize(
    "tail",
    [
        "Tính.",
        "Tìm.",
        "Xác định.",
        "Hãy tính.",
        "Vẽ hình rồi tính.",
        "Mô phỏng hình chóp và tìm.",
        "Dựng mp(SBC).",
        "Dựng mặt phẳng (SAC).",
        "Vẽ mặt phẳng (SBC).",
    ],
)
def test_incomplete_or_unbuilt_plane_request_is_refused_never_silently_dropped(tail: str) -> None:
    r = run_typed_fact_next_v2_route(_base_pyr_payload(tail))
    assert r.status == "REFUSED", f"Unexpectedly served {tail!r}: {r}"
    assert r.code in ("QUESTION_CONTEXT_UNSUPPORTED", "SOURCE_PREMISE_UNREAD")


def test_partial_multi_goal_request_is_refused_as_request_not_answered() -> None:
    r = run_typed_fact_next_v2_route(
        _base_pyr_payload(
            "Tính thể tích khối chóp S.ABCD và độ dài SC.",
            goals=[_vol_goal("Tính thể tích khối chóp S.ABCD")],
        )
    )
    assert r.status == "REFUSED"
    assert r.code == "REQUEST_NOT_ANSWERED"


def test_missing_operand_request_emits_clarification_envelope() -> None:
    r = run_typed_fact_next_v2_route(
        _base_pyr_payload(
            "Tính góc.",
            unresolved=[
                {
                    "unresolved_id": "u1",
                    "kind": "missing_operand",
                    "quote": "Tính góc",
                    "missing_roles": ["target_line_or_plane"],
                    "candidate_relations": ["angle"],
                }
            ],
        )
    )
    assert r.status == "REFUSED"
    assert r.code == "AMBIGUOUS_FACT"
    assert r.route_d["refusal"]["clarification"]["schema_version"] == "route-d-clarification/1"
    assert r.route_d["refusal"]["clarification"]["nlu_class"] == "MISSING_DATA"


# ── 5. Adversarial Review Round 1 Closure (BLOCKER-1, BLOCKER-2, NIT-1) ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "base_clause",
    [
        "có đáy là hình vuông",
        "có đáy là hình thoi",
        "có đáy là hình thang vuông tại B và C",
    ],
)
def test_blocker1_multi_solid_unlabelled_base_shape_contradiction_refused(base_clause: str) -> None:
    text = (
        f"Cho hình chóp S.ABCD {base_clause}, AB = a, AD = a, BC = 2a, "
        "góc BAD vuông, góc ABC vuông, SA vuông góc với (ABCD), SA = a. "
        "Gọi M là trung điểm của SA. Tính tỉ số thể tích của khối chóp M.ABCD và khối chóp S.ABCD."
    )
    r = run_fact_route(
        text,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABCD", "quotes": [f"Cho hình chóp S.ABCD {base_clause}"]},
                {"id": "f1b", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "M.ABCD", "quotes": ["khối chóp M.ABCD"]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "a", "quotes": ["AD = a"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["B", "C"], "value": "2a", "quotes": ["BC = 2a"]},
                {"id": "f6", "kind": "right_angle", "role": "premise", "at": "A", "points": ["B", "D"], "quotes": ["góc BAD vuông"]},
                {"id": "f7", "kind": "right_angle", "role": "premise", "at": "B", "points": ["A", "C"], "quotes": ["góc ABC vuông"]},
                {"id": "f8", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["SA vuông góc với (ABCD)"]},
                {"id": "f9", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
                {"id": "f10", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint", "points": ["S", "A"], "quotes": ["Gọi M là trung điểm của SA"]},
                {"id": "g1", "kind": "question", "role": "question", "quantity": "volume_ratio", "solid_refs": ["f1b", "f1"], "quotes": ["Tính tỉ số thể tích của khối chóp M.ABCD và khối chóp S.ABCD"]},
            ]
        },
    )
    assert r.status == "REFUSED"
    assert r.code == "INCONSISTENT_FACTS"


def test_blocker1_multi_solid_unlabelled_base_shape_valid_positive_served() -> None:
    text = (
        "Cho hình chóp S.ABCD có đáy là hình vuông cạnh a, SA vuông góc với (ABCD), SA = a. "
        "Gọi M là trung điểm của SA. Tính tỉ số thể tích của khối chóp M.ABCD và khối chóp S.ABCD."
    )
    r = run_fact_route(
        text,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABCD", "quotes": ["Cho hình chóp S.ABCD"]},
                {"id": "f1b", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "M.ABCD", "quotes": ["khối chóp M.ABCD"]},
                {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "square", "points": ["A", "B", "C", "D"], "value": "a", "quotes": ["Cho hình chóp S.ABCD có đáy là hình vuông cạnh a"]},
                {"id": "f3", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["SA vuông góc với (ABCD)"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
                {"id": "f5", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint", "points": ["S", "A"], "quotes": ["Gọi M là trung điểm của SA"]},
                {"id": "g1", "kind": "question", "role": "question", "quantity": "volume_ratio", "solid_refs": ["f1b", "f1"], "quotes": ["Tính tỉ số thể tích của khối chóp M.ABCD và khối chóp S.ABCD"]},
            ]
        },
    )
    assert r.status == "SERVED", (r.code, r.reason)
    assert r.answers["g1"] == "1/2"


@pytest.mark.parametrize(
    ("header", "right_flag"),
    [
        ("Cho hình hộp ABCD.A'B'C'D'", False),
        ("Cho hình hộp đứng ABCD.A'B'C'D'", True),
    ],
)
def test_blocker2_parallelepiped_and_right_parallelepiped_reject_trapezoid_base_and_serve_parallelogram(
    header: str, right_flag: bool
) -> None:
    bad_txt = (
        f"{header} có đáy ABCD với AB = a, AD = a, BC = 2a, góc BAD vuông, góc ABC vuông, "
        "AA' vuông góc với (ABCD), AA' = a. Tính thể tích khối lăng trụ ABCD.A'B'C'D'."
    )
    r_bad = run_fact_route(
        bad_txt,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "prism", "solid": "ABCD.A'B'C'D'", "right": right_flag, "quotes": [header]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "a", "quotes": ["AD = a"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["B", "C"], "value": "2a", "quotes": ["BC = 2a"]},
                {"id": "f5", "kind": "right_angle", "role": "premise", "at": "A", "points": ["B", "D"], "quotes": ["góc BAD vuông"]},
                {"id": "f6", "kind": "right_angle", "role": "premise", "at": "B", "points": ["A", "C"], "quotes": ["góc ABC vuông"]},
                {"id": "f7", "kind": "perpendicular", "role": "premise", "points_a": ["A", "A'"], "points_b": ["A", "B", "C", "D"], "quotes": ["AA' vuông góc với (ABCD)"]},
                {"id": "f8", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "A'"], "value": "a", "quotes": ["AA' = a"]},
                {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "ABCD.A'B'C'D'", "quotes": ["Tính thể tích khối lăng trụ ABCD.A'B'C'D'"]},
            ]
        },
    )
    assert r_bad.status == "REFUSED"
    assert r_bad.code == "INCONSISTENT_FACTS"

    ok_txt = (
        f"{header} có đáy ABCD là hình chữ nhật, AB = a, AD = 2a, "
        "AA' vuông góc với (ABCD), AA' = a. Tính thể tích khối lăng trụ ABCD.A'B'C'D'."
    )
    r_ok = run_fact_route(
        ok_txt,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "prism", "solid": "ABCD.A'B'C'D'", "right": right_flag, "quotes": [header]},
                {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "rectangle", "points": ["A", "B", "C", "D"], "quotes": ["đáy ABCD là hình chữ nhật"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "2a", "quotes": ["AD = 2a"]},
                {"id": "f5", "kind": "perpendicular", "role": "premise", "points_a": ["A", "A'"], "points_b": ["A", "B", "C", "D"], "quotes": ["AA' vuông góc với (ABCD)"]},
                {"id": "f6", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "A'"], "value": "a", "quotes": ["AA' = a"]},
                {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "ABCD.A'B'C'D'", "quotes": ["Tính thể tích khối lăng trụ ABCD.A'B'C'D'"]},
            ]
        },
    )
    assert r_ok.status == "SERVED", (r_ok.code, r_ok.reason)


def test_blocker2_postnominal_3d_solid_modifiers_reject_contradictions_and_keep_adverb_deu_safe() -> None:
    # 1. "Cho hình chóp S.ABCD đều" with non-square base + corner SA ⊥ (ABCD)
    t_pyr = (
        "Cho hình chóp S.ABCD đều có AB = a, AD = 2a, BC = 2a, CD = a, "
        "góc BAD vuông, góc ABC vuông, SA vuông góc với (ABCD), SA = a. Tính thể tích khối chóp S.ABCD."
    )
    r_pyr = run_fact_route(
        t_pyr,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABCD", "quotes": ["Cho hình chóp S.ABCD đều"]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "2a", "quotes": ["AD = 2a"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["B", "C"], "value": "2a", "quotes": ["BC = 2a"]},
                {"id": "f5", "kind": "length", "role": "premise", "measure": "segment", "points": ["C", "D"], "value": "a", "quotes": ["CD = a"]},
                {"id": "f6", "kind": "right_angle", "role": "premise", "at": "A", "points": ["B", "D"], "quotes": ["góc BAD vuông"]},
                {"id": "f7", "kind": "right_angle", "role": "premise", "at": "B", "points": ["A", "C"], "quotes": ["góc ABC vuông"]},
                {"id": "f8", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["SA vuông góc với (ABCD)"]},
                {"id": "f9", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
                {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABCD", "quotes": ["Tính thể tích khối chóp S.ABCD"]},
            ]
        },
    )
    assert r_pyr.status == "REFUSED" and r_pyr.code == "INCONSISTENT_FACTS"

    # 2. "Cho tứ diện ABCD đều" with right corner at A (BC = a√2 != a)
    t_tet = (
        "Cho tứ diện ABCD đều có AB = a, AC = a, góc BAC vuông, AD vuông góc với (ABC), AD = a. "
        "Tính thể tích khối tứ diện ABCD."
    )
    r_tet = run_fact_route(
        t_tet,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "tetrahedron", "solid": "ABCD", "quotes": ["Cho tứ diện ABCD đều"]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "C"], "value": "a", "quotes": ["AC = a"]},
                {"id": "f4", "kind": "right_angle", "role": "premise", "at": "A", "points": ["B", "C"], "quotes": ["góc BAC vuông"]},
                {"id": "f5", "kind": "perpendicular", "role": "premise", "points_a": ["A", "D"], "points_b": ["A", "B", "C"], "quotes": ["AD vuông góc với (ABC)"]},
                {"id": "f6", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "a", "quotes": ["AD = a"]},
                {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "ABCD", "quotes": ["Tính thể tích khối tứ diện ABCD"]},
            ]
        },
    )
    assert r_tet.status == "REFUSED" and r_tet.code == "INCONSISTENT_FACTS"

    # 3. "Cho hình lăng trụ ABC.A'B'C' đều" with right non-equilateral base
    t_pri = (
        "Cho hình lăng trụ ABC.A'B'C' đều có AB = a, AC = 2a, góc BAC vuông, AA' vuông góc với (ABC), AA' = a. "
        "Tính thể tích khối lăng trụ ABC.A'B'C'."
    )
    r_pri = run_fact_route(
        t_pri,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "prism", "solid": "ABC.A'B'C'", "quotes": ["Cho hình lăng trụ ABC.A'B'C' đều"]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "C"], "value": "2a", "quotes": ["AC = 2a"]},
                {"id": "f4", "kind": "right_angle", "role": "premise", "at": "A", "points": ["B", "C"], "quotes": ["góc BAC vuông"]},
                {"id": "f5", "kind": "perpendicular", "role": "premise", "points_a": ["A", "A'"], "points_b": ["A", "B", "C"], "quotes": ["AA' vuông góc với (ABC)"]},
                {"id": "f6", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "A'"], "value": "a", "quotes": ["AA' = a"]},
                {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "ABC.A'B'C'", "quotes": ["Tính thể tích khối lăng trụ ABC.A'B'C'"]},
            ]
        },
    )
    assert r_pri.status == "REFUSED" and r_pri.code == "INCONSISTENT_FACTS"

    # 4. Positive control: post-nominal "Cho hình lăng trụ ABC.A'B'C' đều" with equilateral base & right lateral edge
    ok_pri = "Cho hình lăng trụ ABC.A'B'C' đều có đáy ABC là tam giác đều cạnh a, AA' = a. Tính thể tích khối lăng trụ ABC.A'B'C'."
    r_ok_pri = run_fact_route(
        ok_pri,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "prism", "solid": "ABC.A'B'C'", "right": True, "regular": True, "quotes": ["Cho hình lăng trụ ABC.A'B'C' đều"]},
                {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "value": "a", "quotes": ["đáy ABC là tam giác đều cạnh a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "A'"], "value": "a", "quotes": ["AA' = a"]},
                {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "ABC.A'B'C'", "quotes": ["Tính thể tích khối lăng trụ ABC.A'B'C'"]},
            ]
        },
    )
    assert r_ok_pri.status == "SERVED", (r_ok_pri.code, r_ok_pri.reason)


@pytest.mark.parametrize("shape_phrase", ["hình bình hành", "hình thang cân"])
def test_blocker2_2d_parallelogram_and_isosceles_trapezoid_reject_right_trapezoid_and_serve_rectangle(
    shape_phrase: str,
) -> None:
    bad_txt = (
        f"Cho hình chóp S.ABCD có đáy ABCD là {shape_phrase}, AB = a, AD = a, BC = 2a, "
        "góc BAD vuông, góc ABC vuông, SA vuông góc với (ABCD), SA = a. Tính thể tích khối chóp S.ABCD."
    )
    r_bad = run_fact_route(
        bad_txt,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABCD", "quotes": [f"Cho hình chóp S.ABCD có đáy ABCD là {shape_phrase}"]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "a", "quotes": ["AD = a"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["B", "C"], "value": "2a", "quotes": ["BC = 2a"]},
                {"id": "f5", "kind": "right_angle", "role": "premise", "at": "A", "points": ["B", "D"], "quotes": ["góc BAD vuông"]},
                {"id": "f6", "kind": "right_angle", "role": "premise", "at": "B", "points": ["A", "C"], "quotes": ["góc ABC vuông"]},
                {"id": "f7", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["SA vuông góc với (ABCD)"]},
                {"id": "f8", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
                {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABCD", "quotes": ["Tính thể tích khối chóp S.ABCD"]},
            ]
        },
    )
    assert r_bad.status == "REFUSED" and r_bad.code == "INCONSISTENT_FACTS"

    ok_txt = (
        f"Cho hình chóp S.ABCD có đáy ABCD là {shape_phrase}, AB = a, AD = 2a, BC = 2a, CD = a, "
        "góc BAD vuông, góc ABC vuông, SA vuông góc với (ABCD), SA = a. Tính thể tích khối chóp S.ABCD."
    )
    r_ok = run_fact_route(
        ok_txt,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABCD", "quotes": [f"Cho hình chóp S.ABCD có đáy ABCD là {shape_phrase}"]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "2a", "quotes": ["AD = 2a"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["B", "C"], "value": "2a", "quotes": ["BC = 2a"]},
                {"id": "f5", "kind": "length", "role": "premise", "measure": "segment", "points": ["C", "D"], "value": "a", "quotes": ["CD = a"]},
                {"id": "f6", "kind": "right_angle", "role": "premise", "at": "A", "points": ["B", "D"], "quotes": ["góc BAD vuông"]},
                {"id": "f7", "kind": "right_angle", "role": "premise", "at": "B", "points": ["A", "C"], "quotes": ["góc ABC vuông"]},
                {"id": "f8", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["SA vuông góc với (ABCD)"]},
                {"id": "f9", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
                {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABCD", "quotes": ["Tính thể tích khối chóp S.ABCD"]},
            ]
        },
    )
    assert r_ok.status == "SERVED", (r_ok.code, r_ok.reason)


@pytest.mark.parametrize("tri_phrase", ["tam giác nhọn", "tam giác tù"])
def test_blocker2_acute_and_obtuse_triangle_reject_right_triangle_and_serve_valid_angles(tri_phrase: str) -> None:
    bad_txt = (
        f"Cho hình chóp S.ABC có đáy ABC là {tri_phrase}, AB = a, AC = a, góc BAC vuông, "
        "SA vuông góc với (ABC), SA = a. Tính thể tích khối chóp S.ABC."
    )
    r_bad = run_fact_route(
        bad_txt,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABC", "quotes": [f"Cho hình chóp S.ABC có đáy ABC là {tri_phrase}"]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "C"], "value": "a", "quotes": ["AC = a"]},
                {"id": "f4", "kind": "right_angle", "role": "premise", "at": "A", "points": ["B", "C"], "quotes": ["góc BAC vuông"]},
                {"id": "f5", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
                {"id": "f6", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
                {"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABC", "quotes": ["Tính thể tích khối chóp S.ABC"]},
            ]
        },
    )
    assert r_bad.status == "REFUSED" and r_bad.code == "INCONSISTENT_FACTS"

    # Valid positive control: 4-5-6 is acute; 2-2-3 is obtuse at the vertex opposite 3
    sides = ("4", "5", "6") if tri_phrase == "tam giác nhọn" else ("2", "2", "3")
    ok_txt = (
        f"Cho hình chóp S.ABC có đáy ABC là {tri_phrase}, AB = {sides[0]}, AC = {sides[1]}, BC = {sides[2]}, "
        "SA vuông góc với (ABC), SA = 3. Tính độ dài SB."
    )
    r_ok = run_fact_route(
        ok_txt,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABC", "quotes": [f"Cho hình chóp S.ABC có đáy ABC là {tri_phrase}"]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": sides[0], "quotes": [f"AB = {sides[0]}"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "C"], "value": sides[1], "quotes": [f"AC = {sides[1]}"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["B", "C"], "value": sides[2], "quotes": [f"BC = {sides[2]}"]},
                {"id": "f5", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
                {"id": "f6", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "3", "quotes": ["SA = 3"]},
                {"id": "q1", "kind": "question", "quantity": "length", "role": "question", "points": ["S", "B"], "quotes": ["Tính độ dài SB"]},
            ]
        },
    )
    assert r_ok.status == "SERVED", (r_ok.code, r_ok.reason)


def test_blocker1_derived_section_solid_distinct_bases_still_enforces_owner_base_shape() -> None:
    text = (
        "Cho hình chóp S.ABCD có đáy là hình vuông, AB = a, AD = 2a, BC = 2a, CD = a, "
        "góc BAD vuông, góc ABC vuông, SA vuông góc với (ABCD), SA = a. "
        "Gọi M, N, P, Q lần lượt là trung điểm của SA, SB, SC, SD. "
        "Tính tỉ số thể tích của khối chóp S.MNPQ và khối chóp S.ABCD."
    )
    r = run_fact_route(
        text,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABCD", "quotes": ["Cho hình chóp S.ABCD có đáy là hình vuông"]},
                {"id": "f1b", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.MNPQ", "quotes": ["khối chóp S.MNPQ"]},
                {"id": "f2", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "2a", "quotes": ["AD = 2a"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["B", "C"], "value": "2a", "quotes": ["BC = 2a"]},
                {"id": "f5", "kind": "length", "role": "premise", "measure": "segment", "points": ["C", "D"], "value": "a", "quotes": ["CD = a"]},
                {"id": "f6", "kind": "right_angle", "role": "premise", "at": "A", "points": ["B", "D"], "quotes": ["góc BAD vuông"]},
                {"id": "f7", "kind": "right_angle", "role": "premise", "at": "B", "points": ["A", "C"], "quotes": ["góc ABC vuông"]},
                {"id": "f8", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["SA vuông góc với (ABCD)"]},
                {"id": "f9", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
                {"id": "m1", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "midpoint", "points": ["S", "A"], "quotes": ["Gọi M, N, P, Q lần lượt là trung điểm của SA, SB, SC, SD"]},
                {"id": "m2", "kind": "point_def", "role": "premise", "point": "N", "point_kind": "midpoint", "points": ["S", "B"], "quotes": ["Gọi M, N, P, Q lần lượt là trung điểm của SA, SB, SC, SD"]},
                {"id": "m3", "kind": "point_def", "role": "premise", "point": "P", "point_kind": "midpoint", "points": ["S", "C"], "quotes": ["Gọi M, N, P, Q lần lượt là trung điểm của SA, SB, SC, SD"]},
                {"id": "m4", "kind": "point_def", "role": "premise", "point": "Q", "point_kind": "midpoint", "points": ["S", "D"], "quotes": ["Gọi M, N, P, Q lần lượt là trung điểm của SA, SB, SC, SD"]},
                {"id": "g1", "kind": "question", "role": "question", "quantity": "volume_ratio", "solid_refs": ["f1b", "f1"], "quotes": ["Tính tỉ số thể tích của khối chóp S.MNPQ và khối chóp S.ABCD"]},
            ]
        },
    )
    assert r.status == "REFUSED" and r.code == "INCONSISTENT_FACTS"


def test_blocker_r2_1_multi_solid_unlabelled_base_shape_binds_local_prose_solid_and_reapexed_tetrahedron() -> None:
    from app.simulation.geometry_functions.registry import _khop_ky_hieu_khoi, _loai_cum_dung, doc_ke_hoach, doc_khang_dinh_loai_hinh

    # 1. Secondary solid A.BCC'B' claims square base in prose, while BB' = 3a != BC = 2a (blanket quote with len(khoi_calls) == 1)
    contra_one_sent = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 2, BB' = 3, "
        "hình chóp A.BCC'B' có đáy là hình vuông."
    )
    single_solid_calls = doc_ke_hoach({
        "calls": [
            {"id": "c1", "fn": "prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"], "right": True},
             "source": {"quotes": ["Cho hình hộp chữ nhật ABCD.A'B'C'D'"]}},
        ]
    })
    kd_contra = doc_khang_dinh_loai_hinh(contra_one_sent, single_solid_calls)
    assert ("square", ("B", "C", "C'", "B'")) in {(x.kind, x.vertices) for x in kd_contra}
    assert ("square", ("B", "C", "C'", "B'")) in {(x.kind, x.vertices) for x in doc_khang_dinh_loai_hinh(contra_one_sent)}

    ra_contra = run_function_route(
        contra_one_sent,
        {
            "calls": [
                {"id": "c1", "fn": "prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"], "right": True},
                 "source": {"quotes": [contra_one_sent]}},
                {"id": "c2", "fn": "rectangle", "args": {"vertices": list("ABCD")},
                 "source": {"quotes": ["Cho hình hộp chữ nhật ABCD.A'B'C'D'"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "2"},
                 "source": {"quotes": ["AB = 2"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "D"], "value": "2"},
                 "source": {"quotes": ["AD = 2"]}},
                {"id": "c5", "fn": "segment_length", "args": {"segment": ["B", "B'"], "value": "3"},
                 "source": {"quotes": ["BB' = 3"]}},
            ]
        },
    )
    assert ra_contra.status == "REFUSED" and ra_contra.code == "INCONSISTENT_FACTS"

    # 2. Valid symmetric twin: secondary solid D.ABB'A' genuinely has square base ABB'A' (2 x 2), while ABCD is 2 x 3
    valid_one_sent = (
        "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = 2, AD = 3, AA' = 2, "
        "hình chóp D.ABB'A' có đáy là hình vuông."
    )
    ra_valid = run_function_route(
        valid_one_sent,
        {
            "calls": [
                {"id": "c1", "fn": "prism", "args": {"base": list("ABCD"), "top": ["A'", "B'", "C'", "D'"], "right": True},
                 "source": {"quotes": [valid_one_sent]}},
                {"id": "c2", "fn": "rectangle", "args": {"vertices": list("ABCD")},
                 "source": {"quotes": ["Cho hình hộp chữ nhật ABCD.A'B'C'D'"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "2"},
                 "source": {"quotes": ["AB = 2"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "D"], "value": "3"},
                 "source": {"quotes": ["AD = 3"]}},
                {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "2"},
                 "source": {"quotes": ["AA' = 2"]}},
            ]
        },
    )
    assert ra_valid.status == "SERVED", (ra_valid.code, ra_valid.reason)

    # 3. Multi-solid Route B (`len(khoi_calls) == 2`): S.ABCD (2a x 3a) + derived pyramid S.ABNM where M, N divide AD, BC at 2/3 -> ABNM is 2a x 2a square (SERVED), vs midpoints (2a x 1.5a -> INCONSISTENT_FACTS)
    multi_valid_txt = (
        "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 2a, AD = 3a, SA vuông góc với (ABCD), SA = 2a. "
        "Gọi M thuộc cạnh AD sao cho AM = 2MD, N thuộc cạnh BC sao cho BN = 2NC. "
        "Xét hình chóp S.ABNM có đáy là hình vuông. Tính tỉ số thể tích của khối chóp S.ABNM và khối chóp S.ABCD."
    )
    r_multi_valid = run_fact_route(
        multi_valid_txt,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABCD",
                 "quotes": ["Cho hình chóp S.ABCD"]},
                {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "rectangle", "points": list("ABCD"),
                 "quotes": ["đáy ABCD là hình chữ nhật"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "2a",
                 "quotes": ["AB = 2a"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "3a",
                 "quotes": ["AD = 3a"]},
                {"id": "f5", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": list("ABCD"),
                 "quotes": ["SA vuông góc với (ABCD)"]},
                {"id": "f6", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "2a",
                 "quotes": ["SA = 2a"]},
                {"id": "m1", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "divide_segment",
                 "points": ["A", "D"], "value": "2/3", "quotes": ["M thuộc cạnh AD sao cho AM = 2MD"]},
                {"id": "m2", "kind": "point_def", "role": "premise", "point": "N", "point_kind": "divide_segment",
                 "points": ["B", "C"], "value": "2/3", "quotes": ["N thuộc cạnh BC sao cho BN = 2NC"]},
                {"id": "f7", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABNM",
                 "quotes": ["Xét hình chóp S.ABNM có đáy là hình vuông"]},
                {"id": "g1", "kind": "question", "role": "question", "quantity": "volume_ratio", "solid_refs": ["f7", "f1"],
                 "quotes": ["Tính tỉ số thể tích của khối chóp S.ABNM và khối chóp S.ABCD"]},
            ]
        },
    )
    assert r_multi_valid.status == "SERVED", (r_multi_valid.code, r_multi_valid.reason)

    multi_contra_txt = multi_valid_txt.replace("AD = 3a", "AD = 4a")
    r_multi_contra = run_fact_route(
        multi_contra_txt,
        {
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABCD",
                 "quotes": ["Cho hình chóp S.ABCD"]},
                {"id": "f2", "kind": "polygon_shape", "role": "premise", "shape": "rectangle", "points": list("ABCD"),
                 "quotes": ["đáy ABCD là hình chữ nhật"]},
                {"id": "f3", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "B"], "value": "2a",
                 "quotes": ["AB = 2a"]},
                {"id": "f4", "kind": "length", "role": "premise", "measure": "segment", "points": ["A", "D"], "value": "4a",
                 "quotes": ["AD = 4a"]},
                {"id": "f5", "kind": "perpendicular", "role": "premise", "points_a": ["S", "A"], "points_b": list("ABCD"),
                 "quotes": ["SA vuông góc với (ABCD)"]},
                {"id": "f6", "kind": "length", "role": "premise", "measure": "segment", "points": ["S", "A"], "value": "2a",
                 "quotes": ["SA = 2a"]},
                {"id": "m1", "kind": "point_def", "role": "premise", "point": "M", "point_kind": "divide_segment",
                 "points": ["A", "D"], "value": "2/3", "quotes": ["M thuộc cạnh AD sao cho AM = 2MD"]},
                {"id": "m2", "kind": "point_def", "role": "premise", "point": "N", "point_kind": "divide_segment",
                 "points": ["B", "C"], "value": "2/3", "quotes": ["N thuộc cạnh BC sao cho BN = 2NC"]},
                {"id": "f7", "kind": "solid", "role": "premise", "solid_type": "pyramid", "solid": "S.ABNM",
                 "quotes": ["Xét hình chóp S.ABNM có đáy là hình vuông"]},
                {"id": "g1", "kind": "question", "role": "question", "quantity": "volume_ratio", "solid_refs": ["f7", "f1"],
                 "quotes": ["Tính tỉ số thể tích của khối chóp S.ABNM và khối chóp S.ABCD"]},
            ]
        },
    )
    assert r_multi_contra.status == "REFUSED" and r_multi_contra.code == "INCONSISTENT_FACTS"

    # 4. Re-apexed tetrahedron: S.ABC vs A.SBC do NOT collide in _khop_ky_hieu_khoi / _loai_cum_dung / doc_khang_dinh_loai_hinh
    tet_calls = doc_ke_hoach({
        "calls": [
            {"id": "t1", "fn": "regular_pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]},
             "source": {"quotes": ["Cho hình chóp tam giác đều S.ABC"]}},
            {"id": "t2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C"], "side": "2"},
             "source": {"quotes": ["Cho hình chóp tam giác đều S.ABC"]}},
            {"id": "t3", "fn": "pyramid", "args": {"apex": "A", "base": ["S", "B", "C"]},
             "source": {"quotes": ["Xét hình chóp A.SBC có đáy là tam giác đều"]}},
        ]
    })
    assert _khop_ky_hieu_khoi(tet_calls[0], "S.ABC") and not _khop_ky_hieu_khoi(tet_calls[0], "A.SBC")
    assert _khop_ky_hieu_khoi(tet_calls[2], "A.SBC") and not _khop_ky_hieu_khoi(tet_calls[2], "S.ABC")
    assert _loai_cum_dung("hình chóp tam giác đều", "S.ABC", calls=tet_calls)
    assert not _loai_cum_dung("hình chóp tam giác đều", "A.SBC", calls=tet_calls)
    kd_tet = doc_khang_dinh_loai_hinh(
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A. Xét hình chóp A.SBC có đáy là tam giác đều.",
        tet_calls,
    )
    assert ("equilateral_triangle", ("S", "B", "C")) in {(x.kind, x.vertices) for x in kd_tet}
    assert all(x.kind != "ambiguous_base" for x in kd_tet)

    reapex_ok_one_sent = (
        "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại A, AB = 2, AC = 2, "
        "SA vuông góc với (ABC), SA = 2, hình chóp A.SBC có đáy là tam giác đều."
    )
    ra_reapex_ok = run_function_route(
        reapex_ok_one_sent,
        {
            "calls": [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]},
                 "source": {"quotes": [reapex_ok_one_sent]}},
                {"id": "c2", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]},
                 "source": {"quotes": ["tam giác vuông cân tại A"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "2"},
                 "source": {"quotes": ["AB = 2"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "2"},
                 "source": {"quotes": ["AC = 2"]}},
                {"id": "c5", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                 "source": {"quotes": ["SA vuông góc với (ABC)"]}},
                {"id": "c6", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "2"},
                 "source": {"quotes": ["SA = 2"]}},
            ]
        },
    )
    assert ra_reapex_ok.status == "SERVED", (ra_reapex_ok.code, ra_reapex_ok.reason)

    reapex_bad_one_sent = reapex_ok_one_sent.replace("SA = 2,", "SA = 3,")
    ra_reapex_bad = run_function_route(
        reapex_bad_one_sent,
        {
            "calls": [
                {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C"]},
                 "source": {"quotes": [reapex_bad_one_sent]}},
                {"id": "c2", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]},
                 "source": {"quotes": ["tam giác vuông cân tại A"]}},
                {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "2"},
                 "source": {"quotes": ["AB = 2"]}},
                {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "2"},
                 "source": {"quotes": ["AC = 2"]}},
                {"id": "c5", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C"]},
                 "source": {"quotes": ["SA vuông góc với (ABC)"]}},
                {"id": "c6", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "3"},
                 "source": {"quotes": ["SA = 3"]}},
            ]
        },
    )
    assert ra_reapex_bad.status == "REFUSED" and ra_reapex_bad.code == "INCONSISTENT_FACTS"

    # 5. Coordinated multi-solid clause with unlabelled "đáy là ..." fails closed with AMBIGUOUS_REFERENCE
    amb_txt = (
        "Cho hai hình chóp S.ABC và S.ABD có đáy là tam giác đều, AB = 2a, BC = 2a, AC = 2a, "
        "SA vuông góc với (ABC), SA = 2a. Tính thể tích khối chóp S.ABC."
    )
    r_amb = run_typed_fact_next_v2_route(
        _v2_payload(
            amb_txt,
            solid_type="pyramid",
            notation="S.ABC",
            solid_quote="Cho hai hình chóp S.ABC và S.ABD có đáy là tam giác đều",
            premises=[
                _p("segment_length", "AB = 2a", segment=["A", "B"], value="2a"),
                _p("segment_length", "BC = 2a", segment=["B", "C"], value="2a"),
                _p("segment_length", "AC = 2a", segment=["A", "C"], value="2a"),
                _p("perpendicular_line_plane", "SA vuông góc với (ABC)", line=["S", "A"], plane=["A", "B", "C"]),
                _p("segment_length", "SA = 2a", segment=["S", "A"], value="2a"),
            ],
            math_goals=[_vol_goal("Tính thể tích khối chóp S.ABC")],
        )
    )
    assert r_amb.status == "REFUSED" and r_amb.code == "AMBIGUOUS_REFERENCE"


def test_minor_r3_1_three_solid_coordination_and_post_nominal_modifiers():
    """MINOR-R3-1: 3+ coordinated solids walk the entire coordinated chain, and post-nominal solid modifiers bind cleanly."""
    from app.simulation.geometry_functions.registry import doc_khang_dinh_loai_hinh

    # 3 coordinated solids where last two share ABD but first has ABC -> ambiguous_base () -> AMBIGUOUS_REFERENCE
    kds_3 = doc_khang_dinh_loai_hinh("Cho ba hình chóp S.ABC, S.ABD và M.ABD có đáy là tam giác đều.")
    assert any(kd.kind == "ambiguous_base" and kd.vertices == () for kd in kds_3)
    assert not any(kd.kind == "equilateral_triangle" for kd in kds_3)

    # 3 coordinated solids all sharing ABD -> uniquely resolves ('A', 'B', 'D')
    kds_3_same = doc_khang_dinh_loai_hinh("Cho ba hình chóp S.ABD, M.ABD và N.ABD có chung đáy là tam giác đều.")
    assert any(kd.kind == "equilateral_triangle" and kd.vertices == ("A", "B", "D") for kd in kds_3_same)

    # Post-nominal solid modifier after second solid in same sentence binds to second solid's base
    kds_post = doc_khang_dinh_loai_hinh(
        "Cho hình chóp S.ABCD, xét hình lăng trụ EFG.E'F'G' đứng có đáy là tam giác đều."
    )
    assert any(kd.kind == "equilateral_triangle" and kd.vertices == ("E", "F", "G") for kd in kds_post)





