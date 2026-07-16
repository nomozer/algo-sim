# -*- coding: utf-8 -*-
"""Test semantic check + Python generic engine (M7 §6, §8).

Một spec đúng cú pháp nhưng SAI HÀNH VI không được tính là thành công.
"""

from app.simulation.generic_engine import build_timeline, initial_base, values_of
from app.simulation.semantic import check_semantic


def _gate(op):
    return {
        "dsl_version": "1.0",
        "title": f"Cổng {op}",
        "objects": [
            {"id": "a", "type": "switch", "value": 0},
            {"id": "b", "type": "switch", "value": 0},
            {"id": "y", "type": "lamp"},
        ],
        "rules": [{"type": "boolean", "op": op, "inputs": ["a", "b"], "target": "y"}],
        "interactions": [{"type": "toggle", "target": "a"}, {"type": "toggle", "target": "b"}],
        "processes": [],
    }


def _nested(rules):
    """Cảnh 3 công tắc + trung gian t + đèn y — rules truyền vào để thử biến thể."""
    return {
        "dsl_version": "1.0",
        "title": "Đèn A và (B hoặc C)",
        "objects": [
            {"id": "sa", "type": "switch", "value": 0},
            {"id": "sb", "type": "switch", "value": 0},
            {"id": "sc", "type": "switch", "value": 0},
            {"id": "t", "type": "lamp", "label": "B hoặc C"},
            {"id": "y", "type": "lamp", "label": "Đèn"},
        ],
        "rules": rules,
        "interactions": [
            {"type": "toggle", "target": "sa"},
            {"type": "toggle", "target": "sb"},
            {"type": "toggle", "target": "sc"},
        ],
        "processes": [],
    }


# Kỳ vọng hợp thành AND(x, OR(y, z)) — lá là placeholder, ánh xạ id-agnostic.
NESTED_AND_OR = {"op": "and", "args": ["x", {"op": "or", "args": ["y", "z"]}]}


# ── Python engine ─────────────────────────────────────────────

def test_engine_xor_truth_table():
    spec = _gate("xor")
    base = initial_base(spec)
    # 00→0
    assert values_of(spec, {**base, "a": 0, "b": 0})["y"] == 0
    # 01→1, 10→1
    assert values_of(spec, {**base, "a": 0, "b": 1})["y"] == 1
    assert values_of(spec, {**base, "a": 1, "b": 0})["y"] == 1
    # 11→0
    assert values_of(spec, {**base, "a": 1, "b": 1})["y"] == 0


def test_engine_weighted_sum():
    spec = {
        "dsl_version": "1.0",
        "title": "wsum",
        "objects": [
            {"id": "b0", "type": "switch", "value": 1, "weight": 8},
            {"id": "b1", "type": "switch", "value": 1, "weight": 4},
            {"id": "b2", "type": "switch", "value": 0, "weight": 2},
            {"id": "b3", "type": "switch", "value": 1, "weight": 1},
            {"id": "out", "type": "value_box"},
        ],
        "rules": [{"type": "weighted_sum", "inputs": ["b0", "b1", "b2", "b3"], "weights": [8, 4, 2, 1], "target": "out"}],
        "interactions": [],
        "processes": [],
    }
    assert values_of(spec, initial_base(spec))["out"] == 13


