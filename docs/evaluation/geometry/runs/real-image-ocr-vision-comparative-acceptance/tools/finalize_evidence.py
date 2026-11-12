"""Derive reviewable summaries from measured receipts. Never edits source measurements."""
from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from typing import Sequence

import evaluate_acceptance as E
from app.ai.adaptive_input_router import compare_ocr_and_vision_facts, extract_structured_math_tokens

RUN = E.RUN
ROOT = E.ROOT
REPORT = "AXO_REAL_IMAGE_OCR_VISION_COMPARATIVE_ACCEPTANCE_REPORT.md"


def load(name):
    return json.loads((RUN / name).read_text(encoding="utf-8"))


def derived(name, **fields):
    E.write(name, {**E.header(), "classification": "DERIVED_FROM_REFERENCED_MEASUREMENTS_NOT_A_NEW_MEASUREMENT", **fields})


def offline_comparison():
    baseline = subprocess.check_output(["git", "show", "6bb22fa3b:backend/app/ai/adaptive_input_router.py"], cwd=ROOT).decode("utf-8")
    function = next(n for n in ast.parse(baseline).body if isinstance(n, ast.FunctionDef) and n.name == "compare_ocr_and_vision_facts")
    namespace = {"extract_structured_math_tokens": extract_structured_math_tokens, "Sequence": Sequence}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "baseline-comparator", "exec"), namespace)
    original = namespace["compare_ocr_and_vision_facts"]
    statement = "Cho hình chóp S.ABCD có cạnh đáy 2a và chiều cao 3a. Tính thể tích khối chóp."
    cases = [
        ("coefficient_changed", statement, statement.replace("đáy 2a", "đáy a"), True),
        ("height_changed", statement, statement.replace("cao 3a", "cao 2a"), True),
        ("dimension_binding_swapped", statement, statement.replace("đáy 2a", "đáy 3a").replace("cao 3a", "cao 2a"), True),
        ("exam_header_omitted", "Câu 1: " + statement, statement, False),
        ("scalar_spacing", statement, statement.replace("2a", "2 a"), False),
        ("same_dimensions_reordered", statement, "Cho hình chóp S.ABCD có chiều cao 3a và cạnh đáy 2a. Tính thể tích khối chóp.", False),
    ]
    rows = [{"id": name, "expected_conflict": expected, "baseline_conflict": original(left, right)["has_conflict"],
             "candidate": compare_ocr_and_vision_facts(left, right)} for name, left, right, expected in cases]
    assert all(row["candidate"]["has_conflict"] == row["expected_conflict"] for row in rows)
    derived("adaptive_hybrid_comparison.json", mode="MOCK_TRANSCRIPT_CONFLICT_ROUTING_ONLY", actual_provider_calls=0,
            vision_recorded_replay="NOT_MEASURED_NO_REAL_PROVIDER_RECORDING", vision_live="LIVE_VISION_NOT_MEASURED",
            rows=rows, baseline_missed_conflicts=sum(r["expected_conflict"] and not r["baseline_conflict"] for r in rows),
            candidate_missed_conflicts=sum(r["expected_conflict"] and not r["candidate"]["has_conflict"] for r in rows),
            architecture_ranking="DECISION_PENDING_LIVE_EVIDENCE", limitations="Six authored development fixtures, not image recognition or live Vision accuracy")


