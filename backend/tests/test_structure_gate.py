# -*- coding: utf-8 -*-
"""M17 W2A — lock insufficient-structure gate (chống LLM bịa cây).

Deterministic given analyze output: đề duyệt cây KHÔNG có cấu trúc → refuse;
đề có nút + quan hệ → pass. Bất đối xứng: chỉ chặn khi tín hiệu cấu trúc
HOÀN TOÀN vắng (chống chặn oan cây thật).
"""

from __future__ import annotations

from app.simulation.error_codes import ErrorCode
from app.simulation.structure_gate import (
    check_tree_structure_sufficiency,
    tree_structure_present,
)


def _an(objects=None, data=None, relations=None):
    return {
        "objects": objects if objects is not None else [],
        "data": data if data is not None else [],
        "relations": relations if relations is not None else [],
        "goal": "Duyệt cây", "result_ownership": "provided",
    }


# ── THIẾU cấu trúc → gate bắn ──
def test_trong_rong_thieu():
    assert not tree_structure_present(_an())
    v = check_tree_structure_sufficiency(_an())
    assert v is not None and v[0] is ErrorCode.STRUCTURE_INSUFFICIENT


def test_chi_tu_chung_cay_van_thieu():
    # objects chỉ có từ chung "cây" — KHÔNG phải nút cụ thể
    assert not tree_structure_present(_an(objects=["cây"], data=[{"description": "cây nhị phân"}]))
    assert check_tree_structure_sufficiency(_an(objects=["cây"])) is not None


# ── ĐỦ cấu trúc → gate KHÔNG bắn (chống chặn oan) ──
def test_co_relations_du():
    a = _an(relations=[{"type": "parent-child", "from": "A", "to": "B"}])
    assert tree_structure_present(a)
    assert check_tree_structure_sufficiency(a) is None


def test_co_nhieu_object_cu_the_du():
    a = _an(objects=["A", "B", "C", "D"])
    assert tree_structure_present(a)
    assert check_tree_structure_sufficiency(a) is None


def test_co_nhieu_data_cu_the_du():
    a = _an(data=[{"description": "nút A gốc"}, {"description": "nút B con trái"}])
    assert tree_structure_present(a)
    assert check_tree_structure_sufficiency(a) is None


def test_mot_object_cu_the_van_thieu():
    # chỉ một nút cụ thể → chưa đủ thành cây (cần ≥2 hoặc quan hệ)
    assert not tree_structure_present(_an(objects=["cây", "A"]))
