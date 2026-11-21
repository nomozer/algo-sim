"""Writes run.json (axo-evaluation-run/2): identities, gates, verdicts, metric summary and sha256 of every run artifact
(raw bytes as on disk). usage: python finalize_run_manifest.py <t3_status> [t3_detail]   (from the run directory)
"""

import hashlib
import json
import sys
import time
from pathlib import Path

RUN = Path(".")
res = json.loads((RUN / "LIVE_SIMULATION_ACCEPTANCE_RESULTS.json").read_text(encoding="utf-8"))
p2 = res["passes"]["pass2"]["rates"]
artifacts = {p.as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(RUN.rglob("*")) if p.is_file() and p.name != "run.json"}
run = {
    "schema": "axo-evaluation-run/2",
    "run_id": "axo-hybrid-local-only-3d-simulation-live-acceptance-cutover",
    "wave_id": "AXO_HYBRID_LOCAL_ONLY_3D_SIMULATION_LIVE_ACCEPTANCE_CUTOVER",
    "campaign": "AXO HYBRID /10",
    "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "classification": "LIVE_BROWSER_ACCEPTANCE_LOCAL_ONLY_SCOPED_REHEARSAL",
    "branch": "integration/local-only-3d-live-acceptance",
    "start_base_commit": "38c6efbdb",
    "product_commits": {"frontend_keyless": "e10697092", "local_slm_keepalive_fix": "7554e2b72"},
    "freeze_commits": {"acceptance_manifest_and_criteria": "451a59040", "candidate_refreeze": "a0f979392",
                       "pending_template_rebind": "5a07be9b4"},
    "candidate": {"pass1_measured_system": "a7a6bc4157d02018d5a67e5ee408469f22795385f920444eafc39d4772fa8330",
                  "pass2_measured_system": "ce3e3c4b5cc9e075bc260f50e64dc5647408d1a3a614db67bd6d17a3b1d1eb6a",
                  "measured_files": 123, "cache_version": "145", "default_hybrid_route_mode": "live",
                  "model": {"key": "qwen3-0.6b-axo-v9-q4_k_m", "sha256": "73f1484b08b97ed2a1f44e32bcf6610210c7fda51567c4cd0a03d98dffc6cc35"},
                  "runtime": "llama.cpp b12470 (dde9de82c)", "browser": "Playwright Chromium 151.0.7922.34 headless",
                  "frontend_dist_tree_sha256": "89fe949bb31f97208df2d6329a3016c3f01888220aba2671c18563296bf2d0ad"},
    "owner_decisions_this_session": {"frontend": "integration branch only", "default_cutover": "not changed",
                                     "planner_registry_typed_facts": "not modified"},
    "safety_and_scope_boundaries": {"merged": False, "pushed": False, "main_modified": False, "gemini_calls": 0,
                                    "approved_by_user_written": False, "frozen_runs_modified": False,
                                    "construction_v1_v2_modified": False, "fine_tuning": False},
    "quality_gates": {"H0": "PASS", "H1": "PASS", "H2": "PASS", "H3": "PASS", "H4": "PASS_WITH_NOTES (159/160)",
                      "H5": "PASS", "H6": "PASS (NO_EXTERNAL_AI; FULLY_OFFLINE not claimed)", "H7": "PARTIAL (target hardware NOT_MEASURED)",
                      "H8": sys.argv[1], "H9": "PASS (env-var staging; rollback model/config/code)", "H10": "see verdicts"},
    "t3_detail": sys.argv[2] if len(sys.argv) > 2 else None,
    "verdicts": {"BACKEND_LOCAL_ONLY_VERIFIED": True, "FULL_STACK_LOCAL_ONLY_VERIFIED": True, "LIVE_SIMULATION_ACCEPTED": False,
                 "SCOPED_CUTOVER_READY": False, "SCOPED_CUTOVER_COMPLETED": False, "BLOCKED_HARDWARE": "NOT_MEASURED"},
    "metrics_summary_pass2": {k: p2[k] for k in ("simulation_completion_rate", "completion_by_intent", "completion_by_extraction_route",
                                                  "geometry_correctness_rate", "visual_rendering_success_rate", "interaction_success_rate",
                                                  "safe_refusal_rate", "numeric_answer_accuracy", "external_requests")},
    "performance_pass2": res["passes"]["pass2"]["performance"]["served_scenes"],
    "artifacts": artifacts,
}
(RUN / "run.json").write_text(json.dumps(run, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(len(artifacts), "artifacts")
