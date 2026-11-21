# -*- coding: utf-8 -*-
"""Measure Goal-Driven Planner & Generalization Verification telemetry and performance (Section XI).

Measures before (baseline candidate feat/hybrid-production-composition) and after
(feat/hybrid-goal-driven-planner) across Phase 0.1 and Families A–E:
- Planner CPU time (p50, p95, max in ms)
- Exact Kernel execution time (p50, p95, max in ms)
- Total offline route time (p50, p95, max in ms, cold & warm)
- Search telemetry: explored_states, candidate_evaluations, candidate_count,
  pruned_nodes, rejection_reasons, selected_plan, plan_cost, reused_intermediates,
  search_depth, plan_length, classification
"""
from __future__ import annotations

import json
import math
import os
import statistics
import subprocess
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
BACKEND_ROOT = Path(os.environ.get("BENCHMARK_BACKEND_ROOT", str(ROOT / "backend")))
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.insert(0, str(ROOT / "backend" / "tests" / "geometry"))

from app.ai.function_route import run_fact_route  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
from app.simulation.geometry_functions import TuChoi, engine, planner, typed_fact_next as T  # noqa: E402
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2  # noqa: E402

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})


def _pyramid_base_premises(side: str = "2", height: str = "2") -> tuple[str, list[dict]]:
    base_text = (
        f"Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh {side}, "
        f"cạnh bên SA vuông góc với mặt phẳng (ABCD) và SA = {height}. "
    )
    premises = [
        {
            "kind": "regular_polygon",
            "args": {"vertices": ["A", "B", "C", "D"], "side": side},
            "quote": f"đáy ABCD là hình vuông cạnh {side}",
            "solid_id": "s1",
        },
        {
            "kind": "line_perp_plane",
            "args": {"line": ["S", "A"], "plane": ["A", "B", "C", "D"]},
            "quote": "cạnh bên SA vuông góc với mặt phẳng (ABCD)",
            "solid_id": "s1",
        },
        {
            "kind": "segment_length",
            "args": {"segment": ["S", "A"], "value": height},
            "quote": f"SA = {height}",
            "solid_id": "s1",
        },
    ]
    return base_text, premises


def _percentile(sorted_vals: list[float], pct: float) -> float:
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return round(sorted_vals[0], 3)
    idx = min(len(sorted_vals) - 1, max(0, math.ceil((pct / 100.0) * len(sorted_vals)) - 1))
    return round(sorted_vals[idx], 3)


def _stats(vals: list[float]) -> dict[str, float]:
    if not vals:
        return {"p50": 0.0, "p95": 0.0, "max": 0.0}
    s = sorted(vals)
    return {
        "p50": round(statistics.median(s), 3),
        "p95": _percentile(s, 95.0),
        "max": round(max(s), 3),
    }


