# -*- coding: utf-8 -*-
"""Run Wave 2 96-case POST_FEEDBACK_DEVELOPMENT_REGRESSION and W2-A10 scorer adjudication receipt
for W2-M5 Adapter /4 Category A Identity Repair.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
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
if str(WAVE2_RUN / "tools") not in sys.path:
    sys.path.insert(0, str(WAVE2_RUN / "tools"))


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, text=True).strip()


def run_wave2_post_feedback_regression() -> tuple[dict[str, Any], dict[str, Any]]:
    import evaluate_holdout_wave2 as EHW2
    from app.ai.adapter4_route import build_adapter4_response, run_typed_fact_next_v2_route

    with open(WAVE2_RUN / "inputs/holdout-wave2.json", "r", encoding="utf-8") as f:
        cases = json.load(f)["cases"]
    with open(WAVE2_RUN / "oracle/expected.json", "r", encoding="utf-8") as f:
        raw_exp = json.load(f)
        exp_map = raw_exp.get("expected_outcomes") or raw_exp
    with open(WAVE2_RUN / "tools/refusal_taxonomy.json", "r", encoding="utf-8") as f:
        tax = json.load(f)

    # 1. Run unmodified historical scorer (`score_observed_response`)
    raw_records = []
    route_outputs = {}
    for case in cases:
        cid = case["id"]
        exp = exp_map.get(cid)
        payload = deepcopy(case["payload"])
        r = run_typed_fact_next_v2_route(payload)
        resp = build_adapter4_response(deepcopy(r), payload["problem_text"])
        route_outputs[cid] = (r, resp)
        rec = EHW2.score_observed_response(case, exp, tax, r, resp)
        raw_records.append(rec)

    # 2. Adjudicated scorer: in `_check_section_boundary`, resolve `v["label"]` via `EHW2._find_point_xyz`
    # (which `evaluate_holdout_wave2.py` already defines at line 146 and calls at line 232, but omitted at line 184).
    orig_check_section_boundary = EHW2._check_section_boundary

    def _adjudicated_check_section_boundary(
        sec: dict[str, Any],
        td_sec: dict[str, Any],
        objects_by_id: dict[str, dict[str, Any]],
        exp: dict[str, Any],
        is_cat_b: bool,
    ) -> list[str]:
        from app.simulation.geometry_functions.engine import ir_name

        augmented = dict(objects_by_id)
        for v in sec.get("vertices") or []:
            lbl = v.get("label")
            if isinstance(lbl, str) and lbl and lbl not in augmented and ir_name(lbl) in objects_by_id:
                augmented[lbl] = objects_by_id[ir_name(lbl)]
        return orig_check_section_boundary(sec, td_sec, augmented, exp, is_cat_b)

    EHW2._check_section_boundary = _adjudicated_check_section_boundary
    try:
        adjudicated_records = []
        for case in cases:
            cid = case["id"]
            exp = exp_map.get(cid)
            r, resp = route_outputs[cid]
            rec = EHW2.score_observed_response(case, exp, tax, r, resp)
            adjudicated_records.append(rec)
    finally:
        EHW2._check_section_boundary = orig_check_section_boundary

    pos_raw = [x for x in raw_records if x["expected"] == "SERVE"]
    neg_raw = [x for x in raw_records if x["expected"] == "REFUSE"]
    pos_adj = [x for x in adjudicated_records if x["expected"] == "SERVE"]
    neg_adj = [x for x in adjudicated_records if x["expected"] == "REFUSE"]

    cat_counts = Counter(
        (x.get("certificate_category") or ["NONE"])[0]
        for x in pos_adj
        if x["outcome"] == "SERVED_CORRECT"
    )
    refusal_cat_counts = Counter(x.get("category") for x in neg_adj)

    regression_report = {
        "evaluation_label": "POST_FEEDBACK_DEVELOPMENT_REGRESSION",
        "not_a_blind_holdout": True,
        "git_head": _git_head(),
        "total_cases": len(cases),
        "positive_total": len(pos_adj),
        "negative_total": len(neg_adj),
        "raw_unmodified_historical_scorer": {
            "positive_served_correct": sum(1 for x in pos_raw if x["outcome"] == "SERVED_CORRECT"),
            "positive_false_refusal": sum(1 for x in pos_raw if x["outcome"] == "FALSE_REFUSAL"),
            "positive_wrong_served": sum(1 for x in pos_raw if x["outcome"] == "WRONG_SERVED"),
            "negative_safe_refusal": sum(1 for x in neg_raw if x["outcome"] in ("REFUSED_CORRECT_REASON", "REFUSED_REASON_DISAGREEMENT")),
            "negative_refused_correct_reason": sum(1 for x in neg_raw if x["outcome"] == "REFUSED_CORRECT_REASON"),
            "negative_refused_reason_disagreement": sum(1 for x in neg_raw if x["outcome"] == "REFUSED_REASON_DISAGREEMENT"),
            "negative_wrong_served": sum(1 for x in neg_raw if x["outcome"] == "WRONG_SERVED"),
            "note": (
                "W2-A07 is SERVED_CORRECT (47/48). W2-A10 is SERVED by product with exact polygon area_squared=504 "
                "and valid 4-cycle [BB', AA', DD', CC'], but evaluate_holdout_wave2.py:184 checks `v['label'] in objects_by_id` "
                "instead of resolving `ir_name(v['label'])` (`A_prime`), colliding poly_idx=0 for both A' and I."
            ),
        },
        "scorer_adjudicated": {
            "positive_served_correct": sum(1 for x in pos_adj if x["outcome"] == "SERVED_CORRECT"),
            "positive_false_refusal": sum(1 for x in pos_adj if x["outcome"] == "FALSE_REFUSAL"),
            "positive_wrong_served": sum(1 for x in pos_adj if x["outcome"] == "WRONG_SERVED"),
            "negative_safe_refusal": sum(1 for x in neg_adj if x["outcome"] in ("REFUSED_CORRECT_REASON", "REFUSED_REASON_DISAGREEMENT")),
            "negative_refused_correct_reason": sum(1 for x in neg_adj if x["outcome"] == "REFUSED_CORRECT_REASON"),
            "negative_refused_reason_disagreement": sum(1 for x in neg_adj if x["outcome"] == "REFUSED_REASON_DISAGREEMENT"),
            "negative_wrong_served": sum(1 for x in neg_adj if x["outcome"] == "WRONG_SERVED"),
            "category_a_dinh_cat_canh_served_correct": cat_counts.get("DINH_CAT_CANH", 0),
            "category_b_engine_derived_section_served_correct": cat_counts.get("ENGINE_DERIVED_SECTION", 0),
            "exact_oracle_agreement_count": sum(1 for x in pos_adj if not x.get("oracle_mismatches")),
            "learner_facing_source_identity_clean_count": sum(
                1 for x in adjudicated_records if not x.get("source_identity_leaks")
            ),
            "negative_refusal_category_distribution": dict(refusal_cat_counts),
        },
        "target_cases": {
            "W2-A07": next(x for x in pos_adj if x["id"] == "W2-A07"),
            "W2-A10_raw": next(x for x in pos_raw if x["id"] == "W2-A10"),
            "W2-A10_adjudicated": next(x for x in pos_adj if x["id"] == "W2-A10"),
        },
        "adjudicated_records": adjudicated_records,
    }

    r_a10, resp_a10 = route_outputs["W2-A10"]
    objs_a10 = {o["id"]: o for o in resp_a10["envelope"]["scene3d"]["objects"]}
    td_a10 = objs_a10["td_sec"]
    sec_a10 = resp_a10["route_d"]["sections"][0]
    w2_a10_receipt = {
        "case_id": "W2-A10",
        "historical_holdout_commit": "ecdc26b012c8ce80d53524a98dc75cdcb020079d",
        "historical_holdout_files_modified": False,
        "product_status": resp_a10["route_d"]["status"],
        "product_section_vertices": sec_a10["vertices"],
        "product_scene3d_section_polygon": td_a10["polygon"],
        "product_scene3d_vertex_sources": td_a10["vertex_sources"],
        "oracle_boundary": exp_map["W2-A10"]["boundary"],
        "oracle_area_squared": exp_map["W2-A10"]["area_squared"],
        "scorer_bug_location": (
            "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2/"
            "tools/evaluate_holdout_wave2.py:184-185"
        ),
        "scorer_bug_explanation": (
            "At line 146, evaluate_holdout_wave2.py defines `_find_point_xyz(objects_by_id, label)` to resolve primed "
            "labels (`A'` -> `A_prime` / `A′`) and calls it at line 232. However, at line 184 when computing `poly_idx` "
            "to sort `sec['vertices']` into `td_sec['polygon']` cyclic order, it writes `elif v.get('label') and v['label'] in objects_by_id:`, "
            "which is False for `A'` because `objects_by_id` is keyed by `A_prime`. Thus `A'` falls back to `idx_fallback = 0`, "
            "colliding with `I` (which is at `poly_raw[0]`, so `poly_idx = 0`), scrambling the valid 4-cycle "
            "`[I (BB'), A' (AA'), I2 (DD'), I1 (CC')]` into `[A' (AA'), I (BB'), I2 (DD'), I1 (CC')]`."
        ),
        "raw_scorer_verdict": next(x["outcome"] for x in pos_raw if x["id"] == "W2-A10"),
        "raw_scorer_mismatches": next(x["oracle_mismatches"] for x in pos_raw if x["id"] == "W2-A10"),
        "adjudicated_scorer_verdict": next(x["outcome"] for x in pos_adj if x["id"] == "W2-A10"),
        "adjudicated_scorer_mismatches": next(x["oracle_mismatches"] for x in pos_adj if x["id"] == "W2-A10"),
    }
    return regression_report, w2_a10_receipt


def main() -> None:
    results_dir = RUN_DIR / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    reg_report, w2_a10_receipt = run_wave2_post_feedback_regression()
    with open(results_dir / "wave2-post-feedback-regression.json", "w", encoding="utf-8") as f:
        json.dump(reg_report, f, ensure_ascii=False, indent=2)
    with open(results_dir / "w2-a10-scorer-adjudication-receipt.json", "w", encoding="utf-8") as f:
        json.dump(w2_a10_receipt, f, ensure_ascii=False, indent=2)

    adj = reg_report["scorer_adjudicated"]
    raw = reg_report["raw_unmodified_historical_scorer"]
    print(
        f"[WAVE2 REGRESSION] raw_pos={raw['positive_served_correct']}/48 "
        f"adjudicated_pos={adj['positive_served_correct']}/48 "
        f"neg_safe={adj['negative_safe_refusal']}/48 "
        f"(correct_reason={adj['negative_refused_correct_reason']}/48) "
        f"catA={adj['category_a_dinh_cat_canh_served_correct']} "
        f"catB={adj['category_b_engine_derived_section_served_correct']}"
    )


if __name__ == "__main__":
    main()
