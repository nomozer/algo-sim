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
