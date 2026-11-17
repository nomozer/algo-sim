# -*- coding: utf-8 -*-
"""Export deduplicated, verified, conflict-quarantined step-edit feedback into grouped JSONL splits."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(_BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(_BACKEND_DIR))

from app.persistence.db import SessionLocal
from app.persistence.step_edit_models import ensure_step_edit_tables
from app.simulation.geometry_functions.feedback_dataset import (
    UntrainedLocalStepIntentAdapter,
    export_step_feedback_dataset,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare verified step-edit feedback dataset.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=_BACKEND_DIR / "reports" / "step_feedback_dataset",
        help="Directory to write train.jsonl, val.jsonl, test.jsonl, and manifest.json",
    )
    args = parser.parse_args()

    ensure_step_edit_tables()
    with SessionLocal() as db:
        manifest = export_step_feedback_dataset(db)
        db.commit()

    out_dir: Path = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    for split_name in ("train", "val", "test"):
        lines = [
            json.dumps(item, ensure_ascii=False, sort_keys=True)
            for item in manifest["splits"][split_name]
        ]
        (out_dir / f"{split_name}.jsonl").write_text(
            "\n".join(lines) + ("\n" if lines else ""),
            encoding="utf-8",
        )

    benchmark = UntrainedLocalStepIntentAdapter().evaluate_benchmark()
    summary = {
        k: v for k, v in manifest.items() if k != "splits"
    }
    summary["benchmark"] = {
        "model_status": benchmark["model_status"],
        "case_count": benchmark["case_count"],
        "passed_count": benchmark["passed_count"],
        "parser_baseline_accuracy": benchmark["parser_baseline_accuracy"],
    }
    (out_dir / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
