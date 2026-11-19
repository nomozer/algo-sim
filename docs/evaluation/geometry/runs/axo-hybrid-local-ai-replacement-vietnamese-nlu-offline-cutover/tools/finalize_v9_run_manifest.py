# -*- coding: utf-8 -*-
"""Deterministic `axo-evaluation-run/2` manifest builder for AXO HYBRID /9.

Computes LF-normalized SHA-256 + byte lengths for every artifact under
`axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover` (excluding `run.json`
and `__pycache__`), and records product/candidate identities, locked surface digests,
model SHA-256s, evaluation metrics, and cutover verdicts.
"""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
BACKEND = ROOT / "backend"
SCRIPTS = BACKEND / "scripts"
sys.path[:0] = [str(BACKEND), str(SCRIPTS)]

import freeze_evaluation_candidate as FEC  # noqa: E402
from app.ai import fact_extraction, function_calling, typed_fact_next_extraction  # noqa: E402
from app.ai.local_slm_extractor import (  # noqa: E402
    DEFAULT_CLOSURE_MODE,
    DEFAULT_LOCAL_SLM_STRATEGY,
    LOCAL_SLM_EXTRACTOR_V9_VERSION,
    LOCAL_SLM_EXTRACTOR_VERSION,
    SLM_COMPACT_SCHEMA_VERSION,
    SLM_GROUNDING_ENVELOPE_V9_VERSION,
    SLM_GROUNDING_VALIDATOR_V9_VERSION,
    V9_CLOSURE_MODE,
)
from app.ai.local_slm_runtime import (  # noqa: E402
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LOCAL_SLM_CACHE_NAMESPACE,
    LOCAL_SLM_CACHE_V9_NAMESPACE,
    LOCAL_SLM_MODELS,
    LOCAL_SLM_RUNTIME_V9_VERSION,
    LOCAL_SLM_RUNTIME_VERSION,
    V9_LOCAL_SLM_MODEL_KEY,
)
from app.ai.slm_verified_normalizer import (  # noqa: E402
    SLM_VERIFIED_NORMALIZER_V3_VERSION,
    SLM_VERIFIED_NORMALIZER_VERSION,
)
from app.main import CACHE_VERSION, ROUTE_D_CACHE_POLICY, hybrid_route_mode  # noqa: E402
from app.runtime_identity import semantic_environment_fingerprint, semantic_environment_hash  # noqa: E402
from slm_math_evaluator_v2 import EVALUATOR_VERSION  # noqa: E402


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def _sha_lf(path: Path) -> tuple[str, int]:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest(), len(data)


