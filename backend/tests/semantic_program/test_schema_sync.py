# -*- coding: utf-8 -*-
"""Test CI đảm bảo JSON Schema giữa Backend Pydantic và Frontend luôn đồng bộ 100%."""
from pathlib import Path
import json
from app.simulation.semantic_program.contract import generate_json_schema

def test_exported_json_schema_in_sync():
    """Kiểm tra file schema trên đĩa khớp 100% với schema sinh từ Pydantic."""
    # Path(__file__).parents[3] is project root (algo-sim)
    root_dir = Path(__file__).resolve().parents[3]
    docs_schema_path = root_dir / "docs" / "schemas" / "semantic_program.schema.json"
    frontend_schema_path = root_dir / "frontend" / "src" / "simulations" / "domains" / "generic" / "semantic_program.schema.json"

    assert docs_schema_path.exists(), f"Thiếu file schema: {docs_schema_path}"
    assert frontend_schema_path.exists(), f"Thiếu file schema: {frontend_schema_path}"

    expected_schema = generate_json_schema()
    expected_str = json.dumps(expected_schema, indent=2, ensure_ascii=False) + "\n"

    docs_str = docs_schema_path.read_text(encoding="utf-8")
    frontend_str = frontend_schema_path.read_text(encoding="utf-8")

    assert docs_str == expected_str, "Schema trong docs/schemas bị out of sync với Pydantic model! Hãy chạy backend/scripts/export_semantic_program_schema.py."
    assert frontend_str == expected_str, "Schema trong frontend bị out of sync với Pydantic model! Hãy chạy backend/scripts/export_semantic_program_schema.py."
