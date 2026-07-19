# -*- coding: utf-8 -*-
"""M16 Task 4 (W4) — khóa coverage pool `m16` (catalog-wide eval).

Lock TỪNG MỤC Phụ lục B của brief (.superpowers/sdd/m16-task-4-brief.md):
§1 14/14 target × 2 supported positive (explicit + paraphrase);
§2 8/8 family ≥1 valid_boundary (interval ×2, positional ×3, boolean anti-merge);
§3 8/8 family ≥1 near_miss (structural phủ bởi authority_control leak — §5a);
§4 cross_family_recovery (1 success + 1 failure);
§5 authority_control cặp (computation-leak + representation đối chứng);
§6 live subset ≤24 phủ đủ.
Cùng: admission (cũ + m16), id unique/prefix/snapshot, frozen fingerprint Task 1
vẫn xanh, tag ↔ live_eligible nhất quán.
"""

from __future__ import annotations

from app.evaluation.datasets import POOLS, check_admission, get_pool
from app.evaluation.datasets.m16_catalog import M16_ITEMS, M16_REFERENCED_CASES
from app.evaluation.m16_schema import (
    M16Archetype,
    M16Expectation,
    check_m16_admission,
    frozen_dataset_fingerprint,
)
from app.simulation.descriptor import FamilyId

# ── Hằng dùng chung ───────────────────────────────────────────
SORT_TOKEN = "algorithm.comparison_sort"
CS = FamilyId.COMPARISON_SORT.value
PR = FamilyId.POSITIONAL_REPRESENTATION.value
IE = FamilyId.INTERVAL_ELIMINATION.value
SPR = FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION.value
ALL_FAMILIES = {f.value for f in FamilyId}

MECHANISM_EXPOSED = {CS, PR}

# 14 concrete target (Phụ lục B §1) — sorting tách bubble/insertion qua mechanism.
TARGETS = {
    "algorithm.find_max", "algorithm.find_min", "algorithm.sum_if", "algorithm.count_if",
    "algorithm.linear_search", "algorithm.binary_search", "algorithm.bubble_sort",
    "algorithm.insertion_sort", "algorithm.scan", "logic.and_gate",
    "binary.decimal_to_binary", "network.packet_routing", "network.protocol_encapsulation",
    "generic.rule_scene",
}

# Snapshot PIN — danh sách id (sorted) cố định, ổn định qua các lần chạy.
_ID_SNAPSHOT: tuple[str, ...] = (
    "m16-ac-computation-leak",
    "m16-ac-representation-ok",
    "m16-and-explicit",
    "m16-and-paraphrase",
    "m16-binary-explicit",
    "m16-binary-paraphrase",
    "m16-binsearch-explicit",
    "m16-binsearch-paraphrase",
    "m16-bubble-explicit",
    "m16-bubble-paraphrase",
    "m16-countif-explicit",
    "m16-countif-paraphrase",
    "m16-cr-positional-fail",
    "m16-cr-positional-recover",
    "m16-encap-explicit",
    "m16-encap-paraphrase",
    "m16-findmax-explicit",
    "m16-findmax-paraphrase",
    "m16-findmin-explicit",
    "m16-findmin-paraphrase",
    "m16-generic-move",
    "m16-generic-reveal",
    "m16-insertion-explicit",
    "m16-insertion-paraphrase",
    "m16-linear-explicit",
    "m16-linear-paraphrase",
    "m16-nm-freevar-loop",
    "m16-nm-hex-gap",
    "m16-nm-interpolation",
    "m16-nm-sort-partition",
    "m16-nm-tcp-handshake",
    "m16-nm-threshold-kofn",
    "m16-nm-weighted-shortest",
    "m16-routing-explicit",
    "m16-routing-paraphrase",
    "m16-scan-explicit",
    "m16-scan-paraphrase",
    "m16-sumif-explicit",
    "m16-sumif-paraphrase",
    "m16-vb-and3-generic",
    "m16-vb-binary-255",
    "m16-vb-binary-overrange",
    "m16-vb-binary-zero",
    "m16-vb-binsearch-absent",
    "m16-vb-binsearch-unsorted",
    "m16-vb-decapsulation",
    "m16-vb-routing-multipath",
    "m16-vb-scan-optional",
    "m16-vb-sort-duplicates",
    "m16-vb-web-static",
)

# frozen dataset fingerprint PIN (giống test_m16_schema — Task 1 close, M15 c93a7a4).
_FROZEN_FINGERPRINT_PIN = "86e5a31db6d5a11c677dad95842e5ed6eaafc3b373afea651c49ef5258021dbf"


