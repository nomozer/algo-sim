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


# ══════════════ §C1.1 — SEMANTIC OPERATION ══════════════
# Bài học từ live L1-V4: `(target, variant)` TRỘN hai khái niệm khác nhau —
# NGƯỜI DÙNG MUỐN LÀM GÌ (semantic operation) và AI THỰC HIỆN (implementation
# target). Cùng một đề mạch logic, analyze lúc gợi ý `rule_scene` lúc gợi ý
# `boolean_dag`; đó là target hint dao động TRONG CÙNG family, không phải hai
# yêu cầu độc lập. Coi chúng là hai yêu cầu ⇒ TỪ CHỐI OAN đề hợp lệ.
#
# Nguyên tắc: **route được quyền chọn implementation, KHÔNG được quyền viết lại
# hay xoá yêu cầu semantic của người dùng.** Vì vậy so sánh completeness diễn ra
# ở tầng semantic, còn target chỉ khai nó *satisfy* được semantic nào.


@dataclass(frozen=True)
class SemanticRequirement:
    """Danh tính semantic của MỘT yêu cầu. Chỉ gộp khi TRÙNG HOÀN TOÀN."""

    operation_id: str          # "tree.traverse", "scan.find_max"
    variant_id: str | None = None   # "preorder", "bfs", "bubble", "10->2"
    goal_id: str | None = None      # dành cho yêu cầu cùng operation khác mục tiêu

    def as_dict(self) -> dict:
        return {"semantic_operation_id": self.operation_id,
                "semantic_variant_id": self.variant_id,
                "semantic_goal_id": self.goal_id}

    def label_key(self) -> str:
        v = f"/{self.variant_id}" if self.variant_id else ""
        return f"{self.operation_id}{v}"


# Ánh xạ operation CỤ THỂ → yêu cầu SEMANTIC. Dữ liệu thuần; thêm target/variant
# mới mà quên khai ⇒ test khoá đỏ (không lặng lẽ dùng target id làm operation id).
SEMANTIC_OPERATION_MAP: dict[str, SemanticRequirement] = {
    # scan — MỖI mục tiêu là MỘT operation riêng, dù dùng chung cơ chế
    # `track_extreme`. Đây chính là ca max+min: KHÔNG BAO GIỜ được gộp.
    "single_pass_scan:find_max": SemanticRequirement("scan.find_max"),
    "single_pass_scan:find_min": SemanticRequirement("scan.find_min"),
    "single_pass_scan:sum_if": SemanticRequirement("scan.sum_conditional"),
    "single_pass_scan:count_if": SemanticRequirement("scan.count_conditional"),
    "single_pass_scan:linear_search": SemanticRequirement("scan.find_equal"),
    "single_pass_scan:scan": SemanticRequirement("scan.configured_pass"),
    # tìm kiếm nhị phân
    "interval_elimination:binary_search": SemanticRequirement("sequence.binary_search"),
    # sắp xếp — CÙNG operation, KHÁC variant ⇒ không gộp
    "comparison_sort:bubble": SemanticRequirement("sequence.sort", "bubble"),
    "comparison_sort:insertion": SemanticRequirement("sequence.sort", "insertion"),
    "comparison_sort:selection": SemanticRequirement("sequence.sort", "selection"),
    # đổi cơ số — decimal_to_binary là ĐÚNG MỘT phép 10→2; base_conversion là
    # cùng operation nhưng CHƯA nêu cặp cơ số (kém cụ thể hơn ⇒ bị hấp thụ).
    "positional_representation:decimal_to_binary":
        SemanticRequirement("number.convert_base", "10->2"),
    "positional_representation:base_conversion":
        SemanticRequirement("number.convert_base"),
    # duyệt cây — CÙNG operation, KHÁC variant ⇒ không gộp
    "tree_traversal:preorder": SemanticRequirement("tree.traverse", "preorder"),
    "tree_traversal:inorder": SemanticRequirement("tree.traverse", "inorder"),
    "tree_traversal:postorder": SemanticRequirement("tree.traverse", "postorder"),
    "tree_traversal:level_order": SemanticRequirement("tree.traverse", "level_order"),
    # duyệt đồ thị — CÙNG operation, KHÁC variant ⇒ không gộp
    "graph_traversal:bfs": SemanticRequirement("graph.traverse", "bfs"),
    "graph_traversal:dfs": SemanticRequirement("graph.traverse", "dfs"),
    # định tuyến gói tin KHÁC duyệt đồ thị (mục tiêu khác, kết quả khác)
    "graph_traversal:packet_routing": SemanticRequirement("network.route_packet"),
    # mạch logic — BA target khác nhau cùng đáp ứng MỘT yêu cầu "tính biểu thức
    # logic". Đây là chỗ live V4 dao động, và là chỗ ĐƯỢC PHÉP gộp.
    "boolean_composition:and_gate": SemanticRequirement("boolean.evaluate_expression"),
    "boolean_composition:boolean_dag": SemanticRequirement("boolean.evaluate_expression"),
    "boolean_composition:rule_scene": SemanticRequirement("boolean.evaluate_expression"),
    # đóng gói PDU
    "layered_pdu_transform:protocol_encapsulation":
        SemanticRequirement("network.encapsulate_pdu"),
    # cảnh biểu diễn hiện dần (KHÁC family với rule_scene logic ở trên)
    "structural_progressive_representation:rule_scene":
        SemanticRequirement("scene.represent_progressive"),
    # W2B — CÁC TẦNG của một truy vấn là các operation KHÁC NHAU (không gộp);
    # năm hàm tổng hợp cùng operation `table.aggregate` nhưng KHÁC variant nên
    # "đếm" và "tính tổng" vẫn là hai yêu cầu riêng.
    "relational_table_query:filter": SemanticRequirement("table.filter_rows"),
    "relational_table_query:projection": SemanticRequirement("table.project_columns"),
    "relational_table_query:sort": SemanticRequirement("table.sort_rows"),
    "relational_table_query:limit": SemanticRequirement("table.limit_rows"),
    "relational_table_query:count": SemanticRequirement("table.aggregate", "count"),
    "relational_table_query:sum": SemanticRequirement("table.aggregate", "sum"),
    "relational_table_query:avg": SemanticRequirement("table.aggregate", "avg"),
    "relational_table_query:min": SemanticRequirement("table.aggregate", "min"),
    "relational_table_query:max": SemanticRequirement("table.aggregate", "max"),
}


