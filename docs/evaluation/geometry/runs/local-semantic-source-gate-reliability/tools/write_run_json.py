"""run.json: identity, verdicts and the LF-normalised SHA-256 of every artifact in this run (run.json excluded).  Run from backend/."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def main() -> int:
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    reg = json.loads((RUN / "full_regression_summary.json").read_text(encoding="utf-8"))
    fresh = json.loads((RUN / "fresh_external_evaluation.json").read_text(encoding="utf-8"))
    text = json.loads((RUN / "text_to_geometry_before_after.json").read_text(encoding="utf-8"))
    artifacts = {}
    for path in sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "run.json"):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    out = {
        "schema": "algosim-local-semantic-run/1", "run_id": RUN.name, "updated_at_utc": datetime.now(timezone.utc).isoformat(),
        "start_head": git("rev-parse", "c5bb73f51"), "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "product_commit": cand["product_commit_sha"], "candidate_manifest_commit": cand["commit"],
        "candidate_stored_in": git("log", "-1", "--format=%H", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "measured_system": cand["measured_system"]["tree_hash"], "measured_files": cand["measured_system"]["so_file"], "cache_version": cand["cache_version"],
        "contracts_unchanged": ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "height-invariance-certificate/2", "output-policy/1"],
        "regression_verdict": reg.get("verdict"), "regression_gates": {s["name"]: s["verdict"] for s in reg.get("suites", [])},
        # The task fixes the overall verdict to BLOCKED while the publication HEAD awaits the Owner, whatever the offline gates say.
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "text_polyhedron_solved": {"before": text["before_outcomes"].get("LOCAL_SOLVED"), "after": text["after_outcomes"].get("LOCAL_SOLVED"), "of": text["polyhedron_items"],
                                   "wrong_served": len(text["wrong_served_after"]), "evidence_class": "DEVELOPMENT_EXPOSED"},
        "fresh_external": {"sampled": fresh["sampled_rows"], "in_scope": fresh["in_scope_items"], "served_correct": fresh["text_route_outcomes"].get("LOCAL_SOLVED", 0),
                           "wrong_served": len(fresh["wrong_served"]["text"]) + len(fresh["wrong_served"]["image"])},
        "live_vision": "NOT_CALLED", "provider_calls": 0, "independent_h1": "NOT_MEASURED", "real_student_usability": "NOT_MEASURED",
        "merge_push_deploy": "NOT_PERFORMED", "images_in_git": False, "report": "AXO_LOCAL_SEMANTIC_SOURCE_GATE_RELIABILITY_REPORT.md",
        "hash_policy": "SHA-256 of bytes with CRLF normalised to LF; excludes run.json itself", "artifacts": artifacts}
    (RUN / "run.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(out["regression_verdict"], out["regression_gates"], len(artifacts), "artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