# ── Helpers ───────────────────────────────────────────────────
def _m16(item) -> M16Expectation:
    assert isinstance(item.m16, M16Expectation), item.id
    return item.m16


def _target_of(item) -> str:
    """Map một positive case → concrete target. Sorting route qua TOKEN selector
    → target dẫn xuất từ analyze_mechanism_expected (bubble/insertion)."""
    m = _m16(item)
    if m.expected_initial_route == SORT_TOKEN:
        return {
            "comparison_sort.adjacent_compare_swap": "algorithm.bubble_sort",
            "comparison_sort.shift_into_sorted_prefix": "algorithm.insertion_sort",
        }[m.analyze_mechanism_expected]
    return m.expected_initial_route


def _by_archetype(arch: M16Archetype) -> list:
    return [it for it in M16_ITEMS if _m16(it).archetype == arch]


def _families_of(items) -> set[str]:
    return {_m16(it).expected_family for it in items}


# ── Cấu trúc / integrity ──────────────────────────────────────
def test_id_unique_prefix_va_snapshot():
    ids = [it.id for it in M16_ITEMS]
    assert len(ids) == len(set(ids)), "id trùng trong M16_ITEMS"
    assert all(i.startswith("m16-") for i in ids), "mọi id phải prefix 'm16-'"
    assert tuple(sorted(ids)) == _ID_SNAPSHOT, "snapshot id trôi — cập nhật có chủ đích mới sửa PIN"


def test_frozen_dataset_fingerprint_van_xanh():
    # Task 1 khóa 30 case DATASET không đổi — pool m16 KHÔNG được chạm DATASET.
    assert frozen_dataset_fingerprint() == _FROZEN_FINGERPRINT_PIN


def test_pool_m16_dang_ky_va_khong_ro_ri_dataset():
    assert "m16" in POOLS
    assert get_pool("m16") is M16_ITEMS
    historical = {it.id for it in get_pool("regression")}
    assert not ({it.id for it in M16_ITEMS} & historical)


# ── Admission (cũ + m16) xanh toàn pool ───────────────────────
def test_admission_toan_pool_xanh():
    errs: list[str] = []
    for it in M16_ITEMS:
        errs += check_admission(it)
        errs += check_m16_admission(it)
    assert not errs, "Vi phạm admission:\n" + "\n".join(errs)


def test_moi_case_co_m16_expectation():
    for it in M16_ITEMS:
        assert isinstance(it.m16, M16Expectation), it.id
        assert _m16(it).expected_family in ALL_FAMILIES, it.id


# ── Phụ lục B §1 — 14/14 target × 2 supported positive ────────
def test_14_target_du_2_positive_explicit_va_paraphrase():
    explicit: dict[str, int] = {}
    paraphrase: dict[str, int] = {}
    for it in _by_archetype(M16Archetype.EXPLICIT_POSITIVE):
        explicit[_target_of(it)] = explicit.get(_target_of(it), 0) + 1
    for it in _by_archetype(M16Archetype.PARAPHRASE_POSITIVE):
        paraphrase[_target_of(it)] = paraphrase.get(_target_of(it), 0) + 1

    assert set(explicit) | set(paraphrase) >= TARGETS
    for t in TARGETS:
        assert explicit.get(t, 0) >= 1, f"target {t} thiếu explicit_positive"
        assert paraphrase.get(t, 0) >= 1, f"target {t} thiếu paraphrase_positive"


def test_sorting_route_token_va_mechanism_dung():
    """Sorting positive: route TOKEN selector + mechanism canonical đúng biến thể."""
    sorters = [
        it for it in M16_ITEMS
        if _m16(it).expected_family == CS and _m16(it).expected_initial_route is not None
    ]
    assert sorters
    for it in sorters:
        m = _m16(it)
        assert m.expected_initial_route == SORT_TOKEN, it.id
        assert m.analyze_mechanism_expected in {
            "comparison_sort.adjacent_compare_swap",
            "comparison_sort.shift_into_sorted_prefix",
        }, it.id


def test_generic_positive_reveal_va_move():
    """generic 2 positive: reveal_sequence (progressive_reveal) + move (moving_path)."""
    gen_pos = [
        it for it in M16_ITEMS
        if _target_of_safe(it) == "generic.rule_scene"
        and _m16(it).archetype in {M16Archetype.EXPLICIT_POSITIVE, M16Archetype.PARAPHRASE_POSITIVE}
    ]
    kinds = {it.semantic.get("kind") for it in gen_pos}
    assert "progressive_reveal" in kinds
    assert "moving_path" in kinds


