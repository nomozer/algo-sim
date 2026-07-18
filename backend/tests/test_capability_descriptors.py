"""M14 Task 3 — sync-lock capability-descriptors.json (§C4): đổi metadata mà quên
chạy generate_capability_descriptors.py → test ĐỎ (khuôn dsl-contract.json)."""

from __future__ import annotations

import json
from pathlib import Path

from app.simulation.catalog import capability_descriptors

_JSON = (
    Path(__file__).resolve().parents[2]
    / "frontend/src/simulations/capability-descriptors.json"
)


def test_descriptor_json_khong_troi_khoi_nguon():
    committed = json.loads(_JSON.read_text(encoding="utf-8"))
    assert committed == capability_descriptors()


def test_cau_truc_co_ban():
    d = capability_descriptors()
    assert len(d["runtime_targets"]) == 14
    assert "comparison_sort" in d["family_selectors"]
    token = d["family_selectors"]["comparison_sort"]["selector_token"]
    # token selector KHÔNG được là một runtime target
    assert token not in d["runtime_targets"]
    assert token in d["llm_choices"]
    assert "algorithm.bubble_sort" not in d["llm_choices"]


def test_artifact_mang_owned_va_version_moi_entry():
    from app.simulation.catalog import capability_descriptors
    d = capability_descriptors()
    for sim_id, t in d["runtime_targets"].items():
        assert "config_contract_version" in t and t["config_contract_version"]
        for mem in t["family_memberships"]:
            assert "owned_mechanisms" in mem  # có thể () trước W2–W4, nhưng field phải tồn tại


def test_analyze_exposed_owned_xor_intentional_gap():
    """Khóa 2 — đúng MỘT trong hai, không giá trị mồ côi."""
    from app.simulation.catalog import CATALOG
    from app.simulation.families import FAMILY_SELECTORS
    from app.simulation import mechanisms as M
    owned_everywhere = set()
    for spec in CATALOG.values():
        for mem in spec.family_memberships:
            owned_everywhere |= set(mem.owned_mechanisms)
    for sel in FAMILY_SELECTORS.values():
        owned_everywhere |= set(sel.owned_mechanisms)
    for raw in M.analyze_exposed_values():
        canon = M.canonical_mechanism(raw)
        if canon is None:
            continue  # "none"
        is_owned = canon in owned_everywhere
        is_gap = canon in M.INTENTIONAL_GAP_MECHANISMS
        assert is_owned != is_gap, f"{raw}→{canon}: owned={is_owned} gap={is_gap} (phải đúng MỘT)"


def test_formalized_families_owned_khong_rong():
    """K1 theo pha — family đã formalize thì membership tương ứng owned ≠ ()."""
    from app.simulation.catalog import CATALOG
    from app.simulation.mechanisms import FORMALIZED_FAMILIES
    for spec in CATALOG.values():
        for mem in spec.family_memberships:
            if mem.family_id in FORMALIZED_FAMILIES:
                assert mem.owned_mechanisms, f"{spec.simulation_id}/{mem.family_id.value}"
