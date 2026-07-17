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
    field = ANALYZE_SCHEMA["properties"]["prescribed_procedure"]
    assert field["enum"] == list(PRESCRIBED_PROCEDURES)
    assert set(field["enum"]) == {
        PROC_NONE,
        PROC_ADJACENT_SWAP,
        PROC_SHIFT_INSERT,
        PROC_SELECT_EXTREME,
        PROC_PARTITION,
        "other_unspecified",
    }


def test_khong_chua_gia_tri_dang_ket_qua_hay_ten_thuat_toan():
    # §O7: enum mô tả CƠ CHẾ, không chứa result/trace, không tên thuật toán
    field = ANALYZE_SCHEMA["properties"]["prescribed_procedure"]
    banned = {"bubble", "insertion", "selection", "quick", "sorted", "result", "trace", "timeline"}
    for val in field["enum"]:
        assert val not in banned
