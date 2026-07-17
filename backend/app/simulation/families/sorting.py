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

_VARIANT_IDS: tuple[str, ...] = tuple(v.variant_id for v in _VARIANTS)

# ── FamilySpec (Task 5) — bounded, đóng hoàn toàn, không field mở (§D) ──
ARRAY_MIN, ARRAY_MAX = 2, 15

SORTING_FAMILY_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "family_version": {"type": "STRING", "enum": [SORT_FAMILY_VERSION]},
        "variant": {"type": "STRING", "enum": list(_VARIANT_IDS)},
        "array": {"type": "ARRAY", "items": {"type": "NUMBER"}},
        "order": {"type": "STRING", "enum": ["asc", "desc"]},
        "labels": {"type": "ARRAY", "items": {"type": "STRING"}, "nullable": True},
        "notes": {"type": "STRING", "nullable": True},
    },
    "required": ["family_version", "variant", "array", "order"],
}

_ALLOWED_KEYS = {"family_version", "variant", "array", "order", "labels", "notes"}

SORTING_FAMILY_CONTRACT = f"""HỢP ĐỒNG CONFIG (SortingFamilySpec, family_version "{SORT_FAMILY_VERSION}"):
Bạn CHỈ chọn biến thể + điền dữ liệu; engine tất định sở hữu diễn biến/kết quả.
- family_version: đúng "{SORT_FAMILY_VERSION}".
- variant: "bubble" (nổi bọt — đổi chỗ cặp KỀ) hoặc "insertion" (chèn — dời vào phần đã sắp). Chọn theo cơ chế ĐỀ YÊU CẦU; đề không ép cơ chế → chọn "bubble".
- array: dãy số CỦA ĐỀ (2–15 phần tử, đúng thứ tự đề cho, không bịa).
- order: "asc" (tăng dần) hoặc "desc" (giảm dần) theo đề.
- labels: nhãn từng phần tử NẾU đề gắn tên người/vật với giá trị (độ dài khớp array); không có → bỏ trống.
- TUYỆT ĐỐI KHÔNG sinh steps/timeline/kết quả/trạng thái — engine tự chạy.
- KHÔNG dùng cho selection sort / quick sort / merge sort (cơ chế ngoài phạm vi)."""


def _finite_number(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and v not in (float("inf"), float("-inf"))


def validate_family_spec(raw) -> tuple[dict | None, str | None]:
    """Validate SortingFamilySpec — fail-closed, reject key lạ (không strip im
    lặng, tiền lệ M13 Task 12b). Trả (config chuẩn hóa, None) hoặc (None, lỗi).
    Mọi lỗi ở đây map mã cổng `family_spec_invalid` (Task 6/8)."""
    if not isinstance(raw, dict):
        return None, "Config không phải đối tượng JSON."
    extra = set(raw.keys()) - _ALLOWED_KEYS
    if extra:
        return None, f"Config chứa khóa ngoài SortingFamilySpec: {', '.join(sorted(extra))}."
    if raw.get("family_version") != SORT_FAMILY_VERSION:
        return None, f'"family_version" phải là "{SORT_FAMILY_VERSION}".'
    variant = raw.get("variant")
    if variant not in _VARIANT_IDS:
        return None, f'"variant" phải là một trong {list(_VARIANT_IDS)}.'
    array = raw.get("array")
    if not isinstance(array, list) or not (ARRAY_MIN <= len(array) <= ARRAY_MAX):
        return None, f'"array" phải là dãy {ARRAY_MIN}–{ARRAY_MAX} phần tử.'
    if not all(_finite_number(x) for x in array):
        return None, '"array" phải toàn số hữu hạn.'
    order = raw.get("order")
    if order not in ("asc", "desc"):
        return None, '"order" phải là "asc" hoặc "desc".'
    labels = raw.get("labels")
    if labels is not None:
        if not isinstance(labels, list) or not all(isinstance(x, str) for x in labels):
            return None, '"labels" phải là mảng chuỗi.'
        if len(labels) != len(array):
            return None, '"labels" phải khớp độ dài "array".'
    notes = raw.get("notes")
    if notes is not None and not isinstance(notes, str):
        return None, '"notes" phải là chuỗi.'
    return {
        "family_version": SORT_FAMILY_VERSION,
        "variant": variant,
        "array": list(array),
        "order": order,
        "labels": list(labels) if labels else None,
        "notes": notes if isinstance(notes, str) else None,
    }, None


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
    config_schema=SORTING_FAMILY_SCHEMA,
    contract=SORTING_FAMILY_CONTRACT,
    validate_family_spec=validate_family_spec,
    # resolve: Task 7
)
