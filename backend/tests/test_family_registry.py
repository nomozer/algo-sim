"""M14 Task 2 — lock family_memberships (14 entry) + FAMILY_SELECTORS + llm_choices + cross-lock (§C1–C4)."""

from __future__ import annotations

from app.simulation.catalog import CATALOG, llm_choices
from app.simulation.descriptor import FamilyId, FamilyMembership, ResultAuthority
from app.simulation.families import (
    FAMILY_SELECTORS,
    cross_lock_violations,
    selector_for_token,
)
from app.simulation.families.base import FamilySelector, VariantSpec
from app.simulation.families import _selector_internal_violations

VALID_FAMILY_IDS = {f.value for f in FamilyId}


def test_catalog_van_14_runtime_target():
    assert len(CATALOG) == 14


def test_moi_entry_co_metadata_descriptor_day_du():
    for sim_id, spec in CATALOG.items():
        assert spec.family_memberships, f"{sim_id} thiếu family_memberships"
        assert spec.curriculum_anchor.strip(), f"{sim_id} thiếu curriculum_anchor (§O2)"
        assert spec.reachability, f"{sim_id} thiếu reachability"
        assert spec.executor_id == sim_id
        for m in spec.family_memberships:
            assert m.family_id.value in VALID_FAMILY_IDS


def test_generic_co_hai_membership_khac_result_authority():
    gen = CATALOG["generic.rule_scene"]
    auth = {m.result_authority for m in gen.family_memberships}
    assert auth == {ResultAuthority.COMPUTATION, ResultAuthority.REPRESENTATION}


def test_cross_lock_khong_vi_pham():
    assert cross_lock_violations(CATALOG) == []


def test_llm_choices_an_sort_concrete_hien_selector_token():
    choices = llm_choices()
    assert "algorithm.comparison_sort" in choices
    assert "algorithm.bubble_sort" not in choices
    assert "algorithm.insertion_sort" not in choices
    # các choice độc lập vẫn còn
    for keep in ("generic.rule_scene", "logic.and_gate", "algorithm.scan",
                 "binary.decimal_to_binary", "network.packet_routing",
                 "network.protocol_encapsulation", "algorithm.find_max"):
        assert keep in choices
    # 14 target − 2 sort ẩn + 1 selector token = 13
    assert len(choices) == 13
    assert len(choices) == len(set(choices))  # không trùng


def test_selector_token_khong_trung_simulation_id():
    for sel in FAMILY_SELECTORS.values():
        assert sel.selector_token not in CATALOG
    assert selector_for_token("algorithm.comparison_sort") is not None
    assert selector_for_token("khong-ton-tai") is None


def test_bubble_insertion_van_la_runtime_target_trong_catalog():
    # quyết định 6/8: concrete runtime targets GIỮ NGUYÊN trong CATALOG
    assert "algorithm.bubble_sort" in CATALOG
    assert "algorithm.insertion_sort" in CATALOG


def test_duplicate_variant_bi_phat_hien():
    bad = FamilySelector(
        family_id=FamilyId.COMPARISON_SORT,
        selector_token="algorithm.comparison_sort",
        family_spec_version="sort-fam-1",
        owned_mechanisms=("adjacent_compare_swap",),
        variants=(
            VariantSpec("bubble", "algorithm.bubble_sort", "adjacent_compare_swap"),
            VariantSpec("bubble", "algorithm.bubble_sort", "adjacent_compare_swap"),
        ),
    )
    violations = _selector_internal_violations(bad)
    assert any("variant trùng" in v for v in violations)


def test_mechanism_ngoai_owned_bi_phat_hien():
    bad = FamilySelector(
        family_id=FamilyId.COMPARISON_SORT,
        selector_token="algorithm.comparison_sort",
        family_spec_version="sort-fam-1",
        owned_mechanisms=("adjacent_compare_swap",),
        variants=(VariantSpec("selection", "algorithm.bubble_sort", "select_extreme_repeated"),),
    )
    violations = _selector_internal_violations(bad)
    assert any("∉ owned_mechanisms" in v for v in violations)


def test_cross_lock_phat_hien_target_thieu_membership():
    # selector trỏ tới target không có membership khớp → vi phạm
    class _FakeSpec:
        family_memberships: tuple = ()
    fake_catalog = {"algorithm.bubble_sort": _FakeSpec(), "algorithm.insertion_sort": _FakeSpec()}
    violations = cross_lock_violations(fake_catalog)
    assert any("thiếu membership" in v for v in violations)
