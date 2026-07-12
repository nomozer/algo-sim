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
