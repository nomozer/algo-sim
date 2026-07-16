# -*- coding: utf-8 -*-
"""EditPolicy v1 (M7.14D) — affordance chỉnh sửa DẪN XUẤT TỪ NĂNG LỰC cảnh.

Khóa: cảnh generic KHÔNG còn nhận cùng một bộ thao tác; suy diễn thuần từ SPEC
(không tên bài/môn); enforce ở tầng patch (ẩn UI là không đủ); reason_code hai
namespace policy.* / structure.*.
"""

from app.simulation.dsl.validator import validate_generic_config
from app.simulation.edit_policy import (
    POLICY_OBJECT_TYPE_NOT_ALLOWED,
    POLICY_OPERATION_NOT_ALLOWED,
    POLICY_PATH_TOPOLOGY_LOCKED,
    STRUCTURE_INVALID,
    EditFamily,
    edit_policy_of,
    policy_contract_text,
)
from app.simulation.patch import validate_and_apply_patch


def _norm(raw: dict) -> dict:
    cfg, err = validate_generic_config(raw)
    assert err is None, err
    return cfg


TRIANGLE = _norm({  # node + edge + reveal → SPATIAL
    "dsl_version": "1.0", "title": "Tam giác ABC",
    "objects": [
        {"id": "A", "type": "node", "x": 20, "y": 70},
        {"id": "B", "type": "node", "x": 80, "y": 70},
        {"id": "C", "type": "node", "x": 50, "y": 20},
        {"id": "AB", "type": "edge", "from": "A", "to": "B"},
    ],
    "rules": [], "interactions": [{"type": "drag", "target": "C"}],
    "processes": [{"type": "reveal_sequence", "steps": [{"objects": ["A", "B"]}, {"objects": ["AB"]}]}],
})

WEB = _norm({  # container + heading + paragraph → STRUCTURAL
    "dsl_version": "1.0", "title": "Trang giới thiệu",
    "objects": [
        {"id": "page", "type": "container", "text": "Trang"},
        {"id": "h", "type": "heading", "text": "Xin chào", "parent": "page"},
        {"id": "p", "type": "paragraph", "text": "Đoạn văn.", "parent": "page"},
    ],
    "rules": [], "interactions": [], "processes": [],
})

GENERIC_LOGIC = _norm({  # switch + lamp + boolean → VALUE_ONLY
    "dsl_version": "1.0", "title": "Cổng AND",
    "objects": [
        {"id": "a", "type": "switch", "value": 0},
        {"id": "b", "type": "switch", "value": 0},
        {"id": "y", "type": "lamp"},
    ],
    "rules": [{"type": "boolean", "op": "and", "inputs": ["a", "b"], "target": "y"}],
    "interactions": [{"type": "toggle", "target": "a"}], "processes": [],
})

GENERIC_BINARY = _norm({  # switch + value_box + weighted_sum (weights trên rule) → VALUE_ONLY
    "dsl_version": "1.0", "title": "Đổi nhị phân",
    "objects": [
        {"id": "b0", "type": "switch", "value": 1},
        {"id": "b1", "type": "switch", "value": 0},
        {"id": "out", "type": "value_box"},
    ],
    "rules": [{"type": "weighted_sum", "inputs": ["b0", "b1"], "weights": [8, 4], "target": "out"}],
    "interactions": [{"type": "toggle", "target": "b0"}], "processes": [],
})

PACKET = _norm({  # node/edge + moving_entity + move_along_path → OBSERVATION
    "dsl_version": "1.0", "title": "Gói tin",
    "objects": [
        {"id": "c", "type": "node", "node_type": "client"},
        {"id": "s", "type": "node", "node_type": "server"},
        {"id": "e1", "type": "edge", "from": "c", "to": "s"},
        {"id": "pkt", "type": "moving_entity"},
    ],
    "rules": [], "interactions": [],
    "processes": [{"type": "move_along_path", "entity": "pkt", "path": ["c", "s"]}],
})


# ── Suy diễn family (thuần từ spec, không tên bài) ────────────

def test_family_suy_tu_cau_truc_spec():
    assert edit_policy_of(TRIANGLE)["family"] == EditFamily.SPATIAL
    assert edit_policy_of(WEB)["family"] == EditFamily.STRUCTURAL
    assert edit_policy_of(GENERIC_LOGIC)["family"] == EditFamily.VALUE_ONLY
    assert edit_policy_of(GENERIC_BINARY)["family"] == EditFamily.VALUE_ONLY
    assert edit_policy_of(PACKET)["family"] == EditFamily.OBSERVATION


def test_ui_actions_dung_theo_family():
    """Vấn đề gốc M7.14D: cảnh văn bản/giá trị KHÔNG được có Thêm điểm/Nối."""
    spatial = edit_policy_of(TRIANGLE)["ui_actions"]
    assert "add_node" in spatial and "connect" in spatial and "delete" in spatial

    structural = edit_policy_of(WEB)["ui_actions"]
    assert "add_content" in structural and "delete" in structural
    assert "add_node" not in structural and "connect" not in structural

    for scene in (GENERIC_LOGIC, GENERIC_BINARY):
        acts = edit_policy_of(scene)["ui_actions"]
        assert "add_node" not in acts and "connect" not in acts and "delete" not in acts

    obs = edit_policy_of(PACKET)["ui_actions"]
    assert "add_node" not in obs and "connect" not in obs