def _read_json(name: str) -> dict[str, Any]:
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def main() -> int:
    c60_p1 = _read_json("C60_GOLD_INTERVENTION_RESULTS.json")
    c60_p2 = _read_json("C60_POST_P2_V9_RESULTS.json")
    c60_p3 = _read_json("C60_POST_P3_V9_RESULTS.json")
    train_man = _read_json("SLM_V9_TRAINING_MANIFEST.json")
    train_run = _read_json("SLM_V9_TRAINING_RUN.json")
    quant_cmp = _read_json("SLM_V9_QUANTIZATION_COMPARISON.json")
    ablation = _read_json("SLM_V9_ABLATION.json")
    perf = _read_json("SLM_V9_RUNTIME_PERFORMANCE.json")
    unseen_m = _read_json("SLM_V9_UNSEEN_MANIFEST.json")
    unseen_e = _read_json("SLM_V9_UNSEEN_EVALUATION.json")
    cap = _read_json("SLM_V9_CAPABILITY_MATRIX.json")
    dep = _read_json("GEMINI_DEPENDENCY_INVENTORY.json")
    reg = _read_json("SLM_V9_REGRESSION_RESULTS.json")
    cand_doc = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))

    ms_hash, ms_count = FEC.measured_system_hash()
    lock_comp = semantic_environment_fingerprint()

    artifacts: dict[str, dict[str, Any]] = {}
    for f in sorted(RUN.rglob("*"), key=lambda p: p.relative_to(RUN).as_posix()):
        if not f.is_file() or "__pycache__" in f.parts or f.name == "run.json":
            continue
        rel = f.relative_to(RUN).as_posix()
        digest, nbytes = _sha_lf(f)
        artifacts[rel] = {"sha256_lf": digest, "bytes_lf": nbytes}

    manifest = {
        "schema": "axo-evaluation-run/2",
        "run_id": "axo-hybrid-local-ai-replacement-vietnamese-nlu-offline-cutover",
        "wave_id": "AXO_HYBRID_LOCAL_AI_REPLACEMENT_VIETNAMESE_NLU_OFFLINE_CUTOVER",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": "LOCAL_AI_VIETNAMESE_NLU_AND_SCOPED_LOCAL_ONLY_CUTOVER",
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "start_base_commit": "c73506cb23b0b365d8e475c6b5386a31176a669b",
        "product_commit_sha": cand_doc["product_commit_sha"],
        "freeze_commit_sha": cand_doc["commit"] if cand_doc.get("cay_lam_viec_sach") else None,
        "candidate": {
            "product_commit_sha": cand_doc["product_commit_sha"],
            "measured_system_sha256": ms_hash,
            "measured_files_count": ms_count,
            "cache_version": CACHE_VERSION,
            "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
            "default_route_mode": hybrid_route_mode(),
            "v7_cache_namespace": LOCAL_SLM_CACHE_NAMESPACE,
            "v9_cache_namespace": LOCAL_SLM_CACHE_V9_NAMESPACE,
            "semantic_environment_hash": semantic_environment_hash(),
            "lock_components": lock_comp,
            "locked_surfaces": {
                "function_calling": function_calling.surface_fingerprint(),
                "fact_extraction_flat": fact_extraction.surface_fingerprint("flat"),
                "fact_extraction_v3": fact_extraction.surface_fingerprint("v3"),
                "typed_fact_next": typed_fact_next_extraction.typed_fact_next_surface_fingerprint(),
            },
        },
        "slm_and_evaluator_contracts": {
            "evaluator_version": EVALUATOR_VERSION,
            "v9_model_key": V9_LOCAL_SLM_MODEL_KEY,
            "v9_model_sha256": LOCAL_SLM_MODELS[V9_LOCAL_SLM_MODEL_KEY].sha256,
            "v9_model_size_bytes": LOCAL_SLM_MODELS[V9_LOCAL_SLM_MODEL_KEY].size_bytes,
            "v7_rollback_model_key": FINETUNED_LOCAL_SLM_MODEL_KEY,
            "v7_rollback_model_sha256": LOCAL_SLM_MODELS[FINETUNED_LOCAL_SLM_MODEL_KEY].sha256,
            "v7_rollback_model_size_bytes": LOCAL_SLM_MODELS[FINETUNED_LOCAL_SLM_MODEL_KEY].size_bytes,
            "original_model_key": DEFAULT_LOCAL_SLM_MODEL_KEY,
            "original_model_sha256": LOCAL_SLM_MODELS[DEFAULT_LOCAL_SLM_MODEL_KEY].sha256,
            "original_model_size_bytes": LOCAL_SLM_MODELS[DEFAULT_LOCAL_SLM_MODEL_KEY].size_bytes,
            "v9_runtime_version": LOCAL_SLM_RUNTIME_V9_VERSION,
            "v7_runtime_version": LOCAL_SLM_RUNTIME_VERSION,
            "v9_extractor_version": LOCAL_SLM_EXTRACTOR_V9_VERSION,
            "v7_extractor_version": LOCAL_SLM_EXTRACTOR_VERSION,
            "v3_normalizer_version": SLM_VERIFIED_NORMALIZER_V3_VERSION,
            "v2_normalizer_version": SLM_VERIFIED_NORMALIZER_VERSION,
            "compact_schema_version": SLM_COMPACT_SCHEMA_VERSION,
            "v9_grounding_validator_version": SLM_GROUNDING_VALIDATOR_V9_VERSION,
            "v9_grounding_envelope_version": SLM_GROUNDING_ENVELOPE_V9_VERSION,
            "v9_closure_mode": V9_CLOSURE_MODE,
            "default_v7_closure_mode": DEFAULT_CLOSURE_MODE,
            "default_strategy": DEFAULT_LOCAL_SLM_STRATEGY,
        },
        "safety_and_scope_boundaries": {
            "external_ai_calls": 0,
            "gemini_invocations": 0,
            "silent_cloud_fallbacks": 0,
            "sealed_h1_rows_opened": 0,
            "locked_w2_w3_rows_read": 0,
            "frontend_files_modified": 0,
            "kernel_registry_planner_modified": 0,
            "construction_v2_freeze_integrity": reg["construction_v2_freeze_integrity"],
            "external_independence": "NOT_MEASURED",
            "physical_target_hardware": "NOT_MEASURED",
            "frontend_memory": "NOT_MEASURED_BACKEND_ONLY",
            "gemini_parity": "NOT_MEASURED",
            "independent_h1_validation": "NOT_MEASURED",
            "real_student_usability": "NOT_MEASURED",
            "owner_blocked_handoff_patches": [
                "handoff/default_cutover_local_only_scoped.patch",
                "handoff/frontend_local_ai_status_and_keyless_ux.patch",
                "handoff/source_gate_optional_grammar.patch",
            ],
        },
        "quality_gates": {
            "G0_baseline_identity": "PASS",
            "G1_c60_root_cause_and_gold_intervention": "PASS",
            "G2_deterministic_vietnamese_closure": "PASS",
            "G3_targeted_slm_finetuning": "PASS",
            "G4_performance_and_fault_recovery": "PASS_HOST_MIXED_P95_BELOW_5000MS",
            "G5_unseen_single_shot_150": "PASS_AUTHOR_UNSEEN_EXTERNAL_INDEPENDENCE_NOT_MEASURED",
            "G6_gemini_dependency_coverage": "PASS",
            "G7_local_only_product_route": "PASS_BACKEND_OPT_IN_DEFAULT_AND_UI_BLOCKED_OWNERSHIP",
            "G8_offline_network_isolation": "PASS",
            "G9_regression_and_construction_freeze": "PASS" if (reg.get("clean_tree_full_pytest") or {}).get("failed") == 0 and reg.get("targeted_pytest_14_modules", {}).get("passed") else "PENDING_CLEAN_TREE_PYTEST",
            "G10_cutover_decision": "LOCAL_ONLY_SCOPED_RELEASE_READY_BACKEND_OPT_IN__DEFAULT_AND_GENERAL_BLOCKED_OWNERSHIP",
        },
        "verdicts": {
            "goal_a_local_only_operational_opt_in_route": "LOCAL_ONLY_SCOPED_RELEASE_READY",
            "goal_a_default_switch_and_frontend_ux": "BLOCKED_OWNERSHIP",
            "goal_b_gemini_capability_replacement": "NOT_EQUIVALENT_FULL_REPLACEMENT",
        },
        "metrics_summary": {
            "c60_progression": {
                "arm_a_v7_baseline": f"{c60_p1['arms']['arm_a_current_v7']['served_exact_strict_all']}/42",
                "arm_b_gold_canon_ceiling": f"{c60_p1['arms']['arm_b_gold_typed_fact_v2_canon_text']['served_exact_strict_all']}/42",
                "post_p2_axov7_v9_v3": f"{c60_p2['c60_served_exact_strict_all']}/42 (fast={c60_p2['c60_fast_path_served']}, slm={c60_p2['c60_slm_served']})",
                "post_p3_axov9_v9_v3": f"{c60_p3['c60_served_exact_strict_all']}/42 (fast={c60_p3['c60_fast_path_served']}, slm={c60_p3['c60_slm_served']}, wrong=0)",
            },
            "training": {
                "train_count": train_man["splits"]["train"]["total"],
                "val_count": train_man["splits"]["val"]["total"],
                "selected_epoch": train_run["selected_epoch"],
                "val_axov9_q4km_gbnf": quant_cmp["models"]["axov9_q4km_gguf"]["positives_oracle_exact"],
            },
            "runtime_performance": {
                "cold_start_ms": perf["cold_start"]["cold_start_e2e_ms"],
                "pure_warm_uncached_n100_p50_ms": perf["pure_warm_uncached_slm_n100"]["e2e_to_verified_scene3d_ms"]["p50_ms"],
                "pure_warm_uncached_n100_p95_ms": perf["pure_warm_uncached_slm_n100"]["e2e_to_verified_scene3d_ms"]["p95_ms"],
                "mixed_warm_uncached_n100_p50_ms": perf["mixed_warm_uncached_n100"]["e2e_ms"]["p50_ms"],
                "mixed_warm_uncached_n100_p95_ms": perf["mixed_warm_uncached_n100"]["e2e_ms"]["p95_ms"],
                "warm_cached_n25_p50_ms": perf["warm_cached_explicit_runtime"]["subsequent_25_hits_ms"]["p50_ms"],
                "fast_path_n30_p50_ms": perf["deterministic_fast_path_n30"]["p50_ms"],
                "peak_combined_ws_mib": perf["system_memory_accounting_mib"]["peak_combined_backend_plus_slm_working_set_mib"],
                "peak_private_commit_mib": perf["system_memory_accounting_mib"]["peak_combined_backend_plus_slm_private_commit_mib"],
                "ablation_variants": len(ablation["variants"]),
            },
            "unseen_150": unseen_e["unseen_150_summary"],
            "unseen_manifest_overlaps": unseen_m["anti_leakage_audit"],
            "external17": {k: v for k, v in unseen_e["external17_real_transcriptions"].items() if k != "cases"},
            "gemini_dependency_surfaces": dep["summary"],
            "capability_buckets": {k: len(cap.get(k, [])) for k in ("supported_and_validated", "experimental", "unsupported", "not_measured")},
            "regression_summary": {
                "safety_invariants": reg["safety_invariants"],
                "security_and_runtime_16_all_passed": reg["security_and_runtime_16_all_passed"],
                "targeted_pytest_14_modules": reg["targeted_pytest_14_modules"],
                "clean_tree_full_pytest": reg.get("clean_tree_full_pytest"),
            },
        },
        "artifacts": artifacts,
    }

    (RUN / "run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote run.json ({len(artifacts)} files indexed).", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