def _target_of_safe(item) -> str:
    m = _m16(item)
    if m.expected_initial_route in (None, SORT_TOKEN):
        return m.expected_initial_route or "unsupported"
    return m.expected_initial_route


# ── Phụ lục B §2 — 8/8 family ≥1 valid_boundary ───────────────
def test_valid_boundary_du_8_family():
    vb = _by_archetype(M16Archetype.VALID_BOUNDARY)
    fams = _families_of(vb)
    assert fams == ALL_FAMILIES, f"thiếu valid_boundary cho: {ALL_FAMILIES - fams}"


def test_valid_boundary_dem_dac_biet():
    vb = _by_archetype(M16Archetype.VALID_BOUNDARY)
    per_family: dict[str, int] = {}
    for it in vb:
        f = _m16(it).expected_family
        per_family[f] = per_family.get(f, 0) + 1
    # interval_elimination: đúng 2 (target absent + unsorted normalize)
    assert per_family[IE] >= 2, "interval_elimination cần 2 valid_boundary"
    # positional_representation: 3 (0, 255, vượt phạm vi hợp đồng)
    assert per_family[PR] >= 3, "positional_representation cần 3 valid_boundary"


def test_boolean_anti_merge_boundary_ve_generic():
    """valid_boundary boolean_composition (3-input AND) PHẢI expect generic.rule_scene."""
    bc_vb = [
        it for it in _by_archetype(M16Archetype.VALID_BOUNDARY)
        if _m16(it).expected_family == FamilyId.BOOLEAN_COMPOSITION.value
    ]
    assert bc_vb
    for it in bc_vb:
        assert _m16(it).expected_initial_route == "generic.rule_scene", it.id
        assert it.expect_simulation_id == "generic.rule_scene", it.id


# ── Phụ lục B §3 — 8/8 family ≥1 near_miss (structural via authority_control) ──
def test_near_miss_du_8_family_structural_qua_authority_control():
    nm = _by_archetype(M16Archetype.NEAR_MISS_GAP)
    fams = _families_of(nm)
    assert all(it.group == "unsupported" for it in nm), "near_miss phải group unsupported"

    # structural_progressive_representation phủ bởi authority_control leak (§5a):
    leak = [
        it for it in _by_archetype(M16Archetype.AUTHORITY_CONTROL)
        if it.group == "unsupported"
        and _m16(it).expected_gate == "computation"
        and _m16(it).expected_family == SPR
    ]
    assert leak, "thiếu authority_control leak cho structural_progressive"
    fams = fams | {SPR}
    assert fams == ALL_FAMILIES, f"thiếu near_miss cho: {ALL_FAMILIES - fams}"


def test_near_miss_comparison_sort_mechanism_gate():
    """comparison_sort near_miss (partition) → mechanism gate + gate_mechanism_ownership."""
    cs_nm = [
        it for it in _by_archetype(M16Archetype.NEAR_MISS_GAP)
        if _m16(it).expected_family == CS
    ]
    assert cs_nm
    for it in cs_nm:
        m = _m16(it)
        assert m.analyze_mechanism_expected == "comparison_sort.partition_recursive", it.id
        assert m.expected_gate == "mechanism", it.id
        assert m.expected_error_code == "gate_mechanism_ownership", it.id
        assert m.algorithmic_request is True, it.id


# ── Phụ lục B §4 — cross_family_recovery (1 success + 1 failure) ──
def test_cross_family_recovery_success_va_failure():
    cr = _by_archetype(M16Archetype.CROSS_FAMILY_RECOVERY)
    assert len(cr) >= 2

    success = [it for it in cr if it.group != "unsupported"]
    failure = [it for it in cr if it.group == "unsupported"]
    assert success, "thiếu recovery-success (group != unsupported)"
    assert failure, "thiếu recovery-failure (group unsupported)"

    for it in success:
        m = _m16(it)
        assert m.expected_initial_route is not None, it.id
        assert m.recovery_route_exists is True, it.id

    for it in failure:
        m = _m16(it)
        assert m.recovery_route_exists is False, it.id
        assert m.expected_error_code == "route_mechanism_family_mismatch", it.id
        assert m.expected_gate == "route_mechanism", it.id


# ── Phụ lục B §5 — authority_control cặp ──────────────────────
def test_authority_control_cap_leak_va_representation():
    ac = _by_archetype(M16Archetype.AUTHORITY_CONTROL)
    assert len(ac) >= 2

    leak = [it for it in ac if it.group == "unsupported"]
    repr_ = [it for it in ac if it.group == "generic"]
    assert leak, "thiếu computation-leak control"
    assert repr_, "thiếu representation đối chứng"

    for it in leak:
        m = _m16(it)
        assert m.expected_gate == "computation", it.id
        # nhánh computation gate trả capability_gap KHÔNG kèm error_code
        assert m.expected_error_code is None, it.id
        assert m.algorithmic_request is True, it.id

    for it in repr_:
        m = _m16(it)
        assert it.expect_simulation_id == "generic.rule_scene", it.id
        assert m.expected_initial_route == "generic.rule_scene", it.id


