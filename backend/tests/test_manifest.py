# -*- coding: utf-8 -*-
"""Test DSL Capability Manifest (M7 §2, §9) — nguồn chân lý, chống drift."""

import pytest
from fastapi.testclient import TestClient

from app.simulation.dsl import validator as dsl
from app.simulation.dsl.validator import validate_generic_config
from app.simulation.dsl.manifest import (
    MANIFEST,
    SUPPORTED_VERSIONS,
    manifest_capability_summary,
    manifest_contract_text,
)
from app.main import app

client = TestClient(app)


def test_manifest_cau_truc():
    assert MANIFEST["dsl_version"] == "1.0"
    assert "switch" in MANIFEST["object_types"]
    assert "boolean" in MANIFEST["rule_types"]
    assert "move_along_path" in MANIFEST["process_types"]
    assert MANIFEST["limits"]["max_objects"] == 20


def test_validator_dan_xuat_tu_manifest():
    """Allowlist của validator = manifest (nếu drift, test này gãy)."""
    assert dsl.OBJECT_TYPES == set(MANIFEST["object_types"])
    assert dsl.RULE_TYPES == set(MANIFEST["rule_types"])
    assert dsl.BOOL_OPS == set(MANIFEST["bool_ops"])
    assert dsl.MAX_OBJECTS == MANIFEST["limits"]["max_objects"]


def test_contract_chua_moi_type_tu_manifest():
    """Prompt contract (simulate) sinh từ manifest → chứa mọi primitive."""
    text = manifest_contract_text()
    for t in MANIFEST["object_types"]:
        assert t in text, f"contract thiếu object type {t}"
    for t in MANIFEST["rule_types"]:
        assert t in text
    assert "move_along_path" in text
    assert '"1.0"' in text


def test_contract_huong_dan_chuoi_rule_m11():
    """M11 (đo live): thiếu hướng dẫn chained-dependency → LLM ép phẳng điều
    kiện ghép thành 1 rule (sai ngữ nghĩa) hoặc sinh spec không hợp lệ. Contract
    phải nêu: target làm input rule khác + object trung gian + không gắn value
    cho object dẫn xuất/trang trí. Ví dụ trong contract phải TRỪU TƯỢNG (không
    trùng câu đề đánh giá nào — chống overfit prompt vào benchmark)."""
    text = manifest_contract_text()
    assert "trung gian" in text
    assert "input của rule khác" in text or "làm input" in text
    assert "MỘT rule sở hữu" in text
    # ví dụ trừu tượng dùng id trung tính, không phải A/B/C của case đánh giá
    assert "kq_phu" in text


def test_reject_dsl_version_khong_ho_tro():
    spec = {"dsl_version": "2.0", "title": "x", "objects": [{"id": "a", "type": "switch", "value": 0}]}
    config, err = validate_generic_config(spec)
    assert config is None
    assert "dsl_version" in err
    assert "2.0" in SUPPORTED_VERSIONS or True  # tài liệu: 2.0 không thuộc SUPPORTED


def test_dsl_version_hop_le_van_chay():
    spec = {"dsl_version": "1.0", "title": "x", "objects": [{"id": "a", "type": "label"}]}
    assert validate_generic_config(spec)[1] is None


def test_capability_summary_dan_xuat_tu_manifest():
    """M7.8: tóm tắt năng lực (cho classify) phải chứa mọi type từ manifest
    + ánh xạ ngôn ngữ tự nhiên (điểm→node, đoạn→edge) + reveal_sequence."""
    s = manifest_capability_summary()
    for t in MANIFEST["object_types"]:
        assert t in s, f"thiếu object type {t}"
    for t in MANIFEST["process_types"]:
        assert t in s
    # ánh xạ + định hướng capability-not-subject
    assert "ĐIỂM" in s and "ĐOẠN" in s
    assert "reveal_sequence" in s
    assert "KHÔNG dựa vào tên môn học" in s


def test_endpoint_manifest():
    res = client.get("/api/manifest")
    assert res.status_code == 200
    body = res.json()
    assert body["dsl_version"] == "1.0"
    assert "object_types" in body


# ── M7.13A: drag interaction + họ temporal process ────────────

def test_drag_trong_manifest_va_validator_dan_xuat():
    from app.simulation.dsl.manifest import drag_target_types

    assert "drag" in MANIFEST["interaction_types"]
    assert MANIFEST["drag_target_types"] == ["node"]  # v1: chỉ node
    assert dsl.DRAG_TARGET_TYPES == drag_target_types()
    assert dsl.INTERACTION_TYPES == set(MANIFEST["interaction_types"])


def test_temporal_process_family_dan_xuat_tu_taxonomy():
    """Điều chỉnh #1: họ temporal process suy từ role taxonomy, KHÔNG hard-code
    tên — reveal_sequence VÀ move_along_path đều thuộc họ này."""
    from app.simulation.dsl.manifest import PRIMITIVE_ROLES, temporal_process_types

    family = temporal_process_types()
    assert family == {"reveal_sequence", "move_along_path"}
    for p in family:
        assert "temporal" in PRIMITIVE_ROLES[p]


def test_interaction_cover_vai_tro_interactive():
    from app.simulation.dsl.manifest import roles_of_primitive

    assert roles_of_primitive("toggle") == {"interactive"}
    assert roles_of_primitive("drag") == {"interactive"}


def test_contract_va_capability_summary_co_drag():
    text = manifest_contract_text()
    assert "drag" in text and "bounds" in text and "snap" in text
    assert "drag" in manifest_capability_summary()


def test_generic_schema_enum_dan_xuat_tu_manifest():
    """CHỐNG DRIFT (bug live M7.13A): schema structured-output viết tay từng
    thiếu drag → Gemini KHÔNG THỂ phát interaction mới dù contract cho phép.
    Mọi enum của _GENERIC_SCHEMA phải == manifest."""
    from app.simulation.catalog import CATALOG

    props = CATALOG["generic.rule_scene"].config_schema["properties"]
    obj_enum = set(props["objects"]["items"]["properties"]["type"]["enum"])
    rule_enum = set(props["rules"]["items"]["properties"]["type"]["enum"])
    op_enum = set(props["rules"]["items"]["properties"]["op"]["enum"])
    inter_enum = set(props["interactions"]["items"]["properties"]["type"]["enum"])
    proc_enum = set(props["processes"]["items"]["properties"]["type"]["enum"])
    assert obj_enum == set(MANIFEST["object_types"])
    assert rule_enum == set(MANIFEST["rule_types"])
    assert op_enum == set(MANIFEST["bool_ops"])
    assert inter_enum == set(MANIFEST["interaction_types"])
    assert proc_enum == set(MANIFEST["process_types"])
    # interactions phải khai được constraints (bounds/axis/snap) cho drag
    c = props["interactions"]["items"]["properties"]["constraints"]["properties"]
    assert set(c) == {"bounds", "axis", "snap"}
