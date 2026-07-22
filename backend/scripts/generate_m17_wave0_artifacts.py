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

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.wave_snapshots import snapshot_for  # noqa: E402
from app.evaluation.authenticity_artifacts import (  # noqa: E402
    build_authenticity_metrics,
    build_authenticity_report_md,
    build_authenticity_results,
    build_curriculum_coverage,
    build_gap_report_md,
    build_generic_leak_ledger_artifact,
    run_offline_audit,
)

_BASE = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17"
SCHEMA_VERSION = "1"
# Mặc định WAVE 1 (trạng thái hiện tại). Wave 0 là bản ghi lịch sử FROZEN
# (SHA-256 pin ở test_m17_wave0_artifacts.py) — KHÔNG sinh lại.
DEFAULT_WAVE = "wave2a"  # trạng thái HIỆN TẠI (chưa đóng băng)


def _git_commit() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
            cwd=Path(__file__).resolve().parents[2],
        ).stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=DEFAULT_WAVE,
                        help="wave1 (mặc định, trạng thái hiện tại). Wave 0 FROZEN — không sinh lại.")
    parser.add_argument("--out", default=None,
                        help="Thư mục ghi (mặc định docs/evaluation/m17/<wave>). "
                             "Dùng thư mục tạm để KIỂM tái lập mà không đụng bản đã commit.")
    args = parser.parse_args()

    # M17-RC1 §R1 — wave đã đóng băng sinh lại TỪ ẢNH CHỤP ĐẦU VÀO, KHÔNG từ
    # registry sống. Trước đây chạy lại hôm nay cho ra số của Wave 2A (73 case/
    # 19 target) thay vì số đã công bố của Wave 1 (68/18) — bằng chứng lịch sử
    # không tái lập được, chỉ còn "tin vào file đã commit".
    snapshot = snapshot_for(args.wave)
    out_dir = Path(args.out) if args.out else _BASE / args.wave
    run_label = f"{args.wave}-offline"

    records = run_offline_audit(snapshot)
    if snapshot is not None:
        # run_meta lấy TỪ SNAPSHOT: dùng giờ hiện tại thì không bao giờ
        # byte-identical, mà byte-identical mới là bằng chứng tái lập.
        meta = {"git_commit": snapshot.git_commit, "generated_at": snapshot.generated_at}
    else:
        meta = {"git_commit": _git_commit(),
                "generated_at": datetime.now(timezone.utc).isoformat()}
    payloads = {
        "authenticity_results.json": build_authenticity_results(records, snapshot),
        "authenticity_metrics.json": build_authenticity_metrics(records, snapshot),
        "generic_leak_ledger.json": build_generic_leak_ledger_artifact(records, snapshot),
        "curriculum_coverage.json": build_curriculum_coverage(records, snapshot),
    }
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, data in payloads.items():
        payload = {
            "schema_version": SCHEMA_VERSION,
            "run_label": run_label,
            "run_meta": meta,
            "data": data,
        }
        (out_dir / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        print(f"Đã ghi {out_dir / name}")
    (out_dir / "simulation_authenticity_report.md").write_text(
        build_authenticity_report_md(records, snapshot), encoding="utf-8"
    )
    (out_dir / "curriculum_gap_report.md").write_text(
        build_gap_report_md(records, snapshot), encoding="utf-8"
    )
    print(f"Đã ghi {out_dir / 'simulation_authenticity_report.md'}")
    print(f"Đã ghi {out_dir / 'curriculum_gap_report.md'}")


if __name__ == "__main__":
    main()
