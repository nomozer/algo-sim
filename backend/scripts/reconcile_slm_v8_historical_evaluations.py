# -*- coding: utf-8 -*-
"""Read-only historical reconciliation of /5, /6, and /7 SLM evaluations using `axo-math-evaluator/2`.

Never modifies any frozen historical JSON or script. Compares `EVI.same_value` (frozen)
against `slm_math_evaluator_v2.compare_math_expressions` (`axo-math-evaluator/2`) across
all stored evaluation rows, separating formatting/parser defects from expression errors
and genuine mathematical mismatches.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
ROOT = SCRIPTS_DIR.parents[1]
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from slm_math_evaluator_v2 import (  # noqa: E402
    EVALUATOR_VERSION,
    compare_math_expressions,
    infer_goal_kind_from_text,
)

OUT_DIR = ROOT / "docs/evaluation/geometry/runs/independent-validation-local-ai-production-readiness"
EVI_PATH = ROOT / "docs/evaluation/geometry/runs/controlled-vision-real-image-validation/tools/evaluate_images.py"


def _load_evi():
    spec = importlib.util.spec_from_file_location("frozen_evaluate_images", str(EVI_PATH))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _lf_sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def _infer_goal_kind_from_text(text: str | None) -> str | None:
    return infer_goal_kind_from_text(text)


def _wilson_ci95(k: int, n: int) -> list[float]:
    if n <= 0:
        return [0.0, 0.0]
    z = 1.959963984540054
    p = k / n
    denom = 1.0 + z * z / n
    center = (p + z * z / (2.0 * n)) / denom
    half = z * math.sqrt((p * (1.0 - p) + z * z / (4.0 * n)) / n) / denom
    return [round(max(0.0, center - half), 4), round(min(1.0, center + half), 4)]


def _mcnemar_exact(b01: int, b10: int) -> float:
    n = b01 + b10
    if n == 0:
        return 1.0
    k = min(b01, b10)
    tail = sum(math.comb(n, i) for i in range(k + 1)) / (2 ** n)
    return round(min(1.0, 2.0 * tail), 6)


def _reconcile_rows(
    evi: Any,
    rows: list[dict[str, Any]],
    *,
    text_by_id: dict[str, str] | None = None,
    answer_key: str = "answer",
    oracle_key: str = "oracle",
    status_key: str = "status",
    ok_key: str = "ok",
    id_key: str = "id",
) -> dict[str, Any]:
    raw_pos_ok = 0
    v2_pos_ok = 0
    pos_total = 0
    neg_total = 0
    neg_safe = 0
    wrong_served_v2 = 0
    discrepancies: list[dict[str, Any]] = []
    error_breakdown = {
        "FORMAT_MISMATCH_EVI_BUG": 0,
        "TRUE_MATHEMATICAL_ERROR": 0,
        "WRONG_TRIG_FUNCTION_OR_KIND": 0,
        "UNPARSEABLE": 0,
    }

    for row in rows:
        cid = str(row.get(id_key) or row.get("case_id") or "")
        is_pos = (row.get("kind") == "positive") if ("kind" in row) else bool(row.get("expect_serve", True))
        status = row.get(status_key)
        raw_ok = bool(row.get(ok_key))
        ans = row.get(answer_key)
        ora = row.get(oracle_key)
        goal_kind = _infer_goal_kind_from_text((text_by_id or {}).get(cid))

        if not is_pos:
            neg_total += 1
            if status != "SERVED":
                neg_safe += 1
            else:
                wrong_served_v2 += 1
            continue

        pos_total += 1
        if raw_ok:
            raw_pos_ok += 1

        if status != "SERVED" or ora is None or ans is None:
            v2_ok = bool(status == "SERVED" and ora is None)
            if v2_ok:
                v2_pos_ok += 1
            continue

        evi_val = evi.same_value(str(ans), str(ora))
        v2_res = compare_math_expressions(str(ans), str(ora), goal_kind=goal_kind)
        v2_res_untyped = compare_math_expressions(str(ans), str(ora), goal_kind=None)
        v2_ok = bool(v2_res.matched)

        if v2_ok:
            v2_pos_ok += 1
        else:
            wrong_served_v2 += 1
            if v2_res.matched is None:
                error_breakdown["UNPARSEABLE"] += 1
            elif v2_res.verdict_code in ("MISMATCH_WRONG_TRIG_FUNCTION", "MISMATCH_SCALAR_VS_TRIG", "MISMATCH_GOAL_KIND", "MISMATCH_DIMENSION_POWER"):
                error_breakdown["WRONG_TRIG_FUNCTION_OR_KIND"] += 1
            else:
                error_breakdown["TRUE_MATHEMATICAL_ERROR"] += 1

        if raw_ok != v2_ok or bool(evi_val) != v2_ok:
            cat = "FORMAT_MISMATCH_EVI_BUG" if (evi_val is None and v2_ok) else "OTHER_CHANGE"
            if cat == "FORMAT_MISMATCH_EVI_BUG":
                error_breakdown["FORMAT_MISMATCH_EVI_BUG"] += 1
            discrepancies.append({
                "case_id": cid,
                "status": status,
                "answer": str(ans),
                "oracle": str(ora),
                "inferred_goal_kind": goal_kind,
                "recorded_raw_ok": raw_ok,
                "evi_same_value": evi_val,
                "v2_matched": v2_res.matched,
                "v2_verdict_code": v2_res.verdict_code,
                "v2_reason": v2_res.reason,
                "v2_untyped_matched": v2_res_untyped.matched,
                "classification": cat,
            })

    return {
        "positives_total": pos_total,
        "negatives_total": neg_total,
        "raw_positive_correct": raw_pos_ok,
        "raw_positive_rate": round(raw_pos_ok / pos_total, 4) if pos_total else None,
        "v2_positive_correct": v2_pos_ok,
        "v2_positive_rate": round(v2_pos_ok / pos_total, 4) if pos_total else None,
        "v2_positive_wilson95": _wilson_ci95(v2_pos_ok, pos_total),
        "negative_safe_refusal": neg_safe,
        "wrong_served_v2": wrong_served_v2,
        "delta_positive_cases": v2_pos_ok - raw_pos_ok,
        "error_breakdown": error_breakdown,
        "discrepancies": discrepancies,
    }


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    evi = _load_evi()

    v7_manifest_p = ROOT / "docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_MANIFEST.json"
    v7_holdout_p = ROOT / "docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_HOLDOUT_EVALUATION.json"
    v7_ablation_p = ROOT / "docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/SLM_V7_ABLATION.json"
    v6_new_p = ROOT / "docs/evaluation/geometry/runs/specialized-geometry-extraction-slm-optimization/SLM_NEW_HOLDOUT_EVALUATION.json"
    v6_abl_p = ROOT / "docs/evaluation/geometry/runs/specialized-geometry-extraction-slm-optimization/SLM_EXTRACTION_ABLATION.json"
    v5_ext_p = ROOT / "docs/evaluation/geometry/runs/slm-local-geometry-understanding/SLM_EXTRACTION_EVALUATION.json"
    v5_base_p = ROOT / "docs/evaluation/geometry/runs/slm-local-geometry-understanding/SLM_BASELINE_COMPARISON.json"

    source_hashes_before = {
        str(p.relative_to(ROOT)).replace("\\", "/"): _lf_sha256(p)
        for p in [EVI_PATH, v7_manifest_p, v7_holdout_p, v7_ablation_p, v6_new_p, v6_abl_p, v5_ext_p, v5_base_p]
    }

    m7 = json.loads(v7_manifest_p.read_text(encoding="utf-8"))
    v7_texts = {c["case_id"]: c["text"] for c in m7["cases"]}
    v7_eval = json.loads(v7_holdout_p.read_text(encoding="utf-8"))

    v7_reconciled: dict[str, Any] = {}
    v7_row_maps: dict[str, dict[str, dict[str, Any]]] = {}
    for cfg_name, cfg_obj in v7_eval["configs"].items():
        rec = _reconcile_rows(evi, cfg_obj["rows"], text_by_id=v7_texts)
        v7_reconciled[cfg_name] = rec
        v7_row_maps[cfg_name] = {r["id"]: r for r in cfg_obj["rows"]}

    # Paired McNemar on corrected v2 scores between Configs A, B, C, D (positives n=80)
    def paired_pos(c1: str, c2: str) -> dict[str, Any]:
        gained, lost = [], []
        both_pass = both_fail = 0
        for cid, r1 in v7_row_maps[c1].items():
            if r1["kind"] != "positive":
                continue
            r2 = v7_row_maps[c2][cid]
            ok1 = r1["status"] == "SERVED" and bool(compare_math_expressions(str(r1["answer"]), str(r1["oracle"]), goal_kind=_infer_goal_kind_from_text(v7_texts.get(cid))).matched)
            ok2 = r2["status"] == "SERVED" and bool(compare_math_expressions(str(r2["answer"]), str(r2["oracle"]), goal_kind=_infer_goal_kind_from_text(v7_texts.get(cid))).matched)
            if ok1 and ok2:
                both_pass += 1
            elif not ok1 and not ok2:
                both_fail += 1
            elif not ok1 and ok2:
                gained.append(cid)
            else:
                lost.append(cid)
        return {
            "gained": gained,
            "lost": lost,
            "b01_gained": len(gained),
            "b10_lost": len(lost),
            "both_pass": both_pass,
            "both_fail": both_fail,
            "mcnemar_exact_p": _mcnemar_exact(len(gained), len(lost)),
        }

    v7_paired_v2 = {
        "b_to_c_h1_deterministic_closure": paired_pos("config_b_v6_compact_original", "config_c_v7_closure_original_slm"),
        "c_to_d_h2_finetuning_contribution": paired_pos("config_c_v7_closure_original_slm", "config_d_v7_closure_finetuned_slm"),
        "a_to_d_total_local_gain": paired_pos("config_a_deterministic_v145", "config_d_v7_closure_finetuned_slm"),
        "b_to_d_total_v7_over_v6": paired_pos("config_b_v6_compact_original", "config_d_v7_closure_finetuned_slm"),
    }

    # Reconcile /7 SLM_V7_ABLATION datasets
    v7_abl = json.loads(v7_ablation_p.read_text(encoding="utf-8"))
    v7_abl_rec: dict[str, Any] = {}
    for dname, dobj in v7_abl["datasets"].items():
        v7_abl_rec[dname] = {}
        for cname, cobj in dobj["configs"].items():
            v7_abl_rec[dname][cname] = _reconcile_rows(evi, cobj["rows"])

    # Reconcile /6 SLM_NEW_HOLDOUT_EVALUATION & SLM_EXTRACTION_ABLATION
    v6_new = json.loads(v6_new_p.read_text(encoding="utf-8"))
    v6_new_rec = {cname: _reconcile_rows(evi, cobj["rows"]) for cname, cobj in v6_new["configs"].items()}

    v6_abl = json.loads(v6_abl_p.read_text(encoding="utf-8"))
    v6_abl_rec: dict[str, Any] = {}
    for dname, dobj in v6_abl["datasets"].items():
        v6_abl_rec[dname] = {cname: _reconcile_rows(evi, cobj["rows"]) for cname, cobj in dobj["configs"].items()}

    # Reconcile /5 SLM_EXTRACTION_EVALUATION
    v5_ext = json.loads(v5_ext_p.read_text(encoding="utf-8"))
    v5_ext_rec = {mname: _reconcile_rows(evi, mobj["rows"]) for mname, mobj in v5_ext["models"].items()}

    # Reconcile /5 SLM_BASELINE_COMPARISON suites (NC_NL, DEV37, COMP112, etc.)
    v5_base = json.loads(v5_base_p.read_text(encoding="utf-8"))
    v5_base_rec: dict[str, Any] = {}
    for sname, sobj in v5_base["suites"].items():
        rows = sobj.get("rows") or []
        if not rows or "oracle" not in rows[0]:
            continue
        rec_a = _reconcile_rows(evi, rows, answer_key="config_a_answer", status_key="config_a_status", ok_key="config_a_ok")
        rec_b = _reconcile_rows(evi, rows, answer_key="config_b_answer", status_key="config_b_status", ok_key="config_b_ok")
        v5_base_rec[sname] = {"config_a": rec_a, "config_b": rec_b}

    source_hashes_after = {
        str(p.relative_to(ROOT)).replace("\\", "/"): _lf_sha256(p)
        for p in [EVI_PATH, v7_manifest_p, v7_holdout_p, v7_ablation_p, v6_new_p, v6_abl_p, v5_ext_p, v5_base_p]
    }
    assert source_hashes_before == source_hashes_after, "Frozen artifact hash mutated!"

    # Also test exactness of the 5 historical `v7h_p7_06..10` cases explicitly
    v7h_p7_cases = []
    for cid in ["v7h_p7_06", "v7h_p7_07", "v7h_p7_08", "v7h_p7_09", "v7h_p7_10"]:
        row_d = v7_row_maps["config_d_v7_closure_finetuned_slm"][cid]
        res_typed = compare_math_expressions(str(row_d["answer"]), str(row_d["oracle"]), goal_kind="angle")
        v7h_p7_cases.append({
            "case_id": cid,
            "text": v7_texts[cid],
            "answer": row_d["answer"],
            "oracle": row_d["oracle"],
            "evi_same_value": evi.same_value(str(row_d["answer"]), str(row_d["oracle"])),
            "v2_result": {
                "matched": res_typed.matched,
                "verdict_code": res_typed.verdict_code,
                "actual_kind": res_typed.actual_kind,
                "oracle_kind": res_typed.oracle_kind,
                "canonical_actual": res_typed.canonical_actual,
                "canonical_oracle": res_typed.canonical_oracle,
                "reason": res_typed.reason,
            },
        })

    out_payload = {
        "schema": "slm-evaluator-reconciliation/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "evaluator_version": EVALUATOR_VERSION,
        "evi_frozen_source": str(EVI_PATH.relative_to(ROOT)).replace("\\", "/"),
        "frozen_artifacts_unmodified": True,
        "frozen_artifact_lf_sha256": source_hashes_after,
        "root_cause": {
            "location": "docs/evaluation/geometry/runs/controlled-vision-real-image-validation/tools/evaluate_images.py:85-91",
            "defect": "EVI.same_value matched `left` against `cos²=...` and forced `right` (oracle) to match `N°`, returning None whenever `oracle` was also `cos²=...`, asymmetric in arguments, float-based at a in {1.3, 2.1}, missing sin/tan/cos(2x), and unchecked by goal_kind.",
            "secondary_nl_eval_scoring_defect": "backend/scripts/nl_eval_scoring.py:58 strips `^cos²=` unconditionally (conflating trig ratio with untagged scalar `1/2`), rejects degrees `45°`, and rejects symbolic `a`.",
            "ownership_status": "BLOCKED_OWNERSHIP / FROZEN_RUN_ARTIFACT (evaluate_images.py kept byte-immutable; replacement implemented as versioned evaluator `axo-math-evaluator/2` in backend/scripts/slm_math_evaluator_v2.py)",
        },
        "v7h_p7_06_to_10_case_level_evidence": v7h_p7_cases,
        "slm_v7_holdout_112": {
            "configs": v7_reconciled,
            "paired_comparisons_v2": v7_paired_v2,
            "summary_raw_vs_corrected_positives_of_80": {
                k: {
                    "raw": f"{v['raw_positive_correct']}/{v['positives_total']}",
                    "corrected_v2": f"{v['v2_positive_correct']}/{v['positives_total']}",
                    "corrected_rate": v["v2_positive_rate"],
                    "wilson_95_ci": v["v2_positive_wilson95"],
                    "wrong_served_v2": v["wrong_served_v2"],
                }
                for k, v in v7_reconciled.items()
            },
        },
        "slm_v7_ablation_reconciliation": v7_abl_rec,
        "slm_v6_new_holdout_48_reconciliation": v6_new_rec,
        "slm_v6_ablation_reconciliation": v6_abl_rec,
        "slm_v5_extraction_reconciliation": v5_ext_rec,
        "slm_v5_baseline_comparison_reconciliation": v5_base_rec,
    }

    out_path = OUT_DIR / "EVALUATOR_RECONCILIATION.json"
    out_path.write_text(json.dumps(out_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # Print crisp audit summary
    print("=== SLM_V7_HOLDOUT_112 Raw vs Corrected (`axo-math-evaluator/2`) ===")
    for k, v in out_payload["slm_v7_holdout_112"]["summary_raw_vs_corrected_positives_of_80"].items():
        print(f"  {k}: raw={v['raw']} -> corrected_v2={v['corrected_v2']} ({v['corrected_rate']:.2%}, CI={v['wilson_95_ci']}), wrong_served={v['wrong_served_v2']}")
    print("Paired C->D (v2):", v7_paired_v2["c_to_d_h2_finetuning_contribution"])
    # Check if ANY non-v7h_p7 discrepancy exists anywhere else in /5, /6, /7
    other_diffs = []
    for section_name, section in [
        ("v7_ablation", v7_abl_rec),
        ("v6_new_holdout", v6_new_rec),
        ("v6_ablation", v6_abl_rec),
        ("v5_extraction", v5_ext_rec),
        ("v5_baseline", v5_base_rec),
    ]:
        def scan_disc(obj, prefix):
            if isinstance(obj, dict):
                if "discrepancies" in obj and obj["discrepancies"]:
                    other_diffs.append((prefix, len(obj["discrepancies"]), obj["discrepancies"][:2]))
                for kk, vv in obj.items():
                    scan_disc(vv, f"{prefix}.{kk}")
        scan_disc(section, section_name)
    print("Other discrepancies across /5, /6, /7 ablation/baseline:", len(other_diffs), other_diffs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
