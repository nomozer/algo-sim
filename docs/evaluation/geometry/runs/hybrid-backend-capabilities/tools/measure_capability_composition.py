# -*- coding: utf-8 -*-
"""Deterministic telemetry and performance profiler for `hybrid-backend-capabilities`.

Zero live Gemini API calls (`ALLOW_LIVE_AI=0`).
"""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import tracemalloc
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"

ROOT = Path(__file__).resolve().parents[6]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(BACKEND / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND / "scripts"))
if str(BACKEND / "tests" / "geometry") not in sys.path:
    sys.path.insert(0, str(BACKEND / "tests" / "geometry"))

from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline
from app.ai.typed_fact_next_extraction import (
    ReplayExtractor,
    _normalize_transport_payload,
    extract_typed_fact_next_v2,
)
from app.simulation.geometry_functions import engine, planner, registry
import run_s2_student_language_pilot as pilot
import test_hybrid_capability_composition as comp_tests

PREVIEW_POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})
RUN_DIR = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-backend-capabilities"
RESULTS_DIR = RUN_DIR / "results"
LIVE_C26_DIR = ROOT / "docs" / "evaluation" / "geometry" / "runs" / "hybrid-live-extraction-retest"


def _quantile(vals: list[float], q: float) -> float:
    if not vals:
        return 0.0
    s = sorted(vals)
    idx = min(len(s) - 1, max(0, int(round((len(s) - 1) * q))))
    return round(s[idx], 3)


def _profile_case(name: str, text: str, raw_payload: dict[str, Any]) -> dict[str, Any]:
    normed = _normalize_transport_payload(deepcopy(raw_payload))
    tracemalloc.start()
    t0_wall = time.perf_counter()
    t0_cpu = time.process_time()

    s1_t0 = time.perf_counter()
    ext = extract_typed_fact_next_v2(text, ReplayExtractor({text: normed}))
    s1_ms = (time.perf_counter() - s1_t0) * 1000.0

    s2_t0 = time.perf_counter()
    out = run_hybrid_offline(text, ReplayExtractor({text: normed}), policy=PREVIEW_POLICY)
    s2_ms = (time.perf_counter() - s2_t0) * 1000.0

    wall_ms = (time.perf_counter() - t0_wall) * 1000.0
    cpu_ms = (time.process_time() - t0_cpu) * 1000.0
    _, peak_bytes = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    route = out.response["route_d"]
    env = out.response["envelope"]
    tel = (route.get("planner") or {}).get("search_telemetry") or {}
    aux = (route.get("planner") or {}).get("auxiliary") or []
    normal_subgoals = [
        sg
        for d in aux
        if isinstance(d, dict) and isinstance(d.get("search"), dict)
        for sg in d["search"].get("subgoals") or ()
    ]
    return {
        "case_id": name,
        "status": route["status"],
        "envelope_status": env.get("status"),
        "reason_code": env.get("reason_code") or (route.get("refusal") or {}).get("code"),
        "extraction_code": ext.code,
        "answers": {k: v["coef"] for k, v in (route.get("answer_exact") or {}).items()},
        "certificate_verified": (out.receipt.get("engine") or {}).get("status") == "VERIFIED",
        "search_telemetry": {
            "classification": tel.get("classification"),
            "explored_states": tel.get("explored_states", 0),
            "candidate_evaluations": tel.get("candidate_evaluations", 0),
            "max_depth_reached": tel.get("max_depth_reached", 0),
            "pruned_nodes": len(tel.get("rejected_candidates") or ()),
            "reused_intermediates": tel.get("reused_intermediates", 0),
            "planner_originated_steps": len(tel.get("planner_originated_steps") or ()),
            "source_defined_steps": len(tel.get("source_defined_steps") or ()),
            "registered_decomposition_steps": len(tel.get("registered_decomposition_steps") or ()),
            "search_generated_steps": len(tel.get("search_generated_steps") or ()),
            "normal_subgoals": [
                {
                    "need": sg.get("need"),
                    "candidates": sg.get("candidates"),
                    "rejected_count": len(sg.get("rejected") or ()),
                    "rejected_points": [r.get("point") for r in sg.get("rejected") or ()],
                    "selected_point": (sg.get("selected") or {}).get("point"),
                }
                for sg in normal_subgoals
            ],
        },
        "performance": {
            "wall_ms": round(wall_ms, 3),
            "extraction_validation_ms": round(s1_ms, 3),
            "route_and_adapter_ms": round(s2_ms, 3),
            "cpu_ms": round(cpu_ms, 3),
            "peak_memory_kb": round(peak_bytes / 1024.0, 2),
        },
    }


