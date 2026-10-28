# -*- coding: utf-8 -*-
"""Pre-registered development corpus builder, independent exact Fraction oracle,
and RED/GREEN + tamper evaluator for W2-M5 Adapter /4 Category A Identity Repair.

Usage:
    python build_and_evaluate_w2_m5.py build-and-red
    python build_and_evaluate_w2_m5.py green
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"

RUN_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = RUN_DIR.parents[4]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

WAVE2_RUN = REPO_ROOT / "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2"


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def _dot(u: tuple[Fraction, Fraction, Fraction], v: tuple[Fraction, Fraction, Fraction]) -> Fraction:
    return u[0] * v[0] + u[1] * v[1] + u[2] * v[2]


def _sub(u: tuple[Fraction, Fraction, Fraction], v: tuple[Fraction, Fraction, Fraction]) -> tuple[Fraction, Fraction, Fraction]:
    return (u[0] - v[0], u[1] - v[1], u[2] - v[2])


def _cross(u: tuple[Fraction, Fraction, Fraction], v: tuple[Fraction, Fraction, Fraction]) -> tuple[Fraction, Fraction, Fraction]:
    return (
        u[1] * v[2] - u[2] * v[1],
        u[2] * v[0] - u[0] * v[2],
        u[0] * v[1] - u[1] * v[0],
    )


def _triangle_area_sq(
    a: tuple[Fraction, Fraction, Fraction],
    b: tuple[Fraction, Fraction, Fraction],
    c: tuple[Fraction, Fraction, Fraction],
) -> Fraction:
    w = _cross(_sub(b, a), _sub(c, a))
    return _dot(w, w) / Fraction(4)


def _convex_quad_area_sq(
    p0: tuple[Fraction, Fraction, Fraction],
    p1: tuple[Fraction, Fraction, Fraction],
    p2: tuple[Fraction, Fraction, Fraction],
    p3: tuple[Fraction, Fraction, Fraction],
) -> Fraction:
    c1 = _cross(_sub(p1, p0), _sub(p2, p0))
    c2 = _cross(_sub(p2, p0), _sub(p3, p0))
    total = (c1[0] + c2[0], c1[1] + c2[1], c1[2] + c2[2])
    return _dot(total, total) / Fraction(4)


def _make_right_prism_perp_case(
    case_id: str,
    ab: int,
    bc: int,
    aa_prime: int,
    through_pt: str,
    perp_line: list[str],
    named_cuts: list[tuple[list[str], str | None]],
    question_type: str,
    unit: str = "1",
    declared_boundary: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Independent exact Fraction oracle + typed-fact-next/2 payload for a right triangular prism
    ABC.A'B'C' (right at B) cut by a plane through a primed top vertex perpendicular to a diagonal.
    """
    u = "" if unit == "1" else unit
    # Independent 3D coordinates (right at B: B=(0,0,0) or A=(0,0,0), B=(ab,0,0), C=(ab,bc,0)):
    pts: dict[str, tuple[Fraction, Fraction, Fraction]] = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(ab), Fraction(0), Fraction(0)),
        "C": (Fraction(ab), Fraction(bc), Fraction(0)),
        "A'": (Fraction(0), Fraction(0), Fraction(aa_prime)),
        "B'": (Fraction(ab), Fraction(0), Fraction(aa_prime)),
        "C'": (Fraction(ab), Fraction(bc), Fraction(aa_prime)),
    }
    p0 = pts[through_pt]
    n_vec = _sub(pts[perp_line[1]], pts[perp_line[0]])

    all_edges = [["A", "A'"], ["B", "B'"], ["C", "C'"]]
    boundary_oracle = []
    poly_pts = []
    for e in all_edges:
        ea, eb = pts[e[0]], pts[e[1]]
        d_vec = _sub(eb, ea)
        t_val = _dot(_sub(p0, ea), n_vec) / _dot(d_vec, n_vec)
        assert Fraction(0) <= t_val <= Fraction(1), f"{case_id}: t={t_val} out of [0,1]"
        pt_xyz = (
            ea[0] + t_val * d_vec[0],
            ea[1] + t_val * d_vec[1],
            ea[2] + t_val * d_vec[2],
        )
        poly_pts.append(pt_xyz)
        if t_val == Fraction(1):
            boundary_oracle.append({"vertex": e[1]})
        elif t_val == Fraction(0):
            boundary_oracle.append({"vertex": e[0]})
        else:
            boundary_oracle.append({"edge": e, "t": str(t_val)})

    area_sq = _triangle_area_sq(poly_pts[0], poly_pts[1], poly_pts[2])

    edges_str = ", ".join("".join(edge) for edge, _ in named_cuts)
    pts_list = [pt_name for _, pt_name in named_cuts if pt_name]
    if pts_list:
        cut_clause = f"cắt các cạnh bên {edges_str} lần lượt tại {', '.join(pts_list)}"
    else:
        cut_clause = f"cắt các cạnh bên {edges_str}"
    stated_objs = [
        {
            "edge": edge,
            "point": pt_name,
            "quote": cut_clause,
        }
        for edge, pt_name in named_cuts
    ]
    q_parts = []
    sim_goals = []
    math_goals = []
    if question_type in ("section_only", "section_and_area"):
        q_parts.append("Xác định thiết diện của hình lăng trụ đứng ABC.A'B'C' cắt bởi mặt phẳng (α).")
        sim_goals.append(
            {
                "goal_id": "sg1",
                "kind": "construct_plane_section",
                "target_section_id": "sec",
                "target_solid_id": "s1",
                "quote": "Xác định thiết diện của hình lăng trụ đứng ABC.A'B'C' cắt bởi mặt phẳng (α).",
            }
        )
    else:
        sim_goals.append(
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
            }
        )
    if question_type in ("area_only", "section_and_area"):
        q_parts.append("Tính diện tích thiết diện của hình lăng trụ đứng ABC.A'B'C' cắt bởi mặt phẳng (α).")
        math_goals.append(
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "area",
                "solid_id": "s1",
                "target": {"section_id": "sec"},
                "quote": "Tính diện tích thiết diện của hình lăng trụ đứng ABC.A'B'C' cắt bởi mặt phẳng (α).",
            }
        )
    problem_text = (
        f"Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại B, "
        f"AB = {ab}{u}, BC = {bc}{u} và cạnh bên AA' = {aa_prime}{u}. "
        f"Mặt phẳng (α) đi qua điểm {through_pt} và vuông góc với đường thẳng {''.join(perp_line)}, "
        f"{cut_clause}. " + " ".join(q_parts)
    )
    sec_entry: dict[str, Any] = {
        "section_id": "sec",
        "plane_name": "α",
        "target_solid_id": "s1",
        "plane_kind": "through_point_perpendicular_line",
        "through_point": through_pt,
        "perpendicular_line": perp_line,
        "quote": f"Mặt phẳng (α) đi qua điểm {through_pt} và vuông góc với đường thẳng {''.join(perp_line)}, {cut_clause}.",
        "stated_intersections": stated_objs,
    }
    if declared_boundary is not None:
        sec_entry["declared_boundary"] = declared_boundary

    case = {
        "id": case_id,
        "stratum": "P-A",
        "family": "right_triangular_prism",
        "plane_relation": "stated_intersections",
        "question_type": question_type,
        "negative_class": None,
        "negative_origin": None,
        "problem_text": problem_text,
        "payload": {
            "schema_version": "typed-fact-next/2",
            "problem_text": problem_text,
            "length_unit": unit,
            "solids": [
                {
                    "solid_id": "s1",
                    "solid_type": "prism",
                    "notation": "ABC.A'B'C'",
                    "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
                }
            ],
            "premises": [
                {
                    "kind": "right_prism",
                    "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]},
                    "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
                    "solid_id": "s1",
                },
                {
                    "kind": "right_angle",
                    "args": {"vertices": ["A", "B", "C"], "right_at": "B"},
                    "quote": "có đáy ABC là tam giác vuông tại B",
                    "solid_id": "s1",
                },
                {
                    "kind": "segment_length",
                    "args": {"segment": ["A", "B"], "value": f"{ab}{u}"},
                    "quote": f"AB = {ab}{u}",
                    "solid_id": "s1",
                },
                {
                    "kind": "segment_length",
                    "args": {"segment": ["B", "C"], "value": f"{bc}{u}"},
                    "quote": f"BC = {bc}{u}",
                    "solid_id": "s1",
                },
                {
                    "kind": "segment_length",
                    "args": {"segment": ["A", "A'"], "value": f"{aa_prime}{u}"},
                    "quote": f"cạnh bên AA' = {aa_prime}{u}",
                    "solid_id": "s1",
                },
            ],
            "derived_sections": [sec_entry],
            "relations": [],
            "simulation_goals": sim_goals,
            "math_goals": math_goals,
        },
        "expected_disposition": "SERVE",
        "acceptable_categories": [],
    }
    oracle = {
        "solid": "ABC.A'B'C'",
        "section_id": "sec",
        "expected_certificate_category": "DINH_CAT_CANH",
        "area_goal_id": "mg1" if math_goals else None,
        "vertex_count": 3,
        "boundary": boundary_oracle,
        "area_squared": str(area_sq),
    }
    return case, oracle


