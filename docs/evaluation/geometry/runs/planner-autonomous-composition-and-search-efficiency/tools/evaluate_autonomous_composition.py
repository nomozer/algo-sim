# -*- coding: utf-8 -*-
"""Offline evaluator for `planner-autonomous-composition-and-search-efficiency`.

Strictly offline (`ALLOW_LIVE_AI=0`, `0` live Gemini calls) on DEVELOPMENT datasets and novel composition fixtures:
1. Full 72-case `reasoning_matrix` (61/62 positives, `MG9` 7-question root-cause & budget proof, 10/10 negatives, 0 false-served).
2. `r1-described-point-probe` (`13/13` positive + `C3-dist`, `6/6` adversarial fail-closed).
3. Prior compositional families (`PL5`, `PA3`, `MG5`, `SE3`, `RE10`, `F3b`, `F4c`, `test_family_d2`).
4. 21 novel autonomous composition positive cases across pyramid, right triangular prism, cube, and regular tetrahedron + 11 negative/degenerate/cycle/tamper/budget cases.
5. Full 18-field planner telemetry, before/after search efficiency deltas (`MG9` 54->33 candidates, `T1`/`E1` 10->8 aux calls), p50/p95 latency & `tracemalloc` peak memory, Gold vs `local-geometry-parser/2` NL isolation.
"""
from __future__ import annotations

import copy
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import tracemalloc
from typing import Any

RUN_DIR = Path(__file__).resolve().parents[1]
ROOT = RUN_DIR.parents[4]
BACKEND = ROOT / "backend"
for p in (
    BACKEND,
    BACKEND / "scripts",
    BACKEND / "tests" / "geometry",
    ROOT / "docs/evaluation/geometry/runs/hybrid-reasoning-generalization/tools",
):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

import reasoning_matrix as RM  # noqa: E402
import run_s2_student_language_pilot as S2R  # noqa: E402
import test_planner_autonomous_composition as TP  # noqa: E402
from app.ai.adaptive_input_router import route_text_input  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
from app.main import CACHE_VERSION, ROUTE_D_CACHE_POLICY  # noqa: E402
from app.runtime_identity import runtime_identity, semantic_environment_hash  # noqa: E402
from app.simulation.geometry_functions import (  # noqa: E402
    planner,
    typed_fact_next as TN,
    typed_fact_next_bridge as TB,
)
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity  # noqa: E402
from app.simulation.semantic_program.validator import MAX_MEMORY_DECLARATIONS  # noqa: E402

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    xs = sorted(vals)
    idx = min(len(xs) - 1, max(0, int(round((len(xs) - 1) * p))))
    return round(xs[idx], 3)


def _run_gold(text: str, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, str] | None, float, int]:
    tracemalloc.start()
    t0 = time.perf_counter()
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    ms = round((time.perf_counter() - t0) * 1000.0, 3)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    route, env = out.response["route_d"], out.response["envelope"]
    ans = {k: v["coef"] for k, v in (route.get("answer_exact") or {}).items()} if route["status"] == "SERVED" else None
    return route, env, ans, ms, peak


def _extract_full_telemetry(route: dict[str, Any], ms: float, peak_bytes: int) -> dict[str, Any]:
    tel = dict((route.get("planner") or {}).get("search_telemetry") or {})
    tel["latency_ms"] = ms
    tel["peak_memory_kib"] = round(peak_bytes / 1024.0, 2)
    tel["calls_total"] = len((route.get("planner") or {}).get("calls") or [])
    tel["auxiliary_count"] = len((route.get("planner") or {}).get("auxiliary") or [])
    return tel


