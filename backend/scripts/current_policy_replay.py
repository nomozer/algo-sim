# -*- coding: utf-8 -*-
"""M17-RC1 §E chế độ 2 — CURRENT POLICY REPLAY.

Chạy ĐẦU VÀO lịch sử (bất biến, từ `input_snapshot.json`) qua pipeline/cổng
HIỆN TẠI. Kết quả **được phép đổi** — sản phẩm là *migration report*, không
phải kiểm byte-identical (đó là việc của `historical_reproduction.py`).

    python scripts/current_policy_replay.py --out ../docs/evaluation/m17/rc1
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.evaluation.wave_replay import build_migration_report  # noqa: E402
from app.evaluation.wave_snapshots import FROZEN_WAVES, snapshot_for  # noqa: E402

_WAVE_DIR = Path(__file__).resolve().parents[2] / "docs" / "evaluation" / "m17"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="../docs/evaluation/m17/rc1")
    args = p.parse_args()

    waves = []
    for wave_id in FROZEN_WAVES:
        snap = snapshot_for(wave_id)
        published = json.loads(
            (_WAVE_DIR / wave_id / "authenticity_results.json").read_text(encoding="utf-8"))
        waves.append(build_migration_report(snap, published))

    payload = {
        "schema_version": "1",
        "mode": "current_policy_replay",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Đầu vào lịch sử BẤT BIẾN + pipeline HIỆN TẠI. Kết quả được phép "
            "đổi. Artifact đã công bố KHÔNG bị sửa."
        ),
        "waves": waves,
        "unexplained_total": sum(len(w["unexplained_changes"]) for w in waves),
    }
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "current_policy_migration_report.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for w in waves:
        c = w["change_counts"]
        print(f"{w['wave_id']}: {w['case_count']} case · giữ nguyên {c['unchanged']} · "
              f"cổng mới chặn {c['blocked_by_new_gate']} · nay hỗ trợ "
              f"{c['route_now_supported']} · đổi route {c['route_changed']} · "
              f"khác {c['status_changed_other']} · KHÔNG giải thích được "
              f"{len(w['unexplained_changes'])}")
    print(f"Artifact → {out / 'current_policy_migration_report.json'}")
    return 0 if payload["unexplained_total"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
