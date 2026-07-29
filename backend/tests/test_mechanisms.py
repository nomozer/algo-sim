from app.simulation.descriptor import FamilyId
from app.simulation import mechanisms as M

def test_canonical_id_dung_dang_namespace_va_thuoc_taxonomy():
    for fam, mechs in M.FAMILY_MECHANISMS.items():
        for m in mechs:
            ns, _, name = m.partition(".")
            assert ns == fam.value and name  # đúng "<family_id>.<mechanism>"

def test_alias_mot_chieu_chi_sorting_va_dich_thuoc_taxonomy():
    all_canonical = {m for ms in M.FAMILY_MECHANISMS.values() for m in ms}
    for legacy, canon in M.LEGACY_ALIASES.items():
        assert "." not in legacy                     # nguồn là bare value
        assert canon in all_canonical                # đích ∈ taxonomy
        assert M.mechanism_family(canon) == "comparison_sort"  # không alias ngoài sorting
    assert set(M.LEGACY_ALIASES) == {
        "adjacent_compare_swap", "shift_into_sorted_prefix",
        "select_extreme_repeated", "partition_recursive", "other_unspecified",
    }

def test_canonical_mechanism_normalize_va_passthrough():
    assert M.canonical_mechanism(None) is None
    assert M.canonical_mechanism("none") is None
    assert M.canonical_mechanism("adjacent_compare_swap") == "comparison_sort.adjacent_compare_swap"
    assert M.canonical_mechanism("comparison_sort.adjacent_compare_swap") == "comparison_sort.adjacent_compare_swap"
    assert M.canonical_mechanism("positional_representation.non_binary_base") == "positional_representation.non_binary_base"

def test_intentional_gap_thuoc_taxonomy_va_khong_giao_alias_owned_w1():
    all_canonical = {m for ms in M.FAMILY_MECHANISMS.values() for m in ms}
    assert M.INTENTIONAL_GAP_MECHANISMS <= all_canonical

def test_analyze_exposed_gom_legacy_sorting_none_va_positional():
    vals = M.analyze_exposed_values()
    assert "none" in vals
    assert "adjacent_compare_swap" in vals           # legacy GIỮ NGUYÊN (rev2 điểm 2)
    assert "comparison_sort.adjacent_compare_swap" not in vals  # canonical KHÔNG lộ ra analyze trong M15
    assert "positional_representation.binary_positional_weights" in vals
    assert "positional_representation.non_binary_base" in vals


def test_analyze_exposed_phu_DU_co_che_positional_chong_troi_w3_live_c1():
    """M17 W3-LIVE-C1 — CHỐNG TÁI PHÁT anti-pattern #1.

    Họ positional từng được liệt kê bằng string VIẾT TAY, nên khi W3 thêm
    `character_code_mapping` vào FAMILY_MECHANISMS thì enum analyze không đi
    theo ⇒ Gemini KHÔNG THỂ phát ra cơ chế mà target sở hữu (đúng bệnh
    `_GENERIC_SCHEMA` thiếu `drag`), và mechanism gate không bao giờ thoả mãn
    được nhánh direct-ownership. Khoá: enum phải PHỦ ĐỦ taxonomy."""
    vals = set(M.analyze_exposed_values())
    positional = set(M.FAMILY_MECHANISMS[FamilyId.POSITIONAL_REPRESENTATION])
    assert positional <= vals, f"enum analyze bỏ sót: {sorted(positional - vals)}"
    assert "positional_representation.character_code_mapping" in vals
