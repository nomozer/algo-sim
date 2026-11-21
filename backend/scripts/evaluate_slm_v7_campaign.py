# -*- coding: utf-8 -*-
"""AXO HYBRID /7 Evaluation, Ablation, Blind Holdout & CPU Performance Harness.

Runs 100% offline (`ALLOW_LIVE_AI = "0"`, `GEMINI_API_KEY = ""`, `external_ai_calls = 0`)
and writes machine-verified artifacts to:
  docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning/

Phases:
  - post_closure  -> SLM_POST_CLOSURE_EVALUATION.json (Config A vs B vs C on historical diagnostics)
  - ablation      -> SLM_V7_ABLATION.json (Config A vs B vs C vs D with B->C H1 & C->D H2)
  - blind_holdout -> SLM_V7_HOLDOUT_EVALUATION.json (Single-shot frozen evaluation on SLM_V7_HOLDOUT_112)
  - performance   -> SLM_V7_PERFORMANCE.json (Cold + warm uncached n=30 at threads=4,6,8 + separate cached)
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import statistics
import sys
import time
from typing import Any

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
RUN5_DIR = ROOT / "docs/evaluation/geometry/runs/slm-local-geometry-understanding"
RUN6_DIR = ROOT / "docs/evaluation/geometry/runs/specialized-geometry-extraction-slm-optimization"
OUT_DIR = ROOT / "docs/evaluation/geometry/runs/deterministic-geometry-language-closure-slm-finetuning"
OUT_DIR.mkdir(parents=True, exist_ok=True)

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(BACKEND / "scripts") not in sys.path:
    sys.path.insert(0, str(BACKEND / "scripts"))


def _load_mod(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


V6 = _load_mod("_v6_bench_for_v7", BACKEND / "scripts" / "benchmark_slm_v6_campaign.py")
ESC = V6.ESC

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("HYBRID_ROUTE_MODE", None)

from app.ai import adaptive_input_router as AIR  # noqa: E402
from app.ai.local_geometry_parser import clear_local_geometry_parser_cache, parse_geometry_problem_locally  # noqa: E402
from app.ai.local_slm_extractor import (  # noqa: E402
    LOCAL_SLM_EXTRACTOR_VERSION,
    SLM_COMPACT_SCHEMA_VERSION,
    SLM_GROUNDING_VALIDATOR_VERSION,
    run_local_slm_extraction,
)
from app.ai.local_slm_runtime import (  # noqa: E402
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LOCAL_SLM_CACHE_NAMESPACE,
    LOCAL_SLM_RUNTIME_VERSION,
    LocalSlmRuntime,
    get_shared_local_slm_extraction_cache,
    get_shared_local_slm_runtime,
    resolve_local_slm_model_spec,
)
from app.ai.slm_verified_normalizer import (  # noqa: E402
    SLM_VERIFIED_NORMALIZER_VERSION,
    normalize_for_slm_grounding,
)
from app.runtime_identity import runtime_identity, semantic_environment_hash  # noqa: E402


def _load_nh48() -> list[dict[str, Any]]:
    raw = json.loads((RUN6_DIR / "SLM_NEW_HOLDOUT_MANIFEST.json").read_text(encoding="utf-8"))
    items: list[dict[str, Any]] = []
    for c in raw.get("cases") or []:
        cid = c.get("case_id") or c.get("id")
        kind = str(c.get("kind") or ("positive" if c.get("expected_outcome") == "SERVED" else "negative"))
        items.append({
            "id": cid,
            "kind": kind,
            "expect_serve": kind == "positive",
            "text": c.get("text") or c.get("problem_text"),
            "oracle": c.get("oracle"),
            "stratum": c.get("family") or c.get("stratum") or "nh48",
            "is_typo": bool(c.get("is_typo", False)),
        })
    assert len(items) == 48, f"Expected 48 NH48 cases, got {len(items)}"
    return items


def _cohen_h(p1: float, p2: float) -> float:
    return round(2.0 * (math.asin(math.sqrt(max(0.0, min(1.0, p2)))) - math.asin(math.sqrt(max(0.0, min(1.0, p1))))), 4)


def _evaluate_v7_config_on_dataset(
    *,
    config_name: str,
    cases: list[dict[str, Any]],
    mode: str,  # "det" | "compact_clause"
    model_key: str,
    closure_mode: str,
    normalizer_version: str,
    runtime: LocalSlmRuntime | None,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    for c in cases:
        clear_local_geometry_parser_cache()
        text = c["text"]
        kind = c["kind"]
        t0 = time.perf_counter()
        if mode == "det":
            out = AIR.route_text_input(text, allow_live_ai=False)
            norm_changed = False
            norm_rules: list[str] = []
            norm_lp_complete = False
        else:
            norm_preview = normalize_for_slm_grounding(text, normalizer_version=normalizer_version)
            norm_changed = norm_preview.changed
            norm_rules = [s.rule_id for s in norm_preview.steps if s.validation_result == "VALIDATED_MEANING_PRESERVING"]
            norm_lp_complete = bool(
                norm_preview.changed
                and not norm_preview.typo_detected
                and parse_geometry_problem_locally(norm_preview.canonical_text).status == "LOCAL_PARSE_COMPLETE"
            )
            out = AIR.route_text_input_local_slm(
                text,
                model_key=model_key,
                strategy="compact_clause",
                runtime=runtime,
                allow_download=False,
                use_verified_normalizer=True,
                closure_mode=closure_mode,
                normalizer_version=normalizer_version,
                use_cache=False,
                cache_prompt=True,
            )
        wall_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        tel = V6._extract_outcome_telemetry(out)
        rd = out.response.get("route_d") or {}

        if kind == "positive":
            ok, ans, ce = ESC._grade_positive(out.status, out.response, str(c["oracle"]))
            wrong_served = (out.status == "SERVED" and not ok)
        else:
            ok = (out.status != "SERVED")
            ans = ESC._extract_answer_str(out.response) if out.status == "SERVED" else None
            ce = ESC.EUC._continuity_count(out.response.get("envelope") or {}) if out.status == "SERVED" else 0
            wrong_served = (out.status == "SERVED")

        # 9-bucket case-level attribution (`§13`)
        ref_code = str(tel.get("refusal_code") or "")
        ext_mode = str(rd.get("extraction_mode") or "")
        if wrong_served:
            attr = "INCORRECT_SERVED"
        elif kind == "negative":
            attr = "INVALID_OR_AMBIGUOUS_INPUT" if ok else "INCORRECT_SERVED"
        elif ok:
            if tel["chosen_route"] != "LOCAL_SLM_FALLBACK" and not tel["slm_invoked"]:
                attr = "PARSER_SOLVED"
            elif tel.get("grounding_status") == "NORMALIZED_LOCAL_PARSE_COMPLETE" or norm_lp_complete:
                attr = "RULE_RESCUED"
            else:
                attr = "SLM_RESCUED"
        else:
            if c.get("is_typo") or tel.get("failure_taxonomy") == "TYPO_REQUIRES_CONFIRMATION":
                attr = "INVALID_OR_AMBIGUOUS_INPUT"
            elif ref_code in ("UNSUPPORTED_CAPABILITY", "OUT_OF_SCOPE", "EXACT_DOMAIN_EXCEEDED"):
                attr = "DOWNSTREAM_UNSUPPORTED"
            elif ext_mode == "LOCAL_SLM_GROUNDING_REJECTED":
                attr = "GROUNDING_REJECTED"
            elif tel.get("validator_ok"):
                if ref_code in (
                    "QUOTE_NOT_IN_SOURCE",
                    "SOURCE_OBJECT_MISMATCH",
                    "PREDICATE_NOT_IN_QUOTE",
                    "ROLE_NOT_IN_QUOTE",
                    "PLANE_NOT_IN_QUOTE",
                    "UNGROUNDED_VALUE",
                    "SOURCE_PREMISE_UNREAD",
                    "CONDITIONAL_CLAUSE",
                    "UNSUPPORTED_BASE_SHAPE",
                ):
                    attr = "SOURCE_GATE_REJECTED"
                else:
                    attr = "MODEL_SEMANTIC_ERROR"
            else:
                attr = "MODEL_SEMANTIC_ERROR"

        rows.append({
            "id": c["id"],
            "kind": kind,
            "stratum": c.get("stratum"),
            "is_typo": bool(c.get("is_typo") or (c["id"] in V6.TYPO_IDS)),
            "status": out.status,
            "ok": ok,
            "wrong_served": wrong_served,
            "continuity_errors": ce,
            "answer": ans,
            "oracle": c.get("oracle"),
            "wall_ms": wall_ms,
            "norm_changed": norm_changed,
            "norm_rules": norm_rules,
            "norm_lp_complete": norm_lp_complete,
            "attribution_bucket": attr,
            **tel,
        })

    pos = [r for r in rows if r["kind"] == "positive"]
    pos_non_typo = [r for r in pos if not r["is_typo"]]
    neg = [r for r in rows if r["kind"] == "negative"]
    slm_rows = [r for r in rows if r["slm_invoked"]]
    pos_slm_rows = [r for r in pos if r["slm_invoked"]]
    attr_counts = dict(Counter(r["attribution_bucket"] for r in rows))

    pos_passed = sum(1 for r in pos if r["ok"])
    pos_nt_passed = sum(1 for r in pos_non_typo if r["ok"])
    neg_refused = sum(1 for r in neg if r["ok"])
    sg_rej = sum(1 for r in pos if r["attribution_bucket"] == "SOURCE_GATE_REJECTED")

    metrics = {
        "config_name": config_name,
        "model_key": "deterministic" if mode == "det" else model_key,
        "closure_mode": "det_v145" if mode == "det" else closure_mode,
        "normalizer_version": "none" if mode == "det" else normalizer_version,
        "positive_total": len(pos),
        "positive_passed": pos_passed,
        "positive_rate": round(pos_passed / max(1, len(pos)), 4),
        "positive_wilson_95ci": list(V6._wilson_ci(pos_passed, len(pos))),
        "non_typo_positive_total": len(pos_non_typo),
        "non_typo_positive_passed": pos_nt_passed,
        "non_typo_positive_rate": round(pos_nt_passed / max(1, len(pos_non_typo)), 4),
        "non_typo_wilson_95ci": list(V6._wilson_ci(pos_nt_passed, len(pos_non_typo))),
        "negative_total": len(neg),
        "negative_refused": neg_refused,
        "negative_refusal_rate": round(neg_refused / max(1, len(neg)), 4),
        "wrong_served_mode_a_leaks": sum(1 for r in rows if r["wrong_served"]),
        "scene3d_continuity_errors": sum(r["continuity_errors"] for r in rows),
        "parser_solved_count": attr_counts.get("PARSER_SOLVED", 0),
        "rule_rescued_count": attr_counts.get("RULE_RESCUED", 0),
        "slm_rescued_count": attr_counts.get("SLM_RESCUED", 0),
        "source_gate_rejected_positive": sg_rej,
        "slm_invoked_total": len(slm_rows),
        "slm_invoked_positive_total": len(pos_slm_rows),
        "schema_valid_slm_rate": round(sum(1 for r in slm_rows if r["parse_ok"]) / max(1, len(slm_rows)), 4),
        "source_grounded_slm_rate": round(sum(1 for r in slm_rows if r["validator_ok"]) / max(1, len(slm_rows)), 4),
        "attribution_counts": attr_counts,
        "slm_inference_latency_ms": V6._pct_stats([r["slm_inference_ms"] for r in slm_rows if r["slm_inference_ms"] is not None]),
        "total_e2e_latency_ms": V6._pct_stats([r["total_e2e_ms"] for r in rows]),
        "prompt_tokens": V6._pct_stats([r["prompt_tokens"] for r in slm_rows if r["prompt_tokens"] is not None]),
        "cached_prompt_tokens": V6._pct_stats([r["cached_prompt_tokens"] for r in slm_rows if r["cached_prompt_tokens"] is not None]),
        "completion_tokens": V6._pct_stats([r["completion_tokens"] for r in slm_rows if r["completion_tokens"] is not None]),
        "combined_rss_mib": V6._pct_stats([r["combined_rss_mib"] for r in slm_rows if r["combined_rss_mib"] is not None]),
    }
    return {"metrics": metrics, "rows": rows}


def _compute_slot_metrics_for_gold_splits(
    *,
    splits: list[tuple[str, list[dict[str, Any]]]],
    cfg_defs: list[tuple[str, str, str, str, str]],  # (name, mode, model_key, closure_mode, norm_ver)
    runtime: LocalSlmRuntime,
) -> dict[str, Any]:
    import diagnose_slm_v5_bottlenecks as D

    out: dict[str, Any] = {}
    for split_name, cases in splits:
        pos_cases = [c for c in cases if c["kind"] == "positive"]
        split_out: dict[str, Any] = {}
        for cname, mode, mkey, cmode, nver in cfg_defs:
            if mode == "det":
                continue
            ent_tp = ent_pred = ent_gold = 0
            pred_tp = pred_pred = pred_gold = 0
            arg_ok = arg_den = 0
            qty_ok = qty_den = 0
            tf_ok = tf_den = 0

            for c in pos_cases:
                cid, txt = c["id"], c["text"]
                gold = D.build_gold_payload(cid, txt)
                gold_ents = V6._entities_in_payload(gold)
                gold_prems = [V6._canon_premise(p) for p in gold.get("premises") or ()]
                gold_goals = [V6._canon_goal(g) for g in gold.get("math_goals") or ()]
                gold_kinds = Counter(k for k, _, _ in gold_prems)
                gold_args = {(k, e) for k, e, _ in gold_prems}
                gold_qtys = {(k, e, q) for k, e, q in gold_prems if q != ""}

                clear_local_geometry_parser_cache()
                det = AIR.route_text_input(txt, allow_live_ai=False)
                pred_payload: dict[str, Any] | None = None
                if det.status == "SERVED" and det.local_parse_result is not None:
                    pred_payload = det.local_parse_result.payload
                else:
                    ext = run_local_slm_extraction(
                        txt,
                        model_key=mkey,
                        strategy="compact_clause",
                        runtime=runtime,
                        allow_download=False,
                        use_verified_normalizer=True,
                        closure_mode=cmode,
                        normalizer_version=nver,
                        use_cache=False,
                        cache_prompt=True,
                    )
                    pred_payload = ext.canonical_payload

                pred_ents = V6._entities_in_payload(pred_payload)
                ent_tp += len(pred_ents & gold_ents)
                ent_pred += len(pred_ents)
                ent_gold += len(gold_ents)

                pred_prems = [V6._canon_premise(p) for p in (pred_payload or {}).get("premises") or ()]
                pred_goals = [V6._canon_goal(g) for g in (pred_payload or {}).get("math_goals") or ()]
                pred_kinds = Counter(k for k, _, _ in pred_prems)

                pred_tp += sum((gold_kinds & pred_kinds).values())
                pred_pred += len(pred_prems)
                pred_gold += len(gold_prems)

                pred_args_set = {(k, e) for k, e, _ in pred_prems}
                arg_ok += sum(1 for k, e in gold_args if (k, e) in pred_args_set)
                arg_den += len(gold_args)

                pred_qtys_set = {(k, e, q) for k, e, q in pred_prems if q != ""}
                qty_ok += sum(1 for k, e, q in gold_qtys if (k, e, q) in pred_qtys_set)
                qty_den += len(gold_qtys)

                tf_den += 1
                g_sol = "".join(sorted((gold.get("solids") or [{}])[0].get("notation", "").replace(".", "")))
                p_sols = (pred_payload or {}).get("solids") or []
                p_sol = "".join(sorted(p_sols[0].get("notation", "").replace(".", ""))) if p_sols else ""
                if pred_payload is not None and g_sol == p_sol and Counter(gold_prems) == Counter(pred_prems) and Counter(gold_goals) == Counter(pred_goals):
                    tf_ok += 1

            def _r(n: int, d: int) -> dict[str, Any]:
                return {"numerator": n, "denominator": d, "rate": round(n / max(1, d), 4)}

            split_out[cname] = {
                "entity_precision": _r(ent_tp, ent_pred),
                "entity_recall": _r(ent_tp, ent_gold),
                "predicate_precision": _r(pred_tp, pred_pred),
                "predicate_recall": _r(pred_tp, pred_gold),
                "argument_binding_accuracy": _r(arg_ok, arg_den),
                "quantity_binding_accuracy": _r(qty_ok, qty_den),
                "typed_facts_exact_match": _r(tf_ok, tf_den),
            }
        out[split_name] = split_out
    return out


def _pair_cmp(rows1: list[dict[str, Any]], rows2: list[dict[str, Any]], c1: str, c2: str) -> dict[str, Any]:
    pos1 = [a for a in rows1 if a["kind"] == "positive"]
    pos2 = [b for b in rows2 if b["kind"] == "positive"]
    gained = [b["id"] for a, b in zip(pos1, pos2) if not a["ok"] and b["ok"]]
    lost = [b["id"] for a, b in zip(pos1, pos2) if a["ok"] and not b["ok"]]
    p1 = sum(1 for a in pos1 if a["ok"]) / max(1, len(pos1))
    p2 = sum(1 for b in pos2 if b["ok"]) / max(1, len(pos2))
    return {
        "first_config": c1,
        "second_config": c2,
        "positive_total": len(pos1),
        "first_passed": sum(1 for a in pos1 if a["ok"]),
        "second_passed": sum(1 for b in pos2 if b["ok"]),
        "positive_both_pass": sum(1 for a, b in zip(pos1, pos2) if a["ok"] and b["ok"]),
        "positive_both_fail": sum(1 for a, b in zip(pos1, pos2) if not a["ok"] and not b["ok"]),
        "positive_first_only": len(lost),
        "positive_second_only": len(gained),
        "gained_case_ids": gained,
        "regressed_case_ids": lost,
        "net_delta_positive": len(gained) - len(lost),
        "risk_difference": round(p2 - p1, 4),
        "cohen_h": _cohen_h(p1, p2),
        "mcnemar_exact_p_two_sided": V6._mcnemar_exact_p(len(lost), len(gained)),
    }


def run_post_closure_phase(threads: int = 6) -> dict[str, Any]:
    holdout_40 = V6._load_holdout_40()
    nh48 = _load_nh48()
    cfg_defs = [
        ("config_a_deterministic_v145", "det", "deterministic", "det_v145", "none"),
        ("config_b_v6_compact_original", "compact_clause", DEFAULT_LOCAL_SLM_MODEL_KEY, "v6", "v1"),
        ("config_c_v7_closure_original_slm", "compact_clause", DEFAULT_LOCAL_SLM_MODEL_KEY, "v7", "v2"),
    ]
    datasets = [
        ("DEV_CALIBRATION_16", V6.DEV_CAL_16, "HISTORICAL_DIAGNOSTIC"),
        ("HOLDOUT_40", holdout_40, "HISTORICAL_DIAGNOSTIC"),
        ("SLM_NEW_HOLDOUT_48", nh48, "HISTORICAL_DIAGNOSTIC"),
    ]

    ds_results: dict[str, Any] = {}
    rt = LocalSlmRuntime(threads=threads, allow_download=False)
    try:
        for ds_name, ds_cases, ds_role in datasets:
            ds_out: dict[str, Any] = {"dataset_role": ds_role, "total_cases": len(ds_cases), "configs": {}}
            for cname, mode, mkey, cmode, nver in cfg_defs:
                print(f"[POST_CLOSURE] Running {cname} on {ds_name} ({len(ds_cases)} cases)...", flush=True)
                ds_out["configs"][cname] = _evaluate_v7_config_on_dataset(
                    config_name=cname,
                    cases=ds_cases,
                    mode=mode,
                    model_key=mkey,
                    closure_mode=cmode,
                    normalizer_version=nver,
                    runtime=None if mode == "det" else rt,
                )
            ds_out["paired_comparisons"] = {
                "c_vs_b_h1_deterministic_closure": _pair_cmp(
                    ds_out["configs"]["config_b_v6_compact_original"]["rows"],
                    ds_out["configs"]["config_c_v7_closure_original_slm"]["rows"],
                    "config_b_v6_compact_original",
                    "config_c_v7_closure_original_slm",
                ),
                "c_vs_a_over_det_v145": _pair_cmp(
                    ds_out["configs"]["config_a_deterministic_v145"]["rows"],
                    ds_out["configs"]["config_c_v7_closure_original_slm"]["rows"],
                    "config_a_deterministic_v145",
                    "config_c_v7_closure_original_slm",
                ),
            }
            ds_results[ds_name] = ds_out

        slot_metrics = _compute_slot_metrics_for_gold_splits(
            splits=[("DEV_CALIBRATION_16", V6.DEV_CAL_16), ("HOLDOUT_40", holdout_40)],
            cfg_defs=cfg_defs,
            runtime=rt,
        )
    finally:
        rt.shutdown()

    payload = {
        "schema": "slm-post-closure-evaluation/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "dataset_classification": "HISTORICAL_DIAGNOSTIC_ONLY_NOT_V7_HOLDOUT",
        "runtime_version": LOCAL_SLM_RUNTIME_VERSION,
        "extractor_version": LOCAL_SLM_EXTRACTOR_VERSION,
        "validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
        "normalizer_version": SLM_VERIFIED_NORMALIZER_VERSION,
        "cache_namespace": LOCAL_SLM_CACHE_NAMESPACE,
        "model_spec": {
            "model_key": DEFAULT_LOCAL_SLM_MODEL_KEY,
            "sha256": resolve_local_slm_model_spec(DEFAULT_LOCAL_SLM_MODEL_KEY).sha256,
        },
        "datasets": ds_results,
        "slot_level_metrics_on_gold_splits": slot_metrics,
    }
    out_path = OUT_DIR / "SLM_POST_CLOSURE_EVALUATION.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[POST_CLOSURE] Wrote {out_path}", flush=True)
    return payload


def run_ablation_phase(threads: int = 6) -> dict[str, Any]:
    holdout_40 = V6._load_holdout_40()
    nh48 = _load_nh48()
    cfg_defs = [
        ("config_a_deterministic_v145", "det", "deterministic", "det_v145", "none"),
        ("config_b_v6_compact_original", "compact_clause", DEFAULT_LOCAL_SLM_MODEL_KEY, "v6", "v1"),
        ("config_c_v7_closure_original_slm", "compact_clause", DEFAULT_LOCAL_SLM_MODEL_KEY, "v7", "v2"),
        ("config_d_v7_closure_finetuned_slm", "compact_clause", FINETUNED_LOCAL_SLM_MODEL_KEY, "v7", "v2"),
    ]
    datasets = [
        ("DEV_CALIBRATION_16", V6.DEV_CAL_16, "HISTORICAL_DIAGNOSTIC"),
        ("HOLDOUT_40", holdout_40, "HISTORICAL_DIAGNOSTIC"),
        ("SLM_NEW_HOLDOUT_48", nh48, "HISTORICAL_DIAGNOSTIC"),
    ]

    ds_results: dict[str, Any] = {}
    rt = LocalSlmRuntime(threads=threads, allow_download=False)
    try:
        for ds_name, ds_cases, ds_role in datasets:
            ds_out: dict[str, Any] = {"dataset_role": ds_role, "total_cases": len(ds_cases), "configs": {}}
            for cname, mode, mkey, cmode, nver in cfg_defs:
                print(f"[ABLATION] Running {cname} on {ds_name} ({len(ds_cases)} cases)...", flush=True)
                ds_out["configs"][cname] = _evaluate_v7_config_on_dataset(
                    config_name=cname,
                    cases=ds_cases,
                    mode=mode,
                    model_key=mkey,
                    closure_mode=cmode,
                    normalizer_version=nver,
                    runtime=None if mode == "det" else rt,
                )
            r_a = ds_out["configs"]["config_a_deterministic_v145"]["rows"]
            r_b = ds_out["configs"]["config_b_v6_compact_original"]["rows"]
            r_c = ds_out["configs"]["config_c_v7_closure_original_slm"]["rows"]
            r_d = ds_out["configs"]["config_d_v7_closure_finetuned_slm"]["rows"]
            ds_out["paired_comparisons"] = {
                "b_to_c_h1_deterministic_closure": _pair_cmp(r_b, r_c, "config_b_v6_compact_original", "config_c_v7_closure_original_slm"),
                "c_to_d_h2_finetuning_contribution": _pair_cmp(r_c, r_d, "config_c_v7_closure_original_slm", "config_d_v7_closure_finetuned_slm"),
                "a_to_d_total_local_gain": _pair_cmp(r_a, r_d, "config_a_deterministic_v145", "config_d_v7_closure_finetuned_slm"),
                "b_to_d_total_v7_over_v6": _pair_cmp(r_b, r_d, "config_b_v6_compact_original", "config_d_v7_closure_finetuned_slm"),
            }
            ds_results[ds_name] = ds_out

        slot_metrics = _compute_slot_metrics_for_gold_splits(
            splits=[("DEV_CALIBRATION_16", V6.DEV_CAL_16), ("HOLDOUT_40", holdout_40)],
            cfg_defs=cfg_defs,
            runtime=rt,
        )
    finally:
        rt.shutdown()

    payload = {
        "schema": "slm-v7-ablation/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "dataset_classification": "HISTORICAL_DIAGNOSTIC_ONLY",
        "models": {
            "original": resolve_local_slm_model_spec(DEFAULT_LOCAL_SLM_MODEL_KEY).__dict__,
            "finetuned": resolve_local_slm_model_spec(FINETUNED_LOCAL_SLM_MODEL_KEY).__dict__,
        },
        "datasets": ds_results,
        "slot_level_metrics_on_gold_splits": slot_metrics,
    }
    out_path = OUT_DIR / "SLM_V7_ABLATION.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[ABLATION] Wrote {out_path}", flush=True)
    return payload


def run_blind_holdout_phase(threads: int = 6) -> dict[str, Any]:
    man_path = OUT_DIR / "SLM_V7_HOLDOUT_MANIFEST.json"
    manifest = json.loads(man_path.read_text(encoding="utf-8"))
    raw_cases = manifest["cases"]
    cases: list[dict[str, Any]] = []
    for c in raw_cases:
        kind = str(c["kind"])
        cases.append({
            "id": c["case_id"],
            "kind": kind,
            "expect_serve": kind == "positive",
            "text": c["text"],
            "oracle": c.get("oracle"),
            "stratum": c["family"],
            "is_typo": bool(c.get("is_typo", False)),
        })

    cfg_defs = [
        ("config_a_deterministic_v145", "det", "deterministic", "det_v145", "none"),
        ("config_b_v6_compact_original", "compact_clause", DEFAULT_LOCAL_SLM_MODEL_KEY, "v6", "v1"),
        ("config_c_v7_closure_original_slm", "compact_clause", DEFAULT_LOCAL_SLM_MODEL_KEY, "v7", "v2"),
        ("config_d_v7_closure_finetuned_slm", "compact_clause", FINETUNED_LOCAL_SLM_MODEL_KEY, "v7", "v2"),
    ]
    cfg_results: dict[str, Any] = {}
    rt = LocalSlmRuntime(threads=threads, allow_download=False)
    try:
        for cname, mode, mkey, cmode, nver in cfg_defs:
            print(f"[BLIND_HOLDOUT] Single-shot evaluating {cname} on {len(cases)} cases...", flush=True)
            cfg_results[cname] = _evaluate_v7_config_on_dataset(
                config_name=cname,
                cases=cases,
                mode=mode,
                model_key=mkey,
                closure_mode=cmode,
                normalizer_version=nver,
                runtime=None if mode == "det" else rt,
            )
    finally:
        rt.shutdown()

    r_a = cfg_results["config_a_deterministic_v145"]["rows"]
    r_b = cfg_results["config_b_v6_compact_original"]["rows"]
    r_c = cfg_results["config_c_v7_closure_original_slm"]["rows"]
    r_d = cfg_results["config_d_v7_closure_finetuned_slm"]["rows"]

    by_family: dict[str, Any] = {}
    for fam in sorted({c["stratum"] for c in cases}):
        fd: dict[str, Any] = {}
        for cname, res in cfg_results.items():
            frows = [r for r in res["rows"] if r["stratum"] == fam]
            fpos = [r for r in frows if r["kind"] == "positive"]
            fneg = [r for r in frows if r["kind"] == "negative"]
            fd[cname] = {
                "total": len(frows),
                "positive_passed": sum(1 for r in fpos if r["ok"]),
                "positive_total": len(fpos),
                "negative_refused": sum(1 for r in fneg if r["ok"]),
                "negative_total": len(fneg),
            }
        by_family[fam] = fd

    payload = {
        "schema": "slm-v7-holdout-evaluation/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "single_shot": True,
        "external_ai_calls": 0,
        "manifest_sha256_lf": manifest.get("manifest_sha256_lf"),
        "frozen_candidate_sha256": manifest.get("frozen_candidate", {}).get("measured_system_sha256"),
        "configs": cfg_results,
        "paired_comparisons": {
            "b_to_c_h1_deterministic_closure": _pair_cmp(r_b, r_c, "config_b_v6_compact_original", "config_c_v7_closure_original_slm"),
            "c_to_d_h2_finetuning_contribution": _pair_cmp(r_c, r_d, "config_c_v7_closure_original_slm", "config_d_v7_closure_finetuned_slm"),
            "a_to_d_total_local_gain": _pair_cmp(r_a, r_d, "config_a_deterministic_v145", "config_d_v7_closure_finetuned_slm"),
            "b_to_d_total_v7_over_v6": _pair_cmp(r_b, r_d, "config_b_v6_compact_original", "config_d_v7_closure_finetuned_slm"),
        },
        "by_family": by_family,
    }
    out_path = OUT_DIR / "SLM_V7_HOLDOUT_EVALUATION.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[BLIND_HOLDOUT] Wrote {out_path}", flush=True)
    return payload


def run_performance_phase() -> dict[str, Any]:
    spec_ft = resolve_local_slm_model_spec(FINETUNED_LOCAL_SLM_MODEL_KEY)
    spec_orig = resolve_local_slm_model_spec(DEFAULT_LOCAL_SLM_MODEL_KEY)
    workloads = [
        {"id": V6.DEV_CAL_16[0]["id"], "len_tier": "short", "text": V6.DEV_CAL_16[0]["text"]},
        {"id": V6.DEV_CAL_16[4]["id"], "len_tier": "short", "text": V6.DEV_CAL_16[4]["text"]},
        {"id": V6.DEV_CAL_16[6]["id"], "len_tier": "short", "text": V6.DEV_CAL_16[6]["text"]},
        {"id": V6.DEV_CAL_16[2]["id"], "len_tier": "medium", "text": V6.DEV_CAL_16[2]["text"]},
        {"id": V6.DEV_CAL_16[5]["id"], "len_tier": "medium", "text": V6.DEV_CAL_16[5]["text"]},
        {"id": V6.DEV_CAL_16[8]["id"], "len_tier": "medium", "text": V6.DEV_CAL_16[8]["text"]},
        {"id": V6.DEV_CAL_16[9]["id"], "len_tier": "medium", "text": V6.DEV_CAL_16[9]["text"]},
        {"id": V6.DEV_CAL_16[1]["id"], "len_tier": "long", "text": V6.DEV_CAL_16[1]["text"]},
        {"id": V6.DEV_CAL_16[3]["id"], "len_tier": "long", "text": V6.DEV_CAL_16[3]["text"]},
        {"id": V6.DEV_CAL_16[10]["id"], "len_tier": "short_neg", "text": V6.DEV_CAL_16[10]["text"]},
    ]

    def _bench_warm(mkey: str, threads: int, n_runs: int) -> dict[str, Any]:
        rt = LocalSlmRuntime(threads=threads, allow_download=False)
        samples: list[dict[str, Any]] = []
        timeouts = 0
        crashes = 0
        try:
            clear_local_geometry_parser_cache()
            _ = AIR.route_text_input_local_slm(
                workloads[0]["text"], model_key=mkey, strategy="compact_clause",
                runtime=rt, allow_download=False, use_verified_normalizer=True,
                closure_mode="v7", normalizer_version="v2", use_cache=False, cache_prompt=True,
            )
            for idx in range(n_runs):
                w = workloads[idx % len(workloads)]
                clear_local_geometry_parser_cache()
                out = AIR.route_text_input_local_slm(
                    w["text"], model_key=mkey, strategy="compact_clause",
                    runtime=rt, allow_download=False, use_verified_normalizer=True,
                    closure_mode="v7", normalizer_version="v2", use_cache=False, cache_prompt=True,
                )
                tel = V6._extract_outcome_telemetry(out)
                if tel.get("refusal_code") == "LOCAL_SLM_TIMEOUT":
                    timeouts += 1
                if tel.get("refusal_code") == "LOCAL_SLM_PROCESS_CRASHED":
                    crashes += 1
                samples.append({"sample_idx": idx, "workload_id": w["id"], "status": out.status, **tel})
        finally:
            rt.shutdown()

        stage_keys = (
            "local_parse_ms", "preprocessing_ms", "prompt_build_ms", "queue_wait_ms",
            "server_load_time_ms", "prompt_eval_ms", "token_gen_ms", "json_decode_ms",
            "grounding_and_lowering_ms", "source_gate_planner_kernel_scene_ms",
            "slm_inference_ms", "total_e2e_ms",
        )
        return {
            "model_key": mkey,
            "threads": threads,
            "sample_count": len(samples),
            "timeout_rate": round(timeouts / max(1, len(samples)), 4),
            "crash_rate": round(crashes / max(1, len(samples)), 4),
            "stage_stats_ms": {k: V6._pct_stats([s[k] for s in samples]) for k in stage_keys},
            "tokens": {
                "prompt_tokens": V6._pct_stats([s["prompt_tokens"] for s in samples]),
                "cached_prompt_tokens": V6._pct_stats([s["cached_prompt_tokens"] for s in samples]),
                "completion_tokens": V6._pct_stats([s["completion_tokens"] for s in samples]),
                "tokens_per_sec": V6._pct_stats([s["tokens_per_sec"] for s in samples]),
            },
            "combined_rss_mib": V6._pct_stats([s["combined_rss_mib"] for s in samples]),
        }

    # 1. Cold start (n=10) on fine-tuned model
    cold_samples: list[dict[str, Any]] = []
    rt_cold = LocalSlmRuntime(threads=6, allow_download=False)
    try:
        for w in workloads:
            rt_cold.shutdown()
            clear_local_geometry_parser_cache()
            out = AIR.route_text_input_local_slm(
                w["text"], model_key=spec_ft.model_key, strategy="compact_clause",
                runtime=rt_cold, allow_download=False, use_verified_normalizer=True,
                closure_mode="v7", normalizer_version="v2", use_cache=False, cache_prompt=True,
            )
            cold_samples.append({"workload_id": w["id"], "status": out.status, **V6._extract_outcome_telemetry(out)})
    finally:
        rt_cold.shutdown()

    # 2. Warm uncached thread sweep (n=30 each for 4, 6, 8 threads on fine-tuned + 6 threads on original)
    thread_sweep = {
        "finetuned_threads_4_n30": _bench_warm(spec_ft.model_key, 4, 30),
        "finetuned_threads_6_n30": _bench_warm(spec_ft.model_key, 6, 30),
        "finetuned_threads_8_n30": _bench_warm(spec_ft.model_key, 8, 30),
        "original_threads_6_n30": _bench_warm(spec_orig.model_key, 6, 30),
    }

    # 3. Warm cached (n=30, strictly separate)
    cache = get_shared_local_slm_extraction_cache()
    cache.clear()
    rt_singleton = get_shared_local_slm_runtime()
    cache_samples: list[dict[str, Any]] = []
    try:
        for w in workloads:
            _ = AIR.route_text_input_local_slm(
                w["text"], model_key=spec_ft.model_key, strategy="compact_clause",
                allow_download=False, use_verified_normalizer=True,
                closure_mode="v7", normalizer_version="v2", use_cache=True, cache_prompt=True,
            )
        for idx in range(30):
            w = workloads[idx % len(workloads)]
            clear_local_geometry_parser_cache()
            t0 = time.perf_counter()
            out = AIR.route_text_input_local_slm(
                w["text"], model_key=spec_ft.model_key, strategy="compact_clause",
                allow_download=False, use_verified_normalizer=True,
                closure_mode="v7", normalizer_version="v2", use_cache=True, cache_prompt=True,
            )
            e2e_ms = round((time.perf_counter() - t0) * 1000.0, 3)
            env = (out.response.get("route_d") or {}).get("slm_grounding_envelope") or {}
            cache_samples.append({
                "sample_idx": idx,
                "workload_id": w["id"],
                "cache_hit": bool(env.get("cache_hit")),
                "total_e2e_ms": e2e_ms,
                "hybrid_execution_ms": round(float(out.telemetry.hybrid_execution_ms), 3),
            })
    finally:
        rt_singleton.shutdown()
        cache.clear()

    payload = {
        "schema": "slm-v7-performance/1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "external_ai_calls": 0,
        "physical_low_end": "NOT_MEASURED",
        "hardware_disclosure": {
            "host_os": platform.platform(),
            "machine": platform.machine(),
            "cpu_count": os.cpu_count(),
            "physical_4_6gb_ram_verified": False,
            "note": "Measured on Windows development host CPU (15.78 GiB RAM); physical 4-6 GiB RAM target device is NOT_MEASURED.",
        },
        "models": {
            "original": {"model_key": spec_orig.model_key, "sha256": spec_orig.sha256, "size_bytes": spec_orig.size_bytes},
            "finetuned": {"model_key": spec_ft.model_key, "sha256": spec_ft.sha256, "size_bytes": spec_ft.size_bytes},
        },
        "cold_start_finetuned_n10": {
            "sample_count": len(cold_samples),
            "server_load_time_ms": V6._pct_stats([s["server_load_time_ms"] for s in cold_samples]),
            "slm_inference_ms": V6._pct_stats([s["slm_inference_ms"] for s in cold_samples]),
            "total_e2e_ms": V6._pct_stats([s["total_e2e_ms"] for s in cold_samples]),
            "combined_rss_mib": V6._pct_stats([s["combined_rss_mib"] for s in cold_samples]),
        },
        "warm_uncached_thread_sweep": thread_sweep,
        "warm_cached_separate": {
            "disclaimer": "Cached inference latencies are reported strictly separately and never merged into uncached p95.",
            "sample_count": len(cache_samples),
            "all_cache_hits": all(s["cache_hit"] for s in cache_samples),
            "total_e2e_ms": V6._pct_stats([s["total_e2e_ms"] for s in cache_samples]),
            "hybrid_execution_ms": V6._pct_stats([s["hybrid_execution_ms"] for s in cache_samples]),
        },
    }
    out_path = OUT_DIR / "SLM_V7_PERFORMANCE.json"
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[PERFORMANCE] Wrote {out_path}", flush=True)
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="AXO HYBRID /7 evaluation harness")
    parser.add_argument("--phase", required=True, choices=["post_closure", "ablation", "blind_holdout", "performance"])
    parser.add_argument("--threads", type=int, default=6)
    args = parser.parse_args()

    if args.phase == "post_closure":
        run_post_closure_phase(threads=args.threads)
    elif args.phase == "ablation":
        run_ablation_phase(threads=args.threads)
    elif args.phase == "blind_holdout":
        run_blind_holdout_phase(threads=args.threads)
    elif args.phase == "performance":
        run_performance_phase()


if __name__ == "__main__":
    main()
