# -*- coding: utf-8 -*-
"""M17-RC1 §C1 — OPERATION: mục tiêu cụ thể người học yêu cầu.

Phân biệt đã trả giá để học được (RC1-C đo được, case rc1c-scan-max-and-min):

- **operation** = MỤC TIÊU cụ thể ("tìm giá trị lớn nhất", "duyệt trước");
- **mechanism** = CƠ CHẾ thực hiện ("quét một lượt giữ cực trị").

`find_max` và `find_min` là HAI operation khác nhau nhưng dùng CHUNG mechanism
`single_pass_scan.track_extreme`. Cổng completeness cũ định danh yêu cầu bằng
mechanism nên gộp hai thành một → đề "tìm cả max lẫn min" trả `ok` và bỏ im
lặng một nửa. **Operation KHÔNG BAO GIỜ được dedupe theo mechanism.**

Registry DẪN XUẤT TOÀN BỘ từ `CATALOG` + `FAMILY_SELECTORS`:
operation = một (target, variant) THẬT SỰ CHẠY ĐƯỢC.

- target có `variant` enum trong config_schema (tree, graph) → mỗi variant một
  operation;
- target nấp sau selector token (sorting) → mỗi variant của selector;
- target không có variant → chính nó là một operation.

Hệ quả: KHÔNG có operation nào thiếu executor/target thật (điều kiện §C1), và
thêm target/variant mới thì operation tự xuất hiện. Id dùng dấu HAI CHẤM
(`family:operation`) để không bao giờ lẫn với id mechanism (dấu chấm).
"""

from __future__ import annotations

from dataclasses import dataclass

from app.simulation.descriptor import FamilyId

_OP_SEP = ":"


@dataclass(frozen=True)
class OperationSpec:
    """Một operation CHẠY ĐƯỢC: family + target + variant (nếu có) + mechanism
    mà nó dùng (có thể trùng với operation khác — đó chính là điểm mấu chốt)."""

    operation_id: str
    family_id: str
    target_id: str
    variant: str | None
    mechanism: str | None  # None khi target catch-all sở hữu nhiều cơ chế
    label_vi: str

    @property
    def local(self) -> str:
        return self.operation_id.split(_OP_SEP, 1)[1]


def operation_family(operation_id: str) -> str:
    """Family của một operation id — tách bằng dấu hai chấm (id operation),
    KHÔNG dùng cho mechanism id (dấu chấm)."""
    return operation_id.split(_OP_SEP, 1)[0]


# Nhãn tiếng Việt cho học sinh — dữ liệu NỘI DUNG, không suy được từ registry
# (make_title cần config). Thiếu nhãn cho một operation ⇒ test khoá đỏ, không
# lặng lẽ hiện id kỹ thuật cho học sinh.
_LABELS: dict[str, str] = {
    "single_pass_scan:find_max": "tìm giá trị lớn nhất",
    "single_pass_scan:find_min": "tìm giá trị nhỏ nhất",
    "single_pass_scan:sum_if": "tính tổng theo điều kiện",
    "single_pass_scan:count_if": "đếm theo điều kiện",
    "single_pass_scan:linear_search": "tìm kiếm tuần tự",
    "single_pass_scan:scan": "quét dãy một lượt theo cấu hình",
    "interval_elimination:binary_search": "tìm kiếm nhị phân",
    "comparison_sort:bubble": "sắp xếp nổi bọt",
    "comparison_sort:insertion": "sắp xếp chèn",
    "comparison_sort:selection": "sắp xếp chọn",
    "positional_representation:decimal_to_binary": "đổi số thập phân sang nhị phân",
    "positional_representation:base_conversion": "đổi cơ số tổng quát",
    "tree_traversal:preorder": "duyệt cây theo thứ tự trước",
    "tree_traversal:inorder": "duyệt cây theo thứ tự giữa",
    "tree_traversal:postorder": "duyệt cây theo thứ tự sau",
    "tree_traversal:level_order": "duyệt cây theo mức",
    "graph_traversal:bfs": "duyệt đồ thị theo chiều rộng",
    "graph_traversal:dfs": "duyệt đồ thị theo chiều sâu",
    "graph_traversal:packet_routing": "định tuyến gói tin qua mạng",
    "boolean_composition:and_gate": "khảo sát một cổng logic",
    "boolean_composition:boolean_dag": "tính mạch nhiều cổng logic",
    "boolean_composition:rule_scene": "cảnh suy diễn theo luật logic",
    "layered_pdu_transform:protocol_encapsulation": "đóng gói dữ liệu qua các tầng mạng",
    "structural_progressive_representation:rule_scene": "cảnh biểu diễn hiện dần",
}


def _local_name(target_id: str) -> str:
    """Tên cục bộ của target (`algorithm.find_max` → `find_max`)."""
    return target_id.split(".", 1)[1]


