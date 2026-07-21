# -*- coding: utf-8 -*-
"""M17-Lite W0 — lock authenticity contract (app/simulation/authenticity.py).

Cross-lock với CATALOG sống ở đây (authenticity.py không import catalog —
chống vòng import, theo pattern mechanisms.py).
"""

from __future__ import annotations

from app.simulation.authenticity import (
    AUTHENTICITY_CONTRACTS,
    authenticity_descriptor,
)
from app.simulation.catalog import CATALOG, capability_descriptors
from app.simulation.descriptor import ReachabilityLevel
from app.simulation.mechanisms import (
    FAMILY_MECHANISMS,
    INTENTIONAL_GAP_MECHANISMS,
)


def _ai_reachable_ids() -> set[str]:
    return {
        sid
        for sid, spec in CATALOG.items()
        if ReachabilityLevel.AI_REACHABLE_PUBLIC in spec.reachability
    }


def _all_mechanisms() -> set[str]:
    return {m for mechs in FAMILY_MECHANISMS.values() for m in mechs}


def test_du_contract_cho_moi_target_ai_reachable():
    """Khóa phủ: đúng 1 contract cho MỖI AI-reachable target — thêm target
    thứ 15 mà quên contract → đỏ (buộc audit phủ theo catalog thật)."""
    assert set(AUTHENTICITY_CONTRACTS) == _ai_reachable_ids()


def test_generic_allowed_duy_nhat_generic_rule_scene():
    for sid, c in AUTHENTICITY_CONTRACTS.items():
        assert c.generic_allowed == (sid == "generic.rule_scene"), sid


def test_state_va_result_fields_khong_rong():
    """Mọi target phải khai state + result authoritative — contract rỗng là
    contract giả (renderer đẹp không thay được authoritative state)."""
    for sid, c in AUTHENTICITY_CONTRACTS.items():
        assert c.required_state_fields, f"{sid}: required_state_fields rỗng"
        assert c.required_result_fields, f"{sid}: required_result_fields rỗng"
        assert c.renderer_semantic_requirements, f"{sid}: renderer requirements rỗng"


def test_near_miss_la_canonical_va_khong_giao_owned():
    """near_miss ⊆ taxonomy canonical, và không target nào khai near-miss một
    cơ chế CHÍNH NÓ sở hữu (mâu thuẫn owned XOR gap)."""
    universe = _all_mechanisms()
    for sid, c in AUTHENTICITY_CONTRACTS.items():
        owned = {
            m
            for mb in CATALOG[sid].family_memberships
            for m in mb.owned_mechanisms
        }
        for nm in c.near_miss_mechanisms:
            assert nm in universe, f"{sid}: near-miss {nm} ngoài taxonomy"
            assert nm not in owned, f"{sid}: near-miss {nm} lại là owned"


def test_moi_intentional_gap_co_it_nhat_mot_near_miss():
    """Mỗi cơ chế trong INTENTIONAL_GAP_MECHANISMS phải xuất hiện ở near_miss
    của ÍT NHẤT một target → audit matrix sinh case gap-trigger cho nó."""
    declared = {
        nm for c in AUTHENTICITY_CONTRACTS.values() for nm in c.near_miss_mechanisms
    }
    missing = INTENTIONAL_GAP_MECHANISMS - declared
    assert not missing, f"intentional gap thiếu near-miss case: {sorted(missing)}"


def test_descriptor_json_nhung_authenticity_moi_target():
    """capability_descriptors() phải nhúng contract cho mọi AI-reachable target
    (sync-lock file JSON đã có ở test_capability_descriptors)."""
    targets = capability_descriptors()["runtime_targets"]
    for sid in _ai_reachable_ids():
        assert targets[sid]["authenticity"] == authenticity_descriptor(sid), sid
        assert targets[sid]["authenticity"] is not None