def _make_cuboid_perp_case(
    case_id: str,
    ab: int,
    ad: int,
    aa_prime: int,
    through_pt: str,
    perp_line: list[str],
    named_cuts: list[tuple[list[str], str | None]],
    question_type: str,
    unit: str = "1",
    declared_boundary: list[str] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Independent exact Fraction oracle + typed-fact-next/2 payload for a cuboid
    ABCD.A'B'C'D' cut by a plane through a primed top vertex perpendicular to a diagonal.
    """
    u = "" if unit == "1" else unit
    pts: dict[str, tuple[Fraction, Fraction, Fraction]] = {
        "A": (Fraction(0), Fraction(0), Fraction(0)),
        "B": (Fraction(ab), Fraction(0), Fraction(0)),
        "C": (Fraction(ab), Fraction(ad), Fraction(0)),
        "D": (Fraction(0), Fraction(ad), Fraction(0)),
        "A'": (Fraction(0), Fraction(0), Fraction(aa_prime)),
        "B'": (Fraction(ab), Fraction(0), Fraction(aa_prime)),
        "C'": (Fraction(ab), Fraction(ad), Fraction(aa_prime)),
        "D'": (Fraction(0), Fraction(ad), Fraction(aa_prime)),
    }
    p0 = pts[through_pt]
    n_vec = _sub(pts[perp_line[1]], pts[perp_line[0]])

    all_edges = [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]]
    boundary_oracle = []
    poly_pts = []
    for e in all_edges:
        ea, eb = pts[e[0]], pts[e[1]]
        d_vec = _sub(eb, ea)
        t_val = _dot(_sub(p0, ea), n_vec) / _dot(d_vec, n_vec)
        assert Fraction(0) <= t_val <= Fraction(1), f"{case_id}: t={t_val} out of [0,1]"
        pt_xyz = (
            ea[0] + t_val * d_vec[0],
            ea[1] + t_val * d_vec[1],
            ea[2] + t_val * d_vec[2],
        )
        poly_pts.append(pt_xyz)
        if t_val == Fraction(1):
            boundary_oracle.append({"vertex": e[1]})
        elif t_val == Fraction(0):
            boundary_oracle.append({"vertex": e[0]})
        else:
            boundary_oracle.append({"edge": e, "t": str(t_val)})

    area_sq = _convex_quad_area_sq(poly_pts[0], poly_pts[1], poly_pts[2], poly_pts[3])

    edges_str = ", ".join("".join(edge) for edge, _ in named_cuts)
    pts_list = [pt_name for _, pt_name in named_cuts if pt_name]
    if pts_list:
        cut_clause = f"cắt các cạnh bên {edges_str} lần lượt tại {', '.join(pts_list)}"
    else:
        cut_clause = f"cắt các cạnh bên {edges_str}"
    stated_objs = [
        {
            "edge": edge,
            "point": pt_name,
            "quote": cut_clause,
        }
        for edge, pt_name in named_cuts
    ]
    q_parts = []
    sim_goals = []
    math_goals = []
    if question_type in ("section_only", "section_and_area"):
        q_parts.append("Xác định thiết diện của hình hộp chữ nhật ABCD.A'B'C'D' cắt bởi mặt phẳng (Q).")
        sim_goals.append(
            {
                "goal_id": "sg1",
                "kind": "construct_plane_section",
                "target_section_id": "sec",
                "target_solid_id": "s1",
                "quote": "Xác định thiết diện của hình hộp chữ nhật ABCD.A'B'C'D' cắt bởi mặt phẳng (Q).",
            }
        )
    else:
        sim_goals.append(
            {
                "goal_id": "sg1",
                "kind": "construct_object",
                "target_solid_id": "s1",
                "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'",
            }
        )
    if question_type in ("area_only", "section_and_area"):
        q_parts.append("Tính diện tích thiết diện của hình hộp chữ nhật ABCD.A'B'C'D' cắt bởi mặt phẳng (Q).")
        math_goals.append(
            {
                "goal_id": "mg1",
                "kind": "measurement",
                "goal_type": "area",
                "solid_id": "s1",
                "target": {"section_id": "sec"},
                "quote": "Tính diện tích thiết diện của hình hộp chữ nhật ABCD.A'B'C'D' cắt bởi mặt phẳng (Q).",
            }
        )
    problem_text = (
        f"Cho hình hộp chữ nhật ABCD.A'B'C'D' có đáy ABCD là hình chữ nhật với "
        f"AB = {ab}{u}, AD = {ad}{u} và cạnh bên AA' = {aa_prime}{u}. "
        f"Mặt phẳng (Q) đi qua điểm {through_pt} và vuông góc với đường thẳng {''.join(perp_line)}, "
        f"{cut_clause}. " + " ".join(q_parts)
    )
    sec_entry: dict[str, Any] = {
        "section_id": "sec",
        "plane_name": "Q",
        "target_solid_id": "s1",
        "plane_kind": "through_point_perpendicular_line",
        "through_point": through_pt,
        "perpendicular_line": perp_line,
        "quote": f"Mặt phẳng (Q) đi qua điểm {through_pt} và vuông góc với đường thẳng {''.join(perp_line)}, {cut_clause}.",
        "stated_intersections": stated_objs,
    }
    if declared_boundary is not None:
        sec_entry["declared_boundary"] = declared_boundary

    case = {
        "id": case_id,
        "stratum": "P-A",
        "family": "cuboid",
        "plane_relation": "stated_intersections",
        "question_type": question_type,
        "negative_class": None,
        "negative_origin": None,
        "problem_text": problem_text,
        "payload": {
            "schema_version": "typed-fact-next/2",
            "problem_text": problem_text,
            "length_unit": unit,
            "solids": [
                {
                    "solid_id": "s1",
                    "solid_type": "prism",
                    "notation": "ABCD.A'B'C'D'",
                    "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'",
                }
            ],
            "premises": [
                {
                    "kind": "right_prism",
                    "args": {"base": ["A", "B", "C", "D"], "top": ["A'", "B'", "C'", "D'"]},
                    "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'",
                    "solid_id": "s1",
                },
                {
                    "kind": "rectangle",
                    "args": {"vertices": ["A", "B", "C", "D"]},
                    "quote": "có đáy ABCD là hình chữ nhật",
                    "solid_id": "s1",
                },
                {
                    "kind": "segment_length",
                    "args": {"segment": ["A", "B"], "value": f"{ab}{u}"},
                    "quote": f"AB = {ab}{u}",
                    "solid_id": "s1",
                },
                {
                    "kind": "segment_length",
                    "args": {"segment": ["A", "D"], "value": f"{ad}{u}"},
                    "quote": f"AD = {ad}{u}",
                    "solid_id": "s1",
                },
                {
                    "kind": "segment_length",
                    "args": {"segment": ["A", "A'"], "value": f"{aa_prime}{u}"},
                    "quote": f"cạnh bên AA' = {aa_prime}{u}",
                    "solid_id": "s1",
                },
            ],
            "derived_sections": [sec_entry],
            "relations": [],
            "simulation_goals": sim_goals,
            "math_goals": math_goals,
        },
        "expected_disposition": "SERVE",
        "acceptable_categories": [],
    }
    oracle = {
        "solid": "ABCD.A'B'C'D'",
        "section_id": "sec",
        "expected_certificate_category": "DINH_CAT_CANH",
        "area_goal_id": "mg1" if math_goals else None,
        "vertex_count": 4,
        "boundary": boundary_oracle,
        "area_squared": str(area_sq),
    }
    return case, oracle


def build_positive_corpus_and_oracles() -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    with open(WAVE2_RUN / "inputs/holdout-wave2.json", "r", encoding="utf-8") as f:
        w2_cases = {c["id"]: c for c in json.load(f)["cases"]}
    with open(WAVE2_RUN / "oracle/expected.json", "r", encoding="utf-8") as f:
        raw_exp = json.load(f)
        w2_exp = raw_exp.get("expected_outcomes") or raw_exp

    positives: list[dict[str, Any]] = [
        deepcopy(w2_cases["W2-A07"]),
        deepcopy(w2_cases["W2-A10"]),
    ]
    oracles: dict[str, dict[str, Any]] = {
        "W2-A07": deepcopy(w2_exp["W2-A07"]),
        "W2-A10": deepcopy(w2_exp["W2-A10"]),
    }

    specs = [
        # 3. Right triangular prism, named cuts M, N, section_and_area
        _make_right_prism_perp_case(
            "DEV-POS-03", 3, 4, 10, "A'", ["A", "C'"],
            [(["B", "B'"], "M"), (["C", "C'"], "N")], "section_and_area",
        ),
        # 4. Right triangular prism, unnamed cuts on BB', CC', area_only
        _make_right_prism_perp_case(
            "DEV-POS-04", 6, 8, 20, "A'", ["A", "C'"],
            [(["B", "B'"], None), (["C", "C'"], None)], "area_only",
        ),
        # 5. Right triangular prism, through A' perp AB', named cuts M, N, section_only
        _make_right_prism_perp_case(
            "DEV-POS-05", 4, 3, 8, "A'", ["A", "B'"],
            [(["B", "B'"], "M"), (["C", "C'"], "N")], "section_only",
        ),
        # 6. Right triangular prism, through C' perp CA', named cuts M on AA', N on BB', section_and_area
        _make_right_prism_perp_case(
            "DEV-POS-06", 4, 3, 10, "C'", ["C", "A'"],
            [(["A", "A'"], "M"), (["B", "B'"], "N")], "section_and_area",
        ),
        # 7. Right triangular prism, through C' perp CB', unnamed cuts on AA', BB', area_only
        _make_right_prism_perp_case(
            "DEV-POS-07", 3, 4, 8, "C'", ["C", "B'"],
            [(["A", "A'"], None), (["B", "B'"], None)], "area_only",
        ),
        # 8. Right triangular prism with declared_boundary containing primed edge ["A", "A'"] -> closure boundary ["A'", "M", "N"]
        _make_right_prism_perp_case(
            "DEV-POS-08", 5, 5, 10, "A'", ["A", "C'"],
            [(["B", "B'"], "M"), (["C", "C'"], "N")], "section_and_area",
            declared_boundary=[["A", "A'"], ["B", "B'"], ["C", "C'"]],
        ),
        # 9. Cuboid with named cuts M, N, P and primed through-point A', section_and_area
        _make_cuboid_perp_case(
            "DEV-POS-09", 3, 6, 9, "A'", ["A", "C'"],
            [(["B", "B'"], "M"), (["C", "C'"], "N"), (["D", "D'"], "P")], "section_and_area", unit="a",
        ),
        # 10. Cuboid with unnamed cuts and primed through-point A', area_only
        _make_cuboid_perp_case(
            "DEV-POS-10", 6, 8, 20, "A'", ["A", "C'"],
            [(["B", "B'"], None), (["C", "C'"], None), (["D", "D'"], None)], "area_only",
        ),
        # 11. Cuboid with named cuts and declared_boundary [["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]] -> closure boundary ["A'", "M", "N", "P"]
        _make_cuboid_perp_case(
            "DEV-POS-11", 4, 8, 12, "A'", ["A", "C'"],
            [(["B", "B'"], "M"), (["C", "C'"], "N"), (["D", "D'"], "P")], "section_and_area",
            declared_boundary=[["A", "A'"], ["B", "B'"], ["C", "C'"], ["D", "D'"]],
        ),
        # 12. Cuboid with through-point B' perp BD', named cuts M on AA', N on CC', P on DD'
        _make_cuboid_perp_case(
            "DEV-POS-12", 3, 4, 10, "B'", ["B", "D'"],
            [(["A", "A'"], "M"), (["C", "C'"], "N"), (["D", "D'"], "P")], "section_and_area",
        ),
        # 13. Cuboid with through-point C' perp CA', unnamed cuts on AA', BB', DD'
        _make_cuboid_perp_case(
            "DEV-POS-13", 3, 4, 10, "C'", ["C", "A'"],
            [(["A", "A'"], None), (["B", "B'"], None), (["D", "D'"], None)], "section_only",
        ),
        # 14. Cuboid with through-point D' perp DB', named cuts E on AA', F on BB', G on CC'
        _make_cuboid_perp_case(
            "DEV-POS-14", 4, 3, 10, "D'", ["D", "B'"],
            [(["A", "A'"], "E"), (["B", "B'"], "F"), (["C", "C'"], "G")], "area_only",
        ),
    ]
    for c, o in specs:
        positives.append(c)
        oracles[c["id"]] = o
    return positives, oracles


NEGATIVE_SPECS: list[dict[str, Any]] = [
    {
        "id": "TAMPER-01",
        "base_case": "W2-A07",
        "tamper_kind": "NONEXISTENT_PRIMED_POINT",
        "description": "Điểm có dấu phẩy nhưng không tồn tại (Z' in section vertices).",
    },
    {
        "id": "TAMPER-02",
        "base_case": "W2-A07",
        "tamper_kind": "WRONG_SOLID_IDENTITY",
        "description": "Sai solid identity (solid notation in scene3d does not match planner DINH_CAT_CANH solid).",
    },
    {
        "id": "TAMPER-03",
        "base_case": "W2-A07",
        "tamper_kind": "VERTEX_FROM_ANOTHER_SOLID",
        "description": "Đỉnh thuộc solid khác (vertex edge references point from another solid).",
    },
    {
        "id": "TAMPER-04",
        "base_case": "W2-A07",
        "tamper_kind": "CUT_VERTEX_OFF_EDGE",
        "description": "Đỉnh cắt nằm ngoài cạnh (M shifted off line BB').",
    },
    {
        "id": "TAMPER-05",
        "base_case": "W2-A07",
        "tamper_kind": "INTERPOLATION_T_OUTSIDE_0_1",
        "description": "Nội suy t nằm ngoài [0,1] (M collinear with BB' at t = 5/4 > 1).",
    },
    {
        "id": "TAMPER-06",
        "base_case": "W2-A07",
        "tamper_kind": "SAME_LABEL_MISMATCHED_COORDINATES",
        "description": "Nhãn trùng nhưng tọa độ khác (A_prime xyz differs from section polygon vertex).",
    },
    {
        "id": "TAMPER-07",
        "base_case": "W2-A10",
        "tamper_kind": "MISSING_VERTEX_IN_CYCLE",
        "description": "Thiếu một đỉnh trong chu trình (4-vertex polygon with only 3 vertices in section.vertices).",
    },
    {
        "id": "TAMPER-08",
        "base_case": "W2-A07",
        "tamper_kind": "DUPLICATE_VERTEX",
        "description": "Duplicate vertex (A' and A′ / duplicate label in section.vertices).",
    },
    {
        "id": "TAMPER-09",
        "base_case": "W2-A10",
        "tamper_kind": "WRONG_SECTION_TOPOLOGY_ORDER",
        "description": "Sai thứ tự hoặc topology của section (bow-tie 4-cycle crossing non-adjacent prism faces).",
    },
    {
        "id": "TAMPER-10",
        "base_case": "W2-A07",
        "tamper_kind": "CATEGORY_A_B_CERTIFICATE_MIXING",
        "description": "Category A/B certificate mixing (Category A section carries ENGINE_DERIVED_SECTION / certificate_version).",
    },
    {
        "id": "TAMPER-11",
        "base_case": "W2-A07",
        "tamper_kind": "FORGED_PROVENANCE_STATED",
        "description": "Giả mạo stated/derived provenance (THROUGH_POINT_REUSE marked stated=True).",
    },
    {
        "id": "TAMPER-12",
        "base_case": "W2-A07",
        "tamper_kind": "AREA_SQUARED_MISMATCH",
        "description": "Area-squared không khớp oracle (kq_mg1 tampered to disagree with exact section polygon area_squared).",
    },
]


def apply_tamper(r: Any, tamper_kind: str) -> Any:
    """Apply a specific adversarial mutation to a deepcopy of a valid Category A KetQuaTuyen."""
    from app.ai.adapter4_route import _phong_bi
    from app.simulation.geometry.exact import Vec3
    from app.simulation.geometry_functions.planner import DINH_CAT_CANH

    rt = deepcopy(r)
    scene = rt.scene3d
    objs = {o["id"]: o for o in scene["objects"]}
    d_aux = next(d for d in rt.planner["auxiliary"] if d.get("rule") == DINH_CAT_CANH)
    sid = d_aux["goal"]
    td_obj = objs[f"td_{sid}"]

    if tamper_kind == "NONEXISTENT_PRIMED_POINT":
        d_aux["vertices"][0]["label"] = "Z'"
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "WRONG_SOLID_IDENTITY":
        solid_obj = next(o for o in scene["objects"] if o.get("type") == "solid")
        solid_obj["notation"] = "S.XYZ"
    elif tamper_kind == "VERTEX_FROM_ANOTHER_SOLID":
        scene["objects"].append(
            {"id": "X_prime", "type": "point3", "notation": "X′", "origin": "source", "xyz": ["5", "0", "10"]}
        )
        rt.exec_result.final_memory["X_prime"] = Vec3(Fraction(5), Fraction(0), Fraction(10))
        d_aux["vertices"][1]["edge"] = ["B", "X'"]
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "CUT_VERTEX_OFF_EDGE":
        # Shift M off the edge line BB' (x=5, y=0) to (4, 1, 15/2)
        objs["M"]["xyz"] = ["4", "1", "15/2"]
        rt.exec_result.final_memory["M"] = Vec3(Fraction(4), Fraction(1), Fraction(15, 2))
        td_obj["polygon"][1] = ["4", "1", "15/2"]
    elif tamper_kind == "INTERPOLATION_T_OUTSIDE_0_1":
        # Place M on line BB' at z = 25/2 (t = 5/4 > 1)
        objs["M"]["xyz"] = ["5", "0", "25/2"]
        rt.exec_result.final_memory["M"] = Vec3(Fraction(5), Fraction(0), Fraction(25, 2))
        td_obj["polygon"][1] = ["5", "0", "25/2"]
    elif tamper_kind == "SAME_LABEL_MISMATCHED_COORDINATES":
        objs["A_prime"]["xyz"] = ["0", "0", "9"]
        rt.exec_result.final_memory["A_prime"] = Vec3(Fraction(0), Fraction(0), Fraction(9))
    elif tamper_kind == "MISSING_VERTEX_IN_CYCLE":
        d_aux["vertices"] = d_aux["vertices"][:3]
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "DUPLICATE_VERTEX":
        d_aux["vertices"][1]["label"] = "A′"
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "WRONG_SECTION_TOPOLOGY_ORDER":
        # Swap index 1 (AA') and index 2 (DD') with index 3 (CC') so AA' is adjacent to CC' (opposite edges!)
        p = td_obj["polygon"]
        vs = td_obj["vertex_sources"]
        td_obj["polygon"] = [p[0], p[3], p[1], p[2]]
        td_obj["vertex_sources"] = [vs[0], vs[3], vs[1], vs[2]]
    elif tamper_kind == "CATEGORY_A_B_CERTIFICATE_MIXING":
        rt.route_d = _phong_bi(rt)
        rt.route_d["sections"][0]["certificate_category"] = "ENGINE_DERIVED_SECTION"
        rt.route_d["sections"][0]["certificate_version"] = "plane-section-certificate/1"
    elif tamper_kind == "FORGED_PROVENANCE_STATED":
        d_aux["vertices"][0]["stated"] = True
        rt.route_d = _phong_bi(rt)
    elif tamper_kind == "AREA_SQUARED_MISMATCH":
        rt.exec_result.final_memory["kq_mg1"] = Fraction(999)
        objs["kq_mg1"]["value"] = "999"
        rt.answers["mg1"] = "999"
        rt.answer_exact["mg1"]["coef"] = "999"
        rt.route_d = _phong_bi(rt)
    else:
        raise ValueError(f"Unknown tamper_kind: {tamper_kind}")
    return rt


def evaluate_corpus() -> dict[str, Any]:
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route
    from app.simulation.geometry_functions.engine import _binh_phuong

    positives, oracles = build_positive_corpus_and_oracles()
    pos_results = []
    base_route_cache: dict[str, Any] = {}

    for case in positives:
        cid = case["id"]
        exp = oracles[cid]
        r = run_typed_fact_next_v2_route(deepcopy(case["payload"]))
        base_route_cache[cid] = deepcopy(r)
        resp = build_adapter4_response(deepcopy(r), case["problem_text"])

        route_d = resp.get("route_d") or {}
        status = route_d.get("status")
        reason_code = (route_d.get("refusal") or {}).get("code")
        area_sq_obs = None
        area_match = True
        if exp.get("area_goal_id"):
            mem = getattr(r.exec_result, "final_memory", {}) or {}
            ans = mem.get(f"kq_{exp['area_goal_id']}")
            if ans is not None:
                area_sq_obs = str(_binh_phuong(ans))
                area_match = Fraction(area_sq_obs) == Fraction(exp["area_squared"])
            else:
                area_match = False

        # Check learner-facing labels (no _prime leaked in route_d["sections"] or notations)
        sections = route_d.get("sections") or []
        leaked_machine_id = False
        for s in sections:
            for v in s.get("vertices") or []:
                if "_prime" in str(v.get("label") or "") or any("_prime" in str(x) for x in (v.get("edge") or [])):
                    leaked_machine_id = True
            for b in s.get("boundary") or []:
                if "_prime" in str(b):
                    leaked_machine_id = True

        verdict = (
            "SERVED_CORRECT"
            if (status == "SERVED" and area_match and not leaked_machine_id and len(sections) == 1)
            else "FALSE_REFUSAL"
            if status == "REFUSED"
            else "WRONG_SERVED"
        )
        pos_results.append(
            {
                "id": cid,
                "family": case["family"],
                "question_type": case["question_type"],
                "engine_status": r.status,
                "adapter_status": status,
                "reason_code": reason_code,
                "oracle_area_squared": exp["area_squared"],
                "observed_area_squared": area_sq_obs,
                "area_exact_match": area_match,
                "leaked_machine_id": leaked_machine_id,
                "verdict": verdict,
            }
        )

    tamper_results = []
    for spec in NEGATIVE_SPECS:
        base_r = base_route_cache[spec["base_case"]]
        tampered_r = apply_tamper(base_r, spec["tamper_kind"])
        problem_text = next(c["problem_text"] for c in positives if c["id"] == spec["base_case"])
        resp = build_adapter4_response(tampered_r, problem_text)
        route_d = resp.get("route_d") or {}
        status = route_d.get("status")
        reason_code = (route_d.get("refusal") or {}).get("code")
        verdict = "CORRECT_REFUSAL" if status == "REFUSED" else "WRONG_SERVED"
        tamper_results.append(
            {
                "id": spec["id"],
                "base_case": spec["base_case"],
                "tamper_kind": spec["tamper_kind"],
                "description": spec["description"],
                "adapter_status": status,
                "reason_code": reason_code,
                "verdict": verdict,
            }
        )

    summary = {
        "git_head": _git_head(),
        "positive_total": len(pos_results),
        "positive_served_correct": sum(1 for x in pos_results if x["verdict"] == "SERVED_CORRECT"),
        "positive_false_refusal": sum(1 for x in pos_results if x["verdict"] == "FALSE_REFUSAL"),
        "positive_wrong_served": sum(1 for x in pos_results if x["verdict"] == "WRONG_SERVED"),
        "tamper_total": len(tamper_results),
        "tamper_correct_refusal": sum(1 for x in tamper_results if x["verdict"] == "CORRECT_REFUSAL"),
        "tamper_wrong_served": sum(1 for x in tamper_results if x["verdict"] == "WRONG_SERVED"),
        "positive_cases": pos_results,
        "tamper_cases": tamper_results,
    }
    return summary


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "build-and-red"
    sys.path.insert(0, str(WAVE2_RUN / "tools"))
    positives, oracles = build_positive_corpus_and_oracles()

    inputs_dir = RUN_DIR / "inputs"
    results_dir = RUN_DIR / "results"
    inputs_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)

    if mode == "build-and-red":
        with open(inputs_dir / "development.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "task_id": "HYBRID_V2_W2_M5_ADAPTER4_CATEGORY_A_IDENTITY_REPAIR",
                    "positive_cases": positives,
                    "negative_tamper_specs": NEGATIVE_SPECS,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        with open(inputs_dir / "oracle.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "task_id": "HYBRID_V2_W2_M5_ADAPTER4_CATEGORY_A_IDENTITY_REPAIR",
                    "oracles": oracles,
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        summary = evaluate_corpus()
        with open(results_dir / "red-before.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        print(
            f"[RED] positive_served_correct={summary['positive_served_correct']}/{summary['positive_total']} "
            f"tamper_correct_refusal={summary['tamper_correct_refusal']}/{summary['tamper_total']}"
        )
    elif mode == "green":
        summary = evaluate_corpus()
        with open(results_dir / "green-after.json", "w", encoding="utf-8") as f:
            json.dump(summary, f, ensure_ascii=False, indent=2)
        with open(results_dir / "tamper-results.json", "w", encoding="utf-8") as f:
            json.dump(
                {
                    "git_head": summary["git_head"],
                    "tamper_total": summary["tamper_total"],
                    "tamper_correct_refusal": summary["tamper_correct_refusal"],
                    "tamper_wrong_served": summary["tamper_wrong_served"],
                    "tamper_cases": summary["tamper_cases"],
                },
                f,
                ensure_ascii=False,
                indent=2,
            )
        print(
            f"[GREEN] positive_served_correct={summary['positive_served_correct']}/{summary['positive_total']} "
            f"tamper_correct_refusal={summary['tamper_correct_refusal']}/{summary['tamper_total']}"
        )
    else:
        raise SystemExit(f"Unknown mode: {mode}")


if __name__ == "__main__":
    main()
