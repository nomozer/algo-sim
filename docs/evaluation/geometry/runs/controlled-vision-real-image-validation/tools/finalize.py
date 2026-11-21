"""Derive the deliverable receipts from the measured ones and hash the run. Never re-measures, never edits a
measured receipt.  Run from backend/ after every measurement:  python <tools>/finalize.py
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]


def load(name: str):
    path = RUN / name
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def write(name: str, data: dict) -> None:
    (RUN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT).decode().strip()


def derived(**fields) -> dict:
    return {"run_id": RUN.name, "classification": "DERIVED_FROM_REFERENCED_MEASUREMENTS_NOT_A_NEW_MEASUREMENT",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(), **fields}


def candidate_commit() -> str:
    return json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))["product_commit_sha"]


def main() -> int:
    manifest = load("new_in_scope_image_manifest.json")
    after, before = load("image_evaluation_summary.json"), load("image_evaluation_summary_baseline.json")
    diag = {c["case_id"]: c for c in load("transcription_solver_diagnostic.json")["cases"]}
    ocr = {c["case_id"]: c for p in ("development", "frozen_external_evaluation") for c in load(f"local_ocr_{p}.json")["cases"]}
    api = {c["case_id"]: c for p in ("development", "frozen_external_evaluation") for c in load(f"api_acceptance_{p}.json")["cases"]}
    ocr_before = {c["case_id"]: c for p in ("development", "frozen_external_evaluation") for c in load(f"local_ocr_{p}_baseline.json")["cases"]}
    browser = load("browser_in_scope_audit.json") or {}
    browser_rows = {}
    for row in browser.get("rows", []):
        browser_rows.setdefault(row["case_id"], []).append(row)
    pick = lambda summary, part: {k: summary["partitions"][part][k] for k in ("recognition", "critical_facts", "routing")}

    write("local_ocr_baseline.json", derived(
        sources=["local_ocr_*_baseline.json (before c53be83db)", "local_ocr_*.json (after)", "image_evaluation_summary*.json"],
        engines="tesseract vie tessdata_fast + RapidOCR PP-OCR (sidecar) + product reconciliation and reread",
        before_fix={p: pick(before, p) for p in before["partitions"]}, after_fix={p: pick(after, p) for p in after["partitions"]},
        fix="c53be83db: trim neighbour glyphs bleeding into reread crops (found on development image vmmu_r476)",
        evaluation_split_used_for_tuning=False,
        per_case_changes=[{"case_id": cid, "facts_before": sum(f["recovered"] for f in ocr_before[cid]["critical_facts"]),
                           "facts_after": sum(f["recovered"] for f in ocr[cid]["critical_facts"]),
                           "text_changed": ocr_before[cid]["ocr_text"] != ocr[cid]["ocr_text"]}
                          for cid in ocr if ocr_before[cid]["ocr_text"] != ocr[cid]["ocr_text"]],
        exact_statement_note="0 images exact: insertion of diagram labels, footers and spacing differences dominate CER; see critical facts for mathematical fidelity"))

    facts_eval = after["partitions"]["frozen_external_evaluation"]["critical_facts"]
    write("critical_mathematical_fact_evaluation.json", derived(
        rule="a fact is recovered when one accepted form occurs in the OCR text after whitespace removal and prime/degree unification; references are AGENT_TRANSCRIBED_UNVERIFIED",
        evaluation=facts_eval, development=after["partitions"]["development"]["critical_facts"],
        single_engine_vs_reconciled_evaluation={"tesseract": facts_eval["single_engine_recovered"]["tesseract"],
                                                "rapidocr": facts_eval["single_engine_recovered"]["rapidocr"], "reconciled": facts_eval["recovered"], "total": facts_eval["total"]},
        silent_corruption_check={"verified_spans_changing_a_fact": "see local_ocr_baseline.json per_case_changes: the only observed case (duplicated '=' in vmmu_r476, development) was fixed",
                                 "false_acceptance_images": [p for p in after["partitions"] if after["partitions"][p]["routing"]["false_acceptance_verified_but_fact_missing"]]},
        examples_of_dangerous_substitution_checked=["√3→√8 (radical)", "A′→A (prime)", "⊥→∥ (relation)", "60°→600° (degree)"],
        source_glyph_corruption_cases=load("ground_truth_verification_status.json")["source_glyph_corruption_cases"],
        precision="NOT_MEASURED: predicted facts are not extracted from OCR text independently; only recall of reference facts is measured"))

    rows = []
    for item in manifest["items"]:
        cid, a = item["case_id"], api[item["case_id"]]
        kernel = a.get("kernel") or {}
        verdict = a["grade"]["verdict"]
        category = ("C2_USER_CORRECTED_SIMULATED" if verdict == "SERVED_MATCHES_DATASET_KEY" else
                    "E_GEOMETRY_CAPABILITY_GAP" if diag[cid]["solver_scope"] == "IN_SCOPE_GEOMETRY_CAPABILITY_GAP" else
                    "D_SAFE_REFUSAL" if kernel.get("status") in ("REFUSED", "unsupported") else
                    "F_NOT_GRADED" if verdict == "SERVED_NOT_COMPARABLE_NEEDS_ADJUDICATION" else "NOT_SERVED_NO_AI_PARSE")
        rows.append({"case_id": cid, "sha256": item["sha256"], "partition": item["partition"], "ground_truth_status": item["ground_truth_status"],
                     "solver_scope_on_verified_text": diag[cid]["solver_scope"], "ocr_text": ocr[cid]["ocr_text"],
                     "critical_facts_recovered": f"{sum(f['recovered'] for f in ocr[cid]['critical_facts'])}/{len(ocr[cid]['critical_facts'])}",
                     "vision_output": None, "input_route": a["input_route"], "prepare_status": a["prepare_status"], "provider_calls": a["provider_calls"] or 0,
                     "user_corrections": {"kind": "SCRIPTED_FROM_AGENT_REFERENCE", "edits": a.get("scripted_edits"), "actions": a.get("scripted_actions")},
                     "kernel": {k: kernel.get(k) for k in ("http_status", "status", "reason_code", "answers")},
                     "oracle": item["oracle"], "expected_answer": item["expected_answer"], "verdict": verdict, "category": category,
                     "scene3d": a["scene3d"], "api_image_to_result_ms": a["image_to_result_ms"], "browser": browser_rows.get(cid)})
    counts = Counter(r["category"] for r in rows)
    write("real_image_to_scene3d_results.json", derived(
        route="POST /api/input/prepare -> local OCR -> scripted span confirmation -> POST /api/analyze (HYBRID_ROUTE_MODE=local-first, ALLOW_LIVE_AI=0)",
        categories={"A_LOCAL_AUTO": counts.get("A_LOCAL_AUTO", 0), "B_VISION_LIVE": "NOT_MEASURED", "B2_VISION_RECORDED": "NOT_MEASURED_NO_RECORDING",
                    "C_USER_CORRECTED_REAL": "NOT_MEASURED", **{k: v for k, v in counts.items()}},
        wrong_served_with_oracle=[r["case_id"] for r in rows if r["verdict"] == "SERVED_DIFFERS_FROM_DATASET_KEY"],
        browser_receipt="browser_in_scope_audit.json", cases=rows))

    write("student_confirmation_browser_audit.json", derived(
        receipts=["browser_in_scope_audit.json", "browser_confirmation_audit.json", "browser_existing_scenarios.json"],
        in_scope_corpus=({"passed": browser.get("passed"), "total": browser.get("total")} if browser else "NOT_RUN"),
        confirmation_audit={k: (load("browser_confirmation_audit.json") or {}).get(k) for k in ("passed", "total")},
        existing_scenarios=(load("browser_existing_scenarios.json") or {}).get("summary"),
        covered=["upload", "multi-problem selection (existing scenarios)", "span review with crops", "keyboard confirmation", "edit invalidates confirmation",
                 "cancel prevents analyze", "desktop 1440x900, CSS zoom 1.1, mobile 390x844", "Scene3D canvas after build", "Unicode code-point offsets (unit tests)"],
        not_covered_in_browser=["worker timeout and provider-unavailable screens (backend/unit tests only)", "real student reading time"],
        is_human_usability_evidence=False))
    write("human_usability_status.json", {"run_id": RUN.name, "REAL_STUDENT_USABILITY": "NOT_MEASURED", "participants": 0,
                                          "reason": "No consented participants were available to this run; the agent did not role-play students.",
                                          "automated_substitute": "student_confirmation_browser_audit.json (software behaviour only)",
                                          "proposed_protocol": ["3-5 consented students, no personal data beyond anonymous ID", "task: upload one in-scope image, confirm or correct flagged spans, reach the 3D scene",
                                                                "measure completion, time to confirm, edits, misclicks, assistance requests, understanding of messages"]})

    latency, resources = load("cold_warm_latency_benchmark.json"), load("ocr_worker_resource_profile.json")
    cold_process, stages, concurrency = load("cold_process_benchmark.json"), load("ocr_stage_profile.json"), load("concurrent_upload_reliability.json")
    prior_dir = RUN.parent / "real-image-ocr-vision-comparative-acceptance"
    prior = json.loads((prior_dir / "cold_warm_latency_benchmark_final.json").read_text(encoding="utf-8"))
    busy = lambda doc: doc["host"]["whole_machine_cpu_busy_fraction_during_benchmark"]
    write("cold_warm_cache_latency.json", derived(
        sources=["cold_warm_latency_benchmark.json", "cold_process_benchmark.json", "browser_in_scope_audit.json"],
        product_commit=candidate_commit(), images=latency["images"], server_states=latency["server_states"],
        prepare_http_ms=latency["summary"], harness_sampler_ab=latency["harness_sampler_ab"],
        fresh_fastapi_process_ms=cold_process["summary"],
        upload_to_first_usable_scene_ms={"rows": [{k: r[k] for k in ("case_id", "viewport", "uploadToReviewMs", "uploadToFirstUsableSceneMs")} for r in browser.get("rows", [])],
                                         "caveat": "browser runs followed API runs of the same images, so most include an OCR cache hit; scripted confirmation has no reading time"},
        comparison_with_previous_candidate={"previous": {"head": prior["head"], "summary": prior["summary"], "host_cpu_busy": busy(prior)},
                                            "this": {"summary": latency["summary"], "host_cpu_busy": busy(latency)},
                                            "interpretation": "Same harness, images and server states. The product change is a string operation in reconciliation; differences track host load and are not attributed to code."},
        host=concurrency.get("host"), do_not_sum="Stage figures (ocr_bottleneck_profile.json) are separate measurements and are not added into these end-to-end numbers."))
    write("combined_process_memory.json", derived(
        sources=["ocr_worker_resource_profile.json", "cold_process_benchmark.json", "concurrent_upload_reliability.json"],
        peak_rss_mib_by_state=resources["summary_peak_by_mode"],
        fresh_process_whole_lifetime_combined_peak_mib=cold_process["summary_combined_process_tree_peak_rss_mib"],
        concurrency_combined_peak_mib={lv["simultaneous"]: lv["combined_peak_rss_mib"] for lv in concurrency["ladder"]["levels"]},
        worker_crash_recovery=resources["worker_crash_recovery"], after_explicit_shutdown=resources["after_explicit_worker_shutdown"],
        method=resources["combined_memory_note"], process_tree=resources["process_tree_note"],
        not_zero="OCR memory lives in the OCR interpreter process tree; FastAPI RSS alone does not show it."))
    pipeline = stages["pipeline_stage_profile"]["summary"]
    worker = stages["worker_interpreter_profile"]["summary"]
    ranked = sorted(((k, v["p50"]) for k, v in pipeline["warm_worker"].items() if v["p50"] is not None), key=lambda kv: -kv[1])
    write("ocr_bottleneck_profile.json", derived(
        source="ocr_stage_profile.json", measurement_class=stages["measurement_class"],
        warm_stage_p50_ms_ranked=ranked, cold_worker_stage_p50_ms={k: v["p50"] for k, v in pipeline["cold_worker"].items()},
        engine_p50_ms={k: worker[k]["p50"] for k in ("tesseract_warm_inference_ms", "rapidocr_warm_inference_ms", "rapidocr_import_ms",
                                                     "rapidocr_lazy_model_load_estimate_ms", "tesseract_init_ms", "interpreter_start_and_exit_ms")},
        finding="RapidOCR inference dominates warm OCR (~1.5 s of ~1.7 s); a cold worker adds ~1.0 s rapidocr import and ~0.8 s lazy model load. Reread adds 0.1-0.4 s; reconciliation, fidelity and parsing are each under 0.1 s.",
        cache_policy={"observed": concurrency.get("cache_capacity"),
                      "finding": "Normal OCR and reread results share one 16/64-trimmed OrderedDict, so rereads consume OCR slots: after 8 images the first image's OCR is still cached but its reread is not; after 20 images neither is."},
        optimisations_implemented=[],
        optimisations_considered={"pre-warm the OCR worker at startup": "would remove ~1.8-2.3 s from the first upload at the cost of ~400-600 MiB idle RSS: an Owner trade-off, not implemented",
                                  "separate reread cache budget": "small latency gain on repeats; not implemented without a before/after on a repeat-heavy workload",
                                  "drop an engine or the reread": "rejected: both feed cross-family verification of critical facts"}))

    artifacts = {}
    for path in sorted(RUN.rglob("*")):
        if path.is_file() and path.name != "run.json" and "__pycache__" not in path.parts:
            data = path.read_bytes().replace(b"\r\n", b"\n")
            artifacts[path.relative_to(RUN).as_posix()] = {"sha256_lf": hashlib.sha256(data).hexdigest(), "bytes_lf": len(data)}
    candidate = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    regression = load("full_regression_summary.json") or {}
    write("run.json", {"schema": "algosim-controlled-vision-run/1", "run_id": RUN.name, "updated_at_utc": datetime.now(timezone.utc).isoformat(),
                       "start_head": "44807b13bffe608153bc58e453a3bc9c37703485", "head_at_manifest_write": git("rev-parse", "HEAD"),
                       "product_commit": candidate["product_commit_sha"], "candidate_freeze_commit": candidate["commit"],
                       "measured_system": candidate["measured_system"]["tree_hash"], "measured_files": candidate["measured_system"]["so_file"],
                       "cache_version": candidate["cache_version"], "branch": git("branch", "--show-current"),
                       "regression_verdict": regression.get("verdict"), "live_vision": "NOT_GRANTED", "provider_calls": 0,
                       "real_student_usability": "NOT_MEASURED", "independent_h1": "NOT_MEASURED", "physical_low_end": "NOT_MEASURED",
                       "architecture_decision": "ARCHITECTURE_DECISION_PENDING_LIVE_EVIDENCE", "merge_push_deploy": "NOT_PERFORMED",
                       "report": "AXO_CONTROLLED_VISION_REAL_IMAGE_VALIDATION_REPORT.md", "images_in_git": False,
                       "hash_policy": "SHA-256 of bytes with CRLF normalised to LF; excludes run.json itself", "artifacts": artifacts})
    print("derived receipts written;", len(artifacts), "artifacts hashed; categories", dict(counts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
