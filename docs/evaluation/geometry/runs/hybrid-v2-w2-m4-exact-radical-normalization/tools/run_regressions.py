# -*- coding: utf-8 -*-
"""Run Source Gate /19 locked development regression and Wave 2 post-feedback 96-case regression."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

os.environ["ALLOW_LIVE_AI"] = "0"
sys.dont_write_bytecode = True

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "backend"))

SG_RUN = ROOT / "docs/evaluation/geometry/runs/hybrid-v2-wave2-source-gate-language-generalization"
HISTORY_W2 = "ecdc26b012c8ce80d53524a98dc75cdcb020079d"
HIST_W2_PATH = "docs/evaluation/geometry/runs/hybrid-v2-independent-vietnamese-section-holdout-wave2"

spec = importlib.util.spec_from_file_location("sg_eval", SG_RUN / "tools/evaluate_development.py")
sg_eval = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sg_eval)


def run_source_gate_regression() -> None:
    out_path = RUN / "results/source-gate-regression.json"
    if out_path.exists():
        raise FileExistsError(out_path)
    raw_bytes = (SG_RUN / "inputs/development.json").read_bytes()
    supp_bytes = (SG_RUN / "inputs/supplemental.json").read_bytes()
    adj_bytes = (SG_RUN / "results/development-adjudication.json").read_bytes()

    cases = json.loads(raw_bytes)["cases"]
    supplemental = json.loads(supp_bytes)["cases"]
    adjudication = json.loads(adj_bytes)["cases"]

    s = sg_eval.scorer()
    raw_rows = [sg_eval.evaluate_case(c, s) for c in cases]

    adjudicated_rows = []
    for c, r in zip(cases, raw_rows):
        row = deepcopy(r)
        if c["id"] in adjudication:
            corr = adjudication[c["id"]]
            adj_case = dict(
                deepcopy(c),
                expected_status=corr["adjudicated_expected_status"],
                oracle=corr["expected_oracle"],
            )
            row = sg_eval.evaluate_case(adj_case, s)
            row["adjudicated_from_raw_expected"] = corr["raw_expected_status"]
        adjudicated_rows.append(row)

    supp_rows = [sg_eval.evaluate_case(c, s) for c in supplemental]

    orig_positives = [r for c, r in zip(cases, raw_rows) if c["expected_status"] == "SERVED"]
    genuine_negatives = [
        r for c, r in zip(cases, raw_rows)
        if c["expected_status"] == "REFUSED" and c["id"] not in adjudication
    ]
    adjudicated_served = [r for r in adjudicated_rows if r["served"]]

    payload = {
        "schema": "w2-m4-source-gate-regression/1",
        "classification": "LOCKED_DEVELOPMENT_REGRESSION",
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "product_diff_sha256": hashlib.sha256(
            subprocess.check_output(["git", "diff", "--", "backend/app"], cwd=ROOT)
        ).hexdigest(),
        "development_corpus_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "supplemental_corpus_sha256": hashlib.sha256(supp_bytes).hexdigest(),
        "adjudication_sha256": hashlib.sha256(adj_bytes).hexdigest(),
        "live_provider_calls": 0,
        "raw_summary": {
            "overall": s._tally(raw_rows),
            "original_positives_served_correct": f"{sum(r['outcome'] == 'SERVED_CORRECT' for r in orig_positives)}/{len(orig_positives)}",
            "original_positives_false_refusal": f"{sum(r['outcome'] == 'FALSE_REFUSAL' for r in orig_positives)}/{len(orig_positives)}",
            "raw_negatives_refused": f"{sum(not r['served'] for c, r in zip(cases, raw_rows) if c['expected_status'] == 'REFUSED')}/37",
            "raw_wrong_served_labels": sum(r["outcome"] == "WRONG_SERVED" for r in raw_rows),
        },
        "adjudicated_summary": {
            "overall": s._tally(adjudicated_rows),
            "original_positives_served_correct": f"{sum(r['outcome'] == 'SERVED_CORRECT' for r in orig_positives)}/{len(orig_positives)}",
            "genuine_negatives_refused": f"{sum(not r['served'] for r in genuine_negatives)}/{len(genuine_negatives)}",
            "genuine_negatives_correct_reason": f"{sum(r['outcome'] == 'REFUSED_CORRECT_REASON' for r in genuine_negatives)}/{len(genuine_negatives)}",
            "genuine_wrong_served": sum(r["outcome"] == "WRONG_SERVED" for r in adjudicated_rows),
            "served_exact_oracle_agreement": f"{sum(not r.get('oracle_mismatches') for r in adjudicated_served)}/{len(adjudicated_served)}",
            "all_61_adjudicated_cases_match_expected": all(r["matches_expected"] for r in adjudicated_rows),
        },
        "supplemental_summary": {
            "overall": s._tally(supp_rows),
            "matches_expected": f"{sum(r['matches_expected'] for r in supp_rows)}/{len(supp_rows)}",
        },
        "dev_1_3_result": next(r for r in raw_rows if r["id"] == "DEV-1-3"),
        "raw_cases": raw_rows,
        "adjudicated_cases": adjudicated_rows,
        "supplemental_cases": supp_rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("x", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    print("Source Gate /19 regression:", json.dumps(payload["adjudicated_summary"], ensure_ascii=False))


def run_wave2_post_feedback_regression() -> None:
    out_path = RUN / "results/wave2-post-feedback-regression.json"
    if out_path.exists():
        raise FileExistsError(out_path)
    s = sg_eval.scorer()
    cases = json.loads(sg_eval.historical("inputs/holdout-wave2.json"))["cases"]
    expected = json.loads(sg_eval.historical("oracle/expected.json"))
    tax = json.loads(sg_eval.historical("tools/refusal_taxonomy.json"))
    rows = [s.score_case(c, expected.get(c["id"]), tax) for c in cases]
    for r in rows:
        if r.get("outcome") == "HARNESS_ERROR" or r.get("product_exception"):
            raise RuntimeError("Replay execution/scoring error; do not save raw exception content")
        r["classification"] = "POST_FEEDBACK_DEVELOPMENT_REGRESSION"
        r["expected_certificate_category"] = (expected.get(r["id"]) or {}).get("expected_certificate_category")

    def by(key: str) -> dict:
        return {
            k: s._tally([r for r in rows if (r.get(key) or "none") == k])
            for k in sorted({r.get(key) or "none" for r in rows})
        }

    served = [r for r in rows if r["expected"] == "SERVE" and r["served"]]
    remaining_false_refusals = [
        {
            "id": r["id"],
            "family": r["family"],
            "plane_relation": r["plane_relation"],
            "expected_certificate_category": r["expected_certificate_category"],
            "code": r["code"],
            "layer": r.get("layer"),
            "reason": r.get("reason"),
            "root_cause_mechanism": "W2-M5 (out-of-scope Adapter /4 primed-vertex label lookup KeyError: \"A'\")",
        }
        for r in rows
        if r["outcome"] == "FALSE_REFUSAL"
    ]
    result = {
        "schema": "w2-m4-wave2-post-feedback-regression/1",
        "classification": "POST_FEEDBACK_DEVELOPMENT_REGRESSION",
        "claim_ceiling": "NOT_INDEPENDENT_HOLDOUT",
        "historical_commit": HISTORY_W2,
        "corpus_git_sha256": hashlib.sha256(sg_eval.historical("inputs/holdout-wave2.json")).hexdigest(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "product_diff_sha256": hashlib.sha256(
            subprocess.check_output(["git", "diff", "--", "backend/app"], cwd=ROOT)
        ).hexdigest(),
        "live_provider_calls": 0,
        "overall": s._tally(rows),
        "exact_oracle_agreement": {
            "agree": sum(not r.get("oracle_mismatches") for r in served),
            "served": len(served),
        },
        "by_family": by("family"),
        "by_plane_relation": by("plane_relation"),
        "by_category": by("expected_certificate_category"),
        "remaining_first_refusal": dict(Counter(r["code"] for r in rows if r["outcome"] == "FALSE_REFUSAL")),
        "remaining_false_refusal_cases": remaining_false_refusals,
        "refusal_reason_mismatches": [r["id"] for r in rows if r["outcome"] == "REFUSED_REASON_DISAGREEMENT"],
        "w2_a04_result": next(r for r in rows if r["id"] == "W2-A04"),
        "cases": rows,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("x", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        "Wave 2 post-feedback regression:",
        json.dumps(
            {
                "overall": result["overall"],
                "exact_oracle_agreement": result["exact_oracle_agreement"],
                "by_category": result["by_category"],
                "remaining_first_refusal": result["remaining_first_refusal"],
            },
            ensure_ascii=False,
        ),
    )


if __name__ == "__main__":
    run_source_gate_regression()
    run_wave2_post_feedback_regression()
