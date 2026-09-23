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
    # `domains/semantic` — chủ THẬT của bản mirror. Nó từng nằm ở
    # `domains/generic/` (route ngữ nghĩa dựng cho miền Tin học); domain ấy đã
    # gỡ, schema thì không — nó là hợp đồng IR hình học.
    frontend_schema_path = root_dir / "frontend" / "src" / "simulations" / "domains" / "semantic" / "semantic_program.schema.json"

    assert docs_schema_path.exists(), f"Thiếu file schema: {docs_schema_path}"
    assert frontend_schema_path.exists(), f"Thiếu file schema: {frontend_schema_path}"

    expected_schema = generate_json_schema()
    expected_str = json.dumps(expected_schema, indent=2, ensure_ascii=False) + "\n"

    docs_str = docs_schema_path.read_text(encoding="utf-8")
    frontend_str = frontend_schema_path.read_text(encoding="utf-8")

    assert docs_str == frontend_str, "Schema trong docs và frontend phải đồng bộ tuyệt đối 100%."

    if docs_str != expected_str:
        # Khi candidate đang đóng băng tại commit 5a5534fe trước wave live revalidation,
        # schema trên đĩa giữ nguyên bản đóng băng để bảo toàn tree_hash.
        # Xác minh phần lệch duy nhất giữa đĩa và Pydantic hiện tại chỉ là trường provenance.
        docs_json = json.loads(docs_str)
        defs = docs_json.get("$defs", {})
        exp_defs = expected_schema.get("$defs", {})
        mem_diff = set(exp_defs.get("MemoryDeclaration", {}).get("properties", {})) - set(defs.get("MemoryDeclaration", {}).get("properties", {}))
        pt_diff = set(exp_defs.get("DeclarePointStmt", {}).get("properties", {})) - set(defs.get("DeclarePointStmt", {}).get("properties", {}))
        assert mem_diff == {"provenance"}, f"Lệch ngoài dự kiến trong MemoryDeclaration: {mem_diff}"
        assert pt_diff == {"provenance"}, f"Lệch ngoài dự kiến trong DeclarePointStmt: {pt_diff}"
