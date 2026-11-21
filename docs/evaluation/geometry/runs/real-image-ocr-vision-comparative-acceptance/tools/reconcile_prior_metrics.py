"""Recompute prior OCR evidence without importing runtime code or calling providers."""
from __future__ import annotations

import ast
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import statistics
import subprocess

os.environ["ALLOW_LIVE_AI"] = "0"
RUN = Path(__file__).resolve().parent.parent
ROOT = RUN.parents[4]
PRIOR = RUN.parent / "image-first-ocr-verified-geometry"
BASELINE = "6bb22fa3bb183ad28cdf1395c99e5eb375fac97c"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load(name: str) -> dict:
    return json.loads((PRIOR / name).read_text(encoding="utf-8"))


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def distance(hyp: str, ref: str) -> int:
    """Full matrix independently cross-checks the historical rolling-row code."""
    rows = [list(range(len(ref) + 1))]
    for i, ch in enumerate(hyp, 1):
        row = [i]
        for j, other in enumerate(ref, 1):
            row.append(min(rows[i - 1][j] + 1, row[j - 1] + 1,
                           rows[i - 1][j - 1] + (ch != other)))
        rows.append(row)
    return rows[-1][-1]


def extract_function(name: str):
    tree = ast.parse((PRIOR / "tools/evaluate_image_first_ocr.py").read_text(encoding="utf-8"))
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    namespace = {"re": re}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(PRIOR / "tools/evaluate_image_first_ocr.py"), "exec"), namespace)
    return namespace[name]


def catalog(path: Path, name: str) -> list[dict]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == name:
            return ast.literal_eval(node.value)
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"Catalog assignment missing: {name}")


