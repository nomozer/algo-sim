# -*- coding: utf-8 -*-
"""Measure production dynamic function composition telemetry and performance (Section X).

Collects:
- explored_states
- candidate_evaluations
- max_depth_reached (search_depth)
- pruned_nodes
- reused_intermediates
- search_generated_steps
- registered_decomposition_steps
- Planner CPU time (ms)
- Full Hybrid route latency p50 / p95 (ms, cold vs warm)
- Peak traced memory (KiB)
- Refusal / error distribution
"""
from __future__ import annotations

import json
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(ROOT / "backend" / "tests" / "geometry"))

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
from app.simulation.geometry_functions import planner, typed_fact_next as T  # noqa: E402
from app.simulation.geometry_functions.typed_fact_next_bridge import bridge_v2  # noqa: E402
import test_production_dynamic_composition as TPDC  # noqa: E402

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})


def _build_diagnostic_cases() -> list[dict]:
    base_text, premises = TPDC._pyramid_base_premises("2", "3")
    base_text_3, premises_3 = TPDC._pyramid_base_premises("3", "3")
    q_a1 = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    )
    q_a2 = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD) đến đường thẳng AB"
    )
    q_a3 = (
        "Tính khoảng cách từ hình chiếu vuông góc của trung điểm của SC "
        "lên đường thẳng BD đến mặt phẳng (SAB)"
    )
    q_b1_2 = (
        "Tính diện tích tam giác tạo bởi hình chiếu vuông góc của trọng tâm của tam giác SBC "
        "lên mặt phẳng (ABCD), S và A"
    )
    e_quote = "Gọi E là điểm thuộc cạnh SC sao cho SE = 2EC"
    q_c1_1 = (
        "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác EAB "
        "lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    )
    q_c1_2 = (
        "Tính độ dài đoạn thẳng nối hình chiếu vuông góc của trọng tâm của tam giác EAB "
        "lên mặt phẳng (ABCD) với A"
    )
    prism_base = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, "
        "AB = 2, AC = 2, AA' = 3. "
    )
    q_c2_1 = (
        "Tính khoảng cách từ hình chiếu vuông góc của trung điểm của B'C' "
        "lên mặt phẳng (ABC) đến đường thẳng AC"
    )
    q_c2_2 = (
        "Tính khoảng cách từ hình chiếu vuông góc của trung điểm của B'C' "
        "lên mặt phẳng (ABC) đến mặt phẳng (ABB')"
    )
    g_quote = "Gọi G là trọng tâm của tam giác SBC"
    h_quote = "Gọi H là hình chiếu vuông góc của G lên mặt phẳng (ABCD)"
    q_explicit = "Tính khoảng cách từ H đến đường thẳng AB"

    def _pyr_case(cid: str, family: str, text: str, described_points: list[dict], math_goals: list[dict], base_prem=premises):
        return {
            "id": cid,
            "family": family,
            "text": text,
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": text,
                "length_unit": "1",
                "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
                "premises": list(base_prem),
                "relations": [],
                "described_points": described_points,
                "simulation_goals": [
                    {"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}
                ],
                "math_goals": math_goals,
            },
        }

    cases = [
        _pyr_case(
            "A1-centroid-proj-plane-dist",
            "Family A (Sequential 3-step)",
            base_text + q_a1 + ".",
            [
                {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
                {
                    "described_id": "h1",
                    "kind": "orthogonal_projection",
                    "point": "@g1",
                    "plane": ["A", "B", "C", "D"],
                    "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)",
                },
            ],
            [
                {
                    "goal_id": "q1",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {"point": "@h1", "plane": ["S", "A", "D"]},
                    "quote": q_a1,
                    "solid_id": "s1",
                }
            ],
        ),
        _pyr_case(
            "A2-centroid-proj-plane-line-dist",
            "Family A (Sequential 4-step)",
            base_text + q_a2 + ".",
            [
                {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
                {
                    "described_id": "h1",
                    "kind": "orthogonal_projection",
                    "point": "@g1",
                    "plane": ["A", "B", "C", "D"],
                    "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)",
                },
            ],
            [
                {
                    "goal_id": "q1",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {"point": "@h1", "line": ["A", "B"]},
                    "quote": q_a2,
                    "solid_id": "s1",
                }
            ],
        ),
        _pyr_case(
            "A3-midpoint-proj-line-plane-dist",
            "Family A (Sequential Line Proj)",
            base_text + q_a3 + ".",
            [
                {"described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "trung điểm của SC"},
                {
                    "described_id": "h1",
                    "kind": "orthogonal_projection_line",
                    "point": "@m1",
                    "line": ["B", "D"],
                    "quote": "hình chiếu vuông góc của trung điểm của SC lên đường thẳng BD",
                },
            ],
            [
                {
                    "goal_id": "q1",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {"point": "@h1", "plane": ["S", "A", "B"]},
                    "quote": q_a3,
                    "solid_id": "s1",
                }
            ],
        ),
        _pyr_case(
            "B1-shared-intermediate-two-goals",
            "Family B (Shared Intermediates)",
            base_text + q_a2 + ". " + q_b1_2 + ".",
            [
                {"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"},
                {
                    "described_id": "h1",
                    "kind": "orthogonal_projection",
                    "point": "@g1",
                    "plane": ["A", "B", "C", "D"],
                    "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên mặt phẳng (ABCD)",
                },
            ],
            [
                {
                    "goal_id": "q1",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {"point": "@h1", "line": ["A", "B"]},
                    "quote": q_a2,
                    "solid_id": "s1",
                },
                {
                    "goal_id": "q2",
                    "kind": "measurement",
                    "goal_type": "area",
                    "target": {"polygon": ["@h1", "S", "A"]},
                    "quote": q_b1_2,
                    "solid_id": "s1",
                },
            ],
        ),
        _pyr_case(
            "C1-ratio-centroid-proj-multi-goal",
            "Family C (Ratio + Pyramid)",
            base_text_3 + e_quote + ". " + q_c1_1 + ". " + q_c1_2 + ".",
            [
                {"described_id": "g1", "kind": "centroid", "polygon": ["E", "A", "B"], "quote": "trọng tâm của tam giác EAB"},
                {
                    "described_id": "h1",
                    "kind": "orthogonal_projection",
                    "point": "@g1",
                    "plane": ["A", "B", "C", "D"],
                    "quote": "hình chiếu vuông góc của trọng tâm của tam giác EAB lên mặt phẳng (ABCD)",
                },
            ],
            [
                {
                    "goal_id": "q1",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {"point": "@h1", "plane": ["S", "A", "D"]},
                    "quote": q_c1_1,
                    "solid_id": "s1",
                },
                {
                    "goal_id": "q2",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {"segment": ["@h1", "A"]},
                    "quote": q_c1_2,
                    "solid_id": "s1",
                },
            ],
            base_prem=premises_3
            + [{"kind": "divide_segment", "args": {"point": "E", "segment": ["S", "C"], "ratio": "2/3"}, "quote": e_quote, "solid_id": "s1"}],
        ),
        {
            "id": "C2-right-prism-four-step-multi-goal",
            "family": "Family C (Right Prism)",
            "text": prism_base + q_c2_1 + ". " + q_c2_2 + ".",
            "payload": {
                "schema_version": "typed-fact-next/2",
                "problem_text": prism_base + q_c2_1 + ". " + q_c2_2 + ".",
                "length_unit": "1",
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
                        "args": {"vertices": ["A", "B", "C"], "right_at": "A"},
                        "quote": "đáy ABC là tam giác vuông tại A",
                        "solid_id": "s1",
                    },
                    {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "2"}, "quote": "AB = 2", "solid_id": "s1"},
                    {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "2"}, "quote": "AC = 2", "solid_id": "s1"},
                    {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "3"}, "quote": "AA' = 3", "solid_id": "s1"},
                ],
                "relations": [],
                "described_points": [
                    {"described_id": "m1", "kind": "midpoint", "segment": ["B'", "C'"], "quote": "trung điểm của B'C'"},
                    {
                        "described_id": "h1",
                        "kind": "orthogonal_projection",
                        "point": "@m1",
                        "plane": ["A", "B", "C"],
                        "quote": "hình chiếu vuông góc của trung điểm của B'C' lên mặt phẳng (ABC)",
                    },
                ],
                "simulation_goals": [
                    {
                        "goal_id": "sg1",
                        "kind": "construct_object",
                        "target_solid_id": "s1",
                        "quote": "Cho hình lăng trụ đứng ABC.A'B'C'",
                    }
                ],
                "math_goals": [
                    {
                        "goal_id": "q1",
                        "kind": "measurement",
                        "goal_type": "distance",
                        "target": {"point": "@h1", "line": ["A", "C"]},
                        "quote": q_c2_1,
                        "solid_id": "s1",
                    },
                    {
                        "goal_id": "q2",
                        "kind": "measurement",
                        "goal_type": "distance",
                        "target": {"point": "@h1", "plane": ["A", "B", "B'"]},
                        "quote": q_c2_2,
                        "solid_id": "s1",
                    },
                ],
            },
        },
        _pyr_case(
            "Ablation-Control-Explicit-Premises",
            "Section VII Control (Explicit G, H)",
            base_text + g_quote + ". " + h_quote + ". " + q_explicit + ".",
            [],
            [
                {
                    "goal_id": "q1",
                    "kind": "measurement",
                    "goal_type": "distance",
                    "target": {"point": "H", "line": ["A", "B"]},
                    "quote": q_explicit,
                    "solid_id": "s1",
                }
            ],
            base_prem=premises
            + [
                {"kind": "centroid", "args": {"point": "G", "polygon": ["S", "B", "C"]}, "quote": g_quote, "solid_id": "s1"},
                {
                    "kind": "orthogonal_projection",
                    "args": {"point": "G", "plane": ["A", "B", "C", "D"], "image": "H"},
                    "quote": h_quote,
                    "solid_id": "s1",
                },
            ],
        ),
    ]
    return cases


