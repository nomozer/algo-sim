# -*- coding: utf-8 -*-
"""M17 W2A — lock insufficient-structure gate v2 (tín hiệu ĐỊNH DANH NÚT).

Test dùng OUTPUT ANALYZE THẬT ghi từ live run 2 (docs/evaluation/m17/wave2a/
live_smoke.json) — không phải dữ liệu giả định. Đây là điểm mấu chốt: bản v1
(đếm số lượng) cho qua đề trống vì analyze mô tả trừu tượng; v2 đòi quan hệ
giữa hai nút CÓ TÊN.
"""

from __future__ import annotations

import pytest

from app.simulation.error_codes import ErrorCode
from app.simulation.structure_gate import (
    check_tree_structure_sufficiency,
    linked_node_items,
    structure_evidence,
    tree_structure_present,
)

# ── analyze THẬT (live run 2) ─────────────────────────────────
LIVE_INSUFFICIENT = {  # "Mô phỏng duyệt cây preorder." — đề TRỐNG
    "objects": ["cây", "nút (đỉnh) của cây", "cạnh (liên kết) của cây"],
    "data": [{"description": "cây nhị phân"}],
    "relations": ["quan hệ cha-con giữa các nút trong cây"],
}
LIVE_PREORDER = {
    "objects": ["cây", "nút A", "nút B", "nút C", "nút D", "nút E"],
    "data": [],
    "relations": ["A là gốc của cây", "B là con trái của A", "C là con phải của A",
                  "D là con trái của B", "E là con phải của B"],
}
LIVE_INORDER = {
    "objects": ["cây", "nút A", "nút B", "nút C", "nút D"],
    "data": [],
    "relations": ["A là gốc của cây", "B là con trái của A", "C là con phải của A",
                  "D là con trái của B"],
}
LIVE_POSTORDER_EN = {
    "objects": ["tree", "node A", "node B", "node C", "node D"],
    "data": [],
    "relations": ["A là gốc", "A có con trái B", "B có con trái C", "C có con trái D"],
}
LIVE_LEVELORDER = {
    "objects": ["cây", "nút A", "nút B", "nút C"],
    "data": [],
    "relations": ["A là gốc của cây", "B là con của A", "C là con của A"],
}


# ── ĐỀ TRỐNG (live) → gate CHẶN (v1 đã cho qua — hồi quy quan trọng) ──
def test_live_insufficient_bi_chan():
    assert not tree_structure_present(LIVE_INSUFFICIENT)
    v = check_tree_structure_sufficiency(LIVE_INSUFFICIENT)
    assert v is not None and v[0] is ErrorCode.STRUCTURE_INSUFFICIENT


def test_live_insufficient_khong_co_item_hai_dinh_danh():
    # "quan hệ cha-con giữa các nút trong cây" → 0 định danh nút
    assert linked_node_items(LIVE_INSUFFICIENT) == []
    ev = structure_evidence(LIVE_INSUFFICIENT)
    assert ev["relations"] == 1 and ev["linked_items"] == 0 and ev["present"] is False


# ── ĐỀ CÂY THẬT (live 4 case) → gate CHO QUA (không chặn oan) ──
@pytest.mark.parametrize("analysis,name", [
    (LIVE_PREORDER, "preorder"), (LIVE_INORDER, "inorder"),
    (LIVE_POSTORDER_EN, "postorder-en"), (LIVE_LEVELORDER, "level_order"),
])
def test_live_tree_that_khong_bi_chan_oan(analysis, name):
    assert tree_structure_present(analysis), name
    assert check_tree_structure_sufficiency(analysis) is None, name
    ev = structure_evidence(analysis)
    assert ev["linked_items"] >= 1 and len(ev["identifiers"]) >= 2


def test_dinh_danh_trich_dung_tu_quan_he():
    items = linked_node_items(LIVE_PREORDER)
    texts = {i["text"] for i in items}
    assert "B là con trái của A" in texts
    got = next(i for i in items if i["text"] == "B là con trái của A")
    assert got["identifiers"] == ["A", "B"]
    # "A là gốc của cây" chỉ MỘT định danh → không phải bằng chứng quan hệ
    assert "A là gốc của cây" not in texts


# ── ranh giới: hai nhãn RỜI RẠC không có quan hệ → KHÔNG đủ ──
def test_hai_nhan_roi_rac_khong_du():
    a = {"objects": ["nút A", "nút B"], "data": [], "relations": []}
    assert not tree_structure_present(a)  # mỗi item chỉ 1 định danh
    assert check_tree_structure_sufficiency(a) is not None


def test_mot_quan_he_hai_nut_la_du():
    a = {"objects": [], "data": [], "relations": ["B là con trái của A"]}
    assert tree_structure_present(a)


# ── quan hệ đặt ở field khác (data) vẫn được đọc (normalization) ──
def test_quan_he_o_data_van_tinh():
    a = {"objects": [], "relations": [], "data": [{"description": "A có con phải C"}]}
    assert tree_structure_present(a)


def test_quan_he_dang_DICT_co_cau_truc_van_tinh():
    """Analyze có thể trả quan hệ CÓ CẤU TRÚC thay vì prose — phải gộp values
    của MỘT dict thành một item (tách rời thì mỗi mảnh chỉ 1 định danh → chặn
    oan). Đây là adapter normalization, không phải nới tín hiệu."""
    a = {"objects": [], "data": [], "relations": [
        {"type": "left_child", "from": "A", "to": "B"},
    ]}
    assert tree_structure_present(a)
    ev = structure_evidence(a)
    assert ev["identifiers"] == ["A", "B"] and ev["linked_items"] == 1


def test_dict_chi_mot_nut_van_khong_du():
    a = {"objects": [], "data": [], "relations": [{"type": "root", "node": "A"}]}
    assert not tree_structure_present(a)


# ── từ tiếng Việt/Anh dài KHÔNG bị nhầm là định danh ──
def test_tu_thuong_khong_thanh_dinh_danh():
    a = {"objects": ["cây nhị phân", "các nút của cây"], "data": [], "relations": [
        "quan hệ cha con giữa các nút", "the tree has many nodes and children",
    ]}
    assert not tree_structure_present(a)


def test_analysis_rong_hoac_sai_kieu():
    assert not tree_structure_present({})
    assert not tree_structure_present(None)  # type: ignore[arg-type]
    assert structure_evidence(None)["present"] is False  # type: ignore[arg-type]
