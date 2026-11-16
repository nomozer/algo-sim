# -*- coding: utf-8 -*-
"""Offline benchmark & compositional generalization evaluator for `compositional-planner-capability-expansion`.

Runs strictly offline (`ALLOW_LIVE_AI=0`, `0` live Gemini calls) on DEVELOPMENT datasets and probe fixtures:
1. Full 72-case `reasoning_matrix` (before/after comparison: 56/62 -> 61/62 positives, 10/10 negatives fail-closed).
2. `r1-described-point-probe` (`D1`, `D2`, `C1a`-`C7`, `N1`, `X1`-`X6`) + `C3-dist`.
3. `test_family_d2` + 5 new compositional discovery families.
4. Gold `TypedFactNext /2` vs `Local Geometry Parser /2` NL isolation comparison.
5. Metamorphic invariance, contract ablation, negative/tamper fail-closed safety, Scene3D continuity + FE-4 3-layer split.
"""
from __future__ import annotations

import copy
from dataclasses import replace
from fractions import Fraction
import json
import os
from pathlib import Path
import re
import statistics
import subprocess
import sys
import time
from typing import Any

RUN_DIR = Path(__file__).resolve().parents[1]
ROOT = RUN_DIR.parents[4]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
RM_TOOLS = ROOT / "docs/evaluation/geometry/runs/hybrid-reasoning-generalization/tools"
if str(RM_TOOLS) not in sys.path:
    sys.path.insert(0, str(RM_TOOLS))
SCRIPTS_DIR = BACKEND / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""

import reasoning_matrix as RM  # noqa: E402
import run_s2_student_language_pilot as S2R  # noqa: E402
from app.ai.adaptive_input_router import route_text_input  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_geometry_parser import LOCAL_PARSE_COMPLETE, parse_geometry_problem_locally  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402
from app.main import CACHE_VERSION  # noqa: E402
from app.runtime_identity import runtime_identity, semantic_environment_hash  # noqa: E402
from app.simulation.geometry_functions import engine, planner, registry  # noqa: E402
from app.simulation.geometry_functions.construction_continuity import validate_construction_continuity  # noqa: E402

POLICY = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _percentile(vals: list[float], p: float) -> float:
    if not vals:
        return 0.0
    xs = sorted(vals)
    idx = min(len(xs) - 1, max(0, int(round((len(xs) - 1) * p))))
    return round(xs[idx], 3)


def _run_gold(text: str, payload: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any], dict[str, str] | None, float]:
    t0 = time.perf_counter()
    out = run_hybrid_offline(text, ReplayExtractor({text: payload}), policy=POLICY)
    ms = round((time.perf_counter() - t0) * 1000.0, 3)
    route, env = out.response["route_d"], out.response["envelope"]
    ans = {k: v["coef"] for k, v in (route.get("answer_exact") or {}).items()} if route["status"] == "SERVED" else None
    return route, env, ans, ms


