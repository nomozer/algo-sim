"""M15 Task 12 (W2) — proof: family single_pass_scan ĐÃ formalize KHÔNG selector.

ScanSpec (algorithm.scan, M12) là bounded/versioned family-spec — interpreter FE
(core/scan.ts) sở hữu vòng lặp/điểm dừng, không phải LLM. Wave này chỉ khai
`owned_mechanisms` cho 6 entry sẵn có + đưa SINGLE_PASS_SCAN vào FORMALIZED_FAMILIES
(K1 Task 3) — KHÔNG thêm FamilySelector (5 bài chuyên biệt vẫn là choice độc lập
trên menu classify, scan là catch-all trong-family), KHÔNG spec mới, KHÔNG predict.
"""

from __future__ import annotations


def test_scan_spec_da_bounded_versioned_khong_can_spec_moi():
    from app.simulation.catalog import CATALOG
    from app.simulation.scan_engine import SCAN_VERSION

    spec = CATALOG["algorithm.scan"]
    assert spec.config_contract_version == "scan-1.0"
    assert spec.config_schema["properties"]["scan_version"]["enum"] == [SCAN_VERSION]


def test_khong_selector_cho_single_pass_scan():
    from app.simulation.families import FAMILY_SELECTORS

    assert "single_pass_scan" not in FAMILY_SELECTORS  # khóa 10


def test_6_entry_scan_owned_canonical_va_menu_khong_doi():
    from app.simulation.catalog import CATALOG, llm_choices

    ids = [
        "algorithm.find_max", "algorithm.find_min", "algorithm.sum_if",
        "algorithm.count_if", "algorithm.linear_search", "algorithm.scan",
    ]
    for sim_id in ids:
        mems = [
            m for m in CATALOG[sim_id].family_memberships
            if m.family_id.value == "single_pass_scan"
        ]
        assert mems and mems[0].owned_mechanisms
        assert sim_id in llm_choices()          # direct surface GIỮ NGUYÊN

    # scan = catch-all trong-family: owned = TOÀN BỘ không gian family (derived,
    # không hand-written), không phải một cơ chế riêng như 5 bài chuyên biệt.
    from app.simulation.descriptor import FamilyId
    from app.simulation.mechanisms import FAMILY_MECHANISMS

    scan_owned = [
        m for m in CATALOG["algorithm.scan"].family_memberships
        if m.family_id.value == "single_pass_scan"
    ][0].owned_mechanisms
    assert set(scan_owned) == set(FAMILY_MECHANISMS[FamilyId.SINGLE_PASS_SCAN])


def test_scan_khong_khai_predict_o_catalog():
    """`predict` là capability FE-only (SimulationModule.predict) — BE (SimSpec)
    không có field này ở bất kỳ entry nào, scan không phải ngoại lệ. Khóa THẬT của
    "algorithm.scan không predict" nằm ở FE:
    frontend/src/simulations/domains/algorithm/scan-module.test.ts
    (`mod!.predict` phải là `undefined`) — Task 12 thêm assert đó nếu vitest chưa có."""
    from app.simulation.catalog import CATALOG

    spec = CATALOG["algorithm.scan"]
    assert not hasattr(spec, "predict")
