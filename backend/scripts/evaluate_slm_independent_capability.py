# -*- coding: utf-8 -*-
"""Isolated evaluation of AxoV9 SLM independent capability (no deterministic parser bypass).

Forces ``ALLOW_LIVE_AI=0`` and strips ``GEMINI_API_KEY`` prior to product imports,
runs ``v3`` verified normalization + source-rewrite safety verification, calls
``run_local_slm_extraction(..., allow_parser_reconcile=False, use_cache=False)``
without invoking the deterministic geometry parser router, executes ``run_hybrid_offline``
(Source Gate -> Planner -> Exact Kernel -> Adapter /4), and validates every served
Scene3D independently via ``scene_oracle.validate``.
"""
from __future__ import annotations

import os

os.environ["ALLOW_LIVE_AI"] = "0"
os.environ.pop("GEMINI_API_KEY", None)

import argparse
import importlib.util
import json
from pathlib import Path
import sys
import time
from typing import Any


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.ai.adaptive_input_router import _verify_canonical_against_original_source  # noqa: E402
from app.ai.hybrid_offline import hybrid_offline_policy, run_hybrid_offline  # noqa: E402
from app.ai.local_slm_extractor import detect_prompt_injection, run_local_slm_extraction  # noqa: E402
from app.ai.slm_verified_normalizer import normalize_for_slm_grounding  # noqa: E402
from app.ai.typed_fact_next_extraction import ReplayExtractor  # noqa: E402


AUDIT_SCHEMA_VERSION = "axo-slm-independent-capability-audit/1"
SCENE_ORACLE_PATH = REPO_ROOT / "docs/evaluation/geometry/harness/live-acceptance/scene_oracle.py"