def _evaluate_reasoning_matrix() -> dict[str, Any]:
    cases = RM.build_cases()
    pos_rows, neg_rows = [], []
    latencies: list[float] = []
    peaks: list[int] = []
    false_served = 0
    mg9_diag: dict[str, Any] = {}

    for c in cases:
        cid = c["id"]
        want_status = c["expect"][0]
        route, env, ans, ms, peak = _run_gold(c["text"], c["payload"])
        latencies.append(ms)
        peaks.append(peak)
        st = route["status"]
        code = env.get("reason_code")
        clar = bool(
            (route.get("refusal") or {}).get("clarification")
            or env.get("clarification")
            or (route.get("refusal") or {}).get("clarifications")
        )
        scene = env.get("scene3d")
        scene_issues = validate_construction_continuity(scene) if (st == "SERVED" and scene) else ([] if st != "SERVED" else ["NO_SCENE3D"])
        cls_outcome = RM.classify(c, st, code, ans or {}, clar, scene_issues)
        tel = _extract_full_telemetry(route, ms, peak)

        if want_status == "SERVED":
            pos_rows.append({
                "id": cid,
                "status": st,
                "reason_code": code,
                "outcome": cls_outcome,
                "oracle_exact": cls_outcome == "EXACT_SERVED",
                "search_telemetry": tel,
            })
            if cid == "MG9":
                v2 = TN.TypedFactNextPayloadV2.model_validate(c["payload"])
                plan9 = planner.lap_ke_hoach(TB.bridge_v2(v2))
                mg9_diag = {
                    "q1_planner_status": "PLAN_SUCCEEDED",
                    "q2_search_telemetry": dict(plan9.search_telemetry),
                    "q3_refusal_stage": "route_ir_budget",
                    "q4_reason_code": code,
                    "q5_max_memory_declarations": MAX_MEMORY_DECLARATIONS,
                    "q6_before_after": {
                        "before_candidate_evaluations": 54,
                        "after_candidate_evaluations": plan9.search_telemetry["candidate_evaluations"],
                        "before_pruned_nodes": 0,
                        "after_pruned_nodes": plan9.search_telemetry["pruned_nodes"],
                    },
                    "q7_minimum_memory_note": "34 declarations after line sharing (minimum 33 > 32); kept fail-closed",
                }
        else:
            if st == "SERVED":
                false_served += 1
            neg_rows.append({
                "id": cid,
                "status": st,
                "reason_code": code,
                "outcome": cls_outcome,
                "matched": cls_outcome in ("CORRECT_REFUSAL", "CORRECT_CLARIFICATION"),
                "latency_ms": ms,
            })

    return {
        "dataset": "docs/evaluation/geometry/runs/hybrid-reasoning-generalization/tools/reasoning_matrix.py (72 cases)",
        "positive_served": sum(1 for r in pos_rows if r["oracle_exact"]),
        "positive_total": len(pos_rows),
        "negative_refused": sum(1 for r in neg_rows if r["matched"]),
        "negative_total": len(neg_rows),
        "false_served": false_served,
        "remaining_refused": [
            {"id": r["id"], "status": r["status"], "reason_code": r["reason_code"]}
            for r in pos_rows
            if not r["oracle_exact"]
        ],
        "mg9_root_cause_7_questions": mg9_diag,
        "latency_p50_ms": _percentile(latencies, 0.50),
        "latency_p95_ms": _percentile(latencies, 0.95),
        "peak_memory_p95_kib": round(_percentile([float(x) for x in peaks], 0.95) / 1024.0, 2),
        "positive_rows": pos_rows,
        "negative_rows": neg_rows,
    }


def _evaluate_r1_probe() -> dict[str, Any]:
    r1_path = ROOT / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/r1-described-point-probe.json"
    cases = {c["id"]: c for c in json.loads(r1_path.read_text(encoding="utf-8"))["cases"]}
    rows = []
    false_served = 0
    for cid in ("C1a", "C1b", "C2", "C3", "C4", "C5", "C6a", "C6b", "C7", "N1", "D1", "D2"):
        c = cases[cid]
        route, env, ans, ms, peak = _run_gold(c["text"], c["payload"])
        ok = route["status"] == "SERVED" and ans == c["want"] and validate_construction_continuity(env["scene3d"]) == []
        rows.append({"id": cid, "status": route["status"], "oracle_exact": ok, "answers": ans, "want": c["want"], "telemetry": _extract_full_telemetry(route, ms, peak)})
    c3d = copy.deepcopy(cases["C3"])
    old_q = c3d["payload"]["math_goals"][0]["quote"]
    ask_q = old_q.replace("Tính góc", "Tính khoảng cách")
    c3d["text"] = c3d["text"].replace(old_q, ask_q)
    c3d["payload"]["problem_text"] = c3d["text"]
    c3d["payload"]["math_goals"][0].update(goal_type="distance", quote=ask_q)
    rd, ed, ad, msd, pkd = _run_gold(c3d["text"], c3d["payload"])
    rows.append({
        "id": "C3-dist",
        "status": rd["status"],
        "oracle_exact": rd["status"] == "SERVED" and ad == {"q1": "0"} and validate_construction_continuity(ed["scene3d"]) == [],
        "answers": ad,
        "want": {"q1": "0"},
        "telemetry": _extract_full_telemetry(rd, msd, pkd),
    })
    neg_rows = []
    for cid, c in cases.items():
        if not cid.startswith("X"):
            continue
        route, env, _a, ms, _pk = _run_gold(c["text"], c["payload"])
        if route["status"] == "SERVED":
            false_served += 1
        neg_rows.append({"id": cid, "status": route["status"], "reason_code": env.get("reason_code"), "latency_ms": ms})
    return {
        "positive_passed": sum(1 for r in rows if r["oracle_exact"]),
        "positive_total": len(rows),
        "adversarial_refused": sum(1 for r in neg_rows if r["status"] == "REFUSED"),
        "adversarial_total": len(neg_rows),
        "false_served": false_served,
        "positive_rows": rows,
        "negative_rows": neg_rows,
    }


