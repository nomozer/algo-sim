"""M17-Lite Wave 0 — Authenticity contract máy-đọc cho từng AI-reachable target.

Trả lời câu hỏi: "mô phỏng này THẬT đến đâu?" bằng dữ liệu máy-đọc thay vì
lời văn. Mỗi target public khai:

- ``required_state_fields``  — field state mà engine FE tất định SỞ HỮU
  (đúng tên field trong model.ts của domain — cross-lock vitest chạy engine
  thật trên sample config và soi ``Object.keys(state)``);
- ``required_trace_events``  — loại event/step timeline mà trace tất định
  phải phát (đúng ``TraceEvent.type`` / delta kind thật; RỖNG với module
  exploratory không timeline);
- ``required_result_fields`` — kết quả authoritative (field state hoặc TÊN
  hàm dẫn xuất tất định trong model.ts — kết quả KHÔNG BAO GIỜ từ LLM);
- ``renderer_semantic_requirements`` — điều renderer phải thể hiện đúng ngữ
  nghĩa (tài liệu máy-đọc cho khâu audit UI; không phải pixel spec);
- ``generic_allowed``        — True DUY NHẤT cho generic.rule_scene (mọi
  target khác không được "trôi" sang generic — audit soi);
- ``near_miss_mechanisms``   — cơ chế lân cận mà target/family này KHÔNG sở
  hữu → prompt chạm cơ chế đó phải capability_gap (mỗi giá trị sinh một audit
  case near-miss; khớp INTENTIONAL_GAP_MECHANISMS qua lock).

Nguyên tắc (theo mechanisms.py): module này KHÔNG import catalog (chống vòng
import) — mọi cross-lock với CATALOG sống ở test (test_authenticity_contract).
Contract được nhúng vào ``capability_descriptors()`` (catalog.py) → artifact
``capability-descriptors.json`` sync-locked, FE cross-lock đọc từ đó.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuthenticityContract:
    required_state_fields: tuple[str, ...]
    required_trace_events: tuple[str, ...]
    required_result_fields: tuple[str, ...]
    renderer_semantic_requirements: tuple[str, ...]
    generic_allowed: bool = False
    near_miss_mechanisms: tuple[str, ...] = ()


# ── domain algorithm (core/algorithms.ts + trace-builder) ──────────────
# State thật: AlgorithmSimState = {config, trace, branch, cursor} — branch là
# what-if tùy chọn, KHÔNG required. Event thật đọc từ core/algorithms.ts theo
# từng hàm run* (không bịa): find_max/min dùng "compare" (không phải
# compare_value), scan dùng compare_value theo nhánh to_constant.
_ALGO_STATE = ("config", "trace", "cursor")
_ALGO_RENDER = ("array_columns", "narration_per_step", "pseudocode_line")


def _algo(events: tuple[str, ...], *, near_miss: tuple[str, ...] = ()) -> AuthenticityContract:
    return AuthenticityContract(
        required_state_fields=_ALGO_STATE,
        required_trace_events=events,
        required_result_fields=("done.result",),
        renderer_semantic_requirements=_ALGO_RENDER,
        near_miss_mechanisms=near_miss,
    )


# Near-miss của family comparison_sort (INTENTIONAL_GAP): khai trên các target
# sort — matrix dedupe theo mechanism nên mỗi cơ chế sinh ĐÚNG MỘT case.
# M17 W1: select_extreme_repeated flip owned (selection_sort) → rời khỏi near-miss.
_SORT_NEAR_MISS = (
    "comparison_sort.partition_recursive",
    "comparison_sort.other_unspecified",
)

AUTHENTICITY_CONTRACTS: dict[str, AuthenticityContract] = {
    # single_pass_scan — 5 bài chuyên biệt + scan catch-all
    "algorithm.find_max": _algo(("assign_var", "compare", "done")),
    "algorithm.find_min": _algo(("assign_var", "compare", "done")),
    "algorithm.sum_if": _algo(("assign_var", "compare_value", "done")),
    "algorithm.count_if": _algo(("assign_var", "compare_value", "done")),
    "algorithm.linear_search": _algo(("assign_var", "compare_value", "done")),
    # interval_elimination
    "algorithm.binary_search": _algo(("set_range", "compare_value", "done")),
    # comparison_sort (route qua selector token; envelope là id concrete)
    "algorithm.bubble_sort": _algo(("compare", "swap", "mark", "done"), near_miss=_SORT_NEAR_MISS),
    "algorithm.insertion_sort": _algo(
        ("compare", "shift", "insert", "mark", "done"), near_miss=_SORT_NEAR_MISS
    ),
    # M17 W1 — Selection Sort: set_range = vùng chưa sắp, assign_var = vị trí
    # cực trị đang nhớ, swap/mark = đưa về đầu + ranh giới đã sắp.
    "algorithm.selection_sort": _algo(
        ("set_range", "assign_var", "compare", "swap", "mark", "done"),
        near_miss=_SORT_NEAR_MISS,
    ),
    # scan catch-all (ScanSimState = {spec, trace, cursor})
    "algorithm.scan": AuthenticityContract(
        required_state_fields=("spec", "trace", "cursor"),
        required_trace_events=("assign_var", "compare_value", "done"),
        required_result_fields=("done.result",),
        renderer_semantic_requirements=_ALGO_RENDER,
    ),
    # logic — exploratory, không timeline; output là hàm dẫn xuất andOutput
    "logic.and_gate": AuthenticityContract(
        required_state_fields=("inputA", "inputB"),
        required_trace_events=(),
        required_result_fields=("andOutput",),
        renderer_semantic_requirements=("gate_diagram", "output_lamp_reflects_rule"),
    ),
    # binary — exploratory; decimal/binaryString dẫn xuất tất định từ bits
    # (M17 W1: near-miss non_binary_base đã flip owned → binary.base_conversion)
    "binary.decimal_to_binary": AuthenticityContract(
        required_state_fields=("bits", "bitWidth"),
        required_trace_events=(),
        required_result_fields=("decimalOf", "binaryString"),
        renderer_semantic_requirements=("place_values_row", "bit_cells"),
    ),
    # M17 W1 — base conversion tổng quát: progressive, step kinds là event
    # thật của engine (divide 10→X, weight X→10, cả hai + stage khi X→Y).
    "binary.base_conversion": AuthenticityContract(
        required_state_fields=("config", "decimalValue", "steps", "result", "cursor"),
        required_trace_events=("divide", "weight", "result"),
        required_result_fields=("result",),
        renderer_semantic_requirements=(
            "division_or_weight_rows", "digit_assembly", "narration_per_step",
        ),
    ),
    # M17 W1 — mạch nhiều cổng: hybrid (timeline đánh giá topo + toggle);
    # truth table đủ 2^n hàng là kết quả authoritative của engine.
    "logic.boolean_dag": AuthenticityContract(
        required_state_fields=("config", "values", "evalOrder", "nodeOutputs", "steps", "truthTable", "cursor"),
        required_trace_events=("eval", "result"),
        required_result_fields=("nodeOutputs", "truthTable"),
        renderer_semantic_requirements=(
            "gate_table_with_engine_outputs", "truth_table_panel", "narration_per_step",
        ),
    ),
    # network.packet_routing — route BFS engine tính, KHÔNG từ LLM
    "network.packet_routing": AuthenticityContract(
        required_state_fields=("nodes", "links", "source", "destination", "route", "steps", "cursor"),
        required_trace_events=("packetAt",),
        required_result_fields=("route",),
        renderer_semantic_requirements=("graph_topology", "packet_position_per_step", "narration_per_step"),
    ),
    # M17 W1 — duyệt đồ thị BFS/DFS: frontier (queue/stack), thứ tự thăm,
    # đường đi dựng lại; unreachable là result hợp lệ (reachable field).
    "network.graph_traversal": AuthenticityContract(
        required_state_fields=(
            "config", "frontierKind", "steps", "visitedOrder", "path", "reachable", "cursor",
        ),
        required_trace_events=("visit", "result"),
        required_result_fields=("visitedOrder", "path", "reachable"),
        renderer_semantic_requirements=(
            "graph_nodes_edges", "frontier_panel_queue_or_stack", "visited_order_strip",
            "path_highlight", "narration_per_step",
        ),
    ),
    # network.protocol_encapsulation — 9 bước PDU với delta tường minh
    "network.protocol_encapsulation": AuthenticityContract(
        required_state_fields=("payloadLabel", "layers", "steps", "cursor"),
        required_trace_events=("add", "remove", "transmit", "deliver"),
        required_result_fields=("steps.final_pdu",),
        renderer_semantic_requirements=("layer_stacks_sender_receiver", "pdu_segments", "narration_per_step"),
    ),
    # generic — biểu diễn cấu trúc + reveal/move khai báo; computation CHỈ cho
    # boolean rule DAG (M11). KHÔNG sở hữu kết quả thuật toán (bất biến #21).
    "generic.rule_scene": AuthenticityContract(
        required_state_fields=("spec", "base", "pos", "timeline", "cursor"),
        required_trace_events=("reveal", "move"),
        required_result_fields=("rule_derived_values",),
        renderer_semantic_requirements=("declared_objects_only", "frame_visibility", "entity_position_by_node_id"),
        generic_allowed=True,
    ),
}


def authenticity_descriptor(sim_id: str) -> dict | None:
    """Serialize contract cho capability_descriptors() (catalog.py) — máy-đọc,
    sync-locked qua capability-descriptors.json."""
    c = AUTHENTICITY_CONTRACTS.get(sim_id)
    if c is None:
        return None
    return {
        "required_state_fields": list(c.required_state_fields),
        "required_trace_events": list(c.required_trace_events),
        "required_result_fields": list(c.required_result_fields),
        "renderer_semantic_requirements": list(c.renderer_semantic_requirements),
        "generic_allowed": c.generic_allowed,
        "near_miss_mechanisms": list(c.near_miss_mechanisms),
    }
