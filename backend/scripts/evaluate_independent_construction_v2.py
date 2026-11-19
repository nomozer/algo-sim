# -*- coding: utf-8 -*-
"""AXO CONSTRUCTION /2 — Single-Shot Independent Holdout & Search Stress Evaluation.

Strictly enforces `CANDIDATE_V2_FREEZE_SHA256` before evaluating the unseen holdout (`N=60`),
runs SINGLE-SHOT evaluation without tweaking `backend/experimental/construction_planner/`, and
benchmarks Search Stress & 9-Stage E2E latency (`Arm A2` vs `Arm C`).

Emits inside `docs/evaluation/geometry/runs/axo-construction-proof-integrity-independent-evaluation-controlled-integration/`:
  - INDEPENDENT_CONSTRUCTION_HOLDOUT_MANIFEST.json
  - INDEPENDENT_CONSTRUCTION_EVALUATION.json
  - SEARCH_STRESS_BENCHMARK.json
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai import function_route  # noqa: E402
from experimental.construction_planner import DYNAMIC_PLANNER_V2_VERSION  # noqa: E402
from experimental.construction_planner.construction_operators import GoalSpec  # noqa: E402
from experimental.construction_planner.construction_search import (  # noqa: E402
    DynamicConstructionPlanner,
    SearchBudget,
)
from experimental.construction_planner.construction_serializer import canonical_json_dumps  # noqa: E402
from experimental.construction_planner.construction_state import (  # noqa: E402
    PendingConstruction,
    build_initial_frame,
)
from experimental.construction_planner.construction_verifier import verify_full_proof_and_scene  # noqa: E402
from experimental.construction_planner.presentation_validator import (  # noqa: E402
    validate_multiplan_switching,
    validate_presentation_step_graph,
)
from experimental.construction_planner.scene3d_bridge import compile_proof_graph_to_scene3d  # noqa: E402
from experimental.construction_planner.verified_input_bridge import bridge_verified_facts_to_construction_input  # noqa: E402
from scripts.evaluate_axo_construction_v1 import (  # noqa: E402
    _pyramid_equilateral,
    _pyramid_right_B,
    _pyramid_square,
    same_value_v2,
)

V2_RUN_DIR = (
    REPO_ROOT
    / "docs"
    / "evaluation"
    / "geometry"
    / "runs"
    / "axo-construction-proof-integrity-independent-evaluation-controlled-integration"
)

CANDIDATE_V2_FREEZE_SHA256 = "26c9b505fc7796ed9ff6a5c9578701978e92b9c1d6726a8208916a9ea3dca60c"


def compute_candidate_freeze_sha256() -> tuple[str, dict[str, str]]:
    pkg_dir = BACKEND_DIR / "experimental" / "construction_planner"
    files = sorted(pkg_dir.glob("*.py"))
    h = hashlib.sha256()
    per_file: dict[str, str] = {}
    for p in files:
        raw = p.read_bytes().replace(b"\r\n", b"\n")
        per_file[p.name] = hashlib.sha256(raw).hexdigest()
        h.update(p.name.encode("utf-8") + b"\0" + raw + b"\0")
    return h.hexdigest(), per_file


# ---------------------------------------------------------------------------
# Unseen Solid Chart Factories (disjoint parameters from `/1` benchmark)
# ---------------------------------------------------------------------------

def _cuboid_122() -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = "Cho hình hộp chữ nhật ABCD.A'B'C'D' có AB = a, AD = 2a, AA' = 2a."
    solid = {
        "solid_name": "ABCD.A'B'C'D'",
        "solid_type": "prism",
        "right": True,
        "base_vertices": ["A", "B", "C", "D"],
        "top_vertices": ["A'", "B'", "C'", "D'"],
        "quote": "Cho hình hộp chữ nhật ABCD.A'B'C'D'",
    }
    prems = [
        {"id": "p1", "role": "premise", "kind": "polygon_shape", "shape": "rectangle", "points": ["A", "B", "C", "D"], "quotes": ["Cho hình hộp chữ nhật ABCD.A'B'C'D'"]},
        {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
        {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "D"], "value": "2a", "quotes": ["AD = 2a"]},
        {"id": "p4", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "A'"], "value": "2a", "quotes": ["AA' = 2a"]},
    ]
    return txt, solid, prems


def _regular_sq_pyramid(base_side: str, lat_edge: str) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = f"Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng {base_side}, cạnh bên bằng {lat_edge}."
    solid = {
        "solid_name": "S.ABCD",
        "solid_type": "pyramid",
        "regular": True,
        "apex": "S",
        "base_vertices": ["A", "B", "C", "D"],
        "quote": "Cho hình chóp tứ giác đều S.ABCD",
    }
    prems = [
        {"id": "p1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": base_side, "quotes": [f"cạnh đáy bằng {base_side}"]},
        {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": lat_edge, "quotes": [f"cạnh bên bằng {lat_edge}"]},
    ]
    return txt, solid, prems


def _regular_tri_pyramid(base_side: str, lat_edge: str) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = f"Cho hình chóp tam giác đều S.ABC có cạnh đáy bằng {base_side}, cạnh bên bằng {lat_edge}."
    solid = {
        "solid_name": "S.ABC",
        "solid_type": "pyramid",
        "regular": True,
        "apex": "S",
        "base_vertices": ["A", "B", "C"],
        "quote": "Cho hình chóp tam giác đều S.ABC",
    }
    prems = [
        {"id": "p1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": base_side, "quotes": [f"cạnh đáy bằng {base_side}"]},
        {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": lat_edge, "quotes": [f"cạnh bên bằng {lat_edge}"]},
    ]
    return txt, solid, prems


def _right_rect_pyramid(ab: str, ad: str, sa: str) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = f"Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật với AB = {ab}, AD = {ad}. Cạnh bên SA vuông góc với (ABCD) và SA = {sa}."
    solid = {
        "solid_name": "S.ABCD",
        "solid_type": "pyramid",
        "apex": "S",
        "base_vertices": ["A", "B", "C", "D"],
        "quote": "Cho hình chóp S.ABCD",
    }
    prems = [
        {"id": "p1", "role": "premise", "kind": "polygon_shape", "shape": "rectangle", "points": ["A", "B", "C", "D"], "quotes": ["đáy ABCD là hình chữ nhật"]},
        {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": ab, "quotes": [f"AB = {ab}"]},
        {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "D"], "value": ad, "quotes": [f"AD = {ad}"]},
        {"id": "p4", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["SA vuông góc với (ABCD)"]},
        {"id": "p5", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": sa, "quotes": [f"SA = {sa}"]},
    ]
    return txt, solid, prems


def _right_tri_122() -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = "Cho hình chóp S.ABC có đáy ABC là tam giác vuông tại B với AB = a, BC = 2a. Cạnh bên SA vuông góc với (ABC) và SA = 2a."
    solid = {
        "solid_name": "S.ABC",
        "solid_type": "pyramid",
        "apex": "S",
        "base_vertices": ["A", "B", "C"],
        "quote": "Cho hình chóp S.ABC",
    }
    prems = [
        {"id": "p1", "role": "premise", "kind": "right_angle", "at": "B", "points": ["A", "C"], "quotes": ["tam giác vuông tại B"]},
        {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]},
        {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["B", "C"], "value": "2a", "quotes": ["BC = 2a"]},
        {"id": "p4", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc với (ABC)"]},
        {"id": "p5", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": "2a", "quotes": ["SA = 2a"]},
    ]
    return txt, solid, prems


def _oblique_prism_eq_ah() -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    txt = "Cho hình lăng trụ ABC.A'B'C' có đáy ABC là tam giác đều cạnh a. Gọi H là trung điểm của BC, A'H vuông góc với (ABC) và A'H = a."
    solid = {
        "solid_name": "ABC.A'B'C'",
        "solid_type": "prism",
        "right": False,
        "base_vertices": ["A", "B", "C"],
        "top_vertices": ["A'", "B'", "C'"],
        "quote": "Cho hình lăng trụ ABC.A'B'C'",
    }
    prems = [
        {"id": "sh", "role": "premise", "kind": "polygon_shape", "shape": "equilateral_triangle", "points": ["A", "B", "C"], "quotes": ["đáy ABC là tam giác đều cạnh a"]},
        {"id": "l1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["đáy ABC là tam giác đều cạnh a"]},
        {"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "H", "points": ["B", "C"], "quotes": ["Gọi H là trung điểm của BC"]},
        {"id": "pp1", "role": "premise", "kind": "perpendicular", "points_a": ["A'", "H"], "points_b": ["A", "B", "C"], "quotes": ["A'H vuông góc với (ABC)"]},
        {"id": "l2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A'", "H"], "value": "a", "quotes": ["A'H = a"]},
    ]
    return txt, solid, prems


def build_independent_holdout_cases() -> list[dict[str, Any]]:
    """60 brand-new unseen holdout cases (`44` positive + `16` negative/degenerate/contradictory/unsupported)."""
    cases: list[dict[str, Any]] = []

    def add(
        cid: str,
        family: str,
        chart_tuple: tuple[str, dict[str, Any], list[dict[str, Any]]],
        pending: list[PendingConstruction],
        goal: GoalSpec,
        expected_status: str,
        oracle: str | None,
        *,
        q_text: str,
        extra_pending_tf2: list[dict[str, Any]] | None = None,
        q_tf2: dict[str, Any] | None = None,
        min_plans: int = 1,
        tags: tuple[str, ...] = (),
    ) -> None:
        base_txt, sol, prems = chart_tuple
        tf2_facts = [{"id": "s1", "kind": "solid", "role": "premise", "solid": sol["solid_name"], "solid_type": sol["solid_type"], **({"regular": True} if sol.get("regular") else {}), **({"right": sol["right"]} if "right" in sol else {}), "quotes": [sol["quote"]]}, *prems, *(extra_pending_tf2 or []), *( [q_tf2] if q_tf2 else [] )]
        cases.append({
            "case_id": cid,
            "family": family,
            "problem_text": base_txt,
            "full_problem_text": f"{base_txt} {q_text}",
            "solid_spec": sol,
            "chart_premises": prems,
            "pending": pending,
            "goal_spec": goal,
            "expected_status": expected_status,
            "independent_oracle": oracle,
            "baseline_tf2_facts": tf2_facts if q_tf2 else None,
            "min_expected_plans": min_plans,
            "tags": list(tags),
        })

    # ---------------- Family 1: Cuboid (1, 2, 2) [9 positives] ----------------
    add("H01_cuboid_space_diagonal_ac_prime", "Cuboid_122", _cuboid_122(), [], GoalSpec("segment_length", {"a": "A", "b": "C'"}, "a"), "GOAL_VERIFIED", "3a", q_text="Tính độ dài đoạn AC'", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "length", "points": ["A", "C'"], "quotes": ["Tính độ dài đoạn AC'"]})
    add("H02_cuboid_dist_A_A_prime_BD", "Cuboid_122", _cuboid_122(), [], GoalSpec("distance_point_plane", {"point": "A", "plane": ["A'", "B", "D"]}, "a"), "GOAL_VERIFIED", "a√6/3", q_text="Tính khoảng cách từ A đến (A'BD)", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["A'", "B", "D"], "quotes": ["Tính khoảng cách từ A đến (A'BD)"]})
    add("H03_cuboid_midpoint_dist_to_A_prime_BD", "Cuboid_122", _cuboid_122(), [PendingConstruction("p_m", "op.midpoint_segment", "M", {"a": "C'", "b": "D'"}, description="M trung điểm C'D'")], GoalSpec("distance_point_plane", {"point": "M", "plane": ["A'", "B", "D"]}, "a"), "GOAL_VERIFIED", "a√6/2", q_text="Gọi M là trung điểm C'D'. Tính khoảng cách từ M đến (A'BD)", extra_pending_tf2=[{"id": "pd1", "role": "premise", "kind": "point_def", "point_kind": "midpoint", "point": "M", "points": ["C'", "D'"], "quotes": ["Gọi M là trung điểm C'D'"]}], q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "distance", "points_a": ["M"], "points_b": ["A'", "B", "D"], "quotes": ["Tính khoảng cách từ M đến (A'BD)"]})
    add("H04_cuboid_skew_dist_A_prime_B_and_B_prime_C", "Cuboid_122", _cuboid_122(), [], GoalSpec("distance_skew_lines", {"line1": ["A'", "B"], "line2": ["B'", "C"]}, "a"), "GOAL_VERIFIED", "a√6/3", q_text="Tính khoảng cách giữa hai đường thẳng chéo nhau A'B và B'C", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "distance", "points_a": ["A'", "B"], "points_b": ["B'", "C"], "quotes": ["Tính khoảng cách giữa hai đường thẳng chéo nhau A'B và B'C"]}, min_plans=2, tags=("multi_plan",))
    add("H05_cuboid_angle_AC_prime_ABCD", "Cuboid_122", _cuboid_122(), [], GoalSpec("angle_line_plane", {"line": ["A", "C'"], "plane": ["A", "B", "C", "D"]}, "a"), "GOAL_VERIFIED", "cos²=5/9", q_text="Tính góc giữa AC' và (ABCD)", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "angle", "points_a": ["A", "C'"], "points_b": ["A", "B", "C", "D"], "quotes": ["Tính góc giữa AC' và (ABCD)"]})
    add("H06_cuboid_dihedral_A_prime_BD_and_ABCD", "Cuboid_122", _cuboid_122(), [], GoalSpec("angle_plane_plane", {"plane1": ["A'", "B", "D"], "plane2": ["A", "B", "C", "D"]}, "a"), "GOAL_VERIFIED", "cos²=1/6", q_text="Tính góc giữa hai mặt phẳng (A'BD) và (ABCD)", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "angle", "points_a": ["A'", "B", "D"], "points_b": ["A", "B", "C", "D"], "quotes": ["Tính góc giữa hai mặt phẳng (A'BD) và (ABCD)"]})
    add("H07_cuboid_section_area_ACC_prime", "Cuboid_122", _cuboid_122(), [], GoalSpec("section_area", {"plane": ["A", "C", "C'"]}, "a"), "GOAL_VERIFIED", "2√5a²", q_text="Tính diện tích thiết diện cắt bởi (ACC')", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "area", "solid": "ABCD.A'B'C'D'", "points": ["A", "C", "C'"], "quotes": ["Tính diện tích thiết diện cắt bởi (ACC')"]})
    add("H08_cuboid_sub_volume_B_prime_A_prime_BD", "Cuboid_122", _cuboid_122(), [], GoalSpec("solid_volume", {"apex": "B'", "base": ["A'", "B", "D"]}, "a"), "GOAL_VERIFIED", "2a³/3", q_text="Tính thể tích khối chóp B'.A'BD")
    add("H09_cuboid_dist_C_line_BD_prime", "Cuboid_122", _cuboid_122(), [], GoalSpec("distance_point_line", {"point": "C", "line": ["B", "D'"]}, "a"), "GOAL_VERIFIED", "2a√5/3", q_text="Tính khoảng cách từ C đến BD'", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "distance", "points_a": ["C"], "points_b": ["B", "D'"], "quotes": ["Tính khoảng cách từ C đến BD'"]})

    # ---------------- Family 2: Regular Square Pyramid (9 positives) ----------------
    add("H10_reg_sq_volume_edge_a", "RegSq_1_1", _regular_sq_pyramid("a", "a"), [], GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C", "D"]}, "a"), "GOAL_VERIFIED", "a³√2/6", q_text="Tính thể tích khối chóp S.ABCD", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "volume", "solid": "S.ABCD", "quotes": ["Tính thể tích khối chóp S.ABCD"]})
    add("H11_reg_sq_dist_A_SBC_edge_a", "RegSq_1_1", _regular_sq_pyramid("a", "a"), [], GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"), "GOAL_VERIFIED", "a√6/3", q_text="Tính khoảng cách từ A đến (SBC)", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["S", "B", "C"], "quotes": ["Tính khoảng cách từ A đến (SBC)"]})
    add("H12_reg_sq_dihedral_SBC_ABCD_edge_a", "RegSq_1_1", _regular_sq_pyramid("a", "a"), [], GoalSpec("angle_plane_plane", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C", "D"]}, "a"), "GOAL_VERIFIED", "cos²=1/3", q_text="Tính góc giữa hai mặt phẳng (SBC) và (ABCD)", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "angle", "points_a": ["S", "B", "C"], "points_b": ["A", "B", "C", "D"], "quotes": ["Tính góc giữa hai mặt phẳng (SBC) và (ABCD)"]})
    add("H13_reg_sq_skew_SA_BC_multiplan", "RegSq_1_1", _regular_sq_pyramid("a", "a"), [], GoalSpec("distance_skew_lines", {"line1": ["S", "A"], "line2": ["B", "C"]}, "a"), "GOAL_VERIFIED", "a√6/3", q_text="Tính khoảng cách giữa SA và BC", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "distance", "points_a": ["S", "A"], "points_b": ["B", "C"], "quotes": ["Tính khoảng cách giữa SA và BC"]}, min_plans=2, tags=("multi_plan",))
    add("H14_reg_sq_midpoints_MN_length", "RegSq_1_1", _regular_sq_pyramid("a", "a"), [PendingConstruction("p_m", "op.midpoint_segment", "M", {"a": "S", "b": "C"}), PendingConstruction("p_n", "op.midpoint_segment", "N", {"a": "A", "b": "D"})], GoalSpec("segment_length", {"a": "M", "b": "N"}, "a"), "GOAL_VERIFIED", "a√3/2", q_text="Gọi M là trung điểm SC, N là trung điểm AD. Tính MN")
    add("H15_reg_sq_divide_SK_third_dist_ABCD", "RegSq_1_1", _regular_sq_pyramid("a", "a"), [PendingConstruction("p_k", "op.divide_segment_ratio", "K", {"a": "S", "b": "A"}, {"ratio": "1/3"})], GoalSpec("distance_point_plane", {"point": "K", "plane": ["A", "B", "C", "D"]}, "a"), "GOAL_VERIFIED", "a√2/3", q_text="K thuộc SA với SK = 1/3 SA. Tính khoảng cách từ K đến (ABCD)")
    add("H16_reg_sq_1_2_angle_SA_ABCD", "RegSq_1_2", _regular_sq_pyramid("a", "2a"), [], GoalSpec("angle_line_plane", {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "a"), "GOAL_VERIFIED", "cos²=1/8", q_text="Tính góc giữa SA và (ABCD)", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "angle", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["Tính góc giữa SA và (ABCD)"]})
    add("H17_reg_sq_1_2_dist_O_to_SD", "RegSq_1_2", _regular_sq_pyramid("a", "2a"), [PendingConstruction("p_o", "op.midpoint_segment", "O_ac", {"a": "A", "b": "C"})], GoalSpec("distance_point_line", {"point": "O_ac", "line": ["S", "D"]}, "a"), "GOAL_VERIFIED", "a√7/4", q_text="Tính khoảng cách từ tâm đáy đến SD")
    add("H18_reg_sq_angle_SA_BC_skew", "RegSq_1_1", _regular_sq_pyramid("a", "a"), [], GoalSpec("angle_lines", {"line1": ["S", "A"], "line2": ["B", "C"]}, "a"), "GOAL_VERIFIED", "60°", q_text="Tính góc giữa SA và BC", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "angle", "points_a": ["S", "A"], "points_b": ["B", "C"], "quotes": ["Tính góc giữa SA và BC"]})

    # ---------------- Family 3: Regular Triangular Pyramid / Tetrahedron (6 positives) ----------------
    add("H19_reg_tet_skew_SA_BC", "RegTri_1_1", _regular_tri_pyramid("a", "a"), [], GoalSpec("distance_skew_lines", {"line1": ["S", "A"], "line2": ["B", "C"]}, "a"), "GOAL_VERIFIED", "a√2/2", q_text="Tính khoảng cách giữa SA và BC", min_plans=2, tags=("multi_plan",))
    add("H20_reg_tet_dist_A_SBC", "RegTri_1_1", _regular_tri_pyramid("a", "a"), [], GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"), "GOAL_VERIFIED", "a√6/3", q_text="Tính khoảng cách từ A đến (SBC)", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "distance", "points_a": ["A"], "points_b": ["S", "B", "C"], "quotes": ["Tính khoảng cách từ A đến (SBC)"]})
    add("H21_reg_tet_dihedral_SBC_ABC", "RegTri_1_1", _regular_tri_pyramid("a", "a"), [], GoalSpec("angle_plane_plane", {"plane1": ["S", "B", "C"], "plane2": ["A", "B", "C"]}, "a"), "GOAL_VERIFIED", "cos²=1/9", q_text="Tính góc giữa (SBC) và (ABC)", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "angle", "points_a": ["S", "B", "C"], "points_b": ["A", "B", "C"], "quotes": ["Tính góc giữa (SBC) và (ABC)"]})
    # Reg tri 1_2: base a, SA = 2a -> R_circ = a√3/3, h^2 = 4 - 1/3 = 11/3, h = √33/3, V = (1/3)(√3/4)(√33/3) = √99/36 = √11/12
    add("H22_reg_tri_1_2_volume", "RegTri_1_2", _regular_tri_pyramid("a", "2a"), [], GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C"]}, "a"), "GOAL_VERIFIED", "a³√11/12", q_text="Tính thể tích khối chóp S.ABC", q_tf2={"id": "q1", "role": "question", "kind": "question", "quantity": "volume", "solid": "S.ABC", "quotes": ["Tính thể tích khối chóp S.ABC"]})
    # Reg tri 1_2: M=mid(S,A), N=mid(B,C) -> MN median between midpoints:
    # By vector identity on tetrahedron with SA=SB=SC=2, AB=BC=CA=1:
    # 4 MN^2 = SA'^2? Wait M=(S+A)/2, N=(B+C)/2 => 4|MN|^2 = |S+A-B-C|^2. Better: use regular tetrahedron 1_1: |S+A-B-C|^2 = (1+1+1+1)... opposite edges SA, BC are perp & equal a => MN = a√2/2! Check: SA^2+BC^2 = AB^2+AC^2+SB^2+SC^2? No, sum of squares of 4 sides - (2 diag)^2? Specifically MN = d(SA, BC) = a√2/2!
    add("H23_reg_tet_bimedian_MN", "RegTri_1_1", _regular_tri_pyramid("a", "a"), [PendingConstruction("p_m", "op.midpoint_segment", "M", {"a": "S", "b": "A"}), PendingConstruction("p_n", "op.midpoint_segment", "N", {"a": "B", "b": "C"})], GoalSpec("segment_length", {"a": "M", "b": "N"}, "a"), "GOAL_VERIFIED", "a√2/2", q_text="Tính độ dài đoạn nối trung điểm SA và BC")
    # Centroid G of S.BC and midpoint M of AB in RegTet_1_1:
    # A=(0,0,0), B=(1,0,0), C=(1/2, √3/2, 0), S=(1/2, √3/6, √(2/3))
    # G = (S+B+C)/3 = (2/3, 2√3/9, √6/9), M = (1/2, 0, 0)
    # GM = (1/6, 2√3/9, √6/9), |GM|^2 = 1/36 + 12/81 + 6/81 = 1/36 + 2/9 = 9/36 = 1/4 => GM = a/2!!
    add("H24_reg_tet_centroid_to_midpoint", "RegTri_1_1", _regular_tri_pyramid("a", "a"), [PendingConstruction("p_g", "op.triangle_centroid", "G", {"a": "S", "b": "B", "c": "C"}), PendingConstruction("p_m", "op.midpoint_segment", "M", {"a": "A", "b": "B"})], GoalSpec("segment_length", {"a": "G", "b": "M"}, "a"), "GOAL_VERIFIED", "a/2", q_text="Gọi G là trọng tâm tam giác SBC, M là trung điểm AB. Tính GM")

    # ---------------- Family 4: Asymmetric Right Rectangular Pyramid (6 positives) ----------------
    add("H25_right_rect_dist_A_SBD", "RightRect_1_2_2", _right_rect_pyramid("a", "2a", "2a"), [], GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "D"]}, "a"), "GOAL_VERIFIED", "a√6/3", q_text="Tính khoảng cách từ A đến (SBD)", min_plans=2, tags=("multi_plan",))
    add("H26_right_rect_mid_SC_to_SBD", "RightRect_1_2_2", _right_rect_pyramid("a", "2a", "2a"), [PendingConstruction("p_m", "op.midpoint_segment", "M", {"a": "S", "b": "C"})], GoalSpec("distance_point_plane", {"point": "M", "plane": ["S", "B", "D"]}, "a"), "GOAL_VERIFIED", "a√6/6", q_text="M là trung điểm SC. Tính khoảng cách từ M đến (SBD)")
    add("H27_right_rect_dist_D_SBC_parallel_transfer", "RightRect_1_2_2", _right_rect_pyramid("a", "2a", "2a"), [], GoalSpec("distance_point_plane", {"point": "D", "plane": ["S", "B", "C"]}, "a"), "GOAL_VERIFIED", "2a√5/5", q_text="Tính khoảng cách từ D đến (SBC)")
    add("H28_right_rect_skew_SA_BD", "RightRect_1_2_2", _right_rect_pyramid("a", "2a", "2a"), [], GoalSpec("distance_skew_lines", {"line1": ["S", "A"], "line2": ["B", "D"]}, "a"), "GOAL_VERIFIED", "2a√5/5", q_text="Tính khoảng cách giữa SA và BD", min_plans=2, tags=("multi_plan",))
    add("H29_right_rect_angle_SC_ABCD", "RightRect_1_2_2", _right_rect_pyramid("a", "2a", "2a"), [], GoalSpec("angle_line_plane", {"line": ["S", "C"], "plane": ["A", "B", "C", "D"]}, "a"), "GOAL_VERIFIED", "cos²=5/9", q_text="Tính góc giữa SC và (ABCD)")
    add("H30_right_rect_divide_quarter_midpoint_KN", "RightRect_1_2_2", _right_rect_pyramid("a", "2a", "2a"), [PendingConstruction("p_k", "op.divide_segment_ratio", "K", {"a": "S", "b": "B"}, {"ratio": "1/4"}), PendingConstruction("p_n", "op.midpoint_segment", "N", {"a": "C", "b": "D"})], GoalSpec("segment_length", {"a": "K", "b": "N"}, "a"), "GOAL_VERIFIED", "a√101/4", q_text="K thuộc SB với SK = 1/4 SB, N là trung điểm CD. Tính KN")

    # ---------------- Family 5: Oblique Prism Non-Diagonal Gram (6 positives) ----------------
    add("H31_oblique_prism_volume_A_prime_ABC", "ObliquePrism_Gram", _oblique_prism_eq_ah(), [], GoalSpec("solid_volume", {"apex": "A'", "base": ["A", "B", "C"]}, "a"), "GOAL_VERIFIED", "a³√3/12", q_text="Tính thể tích khối chóp A'.ABC")
    add("H32_oblique_prism_AA_prime_length", "ObliquePrism_Gram", _oblique_prism_eq_ah(), [], GoalSpec("segment_length", {"a": "A", "b": "A'"}, "a"), "GOAL_VERIFIED", "a√7/2", q_text="Tính độ dài cạnh bên AA'")
    add("H33_oblique_prism_angle_AA_prime_ABC", "ObliquePrism_Gram", _oblique_prism_eq_ah(), [], GoalSpec("angle_line_plane", {"line": ["A", "A'"], "plane": ["A", "B", "C"]}, "a"), "GOAL_VERIFIED", "cos²=3/7", q_text="Tính góc giữa cạnh bên AA' và (ABC)")
    add("H34_oblique_prism_dist_A_to_BCC_prime_B_prime", "ObliquePrism_Gram", _oblique_prism_eq_ah(), [], GoalSpec("distance_point_plane", {"point": "A", "plane": ["B", "C", "C'"]}, "a"), "GOAL_VERIFIED", "a√21/7", q_text="Tính khoảng cách từ A đến (BCC'B')")
    add("H35_oblique_prism_midpoint_MN_length", "ObliquePrism_Gram", _oblique_prism_eq_ah(), [PendingConstruction("p_m", "op.midpoint_segment", "M", {"a": "A'", "b": "B'"}), PendingConstruction("p_n", "op.midpoint_segment", "N", {"a": "A", "b": "C"})], GoalSpec("segment_length", {"a": "M", "b": "N"}, "a"), "GOAL_VERIFIED", "a√2", q_text="M là trung điểm A'B', N là trung điểm AC. Tính MN")
    add("H36_oblique_prism_perp_dihedral_A_prime_BC_ABC_90deg", "ObliquePrism_Gram", _oblique_prism_eq_ah(), [], GoalSpec("angle_plane_plane", {"plane1": ["A'", "B", "C"], "plane2": ["A", "B", "C"]}, "a"), "GOAL_VERIFIED", "90°", q_text="Tính góc giữa (A'BC) và (ABC)", tags=("boundary_90deg",))

    # ---------------- Family 6: Asymmetric Right Triangle / Long Chain / Boundary / Near-Degenerate (8 positives) ----------------
    add("H37_right_tri_122_dist_A_SBC", "RightTri_1_2_2", _right_tri_122(), [], GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"), "GOAL_VERIFIED", "2a√5/5", q_text="Tính khoảng cách từ A đến (SBC)")
    add("H38_right_tri_122_skew_BC_SA", "RightTri_1_2_2", _right_tri_122(), [], GoalSpec("distance_skew_lines", {"line1": ["B", "C"], "line2": ["S", "A"]}, "a"), "GOAL_VERIFIED", "a", q_text="Tính khoảng cách giữa BC và SA")
    add("H39_right_tri_122_boundary_angle_BC_SAB_90deg", "RightTri_1_2_2", _right_tri_122(), [], GoalSpec("angle_line_plane", {"line": ["B", "C"], "plane": ["S", "A", "B"]}, "a"), "GOAL_VERIFIED", "90°", q_text="Tính góc giữa BC và (SAB)", tags=("boundary_90deg",))
    add("H40_right_tri_122_boundary_angle_mid_line_0deg", "RightTri_1_2_2", _right_tri_122(), [PendingConstruction("p_m", "op.midpoint_segment", "M", {"a": "S", "b": "A"}), PendingConstruction("p_n", "op.midpoint_segment", "N", {"a": "S", "b": "B"})], GoalSpec("angle_line_plane", {"line": ["M", "N"], "plane": ["A", "B", "C"]}, "a"), "GOAL_VERIFIED", "0°", q_text="Tính góc giữa đường thẳng MN và (ABC)", tags=("boundary_0deg",))
    add("H41_near_degenerate_divide_1_20", "RightTri_1_2_2", _right_tri_122(), [PendingConstruction("p_k", "op.divide_segment_ratio", "K", {"a": "A", "b": "B"}, {"ratio": "1/20"})], GoalSpec("segment_length", {"a": "S", "b": "K"}, "a"), "GOAL_VERIFIED", "a√1601/20", q_text="K thuộc AB sao cho AK = 1/20 AB. Tính SK", tags=("near_degenerate_fraction",))
    add("H42_near_degenerate_divide_19_20_dist_plane", "RightTri_1_2_2", _right_tri_122(), [PendingConstruction("p_k", "op.divide_segment_ratio", "K", {"a": "S", "b": "A"}, {"ratio": "1/20"})], GoalSpec("distance_point_plane", {"point": "K", "plane": ["A", "B", "C"]}, "a"), "GOAL_VERIFIED", "19a/10", q_text="K thuộc SA sao cho SK = 1/20 SA. Tính khoảng cách từ K đến (ABC)", tags=("near_degenerate_fraction",))
    add(
        "H43_long_chain_cuboid_7step_dist",
        "Cuboid_122",
        _cuboid_122(),
        [
            PendingConstruction("c1", "op.midpoint_segment", "M", {"a": "A", "b": "B"}),
            PendingConstruction("c2", "op.midpoint_segment", "N", {"a": "C", "b": "D"}),
            PendingConstruction("c3", "op.midpoint_segment", "P", {"a": "A'", "b": "D'"}),
            PendingConstruction("c4", "op.midpoint_segment", "Q", {"a": "B'", "b": "C'"}),
            PendingConstruction("c5", "op.divide_segment_ratio", "K", {"a": "M", "b": "N"}, {"ratio": "1/4"}),
            PendingConstruction("c6", "op.divide_segment_ratio", "L", {"a": "P", "b": "Q"}, {"ratio": "2/3"}),
            PendingConstruction("c7", "op.midpoint_segment", "R", {"a": "K", "b": "L"}),
        ],
        GoalSpec("distance_point_plane", {"point": "R", "plane": ["A'", "B", "D"]}, "a"),
        "GOAL_VERIFIED",
        "11a√6/72",
        q_text="Dựng dãy trung điểm M, N, P, Q, chia K, L và trung điểm R. Tính d(R, (A'BD))",
        tags=("long_chain",),
    )
    add(
        "H44_coincident_point_distance_diag_intersections",
        "Cuboid_122",
        _cuboid_122(),
        [PendingConstruction("p1", "op.midpoint_segment", "O1", {"a": "A", "b": "C"}), PendingConstruction("p2", "op.midpoint_segment", "O2", {"a": "B", "b": "D"})],
        GoalSpec("point_distance", {"a": "O1", "b": "O2"}, "a"),
        "GOAL_VERIFIED",
        "0",
        q_text="O1 là trung điểm AC, O2 là trung điểm BD. Tính khoảng cách giữa O1 và O2",
        tags=("coincident_point_distance",),
    )

    # ---------------- 16 Negative / Degenerate / Contradictory / Unsupported Cases ----------------
    # 4 MISSING_PRECONDITION
    add("HN01_missing_pyramid_height", "Negative_Missing", ("Cho hình chóp S.ABC có đáy ABC là tam giác vuông cân tại B, AB = a.", {"solid_name": "S.ABC", "solid_type": "pyramid", "quote": "Cho hình chóp S.ABC"}, [{"id": "p1", "role": "premise", "kind": "right_angle", "at": "B", "points": ["A", "C"], "quotes": ["tam giác vuông cân tại B"]}, {"id": "p2", "role": "premise", "kind": "equal_lengths", "points_a": ["B", "A"], "points_b": ["B", "C"], "quotes": ["tam giác vuông cân tại B"]}, {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]}]), [], GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C"]}, "a"), "MISSING_PRECONDITION", None, q_text="Tính V(S.ABC)")
    add("HN02_missing_right_rect_sa_length", "Negative_Missing", ("Cho hình chóp S.ABCD có đáy ABCD là hình chữ nhật AB = a, AD = 2a, SA vuông góc với (ABCD).", {"solid_name": "S.ABCD", "solid_type": "pyramid", "quote": "Cho hình chóp S.ABCD"}, [{"id": "p1", "role": "premise", "kind": "polygon_shape", "shape": "rectangle", "points": ["A", "B", "C", "D"], "quotes": ["ABCD là hình chữ nhật"]}, {"id": "p2", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]}, {"id": "p3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "D"], "value": "2a", "quotes": ["AD = 2a"]}, {"id": "p4", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"], "quotes": ["SA vuông góc với (ABCD)"]}]), [], GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "D"]}, "a"), "MISSING_PRECONDITION", None, q_text="Tính d(A, (SBD))")
    add("HN03_missing_reg_sq_lateral_edge", "Negative_Missing", ("Cho hình chóp tứ giác đều S.ABCD có cạnh đáy bằng a.", {"solid_name": "S.ABCD", "solid_type": "pyramid", "regular": True, "quote": "Cho hình chóp tứ giác đều S.ABCD"}, [{"id": "p1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["cạnh đáy bằng a"]}]), [], GoalSpec("distance_point_plane", {"point": "A", "plane": ["S", "B", "C"]}, "a"), "MISSING_PRECONDITION", None, q_text="Tính d(A, (SBC))")
    add("HN04_unknown_undeclared_point_goal", "Negative_Missing", _cuboid_122(), [], GoalSpec("segment_length", {"a": "S", "b": "Z_MISSING"}, "a"), "MISSING_PRECONDITION", None, q_text="Tính độ dài Z_MISSING")

    # 4 DEGENERATE_CONSTRUCTION
    add("HN05_degenerate_coincident_segment_construction", "Negative_Degenerate", _cuboid_122(), [PendingConstruction("p1", "op.midpoint_segment", "O1", {"a": "A", "b": "C"}), PendingConstruction("p2", "op.midpoint_segment", "O2", {"a": "B", "b": "D"})], GoalSpec("segment_length", {"a": "O1", "b": "O2"}, "a"), "DEGENERATE_CONSTRUCTION", None, q_text="Dựng đoạn thẳng nối O1 và O2")
    add("HN06_degenerate_collinear_three_points_plane", "Negative_Degenerate", _cuboid_122(), [PendingConstruction("p1", "op.midpoint_segment", "M", {"a": "A", "b": "B"})], GoalSpec("distance_point_plane", {"point": "S", "plane": ["A", "M", "B"]}, "a"), "DEGENERATE_CONSTRUCTION", None, q_text="Dựng mặt phẳng qua ba điểm thẳng hàng A, M, B")
    add("HN07_degenerate_parallel_lines_intersect", "Negative_Degenerate", _cuboid_122(), [PendingConstruction("p1", "op.intersect_coplanar_lines", "I", {"line1": "ln_A_B", "line2": "ln_C_D"})], GoalSpec("construct_point", {"target_object_id": "I"}, "a"), "DEGENERATE_CONSTRUCTION", None, q_text="Tìm giao điểm AB và CD song song")
    add("HN08_degenerate_line_parallel_plane_intersect", "Negative_Degenerate", _cuboid_122(), [PendingConstruction("p1", "op.intersect_line_plane", "I", {"line": "ln_A'_B'", "plane": "day_ABCD"})], GoalSpec("construct_point", {"target_object_id": "I"}, "a"), "DEGENERATE_CONSTRUCTION", None, q_text="Tìm giao điểm A'B' và (ABCD)")

    # 4 CONTRADICTORY_CONSTRAINTS
    add("HN09_contradictory_reg_sq_slant_too_short", "Negative_Contradictory", _regular_sq_pyramid("2a", "a"), [], GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C", "D"]}, "a"), "CONTRADICTORY_CONSTRAINTS", None, q_text="Tính V(S.ABCD)")
    add("HN10_contradictory_triangle_ineq", "Negative_Contradictory", ("Cho hình chóp S.ABC có AB = a, BC = 2a, AC = 5a, SA vuông góc (ABC), SA = a.", {"solid_name": "S.ABC", "solid_type": "pyramid", "quote": "Cho hình chóp S.ABC"}, [{"id": "l1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]}, {"id": "l2", "role": "premise", "kind": "length", "measure": "segment", "points": ["B", "C"], "value": "2a", "quotes": ["BC = 2a"]}, {"id": "l3", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "C"], "value": "5a", "quotes": ["AC = 5a"]}, {"id": "pp", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc (ABC)"]}, {"id": "l4", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]}]), [], GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C"]}, "a"), "CONTRADICTORY_CONSTRAINTS", None, q_text="Tính V(S.ABC)")
    add("HN11_contradictory_conflicting_edge", "Negative_Contradictory", ("Cho hình chóp S.ABC có đáy tam giác vuông cân tại B, AB = a, BC = 3a, SA vuông góc (ABC), SA = a.", {"solid_name": "S.ABC", "solid_type": "pyramid", "quote": "Cho hình chóp S.ABC"}, [{"id": "p1", "role": "premise", "kind": "right_angle", "at": "B", "points": ["A", "C"], "quotes": ["tam giác vuông cân tại B"]}, {"id": "p2", "role": "premise", "kind": "equal_lengths", "points_a": ["B", "A"], "points_b": ["B", "C"], "quotes": ["tam giác vuông cân tại B"]}, {"id": "l1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]}, {"id": "l2", "role": "premise", "kind": "length", "measure": "segment", "points": ["B", "C"], "value": "3a", "quotes": ["BC = 3a"]}, {"id": "pp", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc (ABC)"]}, {"id": "l3", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": "a", "quotes": ["SA = a"]}]), [], GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C"]}, "a"), "CONTRADICTORY_CONSTRAINTS", None, q_text="Tính V(S.ABC)")
    add("HN12_contradictory_zero_edge", "Negative_Contradictory", ("Cho hình chóp S.ABC có đáy tam giác vuông cân tại B, AB = a, SA vuông góc (ABC), SA = 0.", {"solid_name": "S.ABC", "solid_type": "pyramid", "quote": "Cho hình chóp S.ABC"}, [{"id": "p1", "role": "premise", "kind": "right_angle", "at": "B", "points": ["A", "C"], "quotes": ["tam giác vuông cân tại B"]}, {"id": "p2", "role": "premise", "kind": "equal_lengths", "points_a": ["B", "A"], "points_b": ["B", "C"], "quotes": ["tam giác vuông cân tại B"]}, {"id": "l1", "role": "premise", "kind": "length", "measure": "segment", "points": ["A", "B"], "value": "a", "quotes": ["AB = a"]}, {"id": "pp", "role": "premise", "kind": "perpendicular", "points_a": ["S", "A"], "points_b": ["A", "B", "C"], "quotes": ["SA vuông góc (ABC)"]}, {"id": "l3", "role": "premise", "kind": "length", "measure": "segment", "points": ["S", "A"], "value": "0", "quotes": ["SA = 0"]}]), [], GoalSpec("solid_volume", {"apex": "S", "base": ["A", "B", "C"]}, "a"), "CONTRADICTORY_CONSTRAINTS", None, q_text="Tính V(S.ABC)")

    # 4 UNSUPPORTED_OPERATOR
    add("HN13_unsupported_circumscribed_sphere_radius", "Negative_Unsupported", _cuboid_122(), [], GoalSpec("circumscribed_sphere_radius", {"solid": "ABCD.A'B'C'D'"}, "a"), "UNSUPPORTED_OPERATOR", None, q_text="Tính bán kính mặt cầu ngoại tiếp")
    add("HN14_unsupported_inscribed_sphere_radius", "Negative_Unsupported", _regular_tri_pyramid("a", "a"), [], GoalSpec("inscribed_sphere_radius", {"solid": "S.ABC"}, "a"), "UNSUPPORTED_OPERATOR", None, q_text="Tính bán kính mặt cầu nội tiếp")
    add("HN15_unsupported_tangent_cylinder", "Negative_Unsupported", _pyramid_right_B("a"), [], GoalSpec("unsupported_goal", {"kind": "cylinder_area"}, "a"), "UNSUPPORTED_OPERATOR", None, q_text="Tính diện tích xung quanh hình trụ nội tiếp")
    add("HN16_unsupported_locus_extrema", "Negative_Unsupported", _pyramid_square("a"), [], GoalSpec("unsupported_goal", {"kind": "locus_max_distance"}, "a"), "UNSUPPORTED_OPERATOR", None, q_text="Tìm giá trị lớn nhất khoảng cách khi M di động trên SC")

    return cases


def run_holdout_evaluation(cases: list[dict[str, Any]], freeze_sha: str, per_file_sha: dict[str, str]) -> tuple[dict[str, Any], dict[str, Any]]:
    dp_v2 = DynamicConstructionPlanner(mode="v2")
    budget = SearchBudget()

    manifest = {
        "schema": "axo-independent-construction-holdout-manifest/1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provenance_class": "INTERNAL_POST_FREEZE_INDEPENDENT_SYNTHESIS",
        "external_independence": "NOT_MEASURED",
        "frozen_candidate_version": DYNAMIC_PLANNER_V2_VERSION,
        "candidate_v2_freeze_sha256": freeze_sha,
        "candidate_per_file_sha256": per_file_sha,
        "total_cases": len(cases),
        "positive_cases": sum(1 for c in cases if c["expected_status"] == "GOAL_VERIFIED"),
        "negative_cases": sum(1 for c in cases if c["expected_status"] != "GOAL_VERIFIED"),
        "family_counts": dict(Counter(c["family"] for c in cases)),
        "cases": [
            {
                "case_id": c["case_id"],
                "family": c["family"],
                "problem_text": c["full_problem_text"],
                "goal_spec": c["goal_spec"].to_dict(),
                "expected_status": c["expected_status"],
                "independent_oracle": c["independent_oracle"],
                "tags": c["tags"],
            }
            for c in cases
        ],
    }

    rows: list[dict[str, Any]] = []
    status_counts: Counter[str] = Counter()
    by_family: dict[str, list[bool]] = {}
    a2_comparable = 0
    a2_passed = 0
    c_passed_count = 0
    pos_passed = 0
    pos_total = 0
    neg_passed = 0
    neg_total = 0

    for c in cases:
        t0 = time.perf_counter()
        frame = build_initial_frame(
            case_id=c["case_id"],
            problem_text=c["problem_text"],
            solid_spec=c["solid_spec"],
            chart_premises=c["chart_premises"],
            pending_constructions=c["pending"],
            length_unit="a",
        )
        t_frame_ms = (time.perf_counter() - t0) * 1000.0
        res = dp_v2.plan(frame=frame, goal_spec=c["goal_spec"], budget=budget)

        expected = c["expected_status"]
        l0_l4 = False
        pres_ok = False
        multi_ok = True
        ans = None
        aux_count = 0
        steps_count = 0

        if expected == "GOAL_VERIFIED":
            pos_total += 1
            if res.status == "GOAL_VERIFIED" and res.best_plan is not None:
                ans = res.best_plan.answer
                aux_count = res.best_plan.to_summary_dict()["auxiliary_count"]
                steps_count = len(res.best_plan.proof_graph.nodes)
                sc = compile_proof_graph_to_scene3d(frame, res.best_plan.proof_graph, res.best_plan.presentation_graph)
                rep = verify_full_proof_and_scene(res.best_plan.proof_graph, frame.chart_metric, scene3d=sc, strict_node_replay=True)
                l0_l4 = rep.passed
                pres_ok = validate_presentation_step_graph(res.best_plan.proof_graph, res.best_plan.presentation_graph)["valid"]
                if c["min_expected_plans"] >= 2:
                    multi_ok = validate_multiplan_switching(frame, res.plans)["valid"] and len(res.plans) >= c["min_expected_plans"]
            passed = bool(
                res.status == "GOAL_VERIFIED"
                and ans is not None
                and c["independent_oracle"] is not None
                and same_value_v2(ans, c["independent_oracle"])
                and l0_l4
                and pres_ok
                and multi_ok
            )
            if passed:
                pos_passed += 1
        else:
            neg_total += 1
            passed = bool(
                res.status == expected
                or (expected == "DEGENERATE_CONSTRUCTION" and res.status in ("DEGENERATE_CONSTRUCTION", "CONTRADICTORY_CONSTRAINTS") and "DEGENERATE" in str(res.failure_code or ""))
            )
            # Strict label match check
            if expected == "DEGENERATE_CONSTRUCTION" and res.status != "DEGENERATE_CONSTRUCTION":
                passed = False
            if passed:
                neg_passed += 1

        if passed:
            c_passed_count += 1
        status_counts[res.status] += 1
        by_family.setdefault(c["family"], []).append(passed)

        # Arm A2 comparison on baseline_tf2_facts when expressible
        a2_status = None
        a2_ok = None
        if c["baseline_tf2_facts"] is not None:
            a2_comparable += 1
            r_a2 = function_route.run_fact_route(c["full_problem_text"], {"schema": "typed-facts/2", "facts": c["baseline_tf2_facts"]})
            a2_status = r_a2.status
            if expected == "GOAL_VERIFIED":
                a2_ans = str((r_a2.answers or {}).get("q1") or "")
                a2_ok = bool(r_a2.status == "SERVED" and a2_ans and c["independent_oracle"] and same_value_v2(a2_ans, c["independent_oracle"]))
            else:
                a2_ok = r_a2.status != "SERVED"
            if a2_ok:
                a2_passed += 1

        rows.append({
            "case_id": c["case_id"],
            "family": c["family"],
            "expected_status": expected,
            "independent_oracle": c["independent_oracle"],
            "planner_status": res.status,
            "failure_code": res.failure_code,
            "planner_answer": ans,
            "l0_l4_verified": l0_l4,
            "presentation_valid": pres_ok,
            "plans_count": len(res.plans),
            "multi_plan_valid": multi_ok if c["min_expected_plans"] >= 2 else None,
            "auxiliary_count": aux_count,
            "proof_node_count": steps_count,
            "frame_ms": round(t_frame_ms, 3),
            "search_ms": res.telemetry["search_ms"],
            "expanded_states": res.telemetry["expanded_states"],
            "passed": passed,
            "arm_a2_status": a2_status,
            "arm_a2_ok": a2_ok,
        })

    eval_doc = {
        "schema": "axo-independent-construction-evaluation/1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "provenance_class": "INTERNAL_POST_FREEZE_INDEPENDENT_SYNTHESIS",
        "external_independence": "NOT_MEASURED",
        "candidate_v2_freeze_sha256": freeze_sha,
        "summary": {
            "total_cases": len(cases),
            "total_passed": c_passed_count,
            "overall_pass_rate": f"{c_passed_count}/{len(cases)}",
            "positive_passed": f"{pos_passed}/{pos_total}",
            "negative_passed": f"{neg_passed}/{neg_total}",
            "status_distribution": dict(status_counts),
            "by_family": {fam: f"{sum(vals)}/{len(vals)}" for fam, vals in sorted(by_family.items())},
            "arm_a2_expressible_subset_passed": f"{a2_passed}/{a2_comparable}",
            "avg_search_ms": round(sum(r["search_ms"] for r in rows) / len(rows), 3),
        },
        "cases": rows,
    }
    return manifest, eval_doc


def run_search_stress_and_e2e_timing() -> dict[str, Any]:
    dp_v2 = DynamicConstructionPlanner(mode="v2")
    txt, sol, prems = _cuboid_122()

    # 1. Depth Scaling (`4 -> 18` pending constructions)
    depth_rows: list[dict[str, Any]] = []
    for k_steps in (2, 4, 8, 12, 16, 20):
        pending = [PendingConstruction(f"m{i}", "op.midpoint_segment", f"M_{i}", {"a": "A" if i == 0 else f"M_{i-1}", "b": "C'" if i % 2 == 0 else "D'"}) for i in range(k_steps)]
        f = build_initial_frame(case_id=f"STRESS_depth_{k_steps}", problem_text=txt, solid_spec=sol, chart_premises=prems, pending_constructions=pending, length_unit="a")
        g = GoalSpec("segment_length", {"a": "A", "b": f"M_{k_steps - 1}"}, "a")
        res = dp_v2.plan(frame=f, goal_spec=g, budget=SearchBudget(max_depth=32, max_expanded_states=150, max_wall_clock_ms=3000.0))
        depth_rows.append({
            "pending_steps": k_steps,
            "status": res.status,
            "proof_nodes": len(res.best_plan.proof_graph.nodes) if res.best_plan else 0,
            "search_ms": res.telemetry["search_ms"],
            "expanded_states": res.telemetry["expanded_states"],
        })

    # 2. High-Branching Grid & Tight Budget Checks (`SEARCH_RESOURCE_LIMIT` & `SEARCH_TIMEOUT`)
    f_branch = build_initial_frame(
        case_id="STRESS_branching_blowup",
        problem_text=txt,
        solid_spec=sol,
        chart_premises=prems,
        pending_constructions=[],
        length_unit="a",
    )
    res_limit = dp_v2.plan(
        frame=f_branch,
        goal_spec=GoalSpec("distance_point_plane", {"point": "A", "plane": ["A'", "B", "D"]}, "a"),
        budget=SearchBudget(max_expanded_states=1, max_wall_clock_ms=5000.0),
    )
    res_timeout = dp_v2.plan(
        frame=f_branch,
        goal_spec=GoalSpec("distance_point_plane", {"point": "A", "plane": ["A'", "B", "D"]}, "a"),
        budget=SearchBudget(max_expanded_states=500, max_wall_clock_ms=0.001),
    )
    # Tight budget must NEVER report false CONTRADICTORY_CONSTRAINTS!
    budget_ok = (
        res_limit.status == "SEARCH_RESOURCE_LIMIT"
        and res_limit.status != "CONTRADICTORY_CONSTRAINTS"
        and res_timeout.status in ("SEARCH_TIMEOUT", "GOAL_VERIFIED")
        and res_timeout.status != "CONTRADICTORY_CONSTRAINTS"
    )
    if res_timeout.status == "GOAL_VERIFIED":
        # Trigger timeout inside multi-step search cleanly
        res_timeout2 = dp_v2.plan(
            frame=f_branch,
            goal_spec=GoalSpec("distance_skew_lines", {"line1": ["A'", "B"], "line2": ["B'", "C"]}, "a"),
            budget=SearchBudget(max_expanded_states=500, max_wall_clock_ms=0.0001),
        )
        timeout_status = res_timeout2.status
    else:
        timeout_status = res_timeout.status

    # 3. 9-Stage E2E Timing Comparison (`Arm A2` vs `Arm C` via VerifiedInputBridge)
    from scripts.evaluate_axo_construction_v1 import build_benchmark_cases
    from scripts.reconcile_and_compare_construction_v2 import _arm_a2_equivalent_input

    b01_case = next(c for c in build_benchmark_cases() if c["case_id"] == "B01_divide_segment_ratio_length")
    txt_b01, facts_b01 = _arm_a2_equivalent_input(b01_case)
    t0 = time.perf_counter()
    a2_res = function_route.run_fact_route(txt_b01, {"schema": "typed-facts/2", "facts": facts_b01})
    a2_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    br = bridge_verified_facts_to_construction_input(case_id="E2E_B01", problem_text=txt_b01, raw_facts_payload={"schema": "typed-facts/2", "facts": facts_b01})
    assert br.accepted and br.frame is not None and br.goal_spec is not None, f"Bridge refused E2E_B01: {br.source_gate_code}: {br.source_gate_reason}"
    t2 = time.perf_counter()
    pl_res = dp_v2.plan(frame=br.frame, goal_spec=br.goal_spec, budget=SearchBudget())
    t3 = time.perf_counter()
    sc_e2e = compile_proof_graph_to_scene3d(br.frame, pl_res.best_plan.proof_graph, pl_res.best_plan.presentation_graph)
    t4 = time.perf_counter()
    ver_e2e = verify_full_proof_and_scene(pl_res.best_plan.proof_graph, br.frame.chart_metric, scene3d=sc_e2e, strict_node_replay=True)
    t5 = time.perf_counter()

    return {
        "schema": "axo-search-stress-benchmark/1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "depth_scaling": depth_rows,
        "resource_limit_checks": {
            "max_expanded_states_1_status": res_limit.status,
            "tight_timeout_status": timeout_status,
            "zero_false_contradictory_on_budget_exhaustion": bool(budget_ok and timeout_status != "CONTRADICTORY_CONSTRAINTS"),
        },
        "e2e_stage_timing_ms": {
            "arm_a2_legacy_total_ms": round(a2_ms, 3),
            "arm_a2_status": a2_res.status,
            "arm_c_bridge_and_source_gate_ms": round((t2 - t1) * 1000.0, 3),
            "arm_c_dynamic_search_ms": round((t3 - t2) * 1000.0, 3),
            "arm_c_scene3d_compile_ms": round((t4 - t3) * 1000.0, 3),
            "arm_c_l0_l4_strict_verify_ms": round((t5 - t4) * 1000.0, 3),
            "arm_c_e2e_total_ms": round((t5 - t1) * 1000.0, 3),
            "arm_c_e2e_verified": bool(ver_e2e.passed),
        },
    }


def main() -> int:
    V2_RUN_DIR.mkdir(parents=True, exist_ok=True)
    live_sha, per_file = compute_candidate_freeze_sha256()
    assert live_sha == CANDIDATE_V2_FREEZE_SHA256, (
        f"Candidate package freeze violated BEFORE holdout run: {live_sha} != {CANDIDATE_V2_FREEZE_SHA256}"
    )

    cases = build_independent_holdout_cases()
    manifest, eval_doc = run_holdout_evaluation(cases, live_sha, per_file)
    stress_doc = run_search_stress_and_e2e_timing()

    # Re-assert freeze SHA AFTER run as sanity check
    post_sha, _ = compute_candidate_freeze_sha256()
    assert post_sha == CANDIDATE_V2_FREEZE_SHA256

    (V2_RUN_DIR / "INDEPENDENT_CONSTRUCTION_HOLDOUT_MANIFEST.json").write_text(canonical_json_dumps(manifest), encoding="utf-8")
    (V2_RUN_DIR / "INDEPENDENT_CONSTRUCTION_EVALUATION.json").write_text(canonical_json_dumps(eval_doc), encoding="utf-8")
    (V2_RUN_DIR / "SEARCH_STRESS_BENCHMARK.json").write_text(canonical_json_dumps(stress_doc), encoding="utf-8")

    print("HOLDOUT_SUMMARY:", json.dumps(eval_doc["summary"], ensure_ascii=False))
    print("STRESS_SUMMARY:", json.dumps(stress_doc["resource_limit_checks"], ensure_ascii=False), json.dumps(stress_doc["e2e_stage_timing_ms"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
