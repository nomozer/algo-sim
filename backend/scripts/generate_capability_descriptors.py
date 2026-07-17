"""M14 §C4 — sinh capability-descriptors.json cho frontend từ CATALOG +
FAMILY_SELECTORS (chạy tay khi metadata descriptor đổi).

Artifact TEST/GENERATED — production FE KHÔNG import (điểm 6). Sync-lock:
`tests/test_capability_descriptors.py`.

Cách chạy:  cd backend && .venv/Scripts/python scripts/generate_capability_descriptors.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.simulation.catalog import capability_descriptors  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "frontend/src/simulations/capability-descriptors.json"
OUT.write_text(json.dumps(capability_descriptors(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Đã sinh {OUT}")
