# -*- coding: utf-8 -*-
"""Test SimulationPatch v1 (M7.14A) — validate + apply tăng dần.

Khóa: ops tuần tự trên BẢN SAO; fail bất kỳ bước nào → spec gốc NGUYÊN VẸN;
cascade rõ ràng cho dependents thuần hình; REJECT dependents ngữ nghĩa;
full validator + guard tiến trình + engine smoke là chốt chặn cuối.
"""

import copy

from app.simulation.dsl.validator import validate_generic_config
from app.simulation.patch import MAX_OPS, validate_and_apply_patch


def _norm(raw: dict) -> dict:
    cfg, err = validate_generic_config(raw)
    assert err is None, err
    return cfg


TRIANGLE = _norm({
    "dsl_version": "1.0",
    "title": "Tam giác ABC",
    "objects": [
        {"id": "A", "type": "node", "x": 20, "y": 70},
        {"id": "B", "type": "node", "x": 80, "y": 70},
        {"id": "C", "type": "node", "x": 50, "y": 20},
        {"id": "AB", "type": "edge", "from": "A", "to": "B"},
        {"id": "AC", "type": "edge", "from": "A", "to": "C"},
        {"id": "BC", "type": "edge", "from": "B", "to": "C"},
    ],
    "rules": [],
    "interactions": [{"type": "drag", "target": "C"}],
    "processes": [{"type": "reveal_sequence", "steps": [
        {"objects": ["A", "B"]}, {"objects": ["AB"]}, {"objects": ["C"]}, {"objects": ["AC", "BC"]},
    ]}],
})

AND_GATE = _norm({
    "dsl_version": "1.0",
    "title": "Cổng AND",
    "objects": [
        {"id": "a", "type": "switch", "value": 0},
        {"id": "b", "type": "switch", "value": 0},
        {"id": "y", "type": "lamp"},
    ],
    "rules": [{"type": "boolean", "op": "and", "inputs": ["a", "b"], "target": "y"}],
    "interactions": [{"type": "toggle", "target": "a"}, {"type": "toggle", "target": "b"}],
    "processes": [],
})


def _apply(spec, ops):
    return validate_and_apply_patch(spec, {"operations": ops})


# ── A. Patch validation ───────────────────────────────────────

def test_add_node_va_connect_tuan_tu_trong_mot_patch():
    """Case sống còn: 'thêm D và nối D với A, B' — op sau thấy kết quả op trước."""
    snapshot = copy.deepcopy(TRIANGLE)
    res = _apply(TRIANGLE, [
        {"op": "add_object", "object": {"id": "D", "type": "node", "label": "D", "x": 50, "y": 90}},
        {"op": "connect", "from": "A", "to": "D", "edge_id": "AD"},
        {"op": "connect", "from": "B", "to": "D", "edge_id": "BD", "label": "BD"},
    ])
    assert res["status"] == "valid"
    ids = {o["id"] for o in res["config"]["objects"]}
    assert {"D", "AD", "BD"} <= ids
    bd = next(o for o in res["config"]["objects"] if o["id"] == "BD")
    assert bd["from"] == "B" and bd["to"] == "D" and bd["label"] == "BD"
    assert TRIANGLE == snapshot  # spec gốc nguyên vẹn tuyệt đối


def test_add_id_trung_bi_reject():
    res = _apply(TRIANGLE, [{"op": "add_object", "object": {"id": "A", "type": "node"}}])
    assert res["status"] == "structurally_invalid"
    assert "đã tồn tại" in res["error"]


def test_connect_endpoint_khong_ton_tai_bi_reject():
    res = _apply(TRIANGLE, [{"op": "connect", "from": "A", "to": "Z", "edge_id": "AZ"}])
    assert res["status"] == "structurally_invalid"
    assert "tồn tại" in res["error"]


def test_add_object_type_la_bi_chan():
    """M7.14D: type ngoài manifest bị EditPolicy chặn TRƯỚC (không nằm trong
    addable_types). Bỏ qua policy → validator nguồn chân lý vẫn là chốt cuối."""
    res = _apply(TRIANGLE, [{"op": "add_object", "object": {"id": "X", "type": "hexagon"}}])
    assert res["status"] == "structurally_invalid"
    assert res["reason_code"] == "policy.object_type_not_allowed"

    raw = validate_and_apply_patch(
        TRIANGLE, {"operations": [{"op": "add_object", "object": {"id": "X", "type": "hexagon"}}]},
        enforce_policy=False,
    )
    assert raw["status"] == "structurally_invalid"
    assert raw["reason_code"] == "structure.invalid"
    assert "type" in raw["error"].lower()


def test_qua_10_ops_bi_reject():
    ops = [{"op": "add_object", "object": {"id": f"N{i}", "type": "node"}} for i in range(MAX_OPS + 1)]
    res = _apply(TRIANGLE, ops)
    assert res["status"] == "structurally_invalid"


def test_patch_fail_giua_chung_khong_mutate_spec():
    """Op 1 hợp lệ, op 2 hỏng → KHÔNG có gì được áp (spec gốc không đổi)."""
    snapshot = copy.deepcopy(TRIANGLE)
    res = _apply(TRIANGLE, [
        {"op": "add_object", "object": {"id": "D", "type": "node"}},
        {"op": "connect", "from": "D", "to": "Zzz", "edge_id": "DZ"},
    ])
    assert res["status"] == "structurally_invalid"
    assert TRIANGLE == snapshot
    assert "config" not in res


# ── B. Remove: cascade thuần hình vs reject ngữ nghĩa ─────────

