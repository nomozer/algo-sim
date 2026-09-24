# -*- coding: utf-8 -*-
"""Test CI đảm bảo JSON Schema giữa Backend Pydantic và Frontend luôn đồng bộ 100%."""
import json
import subprocess
import sys
from pathlib import Path

from app.simulation.semantic_program.contract import generate_json_schema


def test_exported_json_schema_in_sync():
    """Kiểm tra file schema trên đĩa khớp 100% với schema sinh từ Pydantic."""
    # Path(__file__).parents[3] is project root (algo-sim)
    root_dir = Path(__file__).resolve().parents[3]
    docs_schema_path = root_dir / "docs" / "schemas" / "semantic_program.schema.json"
    # `domains/semantic` — chủ THẬT của bản mirror. Nó từng nằm ở
    # `domains/generic/` (route ngữ nghĩa dựng cho miền Tin học); domain ấy đã
    # gỡ, schema thì không — nó là hợp đồng IR hình học.
    frontend_schema_path = root_dir / "frontend" / "src" / "simulations" / "domains" / "semantic" / "semantic_program.schema.json"

    assert docs_schema_path.exists(), f"Thiếu file schema: {docs_schema_path}"
    assert frontend_schema_path.exists(), f"Thiếu file schema: {frontend_schema_path}"

    expected_schema = generate_json_schema()
    expected_str = json.dumps(expected_schema, indent=2, ensure_ascii=False) + "\n"

    # Chuẩn hoá LF để đảm bảo kiểm tra độc lập nền tảng
    docs_str = docs_schema_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    frontend_str = frontend_schema_path.read_text(encoding="utf-8").replace("\r\n", "\n")

    # Strict invariant: cả hai schema phải byte-identical với expected_str từ canonical exporter
    assert docs_str == frontend_str, "Schema trong docs và frontend phải đồng bộ tuyệt đối 100%."
    assert docs_str == expected_str, "Schema trong docs/schemas bị out of sync với Pydantic model! Hãy chạy backend/scripts/export_semantic_program_schema.py."
    assert frontend_str == expected_str, "Schema trong frontend bị out of sync với Pydantic model! Hãy chạy backend/scripts/export_semantic_program_schema.py."

    # Xác nhận rõ ràng sự tồn tại của provenance trong cả 2 definitions
    defs = expected_schema.get("$defs", {})
    mem_props = defs.get("MemoryDeclaration", {}).get("properties", {})
    pt_props = defs.get("DeclarePointStmt", {}).get("properties", {})
    assert "provenance" in mem_props, "Thiếu provenance trong MemoryDeclaration properties của Pydantic schema!"
    assert "provenance" in pt_props, "Thiếu provenance trong DeclarePointStmt properties của Pydantic schema!"

    docs_json = json.loads(docs_str)
    docs_defs = docs_json.get("$defs", {})
    assert "provenance" in docs_defs.get("MemoryDeclaration", {}).get("properties", {}), "Thiếu provenance trong docs MemoryDeclaration schema!"
    assert "provenance" in docs_defs.get("DeclarePointStmt", {}).get("properties", {}), "Thiếu provenance trong docs DeclarePointStmt schema!"


def test_exporter_idempotence():
    """Chạy exporter lần hai không tạo ra bất kỳ diff nào."""
    root_dir = Path(__file__).resolve().parents[3]
    script_path = root_dir / "backend" / "scripts" / "export_semantic_program_schema.py"
    docs_schema_path = root_dir / "docs" / "schemas" / "semantic_program.schema.json"
    frontend_schema_path = root_dir / "frontend" / "src" / "simulations" / "domains" / "semantic" / "semantic_program.schema.json"

    docs_truoc = docs_schema_path.read_bytes()
    fe_truoc = frontend_schema_path.read_bytes()

    res = subprocess.run([sys.executable, str(script_path)], capture_output=True, text=True, cwd=str(root_dir))
    assert res.returncode == 0, f"Lỗi chạy exporter: {res.stderr}"

    docs_sau = docs_schema_path.read_bytes()
    fe_sau = frontend_schema_path.read_bytes()

    assert docs_truoc == docs_sau, "Chạy export_semantic_program_schema.py làm thay đổi docs schema!"
    assert fe_truoc == fe_sau, "Chạy export_semantic_program_schema.py làm thay đổi frontend schema!"