def _build() -> dict[str, OperationSpec]:
    # Import TRỄ: catalog import descriptor/mechanisms; module này được catalog
    # dùng gián tiếp qua pipeline nên nạp trễ để tránh vòng import.
    from app.simulation.catalog import CATALOG
    from app.simulation.descriptor import ReachabilityLevel
    from app.simulation.families import FAMILY_SELECTORS

    # (target, variant) đến từ selector token — dựng trước để tra ngược.
    selector_variants: dict[str, list[tuple[str, str]]] = {}
    for sel in FAMILY_SELECTORS.values():
        for v in sel.variants:
            selector_variants.setdefault(v.concrete_simulation_id, []).append(
                (sel.family_id.value, v.variant_id)
            )

    ops: dict[str, OperationSpec] = {}
    for sid in sorted(CATALOG):
        spec = CATALOG[sid]
        if ReachabilityLevel.AI_REACHABLE_PUBLIC not in spec.reachability:
            continue
        props = spec.config_schema.get("properties") or {}
        enum_variants = list((props.get("variant") or {}).get("enum") or [])

        for mb in spec.family_memberships:
            fam = mb.family_id.value
            owned = sorted(mb.owned_mechanisms)
            sel_vs = [v for (f, v) in selector_variants.get(sid, []) if f == fam]

            if enum_variants:      # tree / graph: variant nằm trong config
                variants = [(v, None) for v in enum_variants]
            elif sel_vs:           # sorting: variant nằm ở selector
                variants = [(v, None) for v in sel_vs]
            else:                  # không variant: chính target là operation
                variants = [(None, _local_name(sid))]

            for variant, fallback in variants:
                local = variant or fallback or _local_name(sid)
                op_id = f"{fam}{_OP_SEP}{local}"
                ops[op_id] = OperationSpec(
                    operation_id=op_id,
                    family_id=fam,
                    target_id=sid,
                    variant=variant,
                    mechanism=_mechanism_for(fam, variant, owned),
                    label_vi=_LABELS.get(op_id, local),
                )
    return ops


def _mechanism_for(family: str, variant: str | None, owned: list[str]) -> str | None:
    """Mechanism mà operation dùng. Variant → tra bảng dữ liệu; không variant →
    cơ chế DUY NHẤT target sở hữu; target catch-all (nhiều cơ chế) → None."""
    from app.simulation.operation_policy import mechanism_for_variant

    if variant:
        m = mechanism_for_variant(family, variant)
        if m:
            return m
    return owned[0] if len(owned) == 1 else None


_OPERATIONS: dict[str, OperationSpec] | None = None


def OPERATIONS() -> dict[str, OperationSpec]:
    """Registry operation (lazy — CATALOG phải nạp xong trước)."""
    global _OPERATIONS
    if _OPERATIONS is None:
        _OPERATIONS = _build()
    return _OPERATIONS


def analyze_exposed_operations() -> tuple[str, ...]:
    """Enum `requested_operations` cho ANALYZE_SCHEMA — MỌI operation chạy được.

    Khác hẳn `analyze_exposed_values()` (mechanism, chỉ 3 family): mọi family
    đều phơi operation, nên gate completeness nhận được dữ liệu ở MỌI family —
    đúng lỗ hổng RC1-C đo được."""
    return tuple(sorted(OPERATIONS()))


def operations_for_family(family_value: str) -> list[str]:
    return sorted(op for op, s in OPERATIONS().items() if s.family_id == family_value)


def operations_of_target(target_id: str, variant: str | None = None) -> list[str]:
    """Operation mà một target (đã resolve variant nếu có) THỰC SỰ biểu diễn."""
    out = []
    for op, s in OPERATIONS().items():
        if s.target_id != target_id:
            continue
        if variant is not None and s.variant is not None and s.variant != variant:
            continue
        out.append(op)
    return sorted(out)


def operation_labels(operation_ids) -> list[str]:
    """Nhãn tiếng Việt cho học sinh — KHÔNG bao giờ trả id kỹ thuật nếu có nhãn."""
    reg = OPERATIONS()
    return [reg[o].label_vi if o in reg else o for o in operation_ids]


def family_of_operations(operation_ids) -> set[str]:
    return {operation_family(o) for o in operation_ids}


__all__ = [
    "OPERATIONS",
    "OperationSpec",
    "analyze_exposed_operations",
    "family_of_operations",
    "operation_family",
    "operation_labels",
    "operations_for_family",
    "operations_of_target",
]


def _sanity() -> list[str]:
    """Vi phạm cấu trúc (test khoá gọi): mọi operation phải có target thật,
    có nhãn, và id không đụng namespace mechanism."""
    errs = []
    for op, s in OPERATIONS().items():
        if s.family_id not in {f.value for f in FamilyId}:
            errs.append(f"{op}: family lạ {s.family_id}")
        if _OP_SEP not in op:
            errs.append(f"{op}: id operation phải có '{_OP_SEP}'")
        if "." in op:
            errs.append(f"{op}: id operation KHÔNG được mang dấu chấm (đụng mechanism)")
        if op not in _LABELS:
            errs.append(f"{op}: thiếu nhãn tiếng Việt cho học sinh")
    return errs
