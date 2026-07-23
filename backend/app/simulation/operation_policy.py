# -*- coding: utf-8 -*-
"""M17-RC1 §D — CHÍNH SÁCH SỐ LƯỢNG THAO TÁC theo FAMILY (máy-đọc).

Vấn đề đã quan sát (đề "Mạng lưới truyền tin trong khu bảo tồn"): người dùng hỏi
CẢ BỐN kiểu duyệt cây trong một đề, nhưng `TreeTraversalSpec` chỉ mang MỘT
variant. Nếu hệ lặng lẽ chọn một kiểu rồi trả `status=ok` thì **ba yêu cầu bị
bỏ im lặng** — học sinh tưởng đã được trả lời đủ. Đó là mất mát ngữ nghĩa.

Thiết kế KHÔNG keyword, KHÔNG tree-specific: mỗi FAMILY khai chính sách; gate
dùng chung so `requested` (analyze) với `represented` (spec đã validate).

- `single`   — mỗi lần mô phỏng biểu diễn ĐÚNG MỘT cơ chế (vd duyệt cây, sắp xếp).
- `multiple` — biểu diễn nhiều cơ chế độc lập trong một cảnh.
- `pipeline` — nhiều thao tác NỐI TIẾP là một quy trình (vd lọc → chiếu → sắp).

`variant_mechanism` cho phép suy ra cơ chế MÀ SPEC THỰC SỰ biểu diễn từ trường
`variant` trong config — nguồn dữ liệu, không phải đoán chữ.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.simulation.descriptor import FamilyId
from app.simulation.mechanisms import FAMILY_MECHANISMS

SINGLE = "single"
MULTIPLE = "multiple"
PIPELINE = "pipeline"


@dataclass(frozen=True)
class OperationPolicy:
    """Chính sách của MỘT family. `supported_combinations` rỗng = mọi tập con
    ≤ max_operations đều hợp lệ (chỉ ràng buộc bởi mutually_exclusive)."""

    cardinality: str = SINGLE
    max_operations: int = 1
    supported_combinations: tuple[frozenset[str], ...] = ()
    mutually_exclusive: tuple[frozenset[str], ...] = ()
    # M17 W2B-S1 — số TRUY VẤN/MỤC TIÊU ĐỘC LẬP một lần mô phỏng dựng được.
    # Mặc định 1: mọi spec hiện có mô tả ĐÚNG MỘT yêu cầu. Family nào chưa khai
    # mục tiêu có cấu trúc thì mọi yêu cầu có goal=None ⇒ luôn 1 nhóm ⇒ luật này
    # không bao giờ kích hoạt (tương thích ngược).
    max_independent_goals: int = 1
    note: str = ""

    def exclusive_conflict(self, requested: set[str]) -> list[list[str]]:
        """Các nhóm loại-trừ-nhau mà đề yêu cầu ≥2 phần tử cùng lúc."""
        return [
            sorted(group & requested)
            for group in self.mutually_exclusive
            if len(group & requested) >= 2
        ]


def _all_variants_exclusive(family: FamilyId) -> tuple[frozenset[str], ...]:
    """Toàn bộ cơ chế của family loại trừ nhau — dùng cho family `single`:
    một lần mô phỏng chỉ biểu diễn được một cơ chế."""
    return (frozenset(FAMILY_MECHANISMS[family]),)


# Chính sách per-family. DẪN XUẤT danh sách cơ chế từ FAMILY_MECHANISMS (một
# nguồn) — thêm cơ chế mới tự vào nhóm loại-trừ, không phải sửa tay ở đây.
FAMILY_OPERATION_POLICY: dict[FamilyId, OperationPolicy] = {
    FamilyId.TREE_TRAVERSAL: OperationPolicy(
        cardinality=SINGLE, max_operations=1,
        mutually_exclusive=_all_variants_exclusive(FamilyId.TREE_TRAVERSAL),
        note="Một lần duyệt = một thứ tự. Đề hỏi nhiều thứ tự → tách từng lần.",
    ),
    FamilyId.COMPARISON_SORT: OperationPolicy(
        cardinality=SINGLE, max_operations=1,
        mutually_exclusive=_all_variants_exclusive(FamilyId.COMPARISON_SORT),
        note="Một lần mô phỏng chạy một thuật toán sắp xếp.",
    ),
    FamilyId.GRAPH_TRAVERSAL: OperationPolicy(
        cardinality=SINGLE, max_operations=1,
        mutually_exclusive=_all_variants_exclusive(FamilyId.GRAPH_TRAVERSAL),
        note="BFS và DFS là hai lần duyệt khác nhau — chưa có chế độ so sánh.",
    ),
    FamilyId.POSITIONAL_REPRESENTATION: OperationPolicy(
        cardinality=SINGLE, max_operations=1,
        mutually_exclusive=_all_variants_exclusive(FamilyId.POSITIONAL_REPRESENTATION),
        note="Một lần đổi = một cặp cơ số nguồn→đích.",
    ),
    FamilyId.INTERVAL_ELIMINATION: OperationPolicy(cardinality=SINGLE, max_operations=1),
    FamilyId.SINGLE_PASS_SCAN: OperationPolicy(
        cardinality=SINGLE, max_operations=1,
        note="Một lượt quét cho một mục tiêu (max/min/đếm/tổng/tìm).",
    ),
    FamilyId.BOOLEAN_COMPOSITION: OperationPolicy(
        cardinality=MULTIPLE, max_operations=8,
        note="Một mạch CHỨA nhiều cổng — nhiều cơ chế trong một cảnh là bình thường.",
    ),
    FamilyId.LAYERED_PDU_TRANSFORM: OperationPolicy(
        cardinality=PIPELINE, max_operations=2,
        note="Đóng gói → truyền → tháo gói là MỘT quy trình nối tiếp, không phải xung đột.",
    ),
    # W2B — MỘT truy vấn = nhiều tầng NỐI TIẾP (lọc → chiếu → sắp → lấy n →
    # tổng hợp). Nhiều tầng KHÔNG phải xung đột; đó là bản chất của truy vấn.
    FamilyId.RELATIONAL_TABLE_QUERY: OperationPolicy(
        cardinality=PIPELINE, max_operations=5,
        note="Lọc → chọn cột → sắp xếp → lấy n dòng → tính tổng hợp là MỘT quy "
             "trình nối tiếp trên cùng một bảng.",
    ),
    FamilyId.STRUCTURAL_PROGRESSIVE_REPRESENTATION: OperationPolicy(
        cardinality=MULTIPLE, max_operations=8,
        note="Một cảnh generic có thể vừa hé lộ vừa di chuyển.",
    ),
}

DEFAULT_POLICY = OperationPolicy(cardinality=SINGLE, max_operations=1)


def policy_for_family(family_value: str) -> OperationPolicy:
    for fid, pol in FAMILY_OPERATION_POLICY.items():
        if fid.value == family_value:
            return pol
    return DEFAULT_POLICY


# ── variant (trong config) → cơ chế mà spec THỰC SỰ biểu diễn ──
# Dữ liệu thuần, dùng để tính represented_requirements. Family nào không có
# trường `variant` thì bỏ qua (đã dùng owned_mechanisms của target).
VARIANT_MECHANISM: dict[str, dict[str, str]] = {
    FamilyId.TREE_TRAVERSAL.value: {
        "preorder": "tree_traversal.preorder",
        "inorder": "tree_traversal.inorder",
        "postorder": "tree_traversal.postorder",
        "level_order": "tree_traversal.level_order",
    },
    FamilyId.GRAPH_TRAVERSAL.value: {
        "bfs": "graph_traversal.breadth_first",
        "dfs": "graph_traversal.depth_first",
    },
    FamilyId.COMPARISON_SORT.value: {
        "bubble": "comparison_sort.adjacent_compare_swap",
        "insertion": "comparison_sort.shift_into_sorted_prefix",
        "selection": "comparison_sort.select_extreme_repeated",
    },
}


def mechanism_for_variant(family_value: str, variant: str | None) -> str | None:
    if not variant:
        return None
    return VARIANT_MECHANISM.get(family_value, {}).get(variant)