def build_benchmark_cases() -> list[dict]:
    base_text, premises = _pyramid_base_premises("2", "2")
    base_2_3, prem_2_3 = _pyramid_base_premises("2", "3")

    q0_plane = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác ABC lên mặt phẳng (ABCD) đến mặt phẳng (SBC)"
    q0_seg = "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của trọng tâm của tam giác ABC lên mặt phẳng (ABCD) với S"
    t_phase0 = base_text + q0_plane + ". " + q0_seg + "."

    q_a1 = "Tính khoảng cách từ A đến đường thẳng SB"
    t_a1 = base_2_3 + q_a1 + "."

    t_a2 = (
        "Cho hình chóp S.ABCD. Đáy ABCD là hình vuông cạnh 2. SA vuông góc với (ABCD). SA = 3. "
        "Tìm giao tuyến của (SAD) và (SBC). Tính khoảng cách từ A đến giao tuyến của (SAD) và (SBC)."
    )

    prem_mn = [
        *premises,
        {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"},
        {"kind": "midpoint", "args": {"point": "N", "segment": ["C", "D"]}, "quote": "Gọi N là trung điểm của CD", "solid_id": "s1"},
    ]
    sec_a3 = "Mặt phẳng (P) đi qua M, N và vuông góc với (SBC)"
    ask_sec = "Xác định thiết diện của hình chóp S.ABCD cắt bởi (P) và tính diện tích thiết diện đó"
    t_a3 = base_text + "Gọi M là trung điểm của AB. Gọi N là trung điểm của CD. " + sec_a3 + ". " + ask_sec + "."

    q_b1 = "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBC với A"
    t_b1 = base_text + q_b1 + "."

    q_b2 = "Tính độ dài đoạn thẳng nối tâm đường tròn ngoại tiếp tam giác SBC với A"
    t_b2 = base_text + q_b2 + "."

    sec_b3a = "Mặt phẳng (P) đi qua M, N và vuông góc với (ANB)"
    t_b3a = base_text + "Gọi M là trung điểm của AB. Gọi N là trung điểm của CD. " + sec_b3a + ". " + ask_sec + "."

    k_quote = "Gọi K là hình chiếu vuông góc của A lên mặt phẳng (SBC)"
    t_b3b = (
        base_text
        + "Gọi M là trung điểm của AB. Gọi N là trung điểm của CD. "
        + k_quote + ". " + sec_a3 + ". " + ask_sec + "."
    )

    q_d1 = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    q_d2 = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD) đến đường thẳng AB"
    q_d3 = "Tính diện tích tam giác tạo bởi hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD), S và A"
    t_d = base_2_3 + q_d1 + ". " + q_d2 + ". " + q_d3 + "."

    q_e9 = "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của trung điểm của AB lên mặt phẳng (ABCD) với M"
    t_e9 = base_text + "Gọi M là trung điểm của AB. " + q_e9 + "."

    return [
        {
            "id": "Phase0.1-in-plane-projection",
            "family": "Phase 0.1 (In-Plane Projection)",
            "mode": "hybrid",
            "text": t_phase0,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": t_phase0,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": premises,
                "relations": [],
                "described_points": [
                    {"described_id": "g1", "kind": "centroid", "polygon": ["A", "B", "C"], "quote": "trọng tâm của tam giác ABC"},
                    {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác ABC lên mặt phẳng (ABCD)"},
                ],
                "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
                "math_goals": [
                    {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "plane": ["S", "B", "C"]}, "quote": q0_plane, "solid_id": "s1"},
                    {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@h1", "S"]}, "quote": q0_seg, "solid_id": "s1"},
                ],
            },
        },
        {
            "id": "A1-goal-only-point-line-distance",
            "family": "Family A (Level 3 Goal-Only Foot)",
            "mode": "hybrid",
            "text": t_a1,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": t_a1,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": prem_2_3,
                "relations": [],
                "described_points": [],
                "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
                "math_goals": [
                    {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "line": ["S", "B"]}, "quote": q_a1, "solid_id": "s1"},
                ],
            },
        },
        {
            "id": "A2-goal-only-intersection-line-distance",
            "family": "Family A (Level 3 2-Step Line+Foot)",
            "mode": "fact_route",
            "text": t_a2,
            "payload": {
                "facts": [
                    {"id": "f1", "kind": "solid", "role": "premise", "quotes": ["Cho hình chóp S.ABCD."], "solid": "S.ABCD", "solid_type": "pyramid"},
                    {"id": "f2", "kind": "polygon_shape", "role": "premise", "quotes": ["Đáy ABCD là hình vuông cạnh 2."], "points": ["A", "B", "C", "D"], "shape": "square", "value": "2"},
                    {"id": "f3", "kind": "perpendicular", "role": "premise", "quotes": ["SA vuông góc với (ABCD)."], "points_a": ["S", "A"], "points_b": ["A", "B", "C", "D"]},
                    {"id": "f4", "kind": "length", "role": "premise", "quotes": ["SA = 3."], "points": ["S", "A"], "measure": "segment", "value": "3"},
                    {"id": "g", "kind": "intersection_line", "role": "premise", "quotes": ["Tìm giao tuyến của (SAD) và (SBC)."], "points_a": ["S", "A", "D"], "points_b": ["S", "B", "C"]},
                    {"id": "q1", "kind": "question", "role": "question", "quotes": ["Tính khoảng cách từ A đến giao tuyến của (SAD) và (SBC)."], "quantity": "distance", "points_a": ["A"], "line_ref": "g"},
                ]
            },
        },
        {
            "id": "A3-goal-only-constrained-plane-section",
            "family": "Family A (Level 3 Plane+Section)",
            "mode": "hybrid",
            "text": t_a3,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": t_a3,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": prem_mn,
                "relations": [],
                "derived_sections": [
                    {
                        "section_id": "sec1",
                        "plane_name": "P",
                        "target_solid_id": "s1",
                        "quote": sec_a3,
                        "plane_kind": "constrained",
                        "constraints": [
                            {"kind": "contains_points", "operands": ["M", "N"]},
                            {"kind": "perpendicular_to_plane", "operands": ["S", "B", "C"]},
                        ],
                        "stated_intersections": [],
                    }
                ],
                "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
                "math_goals": [
                    {"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": ask_sec, "solid_id": "s1"},
                ],
            },
        },
        {
            "id": "B1-competing-perpline-orthocenter",
            "family": "Family B (Competing PerpLine Plans)",
            "mode": "hybrid",
            "text": t_b1,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": t_b1,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": premises,
                "relations": [],
                "described_points": [
                    {"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "C"], "quote": "trực tâm của tam giác SBC"},
                ],
                "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
                "math_goals": [
                    {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@o1", "A"]}, "quote": q_b1, "solid_id": "s1"},
                ],
            },
        },
        {
            "id": "B2-competing-perpline-circumcenter",
            "family": "Family B (Precondition Pruning)",
            "mode": "hybrid",
            "text": t_b2,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": t_b2,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": premises,
                "relations": [],
                "described_points": [
                    {"described_id": "c1", "kind": "circumcenter", "polygon": ["S", "B", "C"], "quote": "tâm đường tròn ngoại tiếp tam giác SBC"},
                ],
                "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
                "math_goals": [
                    {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@c1", "A"]}, "quote": q_b2, "solid_id": "s1"},
                ],
            },
        },
        {
            "id": "B3a-competing-normal-premise-plane-equiv",
            "family": "Family B (Competing Normal Premise Cost 0)",
            "mode": "hybrid",
            "text": t_b3a,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": t_b3a,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": prem_mn,
                "relations": [],
                "derived_sections": [
                    {
                        "section_id": "sec1",
                        "plane_name": "P",
                        "target_solid_id": "s1",
                        "quote": sec_b3a,
                        "plane_kind": "constrained",
                        "constraints": [
                            {"kind": "contains_points", "operands": ["M", "N"]},
                            {"kind": "perpendicular_to_plane", "operands": ["A", "N", "B"]},
                        ],
                        "stated_intersections": [],
                    }
                ],
                "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
                "math_goals": [
                    {"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": ask_sec, "solid_id": "s1"},
                ],
            },
        },
        {
            "id": "B3b-competing-normal-reuses-existing-projection",
            "family": "Family B (Competing Normal Reuse Cost 0)",
            "mode": "hybrid",
            "text": t_b3b,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": t_b3b,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": prem_mn + [
                    {"kind": "orthogonal_projection", "args": {"point": "A", "plane": ["S", "B", "C"], "image": "K"}, "quote": k_quote, "solid_id": "s1"},
                ],
                "relations": [],
                "derived_sections": [
                    {
                        "section_id": "sec1",
                        "plane_name": "P",
                        "target_solid_id": "s1",
                        "quote": sec_a3,
                        "plane_kind": "constrained",
                        "constraints": [
                            {"kind": "contains_points", "operands": ["M", "N"]},
                            {"kind": "perpendicular_to_plane", "operands": ["S", "B", "C"]},
                        ],
                        "stated_intersections": [],
                    }
                ],
                "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
                "math_goals": [
                    {"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": ask_sec, "solid_id": "s1"},
                ],
            },
        },
        {
            "id": "D-shared-intermediates-three-goals",
            "family": "Family D (Shared Intermediates Across 3 Goals)",
            "mode": "hybrid",
            "text": t_d,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": t_d,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": prem_2_3,
                "relations": [],
                "described_points": [
                    {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
                    {"described_id": "h1", "kind": "orthogonal_projection", "point": "@g1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)"},
                ],
                "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
                "math_goals": [
                    {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "plane": ["S", "A", "D"]}, "quote": q_d1, "solid_id": "s1"},
                    {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "line": ["A", "B"]}, "quote": q_d2, "solid_id": "s1"},
                    {"goal_id": "q3", "kind": "measurement", "goal_type": "area", "target": {"polygon": ["@h1", "S", "A"]}, "quote": q_d3, "solid_id": "s1"},
                ],
            },
        },
        {
            "id": "E9-degenerate-coinciding-projection-segment",
            "family": "Family E (Degenerate Segment Refusal)",
            "mode": "hybrid",
            "text": t_e9,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": t_e9,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": [
                    *premises,
                    {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"},
                ],
                "relations": [],
                "described_points": [
                    {"described_id": "m1", "kind": "midpoint", "segment": ["A", "B"], "quote": "trung điểm của AB"},
                    {"described_id": "h1", "kind": "orthogonal_projection", "point": "@m1", "plane": ["A", "B", "C", "D"], "quote": "hình chiếu vuông góc của trung điểm của AB lên mặt phẳng (ABCD)"},
                ],
                "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
                "math_goals": [
                    {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@h1", "M"]}, "quote": q_e9, "solid_id": "s1"},
                ],
            },
        },
    ]


