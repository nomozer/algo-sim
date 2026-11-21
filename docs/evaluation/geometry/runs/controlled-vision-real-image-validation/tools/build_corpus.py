"""Freeze the image manifest, ground-truth status and contamination audit from corpus_cases.py and the local cache.

Writes no OCR result and reads none. The split rule depends only on the dataset id, so it is fixed before any
recognition measurement on these images.  Run from backend/.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import unicodedata
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from acquire_corpus import CACHE, ID_CORE, META, SCREEN, previously_used  # noqa: E402
from corpus_cases import AGENT_DERIVED_LETTER, CASES, OUT_OF_SCOPE_BY_DOMAIN  # noqa: E402

PRIMES = str.maketrans({"’": "'", "′": "'", "ʹ": "'", "`": "'", "´": "'", "‘": "'", "º": "°", "⁰": "°", "∠": "", "^": "", "·": "."})


def fact_norm(text: str) -> str:
    """Whitespace-free, prime/degree-unified form used to look a critical fact up in a transcription or an OCR text."""
    text = unicodedata.normalize("NFC", text).translate(PRIMES)
    text = "".join(c for c in unicodedata.normalize("NFD", text) if c not in "̂̑")
    return re.sub(r"\s+", "", unicodedata.normalize("NFC", text))


def reference_text(case: dict) -> str:
    return case["statement"] + "\n" + " ".join(f"{letter}. {value}." for letter, value in case["choices"].items())


def write(name: str, data: dict) -> None:
    (RUN / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    meta = {r["row_idx"]: r for r in json.loads(META.read_text(encoding="utf-8"))["rows"]}
    screen = json.loads(SCREEN.read_text(encoding="utf-8"))
    sheet_index = json.loads((CACHE / "sheet_index.json").read_text(encoding="utf-8"))
    now = datetime.now(timezone.utc).isoformat()
    items = []
    for row_idx, case in sorted(CASES.items()):
        row = meta[row_idx]
        name = f"r{row_idx}_{row['dataset_id']}"
        data = (CACHE / name).read_bytes()
        reference = reference_text(case)
        normal = fact_norm(reference)
        for kind, forms in case["facts"]:  # every listed fact must literally be in the agent's own transcription
            assert any(fact_norm(form) in normal for form in forms), (row_idx, kind, forms)
        digest = hashlib.sha256(row["dataset_id"].encode()).hexdigest()
        key = row["dataset_answer_key"]
        assert key in case["choices"] and re.search(r"_key_([A-D])_", row["dataset_id"]).group(1) == key
        items.append({
            "case_id": f"vmmu_r{row_idx}", "row_idx": row_idx, "dataset": "anvo25/vmmu", "dataset_split": "full_vqa",
            "dataset_id": row["dataset_id"], "cache_path": f".superpowers/external_image_cache/controlled-vision-vmmu/{name}",
            "sha256": hashlib.sha256(data).hexdigest(), "file_size_bytes": len(data), "image_width": row["width"], "image_height": row["height"],
            "source_url": "https://huggingface.co/datasets/anvo25/vmmu",
            "api_row_url": f"https://datasets-server.huggingface.co/rows?dataset=anvo25/vmmu&config=default&split=full_vqa&offset={row_idx}&length=1",
            "license_status": "MIT_DECLARED_BY_DATASET_PUBLISHER", "underlying_exam_rights_independently_verified": False,
            "image_committed_to_git": False, "contains_personal_data": False,
            "partition": "development" if int(digest, 16) % 4 == 0 else "frozen_external_evaluation",
            "split_hash_sha256_of_dataset_id": digest,
            "printed_or_handwritten": "PRINTED", "capture": "RENDERED_EXAM_PAGE_CROP_NOT_A_PHOTOGRAPH",
            "ground_truth_text": reference, "statement": case["statement"], "choices": case["choices"],
            "ground_truth_status": "AGENT_TRANSCRIBED_UNVERIFIED",
            "critical_facts": [{"kind": kind, "accepted_forms": forms} for kind, forms in case["facts"]],
            "diagram_description": case["diagram"], "diagram_embedded_facts": case["diagram_facts"],
            "diagram_dependency_by_agent_reading": "REFERENCE_FIGURE_ONLY_ALL_PREMISES_IN_TEXT",
            "source_notes": case["source_notes"], "tags": case["tags"],
            "dataset_answer_key": key, "expected_answer": case["choices"][key],
            "oracle": {"provenance": "DATASET_ANSWER_KEY", "independent_of_axo_output": True, "independent_of_agent": True,
                       "agent_hand_derivation_letter": AGENT_DERIVED_LETTER.get(row_idx),
                       "agent_derivation_agrees_with_key": (AGENT_DERIVED_LETTER[row_idx] == key) if row_idx in AGENT_DERIVED_LETTER else None,
                       "status": "DATASET_KEY_NOT_INDEPENDENTLY_ADJUDICATED"},
            "solver_scope": "OUT_OF_SCOPE" if row_idx in OUT_OF_SCOPE_BY_DOMAIN else "UNKNOWN_PENDING_ADJUDICATION",
            "solver_scope_basis": OUT_OF_SCOPE_BY_DOMAIN.get(row_idx, "set by the verified-text diagnostic in transcription_solver_diagnostic.json, never by keywords"),
        })
    assert len({i["sha256"] for i in items}) == len(items)
    split = Counter(i["partition"] for i in items)
    listed = sorted(meta)
    downloaded = sorted(v["row_idx"] for v in screen.values())
    used_before = previously_used()
    untouched = [r for r in listed if r not in downloaded and ID_CORE.search(meta[r]["dataset_id"]).group(0) not in used_before]
    audit_names = sheet_index["audit"]
    write("new_in_scope_image_manifest.json", {
        "schema": "algosim-in-scope-real-image-corpus/1", "run_id": RUN.name, "frozen_at_utc": now,
        "status": "FROZEN_BEFORE_OCR_EVALUATION", "ground_truth_authority": "AGENT_TRANSCRIBED_UNVERIFIED", "independent_h1": "NOT_MEASURED",
        "requested_candidates": [15, 25], "actual_items": len(items), "polyhedron_items": len(items) - len(OUT_OF_SCOPE_BY_DOMAIN),
        "split_rule": "development iff int(sha256(dataset_id), 16) % 4 == 0, else frozen_external_evaluation; depends on the dataset id only",
        "split_counts": dict(split),
        "coverage": dict(Counter(tag for i in items for tag in i["tags"])),
        "coverage_gaps": ["NO_HANDWRITTEN_IMAGES", "NO_CAMERA_PHOTOGRAPHS_OF_PAPER (rendered page crops only)", "NO_MULTI_PROBLEM_IMAGES",
                          "NO_CROSS_SECTION_PROBLEM", "ALL_ITEMS_MULTIPLE_CHOICE_FROM_ONE_DATASET"],
        "items": items})
    write("ground_truth_verification_status.json", {
        "schema": "algosim-ground-truth-verification-status/1", "run_id": RUN.name, "generated_at_utc": now,
        "items": len(items), "human_verified": 0, "agent_transcribed_unverified": len(items), "ocr_or_axo_output_used_as_reference": 0,
        "transcription_method": "Agent read contact sheets and native-resolution crops of the cached images. No OCR text of these images had been inspected; the keyword screen stored only hit lists.",
        "answer_oracle": {"provenance": "DATASET_ANSWER_KEY (letter in the dataset id and ground_truth column)",
                          "agent_hand_derivations": len(AGENT_DERIVED_LETTER),
                          "agent_derivations_agreeing_with_key": sum(i["oracle"]["agent_derivation_agrees_with_key"] is True for i in items),
                          "agent_derivations_disagreeing": [i["case_id"] for i in items if i["oracle"]["agent_derivation_agrees_with_key"] is False],
                          "not_derived_by_agent": [i["case_id"] for i in items if i["oracle"]["agent_hand_derivation_letter"] is None],
                          "status": "The key is independent of Axo and of the agent but was not re-adjudicated by a human."},
        "source_glyph_corruption_cases": [i["case_id"] for i in items if any("SOURCE_GLYPH_CORRUPTION" in n for n in i["source_notes"])],
        "source_glyph_corruption_policy": "The reference carries the intended notation (prime, degree). An OCR that reproduces the corrupted glyph is counted as not recovering the fact, because the solver cannot use it.",
        "independent_h1": "NOT_MEASURED", "human_verification_required_for": ["HUMAN_VERIFIED label", "independent H-1 claim", "any accuracy figure quoted outside this run"]})
    write("corpus_contamination_audit.json", {
        "schema": "algosim-corpus-contamination-audit/1", "run_id": RUN.name, "generated_at_utc": now,
        "source_population": {"dataset": "anvo25/vmmu", "split": "full_vqa", "math_rows_listed": len(listed), "row_range": [listed[0], listed[-1]]},
        "excluded_as_seen_by_earlier_runs": sum(ID_CORE.search(meta[r]["dataset_id"]).group(0) in used_before for r in listed),
        "exclusion_basis": "dataset question id found in any earlier cache file name, whether or not that image was finally evaluated",
        "downloaded_and_screened_this_run": len(downloaded), "downloaded_row_range": [downloaded[0], downloaded[-1]],
        "selection": {
            "stage_1": "accent-insensitive keyword match on Tesseract-only text (one of the product engines)",
            "stage_1_hits": len(sheet_index["hits"]), "stage_1_non_hits": sheet_index["non_hits"],
            "stage_2": "agent viewed every hit; all hits were solid-geometry problems and all were kept",
            "selection_bias": "Images whose keywords Tesseract cannot read are under-represented, so recognition figures on this corpus may be optimistic.",
            "miss_rate_audit": {"viewed_non_hits": 43 + len(audit_names), "note": "all 43 non-hits of rows 240-299 were viewed, then a seeded sample of the full non-hit pool (seed 20261112)",
                                "sample_overlaps_first_batch": "possible; the two views are not disjoint",
                                "in_scope_polyhedron_metric_problems_missed_in_first_43": 0,
                                "solid_geometry_but_out_of_scope_in_first_43": ["row 257: count edges of a drawn polyhedron", "row 289: cone filled with water"],
                                "second_sample_reviewed": False}},
        "partitions": {"development": [i["case_id"] for i in items if i["partition"] == "development"],
                       "frozen_external_evaluation": [i["case_id"] for i in items if i["partition"] == "frozen_external_evaluation"]},
        "evaluation_images_used_for_tuning": [],
        "exposure_of_evaluation_split": "The agent that transcribed the images also runs the evaluation, so the split is developer-exposed, not blind. No product code may be tuned on it; any item used for a fix must be moved to development and reported.",
        "independent_h1_candidate_pool": {"status": "RESERVED_UNTOUCHED_NOT_AN_H1_RESULT", "rows": untouched, "count": len(untouched),
                                          "condition": "listed by metadata only; images never downloaded or viewed by any agent in this run. Becomes H-1 only if an independent person selects, transcribes and scores them."},
        "prior_corpora": "The 12 older VMMU images and the 8 images of real-image-ocr-vision-comparative-acceptance are development-exposed and are not reused here."})
    print(json.dumps({"items": len(items), "split": dict(split), "h1_pool": len(untouched),
                      "agent_vs_key": Counter(str(i["oracle"]["agent_derivation_agrees_with_key"]) for i in items)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