def main() -> None:
    cases = _build_diagnostic_cases()
    rows = []
    planner_times_ms = []
    cold_route_times_ms = []
    warm_route_times_ms = []
    peak_kib_list = []

    for c in cases:
        text, payload = c["text"], c["payload"]
        parsed = T._parse(T.TypedFactNextPayloadV2, payload)
        bridged = bridge_v2(parsed)

        # Planner-only CPU time
        t0 = time.perf_counter()
        plan = planner.lap_ke_hoach(bridged, text)
        t_plan_ms = (time.perf_counter() - t0) * 1000.0
        planner_times_ms.append(t_plan_ms)

        # Cold route + peak memory
        tracemalloc.start()
        t_c0 = time.perf_counter()
        out_cold = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
        t_cold_ms = (time.perf_counter() - t_c0) * 1000.0
        _, peak_bytes = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        cold_route_times_ms.append(t_cold_ms)
        peak_kib_list.append(peak_bytes / 1024.0)

        # Warm route (3 iterations median)
        w_samples = []
        for _ in range(3):
            tw0 = time.perf_counter()
            run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
            w_samples.append((time.perf_counter() - tw0) * 1000.0)
        t_warm_ms = statistics.median(w_samples)
        warm_route_times_ms.append(t_warm_ms)

        route = out_cold.response["route_d"]
        tel = route["planner"]["search_telemetry"]
        rows.append(
            {
                "id": c["id"],
                "family": c["family"],
                "status": route["status"],
                "answers": {k: v.get("coef") for k, v in (route.get("answer_exact") or {}).items()},
                "classification": tel["classification"],
                "explored_states": tel["explored_states"],
                "candidate_evaluations": tel["candidate_evaluations"],
                "max_depth_reached": tel["search_depth"],
                "pruned_nodes": len(plan.resolver.rejected),
                "reused_intermediates": tel["reused_intermediates"],
                "search_generated_steps": tel["search_generated_steps"],
                "registered_decomposition_steps": tel["registered_decomposition_steps"],
                "source_defined_steps": tel["source_defined_steps"],
                "planner_cpu_ms": round(t_plan_ms, 3),
                "route_cold_ms": round(t_cold_ms, 3),
                "route_warm_ms": round(t_warm_ms, 3),
                "peak_memory_kib": round(peak_bytes / 1024.0, 2),
                "plan_calls": [call["fn"] for call in plan.calls],
            }
        )

    summary = {
        "schema": "production-dynamic-composition-metrics/1",
        "case_count": len(rows),
        "planner_cpu_ms": {
            "p50": round(statistics.median(planner_times_ms), 3),
            "max": round(max(planner_times_ms), 3),
        },
        "route_cold_ms": {
            "p50": round(statistics.median(cold_route_times_ms), 3),
            "p95": round(max(cold_route_times_ms), 3),
        },
        "route_warm_ms": {
            "p50": round(statistics.median(warm_route_times_ms), 3),
            "p95": round(max(warm_route_times_ms), 3),
        },
        "peak_memory_kib_max": round(max(peak_kib_list), 2),
        "cases": rows,
    }
    out_path = ROOT / "docs/evaluation/geometry/runs/hybrid-production-composition/results/production_composition_metrics.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("WROTE", out_path)


if __name__ == "__main__":
    main()
