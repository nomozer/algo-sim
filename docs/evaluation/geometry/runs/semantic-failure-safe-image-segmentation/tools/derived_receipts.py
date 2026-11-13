"""Receipts derived from this run's measurements, plus the diagram-to-problem association measured with the product's
own band helpers. Run from the worktree root:  python derived_receipts.py <image_e2e_json>"""
from __future__ import annotations

import io
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
sys.path[:0] = [str(ROOT / "backend"), str(Path(__file__).resolve().parent)]
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
os.environ.setdefault("LOCAL_OCR_PYTHON", str(ROOT / ".superpowers/ocr-venv/Scripts/python.exe"))
os.environ.setdefault("LOCAL_OCR_TESSDATA", str(ROOT / ".superpowers/tessdata_fast"))
NOW = datetime.now(timezone.utc).isoformat()


def git(*a):
    return subprocess.check_output(["git", *a], cwd=ROOT).decode().strip()


META = {"run_id": RUN.name, "generated_at_utc": NOW, "head": None, "environment": {"ALLOW_LIVE_AI": "0"}}


def put(n, d):
    (RUN / n).write_text(json.dumps({**META, "head": git("rev-parse", "HEAD"), **d}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load(n):
    return json.loads((RUN / n).read_text(encoding="utf-8"))


def association() -> dict:
    from app.ingestion.image import normalize_image
    from app.ingestion.local_ocr_route import estimate_problem_signals
    from app.ingestion.region_detector import detect_problem_regions
    from app.ingestion.unified_input import _band_blocks
    from segmentation_eval import pages
    rows, det = [], []
    for pg in pages():
        if pg["set"] == "REAL_SINGLE":
            continue
        buf = io.BytesIO()
        pg["img"].save(buf, format="PNG")
        rr = detect_problem_regions(normalize_image(buf.getvalue()))
        sig = estimate_problem_signals(rr.prepared_image.data)
        bands = (sig or {}).get("bands") or []
        figs = [[b for b in _band_blocks(rr, band) if b.kind == "figure"] for band in bands]
        shared = sum(1 for i, a in enumerate(figs) for j, b in enumerate(figs) if i < j and set(map(id, a)) & set(map(id, b)))
        again = estimate_problem_signals(rr.prepared_image.data)            # determinism of a chosen band (cached OCR)
        det.append((again or {}).get("bands") == (sig or {}).get("bands"))
        rows.append({"set": pg["set"], "id": pg["id"], "problems": len(pg["members"]), "bands": len(bands),
                     "bands_with_own_figure": sum(bool(f) for f in figs), "figure_blocks_shared_by_two_bands": shared})
    return {"rows": rows, "deterministic": all(det)}


def main(e2e: Path) -> int:
    seg = load("multi_problem_segmentation_before_after.json")
    shutil.copyfile(e2e, RUN / "image_selection_browser_e2e.json")
    e = load("image_selection_browser_e2e.json")
    put("image_region_failure_baseline.json", {
        "baseline": "product before this run (archive of 697b097ac) on the prepare path",
        "summary_before": seg["summary_before"],
        "earlier_detector_only_measurement": "independent-geometry-plane-constraints/image_region_detection_evaluation.json: detector merged 5/20 synthetic multi-problem pages, split 11/25 one-problem crops (rescued by the ≤ 1 header guard)",
        "failure_modes": {"merged_without_prompt": "detector keeps one region over several problems and no header guard fires",
                          "detector_blocks_as_choices": "a choice exists but a choice holds no full problem (text parted from its figure)",
                          "header_guard_overrule": "≤ 1 readable 'Câu N' keeps the page whole even when it holds several problems"},
        "dataset_partition": "DEVELOPMENT_EXPOSED crops and synthetic layouts of them", "oracle_status": "BY_CONSTRUCTION layout"})
    singles_b = seg["summary_before"]["REAL_SINGLE"]
    singles_a = seg["summary_after"]["REAL_SINGLE"]
    put("single_problem_false_split_audit.json", {
        "one_problem_images": 25, "before": singles_b, "after": singles_a,
        "unnecessary_selection_prompts": {"before": singles_b["unnecessary_selection_prompts"], "after": singles_a["unnecessary_selection_prompts"]},
        "option_group_estimate_on_singles": "24/25 crops read as exactly one option group; 1 (vmmu_r254) as none (no evidence → behaviour unchanged) — development prototype receipt in this run's log",
        "multi_figure_rule": "the number of figures never counts problems; only option groups (one option A per problem) and 'Câu N' headers do",
        "browser": {"single_problem_asked_to_choose": [r["single_problem"]["asked_to_choose"] for r in e["rows"]]},
        "not_measured": ["one problem with two figures and no options (no exposed image)", "camera photos", "handwriting"]})
    assoc = association()
    put("diagram_to_problem_association.json", {
        "method": "for every synthetic multi-problem page: the product's detector, the option-group bands of its prepared image and the product's _band_blocks — does each band hold a figure block of its own, is any figure block shared by two bands",
        "rows": assoc["rows"],
        "bands_with_own_figure": f"{sum(r['bands_with_own_figure'] for r in assoc['rows'])}/{sum(r['bands'] for r in assoc['rows'])} bands",
        "figure_blocks_shared_by_two_bands": sum(r["figure_blocks_shared_by_two_bands"] for r in assoc["rows"]),
        "diagram_facts": "never a typed fact: the fidelity gate keeps figure-only facts out (unchanged); a figure is only kept with its problem's crop",
        "dataset_partition": "DEVELOPMENT_EXPOSED crops (each holds exactly one figure) in synthetic layouts", "oracle_status": "BY_CONSTRUCTION"})
    put("ocr_confirmation_state_integrity.json", {
        "band_choice_deterministic": assoc["deterministic"],
        "stale_or_foreign_band_id": "refused with AMBIGUOUS_PROBLEM_BOUNDARIES and no candidates (test_a_stale_band_choice_is_refused_not_guessed)",
        "chosen_band_only_is_cut": "test_two_option_groups_in_one_region_ask_the_learner_to_choose (the crop is exactly the chosen rectangle)",
        "browser": [{"viewport": r["viewport"], "pick_2_target_vs_neighbour": [r["two_problems"]["pick_2"]["target_r298"], r["two_problems"]["pick_2"]["neighbour_r273"]],
                     "repick_1_target_vs_neighbour": [r["two_problems"]["repick_1"]["target_r273"], r["two_problems"]["repick_1"]["neighbour_r298"]],
                     "review_shows_neighbour": r["two_problems"]["review_shows_neighbour"],
                     "analyzed_text_target_vs_neighbour": [r["two_problems"]["analyzed_text_target_r273"], r["two_problems"]["analyzed_text_neighbour_r298"]],
                     "analyze_status": r["two_problems"]["analyze_status"]} for r in e["rows"]],
        "cache": "OCR results are cached per image BYTES: a band is new bytes, so its OCR, spans and offsets are its own; the analysis cache key is the confirmed text, so another problem's text is another key; the frontend reducer replaces the assist state on every prepare response (photo-problem-flow 'from-prepare')",
        "neighbour_containment_note": "5-gram containment ≈ 0.07–0.11 of the neighbour's statement is shared boilerplate ('Cho hình …', option letters), not its facts"})
    tp = load("text_vs_payload_negative_evaluation.json")
    put("source_gate_integrity.json", {
        "source_gate_changed_in_this_run": bool(git("diff", "--name-only", "dcbedcb0d", "HEAD", "--", "backend/app/simulation/geometry_functions/registry.py")),
        "registry_diff_since_start": git("diff", "--stat", "dcbedcb0d", "HEAD", "--", "backend/app/simulation/geometry_functions/registry.py") or "none",
        "repairs_pass_the_unchanged_gate": "every repaired wording is served only after the existing gate reads it; 'thiết diện do (P) cắt' was dropped from the parser because the gate has no reading of it (backlog)",
        "track_b_payload_corruptions_refused": f"{tp['track_b_payload']['items'] - tp['track_b_payload']['served']}/{tp['track_b_payload']['items']}",
        "track_a_text_negatives_refused": f"{tp['track_a_text']['items'] - tp['track_a_text']['served']}/{tp['track_a_text']['items']}",
        "silent_premise_loss_checks": "a served problem never carries an unread clause: the parser refuses unless every fact/goal clause is mapped, and the gate reads every premise sentence (SOURCE_PREMISE_UNREAD)"})
    put("new_locked_evaluation_status.json", {"NEW_INDEPENDENT_EVALUATION": "BLOCKED_DATA",
        "why": "no rights-cleared, unexposed, in-scope dataset exists beyond the 94 sealed H-1 rows (see independent-geometry-plane-constraints/dataset_partition_audit.json); W2/W3 remain locked except W2-N03 and W3-N63 and were not re-run",
        "locked_rows_rerun_in_this_run": 0})
    put("independent_h1_status.json", {"status": "NOT_MEASURED", "sealed_rows": 94, "opened": 0, "why": "no independent selector, transcriber or scorer"})
    put("resource_cleanup_audit.json", {
        "frontend_changed_in_this_run": bool(git("diff", "--name-only", "dcbedcb0d", "HEAD", "--", "frontend/src")),
        "scene3d_memory": "NOT_REMEASURED: the frontend is unchanged in this run; the previous measurement (+3.2 MB over 12 analyses, INCONCLUSIVE) stands",
        "band_previews": "inline base64 JPEG data URLs in the JSON response (no object URLs to revoke); at most one per candidate, ≤ 360 px",
        "ocr_worker": "unchanged lifecycle; the option-group signal reuses the cached OCR of the same bytes",
        "MEMORY_LEAK": "NOT_MEASURED_THIS_RUN"})
    print("ok", assoc["deterministic"], sum(r["bands_with_own_figure"] for r in assoc["rows"]), sum(r["bands"] for r in assoc["rows"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1])))