def test_engine_build_timeline():
    spec = {
        "dsl_version": "1.0",
        "title": "path",
        "objects": [
            {"id": "n1", "type": "node"},
            {"id": "n2", "type": "node"},
            {"id": "n3", "type": "node"},
            {"id": "pkt", "type": "moving_entity"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [{"type": "move_along_path", "entity": "pkt", "path": ["n1", "n2", "n3"]}],
    }
    frames = build_timeline(spec)
    assert [f["entityPos"]["pkt"] for f in frames] == ["n1", "n2", "n3"]


# ── semantic check ────────────────────────────────────────────

def test_semantic_xor_dung():
    ok, detail = check_semantic(_gate("xor"), {"kind": "boolean_gate", "op": "xor"})
    assert ok, detail


def test_semantic_bat_sai_op():
    """§8: spec cú pháp đúng nhưng LLM chọn OR khi cần XOR → semantic FAIL."""
    ok, detail = check_semantic(_gate("or"), {"kind": "boolean_gate", "op": "xor"})
    assert not ok
    assert "op=xor" in detail or "boolean" in detail


def test_semantic_weighted_sum_sai_gia_tri():
    spec = {
        "dsl_version": "1.0",
        "title": "wsum sai",
        "objects": [
            {"id": "b0", "type": "switch", "value": 1, "weight": 8},
            {"id": "b1", "type": "switch", "value": 0, "weight": 4},  # đáng lẽ bật để ra 13
            {"id": "out", "type": "value_box"},
        ],
        "rules": [{"type": "weighted_sum", "inputs": ["b0", "b1"], "weights": [8, 4], "target": "out"}],
        "interactions": [],
        "processes": [],
    }
    ok, _ = check_semantic(spec, {"kind": "weighted_sum", "value": 13})
    assert not ok  # ra 8 ≠ 13


def test_semantic_moving_path():
    spec = {
        "dsl_version": "1.0",
        "title": "p",
        "objects": [
            {"id": "a", "type": "node"},
            {"id": "b", "type": "node"},
            {"id": "c", "type": "node"},
            {"id": "d", "type": "node"},
            {"id": "e", "type": "moving_entity"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [{"type": "move_along_path", "entity": "e", "path": ["a", "b", "c", "d"]}],
    }
    ok, _ = check_semantic(spec, {"kind": "moving_path", "min_len": 4})
    assert ok
    ok2, _ = check_semantic(spec, {"kind": "moving_path", "min_len": 5})
    assert not ok2  # path chỉ 4 nút


# ── reveal / progressive (M7.7) ───────────────────────────────

# Cùng cấu trúc GENERIC_REVEAL_SPEC bên frontend — dùng để kiểm PARITY 2 tầng.
_TRIANGLE = {
    "dsl_version": "1.0",
    "title": "Tam giác ABC",
    "objects": [
        {"id": "A", "type": "node"},
        {"id": "B", "type": "node"},
        {"id": "C", "type": "node"},
        {"id": "AB", "type": "edge", "from": "A", "to": "B"},
        {"id": "AC", "type": "edge", "from": "A", "to": "C"},
        {"id": "BC", "type": "edge", "from": "B", "to": "C"},
    ],
    "rules": [],
    "interactions": [],
    "processes": [
        {"type": "reveal_sequence", "steps": [
            {"objects": ["A", "B"]}, {"objects": ["AB"]}, {"objects": ["C"]},
            {"objects": ["AC"]}, {"objects": ["BC"]},
        ]},
    ],
}


def test_engine_reveal_visibleids_tich_luy_PARITY():
    """visibleIds phải KHỚP CHÍNH XÁC bản TS (parity 2 tầng engine)."""
    frames = build_timeline(_TRIANGLE)
    vis = [f["visibleIds"] for f in frames]
    assert vis[0] == ["A", "B"]
    assert vis[1] == ["A", "B", "AB"]
    assert vis[2] == ["A", "B", "C", "AB"]  # thứ tự theo khai báo object
    assert vis[3] == ["A", "B", "C", "AB", "AC"]
    assert vis[4] == ["A", "B", "C", "AB", "AC", "BC"]


def test_engine_khong_reveal_thi_moi_object_visible():
    spec = _gate("and")  # không process → 1 frame, visible tất cả
    frames = build_timeline(spec)
    assert len(frames) == 1
    assert set(frames[0]["visibleIds"]) == {"a", "b", "y"}


def test_semantic_progressive_reveal_dung():
    ok, detail = check_semantic(_TRIANGLE, {"kind": "progressive_reveal", "min_steps": 4})
    assert ok, detail


def test_semantic_progressive_reveal_khong_co_reveal_thi_fail():
    """Spec hiện toàn bộ ngay (không reveal) → không phải progressive → FAIL."""
    no_reveal = {**_TRIANGLE, "processes": []}
    ok, _ = check_semantic(no_reveal, {"kind": "progressive_reveal", "min_steps": 4})
    assert not ok


# ── M7.13A: role coverage quét interactions + kinds mới ───────

from app.simulation.semantic import roles_covered_by_spec

_TRIANGLE_DRAG = {
    "dsl_version": "1.0",
    "title": "Tam giác kéo được",
    "objects": [
        {"id": "A", "type": "node", "x": 20, "y": 70},
        {"id": "B", "type": "node", "x": 80, "y": 70},
        {"id": "C", "type": "node", "x": 50, "y": 20},
        {"id": "AB", "type": "edge", "from": "A", "to": "B"},
        {"id": "AC", "type": "edge", "from": "A", "to": "C"},
        {"id": "BC", "type": "edge", "from": "B", "to": "C"},
    ],
    "rules": [],
    "interactions": [{"type": "drag", "target": "A"}],
    "processes": [{"type": "reveal_sequence", "steps": [
        {"objects": ["A", "B"]}, {"objects": ["AB"]}, {"objects": ["C"]}, {"objects": ["AC", "BC"]},
    ]}],
}

_WEB_STATIC = {
    "dsl_version": "1.0",
    "title": "Trang web",
    "objects": [
        {"id": "page", "type": "container", "text": "Trang web"},
        {"id": "h", "type": "heading", "text": "Xin chào", "parent": "page"},
        {"id": "p", "type": "paragraph", "text": "Đoạn giới thiệu.", "parent": "page"},
    ],
    "rules": [], "interactions": [], "processes": [],
}


def test_roles_covered_quet_ca_interactions():
    """M7.13A: cảnh node/edge + drag (KHÔNG switch) phải được tính là cover
    'interactive' — trước đây chỉ objects/rules/processes được quét."""
    covered = roles_covered_by_spec(_TRIANGLE_DRAG)
    assert "interactive" in covered
    assert "relational" in covered and "temporal" in covered


def test_static_structural_dung():
    ok, detail = check_semantic(_WEB_STATIC, {"kind": "static_structural"})
    assert ok, detail


def test_static_structural_bat_reveal_gia():
    """Cảnh tĩnh mà spec chèn reveal giả (để 'có nhiều bước') → FAIL."""
    fake = {**_WEB_STATIC, "processes": [{"type": "reveal_sequence", "steps": [
        {"objects": ["h"]}, {"objects": ["p"]},
    ]}]}
    ok, detail = check_semantic(fake, {"kind": "static_structural"})
    assert not ok
    assert "reveal giả" in detail or "diễn biến" in detail


def test_static_structural_can_object_cau_truc():
    gate = _gate("and")
    ok, _ = check_semantic(gate, {"kind": "static_structural"})
    assert not ok


def test_draggable_reveal_dung():
    ok, detail = check_semantic(_TRIANGLE_DRAG, {"kind": "draggable_reveal", "min_steps": 3})
    assert ok, detail


def test_draggable_reveal_thieu_drag_thi_fail():
    no_drag = {**_TRIANGLE_DRAG, "interactions": []}
    ok, detail = check_semantic(no_drag, {"kind": "draggable_reveal", "min_steps": 3})
    assert not ok
    assert "drag" in detail


# ── M11: nested_boolean — kỳ vọng HỢP THÀNH, dò theo NGUỒN ────────────────
# Probe boolean_gate cũ tiêm giá trị vào input của rule; với rule lồng, input
# là TARGET của rule khác nên bị values_of tính đè → âm tính giả. nested_boolean
# chỉ tiêm vào NGUỒN (initial_base) và so bảng chân trị hợp thành tại sink.

def test_nested_boolean_dung_toan_bo_bang_chan_tri():
    spec = _nested([
        {"type": "boolean", "op": "or", "inputs": ["sb", "sc"], "target": "t"},
        {"type": "boolean", "op": "and", "inputs": ["sa", "t"], "target": "y"},
    ])
    ok, detail = check_semantic(spec, {"kind": "nested_boolean", "expr": NESTED_AND_OR})
    assert ok, detail


def test_nested_boolean_id_agnostic_hoan_vi_nguon():
    """Biến phân biệt (x) là sc chứ không phải sa — ánh xạ phải tự tìm ra."""
    spec = _nested([
        {"type": "boolean", "op": "or", "inputs": ["sa", "sb"], "target": "t"},
        {"type": "boolean", "op": "and", "inputs": ["sc", "t"], "target": "y"},
    ])
    ok, detail = check_semantic(spec, {"kind": "nested_boolean", "expr": NESTED_AND_OR})
    assert ok, detail


def test_nested_boolean_doc_lap_thu_tu_khai_bao_rule():
    """Rule AND khai TRƯỚC rule OR nuôi nó — điểm bất động vẫn hội tụ đúng."""
    spec = _nested([
        {"type": "boolean", "op": "and", "inputs": ["sa", "t"], "target": "y"},
        {"type": "boolean", "op": "or", "inputs": ["sb", "sc"], "target": "t"},
    ])
    ok, detail = check_semantic(spec, {"kind": "nested_boolean", "expr": NESTED_AND_OR})
    assert ok, detail


def test_nested_boolean_sai_logic_bi_fail():
    """OR ở cả hai tầng ≠ AND(x, OR(y,z)) → phải trượt bảng chân trị."""
    spec = _nested([
        {"type": "boolean", "op": "or", "inputs": ["sb", "sc"], "target": "t"},
        {"type": "boolean", "op": "or", "inputs": ["sa", "t"], "target": "y"},
    ])
    ok, _ = check_semantic(spec, {"kind": "nested_boolean", "expr": NESTED_AND_OR})
    assert not ok


def test_nested_boolean_spec_phang_khong_phai_composition():
    """Một rule AND 3 đầu vào phẳng: không có chuỗi rule → FAIL cấu trúc."""
    flat = _nested([
        {"type": "boolean", "op": "and", "inputs": ["sa", "sb", "sc"], "target": "y"},
    ])
    ok, detail = check_semantic(flat, {"kind": "nested_boolean", "expr": NESTED_AND_OR})
    assert not ok
    assert "chuỗi" in detail or "composition" in detail.lower() or "rule" in detail.lower()


def test_nested_boolean_bo_qua_object_trang_tri_co_value():
    """Đo live (M11 baseline): LLM thỉnh thoảng gắn value=0 cho label/đèn trang
    trí → probe đếm 'mọi object có value' ra 7 nguồn thay vì 3 (âm tính giả).
    Nguồn của bảng chân trị phải là ĐẦU VÀO HỌC SINH ĐIỀU KHIỂN — target của
    toggle khai trong spec."""
    spec = _nested([
        {"type": "boolean", "op": "or", "inputs": ["sb", "sc"], "target": "t"},
        {"type": "boolean", "op": "and", "inputs": ["sa", "t"], "target": "y"},
    ])
    spec["objects"] = spec["objects"] + [
        {"id": f"lbl{i}", "type": "label", "label": f"nhãn {i}", "value": 0}
        for i in range(4)
    ]
    ok, detail = check_semantic(spec, {"kind": "nested_boolean", "expr": NESTED_AND_OR})
    assert ok, detail


def test_nested_boolean_not_bien_the():
    """AND(x, NOT y) — 2 nguồn, dùng op not có thật trong manifest."""
    spec = {
        "dsl_version": "1.0",
        "title": "A và không B",
        "objects": [
            {"id": "sa", "type": "switch", "value": 0},
            {"id": "sb", "type": "switch", "value": 0},
            {"id": "t", "type": "lamp", "label": "không B"},
            {"id": "y", "type": "lamp"},
        ],
        "rules": [
            {"type": "boolean", "op": "not", "inputs": ["sb"], "target": "t"},
            {"type": "boolean", "op": "and", "inputs": ["sa", "t"], "target": "y"},
        ],
        "interactions": [{"type": "toggle", "target": "sa"}, {"type": "toggle", "target": "sb"}],
        "processes": [],
    }
    expr = {"op": "and", "args": ["x", {"op": "not", "args": ["y"]}]}
    ok, detail = check_semantic(spec, {"kind": "nested_boolean", "expr": expr})
    assert ok, detail
