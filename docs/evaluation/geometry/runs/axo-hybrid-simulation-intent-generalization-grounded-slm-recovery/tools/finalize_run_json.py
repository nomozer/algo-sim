"""Writes run.json of /11 from the result files (no measurement). usage (from the run dir): python tools/finalize_run_json.py "<t3 detail>" """
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

rd = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
res, frz = rd("V11_LIVE_ACCEPTANCE_RESULTS.json"), rd("V11_LIVE_ACCEPTANCE_FREEZE.json")
perf = rd("V11_FULL_STACK_PERFORMANCE.json")
r = res["rates"]
run = {
    "schema": "axo-evaluation-run/2",
    "run_id": "axo-hybrid-simulation-intent-generalization-grounded-slm-recovery",
    "wave_id": "AXO_HYBRID_SIMULATION_INTENT_GENERALIZATION_GROUNDED_SLM_RECOVERY",
    "campaign": "AXO HYBRID /11",
    "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "classification": "SLM_CAUSAL_AUDIT + PRODUCT_FIXES + BLIND_LIVE_BROWSER_ACCEPTANCE_LOCAL_ONLY_SCOPED",
    "branch": "feat/simulation-intent-slm-recovery",
    "start_base_commit": "2f12b96b0",
    "preregistration_commit": "5d0e86dad",
    "product_commits": {"source_gate_request_nouns": "806a7d338", "parser_simulation_intent": "0557dcaf6",
                        "frontend_clarification_and_retry": "3e5eb8809", "slm_simulation_only_contract": "fcf68e91b",
                        "scene3d_v17_overlay_drag": "b15fd9e92", "cache_146": "5c25c7ea9", "scene3d_u08_label_glide": "31e6b47c9"},
    "freeze_commits": {"candidate_refreeze_1": "fad0db5f2", "acceptance_freeze": "fec016682", "candidate_refreeze_2": "18aadea7b"},
    "candidate": {"measured_system_tree_hash": frz["code"]["measured_system_tree_hash"], "measured_files": frz["code"]["measured_system_files"],
                  "cache_version": "146", "default_hybrid_route_mode": "live", "model": frz["model"], "browser": frz["browser"],
                  "parser": frz["code"]["parser_version"], "extractor": frz["code"]["slm_extractor_version"], "grounding": frz["code"]["slm_validator_version"],
                  "source_gate_registry": "geometry-functions/33", "manifest_sha256": frz["inputs"]["manifest_sha256"], "criteria_sha256": frz["inputs"]["criteria_sha256"],
                  "oracle": "tools/scene_oracle.py (independent exact Fraction + Gram; copied from /10, + ratio2)"},
    "owner_decisions_this_session": {"parser_slm_adapter": "OWNED", "frontend": "OWNED", "source_gate": "NARROW: _VAT_MO_PHONG only",
                                     "domain_gate": "PATCH_AND_HANDOFF_ONLY", "planner_engine_kernel_typed_facts": "LOCKED (prototype + handoff)",
                                     "hybrid_preview": "LOCKED", "holdout": "AGENT_AUTHORED_FROZEN_BEFORE_CHANGES"},
    "safety_and_scope_boundaries": {"merged": False, "pushed": False, "main_modified": False, "gemini_calls": 0, "approved_by_user_written": False,
                                    "frozen_runs_modified": False, "construction_v1_v2_modified": False, "fine_tuning": False, "needle3": False},
    "quality_gates": {"J0_baseline_ownership": "PASS", "J1_slm20_root_cause": "PASS", "J2_simulation_intent_generalization": "PARTIAL",
                      "J3_grounded_slm_recovery": "FAIL (4/30 < 0.30)", "J4_underdetermination": "PARTIAL (3/5 clarify, D02/D03 'chưa hỗ trợ'; design handed off)",
                      "J5_user_experience": "PARTIAL (clarification + retry PASS; diacritic-free NOT applied)",
                      "J6_scene3d_interaction": "PASS (V17 fixed; U08 fixed post hoc; O provenance handed off)",
                      "J7_new_blind_live": "FAIL (completion 0.659 < 0.85)", "J8_performance_offline": "PASS (dev host)",
                      "J9_full_regression": sys.argv[1] if len(sys.argv) > 1 else "NOT_MEASURED", "J10_release": "see verdicts"},
    "t3_detail": sys.argv[1] if len(sys.argv) > 1 else "NOT_MEASURED",
    "verdicts": {"SIMULATION_INTENT_GENERALIZATION_VERIFIED": "FALSE (partial)", "GROUNDED_SLM_RECOVERY_VERIFIED": False,
                 "FULL_STACK_LOCAL_ONLY_VERIFIED": True, "LIVE_SIMULATION_ACCEPTED": False, "SCOPED_CUTOVER_READY": False,
                 "SCOPED_CUTOVER_COMPLETED": False, "BLOCKED_OWNERSHIP": True, "BLOCKED_MODEL_EXTRACTION": False,
                 "BLOCKED_SOURCE_GROUNDING": True, "BLOCKED_DOWNSTREAM_CAPABILITY": "PARTIAL", "BLOCKED_VISUAL_INTERACTION": False,
                 "BLOCKED_PERFORMANCE": False,
                 "NOT_MEASURED": ["EXTERNAL_INDEPENDENCE", "PHYSICAL_TARGET_HARDWARE_4_8_GIB", "REAL_STUDENT_USABILITY", "GEMINI_PARITY"]},
    "metrics_summary": {k: r[k] for k in ("SIMULATION_COMPLETION_RATE_in_scope", "completion_by_stratum", "completion_by_intent",
                                          "SLM_VERIFIED_SCENE_RATE", "geometry_correctness_of_served", "numeric_answers_correct",
                                          "visual_ok_of_served", "interaction_ops", "safe_refusal_negatives", "safety")},
    "performance": {k: perf[k] for k in ("fast_path_backend_ms", "slm_path_backend_ms", "served_first_visible_scene_ms",
                                         "served_first_interactive_frame_ms", "stack_ws_total_max_mb")},
    "artifacts": sorted(str(p).replace("\\", "/") for p in Path(".").glob("*") if p.is_file()),
}
Path("run.json").write_text(json.dumps(run, ensure_ascii=False, indent=1), encoding="utf-8")
print("run.json written")
