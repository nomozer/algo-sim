"""Phase 0 receipts of run `semantic-failure-safe-image-segmentation`: baseline candidate integrity, holdout protection
audit and the observability audit of the parser before this run. Run from the worktree root."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
RUNS = RUN.parent
NOW = datetime.now(timezone.utc).isoformat()
START = "dcbedcb0d"


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT).decode().strip()


def put(n, d):
    (RUN / n).write_text(json.dumps({"run_id": RUN.name, "generated_at_utc": NOW, **d}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    put("baseline_candidate_integrity.json", {
        "start_head": git("rev-parse", START), "branch": git("branch", "--show-current"),
        "reported": {"head": "dcbedcb0d", "product_commit": "697b097ac", "candidate_manifest_commit": "da06829fe", "candidate_stored_in": "8852c4070",
                     "measured_system": "040de2fd63fb687203610918160b1170ad025117b2d221acf12ef25215bd831c", "measured_files": 115, "cache_version": "134"},
        "verified_at_start": {"head_matches": True, "ancestors_of_head": ["697b097ac", "da06829fe", "8852c4070"], "working_tree_clean": True,
                              "freeze_verify": "match 115 files 040de2fd63fb6872", "cache_lock": "CACHE_VERSION 134, environment 3d5400a5",
                              "servers_listening": "none (8767/8770/5173)"},
        "note": "report HEAD dcbedcb0d, manifest commit da06829fe and freeze commit 8852c4070 are distinct; product 697b097ac is the last commit touching measured paths",
        "discrepancies": []})
    w2 = RUNS / "hybrid-v2-independent-vietnamese-section-holdout-wave2/inputs/holdout-wave2.json"
    w3 = RUNS / "hybrid-v2-independent-vietnamese-geometry-holdout-wave3/inputs/holdout-wave3.json"
    put("holdout_protection_audit.json", {
        "sealed_h1": {"rows": 94, "opened": 0, "row_numbers_only": "local-semantic-source-gate-reliability/fresh_external_preregistration.json",
                      "vmmu_page_renders": "not opened (a page may hold a sealed question)"},
        "w2_w3_locked": {"inputs_sha256": {"W2": hashlib.sha256(w2.read_bytes()).hexdigest(), "W3": hashlib.sha256(w3.read_bytes()).hexdigest()},
                         "exposed_rows": ["W2-N03", "W3-N63"], "rows_read_in_this_run": 0,
                         "used_for": "nothing: only this phase0.py reads the two input files' BYTES to record their SHA-256 (never parsed); no other tool of this run names either file (grep of tools/)",
                         "aggregate_results_quoted": "only the published aggregates of independent-geometry-plane-constraints (2/48, 0/72, 2 WRONG_SERVED under the registered rule)"},
        "development_sources": {"DEV": "tools/semantic_dev_corpus.py (agent-written in this run)", "REAL27": "25 controlled-vision transcriptions + 2 earlier fresh items (exposed)",
                                "PROBES": "the 39 plane-constraint probes of the previous run (exposed)", "IMAGES": "the 25 controlled-vision crops (exposed) and layouts composed from them"},
        "boundary_checks": ["semantic_eval.py and segmentation_eval.py read only the manifests above", "no network access during measurement", "ALLOW_LIVE_AI=0 everywhere"]})
    put("existing_parser_observability_audit.json", {
        "before_this_run": {
            "clause_segmentation": "split_into_clauses: sentence ends, ';' and clause-level separators; each clause classified MAPPED_FACT / MAPPED_GOAL / BENIGN_DISCOURSE / UNPARSED_FACT_CANDIDATE / UNPARSED_GOAL_CANDIDATE / UNRESOLVED_REFERENCE with offsets (SourceCoverageReport)",
            "where_exposed": "route_d.adaptive_telemetry.source_coverage (clause list) and route_d.refusal.fallback_reason (UNPARSED_GOAL_CANDIDATE, SOURCE_GATE_MISMATCH:<code>:<reason>, SCHEMA_VALIDATION_FAILED:…)",
            "terminal_reason": "route_d.refusal.code = LIVE_AI_DISABLED for every local parse that is not complete while live AI is off (adaptive_input_router Case 4) — the code names the blocked fallback, not what was unread",
            "missing": ["no root cause separate from the terminal reason", "no responsible layer (first loss vs detector vs decider)",
                        "no clause TYPE (relation / definition / goal …)", "no downstream dependency (a goal on an unread plane looked like an unread goal)",
                        "no distinction 'understood but unsupported' (cos/tan of an angle, proofs) vs 'not understood'",
                        "Case 2 refusals (local parse complete, planner/kernel refused) carried no layer attribution"]},
        "added_in_this_run": "backend/app/ai/local_failure_diagnostics.py → route_d.local_diagnostics on refusals only (local-failure-diagnostics/1): root_cause, first_loss_layer, detected_by, decided_by, fallback, per-clause type/status/failure_reason/downstream_dependency/offsets; refusal codes grouped with hybrid_preview.classify_refusal (no new public code)",
        "cache": "refusals are never cached (main._served_route_d serves SERVED rows only); the field is absent on served responses"})
    print("ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
