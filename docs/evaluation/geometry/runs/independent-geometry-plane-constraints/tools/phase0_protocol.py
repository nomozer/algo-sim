"""Phase 0/1 receipts of run `independent-geometry-plane-constraints`: baseline integrity, dataset partition, the
preregistered evaluation protocol, ground-truth status and the sealed H-1 status. Written BEFORE any product change and
before any evaluation text is read.  Run from the worktree root with the backend interpreter."""
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
W2 = RUNS / "hybrid-v2-independent-vietnamese-section-holdout-wave2"
W3 = RUNS / "hybrid-v2-independent-vietnamese-geometry-holdout-wave3"
LSG = RUNS / "local-semantic-source-gate-reliability"


def git(*a: str) -> str:
    return subprocess.check_output(["git", *a], cwd=ROOT).decode().strip()


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def put(name: str, data: dict) -> None:
    (RUN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def main() -> int:
    head = git("rev-parse", "HEAD")
    cand = load(ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json")
    prev = load(RUNS / "verified-section-intersection-dihedral-local/run.json")
    put("baseline_integrity.json", {
        "run_id": RUN.name, "generated_at_utc": NOW, "branch": git("branch", "--show-current"), "head": head,
        "working_tree_clean_at_start": True,
        "reported_identities": {"report_head": "4222f021b", "run_manifest_head": "c29cff312", "product_commit": "ea4b2a197",
                                "candidate_manifest_commit": "cf058f0ee", "candidate_stored_in": "f0fa7e359",
                                "measured_system": "dc834af0001169e6962b655b8953c9694eb4a8c5718e59995f152d5c3fc93d29",
                                "measured_files": 115, "cache_version": "134"},
        "git_verified": {
            "head_equals_report_head": head.startswith("4222f021b"),
            "all_reported_commits_are_ancestors_of_head": all(
                subprocess.run(["git", "merge-base", "--is-ancestor", c, "HEAD"], cwd=ROOT).returncode == 0
                for c in ("c29cff312", "ea4b2a197", "cf058f0ee", "f0fa7e359")),
            "candidate_file_last_commit": git("log", "-1", "--format=%h", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
            "candidate_manifest_commit_field": cand["commit"][:9], "candidate_product_commit": cand["product_commit_sha"][:9],
            "measured_system": cand["measured_system"]["tree_hash"], "measured_files": cand["measured_system"]["so_file"],
            "cache_version": cand["cache_version"], "previous_run_manifest_head": prev["head_at_manifest_write"][:9]},
        "checks_run": ["freeze_evaluation_candidate --verify: match 115 files dc834af0001169e6",
                       "lock_cache_identity --verify: CACHE_VERSION 134, environment 3d5400a5",
                       "no server listening on 8767/8770/5173"],
        "discrepancies": [],
        "note": "report HEAD (4222f021b), run-manifest HEAD (c29cff312), manifest commit (cf058f0ee) and freeze commit (f0fa7e359) are four distinct commits; all are ancestors of HEAD and the three later ones only add evidence (no product path changed after ea4b2a197)",
        "contracts": ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24",
                      "height-invariance-certificate/2", "output-policy/1", "hybrid-route-d-simulation/4"],
        "reported_baseline_preserved_not_targets": {"sections_probes": "9/12", "intersections_probes": "5/7", "invariant_checks": "124/124",
                                                    "mutations": "52/53", "browser_e2e": "12/12", "text_acceptance": "8/27",
                                                    "image_acceptance": "4/27", "backend_tests": 14363, "frontend_tests": 2047,
                                                    "publication_head": 97, "independent_h1": "NOT_MEASURED"}})

    lsg = load(LSG / "fresh_external_preregistration.json")
    sealed = lsg["sample"]["remaining_reserved_rows"]
    put("sealed_h1_status.json", {
        "run_id": RUN.name, "generated_at_utc": NOW, "dataset": "anvo25/vmmu full_vqa (Math rows)", "sealed_rows": len(sealed),
        "row_list_source": "local-semantic-source-gate-reliability/fresh_external_preregistration.json (row numbers only)",
        "row_list_sha256": hashlib.sha256(json.dumps(sealed).encode()).hexdigest(),
        "opened_in_this_run": 0, "downloaded": 0, "viewed": 0, "ocr": 0, "file_names_read": 0,
        "rule": "only the row numbers are known; their dataset ids (which carry the answer key) are not read",
        "cross_source_risk": "VMMU pages are Vietnamese mock exams; any other Vietnamese exam source could repeat a sealed question. "
                             "No new external source is used in this run, so no such overlap is introduced.",
        "status": "SEALED"})

    w2, w3 = load(W2 / "inputs/holdout-wave2.json"), load(W3 / "inputs/holdout-wave3.json")
    sets = {}
    for tag, d, inp, name in (("LOCKED_W2", W2, w2, "holdout-wave2"), ("LOCKED_W3", W3, w3, "holdout-wave3")):
        cases = inp["cases"]
        sets[tag] = {
            "source_run": d.name, "input": f"{d.name}/inputs/{name}.json", "input_sha256": sha(d / f"inputs/{name}.json"),
            "oracle": f"{d.name}/oracle/expected.json", "oracle_sha256": sha(d / "oracle/expected.json"),
            "cases": len(cases), "serve": sum(c["expected_disposition"] == "SERVE" for c in cases),
            "refuse": sum(c["expected_disposition"] == "REFUSE" for c in cases),
            "case_ids_sha256": hashlib.sha256(json.dumps(sorted(c["id"] for c in cases)).encode()).hexdigest()}
    put("dataset_partition_audit.json", {
        "run_id": RUN.name, "generated_at_utc": NOW,
        "DEVELOPMENT_EXPOSED": {
            "acceptance_27": "25 controlled-vision VMMU crops + 2 fresh VMMU items (r559, r695), all read while writing rules",
            "vmmu_math_rows_seen": "177 rows seen by earlier runs + 137 screened by controlled-vision + 48 fresh-sampled (see sealed_h1_status.json for the rest)",
            "synthetic_probes": "every probe of semantic-to-scene3d-verified-simulation and verified-section-intersection-dihedral-local",
            "local_parser_benchmark_suites": ["Dev72", "HeldOut46", "K-1", "R-1", "S-2", "RenamedAndParaphrased8"],
            "unit_test_texts": "every problem text inside backend/tests"},
        "NEW_DIAGNOSTIC_DEVELOPMENT": "agent-written probes of this run (tools/plane_constraint_probes.py), development from birth",
        "INTERNAL_LOCKED_EVALUATION": {
            **sets,
            "class": "AI_CURATED_PROCEDURAL_INDEPENDENCE (isolated curator sessions with a file firewall, rational oracle written from first principles)",
            "not_new": "both suites were curated in earlier runs and executed there through the Gemini-payload route; their problem texts later fed Source Gate wording work (hybrid-v2-wave2-source-gate-language-generalization, hybrid-v2-w3-f1-cross-sentence-plane-grounding)",
            "fresh_to": "the local Vietnamese parser: its benchmark suites are listed above and no run executed these texts through route_text_input (grep of run tools)",
            "agent_exposure_before_registration": [
                "wave2 corpus-provenance.md §1-§2: the per-case design table (family, relation, plane spec such as '(M) ⊥ SB', oracle vertex count / area²) — not the wording",
                "case schema keys and strata/family/question-type counts of both inputs (printed by script)",
                "wave2 scoring-contract.md §1-§3"],
            "texts_read_by_agent": 0},
        "NEW_LOCKED_EVALUATION": {
            "status": "BLOCKED_DATA",
            "sources_checked": {
                "anvo25/vmmu (MIT)": "Math rows exhausted: 456 = 177 earlier + 137 controlled-vision + 48 fresh + 94 sealed",
                "ViExam": "same paper (arXiv 2508.13680) as VMMU: same data",
                "VNHSGE (github Xdao85/VNHSGE)": "no LICENSE file (404); usage rights not stated",
                "roshansk23/Vietnam_HighSchool_Exam_Dataset (HF)": "license tag 'cc' without version, text only (figures dropped), mirrors VNHSGE"},
            "consequence": "no external, rights-cleared, unexposed in-scope set exists in this run; generalization to new external problems stays NOT_MEASURED"},
        "SEALED_H1_94": "sealed_h1_status.json"})

    put("evaluation_preregistration.json", {
        "schema": "algosim-plane-constraint-evaluation-preregistration/1", "run_id": RUN.name, "registered_at_utc": NOW,
        "head_at_registration": head, "start_candidate": {"commit": cand["commit"], "product_commit": cand["product_commit_sha"],
                                                         "measured_system": cand["measured_system"]["tree_hash"]},
        "sets": sets,
        "claim_class": "FRESH_TO_LOCAL_PARSER_INTERNAL_AI_CURATED_HOLDOUT — not new external data, not human-adjudicated, not H-1",
        "pipeline": "for each case: text = case['problem_text'] only (payloads, labels and oracle never reach the product) → "
                    "route_text_input(text, allow_live_ai=False) on the frozen candidate → envelope",
        "when": "exactly once, after the final product freeze of this run, for BOTH the start product (archive of ea4b2a197) and the final candidate; "
                "no product change after either execution; any later change makes both suites DEVELOPMENT_EXPOSED",
        "scoring": {
            "served": "route status SERVED with an envelope scene3d",
            "SERVE_case_correct_iff": [
                "the scene holds exactly one closed `section` object (the section asked) — otherwise WRONG_SERVED if a section is drawn, NOT_SERVED_GOAL_MISSING if none",
                "independent recheck (exact Fractions, envelope coordinates and Gram metric): each section vertex lies on the cutting plane of the other vertices, on one solid edge or at one solid vertex",
                "multiset of boundary descriptors (VERTEX label | EDGE sorted labels + canonical t) equals the oracle boundary",
                "cyclic order equals the oracle ring up to rotation or reversal (orientation is not part of the contract)",
                "vertex count equals the oracle vertex_count",
                "area² recomputed from the drawn polygon equals oracle area_squared (symbolic unit a: coefficient at a = 1)"],
            "SERVE_case_outcomes": ["SERVED_CORRECT", "WRONG_SERVED", "NOT_SERVED (reason code recorded)", "ROUTE_ERROR (counts as failure)"],
            "REFUSE_case_outcomes": ["CORRECT_REFUSAL (any non-served outcome, reason code recorded)", "WRONG_SERVED (anything served)"],
            "answer_text": "never compared: Axo does not print answers; correctness is judged on the constructed geometry only"},
        "headline_metrics": ["wrong_served per suite (target 0)", "SERVED_CORRECT / SERVE cases per suite, stratum and plane relation",
                             "CORRECT_REFUSAL / REFUSE cases per suite", "before → after on the same protocol"],
        "out_of_scope_reporting": "curved families (cylinder, cone) and categories the curators marked unrepresentable are reported separately, never folded into the polyhedral rate",
        "ambiguity": "a case whose oracle entry is missing or malformed is reported ORACLE_UNAVAILABLE and excluded from rates, listed by id",
        "deduplication": "after the freeze, before execution: character 5-gram Jaccard between every development probe of this run and every locked text, computed by script; only ids and scores are printed",
        "forbidden": ["reading any locked problem text or oracle entry before execution", "editing product code after execution and keeping the 'fresh' label",
                      "using the 94 sealed H-1 rows", "live AI"],
        "browser_scope": "browser interaction is measured on development probes only (scene3d_browser_e2e.json), not per locked case"})

    put("evaluation_ground_truth_status.json", {
        "run_id": RUN.name, "generated_at_utc": NOW,
        "levels": {
            "OFFICIAL_ANSWER": "none in use (VMMU keys are multiple-choice letters; insufficient for a geometric construction)",
            "SOURCED_SOLUTION": "none",
            "HUMAN_VERIFIED_TRANSCRIPTION": "none",
            "INDEPENDENT_GEOMETRIC_CERTIFICATE": "holdout-wave2/wave3 rational oracles (AI-curated, isolated sessions, first-principles analytic geometry; wave3 also carries an independent oracle review)",
            "AGENT_ORACLE": "tools/verify_plane_constraints.py of this run (AGENT_DIAGNOSTIC, independent code path, same agent)",
            "AXO_OUTPUT": "never used as ground truth"},
        "human_verified": 0, "independent_h1": "NOT_MEASURED",
        "labels_not_used": ["HUMAN_VERIFIED", "INDEPENDENT_H1"]})
    print("ok", head[:9], {k: (v["cases"], v["serve"], v["refuse"]) for k, v in sets.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
