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
    assert len(d["runtime_targets"]) == 22  # W2A +tree.traversal · W2B +database.relational_table_query · W2C +algorithm.bounded_control_flow
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


# ── M17 P0 — khả năng 2D/3D là MỘT nguồn ────────────────────────────────
#
# Audit authenticity phát hiện: catalog khai cứng visual_mode="2d" cho cả 22
# entry, kể cả hai target thật sự render 3D ⇒ bảng năng lực sinh tự động báo
# 3D = 0/22 và tự phản chứng tên đề tài "2D/3D". Nay `visual_modes` là nguồn,
# `visual_mode` (payload API) dẫn xuất. Parity phía FE: capability-descriptors.test.ts.

# W4B-2R: MOT target 3D, khong phai hai. `packet_routing` chuyen 2D_ONLY vi
# chinh module frontend khai `threeD.role = "architectural_poc"` — Z chi la bo
# cuc, khong mang nghia khai niem. Con lai dung bai ma chieu sau CHO NGHIA:
# Z = tang giao thuc.
TARGETS_3D = {"network.protocol_encapsulation"}


def test_dung_mot_target_ho_tro_3d():
    from app.simulation.catalog import CATALOG
    assert {k for k, s in CATALOG.items() if s.supports_3d()} == TARGETS_3D


def test_target_chi_2d_khong_bi_khai_3d():
    from app.simulation.catalog import CATALOG
    for sim_id, spec in CATALOG.items():
        if sim_id not in TARGETS_3D:
            assert spec.visual_modes == ("2d",), sim_id


def test_visual_mode_payload_luon_dan_xuat_khong_khai_tay():
    """Không thể tồn tại entry vừa khai 3d vừa có scalar mâu thuẫn."""
    from app.simulation.catalog import CATALOG
    for spec in CATALOG.values():
        assert spec.visual_mode == spec.visual_modes[0] == "2d"


def test_visual_modes_thuoc_tu_vung_dong():
    from app.simulation.catalog import CATALOG, VISUAL_MODES
    for spec in CATALOG.values():
        assert set(spec.visual_modes) <= set(VISUAL_MODES), spec.simulation_id


def test_che_do_la_tu_vung_dong_khong_phai_chuoi_tuy_y():
    """Khai một chế độ lạ phải VỠ NGAY lúc dựng, không âm thầm đi ra descriptor."""
    import pytest
    from app.simulation.catalog import CATALOG, SimSpec
    mau = CATALOG["binary.decimal_to_binary"]
    for xau in [("2d", "4d"), ("3d",), (), ("2d", "2d")]:
        with pytest.raises(ValueError):
            SimSpec(
                simulation_id="thu.nghiem",
                domain="binary",
                visual_modes=xau,
                description=mau.description,
                config_schema=mau.config_schema,
                contract=mau.contract,
                validate=mau.validate,
                make_title=mau.make_title,
            )


def test_descriptor_mang_dung_visual_modes():
    """Bảng năng lực sinh tự động phải báo 1/22, không phải 0/22."""
    d = capability_descriptors()["runtime_targets"]
    assert len(d) == 22
    co_3d = {k for k, t in d.items() if "3d" in t["visual_modes"]}
    assert co_3d == TARGETS_3D
    assert sum(1 for t in d.values() if t["visual_modes"] == ["2d"]) == 21
