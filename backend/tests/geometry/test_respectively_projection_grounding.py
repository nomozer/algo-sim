# -*- coding: utf-8 -*-
"""Source Gate: "H, K lần lượt là hình chiếu vuông góc của A trên SB, SC" binds each name to its operand IN ORDER.

Found by the hybrid-master development probe (`tools/topology_probe.py`, T3.HK): the planner already composes HK from
two projections (split clauses are served exactly), but the projection grammar read one name per clause, so the
respectively form — which the LLM_ONLY grounding reads (W18) and midpoints/centroids already read on Route D — was
refused `SOURCE_OBJECT_MISMATCH`. Same discipline as `_dinh_nghia_diem_dung_nguon`: equal counts, ordered pairing,
several names only with "lần lượt". 0 provider calls.

Chart (hand oracle): A(0,0,0) B(3,0,0) C(3,4,0) S(0,0,4); AH ⊥ (SBC) ⇒ HK² = AK² − AH² = 400/41 − 144/25 = 4096/1025.
"""
from __future__ import annotations

from fractions import Fraction

import pytest

from app.ai.adapter4_route import run_typed_fact_next_v2_route
from app.simulation.geometry_functions.registry import REGISTRY_VERSION

GIVEN = ("Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, SA vuông góc với mặt phẳng (ABC) "
         "và SA = 4.")


def _p(kind, quote, **args):
    return {"kind": kind, "args": args, "quote": quote, "solid_id": "s1"}


BASE = [_p("right_angle", "đáy ABC là tam giác vuông tại B", vertex="B", rays=["A", "C"]),
        _p("segment_length", "AB = 3", segment=["A", "B"], value="3"),
        _p("segment_length", "BC = 4", segment=["B", "C"], value="4"),
        _p("perpendicular_line_plane", "SA vuông góc với mặt phẳng (ABC)", line=["S", "A"], plane=["A", "B", "C"]),
        _p("segment_length", "SA = 4", segment=["S", "A"], value="4")]


def _run(clause, images, ask=("H", "K")):
    """`images` = [(source point, image, line)] — one projection premise per entry, all quoting `clause`."""
    question = "Tính độ dài " + "".join(ask) + "."
    text = f"{GIVEN} {clause}. {question}"
    return run_typed_fact_next_v2_route({
        "schema_version": "typed-fact-next/2", "problem_text": text, "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABC", "quote": "Cho hình chóp S.ABC"}],
        "premises": [*BASE, *(_p("orthogonal_projection_line", clause, point=p, image=i, line=list(d))
                              for p, i, d in images)],
        "derived_sections": [], "relations": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1",
                              "quote": "Cho hình chóp S.ABC"}],
        "math_goals": [{"goal_id": "mg1", "kind": "measurement", "goal_type": "distance", "solid_id": "s1",
                        "target": {"segment": list(ask)}, "quote": question.rstrip(".")}]})


RESPECTIVELY = "Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SC"


def _squared(coef: str) -> Fraction:
    num, _, den = coef.partition("/")
    p, _, r = num.partition("√")
    return Fraction(int(p or 1) ** 2 * int(r or 1), int(den or 1) ** 2)


def test_respectively_projections_bind_in_order_and_compose_exactly():
    r = run_typed_fact_next_v2_route  # noqa: F841 — the route is the only authority exercised
    out = _run(RESPECTIVELY, [("A", "H", "SB"), ("A", "K", "SC")])
    assert out.status == "SERVED" and out.kernel_check is True, (out.code, out.reason)
    assert _squared(out.answer_exact["mg1"]["coef"]) == Fraction(4096, 1025)


@pytest.mark.parametrize("clause,images", [
    (RESPECTIVELY, [("A", "H", "SC"), ("A", "K", "SB")]),                           # pairing swapped
    ("Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB", [("A", "H", "SB"), ("A", "K", "SB")]),  # 2 names, 1 line
    ("Gọi H, K là hình chiếu vuông góc của A trên SB, SC", [("A", "H", "SB"), ("A", "K", "SC")]),     # no "lần lượt"
    (RESPECTIVELY, [("B", "H", "SB"), ("A", "K", "SC")]),                           # wrong source point
    ("Gọi H, K lần lượt là hình chiếu vuông góc của A trên SB, SC, BC", [("A", "H", "SB"), ("A", "K", "SC")]),
])
def test_a_misbound_respectively_list_is_refused(clause, images):
    out = _run(clause, images)
    assert out.status == "REFUSED" and not out.answer_exact and out.scene3d is None
    assert out.code in {"SOURCE_OBJECT_MISMATCH", "ROLE_NOT_IN_QUOTE"}, (out.code, out.reason)


def test_a_single_name_clause_is_unchanged():
    out = _run("Gọi H là hình chiếu vuông góc của A trên SB", [("A", "H", "SB")], ask=("A", "H"))
    assert out.status == "SERVED" and _squared(out.answer_exact["mg1"]["coef"]) == Fraction(144, 25)


def test_registry_version_records_the_language_change():
    assert REGISTRY_VERSION == "geometry-functions/28"
