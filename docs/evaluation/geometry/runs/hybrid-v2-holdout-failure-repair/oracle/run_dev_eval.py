# -*- coding: utf-8 -*-
"""Run RED or GREEN evaluation on the 32-case development corpus (`new-development-corpus.json`).

Zero live provider calls (`ALLOW_LIVE_AI=0`).
Usage:
    python run_dev_eval.py <output_json_path> [--phase RED|GREEN]
"""
from __future__ import annotations

from copy import deepcopy
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

os.environ["ALLOW_LIVE_AI"] = "0"

HERE = Path(__file__).resolve().parent
RUN_DIR = HERE.parent
ROOT = RUN_DIR.parents[4]
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(HERE))

from app.ai.adapter4_route import ADAPTER_V4_VERSION, build_adapter4_response, run_typed_fact_next_v2_route  # noqa: E402
from app.simulation.geometry_functions.engine import ENGINE_VERSION, PLANE_SECTION_CERTIFICATE_VERSION  # noqa: E402
from app.simulation.geometry_functions.planner import PLANNER_VERSION  # noqa: E402
from app.simulation.geometry_functions.registry import REGISTRY_VERSION  # noqa: E402
from new_dev_oracle import ORACLE_TABLE  # noqa: E402


def _square(v) -> Fraction:
    if hasattr(v, "he") and hasattr(v, "can"):
        return Fraction(v.he) ** 2 * Fraction(v.can)
    return Fraction(v) ** 2


def _aux_point_leaks(r, scene: dict, text: str) -> list[str]:
    aux = set()
    for d in (r.planner or {}).get("auxiliary") or []:
        aux |= set(d.get("labels") or []) | set(d.get("feet") or [])
    aux = {a for a in aux if isinstance(a, str) and not re.search(rf"(?<![\w']){re.escape(a)}(?![\w'])", text)}
    if not aux:
        return []
    leaks = set()
    for o in scene.get("objects") or []:
        for key in ("name", "label", "display_label", "notation", "reference", "description"):
            s = o.get(key)
            if isinstance(s, str):
                for a in aux:
                    if re.search(rf"(?<![\w']){re.escape(a)}(?![\w'])", s):
                        leaks.add(f"{o.get('id')}.{key}:{a}")
    return sorted(leaks)


