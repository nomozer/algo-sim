"""candidate_freeze.json, publication_gate_status.json and run.json (identity, verdicts, LF-normalised SHA-256 of every
artifact in this run, run.json excluded), written after the full regression.  Run from backend/."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
CONTRACTS = ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "height-invariance-certificate/2",
             "output-policy/1", "hybrid-route-d-simulation/4"]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def put(name: str, data: dict) -> None:
    (RUN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    reg = json.loads((RUN / "full_regression_summary.json").read_text(encoding="utf-8"))
    gates = {s["name"]: s for s in reg.get("suites", [])}
    put("candidate_freeze.json", {
        "run_id": RUN.name, "generated_at_utc": now, "head": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "freeze_commit_field": cand["commit"], "freeze_stored_in": git("log", "-1", "--format=%H", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "product_commit": cand["product_commit_sha"], "measured_system": cand["measured_system"], "cache_version": cand["cache_version"],
        "cache_version_bumped": "132 -> 133: served envelopes gained angle_construction (test_cache_angle_construction_invalidation.py proves a 132:route-d row MISSES)",
        "contracts_unchanged": CONTRACTS, "freeze_verify_in_regression": (gates.get("freeze_verify") or {}).get("verdict")})
    head_gate = gates.get("publication_head") or {}
    put("publication_gate_status.json", {
        "run_id": RUN.name, "generated_at_utc": now, "publication_head": "BLOCKED_PENDING_OWNER_REVIEW",
        "publication_head_scan": head_gate.get("summary_lines"), "publication_range_scan": (gates.get("publication_range") or {}).get("summary_lines"),
        "full_release_gate": "BLOCKED_GATES_REMAIN",
        "new_finding_in_this_run": {"rule": "HARDCODED_PASSWORD", "path": "docs/evaluation/geometry/runs/semantic-to-scene3d-verified-simulation/tools/browser_simulation_e2e.mjs",
                                   "blob_sha1": "2bfce9c8e306ca707141c41806e1fac31623c2e9", "blob_sha256": "75a685edde68459fa308794bb6e5d7d6abc543fef61874669e0277dc0acab6c0",
                                   "introduced_in": "fe835d424", "removed_at": "8da3ea754 (random per-run password)",
                                   "nature": "synthetic password for a throwaway account in the measured app's own local SQLite file; never a real credential",
                                   "status": "PENDING_OWNER_DECISION: the blob stays in history (no rewrite); only the Owner may add an exact-blob exception"},
        "agent_actions": "none: no approval written, no exception or wildcard added, no history rewritten, no frozen evidence removed",
        "pending_templates": "K-1/R-1/S-2 re-bound to the refrozen measured_system as metadata only (pending_template_refresh.json); owner_decision stays PENDING_OWNER_DECISION"})
    artifacts = {}
    for path in sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "run.json"):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    gap = json.loads((RUN / "semantic_to_scene_gap_matrix.json").read_text(encoding="utf-8"))
    inv = json.loads((RUN / "scene3d_mathematical_invariants.json").read_text(encoding="utf-8"))
    e2e = json.loads((RUN / "scene3d_interaction_browser_e2e.json").read_text(encoding="utf-8"))
    put("run.json", {
        "schema": "algosim-semantic-to-scene3d-run/1", "run_id": RUN.name, "updated_at_utc": now,
        "start_head": git("rev-parse", "8a5a54e37"), "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "product_commit": cand["product_commit_sha"], "candidate_manifest_commit": cand["commit"], "measured_system": cand["measured_system"]["tree_hash"],
        "measured_files": cand["measured_system"]["so_file"], "cache_version": cand["cache_version"], "contracts_unchanged": CONTRACTS,
        "regression_verdict": reg.get("verdict"), "regression_gates": {k: v["verdict"] for k, v in gates.items()},
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "goal_levels": {"before": gap["before_levels"], "after": gap["after_levels"]},
        "invariants": {"served_scenes": inv["served_scenes"], "checks": inv["checks_total"], "failed": inv["checks_failed"]},
        "browser_e2e": {"passed": e2e["passed"], "total": e2e["total"]},
        "unseen_evaluation": "NOT_MEASURED", "independent_h1": "NOT_MEASURED", "live_ai_calls": 0, "physical_low_end": "NOT_MEASURED",
        "merge_push_deploy": "NOT_PERFORMED", "images_in_git": False, "report": "AXO_SEMANTIC_TO_SCENE3D_VERIFIED_SIMULATION_REPORT.md",
        "hash_policy": "SHA-256 of bytes with CRLF normalised to LF; excludes run.json itself", "artifacts": artifacts})
    print(reg.get("verdict"), {k: v["verdict"] for k, v in gates.items()}, len(artifacts), "artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