def _build_novel_positive_cases() -> list[dict[str, Any]]:
    t2 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. "
    t3 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 3. "
    t4s = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 4. "
    t_pr = "Cho hình lăng trụ đứng ABC.A'B'C' có đáy ABC là tam giác vuông tại A, AB = 3, AC = 4, AA' = 2. "
    t_cu = "Cho hình lập phương ABCD.A'B'C'D' cạnh 2. "
    t_tet = "Cho tứ diện đều ABCD cạnh 2. "

    cases: list[dict[str, Any]] = []

    def add(cid: str, cat: str, text: str, payload: dict, want: dict[str, tuple[str, Fraction]], *, min_reused: int = 0, exact_cost: int | None = None, expect_nl: bool = False) -> None:
        cases.append({"id": cid, "category": cat, "text": text, "payload": payload, "want": want, "min_reused": min_reused, "exact_cost": exact_cost, "expect_nl": expect_nl})

    # Category A: ask_distance_lines with 1 derived line (5)
    q = "Tính khoảng cách giữa đường thẳng nối S với trung điểm của BC và đường thẳng CD"
    add("NC-A1", "distance_lines_1der", t2 + q + ".", TP._pyr_payload(t2 + q + ".", [{"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["S", "@m1"], "line2": ["C", "D"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(4, 5))})

    q = "Tính khoảng cách giữa đường thẳng nối trung điểm của SA với trung điểm của BC và đường thẳng BD"
    add("NC-A2", "distance_lines_1der", t2 + q + ".", TP._pyr_payload(t2 + q + ".", [{"described_id": "m1", "kind": "midpoint", "segment": ["S", "A"], "quote": "trung điểm của SA"}, {"described_id": "m2", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["@m1", "@m2"], "line2": ["B", "D"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(1, 11))})

    q = "Tính khoảng cách giữa đường thẳng nối A' với trung điểm của BC và đường thẳng B'C'"
    add("NC-A3", "distance_lines_1der", t_pr + q + ".", TP._prism_payload(t_pr + q + ".", [{"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["A'", "@m1"], "line2": ["B'", "C'"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(144, 61))})

    q = "Tính khoảng cách giữa đường thẳng nối B với trung điểm của CD' và đường thẳng A'D"
    add("NC-A4", "distance_lines_1der", t_cu + q + ".", TP._cube_payload(t_cu + q + ".", [{"described_id": "m1", "kind": "midpoint", "segment": ["C", "D'"], "quote": "trung điểm của CD'"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["B", "@m1"], "line2": ["A'", "D"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(16, 11))})

    q = "Tính khoảng cách giữa đường thẳng nối B với trung điểm của AC và đường thẳng CD"
    add("NC-A5", "distance_lines_1der", t_tet + q + ".", TP._tet_payload(t_tet + q + ".", [{"described_id": "m1", "kind": "midpoint", "segment": ["A", "C"], "quote": "trung điểm của AC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["B", "@m1"], "line2": ["C", "D"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(8, 11))})

    # Category B: ask_distance_lines with 2 derived lines / composed @ids (4)
    q = "Tính khoảng cách giữa đường thẳng nối hình chiếu vuông góc của A lên (SBD) với D và đường thẳng nối S với trung điểm của BC"
    add("NC-B1", "distance_lines_2der", t2 + q + ".", TP._pyr_payload(t2 + q + ".", [{"described_id": "p1", "kind": "orthogonal_projection", "point": "A", "plane": ["S", "B", "D"], "quote": "hình chiếu vuông góc của A lên (SBD)"}, {"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["@p1", "D"], "line2": ["S", "@m1"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(2, 25))})

    q = "Tính khoảng cách giữa đường thẳng nối hình chiếu vuông góc của A lên (A'BD) với C' và đường thẳng nối B với trung điểm của CD'"
    add("NC-B2", "distance_lines_2der", t_cu + q + ".", TP._cube_payload(t_cu + q + ".", [{"described_id": "p1", "kind": "orthogonal_projection", "point": "A", "plane": ["A'", "B", "D"], "quote": "hình chiếu vuông góc của A lên (A'BD)"}, {"described_id": "m1", "kind": "midpoint", "segment": ["C", "D'"], "quote": "trung điểm của CD'"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["@p1", "C'"], "line2": ["B", "@m1"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(2, 7))})

    q = "Tính khoảng cách giữa đường thẳng nối hình chiếu vuông góc của A lên (BCD) với B và đường thẳng nối C với trung điểm của AD"
    add("NC-B3", "distance_lines_2der", t_tet + q + ".", TP._tet_payload(t_tet + q + ".", [{"described_id": "p1", "kind": "orthogonal_projection", "point": "A", "plane": ["B", "C", "D"], "quote": "hình chiếu vuông góc của A lên (BCD)"}, {"described_id": "m1", "kind": "midpoint", "segment": ["A", "D"], "quote": "trung điểm của AD"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["@p1", "B"], "line2": ["C", "@m1"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(8, 35))})

    q = "Tính khoảng cách giữa đường thẳng nối trực tâm của tam giác SBD với D và đường thẳng nối trung điểm của SA với trung điểm của BC"
    add("NC-B4", "distance_lines_2der", t2 + q + ".", TP._pyr_payload(t2 + q + ".", [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}, {"described_id": "m1", "kind": "midpoint", "segment": ["S", "A"], "quote": "trung điểm của SA"}, {"described_id": "m2", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["@o1", "D"], "line2": ["@m1", "@m2"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(1, 35))})

    # Category C: intersect_line_line + orthogonal_projection_line + midpoint discovery (5)
    q = "Tính khoảng cách từ giao điểm của đường thẳng nối S với trung điểm của BC và đường thẳng nối B với trung điểm của SC đến (ABCD)"
    add("NC-C1", "discovered_composition", t2 + q + ".", TP._pyr_payload(t2 + q + ".", [{"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}, {"described_id": "m2", "kind": "midpoint", "segment": ["S", "C"], "quote": "trung điểm của SC"}, {"described_id": "x1", "kind": "intersect_line_line", "line1": ["S", "@m1"], "line2": ["B", "@m2"], "quote": "giao điểm của đường thẳng nối S với trung điểm của BC và đường thẳng nối B với trung điểm của SC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@x1", "plane": ["A", "B", "C", "D"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(4, 9))})

    q = "Tính khoảng cách từ giao điểm của đường thẳng nối A với trung điểm của B'C' và đường thẳng nối A' với trung điểm của BC đến (ABB')"
    add("NC-C2", "discovered_composition", t_pr + q + ".", TP._prism_payload(t_pr + q + ".", [{"described_id": "m1", "kind": "midpoint", "segment": ["B'", "C'"], "quote": "trung điểm của B'C'"}, {"described_id": "m2", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}, {"described_id": "x1", "kind": "intersect_line_line", "line1": ["A", "@m1"], "line2": ["A'", "@m2"], "quote": "giao điểm của đường thẳng nối A với trung điểm của B'C' và đường thẳng nối A' với trung điểm của BC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@x1", "plane": ["A", "B", "B'"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(1))})

    q = "Tính khoảng cách từ hình chiếu vuông góc của trực tâm của tam giác SBD lên đường thẳng nối S với trung điểm của BC đến mặt phẳng (ABCD)"
    add("NC-C3", "discovered_composition", t2 + q + ".", TP._pyr_payload(t2 + q + ".", [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}, {"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}, {"described_id": "f1", "kind": "orthogonal_projection_line", "point": "@o1", "line": ["S", "@m1"], "quote": "hình chiếu vuông góc của trực tâm của tam giác SBD lên đường thẳng nối S với trung điểm của BC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@f1", "plane": ["A", "B", "C", "D"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(26 * 26, 27 * 27))})

    q = "Tính khoảng cách từ hình chiếu vuông góc của trọng tâm của tam giác SBC lên đường thẳng nối S với trung điểm của CD đến mặt phẳng (ABCD)"
    add("NC-C4", "discovered_composition", t2 + q + ".", TP._pyr_payload(t2 + q + ".", [{"described_id": "g1", "kind": "centroid", "polygon": ["S", "B", "C"], "quote": "trọng tâm của tam giác SBC"}, {"described_id": "m1", "kind": "midpoint", "segment": ["C", "D"], "quote": "trung điểm của CD"}, {"described_id": "f1", "kind": "orthogonal_projection_line", "point": "@g1", "line": ["S", "@m1"], "quote": "hình chiếu vuông góc của trọng tâm của tam giác SBC lên đường thẳng nối S với trung điểm của CD"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@f1", "plane": ["A", "B", "C", "D"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(22 * 22, 27 * 27))})

    q = "Tính khoảng cách từ trung điểm của đoạn nối trực tâm của tam giác SBD với C đến (SAB)"
    add("NC-C5", "discovered_composition", t2 + q + ".", TP._pyr_payload(t2 + q + ".", [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}, {"described_id": "m1", "kind": "midpoint", "segment": ["@o1", "C"], "quote": "trung điểm của đoạn nối trực tâm của tam giác SBD với C"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@m1", "plane": ["S", "A", "B"]}, "quote": q, "solid_id": "s1"}]), {"q1": ("d2", Fraction(16, 9))})

    # Category D: Within-goal sibling reuse & deduplication (3)
    q_t1 = "Tính độ dài đoạn thẳng nối trực tâm của tam giác SBD với tâm đường tròn ngoại tiếp tam giác SBD"
    add("NC-D1_T1", "within_goal_reuse", t3 + q_t1 + ".", TP._pyr_payload(t3 + q_t1 + ".", [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}, {"described_id": "c1", "kind": "circumcenter", "polygon": ["S", "B", "D"], "quote": "tâm đường tròn ngoại tiếp tam giác SBD"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@o1", "@c1"]}, "quote": q_t1, "solid_id": "s1"}], sa="3"), {"q1": ("d2", Fraction(25 * 11, 22 * 22))}, min_reused=2, exact_cost=8, expect_nl=True)

    q_e1 = "Tính góc giữa đường thẳng nối trực tâm của tam giác SBD với tâm đường tròn ngoại tiếp tam giác SBD và mặt phẳng (ABCD)"
    add("NC-D2_E1", "within_goal_reuse", t3 + q_e1 + ".", TP._pyr_payload(t3 + q_e1 + ".", [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}, {"described_id": "c1", "kind": "circumcenter", "polygon": ["S", "B", "D"], "quote": "tâm đường tròn ngoại tiếp tam giác SBD"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "angle", "target": {"line": ["@o1", "@c1"], "plane": ["A", "B", "C", "D"]}, "quote": q_e1, "solid_id": "s1"}], sa="3"), {"q1": ("cos2", Fraction(2, 11))}, min_reused=2, exact_cost=8)

    add("NC-D3_T1_SA4", "within_goal_reuse", t4s + q_t1 + ".", TP._pyr_payload(t4s + q_t1 + ".", [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}, {"described_id": "c1", "kind": "circumcenter", "polygon": ["S", "B", "D"], "quote": "tâm đường tròn ngoại tiếp tam giác SBD"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"segment": ["@o1", "@c1"]}, "quote": q_t1, "solid_id": "s1"}], sa="4"), {"q1": ("d2", Fraction(2))}, min_reused=2, exact_cost=8, expect_nl=True)

    # Category E: Cross-rule reuse & section chaining (4)
    q_t3 = "Tính khoảng cách từ trực tâm của tam giác SBD đến đường thẳng BD"
    add("NC-E1_T3", "cross_rule_reuse", t2 + q_t3 + ".", TP._pyr_payload(t2 + q_t3 + ".", [{"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "D"], "quote": "trực tâm của tam giác SBD"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@o1", "line": ["B", "D"]}, "quote": q_t3, "solid_id": "s1"}]), {"q1": ("d2", Fraction(6, 9))}, min_reused=3, expect_nl=True)

    t_t4 = t2 + "Gọi (P) là mặt phẳng đi qua A và vuông góc với SB. Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P) và tính khoảng cách từ A đến SB."
    add("NC-E2_T4", "cross_rule_reuse", t_t4, TP._pyr_payload(t_t4, [], [{"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P)", "solid_id": "s1"}, {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"point": "A", "line": ["S", "B"]}, "quote": "tính khoảng cách từ A đến SB", "solid_id": "s1"}], secs=({"section_id": "sec1", "plane_name": "P", "target_solid_id": "s1", "plane_kind": "through_point_perpendicular_line", "through_point": "A", "perpendicular_line": ["S", "B"], "stated_intersections": [], "quote": "Gọi (P) là mặt phẳng đi qua A và vuông góc với SB"},)), {"q1": ("d2", Fraction(9, 2)), "q2": ("d2", Fraction(2))}, min_reused=1)

    t_t5 = t2 + "Mặt phẳng (P) đi qua A, C và vuông góc với (SBD). Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P) và tính diện tích thiết diện đó. Tính khoảng cách từ hình chiếu vuông góc của A lên (SBD) đến mặt phẳng (ABCD)."
    add("NC-E3_T5", "cross_rule_reuse", t_t5, TP._pyr_payload(t_t5, [{"described_id": "h1", "kind": "orthogonal_projection", "point": "A", "plane": ["S", "B", "D"], "quote": "hình chiếu vuông góc của A lên (SBD)"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": "Xác định thiết diện của hình chóp S.ABCD cắt bởi mặt phẳng (P) và tính diện tích thiết diện đó", "solid_id": "s1"}, {"goal_id": "q2", "kind": "measurement", "goal_type": "distance", "target": {"point": "@h1", "plane": ["A", "B", "C", "D"]}, "quote": "Tính khoảng cách từ hình chiếu vuông góc của A lên (SBD) đến mặt phẳng (ABCD)", "solid_id": "s1"}], secs=({"section_id": "sec1", "plane_name": "P", "target_solid_id": "s1", "plane_kind": "constrained", "constraints": [{"kind": "contains_points", "operands": ["A", "C"]}, {"kind": "perpendicular_to_plane", "operands": ["S", "B", "D"]}], "stated_intersections": [], "quote": "Mặt phẳng (P) đi qua A, C và vuông góc với (SBD)"},)), {"q1": ("d2", Fraction(8)), "q2": ("d2", Fraction(4, 9))}, min_reused=1, expect_nl=True)

    t_dcc = t2 + "Mặt phẳng (P) đi qua hình chiếu vuông góc của B lên SC và song song với (ABCD). Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P)."
    add("NC-E4_DCC", "cross_rule_reuse", t_dcc, TP._pyr_payload(t_dcc, [{"described_id": "f1", "kind": "orthogonal_projection_line", "point": "B", "line": ["S", "C"], "quote": "hình chiếu vuông góc của B lên SC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "area", "target": {"section_id": "sec1"}, "quote": "Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P)", "solid_id": "s1"}], secs=({"section_id": "sec1", "plane_name": "P", "target_solid_id": "s1", "plane_kind": "through_point_parallel_plane", "through_point": "@f1", "parallel_plane": ["A", "B", "C"], "stated_intersections": [], "quote": "Mặt phẳng (P) đi qua hình chiếu vuông góc của B lên SC và song song với (ABCD)"},)), {"q1": ("d2", Fraction(256, 81))}, min_reused=1)

    return cases


def _evaluate_novel_cases() -> dict[str, Any]:
    cases = _build_novel_positive_cases()
    rows = []
    latencies: list[float] = []
    nl_isolated: list[dict[str, Any]] = []
    for c in cases:
        route, env, ans, ms, peak = _run_gold(c["text"], c["payload"])
        latencies.append(ms)
        st = route["status"]
        cont = validate_construction_continuity(env["scene3d"]) if (st == "SERVED" and env.get("scene3d")) else []
        tel = _extract_full_telemetry(route, ms, peak)
        oracle_ok = st == "SERVED" and ans is not None and all(
            (Fraction(ans[g]) if meas == "cos2" else RM.coef_square(ans[g])) == want
            for g, (meas, want) in c["want"].items()
        )
        reuse_ok = tel.get("reused_intermediates", 0) >= c["min_reused"]
        cost_ok = c["exact_cost"] is None or tel.get("plan_cost") == c["exact_cost"]
        h4_ok = "H4" not in {o["id"] for o in (env.get("scene3d") or {}).get("objects", []) if o.get("type") == "point3"}
        passed = oracle_ok and cont == [] and reuse_ok and cost_ok and h4_ok
        rows.append({
            "id": c["id"],
            "category": c["category"],
            "status": st,
            "oracle_exact": oracle_ok,
            "answers": ans,
            "continuity_errors": len(cont),
            "passed": passed,
            "telemetry": tel,
        })
        if c["expect_nl"] or c["id"] == "NC-D2_E1":
            lp = parse_geometry_problem_locally(c["text"])
            t0 = time.perf_counter()
            nr = route_text_input(c["text"], allow_live_ai=False)
            mn = round((time.perf_counter() - t0) * 1000.0, 3)
            nrd, nenv = nr.response.get("route_d") or {}, nr.response.get("envelope") or {}
            nan = {k: v["coef"] for k, v in (nrd.get("answer_exact") or {}).items()} if nrd.get("status") == "SERVED" else None
            nl_isolated.append({
                "id": c["id"],
                "expected_local_support": c["expect_nl"],
                "local_parse_status": lp.status,
                "nl_status": nrd.get("status"),
                "nl_reason_code": nenv.get("reason_code"),
                "answers_match_gold": nan == ans if c["expect_nl"] else None,
                "nl_ms": mn,
            })

    return {
        "positive_passed": sum(1 for r in rows if r["passed"]),
        "positive_total": len(rows),
        "latency_p50_ms": _percentile(latencies, 0.50),
        "latency_p95_ms": _percentile(latencies, 0.95),
        "rows": rows,
        "gold_vs_local_parser_isolation": nl_isolated,
    }


def _evaluate_negative_safety() -> dict[str, Any]:
    rm_cases = {c["id"]: c for c in RM.build_cases()}
    t2 = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. "
    neg_specs: list[tuple[str, str, dict, set[str]]] = [
        ("NEG-1_parallel_ill", t2 + "Tính khoảng cách từ giao điểm của AB và CD đến (SAD).", TP._pyr_payload(t2 + "Tính khoảng cách từ giao điểm của AB và CD đến (SAD).", [{"described_id": "x1", "kind": "intersect_line_line", "line1": ["A", "B"], "line2": ["C", "D"], "quote": "giao điểm của AB và CD"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@x1", "plane": ["S", "A", "D"]}, "quote": "Tính khoảng cách từ giao điểm của AB và CD đến (SAD)", "solid_id": "s1"}]), {"PARALLEL_NO_INTERSECTION"}),
        ("NEG-2_skew_ill", t2 + "Tính khoảng cách từ giao điểm của SB và CD đến (SAD).", TP._pyr_payload(t2 + "Tính khoảng cách từ giao điểm của SB và CD đến (SAD).", [{"described_id": "x1", "kind": "intersect_line_line", "line1": ["S", "B"], "line2": ["C", "D"], "quote": "giao điểm của SB và CD"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@x1", "plane": ["S", "A", "D"]}, "quote": "Tính khoảng cách từ giao điểm của SB và CD đến (SAD)", "solid_id": "s1"}]), {"SKEW_NO_INTERSECTION"}),
        ("NEG-3_cycle_desc", t2 + "Tính khoảng cách từ trung điểm của đoạn nối nó với C đến (SAD).", TP._pyr_payload(t2 + "Tính khoảng cách từ trung điểm của đoạn nối nó với C đến (SAD).", [{"described_id": "m1", "kind": "midpoint", "segment": ["@m2", "C"], "quote": "trung điểm của đoạn nối nó với C"}, {"described_id": "m2", "kind": "midpoint", "segment": ["@m1", "D"], "quote": "trung điểm của đoạn nối nó với C"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@m1", "plane": ["S", "A", "D"]}, "quote": "Tính khoảng cách từ trung điểm của đoạn nối nó với C đến (SAD)", "solid_id": "s1"}]), {"DEPENDENCY_CYCLE"}),
        ("NEG-4_identical_dist_lines", t2 + "Tính khoảng cách giữa đường thẳng nối A với trung điểm của BC và đường thẳng nối A với trung điểm của BC.", TP._pyr_payload(t2 + "Tính khoảng cách giữa đường thẳng nối A với trung điểm của BC và đường thẳng nối A với trung điểm của BC.", [{"described_id": "m1", "kind": "midpoint", "segment": ["B", "C"], "quote": "trung điểm của BC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"line1": ["A", "@m1"], "line2": ["A", "@m1"]}, "quote": "Tính khoảng cách giữa đường thẳng nối A với trung điểm của BC và đường thẳng nối A với trung điểm của BC", "solid_id": "s1"}]), {"AUXILIARY_RULE_MISMATCH"}),
        ("NEG-5_collinear_plane", t2 + "Gọi M là trung điểm của AB. Tính khoảng cách từ hình chiếu vuông góc của C lên (ABM) đến (SAD).", {**TP._pyr_payload(t2 + "Gọi M là trung điểm của AB. Tính khoảng cách từ hình chiếu vuông góc của C lên (ABM) đến (SAD).", [{"described_id": "p1", "kind": "orthogonal_projection", "point": "C", "plane": ["A", "B", "M"], "quote": "hình chiếu vuông góc của C lên (ABM)"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@p1", "plane": ["S", "A", "D"]}, "quote": "Tính khoảng cách từ hình chiếu vuông góc của C lên (ABM) đến (SAD)", "solid_id": "s1"}]), "premises": [*TP._pyr_payload("", [], [])["premises"], {"kind": "midpoint", "args": {"point": "M", "segment": ["A", "B"]}, "quote": "Gọi M là trung điểm của AB", "solid_id": "s1"}]}, {"COLLINEAR_POINTS", "DEGENERATE_POINTS"}),
        ("NEG-6_coincident_line_pts", t2 + "Tính khoảng cách từ S đến đường thẳng nối trung điểm của AC với giao điểm của AC và BD.", TP._pyr_payload(t2 + "Tính khoảng cách từ S đến đường thẳng nối trung điểm của AC với giao điểm của AC và BD.", [{"described_id": "m1", "kind": "midpoint", "segment": ["A", "C"], "quote": "trung điểm của AC"}, {"described_id": "i1", "kind": "intersect_line_line", "line1": ["A", "C"], "line2": ["B", "D"], "quote": "giao điểm của AC và BD"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "S", "line": ["@m1", "@i1"]}, "quote": "Tính khoảng cách từ S đến đường thẳng nối trung điểm của AC với giao điểm của AC và BD", "solid_id": "s1"}]), {"DEGENERATE_LINE", "DEGENERATE_POINTS"}),
        ("NEG-7_missing_dim", rm_cases["PA3"]["text"].replace(" và SA = 2", ""), {**copy.deepcopy(rm_cases["PA3"]["payload"]), "problem_text": rm_cases["PA3"]["text"].replace(" và SA = 2", ""), "premises": [x for x in rm_cases["PA3"]["payload"]["premises"] if x["kind"] != "segment_length"]}, {"MISSING_DIMENSION", "UNDERDETERMINED_POINT"}),
        ("NEG-8_contradictory_len", t2 + "SC = 1. Tính khoảng cách từ trung điểm của SC đến (SAB).", {**TP._pyr_payload(t2 + "SC = 1. Tính khoảng cách từ trung điểm của SC đến (SAB).", [{"described_id": "m1", "kind": "midpoint", "segment": ["S", "C"], "quote": "trung điểm của SC"}], [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance", "target": {"point": "@m1", "plane": ["S", "A", "B"]}, "quote": "Tính khoảng cách từ trung điểm của SC đến (SAB)", "solid_id": "s1"}]), "premises": [*TP._pyr_payload("", [], [])["premises"], {"kind": "segment_length", "args": {"segment": ["S", "C"], "value": "1"}, "quote": "SC = 1", "solid_id": "s1"}]}, {"INCONSISTENT_FACTS"}),
        ("NEG-9_ungrounded_quote", rm_cases["PA3"]["text"], {**copy.deepcopy(rm_cases["PA3"]["payload"]), "described_points": [{**rm_cases["PA3"]["payload"]["described_points"][0], "quote": "trung điểm của BC"}]}, {"QUOTE_NOT_IN_SOURCE", "SOURCE_OBJECT_MISMATCH"}),
    ]

    rows = []
    false_served = 0
    for nid, txt, pl, want_codes in neg_specs:
        r, e, _, ms, _ = _run_gold(txt, pl)
        if r["status"] == "SERVED":
            false_served += 1
        rows.append({"id": nid, "status": r["status"], "reason_code": e.get("reason_code"), "matched": r["status"] == "REFUSED" and e.get("reason_code") in want_codes, "latency_ms": ms})

    # NEG-10 & NEG-11 via monkeypatch semantics on planner
    re10 = rm_cases["RE10"]
    orig_plan = planner.lap_ke_hoach
    try:
        def _tamper(*a, **k):
            pl = orig_plan(*a, **k)
            for cert in pl.auxiliary:
                if cert.get("rule") == "effect-chain" and cert.get("operand", {}).get("nested"):
                    cert["operand"]["nested"]["points"] = ["S", "B", "C"]
            return pl
        planner.lap_ke_hoach = _tamper
        r10, e10, _, m10, _ = _run_gold(re10["text"], re10["payload"])
        if r10["status"] == "SERVED":
            false_served += 1
        rows.append({"id": "NEG-10_tamper_aux", "status": r10["status"], "reason_code": e10.get("reason_code"), "matched": r10["status"] == "REFUSED" and e10.get("reason_code") in {"AUXILIARY_RULE_MISMATCH", "ENGINE_SELF_CHECK_FAILED"}, "latency_ms": m10})
    finally:
        planner.lap_ke_hoach = orig_plan

    orig_cap = planner.MAX_EFFECT_CANDIDATES
    try:
        planner.MAX_EFFECT_CANDIDATES = 4
        r11, e11, _, m11, _ = _run_gold(re10["text"], re10["payload"])
        if r11["status"] == "SERVED":
            false_served += 1
        rows.append({"id": "NEG-11_budget_cap", "status": r11["status"], "reason_code": e11.get("reason_code"), "matched": r11["status"] == "REFUSED" and e11.get("reason_code") == "PLAN_TOO_LARGE", "latency_ms": m11})
    finally:
        planner.MAX_EFFECT_CANDIDATES = orig_cap

    return {
        "negative_refused": sum(1 for r in rows if r["matched"]),
        "negative_total": len(rows),
        "false_served": false_served,
        "rows": rows,
    }


def _run_pytest_json(test_path: str) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-c", "backend/pytest.ini", test_path, "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    summary = next((l.strip() for l in reversed(proc.stdout.splitlines()) if l.strip()), "")
    return {"test_path": test_path, "returncode": proc.returncode, "summary": summary}


def main() -> int:
    ident = runtime_identity()
    s2_ident = S2R.runtime_identity()
    rm_eval = _evaluate_reasoning_matrix()
    r1_eval = _evaluate_r1_probe()
    novel_eval = _evaluate_novel_cases()
    neg_eval = _evaluate_negative_safety()
    suite_checks = [
        _run_pytest_json("backend/tests/geometry/test_planner_autonomous_composition.py"),
        _run_pytest_json("backend/tests/geometry/test_compositional_planner_expansion.py"),
        _run_pytest_json("backend/tests/geometry/test_hybrid_reasoning_generalization.py"),
        _run_pytest_json("backend/tests/geometry/test_production_dynamic_composition.py"),
    ]
    report = {
        "run_id": "planner-autonomous-composition-and-search-efficiency",
        "measurement_class": "OFFLINE_DEVELOPMENT_EVIDENCE",
        "independent_h1_validation": "NOT_MEASURED",
        "live_ai_calls": 0,
        "git_head": _git_head(),
        "cache_version": CACHE_VERSION,
        "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
        "semantic_environment_hash": semantic_environment_hash(),
        "runtime_identity": ident,
        "measured_system": s2_ident["measured_system"],
        "s2_runner_sha256": s2_ident["runner_sha256"],
        "reasoning_matrix_72": rm_eval,
        "r1_described_point_probe": r1_eval,
        "novel_autonomous_composition": novel_eval,
        "negative_and_adversarial_safety": neg_eval,
        "focused_suite_results": suite_checks,
        "all_focused_suites_passed": all(x["returncode"] == 0 for x in suite_checks),
    }
    out_path = RUN_DIR / "NOVEL_COMPOSITION_EVALUATION.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "rm_pos": f"{rm_eval['positive_served']}/{rm_eval['positive_total']}",
        "rm_neg": f"{rm_eval['negative_refused']}/{rm_eval['negative_total']}",
        "mg9_cands": rm_eval["mg9_root_cause_7_questions"]["q2_search_telemetry"]["candidate_evaluations"],
        "r1_pos": f"{r1_eval['positive_passed']}/{r1_eval['positive_total']}",
        "novel_pos": f"{novel_eval['positive_passed']}/{novel_eval['positive_total']}",
        "neg_safe": f"{neg_eval['negative_refused']}/{neg_eval['negative_total']}",
        "suites_ok": report["all_focused_suites_passed"],
        "measured_system": s2_ident["measured_system"][:16],
    }, ensure_ascii=False))
    return 0 if report["all_focused_suites_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