def measure_current_worktree() -> dict:
    cases = build_benchmark_cases()
    rows = []
    planner_times_ms = []
    kernel_times_ms = []
    cold_route_times_ms = []
    warm_route_times_ms = []
    peak_kib_list = []

    for c in cases:
        text, payload = c["text"], c["payload"]
        if c["mode"] == "fact_route":
            bridged = payload
        else:
            parsed = T._parse(T.TypedFactNextPayloadV2, payload)
            bridged = bridge_v2(parsed)

        # Planner-only CPU time
        t0 = time.perf_counter()
        try:
            plan = planner.lap_ke_hoach(bridged, text)
            plan_ok = True
        except TuChoi:
            plan = None
            plan_ok = False
        t_plan_ms = (time.perf_counter() - t0) * 1000.0
        planner_times_ms.append(t_plan_ms)

        # Kernel-only CPU time (if plan_ok)
        t_k0 = time.perf_counter()
        if plan_ok and plan is not None:
            doc = tuple(q for g in (*plan.goals, *plan.negated) if g.get("call") for q in g["call"]["source"]["quotes"])
            k_res = engine.dung_tu_loi_goi(
                text,
                {"calls": plan.calls, "named_planes": plan.named_planes},
                tuple(plan.auxiliary),
                doc,
            )
            k_ok = k_res.status == "SERVED"
        else:
            k_ok = False
        t_kernel_ms = (time.perf_counter() - t_k0) * 1000.0
        if plan_ok:
            kernel_times_ms.append(t_kernel_ms)

        # Cold route + peak memory
        tracemalloc.start()
        t_c0 = time.perf_counter()
        if c["mode"] == "fact_route":
            r_fact = run_fact_route(text, payload)
            t_cold_ms = (time.perf_counter() - t_c0) * 1000.0
            _, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            w_samples = []
            for _ in range(3):
                tw0 = time.perf_counter()
                run_fact_route(text, payload)
                w_samples.append((time.perf_counter() - tw0) * 1000.0)
            t_warm_ms = statistics.median(w_samples)
            status = r_fact.status
            reason_code = r_fact.code if r_fact.status != "SERVED" else None
            answers = r_fact.answers or {}
            tel = (r_fact.planner or {}).get("search_telemetry") or {}
        else:
            out_cold = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
            t_cold_ms = (time.perf_counter() - t_c0) * 1000.0
            _, peak_bytes = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            w_samples = []
            for _ in range(3):
                tw0 = time.perf_counter()
                run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
                w_samples.append((time.perf_counter() - tw0) * 1000.0)
            t_warm_ms = statistics.median(w_samples)
            route = out_cold.response["route_d"]
            status = route["status"]
            reason_code = out_cold.response.get("reason_code")
            answers = {k: v.get("coef") for k, v in (route.get("answer_exact") or {}).items()}
            tel = (route.get("planner") or {}).get("search_telemetry") or {}

        cold_route_times_ms.append(t_cold_ms)
        warm_route_times_ms.append(t_warm_ms)
        peak_kib_list.append(peak_bytes / 1024.0)

        rows.append(
            {
                "id": c["id"],
                "family": c["family"],
                "status": status,
                "reason_code": reason_code,
                "answers": answers,
                "classification": tel.get("classification"),
                "explored_states": tel.get("explored_states", 0),
                "candidate_evaluations": tel.get("candidate_evaluations", 0),
                "candidate_count": tel.get("candidate_count", tel.get("candidate_evaluations", 0)),
                "pruned_nodes": tel.get("pruned_nodes", len(plan.resolver.rejected) if plan_ok and plan else 0),
                "rejection_reasons": tel.get("rejection_reasons", {}),
                "selected_plan": tel.get("selected_plan", []),
                "plan_cost": tel.get("plan_cost", 0),
                "reused_intermediates": tel.get("reused_intermediates", 0),
                "search_generated_steps": tel.get("search_generated_steps", 0),
                "registered_decomposition_steps": tel.get("registered_decomposition_steps", 0),
                "source_defined_steps": tel.get("source_defined_steps", 0),
                "search_depth": tel.get("search_depth", 0),
                "plan_length": len(plan.calls) if plan_ok and plan else 0,
                "planner_cpu_ms": round(t_plan_ms, 3),
                "kernel_cpu_ms": round(t_kernel_ms, 3),
                "route_cold_ms": round(t_cold_ms, 3),
                "route_warm_ms": round(t_warm_ms, 3),
                "peak_memory_kib": round(peak_bytes / 1024.0, 2),
                "plan_calls": [call["fn"] for call in plan.calls] if plan_ok and plan else [],
                "kernel_ok": k_ok,
            }
        )

    return {
        "case_count": len(rows),
        "planner_cpu_ms": _stats(planner_times_ms),
        "kernel_cpu_ms": _stats(kernel_times_ms),
        "route_cold_ms": _stats(cold_route_times_ms),
        "route_warm_ms": _stats(warm_route_times_ms),
        "peak_memory_kib_max": round(max(peak_kib_list), 2) if peak_kib_list else 0.0,
        "cases": rows,
    }