def test_structural_addable_types_va_gioi_han_do_sau():
    p = edit_policy_of(WEB)
    assert set(p["addable_types"]) >= {"heading", "paragraph", "text"}
    assert "node" not in p["addable_types"] and "edge" not in p["addable_types"]
    # còn dư độ sâu (max 4, hiện 1) → được thêm container/group
    assert "container" in p["addable_types"]

    deep = _norm({
        "dsl_version": "1.0", "title": "Lồng sâu",
        "objects": [
            {"id": "c1", "type": "container", "text": "1"},
            {"id": "c2", "type": "container", "text": "2", "parent": "c1"},
            {"id": "c3", "type": "container", "text": "3", "parent": "c2"},
            {"id": "h", "type": "heading", "text": "Sâu", "parent": "c3"},
        ],
        "rules": [], "interactions": [], "processes": [],
    })
    assert "container" not in edit_policy_of(deep)["addable_types"]  # hết dư độ sâu


# ── Precedence cảnh LAI (bảo thủ — chưa hỗ trợ multi-family) ──

def test_canh_lai_dung_precedence_bao_thu():
    """LIMITATION có chủ đích: cảnh vừa structural vừa node/edge → chọn family
    HẠN CHẾ HƠN (structural). Multi-family edit CHƯA được hỗ trợ."""
    mixed = _norm({
        "dsl_version": "1.0", "title": "Lai",
        "objects": [
            {"id": "page", "type": "container", "text": "Trang"},
            {"id": "h", "type": "heading", "text": "Tiêu đề", "parent": "page"},
            {"id": "A", "type": "node", "x": 10, "y": 10},
            {"id": "B", "type": "node", "x": 90, "y": 10},
        ],
        "rules": [], "interactions": [], "processes": [],
    })
    p = edit_policy_of(mixed)
    assert p["family"] == EditFamily.STRUCTURAL  # structural thắng spatial
    assert "connect" not in p["allowed_ops"]

    # move_along_path thắng TẤT CẢ (kể cả structural)
    mixed_move = _norm({
        **mixed,
        "objects": mixed["objects"] + [{"id": "pkt", "type": "moving_entity"}],
        "processes": [{"type": "move_along_path", "entity": "pkt", "path": ["A", "B"]}],
    })
    assert edit_policy_of(mixed_move)["family"] == EditFamily.OBSERVATION


# ── Enforce ở tầng patch (ẩn UI là KHÔNG đủ) ──────────────────

def _apply(spec, ops):
    return validate_and_apply_patch(spec, {"operations": ops})


def test_structural_them_node_bi_tu_choi_dung_reason_code():
    res = _apply(WEB, [{"op": "add_object", "object": {"id": "P1", "type": "node", "x": 50, "y": 50}}])
    assert res["status"] == "structurally_invalid"
    assert res["reason_code"] == POLICY_OBJECT_TYPE_NOT_ALLOWED
    assert "node" in res["error"]


def test_structural_them_paragraph_duoc_chap_nhan():
    res = _apply(WEB, [{
        "op": "add_object",
        "object": {"id": "p2", "type": "paragraph", "text": "Đoạn văn mới.", "parent": "page"},
    }])
    assert res["status"] == "valid"
    assert any(o["id"] == "p2" for o in res["config"]["objects"])


def test_structural_connect_bi_tu_choi():
    res = _apply(WEB, [{"op": "connect", "from": "h", "to": "p", "edge_id": "e"}])
    assert res["status"] == "structurally_invalid"
    assert res["reason_code"] == POLICY_OPERATION_NOT_ALLOWED


def test_value_only_khong_sua_cau_truc():
    for scene in (GENERIC_LOGIC, GENERIC_BINARY):
        add = _apply(scene, [{"op": "add_object", "object": {"id": "P1", "type": "node"}}])
        assert add["reason_code"] == POLICY_OPERATION_NOT_ALLOWED
        rm = _apply(scene, [{"op": "remove_object", "id": "a" if scene is GENERIC_LOGIC else "b0"}])
        assert rm["reason_code"] == POLICY_OPERATION_NOT_ALLOWED
    # update nhãn vẫn được (vô hại, không đổi cấu trúc)
    ok = _apply(GENERIC_LOGIC, [{"op": "update_object", "id": "a", "fields": {"label": "Công tắc A"}}])
    assert ok["status"] == "valid"


def test_move_along_path_khoa_topology():
    res = _apply(PACKET, [{"op": "add_object", "object": {"id": "r", "type": "node", "node_type": "router"}}])
    assert res["status"] == "structurally_invalid"
    assert res["reason_code"] == POLICY_PATH_TOPOLOGY_LOCKED
    assert "đường" in res["error"]


def test_spatial_van_them_diem_va_noi_duoc():
    """Không regression: cảnh điểm–cạnh giữ nguyên khả năng sửa của M7.14."""
    res = _apply(TRIANGLE, [
        {"op": "add_object", "object": {"id": "D", "type": "node", "label": "D", "x": 50, "y": 90}},
        {"op": "connect", "from": "A", "to": "D", "edge_id": "AD"},
    ])
    assert res["status"] == "valid"
    ids = {o["id"] for o in res["config"]["objects"]}
    assert {"D", "AD"} <= ids


def test_loi_cau_truc_giu_namespace_structure():
    """reason_code hai namespace: id trùng vẫn là structure.*, không phải policy.*"""
    res = _apply(TRIANGLE, [{"op": "add_object", "object": {"id": "A", "type": "node"}}])
    assert res["status"] == "structurally_invalid"
    assert res["reason_code"] == STRUCTURE_INVALID
    assert res["reason_code"].startswith("structure.")


# ── Prompt edit chỉ thấy phạm vi của cảnh ─────────────────────

def test_policy_contract_text_theo_canh():
    web_text = policy_contract_text(WEB)
    assert "add_object" in web_text and "heading" in web_text
    assert "connect" not in web_text

    val_text = policy_contract_text(GENERIC_LOGIC)
    assert "update_object" in val_text
    assert "add_object" not in val_text

    obs_text = policy_contract_text(PACKET)
    assert "update_object" in obs_text and "add_object" not in obs_text
