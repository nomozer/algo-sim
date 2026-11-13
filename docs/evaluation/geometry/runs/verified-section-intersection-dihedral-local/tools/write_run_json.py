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
START = "ffc62f6fe"
CONTRACTS = ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "height-invariance-certificate/2",
             "output-policy/1", "hybrid-route-d-simulation/4"]
ADDITIVE = ["angle-construction/1 + angle_domain", "altitude-construction/1 (new optional quantity field)",
            "typed-fact-next/2 + simulation goal construct_intersection_line (/1 snapshot and provider framing unchanged)"]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def put(name: str, data: dict) -> None:
    (RUN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(name: str) -> dict:
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    reg = load("full_regression_summary.json")
    gates = {s["name"]: s for s in reg.get("suites", [])}
    put("candidate_freeze.json", {
        "run_id": RUN.name, "generated_at_utc": now, "head": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "freeze_commit_field": cand["commit"], "freeze_stored_in": git("log", "-1", "--format=%H", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "product_commit": cand["product_commit_sha"], "measured_system": cand["measured_system"], "cache_version": cand["cache_version"],
        "cache_version_bumped": "133 -> 134: served envelopes changed (acute angle rays + angle_domain, altitude_construction); "
                                "test_cache_dihedral_altitude_invalidation.py proves a 133:route-d row MISSES",
        "contracts_unchanged": CONTRACTS, "additive_fields": ADDITIVE,
        "freeze_verify_in_regression": (gates.get("freeze_verify") or {}).get("verdict"),
        "earlier_freezes_in_this_run": {"89aed139e": "measured_system 8f49cd2d4d32…, superseded: regression attempt 1 failed 2 scope-census tests (logs/attempt1/)"}})
    put("publication_gate_status.json", {
        "run_id": RUN.name, "generated_at_utc": now,
        "publication_head": "BLOCKED_PENDING_OWNER_REVIEW",
        "publication_head_scan": (gates.get("publication_head") or {}).get("summary_lines"),
        "publication_range": "BLOCKED_PENDING_OWNER_REVIEW",
        "publication_range_scan_this_run": {"range": f"{git('rev-parse', '--short=9', START)}..HEAD",
                                            "summary_lines": (gates.get("publication_range") or {}).get("summary_lines"),
                                            "verdict": (gates.get("publication_range") or {}).get("verdict")},
        "full_release_gate": "BLOCKED_GATES_REMAIN",
        "historical_range_finding": {
            "rule": "HARDCODED_PASSWORD", "path": "docs/evaluation/geometry/runs/semantic-to-scene3d-verified-simulation/tools/browser_simulation_e2e.mjs",
            "blob_sha1": "2bfce9c8e306ca707141c41806e1fac31623c2e9", "blob_sha256": "75a685edde68459fa308794bb6e5d7d6abc543fef61874669e0277dc0acab6c0",
            "introduced_in": "fe835d424", "removed_at": "8da3ea754 (random per-run password)",
            "git_verified": "git cat-file -t 2bfce9c8 = blob; ls-tree fe835d424 holds it at that path, 8da3ea754 and HEAD hold 539d90f5; fe835d424 is an ancestor of the run start ffc62f6fe; rev-list --objects ffc62f6fe..HEAD lists it 0 times (VERIFIED FACT, session log)",
            "in_this_run_range": False,
            "nature": "synthetic password for a throwaway account in the measured app's own local SQLite file; never a real credential",
            "status": "PENDING_OWNER_DECISION: the blob stays in history (no rewrite); only the Owner may add an exact-blob exception"},
        "agent_actions": "none: no approval written, no exception or wildcard added, scan policy unchanged, no history rewritten, no evidence removed, the old value not repeated",
        "pending_templates": "K-1/R-1/S-2 re-bound to the refrozen measured_system as metadata only (pending_template_refresh.json); owner_decision stays PENDING_OWNER_DECISION"})
    artifacts = {}
    for path in sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "run.json" and "__pycache__" not in p.parts):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    inv, e2e = load("scene3d_mathematical_invariants.json"), load("scene3d_section_intersection_browser_e2e.json")
    sec, il = load("polyhedron_section_correctness.json"), load("plane_intersection_correctness.json")
    ang = load("angle_construction_before_after.json")
    put("run.json", {
        "schema": "algosim-verified-section-intersection-run/1", "run_id": RUN.name, "updated_at_utc": now,
        "start_head": git("rev-parse", START), "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "product_commit": cand["product_commit_sha"], "candidate_manifest_commit": cand["commit"], "measured_system": cand["measured_system"]["tree_hash"],
        "measured_files": cand["measured_system"]["so_file"], "cache_version": cand["cache_version"],
        "contracts_unchanged": CONTRACTS, "additive_fields": ADDITIVE,
        "regression_verdict": reg.get("verdict"), "regression_gates": {k: v["verdict"] for k, v in gates.items()},
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD and range BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "obtuse_angle_constructions": {"before": len(ang["before_obtuse_drawn"]), "after": len(ang["after_obtuse_drawn"])},
        "sections_served": {"before": sec["served_before"], "after": sec["served_after"], "probes": len(sec["rows"])},
        "intersection_lines_served": {"before": il["served_before"], "after": il["served_after"], "probes": len(il["rows"])},
        "invariants": {"served_scenes": inv["served_scenes_after"], "checks": inv["checks_total"], "failed": inv["checks_failed"],
                       "mutations": {"applied": sum(m["applied"] for m in inv["mutation_summary"].values()),
                                     "caught": sum(m["caught"] for m in inv["mutation_summary"].values())}},
        "browser_e2e": {"passed": e2e["passed"], "total": e2e["total"]},
        "unseen_evaluation": "NOT_MEASURED", "independent_h1": "NOT_MEASURED", "sealed_h1_rows_opened": 0, "live_ai_calls": 0,
        "physical_low_end": "NOT_MEASURED", "merge_push_deploy": "NOT_PERFORMED", "images_in_git": False,
        "report": "AXO_VERIFIED_SECTION_INTERSECTION_DIHEDRAL_LOCAL_REPORT.md",
        "hash_policy": "SHA-256 of bytes with CRLF normalised to LF; excludes run.json itself", "artifacts": artifacts})
    print(reg.get("verdict"), {k: v["verdict"] for k, v in gates.items()}, len(artifacts), "artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