def semantic_of(operation_id: str) -> SemanticRequirement | None:
    return SEMANTIC_OPERATION_MAP.get(operation_id)


def requirements_from_structured(analysis: dict) -> list[SemanticRequirement]:
    """M17 W2B-S1 — đọc `requested_requirements` (có mục tiêu) → yêu cầu semantic
    KÈM `goal_id` là chữ ký tất định. Trường lạ/operation lạ bị bỏ qua."""
    from app.simulation.goal_signature import canonical_goal_signature

    if not isinstance(analysis, dict):
        return []
    raw = analysis.get("requested_requirements")
    if not isinstance(raw, list):
        return []
    out: list[SemanticRequirement] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        base = SEMANTIC_OPERATION_MAP.get(item.get("operation"))
        if base is None:
            continue
        req = SemanticRequirement(base.operation_id, base.variant_id,
                                  canonical_goal_signature(item))
        if req not in out:
            out.append(req)
    return out


def query_keys_of(analysis: dict, families: set[str]) -> list[str | None]:
    """Định danh các TRUY VẤN ĐỘC LẬP mà đề yêu cầu, trong phạm vi family."""
    from app.simulation.goal_signature import query_key

    if not isinstance(analysis, dict):
        return []
    raw = analysis.get("requested_requirements")
    if not isinstance(raw, list):
        return []
    keys: list[str | None] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        base = SEMANTIC_OPERATION_MAP.get(item.get("operation"))
        if base is None or operation_family(item["operation"]) not in families:
            continue
        k = query_key(item, item.get("query_group"))
        if k not in keys:
            keys.append(k)
    return keys


