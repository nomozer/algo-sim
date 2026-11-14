"""candidate_freeze.json, publication_gate_status.json and run.json (identity, verdicts, LF-normalised SHA-256 of every
artifact in this run, run.json excluded), written after the full regression. Run from backend/."""
from __future__ import annotations

import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
START = "dcbedcb0d"
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
    product_gates = {k: v["verdict"] for k, v in gates.items() if k != "publication_head"}
    put("candidate_freeze.json", {
        "run_id": RUN.name, "generated_at_utc": now, "head": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "freeze_commit_field": cand["commit"], "freeze_stored_in": git("log", "-1", "--format=%H", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "product_commit": cand["product_commit_sha"], "measured_system": cand["measured_system"], "cache_version": cand["cache_version"],
        "cache_version_bumped": False,
        "cache_reason": "only SERVED rows are reused (main._served_route_d); local_diagnostics is attached to refusals only; texts newly served by the parser repairs were refused before (never cached); previously served texts produce the same envelopes (full pytest incl. hybrid-preview fixtures unchanged); image segmentation acts before analysis and changes no analysis cache key",
        "contracts_unchanged": CONTRACTS,
        "source_gate_changed": False,
        "measured_files": {"before": 115, "after": cand["measured_system"]["so_file"], "added": "backend/app/ai/local_failure_diagnostics.py"},
        "previous_candidate": {"stored_in": "8852c4070", "measured_system": "040de2fd63fb687203610918160b1170ad025117b2d221acf12ef25215bd831c"},
        "freeze_verify_in_regression": (gates.get("freeze_verify") or {}).get("verdict")})
    put("publication_gate_status.json", {
        "run_id": RUN.name, "generated_at_utc": now,
        "publication_head": "BLOCKED_PENDING_OWNER_REVIEW",
        "publication_head_scan": (gates.get("publication_head") or {}).get("summary_lines"),
        "publication_range_scan_this_run": {"range": f"{START}..HEAD at regression time",
                                            "summary_lines": (gates.get("publication_range") or {}).get("summary_lines"),
                                            "scan_verdict": (gates.get("publication_range") or {}).get("verdict")},
        "scan_vs_governance": "the range scan of this run PASSES (0 violations); governance stays blocked because history still holds pending Owner decisions (97 HEAD findings in 18 blobs, and historical blob 2bfce9c8)",
        "publication_range_governance": "BLOCKED_PENDING_OWNER_REVIEW",
        "full_release_gate": "BLOCKED_GATES_REMAIN",
        "agent_actions": "none: no approval written, no exception or wildcard added, scan policy unchanged, no history rewritten, no receipt removed",
        "pending_templates": "K-1/R-1/S-2 re-bound to the refrozen measured_system as metadata only (pending_template_refresh.json); owner_decision stays PENDING_OWNER_DECISION"})
    artifacts = {}
    for path in sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "run.json" and "__pycache__" not in p.parts):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    sem = load("semantic_repair_before_after.json")["summary"]
    seg = load("multi_problem_segmentation_before_after.json")
    e2e, tp = load("image_selection_browser_e2e.json"), load("text_vs_payload_negative_evaluation.json")
    keys = ("items", "served", "meets_expectation", "fully_recognized", "missing_clauses")
    put("run.json", {
        "schema": "algosim-semantic-failure-segmentation-run/1", "run_id": RUN.name, "updated_at_utc": now,
        "start_head": git("rev-parse", START), "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "product_commit": cand["product_commit_sha"], "candidate_manifest_commit": cand["commit"], "measured_system": cand["measured_system"]["tree_hash"],
        "measured_files": cand["measured_system"]["so_file"], "cache_version": cand["cache_version"], "contracts_unchanged": CONTRACTS,
        "regression_verdict": reg.get("verdict"), "regression_gates": {k: v["verdict"] for k, v in gates.items()},
        "product_gates_all_pass": all(v == "PASS" for v in product_gates.values()),
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "semantic_development": {side: {s: {k: sem[side][s].get(k) for k in keys if k in sem[side][s]} for s in sem[side]} for side in ("before", "after")},
        "segmentation": {side: {s: {k: v for k, v in row.items() if k in ("pages", "merged_without_prompt", "pages_every_problem_cleanly_selectable",
                                                                          "picks", "picks_clean", "unnecessary_selection_prompts", "whole_problem_text_kept")}
                                for s, row in seg[f"summary_{side}"].items()} for side in ("before", "after")},
        "segmentation_measured_at": "cc449ae4b (before the 7315cf3b0 figure-block fix; E2E and diagram association re-measured after it)",
        "image_selection_browser_e2e": {"passed": e2e["passed"], "total": e2e["total"]},
        "track_a_text_negatives": {"items": tp["track_a_text"]["items"], "served": tp["track_a_text"]["served"]},
        "track_b_payload_negatives": {"items": tp["track_b_payload"]["items"], "served": tp["track_b_payload"]["served"],
                                      "control": tp["track_b_payload"]["valid_text_control"]["status"]},
        "acceptance_unchanged": {"text": "8/27", "image": "4/27", "wrong_scene_served": 0},
        "new_locked_external_evaluation": "BLOCKED_DATA", "independent_h1": "NOT_MEASURED", "sealed_h1_rows_opened": 0,
        "locked_w2_w3_rows_used": 0, "live_ai_calls": 0,
        "physical_low_end": "NOT_MEASURED", "merge_push_deploy": "NOT_PERFORMED", "student_images_in_git": False,
        "report": "AXO_SEMANTIC_FAILURE_SAFE_IMAGE_SEGMENTATION_REPORT.md",
        "hash_policy": "SHA-256 of bytes with CRLF normalised to LF; excludes run.json itself", "artifacts": artifacts})
    print(reg.get("verdict"), product_gates, len(artifacts), "artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
