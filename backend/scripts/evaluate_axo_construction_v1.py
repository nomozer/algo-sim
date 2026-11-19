# -*- coding: utf-8 -*-
"""Gold Typed Facts Benchmark, Novelty Audit, Baseline A vs Candidate B & Performance Telemetry (`AXO CONSTRUCTION /1`).

Runs completely offline (`ALLOW_LIVE_AI=0`, `GEMINI_API_KEY=""`) on 40 verified cases across Groups A–E,
comparing:
- Baseline A: `Planner /26 -> Registry /33 -> Engine /24 -> Adapter /4`
- Candidate B: `Dynamic Construction Planner /1 + Scene3D Bridge + L0-L4 Exact Verifier`

Emits:
- `GOLD_CONSTRUCTION_BENCHMARK_MANIFEST.json`
- `GOLD_CONSTRUCTION_BENCHMARK_RESULTS.json`
- `DYNAMIC_COMPOSITION_EVALUATION.json`
- `CONSTRUCTION_PERFORMANCE.json`
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("ALLOW_LIVE_AI", "0")
os.environ.setdefault("GEMINI_API_KEY", "")

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
SCRIPTS_DIR = REPO_ROOT / "backend" / "scripts"
for p in (BACKEND_DIR, SCRIPTS_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from app.ai import adapter4_route  # noqa: E402
from app.simulation.geometry_functions import engine, planner, registry  # noqa: E402
from experimental.construction_planner import (  # noqa: E402
    CONSTRUCTION_OPERATOR_SCHEMA,
    DYNAMIC_PLANNER_VERSION,
    EXACT_VERIFIER_VERSION,
    VERIFIED_CONSTRUCTION_GRAPH_SCHEMA,
)
from experimental.construction_planner.construction_operators import GoalSpec  # noqa: E402
from experimental.construction_planner.construction_search import DynamicConstructionPlanner, SearchBudget  # noqa: E402
from experimental.construction_planner.construction_serializer import canonical_json_dumps, serialize_proof_graph  # noqa: E402
from experimental.construction_planner.construction_state import PendingConstruction, build_initial_frame  # noqa: E402
from experimental.construction_planner.construction_verifier import verify_full_proof_and_scene  # noqa: E402
from experimental.construction_planner.scene3d_bridge import compile_proof_graph_to_scene3d  # noqa: E402
from slm_math_evaluator_v2 import same_value_v2  # noqa: E402

RUN_ID = "axo-construction-verified-graph-dynamic-planner-feasibility"
RUN_DIR = REPO_ROOT / "docs" / "evaluation" / "geometry" / "runs" / RUN_ID


# ---------------------------------------------------------------------------
# Reusable Solid Spec Builders for 40 Gold Typed Facts Cases (Groups A–E)
# ---------------------------------------------------------------------------


def _pyramid_right_B(a_sa: str = "a") -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = f"Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, AB = a, SA vuông góc với (ABC), SA = {a_sa}."
    solid = {"solid_name": "S.ABC", "solid_type": "pyramid", "apex": "S", "base_vertices": ["A", "B", "C"], "quote": "Cho hình chóp S.ABC"}
    prems = [
        {"id": "p1", "role": "premise", "kind": "right_angle", "at": "B", "points": ["A", "C"], "quotes": ["đáy ABC là tam giác vuông cân tại B"]},
        {"id": "p2", "role": "premise", "kind": "equal_lengths", "points_a": ["B", "A"], "points_b": ["B", "C"], "quotes": ["đáy ABC là tam giác vuông cân tại B"]},
        {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
        {"id": "p4", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
        {"id": "p5", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": a_sa, "quotes": [f"SA = {a_sa}"]},
    ]
    return txt, solid, prems


def _pyramid_equilateral(a_sa: str = "a") -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = f"Cho hình chóp S.ABC có đáy ABC là tam giác đều cạnh a, SA vuông góc với (ABC), SA = {a_sa}."
    solid = {"solid_name": "S.ABC", "solid_type": "pyramid", "apex": "S", "base_vertices": ["A", "B", "C"], "quote": "Cho hình chóp S.ABC"}
    prems = [
        {"id": "p1", "role": "premise", "kind": "polygon_shape", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "quotes": ["đáy ABC là tam giác đều cạnh a"]},
        {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["đáy ABC là tam giác đều cạnh a"]},
        {"id": "p3", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
        {"id": "p4", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": a_sa, "quotes": [f"SA = {a_sa}"]},
    ]
    return txt, solid, prems


def _pyramid_square(a_sa: str = "a") -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh a, SA vuông góc với (ABCD), SA = {a_sa}."
    solid = {"solid_name": "S.ABCD", "solid_type": "pyramid", "apex": "S", "base_vertices": ["A", "B", "C", "D"], "quote": "Cho hình chóp S.ABCD"}
    prems = [
        {"id": "p1", "role": "premise", "kind": "polygon_shape", "shape": "square", "points": ["A", "B", "C", "D"], "quotes": ["đáy ABCD là hình vuông cạnh a"]},
        {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["đáy ABCD là hình vuông cạnh a"]},
        {"id": "p3", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["SA vuông góc với (ABCD)"]},
        {"id": "p4", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": a_sa, "quotes": [f"SA = {a_sa}"]},
    ]
    return txt, solid, prems


def _cube_unit() -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = "Cho hình lập phương ABCD.A'B'C'D' cạnh a."
    solid = {
        "solid_name": "ABCD.A'B'C'D'",
        "solid_type": "cube",
        "right": True,
        "base_vertices": ["A", "B", "C", "D"],
        "top_vertices": ["A'", "B'", "C'", "D'"],
        "quote": "Cho hình lập phương ABCD.A'B'C'D' cạnh a",
    }
    prems = [
        {"id": "p1", "role": "premise", "kind": "polygon_shape", "shape": "square", "points": ["A", "B", "C", "D"], "value": "a", "quotes": ["Cho hình lập phương ABCD.A'B'C'D' cạnh a"]},
        {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "A'"], "value": "a", "quotes": ["Cho hình lập phương ABCD.A'B'C'D' cạnh a"]},
    ]
    return txt, solid, prems


def _right_prism_equilateral(h_val: str = "2a") -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = f"Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác đều cạnh a, AA' = {h_val}."
    solid = {
        "solid_name": "ABC.A'B'C'",
        "solid_type": "prism",
        "right": True,
        "base_vertices": ["A", "B", "C"],
        "top_vertices": ["A'", "B'", "C'"],
        "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
    }
    prems = [
        {"id": "p1", "role": "premise", "kind": "polygon_shape", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "quotes": ["đáy ABC là tam giác đều cạnh a"]},
        {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["đáy ABC là tam giác đều cạnh a"]},
        {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "A'"], "value": h_val, "quotes": [f"AA' = {h_val}"]},
    ]
    return txt, solid, prems


def build_benchmark_cases() -> list[dict[str, Any]]:
    """Build 40 verified Gold Typed Facts cases across Groups A–E with independent analytical oracles."""
    cases: list[dict[str, Any]] = []

    def add_case(
        cid: str,
        group: str,
        source: str,
        chart_tuple: tuple[str, dict[str, Any], list[dict[str, Any]]],
        pending: list[PendingConstruction],
        goal: GoalSpec,
        expected_status: str,
        oracle: str | None,
        baseline_tf2_extra: list[dict[str, Any]],
        baseline_question_text: str,
        capability_label: str,
        min_expected_plans: int = 1,
    ) -> None:
        base_txt, solid, prems = chart_tuple
        full_txt = (base_txt + " " + baseline_question_text).strip()
        tf2_facts = [
            {
                "id": "s1",
                "kind": "solid",
                "role": "premise",
                "solid": solid["solid_name"],
                "solid_type": solid["solid_type"],
                **({"right": bool(solid["right"])} if "right" in solid else {}),
                "quotes": [solid["quote"]],
            },
            *prems,
            *baseline_tf2_extra,
        ]
        cases.append(
            {
                "case_id": cid,
                "group": group,
                "source_provenance": source,
                "problem_text": base_txt,
                "full_problem_text": full_txt,
                "solid_spec": solid,
                "chart_premises": prems,
                "pending": pending,
                "goal_spec": goal,
                "expected_status": expected_status,
                "independent_oracle": oracle,
                "capability_label": capability_label,
                "min_expected_plans": min_expected_plans,
                "baseline_tf2_facts": tf2_facts,
            }
        )

    # ======================== GROUP A: 10 Existing Validated Constructions ========================
    add_case(
        "A01_sb_length_right_pyramid",
        "Group_A",
        "Curriculum_G11_Pyramid_Metric",
        _pyramid_right_B("a"),
        [],
        GoalSpec("segment_length", {"a": "S", "b": "B"}, "a"),
        "GOAL_VERIFIED",
        "a√2",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["S", "B"], "quotes": ["Tính độ dài SB"]}],
        "Tính độ dài SB.",
        "DIRECT_SOLID_EDGE_LENGTH",
    )
    add_case(
        "A02_midpoint_sm_equilateral",
        "Group_A",
        "Curriculum_G11_Midpoint_Segment",
        _pyramid_equilateral("a"),
        [PendingConstruction("pend_M", "op.midpoint_segment", "M", {"a": "B", "b": "C"}, description="Gọi M là trung điểm BC")],
        GoalSpec("segment_length", {"a": "S", "b": "M"}, "a"),
        "GOAL_VERIFIED",
        "a√7/2",
        [
            {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M", "points": ["B", "C"], "quotes": ["Gọi M là trung điểm BC"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["S", "M"], "quotes": ["Tính SM"]},
        ],
        "Gọi M là trung điểm BC. Tính SM.",
        "MIDPOINT_COMPOSITION",
    )
    add_case(
        "A03_centroid_sg_square_base",
        "Group_A",
        "Curriculum_G11_Centroid",
        _pyramid_square("2a"),
        [PendingConstruction("pend_G", "op.triangle_centroid", "G", {"a": "A", "b": "B", "c": "C"}, description="Gọi G là trọng tâm tam giác ABC")],
        GoalSpec("segment_length", {"a": "S", "b": "G"}, "a"),
        "GOAL_VERIFIED",
        "a√41/3",
        [
            {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "centroid", "point": "G", "points": ["A", "B", "C"], "quotes": ["Gọi G là trọng tâm tam giác ABC"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["S", "G"], "quotes": ["Tính SG"]},
        ],
        "Gọi G là trọng tâm tam giác ABC. Tính SG.",
        "CENTROID_COMPOSITION",
    )

    add_case(
        "A04_midpoint_am_right_B",
        "Group_A",
        "Curriculum_G11_Midpoint_Segment",
        _pyramid_right_B("a"),
        [PendingConstruction("pend_M", "op.midpoint_segment", "M", {"a": "S", "b": "C"}, description="Gọi M là trung điểm SC")],
        GoalSpec("segment_length", {"a": "A", "b": "M"}, "a"),
        "GOAL_VERIFIED",
        "a√3/2",
        [
            {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M", "points": ["S", "C"], "quotes": ["Gọi M là trung điểm SC"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "M"], "quotes": ["Tính AM"]},
        ],
        "Gọi M là trung điểm SC. Tính AM.",
        "HYPOTENUSE_MEDIAN",
    )
    add_case(
        "A05_volume_pyramid_right_B",
        "Group_A",
        "Curriculum_G12_Solid_Volume",
        _pyramid_right_B("2a"),
        [],
        GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "a³/3",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABC", "quotes": ["Tính thể tích khối chóp S.ABC"]}],
        "Tính thể tích khối chóp S.ABC.",
        "VOLUME_WITH_ALTITUDE_WITNESS",
    )
    add_case(
        "A06_volume_equilateral_pyramid",
        "Group_A",
        "Curriculum_G12_Solid_Volume",
        _pyramid_equilateral("3a"),
        [],
        GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "a³√3/4",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABC", "quotes": ["Tính thể tích khối chóp S.ABC"]}],
        "Tính thể tích khối chóp S.ABC.",
        "VOLUME_OBLIQUE_METRIC",
    )
    add_case(
        "A07_angle_sc_base_square",
        "Group_A",
        "Curriculum_G11_Line_Plane_Angle",
        _pyramid_square("2a"),
        [],
        GoalSpec("angle_line_plane", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"], "output_mode": "cos"}, "a"),
        "GOAL_VERIFIED",
        "cos=√3/3",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "angle", "points_a": ["S", "C"], "points_b": ["A", "B", "C", "D"], "quotes": ["Tính góc giữa SC và (ABCD)"]}],
        "Tính góc giữa SC và (ABCD).",
        "ANGLE_LINE_PLANE_GIVEN_ALTITUDE",
    )
    add_case(
        "A08_angle_sb_base_right",
        "Group_A",
        "Curriculum_G11_Line_Plane_Angle",
        _pyramid_right_B("a"),
        [],
        GoalSpec("angle_line_plane", {"line": ["S", "B"], "plane": ["A", "B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "45°",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "angle", "points_a": ["S", "B"], "points_b": ["A", "B", "C"], "quotes": ["Tính góc giữa SB và (ABC)"]}],
        "Tính góc giữa SB và (ABC).",
        "ANGLE_LINE_PLANE_SPECIAL",
    )
    add_case(
        "A09_cube_face_diagonal_intersection_midpoint",
        "Group_A",
        "Curriculum_G11_Cube_Intersection",
        _cube_unit(),
        [
            PendingConstruction("pend_AC", "op.line_through_points", "ln_AC", {"a": "A", "b": "C"}, description="Đường chéo AC"),
            PendingConstruction("pend_BD", "op.line_through_points", "ln_BD", {"a": "B", "b": "D"}, description="Đường chéo BD"),
            PendingConstruction("pend_O", "op.intersect_coplanar_lines", "O", {"line1": "ln_AC", "line2": "ln_BD"}, description="Gọi O là giao điểm AC và BD"),
        ],
        GoalSpec("segment_length", {"a": "A'", "b": "O"}, "a"),
        "GOAL_VERIFIED",
        "a√6/2",
        [
            {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "intersect_line_line", "point": "O", "points_a": ["A", "C"], "points_b": ["B", "D"], "quotes": ["Gọi O là giao điểm AC và BD"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["A'", "O"], "quotes": ["Tính A'O"]},
        ],
        "Gọi O là giao điểm AC và BD. Tính A'O.",
        "LINE_LINE_INTERSECTION",
    )
    add_case(
        "A10_cube_section_diagonal_plane",
        "Group_A",
        "Curriculum_G11_Section_Area",
        _cube_unit(),
        [],
        GoalSpec("section_area", {"plane": ["B", "D", "D'"]}, "a"),
        "GOAL_VERIFIED",
        "a²√2",
        [
            {"id": "sec1", "role": "premise", "kind": "section", "solid": "ABCD.A'B'C'D'", "points": ["B", "D", "D'"], "quotes": ["Tính diện tích thiết diện của (BDD') với ABCD.A'B'C'D'"]},
            {"id": "q1", "role": "question", "kind": "question", "quantity": "area", "solid": "ABCD.A'B'C'D'", "points": ["B", "D", "D'"], "quotes": ["Tính diện tích thiết diện của (BDD') với ABCD.A'B'C'D'"]},
        ],
        "Tính diện tích thiết diện của (BDD') với ABCD.A'B'C'D'.",
        "SECTION_AREA",
    )

    # ======================== GROUP B: 10 Dynamic Composition Candidates ========================
    add_case(
        "B01_divide_segment_ratio_length",
        "Group_B",
        "Dynamic_DivideSegment_Chain",
        _pyramid_square("3a"),
        [
            PendingConstruction("pend_K", "op.divide_segment_ratio", "K", {"a": "S", "b": "A"}, params={"ratio": "1/3"}, description="Lấy K trên SA sao cho SK = 1/3 SA"),
            PendingConstruction("pend_M", "op.midpoint_segment", "M", {"a": "B", "b": "C"}, description="Gọi M là trung điểm BC"),
        ],
        GoalSpec("segment_length", {"a": "K", "b": "M"}, "a"),
        "GOAL_VERIFIED",
        "a√21/2",
        [
            {"id": "pd1", "role": "premise", "kind": "segment_ratio", "points_a": ["S", "K"], "points_b": ["S", "A"], "value": "1/3", "quotes": ["Lấy K trên SA sao cho SK = 1/3 SA"]},
            {"id": "pd2", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M", "points": ["B", "C"], "quotes": ["Gọi M là trung điểm BC"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["K", "M"], "quotes": ["Tính KM"]},
        ],
        "Lấy K trên SA sao cho SK = 1/3 SA. Gọi M là trung điểm BC. Tính KM.",
        "DIVIDE_SEGMENT_DYNAMIC_COMPOSITION",
    )
    add_case(
        "B02_point_reflection_distance",
        "Group_B",
        "Dynamic_PointReflection_Chain",
        _pyramid_right_B("a"),
        [
            PendingConstruction("pend_P", "op.point_reflection", "P", {"point": "A", "center": "B"}, description="Lấy P đối xứng với A qua B"),
        ],
        GoalSpec("segment_length", {"a": "S", "b": "P"}, "a"),
        "GOAL_VERIFIED",
        "a√5",
        [
            {"id": "pd1", "role": "premise", "kind": "point_reflection", "at": "P", "point": "A", "points": ["B"], "quotes": ["Lấy P đối xứng với A qua B"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["S", "P"], "quotes": ["Tính SP"]},
        ],
        "Lấy P đối xứng với A qua B. Tính SP.",
        "POINT_REFLECTION_DYNAMIC_COMPOSITION",
    )
    add_case(
        "B03_dihedral_linear_angle_equilateral",
        "Group_B",
        "Dynamic_Dihedral_ZeroContractInRegistry33",
        _pyramid_equilateral("a"),
        [],
        GoalSpec("angle_plane_plane", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "cos²=3/7",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "angle", "points_a": ["S", "B", "C"], "points_b": ["A", "B", "C"], "quotes": ["Tính góc giữa (SBC) và (ABC)"]}],
        "Tính góc giữa (SBC) và (ABC).",
        "DIHEDRAL_LINEAR_ANGLE_SYNTHESIS",
    )
    add_case(
        "B04_dihedral_linear_angle_cube",
        "Group_B",
        "Dynamic_Dihedral_Cube",
        _cube_unit(),
        [],
        GoalSpec("angle_plane_plane", {"plane1": ["B", "D", "A'"], "plane2": ["A", "B", "C", "D"]}, "a"),
        "GOAL_VERIFIED",
        "cos²=1/3",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "angle", "points_a": ["B", "D", "A'"], "points_b": ["A", "B", "C", "D"], "quotes": ["Tính góc giữa (BDA') và (ABCD)"]}],
        "Tính góc giữa (BDA') và (ABCD).",
        "DIHEDRAL_LINEAR_ANGLE_SYNTHESIS",
    )
    add_case(
        "B05_skew_angle_cube_parallel_transfer",
        "Group_B",
        "Dynamic_SkewLines_ParallelTransfer",
        _cube_unit(),
        [],
        GoalSpec("angle_lines", {"line1": ["A", "B'"], "line2": ["B", "C'"]}, "a"),
        "GOAL_VERIFIED",
        "60°",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "angle", "points_a": ["A", "B'"], "points_b": ["B", "C'"], "quotes": ["Tính góc giữa AB' và BC'"]}],
        "Tính góc giữa AB' và BC'.",
        "PARALLEL_TRANSFER_ANGLE_SYNTHESIS",
    )
    add_case(
        "B06_divide_segment_plus_point_plane_distance",
        "Group_B",
        "Dynamic_DivideSegment_AuxProjection",
        _pyramid_square("3a"),
        [
            PendingConstruction("pend_K", "op.divide_segment_ratio", "K", {"a": "S", "b": "A"}, params={"ratio": "1/3"}, description="Lấy K trên SA sao cho SK = 1/3 SA"),
        ],
        GoalSpec("distance_point_plane", {"point": "K", "plane": ["S", "B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "a√10/10",
        [
            {"id": "pd1", "role": "premise", "kind": "segment_ratio", "points_a": ["S", "K"], "points_b": ["S", "A"], "value": "1/3", "quotes": ["Lấy K trên SA sao cho SK = 1/3 SA"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["K"], "points_b": ["S", "B", "C"], "quotes": ["Tính khoảng cách từ K đến (SBC)"]},
        ],
        "Lấy K trên SA sao cho SK = 1/3 SA. Tính khoảng cách từ K đến (SBC).",
        "RATIO_TO_PLANE_DISTANCE",
    )

    add_case(
        "B07_reflection_plus_centroid_length",
        "Group_B",
        "Dynamic_Reflection_Centroid_MultiStep",
        _pyramid_right_B("2a"),
        [
            PendingConstruction("pend_P", "op.point_reflection", "P", {"point": "A", "center": "C"}, description="Lấy P đối xứng A qua C"),
            PendingConstruction("pend_G", "op.triangle_centroid", "G", {"a": "S", "b": "B", "c": "P"}, description="Gọi G là trọng tâm tam giác SBP"),
        ],
        GoalSpec("segment_length", {"a": "A", "b": "G"}, "a"),
        "GOAL_VERIFIED",
        "a√17/3",
        [
            {"id": "pd1", "role": "premise", "kind": "point_reflection", "at": "P", "point": "A", "points": ["C"], "quotes": ["Lấy P đối xứng A qua C"]},
            {"id": "pd2", "role": "premise", "kind": "point_def", "point_kind": "centroid", "point": "G", "points": ["S", "B", "P"], "quotes": ["Gọi G là trọng tâm tam giác SBP"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "G"], "quotes": ["Tính AG"]},
        ],
        "Lấy P đối xứng A qua C. Gọi G là trọng tâm tam giác SBP. Tính AG.",
        "MULTI_OPERATOR_CHAIN",
    )

    add_case(
        "B08_intersection_point_derived_plane_prism",
        "Group_B",
        "Dynamic_Prism_Midpoint_Intersect_Line_Plane",
        _right_prism_equilateral("2a"),
        [
            PendingConstruction("pend_M", "op.midpoint_segment", "M", {"a": "A'", "b": "B'"}, description="Gọi M là trung điểm A'B'"),
            PendingConstruction("pend_N", "op.midpoint_segment", "N", {"a": "B'", "b": "C'"}, description="Gọi N là trung điểm B'C'"),
            PendingConstruction("pend_pl", "op.plane_through_three_points", "pl_AMN", {"a": "A", "b": "M", "c": "N"}, description="Mặt phẳng (AMN)"),
            PendingConstruction("pend_I", "op.intersect_line_plane", "I", {"line": ["B", "B'"], "plane": "pl_AMN"}, description="Gọi I là giao điểm của BB' và (AMN)"),
        ],
        GoalSpec("segment_length", {"a": "B", "b": "I"}, "a"),
        "GOAL_VERIFIED",
        "4a",
        [
            {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M", "points": ["A'", "B'"], "quotes": ["Gọi M là trung điểm A'B'"]},
            {"id": "pd2", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "N", "points": ["B'", "C'"], "quotes": ["Gọi N là trung điểm B'C'"]},
            {"id": "pd3", "role": "premise", "kind": "point_def", "point_kind": "intersect_line_plane", "point": "I", "points_a": ["B", "B'"], "points_b": ["A", "M", "N"], "quotes": ["Gọi I là giao điểm của BB' và (AMN)"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["B", "I"], "quotes": ["Tính BI"]},
        ],
        "Gọi M là trung điểm A'B'. Gọi N là trung điểm B'C'. Gọi I là giao điểm của BB' và (AMN). Tính BI.",
        "MULTI_STEP_DERIVED_PLANE_INTERSECTION",
    )

    # B09: Deep 19-step chain (> 32 IR memory declarations on Baseline A SemanticProgramSpec) -> exact center of unit cube M19 -> |AM19| = a√3/2
    b09_pends = [
        PendingConstruction("pend_M1", "op.midpoint_segment", "M1", {"a": "A", "b": "B"}, description="Gọi M1 là trung điểm của AB"),
        PendingConstruction("pend_M2", "op.midpoint_segment", "M2", {"a": "B", "b": "C"}, description="Gọi M2 là trung điểm của BC"),
        PendingConstruction("pend_M3", "op.midpoint_segment", "M3", {"a": "C", "b": "D"}, description="Gọi M3 là trung điểm của CD"),
        PendingConstruction("pend_M4", "op.midpoint_segment", "M4", {"a": "D", "b": "A"}, description="Gọi M4 là trung điểm của DA"),
        PendingConstruction("pend_M5", "op.midpoint_segment", "M5", {"a": "A'", "b": "B'"}, description="Gọi M5 là trung điểm của A'B'"),
        PendingConstruction("pend_M6", "op.midpoint_segment", "M6", {"a": "B'", "b": "C'"}, description="Gọi M6 là trung điểm của B'C'"),
        PendingConstruction("pend_M7", "op.midpoint_segment", "M7", {"a": "C'", "b": "D'"}, description="Gọi M7 là trung điểm của C'D'"),
        PendingConstruction("pend_M8", "op.midpoint_segment", "M8", {"a": "D'", "b": "A'"}, description="Gọi M8 là trung điểm của D'A'"),
        PendingConstruction("pend_M9", "op.midpoint_segment", "M9", {"a": "A", "b": "A'"}, description="Gọi M9 là trung điểm của AA'"),
        PendingConstruction("pend_M10", "op.midpoint_segment", "M10", {"a": "B", "b": "B'"}, description="Gọi M10 là trung điểm của BB'"),
        PendingConstruction("pend_M11", "op.midpoint_segment", "M11", {"a": "C", "b": "C'"}, description="Gọi M11 là trung điểm của CC'"),
        PendingConstruction("pend_M12", "op.midpoint_segment", "M12", {"a": "D", "b": "D'"}, description="Gọi M12 là trung điểm của DD'"),
        PendingConstruction("pend_M13", "op.triangle_centroid", "M13", {"a": "M1", "b": "M2", "c": "M3"}, description="Gọi M13 là trọng tâm tam giác M1M2M3"),
        PendingConstruction("pend_M14", "op.triangle_centroid", "M14", {"a": "M4", "b": "M5", "c": "M6"}, description="Gọi M14 là trọng tâm tam giác M4M5M6"),
        PendingConstruction("pend_M15", "op.triangle_centroid", "M15", {"a": "M7", "b": "M8", "c": "M9"}, description="Gọi M15 là trọng tâm tam giác M7M8M9"),
        PendingConstruction("pend_M16", "op.triangle_centroid", "M16", {"a": "M10", "b": "M11", "c": "M12"}, description="Gọi M16 là trọng tâm tam giác M10M11M12"),
        PendingConstruction("pend_M17", "op.midpoint_segment", "M17", {"a": "M13", "b": "M14"}, description="Gọi M17 là trung điểm của M13M14"),
        PendingConstruction("pend_M18", "op.midpoint_segment", "M18", {"a": "M15", "b": "M16"}, description="Gọi M18 là trung điểm của M15M16"),
        PendingConstruction("pend_M19", "op.midpoint_segment", "M19", {"a": "M17", "b": "M18"}, description="Gọi M19 là trung điểm của M17M18"),
    ]
    b09_quotes = [p.description for p in b09_pends]
    b09_tf2 = [
        {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M1", "points": ["A", "B"], "quotes": ["Gọi M1 là trung điểm của AB"]},
        {"id": "pd2", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M2", "points": ["B", "C"], "quotes": ["Gọi M2 là trung điểm của BC"]},
        {"id": "pd3", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M3", "points": ["C", "D"], "quotes": ["Gọi M3 là trung điểm của CD"]},
        {"id": "pd4", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M4", "points": ["D", "A"], "quotes": ["Gọi M4 là trung điểm của DA"]},
        {"id": "pd5", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M5", "points": ["A'", "B'"], "quotes": ["Gọi M5 là trung điểm của A'B'"]},
        {"id": "pd6", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M6", "points": ["B'", "C'"], "quotes": ["Gọi M6 là trung điểm của B'C'"]},
        {"id": "pd7", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M7", "points": ["C'", "D'"], "quotes": ["Gọi M7 là trung điểm của C'D'"]},
        {"id": "pd8", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M8", "points": ["D'", "A'"], "quotes": ["Gọi M8 là trung điểm của D'A'"]},
        {"id": "pd9", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M9", "points": ["A", "A'"], "quotes": ["Gọi M9 là trung điểm của AA'"]},
        {"id": "pd10", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M10", "points": ["B", "B'"], "quotes": ["Gọi M10 là trung điểm của BB'"]},
        {"id": "pd11", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M11", "points": ["C", "C'"], "quotes": ["Gọi M11 là trung điểm của CC'"]},
        {"id": "pd12", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M12", "points": ["D", "D'"], "quotes": ["Gọi M12 là trung điểm của DD'"]},
        {"id": "pd13", "role": "premise", "kind": "point_def", "point_kind": "centroid", "point": "M13", "points": ["M1", "M2", "M3"], "quotes": ["Gọi M13 là trọng tâm tam giác M1M2M3"]},
        {"id": "pd14", "role": "premise", "kind": "point_def", "point_kind": "centroid", "point": "M14", "points": ["M4", "M5", "M6"], "quotes": ["Gọi M14 là trọng tâm tam giác M4M5M6"]},
        {"id": "pd15", "role": "premise", "kind": "point_def", "point_kind": "centroid", "point": "M15", "points": ["M7", "M8", "M9"], "quotes": ["Gọi M15 là trọng tâm tam giác M7M8M9"]},
        {"id": "pd16", "role": "premise", "kind": "point_def", "point_kind": "centroid", "point": "M16", "points": ["M10", "M11", "M12"], "quotes": ["Gọi M16 là trọng tâm tam giác M10M11M12"]},
        {"id": "pd17", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M17", "points": ["M13", "M14"], "quotes": ["Gọi M17 là trung điểm của M13M14"]},
        {"id": "pd18", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M18", "points": ["M15", "M16"], "quotes": ["Gọi M18 là trung điểm của M15M16"]},
        {"id": "pd19", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M19", "points": ["M17", "M18"], "quotes": ["Gọi M19 là trung điểm của M17M18"]},
        {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "M19"], "quotes": ["Tính AM19"]},
    ]
    add_case(
        "B09_deep_19step_chain_exceeds_32_ir_slots",
        "Group_B",
        "Dynamic_Deep_Chain_Exceeds_IR32",
        _cube_unit(),
        b09_pends,
        GoalSpec("segment_length", {"a": "A", "b": "M19"}, "a"),
        "GOAL_VERIFIED",
        "a√3/2",
        b09_tf2,
        ". ".join(b09_quotes) + ". Tính AM19.",
        "DEEP_CHAIN_EXCEEDS_32_IR_SLOTS",
    )
    add_case(
        "B10_derived_polygon_area_after_ratio",
        "Group_B",
        "Dynamic_PolygonArea_ComposedPoints",
        _pyramid_square("2a"),
        [
            PendingConstruction("pend_M", "op.divide_segment_ratio", "M", {"a": "S", "b": "B"}, params={"ratio": "1/2"}, description="M trung điểm SB"),
            PendingConstruction("pend_N", "op.divide_segment_ratio", "N", {"a": "S", "b": "C"}, params={"ratio": "1/2"}, description="N trung điểm SC"),
            PendingConstruction("pend_P", "op.divide_segment_ratio", "P", {"a": "S", "b": "D"}, params={"ratio": "1/2"}, description="P trung điểm SD"),
        ],
        GoalSpec("polygon_area", {"points": ["A", "M", "N"]}, "a"),
        "GOAL_VERIFIED",
        "a²√5/8",
        [
            {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M", "points": ["S", "B"], "quotes": ["Gọi M là trung điểm của SB"]},
            {"id": "pd2", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "N", "points": ["S", "C"], "quotes": ["Gọi N là trung điểm của SC"]},
            {"id": "pd3", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "P", "points": ["S", "D"], "quotes": ["Gọi P là trung điểm của SD"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "area", "points": ["A", "M", "N"], "quotes": ["Tính diện tích tam giác AMN"]},
        ],
        "Gọi M là trung điểm của SB. Gọi N là trung điểm của SC. Gọi P là trung điểm của SD. Tính diện tích tam giác AMN.",
        "DERIVED_TRIANGLE_AREA_CONSTRUCTED_EDGES",
    )

    # ======================== GROUP C: 8 Auxiliary Construction Cases ========================
    add_case(
        "C01_aux_foot_d_A_SBC_equilateral",
        "Group_C",
        "Aux_Foot_PointToPlane_Equilateral",
        _pyramid_equilateral("a"),
        [],
        GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "a√21/7",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["S", "B", "C"], "quotes": ["Tính khoảng cách từ A đến (SBC)"]}],
        "Tính khoảng cách từ A đến (SBC).",
        "AUX_FOOT_DISCOVERY",
    )
    add_case(
        "C02_aux_foot_d_A_SBD_square",
        "Group_C",
        "Aux_Foot_PointToPlane_SquareDiagonal",
        _pyramid_square("a"),
        [],
        GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "D"]}, "a"),
        "GOAL_VERIFIED",
        "a√3/3",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["S", "B", "D"], "quotes": ["Tính khoảng cách từ A đến (SBD)"]}],
        "Tính khoảng cách từ A đến (SBD).",
        "AUX_FOOT_DISCOVERY",
    )
    add_case(
        "C03_aux_parallel_line_plane_transfer",
        "Group_C",
        "Aux_LinePlane_DistanceTransfer",
        _pyramid_square("a"),
        [],
        GoalSpec("distance_line_plane", {"line": ["A", "B"], "plane": ["S", "C", "D"]}, "a"),
        "GOAL_VERIFIED",
        "a√2/2",  # AB // (SCD) -> d(A, (SCD)) = a√2/2
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["A", "B"], "points_b": ["S", "C", "D"], "quotes": ["Tính khoảng cách giữa AB và (SCD)"]}],
        "Tính khoảng cách giữa AB và (SCD).",
        "AUX_PARALLEL_TRANSFER_AND_FOOT",
    )
    add_case(
        "C04_aux_skew_lines_cube_ABp_BCp",
        "Group_C",
        "Aux_SkewLines_CubeDiagonals",
        _cube_unit(),
        [],
        GoalSpec("distance_skew_lines", {"line1": ["A", "B'"], "line2": ["B", "C'"]}, "a"),
        "GOAL_VERIFIED",
        "a√3/3",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["A", "B'"], "points_b": ["B", "C'"], "quotes": ["Tính khoảng cách giữa AB' và BC'"]}],
        "Tính khoảng cách giữa AB' và BC'.",
        "AUX_COMMON_PERP_OR_PAR_PLANE",
    )
    add_case(
        "C05_aux_skew_lines_pyramid_SA_BD",
        "Group_C",
        "Aux_SkewLines_SquarePyramid",
        _pyramid_square("2a"),
        [],
        GoalSpec("distance_skew_lines", {"line1": ["S", "A"], "line2": ["B", "D"]}, "a"),
        "GOAL_VERIFIED",
        "a√2/2",  # AO = a√2/2 perpendicular to both SA and BD
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["S", "A"], "points_b": ["B", "D"], "quotes": ["Tính khoảng cách giữa SA và BD"]}],
        "Tính khoảng cách giữa SA và BD.",
        "AUX_COMMON_PERP_OR_PAR_PLANE",
    )
    add_case(
        "C06_aux_point_to_line_foot",
        "Group_C",
        "Aux_PointToLine_Foot",
        _pyramid_right_B("a"),
        [],
        GoalSpec("distance_point_line", {"point": "A", "line": ["S", "C"]}, "a"),
        "GOAL_VERIFIED",
        "a√6/3",  # Right triangle SAC: SA=a, AC=a√2, SC=a√3 -> d(A,SC) = a*a√2/(a√3) = a√6/3!
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["S", "C"], "quotes": ["Tính khoảng cách từ A đến SC"]}],
        "Tính khoảng cách từ A đến SC.",
        "AUX_POINT_LINE_FOOT",
    )
    add_case(
        "C07_aux_angle_line_plane_SB_SAC",
        "Group_C",
        "Aux_Angle_LinePlane_FootProjection",
        _pyramid_square("2a"),
        [],
        GoalSpec("angle_line_plane", {"line": ["S", "B"], "plane": ["S", "A", "C"]}, "a"),
        "GOAL_VERIFIED",
        # S(0,0,2), B(1,0,0), plane (SAC): x - y = 0. Foot of B onto (SAC) is O(1/2, 1/2, 0). |BO| = √2/2, |SB| = √5 -> sin θ = (√2/2)/√5 = √10/10, cos² = 9/10!
        "cos²=9/10",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "angle", "points_a": ["S", "B"], "points_b": ["S", "A", "C"], "quotes": ["Tính góc giữa SB và (SAC)"]}],
        "Tính góc giữa SB và (SAC).",
        "AUX_LINE_PLANE_PROJECTION_WITNESS",
    )
    add_case(
        "C08_aux_parallel_plane_section_through_midpoint",
        "Group_C",
        "Aux_ParallelPlane_Section",
        _pyramid_equilateral("2a"),
        [
            PendingConstruction("pend_M", "op.midpoint_segment", "M", {"a": "S", "b": "A"}, description="Gọi M là trung điểm SA"),
            PendingConstruction("pend_pl", "op.plane_through_point_parallel_plane", "pl_sec", {"point": "M", "plane": "day_ABC"}, description="Mặt phẳng qua M song song với (ABC)"),
        ],
        GoalSpec("section_area", {"plane": "pl_sec"}, "a"),
        "GOAL_VERIFIED",
        "a²√3/16",
        [
            {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M", "points": ["S", "A"], "quotes": ["Gọi M là trung điểm của SA"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "area", "solid": "S.ABC", "plane_relation": "parallel", "point": "M", "points_b": ["A", "B", "C"], "quotes": ["Tính diện tích thiết diện của mặt phẳng qua M song song với (ABC)"]},
        ],
        "Gọi M là trung điểm của SA. Tính diện tích thiết diện của mặt phẳng qua M song song với (ABC).",
        "AUX_PARALLEL_PLANE_SECTION",
    )

    # ======================== GROUP D: 7 Negative / Degenerate / Contradictory / Unsupported ========================
    add_case(
        "D01_missing_height_precondition",
        "Group_D",
        "Negative_MissingDimension",
        (
            "Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, AB = a, SA vuông góc với (ABC).",
            {"solid_name": "S.ABC", "solid_type": "pyramid", "apex": "S", "base_vertices": ["A", "B", "C"], "quote": "Cho hình chóp S.ABC"},
            [
                {"id": "p1", "role": "premise", "kind": "right_angle", "at": "B", "points": ["A", "C"], "quotes": ["đáy ABC là tam giác vuông cân tại B"]},
                {"id": "p2", "role": "premise", "kind": "equal_lengths", "points_a": ["B", "A"], "points_b": ["B", "C"], "quotes": ["đáy ABC là tam giác vuông cân tại B"]},
                {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "p4", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
            ],
        ),
        [],
        GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"),
        "MISSING_PRECONDITION",
        None,
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["S", "B", "C"], "quotes": ["Tính khoảng cách từ A đến (SBC)"]}],
        "Tính khoảng cách từ A đến (SBC).",
        "REFUSAL_MISSING_PRECONDITION",
    )
    add_case(
        "D02_degenerate_coincident_points",
        "Group_D",
        "Negative_CoincidentPoints",
        _pyramid_right_B("a"),
        [PendingConstruction("pend_seg", "op.connect_segment", "seg_AA", {"a": "A", "b": "A"}, description="Đoạn AA trùng điểm")],
        GoalSpec("segment_length", {"a": "A", "b": "A"}, "a"),
        "CONTRADICTORY_CONSTRAINTS",
        None,
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "A"], "quotes": ["Tính AA"]}],
        "Tính AA.",
        "REFUSAL_DEGENERATE_COINCIDENT",
    )
    add_case(
        "D03_degenerate_collinear_plane",
        "Group_D",
        "Negative_CollinearPlane",
        _pyramid_right_B("a"),
        [
            PendingConstruction("pend_M", "op.midpoint_segment", "M", {"a": "A", "b": "B"}, description="M trung điểm AB"),
            PendingConstruction("pend_pl", "op.plane_through_three_points", "pl_AMB", {"a": "A", "b": "M", "c": "B"}, description="Mặt phẳng (AMB) thẳng hàng"),
        ],
        GoalSpec("distance_point_plane", {"point": "S", "plane": "pl_AMB"}, "a"),
        "CONTRADICTORY_CONSTRAINTS",
        None,
        [
            {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M", "points": ["A", "B"], "quotes": ["M trung điểm AB"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["S"], "points_b": ["A", "M", "B"], "quotes": ["Tính khoảng cách từ S đến (AMB)"]},
        ],
        "M trung điểm AB. Tính khoảng cách từ S đến (AMB).",
        "REFUSAL_DEGENERATE_COLLINEAR",
    )
    add_case(
        "D04_degenerate_parallel_no_intersection",
        "Group_D",
        "Negative_ParallelNoIntersection",
        _pyramid_square("a"),
        [
            PendingConstruction("pend_I", "op.intersect_line_plane", "I", {"line": ["A", "B"], "plane": "mat_SCD"}, description="Giao điểm AB và (SCD)"),
        ],
        GoalSpec("construct_point", {"target_object_id": "I"}, "a"),
        "CONTRADICTORY_CONSTRAINTS",
        None,
        [
            {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "intersect_line_plane", "point": "I", "points_a": ["A", "B"], "points_b": ["S", "C", "D"], "quotes": ["Giao điểm AB và (SCD)"]},
            {"id": "q1", "kind": "question", "role": "question", "quantity": "length", "points": ["A", "I"], "quotes": ["Tính AI"]},
        ],
        "Giao điểm AB và (SCD). Tính AI.",
        "REFUSAL_PARALLEL_NO_INTERSECTION",
    )
    add_case(
        "D05_contradictory_triangle_inequality",
        "Group_D",
        "Negative_ContradictoryTriangle",
        (
            "Cho hình chóp S.ABC có AB = a, BC = a, AC = 5a, SA vuông góc với (ABC), SA = a.",
            {"solid_name": "S.ABC", "solid_type": "pyramid", "apex": "S", "base_vertices": ["A", "B", "C"], "quote": "Cho hình chóp S.ABC"},
            [
                {"id": "p1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["B", "C"], "value": "a", "quotes": ["BC = a"]},
                {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "C"], "value": "5a", "quotes": ["AC = 5a"]},
                {"id": "p4", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
                {"id": "p5", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]},
            ],
        ),
        [],
        GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"),
        "CONTRADICTORY_CONSTRAINTS",
        None,
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["S", "B", "C"], "quotes": ["Tính khoảng cách từ A đến (SBC)"]}],
        "Tính khoảng cách từ A đến (SBC).",
        "REFUSAL_CONTRADICTORY_DATA",
    )
    add_case(
        "D06_unsupported_curved_tangent_sphere",
        "Group_D",
        "Negative_UnsupportedNewPrimitive_CaseC",
        _pyramid_right_B("a"),
        [],
        GoalSpec("unsupported_goal", {"reason": "Circumscribed tangent sphere locus construction is outside affine polyhedral operator inventory (Case C)."}, "a"),
        "UNSUPPORTED_OPERATOR",
        None,
        [{"id": "q1", "kind": "unsupported", "role": "question", "reason": "mặt cầu tiếp xúc tổng quát", "quotes": ["Xác định tâm mặt cầu tiếp xúc"]}],
        "Xác định tâm mặt cầu tiếp xúc.",
        "CASE_C_UNSUPPORTED_PRIMITIVE",
    )
    add_case(
        "D07_missing_base_right_angle_underdetermined",
        "Group_D",
        "Negative_UnderdeterminedApex",
        (
            "Cho hình chóp S.ABC có AB = a, BC = a.",
            {"solid_name": "S.ABC", "solid_type": "pyramid", "apex": "S", "base_vertices": ["A", "B", "C"], "quote": "Cho hình chóp S.ABC"},
            [
                {"id": "p1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
                {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["B", "C"], "value": "a", "quotes": ["BC = a"]},
            ],
        ),
        [],
        GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C"]}, "a"),
        "MISSING_PRECONDITION",
        None,
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "volume", "solid": "S.ABC", "quotes": ["Tính thể tích khối chóp S.ABC"]}],
        "Tính thể tích khối chóp S.ABC.",
        "REFUSAL_UNDERDETERMINED",
    )

    # ======================== GROUP E: 5 Alternative Valid Plans ========================
    add_case(
        "E01_multiplan_d_A_SBC_equilateral",
        "Group_E",
        "MultiPlan_DirectVsSyntheticTwoStep_Equilateral",
        _pyramid_equilateral("a"),
        [],
        GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "a√21/7",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["S", "B", "C"], "quotes": ["Tính khoảng cách từ A đến (SBC)"]}],
        "Tính khoảng cách từ A đến (SBC).",
        "MULTI_PLAN_EQUILATERAL_ALTITUDE",
        min_expected_plans=2,
    )
    add_case(
        "E02_multiplan_d_A_SBC_right_B",
        "Group_E",
        "MultiPlan_DirectVsSyntheticTwoStep_RightB",
        _pyramid_right_B("a"),
        [],
        GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "a√2/2",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["S", "B", "C"], "quotes": ["Tính khoảng cách từ A đến (SBC)"]}],
        "Tính khoảng cách từ A đến (SBC).",
        "MULTI_PLAN_RIGHT_ALTITUDE",
        min_expected_plans=2,
    )
    add_case(
        "E03_multiplan_skew_d_SA_BC",
        "Group_E",
        "MultiPlan_Skew_CommonPerpVsParallelPlane",
        _pyramid_right_B("a"),
        [],
        GoalSpec("distance_skew_lines", {"line1": ["S", "A"], "line2": ["B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "a",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "distance", "points_a": ["S", "A"], "points_b": ["B", "C"], "quotes": ["Tính khoảng cách giữa SA và BC"]}],
        "Tính khoảng cách giữa SA và BC.",
        "MULTI_PLAN_SKEW_DISTANCE",
        min_expected_plans=2,
    )
    add_case(
        "E04_multiplan_skew_angle_cube_symmetric_anchors",
        "Group_E",
        "MultiPlan_SkewAngle_ParallelAtAVsParallelAtB",
        _cube_unit(),
        [],
        GoalSpec("angle_lines", {"line1": ["A", "B'"], "line2": ["B", "C'"]}, "a"),
        "GOAL_VERIFIED",
        "60°",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "angle", "points_a": ["A", "B'"], "points_b": ["B", "C'"], "quotes": ["Tính góc giữa AB' và BC'"]}],
        "Tính góc giữa AB' và BC'.",
        "MULTI_PLAN_SKEW_ANGLE",
        min_expected_plans=2,
    )
    add_case(
        "E05_multiplan_dihedral_linear_vs_synthetic",
        "Group_E",
        "MultiPlan_Dihedral_DirectLinearVsOrthPlane",
        _pyramid_equilateral("a"),
        [],
        GoalSpec("angle_plane_plane", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"]}, "a"),
        "GOAL_VERIFIED",
        "cos²=3/7",
        [{"id": "q1", "kind": "question", "role": "question", "quantity": "angle", "points_a": ["S", "B", "C"], "points_b": ["A", "B", "C"], "quotes": ["Tính góc giữa (SBC) và (ABC)"]}],
        "Tính góc giữa (SBC) và (ABC).",
        "MULTI_PLAN_DIHEDRAL",
        min_expected_plans=2,
    )

    return cases


def _run_baseline_a(case: dict[str, Any]) -> dict[str, Any]:
    """Run Baseline A (`Planner /26 -> Registry /33 -> Engine /24`) on the same Gold facts cleanly."""
    t0 = time.perf_counter()
    tracemalloc.start()
    try:
        kh = planner.lap_ke_hoach({"schema": "typed-facts/2", "facts": case["baseline_tf2_facts"]}, case["full_problem_text"])
        plan_dict = {"calls": kh.calls, "goals": [g["call"] for g in kh.goals], "negated": [n["call"] for n in kh.negated]}
        kq = engine.dung_tu_loi_goi(case["full_problem_text"], plan_dict, auxiliary=tuple(kh.auxiliary))
        resp = adapter4_route.build_adapter4_response(kq, case["full_problem_text"]) if kq.status == "SERVED" else {}
        scene = resp.get("envelope", {}).get("scene3d") or kq.scene3d or {}
        ans = str((kq.answers or {}).get("q1") or "")
        scene_pts = [o.get("id") for o in scene.get("objects", []) if o.get("type") == "point3"]
        base_pts = set(case["solid_spec"].get("base_vertices") or ()) | ({case["solid_spec"].get("apex")} - {None}) | set(case["solid_spec"].get("top_vertices") or ())
        has_aux = any(pid not in base_pts for pid in scene_pts)
        status = kq.status
        code = kq.code
        classification = kh.search_telemetry.get("classification") if hasattr(kh, "search_telemetry") else None
        oracle = case["independent_oracle"]
        math_ok = False
        if status == "SERVED" and oracle is not None:
            math_ok = bool(same_value_v2(ans, oracle))
        elif status != "SERVED" and case["expected_status"] != "GOAL_VERIFIED":
            math_ok = True
        dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return {
            "status": status,
            "code": code,
            "answer": ans or None,
            "math_or_refusal_correct": math_ok,
            "constructed_aux_witness_in_scene": has_aux,
            "planner_classification": classification,
            "calls": [c["fn"] for c in kh.calls],
            "elapsed_ms": dt_ms,
            "peak_memory_kib": round(peak / 1024.0, 2),
        }
    except Exception as exc:
        dt_ms = round((time.perf_counter() - t0) * 1000.0, 3)
        try:
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
        except Exception:
            peak = 0
        code = getattr(exc, "code", type(exc).__name__)
        return {
            "status": "REFUSED",
            "code": str(code),
            "answer": None,
            "math_or_refusal_correct": case["expected_status"] != "GOAL_VERIFIED",
            "constructed_aux_witness_in_scene": False,
            "planner_classification": None,
            "calls": [],
            "elapsed_ms": dt_ms,
            "peak_memory_kib": round(peak / 1024.0, 2),
        }


def _audit_novelty(case: dict[str, Any], best_ops: list[str], baseline_res: dict[str, Any]) -> dict[str, Any]:
    """Programmatic Novelty Audit (§11) classifying Case A vs Case B vs Case C truthfully."""
    if case["expected_status"] != "GOAL_VERIFIED":
        return {
            "novelty_class": "CASE_C_UNSUPPORTED_OR_NEGATIVE" if case["expected_status"] == "UNSUPPORTED_OPERATOR" else "NEGATIVE_REFUSAL_CASE",
            "operators_used": best_ops,
            "complete_sequence_predefined_recipe": False,
            "created_by": "FAIL_CLOSED_VERIFICATION",
            "equivalent_template_in_planner26": None,
            "kernel_primitives_newly_written": False,
            "visual_only_steps": 0,
        }

    # Check if exact Baseline A already has an official PlanningContract/rule producing ALL auxiliary objects & answer
    has_missing_contract_op = any(
        op_id in (
            "op.divide_segment_ratio",
            "op.point_reflection",
            "op.construct_dihedral_linear_angle",
            "op.common_perpendicular_skew_lines",
            "op.plane_through_line_parallel_line",
            "op.plane_through_point_parallel_plane",
            "op.line_parallel_through_point",
            "op.deduce_line_perp_plane_two_lines",
            "op.deduce_parallel_line_plane_transfer",
            "op.polyhedron_plane_section",
        )
        for op_id in best_ops
    )
    baseline_lacked_aux_witness = (not baseline_res["constructed_aux_witness_in_scene"]) and ("op.project_point_to_plane" in best_ops or "op.project_point_to_line" in best_ops)
    is_multi_step = len([x for x in best_ops if not x.startswith("goal.")]) >= 2
    if case["group"] == "Group_A" and not baseline_lacked_aux_witness and baseline_res["status"] == "SERVED" and not is_multi_step:
        novelty_cls = "CASE_A_PREDEFINED_OR_PARITY"
        created_by = "PARITY_WITH_WITNESS_GRAPH"
        equiv = f"Planner/26:{baseline_res.get('planner_classification')}"
    elif has_missing_contract_op or baseline_lacked_aux_witness or baseline_res["status"] != "SERVED" or is_multi_step:
        novelty_cls = "CASE_B_DYNAMIC_COMPOSITION"
        created_by = "DYNAMIC_SEARCH_COMPOSITION"
        equiv = None
    else:
        novelty_cls = "CASE_A_PREDEFINED_OR_PARITY"
        created_by = "PARITY_WITH_WITNESS_GRAPH"
        equiv = f"Planner/26:{baseline_res.get('planner_classification')}"

    return {
        "novelty_class": novelty_cls,
        "operators_used": best_ops,
        "complete_sequence_predefined_recipe": novelty_cls == "CASE_A_PREDEFINED_OR_PARITY",
        "created_by": created_by,
        "equivalent_template_in_planner26": equiv,
        "kernel_primitives_newly_written": False,
        "visual_only_steps": 0,
    }


def main() -> int:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    head_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()
    cases = build_benchmark_cases()
    dyn_planner = DynamicConstructionPlanner()
    budget = SearchBudget()

    manifest_rows = []
    results_rows = []
    novelty_rows = []
    perf_rows = []

    sample_e2e_scene3d: dict[str, Any] | None = None
    sample_e2e_proof_sha: str | None = None

    for c in cases:
        t_build0 = time.perf_counter()
        frame = build_initial_frame(
            case_id=c["case_id"],
            problem_text=c["problem_text"],
            solid_spec=c["solid_spec"],
            chart_premises=c["chart_premises"],
            pending_constructions=c["pending"],
            length_unit="a",
        )
        t_build_ms = round((time.perf_counter() - t_build0) * 1000.0, 3)

        # Manifest record with SHA-256 of input facts (independent of planner output!)
        in_payload = {
            "case_id": c["case_id"],
            "problem_text": c["full_problem_text"],
            "solid_spec": c["solid_spec"],
            "chart_premises": c["chart_premises"],
            "goal_spec": c["goal_spec"].to_dict(),
        }
        in_hash = hashlib.sha256(canonical_json_dumps(in_payload).encode("utf-8")).hexdigest()
        manifest_rows.append(
            {
                **in_payload,
                "input_facts_sha256": in_hash,
                "group": c["group"],
                "source_provenance": c["source_provenance"],
                "expected_status": c["expected_status"],
                "independent_oracle": c["independent_oracle"],
                "capability_label": c["capability_label"],
                "min_expected_plans": c["min_expected_plans"],
            }
        )

        # Run Baseline A
        base_res = _run_baseline_a(c)

        # Run Candidate B (ZERO oracle input!)
        res = dyn_planner.plan(frame=frame, goal_spec=c["goal_spec"], budget=budget)

        # Run Verification + Scene3D + Serialization timing on best plan
        t_ver0 = time.perf_counter()
        scene_ok = False
        ser_ms = 0.0
        best_ops: list[str] = []
        best_answer: str | None = None
        best_node_count = 0
        best_plan_len = 0
        oracle_match = False

        if res.best_plan is not None:
            bp = res.best_plan
            best_ops = [n.producing_operation_id for n in bp.proof_graph.nodes if n.producing_operation_id]
            best_answer = bp.answer
            best_node_count = len(bp.proof_graph.nodes)
            best_plan_len = len([n for n in bp.proof_graph.nodes if n.node_type in ("CONSTRUCTION", "DERIVED_RELATION")])
            scene = compile_proof_graph_to_scene3d(frame, bp.proof_graph, bp.presentation_graph)
            full_rep = verify_full_proof_and_scene(bp.proof_graph, frame.chart_metric, scene3d=scene)
            scene_ok = full_rep.passed
            t_ver_ms = round((time.perf_counter() - t_ver0) * 1000.0, 3)

            t_ser0 = time.perf_counter()
            pg_json = serialize_proof_graph(bp.proof_graph)
            sc_json = canonical_json_dumps(scene)
            ser_ms = round((time.perf_counter() - t_ser0) * 1000.0, 3)

            if c["independent_oracle"] is not None:
                oracle_match = bool(same_value_v2(best_answer, c["independent_oracle"]))
            if sample_e2e_scene3d is None and c["case_id"] == "C01_aux_foot_d_A_SBC_equilateral":
                sample_e2e_scene3d = scene
                sample_e2e_proof_sha = hashlib.sha256(pg_json.encode("utf-8")).hexdigest()
        else:
            t_ver_ms = round((time.perf_counter() - t_ver0) * 1000.0, 3)
            # Negative case check
            oracle_match = res.status == c["expected_status"]
            scene_ok = False

        passed = (
            res.status == c["expected_status"]
            and oracle_match
            and (True if c["expected_status"] != "GOAL_VERIFIED" else (scene_ok and len(res.plans) >= c["min_expected_plans"]))
        )

        novelty = _audit_novelty(c, best_ops, base_res)
        novelty_rows.append(
            {
                "case_id": c["case_id"],
                "group": c["group"],
                "candidate_status": res.status,
                "baseline_a_status": base_res["status"],
                "baseline_a_aux_witness": base_res["constructed_aux_witness_in_scene"],
                "plans_count": len(res.plans),
                **novelty,
            }
        )

        results_rows.append(
            {
                "case_id": c["case_id"],
                "group": c["group"],
                "expected_status": c["expected_status"],
                "independent_oracle": c["independent_oracle"],
                "passed": passed,
                "baseline_a": base_res,
                "candidate_b": {
                    "status": res.status,
                    "failure_code": res.failure_code,
                    "answer": best_answer,
                    "oracle_match": oracle_match,
                    "l0_l4_scene_verified": scene_ok,
                    "plans_count": len(res.plans),
                    "best_operators": best_ops,
                    "plans": [p.to_summary_dict() for p in res.plans],
                },
            }
        )

        perf_rows.append(
            {
                "case_id": c["case_id"],
                "group": c["group"],
                "graph_construction_ms": t_build_ms,
                "search_ms": res.telemetry["search_ms"],
                "exact_verification_ms": t_ver_ms,
                "serialization_ms": ser_ms,
                "expanded_states": res.telemetry["expanded_states"],
                "generated_candidates": res.telemetry["generated_candidates"],
                "pruned_states": res.telemetry["pruned_states"],
                "peak_memory_kib": res.telemetry["peak_memory_kib"],
                "graph_node_count": best_node_count,
                "final_plan_length": best_plan_len,
                "timeout_hit": res.telemetry["timeout_hit"],
                "baseline_a_ms": base_res["elapsed_ms"],
                "baseline_a_memory_kib": base_res["peak_memory_kib"],
            }
        )

    repro_meta = {
        "git_commit": head_commit,
        "run_id": RUN_ID,
        "candidate_identity": DYNAMIC_PLANNER_VERSION,
        "operator_inventory_version": CONSTRUCTION_OPERATOR_SCHEMA,
        "graph_schema_version": VERIFIED_CONSTRUCTION_GRAPH_SCHEMA,
        "exact_verifier_identity": EXACT_VERIFIER_VERSION,
        "search_algorithm": "bounded_best_first_dependency_aware_search",
        "search_budget": budget.to_dict(),
        "test_seed": 0,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    total = len(results_rows)
    total_pos = sum(1 for r in results_rows if r["expected_status"] == "GOAL_VERIFIED")
    total_neg = total - total_pos
    cand_pass = sum(1 for r in results_rows if r["passed"])
    cand_pos_pass = sum(1 for r in results_rows if r["passed"] and r["expected_status"] == "GOAL_VERIFIED")
    cand_neg_pass = sum(1 for r in results_rows if r["passed"] and r["expected_status"] != "GOAL_VERIFIED")
    base_correct = sum(1 for r in results_rows if r["baseline_a"]["math_or_refusal_correct"])
    base_pos_served = sum(1 for r in results_rows if r["expected_status"] == "GOAL_VERIFIED" and r["baseline_a"]["math_or_refusal_correct"])
    base_pos_with_aux = sum(1 for r in results_rows if r["expected_status"] == "GOAL_VERIFIED" and r["baseline_a"]["constructed_aux_witness_in_scene"])

    case_b_count = sum(1 for n in novelty_rows if n["novelty_class"] == "CASE_B_DYNAMIC_COMPOSITION" and n["candidate_status"] == "GOAL_VERIFIED")
    case_a_count = sum(1 for n in novelty_rows if n["novelty_class"] == "CASE_A_PREDEFINED_OR_PARITY" and n["candidate_status"] == "GOAL_VERIFIED")
    case_c_count = sum(1 for n in novelty_rows if n["novelty_class"] == "CASE_C_UNSUPPORTED_OR_NEGATIVE")

    manifest_doc = {"schema": "axo-gold-construction-benchmark-manifest/1", **repro_meta, "total_cases": total, "cases": manifest_rows}
    results_doc = {
        "schema": "axo-gold-construction-benchmark-results/1",
        **repro_meta,
        "summary": {
            "total_cases": total,
            "positive_cases": total_pos,
            "negative_or_unsupported_cases": total_neg,
            "candidate_b_passed_total": f"{cand_pass}/{total}",
            "candidate_b_positive_verified": f"{cand_pos_pass}/{total_pos}",
            "candidate_b_negative_refused_safely": f"{cand_neg_pass}/{total_neg}",
            "baseline_a_math_or_refusal_ok": f"{base_correct}/{total}",
            "baseline_a_positive_served": f"{base_pos_served}/{total_pos}",
            "baseline_a_positive_with_aux_witness": f"{base_pos_with_aux}/{total_pos}",
        },
        "cases": results_rows,
    }
    novelty_doc = {
        "schema": "axo-dynamic-composition-evaluation/1",
        **repro_meta,
        "summary": {
            "case_b_dynamic_composition_verified": case_b_count,
            "case_a_parity": case_a_count,
            "case_c_unsupported_or_negative": case_c_count,
            "multi_plan_cases_verified": sum(1 for r in results_rows if r["group"] == "Group_E" and r["passed"] and r["candidate_b"]["plans_count"] >= 2),
        },
        "cases": novelty_rows,
    }
    avg = lambda key: round(sum(x[key] for x in perf_rows) / len(perf_rows), 3)
    perf_doc = {
        "schema": "axo-construction-performance/1",
        **repro_meta,
        "summary": {
            "total_cases": len(perf_rows),
            "avg_graph_construction_ms": avg("graph_construction_ms"),
            "avg_search_ms": avg("search_ms"),
            "max_search_ms": max(x["search_ms"] for x in perf_rows),
            "avg_exact_verification_ms": avg("exact_verification_ms"),
            "avg_serialization_ms": avg("serialization_ms"),
            "avg_expanded_states": avg("expanded_states"),
            "max_expanded_states": max(x["expanded_states"] for x in perf_rows),
            "avg_generated_candidates": avg("generated_candidates"),
            "avg_pruned_states": avg("pruned_states"),
            "max_peak_memory_kib": max(x["peak_memory_kib"] for x in perf_rows),
            "avg_graph_node_count": avg("graph_node_count"),
            "avg_final_plan_length": avg("final_plan_length"),
            "search_timeout_rate": round(sum(1 for x in perf_rows if x["timeout_hit"]) / len(perf_rows), 4),
            "avg_baseline_a_ms": avg("baseline_a_ms"),
        },
        "cases": perf_rows,
    }

    (RUN_DIR / "GOLD_CONSTRUCTION_BENCHMARK_MANIFEST.json").write_text(canonical_json_dumps(manifest_doc), encoding="utf-8")
    (RUN_DIR / "GOLD_CONSTRUCTION_BENCHMARK_RESULTS.json").write_text(canonical_json_dumps(results_doc), encoding="utf-8")
    (RUN_DIR / "DYNAMIC_COMPOSITION_EVALUATION.json").write_text(canonical_json_dumps(novelty_doc), encoding="utf-8")
    (RUN_DIR / "CONSTRUCTION_PERFORMANCE.json").write_text(canonical_json_dumps(perf_doc), encoding="utf-8")
    sample_extra = RUN_DIR / "SAMPLE_E2E_SCENE3D_C01.json"
    if sample_extra.exists():
        sample_extra.unlink()

    print("BENCHMARK SUMMARY:", json.dumps(results_doc["summary"], ensure_ascii=False))
    print("NOVELTY SUMMARY:", json.dumps(novelty_doc["summary"], ensure_ascii=False))
    print("PERF SUMMARY:", json.dumps(perf_doc["summary"], ensure_ascii=False))
    for r in results_rows:
        if not r["passed"]:
            print("  FAILED CASE:", r["case_id"], "expected:", r["expected_status"], "got:", r["candidate_b"]["status"], r["candidate_b"]["failure_code"], "ans:", r["candidate_b"]["answer"], "oracle:", r["independent_oracle"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
