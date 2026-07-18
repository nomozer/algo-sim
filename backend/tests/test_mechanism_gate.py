"""M14 Task 6 — lock mechanism-consistency gate (§E4). Test dùng ENUM
prescribed_procedure, KHÔNG text đề → chứng minh không keyword-patch."""

from __future__ import annotations

from app.simulation.error_codes import ErrorCode
from app.simulation.families.sorting import (
    PROC_ADJACENT_SWAP,
    PROC_NONE,
    PROC_PARTITION,
    PROC_SELECT_EXTREME,
    PROC_SHIFT_INSERT,
    SORTING_SELECTOR,
)
from app.simulation.mechanism_gate import (
    check_mechanism_ownership,
    check_variant_consistency,
)


def _an(proc):
    return {"prescribed_procedure": proc}


# ── Tầng 1: ownership ──────────────────────────────────────────
def test_selection_sort_gap():
    res = check_mechanism_ownership(_an(PROC_SELECT_EXTREME), SORTING_SELECTOR)
    assert res is not None and res[0] is ErrorCode.GATE_MECHANISM_OWNERSHIP


def test_quick_sort_gap():
    res = check_mechanism_ownership(_an(PROC_PARTITION), SORTING_SELECTOR)
    assert res is not None and res[0] is ErrorCode.GATE_MECHANISM_OWNERSHIP


def test_other_unspecified_gap():
    res = check_mechanism_ownership(_an("other_unspecified"), SORTING_SELECTOR)
    assert res is not None and res[0] is ErrorCode.GATE_MECHANISM_OWNERSHIP


def test_none_va_null_permissive_khong_gap():
    assert check_mechanism_ownership(_an(PROC_NONE), SORTING_SELECTOR) is None
    assert check_mechanism_ownership(_an(None), SORTING_SELECTOR) is None
    assert check_mechanism_ownership({}, SORTING_SELECTOR) is None  # field vắng


def test_owned_mechanism_qua_tang_1():
    assert check_mechanism_ownership(_an(PROC_ADJACENT_SWAP), SORTING_SELECTOR) is None
    assert check_mechanism_ownership(_an(PROC_SHIFT_INSERT), SORTING_SELECTOR) is None


# ── Tầng 2: variant consistency ────────────────────────────────
def test_variant_khop_co_che_pass():
    assert check_variant_consistency(_an(PROC_ADJACENT_SWAP), SORTING_SELECTOR, "bubble") is None
    assert check_variant_consistency(_an(PROC_SHIFT_INSERT), SORTING_SELECTOR, "insertion") is None


def test_variant_lech_co_che_mismatch():
    # đề đòi shift (insertion) nhưng LLM chọn bubble → mismatch → retry
    res = check_variant_consistency(_an(PROC_SHIFT_INSERT), SORTING_SELECTOR, "bubble")
    assert res is not None and res[0] is ErrorCode.MECHANISM_VARIANT_MISMATCH
    # đề đòi adjacent (bubble) nhưng LLM chọn insertion → mismatch
    res2 = check_variant_consistency(_an(PROC_ADJACENT_SWAP), SORTING_SELECTOR, "insertion")
    assert res2 is not None and res2[0] is ErrorCode.MECHANISM_VARIANT_MISMATCH


def test_variant_khong_ep_co_che_thi_variant_nao_cung_pass():
    assert check_variant_consistency(_an(PROC_NONE), SORTING_SELECTOR, "bubble") is None
    assert check_variant_consistency(_an(None), SORTING_SELECTOR, "insertion") is None


def test_error_codes_dong():
    vals = {c.value for c in ErrorCode}
    assert "gate_mechanism_ownership" in vals
    assert "mechanism_variant_mismatch" in vals
    assert "family_spec_invalid" in vals


# ── M15 Task 4: mã lỗi structured cho E2 nhánh 3 ───────────────
def test_error_code_route_mismatch_ton_tai():
    assert ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH.value == "route_mechanism_family_mismatch"
