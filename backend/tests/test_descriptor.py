"""M14 §C — lock descriptor vocabulary: enum đóng + FamilyMembership immutable."""

from __future__ import annotations

import dataclasses

import pytest

from app.simulation.descriptor import (
    FamilyId,
    FamilyMembership,
    ReachabilityLevel,
    ResultAuthority,
)


def test_result_authority_dong_dung_hai_gia_tri():
    assert {a.value for a in ResultAuthority} == {"computation", "representation"}


def test_reachability_dong_bon_muc():
    assert {r.value for r in ReachabilityLevel} == {
        "registered",
        "library_discoverable",
        "ai_reachable_public",
        "internal_fixture",
    }


def test_family_taxonomy_dong_dung_tam_family():
    assert {f.value for f in FamilyId} == {
        "single_pass_scan",
        "interval_elimination",
        "comparison_sort",
        "boolean_composition",
        "positional_representation",
        "graph_traversal",
        "layered_pdu_transform",
        "structural_progressive_representation",
    }


def test_membership_immutable_va_ho_tro_da_membership_khac_result_authority():
    # generic: cùng target, hai membership, result_authority khác nhau (§C1)
    m_comp = FamilyMembership(FamilyId.BOOLEAN_COMPOSITION, ResultAuthority.COMPUTATION)
    m_repr = FamilyMembership(
        FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION, ResultAuthority.REPRESENTATION
    )
    assert m_comp.result_authority is not m_repr.result_authority
    with pytest.raises(dataclasses.FrozenInstanceError):
        m_comp.variant_id = "x"  # type: ignore[misc]


def test_membership_variant_fields_mac_dinh_none():
    m = FamilyMembership(FamilyId.SINGLE_PASS_SCAN, ResultAuthority.COMPUTATION)
    assert m.variant_id is None
    assert m.family_spec_version is None
    assert m.mechanism_id is None
