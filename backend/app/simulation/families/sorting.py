"""M14 — comparison_sort family (pilot).

§C3/§D: family so-sánh; hai variant (bubble/insertion) resolve về hai runtime
target concrete (algorithm.bubble_sort / algorithm.insertion_sort) — executor
GIỮ NGUYÊN, không viết lại. Cơ chế family SỞ HỮU: adjacent_compare_swap
(bubble), shift_into_sorted_prefix (insertion). Selection/quick KHÔNG thuộc
owned → mechanism gate (Task 6) trả capability_gap.

Khung Task 2: variants + owned_mechanisms + version + token. Schema/validator
(Task 5) và resolve (Task 7) điền sau — construct SORTING_SELECTOR sẽ được cập
nhật ở các task đó.
"""

from __future__ import annotations

from app.simulation.descriptor import FamilyId
from app.simulation.families.base import FamilySelector, VariantSpec

SORT_FAMILY_VERSION = "sort-fam-1"
SELECTOR_TOKEN = "algorithm.comparison_sort"

# Cơ chế family THỰC SỰ sở hữu (executor hiện có biểu diễn được). Dùng cho
# mechanism gate (Task 6) và cross-lock variant.mechanism_id ⊆ owned.
MECH_ADJACENT_SWAP = "adjacent_compare_swap"
MECH_SHIFT_INSERT = "shift_into_sorted_prefix"
OWNED_MECHANISMS: tuple[str, ...] = (MECH_ADJACENT_SWAP, MECH_SHIFT_INSERT)

# ── prescribed_procedure (analyze signal, §E4/§O7) ────────────
# Enum ĐÓNG mô tả CƠ CHẾ đề yêu cầu — KHÔNG free-text, KHÔNG tên thuật toán,
# KHÔNG chứa result/trace/timeline. Đủ để mechanism gate (Task 6) so
# family/variant consistency. Gồm: none (không ép cơ chế) + cơ chế OWNED +
# cơ chế NGOÀI family (select/partition — không executor nào sở hữu) + other.
PROC_NONE = "none"
PROC_ADJACENT_SWAP = MECH_ADJACENT_SWAP
PROC_SHIFT_INSERT = MECH_SHIFT_INSERT
PROC_SELECT_EXTREME = "select_extreme_repeated"
PROC_PARTITION = "partition_recursive"
PROC_OTHER = "other_unspecified"
PRESCRIBED_PROCEDURES: tuple[str, ...] = (
    PROC_NONE,
    PROC_ADJACENT_SWAP,
    PROC_SHIFT_INSERT,
    PROC_SELECT_EXTREME,
    PROC_PARTITION,
    PROC_OTHER,
)

_VARIANTS: tuple[VariantSpec, ...] = (
    VariantSpec("bubble", "algorithm.bubble_sort", MECH_ADJACENT_SWAP),
    VariantSpec("insertion", "algorithm.insertion_sort", MECH_SHIFT_INSERT),
)

SORTING_SELECTOR = FamilySelector(
    family_id=FamilyId.COMPARISON_SORT,
    selector_token=SELECTOR_TOKEN,
    family_spec_version=SORT_FAMILY_VERSION,
    owned_mechanisms=OWNED_MECHANISMS,
    variants=_VARIANTS,
    description=(
        "sắp xếp một dãy số bằng THUẬT TOÁN SO SÁNH — nổi bọt (bubble, đổi chỗ cặp "
        "kề) hoặc chèn (insertion, dời phần tử vào phần đã sắp). Dùng khi đề yêu cầu "
        "SẮP XẾP một dãy. KHÔNG dùng cho selection sort / quick sort / merge sort — "
        "các cơ chế đó chưa có engine tất định sở hữu (trả unsupported)."
    ),
    # config_schema/contract/validate_family_spec: Task 5 · resolve: Task 7
)
