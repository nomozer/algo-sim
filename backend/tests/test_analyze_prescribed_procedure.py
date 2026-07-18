"""M14 Task 4 — lock prescribed_procedure trong ANALYZE_SCHEMA (§E4, nullable, enum đóng)."""

from __future__ import annotations

from app.ai.pipeline import ANALYZE_SCHEMA
from app.simulation.families.sorting import (
    PRESCRIBED_PROCEDURES,
    PROC_ADJACENT_SWAP,
    PROC_NONE,
    PROC_PARTITION,
    PROC_SELECT_EXTREME,
    PROC_SHIFT_INSERT,
)


def test_field_ton_tai_nullable_khong_bat_buoc():
    props = ANALYZE_SCHEMA["properties"]
    assert "prescribed_procedure" in props
    field = props["prescribed_procedure"]
    assert field["type"] == "STRING"
    assert field.get("nullable") is True
    # KHÔNG nằm trong required (không phá analyze domain khác — N7)
    assert "prescribed_procedure" not in ANALYZE_SCHEMA["required"]


def test_enum_dong_dung_sau_gia_tri():
    # M15 Task 7: enum giờ dẫn xuất từ analyze_exposed_values() (superset của
    # PRESCRIBED_PROCEDURES legacy sorting + giá trị positional mới) — vẫn ĐÓNG,
    # legacy sorting giữ nguyên giá trị (rev2 điểm 2).
    field = ANALYZE_SCHEMA["properties"]["prescribed_procedure"]
    assert set(PRESCRIBED_PROCEDURES) <= set(field["enum"])
    assert set(field["enum"]) == {
        PROC_NONE,
        PROC_ADJACENT_SWAP,
        PROC_SHIFT_INSERT,
        PROC_SELECT_EXTREME,
        PROC_PARTITION,
        "other_unspecified",
        "positional_representation.binary_positional_weights",
        "positional_representation.non_binary_base",
    }


def test_khong_chua_gia_tri_dang_ket_qua_hay_ten_thuat_toan():
    # §O7: enum mô tả CƠ CHẾ, không chứa result/trace, không tên thuật toán
    field = ANALYZE_SCHEMA["properties"]["prescribed_procedure"]
    banned = {"bubble", "insertion", "selection", "quick", "sorted", "result", "trace", "timeline"}
    for val in field["enum"]:
        assert val not in banned


def test_analyze_schema_enum_dan_xuat_tu_mechanisms():
    from app.ai.pipeline import ANALYZE_SCHEMA
    from app.simulation.mechanisms import analyze_exposed_values
    assert ANALYZE_SCHEMA["properties"]["prescribed_procedure"]["enum"] == list(analyze_exposed_values())


def test_enum_giu_legacy_sorting_va_co_positional():
    from app.ai.pipeline import ANALYZE_SCHEMA
    e = ANALYZE_SCHEMA["properties"]["prescribed_procedure"]["enum"]
    assert "adjacent_compare_swap" in e and "positional_representation.non_binary_base" in e