def main() -> None:
    original_cer = extract_function("_cer")
    examples = [("", "", 0), ("", "abc", 3), ("abc", "", 3),
                ("kitten", "sitting", 3), ("ab", "ba", 2),
                ("a", "a", 0), ("A'D", "AD", 1), ("a", "á", 1)]
    for hyp, ref, expected in examples:
        assert distance(hyp, ref) == expected
        assert original_cer(hyp, ref) == (round(expected / len(ref), 4) if ref else 0.0)
    assert normalize("  a\n\t b  ") == "a b"
    assert original_cer("  a\n\t b  ", "a b") == 0.0
    assert original_cer("′", "'") == 1.0
    assert original_cer("é", "e\u0301") == 1.0

    new_items = catalog(PRIOR / "tools/new_external_catalog.py", "NEW_EXTERNAL_ITEMS")
    prior_items_path = RUN.parent / "real-world-printed-handwriting-acquisition/tools/corpus_catalog.py"
    old_items = catalog(prior_items_path, "CORPUS_ITEMS")
    new_receipt = load("new_external_image_evaluation.json")
    items_by_id = {i["image_id"]: i for i in new_items}
    old_hashes = {i.get("original_file_sha256") for i in old_items if i.get("original_file_sha256")}
    report_values = [0.0049, 0.0258, 0.0110, 0.0056, 0.0148]
    case_metrics = []
    for index, case in enumerate(new_receipt["cases"]):
        item = items_by_id[case["image_id"]]
        ref = item["ground_truth_text"]
        predictions = {name: "\n".join(line["text"] for line in engine["lines"])
                       for name, engine in case["ocr"]["engines"].items()}
        predictions["reconciled_draft"] = case["after_reconcile"]["draft_text"]
        reader_metrics = {}
        for reader, hyp in predictions.items():
            h, r = normalize(hyp), normalize(ref)
            edits = distance(h, r)
            value = round(edits / len(r), 4) if r else 0.0
            assert value == original_cer(hyp, ref)
            reader_metrics[reader] = {
                "normalized_hypothesis_sha256": sha(h.encode()),
                "normalized_hypothesis_characters": len(h),
                "edit_distance": edits, "cer_exact_ratio": f"{edits}/{len(r)}",
                "cer_unrounded": edits / len(r) if r else 0.0,
                "cer_rounded_4dp": value,
                "receipt_cer": case["scoring"]["cer"][reader],
                "matches_receipt": value == case["scoring"]["cer"][reader],
            }
        case_metrics.append({
            "image_id": case["image_id"], "source_case_json_pointer": f"/cases/{index}",
            "ground_truth_source": f"tools/new_external_catalog.py:NEW_EXTERNAL_ITEMS[{index}].ground_truth_text",
            "ground_truth_status": item["ground_truth_verification_status"],
            "normalized_reference_sha256": sha(normalize(ref).encode()),
            "normalized_reference_characters": len(normalize(ref)),
            "image_sha256_receipt": case["sha256_original"],
            "image_sha256_matches_catalog": case["sha256_original"] == item["original_file_sha256"],
            "identical_image_hash_in_external16_catalog": case["sha256_original"] in old_hashes,
            "original_image_byte_revalidation": "NOT_MEASURED (this audit reads committed evidence only)",
            "partition_claimed": case["data_partition"],
            "partition_for_followup": "PRIOR_EXPOSED_DEVELOPMENT_REGRESSION",
            "included_in_polyhedral_5": index < 5,
            "readers": reader_metrics,
            "report_table_cer": report_values[index] if index < 5 else None,
        })

    old_by_id = {i["image_id"]: i for i in old_items}
    old_cases = load("external16_image_diagnostics.json")["cases"]
    old_reader_values = {reader: [] for reader in ("tesseract", "rapidocr", "reconciled_draft")}
    for case in old_cases:
        ref = old_by_id[case["image_id"]]["ground_truth_text"]
        for reader in old_reader_values:
            hyp = case["after_reconcile"]["draft_text"] if reader == "reconciled_draft" else "\n".join(
                line["text"] for line in case["ocr"]["engines"][reader]["lines"])
            assert original_cer(hyp, ref) == case["scoring"]["cer"][reader]
            if case["printed_or_handwritten"] == "PRINTED":
                old_reader_values[reader].append(original_cer(hyp, ref))

    manifest = load("run.json")
    artifacts = []
    for path in sorted(PRIOR.rglob("*")):
        if not path.is_file() or "__pycache__" in path.parts:
            continue
        relative = path.relative_to(ROOT).as_posix()
        content = path.read_bytes()
        blob = subprocess.check_output(["git", "show", f"{BASELINE}:{relative}"], cwd=ROOT)
        declaration = manifest["deliverables"].get(path.name, {}).get("sha256")
        artifacts.append({
            "path": relative, "bytes_working_tree": len(content),
            "sha256_working_tree_bytes": sha(content), "sha256_lf_normalized": sha(content.replace(b"\r\n", b"\n")),
            "sha256_baseline_git_blob": sha(blob), "manifest_declared_sha256": declaration,
            "manifest_matches_baseline_git_blob": sha(blob) == declaration if declaration else None,
            "manifest_matches_lf_normalized": sha(content.replace(b"\r\n", b"\n")) == declaration if declaration else None,
            "working_tree_text_matches_baseline": content.replace(b"\r\n", b"\n") == blob.replace(b"\r\n", b"\n"),
        })

    reconciled = [c["readers"]["reconciled_draft"]["cer_rounded_4dp"] for c in case_metrics]
    poly = reconciled[:5]
    outcomes = load("real_image_to_scene3d_acceptance.json")
    vision = load("vision_fallback_offline_receipt.json")
    report_path = PRIOR / "ALGOSIM_IMAGE_FIRST_OCR_VERIFIED_GEOMETRY_REPORT.md"
    result = {
        "schema": "algosim-prior-metric-reconciliation/1",
        "run_id": RUN.name, "prior_run_id": PRIOR.name, "baseline_commit": BASELINE,
        "classification": "OFFLINE_PRIOR_EVIDENCE_RECOMPUTATION_CORRECTION_LAYER",
        "allow_live_ai": 0, "provider_calls": 0, "independent_h1_validation": "NOT_MEASURED",
        "formula": {
            "source": "tools/evaluate_image_first_ocr.py::_cer",
            "normalization": "re.sub(r'\\s+', ' ', text).strip() independently on prediction and reference",
            "distance": "Unicode codepoint Levenshtein; insertion/deletion/substitution cost 1; no transposition",
            "denominator": "len(normalized ground_truth_text), including answer choices",
            "case_rounding": "Python round(distance / denominator, 4)",
            "summary": "round(statistics.median(per-case rounded CER), 4)",
            "empty_reference_historical_behavior": "returns 0.0 even for nonempty hypothesis; no empty references in these 12 cases",
            "no_other_normalization": ["no case folding", "no accent removal", "no Unicode normalization", "no prime folding", "no answer-choice stripping"],
            "original_function_extracted_with_ast_without_importing_evaluator": True,
            "independent_distance_self_checks_passed": len(examples),
            "additional_normalization_self_checks_passed": 4,
        },
        "filter": {
            "all_12": "all cases from prior new_external_image_evaluation.json, joined by image_id to NEW_EXTERNAL_ITEMS",
            "polyhedral_5": "the first five cases as used by prior generate_all_receipts.py (new_ext_01 through new_ext_05)",
            "polyhedral_image_ids": [c["image_id"] for c in case_metrics[:5]],
        },
        "recomputed_summary": {
            "total_cases": len(case_metrics), "polyhedral_cases": len(poly),
            "reconciled_cer_median_all_12": round(statistics.median(reconciled), 4),
            "reconciled_cer_median_polyhedral_5": round(statistics.median(poly), 4),
            "receipt_summary": new_receipt["corpus_summary"],
            "all_36_reader_case_cer_values_match_receipt": all(m["matches_receipt"] for c in case_metrics for m in c["readers"].values()),
            "report_claimed_polyhedral_median": 0.0110,
            "report_claim_reproduced": False,
            "resolution": "Use 0.1135 for the original evaluator's full-text 5-case median. Report values have no reconstructible derivation in committed evidence; do not reinterpret as a stem-only score.",
        },
        "cases": case_metrics,
        "receipt_audit": {
            "json_receipts_parsed": [p.name for p in sorted(PRIOR.glob("*.json")) if json.loads(p.read_text(encoding="utf-8")) is not None],
            "external16_printed_recomputation": {
                "all_48_reader_case_values_match_receipt": True,
                "printed_case_count": len(old_reader_values["reconciled_draft"]),
                "cer_by_reader": {reader: {"mean": round(statistics.mean(values), 4), "median": round(statistics.median(values), 4)} for reader, values in old_reader_values.items()},
            },
            "real_vs_simulated": {
                "real_local_ocr": "Prior raw reader outputs and image-to-prepare receipts exist; this audit recomputes scores, does not rerun OCR.",
                "external16_metrics": outcomes["strictly_separated_metrics"],
                "new_external_outcome_counts": dict(Counter(c["outcome_category"] for c in new_receipt["outcomes_summary"])),
                "new_external_served_categories": [c["outcome_category"] for c in new_receipt["outcomes_summary"] if c["status"] == "SERVED"],
                "user_correction_source": "Evaluator simulates targeted edits and confirmations using catalog ground truth; no observed student study.",
                "vision_live": "NOT_MEASURED; 0 live calls",
                "vision_replay": "NOT_MEASURED; no recorded external-image provider responses",
                "vision_simulated_route": vision["deterministic_cross_check_verification"]["simulated_vision_ready_to_local_parser_route"],
                "vision_simulated_call_count_meaning": "gemini_vision_calls=1 was supplied as metrics.vlm_calls in a synthetic ready fixture, not a provider receipt",
                "vision_conflict_probe": vision["deterministic_cross_check_verification"]["ocr_vs_vision_conflict_detected"],
                "vision_conflict_probe_discrepancy": "Named conflict-detected probe compares side 2a versus a but records has_conflict=false; cannot support conflict-detection success.",
                "browser_e2e": "6 automated Chromium scenarios with real uploads/backend; scripted corrections are not observed student confirmations.",
            },
            "partition": {
                "claimed": "independent_holdout for 12 new images",
                "same_agent_ground_truth": "First eight GROUND_TRUTH_UNVERIFIED; last four AUTHOR_PROVIDED_VMMU_DESCRIPTION",
                "case_ids_and_image_hashes_new_vs_external16": "Checked exact image hashes; see per-case overlap flags. Different hashes do not establish conceptual independence.",
                "exposure": "Report Q23 documents parser changes for new_ext_02 and OCR wording encountered in this evaluation; Q29 explicitly denies independent H1 status.",
                "followup_classification": "All prior images and transcripts are exposed development/regression material; no sealed independent holdout remains in these receipts.",
                "runtime_ground_truth_injection": "No direct catalog/ground_truth_text imports found in product code by scoped search; lexicon builder reads parser/registry strings plus curated general syllables. This does not establish blind evaluation.",
            },
            "hash_integrity": {
                "declared_deliverables": len(manifest["deliverables"]),
                "all_declared_hashes_match_git_blob": all(a["manifest_matches_baseline_git_blob"] for a in artifacts if a["manifest_declared_sha256"]),
                "working_tree_line_ending_caveat": "Manifest hashes are LF serialization hashes and match committed git blobs. CRLF checkout bytes differ; record both without modifying historical files.",
                "unmanifested_artifacts": [a["path"] for a in artifacts if a["manifest_declared_sha256"] is None],
            },
            "regression_scope": {
                "receipt_claims": load("full_regression_summary.json")["regression_gates"],
                "report_additional_claims": {"backend": "169/169", "frontend": "108/108", "demo": "5/5 + 1/1"},
                "discrepancies": ["Receipt only lists 18+2 backend tests and 18 frontend tests, not report's 169 and 108.", "Receipt parser test path backend/tests/test_local_geometry_parser.py is absent; actual path backend/tests/geometry/test_local_geometry_parser.py.", "Receipt demo count 7/7 differs from report's 5/5 + 1/1.", "No command logs/full-suite machine receipt in this prior run establish a clean detached Full T3 execution."],
                "status": "TARGETED_REGRESSION_CLAIMED; FULL_SUITE_NOT_ESTABLISHED_BY_PRIOR_RECEIPTS",
                "new_tests_executed_by_this_audit": "Only deterministic formula/distance self-checks; no product regression rerun",
            },
            "span_grounding_discrepancy": {
                "receipt": load("dual_ocr_reconciliation_receipt.json")["reconciliation_architecture"]["silent_corruption_rate_across_external16"],
                "diagnostic_flagged_spans": [{"image_id": c["image_id"], "values": c["scoring"]["verified_math_spans_not_in_ground_truth"]} for c in old_cases if c["scoring"]["verified_math_spans_not_in_ground_truth"]],
                "flagged_span_quotient": "2/141 = 0.014184397163120567",
                "interpretation": "The generator hardcodes rate 0.0 despite two diagnostic flags; fidelity receipt instead claims 0/152. Flags require human adjudication (e.g. diagram text may be omitted from reference), so neither zero corruption nor a measured true corruption rate follows from these fields.",
            },
            "other_report_discrepancies": ["Report's new_ext_02 table says one edit; receipt records two (AD to A'D and solid separator).", "Report maps curved refusals to CURVED_WORDING_UNSUPPORTED; actual outcomes new_ext_06..08 reason_code is LIVE_AI_DISABLED, an infrastructure reason. This supports non-service, not verified mathematical scope classification.", "Report labels zero targeted edits as zero OCR errors on cases 03..05; full-text CER remains nonzero and no-edit count alone does not establish semantic text perfection.", "Resource report region-detection p50=102.72 ms differs from resource receipt p50=73.62 ms; use receipt value with its scope rather than merge these figures."],
        },
        "source_artifacts": artifacts,
        "additional_source": {"path": prior_items_path.relative_to(ROOT).as_posix(), "sha256_working_tree_bytes": sha(prior_items_path.read_bytes())},
        "generator": {"path": Path(__file__).relative_to(ROOT).as_posix(), "sha256_bytes": sha(Path(__file__).read_bytes())},
        "historical_report": {"path": report_path.relative_to(ROOT).as_posix(), "unchanged": True},
    }
    assert len(case_metrics) == 12 and len(poly) == 5
    assert result["recomputed_summary"]["all_36_reader_case_cer_values_match_receipt"]
    assert result["recomputed_summary"]["reconciled_cer_median_polyhedral_5"] == 0.1135
    assert result["receipt_audit"]["hash_integrity"]["all_declared_hashes_match_git_blob"]
    output = RUN / "prior_metric_reconciliation.json"
    output.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"12 cases / 36 CER values reconciled; polyhedral median=0.1135; output={output}")


if __name__ == "__main__":
    main()
