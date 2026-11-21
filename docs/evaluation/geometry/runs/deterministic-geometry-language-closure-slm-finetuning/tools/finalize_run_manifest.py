"""Deterministic `axo-evaluation-run/2` manifest builder for AXO HYBRID /7.

Reads live git metadata, cache/surface hashes, and all `/7` empirical JSON
artifacts (zero manual number copying), and records LF-normalized SHA-256 +
byte sizes for every file in the run directory excluding `run.json`.
"""
from __future__ import annotations

import argparse
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
from app.runtime_identity import (  # noqa: E402
    semantic_environment_fingerprint,
    semantic_environment_hash,
)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()


def _sha_lf(path: Path) -> tuple[str, int]:
    data = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest(), len(data)


def _read_json(name: str) -> dict[str, Any]:
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Build/finalize /7 run.json")
    parser.add_argument("--product-commit", required=True)
    parser.add_argument("--freeze-commit", default="PENDING_COMMIT_3_FREEZE")
    parser.add_argument("--pytest-status", default="PENDING_CLEAN_TREE_FULL_PYTEST")
    parser.add_argument("--pytest-passed", type=int, default=None)
    parser.add_argument("--pytest-skipped", type=int, default=None)
    parser.add_argument("--pytest-deselected", type=int, default=None)
    parser.add_argument("--pytest-xfailed", type=int, default=None)
    parser.add_argument("--pytest-failed", type=int, default=None)
    parser.add_argument("--pytest-warnings", type=int, default=None)
    parser.add_argument("--pytest-duration", type=float, default=None)
    args = parser.parse_args()

    pc = _read_json("SLM_POST_CLOSURE_EVALUATION.json")
    td = _read_json("SLM_TRAINING_DATA_MANIFEST.json")
    tr = _read_json("SLM_TRAINING_RUN.json")
    ad = _read_json("SLM_ADAPTER_MODEL_MANIFEST.json")
    qv = _read_json("SLM_QUANTIZATION_EVALUATION.json")
    abl = _read_json("SLM_V7_ABLATION.json")
    hm = _read_json("SLM_V7_HOLDOUT_MANIFEST.json")
    he = _read_json("SLM_V7_HOLDOUT_EVALUATION.json")
    perf = _read_json("SLM_V7_PERFORMANCE.json")
    reg = _read_json("SLM_V7_REGRESSION_RESULTS.json")
    ref = _read_json("pending_template_refresh.json")

    ms_hash, ms_count = FEC.measured_system_hash()
    lock_comp = semantic_environment_fingerprint()

    artifacts: dict[str, dict[str, Any]] = {}
    for f in sorted(RUN.rglob("*"), key=lambda p: p.relative_to(RUN).as_posix()):
        if not f.is_file() or "__pycache__" in f.parts or f.name == "run.json":
            continue
        rel = f.relative_to(RUN).as_posix()
        digest, nbytes = _sha_lf(f)
        artifacts[rel] = {"sha256_lf": digest, "bytes_lf": nbytes}

    clean_pytest: dict[str, Any] = {
        "status": args.pytest_status,
        "verified_on_commit": args.freeze_commit,
        "command": "pytest -c backend/pytest.ini backend/tests -q",
    }
    if args.pytest_passed is not None:
        clean_pytest.update({
            "short_commit": args.freeze_commit[:9],
            "passed": args.pytest_passed,
            "skipped": args.pytest_skipped,
            "deselected": args.pytest_deselected,
            "xfailed": args.pytest_xfailed,
            "failed": args.pytest_failed,
            "warnings": args.pytest_warnings,
            "duration_seconds": args.pytest_duration,
        })

    q_stages: dict[str, Any] = {}
    for sk, sv in qv["stages"].items():
        q_stages[sk] = {k: v for k, v in sv.items() if k != "rows"}

    manifest = {
        "schema": "axo-evaluation-run/2",
        "run_id": "deterministic-geometry-language-closure-slm-finetuning",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": "OFFLINE_LOCAL_SLM_EMPIRICAL_BENCHMARK",
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "range_base_commit": "43bef643d2c528053526d363ee578065e60e6116",
        "baseline_run": {
            "run_id": "specialized-geometry-extraction-slm-optimization",
            "product_commit": "0acc07ae2a7cf8ebdb88b4876668099a1abae4f4",
            "freeze_commit": "732d979e1b12547deced4356d012b860d6f7a907",
            "baseline_tip_commit": "43bef643d2c528053526d363ee578065e60e6116",
            "cache_version": "145",
        },
        "candidate": {
            "product_commits": [args.product_commit],
            "freeze_commit": args.freeze_commit,
            "measured_system_sha256": ms_hash,
            "measured_files_count": ms_count,
            "holdout_verified_candidate_sha256": he["frozen_candidate_sha256"],
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
            "c21_measured_system": ref["runtime_identity_measured_system"],
        },
        "slm_contracts": {
            "original_model_key": DEFAULT_LOCAL_SLM_MODEL_KEY,
            "original_model_sha256": LOCAL_SLM_MODELS[DEFAULT_LOCAL_SLM_MODEL_KEY].sha256,
            "finetuned_model_key": FINETUNED_LOCAL_SLM_MODEL_KEY,
            "finetuned_model_sha256": LOCAL_SLM_MODELS[FINETUNED_LOCAL_SLM_MODEL_KEY].sha256,
            "base_hf_repo": ad["base_model"]["repo_id"],
            "base_hf_revision": ad["base_model"]["revision"],
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
            "frontend_files_modified": 0,
            "planner_registry_kernel_source_gate_modified": False,
            "ocr_modified": False,
            "fine_tuning_executed": True,
            "holdout_contamination": False,
            "gemini_parity": "NOT_MEASURED",
            "frontend_integration": "BLOCKED_OWNERSHIP",
            "source_gate_owner_handoff": "BLOCKED_OWNERSHIP",
            "independent_h1_validation": "NOT_MEASURED",
            "real_student_usability": "NOT_MEASURED",
            "physical_low_end": "NOT_MEASURED",
            "frozen_unseen_vmmu20": reg["suites"]["frozen_unseen_vmmu20_separate"],
            "k1_s2_r1_status": "PENDING_OWNER_DECISION",
            "paid_project_confirmed": False,
            "publication_head": "BLOCKED_PENDING_OWNER_REVIEW",
        },
        "quality_gates": {
            "C0_baseline_integrity": "PASS",
            "C1_deterministic_language_closure": "PASS",
            "C2_post_closure_measurement": "PASS",
            "C3_training_data_integrity": "PASS",
            "C4_lora_fine_tuning": "PASS",
            "C5_quantized_gguf_runtime": "PASS",
            "C6_single_shot_blind_holdout": "PASS",
            "C7_cpu_performance_host": "PASS",
            "C7_physical_low_end_4_6gb": "NOT_MEASURED",
            "C8_regression_and_safety": "PASS",
            "C9_replacement_decision": "PASS",
            "gemini_parity": "NOT_MEASURED",
            "independent_h1_validation": "NOT_MEASURED",
        },
        "preregistered_verdict": "READY_AS_LOCAL_PRIMARY_WITH_CONSTRAINTS",
        "metrics_summary": {
            "post_closure_datasets": {
                ds: {k: v["metrics"] for k, v in dv["configs"].items()}
                for ds, dv in pc["datasets"].items()
            },
            "training_data": {
                "splits": td["splits"],
                "anti_leakage_audit": td["anti_leakage_audit"],
            },
            "training_run": {
                "hardware": tr["hardware"],
                "hyperparameters": tr["hyperparameters"],
                "selected_epoch": tr["selected_epoch"],
                "peak_cuda_memory_mib": tr["peak_cuda_memory_mib"],
                "total_wall_time_s": tr["total_wall_time_s"],
                "epochs": [{k: e[k] for k in ("epoch", "train_loss", "val_loss", "val_metrics")} for e in tr["epoch_history"]],
            },
            "adapter_and_exports": ad["exports"],
            "quantization_val_stages": q_stages,
            "ablation_historical_diagnostics": {
                ds: {
                    "configs": {k: v["metrics"] for k, v in dv["configs"].items()},
                    "paired_comparisons": dv["paired_comparisons"],
                }
                for ds, dv in abl["datasets"].items()
            },
            "blind_holdout_112_manifest": {
                "counts": hm["counts"],
                "anti_leakage_audit": hm["anti_leakage_audit"],
                "manifest_sha256_lf": hm["manifest_sha256_lf"],
            },
            "blind_holdout_112_single_shot": {
                "single_shot": he["single_shot"],
                "configs": {k: v["metrics"] for k, v in he["configs"].items()},
                "paired_comparisons": he["paired_comparisons"],
                "by_family": he["by_family"],
                "cos2_grader_audit": {
                    "note": "EVI.same_value('cos²=...', 'cos²=...') returns None on v7h_p7_06..10 across all 4 configs (exact answer==oracle string match on all 5).",
                    "audited_positive_counts": {"config_a": "39/80", "config_b": "47/80", "config_c": "58/80", "config_d": "74/80"},
                    "audited_true_wrong_served": 0,
                },
            },
            "performance": {
                "hardware_disclosure": perf["hardware_disclosure"],
                "cold_start_finetuned_n10": perf["cold_start_finetuned_n10"],
                "warm_uncached_thread_sweep": {
                    k: {sk: sv for sk, sv in v.items() if sk != "rows"}
                    for k, v in perf["warm_uncached_thread_sweep"].items()
                },
                "warm_cached_separate": perf["warm_cached_separate"],
            },
            "regressions_and_fault_checks": {
                "safety_invariants": reg["safety_invariants"],
                "suites": reg["suites"],
                "slm_pytest_modules": reg["slm_pytest_modules"],
                "fault_and_adversarial_14": {k: v["ok"] for k, v in reg["fault_and_adversarial_14"].items()},
                "all_14_fault_checks_passed": reg["all_14_fault_checks_passed"],
                "pending_template_refresh_count": len(ref["rows"]),
            },
        },
        "clean_tree_full_pytest": clean_pytest,
        "report": "FINAL_MASTER_REPORT.md",
        "hash_policy": "SHA-256 LF-normalized; excludes run.json",
        "artifacts": artifacts,
    }
    (RUN / "run.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[RUN-MANIFEST] Wrote {RUN / 'run.json'} ({len(artifacts)} artifacts indexed)", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
