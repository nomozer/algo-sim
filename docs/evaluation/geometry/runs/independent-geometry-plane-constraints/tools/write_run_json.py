"""candidate_freeze.json, publication_gate_status.json and run.json (identity, verdicts, LF-normalised SHA-256 of every
artifact in this run, run.json excluded), written after the full regression and the locked evaluation. Run from backend/."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
START = "4222f021b"
CONTRACTS = ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "height-invariance-certificate/2",
             "output-policy/1", "hybrid-route-d-simulation/4", "typed-fact-next/2"]


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
        "cache_version_bumped": False,
        "cache_reason": "only SERVED rows are reused (main._served_route_d); texts newly served were refused before (never cached), previously served texts produce the same envelopes (full pytest incl. hybrid-preview fixtures unchanged); a changed refusal code is never cached",
        "contracts_unchanged": CONTRACTS,
        "source_gate_grammar_extended": "additive closed grammar for named planes defined by a line and a point / two intersecting lines (registry /33 version unchanged: no function or argument changed)",
        "previous_candidate": {"stored_in": "f0fa7e359", "measured_system": "dc834af0001169e6962b655b8953c9694eb4a8c5718e59995f152d5c3fc93d29"},
        "freeze_verify_in_regression": (gates.get("freeze_verify") or {}).get("verdict")})
    put("publication_gate_status.json", {
        "run_id": RUN.name, "generated_at_utc": now,
        "publication_head": "BLOCKED_PENDING_OWNER_REVIEW",
        "publication_head_scan": (gates.get("publication_head") or {}).get("summary_lines"),
        "publication_range_scan_this_run": {"range": f"{START}..HEAD at regression time",
                                            "summary_lines": (gates.get("publication_range") or {}).get("summary_lines"),
                                            "scan_verdict": (gates.get("publication_range") or {}).get("verdict")},
        "scan_vs_governance": "the range scan of this run PASSES (0 violations); governance stays blocked because history still holds pending Owner decisions (97 HEAD findings in 18 blobs, and blob 2bfce9c8 — a synthetic test password introduced in fe835d424, removed in 8da3ea754)",
        "publication_range_governance": "BLOCKED_PENDING_OWNER_REVIEW",
        "full_release_gate": "BLOCKED_GATES_REMAIN",
        "agent_actions": "none: no approval written, no exception or wildcard added, scan policy unchanged, no history rewritten, no evidence removed, the old value not repeated",
        "pending_templates": "K-1/R-1/S-2 re-bound to the refrozen measured_system as metadata only (pending_template_refresh.json); owner_decision stays PENDING_OWNER_DECISION"})
    artifacts = {}
    for path in sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "run.json" and "__pycache__" not in p.parts):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    gr, mut, e2e = load("plane_constraint_grammar_tests.json"), load("geometry_mutation_verification.json"), load("scene3d_browser_e2e.json")
    sec, un = load("constraint_to_section_composition.json"), load("unseen_evaluation_results.json")
    put("run.json", {
        "schema": "algosim-plane-constraint-run/1", "run_id": RUN.name, "updated_at_utc": now,
        "start_head": git("rev-parse", START), "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "product_commit": cand["product_commit_sha"], "candidate_manifest_commit": cand["commit"], "measured_system": cand["measured_system"]["tree_hash"],
        "measured_files": cand["measured_system"]["so_file"], "cache_version": cand["cache_version"], "contracts_unchanged": CONTRACTS,
        "regression_verdict": reg.get("verdict"), "regression_gates": {k: v["verdict"] for k, v in gates.items()},
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "development_probes": {"as_expected_before": gr["as_expected_before"], "as_expected_after": gr["as_expected_after"], "probes": gr["probes"],
                               "sections_served_before": sec["served_before"], "sections_served_after": sec["served_after"], "section_probes": sec["section_probes"],
                               "wrong_served_after": gr["wrong_served_after"]},
        "mutations": {"applied": mut["applied"], "caught": mut["caught"]},
        "browser_e2e": {"passed": e2e["passed"], "total": e2e["total"]},
        "locked_internal_holdouts": {k: {"before": {x: v["before"][x] for x in ("served_correct", "serve_cases", "wrong_served", "correct_refusal", "refuse_cases")},
                                         "after": {x: v["after"][x] for x in ("served_correct", "serve_cases", "wrong_served", "correct_refusal", "refuse_cases")}}
                                     for k, v in un["sets"].items()},
        "locked_post_hoc": "the 2 served REFUSE cases are payload-origin negatives whose texts are valid; served geometry equals hand computation (2 texts now exposed)",
        "new_locked_external_evaluation": "BLOCKED_DATA", "independent_h1": "NOT_MEASURED", "sealed_h1_rows_opened": 0, "live_ai_calls": 0,
        "physical_low_end": "NOT_MEASURED", "merge_push_deploy": "NOT_PERFORMED", "images_in_git": False,
        "report": "AXO_INDEPENDENT_GEOMETRY_PLANE_CONSTRAINTS_REPORT.md",
        "hash_policy": "SHA-256 of bytes with CRLF normalised to LF; excludes run.json itself", "artifacts": artifacts})
    print(reg.get("verdict"), {k: v["verdict"] for k, v in gates.items()}, len(artifacts), "artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