def canonical_requirements(operation_ids) -> list[SemanticRequirement]:
    """Gợi ý target/mechanism thô → YÊU CẦU SEMANTIC chuẩn hoá.

    Hai luật gộp, cả hai đều bảo toàn ý người dùng:
    1. TRÙNG HOÀN TOÀN danh tính semantic → một yêu cầu (vd rule_scene và
       boolean_dag đều là `boolean.evaluate_expression`);
    2. HẤP THỤ KÉM-CỤ-THỂ: yêu cầu không nêu variant bị hấp thụ bởi yêu cầu
       CÙNG operation CÓ variant (vd "đổi cơ số" + "đổi 10→2" = một việc).

    KHÔNG BAO GIỜ gộp khi khác `operation_id` (max vs min) hoặc khác
    `variant_id` (bfs vs dfs, bubble vs insertion, preorder vs inorder).
    """
    reqs: list[SemanticRequirement] = []
    for op in operation_ids:
        r = SEMANTIC_OPERATION_MAP.get(op)
        if r is not None and r not in reqs:
            reqs.append(r)
    with_variant = {r.operation_id for r in reqs if r.variant_id}
    kept = [r for r in reqs if r.variant_id or r.operation_id not in with_variant]
    return sorted(kept, key=lambda r: (r.operation_id, r.variant_id or "", r.goal_id or ""))


def satisfies_semantic_operations(target_id: str, variant: str | None = None) -> list[SemanticRequirement]:
    """Yêu cầu semantic mà TARGET (kèm variant đã resolve) đáp ứng được.

    Target khai qua chính operation nó sở hữu — không có bảng thứ hai để lệch."""
    return sorted(
        {
            r for op in operations_of_target(target_id, variant)
            if (r := SEMANTIC_OPERATION_MAP.get(op)) is not None
        },
        key=lambda r: (r.operation_id, r.variant_id or "", r.goal_id or ""),
    )


def semantic_label(req: SemanticRequirement) -> str:
    """Nhãn tiếng Việt cho học sinh — lấy từ operation cụ thể đầu tiên khớp."""
    for op, r in SEMANTIC_OPERATION_MAP.items():
        if r == req:
            spec = OPERATIONS().get(op)
            if spec is not None:
                return spec.label_vi
    return req.label_key()


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
    # W2B — mỗi tầng của MỘT truy vấn bảng
    "relational_table_query:filter": "lọc dòng theo điều kiện",
    "relational_table_query:projection": "chọn cột cần hiển thị",
    "relational_table_query:sort": "sắp xếp bảng",
    "relational_table_query:limit": "lấy số dòng đầu",
    "relational_table_query:count": "đếm số dòng",
    "relational_table_query:sum": "tính tổng một cột",
    "relational_table_query:avg": "tính trung bình một cột",
    "relational_table_query:min": "tìm giá trị nhỏ nhất của cột",
    "relational_table_query:max": "tìm giá trị lớn nhất của cột",
}


def _local_name(target_id: str) -> str:
    """Tên cục bộ của target (`algorithm.find_max` → `find_max`)."""
    return target_id.split(".", 1)[1]


# Target mà operation KHÔNG suy được từ `variant` (không có variant enum, không
# nấp sau selector). W2B: một truy vấn bảng gồm NHIỀU TẦNG nối tiếp — mỗi tầng
# là một operation, và đó chính là lý do family này có cardinality `pipeline`.
EXPLICIT_TARGET_OPERATIONS: dict[str, tuple[str, ...]] = {
    "database.relational_table_query": (
        "filter", "projection", "sort", "limit", "count", "sum", "avg", "min", "max",
    ),
}


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

            explicit = EXPLICIT_TARGET_OPERATIONS.get(sid)
            if explicit:           # target khai tường minh (W2B: tầng pipeline)
                variants = [(None, name) for name in explicit]
            elif enum_variants:    # tree / graph: variant nằm trong config
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
    "SEMANTIC_OPERATION_MAP",
    "OperationSpec",
    "SemanticRequirement",
    "analyze_exposed_operations",
    "canonical_requirements",
    "satisfies_semantic_operations",
    "semantic_label",
    "semantic_of",
    "family_of_operations",
    "operation_family",
    "operation_labels",
    "operations_for_family",
    "operations_of_target",
]


def _sanity() -> list[str]:
    """Vi phạm cấu trúc (test khoá gọi): mọi operation phải có target thật,
    có nhãn, có ánh xạ semantic, và id không đụng namespace mechanism."""
    errs = []
    for op in OPERATIONS():
        if op not in SEMANTIC_OPERATION_MAP:
            errs.append(f"{op}: thiếu ánh xạ semantic (target id KHÔNG được tự "
                        "động thành operation id)")
    for op in SEMANTIC_OPERATION_MAP:
        if op not in OPERATIONS():
            errs.append(f"{op}: ánh xạ semantic trỏ operation không tồn tại")
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
