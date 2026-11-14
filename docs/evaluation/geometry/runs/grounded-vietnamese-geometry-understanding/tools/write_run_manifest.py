"""run.json of run `grounded-vietnamese-geometry-understanding`: verdicts from the receipts + SHA-256 (LF-normalised) of every
file of the run directory except run.json and bytecode.  python write_run_manifest.py   # worktree root, after derive_receipts
"""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
L = lambda n: json.loads((RUN / n).read_text(encoding="utf-8"))  # noqa: E731
git = lambda *a: subprocess.check_output(["git", *a], cwd=ROOT).decode().strip()  # noqa: E731

reg, pub, acc = L("full_regression_summary.json"), L("publication_gate_status.json"), L("real27_acceptance_before_after.json")
e2e, cf = L("scene3d_browser_e2e.json"), L("candidate_freeze.json")
arts = {}
for p in sorted(RUN.rglob("*")):
    if p.is_file() and p.name != "run.json" and "__pycache__" not in p.parts:
        b = p.read_bytes().replace(b"\r\n", b"\n")
        arts[p.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(b).hexdigest(), "bytes_lf": len(b)}
manifest = {
    "run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "schema": "algosim-grounded-understanding-run/1",
    "product_commits": cf["product_commits"], "candidate_freeze_commit": cf["freeze_stored_in"], "candidate_commit_field": cf["commit_field"],
    "measured_system": L("baseline_candidate_integrity.json")["measured_system"], "cache_version": "139",
    "dataset_partition": "DEVELOPMENT (agent-written corpus, exposed REAL27, exposed probes); never H-1 or locked W2/W3",
    "environment": {"ALLOW_LIVE_AI": "0", "HYBRID_ROUTE_MODE": "local-first", "live_ai_calls": 0},
    "start_head": git("rev-parse", "83fdc3071"), "head_at_manifest_write": git("rev-parse", "HEAD"),
    "branch": git("rev-parse", "--abbrev-ref", "HEAD"),
    "contracts_unchanged": L("semantic_pipeline_architecture_audit.json")["contracts_unchanged"],
    "regression_gates": {s["name"]: s["verdict"] for s in reg["suites"]},
    "PRODUCT_REGRESSION_VERDICT": pub["PRODUCT_REGRESSION_VERDICT"], "PUBLICATION_HEAD_VERDICT": pub["PUBLICATION_HEAD_VERDICT"],
    "PUBLICATION_RANGE_VERDICT": pub["PUBLICATION_RANGE_VERDICT"], "PUBLICATION_GOVERNANCE_STATUS": pub["PUBLICATION_GOVERNANCE_STATUS"],
    "FULL_RELEASE_GATE": pub["FULL_RELEASE_GATE"],
    "browser_e2e": f"{e2e['passed']}/{e2e['total']}",
    "acceptance": {k: {"before": acc[k]["grades_before"], "after": acc[k]["grades_after"]} for k in ("text", "image")},
    "independent_generalization": "NOT_MEASURED", "new_independent_evaluation": "BLOCKED_DATA", "h1": "NOT_MEASURED",
    "memory_leak": "INCONCLUSIVE", "merge_push_deploy": "NOT_PERFORMED",
    "report": "AXO_GROUNDED_VIETNAMESE_GEOMETRY_UNDERSTANDING_REPORT.md",
    "hash_policy": "SHA-256 LF-normalised; excludes run.json and __pycache__", "artifacts": arts,
}
(RUN / "run.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(len(arts), "artifacts")