def main():
    E.summarize()
    offline_comparison()
    summary = load("image_acceptance_summary.json")
    corpus = load("new_image_corpus_manifest.json")
    regression = load("full_regression_summary.json")
    prior = summary["prior_corpus_actual_rerun"]
    new = summary["new_corpus"]
    evaluation = new["frozen_external_evaluation"]
    dev = new["development"]
    browser_name = "frontend_browser_final_existing.json" if (RUN / "frontend_browser_final_existing.json").exists() else "frontend_browser_existing_scenarios.json"
    confirmation_name = "frontend_browser_final_confirmation.json" if (RUN / "frontend_browser_final_confirmation.json").exists() else "frontend_browser_confirmation_audit.json"
    browser = load(browser_name)
    extra_browser = load(confirmation_name)
    latency = load("cold_warm_latency_benchmark.json")
    resources = load("ocr_worker_resource_profile.json")
    # Re-measurements taken on the sealed candidate (evaluate_acceptance.py --tag final). The untagged precursor
    # receipts keep their own identity; nothing is relabelled.
    final_latency, final_resources, final_cold = (load(name) for name in (
        "cold_warm_latency_benchmark_final.json", "ocr_worker_resource_profile_final.json", "cold_process_benchmark_final.json"))
    assert final_latency["head"] == final_resources["head"] == final_cold["head"]
    final_head = final_latency["head"][:9]
    final_api = [case for partition in ("development", "frozen_external_evaluation") for case in load(f"api_acceptance_{partition}_final.json")["cases"]]
    new_cases = [case for partition in ("development", "frozen_external_evaluation") for case in load(f"local_ocr_{partition}.json")["cases"]]
    api_cases = [case for partition in ("development", "frozen_external_evaluation") for case in load(f"api_acceptance_{partition}.json")["cases"]]

    derived("local_ocr_evaluation.json", source="image_acceptance_summary.json", partitions=new,
            trusted_human_transcriptions=0, handwriting_accuracy="NOT_MEASURED_NO_NEW_HANDWRITTEN_IMAGES",
            recognition_metric_scope="OCR full draft vs target statement+options. Figure labels, footers and adjacent fragments in OCR count as insertions; this is NOT a pure matched-region recognizer benchmark.",
            critical_fact_precision="NOT_MEASURED_NO_ADJUDICATED_PREDICTED_FACTS",
            critical_fact_recall="Only exact-substring proxy below; not semantic adjudication",
            false_acceptance="Zero verified images; no observed auto acceptance in this small corpus, not a universal safety guarantee",
            false_refusal="NOT_MEASURED_NO_INDEPENDENT_SUPPORTED_CASE_ORACLE")
    derived("math_symbol_error_analysis.json", source="local_ocr_* and corpus manifest", cases=[{
        "case_id": c["case_id"], "partition": c["partition"], "scores": c["scores_against_unverified_reference"],
        "critical_fact_substring_proxy": c.get("critical_fact_recovery_proxy"),
        "blocking_reasons": c["blocking_reasons"]} for c in new_cases],
        exclusions=["Choice {3;4} in r310 and 22a² in r450 are answers, not premises; do not treat those manifest strings as critical input facts.",
                    "Token precision/recall includes MC choices and does not establish mathematical fact precision/recall."])
    derived("ocr_targeted_improvements.json", recognition_algorithm_change=False, ocr_model_change=False,
            development_images_used_for_tuning=[], frozen_evaluation_images_used_for_tuning=[],
            reason="New corpus is too small and predominantly outside solver scope; no image-specific heuristics warranted.",
            product_fixes=["worker exit/protocol/reaping", "codepoint-correct spans", "confirmation reset after edit",
                           "target-bound worded dimension conflict check", "prepare session guard runs off the event loop", "plain reviewed status label"],
            before_after_recognition="NO_RECOGNITION_ALGORITHM_CHANGE: current receipts preserve initial 4ab43853 measurements in logs/initial-*.json",
            false_acceptance_before_after="Not a population estimate; mock dimension conflicts missed3/3 before,0/3 after (adaptive_hybrid_comparison.json)",
            geometry_expansion=False, wrong_served_new="No automatic result on eight images; all corrected attempts unserved")

    final_conc = final_resources["concurrent_uploads"]
    kernel_of = lambda cases: {c["case_id"]: [(o["category"], (o.get("kernel") or {}).get("status"), (o.get("kernel") or {}).get("reason_code")) for o in c["outcomes"]] for c in cases}
    api_final_matches = kernel_of(final_api) == kernel_of(api_cases) and [c["prepare_status"] for c in final_api] == [c["prepare_status"] for c in api_cases]
    before = load("concurrent_upload_diagnosis_before.json")
    after = load("concurrent_upload_diagnosis_after.json")
    derived("resource_measurement_correction.json", corrects="ocr_worker_resource_profile.json::concurrent_uploads.failure_cause",
            original_observation="5/20 HTTP500 on the measured precursor4ab43853; this observation is retained",
            original_causal_attribution="UNSUPPORTED: original failure_surface.json has no SQLite exception event",
            source_mechanism="Controlled SQLite-lock regression test failed with sqlite3.OperationalError when the synchronous session guard blocked event-loop cleanup; moved guard to existing run_in_threadpool; test passes",
            exact_cause_of_original_5xx="UNKNOWN: current bounded HTTP reproduction did not reproduce the original failures",
            subsequent_before_fix_http_statuses=[r["http_status"] for row in before["rounds"] for r in row["requests"]],
            subsequent_after_fix_http_statuses=[r["http_status"] for row in after["rounds"] for r in row["requests"]],
            causal_improvement_claim=False,
            first_hand_log_observation="NOT_RECOVERABLE_AS_ARTIFACT: the session that ran the precursor benchmark read the server traceback of one HTTP500 (sqlite3 'database is locked' on UPDATE auth_sessions inside the prepare session guard) and an ad-hoc repeat with new guest sessions failed 4/30. That log was overwritten by later server restarts and no receipt was written, so it is recorded here as testimony, not evidence.",
            final_candidate_concurrent_uploads={k: final_conc[k] for k in ("requests", "http_200", "http_5xx", "server_exception_events", "failure_cause")},
            final_candidate_head=final_latency["head"],
            final_load_acceptance=f"LIMITED: sealed candidate {final_conc['http_200']}/{final_conc['requests']} with {len(final_conc['server_exception_events'])} captured server exceptions (two simultaneous new-session uploads, {final_latency['repeats_per_mode']} rounds, SQLite). Sustained or wider concurrent load and PostgreSQL remain NOT_MEASURED")
    derived("frontend_browser_e2e.json", existing_scenarios=browser["summary"], confirmation_audit={"passed": extra_browser["passed"], "total": extra_browser["total"]},
            source_receipts=[browser_name, confirmation_name],
            browser_zoom="Old harness used deviceScaleFactor (DPR), added harness uses CSS zoom1/1.1; browser chrome zoom itself NOT_MEASURED",
            real_student_usability="NOT_MEASURED", screenshots="Ignored local only because source-image crops have redistribution limitations")
    student = load("student_confirmation_usability.json")
    student.update(automated_confirmation_status="AUTOMATED_E2E_VERIFIED_NOT_HUMAN_STUDY",
                   automated_evidence_paths=[browser_name, confirmation_name],
                   automated_scenarios_passed=browser["summary"]["passed_scenarios"] + extra_browser["passed"],
                   automated_scenarios_total=browser["summary"]["total_scenarios"] + extra_browser["total"],
                   automation_is_human_usability_evidence=False)
    E.write("student_confirmation_usability.json", student)
    derived("user_correction_e2e.json", prior_corpus=prior, new_cases=api_cases,
            categories_separate=True, real_user_corrections="NOT_MEASURED", participant_count=0,
            edits_are="Script chooses only flagged spans from agent reference; unflagged errors remain. It does not replace the entire statement.",
            stale_cache="Historical browser scenario changes60°→45°, gets different answers and scene without a second image prepare. Confirmation now invalidates on further edit.")
    derived("real_image_to_scene3d_acceptance.json", prior_corpus=prior, new_cases=api_cases,
            oracle_status="Prior mathematical derivations retained; all new corpus served answers would remain ungraded without separate oracle",
            new_in_scope_oracle={"case_id": "new_vmmu_full_r446", "classification": "AGENT_DERIVED_NOT_INDEPENDENT_H1",
                "derivation": "SA=AB=AC=2. S=(0,0,2),B=(2,0,0),C=(0,2,0),M=(1,0,0). Plane(SBC):x+y+z=2, d=1/sqrt(3)=sqrt(3)/3.",
                "source_option": "C (dataset metadata), consistent with hand derivation", "actual": "REFUSED/MISSING_DIMENSION: existing unsupported deduction from right-isosceles hypotenuse; GEOMETRY_CAPABILITY_GAP, no primitive added"},
            vision_live="NOT_AUTHORIZED", real_student="NOT_MEASURED", independent_h1="NOT_MEASURED")

    choice_entries = {("new_vmmu_full_r310", "{3;4}"), ("new_vmmu_full_r450", "22a²")}
    evaluation_facts = [f for c in new_cases if c["partition"] == "frozen_external_evaluation"
                        for f in c.get("critical_fact_recovery_proxy", [])
                        if (c["case_id"], f["reference"]) not in choice_entries]
    cf = {"found": sum(f["found_exactly"] for f in evaluation_facts), "total": len(evaluation_facts)}
    derived("critical_fact_adjudication.json", status="AGENT_ROLE_REVIEW_NOT_HUMAN_VERIFICATION",
            excluded_choice_entries=[list(pair) for pair in sorted(choice_entries)],
            evaluation_premise_and_goal_substring_proxy=cf,
            reason="Manifest critical_fact_texts contains two expected choice answers. Preserve the frozen manifest, exclude those strings from input-fact recall claims.")
    mt = evaluation["math_tokens_reconciled_draft"]
    cer = evaluation["recognition_against_unverified_reference"]["reconciled_draft"]["cer_median"]
    cold, warm, hit = (latency["summary"][k] for k in ("cold_model_cache_miss", "warm_model_cache_miss", "cache_hit"))
    peak = resources["summary_peak_by_mode"]["warm_model_cache_miss"]["combined_process_tree_peak_rss_mib"]
    f_cold, f_warm, f_hit = (final_latency["summary"][k] for k in ("cold_model_cache_miss", "warm_model_cache_miss", "cache_hit"))
    f_peak = final_resources["summary_peak_by_mode"]["warm_model_cache_miss"]
    f_proc = final_cold["summary"]
    f_busy, p_busy = (doc["host"]["whole_machine_cpu_busy_fraction_during_benchmark"] for doc in (final_latency, latency))
    ms = lambda node: f"{node['p50']:.0f}/{node['p95_nearest_rank']:.0f}ms"
    reg_lines = [(s["name"], s.get("verdict"), s.get("summary", s.get("summary_lines", ""))) for s in regression.get("suites", [])]
    backend_suite = next((s for s in regression.get("suites", []) if s["name"] == "backend_pytest"), {})
    rows = [
        (1,"Baseline OCR", "VERIFIED FACT", "Actual rerun16 images/17 variants:1/11 local auto in supported printed instances;10/10 further simulated corrections served correctly;6 other variants unserved. Keep the arms separate."),
        (2,"CER discrepancy", "VERIFIED FACT", "Five polyhedral cases median0.1135; all12 median0.1040. All source per-case scores reproduce receipts; report0.0110 is an unreproducible reporting error, not a new normalization result."),
        (3,"Full regression", "VERIFIED FACT" if regression.get("product_test_status")=="PASS" else "BLOCKED", f"Product tests={regression.get('product_test_status','PENDING')}; backend {backend_suite.get('summary','PENDING')}. Overall gates={regression.get('verdict')}; whole-HEAD publication remains blocked by97 unchanged baseline pending entries. Exact commands/exclusions below."),
        (4,"New images found", "VERIFIED FACT", "31 fresh downloads;5 relevant selected. Three older acquired-but-unevaluated geometry images added with exposure disclosed.26 irrelevant algebra images excluded; source stopped at429."),
        (5,"Eligible new corpus", "VERIFIED FACT", "8 relevant technical images:2 development/6 frozen external evaluation. This falls short of20–30; only1 evaluation item is a named-polyhedron distance problem in solver scope."),
        (6,"Verified ground truth", "NOT_MEASURED", "0 HUMAN_VERIFIED;8 AGENT_TRANSCRIBED_UNVERIFIED references. No independent scorer or sealed H-1."),
        (7,"Printed/handwritten accuracy", "VERIFIED FACT", f"Printed evaluation draft median CER={cer:.4f}; handwriting NOT_MEASURED (no new handwritten sample). Prose+choices references exclude diagram labels/footer: insertions reflect both segmentation and recognition."),
        (8,"Critical math tokens", "VERIFIED FACT", f"Evaluation token micro precision={mt['micro_precision']:.4f}, recall={mt['micro_recall']:.4f}; exact-substring fact proxy={cf['found']}/{cf['total']}. These are not semantic fact precision/recall; answer-choice strings in the manifest must be excluded from premise claims."),
        (9,"Fully exact images", "VERIFIED FACT", f"{mt['images_with_exact_full_statement']}/6 exact full statements;{mt['images_with_exact_token_sequence']}/6 exact math-token sequences, against agent references."),
        (10,"New local automatic solves", "VERIFIED FACT", "0/8;0/6 evaluation. All eight API preparations require confirmation; no oracle text enters the automatic arm."),
        (11,"Need corrections", "VERIFIED FACT", "8/8 require review/confirmation, which does not mean all can be solved after correction. Simulated span corrections did not serve a new result."),
        (12,"Need Vision", "NOT_MEASURED", "No calibrated count of images uniquely requiring Vision. Handwriting/diagram coverage remains a hypothesis for Vision, not measured success."),
        (13,"False acceptance", "VERIFIED FACT", "0 observed automatic acceptances on8 images; no automatic accepted item to grade. Do not claim a population false-acceptance probability or zero silent corruption."),
        (14,"False refusal", "NOT_MEASURED", "No independently adjudicated eligible-support oracle set. Known r446 has correct answer√3/3 but existing kernel deduction gap; token-exact r310 still has diagram and prose ambiguity."),
        (15,"Live Gemini Vision", "BLOCKED", "NOT_AUTHORIZED / LIVE_VISION_NOT_MEASURED;0 actual calls. No real recorded Vision replay exists for this corpus."),
        (16,"Live cost/latency", "NOT_MEASURED", "Unknown, not0. Authorization preflight exists; actual live executor/cost accounting remains deliberately unconnected pending authorization."),
        (17,"Adaptive benefit", "INFERENCE", "Mock transcript cross-check improves six authored conflict/control fixtures; it establishes routing safety only. Recognition/latency/cost superiority over local-only remains unmeasured."),
        (18,"Replace OCR model", "INFERENCE", "No evidence justifies a model replacement yet; no new model or training. New corpus too small and mostly outside solver scope."),
        (19,"Handwriting improvement", "NOT_MEASURED", "No new handwritten evaluation or recognition algorithm improvement claimed; prior handwriting case remains unserved."),
        (20,"Real student usability", "NOT_MEASURED", "No real participant; automated browser scripts are not students."),
        (21,"Correction actions", "VERIFIED FACT", "Per-case scripted edits/confirmation actions in user_correction_e2e.json; no human time-to-correct/keystroke benefit claim."),
        (22,"Stale cache", "VERIFIED FACT", "Browser text-edit scenario changes answers and Scene3D without re-preparing image; further span/free edits clear old confirmation. Other cache states are covered only as explicitly tested."),
        (23,"Correct image-to-result", "VERIFIED FACT", "Prior development11 outcomes:1 LOCAL_AUTO,10 USER_CORRECTED_SIMULATED. New corpus0 served. Never combine local, simulated, live or real-user categories into one accuracy."),
        (24,"Scene3D", "VERIFIED FACT", "Actual browser6/6 existing scenarios and4/4 confirmation checks; supported prior scenes render and continuity checked. No new corpus scene served; no blanket geometric fidelity claim."),
        (25,"Combined RSS", "VERIFIED FACT", f"Measured precursor4ab43853 warm miss combined sampled-peak p50={peak['p50']:.1f}MiB,p95={peak['p95_nearest_rank']:.1f}MiB,n=10. Includes Windows venv launcher, actual interpreter and descendants, not just4MiB launcher. Shared working sets may double count pages. Sealed candidate {final_head} re-measured: combined p50={f_peak['combined_process_tree_peak_rss_mib']['p50']:.1f}MiB,p95={f_peak['combined_process_tree_peak_rss_mib']['p95_nearest_rank']:.1f}MiB; OCR process tree alone p50={f_peak['ocr_process_tree_peak_rss_mib']['p50']:.1f}MiB,p95={f_peak['ocr_process_tree_peak_rss_mib']['p95_nearest_rank']:.1f}MiB (n=10)."),
        (26,"Cold/warm latency", "VERIFIED FACT", f"Precursor HTTP prepare-only p50/p95: cold-model{cold['p50']:.0f}/{cold['p95_nearest_rank']:.0f}ms(n10);warm miss{warm['p50']:.0f}/{warm['p95_nearest_rank']:.0f}ms(n10);cache{hit['p50']:.0f}/{hit['p95_nearest_rank']:.0f}ms(n10). Sealed candidate {final_head} re-measured (n10 each): cold-model{ms(f_cold)};warm miss{ms(f_warm)};cache{ms(f_hit)}. Fresh FastAPI process (n5): start-to-health{ms(f_proc['process_start_to_health_ready_ms'])}, first image{ms(f_proc['first_request_cold_process_cold_model'])}, next image{ms(f_proc['second_request_other_image_warm_model'])}, repeat{ms(f_proc['third_request_repeat_first_image_cache_hit'])}. The two runs differ in host load (whole-machine CPU busy{p_busy:.0%} vs{f_busy:.0%}, OCR itself included), so the difference is NOT a measured regression or improvement. Do not add stages or call prepare latency upload-to-Scene3D."),
        (27,"Physical low-end", "NOT_MEASURED", f"12 logical CPU/16GB shared host; PHYSICAL_LOW_END_NOT_MEASURED. Host CPU busy{p_busy:.0%} (precursor) and{f_busy:.0%} (sealed candidate) during the benchmarks, the OCR engines' own threads included; available RAM{final_latency['host']['available_physical_mib_at_start']:.0f}MiB at start. Not an isolated hardware claim."),
        (28,"Independent H-1", "NOT_MEASURED", "H1_NOT_MEASURED. Frozen external split is developer-collected and agent-transcribed; old12 VMMU images are exposed development/regression material."),
        (29,"Architecture choice", "INFERENCE", "Provisional local-first+targeted confirmation; DECISION_PENDING_LIVE_EVIDENCE. No empirical basis to rank Vision-first or adaptive live quality/cost."),
        (30,"Rust/training", "INFERENCE", "No new evidence requiring Rust, GPU or training. Engine inference dominates CPU; retain existing stack pending representative licensed data and approved comparison."),
        (31,"Pilot readiness", "BLOCKED", f"Not ready for unrestricted student pilot: new corpus has0 solves, no human usability/live comparison/H1, and concurrency is checked only for two simultaneous uploads on SQLite ({final_conc['http_200']}/{final_conc['requests']} on the sealed candidate). Supervised technical evaluation with declared limits is feasible."),
        (32,"Remaining limits", "VERIFIED FACT", "Small nonrepresentative corpus, unverified transcriptions, recognition/segmentation errors, unresolved geometry capability gaps, no live Vision/human/H1/physical-low-end evidence, and limited concurrent-load follow-up."),
    ]
    text = "# AXO — Real-image OCR/Vision comparative acceptance\n\n"
    text += f"Status: **OFFLINE_EVALUATION_WITH_LIMITS; REGRESSION={regression.get('verdict')}; LIVE/HUMAN/H1 NOT_MEASURED; ARCHITECTURE DECISION_PENDING_LIVE_EVIDENCE**. No merge, push or deploy.\n\n"
    text += "Product checkpoints:2969e9e76 and7b1700214; baseline6bb22fa3b. Planner/26, Registry/33, Engine/24, height-invariance-certificate/2, output-policy/1 and cache132 unchanged. Candidate measured hash recorded in run.json; full working-source fingerprint in regression receipts additionally covers UI files outside the115-file freeze surface.\n\n"
    text += "Actual offline API measurements use HYBRID_ROUTE_MODE=local-first, HYBRID_LOCAL_FIRST=1, ALLOW_LIVE_AI=0 and an empty provider key. The official live Hybrid default and deployment configuration are unchanged. A503 LIVE_AI_DISABLED is an infrastructure refusal, not evidence of mathematical out-of-scope classification.\n\n"
    text += "This run corrects [the original report](../image-first-ocr-verified-geometry/ALGOSIM_IMAGE_FIRST_OCR_VERIFIED_GEOMETRY_REPORT.md), preserving historical bytes. See [metric reconciliation](prior_metric_reconciliation.json), [baseline audit](baseline_integrity.json) and [review](review.md).\n\n"
    text += "## Owner questions\n\n|#|Question|Classification|Finding|\n|---:|---|---|---|\n"
    text += "\n".join(f"|{number}|{question}|{classification}|{answer}|" for number,question,classification,answer in rows) + "\n\n"
    text += "## Regression and acceptance boundaries\n\n"
    text += "\n".join(f"- `{name}`: **{verdict}**; {details}".rstrip() for name, verdict, details in reg_lines) + "\n\n"
    text += "Postgres and external-evidence markers remain explicitly opt-in/excluded by canonical pytest.ini. Earlier interrupted runs and the pre-existing UI glyph failure are retained in regression history; none supply final PASS counts. Canonical full-gate.mjs alone owns FULL_PRODUCT_GATE_PASS; this report does not invent that label.\n\n"
    text += "Publication range passes with no new finding. Whole-HEAD publication reports97 pending exceptions; every reported path/blob matches the baseline. No exception or human approval was changed. See publication_safety_baseline_comparison.json. Product test success must not be read as permission to publish the repository.\n\n"
    text += "## Resource and failure correction\n\nOriginal precursor measured5/20 concurrent HTTP500. The claim that their precise cause was SQLite lacked exception evidence. A controlled real-SQLite regression demonstrates an event-loop/session-lock mechanism and now passes after offloading the guard; fresh actual HTTP follow-ups before and after each returned10/10. This does **not** prove elimination of the original stochastic failure or production-load reliability. [Correction receipt](resource_measurement_correction.json).\n\n"
    text += f"Sealed candidate {final_head}: the same benchmark workload returned {final_conc['http_200']}/{final_conc['requests']} HTTP200 with {len(final_conc['server_exception_events'])} captured server exceptions ([profile](ocr_worker_resource_profile_final.json)). The precursor run had no exception capture, so this is an observation on the candidate, not a controlled before/after experiment.\n\n"
    text += f"Precursor resource/latency files identify4ab43853 explicitly; final patches affect confirmation, comparison and session waiting rather than OCR inference. They are not relabelled as a final-candidate performance run; the sealed candidate has its own `*_final.json` latency, resource and cold-process receipts, and its API acceptance re-run {'reproduces' if api_final_matches else 'DIFFERS FROM'} the prepare and solve statuses of all eight new-corpus images. Original long-form stage timings and cold-process measurements remain separate. A historical idle-RSS delta0MiB is not active OCR memory.\n\n"
    text += "The shared OCR result cache has operation-dependent bounds: normal OCR inserts trim to16 entries, while reread inserts trim to64. The previous statement of a fixed32-entry cache does not match current code. Cache occupancy and descendant RSS are recorded separately.\n\n"
    text += "## Corpus, provenance and contamination\n\n[Manifest](new_image_corpus_manifest.json), [references](ground_truth_provenance.json), [split audit](dataset_split_and_contamination_audit.json). Source: [VMMU dataset](https://huggingface.co/datasets/anvo25/vmmu) declares MIT; upstream exam redistribution rights are not independently established, so image binaries and browser screenshots containing crops remain ignored locally. Reference text is agent transcribed, not OCR output; exact image hashes and retrieval records are in the manifest. No evaluation image drove a recognition heuristic or geometry expansion. Existing12 VMMU cases cannot be independent H1 after parser tuning in the old run.\n\n"
    text += "## Post-flight\n\nReused modules: existing OCR worker/client, lexer, reconciler, fidelity gate, region detector, parser, Hybrid adapter, continuity checker, browser harness and canonical audits. Created product modules:none. Added focused regression tests and run-scoped measurement tools only. Duplicate check: CODE_INDEX and callers inspected; no parallel solver/OCR implementation. No changed expected answers or deleted tests.\n"
    (RUN / REPORT).write_text(text, encoding="utf-8")
    print("Derived receipts and report written; regression status", regression.get("verdict"))


if __name__ == "__main__":
    main()