def _evaluate_c26_study(study: str, jsonl_name: str) -> dict[str, Any]:
    specs = pilot.default_c21_pilot_specs()
    cpath = Path(specs[study]["corpus_path"])
    corpus = json.loads(cpath.read_text(encoding="utf-8"))
    raw_by_id: dict[str, dict[str, Any]] = {}
    for phase in ("full", "canary"):
        jpath = LIVE_C26_DIR / phase / jsonl_name
        if not jpath.is_file():
            continue
        for line in jpath.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("type") == "row" and row.get("case_id") not in raw_by_id:
                raw_by_id[row["case_id"]] = row["raw_extraction"]

    rows = []
    latencies_ms = []
    positive_total = 0
    positive_served_oracle_exact = 0
    negative_total = 0
    negative_refused_or_clarified = 0
    wrong_served = 0

    for case in corpus["cases"]:
        cid = case["id"]
        raw = _normalize_transport_payload(deepcopy(raw_by_id[cid]))
        t0 = time.perf_counter()
        observed, extra = pilot.observe(
            case["problem_text"],
            ReplayExtractor({case["problem_text"]: raw}),
        )
        lat_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(lat_ms)
        expected = pilot.expected_record(case)
        gold = case.get("gold_extraction")
        gold_obs, gold_extra = pilot.observe(
            case["problem_text"],
            ReplayExtractor({case["problem_text"]: gold} if gold else {}),
        )
        row = {
            "case_id": cid,
            "stratum": case.get("stratum"),
            "technical_failure": False,
            "expected": expected,
            "observed": observed,
            **extra,
        }
        row["end_to_end_status_only"] = pilot.end_to_end_correct(expected, observed)
        row["reason_verified"] = pilot.reason_verified(
            row, gold_extra.get("hybrid_code"), gold, case["problem_text"]
        )
        row["end_to_end_correct"] = (
            row["end_to_end_status_only"]
            if expected["outcome"] == "SERVED" or not row["end_to_end_status_only"]
            else row["reason_verified"] is True
        )
        row["hybrid_outcome"] = pilot.hybrid_outcome(row)

        if expected["outcome"] == "SERVED":
            positive_total += 1
            if (
                observed.get("status") == "SERVED"
                and observed.get("certificate_verified") is True
                and observed.get("answers") == expected.get("expected_answers")
            ):
                positive_served_oracle_exact += 1
            elif observed.get("status") == "SERVED":
                wrong_served += 1
        else:
            negative_total += 1
            if observed.get("status") in ("REFUSED", "CLARIFY"):
                negative_refused_or_clarified += 1
            elif observed.get("status") == "SERVED":
                wrong_served += 1

        rows.append(
            {
                "case_id": cid,
                "expected_outcome": expected["outcome"],
                "observed_status": observed.get("status"),
                "hybrid_code": extra.get("hybrid_code"),
                "end_to_end_correct": row["end_to_end_correct"],
                "reason_verified": row["reason_verified"],
                "hybrid_outcome": row["hybrid_outcome"],
                "latency_ms": round(lat_ms, 3),
            }
        )

    outcomes: dict[str, int] = {}
    for r in rows:
        outcomes[r["hybrid_outcome"]] = outcomes.get(r["hybrid_outcome"], 0) + 1
    return {
        "study": study,
        "cases_total": len(rows),
        "positive_served_oracle_exact": {
            "numerator": positive_served_oracle_exact,
            "denominator": positive_total,
        },
        "negative_refused_or_clarified": {
            "numerator": negative_refused_or_clarified,
            "denominator": negative_total,
        },
        "wrong_served": wrong_served,
        "strict_gold_projection_correct": sum(1 for r in rows if r["end_to_end_correct"]),
        "outcomes": outcomes,
        "latency_p50_ms": _quantile(latencies_ms, 0.5),
        "latency_p95_ms": _quantile(latencies_ms, 0.95),
        "clarify_cases": [r for r in rows if r["expected_outcome"] == "CLARIFY"],
    }


