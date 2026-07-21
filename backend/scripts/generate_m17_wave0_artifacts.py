# -*- coding: utf-8 -*-
"""CLI sinh 6 artifact M17-Lite Wave 0 → docs/evaluation/m17/wave0/.

Chạy TOÀN BỘ audit matrix offline (provider scripted, 0 network) qua
production run_pipeline rồi ghi:
- authenticity_results.json / authenticity_metrics.json /
  generic_leak_ledger.json / curriculum_coverage.json  (payload chuẩn:
  schema_version + run_label + run_meta{git_commit, generated_at} + data)
- simulation_authenticity_report.md / curriculum_gap_report.md (tất định,
  KHÔNG timestamp trong nội dung → sync-lock so nguyên văn)

Cách chạy:  cd backend && .venv/Scripts/python.exe scripts/generate_m17_wave0_artifacts.py
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.authenticity_artifacts import (  # noqa: E402
    build_authenticity_metrics,
    build_authenticity_report_md,
    build_authenticity_results,
    build_curriculum_coverage,
    build_gap_report_md,
    build_generic_leak_ledger_artifact,
    run_offline_audit,
)

OUT_DIR = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17" / "wave0"
SCHEMA_VERSION = "1"
RUN_LABEL = "wave0-offline"


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
            cwd=Path(__file__).resolve().parents[2],
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    records = run_offline_audit()
    meta = {"git_commit": _git_commit(), "generated_at": datetime.now(timezone.utc).isoformat()}
    payloads = {
        "authenticity_results.json": build_authenticity_results(records),
        "authenticity_metrics.json": build_authenticity_metrics(records),
        "generic_leak_ledger.json": build_generic_leak_ledger_artifact(records),
        "curriculum_coverage.json": build_curriculum_coverage(records),
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, data in payloads.items():
        payload = {
            "schema_version": SCHEMA_VERSION,
            "run_label": RUN_LABEL,
            "run_meta": meta,
            "data": data,
        }
        (OUT_DIR / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Đã ghi {OUT_DIR / name}")
    (OUT_DIR / "simulation_authenticity_report.md").write_text(
        build_authenticity_report_md(records), encoding="utf-8"
    )
    (OUT_DIR / "curriculum_gap_report.md").write_text(
        build_gap_report_md(records), encoding="utf-8"
    )
    print(f"Đã ghi {OUT_DIR / 'simulation_authenticity_report.md'}")
    print(f"Đã ghi {OUT_DIR / 'curriculum_gap_report.md'}")


if __name__ == "__main__":
    main()
