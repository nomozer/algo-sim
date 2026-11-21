"""Deterministic `axo-evaluation-run/2` manifest builder for AXO HYBRID /8 (`independent-validation-local-ai-production-readiness`).

Reads live git metadata, frozen candidate/surface hashes, and all `/8` empirical JSON
artifacts, recording LF-normalized SHA-256 + byte lengths for every file in the `/8`
run directory excluding `run.json`.
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
    LOCAL_SLM_EXTRACTOR_VERSION,
    SLM_COMPACT_SCHEMA_VERSION,
    SLM_GROUNDING_ENVELOPE_VERSION,
    SLM_GROUNDING_VALIDATOR_VERSION,
)
from app.ai.local_slm_runtime import (  # noqa: E402
    DEFAULT_LOCAL_SLM_MODEL_KEY,
    FINETUNED_LOCAL_SLM_MODEL_KEY,
    LOCAL_SLM_CACHE_NAMESPACE,
    LOCAL_SLM_MODELS,
    LOCAL_SLM_RUNTIME_VERSION,
)
from app.ai.slm_verified_normalizer import SLM_VERIFIED_NORMALIZER_VERSION  # noqa: E402
from app.main import CACHE_VERSION, ROUTE_D_CACHE_POLICY  # noqa: E402
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
    rec = _read_json("EVALUATOR_RECONCILIATION.json")
    cap = _read_json("SLM_CAPABILITY_MATRIX.json")
    unseen_m = _read_json("PERMISSIBLE_UNSEEN_CORPUS_MANIFEST.json")
    unseen_e = _read_json("PERMISSIBLE_UNSEEN_CORPUS_EVALUATION.json")
    res = _read_json("SYSTEM_RESOURCE_AND_CONCURRENCY_BENCHMARK.json")
    sim = _read_json("SCOPED_LOCAL_ROUTING_SIMULATION.json")
    reg = _read_json("SLM_V8_REGRESSION_RESULTS.json")

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
        "run_id": "independent-validation-local-ai-production-readiness",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": "OFFLINE_INDEPENDENT_LOCAL_SLM_VALIDATION",
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "range_base_commit": "ae20a9a6e02a00dea19c259c4e8d02350028e4d1",
        "v8_harness_commit": reg["clean_tree_full_pytest"]["verified_on_commit"],
        "baseline_run": {
            "run_id": "deterministic-geometry-language-closure-slm-finetuning",
            "product_commit": "6310113f2202bc3a4919406b26fad08cb09b38c9",
            "freeze_commit": "9a9352d586caa360f82052ba1b76fe9b4227f26c",
            "baseline_tip_commit": "ae20a9a6e02a00dea19c259c4e8d02350028e4d1",
            "cache_version": "145",
        },
        "candidate": {
            "product_commits": ["6310113f2202bc3a4919406b26fad08cb09b38c9"],
            "freeze_commit": "9a9352d586caa360f82052ba1b76fe9b4227f26c",
            "product_modified_in_v8": False,
            "measured_system_sha256": ms_hash,
            "measured_files_count": ms_count,
            "cache_version": CACHE_VERSION,
            "route_d_cache_policy": ROUTE_D_CACHE_POLICY,
            "local_slm_cache_namespace": LOCAL_SLM_CACHE_NAMESPACE,
            "semantic_environment_hash": semantic_environment_hash(),
            "stable_capability_hash": lock_comp["capability"],
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
            "original_model_key": DEFAULT_LOCAL_SLM_MODEL_KEY,
            "original_model_sha256": LOCAL_SLM_MODELS[DEFAULT_LOCAL_SLM_MODEL_KEY].sha256,
            "finetuned_model_key": FINETUNED_LOCAL_SLM_MODEL_KEY,
            "finetuned_model_sha256": LOCAL_SLM_MODELS[FINETUNED_LOCAL_SLM_MODEL_KEY].sha256,
            "runtime_version": LOCAL_SLM_RUNTIME_VERSION,
            "extractor_version": LOCAL_SLM_EXTRACTOR_VERSION,
            "normalizer_version": SLM_VERIFIED_NORMALIZER_VERSION,
            "compact_schema_version": SLM_COMPACT_SCHEMA_VERSION,
            "grounding_validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "grounding_envelope_version": SLM_GROUNDING_ENVELOPE_VERSION,
            "default_strategy": DEFAULT_LOCAL_SLM_STRATEGY,
            "default_closure_mode": DEFAULT_CLOSURE_MODE,
        },
        "environment": {
            "ALLOW_LIVE_AI": "0",
            "GEMINI_API_KEY": "",
            "external_ai_calls": 0,
            "HYBRID_ROUTE_MODE_DEFAULT": "live",
            "local_slm_route_mode": "local-slm",
        },
        "safety_and_scope_boundaries": {
            "live_ai_calls": 0,
            "sealed_h1_rows_opened": 0,
            "locked_w2_w3_rows_read": 0,
            "backend_app_files_modified": 0,
            "frontend_files_modified": 0,
            "fine_tuning_executed": False,
            "model_weights_modified": False,
            "independent_external_corpus": "BLOCKED_DATA_ACCESS",
            "gemini_parity": "NOT_MEASURED",
            "physical_low_end": "NOT_MEASURED",
            "independent_h1_validation": "NOT_MEASURED",
            "real_student_usability": "NOT_MEASURED",
            "source_gate_owner_handoff": "BLOCKED_OWNERSHIP",
            "frontend_integration": "BLOCKED_OWNERSHIP",
            "frozen_unseen_vmmu20_separate": reg["baseline_suites"]["frozen_unseen_vmmu20_separate"],
        },
        "quality_gates": {
            "D0_baseline_integrity": "PASS",
            "D1_evaluator_correction_and_reconciliation": "PASS",
            "D2_failure_audit_and_capability_matrix": "PASS",
            "D3_independent_external_corpus": "BLOCKED_DATA_ACCESS",
            "D3_permissible_unseen_zero_leakage": "PASS_EXECUTED",
            "D4_system_resource_and_concurrency": "PASS_HOST_MIXED_P95_ABOVE_5000MS",
            "D4_physical_low_end_4_6gb": "NOT_MEASURED",
            "D5_source_gate_owner_handoff": "BLOCKED_OWNERSHIP",
            "D6_gemini_parity": "NOT_MEASURED",
            "D7_real_student_usability": "NOT_MEASURED",
            "D8_scoped_routing_and_regressions": "PASS",
            "D9_security_16_and_full_pytest": "PASS",
            "D10_release_readiness_decision": "PASS",
        },
        "verdict": "EXPERIMENTAL_LOCAL",
        "metrics_summary": {
            "reconciled_v7h_112": reg["historical_slm_suites_live_config_d_v2_reverified"]["SLM_V7_HOLDOUT_112"],
            "evaluator_reconciliation_v2": rec.get("studies", {}),
            "capability_matrix_positive_pool_size": cap["positive_pool_size"],
            "permissible_unseen_manifest": {
                "counts": unseen_m["counts"],
                "anti_leakage_summary": unseen_m["anti_leakage_summary"],
                "manifest_sha256_lf": unseen_e["manifest_sha256_lf"],
            },
            "permissible_unseen_results": {
                k: {
                    "summary_overall": v["summary_overall"],
                    "summary_c60_blind_nlu": v["summary_c60_blind_nlu"],
                    "summary_external17": v["summary_external17"],
                    "stage_separation": v["stage_separation"],
                }
                for k, v in unseen_e["configs"].items()
            },
            "permissible_unseen_paired": unseen_e["paired_comparisons"],
            "resource_benchmark": {
                "cold_start": res["cold_start"],
                "warm_uncached_n100_threads6": res["warm_uncached_n100_threads6"],
                "deterministic_fast_path_n30": res["deterministic_fast_path_n30"],
                "peak_combined_ws_mib": res["system_memory_accounting_mib"]["peak_combined_backend_plus_slm_working_set_mib"],
                "peak_combined_private_commit_mib": res["system_memory_accounting_mib"]["peak_combined_backend_plus_slm_private_commit_mib"],
                "registered_threshold_evaluation": res["registered_threshold_evaluation"],
                "simulated_constrained_diagnostic": res["simulated_constrained_diagnostic"],
            },
            "scoped_routing_sim": {
                "v7_holdout_simulation": sim["v7_holdout_simulation"],
                "unseen_corpora_simulation": sim["unseen_corpora_simulation"],
            },
            "regression_and_security": {
                "safety_invariants": reg["safety_invariants"],
                "historical_slm_suites_live_config_d_v2_reverified": reg["historical_slm_suites_live_config_d_v2_reverified"],
                "security_and_runtime_16_all_passed": reg["security_and_runtime_16_all_passed"],
                "slm_and_v8_pytest_modules": reg["slm_and_v8_pytest_modules"],
            },
        },
        "clean_tree_full_pytest": reg["clean_tree_full_pytest"],
        "report": "FINAL_MASTER_REPORT.md",
        "hash_policy": "SHA-256 LF-normalized; excludes run.json",
        "artifacts": artifacts,
    }
    (RUN / "run.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[V8 RUN-MANIFEST] Wrote {RUN / 'run.json'} ({len(artifacts)} artifacts indexed)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