def _composition_probe_cases() -> list[dict[str, Any]]:
    # Case 1
    q_vol = "Tính thể tích khối chóp S.ABCD"
    q_dist = "khoảng cách từ A đến mặt phẳng (SBC)"
    t1 = f"{comp_tests.BASE_PYRAMID_TEXT}{q_vol} và {q_dist}."
    p1 = {
        "schema_version": "typed-fact-next/2",
        "problem_text": t1,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": deepcopy(comp_tests.BASE_PYRAMID_PREMISES),
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {"goal_id": "g_vol", "kind": "measurement", "goal_type": "volume", "solid_id": "s1", "target": {"solid_id": "s1"}, "quote": q_vol},
            {"goal_id": "g_dist", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"point": "A", "plane": ["S", "B", "C"]}, "quote": q_dist},
        ],
    }

    # Case 2
    q2_dist = "Tính khoảng cách từ A đến đường thẳng SB"
    t2 = f"{comp_tests.BASE_PYRAMID_TEXT}{q2_dist}."
    p2 = {
        "schema_version": "typed-fact-next/2",
        "problem_text": t2,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": deepcopy(comp_tests.BASE_PYRAMID_PREMISES),
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {"goal_id": "g1", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"point": "A", "line": ["S", "B"]}, "quote": q2_dist}
        ],
    }

    # Case 3a
    q3a_1 = "Tính khoảng cách từ trực tâm của tam giác CDM đến mặt phẳng (SAB)"
    q3a_2 = "Tính khoảng cách từ tâm đường tròn ngoại tiếp tam giác CDM đến mặt phẳng (SAB)"
    t3a = f"{comp_tests.BASE_PYRAMID_TEXT}Gọi M là trung điểm của AB. {q3a_1}. {q3a_2}."
    p3a = {
        "schema_version": "typed-fact-next/2",
        "problem_text": t3a,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": [
            *deepcopy(comp_tests.BASE_PYRAMID_PREMISES),
            {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"},
        ],
        "described_points": [
            {"described_id": "h1", "kind": "orthocenter", "polygon": ["C", "D", "M"], "quote": "trực tâm của tam giác CDM"},
            {"described_id": "o1", "kind": "circumcenter", "polygon": ["C", "D", "M"], "quote": "tâm đường tròn ngoại tiếp tam giác CDM"},
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [
            {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"point": "@h1", "plane": ["S", "A", "B"]}, "quote": q3a_1},
            {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"point": "@o1", "plane": ["S", "A", "B"]}, "quote": q3a_2},
        ],
    }

    # Case 3b
    q3b_1 = "Tính khoảng cách từ trực tâm của tam giác BC'M đến mặt phẳng (ABC)"
    q3b_2 = "Tính khoảng cách từ tâm đường tròn ngoại tiếp tam giác BC'M đến mặt phẳng (ABC)"
    t3b = (
        "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4 và AA' = 2. "
        "Gọi M là trung điểm của BC. Gọi N là trung điểm của A'B'. "
        f"{q3b_1}. {q3b_2}."
    )
    p3b = {
        "schema_version": "typed-fact-next/2",
        "problem_text": t3b,
        "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "prism", "notation": "ABC.A'B'C'", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}],
        "premises": [
            {"kind": "right_prism", "args": {"base": ["A", "B", "C"], "top": ["A'", "B'", "C'"]}, "quote": "Cho hình lăng trụ đứng ABC.A'B'C'", "solid_id": "s1"},
            {"kind": "right_angle", "args": {"vertex": "A", "rays": ["B", "C"]}, "quote": "đáy ABC là tam giác vuông tại A", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "B"], "value": "3"}, "quote": "AB = 3", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "C"], "value": "4"}, "quote": "AC = 4", "solid_id": "s1"},
            {"kind": "segment_length", "args": {"segment": ["A", "A'"], "value": "2"}, "quote": "AA' = 2", "solid_id": "s1"},
            {"kind": "midpoint", "args": {"point": "M", "segment": ["B", "C"]}, "quote": "Gọi M là trung điểm của BC", "solid_id": "s1"},
            {"kind": "midpoint", "args": {"point": "N", "segment": ["A'", "B'"]}, "quote": "Gọi N là trung điểm của A'B'", "solid_id": "s1"},
        ],
        "described_points": [
            {"described_id": "h1", "kind": "orthocenter", "polygon": ["B", "C'", "M"], "quote": "trực tâm của tam giác BC'M"},
            {"described_id": "o1", "kind": "circumcenter", "polygon": ["B", "C'", "M"], "quote": "tâm đường tròn ngoại tiếp tam giác BC'M"},
        ],
        "relations": [],
        "derived_sections": [],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình lăng trụ đứng ABC.A'B'C'"}],
        "math_goals": [
            {"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"point": "@h1", "plane": ["A", "B", "C"]}, "quote": q3b_1},
            {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "solid_id": "s1", "target": {"point": "@o1", "plane": ["A", "B", "C"]}, "quote": q3b_2},
        ],
    }

    return [
        _profile_case("Case1_Direct_Primitive", t1, p1),
        _profile_case("Case2_TwoStep_PointToLine", t2, p2),
        _profile_case("Case3a_Pyramid_MultiGoal_SharedFoot", t3a, p3a),
        _profile_case("Case3b_Prism_MultiGoal_SharedFoot", t3b, p3b),
    ]