def measure_baseline_worktree(baseline_root: Path) -> dict:
    """Run an inline measurement probe against the unmodified baseline worktree."""
    probe_code = """
import json, sys
from pathlib import Path
t_root = Path(sys.argv[1])
sys.path.insert(0, str(t_root / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-goal-driven-planner" / "tools"))
import measure_goal_driven_planning as M
res = M.measure_current_worktree()
print("BASELINE_JSON_START")
print(json.dumps(res, ensure_ascii=False))
"""
    baseline_wt = ROOT.parent / "hybrid-production-composition"
    if not baseline_wt.exists():
        return {"available": False}
    env = {**os.environ, "BENCHMARK_BACKEND_ROOT": str(baseline_wt / "backend"), "PYTHONIOENCODING": "utf-8"}
    proc = subprocess.run(
        [sys.executable, "-c", probe_code, str(ROOT)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env=env,
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Baseline subprocess failed:\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    marker = "BASELINE_JSON_START"
    idx = proc.stdout.find(marker)
    raw = proc.stdout[idx + len(marker) :].strip()
    return json.loads(raw)


def main() -> None:
    after = measure_current_worktree()
    before = measure_baseline_worktree(ROOT.parent / "hybrid-production-composition")
    summary = {
        "schema": "goal-driven-planner-generalization-metrics/1",
        "before_baseline_candidate": before,
        "after_goal_driven_candidate": after,
    }
    out_path = ROOT / "docs/evaluation/geometry/runs/hybrid-goal-driven-planner/results/goal_driven_planning_metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", out_path)


if __name__ == "__main__":
    main()
