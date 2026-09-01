# -*- coding: utf-8 -*-
"""Script xuất JSON Schema cho SemanticProgramSpec từ Python Pydantic Model sang Frontend & Docs."""
from pathlib import Path
import json
import sys

# Ensure backend path in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.simulation.semantic_program.contract import generate_json_schema

def export_schema():
    schema = generate_json_schema()
    formatted = json.dumps(schema, indent=2, ensure_ascii=False) + "\n"

    # Targets
    root_dir = backend_dir.parent
    docs_target = root_dir / "docs" / "schemas" / "semantic_program.schema.json"
    # Bản mirror nằm cạnh module SỞ HỮU nó. Trước đây nó ở `domains/generic/`
    # vì route ngữ nghĩa từng dựng cho miền Tin học; `generic` đã gỡ cùng chín
    # domain ấy, còn schema thì thuộc về `domains/semantic` — nơi đăng ký
    # `generic.semantic_program`, tức nơi thật sự đọc nó.
    frontend_target = root_dir / "frontend" / "src" / "simulations" / "domains" / "semantic" / "semantic_program.schema.json"

    docs_target.parent.mkdir(parents=True, exist_ok=True)
    docs_target.write_text(formatted, encoding="utf-8")
    print(f"Exported schema -> {docs_target}")

    frontend_target.parent.mkdir(parents=True, exist_ok=True)
    frontend_target.write_text(formatted, encoding="utf-8")
    print(f"Exported schema -> {frontend_target}")

if __name__ == "__main__":
    export_schema()