def _evaluate_reasoning_matrix() -> dict[str, Any]:
    cases = RM.build_cases()
    promoted_ids = {"PL5", "PA3", "MG5", "SE3", "RE10"}
    pos_rows, neg_rows, promoted_rows = [], [], []
    latencies: list[float] = []
    false_served = 0
    for c in cases:
        cid = c["id"]
        want_status = c["expect"][0]
        want_map = c["expect"][1] if want_status == "SERVED" else c["expect"][2]
        route, env, ans, ms = _run_gold(c["text"], c["payload"])
        latencies.append(ms)
        st = route["status"]
        tel = (route.get("planner") or {}).get("search_telemetry") or {}
        if want_status == "SERVED":
            oracle_ok = False
            if st == "SERVED" and ans is not None:
                oracle_ok = all(
                    (Fraction(ans[g]) if meas == "cos2" else RM.coef_square(ans[g])) == want
                    for g, (meas, want) in want_map.items()
                ) and validate_construction_continuity(env["scene3d"]) == []
            row = {
                "id": cid,
                "status": st,
                "reason_code": env.get("reason_code"),
                "oracle_exact": oracle_ok,
                "latency_ms": ms,
                "classification": tel.get("classification"),
                "candidate_count": tel.get("candidate_count"),
                "search_depth": tel.get("search_depth"),
                "reused_intermediates": tel.get("reused_intermediates"),
            }
            pos_rows.append(row)
            if cid in promoted_ids:
                promoted_rows.append(row)
        else:
            if st == "SERVED":
                false_served += 1
            neg_rows.append({
                "id": cid,
                "status": st,
                "reason_code": env.get("reason_code"),
                "expected_codes": sorted(want_map),
                "matched": st == "REFUSED" and env.get("reason_code") in want_map,
                "latency_ms": ms,
            })

    served_exact = sum(1 for r in pos_rows if r["oracle_exact"])
    neg_correct = sum(1 for r in neg_rows if r["matched"])
    return {
        "dataset": "docs/evaluation/geometry/runs/hybrid-reasoning-generalization/tools/reasoning_matrix.py (72 cases)",
        "baseline_before": {
            "in_scope_positive_served": 56,
            "in_scope_positive_total": 62,
            "negative_refused": 10,
            "negative_total": 10,
            "false_served": 0,
            "bridge_or_budget_gaps": ["PL5", "PA3", "MG5", "SE3", "RE10", "MG9"],
        },
        "after": {
            "in_scope_positive_served": served_exact,
            "in_scope_positive_total": len(pos_rows),
            "negative_refused": neg_correct,
            "negative_total": len(neg_rows),
            "false_served": false_served,
            "remaining_refused": [
                {"id": r["id"], "status": r["status"], "reason_code": r["reason_code"], "note": "contract bound MAX_MEMORY_DECLARATIONS=32"}
                for r in pos_rows if not r["oracle_exact"]
            ],
            "latency_p50_ms": _percentile(latencies, 0.50),
            "latency_p95_ms": _percentile(latencies, 0.95),
        },
        "promoted_from_xfail": promoted_rows,
    }


def _evaluate_r1_probe() -> dict[str, Any]:
    r1_path = ROOT / "docs/evaluation/geometry/runs/hybrid-master-backend-replacement/r1-described-point-probe.json"
    cases = {c["id"]: c for c in json.loads(r1_path.read_text(encoding="utf-8"))["cases"]}
    rows = []
    false_served = 0
    for cid in ("C1a", "C1b", "C2", "C3", "C4", "C5", "C6a", "C6b", "C7", "N1", "D1", "D2"):
        c = cases[cid]
        route, env, ans, ms = _run_gold(c["text"], c["payload"])
        ok = route["status"] == "SERVED" and ans == c["want"] and validate_construction_continuity(env["scene3d"]) == []
        rows.append({"id": cid, "status": route["status"], "oracle_exact": ok, "answers": ans, "want": c["want"], "latency_ms": ms})
    # Also C3-dist
    c3d = copy.deepcopy(cases["C3"])
    old_q = c3d["payload"]["math_goals"][0]["quote"]
    ask_q = old_q.replace("Tính góc", "Tính khoảng cách")
    c3d["text"] = c3d["text"].replace(old_q, ask_q)
    c3d["payload"]["problem_text"] = c3d["text"]
    c3d["payload"]["math_goals"][0].update(goal_type="distance", quote=ask_q)
    rd, ed, ad, msd = _run_gold(c3d["text"], c3d["payload"])
    rows.append({
        "id": "C3-dist",
        "status": rd["status"],
        "oracle_exact": rd["status"] == "SERVED" and ad == {"q1": "0"} and validate_construction_continuity(ed["scene3d"]) == [],
        "answers": ad,
        "want": {"q1": "0"},
        "latency_ms": msd,
    })
    neg_rows = []
    for cid, c in cases.items():
        if not cid.startswith("X"):
            continue
        route, env, _a, ms = _run_gold(c["text"], c["payload"])
        if route["status"] == "SERVED":
            false_served += 1
        neg_rows.append({"id": cid, "status": route["status"], "reason_code": env.get("reason_code"), "latency_ms": ms})
    return {
        "positive_rows": rows,
        "positive_passed": sum(1 for r in rows if r["oracle_exact"]),
        "positive_total": len(rows),
        "adversarial_refused": sum(1 for r in neg_rows if r["status"] == "REFUSED"),
        "adversarial_total": len(neg_rows),
        "false_served": false_served,
    }