def test_remove_node_cascade_edges_interactions_reveal():
    res = _apply(TRIANGLE, [{"op": "remove_object", "id": "C"}])
    assert res["status"] == "valid"
    ids = {o["id"] for o in res["config"]["objects"]}
    assert "C" not in ids and "AC" not in ids and "BC" not in ids  # edges cascade
    assert all(it["target"] != "C" for it in res["config"]["interactions"])  # drag C bị gỡ
    for p in res["config"]["processes"]:
        for st in p["steps"]:
            assert "C" not in st["objects"] and "AC" not in st["objects"]
            assert st["objects"]  # không còn step rỗng


def test_remove_object_dinh_rule_bi_reject():
    """Dependents NGỮ NGHĨA không cascade mù: switch là input của rule.

    M7.14D: cảnh switch/lamp là VALUE_ONLY nên EditPolicy chặn remove TRƯỚC
    (reason_code policy.*). Luật dependents vẫn là chốt chặn độc lập — kiểm
    bằng cách bỏ qua policy."""
    res = _apply(AND_GATE, [{"op": "remove_object", "id": "a"}])
    assert res["status"] == "structurally_invalid"
    assert res["reason_code"] == "policy.operation_not_allowed"

    raw = validate_and_apply_patch(
        AND_GATE, {"operations": [{"op": "remove_object", "id": "a"}]}, enforce_policy=False,
    )
    assert raw["status"] == "structurally_invalid"
    assert "rule" in raw["error"]


def test_remove_entity_hoac_path_node_bi_reject():
    packet = _norm({
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
    assert _apply(packet, [{"op": "remove_object", "id": "pkt"}])["status"] == "structurally_invalid"
    assert _apply(packet, [{"op": "remove_object", "id": "c"}])["status"] == "structurally_invalid"


def test_remove_container_con_con_bi_reject():
    web = _norm({
        "dsl_version": "1.0", "title": "Trang",
        "objects": [
            {"id": "page", "type": "container", "text": "Trang"},
            {"id": "h", "type": "heading", "text": "Tiêu đề", "parent": "page"},
            {"id": "footer", "type": "text", "text": "Chân trang"},
        ],
        "rules": [], "interactions": [], "processes": [],
    })
    res = _apply(web, [{"op": "remove_object", "id": "page"}])
    assert res["status"] == "structurally_invalid"
    assert "con" in res["error"]
    # xóa con trước rồi xóa container trong CÙNG patch → hợp lệ (footer còn lại)
    res2 = _apply(web, [{"op": "remove_object", "id": "h"}, {"op": "remove_object", "id": "page"}])
    assert res2["status"] == "valid"
    assert [o["id"] for o in res2["config"]["objects"]] == ["footer"]
    # nhưng xóa đến mức spec RỖNG thì validator sàn 1–20 object chặn lại
    res3 = _apply(web, [
        {"op": "remove_object", "id": "h"},
        {"op": "remove_object", "id": "page"},
        {"op": "remove_object", "id": "footer"},
    ])
    assert res3["status"] == "structurally_invalid"


def test_xoa_het_object_reveal_lam_mat_tien_trinh_bi_guard_chan():
    """Xóa nhiều tới mức reveal rỗng → cảnh progressive mất diễn biến → reject
    (bảo toàn scene_mode — không cần plan, suy từ chính spec)."""
    mini = _norm({
        "dsl_version": "1.0", "title": "Hai điểm",
        "objects": [
            {"id": "A", "type": "node"}, {"id": "B", "type": "node"},
            {"id": "bg", "type": "label", "label": "nền"},
        ],
        "rules": [], "interactions": [],
        "processes": [{"type": "reveal_sequence", "steps": [{"objects": ["A"]}, {"objects": ["B"]}]}],
    })
    res = _apply(mini, [{"op": "remove_object", "id": "A"}, {"op": "remove_object", "id": "B"}])
    assert res["status"] == "structurally_invalid"
    assert "tiến trình" in res["error"]


# ── C. update / disconnect ────────────────────────────────────

def test_update_object_chi_fields_allowlist():
    res = _apply(TRIANGLE, [{"op": "update_object", "id": "A", "fields": {"x": 30, "label": "A'"}}])
    assert res["status"] == "valid"
    a = next(o for o in res["config"]["objects"] if o["id"] == "A")
    assert a["x"] == 30 and a["label"] == "A'"
    # đổi cấu trúc qua update bị chặn với hướng dẫn remove+add
    res2 = _apply(TRIANGLE, [{"op": "update_object", "id": "AB", "fields": {"from": "C"}}])
    assert res2["status"] == "structurally_invalid"
    assert "remove + add" in res2["error"]


def test_disconnect_dung_edge():
    res = _apply(TRIANGLE, [{"op": "disconnect", "edge_id": "BC"}])
    assert res["status"] == "valid"
    ids = {o["id"] for o in res["config"]["objects"]}
    assert "BC" not in ids and {"A", "B", "C", "AB", "AC"} <= ids
    # disconnect một node (không phải edge) → reject
    res2 = _apply(TRIANGLE, [{"op": "disconnect", "edge_id": "A"}])
    assert res2["status"] == "structurally_invalid"


def test_patch_khong_operations_bi_reject():
    assert validate_and_apply_patch(TRIANGLE, {})["status"] == "structurally_invalid"
    assert validate_and_apply_patch(TRIANGLE, {"operations": []})["status"] == "structurally_invalid"
    assert validate_and_apply_patch(TRIANGLE, "x")["status"] == "structurally_invalid"
