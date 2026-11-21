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
START = "1a9ee8b0c"
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
        "cache_reason": "only SERVED rows are reused (main._served_route_d); every newly served text was refused before (never cached); no previously served text changed status or answers on any corpus; source_goal_completion appears only on trigonometric-value questions (previously refused)",
        "contracts_unchanged": CONTRACTS,
        "source_gate_changed": "closed-grammar additions only (named-plane definition clause; trigonometric value of an angle read as the angle object and reported NOT_ANSWERED); verification policy unchanged; registry /33 unchanged",
        "measured_files": {"before": 116, "after": cand["measured_system"]["so_file"]},
        "previous_candidate": {"stored_in": "18a7ba008", "measured_system": "1f62a4a47bb72071e861d894a5e08ce27877c47dee1f896353b6f40c83ab1077"},
        "freezes_in_this_run": {"cf12c59e1": "after 13f1b482c (measured cb16082a…)", "9b16af799": "after 379d33969 (measured b652e635…, frozen on a dirty tree — backend_pytest attempt 1 FAIL, commit 07f29a83a)", "54268761e": "same measured system on a clean tree (final)"},
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
    sem = load("semantic_development_before_after.json")
    seg = load("final_candidate_image_segmentation_revalidation.json")["summary_final_candidate"]
    e2e, img = load("scene3d_browser_e2e.json"), load("image_selection_browser_e2e.json")
    inv, tacc, iacc = load("scene3d_mathematical_invariants.json"), load("local_text_to_simulation_acceptance.json"), load("local_image_to_simulation_acceptance.json")
    put("run.json", {
        "schema": "algosim-compositional-semantics-run/1", "run_id": RUN.name, "updated_at_utc": now,
        "start_head": git("rev-parse", START), "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "product_commit": cand["product_commit_sha"], "candidate_manifest_commit": cand["commit"], "measured_system": cand["measured_system"]["tree_hash"],
        "measured_files": cand["measured_system"]["so_file"], "cache_version": cand["cache_version"], "contracts_unchanged": CONTRACTS,
        "optional_field_added": "route_d.source_goal_completion (source-goal-completion/1)",
        "regression_verdict": reg.get("verdict"), "regression_gates": {k: v["verdict"] for k, v in gates.items()},
        "product_gates_all_pass": all(v == "PASS" for v in product_gates.values()),
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "semantic_development": {"served": sem["served"], "comp_expectations_met": sem["comp_expectations_met"],
                                 "previously_served_changed": sem["previously_served_changed"]},
        "acceptance": {"text": tacc["grades"], "image": iacc["grades"], "wrong_scene_served": tacc["wrong_scene_served"] + iacc["wrong_scene_served"]},
        "scene_invariants": {k: inv[k] for k in ("plane_constraint_probes", "section_intersection_dihedral_probes", "new_served_checks", "new_served_failed", "mutations_caught")},
        "segmentation_final_candidate": {s2: {k: v for k, v in r.items() if k in ("pages", "merged_without_prompt", "pages_every_problem_cleanly_selectable", "unnecessary_selection_prompts")} for s2, r in seg.items()},
        "browser_e2e": {"goal_flows": f"{e2e['passed']}/{e2e['total']}", "image_selection": f"{img['passed']}/{img['total']}",
                        "failed_rows": [r["case"] for r in e2e["rows"] if not r["pass"]],
                        "failed_row_cause": "instrument has no construction-timing criterion for a distance goal (all other checks of the row pass)"},
        "new_locked_external_evaluation": "BLOCKED_DATA", "independent_h1": "NOT_MEASURED", "sealed_h1_rows_opened": 0,
        "locked_w2_w3_rows_used": 0, "live_ai_calls": 0,
        "physical_low_end": "NOT_MEASURED", "merge_push_deploy": "NOT_PERFORMED", "student_images_in_git": False,
        "report": "AXO_COMPOSITIONAL_SEMANTICS_SIMULATION_GOALS_REPORT.md",
        "hash_policy": "SHA-256 of bytes with CRLF normalised to LF; excludes run.json itself", "artifacts": artifacts})
    print(reg.get("verdict"), product_gates, len(artifacts), "artifacts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