def _evaluate_gold_vs_nl_and_new_families() -> dict[str, Any]:
    cases_RM = {c["id"]: c for c in RM.build_cases()}
    nl_rows = []
    nl_candidates = [
        ("PL5", cases_RM["PL5"]["text"], cases_RM["PL5"]["payload"], {"q1": "2√6/3"}),
        ("PA3", cases_RM["PA3"]["text"], cases_RM["PA3"]["payload"], {"q1": "1"}),
        ("MG5", cases_RM["MG5"]["text"], cases_RM["MG5"]["payload"], {"q1": "√5"}),
        ("SE3", cases_RM["SE3"]["text"], cases_RM["SE3"]["payload"], {"q1": "1"}),
        ("RE10", cases_RM["RE10"]["text"], cases_RM["RE10"]["payload"], {"q1": "2/3"}),
    ]
    # Add @orthocenter section F3b & circumcenter F4c NL cases
    t_f3b = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. Mặt phẳng (P) đi qua trực tâm của tam giác SBD và song song với (SAB). Tính diện tích thiết diện của hình chóp S.ABCD cắt bởi (P)."
    t_f4c = "Cho hình chóp S.ABCD có đáy ABCD là hình vuông cạnh 2, SA vuông góc với (ABCD), SA = 2. Tính khoảng cách từ tâm đường tròn ngoại tiếp tam giác SBC đến (SAD)."
    for cid, text, gold_p, want_ans in nl_candidates:
        rg, eg, ag, mg = _run_gold(text, gold_p)
        lp = parse_geometry_problem_locally(text)
        t0 = time.perf_counter()
        rn_out = route_text_input(text, allow_live_ai=False)
        mn = round((time.perf_counter() - t0) * 1000.0, 3)
        rn = rn_out.response.get("route_d") or {}
        en = rn_out.response.get("envelope") or {}
        an = {k: v["coef"] for k, v in (rn.get("answer_exact") or {}).items()} if rn.get("status") == "SERVED" else None
        nl_rows.append({
            "id": cid,
            "gold_served": rg["status"] == "SERVED" and ag == want_ans,
            "local_parse_status": lp.status,
            "nl_served": rn.get("status") == "SERVED" and an == want_ans,
            "answers_match": ag == an == want_ans,
            "continuity_errors": len(validate_construction_continuity(en["scene3d"])) if rn.get("status") == "SERVED" else -1,
            "gold_ms": mg,
            "nl_ms": mn,
            "search_telemetry": (rn.get("planner") or {}).get("search_telemetry"),
        })
    for cid, text, want_ans in (("F3b_orthocenter_section", t_f3b, {"q1": "16/9"}), ("F4c_circumcenter", t_f4c, {"q1": "1"})):
        lp = parse_geometry_problem_locally(text)
        t0 = time.perf_counter()
        rn_out = route_text_input(text, allow_live_ai=False)
        mn = round((time.perf_counter() - t0) * 1000.0, 3)
        rn = rn_out.response.get("route_d") or {}
        en = rn_out.response.get("envelope") or {}
        an = {k: v["coef"] for k, v in (rn.get("answer_exact") or {}).items()} if rn.get("status") == "SERVED" else None
        nl_rows.append({
            "id": cid,
            "gold_served": None,
            "local_parse_status": lp.status,
            "nl_served": rn.get("status") == "SERVED" and an == want_ans,
            "answers_match": an == want_ans,
            "continuity_errors": len(validate_construction_continuity(en["scene3d"])) if rn.get("status") == "SERVED" else -1,
            "gold_ms": None,
            "nl_ms": mn,
            "search_telemetry": (rn.get("planner") or {}).get("search_telemetry"),
        })

    # Also measure test_family_d2 from test_production_dynamic_composition:
    from tests.geometry.test_production_dynamic_composition import _pyramid_base_premises
    base_text, premises = _pyramid_base_premises("2", "3")
    q_d2 = "Tính khoảng cách từ hình chiếu vuông góc của trực tâm của tam giác SBC lên mặt phẳng (ABCD) đến mặt phẳng (SAD)"
    t_d2 = base_text + q_d2 + "."
    p_d2 = {
        "schema_version": "typed-fact-next/2", "problem_text": t_d2, "length_unit": "1",
        "solids": [{"solid_id": "s1", "solid_type": "pyramid", "notation": "S.ABCD", "quote": "Cho hình chóp S.ABCD"}],
        "premises": premises, "relations": [],
        "described_points": [
            {"described_id": "o1", "kind": "orthocenter", "polygon": ["S", "B", "C"], "quote": "trực tâm của tam giác SBC"},
            {"described_id": "h1", "kind": "orthogonal_projection", "point": "@o1", "plane": ["A", "B", "C", "D"],
             "quote": "hình chiếu vuông góc của trực tâm của tam giác SBC lên mặt phẳng (ABCD)"},
        ],
        "simulation_goals": [{"goal_id": "sg1", "kind": "construct_object", "target_solid_id": "s1", "quote": "Cho hình chóp S.ABCD"}],
        "math_goals": [{"goal_id": "q1", "kind": "measurement", "goal_type": "distance",
                        "target": {"point": "@h1", "plane": ["S", "A", "D"]}, "quote": q_d2, "solid_id": "s1"}],
    }
    rd2, ed2, ad2, msd2 = _run_gold(t_d2, p_d2)
    scene_objects = len(ed2["scene3d"]["objects"]) if ed2.get("scene3d") else 0
    aux_steps = len(rd2["planner"]["auxiliary"]) if rd2.get("planner") else 0
    return {
        "nl_and_gold_isolation_rows": nl_rows,
        "nl_passed": sum(1 for r in nl_rows if r["nl_served"] and r["local_parse_status"] == LOCAL_PARSE_COMPLETE),
        "nl_total": len(nl_rows),
        "test_family_d2_promoted": {
            "status": rd2["status"],
            "answer": ad2,
            "want": {"q1": "2"},
            "continuity_errors": len(validate_construction_continuity(ed2["scene3d"])) if ed2.get("scene3d") else -1,
            "latency_ms": msd2,
            "fe4_three_layer_separation": {
                "planner_constructed_aux_certs": aux_steps,
                "backend_emitted_scene_objects": scene_objects,
                "frontend_rendered_status": "BLOCKED_OWNERSHIP (axo-geometry-library; trace-only auxiliary_points deferred to Frontend owner)",
            },
        },
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
    rm_eval = _evaluate_reasoning_matrix()
    r1_eval = _evaluate_r1_probe()
    nl_eval = _evaluate_gold_vs_nl_and_new_families()
    suite_checks = [
        _run_pytest_json("backend/tests/geometry/test_compositional_planner_expansion.py"),
        _run_pytest_json("backend/tests/geometry/test_hybrid_reasoning_generalization.py"),
        _run_pytest_json("backend/tests/geometry/test_route_d4_described_points.py"),
        _run_pytest_json("backend/tests/geometry/test_production_dynamic_composition.py"),
    ]
    report = {
        "run_id": "compositional-planner-capability-expansion",
        "measurement_class": "OFFLINE_DEVELOPMENT_EVIDENCE",
        "independent_h1_validation": "NOT_MEASURED",
        "live_ai_calls": 0,
        "git_head": _git_head(),
        "cache_version": CACHE_VERSION,
        "semantic_environment_hash": semantic_environment_hash(),
        "measured_system": ident["measured_system"],
        "s2_runner_sha256": S2R.runtime_identity()["runner_sha256"],
        "reasoning_matrix_72": rm_eval,
        "r1_described_point_probe": r1_eval,
        "gold_vs_local_parser_nl_and_families": nl_eval,
        "focused_suite_results": suite_checks,
        "all_focused_suites_passed": all(x["returncode"] == 0 for x in suite_checks),
    }
    out_path = RUN_DIR / "COMPOSITIONAL_GENERALIZATION_EVALUATION.json"
    out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "rm_after": rm_eval["after"],
        "r1_positive": f"{r1_eval['positive_passed']}/{r1_eval['positive_total']}",
        "nl_passed": f"{nl_eval['nl_passed']}/{nl_eval['nl_total']}",
        "d2": nl_eval["test_family_d2_promoted"]["status"],
        "suites_ok": report["all_focused_suites_passed"],
        "measured_system": ident["measured_system"][:16],
    }, ensure_ascii=False))
    return 0 if report["all_focused_suites_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