def main() -> int:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    composition_cases = _composition_probe_cases()

    gap1_cases = []
    for name, extra_s, extra_p, through, perp in [
        (
            "Gap1A_divide_segment_on_AB",
            "Lấy điểm M trên cạnh AB sao cho AM = 1/3 AB",
            {"kind": "divide_segment", "args": {"point": "M", "segment": ["A", "B"], "ratio": "1/3"}, "quote": "Lấy điểm M trên cạnh AB sao cho AM = 1/3 AB", "solid_id": "s1"},
            ["S", "N"],
            ["S", "A", "M"],
        ),
        (
            "Gap1B_centroid_on_SAB",
            "Gọi G là trọng tâm tam giác SAB",
            {"kind": "centroid", "args": {"point": "G", "polygon": ["S", "A", "B"]}, "quote": "Gọi G là trọng tâm tam giác SAB", "solid_id": "s1"},
            ["S", "N"],
            ["S", "A", "G"],
        ),
        (
            "Gap1C_projection_on_SB",
            "Gọi H là hình chiếu vuông góc của A lên đường thẳng SB",
            {"kind": "orthogonal_projection_line", "args": {"point": "A", "line": ["S", "B"], "image": "H"}, "quote": "Gọi H là hình chiếu vuông góc của A lên đường thẳng SB", "solid_id": "s1"},
            ["S", "N"],
            ["S", "A", "H"],
        ),
        (
            "Gap1D_intersection_on_AC_BD",
            "Gọi O là giao điểm của AC và BD",
            {"kind": "intersect_line_line", "args": {"point": "O", "line1": ["A", "C"], "line2": ["B", "D"]}, "quote": "Gọi O là giao điểm của AC và BD", "solid_id": "s1"},
            ["S", "N"],
            ["S", "C", "O"],
        ),
    ]:
        txt, pld = comp_tests._constrained_section_case(extra_p, extra_s, through, perp)
        gap1_cases.append(_profile_case(name, txt, pld))

    c26_k1 = _evaluate_c26_study("K-1", "k1-live.jsonl")
    c26_s2 = _evaluate_c26_study("S-2", "s2-live.jsonl")
    c26_r1 = _evaluate_c26_study("R-1", "r1-live.jsonl")

    specs = pilot.default_c21_pilot_specs()
    gold_summary = {}
    with tempfile.TemporaryDirectory() as tmpd:
        for study in ("K-1", "S-2", "R-1"):
            out = pilot.evaluate(Path(specs[study]["corpus_path"]), Path(tmpd) / f"{study}.jsonl", None)
            sup = out["supplementary"]
            gold_summary[study] = {
                "end_to_end_correct": sup["end_to_end_correct"],
                "hybrid_outcomes": sup["hybrid_outcomes"],
            }

    all_profiled = [*composition_cases, *gap1_cases]
    all_wall = [c["performance"]["wall_ms"] for c in all_profiled]
    all_cpu = [c["performance"]["cpu_ms"] for c in all_profiled]
    all_mem = [c["performance"]["peak_memory_kb"] for c in all_profiled]
    warm_wall = [c["performance"]["wall_ms"] for c in all_profiled[1:]]
    warm_cpu = [c["performance"]["cpu_ms"] for c in all_profiled[1:]]
    warm_mem = [c["performance"]["peak_memory_kb"] for c in all_profiled[1:]]

    from scripts import freeze_evaluation_candidate as freeze_cand

    measured_entries = freeze_cand._measured_system_files()
    unique_measured = sorted({p.resolve() for p in measured_entries})
    backend_app_files = [
        p for p in unique_measured
        if p.relative_to(ROOT).as_posix().startswith("backend/app/")
    ]
    frontend_semantic_files = [
        p for p in unique_measured
        if p.relative_to(ROOT).as_posix().startswith("frontend/src/simulations/domains/semantic/")
    ]
    cand_hash, cand_so_file = freeze_cand.measured_system_hash()

    report_data = {
        "schema": "hybrid-capability-telemetry-metrics/1",
        "live_gemini_requests": 0,
        "versions": {
            "registry": registry.REGISTRY_VERSION,
            "planner": planner.PLANNER_VERSION,
            "engine": engine.ENGINE_VERSION,
        },
        "registry_inventory": {
            "total_registered_functions": len(registry.REGISTRY),
            "provider_offered_true": sum(1 for f in registry.REGISTRY.values() if f.provider_offered),
            "provider_offered_false": sum(1 for f in registry.REGISTRY.values() if not f.provider_offered),
            "auxiliary_only_true": sum(1 for f in registry.REGISTRY.values() if f.auxiliary_only),
            "provider_functions_exposed": len(registry.PROVIDER_FUNCTIONS),
        },
        "candidate_inventory": {
            "measured_system_paths": list(freeze_cand.MEASURED_SYSTEM_PATHS),
            "hashed_entries_so_file": cand_so_file,
            "unique_measured_files": len(unique_measured),
            "backend_app_files": len(backend_app_files),
            "frontend_semantic_files": len(frontend_semantic_files),
            "duplicate_explicit_path": "frontend/src/simulations/domains/semantic/semantic_program.schema.json",
            "measured_system_tree_hash": cand_hash,
        },
        "composition_discriminating_probes": composition_cases,
        "gap1_constrained_plane_coplanarity": {
            "before_fix": {
                "Gap1A_divide_segment_on_AB": {"status": "REFUSED", "reason_code": "ENGINE_SELF_CHECK_FAILED", "rejected_normal_candidates": ["S", "A"], "selected_point": "B"},
                "Gap1B_centroid_on_SAB": {"status": "REFUSED", "reason_code": "ENGINE_SELF_CHECK_FAILED", "rejected_normal_candidates": ["S", "A"], "selected_point": "B"},
                "Gap1C_projection_on_SB": {"status": "REFUSED", "reason_code": "ENGINE_SELF_CHECK_FAILED", "rejected_normal_candidates": ["S", "A"], "selected_point": "B"},
                "Gap1D_intersection_on_AC_BD": {"status": "REFUSED", "reason_code": "ENGINE_SELF_CHECK_FAILED", "rejected_normal_candidates": ["S", "C"], "selected_point": "A"},
            },
            "after_fix": gap1_cases,
        },
        "gap2_c26_clarification_recovery": {
            "before_fix": {
                "S-2_strict_gold_projection_correct": {"numerator": 26, "denominator": 36},
                "S-2_correct_clarification": {"numerator": 0, "denominator": 6},
                "S-2_clarify_status_recovered": {"numerator": 3, "denominator": 6},
                "failing_s2_clarify_cases": [
                    {"case_id": "S2-C-D05_projection_missing_target", "observed_status": "REFUSED", "hybrid_code": "QUOTE_NOT_IN_SOURCE", "hybrid_outcome": "WRONG_REASON_REFUSAL"},
                    {"case_id": "S2-C-C04_angle_plane_missing", "observed_status": "REFUSED", "hybrid_code": "INVALID_MATH_GOAL", "hybrid_outcome": "WRONG_REASON_REFUSAL"},
                    {"case_id": "S2-C-A01_goc_chieu", "observed_status": "CLARIFY", "hybrid_code": "AMBIGUOUS_FACT", "hybrid_outcome": "WRONG_REASON_CLARIFICATION"},
                ],
            },
            "after_fix": {
                "K-1": c26_k1,
                "S-2": c26_s2,
                "R-1": c26_r1,
                "combined_70_positive_served_oracle_exact": {
                    "numerator": c26_k1["positive_served_oracle_exact"]["numerator"] + c26_s2["positive_served_oracle_exact"]["numerator"] + c26_r1["positive_served_oracle_exact"]["numerator"],
                    "denominator": c26_k1["positive_served_oracle_exact"]["denominator"] + c26_s2["positive_served_oracle_exact"]["denominator"] + c26_r1["positive_served_oracle_exact"]["denominator"],
                },
                "combined_70_negative_refused_or_clarified": {
                    "numerator": c26_k1["negative_refused_or_clarified"]["numerator"] + c26_s2["negative_refused_or_clarified"]["numerator"] + c26_r1["negative_refused_or_clarified"]["numerator"],
                    "denominator": c26_k1["negative_refused_or_clarified"]["denominator"] + c26_s2["negative_refused_or_clarified"]["denominator"] + c26_r1["negative_refused_or_clarified"]["denominator"],
                },
                "combined_70_wrong_served": c26_k1["wrong_served"] + c26_s2["wrong_served"] + c26_r1["wrong_served"],
                "S-2_strict_gold_projection_correct": {"numerator": c26_s2["strict_gold_projection_correct"], "denominator": 36},
                "S-2_correct_clarification": {"numerator": c26_s2["outcomes"].get("CORRECT_CLARIFICATION", 0), "denominator": 6},
                "S-2_clarify_status_recovered": {
                    "numerator": sum(1 for r in c26_s2["clarify_cases"] if r["observed_status"] == "CLARIFY"),
                    "denominator": len(c26_s2["clarify_cases"]),
                },
            },
        },
        "gold_replay_verification": gold_summary,
        "performance_summary": {
            "profiled_cases_count": len(all_profiled),
            "cold_start_first_case_wall_ms": all_wall[0] if all_wall else 0.0,
            "cold_start_first_case_peak_memory_kb": all_mem[0] if all_mem else 0.0,
            "warm_steady_state_cases_count": len(warm_wall),
            "warm_wall_p50_ms": _quantile(warm_wall, 0.5),
            "warm_wall_p95_ms": _quantile(warm_wall, 0.95),
            "warm_cpu_p50_ms": _quantile(warm_cpu, 0.5),
            "warm_peak_memory_max_kb": round(max(warm_mem) if warm_mem else 0.0, 2),
            "wall_p50_ms": _quantile(all_wall, 0.5),
            "wall_p95_ms": _quantile(all_wall, 0.95),
            "cpu_p50_ms": _quantile(all_cpu, 0.5),
            "peak_memory_max_kb": round(max(all_mem) if all_mem else 0.0, 2),
        },
    }

    out_path = RESULTS_DIR / "capability_telemetry_metrics.json"
    out_path.write_text(json.dumps(report_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(f"Wrote {out_path.relative_to(ROOT)}")
    print("Positive served oracle exact:", report_data["gap2_c26_clarification_recovery"]["after_fix"]["combined_70_positive_served_oracle_exact"])
    print("Negative refused/clarified:", report_data["gap2_c26_clarification_recovery"]["after_fix"]["combined_70_negative_refused_or_clarified"])
    print("S-2 clarify status recovered:", report_data["gap2_c26_clarification_recovery"]["after_fix"]["S-2_clarify_status_recovered"])
    print("S-2 strict CORRECT_CLARIFICATION:", report_data["gap2_c26_clarification_recovery"]["after_fix"]["S-2_correct_clarification"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
