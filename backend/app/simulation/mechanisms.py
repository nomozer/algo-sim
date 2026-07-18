"""M15 — taxonomy cơ chế canonical namespaced (nguồn DUY NHẤT) + alias boundary.

Khóa 1: canonical_mechanism là compatibility boundary duy nhất — legacy sorting
(live-verified M14) → canonical; canonical passthrough; alias MỘT CHIỀU, không
phải taxonomy thứ hai. Gate/descriptor/cross-lock CHỈ so canonical.
Khóa 2: giá trị analyze-exposed unowned phải nằm trong INTENTIONAL_GAP_MECHANISMS.
KHÔNG import catalog (chống vòng import — cross-lock với catalog ở test).
"""
from __future__ import annotations

from app.simulation.descriptor import FamilyId

NO_PRESCRIPTION = "none"

FAMILY_MECHANISMS: dict[FamilyId, tuple[str, ...]] = {
    FamilyId.COMPARISON_SORT: (
        "comparison_sort.adjacent_compare_swap",
        "comparison_sort.shift_into_sorted_prefix",
        "comparison_sort.select_extreme_repeated",
        "comparison_sort.partition_recursive",
        "comparison_sort.other_unspecified",
    ),
    FamilyId.POSITIONAL_REPRESENTATION: (
        "positional_representation.binary_positional_weights",
        "positional_representation.non_binary_base",
    ),
    FamilyId.INTERVAL_ELIMINATION: ("interval_elimination.halve_sorted_interval",),
    FamilyId.SINGLE_PASS_SCAN: (
        "single_pass_scan.track_extreme",
        "single_pass_scan.accumulate_conditional",
        "single_pass_scan.count_conditional",
        "single_pass_scan.find_equal_early_stop",
        "single_pass_scan.configured_single_pass",
    ),
    FamilyId.BOOLEAN_COMPOSITION: (
        "boolean_composition.single_gate_truth_table",
        "boolean_composition.composed_rule_dag",
    ),
    FamilyId.GRAPH_TRAVERSAL: ("graph_traversal.unweighted_hop_bfs",),
    FamilyId.LAYERED_PDU_TRANSFORM: (
        "layered_pdu_transform.encapsulate_decapsulate_4layer",
    ),
    FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION: (
        "structural_progressive_representation.reveal_sequence",
        "structural_progressive_representation.move_along_path",
    ),
}

# Khóa 2 — giá trị CỐ Ý không target nào sở hữu (gap-trigger, khai tường minh)
INTENTIONAL_GAP_MECHANISMS: frozenset[str] = frozenset({
    "comparison_sort.select_extreme_repeated",
    "comparison_sort.partition_recursive",
    "comparison_sort.other_unspecified",
    "positional_representation.non_binary_base",
})

# Khóa 1 — alias MỘT CHIỀU legacy→canonical, CHỈ namespace comparison_sort (M14 compat)
LEGACY_ALIASES: dict[str, str] = {
    "adjacent_compare_swap": "comparison_sort.adjacent_compare_swap",
    "shift_into_sorted_prefix": "comparison_sort.shift_into_sorted_prefix",
    "select_extreme_repeated": "comparison_sort.select_extreme_repeated",
    "partition_recursive": "comparison_sort.partition_recursive",
    "other_unspecified": "comparison_sort.other_unspecified",
}

# Registry tiến độ formalization — wave sau MỞ RỘNG; W5 lock == toàn bộ FamilyId
FORMALIZED_FAMILIES: frozenset[FamilyId] = frozenset({
    FamilyId.COMPARISON_SORT,           # M14 (reference)
    FamilyId.POSITIONAL_REPRESENTATION, # W1
    FamilyId.INTERVAL_ELIMINATION,      # W1
})


def canonical_mechanism(raw: str | None) -> str | None:
    """Boundary DUY NHẤT legacy→canonical. None/"none" → None (không ép cơ chế)."""
    if raw is None or raw == NO_PRESCRIPTION:
        return None
    return LEGACY_ALIASES.get(raw, raw)


def mechanism_family(canonical: str) -> str:
    return canonical.split(".", 1)[0]


def analyze_exposed_values() -> tuple[str, ...]:
    """Nguồn enum `prescribed_procedure` của ANALYZE_SCHEMA (dẫn xuất — anti-pattern #1).
    M15: legacy sorting GIỮ NGUYÊN (rev2 điểm 2) + none + positional namespaced."""
    return (
        NO_PRESCRIPTION,
        *LEGACY_ALIASES.keys(),
        "positional_representation.binary_positional_weights",
        "positional_representation.non_binary_base",
    )
