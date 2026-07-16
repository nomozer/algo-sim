"""Sinh dsl-contract.json cho frontend từ manifest (chạy tay khi manifest đổi).
Cách chạy:  cd backend && .venv/Scripts/python scripts/generate_dsl_contract.py"""
import json
import sys
from pathlib import Path

# Chạy trực tiếp file (không qua -m) không tự thêm backend/ vào sys.path trên
# mọi nền tảng — bootstrap thủ công để "app" import được dù chạy kiểu nào.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if hasattr(sys.stdout, "reconfigure"):  # console Windows mặc định không phải UTF-8
    sys.stdout.reconfigure(encoding="utf-8")

from app.simulation.dsl.manifest import dsl_semantic_contract  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "frontend/src/simulations/domains/generic/dsl-contract.json"
OUT.write_text(json.dumps(dsl_semantic_contract(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"Đã sinh {OUT}")
