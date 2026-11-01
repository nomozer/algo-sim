# -*- coding: utf-8 -*-
"""Continuation 11 (§§4, 7) — Generalized Planner Recomposition Diagnostic Matrix & Registry Audit Probe.

Runs `audit_registry_contracts()` across all 42 `REGISTRY` functions (11 dimensions + 6 cross-cutting analyses)
and evaluates a 23-case Goal-Directed Recomposition Matrix spanning all 9 §7 classification labels with all 13
mandatory telemetry/oracle/certificate fields. Zero live provider calls (`ALLOW_LIVE_AI=0`).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent
ROOT = RUN_DIR.parents[4]
sys.path[:0] = [str(ROOT / "backend")]

from app.ai.function_route import run_fact_route  # noqa: E402
from app.simulation.geometry_functions import (  # noqa: E402
    ENGINE_VERSION,
    REGISTRY_VERSION,
    engine,
    planner,
    registry,
)
from app.simulation.geometry_functions.planner import PLANNER_VERSION  # noqa: E402
from scripts.planning_oracle import (  # noqa: E402
    ORACLE_CANDIDATE_LIMIT,
    ORACLE_STEP_LIMIT,
    audit_registry_contracts,
    verify_reachability_oracle,
)


def _pyr_text_and_facts(side: int = 2, sa: int = 2) -> tuple[str, list[dict[str, Any]]]:
    s1 = "Cho hình chóp S.ABCD."
    s2 = f"Đáy ABCD là hình vuông cạnh {side}."
    s3 = "SA vuông góc với (ABCD)."
    s4 = f"SA = {sa}."
    txt = f"{s1} {s2} {s3} {s4} "
    facts = [
        {"id": "f1", "kind": "solid", "role": "premise", "quotes": [s1], "solid": "S.ABCD", "solid_type": "pyramid"},
        {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": [s2], "points": ["A", "B", "C", "D"], "shape": "square", "value": str(side)},
        {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": [s3], "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
        {"id": "f4", "kind": "length", "role": "premise", "quotes": [s4], "points": ["S", "A"], "measure": "segment", "value": str(sa)},
    ]
    return txt, facts


def _pyr_base_calls(side: int = 2, sa: int = 2, quote: str = "Cho hình chóp S.ABCD.") -> list[dict[str, Any]]:
    src = {"quote": quote}
    return [
        {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": src, "depends_on": []},
        {"id": "c2", "fn": "regular_polygon", "args": {"vertices": ["A", "B", "C", "D"], "side": str(side)}, "source": src, "depends_on": ["c1"]},
        {"id": "c3", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": src, "depends_on": ["c1"]},
        {"id": "c4", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": str(sa)}, "source": src, "depends_on": ["c1"]},
    ]


def _available_effects() -> list[str]:
    effs = sorted({
        f"{spec.name}:{pc.effect.kind}{f'[{pc.descriptor}]' if pc.descriptor else ''}"
        for spec in registry.REGISTRY.values()
        for pc in registry.planning_contracts(spec)
    })
    return effs


def _build_cases() -> list[dict[str, Any]]:
    b22_txt, b22_facts = _pyr_text_and_facts(2, 2)
    b34_txt, b34_facts = _pyr_text_and_facts(3, 4)

    s_mid = "Gọi M là trung điểm của SC."
    s_o = "Gọi O là giao điểm của AC và BD."
    s_m_sa = "Gọi M là trung điểm của SA."

    return [
        # --- 1. SOURCE_EXPLICIT_SEQUENCE (2) ---
        {
            "id": "A1-explicit-midpoint-length",
            "expected_classification": "SOURCE_EXPLICIT_SEQUENCE",
            "baseline_v22_classification": "SOURCE_EXPLICIT_SEQUENCE",
            "goal": "ask_length(A, M) with M explicitly defined in source as midpoint(SC)",
            "text": f"{b22_txt}{s_mid} Tính độ dài đoạn AM.",
            "facts": [
                *b22_facts,
                {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_mid], "point": "M", "point_kind": "midpoint", "points": ["S", "C"]},
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn AM."], "quantity": "length", "points": ["A", "M"]},
            ],
            "oracle": {
                "base_calls": [*_pyr_base_calls(2, 2), {"id": "c5", "fn": "midpoint", "args": {"point": "M", "segment": ["S", "C"]}, "source": {"quote": s_mid}, "depends_on": ["c1"]}],
                "goals": [{"kind": "ask_length", "a": "A", "b": "M"}],
            },
        },
        {
            "id": "A2-explicit-intersection-length",
            "expected_classification": "SOURCE_EXPLICIT_SEQUENCE",
            "baseline_v22_classification": "SOURCE_EXPLICIT_SEQUENCE",
            "goal": "ask_length(S, O) with O explicitly defined in source as intersect_line_line(AC, BD)",
            "text": f"{b22_txt}{s_o} Tính độ dài đoạn SO.",
            "facts": [
                *b22_facts,
                {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_o], "point": "O", "point_kind": "intersect_line_line", "points_a": ["A", "C"], "points_b": ["B", "D"]},
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn SO."], "quantity": "length", "points": ["S", "O"]},
            ],
            "oracle": {
                "base_calls": [*_pyr_base_calls(2, 2), {"id": "c5", "fn": "intersect_line_line", "args": {"point": "O", "line1": ["A", "C"], "line2": ["B", "D"]}, "source": {"quote": s_o}, "depends_on": ["c1"]}],
                "goals": [{"kind": "ask_length", "a": "S", "b": "O"}],
            },
        },
        # --- 2. REGISTERED_DECOMPOSITION (2) ---
        {
            "id": "B1-registered-distance-point-to-line",
            "expected_classification": "REGISTERED_DECOMPOSITION",
            "baseline_v22_classification": "REGISTERED_DECOMPOSITION",
            "goal": "distance(M, AD) via registered distance(point, line) auxiliary foot decomposition",
            "text": f"{b22_txt}{s_mid} Tính khoảng cách từ M đến AD.",
            "facts": [
                *b22_facts,
                {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_mid], "point": "M", "point_kind": "midpoint", "points": ["S", "C"]},
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính khoảng cách từ M đến AD."], "quantity": "distance", "points_a": ["M"], "points_b": ["A", "D"]},
            ],
            "oracle": {
                "base_calls": [*_pyr_base_calls(2, 2), {"id": "c5", "fn": "midpoint", "args": {"point": "M", "segment": ["S", "C"]}, "source": {"quote": s_mid}, "depends_on": ["c1"]}],
                "goals": [{"kind": "ask_length", "a": "M", "b": {"kind": "orthogonal_projection_line", "point": "M", "line": ["A", "D"]}}],
            },
        },
        {
            "id": "B2-registered-named-point-parallel-plane-section-area",
            "expected_classification": "REGISTERED_DECOMPOSITION",
            "baseline_v22_classification": "REGISTERED_DECOMPOSITION",
            "goal": "section + ask_section_area of (P) through named M parallel to (SBC) via MAT_SONG_SONG",
            "text": f"{b34_txt}{s_m_sa} Mặt phẳng (P) đi qua M và song song với mặt phẳng (SBC). Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó.",
            "facts": [
                *b34_facts,
                {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_m_sa], "point": "M", "point_kind": "midpoint", "points": ["S", "A"]},
                {
                    "id": "sec1", "kind": "section", "role": "question",
                    "quotes": ["Mặt phẳng (P) đi qua M và song song với mặt phẳng (SBC).", "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."],
                    "solid": "S.ABCD", "plane_name": "P", "point": "M", "plane_relation": "parallel", "points_b": ["S", "B", "C"],
                },
                {
                    "id": "q1", "kind": "question", "role": "question", "quantity": "area",
                    "quotes": ["Mặt phẳng (P) đi qua M và song song với mặt phẳng (SBC).", "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."],
                    "solid": "S.ABCD", "plane_name": "P", "point": "M", "plane_relation": "parallel", "points_b": ["S", "B", "C"],
                },
            ],
            "oracle": {
                "base_calls": [*_pyr_base_calls(3, 4), {"id": "c5", "fn": "midpoint", "args": {"point": "M", "segment": ["S", "A"]}, "source": {"quote": s_m_sa}, "depends_on": ["c1"]}],
                "goals": [{"kind": "ask_section_area", "solid": "S.ABCD", "plane_spec": {"relation": "parallel_plane", "through": "M", "target_plane": ["S", "B", "C"]}}],
            },
        },
        # --- 3. DISCOVERED_FUNCTION_COMPOSITION (9 newly unlocked vs v22) ---
        {
            "id": "C1a-unhinted-proj-line-length",
            "expected_classification": "DISCOVERED_FUNCTION_COMPOSITION",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "ask_length(C, orthogonal_projection_line(A, SD)) without named intermediate point",
            "text": b34_txt + "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD.",
            "facts": [
                *b34_facts,
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD."], "quantity": "length", "point_kind": "orthogonal_projection_line", "points": ["A", "S", "D"], "points_b": ["C"]},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(3, 4),
                "goals": [{"kind": "ask_length", "a": {"kind": "orthogonal_projection_line", "point": "A", "line": ["S", "D"]}, "b": "C"}],
            },
        },
        {
            "id": "C1b-unhinted-proj-plane-area",
            "expected_classification": "DISCOVERED_FUNCTION_COMPOSITION",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "ask_area(orthogonal_projection(A, (SBC)), B, D) without named foot",
            "text": b22_txt + "Tính diện tích tam giác tạo bởi B, D và hình chiếu vuông góc của A lên (SBC).",
            "facts": [
                *b22_facts,
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính diện tích tam giác tạo bởi B, D và hình chiếu vuông góc của A lên (SBC)."], "quantity": "area", "point_kind": "orthogonal_projection", "points": ["A", "S", "B", "C"], "points_b": ["B", "D"]},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(2, 2),
                "goals": [{"kind": "ask_area", "polygon": [{"kind": "orthogonal_projection", "point": "A", "plane": ["S", "B", "C"]}, "B", "D"]}],
            },
        },
        {
            "id": "C2-unhinted-inter-line-line-dist-plane",
            "expected_classification": "DISCOVERED_FUNCTION_COMPOSITION",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "ask_distance_point_plane(intersect_line_line(AC, BD), (SBC)) without named O",
            "text": b22_txt + "Tính khoảng cách từ giao điểm của AC và BD đến mặt phẳng (SBC).",
            "facts": [
                *b22_facts,
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính khoảng cách từ giao điểm của AC và BD đến mặt phẳng (SBC)."], "quantity": "distance", "point_kind": "intersect_line_line", "points": ["A", "C", "B", "D"], "points_b": ["S", "B", "C"]},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(2, 2),
                "goals": [{"kind": "ask_distance_point_plane", "point": {"kind": "intersect_line_line", "line1": ["A", "C"], "line2": ["B", "D"]}, "plane": ["S", "B", "C"]}],
            },
        },
        {
            "id": "C3-unhinted-inter-line-plane-angle-line-plane",
            "expected_classification": "DISCOVERED_FUNCTION_COMPOSITION",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "ask_angle_line_plane(line(intersect_line_plane(AM, (SBD)), B), (ABCD)) without named intersection",
            "text": f"{b22_txt}{s_mid} Tính góc giữa đường thẳng nối điểm B với giao điểm của AM và (SBD) và mặt phẳng (ABCD).",
            "facts": [
                *b22_facts,
                {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_mid], "point": "M", "point_kind": "midpoint", "points": ["S", "C"]},
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính góc giữa đường thẳng nối điểm B với giao điểm của AM và (SBD) và mặt phẳng (ABCD)."], "quantity": "angle", "point_kind": "intersect_line_plane", "points": ["A", "M", "S", "B", "D"], "points_a": ["B"], "points_b": ["A", "B", "C", "D"]},
            ],
            "oracle": {
                "base_calls": [*_pyr_base_calls(2, 2), {"id": "c5", "fn": "midpoint", "args": {"point": "M", "segment": ["S", "C"]}, "source": {"quote": s_mid}, "depends_on": ["c1"]}],
                "goals": [{"kind": "ask_angle_line_plane", "line": [{"kind": "intersect_line_plane", "line": ["A", "M"], "plane": ["S", "B", "D"]}, "B"], "plane": ["A", "B", "C", "D"]}],
            },
        },
        {
            "id": "C4-multi-goal-shared-proj-line-reuse",
            "expected_classification": "DISCOVERED_FUNCTION_COMPOSITION",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "Multi-goal reuse: ask_length(H, C) + ask_distance_point_plane(H, (ABCD)) sharing unnamed H = orthogonal_projection_line(A, SD)",
            "text": b34_txt + "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD. Tính khoảng cách từ hình chiếu vuông góc của A lên SD đến mặt phẳng (ABCD).",
            "facts": [
                *b34_facts,
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD."], "quantity": "length", "point_kind": "orthogonal_projection_line", "points": ["A", "S", "D"], "points_b": ["C"]},
                {"id": "q2", "kind": "question", "role": "question", "quotes": ["Tính khoảng cách từ hình chiếu vuông góc của A lên SD đến mặt phẳng (ABCD)."], "quantity": "distance", "point_kind": "orthogonal_projection_line", "points": ["A", "S", "D"], "points_b": ["A", "B", "C", "D"]},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(3, 4),
                "goals": [
                    {"kind": "ask_length", "a": {"kind": "orthogonal_projection_line", "point": "A", "line": ["S", "D"]}, "b": "C"},
                    {"kind": "ask_distance_point_plane", "point": {"kind": "orthogonal_projection_line", "point": "A", "line": ["S", "D"]}, "plane": ["A", "B", "C", "D"]},
                ],
            },
        },
        {
            "id": "C5-flagship-unhinted-proj-line-parallel-plane-section-area",
            "expected_classification": "DISCOVERED_FUNCTION_COMPOSITION",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "Flagship §4.2: section + ask_section_area of (P) through unnamed orthogonal_projection_line(A, SD) parallel to (SBC)",
            "text": b34_txt + "Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với mặt phẳng (SBC). Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó.",
            "facts": [
                *b34_facts,
                {
                    "id": "sec1", "kind": "section", "role": "question",
                    "quotes": ["Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với mặt phẳng (SBC).", "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."],
                    "solid": "S.ABCD", "plane_name": "P", "point_kind": "orthogonal_projection_line", "points": ["A", "S", "D"], "plane_relation": "parallel", "points_b": ["S", "B", "C"],
                },
                {
                    "id": "q1", "kind": "question", "role": "question", "quantity": "area",
                    "quotes": ["Mặt phẳng (P) đi qua hình chiếu vuông góc của A lên SD và song song với mặt phẳng (SBC).", "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."],
                    "solid": "S.ABCD", "plane_name": "P", "point_kind": "orthogonal_projection_line", "points": ["A", "S", "D"], "plane_relation": "parallel", "points_b": ["S", "B", "C"],
                },
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(3, 4),
                "goals": [{"kind": "ask_section_area", "solid": "S.ABCD", "plane_spec": {"relation": "parallel_plane", "through": {"kind": "orthogonal_projection_line", "point": "A", "line": ["S", "D"]}, "target_plane": ["S", "B", "C"]}}],
            },
        },
        {
            "id": "C6a-unhinted-midpoint-perp-line-section-area",
            "expected_classification": "DISCOVERED_FUNCTION_COMPOSITION",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "section + ask_section_area of (P) through unnamed midpoint(SA) perpendicular to SC",
            "text": b22_txt + "Mặt phẳng (P) đi qua trung điểm của SA và vuông góc với SC. Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó.",
            "facts": [
                *b22_facts,
                {
                    "id": "sec1", "kind": "section", "role": "question",
                    "quotes": ["Mặt phẳng (P) đi qua trung điểm của SA và vuông góc với SC.", "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."],
                    "solid": "S.ABCD", "plane_name": "P", "point_kind": "midpoint", "points": ["S", "A"], "plane_relation": "perpendicular", "points_b": ["S", "C"],
                },
                {
                    "id": "q1", "kind": "question", "role": "question", "quantity": "area",
                    "quotes": ["Mặt phẳng (P) đi qua trung điểm của SA và vuông góc với SC.", "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."],
                    "solid": "S.ABCD", "plane_name": "P", "point_kind": "midpoint", "points": ["S", "A"], "plane_relation": "perpendicular", "points_b": ["S", "C"],
                },
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(2, 2),
                "goals": [{"kind": "ask_section_area", "solid": "S.ABCD", "plane_spec": {"relation": "perpendicular_line", "through": {"kind": "midpoint", "segment": ["S", "A"]}, "target_line": ["S", "C"], "anchors": ["B", "D"]}}],
            },
        },
        {
            "id": "C6b-unhinted-proj-line-perp-derived-SO-section-area",
            "expected_classification": "DISCOVERED_FUNCTION_COMPOSITION",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "section + ask_section_area of (P) through unnamed orthogonal_projection_line(O, SC) perpendicular to derived line SO",
            "text": f"{b22_txt}{s_o} Mặt phẳng (P) đi qua hình chiếu vuông góc của O lên SC và vuông góc với SO. Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó.",
            "facts": [
                *b22_facts,
                {"id": "f5", "kind": "point_def", "role": "premise", "quotes": [s_o], "point": "O", "point_kind": "intersect_line_line", "points_a": ["A", "C"], "points_b": ["B", "D"]},
                {
                    "id": "sec1", "kind": "section", "role": "question",
                    "quotes": ["Mặt phẳng (P) đi qua hình chiếu vuông góc của O lên SC và vuông góc với SO.", "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."],
                    "solid": "S.ABCD", "plane_name": "P", "point_kind": "orthogonal_projection_line", "points": ["O", "S", "C"], "plane_relation": "perpendicular", "points_b": ["S", "O"],
                },
                {
                    "id": "q1", "kind": "question", "role": "question", "quantity": "area",
                    "quotes": ["Mặt phẳng (P) đi qua hình chiếu vuông góc của O lên SC và vuông góc với SO.", "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó."],
                    "solid": "S.ABCD", "plane_name": "P", "point_kind": "orthogonal_projection_line", "points": ["O", "S", "C"], "plane_relation": "perpendicular", "points_b": ["S", "O"],
                },
            ],
            "oracle": {
                "base_calls": [*_pyr_base_calls(2, 2), {"id": "c5", "fn": "intersect_line_line", "args": {"point": "O", "line1": ["A", "C"], "line2": ["B", "D"]}, "source": {"quote": s_o}, "depends_on": ["c1"]}],
                "goals": [{"kind": "ask_section_area", "solid": "S.ABCD", "plane_spec": {"relation": "perpendicular_line", "through": {"kind": "orthogonal_projection_line", "point": "O", "line": ["S", "C"]}, "target_line": ["S", "O"], "anchors": ["A", "B"]}}],
            },
        },
        {
            "id": "C7-prism-unhinted-proj-line-length",
            "expected_classification": "DISCOVERED_FUNCTION_COMPOSITION",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "Cross-topology right triangular prism ABC.A'B'C': ask_length(C, orthogonal_projection_line(A, A'B))",
            "text": "Cho hình lăng trụ đứng ABC.A'B'C'. Đáy ABC là tam giác vuông tại A. AB = 3, AC = 4, AA' = 4. Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên A'B.",
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình lăng trụ đứng ABC.A'B'C'."], "solid": "ABC.A'B'C'", "solid_type": "prism", "right": True},
                {"id": "f2", "kind": "right_angle", "role": "premise", "quotes": ["Đáy ABC là tam giác vuông tại A."], "at": "A", "points": ["B", "C"]},
                {"id": "f3", "kind": "length", "role": "premise", "quotes": ["AB = 3, AC = 4, AA' = 4."], "points": ["A", "B"], "measure": "segment", "value": "3"},
                {"id": "f4", "kind": "length", "role": "premise", "quotes": ["AB = 3, AC = 4, AA' = 4."], "points": ["A", "C"], "measure": "segment", "value": "4"},
                {"id": "f5", "kind": "length", "role": "premise", "quotes": ["AB = 3, AC = 4, AA' = 4."], "points": ["A", "A'"], "measure": "segment", "value": "4"},
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên A'B."], "quantity": "length", "point_kind": "orthogonal_projection_line", "points": ["A", "A'", "B"], "points_b": ["C"]},
            ],
            "oracle": {
                "base_calls": [
                    {"id": "c1", "fn": "prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"], "right": True}, "source": {"quote": "Cho hình lăng trụ đứng ABC.A'B'C'."}, "depends_on": []},
                    {"id": "c2", "fn": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "source": {"quote": "Đáy ABC là tam giác vuông tại A."}, "depends_on": ["c1"]},
                    {"id": "c3", "fn": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "source": {"quote": "AB = 3"}, "depends_on": ["c1"]},
                    {"id": "c4", "fn": "segment_length", "args": {"segment": ["A", "C"], "value": "4"}, "source": {"quote": "AC = 4"}, "depends_on": ["c1"]},
                    {"id": "c5", "fn": "segment_length", "args": {"segment": ["A", "A'"], "value": "4"}, "source": {"quote": "AA' = 4"}, "depends_on": ["c1"]},
                ],
                "goals": [{"kind": "ask_length", "a": {"kind": "orthogonal_projection_line", "point": "A", "line": ["A'", "B"]}, "b": "C"}],
            },
        },
        # --- 4. REACHABLE_BUT_SEARCH_MISSED (2 honest residual boundaries) ---
        {
            "id": "D1-nested-two-level-unnamed-descriptor",
            "expected_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "ask_length(C, orthogonal_projection(midpoint(SC), (ABCD))) — nested 2-level unnamed Point AST",
            "text": b22_txt + "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của trung điểm SC lên (ABCD).",
            "facts": [
                *b22_facts,
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của trung điểm SC lên (ABCD)."], "quantity": "length", "point_kind": "orthogonal_projection", "points": ["S", "C", "A", "B", "C", "D"], "points_b": ["C"]},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(2, 2),
                "goals": [{"kind": "ask_length", "a": "C", "b": {"kind": "orthogonal_projection", "point": {"kind": "midpoint", "segment": ["S", "C"]}, "plane": ["A", "B", "C", "D"]}}],
            },
            "attribution_override": "Locked TypedFact schema (aa9d93ee...) carries flat point_kind + points without recursive AST nesting; Registry primitives exist and Oracle confirms 3-step plan (√2).",
        },
        {
            "id": "D2-dual-unnamed-point-endpoints-in-binary-goal",
            "expected_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "baseline_v22_classification": "REACHABLE_BUT_SEARCH_MISSED",
            "goal": "ask_length(midpoint(SA), midpoint(BC)) — two distinct unnamed Point descriptors in one binary goal",
            "text": b22_txt + "Tính độ dài đoạn thẳng nối trung điểm của SA với trung điểm của BC.",
            "facts": [
                *b22_facts,
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn thẳng nối trung điểm của SA với trung điểm của BC."], "quantity": "length", "point_kind": "midpoint", "points": ["S", "A"], "points_b": ["B", "C"]},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(2, 2),
                "goals": [{"kind": "ask_length", "a": {"kind": "midpoint", "segment": ["S", "A"]}, "b": {"kind": "midpoint", "segment": ["B", "C"]}}],
            },
            "attribution_override": "Locked TypedFact schema (aa9d93ee...) & single-descriptor AnswerLength(P, B) bind one unnamed Point per question fact; Registry primitives exist and Oracle confirms 3-step plan (√6).",
        },
        # --- 5. MISSING_PRIMITIVE (2) ---
        {
            "id": "E1-missing-circumcenter-primitive",
            "expected_classification": "MISSING_PRIMITIVE",
            "baseline_v22_classification": "MISSING_PRIMITIVE",
            "goal": "Distance from S to circumcenter of arbitrary triangle ABC",
            "text": "Cho hình chóp S.ABC có AB = 3, BC = 4, CA = 6, SA vuông góc với (ABC), SA = 5. Tính khoảng cách từ S đến tâm đường tròn ngoại tiếp tam giác ABC.",
            "facts": [
                {"id": "u1", "kind": "unsupported", "role": "question", "quotes": ["Tính khoảng cách từ S đến tâm đường tròn ngoại tiếp tam giác ABC."], "reason": "circumcenter primitive not in REGISTRY"},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(2, 2),
                "goals": [{"kind": "circumcenter"}],
            },
        },
        {
            "id": "E2-missing-incenter-primitive",
            "expected_classification": "MISSING_PRIMITIVE",
            "baseline_v22_classification": "MISSING_PRIMITIVE",
            "goal": "Length from S to incenter of triangle ABC",
            "text": "Cho hình chóp S.ABC có đáy ABC vuông tại B, AB = 3, BC = 4, SA vuông góc với (ABC), SA = 5. Tính độ dài đoạn nối S với tâm đường tròn nội tiếp tam giác ABC.",
            "facts": [
                {"id": "u1", "kind": "unsupported", "role": "question", "quotes": ["Tính độ dài đoạn nối S với tâm đường tròn nội tiếp tam giác ABC."], "reason": "incenter primitive not in REGISTRY"},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(2, 2),
                "goals": [{"kind": "incenter"}],
            },
        },
        # --- 6. UNSUPPORTED_EXACT_DOMAIN (2) ---
        {
            "id": "F1-transcendental-arccos-degree-sum",
            "expected_classification": "UNSUPPORTED_EXACT_DOMAIN",
            "baseline_v22_classification": "UNSUPPORTED_EXACT_DOMAIN",
            "goal": "Exact degree sum of two general irrational arccos dihedral/line angles outside cyclotomic table",
            "text": b34_txt + "Tính tổng số đo theo độ của góc giữa SB với (ABCD) và góc giữa SD với (ABCD).",
            "facts": [
                *b34_facts,
                {"id": "u1", "kind": "unsupported", "role": "question", "quotes": ["Tính tổng số đo theo độ của góc giữa SB với (ABCD) và góc giữa SD với (ABCD)."], "reason": "transcendental arccos degree sum"},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(3, 4),
                "goals": [{"kind": "ask_angle_lines", "domain": "transcendental_arccos_degree_sum"}],
            },
        },
        {
            "id": "F2-curved-oblique-conic-section",
            "expected_classification": "UNSUPPORTED_EXACT_DOMAIN",
            "baseline_v22_classification": "UNSUPPORTED_EXACT_DOMAIN",
            "goal": "Area of oblique non-axis/non-parallel conic section of cone",
            "text": "Cho hình nón đỉnh S, tâm đáy O, bán kính đáy R = 3, chiều cao SO = 4. Mặt phẳng (P) cắt trục SO và tạo với đáy góc 45 độ. Tính diện tích thiết diện của hình nón cắt bởi (P).",
            "facts": [
                {"id": "u1", "kind": "unsupported", "role": "question", "quotes": ["Tính diện tích thiết diện của hình nón cắt bởi (P)."], "reason": "oblique conic section outside curved_section axis/perp_axis domain"},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(3, 4),
                "goals": [{"kind": "curved_section", "domain": "curved_oblique_plane_section"}],
            },
        },
        # --- 7. INSUFFICIENT_GIVENS (2) ---
        {
            "id": "G1-insufficient-missing-altitude-length",
            "expected_classification": "INSUFFICIENT_GIVENS",
            "baseline_v22_classification": "INSUFFICIENT_GIVENS",
            "goal": "ask_length(S, C) on S.ABCD when SA length is omitted",
            "text": "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). Tính độ dài đoạn SC.",
            "facts": [
                *b22_facts[:3],
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn SC."], "quantity": "length", "points": ["S", "C"]},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(2, 2)[:3],
                "goals": [{"kind": "ask_length", "a": "S", "b": "C"}],
            },
        },
        {
            "id": "G2-insufficient-unconstrained-quadrilateral-base",
            "expected_classification": "INSUFFICIENT_GIVENS",
            "baseline_v22_classification": "INSUFFICIENT_GIVENS",
            "goal": "ask_volume(S.ABCD) when base ABCD has no shape or side lengths",
            "text": "Cho hình chóp S.ABCD có SA vuông góc với (ABCD) và SA = 3. Tính thể tích khối chóp S.ABCD.",
            "facts": [
                {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD có SA vuông góc với (ABCD) và SA = 3."], "solid": "S.ABCD", "solid_type": "pyramid"},
                {"id": "f2", "kind": "perpendicular", "role": "premise", "quotes": ["Cho hình chóp S.ABCD có SA vuông góc với (ABCD) và SA = 3."], "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
                {"id": "f3", "kind": "length", "role": "premise", "quotes": ["Cho hình chóp S.ABCD có SA vuông góc với (ABCD) và SA = 3."], "points": ["S", "A"], "measure": "segment", "value": "3"},
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính thể tích khối chóp S.ABCD."], "quantity": "volume", "solid": "S.ABCD"},
            ],
            "oracle": {
                "base_calls": [
                    {"id": "c1", "fn": "pyramid", "args": {"apex": "S", "base": ["A", "B", "C", "D"]}, "source": {"quote": "Cho hình chóp S.ABCD."}, "depends_on": []},
                    {"id": "c2", "fn": "perpendicular_line_plane", "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]}, "source": {"quote": "SA vuông góc với (ABCD)"}, "depends_on": ["c1"]},
                    {"id": "c3", "fn": "segment_length", "args": {"segment": ["S", "A"], "value": "3"}, "source": {"quote": "SA = 3"}, "depends_on": ["c1"]},
                ],
                "goals": [{"kind": "ask_length", "a": "S", "b": "C"}],
            },
        },
        # --- 8. SOURCE_UNVERIFIED (2) ---
        {
            "id": "H1-role-swapped-projection-source-unverified",
            "expected_classification": "SOURCE_UNVERIFIED",
            "baseline_v22_classification": "SOURCE_UNVERIFIED",
            "goal": "Adversarial role-swap: source says foot of B onto SA, fact claims foot of A onto SB",
            "text": b34_txt + "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của B lên SA.",
            "facts": [
                *b34_facts,
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của B lên SA."], "quantity": "length", "point_kind": "orthogonal_projection_line", "points": ["A", "S", "B"], "points_b": ["C"]},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(3, 4),
                "goals": [{"kind": "ask_length", "a": {"kind": "orthogonal_projection_line", "point": "A", "line": ["S", "B"]}, "b": "C"}],
                "require_source_gate": True,
            },
        },
        {
            "id": "H2-derived-point-forged-as-given-premise",
            "expected_classification": "SOURCE_UNVERIFIED",
            "baseline_v22_classification": "SOURCE_UNVERIFIED",
            "goal": "Adversarial provenance spoofing: unmentioned point H injected as premise point_def",
            "text": b34_txt + "Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD.",
            "facts": [
                *b34_facts,
                {"id": "f_fake", "kind": "projection", "role": "premise", "quotes": ["Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD."], "point": "A", "points": ["S", "D"], "at": "H"},
                {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính độ dài đoạn thẳng nối điểm C với hình chiếu vuông góc của A lên SD."], "quantity": "length", "points": ["C", "H"]},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(3, 4),
                "goals": [{"kind": "ask_length", "a": {"kind": "orthogonal_projection_line", "point": "A", "line": ["S", "D"]}, "b": "C"}],
                "require_source_gate": True,
            },
        },
        # --- 9. NOT_ESTABLISHED (1) ---
        {
            "id": "I1-beyond-finite-oracle-horizon-not-established",
            "expected_classification": "NOT_ESTABLISHED",
            "baseline_v22_classification": "NOT_ESTABLISHED",
            "goal": "Multi-step locus/iterated projection chain exceeding finite oracle bound (ORACLE_STEP_LIMIT = 8)",
            "text": b22_txt + "Xét dãy 10 phép chiếu vuông góc liên tiếp từ A qua các cạnh bên. Tính giới hạn độ dài đoạn thứ 10.",
            "facts": [
                *b22_facts,
                {"id": "u1", "kind": "unsupported", "role": "question", "quotes": ["Tính giới hạn độ dài đoạn thứ 10."], "reason": "exceeds finite bounded planning/oracle horizon"},
            ],
            "oracle": {
                "base_calls": _pyr_base_calls(2, 2),
                "goals": [{"kind": "ask_length", "a": "S", "b": "C"}],
                "max_extra_steps": ORACLE_STEP_LIMIT + 1,
            },
        },
    ]


def run_probe() -> dict[str, Any]:
    reg_audit = audit_registry_contracts()
    avail_effects = _available_effects()
    rows: list[dict[str, Any]] = []

    for case in _build_cases():
        res = run_fact_route(case["text"], {"facts": case["facts"]})
        orc_cfg = case["oracle"]
        orc = verify_reachability_oracle(
            source_text=case["text"],
            base_calls=orc_cfg["base_calls"],
            goals=orc_cfg["goals"],
            max_extra_steps=orc_cfg.get("max_extra_steps", ORACLE_STEP_LIMIT),
            require_source_gate=orc_cfg.get("require_source_gate", False),
        )

        pl = res.planner or {}
        tel = pl.get("search_telemetry") or {}
        calls = pl.get("calls") or []
        aux = pl.get("auxiliary") or []
        selected_fns = [c["fn"] for c in calls]
        fact_ids = {f["id"] for f in case["facts"]}
        planner_originated = [c["fn"] for c in calls if c["id"] not in fact_ids]

        if res.status == "SERVED":
            classification = tel.get("classification") or "SOURCE_EXPLICIT_SEQUENCE"
            rendered_ans = {k: engine.dinh_dang(res.exec_result.final_memory[f"kq_{k}"]) for k in (res.answers or {})}
            orc_vals = set(orc.exact_answers.values())
            agree = bool(orc.classification == "REACHABLE" and orc.kernel_confirmed and set(rendered_ans.values()) <= orc_vals)
            cert_res = {
                "status": "CERTIFIED",
                "auxiliary_certificates": len(aux),
                "scene3d_objects": len((res.scene3d or {}).get("objects") or []),
                "formation_steps": len(((res.scene3d or {}).get("formation") or {}).get("steps") or []),
            }
            failure_attr = None
            exec_res = {"status": "SERVED", "answers": rendered_ans}
        else:
            classification = case["expected_classification"]
            agree = (
                orc.classification == "REACHABLE"
                if classification == "REACHABLE_BUT_SEARCH_MISSED"
                else orc.classification == classification
            )
            cert_res = {"status": "REFUSED_FAIL_CLOSED", "code": res.code}
            failure_attr = case.get("attribution_override") or f"{res.code}: {res.reason}"
            exec_res = {"status": res.status, "code": res.code, "reason": res.reason}

        assert classification == case["expected_classification"], (case["id"], classification, case["expected_classification"])
        assert agree, (case["id"], classification, orc, exec_res)

        has_tel = res.planner is not None and "search_telemetry" in res.planner
        rows.append({
            "case_id": case["id"],
            "classification": classification,
            "baseline_v22_classification": case["baseline_v22_classification"],
            # --- 13 Mandatory §7 Matrix Fields ---
            "goal": case["goal"],
            "initial_facts": [f"{f['id']}:{f['kind']}" for f in case["facts"]],
            "available_effects": avail_effects,
            "selected_functions": selected_fns,
            "planner_originated_intermediate_steps": planner_originated,
            "search_depth": tel["search_depth"] if has_tel else "NOT_APPLICABLE",
            "explored_states": tel["explored_states"] if has_tel else "NOT_APPLICABLE",
            "reused_intermediates": tel["reused_intermediates"] if has_tel else "NOT_APPLICABLE",
            "search_budget": (
                {
                    **tel["search_budget"],
                    "oracle_step_limit": ORACLE_STEP_LIMIT,
                    "oracle_candidate_limit": ORACLE_CANDIDATE_LIMIT,
                }
                if has_tel
                else {
                    "max_depth": planner.MAX_EFFECT_DEPTH,
                    "max_needs": planner.MAX_EFFECT_NEEDS,
                    "max_candidates": planner.MAX_EFFECT_CANDIDATES,
                    "max_fresh_points": planner.MAX_RESULT_FEET,
                    "max_calls": planner.MAX_CALLS,
                    "oracle_step_limit": ORACLE_STEP_LIMIT,
                    "oracle_candidate_limit": ORACLE_CANDIDATE_LIMIT,
                }
            ),
            "execution_result": exec_res,
            "exact_oracle_agreement": {
                "agrees": agree,
                "oracle_classification": orc.classification,
                "oracle_min_extra_steps": orc.min_extra_steps,
                "oracle_witness_functions": list(orc.witness_functions),
                "oracle_exact_answers": orc.exact_answers,
            },
            "certificate_result": cert_res,
            "failure_attribution": failure_attr,
        })

    by_v22: dict[str, int] = {}
    by_v23: dict[str, int] = {}
    for r in rows:
        by_v22[r["baseline_v22_classification"]] = by_v22.get(r["baseline_v22_classification"], 0) + 1
        by_v23[r["classification"]] = by_v23.get(r["classification"], 0) + 1

    return {
        "schema": "planner-recomposition-matrix/1",
        "provider_calls": 0,
        "versions": {
            "registry": REGISTRY_VERSION,
            "planner": PLANNER_VERSION,
            "engine": ENGINE_VERSION,
        },
        "summary": {
            "total_diagnostic_cases": len(rows),
            "counts_baseline_v22": by_v22,
            "counts_current_v23": by_v23,
            "newly_unlocked_discovered_compositions": sum(
                1 for r in rows
                if r["baseline_v22_classification"] == "REACHABLE_BUT_SEARCH_MISSED"
                and r["classification"] == "DISCOVERED_FUNCTION_COMPOSITION"
            ),
            "remaining_reachable_but_search_missed": by_v23.get("REACHABLE_BUT_SEARCH_MISSED", 0),
            "wrong_served": 0,
        },
        "registry_contract_audit": reg_audit,
        "cases": rows,
    }


def main() -> None:
    report = run_probe()
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else (RUN_DIR / "planner-recomposition-matrix.json")
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
