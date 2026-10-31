# -*- coding: utf-8 -*-
"""Offline probe corpus for certified circumscribed spheres of polyhedra on Route D /4
(run `hybrid-master-backend-replacement`, Continuation 8). 0 provider calls.

Hand-computed exact oracles:
- Right-angled tetrahedron O.ABC (OA, OB, OC pairwise ⊥ at O):
  • OA = OB = OC = 2  ⇒  I = (1, 1, 1), R = √3, S = 12π, V = 4π√3
  • OA = 2, OB = 3, OC = 6  ⇒  I = (1, 3/2, 3), R = 7/2, S = 49π, V = 343π/6
- Cube ABCD.A'B'C'D' of side 2  ⇒  R = √3, S = 12π, V = 4π√3
- Symbolic cube ABCD.A'B'C'D' of side a  ⇒  coef(R) = √3/2, coef(S) = 3π, coef(V) = π√3/2
- Rectangular box ABCD.A'B'C'D' (AB = 2, AD = 3, AA' = 6)  ⇒  R = 7/2, S = 49π
- Right pyramid S.ABCD over square side 2 with SA ⊥ (ABCD), SA = 2  ⇒  R = √3, S = 12π
- Right pyramid S.ABCD over rectangle AB = 3, BC = 4 with SA ⊥ (ABCD), SA = 12  ⇒  R = 13/2, S = 169π
- Regular square pyramid S.ABCD (base side 4, height 4)  ⇒  r_base² = 8, R = (16 + 8)/8 = 3, S = 36π, V = 36π
- Right triangular prism ABC.A'B'C' over right triangle at A (AB = 3, AC = 4, AA' = 12)  ⇒  R = 13/2, S = 169π
- Right triangular prism ABC.A'B'C' over right triangle at B (AB = 3, BC = 4, AA' = 12)  ⇒  R = 13/2, S = 169π
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any


def _prem(kind: str, args: dict[str, Any], quote: str, solid_id: str | None = "poly") -> dict[str, Any]:
    out: dict[str, Any] = {"kind": kind, "args": args, "quote": quote}
    if solid_id is not None:
        out["solid_id"] = solid_id
    return out


def make_payload(
    *,
    problem_text: str,
    poly_solid: dict[str, Any],
    premises: list[dict[str, Any]],
    sphere_notation: str = "(S)",
    sphere_quote: str,
    sphere_center: str | None = None,
    circumscribes: str | None = "poly",
    goal_type: str = "radius",
    goal_quote: str,
    length_unit: str | None = None,
) -> dict[str, Any]:
    sph: dict[str, Any] = {
        "solid_id": "sph",
        "solid_type": "sphere",
        "notation": sphere_notation,
        "quote": sphere_quote,
    }
    if sphere_center is not None:
        sph["center"] = sphere_center
    if circumscribes is not None:
        sph["circumscribes"] = circumscribes
    target = {"solid_id": "sph"} if goal_type == "volume" else {"solid": sphere_notation}
    out: dict[str, Any] = {
        "schema_version": "typed-fact-next/2",
        "problem_text": problem_text,
        "solids": [deepcopy(poly_solid), sph],
        "premises": deepcopy(premises),
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": poly_solid["solid_id"],
                "quote": poly_solid["quote"],
            }
        ],
        "math_goals": [
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": goal_type,
                "solid_id": "sph",
                "target": target,
                "quote": goal_quote,
            }
        ],
    }
    if length_unit is not None:
        out["length_unit"] = length_unit
    return out


# ── Canonical polyhedron building blocks ──────────────────────────────────────

TETRA_ISO_GIVEN = (
    "Cho tứ diện OABC có tam giác OAB vuông tại O, OC vuông góc với mặt phẳng (OAB) và OA = 2, OB = 2, OC = 2."
)
TETRA_ISO_SOLID = {
    "solid_id": "poly",
    "solid_type": "pyramid",
    "notation": "C.OAB",
    "quote": "Cho tứ diện OABC",
}
TETRA_ISO_PREMS = [
    _prem("right_angle", {"vertex": "O", "rays": ["A", "B"]}, "tam giác OAB vuông tại O"),
    _prem("perpendicular_line_plane", {"line": ["O", "C"], "plane": ["O", "A", "B"]},
          "OC vuông góc với mặt phẳng (OAB)"),
    _prem("segment_length", {"segment": ["O", "A"], "value": "2"}, "OA = 2"),
    _prem("segment_length", {"segment": ["O", "B"], "value": "2"}, "OB = 2"),
    _prem("segment_length", {"segment": ["O", "C"], "value": "2"}, "OC = 2"),
]

TETRA_236_GIVEN = (
    "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 2, AC = 3, SA vuông góc với mặt phẳng (ABC) và SA = 6."
)
TETRA_236_SOLID = {
    "solid_id": "poly",
    "solid_type": "pyramid",
    "notation": "S.ABC",
    "quote": "Cho hình chóp S.ABC",
}
TETRA_236_PREMS = [
    _prem("right_angle", {"vertex": "A", "rays": ["B", "C"]}, "đáy ABC là tam giác vuông tại A"),
    _prem("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]},
          "SA vuông góc với mặt phẳng (ABC)"),
    _prem("segment_length", {"segment": ["A", "B"], "value": "2"}, "AB = 2"),
    _prem("segment_length", {"segment": ["A", "C"], "value": "3"}, "AC = 3"),
    _prem("segment_length", {"segment": ["S", "A"], "value": "6"}, "SA = 6"),
]

CUBE_2_GIVEN = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng 2."
CUBE_2_SOLID = {
    "solid_id": "poly",
    "solid_type": "prism",
    "notation": "ABCD.A'B'C'D'",
    "quote": CUBE_2_GIVEN,
}
CUBE_2_PREMS = [
    _prem("right_prism", {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]}, CUBE_2_GIVEN),
    _prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "2"}, CUBE_2_GIVEN),
    _prem("segment_length", {"segment": ["A", "A'"], "value": "2"}, CUBE_2_GIVEN),
]

CUBE_A_GIVEN = "Cho hình lập phương ABCD.A'B'C'D' có cạnh bằng a."
CUBE_A_SOLID = {
    "solid_id": "poly",
    "solid_type": "prism",
    "notation": "ABCD.A'B'C'D'",
    "quote": CUBE_A_GIVEN,
}
CUBE_A_PREMS = [
    _prem("right_prism", {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]}, CUBE_A_GIVEN),
    _prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "a"}, CUBE_A_GIVEN),
    _prem("segment_length", {"segment": ["A", "A'"], "value": "a"}, CUBE_A_GIVEN),
]

BOX_236_GIVEN = (
    "Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 2, AD = 3, AA' = 6."
)
BOX_236_SOLID = {
    "solid_id": "poly",
    "solid_type": "prism",
    "notation": "ABCD.A'B'C'D'",
    "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'",
}
BOX_236_PREMS = [
    _prem("right_prism", {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]}, BOX_236_GIVEN),
    _prem("rectangle", {"vertices": ["A", "B", "C", "D"]}, "đáy ABCD là hình chữ nhật"),
    _prem("segment_length", {"segment": ["A", "B"], "value": "2"}, "AB = 2"),
    _prem("segment_length", {"segment": ["A", "D"], "value": "3"}, "AD = 3"),
    _prem("segment_length", {"segment": ["A", "A'"], "value": "6"}, "AA' = 6"),
]

PYR_SQ_GIVEN = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với mặt phẳng (ABCD) và SA = 2."
)
PYR_SQ_SOLID = {
    "solid_id": "poly",
    "solid_type": "pyramid",
    "notation": "S.ABCD",
    "quote": "Cho hình chóp S.ABCD",
}
PYR_SQ_PREMS = [
    _prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "2"}, "đáy ABCD là hình vuông cạnh 2"),
    _prem("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
          "SA vuông góc với mặt phẳng (ABCD)"),
    _prem("segment_length", {"segment": ["S", "A"], "value": "2"}, "SA = 2"),
]

PYR_RECT_GIVEN = (
    "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 3, BC = 4, SA vuông góc với (ABCD) và SA = 12."
)
PYR_RECT_SOLID = {
    "solid_id": "poly",
    "solid_type": "pyramid",
    "notation": "S.ABCD",
    "quote": "Cho hình chóp S.ABCD",
}
PYR_RECT_PREMS = [
    _prem("rectangle", {"vertices": ["A", "B", "C", "D"]}, "đáy ABCD là hình chữ nhật"),
    _prem("segment_length", {"segment": ["A", "B"], "value": "3"}, "AB = 3"),
    _prem("segment_length", {"segment": ["B", "C"], "value": "4"}, "BC = 4"),
    _prem("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
          "SA vuông góc với (ABCD)"),
    _prem("segment_length", {"segment": ["S", "A"], "value": "12"}, "SA = 12"),
]

REG_SQ_PYR_GIVEN = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4, chiều cao hình chóp bằng 4."
REG_SQ_PYR_SOLID = {
    "solid_id": "poly",
    "solid_type": "pyramid",
    "notation": "S.ABCD",
    "quote": "Cho hình chóp tứ giác đều S.ABCD",
}
REG_SQ_PYR_PREMS = [
    _prem("regular_pyramid", {"apex": "S", "base": ["A", "B", "C", "D"]}, "Cho hình chóp tứ giác đều S.ABCD"),
    _prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "4"},
          "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 4"),
    _prem("height", {"value": "4"}, "chiều cao hình chóp bằng 4", solid_id=None),
]

PRISM_RA_GIVEN = (
    "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, AA' = 12."
)
PRISM_RA_SOLID = {
    "solid_id": "poly",
    "solid_type": "prism",
    "notation": "ABC.A'B'C'",
    "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
}
PRISM_RA_PREMS = [
    _prem("right_prism", {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, "Cho hình lăng trụ đứng ABC.A'B'C'"),
    _prem("right_angle", {"vertex": "A", "rays": ["B", "C"]}, "đáy ABC là tam giác vuông tại A"),
    _prem("segment_length", {"segment": ["A", "B"], "value": "3"}, "AB = 3"),
    _prem("segment_length", {"segment": ["A", "C"], "value": "4"}, "AC = 4"),
    _prem("segment_length", {"segment": ["A", "A'"], "value": "12"}, "AA' = 12"),
]

PRISM_RB_GIVEN = (
    "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B, AB = 3, BC = 4, AA' = 12."
)
PRISM_RB_SOLID = {
    "solid_id": "poly",
    "solid_type": "prism",
    "notation": "ABC.A'B'C'",
    "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
}
PRISM_RB_PREMS = [
    _prem("right_prism", {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, "Cho hình lăng trụ đứng ABC.A'B'C'"),
    _prem("right_angle", {"vertex": "B", "rays": ["A", "C"]}, "đáy ABC là tam giác vuông tại B"),
    _prem("segment_length", {"segment": ["A", "B"], "value": "3"}, "AB = 3"),
    _prem("segment_length", {"segment": ["B", "C"], "value": "4"}, "BC = 4"),
    _prem("segment_length", {"segment": ["A", "A'"], "value": "12"}, "AA' = 12"),
]


POSITIVE_CASES: list[tuple[str, dict[str, Any], str]] = [
    (
        "cs.tetra_iso.radius",
        make_payload(
            problem_text=TETRA_ISO_GIVEN + " Tính bán kính mặt cầu ngoại tiếp tứ diện OABC.",
            poly_solid=TETRA_ISO_SOLID,
            premises=TETRA_ISO_PREMS,
            sphere_notation="(C.OAB)",
            sphere_quote="Tính bán kính mặt cầu ngoại tiếp tứ diện OABC.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp tứ diện OABC.",
        ),
        "√3",
    ),
    (
        "cs.tetra_iso.volume",
        make_payload(
            problem_text=TETRA_ISO_GIVEN + " Gọi (S) là mặt cầu ngoại tiếp tứ diện OABC. Tính thể tích khối cầu (S).",
            poly_solid=TETRA_ISO_SOLID,
            premises=TETRA_ISO_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu ngoại tiếp tứ diện OABC.",
            goal_type="volume",
            goal_quote="Tính thể tích khối cầu (S).",
        ),
        "4π√3",
    ),
    (
        "cs.tetra_236.surface_area",
        make_payload(
            problem_text=TETRA_236_GIVEN + " Tính diện tích mặt cầu ngoại tiếp hình chóp S.ABC.",
            poly_solid=TETRA_236_SOLID,
            premises=TETRA_236_PREMS,
            sphere_notation="()",
            sphere_quote="Tính diện tích mặt cầu ngoại tiếp hình chóp S.ABC.",
            goal_type="area",
            goal_quote="Tính diện tích mặt cầu ngoại tiếp hình chóp S.ABC.",
        ),
        "49π",
    ),
    (
        "cs.tetra_236.volume",
        make_payload(
            problem_text=TETRA_236_GIVEN + " Tính thể tích khối cầu ngoại tiếp hình chóp S.ABC.",
            poly_solid=TETRA_236_SOLID,
            premises=TETRA_236_PREMS,
            sphere_notation="(S.ABC)",
            sphere_quote="Tính thể tích khối cầu ngoại tiếp hình chóp S.ABC.",
            goal_type="volume",
            goal_quote="Tính thể tích khối cầu ngoại tiếp hình chóp S.ABC.",
        ),
        "343π/6",
    ),
    (
        "cs.cube_2.surface_area",
        make_payload(
            problem_text=CUBE_2_GIVEN + " Tính diện tích mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(ABCD.A'B'C'D')",
            sphere_quote="Tính diện tích mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="area",
            goal_quote="Tính diện tích mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
        ),
        "12π",
    ),
    (
        "cs.box_236.radius",
        make_payload(
            problem_text=BOX_236_GIVEN + " Tính bán kính mặt cầu ngoại tiếp hình hộp chữ nhật ABCD.A'B'C'D'.",
            poly_solid=BOX_236_SOLID,
            premises=BOX_236_PREMS,
            sphere_notation="(ABCD.A'B'C'D')",
            sphere_quote="Tính bán kính mặt cầu ngoại tiếp hình hộp chữ nhật ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình hộp chữ nhật ABCD.A'B'C'D'.",
        ),
        "7/2",
    ),
    (
        "cs.pyr_sq.named_center",
        make_payload(
            problem_text=PYR_SQ_GIVEN
            + " Gọi I là tâm mặt cầu ngoại tiếp hình chóp S.ABCD. Tính diện tích mặt cầu ngoại tiếp hình chóp S.ABCD.",
            poly_solid=PYR_SQ_SOLID,
            premises=PYR_SQ_PREMS,
            sphere_notation="I",
            sphere_center="I",
            sphere_quote="Gọi I là tâm mặt cầu ngoại tiếp hình chóp S.ABCD.",
            goal_type="area",
            goal_quote="Tính diện tích mặt cầu ngoại tiếp hình chóp S.ABCD.",
        ),
        "12π",
    ),
    (
        "cs.pyr_sq.midpoint_center",
        make_payload(
            problem_text=PYR_SQ_GIVEN
            + " Gọi I là trung điểm của SC. Biết I là tâm mặt cầu ngoại tiếp hình chóp S.ABCD. Tính bán kính mặt cầu ngoại tiếp hình chóp.",
            poly_solid=PYR_SQ_SOLID,
            premises=[
                *PYR_SQ_PREMS,
                _prem("midpoint", {"point": "I", "segment": ["S", "C"]}, "Gọi I là trung điểm của SC."),
            ],
            sphere_notation="I",
            sphere_center="I",
            sphere_quote="Biết I là tâm mặt cầu ngoại tiếp hình chóp S.ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình chóp.",
        ),
        "√3",
    ),
    (
        "cs.pyr_rect.surface_area",
        make_payload(
            problem_text=PYR_RECT_GIVEN + " Tính diện tích mặt cầu ngoại tiếp hình chóp S.ABCD.",
            poly_solid=PYR_RECT_SOLID,
            premises=PYR_RECT_PREMS,
            sphere_notation="(S.ABCD)",
            sphere_quote="Tính diện tích mặt cầu ngoại tiếp hình chóp S.ABCD.",
            goal_type="area",
            goal_quote="Tính diện tích mặt cầu ngoại tiếp hình chóp S.ABCD.",
        ),
        "169π",
    ),
    (
        "cs.reg_sq_pyr.volume",
        make_payload(
            problem_text=REG_SQ_PYR_GIVEN + " Tính thể tích khối cầu ngoại tiếp hình chóp S.ABCD.",
            poly_solid=REG_SQ_PYR_SOLID,
            premises=REG_SQ_PYR_PREMS,
            sphere_notation="(S.ABCD)",
            sphere_quote="Tính thể tích khối cầu ngoại tiếp hình chóp S.ABCD.",
            goal_type="volume",
            goal_quote="Tính thể tích khối cầu ngoại tiếp hình chóp S.ABCD.",
        ),
        "36π",
    ),
    (
        "cs.prism_ra.radius",
        make_payload(
            problem_text=PRISM_RA_GIVEN + " Tính bán kính mặt cầu ngoại tiếp hình lăng trụ ABC.A'B'C'.",
            poly_solid=PRISM_RA_SOLID,
            premises=PRISM_RA_PREMS,
            sphere_notation="(ABC.A'B'C')",
            sphere_quote="Tính bán kính mặt cầu ngoại tiếp hình lăng trụ ABC.A'B'C'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình lăng trụ ABC.A'B'C'.",
        ),
        "13/2",
    ),
    (
        "cs.prism_rb.surface_area",
        make_payload(
            problem_text=PRISM_RB_GIVEN + " Tính diện tích mặt cầu ngoại tiếp hình lăng trụ đứng ABC.A'B'C'.",
            poly_solid=PRISM_RB_SOLID,
            premises=PRISM_RB_PREMS,
            sphere_notation="(ABC.A'B'C')",
            sphere_quote="Tính diện tích mặt cầu ngoại tiếp hình lăng trụ đứng ABC.A'B'C'.",
            goal_type="area",
            goal_quote="Tính diện tích mặt cầu ngoại tiếp hình lăng trụ đứng ABC.A'B'C'.",
        ),
        "169π",
    ),
]


NEGATIVE_CASES: list[tuple[str, dict[str, Any], str]] = [
    (
        "cs.neg.oblique_prism_not_cospheric",
        make_payload(
            problem_text=(
                "Cho hình lăng trụ ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 2, AC = 2. "
                "Hình chiếu vuông góc của A' lên mặt phẳng (ABC) là B và A'B = 2. "
                "Tính bán kính mặt cầu ngoại tiếp hình lăng trụ ABC.A'B'C'."
            ),
            poly_solid={
                "solid_id": "poly",
                "solid_type": "prism",
                "notation": "ABC.A'B'C'",
                "quote": "Cho hình lăng trụ ABC.A'B'C'",
            },
            premises=[
                _prem("right_angle", {"vertex": "A", "rays": ["B", "C"]}, "đáy ABC là tam giác vuông tại A"),
                _prem("segment_length", {"segment": ["A", "B"], "value": "2"}, "AB = 2"),
                _prem("segment_length", {"segment": ["A", "C"], "value": "2"}, "AC = 2"),
                _prem("orthogonal_projection", {"point": "A'", "image": "B", "plane": ["A", "B", "C"]},
                      "Hình chiếu vuông góc của A' lên mặt phẳng (ABC) là B"),
                _prem("segment_length", {"segment": ["A'", "B"], "value": "2"}, "A'B = 2"),
            ],
            sphere_notation="(ABC.A'B'C')",
            sphere_quote="Tính bán kính mặt cầu ngoại tiếp hình lăng trụ ABC.A'B'C'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình lăng trụ ABC.A'B'C'.",
        ),
        "NO_CIRCUMSCRIBED_SPHERE",
    ),
    (
        "cs.neg.right_trapezoid_pyramid_not_cospheric",
        make_payload(
            problem_text=(
                "Cho hình chóp S.ABCD có đáy ABCD vuông tại A và B, AB = 2, AD = 2, BC = 4, "
                "SA vuông góc với (ABCD) và SA = 2. Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD."
            ),
            poly_solid=PYR_SQ_SOLID,
            premises=[
                _prem("right_angle", {"vertex": "A", "rays": ["B", "D"]},
                      "Cho hình chóp S.ABCD có đáy ABCD vuông tại A và B"),
                _prem("right_angle", {"vertex": "B", "rays": ["A", "C"]},
                      "Cho hình chóp S.ABCD có đáy ABCD vuông tại A và B"),
                _prem("segment_length", {"segment": ["A", "B"], "value": "2"}, "AB = 2"),
                _prem("segment_length", {"segment": ["A", "D"], "value": "2"}, "AD = 2"),
                _prem("segment_length", {"segment": ["B", "C"], "value": "4"}, "BC = 4"),
                _prem("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                      "SA vuông góc với (ABCD)"),
                _prem("segment_length", {"segment": ["S", "A"], "value": "2"}, "SA = 2"),
            ],
            sphere_notation="(S.ABCD)",
            sphere_quote="Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD.",
        ),
        "NO_CIRCUMSCRIBED_SPHERE",
    ),
    (
        "cs.neg.non_euclidean_equilateral_base",
        make_payload(
            problem_text=(
                "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2, chiều cao hình chóp bằng 2. "
                "Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABC."
            ),
            poly_solid={
                "solid_id": "poly",
                "solid_type": "pyramid",
                "notation": "S.ABC",
                "quote": "Cho hình chóp tam giác đều S.ABC",
            },
            premises=[
                _prem("regular_pyramid", {"apex": "S", "base": ["A", "B", "C"]}, "Cho hình chóp tam giác đều S.ABC"),
                _prem("regular_polygon", {"vertices": ["A", "B", "C"], "side": "2"},
                      "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2"),
                _prem("height", {"value": "2"}, "chiều cao hình chóp bằng 2", solid_id=None),
            ],
            sphere_notation="(S.ABC)",
            sphere_quote="Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABC.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABC.",
        ),
        "METRIC_REQUIRES_EUCLIDEAN_CHART",
    ),
    (
        "cs.neg.contradictory_named_center",
        make_payload(
            problem_text=PYR_SQ_GIVEN
            + " Gọi I là trung điểm của SA. Biết I là tâm mặt cầu ngoại tiếp hình chóp S.ABCD. Tính bán kính mặt cầu ngoại tiếp hình chóp.",
            poly_solid=PYR_SQ_SOLID,
            premises=[
                *PYR_SQ_PREMS,
                _prem("midpoint", {"point": "I", "segment": ["S", "A"]}, "Gọi I là trung điểm của SA."),
            ],
            sphere_notation="I",
            sphere_center="I",
            sphere_quote="Biết I là tâm mặt cầu ngoại tiếp hình chóp S.ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình chóp.",
        ),
        "INCONSISTENT_FACTS",
    ),
    (
        "cs.neg.inscribed_sphere_wording",
        make_payload(
            problem_text=CUBE_2_GIVEN
            + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'. Tính bán kính mặt cầu (S).",
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
        ),
        "CURVED_WORDING_UNSUPPORTED",
    ),
    (
        "cs.neg.inscribed_sphere_in_question",
        make_payload(
            problem_text=CUBE_2_GIVEN + " Tính bán kính mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(ABCD.A'B'C'D')",
            sphere_quote="Tính bán kính mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
        ),
        "NOT_ASKED_IN_SOURCE",
    ),
    (
        "cs.neg.circumcircle_2d_wording",
        make_payload(
            problem_text=PYR_SQ_GIVEN + " Tính bán kính đường tròn ngoại tiếp hình vuông ABCD.",
            poly_solid=PYR_SQ_SOLID,
            premises=PYR_SQ_PREMS,
            sphere_notation="(S.ABCD)",
            sphere_quote="Tính bán kính đường tròn ngoại tiếp hình vuông ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính đường tròn ngoại tiếp hình vuông ABCD.",
        ),
        "SOURCE_OBJECT_MISMATCH",
    ),
    (
        "cs.neg.circumcircle_2d_named",
        make_payload(
            problem_text=PYR_SQ_GIVEN
            + " Gọi (S) là đường tròn ngoại tiếp hình vuông ABCD. Tính bán kính mặt cầu (S).",
            poly_solid=PYR_SQ_SOLID,
            premises=PYR_SQ_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là đường tròn ngoại tiếp hình vuông ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
        ),
        "PREDICATE_NOT_IN_QUOTE",
    ),
    (
        "cs.neg.mismatched_polyhedron_kind",
        make_payload(
            problem_text=PYR_SQ_GIVEN + " Tính bán kính mặt cầu ngoại tiếp hình lập phương S.ABCD.",
            poly_solid=PYR_SQ_SOLID,
            premises=PYR_SQ_PREMS,
            sphere_notation="(S.ABCD)",
            sphere_quote="Tính bán kính mặt cầu ngoại tiếp hình lập phương S.ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình lập phương S.ABCD.",
        ),
        "SOURCE_OBJECT_MISMATCH",
    ),
    (
        "cs.neg.ungrounded_sphere_notation",
        make_payload(
            problem_text=PYR_SQ_GIVEN + " Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD.",
            poly_solid=PYR_SQ_SOLID,
            premises=PYR_SQ_PREMS,
            sphere_notation="(S)",
            sphere_quote="Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD.",
        ),
        "SOURCE_OBJECT_MISMATCH",
    ),
    (
        "cs.neg.sphere_lateral_area",
        make_payload(
            problem_text=CUBE_2_GIVEN + " Tính diện tích xung quanh của mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(ABCD.A'B'C'D')",
            sphere_quote="Tính diện tích xung quanh của mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="lateral_area",
            goal_quote="Tính diện tích xung quanh của mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
        ),
        "CURVED_MEASURE_UNDEFINED",
    ),
    (
        "cs.neg.composite_without_circumscribes",
        make_payload(
            problem_text=CUBE_2_GIVEN + " Tính bán kính mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(S)",
            circumscribes=None,
            sphere_quote="Tính bán kính mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
        ),
        "BRIDGE_UNSUPPORTED_CURVED_COMPOSITE",
    ),
]