# ── mechanism-exposed: sorting/positional CÓ analyze_mechanism_expected ──
def test_sorting_positional_co_mechanism_khac_family_khong_co():
    for it in M16_ITEMS:
        m = _m16(it)
        if m.expected_family in MECHANISM_EXPOSED:
            assert m.analyze_mechanism_expected is not None, (
                f"{it.id}: family {m.expected_family} phải có analyze_mechanism_expected"
            )
        else:
            # check_m16_admission đã cấm; khóa lại tường minh ở đây.
            assert m.analyze_mechanism_expected is None, (
                f"{it.id}: family {m.expected_family} KHÔNG được có analyze_mechanism_expected"
            )


# ── Phụ lục B §6 — live subset ≤24 phủ đủ ─────────────────────
def test_live_subset_khong_qua_24():
    live = [it for it in M16_ITEMS if _m16(it).live_eligible]
    assert len(live) <= 24, f"live_eligible = {len(live)} > 24"


def test_live_subset_phu_positive_moi_target():
    live = [it for it in M16_ITEMS if _m16(it).live_eligible]
    pos = [
        it for it in live
        if _m16(it).archetype in {M16Archetype.EXPLICIT_POSITIVE, M16Archetype.PARAPHRASE_POSITIVE}
    ]
    covered = {_target_of(it) for it in pos}
    assert covered == TARGETS, f"live thiếu positive cho target: {TARGETS - covered}"


def test_live_subset_phu_near_miss_moi_family_va_paraphrase():
    live = [it for it in M16_ITEMS if _m16(it).live_eligible]

    # ≥1 near-miss/family (structural qua authority_control leak)
    nm_fams = {
        _m16(it).expected_family for it in live
        if _m16(it).archetype == M16Archetype.NEAR_MISS_GAP
    }
    leak = [
        it for it in live
        if _m16(it).archetype == M16Archetype.AUTHORITY_CONTROL
        and it.group == "unsupported"
        and _m16(it).expected_family == SPR
    ]
    if leak:
        nm_fams = nm_fams | {SPR}
    assert nm_fams == ALL_FAMILIES, f"live thiếu near-miss cho family: {ALL_FAMILIES - nm_fams}"

    # paraphrase hiện diện ở MỌI family trong live subset
    para_fams = {
        _m16(it).expected_family for it in live
        if _m16(it).archetype == M16Archetype.PARAPHRASE_POSITIVE
    }
    assert para_fams == ALL_FAMILIES, f"live thiếu paraphrase cho family: {ALL_FAMILIES - para_fams}"


def test_live_subset_phu_cac_diem_bat_buoc():
    live_ids = {it.id for it in M16_ITEMS if _m16(it).live_eligible}
    # positional binary positive + hex gap
    assert "m16-binary-paraphrase" in live_ids or "m16-binary-explicit" in live_ids
    assert "m16-nm-hex-gap" in live_ids
    # generic representation positive + leak control
    assert "m16-generic-move" in live_ids or "m16-generic-reveal" in live_ids
    assert "m16-ac-computation-leak" in live_ids
    # 2 cross_family_recovery
    assert "m16-cr-positional-recover" in live_ids
    assert "m16-cr-positional-fail" in live_ids


# ── Tag ↔ live_eligible nhất quán ─────────────────────────────
def test_tag_m16_offline_va_catalog_live_nhat_quan():
    for it in M16_ITEMS:
        assert "m16_offline" in it.tags, f"{it.id} thiếu tag m16_offline"
        has_live_tag = "m16_catalog_live" in it.tags
        assert has_live_tag == _m16(it).live_eligible, (
            f"{it.id}: tag m16_catalog_live ({has_live_tag}) != live_eligible ({_m16(it).live_eligible})"
        )


# ── Registry tham chiếu trỏ tới case CÓ THẬT ở pool cũ ────────
def test_referenced_cases_ton_tai_trong_pool_cu():
    known = {
        it.id
        for name, pool in POOLS.items()
        if name != "m16"
        for it in pool
    }
    missing = set(M16_REFERENCED_CASES) - known
    assert not missing, f"M16_REFERENCED_CASES trỏ id không tồn tại: {missing}"
