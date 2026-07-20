"""M16 Task 6 (W6) — sinh 5 artifact JSON máy-đọc (docs/evaluation/m16/) từ
pool m16 + offline scripted run (chạy TRONG-PROCESS qua
`app.evaluation.m16_artifacts.run_offline_and_build_all()` — production
`run_pipeline` thật, bất biến #22, KHÔNG mạng thật: monkeypatch thủ công
`pipeline.call_gemini` bằng provider scripted, tự khôi phục trong `finally`).

Artifact GENERATED — sync-lock: `tests/test_m16_artifacts.py`. Chạy tay khi
pool/scripts/metric M16 đổi.

Cách chạy: cd backend && .venv/Scripts/python scripts/generate_m16_artifacts.py
(Windows: set PYTHONIOENCODING=utf-8 trước nếu console lỗi encode tiếng Việt)
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.evaluation.m16_artifacts import run_offline_and_build_all  # noqa: E402
from app.evaluation.m16_schema import M16_DATASET_VERSION  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = _REPO_ROOT / "docs/evaluation/m16"

# key (run_offline_and_build_all()) → tên file JSON commit.
_FILES: dict[str, str] = {
    "case_matrix": "m16-case-matrix.json",
    "coverage_report": "m16-coverage-report.json",
    "offline_results": "m16-offline-results.json",
    "metrics": "m16-metrics.json",
    "failure_ledger": "m16-failure-ledger.json",
}


def _git_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=str(_REPO_ROOT),
        )
        return out.stdout.strip()
    except Exception:
        return "unknown"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = run_offline_and_build_all()
    run_meta = {
        "git_commit": _git_commit(),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    for key, filename in _FILES.items():
        payload = {
            "schema_version": "1",
            "dataset_version": M16_DATASET_VERSION,
            "run_label": "offline",
            "run_meta": run_meta,
            "data": artifacts[key],
        }
        out_path = OUT_DIR / filename
        out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"Đã sinh {out_path}")


if __name__ == "__main__":
    main()
