"""Image segmentation re-measured on the FINAL product code of run `compositional-semantics-simulation-goals`.

The previous run measured segmentation at cc449ae4b, before its last product commit 7315cf3b0 (figure blocks to the band
holding most of them). This tool re-runs the same instrument (semantic-failure-safe-image-segmentation/tools/
segmentation_eval.py: run + summarise, unchanged) on the current backend, adds the diagram-to-problem association measured
with the product's own `_band_blocks`, and writes the receipt HERE (nothing written into the earlier run).

  python segmentation_revalidation.py      # from the worktree root, backend interpreter, local OCR env set
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

RUN = Path(__file__).resolve().parents[1]
ROOT = RUN.parents[4]
PREV = RUN.parent / "semantic-failure-safe-image-segmentation"
sys.path[:0] = [str(ROOT / "backend"), str(PREV / "tools")]
os.environ["ALLOW_LIVE_AI"], os.environ["GEMINI_API_KEY"] = "0", ""
os.environ.setdefault("LOCAL_OCR_PYTHON", str(ROOT / ".superpowers/ocr-venv/Scripts/python.exe"))
os.environ.setdefault("LOCAL_OCR_TESSDATA", str(ROOT / ".superpowers/tessdata_fast"))
import segmentation_eval as SE  # noqa: E402
from derived_receipts import association  # noqa: E402  (pure function; writes nothing)


def main() -> int:
    rows = SE.run(ROOT / "backend")
    summary = SE.summarise(rows)
    assoc = association()
    prev = json.loads((PREV / "multi_problem_segmentation_before_after.json").read_text(encoding="utf-8"))["summary_after"]
    cand = json.loads((ROOT / "docs/evaluation/semantic-benchmark/EVALUATION_CANDIDATE.json").read_text(encoding="utf-8"))
    out = {"run_id": RUN.name, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
           "head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip(),
           "candidate_manifest_at_measurement": {"commit": cand["commit"], "measured_system": cand["measured_system"]["tree_hash"]},
           "environment": {"ALLOW_LIVE_AI": "0", "local_ocr": "RapidOCR + Tesseract (unchanged engines)"},
           "command": "python docs/evaluation/geometry/runs/compositional-semantics-simulation-goals/tools/segmentation_revalidation.py",
           "instrument": "semantic-failure-safe-image-segmentation/tools/segmentation_eval.py (run, summarise) — unchanged",
           "dataset_partition": "DEVELOPMENT_EXPOSED crops; composites and side-by-side pages are SYNTHETIC layouts of those crops (not camera photos)",
           "oracle_status": "BY_CONSTRUCTION page layout; text containment against AGENT_TRANSCRIBED_UNVERIFIED statements",
           "summary_final_candidate": summary, "previous_run_summary_at_cc449ae4b": prev,
           "diagram_to_problem_association": {
               "bands_with_own_figure": f"{sum(r['bands_with_own_figure'] for r in assoc['rows'])}/{sum(r['bands'] for r in assoc['rows'])}",
               "figure_blocks_shared_by_two_bands": sum(r["figure_blocks_shared_by_two_bands"] for r in assoc["rows"]),
               "band_choice_deterministic": assoc["deterministic"], "rows": assoc["rows"]},
           "rows": rows}
    (RUN / "final_candidate_image_segmentation_revalidation.json").write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"final": summary, "assoc": out["diagram_to_problem_association"]["bands_with_own_figure"],
                      "shared": out["diagram_to_problem_association"]["figure_blocks_shared_by_two_bands"]}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
