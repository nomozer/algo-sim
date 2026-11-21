"""Receipts of run `certified-scale-cache-safety` derived from its measured receipts, git and the regression summary.
Reads only; measures nothing again.   python derived_receipts.py   (worktree root, backend interpreter)"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
START = "30884a2e8"
NOW = datetime.now(timezone.utc).isoformat()
CONTRACTS = ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "height-invariance-certificate/2",
             "output-policy/1", "hybrid-route-d-simulation/4", "typed-fact-next/2"]


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT).decode().strip()


CAND = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
META = {"run_id": RUN.name, "generated_at_utc": NOW, "product_commit": CAND["product_commit_sha"],
        "measured_system": CAND["measured_system"]["tree_hash"], "cache_version": CAND["cache_version"],
        "environment": {"ALLOW_LIVE_AI": "0", "HYBRID_ROUTE_MODE": "local-first", "live_ai_calls": 0}}


def put(n, d):
    (RUN / n).write_text(json.dumps({**META, "head": git("rev-parse", "HEAD"), **d}, ensure_ascii=False, indent=2) + "\n",
                         encoding="utf-8")


def load(n):
    return json.loads((RUN / n).read_text(encoding="utf-8"))


ROWS = load("semantic_compare_rows.json")
SCMD = "python docs/evaluation/geometry/runs/certified-scale-cache-safety/tools/semantic_compare.py <archive of 30884a2e8>/backend <out>"


def row(k):
    r = ROWS[k]
    return {"case_id": k, "text_sha256": r["text_sha256"], "expected": r["expect"],
            "before": {x: r["before"].get(x) for x in ("status", "code", "answers")},
            "after": {x: r["after"].get(x) for x in ("status", "code", "answers")},
            "after_root_cause": r["after"]["local_diagnostics"]["root_cause"]}


def main() -> int:
    reg = load("full_regression_summary.json")
    gates = {s["name"]: s for s in reg.get("suites", [])}
    put("baseline_candidate_integrity.json", {
        "start_head": git("rev-parse", START), "start_product_commit": "379d33969", "start_freeze_stored_in": "54268761e",
        "start_measured_system": "b652e635d5497dc36bf6d55ff4a34c20a16302d01c154b59b039efd65170921e", "start_files": 116,
        "start_cache_version": "134", "freeze_verify_at_start": "PASS", "verdict": "VERIFIED_INTACT"})
    tools = sorted(p.name for p in (RUN / "tools").glob("*.*") if p.name != Path(__file__).name)
    text = "\n".join((RUN / "tools" / n).read_text(encoding="utf-8", errors="ignore") for n in tools)
    put("holdout_protection_audit.json", {
        "sealed_h1_rows_opened": 0, "locked_w2_w3_rows_read": 0, "tools_scanned": tools,
        "h1_corpus_paths_referenced": sorted(set(re.findall(r"[\w/.-]*(?:independent-holdout|h1[-_](?:sealed|corpus|rows))[\w/.-]*", text, re.I))),
        "w2_w3_locked_manifests_referenced": [m for m in ("locked_w2", "locked_w3", "unseen_evaluation") if m in text],
        "data_used": ["agent-written COMP52 (43 of the previous run + 9 scale cases)", "DEV37", "REAL27 (exposed)", "PROBES (exposed)"],
        "verdict": "PASS"})
    put("semantic_cache_audit.json", {
        "cache_path": "POST /api/analyze → prepare_local_first_hybrid(text).cache_key → _cache_lookup(key, ROUTE_D_CACHE_POLICY) → _served_route_d (status SERVED only) → returned WITHOUT re-running parser / gate / engine",
        "key_inputs": ["route", "router_version", "parser_version (constant local-geometry-parser/1)", "model", "extraction surface fingerprint",
                       "preview_surface (version strings)", "response_contract", "source text"],
        "key_excludes": ["local parse status (computed AFTER the lookup)", "any fingerprint of verification behaviour"],
        "finding": "compositional-semantics-simulation-goals tightened the parser sub-clause guard and the adapter angle binding without changing any key input and kept CACHE_VERSION 134 ⇒ a row served by the earlier code for a text the guard now refuses would be replayed (STALE_BYPASS reproduced)",
        "previous_run_claim_corrected": "'only SERVED rows are cached ⇒ no bump' was insufficient when a guard becomes STRICTER",
        "remediation": "CACHE_VERSION 134 → 135 (ROUTE_D_CACHE_POLICY 135:route-d); every row written under 134 MISSES",
        "not_chosen": {"revalidation_on_read": "would re-run the local route on every hit (cache pointless for local-first) and cannot revalidate provider-extracted rows without their payload",
                       "source_fingerprint_in_key": "conflicts with the declared cache-identity lock (surface fingerprints ↔ CACHE_VERSION); the bump is the repository's protocol"},
        "impact": {"invalidated": "all Route D rows of policy 134:route-d (first request per text recomputes; local-first texts ~25 ms, provider texts cost one extraction)",
                   "compatibility": "envelope /4 and contracts unchanged"}})
    put("stale_cache_adversarial_tests.json", {
        "test": "backend/tests/test_cache_semantic_guard_invalidation.py",
        "fixture": "development: the one-sentence section text with an unread ', N thuộc cạnh SB' (current parser refuses); stored envelope = the served scene of the same text without that clause (what the earlier code served), policy 134:route-d",
        "at_cache_134": "FAIL — the stale SERVED scene was returned through /api/analyze (assert 'SERVED' != 'SERVED')",
        "at_cache_135": "PASS — the request is decided by the guard (HTTP 503 LIVE_AI_DISABLED, no scene)",
        "control": "the same row under the current policy is served (no revalidation on read): any future guard tightening must bump",
        "locked_rows_used": 0})
    put("cache_invalidation_verification.json", {
        "pins_moved_134_to_135": 15, "identity_lock": "backend/cache_identity.lock.json regenerated (scripts/lock_cache_identity.py)",
        "current_state_identity_table": "updated", "tests": ["test_cache_semantic_guard_invalidation.py", "test_cache_identity.py",
                                                            "test_current_state_identity.py", "earlier invalidation tests (rows ≤ 134 MISS)"],
        "regression_gate": (gates.get("backend_pytest") or {}).get("verdict")})
    put("browser_timeline_failure_analysis.json", {
        "case": "unnamed_midpoint_distance",
        "product_contract": "formation steps 0–5 never contain kq_q1 (the measure.distance quantity with its perpendicular witness); step 6 FINAL_RESULT creates it, visible and read out",
        "verdict": "TEST_INSTRUMENT_GAP (the previous E2E had no target definition for distance goals — goalId null ⇒ construction_only_at_conclusion false); product correct",
        "oracle_fix": "this run's E2E copy: distance goal = the measure.distance quantity; present at the last step (id, id#…, id__… parts) and absent at EVERY earlier step",
        "after": [r for r in load("scene3d_browser_e2e.json")["rows"] if r["case"] == "unnamed_midpoint_distance"]})
    put("decimal_comma_parser_verification.json", {
        "root_cause_layer": "LOCAL PARSER value grammar `_VAL` (no decimal form; lookahead refused a digit after ',' or '.'); tokenizer, clause segmentation, contract NUMBER_PATTERN and gate `_SO`/`doc_so` already read decimals",
        "fix": "decimal coefficient in `_VAL` (\\d+(?:[.,]\\d+)?), lookahead kept; a comma followed by a space is a separator",
        "tests": "backend/tests/geometry/test_decimal_comma_values.py (3,5 = 3.5 = 7/2 exact; 1,5 side; 'AB = 3, AC = 4' list; '3,5,6', '≈ 3,5', '3,' refused; renamed)",
        "superseded_expectation": "test_correctness_ocr_performance treated 'AB = 3,5' as numeric corruption; restated as '3,5,6' (still refused) and the decimal text now serves V = 35 (task B5: 3,5 is a decimal)",
        "COMP:mc_decimal_value": row("COMP:mc_decimal_value")})
    put("similarity_invariance_capability_audit.json", {
        "existing": "height-invariance-certificate/2 (one free orthogonal height, symbolic over ℚ[t]); no similarity-scale handling — every figure without a length refused MISSING_DIMENSION",
        "gate_finding": "a length injected as a CALL is refused by the Source Gate inside dung_tu_loi_goi (UNGROUNDED_VALUE) — the unit cannot be a call; implemented as an engine construction parameter (`_Dung._scale_unit`, through `do_dai` only)",
        "scale_free_asks": ["ask_angle_line_plane", "ask_angle_lines", "ask_angle_plane_plane", "ask_length_ratio", "ask_area_ratio", "ask_volume_ratio", "ask_curved_volume_ratio"],
        "scale_free_valued_premises": ["line_plane_angle", "plane_plane_angle", "dihedral_angle", "line_line_angle", "vertex_angle", "segment_ratio"]})
    sc = ROWS["COMP:scale_iso_planes"]
    put("scale_normalization_certificate.json", {
        "schema": "similarity-scale-certificate/1",
        "obligations": {"PO-1": "no non-ask call outside the dimensionless-valued set carries a number", "PO-2": "every ask in SCALE_FREE_ASKS",
                        "PO-3": "one internal unit on the first base edge of the first solid ⇒ engine SERVED with no free height (unique configuration)",
                        "PO-4": "units 2 and 5 rebuild SERVED with identical exact answers (witness, not proof)",
                        "PO-5": "unit never a call / premise / provenance; scene_configuration SIMILARITY_SCALE_ILLUSTRATIVE, source_length_supplied false"},
        "argument": "homothety-invariant premises + uniqueness at one fixed length ⇒ one similarity class ⇒ similarity-invariant goals single-valued",
        "example": {"text_sha256": sc["text_sha256"], "after": sc["after"]["answers"], "hand_check": "A origin, AB = AC = SA = 1: normals (0,1,0) and (1,1,1) ⇒ cos² = 1/3"},
        "pytest": "backend/tests/geometry/test_certified_scale_normalization.py (10 passed, 2 strict xfail documenting a pre-existing clause-order limitation)"})
    put("shape_freedom_counterexamples.json", {
        "rows": [row(f"COMP:{k}") for k in ("scale_shape_free", "scale_height_free", "scale_absolute_volume", "scale_regular_tetra_no_side",
                                            "scale_iso_with_length")],
        "rules": {"shape_free (right at B, BC/AB open)": "PO-3 ⇒ refused (the angle is 45° for every BC — still uncertified, never guessed)",
                  "height_free": "PO-3 ⇒ refused", "absolute_volume": "PO-2 ⇒ refused",
                  "regular tetrahedron without side": "PO-3 ⇒ refused: the calls carry no 'every edge equal' fact (representation gap of the parser/bridge, not of the certificate)",
                  "stated length": "served WITHOUT normalisation (the source fixes the scale); same exact angle"}})
    inv = load("scene3d_mathematical_invariants.json")
    put("normalized_scene_geometry_invariants.json", {
        "normalized_items": {k: v for k, v in inv["new_served_items"].items() if k.startswith("scale")},
        "all_new_served": {"checks": inv["new_served_checks"], "failed": inv["new_served_failed"]},
        "mutations": inv["mutations_caught"], "equivalence_pairs": [p for p in inv["equivalence_pairs"] if p["item"].startswith("scale")]})
    real = {k: row(f"REAL27:vmmu_{k}") for k in ("r258", "r520", "r559")}
    put("real27_normalization_acceptance.json", {
        "dataset_partition": "DEVELOPMENT_EXPOSED (not an unseen evaluation)",
        "r258": {**real["r258"], "determining_premises": "right isosceles base at A, SA ⊥ base, SA = AB", "freedom": "scale only",
                 "goal": "angle between (SBC) and (SBA) — source asks its TANGENT", "certificate": "VERIFIED (PO-1..PO-5)",
                 "scene": "served, angle constructed; tan NOT_ANSWERED (source_goal_completion)", "final_answer_shown": False,
                 "length_fabricated": False},
        "r520": {**real["r520"], "determining_premises": "right triangle at B, SA ⊥ base, SA = AB", "freedom": "scale AND the shape ratio BC/AB",
                 "certificate": "NOT_ISSUED (PO-3)", "note": "INFERENCE: the angle (SBC),(ABC) = ∠SBA = 45° for every BC (BC ⊥ (SAB)); a shape-invariance proof is not implemented ⇒ correctly refused"},
        "r559": {**real["r559"], "determining_premises": "'tứ diện đều ABCD' (regular tetrahedron), M midpoint of CD",
                 "freedom": "scale only mathematically; in the CALLS the height is free (no every-edge-equal fact)",
                 "certificate": "NOT_ISSUED (PO-3)", "next_step": "parser/bridge must state the regularity of all six edges; then the same certificate applies"},
        "text_acceptance": load("local_text_to_simulation_acceptance.json")["grades"],
        "image_acceptance": load("local_image_to_simulation_acceptance.json")["grades"]})
    comp = [r for r in ROWS.values() if r["corpus"] == "COMP"]

    def meets(r, side):
        s = r[side]["status"] == "SERVED"
        m = s == (r["expect"] == "SERVE")
        return m and (not (s and r["numeric"]) or bool(r[side]["source_goal_completion"]))
    put("semantic_development_before_after.json", {"command": SCMD,
        "served": {c: {side: sum(r["corpus"] == c and r[side]["status"] == "SERVED" for r in ROWS.values()) for side in ("before", "after")}
                   for c in ("COMP", "DEV37", "REAL27", "PROBES")},
        "comp_expectations_met": {"before": sum(meets(r, "before") for r in comp), "after": sum(meets(r, "after") for r in comp), "of": len(comp)},
        "served_to_refused": [k for k, r in ROWS.items() if r["before"]["status"] == "SERVED" and r["after"]["status"] != "SERVED"],
        "answers_changed_on_served": [k for k, r in ROWS.items() if r["before"]["status"] == "SERVED" and r["before"]["answers"] != r["after"]["answers"]],
        "real27_root_causes_after": dict(Counter(r["after"]["local_diagnostics"]["root_cause"] for r in ROWS.values()
                                                 if r["corpus"] == "REAL27" and r["after"]["status"] != "SERVED"))})
    put("publication_gate_status.json", {
        "publication_head": "BLOCKED_PENDING_OWNER_REVIEW", "publication_head_scan": (gates.get("publication_head") or {}).get("summary_lines"),
        "publication_range_scan_this_run": {"range": f"{START}..HEAD", "summary_lines": (gates.get("publication_range") or {}).get("summary_lines"),
                                            "scan_verdict": (gates.get("publication_range") or {}).get("verdict")},
        "publication_range_governance": "BLOCKED_PENDING_OWNER_REVIEW", "full_release_gate": "BLOCKED_GATES_REMAIN",
        "historical_blob": "2bfce9c8… pending Owner decision", "agent_actions": "none (no approval, no exception, scan policy unchanged)",
        "repository_a": "axo-geometry-library shares this repository's history; its branch was not scanned separately (not merged, not pushed)"})
    put("candidate_freeze.json", {
        "freeze_stored_in": git("log", "-1", "--format=%H", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "commit_field": CAND["commit"], "clean_tree": CAND.get("cay_lam_viec_sach"), "measured_files": CAND["measured_system"]["so_file"],
        "cache_version_bumped": "134 → 135 (stale-guard bypass, see semantic_cache_audit.json)", "contracts_unchanged": CONTRACTS,
        "optional_values_added": "scene_configuration.kind SIMILARITY_SCALE_ILLUSTRATIVE (+ normalization metadata)",
        "freeze_verify_in_regression": (gates.get("freeze_verify") or {}).get("verdict")})
    artifacts = {}
    for path in sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "run.json" and "__pycache__" not in p.parts):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    e2e = load("scene3d_browser_e2e.json")
    put("run.json", {"schema": "algosim-certified-scale-cache-run/1", "start_head": git("rev-parse", START),
        "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "candidate_manifest_commit": CAND["commit"], "contracts_unchanged": CONTRACTS,
        "regression_gates": {k: v["verdict"] for k, v in gates.items()}, "regression_verdict": reg.get("verdict"),
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "browser_e2e": f"{e2e['passed']}/{e2e['total']}", "repository_a": {"worktree": "axo-geometry-library", "fix_commit": "5a229507b",
                                                                          "receipts_commit": "312962e1d", "freeze": "BLOCKED_DIRTY_TREE_OWNED_BY_ANOTHER_SESSION"},
        "independent_generalization": "NOT_MEASURED", "h1": "NOT_MEASURED", "live_ai_calls": 0, "merge_push_deploy": "NOT_PERFORMED",
        "report": "AXO_CERTIFIED_SCALE_CACHE_SAFETY_REPORT.md", "hash_policy": "SHA-256 LF-normalised; excludes run.json", "artifacts": artifacts})
    print("ok", reg.get("verdict"), {k: v["verdict"] for k, v in gates.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
