"""Write this run's summary receipts from the evidence files already committed in the run directory.

Counts are read from the receipts; per-case root causes are the agent's adjudication of the layered traces
(labelled INFERENCE where they go beyond what a trace prints). Nothing is re-measured here.  Run from backend/.
"""
from __future__ import annotations

import json
import statistics
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PRIOR = RUN.parent / "controlled-vision-real-image-validation"
START = "c5bb73f51"
NOW = datetime.now(timezone.utc).isoformat()
CONTRACTS = ["geometry-fact-planner/26", "geometry-functions/33", "geometry-function-engine/24", "height-invariance-certificate/2", "output-policy/1"]
TESTS = "backend/tests/geometry/test_local_semantic_coverage.py"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode("utf-8", "replace").strip()


def load(name: str, base: Path = RUN) -> dict:
    return json.loads((base / name).read_text(encoding="utf-8"))


def write(name: str, data: dict) -> None:
    (RUN / name).write_text(json.dumps({"run_id": RUN.name, "generated_at_utc": NOW, **data}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# Agent adjudication of each of the 17 traces (root cause, the general rule it would need, what this run did).
ADJ = {
    "vmmu_r254": ("PARSER_COVERAGE", "projection of a vertex onto the base 'trùng với trọng tâm' (centroid foot) and a sub-solid volume goal (tứ diện A'ABC)", "oblique prism by centroid foot; sub-solid volume goal", "NOT_REPAIRED_CAPABILITY_GAP"),
    "vmmu_r256": ("PARSER_COVERAGE", "equilateral lateral face plus face-perpendicular-to-base '(SAB) ⊥ (ABCD)'; source typo 'đên'", "lateral face ⟂ base construction", "NOT_REPAIRED_CAPABILITY_GAP"),
    "vmmu_r258": ("SOURCE_GATE", "bare equality 'SA = AB' was silently dropped (fixed); the goal asks 'Tang của góc', an output function the closed output policy does not serve, and the problem is scale-free", "tan output function under output-policy versioning", "PARTIAL_FACT_READ_GOAL_FUNCTION_UNSUPPORTED"),
    "vmmu_r270": ("PARSER_COVERAGE", "volume goal without 'khối' ('Tính thể tích lăng trụ …') and a value followed by 'biết' with no punctuation", "volume goal wording; value boundary at 'biết' / new capitalised clause", "REPAIRED_SERVED_MATCHES_KEY"),
    "vmmu_r277": ("PARSER_COVERAGE", "points defined as reflections of O through edge midpoints", "point reflection construction", "NOT_REPAIRED_CAPABILITY_GAP"),
    "vmmu_r284": ("PARSER_COVERAGE", "lateral face perpendicular to the base is held by an explicit unsupported-relation guard", "lateral face ⟂ base construction", "NOT_REPAIRED_CAPABILITY_GAP"),
    "vmmu_r298": ("PARSER_COVERAGE", "regular prism with a list of dimensions 'cạnh đáy …, cạnh bên …' in either order", "solid dimension list", "REPAIRED_SERVED_MATCHES_KEY"),
    "vmmu_r375": ("PARSER_COVERAGE", "'độ dài cạnh đáy … cạnh bên …' was dropped by the parser; the Source Gate then caught the unread premise (the gate was right)", "solid dimension list with 'độ dài'", "REPAIRED_SERVED_MATCHES_KEY"),
    "vmmu_r460": ("SOURCE_GATE", "'… theo a bằng' tail was not recognised as asking (fixed) and 'vuông ở' (fixed); still 'tam giác SAB cân' is unread and the hypotenuse-leg relation is not modelled", "isosceles vertex inference; hypotenuse from legs", "PARTIAL_GATE_FIX_STILL_REFUSED"),
    "vmmu_r463": ("PARSER_COVERAGE", "solid written without the dot 'ABCDA'B'C'D'' gives no solid; rhombus defined by an inverse condition", "dot-less prism notation (ambiguous split must ask, not guess)", "NOT_REPAIRED_CAPABILITY_GAP"),
    "vmmu_r488": ("PARSER_COVERAGE", "volume of a sub-solid 'B'.ACC'A''", "sub-solid volume goal", "NOT_REPAIRED_CAPABILITY_GAP"),
    "vmmu_r491": ("PARSER_COVERAGE", "point I on BC left free (answer must be invariant in I); invariance certificate does not cover it", "free-parameter invariance", "NOT_REPAIRED_CAPABILITY_GAP"),
    "vmmu_r498": ("SOURCE_GATE", "dimension list fixed; the goal 'cosin của góc' asks an output function the closed policy does not serve, so NOT_ASKED_IN_SOURCE is the correct refusal", "cos output function under output-policy versioning", "PARTIAL_FACT_READ_GOAL_FUNCTION_UNSUPPORTED"),
    "vmmu_r513": ("SOURCE_GATE", "missing period before the question (fixed by the value boundary); the plane is written without parentheses, so the question context is unsupported", "plane names without parentheses", "PARTIAL_STILL_REFUSED"),
    "vmmu_r520": ("EXACT_KERNEL", "parse now complete; the problem is scale-free and the exact kernel refuses with MISSING_DIMENSION instead of inventing a length", "scale-free answers (ratio/angle) without a length", "PARSE_REPAIRED_KERNEL_REFUSES_SAFELY"),
    "vmmu_r537": ("SOURCE_GATE", "an area value 'a²' for a face is not a supported premise value; the gate fails closed with UNGROUNDED_VALUE (correct)", "area premise values", "NOT_REPAIRED_FAIL_CLOSED_CORRECT"),
    "vmmu_r538": ("PARSER_COVERAGE", "angle operands named by role 'cạnh bên' and 'mặt đáy' instead of by points", "role-named angle operands in a regular pyramid", "NOT_REPAIRED_CAPABILITY_GAP"),
}


def main() -> int:
    head = git("rev-parse", "HEAD")
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    prior_cand = json.loads(git("show", f"{START}:docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"))
    base, final = load("semantic17_trace_baseline.json"), load("semantic17_trace_final.json")
    bcase = {c["case_id"]: c for c in base["cases"]}
    text = load("text_to_geometry_before_after.json")
    fresh = load("fresh_external_evaluation.json")
    manifest = {i["case_id"]: i for i in load("new_in_scope_image_manifest.json", PRIOR)["items"]}

    write("baseline_integrity.json", {
        "start_head": git("rev-parse", START), "start_head_is_ancestor_of_head": subprocess.run(["git", "merge-base", "--is-ancestor", START, "HEAD"], cwd=ROOT).returncode == 0,
        "candidate_at_start": {"commit": prior_cand["commit"], "product_commit": prior_cand["product_commit_sha"],
                               "measured_system": prior_cand["measured_system"]["tree_hash"], "files": prior_cand["measured_system"]["so_file"], "cache_version": prior_cand["cache_version"]},
        "verified_at_start": "freeze_evaluation_candidate.py --verify matched cd9b9f518805d305 (115 files) on a clean tree before any change (VERIFIED FACT, session log)",
        "commits_since_start": git("log", "--format=%h %s", f"{START}..HEAD").splitlines(),
        "product_diff_since_start": git("diff", "--stat", START, "HEAD", "--", "backend/app", "frontend/src").splitlines()[-1]})

    write("candidate_commit_reconciliation.json", {
        "question": "Two SHAs were quoted for the controlled-vision candidate: 835786746 and a78b1e087. Which is the candidate?",
        "answer": "Both, in different roles. 835786746 is the HEAD at freeze time and is what EVALUATION_CANDIDATE.json records as `commit`; a78b1e087 is the child commit that stores that manifest. They measure the same product (product commit c53be83db, measured_system cd9b9f51…).",
        "evidence": {"manifest_commit_field_at_start": prior_cand["commit"], "manifest_product_commit_at_start": prior_cand["product_commit_sha"],
                     "a78b1e087_parent": git("rev-parse", "a78b1e087^"), "a78b1e087_changes_only": git("show", "--name-only", "--format=", "a78b1e087").splitlines()},
        "mislabel": "controlled-vision run.json named the storing commit as the candidate; that is a labelling slip, not two candidates. The previous run's receipts are immutable and are not edited; this receipt is the correction layer.",
        "classification": "VERIFIED_FACT"})

    rows = []
    for c in final["cases"]:
        cid, b = c["case_id"], bcase[c["case_id"]]
        layer, cause, rule, status = ADJ[cid]
        rows.append({"case_id": cid, "partition_in_previous_run": manifest[cid]["partition"], "expected_answer": manifest[cid]["expected_answer"],
                     "previous_run_label": b["previous_layer_label"], "baseline": {"first_failure_layer": b["first_failure_layer"], "reason_code": b["local_parser"].get("reason_code")},
                     "final": {"first_failure_layer": c["first_failure_layer"], "status": c["local_parser"].get("status"), "reason_code": c["local_parser"].get("reason_code"),
                               "downstream": c["downstream_on_built_facts"]},
                     "root_cause_owner": layer, "root_cause": cause, "candidate_general_rule": rule, "repair_status": status,
                     "label": "INFERENCE (agent adjudication of the layered trace; traces are VERIFIED FACT)"})
    write("semantic17_case_diagnostics.json", {
        "inputs": ["semantic17_trace_baseline.json (c5bb73f51 + working tree before any fix)", "semantic17_trace_final.json (frozen candidate)"],
        "reference_status": "AGENT_TRANSCRIBED_UNVERIFIED", "exposure": "all 17 were read while writing the rules: development evidence only",
        "repair_status_counts": dict(Counter(r["repair_status"] for r in rows)),
        "root_cause_owner_counts": dict(Counter(r["root_cause_owner"] for r in rows)),
        "previous_run_misclassification": "Of the 5 cases the previous run filed under Source Gate, only r460 was a gate gap; r375 and r537 were parser silent drops the gate correctly caught, r498 is a parser drop plus an unsupported output function, r513 a missing period plus plane notation.",
        "cases": rows})

    def taxonomy(trace: dict) -> dict:
        return dict(Counter(f"{c['first_failure_layer']}:{c['local_parser'].get('reason_code')}" for c in trace["cases"]))
    write("parser_failure_taxonomy.json", {
        "population": "the 17 polyhedron transcriptions the solver did not finish without AI (controlled-vision)",
        "baseline": taxonomy(base), "final": taxonomy(final),
        "parser_classes": {"silent_drop_caught_by_gate": ["vmmu_r375", "vmmu_r537"], "unparsed_goal_wording": ["vmmu_r270", "vmmu_r254", "vmmu_r488", "vmmu_r538", "vmmu_r277", "vmmu_r256"],
                           "unparsed_fact_construction": ["vmmu_r284", "vmmu_r491", "vmmu_r256"], "solid_notation": ["vmmu_r463"],
                           "value_boundary_without_punctuation": ["vmmu_r270", "vmmu_r513"], "bare_equality": ["vmmu_r258"], "dimension_list": ["vmmu_r298", "vmmu_r375", "vmmu_r498"]},
        "guard_notes": "Each unparsed clause now carries the guard that held it (clause.notes, e.g. UNBACKED_EQUALS@i:ctx, NO_GOAL_RULE_MATCHED) in the coverage report."})

    write("parser_generalization_receipt.json", {
        "rules": [
            {"rule": "solid dimension list", "code": "local_geometry_parser._solid_dimension_items / _DIM_FIRST_RE / _DIM_NEXT_RE",
             "covers": "'cạnh đáy …, cạnh bên …' in either order, optional 'độ dài (của)', 'đều bằng/là/='; regular pyramid and right/regular prism",
             "stops": "at the first gap or a repeated attribute; each later item quotes its own text so the gate attributes every value once",
             "tests": [f"{TESTS}::test_regular_solid_dimension_lists_serve_the_hand_derived_answer", f"{TESTS}::test_dimension_items_stop_at_the_first_gap_and_never_repeat_an_attribute",
                       f"{TESTS}::test_contradicting_lateral_edge_is_refused_not_served", f"{TESTS}::test_unsupported_dimension_word_still_fails_closed"]},
            {"rule": "bare segment equality", "code": "local_geometry_parser._BARE_SEGMENT_EQUALITY_RE",
             "covers": "'SA = AB (= …)' as equal_length premises with their own quote", "rejects": "degenerate (SA = AA), repeated (SA = AS), scaled (SA = 2AB)",
             "tests": [f"{TESTS}::test_bare_segment_equality_is_read_as_congruence_with_its_own_quote", f"{TESTS}::test_degenerate_repeated_or_scaled_equalities_are_not_congruences",
                       f"{TESTS}::test_scale_free_equality_problem_refuses_safely_instead_of_inventing_a_length"]},
            {"rule": "volume goal wording", "covers": "'thể tích (V) (của) …', bare 'lăng trụ'", "rejects": "a volume goal naming a solid that was never declared",
             "tests": [f"{TESTS}::test_volume_goal_without_khoi_or_with_named_variable", f"{TESTS}::test_volume_goal_naming_an_undeclared_solid_stays_unparsed"]},
            {"rule": "right / right-isosceles triangle vertex 'ở X'", "tests": [f"{TESTS}::test_right_triangle_vertex_with_o_or_tai"]},
            {"rule": "Source Gate: '… theo a bằng' is a question tail; a value closes at 'biết' or a new capitalised clause",
             "code": "registry._HOI_CUOI_DE, registry._DUOI_BANG", "rejects": "'theo a bằng 2a³' (an assignment, not a question); 'AB = 2 BC', disjunction 'hoặc'",
             "tests": [f"{TESTS}::test_multiple_choice_question_with_theo_a_tail_is_asked", f"{TESTS}::test_theo_a_tail_with_a_value_is_an_assignment_not_a_question",
                       f"{TESTS}::test_value_closed_by_bien_and_by_a_new_capitalised_sentence", f"{TESTS}::test_value_boundary_does_not_accept_multiples_or_disjunctions"]},
        ],
        "not_per_case": "No rule names a case id, a vertex label set or an expected answer; every rule is exercised by synthetic statements different from the 17 (tests above) and fails closed on counterexamples.",
        "ab_evidence": {"text_route_before": text["before_outcomes"], "text_route_after": text["after_outcomes"], "wrong_served_after": text["wrong_served_after"]},
        "generalisation_claim": "NOT_ESTABLISHED: the 23 transcriptions were exposed; the fresh sample had 2 in-scope items and neither was served (see fresh_external_evaluation.json)"})

    gate_rows = [{"case_id": c["case_id"], "gate": c["downstream_on_built_facts"].get("source_gate"), "first_failure": c["first_failure_layer"],
                  "refusal_correct": ADJ[c["case_id"]][3] not in ("REPAIRED_SERVED_MATCHES_KEY",)} for c in final["cases"] if c["downstream_on_built_facts"].get("source_gate")]
    write("source_gate_failure_taxonomy.json", {
        "final_gate_verdicts_on_built_facts": dict(Counter(r["gate"] for r in gate_rows)),
        "gate_refusal_classes": {"SOURCE_PREMISE_UNREAD": "a premise sentence the parser did not turn into a fact (parser gap, gate correct)",
                                 "NOT_ASKED_IN_SOURCE": "the source asks a function the output policy does not serve (tan, cos) — correct",
                                 "UNGROUNDED_VALUE": "a value the parser could not ground (area a²) — correct, fail closed",
                                 "QUESTION_CONTEXT_UNSUPPORTED": "plane written without parentheses — correct"},
        "true_gate_gaps_found": ["'… theo a bằng' question tail (r460)", "value boundary at 'biết' / new clause without punctuation (r270, r513)"],
        "loosened": False, "cases": gate_rows})

    write("source_grounding_contract_verification.json", {
        "contract": "every typed fact cites a verbatim quote; every value occurrence in a premise sentence is attributed to exactly one call's quote; asked quantities must be asked in the source",
        "changes": ["_HOI_CUOI_DE accepts an optional 'theo <letter>' before 'bằng/là' at the end of the question only",
                    "_DUOI_BANG closes a value at 'biết' or at a capitalised new clause, so the next clause is not swallowed into the value"],
        "weakened": False,
        "why_not_weakened": "Both changes narrow where a value or a question ends; neither lets an unread premise or an unasked quantity pass. Counterexamples stay refused: 'theo a bằng 2a³' is not a question, 'AB = 2 BC' is not an equality of segments, a 'hoặc' disjunction is refused as NEGATED_CLAUSE.",
        "tests": [f"{TESTS}::test_theo_a_tail_with_a_value_is_an_assignment_not_a_question", f"{TESTS}::test_value_boundary_does_not_accept_multiples_or_disjunctions",
                  "backend/tests (full suite, see full_regression_summary.json)"],
        "wrong_served_after_on_exposed_set": text["wrong_served_after"], "classification": "VERIFIED_FACT for the tests; INFERENCE for 'no weakening' beyond the tested cases"})

    schema = Counter((c["downstream_on_built_facts"].get("schema") or "NONE") for c in final["cases"])
    write("typed_facts_bridge_integrity.json", {
        "population": "facts the parser built for the 17 cases (also partial parses), replayed through TypedFactNext schema and bridge_v2",
        "schema_results": dict(schema), "bridge_ambiguities": sum(bool(c["downstream_on_built_facts"].get("bridge_ambiguities")) for c in final["cases"]),
        "invented_facts": "none: every new fact carries its own verbatim quote (Source Gate ACCEPTED only where the whole text is read)",
        "contradiction_handling": f"{TESTS}::test_contradicting_lateral_edge_is_refused_not_served (INCONSISTENT_FACTS)",
        "schema_version_changed": False})

    served = [c for c in text["cases"] if c["after"]["outcome"] == "LOCAL_SOLVED"]
    write("planner_composition_verification.json", {
        "contracts_unchanged": CONTRACTS, "planner_or_registry_function_added": False,
        "served_after": [{"case_id": c["case_id"], "answer": c["after"]["kernel"]["answers"], "expected": c["expected"]} for c in served],
        "composition": "Newly served cases use existing registry functions chosen by the deterministic planner from the typed facts (regular solid + segment length + volume); no per-case handler, no AI choosing a function.",
        "wrong_served": text["wrong_served_after"], "fresh_wrong_served": fresh["wrong_served"],
        "classification": "VERIFIED_FACT (answers vs dataset key on exposed items); generalisation NOT_ESTABLISHED"})

    write("angle_output_policy_receipt.json", {
        "backend": {"output_policy": "output-policy/1 unchanged", "rule": "degrees only when the source asks for a measure in degrees ('số đo góc', 'theo độ') and cos² is one of 1, 3/4, 1/2, 1/4, 0; otherwise the exact cos² is served",
                    "observed": {"'Tính góc giữa hai đường thẳng AC và A'D' (cube)": "cos²=1/4", "'Tính số đo góc giữa …'": "60°"}, "versioned_change": False},
        "frontend": {"change": "scene3d-model.ts soDoGocDacBiet / COS2_DO_DAC_BIET: a requested angle served as a special cos² is labelled 'Góc …' with the degree value and keeps 'cos² = …' as the exact value; no branch guessing (angles between lines/planes lie in [0°, 90°], where cos² determines the angle)",
                     "tests": ["frontend/src/components/hybrid-preview-contract.test.tsx (2 tests)"],
                     "reach_on_product_path": "NOT_VISIBLE: browser_span_angle_check.json shows the shipped workspace hides the final answer (simulation first) and does not mount the Scene3DExplorer analysis panel that renders requestedResults. The change is correct but has no learner-visible effect on the current workspace."},
        "classification": "VERIFIED_FACT"})

    browser = load("browser_span_angle_check.json")
    write("multi_span_confirmation_receipt.json", {
        "problem": "OCR splits one expression into adjacent flagged spans ('4BCD-' + 'A'B'C'D''); the space between belongs to no span, so per-span edits cannot rebuild 'ABCD.A'B'C'D''.",
        "change": "photo-problem-flow.ts extendSpanTarget + actions extend-span / restore-span; PhotoProblemPanel buttons 'Nối với chữ kế tiếp' / 'Tách lại như máy đọc'",
        "rules": ["gap of 1-3 spaces/tabs only", "next word ≤ 24 chars and not prose (two lower-case letters)", "never across a sentence end", "a flagged span inside the extension is absorbed whole",
                  "extending or restoring clears every confirmation"],
        "unit_tests": "frontend/src/components/photo-span-review.test.tsx (4 new)",
        "browser": {"file": "browser_span_angle_check.json", "passed": browser["passed"], "total": browser["total"], "evidence_kind": browser["evidence_kind"]},
        "classification": "VERIFIED_FACT (FIXTURE prepare response; real UI and real /api/analyze)"})

    before, after, rep = load("sqlite_concurrency_before.json"), load("sqlite_concurrency_after.json"), load("sqlite_concurrency_after_repeat.json")
    lv = lambda d: {L["simultaneous"]: {k: L[k] for k in ("prepare_200", "auth_me_5xx", "prepare_5xx", "prepare_401", "prepare_401_after_auth_me_5xx", "transport_errors", "prepare_ms_p50")}
                    | {"health_max_ms": L["health_probe_ms"]["max"], "server_exception_types": sorted({e.get("sqlite_errorname") or e["exception_type"] for e in L["server_exceptions"]})} for L in d["levels"]}
    write("sqlite_concurrency_before_after.json", {
        "root_cause": "Synchronous OCR and region detection ran on the event loop inside async /api/input/prepare while the request's get_caller session held an uncommitted write (session row flushed, committed at teardown). With the loop blocked, other requests waited on the SQLite write lock past the 5 s busy timeout -> SQLITE_BUSY.",
        "fix": "backend/app/ingestion/unified_input.py runs detect_problem_regions, count_problem_headers_on_page and run_local_ocr_route through starlette run_in_threadpool (commit d6b38b172)",
        "regression_test": "backend/tests/test_input_prepare_concurrency.py::test_prepare_keeps_the_event_loop_free_while_local_ocr_runs",
        "before": lv(before), "after": lv(after), "after_repeat": lv(rep),
        "throughput_note": "Prepare latency at 8 simultaneous uploads is ~13 s after the fix: OCR work is CPU bound and queues. The fix removes errors and keeps the server responsive (/api/health max < 0.7 s); it does not add OCR throughput.",
        "classification": "VERIFIED_FACT (loopback measured_app, own SQLite file, scripted uploads)"})

    write("api_error_classification.json", {
        "observed_before_fix_at_8_uploads": lv(before)[8],
        "classification": {"500 on /api/auth/me and /api/input/prepare": "INFRASTRUCTURE (SQLITE_BUSY: database is locked) — a server fault, never a math refusal",
                           "401 on /api/input/prepare": "CONSEQUENCE: every 401 followed a failed /api/auth/me session creation in the same client; the client then had no session cookie. Mapping 401 is correct for a request without a session.",
                           "dropped connections": "transport errors while the event loop was blocked"},
        "after_fix": "no 5xx, no 401, no dropped connection in 120 uploads (after + after_repeat)",
        "auth_contract_changed": False})

    ocr = load("ocr_false_rejection_audit.json")
    no_diagram = [c["case_id"] for c in ocr["cases"] if c["verdict"] == "HOLD_WITH_FLAGGED_SPANS_ALL_FALSE_ALARMS" and "DIAGRAM_FACTS_UNVERIFIED" not in c["blocking_reasons"]]
    write("ocr_false_rejection_summary.json", {
        "source": "ocr_false_rejection_audit.json", "images_with_all_critical_facts": ocr["images_with_all_critical_facts"],
        "verdicts": ocr["verdicts_among_all_facts_images"], "blocking_flags_total": ocr["blocking_flags_total"], "blocking_flags_false_alarms": ocr["blocking_flags_false_alarms"],
        "candidate_false_rejections_without_diagram_hold": no_diagram,
        "decision": "NO_GATE_CHANGE",
        "why": "Most holds also carry DIAGRAM_FACTS_UNVERIFIED; the references are agent transcriptions, not human-verified; the word diff is a proxy and found unflagged math differences on 2 images (r266 lost '∠' earlier, r520 lost part of the goal). Loosening span flags on this evidence could pass a wrong statement silently."})

    img_b = {p: load(f"api_acceptance_{p}.json", PRIOR)["cases"] for p in ("development", "frozen_external_evaluation")}
    img_a = {p: load(f"api_acceptance_{p}.json")["cases"] for p in img_b}
    write("image_to_scene3d_before_after.json", {
        "before_source": "controlled-vision-real-image-validation/api_acceptance_*.json (c53be83db)", "after_source": "api_acceptance_*.json in this run (working tree = frozen product)",
        "route": "image -> /api/input/prepare (local OCR) -> scripted correction of flagged spans only -> /api/analyze; ALLOW_LIVE_AI=0",
        "by_partition": {p: {"before": dict(Counter(r["grade"]["verdict"] for r in img_b[p])), "after": dict(Counter(r["grade"]["verdict"] for r in img_a[p])),
                             "prepare_ms_median_before": statistics.median(r["prepare_ms"] for r in img_b[p]), "prepare_ms_median_after": statistics.median(r["prepare_ms"] for r in img_a[p])} for p in img_b},
        "newly_served": sorted(r["case_id"] for p in img_a for r in img_a[p] if r["grade"]["verdict"] == "SERVED_MATCHES_DATASET_KEY"
                               and {x["case_id"]: x for x in img_b[p]}[r["case_id"]]["grade"]["verdict"] != "SERVED_MATCHES_DATASET_KEY"),
        "wrong_served_after": sorted(r["case_id"] for p in img_a for r in img_a[p] if r["grade"]["verdict"] == "SERVED_DIFFERS_FROM_DATASET_KEY"),
        "why_r270_r375_not_from_image": "solved from the transcription but OCR does not recover every critical fact of those images (local_ocr_* receipts of the previous run)",
        "exposure": "all items exposed during development; not a generalisation figure"})

    exposed17 = [r["case_id"] for r in rows]
    write("dataset_partition_audit.json", {
        "previous_partitions": {"development": [k for k, v in manifest.items() if v["partition"] == "development"],
                                "frozen_external_evaluation": [k for k, v in manifest.items() if v["partition"] == "frozen_external_evaluation"]},
        "exposed_in_this_run": {"items": sorted(manifest), "reason": "all 23 polyhedron transcriptions and the 17 failing traces were read while writing the rules",
                                "frozen_external_items_now_exposed": sorted(k for k in exposed17 if manifest[k]["partition"] == "frozen_external_evaluation")},
        "consequence": "The controlled-vision frozen_external_evaluation split is no longer held out for any claim about this run's rules; its after-numbers are development evidence.",
        "fresh_sample": {"pool": 142, "sampled_after_freeze": fresh["sample"]["size"], "seed": fresh["sample"]["seed"],
                         "remaining_reserved_untouched": fresh["sample"]["remaining_reserved_count"], "in_scope": fresh["in_scope_items"]},
        "independent_h1_pool_status": "94 rows remain listed-only (never downloaded or viewed); fresh_external_preregistration.json holds the list"})

    write("independent_h1_status.json", {
        "status": "NOT_MEASURED", "why": "No independent person selected, transcribed or scored any item; the fresh diagnostic was run by the same agent that wrote the fixes.",
        "reserved_pool": "94 untouched VMMU rows (fresh_external_preregistration.json: remaining_reserved_rows)",
        "needed": ["an independent transcriber/scorer", "a pre-registered protocol and stop rules", "owner decision"]})

    lat = load("parser_latency_before_after.json")
    write("performance_impact.json", {
        "parser": {"source": "parser_latency_before_after.json", "median_of_statement_medians_ms": lat["median_of_statement_medians_ms"],
                   "per_statement_after_over_before": lat["after_over_before_median_ratio"], "p95_ms": lat["p95_all_calls_ms"],
                   "sum_of_statement_medians_ms": {k: sum(r[k] for r in lat["per_statement_median_ms"]) for k in ("before", "after")},
                   "reading": "18 of 25 statements cost the same (ratio 0.94-1.08). The 7 that grew (1.6x-11x, at most ~15 ms) are the statements whose parse now goes further: more facts read and Stage 8 (bridge, planner, Source Gate) reached. One got faster. Milliseconds against seconds of OCR."},
        "prepare_image": {"source": "image_to_scene3d_before_after.json", "note": "medians from two separate sessions on the same machine; not a controlled comparison — no regression is claimed or excluded beyond that"},
        "concurrency": {"source": "sqlite_concurrency_before_after.json", "health_probe_max_ms_at_8": {"before": lv(before)[8]["health_max_ms"], "after": lv(after)[8]["health_max_ms"]}},
        "memory": "NOT_MEASURED: no new process, model or cache; the threadpool reuses AnyIO's default worker limit",
        "rust_or_prewarm": "not done (forbidden by the task)"})

    write("publication_owner_review_status.json", {
        "publication_head": "BLOCKED_PENDING_OWNER_REVIEW", "full_release_gate": "BLOCKED_GATES_REMAIN",
        "pending_findings_and_blobs": "unchanged from controlled-vision (97 findings / 18 blobs) unless full_regression_summary.json publication gates report otherwise",
        "agent_actions": "none: no approval written, no exception added, no history rewritten, no frozen evidence removed",
        "pending_templates": "K-1/R-1/S-2 re-bound to the refrozen measured_system as metadata only (pending_template_refresh.json); owner_decision stays PENDING_OWNER_DECISION"})

    write("candidate_freeze.json", {
        "head": head, "branch": git("branch", "--show-current"), "freeze_commit_field": cand["commit"], "freeze_stored_in": git("log", "-1", "--format=%h", "--", "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json"),
        "product_commit": cand["product_commit_sha"], "measured_system": cand["measured_system"], "cache_version": cand["cache_version"],
        "cache_version_bumped": False, "why_no_bump": "backend/tests/test_cache_identity.py passes against cache_identity.lock.json: the fingerprinted model surface (prompts, grammar card, schema, capability table, TypedFactNext and Hybrid surfaces) did not change. Cached rows hold only SERVED results; a parse that newly completes reaches the solver instead of a cached result.",
        "contracts_unchanged": CONTRACTS, "previous_candidate": {"commit": prior_cand["commit"], "measured_system": prior_cand["measured_system"]["tree_hash"]}})
    print("receipts written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
