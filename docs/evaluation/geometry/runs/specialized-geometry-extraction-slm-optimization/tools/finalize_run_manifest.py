"""Deterministic `axo-evaluation-run/2` manifest builder for AXO HYBRID /6.

Reads live git metadata, cache/surface hashes, and all `/6` empirical JSON
reports (no manual number copying), and records LF-normalized SHA-256 + byte
sizes for every file in the run directory excluding `run.json`.
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
    DEFAULT_LOCAL_SLM_STRATEGY,
    LOCAL_SLM_EXTRACTOR_VERSION,
    SLM_COMPACT_SCHEMA_VERSION,
    SLM_GROUNDING_ENVELOPE_VERSION,
    SLM_GROUNDING_VALIDATOR_VERSION,
)
from app.ai.local_slm_runtime import LOCAL_SLM_CACHE_NAMESPACE, LOCAL_SLM_RUNTIME_VERSION  # noqa: E402
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
    parser = argparse.ArgumentParser(description="Build/finalize /6 run.json")
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

    gold = _read_json("SLM_GOLD_INTERVENTION_RESULTS.json")
    abl = _read_json("SLM_EXTRACTION_ABLATION.json")
    grd = _read_json("SLM_GROUNDING_RELIABILITY.json")
    lat = _read_json("SLM_LATENCY_OPTIMIZATION.json")
    nh_man = _read_json("SLM_NEW_HOLDOUT_MANIFEST.json")
    nh_ev = _read_json("SLM_NEW_HOLDOUT_EVALUATION.json")
    reg = _read_json("SLM_REGRESSION_RESULTS.json")
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

    manifest = {
        "schema": "axo-evaluation-run/2",
        "run_id": "specialized-geometry-extraction-slm-optimization",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "classification": "OFFLINE_LOCAL_SLM_EMPIRICAL_BENCHMARK",
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "range_base_commit": "463c6b0408e192a19ff1f25a1bff2a6c94e4e75f",
        "baseline_run": {
            "run_id": "slm-local-geometry-understanding",
            "product_commit": "a182b54600752e57f3be408aad6a673bd9a0d41f",
            "freeze_commit": "96791162faa46df330beee9aef2f17f82e03c868",
            "baseline_tip_commit": "463c6b0408e192a19ff1f25a1bff2a6c94e4e75f",
            "cache_version": "145",
        },
        "candidate": {
            "product_commits": [args.product_commit],
            "freeze_commit": args.freeze_commit,
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
            "c21_measured_system": ref["runtime_identity_measured_system"],
            "backend_app_freeze_sha256": nh_ev["backend_app_freeze_sha256"],
            "freeze_integrity_verified": nh_ev["freeze_integrity_verified"],
        },
        "slm_contracts": {
            "model_key": lat["model_key"],
            "model_sha256": lat["model_sha256"],
            "runtime_version": LOCAL_SLM_RUNTIME_VERSION,
            "extractor_version": LOCAL_SLM_EXTRACTOR_VERSION,
            "normalizer_version": SLM_VERIFIED_NORMALIZER_VERSION,
            "compact_schema_version": SLM_COMPACT_SCHEMA_VERSION,
            "grounding_validator_version": SLM_GROUNDING_VALIDATOR_VERSION,
            "grounding_envelope_version": SLM_GROUNDING_ENVELOPE_VERSION,
            "default_strategy": DEFAULT_LOCAL_SLM_STRATEGY,
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
            "fine_tuning_executed_in_v6": False,
            "frontend_integration": "BLOCKED_OWNERSHIP",
            "independent_h1_validation": "NOT_MEASURED",
            "real_student_usability": "NOT_MEASURED",
            "physical_low_end": "NOT_MEASURED",
            "frozen_unseen_vmmu20": reg["suites"]["frozen_unseen_vmmu20_separate"],
            "k1_s2_r1_status": "PENDING_OWNER_DECISION",
            "paid_project_confirmed": False,
            "publication_head": "BLOCKED_PENDING_OWNER_REVIEW",
        },
        "preregistered_verdict": "PARTIAL_GAIN_KEEP_HYBRID_EXPERIMENTAL",
        "fine_tuning_recommendation": "HYBRID_CASE_C_SOURCE_GATE_CLOSURE_THEN_CASE_B_DISJOINT_QLORA",
        "metrics_summary": {
            "gold_intervention_phase_a": gold["summary"],
            "dev_calibration_16": {
                k: v["metrics"] for k, v in abl["datasets"]["DEV_CALIBRATION_16"]["configs"].items()
            },
            "dev_calibration_16_paired": abl["datasets"]["DEV_CALIBRATION_16"]["paired_comparisons"],
            "holdout_40_historical_diagnostic": {
                k: v["metrics"] for k, v in abl["datasets"]["HOLDOUT_40"]["configs"].items()
            },
            "holdout_40_paired": abl["datasets"]["HOLDOUT_40"]["paired_comparisons"],
            "e4_slot_level_metrics": abl["e4_slot_level_metrics"],
            "new_holdout_48_manifest": {
                "total_items": nh_man["total_items"],
                "positive_count": nh_man["positive_count"],
                "negative_count": nh_man["negative_count"],
                "exact_normalized_overlaps": nh_man["anti_clone_and_coord_audit"]["exact_normalized_overlaps"],
                "structural_skeleton_overlaps": nh_man["anti_clone_and_coord_audit"]["structural_skeleton_overlaps"],
                "coord_60digit_verified_positives": nh_man["anti_clone_and_coord_audit"]["coord_60digit_verified_positives"],
            },
            "new_holdout_48_single_shot": {
                "single_shot": nh_ev["single_shot"],
                "configs": {k: v["metrics"] for k, v in nh_ev["configs"].items()},
                "by_family_config_c_full": nh_ev["by_family_config_c_full"],
                "paired_comparisons": nh_ev["paired_comparisons"],
            },
            "latency_optimization": {
                "cold_start": lat["cold_start"],
                "threads_6": {k: v for k, v in lat["warm_uncached_thread_sweep"]["threads_6"].items() if k != "samples"},
                "threads_4_slm_ms": lat["warm_uncached_thread_sweep"]["threads_4"]["stage_stats_ms"]["slm_inference_ms"],
                "threads_8_slm_ms": lat["warm_uncached_thread_sweep"]["threads_8"]["stage_stats_ms"]["slm_inference_ms"],
                "decomposition": {k: {sk: sv for sk, sv in v.items() if sk != "rows"} for k, v in lat["warm_uncached_optimization_decomposition"].items()},
                "warm_extraction_cache_hit_separate": lat["warm_extraction_cache_hit_separate"],
            },
            "grounding_reliability": grd["summary"],
            "regressions_and_fault_checks": {
                "safety_invariants": reg["safety_invariants"],
                "fault_checks_14": reg["fault_checks_14"],
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
    print(f"[RUN-MANIFEST] Wrote {RUN / 'run.json'} ({len(artifacts)} artifacts indexed)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