def evaluate_corpus(phase: str) -> dict:
    corpus_path = RUN_DIR / "new-development-corpus.json"
    corpus_bytes = corpus_path.read_bytes()
    corpus_sha256 = hashlib.sha256(corpus_bytes).hexdigest()
    corpus = json.loads(corpus_bytes.decode("utf-8"))

    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()

    rows = []
    pos_total = 0
    pos_served = 0
    pos_oracle_agree = 0
    neg_total = 0
    neg_refused = 0
    neg_code_match = 0
    wrong_served = 0
    cases_with_aux_leaks = []

    for case in corpus["cases"]:
        cid = case["id"]
        exp_status = case["expected_status"]
        payload = deepcopy(case["payload"])
        r = run_typed_fact_next_v2_route(payload)
        resp = build_adapter4_response(r, payload["problem_text"])
        rd = resp.get("route_d") or {}
        env = resp.get("envelope") or {}
        served = r.status == "SERVED" and rd.get("status") == "SERVED" and env.get("status") == "ok"
        code = None if served else ((rd.get("refusal") or {}).get("code") or r.code)
        detail = None if served else (r.reason or (rd.get("refusal") or {}).get("detail"))

        oracle_check = None
        aux_leaks = []
        if served:
            scene = env.get("scene3d") or {}
            aux_leaks = _aux_point_leaks(r, scene, payload["problem_text"])
            if aux_leaks:
                cases_with_aux_leaks.append(cid)

        if exp_status == "SERVED":
            pos_total += 1
            oracle_info = ORACLE_TABLE[cid]
            if served:
                pos_served += 1
                mismatches = []
                secs = rd.get("sections") or []
                if not secs:
                    mismatches.append("missing section in route_d.sections")
                else:
                    sec0 = secs[0]
                    v_count = len(sec0.get("vertices") or [])
                    if v_count != oracle_info["polygon_vertices"]:
                        mismatches.append(f"vertex_count {v_count} != oracle {oracle_info['polygon_vertices']}")
                    cert_cat = sec0.get("certificate_category", "DINH_CAT_CANH")
                    if cert_cat != oracle_info["certificate_category"]:
                        mismatches.append(f"certificate_category {cert_cat} != oracle {oracle_info['certificate_category']}")
                if oracle_info.get("area_sq") is not None:
                    if not r.answers:
                        mismatches.append("missing scalar answer")
                    else:
                        goal_id = next(iter(r.answers.keys()))
                        mem_val = r.exec_result.final_memory[f"kq_{goal_id}"]
                        got_sq = _square(mem_val)
                        exp_sq = Fraction(oracle_info["area_sq"])
                        if got_sq != exp_sq:
                            mismatches.append(f"area_sq {got_sq} != oracle {exp_sq}")
                        got_ans = r.answers[goal_id]
                        if got_ans != oracle_info["expected_answer"]:
                            mismatches.append(f"answer {got_ans} != oracle {oracle_info['expected_answer']}")
                oracle_check = {
                    "agree": len(mismatches) == 0,
                    "mismatches": mismatches,
                    "oracle_expected_answer": oracle_info.get("expected_answer"),
                    "oracle_area_sq": str(oracle_info["area_sq"]) if oracle_info.get("area_sq") is not None else None,
                    "oracle_polygon_vertices": oracle_info["polygon_vertices"],
                    "oracle_certificate_category": oracle_info["certificate_category"],
                }
                if len(mismatches) == 0:
                    pos_oracle_agree += 1
                else:
                    wrong_served += 1
        else:
            neg_total += 1
            if not served:
                neg_refused += 1
                if code in (case.get("expected_codes") or []):
                    neg_code_match += 1
            else:
                wrong_served += 1

        rows.append({
            "id": cid,
            "defect_family": case["defect_family"],
            "expected_status": exp_status,
            "served": served,
            "route_status": r.status,
            "adapter4_status": rd.get("status"),
            "code": code,
            "detail": detail,
            "expected_codes": case.get("expected_codes"),
            "oracle_check": oracle_check,
            "aux_point_leaks": aux_leaks,
        })

    return {
        "schema": "HOLDOUT_REPAIR_DEV_EVAL/1",
        "phase": phase,
        "live_provider_calls": 0,
        "git_head": head_sha,
        "corpus_sha256": corpus_sha256,
        "versions": {
            "registry": REGISTRY_VERSION,
            "planner": PLANNER_VERSION,
            "engine": ENGINE_VERSION,
            "adapter": ADAPTER_V4_VERSION,
            "section_certificate": PLANE_SECTION_CERTIFICATE_VERSION,
        },
        "summary": {
            "total_cases": len(rows),
            "positive_total": pos_total,
            "positive_served": pos_served,
            "positive_oracle_agree": pos_oracle_agree,
            "positive_false_refusals": pos_total - pos_served,
            "negative_total": neg_total,
            "negative_refused": neg_refused,
            "negative_expected_code_match": neg_code_match,
            "wrong_served_total": wrong_served,
            "cases_with_aux_point_leaks": cases_with_aux_leaks,
        },
        "cases": rows,
    }


if __name__ == "__main__":
    out_path = Path(sys.argv[1])
    phase_arg = "RED"
    if "--phase" in sys.argv:
        idx = sys.argv.index("--phase")
        phase_arg = sys.argv[idx + 1]
    res = evaluate_corpus(phase_arg)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    s = res["summary"]
    print(
        f"[{phase_arg}] pos_served={s['positive_served']}/{s['positive_total']} "
        f"(oracle_agree={s['positive_oracle_agree']}/{s['positive_total']}), "
        f"neg_refused={s['negative_refused']}/{s['negative_total']} "
        f"(code_match={s['negative_expected_code_match']}/{s['negative_total']}), "
        f"wrong_served={s['wrong_served_total']}, "
        f"aux_leak_cases={len(s['cases_with_aux_point_leaks'])}"
    )
    for c in res["cases"]:
        print(f"  {c['id']} ({c['defect_family']}, exp={c['expected_status']}): served={c['served']} code={c['code']} detail={c['detail']}")
