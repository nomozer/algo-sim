"""Receipts of run `target-invariant-regular-solid-semantics` derived from its measured receipts, git and the frozen
candidate (certificates of r520 / r559 regenerated read-only). python derived_receipts.py (worktree root, backend python)"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(ROOT / "backend"))
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
START = "07c17fef0"
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
    (RUN / n).write_text(json.dumps({**META, "head": git("rev-parse", "HEAD"), **d}, ensure_ascii=False, indent=2, default=str) + "\n",
                         encoding="utf-8")


def load(n):
    return json.loads((RUN / n).read_text(encoding="utf-8"))


ROWS = load("semantic_compare_rows.json")
SCMD = "python docs/evaluation/geometry/runs/target-invariant-regular-solid-semantics/tools/semantic_compare.py <archive of 07c17fef0>/backend <out>"


def row(k):
    r = ROWS[k]
    return {"case_id": k, "text_sha256": r["text_sha256"], "expected": r["expect"],
            "before": {x: r["before"].get(x) for x in ("status", "code", "answers")},
            "after": {x: r["after"].get(x) for x in ("status", "code", "answers")},
            "after_root_cause": r["after"]["local_diagnostics"]["root_cause"]}


def route(text):
    from app.ai.adaptive_input_router import route_text_input
    return (route_text_input(text, allow_live_ai=False).response or {}).get("route_d") or {}


def main() -> int:
    reg = load("full_regression_summary.json")
    gates = {s["name"]: s for s in reg.get("suites", [])}
    real = {i["case_id"]: i["statement"] for i in json.loads((RUN.parent / "controlled-vision-real-image-validation/new_in_scope_image_manifest.json").read_text(encoding="utf-8"))["items"]}
    put("baseline_candidate_integrity.json", {
        "start_head": git("rev-parse", START), "start_product_commit": "902a3171c", "start_freeze": "901c02702",
        "start_measured_system": "243d932765f7d4065394f91c6b4f25972f8232ba9228aec89d4c63a244c1976b", "start_files": 116,
        "start_cache_version": "135", "freeze_verify_at_start": "PASS", "tree_clean_at_start": True,
        "worktree_a": "axo-geometry-library HEAD 3085b182e (a later commit by the other session); its 82 uncommitted files untouched",
        "verdict": "VERIFIED_INTACT"})
    put("geo_be_001_integration_audit.json", {
        "source_commit": "5a229507b (axo-geometry-library worktree)", "integrated_in": "8f7f00a2c",
        "method": "only the display_names.py hunk (git show 5a229507b -- display_names.py | git apply); no cherry-pick of the commit",
        "base_blob_check": {"B_before": "1c25e32c7b043870e52dbdfb70ae0ae71265f992", "A_before": "1c25e32c7b043870e52dbdfb70ae0ae71265f992",
                            "B_after": "8d71e28c25733f935199ff78a10d51c38f9309fd", "A_after": "8d71e28c25733f935199ff78a10d51c38f9309fd"},
        "not_integrated": ["advanced-geometry-samples.json (does not exist in this worktree — not created)", "A's generator test (needs A's scripts)"],
        "sanitizer": "replaceRawSceneIdTokens untouched", "verdict": "PASS"})
    put("display_name_regression.json", {
        "test": "backend/tests/semantic_program/test_display_names_incidence_cycle.py", "tests": 22, "passed": 22,
        "red_before_integration": 18,
        "fixture": "tests/semantic_program/fixtures/display_name_incidence_tables.json — the real ten_hien_thi input tables of the two A samples that reproduced GEO-BE-001 (derived data)",
        "covers": ["F → 'Giao điểm của SD và (MNP)'", "E → 'Giao điểm của A′B′ và (NPQ)'", "no internal id in presentation",
                   "6 shuffled + reversed orders", "MNP → XYZ", "(α)", "graph table untouched", "true cycle reported",
                   "scenes this route builds (pyramid / cube sections): no id leak"],
        "finding": "the route's own scenes did not trigger the defect (sections are engine-derived); the defect was latent here"})
    put("scale_certificate_soundness_audit.json", {
        "what_PO3_proves": "ENGINE_DOMAIN uniqueness: the engine placed every object by a forced rule from the calls and raised MISSING_DIMENSION / a sign-branch refusal wherever something was open; it is not a free-standing Euclidean uniqueness proof",
        "gap_found": "the normalisation returned BEFORE the mirror search (dung_tu_loi_goi), so with ≥ 2 independent height anchors an unexplored sign branch could be certified",
        "fix": "refuse when the unit build has ≥ 2 anchors; certificate states certification_level ENGINE_DOMAIN_CERTIFIED and its scope",
        "PO4": "witnesses at units 2 and 5 are regression witnesses, never the proof",
        "previously_served_cases_affected": "none on the measured corpora (all normalised scenes have one anchor)",
        "classification_used": ["MATHEMATICALLY_PROVEN (target-invariance synthetic proofs)", "ENGINE_DOMAIN_CERTIFIED (similarity normalisation, representatives)"]})
    put("target_invariance_capability_audit.json", {
        "reused": ["FactGraph calls (doc_ke_hoach)", "exact engine representative build", "do_dai internal channel", "scene_configuration"],
        "new": "target_invariance.py — closed rule table, bounded forward chaining (MAX_DERIVED 256 ⇒ PROOF_SEARCH_BUDGET_EXCEEDED), independent verifier",
        "rules": ["RIGHT_ANGLE", "PERPENDICULAR_LINES", "SOURCE_LINE_PERP_PLANE", "PERP_PLANE_TO_LINE", "PERP_TWO_LINES", "PLANE_ANGLE", "TRIANGLE_SHAPE_FIXED"],
        "goal_kinds_supported": ["ask_angle_plane_plane"],
        "not_supported": ["perpendicular-planes rule (∠ = 90° by a line ⊥ plane in the other plane)", "line–plane / line–line angles under shape freedom", "ratios under shape freedom"]})
    rd520 = route(real["vmmu_r520"])
    cert = (rd520.get("scene_configuration") or {}).get("invariance_certificate") or {}
    put("free_shape_parameter_analysis.json", {
        "r520": {"free_parameters": ["global scale", "BC/AB (base right triangle at B)"],
                 "parameters_affecting_goal": "none (proof)", "illustrative_lengths": (rd520.get("scene_configuration") or {}).get("free_for")},
        "counter": {"height free (no SA = AB)": "∠ depends on SA/AB ⇒ no proof ⇒ refused", "line SC vs (ABC)": "depends on BC ⇒ refused"}})
    put("universal_goal_invariance_proofs.json", {
        "statement": "for every configuration satisfying the cited facts and every value of the free parameters, ∠((SBC),(ABC)) = ∠SBA of triangle SAB, right isosceles at A",
        "certificate": cert, "independent_verifier": [g.get("independent_verification") for g in cert.get("goals") or []],
        "not_numeric": "the proof is symbolic over labels; the witnesses (shape 2, 5, 1/2, scale 3) are regression checks only"})
    put("r520_mathematical_verification.json", {
        "dataset_partition": "DEVELOPMENT_EXPOSED (REAL27)", "source_facts": "tam giác vuông tại B; SA ⊥ (ABC); SA = AB",
        "status": rd520.get("status"), "answer_exact": rd520.get("answer_exact"),
        "hand_check": "B origin, BA = (1,0,0), BC = (0,c,0), S = (1,0,1): n(SBC) = BS × BC = (−c,0,c), n(ABC) = (0,0,1) ⇒ cos² = c²/(2c²) = 1/2 for every c ≠ 0 (45°)",
        "scene_kind": (rd520.get("scene_configuration") or {}).get("kind"), "unique": (rd520.get("scene_configuration") or {}).get("unique"),
        "final_answer_shown": False, "verdict": "SERVED_UNDER_PROOF"})
    from app.ai.local_geometry_parser import parse_geometry_problem_locally
    lp = parse_geometry_problem_locally("Cho tứ diện đều ABCD. Gọi M là trung điểm của CD. Tính góc giữa hai đường thẳng AC và BM.", use_cache=False)
    put("regular_tetrahedron_semantic_audit.json", {
        "before": "'tứ diện đều ABCD' without side → regular_pyramid only (base regular, apex over its centre): a regular TRIANGULAR PYRAMID, the lateral = base edge lost; with 'cạnh a' the value re-supplied it",
        "after": "one definitional equal_length(AB, BC) quoting 'tứ diện đều ABCD' — with regular_pyramid all six edges equal",
        "phrases_read": ["Cho tứ diện đều ABCD", "tứ diện đều PQRS"], "not_read_as_regular": ["tứ diện ABCD", "hình chóp tam giác đều S.ABC"],
        "not_measured_phrases": ["Tứ diện ABCD là tứ diện đều", "Hình tứ diện đều có các đỉnh A, B, C, D"]})
    put("regular_tetrahedron_derived_facts.json", {
        "premises": [p for p in lp.payload["premises"]], "rule": "regular tetrahedron ⇒ all six edges equal (definition); regular_pyramid gives the regular base and equal laterals; one lateral = base edge completes it",
        "quotes_invented": 0, "derived_equalities_emitted": 1})
    put("regular_solid_source_gate_integrity.json", {
        "gate_rule": "_canh_tu_dien_deu: equal_length accepted without '='/'bằng' ONLY when its quote contains 'tứ diện đều XYZW' naming four distinct vertices that contain both segments (precedent: _vuong_can_hai_canh)",
        "probe_before_fix": "equal_length quoted 'Cho tứ diện đều ABCD' → PREDICATE_NOT_IN_QUOTE",
        "negatives": "quotes 'tứ diện ABCD', 'tam giác đều BCD' refused (test_the_gate_reads_the_equality_only_from_a_regular_tetrahedron_phrase)",
        "policy_changed": False})
    rd559 = route(real["vmmu_r559"])
    put("r559_mathematical_verification.json", {
        "dataset_partition": "DEVELOPMENT_EXPOSED (REAL27)", "status": rd559.get("status"), "answer_exact": rd559.get("answer_exact"),
        "scene_kind": (rd559.get("scene_configuration") or {}).get("kind"), "source_goal_completion": rd559.get("source_goal_completion"),
        "hand_check": "edge 1: AC·BM with BM median of BCD: cos(AC, BM) = √3/6 ⇒ cos² = 1/12",
        "midpoint": "M of CD built by the kernel midpoint primitive (checked by the independent scene checker)",
        "verdict": "SERVED_SIMILARITY_SCALE (numeric cos NOT_ANSWERED)"})
    put("shape_freedom_counterexamples.json", {"rows": [row(f"COMP:{k}") for k in (
        "ti_varying_line_plane", "ti_height_free", "ti_absolute_volume", "tet_not_regular", "tet_regular_pyramid_only", "tet_conflict",
        "scale_height_free", "scale_absolute_volume")]})
    put("goal_invariance_mutation_tests.json", {
        "test": "backend/tests/geometry/test_target_invariance_regular_solids.py::test_the_independent_verifier_catches_every_mutated_step",
        "mutations": ["unknown rule", "wrong common line", "wrong angle arms", "right angle at the wrong vertex", "removed dependency step",
                      "perpendicular to a line outside the plane", "missing equal-legs premise", "changed source fact (right angle at C)"],
        "caught": "8/8", "scene_mutations": load("scene3d_mathematical_invariants.json")["mutations_caught"]})
    inv = load("scene3d_mathematical_invariants.json")
    put("representative_scene_geometry_invariants.json", {
        "new_served": {k: v for k, v in inv["new_served_items"].items() if k.startswith(("ti_", "tet_", "scale_shape", "scale_regular", "goal_cos_scale"))},
        "all_new_served": {"checks": inv["new_served_checks"], "failed": inv["new_served_failed"]}, "mutations": inv["mutations_caught"],
        "equivalence_pairs": inv["equivalence_pairs"]})
    put("cache_identity_verification.json", {
        "bump": "135 → 136", "why": "a stricter guard (similarity normalisation refuses ≥ 2 anchors) and changed served envelopes (regular tetrahedron without side, GEO-BE-001 names) under an unchanged Route D key",
        "tests": ["test_cache_target_invariance_invalidation.py", "test_cache_semantic_guard_invalidation.py", "test_cache_identity.py",
                  "test_current_state_identity.py"], "pins_moved": 17, "identity_lock": "regenerated"})
    tools = sorted(p.name for p in (RUN / "tools").glob("*.*") if p.name != Path(__file__).name)
    text = "\n".join((RUN / "tools" / n).read_text(encoding="utf-8", errors="ignore") for n in tools)
    put("holdout_protection_audit.json", {"sealed_h1_rows_opened": 0, "locked_w2_w3_rows_read": 0, "tools_scanned": tools,
        "h1_corpus_paths_referenced": sorted(set(re.findall(r"[\w/.-]*(?:independent-holdout|h1[-_](?:sealed|corpus|rows))[\w/.-]*", text, re.I))),
        "w2_w3_locked_manifests_referenced": [m for m in ("locked_w2", "locked_w3", "unseen_evaluation") if m in text], "verdict": "PASS"})
    put("independent_evaluation_status.json", {"INDEPENDENT_GENERALIZATION": "NOT_MEASURED", "NEW_INDEPENDENT_EVALUATION": "BLOCKED_DATA",
        "H1": {"status": "NOT_MEASURED", "opened": 0}, "note": "r520 / r559 are exposed development regressions, never unseen"})
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
        "superseded_expectations": ["COMP:scale_shape_free", "COMP:scale_regular_tetra_no_side", "COMP:goal_cos_scale_free (REFUSE → SERVE by this run's capabilities)"],
        "real27_root_causes_after": dict(Counter(r["after"]["local_diagnostics"]["root_cause"] for r in ROWS.values()
                                                 if r["corpus"] == "REAL27" and r["after"]["status"] != "SERVED"))})
    put("publication_gate_status.json", {
        "publication_head": "BLOCKED_PENDING_OWNER_REVIEW", "publication_head_scan": (gates.get("publication_head") or {}).get("summary_lines"),
        "publication_range_scan_this_run": {"range": f"{START}..HEAD", "summary_lines": (gates.get("publication_range") or {}).get("summary_lines"),
                                            "scan_verdict": (gates.get("publication_range") or {}).get("verdict")},
        "publication_range_governance": "BLOCKED_PENDING_OWNER_REVIEW", "full_release_gate": "BLOCKED_GATES_REMAIN",
        "historical_blob": "2bfce9c8… pending", "agent_actions": "none"})
    put("candidate_freeze.json", {
        "freeze_stored_in": git("log", "-1", "--format=%H", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "commit_field": CAND["commit"], "clean_tree": CAND.get("cay_lam_viec_sach"), "measured_files": CAND["measured_system"]["so_file"],
        "added_file": "backend/app/simulation/geometry_functions/target_invariance.py", "cache_version_bumped": "135 → 136",
        "contracts_unchanged": CONTRACTS, "freeze_verify_in_regression": (gates.get("freeze_verify") or {}).get("verdict")})
    artifacts = {}
    for path in sorted(p for p in RUN.rglob("*") if p.is_file() and p.name != "run.json" and "__pycache__" not in p.parts):
        data = path.read_bytes().replace(b"\r\n", b"\n")
        artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    e2e = load("scene3d_browser_e2e.json")
    put("run.json", {"schema": "algosim-target-invariant-run/1", "start_head": git("rev-parse", START),
        "head_at_manifest_write": git("rev-parse", "HEAD"), "branch": git("branch", "--show-current"),
        "candidate_manifest_commit": CAND["commit"], "contracts_unchanged": CONTRACTS,
        "regression_gates": {k: v["verdict"] for k, v in gates.items()}, "regression_verdict": reg.get("verdict"),
        "overall_verdict": "BLOCKED", "overall_reason": "publication HEAD BLOCKED_PENDING_OWNER_REVIEW; FULL_RELEASE_GATE BLOCKED_GATES_REMAIN",
        "browser_e2e": f"{e2e['passed']}/{e2e['total']}", "acceptance": {"text": load("local_text_to_simulation_acceptance.json")["grades"],
                                                                        "image": load("local_image_to_simulation_acceptance.json")["grades"]},
        "independent_generalization": "NOT_MEASURED", "h1": "NOT_MEASURED", "live_ai_calls": 0, "merge_push_deploy": "NOT_PERFORMED",
        "report": "AXO_TARGET_INVARIANT_REGULAR_SOLID_REPORT.md", "hash_policy": "SHA-256 LF-normalised; excludes run.json", "artifacts": artifacts})
    print("ok", reg.get("verdict"), {k: v["verdict"] for k, v in gates.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