def _load_scene_oracle():
    spec = importlib.util.spec_from_file_location("axo_live_scene_oracle", SCENE_ORACLE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load scene_oracle from {SCENE_ORACLE_PATH}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _has_parser_reconcile(accepted_ops: list[Any]) -> bool:
    for item in accepted_ops or ():
        if item == "parser_reconcile":
            return True
        if isinstance(item, dict) and item.get("op") == "parser_reconcile":
            return True
    return False


def _evaluate_case(
    case: dict[str, Any],
    *,
    stratum: str,
    pol: Any,
    scene_oracle_mod: Any,
) -> dict[str, Any]:
    cid = str(case.get("case_id") or "")
    orig_text = str(case.get("original_input") or case.get("problem_text") or "")
    t0 = time.perf_counter()

    inj = detect_prompt_injection(orig_text)
    if inj is not None:
        return {
            "case_id": cid,
            "stratum": stratum,
            "expected_behavior": case.get("expected_behavior"),
            "stage": "prompt_injection_guard",
            "slm_invoked": False,
            "slm_ok": False,
            "extracted_ok": False,
            "grounded_ok": False,
            "served": False,
            "verified_scene": False,
            "safe_refused": stratum == "negative",
            "reason_code": "UNGROUNDED_VALUE",
            "failure_taxonomy": "PROMPT_INJECTION_REJECTED",
            "scene_validation": "NOT_SERVED",
            "numeric": None,
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        }

    v3 = normalize_for_slm_grounding(orig_text, normalizer_version="v3")
    if v3.typo_detected:
        return {
            "case_id": cid,
            "stratum": stratum,
            "expected_behavior": case.get("expected_behavior"),
            "stage": "v3_typo_guard",
            "slm_invoked": False,
            "slm_ok": False,
            "extracted_ok": False,
            "grounded_ok": False,
            "served": False,
            "verified_scene": False,
            "safe_refused": stratum == "negative",
            "reason_code": "AMBIGUOUS_FACT",
            "failure_taxonomy": "TYPO_REQUIRES_CONFIRMATION",
            "scene_validation": "NOT_SERVED",
            "numeric": None,
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        }

    if v3.changed and v3.canonical_text != orig_text:
        ok_src, err_src = _verify_canonical_against_original_source(orig_text, v3)
        if not ok_src:
            return {
                "case_id": cid,
                "stratum": stratum,
                "expected_behavior": case.get("expected_behavior"),
                "stage": "v3_original_source_safety",
                "slm_invoked": False,
                "slm_ok": False,
                "extracted_ok": False,
                "grounded_ok": False,
                "served": False,
                "verified_scene": False,
                "safe_refused": stratum == "negative",
                "reason_code": "AMBIGUOUS_FACT",
                "failure_taxonomy": str(err_src or "SEMANTIC_REWRITE_SAFETY_REJECTED"),
                "scene_validation": "NOT_SERVED",
                "numeric": None,
                "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
            }

    work_text = v3.canonical_text if v3.changed else orig_text
    slm = run_local_slm_extraction(
        work_text,
        model_key="v9",
        closure_mode="v9",
        normalizer_version="v3",
        use_cache=False,
        allow_download=False,
        allow_parser_reconcile=False,
    )
    env = slm.grounding_envelope or {}
    if _has_parser_reconcile(list(env.get("accepted_ops") or [])):
        raise RuntimeError(f"Isolation violation on {cid}: parser_reconcile observed despite allow_parser_reconcile=False")

    if not slm.ok or slm.canonical_payload is None:
        return {
            "case_id": cid,
            "stratum": stratum,
            "expected_behavior": case.get("expected_behavior"),
            "stage": "local_slm_extraction",
            "model_key": slm.model_key,
            "model_sha256": slm.model_sha256,
            "slm_invoked": bool(env.get("slm_invoked", True)),
            "slm_ok": False,
            "extracted_ok": False,
            "grounded_ok": False,
            "served": False,
            "verified_scene": False,
            "safe_refused": stratum == "negative",
            "reason_code": slm.reason_code,
            "failure_taxonomy": slm.failure_taxonomy,
            "grounding_status": env.get("grounding_status"),
            "scene_validation": "NOT_SERVED",
            "numeric": None,
            "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
        }

    hyb = run_hybrid_offline(
        slm.norm_text,
        ReplayExtractor({slm.norm_text: slm.canonical_payload}),
        policy=pol,
        timeout_seconds=30.0,
    )
    body = hyb.response or {}
    rd = body.get("route_d") or {}
    rd_status = str(rd.get("status") or "")
    refusal = rd.get("refusal") if isinstance(rd.get("refusal"), dict) else {}
    reason_code = refusal.get("reason_code") or refusal.get("code") or rd.get("reason_code")
    source_gate_rejected = reason_code in {"QUOTE_NOT_IN_SOURCE", "UNGROUNDED_VALUE", "SOURCE_OBJECT_MISMATCH"}

    sv = scene_oracle_mod.validate(case, body)
    served = rd_status == "SERVED"
    num_info = sv.get("numeric") if isinstance(sv.get("numeric"), dict) else None
    num_ok = True if not case.get("metric_oracle") else bool(num_info and num_info.get("status") == "CORRECT")
    scene_ok = bool(served and sv.get("scene_validation") == "MATHEMATICALLY_VALID" and num_ok)

    return {
        "case_id": cid,
        "stratum": stratum,
        "expected_behavior": case.get("expected_behavior"),
        "stage": "hybrid_offline",
        "model_key": slm.model_key,
        "model_sha256": slm.model_sha256,
        "slm_invoked": bool(env.get("slm_invoked", True)),
        "slm_ok": True,
        "extracted_ok": True,
        "grounded_ok": bool(slm.ok and not source_gate_rejected),
        "served": served,
        "verified_scene": scene_ok,
        "safe_refused": (stratum == "negative" and not served),
        "reason_code": reason_code,
        "grounding_status": env.get("grounding_status"),
        "scene_validation": sv.get("scene_validation"),
        "oracle_issues": list(sv.get("issues") or []),
        "numeric": num_info,
        "latency_ms": round((time.perf_counter() - t0) * 1000.0, 2),
    }


def evaluate_manifest(
    manifest: dict[str, Any],
    *,
    criteria: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate valid + negative cases strictly through AxoV9 without parser fallback."""
    scene_oracle_mod = _load_scene_oracle()
    pol = hybrid_offline_policy({"HYBRID_ROUTE_D_PREVIEW": "1"})

    valid_cases = list(manifest.get("valid_cases") or [])
    negative_cases = list(manifest.get("negative_cases") or [])
    rows: list[dict[str, Any]] = []
    for c in valid_cases:
        rows.append(_evaluate_case(c, stratum="positive", pol=pol, scene_oracle_mod=scene_oracle_mod))
    for c in negative_cases:
        rows.append(_evaluate_case(c, stratum="negative", pol=pol, scene_oracle_mod=scene_oracle_mod))

    pos_rows = [r for r in rows if r["stratum"] == "positive"]
    neg_rows = [r for r in rows if r["stratum"] == "negative"]
    positive_total = len(pos_rows)
    negative_total = len(neg_rows)
    verified_scenes = sum(1 for r in pos_rows if r["verified_scene"])
    extracted_ok = sum(1 for r in pos_rows if r["extracted_ok"])
    grounded_ok = sum(1 for r in pos_rows if r["grounded_ok"])
    negative_safe_refused = sum(1 for r in neg_rows if r["safe_refused"])
    false_assertions_served = sum(1 for r in neg_rows if r["served"])
    invalid_relations_served = sum(
        1 for r in pos_rows if r["served"] and not r["verified_scene"]
    ) + false_assertions_served

    rate = (verified_scenes / positive_total) if positive_total > 0 else 0.0
    extraction_correctness = (extracted_ok / positive_total) if positive_total > 0 else 0.0
    grounding_correctness = (grounded_ok / positive_total) if positive_total > 0 else 0.0

    ind_crit = (criteria or {}).get("slm_independent") or {}
    req_rate = float(ind_crit.get("verified_scene_rate_min", 0.60))
    req_min_scenes = int(ind_crit.get("min_verified_scenes", 18 if positive_total >= 30 else 0))
    req_neg_rate = float(ind_crit.get("negative_safe_refusal_rate_min", 1.0))
    max_false = int(ind_crit.get("false_assertions_max", 0))
    max_inv = int(ind_crit.get("invalid_relations_max", 0))
    neg_rate = (negative_safe_refused / negative_total) if negative_total > 0 else 1.0

    gate_pass = bool(
        positive_total > 0
        and rate >= req_rate
        and verified_scenes >= req_min_scenes
        and neg_rate >= req_neg_rate
        and false_assertions_served <= max_false
        and invalid_relations_served <= max_inv
    )

    model_key = next((r.get("model_key") for r in rows if r.get("model_key")), "qwen3-0.6b-axo-v9-q4_k_m")
    model_sha256 = next((r.get("model_sha256") for r in rows if r.get("model_sha256")), "")
    if not model_sha256:
        from app.ai.local_slm_runtime import resolve_local_slm_model_spec
        model_sha256 = resolve_local_slm_model_spec("v9").sha256

    return {
        "schema": AUDIT_SCHEMA_VERSION,
        "manifest_run_id": manifest.get("run_id"),
        "manifest_set": manifest.get("set"),
        "model_key": model_key,
        "model_sha256": model_sha256,
        "allow_parser_reconcile": False,
        "local_parser_bypass_used": False,
        "allow_live_ai": False,
        "summary": {
            "verified_scenes": verified_scenes,
            "positive_total": positive_total,
            "rate": rate,
            "extraction_correctness": extraction_correctness,
            "grounding_correctness": grounding_correctness,
            "negative_safe_refused": negative_safe_refused,
            "negative_total": negative_total,
            "false_assertions_served": false_assertions_served,
            "invalid_relations_served": invalid_relations_served,
            "thresholds": {
                "verified_scene_rate_min": req_rate,
                "min_verified_scenes": req_min_scenes,
                "negative_safe_refusal_rate_min": req_neg_rate,
                "false_assertions_max": max_false,
                "invalid_relations_max": max_inv,
            },
            "gate_pass": gate_pass,
        },
        "cases": rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Isolated AxoV9 independent capability evaluator.")
    parser.add_argument("--manifest", type=Path, required=True, help="Path to SLM_INDEPENDENT_MANIFEST.json")
    parser.add_argument("--out", type=Path, required=True, help="Destination JSON output path")
    parser.add_argument("--criteria", type=Path, default=None, help="Optional ACCEPTANCE_CRITERIA.json")
    parser.add_argument("--force", action="store_true", help="Allow overwriting an existing non-empty --out file")
    args = parser.parse_args(argv)

    if args.out.exists() and args.out.stat().st_size > 0 and not args.force:
        raise FileExistsError(f"Refusing to overwrite existing output without --force: {args.out}")

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    criteria = json.loads(args.criteria.read_text(encoding="utf-8")) if args.criteria is not None else None
    report = evaluate_manifest(manifest, criteria=criteria)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
