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
def test_selection_sort_owned_qua_gate_m17_w1():
    # M17 W1: select_extreme_repeated flip GAP → OWNED (algorithm.selection_sort)
    assert check_mechanism_ownership(_an(PROC_SELECT_EXTREME), SORTING_SELECTOR) is None


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
    assert check_variant_consistency(_an(PROC_SELECT_EXTREME), SORTING_SELECTOR, "selection") is None


def test_variant_selection_lech_co_che_mismatch():
    # đề đòi select_extreme nhưng LLM chọn bubble → mismatch tầng 2 → retry
    res = check_variant_consistency(_an(PROC_SELECT_EXTREME), SORTING_SELECTOR, "bubble")
    assert res is not None and res[0] is ErrorCode.MECHANISM_VARIANT_MISMATCH


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


# ── M15 Task 5: check_mechanism_consistency_for_target (pure, direct route) ──
from app.simulation.catalog import CATALOG
from app.simulation.mechanism_gate import (
    check_mechanism_consistency_for_target as check,
)


def test_T1_non_binary_base_tren_binary_target_la_ownership_gap():
    r = check({"prescribed_procedure": "positional_representation.non_binary_base"},
              CATALOG["binary.decimal_to_binary"])
    assert r is not None and r[0] == ErrorCode.GATE_MECHANISM_OWNERSHIP


def test_T3_sorting_prescribed_tren_binary_target_la_family_mismatch():
    r = check({"prescribed_procedure": "adjacent_compare_swap"},  # legacy → alias
              CATALOG["binary.decimal_to_binary"])
    assert r is not None and r[0] == ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH


def test_positional_tren_binary_search_la_family_mismatch():  # T2 phần pure
    r = check({"prescribed_procedure": "positional_representation.non_binary_base"},
              CATALOG["algorithm.binary_search"])
    assert r is not None and r[0] == ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH


def test_T4_null_va_none_khong_chan_moi_direct_entry():
    for sim_id, spec in CATALOG.items():
        assert check({"prescribed_procedure": None}, spec) is None
        assert check({"prescribed_procedure": "none"}, spec) is None


def test_owned_hop_le_di_tiep():
    r = check({"prescribed_procedure": "positional_representation.binary_positional_weights"},
              CATALOG["binary.decimal_to_binary"])
    assert r is None


# ── M17 W3-LIVE-C1: mã hoá ký tự ─────────────────────────────────
# Root cause ĐO ĐƯỢC (probe live, 3 HTTP): analyze phát `None` (ENC-1/ENC-2) hoặc
# `binary_positional_weights` (ENC-3) — KHÔNG BAO GIỜ phát cơ chế mà W3 sở hữu,
# vì `character_code_mapping` chưa từng nằm trong enum analyze. Cách sửa là NỐI
# cơ chế vào enum (mechanisms.analyze_exposed_values), KHÔNG nới cổng.

W3 = "binary.character_encoding"
MECH_CHAR_MAP = "positional_representation.character_code_mapping"
MECH_NON_BINARY = "positional_representation.non_binary_base"
MECH_BIN_WEIGHTS = "positional_representation.binary_positional_weights"


def test_w3_co_che_so_huu_qua_gate():
    """Cơ chế W3 THẬT SỰ sở hữu phải đi tiếp — nay analyze phát được nó."""
    assert check({"prescribed_procedure": MECH_CHAR_MAP}, CATALOG[W3]) is None


def test_w3_khong_so_huu_co_che_doi_co_so_van_gap():
    """FAIL-CLOSED giữ nguyên: W3 KHÔNG được cấp quyền lên hai cơ chế đổi cơ số.

    `binary_positional_weights` chính là giá trị đo được đang chặn W3 ở live —
    nó VẪN phải gap: cơ chế đó gắn với `decimal_to_binary` (chặn cứng 0–255/8
    bit) nên không chở nổi BMP tới 65535."""
    for mech in (MECH_BIN_WEIGHTS, MECH_NON_BINARY):
        r = check({"prescribed_procedure": mech}, CATALOG[W3])
        assert r is not None and r[0] == ErrorCode.GATE_MECHANISM_OWNERSHIP, mech


def test_w3_owned_metadata_khong_chua_co_che_doi_co_so():
    """Không cấp ownership giả: metadata W3 chỉ có ĐÚNG cơ chế tra bảng mã."""
    owned = {m for mem in CATALOG[W3].family_memberships for m in mem.owned_mechanisms}
    assert owned == {MECH_CHAR_MAP}
    assert MECH_NON_BINARY not in owned
    assert MECH_BIN_WEIGHTS not in owned


def test_w3_co_che_khac_ho_la_family_mismatch():
    for mech in ("relational_table_query.row_predicate_filter",
                 "structural_progressive_representation.reveal_sequence",
                 "tree_traversal.preorder"):
        r = check({"prescribed_procedure": mech}, CATALOG[W3])
        assert r is not None and r[0] == ErrorCode.ROUTE_MECHANISM_FAMILY_MISMATCH, mech


def test_w3_co_che_khong_ton_tai_fail_closed():
    for mech in ("positional_representation.khong_ton_tai", "hoan_toan_bia", ""):
        assert check({"prescribed_procedure": mech}, CATALOG[W3]) is not None, mech


def test_target_khac_khong_doi_hanh_vi():
    """Regression: nối enum KHÔNG được đụng target đã có."""
    assert check({"prescribed_procedure": MECH_NON_BINARY},
                 CATALOG["binary.base_conversion"]) is None
    assert check({"prescribed_procedure": MECH_BIN_WEIGHTS},
                 CATALOG["binary.base_conversion"]) is None
    assert check({"prescribed_procedure": "bounded_control_flow.bounded_loop"},
                 CATALOG["algorithm.bounded_control_flow"]) is None
    assert check({"prescribed_procedure": "relational_table_query.row_predicate_filter"},
                 CATALOG["database.relational_table_query"]) is None
    # W3 KHÔNG được nuốt cơ chế của hàng xóm cùng họ
    r = check({"prescribed_procedure": MECH_CHAR_MAP}, CATALOG["binary.decimal_to_binary"])
    assert r is not None and r[0] == ErrorCode.GATE_MECHANISM_OWNERSHIP


def test_gate_khong_hard_code_target_id():
    """§5.13 — cấm special case theo tên target/tiền tố/từ khoá trong cổng."""
    from pathlib import Path

    import app.simulation.mechanism_gate as gate_mod

    src = Path(gate_mod.__file__).read_text(encoding="utf-8")
    for banned in ("binary.character_encoding", "character_encoding", "binary.",
                   "decimal_to_binary", "base_conversion"):
        assert banned not in src, banned
