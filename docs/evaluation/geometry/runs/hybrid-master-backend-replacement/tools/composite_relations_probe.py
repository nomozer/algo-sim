# -*- coding: utf-8 -*-
"""Deterministic probe & preregistered hand-computed exact oracles for Continuation 9:
Multi-Object FactGraph + Composite Geometry + Generalized Geometric Relations on Route D `/4`.

0 live provider calls. Every positive oracle is derived by hand from closed-form Euclidean
solid geometry before production implementation (TDD RED -> GREEN).
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
from typing import Any


def _prem(kind: str, args: dict[str, Any], quote: str, solid_id: str | None = "poly") -> dict[str, Any]:
    out: dict[str, Any] = {"kind": kind, "args": args, "quote": quote}
    if solid_id is not None:
        out["solid_id"] = solid_id
    return out


# ---------------------------------------------------------------------------
# Reusable base polyhedron building blocks
# ---------------------------------------------------------------------------
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

PYR_SQ_64_GIVEN = "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6, chiều cao hình chóp bằng 4."
PYR_SQ_64_SOLID = {
    "solid_id": "poly",
    "solid_type": "pyramid",
    "notation": "S.ABCD",
    "quote": "Cho hình chóp tứ giác đều S.ABCD",
}
PYR_SQ_64_PREMS = [
    _prem("regular_pyramid", {"apex": "S", "base": ["A", "B", "C", "D"]},
          "Cho hình chóp tứ giác đều S.ABCD"),
    _prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "6"},
          "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6"),
    _prem("height", {"value": "4"}, "chiều cao hình chóp bằng 4", solid_id=None),
]

PRISM_345_H2_GIVEN = (
    "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, "
    "AB = 3, AC = 4, AA' = 2."
)
PRISM_345_H2_SOLID = {
    "solid_id": "poly",
    "solid_type": "prism",
    "notation": "ABC.A'B'C'",
    "quote": "Cho lăng trụ đứng ABC.A'B'C'",
}
PRISM_345_H2_PREMS = [
    _prem("right_prism", {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
          "Cho lăng trụ đứng ABC.A'B'C'"),
    _prem("right_angle", {"vertex": "A", "rays": ["B", "C"]}, "đáy ABC là tam giác vuông tại A"),
    _prem("segment_length", {"segment": ["A", "B"], "value": "3"}, "AB = 3"),
    _prem("segment_length", {"segment": ["A", "C"], "value": "4"}, "AC = 4"),
    _prem("segment_length", {"segment": ["A", "A'"], "value": "2"}, "AA' = 2"),
]

TETRA_132_GIVEN = (
    "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại A, AB = 3, AC = 2, "
    "SA vuông góc với mặt phẳng (ABC) và SA = 1."
)
TETRA_132_SOLID = {
    "solid_id": "poly",
    "solid_type": "pyramid",
    "notation": "S.ABC",
    "quote": "Cho hình chóp S.ABC",
}
TETRA_132_PREMS = [
    _prem("right_angle", {"vertex": "A", "rays": ["B", "C"]}, "đáy ABC là tam giác vuông tại A"),
    _prem("segment_length", {"segment": ["A", "B"], "value": "3"}, "AB = 3"),
    _prem("segment_length", {"segment": ["A", "C"], "value": "2"}, "AC = 2"),
    _prem("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C"]},
          "SA vuông góc với mặt phẳng (ABC)"),
    _prem("segment_length", {"segment": ["S", "A"], "value": "1"}, "SA = 1"),
]


def _sphere_goal(goal_id: str, goal_type: str, solid_id: str, notation: str, quote: str) -> dict[str, Any]:
    target = {"solid_id": solid_id} if goal_type == "volume" else {"solid": notation}
    return {
        "goal_id": goal_id,
        "kind": "measurement",
        "goal_type": goal_type,
        "solid_id": solid_id,
        "target": target,
        "quote": quote,
    }


def make_inscribed_payload(
    *,
    problem_text: str,
    poly_solid: dict[str, Any],
    premises: list[dict[str, Any]],
    sphere_notation: str,
    sphere_quote: str,
    goal_type: str,
    goal_quote: str,
    sphere_center: str | None = None,
    use_relation_spec: bool = False,
    extra_relations: list[dict[str, Any]] | None = None,
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
    rels = list(extra_relations or [])
    if use_relation_spec:
        rels.insert(
            0,
            {
                "relation_id": "rel_ins",
                "kind": "inscribed_in",
                "solid_a": "sph",
                "solid_b": poly_solid["solid_id"],
                "quote": sphere_quote,
            },
        )
    else:
        sph["inscribed_in"] = poly_solid["solid_id"]
    out: dict[str, Any] = {
        "schema_version": "typed-fact-next/2",
        "problem_text": problem_text,
        "solids": [deepcopy(poly_solid), sph],
        "premises": deepcopy(premises),
        "relations": rels,
        "derived_sections": [],
        "simulation_goals": [
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": poly_solid["solid_id"],
                "quote": poly_solid["quote"],
            }
        ],
        "math_goals": [_sphere_goal("mg1", goal_type, "sph", sphere_notation, goal_quote)],
    }
    if length_unit is not None:
        out["length_unit"] = length_unit
    return out


# ---------------------------------------------------------------------------
# Preregistered Positive Composite Cases (id, payload, expected_answers_map)
# ---------------------------------------------------------------------------
POSITIVE_CASES: list[tuple[str, dict[str, Any], dict[str, str]]] = [
    # 1-3: Cube a=2 inscribed sphere (radius=1, area=4π, volume=4π/3 via GeometricRelationSpecV2)
    (
        "cr.cube_2.inscribed.radius",
        make_inscribed_payload(
            problem_text=CUBE_2_GIVEN + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'. Tính bán kính mặt cầu (S).",
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
        ),
        {"mg1": "1"},
    ),
    (
        "cr.cube_2.inscribed.area",
        make_inscribed_payload(
            problem_text=CUBE_2_GIVEN + " Tính diện tích mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(ABCD.A'B'C'D')",
            sphere_quote="Tính diện tích mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="area",
            goal_quote="Tính diện tích mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
        ),
        {"mg1": "4π"},
    ),
    (
        "cr.cube_2.inscribed.volume_rel_v2",
        make_inscribed_payload(
            problem_text=CUBE_2_GIVEN + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'. Tính thể tích khối cầu (S).",
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="volume",
            goal_quote="Tính thể tích khối cầu (S).",
            use_relation_spec=True,
        ),
        {"mg1": "4π/3"},
    ),
    # 4: Cube a=2 with explicit GeometricRelationSpecV2(kind="circumscribes")
    (
        "cr.cube_2.circumscribes_rel_v2",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": CUBE_2_GIVEN + " Gọi (S) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'. Tính bán kính mặt cầu (S).",
            "solids": [
                deepcopy(CUBE_2_SOLID),
                {
                    "solid_id": "sph",
                    "solid_type": "sphere",
                    "notation": "(S)",
                    "quote": "Gọi (S) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
                },
            ],
            "premises": deepcopy(CUBE_2_PREMS),
            "relations": [
                {
                    "relation_id": "rel_circ",
                    "kind": "circumscribes",
                    "solid_a": "sph",
                    "solid_b": "poly",
                    "quote": "Gọi (S) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
                }
            ],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": CUBE_2_SOLID["quote"]}],
            "math_goals": [_sphere_goal("mg1", "radius", "sph", "(S)", "Tính bán kính mặt cầu (S).")],
        },
        {"mg1": "√3"},
    ),
    # 5: Dual spheres on Cube a=2: (S1) circumscribed + (S2) inscribed + polyhedron volume (3 goals across 3 objects)
    (
        "cr.cube_2.dual_spheres.multi_goal",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                CUBE_2_GIVEN
                + " Gọi (S1) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'."
                + " Gọi (S2) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
                + " Tính diện tích mặt cầu (S1), diện tích mặt cầu (S2) và thể tích khối lập phương ABCD.A'B'C'D'."
            ),
            "solids": [
                deepcopy(CUBE_2_SOLID),
                {
                    "solid_id": "sph_out",
                    "solid_type": "sphere",
                    "notation": "(S1)",
                    "circumscribes": "poly",
                    "quote": "Gọi (S1) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
                },
                {
                    "solid_id": "sph_in",
                    "solid_type": "sphere",
                    "notation": "(S2)",
                    "inscribed_in": "poly",
                    "quote": "Gọi (S2) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
                },
            ],
            "premises": deepcopy(CUBE_2_PREMS),
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": CUBE_2_SOLID["quote"]}],
            "math_goals": [
                _sphere_goal(
                    "mg1", "area", "sph_out", "(S1)",
                    "Tính diện tích mặt cầu (S1), diện tích mặt cầu (S2) và thể tích khối lập phương ABCD.A'B'C'D'.",
                ),
                _sphere_goal(
                    "mg2", "area", "sph_in", "(S2)",
                    "Tính diện tích mặt cầu (S1), diện tích mặt cầu (S2) và thể tích khối lập phương ABCD.A'B'C'D'.",
                ),
                {
                    "goal_id": "mg3",
                    "kind": "measurement",
                    "goal_type": "volume",
                    "solid_id": "poly",
                    "target": {"solid_id": "poly"},
                    "quote": "Tính diện tích mặt cầu (S1), diện tích mặt cầu (S2) và thể tích khối lập phương ABCD.A'B'C'D'.",
                },
            ],
        },
        {"mg1": "12π", "mg2": "4π", "mg3": "8"},
    ),
    # 6: Regular square pyramid S.ABCD (AB=6, h=4) inscribed sphere radius = 3/2
    (
        "cr.pyr_sq_6_4.inscribed.radius",
        make_inscribed_payload(
            problem_text=PYR_SQ_64_GIVEN + " Tính bán kính mặt cầu nội tiếp hình chóp S.ABCD.",
            poly_solid=PYR_SQ_64_SOLID,
            premises=PYR_SQ_64_PREMS,
            sphere_notation="(S.ABCD)",
            sphere_quote="Tính bán kính mặt cầu nội tiếp hình chóp S.ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu nội tiếp hình chóp S.ABCD.",
        ),
        {"mg1": "3/2"},
    ),
    # 7: Regular square pyramid S.ABCD (AB=6, h=4) "tiếp xúc với tất cả các mặt của..." wording -> volume = 9π/2
    (
        "cr.pyr_sq_6_4.inscribed.all_faces_wording",
        make_inscribed_payload(
            problem_text=(
                PYR_SQ_64_GIVEN
                + " Gọi (S) là mặt cầu tiếp xúc với tất cả các mặt của hình chóp S.ABCD."
                + " Tính thể tích khối cầu (S)."
            ),
            poly_solid=PYR_SQ_64_SOLID,
            premises=PYR_SQ_64_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu tiếp xúc với tất cả các mặt của hình chóp S.ABCD.",
            goal_type="volume",
            goal_quote="Tính thể tích khối cầu (S).",
        ),
        {"mg1": "9π/2"},
    ),
    # 8: Dual spheres on S.ABCD (AB=6, h=4) with distinct non-concentric centers: R_out = 17/4, r_in = 3/2
    (
        "cr.pyr_sq_6_4.dual_spheres.distinct_centers",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                PYR_SQ_64_GIVEN
                + " Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD và bán kính mặt cầu nội tiếp hình chóp S.ABCD."
            ),
            "solids": [
                deepcopy(PYR_SQ_64_SOLID),
                {
                    "solid_id": "sph_out",
                    "solid_type": "sphere",
                    "notation": "(S.ABCD)",
                    "circumscribes": "poly",
                    "quote": "Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD",
                },
                {
                    "solid_id": "sph_in",
                    "solid_type": "sphere",
                    "notation": "()",
                    "inscribed_in": "poly",
                    "quote": "bán kính mặt cầu nội tiếp hình chóp S.ABCD.",
                },
            ],
            "premises": deepcopy(PYR_SQ_64_PREMS),
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": PYR_SQ_64_SOLID["quote"]}],
            "math_goals": [
                _sphere_goal(
                    "mg1", "radius", "sph_out", "(S.ABCD)",
                    "Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD và bán kính mặt cầu nội tiếp hình chóp S.ABCD.",
                ),
                _sphere_goal(
                    "mg2", "radius", "sph_in", "()",
                    "Tính bán kính mặt cầu ngoại tiếp hình chóp S.ABCD và bán kính mặt cầu nội tiếp hình chóp S.ABCD.",
                ),
            ],
        },
        {"mg1": "17/4", "mg2": "3/2"},
    ),
    # 9: Non-regular tangential right triangular prism ABC.A'B'C' (3,4,5, h=2) inscribed sphere area = 4π
    (
        "cr.prism_345_h2.inscribed.area",
        make_inscribed_payload(
            problem_text=PRISM_345_H2_GIVEN + " Gọi (S) là mặt cầu nội tiếp lăng trụ ABC.A'B'C'. Tính diện tích mặt cầu (S).",
            poly_solid=PRISM_345_H2_SOLID,
            premises=PRISM_345_H2_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp lăng trụ ABC.A'B'C'.",
            goal_type="area",
            goal_quote="Tính diện tích mặt cầu (S).",
        ),
        {"mg1": "4π"},
    ),
    # 10: Dual spheres on non-regular right triangular prism (3,4,5, h=2): R_out = √29/2 (S_out = 29π), V_in = 4π/3
    (
        "cr.prism_345_h2.dual_spheres.multi_goal",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                PRISM_345_H2_GIVEN
                + " Gọi (S1) là mặt cầu ngoại tiếp lăng trụ ABC.A'B'C'."
                + " Gọi (S2) là mặt cầu nội tiếp lăng trụ ABC.A'B'C'."
                + " Tính diện tích mặt cầu (S1) và thể tích khối cầu (S2)."
            ),
            "solids": [
                deepcopy(PRISM_345_H2_SOLID),
                {
                    "solid_id": "sph_out",
                    "solid_type": "sphere",
                    "notation": "(S1)",
                    "circumscribes": "poly",
                    "quote": "Gọi (S1) là mặt cầu ngoại tiếp lăng trụ ABC.A'B'C'.",
                },
                {
                    "solid_id": "sph_in",
                    "solid_type": "sphere",
                    "notation": "(S2)",
                    "inscribed_in": "poly",
                    "quote": "Gọi (S2) là mặt cầu nội tiếp lăng trụ ABC.A'B'C'.",
                },
            ],
            "premises": deepcopy(PRISM_345_H2_PREMS),
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": PRISM_345_H2_SOLID["quote"]}],
            "math_goals": [
                _sphere_goal("mg1", "area", "sph_out", "(S1)", "Tính diện tích mặt cầu (S1) và thể tích khối cầu (S2)."),
                _sphere_goal("mg2", "volume", "sph_in", "(S2)", "Tính diện tích mặt cầu (S1) và thể tích khối cầu (S2)."),
            ],
        },
        {"mg1": "29π", "mg2": "4π/3"},
    ),
    # 11: Asymmetric right-corner tetrahedron S.ABC (SA=1, AB=3, AC=2) with named incenter I: r = 1/3, AI = √3/3
    (
        "cr.tetra_asym_132.inscribed.named_center",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                TETRA_132_GIVEN
                + " Gọi I là tâm mặt cầu nội tiếp hình chóp S.ABC."
                + " Tính bán kính mặt cầu nội tiếp hình chóp S.ABC và độ dài AI."
            ),
            "solids": [
                deepcopy(TETRA_132_SOLID),
                {
                    "solid_id": "sph",
                    "solid_type": "sphere",
                    "notation": "I",
                    "center": "I",
                    "inscribed_in": "poly",
                    "quote": "Gọi I là tâm mặt cầu nội tiếp hình chóp S.ABC.",
                },
            ],
            "premises": deepcopy(TETRA_132_PREMS),
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": TETRA_132_SOLID["quote"]}],
            "math_goals": [
                _sphere_goal("mg1", "radius", "sph", "I", "Tính bán kính mặt cầu nội tiếp hình chóp S.ABC và độ dài AI."),
                {
                    "goal_id": "mg2",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "solid_id": "poly",
                    "target": {"segment": ["A", "I"]},
                    "quote": "Tính bán kính mặt cầu nội tiếp hình chóp S.ABC và độ dài AI.",
                },
            ],
        },
        {"mg1": "1/3", "mg2": "√3/3"},
    ),
    # 12: Explicit tangent_to relation with named contact point T on oblique face (SBC) of S.ABC (SA=1, AB=3, AC=2)
    #     T = (3/7, 10/21, 13/21), I = (1/3, 1/3, 1/3), IT = 1/3, volume = 4π/81
    (
        "cr.tetra_asym_132.tangent_plane_with_contact_point",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                TETRA_132_GIVEN
                + " Gọi (S) là mặt cầu có tâm I nội tiếp hình chóp S.ABC."
                + " Mặt cầu (S) tiếp xúc với mặt phẳng (SBC) tại T."
                + " Tính độ dài IT và thể tích khối cầu (S)."
            ),
            "solids": [
                deepcopy(TETRA_132_SOLID),
                {
                    "solid_id": "sph",
                    "solid_type": "sphere",
                    "notation": "(S)",
                    "center": "I",
                    "inscribed_in": "poly",
                    "quote": "Gọi (S) là mặt cầu có tâm I nội tiếp hình chóp S.ABC.",
                },
            ],
            "premises": deepcopy(TETRA_132_PREMS),
            "relations": [
                {
                    "relation_id": "rel_tan",
                    "kind": "tangent_to",
                    "solid_a": "sph",
                    "solid_b": "poly",
                    "entity_b": ["S", "B", "C"],
                    "contact_ref": "T",
                    "quote": "Mặt cầu (S) tiếp xúc với mặt phẳng (SBC) tại T.",
                }
            ],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": TETRA_132_SOLID["quote"]}],
            "math_goals": [
                {
                    "goal_id": "mg1",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "solid_id": "poly",
                    "target": {"segment": ["I", "T"]},
                    "quote": "Tính độ dài IT và thể tích khối cầu (S).",
                },
                _sphere_goal("mg2", "volume", "sph", "(S)", "Tính độ dài IT và thể tích khối cầu (S)."),
            ],
        },
        {"mg1": "1/3", "mg2": "4π/81"},
    ),
    # 13: Two pyramids sharing base ABCD (shared_faces) + sphere inscribed in S.ABCD + multi-solid goals
    (
        "cr.shared_base_pyramids_plus_inscribed_sphere",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD. "
                "Hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6, chiều cao của hình chóp S.ABCD bằng 4. "
                "Biết TA vuông góc với mặt phẳng (ABCD) và TA = 6. "
                "Gọi (S) là mặt cầu nội tiếp hình chóp S.ABCD. "
                "Tính thể tích khối chóp T.ABCD và diện tích mặt cầu (S)."
            ),
            "solids": [
                {
                    "solid_id": "s1",
                    "solid_type": "pyramid",
                    "notation": "S.ABCD",
                    "coordinate_frame_id": "root",
                    "quote": "Hình chóp tứ giác đều S.ABCD",
                },
                {
                    "solid_id": "s2",
                    "solid_type": "pyramid",
                    "notation": "T.ABCD",
                    "coordinate_frame_id": "root",
                    "quote": "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD.",
                },
                {
                    "solid_id": "sph",
                    "solid_type": "sphere",
                    "notation": "(S)",
                    "inscribed_in": "s1",
                    "quote": "Gọi (S) là mặt cầu nội tiếp hình chóp S.ABCD.",
                },
            ],
            "premises": [
                _prem("regular_pyramid", {"apex": "S", "base": ["A", "B", "C", "D"]},
                      "Hình chóp tứ giác đều S.ABCD", solid_id="s1"),
                _prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "6"},
                      "Hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6", solid_id="s1"),
                _prem("height", {"value": "4", "solid": "s1"},
                      "Hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6, chiều cao của hình chóp S.ABCD bằng 4.", solid_id="s1"),
                _prem("perpendicular_line_plane", {"line": ["T", "A"], "plane": ["A", "B", "C", "D"]},
                      "Biết TA vuông góc với mặt phẳng (ABCD)", solid_id="s2"),
                _prem("segment_length", {"segment": ["T", "A"], "value": "6"}, "TA = 6", solid_id="s2"),
            ],
            "relations": [
                {
                    "relation_id": "r_shared",
                    "kind": "shared_faces",
                    "solid_a": "s1",
                    "solid_b": "s2",
                    "face_a": ["A", "B", "C", "D"],
                    "face_b": ["A", "B", "C", "D"],
                    "quote": "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD.",
                },
                {
                    "relation_id": "r_f1",
                    "kind": "coordinate_frame",
                    "solid_id": "s1",
                    "frame_id": "root",
                    "quote": "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD.",
                },
                {
                    "relation_id": "r_f2",
                    "kind": "coordinate_frame",
                    "solid_id": "s2",
                    "frame_id": "root",
                    "quote": "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD.",
                },
            ],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Hình chóp tứ giác đều S.ABCD"}],
            "math_goals": [
                {
                    "goal_id": "mg1",
                    "kind": "measurement",
                    "goal_type": "volume",
                    "solid_id": "s2",
                    "target": {"solid_id": "s2"},
                    "quote": "Tính thể tích khối chóp T.ABCD và diện tích mặt cầu (S).",
                },
                _sphere_goal("mg2", "area", "sph", "(S)", "Tính thể tích khối chóp T.ABCD và diện tích mặt cầu (S)."),
            ],
        },
        {"mg1": "72", "mg2": "9π"},
    ),
    # 14: Polyhedron derived section + inscribed sphere coexisting in one composite problem
    #     M is midpoint of AA'; plane (P) through M parallel to (ABCD) cuts cube of side 2 in a 2x2 square (area = 4); sphere V = 4π/3
    (
        "cr.cube_section_plus_inscribed_sphere",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                CUBE_2_GIVEN
                + " Gọi M là trung điểm của AA'."
                + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
                + " Mặt phẳng (P) đi qua M và song song với (ABCD)."
                + " Tính diện tích thiết diện của hình lập phương ABCD.A'B'C'D' cắt bởi (P) và thể tích khối cầu (S)."
            ),
            "solids": [
                deepcopy(CUBE_2_SOLID),
                {
                    "solid_id": "sph",
                    "solid_type": "sphere",
                    "notation": "(S)",
                    "inscribed_in": "poly",
                    "quote": "Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
                },
            ],
            "premises": [
                *deepcopy(CUBE_2_PREMS),
                _prem("midpoint", {"point": "M", "segment": ["A", "A'"]}, "Gọi M là trung điểm của AA'."),
            ],
            "relations": [],
            "derived_sections": [
                {
                    "section_id": "sec1",
                    "plane_name": "P",
                    "target_solid_id": "poly",
                    "plane_kind": "through_point_parallel_plane",
                    "through_point": "M",
                    "parallel_plane": ["A", "B", "C"],
                    "quote": "Mặt phẳng (P) đi qua M và song song với (ABCD).",
                }
            ],
            "simulation_goals": [
                {
                    "goal_id": "sg1",
                    "kind": "construct_plane_section",
                    "target_section_id": "sec1",
                    "quote": "Tính diện tích thiết diện của hình lập phương ABCD.A'B'C'D' cắt bởi (P) và thể tích khối cầu (S).",
                }
            ],
            "math_goals": [
                {
                    "goal_id": "mg1",
                    "kind": "measurement",
                    "goal_type": "area",
                    "solid_id": "poly",
                    "target": {"section_id": "sec1"},
                    "quote": "Tính diện tích thiết diện của hình lập phương ABCD.A'B'C'D' cắt bởi (P) và thể tích khối cầu (S).",
                },
                _sphere_goal(
                    "mg2", "volume", "sph", "(S)",
                    "Tính diện tích thiết diện của hình lập phương ABCD.A'B'C'D' cắt bởi (P) và thể tích khối cầu (S).",
                ),
            ],
        },
        {"mg1": "4", "mg2": "4π/3"},
    ),
    # 15: Right cylinder (R=3, h=6) + inscribed sphere (r=3, V=36π)
    (
        "cr.cylinder_r3_h6.inscribed.volume",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                "Cho hình trụ (T) có bán kính đáy R = 3 và chiều cao h = 6. "
                "Gọi (S) là mặt cầu nội tiếp hình trụ (T). Tính thể tích khối cầu (S)."
            ),
            "solids": [
                {
                    "solid_id": "cyl",
                    "solid_type": "cylinder",
                    "notation": "(T)",
                    "radius": "3",
                    "height": "6",
                    "quote": "Cho hình trụ (T) có bán kính đáy R = 3 và chiều cao h = 6.",
                },
                {
                    "solid_id": "sph",
                    "solid_type": "sphere",
                    "notation": "(S)",
                    "inscribed_in": "cyl",
                    "quote": "Gọi (S) là mặt cầu nội tiếp hình trụ (T).",
                },
            ],
            "premises": [],
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "cyl",
                                  "quote": "Cho hình trụ (T) có bán kính đáy R = 3 và chiều cao h = 6."}],
            "math_goals": [_sphere_goal("mg1", "volume", "sph", "(S)", "Tính thể tích khối cầu (S).")],
        },
        {"mg1": "36π"},
    ),
    # 16: Right cylinder (R=3, h=6) + dual spheres: (S1) circumscribed (area=72π) + (S2) inscribed (area=36π)
    (
        "cr.cylinder_r3_h6.dual_spheres",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                "Cho hình trụ (T) có bán kính đáy R = 3 và chiều cao h = 6. "
                "Gọi (S1) là mặt cầu ngoại tiếp hình trụ (T). "
                "Gọi (S2) là mặt cầu nội tiếp hình trụ (T). "
                "Tính diện tích mặt cầu (S1) và diện tích mặt cầu (S2)."
            ),
            "solids": [
                {
                    "solid_id": "cyl",
                    "solid_type": "cylinder",
                    "notation": "(T)",
                    "radius": "3",
                    "height": "6",
                    "quote": "Cho hình trụ (T) có bán kính đáy R = 3 và chiều cao h = 6.",
                },
                {
                    "solid_id": "sph_out",
                    "solid_type": "sphere",
                    "notation": "(S1)",
                    "circumscribes": "cyl",
                    "quote": "Gọi (S1) là mặt cầu ngoại tiếp hình trụ (T).",
                },
                {
                    "solid_id": "sph_in",
                    "solid_type": "sphere",
                    "notation": "(S2)",
                    "inscribed_in": "cyl",
                    "quote": "Gọi (S2) là mặt cầu nội tiếp hình trụ (T).",
                },
            ],
            "premises": [],
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "cyl",
                                  "quote": "Cho hình trụ (T) có bán kính đáy R = 3 và chiều cao h = 6."}],
            "math_goals": [
                _sphere_goal("mg1", "area", "sph_out", "(S1)", "Tính diện tích mặt cầu (S1) và diện tích mặt cầu (S2)."),
                _sphere_goal("mg2", "area", "sph_in", "(S2)", "Tính diện tích mặt cầu (S1) và diện tích mặt cầu (S2)."),
            ],
        },
        {"mg1": "72π", "mg2": "36π"},
    ),
    # 17: Right circular cone (R=3, h=4, l=5) + circumscribed sphere (R=25/8) + inscribed sphere (r=3/2, S=9π)
    (
        "cr.cone_r3_h4.dual_spheres",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                "Cho hình nón (N) có bán kính đáy R = 3 và chiều cao h = 4. "
                "Gọi (S1) là mặt cầu ngoại tiếp hình nón (N). "
                "Gọi (S2) là mặt cầu nội tiếp hình nón (N). "
                "Tính bán kính mặt cầu (S1) và diện tích mặt cầu (S2)."
            ),
            "solids": [
                {
                    "solid_id": "cone",
                    "solid_type": "cone",
                    "notation": "(N)",
                    "radius": "3",
                    "height": "4",
                    "quote": "Cho hình nón (N) có bán kính đáy R = 3 và chiều cao h = 4.",
                },
                {
                    "solid_id": "sph_out",
                    "solid_type": "sphere",
                    "notation": "(S1)",
                    "circumscribes": "cone",
                    "quote": "Gọi (S1) là mặt cầu ngoại tiếp hình nón (N).",
                },
                {
                    "solid_id": "sph_in",
                    "solid_type": "sphere",
                    "notation": "(S2)",
                    "inscribed_in": "cone",
                    "quote": "Gọi (S2) là mặt cầu nội tiếp hình nón (N).",
                },
            ],
            "premises": [],
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "cone",
                                  "quote": "Cho hình nón (N) có bán kính đáy R = 3 và chiều cao h = 4."}],
            "math_goals": [
                _sphere_goal("mg1", "radius", "sph_out", "(S1)", "Tính bán kính mặt cầu (S1) và diện tích mặt cầu (S2)."),
                _sphere_goal("mg2", "area", "sph_in", "(S2)", "Tính bán kính mặt cầu (S1) và diện tích mặt cầu (S2)."),
            ],
        },
        {"mg1": "25/8", "mg2": "9π"},
    ),
]


# ---------------------------------------------------------------------------
# Preregistered Adversarial / Negative Cases (id, payload, expected_refusal_code)
# ---------------------------------------------------------------------------
NEGATIVE_CASES: list[tuple[str, dict[str, Any], str]] = [
    # 1. Non-tangential cuboid 2 x 2 x 4 -> NO_INSCRIBED_SPHERE
    (
        "cr.neg.cuboid_224_no_inscribed_sphere",
        make_inscribed_payload(
            problem_text=(
                "Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật, AB = 2, AD = 2, AA' = 4. "
                "Tính bán kính mặt cầu nội tiếp hình hộp chữ nhật ABCD.A'B'C'D'."
            ),
            poly_solid={
                "solid_id": "poly",
                "solid_type": "prism",
                "notation": "ABCD.A'B'C'D'",
                "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'",
            },
            premises=[
                _prem("right_prism", {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]},
                      "Cho hình hộp chữ nhật ABCD.A'B'C'D'"),
                _prem("rectangle", {"vertices": ["A", "B", "C", "D"]},
                      "đáy ABCD là hình chữ nhật"),
                _prem("segment_length", {"segment": ["A", "B"], "value": "2"}, "AB = 2"),
                _prem("segment_length", {"segment": ["A", "D"], "value": "2"}, "AD = 2"),
                _prem("segment_length", {"segment": ["A", "A'"], "value": "4"}, "AA' = 4"),
            ],
            sphere_notation="(ABCD.A'B'C'D')",
            sphere_quote="Tính bán kính mặt cầu nội tiếp hình hộp chữ nhật ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu nội tiếp hình hộp chữ nhật ABCD.A'B'C'D'.",
        ),
        "NO_INSCRIBED_SPHERE",
    ),
    # 2. Right triangular prism (3,4,5) with height AA'=5 != 2*r_in=2 -> NO_INSCRIBED_SPHERE
    (
        "cr.neg.prism_345_h5_no_inscribed_sphere",
        make_inscribed_payload(
            problem_text=(
                "Cho lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, AA' = 5. "
                "Gọi (S) là mặt cầu nội tiếp lăng trụ ABC.A'B'C'. Tính bán kính mặt cầu (S)."
            ),
            poly_solid=PRISM_345_H2_SOLID,
            premises=[
                *PRISM_345_H2_PREMS[:-1],
                _prem("segment_length", {"segment": ["A", "A'"], "value": "5"}, "AA' = 5"),
            ],
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp lăng trụ ABC.A'B'C'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
        ),
        "NO_INSCRIBED_SPHERE",
    ),
    # 3. Rectangular pyramid AB=2, AD=4, SA⊥(ABCD), SA=2 (irrational face normals with NO common radius) -> NO_INSCRIBED_SPHERE
    (
        "cr.neg.rect_pyramid_no_inscribed_sphere",
        make_inscribed_payload(
            problem_text=(
                "Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật, AB = 2, AD = 4, "
                "SA vuông góc với mặt phẳng (ABCD) và SA = 2. "
                "Gọi (S) là mặt cầu nội tiếp hình chóp S.ABCD. Tính bán kính mặt cầu (S)."
            ),
            poly_solid={"solid_id": "poly", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"},
            premises=[
                _prem("rectangle", {"vertices": ["A", "B", "C", "D"]}, "đáy ABCD là hình chữ nhật"),
                _prem("segment_length", {"segment": ["A", "B"], "value": "2"}, "AB = 2"),
                _prem("segment_length", {"segment": ["A", "D"], "value": "4"}, "AD = 4"),
                _prem("perpendicular_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
                      "SA vuông góc với mặt phẳng (ABCD)"),
                _prem("segment_length", {"segment": ["S", "A"], "value": "2"}, "SA = 2"),
            ],
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp hình chóp S.ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
        ),
        "NO_INSCRIBED_SPHERE",
    ),
    # 4. Cylinder with h != 2R (R=3, h=4) -> NO_INSCRIBED_SPHERE
    (
        "cr.neg.cylinder_r3_h4_no_inscribed_sphere",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                "Cho hình trụ (T) có bán kính đáy R = 3 và chiều cao h = 4. "
                "Gọi (S) là mặt cầu nội tiếp hình trụ (T). Tính bán kính mặt cầu (S)."
            ),
            "solids": [
                {
                    "solid_id": "cyl",
                    "solid_type": "cylinder",
                    "notation": "(T)",
                    "radius": "3",
                    "height": "4",
                    "quote": "Cho hình trụ (T) có bán kính đáy R = 3 và chiều cao h = 4.",
                },
                {
                    "solid_id": "sph",
                    "solid_type": "sphere",
                    "notation": "(S)",
                    "inscribed_in": "cyl",
                    "quote": "Gọi (S) là mặt cầu nội tiếp hình trụ (T).",
                },
            ],
            "premises": [],
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "cyl",
                                  "quote": "Cho hình trụ (T) có bán kính đáy R = 3 và chiều cao h = 4."}],
            "math_goals": [_sphere_goal("mg1", "radius", "sph", "(S)", "Tính bán kính mặt cầu (S).")],
        },
        "NO_INSCRIBED_SPHERE",
    ),
    # 5. Real inscribed sphere exists with irrational coordinates/inradius: regular square pyramid AB=2, SO=2 -> EXACT_DOMAIN_EXCEEDED
    (
        "cr.neg.pyr_sq_2_2_irrational_incenter_exact_domain_exceeded",
        make_inscribed_payload(
            problem_text="Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2, chiều cao hình chóp bằng 2. Tính bán kính mặt cầu nội tiếp hình chóp S.ABCD.",
            poly_solid=PYR_SQ_64_SOLID,
            premises=[
                _prem("regular_pyramid", {"apex": "S", "base": ["A", "B", "C", "D"]},
                      "Cho hình chóp tứ giác đều S.ABCD"),
                _prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "2"},
                      "Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 2"),
                _prem("height", {"value": "2"}, "chiều cao hình chóp bằng 2", solid_id=None),
            ],
            sphere_notation="(S.ABCD)",
            sphere_quote="Tính bán kính mặt cầu nội tiếp hình chóp S.ABCD.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu nội tiếp hình chóp S.ABCD.",
        ),
        "EXACT_DOMAIN_EXCEEDED",
    ),
    # 6. Cone R=1, h=1 (slant l=√2 irrational -> r_in = 1/(1+√2) irrational) -> EXACT_DOMAIN_EXCEEDED
    (
        "cr.neg.cone_r1_h1_irrational_inradius_exact_domain_exceeded",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                "Cho hình nón (N) có bán kính đáy R = 1 và chiều cao h = 1. "
                "Gọi (S) là mặt cầu nội tiếp hình nón (N). Tính bán kính mặt cầu (S)."
            ),
            "solids": [
                {
                    "solid_id": "cone",
                    "solid_type": "cone",
                    "notation": "(N)",
                    "radius": "1",
                    "height": "1",
                    "quote": "Cho hình nón (N) có bán kính đáy R = 1 và chiều cao h = 1.",
                },
                {
                    "solid_id": "sph",
                    "solid_type": "sphere",
                    "notation": "(S)",
                    "inscribed_in": "cone",
                    "quote": "Gọi (S) là mặt cầu nội tiếp hình nón (N).",
                },
            ],
            "premises": [],
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "cone",
                                  "quote": "Cho hình nón (N) có bán kính đáy R = 1 và chiều cao h = 1."}],
            "math_goals": [_sphere_goal("mg1", "radius", "sph", "(S)", "Tính bán kính mặt cầu (S).")],
        },
        "EXACT_DOMAIN_EXCEEDED",
    ),
    # 7. Equilateral base chart (irrational Cholesky embedding) -> METRIC_REQUIRES_EUCLIDEAN_CHART
    (
        "cr.neg.equilateral_pyramid_inscribed_non_euclidean_chart",
        make_inscribed_payload(
            problem_text=(
                "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2, chiều cao hình chóp bằng 2. "
                "Gọi (S) là mặt cầu nội tiếp hình chóp S.ABC. Tính bán kính mặt cầu (S)."
            ),
            poly_solid={"solid_id": "poly", "solid_type": "pyramid", "notation": "S.ABC", "quote": "Cho hình chóp tam giác đều S.ABC"},
            premises=[
                _prem("regular_pyramid", {"apex": "S", "base": ["A", "B", "C"]}, "Cho hình chóp tam giác đều S.ABC"),
                _prem("regular_polygon", {"vertices": ["A", "B", "C"], "side": "2"},
                      "Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng 2"),
                _prem("height", {"value": "2"}, "chiều cao hình chóp bằng 2", solid_id=None),
            ],
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp hình chóp S.ABC.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
        ),
        "METRIC_REQUIRES_EUCLIDEAN_CHART",
    ),
    # 8. Contradictory pre-declared center for inscribed sphere -> INCONSISTENT_FACTS
    (
        "cr.neg.contradictory_named_incenter",
        make_inscribed_payload(
            problem_text=(
                CUBE_2_GIVEN
                + " Gọi I là trung điểm của AA'. Gọi (S) là mặt cầu có tâm I nội tiếp hình lập phương ABCD.A'B'C'D'."
                + " Tính bán kính mặt cầu (S)."
            ),
            poly_solid=CUBE_2_SOLID,
            premises=[
                *CUBE_2_PREMS,
                _prem("midpoint", {"point": "I", "segment": ["A", "A'"]}, "Gọi I là trung điểm của AA'."),
            ],
            sphere_notation="(S)",
            sphere_center="I",
            sphere_quote="Gọi (S) là mặt cầu có tâm I nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
        ),
        "INCONSISTENT_FACTS",
    ),
    # 9. Secant plane (d < R) claimed tangent_to -> PLANE_INTERSECTS_SPHERE_NOT_TANGENT
    (
        "cr.neg.secant_plane_claimed_tangent",
        make_inscribed_payload(
            problem_text=(
                CUBE_2_GIVEN
                + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
                + " Mặt cầu (S) tiếp xúc với mặt phẳng (ACC')."
                + " Tính bán kính mặt cầu (S)."
            ),
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
            extra_relations=[
                {
                    "relation_id": "rel_secant",
                    "kind": "tangent_to",
                    "solid_a": "sph",
                    "solid_b": "poly",
                    "entity_b": ["A", "C", "C'"],
                    "quote": "Mặt cầu (S) tiếp xúc với mặt phẳng (ACC').",
                }
            ],
        ),
        "PLANE_INTERSECTS_SPHERE_NOT_TANGENT",
    ),
    # 10. Disjoint plane (d > R) claimed tangent_to -> PLANE_DOES_NOT_TOUCH_SPHERE
    (
        "cr.neg.disjoint_plane_claimed_tangent",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD. "
                "Hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6, chiều cao của hình chóp S.ABCD bằng 4. "
                "Biết TA vuông góc với mặt phẳng (ABCD) và TA = 12. "
                "Gọi (S) là mặt cầu nội tiếp hình chóp S.ABCD. "
                "Mặt cầu (S) tiếp xúc với mặt phẳng (TBC). "
                "Tính bán kính mặt cầu (S)."
            ),
            "solids": [
                {"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "coordinate_frame_id": "root",
                 "quote": "Hình chóp tứ giác đều S.ABCD"},
                {"solid_id": "s2", "solid_type": "pyramid", "notation": "T.ABCD", "coordinate_frame_id": "root",
                 "quote": "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD."},
                {"solid_id": "sph", "solid_type": "sphere", "notation": "(S)", "inscribed_in": "s1",
                 "quote": "Gọi (S) là mặt cầu nội tiếp hình chóp S.ABCD."},
            ],
            "premises": [
                _prem("regular_pyramid", {"apex": "S", "base": ["A", "B", "C", "D"]},
                      "Hình chóp tứ giác đều S.ABCD", solid_id="s1"),
                _prem("regular_polygon", {"vertices": ["A", "B", "C", "D"], "side": "6"},
                      "Hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6", solid_id="s1"),
                _prem("height", {"value": "4", "solid": "s1"},
                      "Hình chóp tứ giác đều S.ABCD có cạnh đáy bằng 6, chiều cao của hình chóp S.ABCD bằng 4.", solid_id="s1"),
                _prem("perpendicular_line_plane", {"line": ["T", "A"], "plane": ["A", "B", "C", "D"]},
                      "Biết TA vuông góc với mặt phẳng (ABCD)", solid_id="s2"),
                _prem("segment_length", {"segment": ["T", "A"], "value": "12"}, "TA = 12", solid_id="s2"),
            ],
            "relations": [
                {
                    "relation_id": "r_shared",
                    "kind": "shared_faces",
                    "solid_a": "s1",
                    "solid_b": "s2",
                    "face_a": ["A", "B", "C", "D"],
                    "face_b": ["A", "B", "C", "D"],
                    "quote": "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD.",
                },
                {
                    "relation_id": "r_f1",
                    "kind": "coordinate_frame",
                    "solid_id": "s1",
                    "frame_id": "root",
                    "quote": "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD.",
                },
                {
                    "relation_id": "r_f2",
                    "kind": "coordinate_frame",
                    "solid_id": "s2",
                    "frame_id": "root",
                    "quote": "Hai hình chóp S.ABCD và T.ABCD có mặt chung ABCD.",
                },
                {
                    "relation_id": "r_disjoint",
                    "kind": "tangent_to",
                    "solid_a": "sph",
                    "solid_b": "s2",
                    "entity_b": ["T", "B", "C"],
                    "quote": "Mặt cầu (S) tiếp xúc với mặt phẳng (TBC).",
                },
            ],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1",
                                  "quote": "Hình chóp tứ giác đều S.ABCD"}],
            "math_goals": [_sphere_goal("mg1", "radius", "sph", "(S)", "Tính bán kính mặt cầu (S).")],
        },
        "PLANE_DOES_NOT_TOUCH_SPHERE",
    ),
    # 11. Wrong contact point claimed on a genuinely tangent plane -> INCONSISTENT_FACTS
    (
        "cr.neg.wrong_contact_point_on_tangent_plane",
        make_inscribed_payload(
            problem_text=(
                CUBE_2_GIVEN
                + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
                + " Mặt cầu (S) tiếp xúc với mặt phẳng (ABCD) tại A."
                + " Tính bán kính mặt cầu (S)."
            ),
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
            extra_relations=[
                {
                    "relation_id": "rel_wrong_pt",
                    "kind": "tangent_to",
                    "solid_a": "sph",
                    "solid_b": "poly",
                    "entity_b": ["A", "B", "C", "D"],
                    "contact_ref": "A",
                    "quote": "Mặt cầu (S) tiếp xúc với mặt phẳng (ABCD) tại A.",
                }
            ],
        ),
        "INCONSISTENT_FACTS",
    ),
    # 12. Reversed relation direction: polyhedron inscribed_in sphere -> SOURCE_OBJECT_MISMATCH
    (
        "cr.neg.reversed_inscribed_direction",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": CUBE_2_GIVEN + " Gọi (S) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'. Tính bán kính mặt cầu (S).",
            "solids": [
                deepcopy(CUBE_2_SOLID),
                {"solid_id": "sph", "solid_type": "sphere", "notation": "(S)",
                 "quote": "Gọi (S) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'."},
            ],
            "premises": deepcopy(CUBE_2_PREMS),
            "relations": [
                {
                    "relation_id": "rel_rev",
                    "kind": "inscribed_in",
                    "solid_a": "poly",
                    "solid_b": "sph",
                    "quote": "Gọi (S) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
                }
            ],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": CUBE_2_SOLID["quote"]}],
            "math_goals": [_sphere_goal("mg1", "radius", "sph", "(S)", "Tính bán kính mặt cầu (S).")],
        },
        "SOURCE_OBJECT_MISMATCH",
    ),
    # 13. Conflicting circumscribes + inscribed_in on the same sphere -> SOURCE_OBJECT_MISMATCH
    (
        "cr.neg.conflicting_circumscribes_and_inscribed",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": CUBE_2_GIVEN + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'. Tính bán kính mặt cầu (S).",
            "solids": [
                deepcopy(CUBE_2_SOLID),
                {
                    "solid_id": "sph",
                    "solid_type": "sphere",
                    "notation": "(S)",
                    "circumscribes": "poly",
                    "inscribed_in": "poly",
                    "quote": "Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
                },
            ],
            "premises": deepcopy(CUBE_2_PREMS),
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": CUBE_2_SOLID["quote"]}],
            "math_goals": [_sphere_goal("mg1", "radius", "sph", "(S)", "Tính bán kính mặt cầu (S).")],
        },
        "SOURCE_OBJECT_MISMATCH",
    ),
    # 14. Ambiguous bare "Tính thể tích khối cầu." when TWO spheres (S1) and (S2) exist -> SOURCE_OBJECT_MISMATCH
    (
        "cr.neg.ambiguous_bare_sphere_question_with_two_spheres",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                CUBE_2_GIVEN
                + " Gọi (S1) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'."
                + " Gọi (S2) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
                + " Tính thể tích khối cầu."
            ),
            "solids": [
                deepcopy(CUBE_2_SOLID),
                {
                    "solid_id": "sph_out",
                    "solid_type": "sphere",
                    "notation": "(S1)",
                    "circumscribes": "poly",
                    "quote": "Gọi (S1) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
                },
                {
                    "solid_id": "sph_in",
                    "solid_type": "sphere",
                    "notation": "(S2)",
                    "inscribed_in": "poly",
                    "quote": "Gọi (S2) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
                },
            ],
            "premises": deepcopy(CUBE_2_PREMS),
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": CUBE_2_SOLID["quote"]}],
            "math_goals": [_sphere_goal("mg1", "volume", "sph_out", "(S1)", "Tính thể tích khối cầu.")],
        },
        "SOURCE_OBJECT_MISMATCH",
    ),
    # 15. Wrong sphere ID bound to "nội tiếp" question when both (S1) circumscribed and (S2) inscribed exist -> SOURCE_OBJECT_MISMATCH
    (
        "cr.neg.wrong_sphere_id_for_inscribed_question",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                CUBE_2_GIVEN
                + " Gọi (S1) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'."
                + " Gọi (S2) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
                + " Tính diện tích mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
            ),
            "solids": [
                deepcopy(CUBE_2_SOLID),
                {
                    "solid_id": "sph_out",
                    "solid_type": "sphere",
                    "notation": "(S1)",
                    "circumscribes": "poly",
                    "quote": "Gọi (S1) là mặt cầu ngoại tiếp hình lập phương ABCD.A'B'C'D'.",
                },
                {
                    "solid_id": "sph_in",
                    "solid_type": "sphere",
                    "notation": "(S2)",
                    "inscribed_in": "poly",
                    "quote": "Gọi (S2) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
                },
            ],
            "premises": deepcopy(CUBE_2_PREMS),
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "poly", "quote": CUBE_2_SOLID["quote"]}],
            "math_goals": [
                _sphere_goal(
                    "mg1", "area", "sph_out", "(S1)",
                    "Tính diện tích mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
                )
            ],
        },
        "SOURCE_OBJECT_MISMATCH",
    ),
    # 16. Negated inscribed clause -> NEGATED_CLAUSE
    (
        "cr.neg.negated_inscribed_clause",
        make_inscribed_payload(
            problem_text=(
                CUBE_2_GIVEN
                + " Biết mặt cầu (S) không phải là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
                + " Tính bán kính mặt cầu (S)."
            ),
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(S)",
            sphere_quote="Biết mặt cầu (S) không phải là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
        ),
        "NEGATED_CLAUSE",
    ),
    # 17. Conditional inscribed clause -> CONDITIONAL_CLAUSE
    (
        "cr.neg.conditional_inscribed_clause",
        make_inscribed_payload(
            problem_text=(
                CUBE_2_GIVEN
                + " Nếu (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D' thì bán kính bằng 1."
                + " Tính bán kính mặt cầu (S)."
            ),
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(S)",
            sphere_quote="Nếu (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
        ),
        "CONDITIONAL_CLAUSE",
    ),
    # 18. Goal ("Chứng minh ...") tangent clause used as premise -> GOAL_CLAUSE_NOT_PREMISE
    (
        "cr.neg.goal_prove_tangent_clause",
        make_inscribed_payload(
            problem_text=(
                CUBE_2_GIVEN
                + " Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'."
                + " Chứng minh mặt cầu (S) tiếp xúc với mặt phẳng (ABCD)."
                + " Tính bán kính mặt cầu (S)."
            ),
            poly_solid=CUBE_2_SOLID,
            premises=CUBE_2_PREMS,
            sphere_notation="(S)",
            sphere_quote="Gọi (S) là mặt cầu nội tiếp hình lập phương ABCD.A'B'C'D'.",
            goal_type="radius",
            goal_quote="Tính bán kính mặt cầu (S).",
            extra_relations=[
                {
                    "relation_id": "rel_goal_tan",
                    "kind": "tangent_to",
                    "solid_a": "sph",
                    "solid_b": "poly",
                    "entity_b": ["A", "B", "C", "D"],
                    "quote": "Chứng minh mặt cầu (S) tiếp xúc với mặt phẳng (ABCD).",
                }
            ],
        ),
        "GOAL_CLAUSE_NOT_PREMISE",
    ),
    # 19. Two unrelated cylinders without relation anchor -> BRIDGE_UNSUPPORTED_CURVED_COMPOSITE
    (
        "cr.neg.two_unanchored_cylinders_refused",
        {
            "schema_version": "typed-fact-next/2",
            "problem_text": (
                "Cho hình trụ T1 có bán kính đáy R = 2 và chiều cao h = 4. "
                "Cho hình trụ T2 có bán kính đáy R = 3 và chiều cao h = 5. "
                "Tính thể tích khối trụ T1."
            ),
            "solids": [
                {"solid_id": "c1", "solid_type": "cylinder", "notation": "T1", "radius": "2", "height": "4",
                 "quote": "Cho hình trụ T1 có bán kính đáy R = 2 và chiều cao h = 4."},
                {"solid_id": "c2", "solid_type": "cylinder", "notation": "T2", "radius": "3", "height": "5",
                 "quote": "Cho hình trụ T2 có bán kính đáy R = 3 và chiều cao h = 5."},
            ],
            "premises": [],
            "relations": [],
            "derived_sections": [],
            "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "c1",
                                  "quote": "Cho hình trụ T1 có bán kính đáy R = 2 và chiều cao h = 4."}],
            "math_goals": [
                {"goal_id": "mg1", "kind": "measurement", "goal_type": "volume", "solid_id": "c1",
                 "target": {"solid_id": "c1"}, "quote": "Tính thể tích khối trụ T1."}
            ],
        },
        "BRIDGE_UNSUPPORTED_CURVED_COMPOSITE",
    ),
]


def run_probe() -> dict[str, Any]:
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
    from app.simulation.geometry.radical import parse_exact

    pos_rows = []
    for cid, payload, want_map in POSITIVE_CASES:
        r = run_typed_fact_next_v2_route(payload)
        env = build_adapter4_response(r, payload["problem_text"])
        matched = (
            r.status == "SERVED"
            and r.kernel_check is True
            and set(want_map).issubset(r.answer_exact)
            and all(parse_exact(r.answer_exact[k]["coef"]) == parse_exact(v) for k, v in want_map.items())
            and bool(env["route_d"].get("relation_certificates"))
        )
        pos_rows.append(
            {
                "case_id": cid,
                "status": r.status,
                "code": r.code,
                "answers": {k: r.answer_exact[k]["coef"] for k in want_map if k in r.answer_exact},
                "expected": want_map,
                "relation_certificates": len(env["route_d"].get("relation_certificates") or []),
                "matched_oracle": matched,
            }
        )

    neg_rows = []
    for cid, payload, want_code in NEGATIVE_CASES:
        r = run_typed_fact_next_v2_route(payload)
        env = build_adapter4_response(r, payload["problem_text"])
        matched = (
            r.status == "REFUSED"
            and r.code == want_code
            and not r.answer_exact
            and r.scene3d is None
            and r.route_d.get("relation_certificates") == []
            and "relation_certificates" not in env["route_d"]
        )
        neg_rows.append(
            {
                "case_id": cid,
                "status": r.status,
                "code": r.code,
                "expected_code": want_code,
                "matched_oracle": matched,
            }
        )

    return {
        "epic": "ALGOSIM_MASTER_HYBRID_BACKEND_REPLACEMENT",
        "continuation": "multi_object_factgraph_composite_geometry_relations",
        "live_provider_calls": 0,
        "positive_total": len(pos_rows),
        "positive_passed": sum(x["matched_oracle"] for x in pos_rows),
        "negative_total": len(neg_rows),
        "negative_passed": sum(x["matched_oracle"] for x in neg_rows),
        "positives": pos_rows,
        "negatives": neg_rows,
    }


if __name__ == "__main__":
    report = run_probe()
    out_path = Path(__file__).resolve().parents[1] / "composite-relations-probe.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Positives: {report['positive_passed']}/{report['positive_total']} | "
        f"Negatives: {report['negative_passed']}/{report['negative_total']}"
    )
