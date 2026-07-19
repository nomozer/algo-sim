# -*- coding: utf-8 -*-
"""M16 Task 5 (W5) — kịch bản provider OFFLINE cho TOÀN BỘ pool m16 (50 case).

Module DATA THUẦN: `CaseScript` (analysis / classify-seq / simulate-seq đúng
schema production) + `SCRIPTS` (map case_id → CaseScript) + factory
`build_scripted_provider` (async fake `call_gemini`, KHÔNG import pytest). Task 6
(generator) tái dùng module này; test `tests/test_m16_offline_eval.py` chạy nó
qua production `run_pipeline` (bất biến #22) rồi assert HARD CORRECTNESS.

Nguyên tắc dựng kịch bản (đối chiếu notes TỪNG case trong `datasets/m16_catalog.py`
+ hành vi pipeline THẬT đã đọc — KHÔNG đoán):
- Mọi JSON đúng schema production: analysis theo `ANALYZE_SCHEMA` (đủ 9 required
  key + prescribed_procedure khi case cần tín hiệu cơ chế), config concrete qua
  validator THẬT của từng entry (`app/validation/simulation.py`), FamilySpec
  sorting theo `families/sorting.py` (family_version "sort-fam-1").
- sorting đi qua TOKEN `algorithm.comparison_sort` → stage_simulate_family →
  selector.resolve → validator concrete; script trả FamilySpec, KHÔNG config
  concrete.
- Case unsupported ở classify (status unsupported) KHÔNG tới simulate.
- Case gate chặn TRƯỚC simulate (mechanism/route/computation) → simulate_seq rỗng.
- prescribed_procedure dùng bề mặt analyze-exposed THẬT (sorting = bare legacy
  live-verified M14; positional = namespaced) — `canonical_mechanism` (một
  boundary) chuẩn hoá; metric #1 so `canonical_prescribed` với mech kỳ vọng.

Đường đi CỐ ĐỊNH cho các case đa-nhánh (theo notes):
- m16-nm-hex-gap: đường (A) classify→binary.decimal_to_binary → direct-route
  ownership gate (non_binary_base không sở hữu) → gate_mechanism_ownership.
- m16-cr-positional-fail: đường (a) classify→generic (family mismatch positional)
  → ≤1 reclassify vẫn generic → fail-closed route_mechanism_family_mismatch.
- m16-vb-binary-overrange: attempt1 giữ 300 (validator 0–255 từ chối cấu trúc →
  retry) → attempt2 config hợp lệ → ok (phủ nhánh retry).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from app.simulation.scan_engine import SCAN_VERSION

_SORT_FAMILY_VERSION = "sort-fam-1"


def _j(obj) -> str:
    return json.dumps(obj, ensure_ascii=False)


# ── CaseScript ────────────────────────────────────────────────
@dataclass(frozen=True)
class CaseScript:
    """Kịch bản MỘT case: analysis (dict đúng ANALYZE_SCHEMA), classify_seq
    (list dict {status, simulation_id, reason} — lượt 1 [, lượt 2 khi kỳ vọng
    reclassify]), simulate_seq (list JSON string cho từng simulate attempt;
    rỗng khi không tới simulate)."""

    analysis: dict
    classify_seq: list[dict]
    simulate_seq: list[str] = field(default_factory=list)


# ── builder analysis (đủ required key ANALYZE_SCHEMA) ─────────
def _analysis(
    *,
    goal: str = "Mô phỏng đề bài",
    ownership: str = "provided",
    prescribed: str | None = None,
    scene_construction: str | None = None,
    entity_roles: list[str] | None = None,
    relation_roles: list[str] | None = None,
    process_roles: list[str] | None = None,
    interaction_needs: list[str] | None = None,
    visual_needs: list[str] | None = None,
    temporal_needs: list[str] | None = None,
) -> dict:
    a: dict = {
        "objects": ["đối tượng"],
        "data": [{"description": "dữ liệu của đề"}],
        "relations": [],
        "processes": [],
        "constraints": [],
        "goal": goal,
        "input_description": "đầu vào của đề",
        "output_description": "kết quả mong muốn",
        "result_ownership": ownership,
    }
    if prescribed is not None:
        a["prescribed_procedure"] = prescribed
    if scene_construction is not None:
        a["scene_construction"] = scene_construction
    for key, val in (
        ("entity_roles", entity_roles),
        ("relation_roles", relation_roles),
        ("process_roles", process_roles),
        ("interaction_needs", interaction_needs),
        ("visual_needs", visual_needs),
        ("temporal_needs", temporal_needs),
    ):
        if val is not None:
            a[key] = val
    return a


def _classify(sim_id: str | None, status: str = "ok", reason: str | None = None) -> dict:
    return {"status": status, "simulation_id": sim_id, "reason": reason}


# ── config builders (đúng schema từng validator concrete) ─────
def _algo_cfg(array, *, target=None, condition=None, order=None, summary="Mô phỏng thuật toán") -> str:
    data: dict = {"array": list(array)}
    if target is not None:
        data["target"] = target
    if condition is not None:
        data["condition"] = condition
    if order is not None:
        data["order"] = order
    return _j({"problem": {"summary": summary, "input": "Dãy số", "output": "Kết quả"}, "data": data})


def _sort_spec(variant: str, array, order: str = "asc") -> str:
    return _j(
        {"family_version": _SORT_FAMILY_VERSION, "variant": variant, "array": list(array), "order": order}
    )


def _scan_cfg(array, threshold, op=">") -> str:
    return _j(
        {
            "scan_version": SCAN_VERSION,
            "array": list(array),
            "seed": {"from": "constant", "value": threshold, "varName": "nguong"},
            "compare": {"kind": "to_constant", "op": op, "value": threshold},
            "update": {"kind": "none"},
            "marking": "match_highlight",
            "stop": "first_match",
        }
    )


def _logic_cfg(a=1, b=1) -> str:
    return _j({"inputA": a, "inputB": b})


def _binary_cfg(dec, width=8) -> str:
    return _j({"decimalValue": dec, "bitWidth": width})


def _net_cfg(nodes, links, source, destination) -> str:
    return _j({"nodes": nodes, "links": links, "source": source, "destination": destination})


def _encap_cfg(payload="Dữ liệu ứng dụng") -> str:
    return _j({"payloadLabel": payload})


# ── generic DSL configs (đúng validate_generic_config + semantic) ──
_TRIANGLE_REVEAL = _j(
    {
        "dsl_version": "1.0",
        "title": "Dựng tam giác ABC từng bước",
        "objects": [
            {"id": "A", "type": "node", "label": "A"},
            {"id": "B", "type": "node", "label": "B"},
            {"id": "C", "type": "node", "label": "C"},
            {"id": "AB", "type": "edge", "from": "A", "to": "B"},
            {"id": "AC", "type": "edge", "from": "A", "to": "C"},
            {"id": "BC", "type": "edge", "from": "B", "to": "C"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "reveal_sequence",
                "steps": [
                    {"objects": ["A", "B", "AB"], "narration": "Vẽ đoạn AB"},
                    {"objects": ["C"], "narration": "Thêm điểm C"},
                    {"objects": ["AC", "BC"], "narration": "Nối AC và BC"},
                ],
            }
        ],
    }
)

_MOVING_PATH = _j(
    {
        "dsl_version": "1.0",
        "title": "Robot đi qua các trạm A→B→C→D→E",
        "objects": [
            {"id": "A", "type": "node", "label": "A"},
            {"id": "B", "type": "node", "label": "B"},
            {"id": "C", "type": "node", "label": "C"},
            {"id": "D", "type": "node", "label": "D"},
            {"id": "E", "type": "node", "label": "E"},
            {"id": "robot", "type": "moving_entity", "label": "Robot"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [{"type": "move_along_path", "entity": "robot", "path": ["A", "B", "C", "D", "E"]}],
    }
)

_AND3_GATE = _j(
    {
        "dsl_version": "1.0",
        "title": "Mạch AND ba công tắc",
        "objects": [
            {"id": "a", "type": "switch", "label": "A", "value": 0},
            {"id": "b", "type": "switch", "label": "B", "value": 0},
            {"id": "c", "type": "switch", "label": "C", "value": 0},
            {"id": "den", "type": "lamp", "label": "Đèn"},
        ],
        "rules": [{"type": "boolean", "op": "and", "inputs": ["a", "b", "c"], "target": "den"}],
        "interactions": [
            {"type": "toggle", "target": "a"},
            {"type": "toggle", "target": "b"},
            {"type": "toggle", "target": "c"},
        ],
        "processes": [],
    }
)

_WEB_STATIC = _j(
    {
        "dsl_version": "1.0",
        "title": "Cấu trúc trang web",
        "objects": [
            {"id": "page", "type": "container", "label": "Trang web"},
            {"id": "header", "type": "heading", "text": "Tiêu đề trang", "parent": "page"},
            {"id": "intro", "type": "paragraph", "text": "Đoạn văn giới thiệu.", "parent": "page"},
            {"id": "footer", "type": "paragraph", "text": "Chân trang.", "parent": "page"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [],
    }
)

_STATION_REVEAL = _j(
    {
        "dsl_version": "1.0",
        "title": "Vẽ sơ đồ các trạm theo mô tả",
        "objects": [
            {"id": "s1", "type": "node", "label": "Trạm 1"},
            {"id": "s2", "type": "node", "label": "Trạm 2"},
            {"id": "s3", "type": "node", "label": "Trạm 3"},
            {"id": "e12", "type": "edge", "from": "s1", "to": "s2"},
            {"id": "e23", "type": "edge", "from": "s2", "to": "s3"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {
                "type": "reveal_sequence",
                "steps": [
                    {"objects": ["s1"]},
                    {"objects": ["s2", "e12"]},
                    {"objects": ["s3", "e23"]},
                ],
            }
        ],
    }
)


# ── refusal reasons (classify unsupported thẳng) ──────────────
_TCP_ADVANCED_REASON = (
    "Bắt tay ba bước / máy trạng thái giao thức vượt năng lực v1 — trả unsupported trung thực."
)

# ── canonical mechanism bare/namespaced (bề mặt analyze-exposed THẬT) ──
_P_ADJ = "adjacent_compare_swap"            # → comparison_sort.adjacent_compare_swap
_P_SHIFT = "shift_into_sorted_prefix"       # → comparison_sort.shift_into_sorted_prefix
_P_PARTITION = "partition_recursive"        # → comparison_sort.partition_recursive (không sở hữu)
_P_BINW = "positional_representation.binary_positional_weights"
_P_NONBIN = "positional_representation.non_binary_base"

_TOKEN = "algorithm.comparison_sort"
_GENERIC = "generic.rule_scene"
_BINARY = "binary.decimal_to_binary"


SCRIPTS: dict[str, CaseScript] = {
    # ══════════════ §1 — 14/14 target × (explicit + paraphrase) ══════════════
    # single_pass_scan — find_max
    "m16-findmax-explicit": CaseScript(
        _analysis(goal="Tìm phần tử lớn nhất"),
        [_classify("algorithm.find_max")],
        [_algo_cfg([12, 7, 25, 9, 18, 3], summary="Tìm giá trị lớn nhất")],
    ),
    "m16-findmax-paraphrase": CaseScript(
        _analysis(goal="Tìm người cao nhất"),
        [_classify("algorithm.find_max")],
        [_algo_cfg([165, 172, 158, 180, 169, 174], summary="Tìm giá trị lớn nhất")],
    ),
    # find_min
    "m16-findmin-explicit": CaseScript(
        _analysis(goal="Tìm phần tử nhỏ nhất"),
        [_classify("algorithm.find_min")],
        [_algo_cfg([45, 12, 78, 6, 33, 20], summary="Tìm giá trị nhỏ nhất")],
    ),
    "m16-findmin-paraphrase": CaseScript(
        _analysis(goal="Tìm ngày lạnh nhất"),
        [_classify("algorithm.find_min")],
        [_algo_cfg([18, 15, 21, 12, 19, 14], summary="Tìm giá trị nhỏ nhất")],
    ),
    # sum_if
    "m16-sumif-explicit": CaseScript(
        _analysis(goal="Tính tổng các số lớn hơn 5"),
        [_classify("algorithm.sum_if")],
        [_algo_cfg([6, 11, 4, 9, 15, 3], condition={"op": ">", "value": 5}, summary="Tổng theo điều kiện")],
    ),
    "m16-sumif-paraphrase": CaseScript(
        _analysis(goal="Cộng dồn các khoản lớn"),
        [_classify("algorithm.sum_if")],
        [_algo_cfg([20, 50, 10, 80, 35], condition={"op": ">=", "value": 30}, summary="Tổng theo điều kiện")],
    ),
    # count_if
    "m16-countif-explicit": CaseScript(
        _analysis(goal="Đếm số bạn đạt từ 8 trở lên"),
        [_classify("algorithm.count_if")],
        [_algo_cfg([6, 8.5, 7, 9, 5.5, 8, 4, 9.5], condition={"op": ">=", "value": 8}, summary="Đếm theo điều kiện")],
    ),
    "m16-countif-paraphrase": CaseScript(
        _analysis(goal="Đếm số lần tủ quá ấm"),
        [_classify("algorithm.count_if")],
        [_algo_cfg([3, 6, 2, 8, 5, 7, 1], condition={"op": ">", "value": 4}, summary="Đếm theo điều kiện")],
    ),
    # linear_search
    "m16-linear-explicit": CaseScript(
        _analysis(goal="Tìm 194 trong danh sách"),
        [_classify("algorithm.linear_search")],
        [_algo_cfg([305, 118, 227, 194, 260], target=194, summary="Tìm kiếm tuần tự")],
    ),
    "m16-linear-paraphrase": CaseScript(
        _analysis(goal="Tìm mã 90"),
        [_classify("algorithm.linear_search")],
        [_algo_cfg([71, 34, 90, 12, 58], target=90, summary="Tìm kiếm tuần tự")],
    ),
    # interval_elimination — binary_search
    "m16-binsearch-explicit": CaseScript(
        _analysis(goal="Tìm 30 bằng chia đôi"),
        [_classify("algorithm.binary_search")],
        [_algo_cfg([3, 8, 15, 22, 30, 41, 55], target=30, summary="Tìm kiếm nhị phân")],
    ),
    "m16-binsearch-paraphrase": CaseScript(
        _analysis(goal="Tìm 203 bằng cách xét phần tử giữa"),
        [_classify("algorithm.binary_search")],
        [_algo_cfg([101, 145, 178, 203, 256, 289], target=203, summary="Tìm kiếm nhị phân")],
    ),
    # comparison_sort — bubble (route qua TOKEN, prescribed adjacent_compare_swap)
    "m16-bubble-explicit": CaseScript(
        _analysis(goal="Sắp xếp tăng dần bằng nổi bọt", prescribed=_P_ADJ),
        [_classify(_TOKEN)],
        [_sort_spec("bubble", [9, 4, 7, 2, 6])],
    ),
    "m16-bubble-paraphrase": CaseScript(
        _analysis(goal="Sắp xếp bằng đổi chỗ cặp kề", prescribed=_P_ADJ),
        [_classify(_TOKEN)],
        [_sort_spec("bubble", [8, 3, 6, 1])],
    ),
    # insertion (prescribed shift_into_sorted_prefix)
    "m16-insertion-explicit": CaseScript(
        _analysis(goal="Sắp xếp tăng dần bằng chèn", prescribed=_P_SHIFT),
        [_classify(_TOKEN)],
        [_sort_spec("insertion", [7, 2, 9, 4, 5])],
    ),
    "m16-insertion-paraphrase": CaseScript(
        _analysis(goal="Chèn từng lá bài vào phần đã sắp", prescribed=_P_SHIFT),
        [_classify(_TOKEN)],
        [_sort_spec("insertion", [6, 2, 8, 3, 5])],
    ),
    # single_pass_scan — scan (bounded)
    "m16-scan-explicit": CaseScript(
        _analysis(goal="Tìm ngày đầu tiên vượt 35 độ"),
        [_classify("algorithm.scan")],
        [_scan_cfg([31, 33, 30, 36, 32, 38, 29], 35, op=">")],
    ),
    "m16-scan-paraphrase": CaseScript(
        _analysis(goal="Dừng ở bình đầu tiên ≥ 18 bar"),
        [_classify("algorithm.scan")],
        [_scan_cfg([12, 15, 11, 18, 14, 20], 18, op=">=")],
    ),
    # boolean_composition — logic.and_gate (KHÔNG mechanism-exposed)
    "m16-and-explicit": CaseScript(
        _analysis(goal="Cổng AND hai đầu vào"),
        [_classify("logic.and_gate")],
        [_logic_cfg(0, 0)],
    ),
    "m16-and-paraphrase": CaseScript(
        _analysis(goal="Đầu ra 1 chỉ khi cả hai vào 1"),
        [_classify("logic.and_gate")],
        [_logic_cfg(0, 0)],
    ),
    # positional_representation — binary (prescribed binary_positional_weights)
    "m16-binary-explicit": CaseScript(
        _analysis(goal="Biểu diễn 156 nhị phân", prescribed=_P_BINW),
        [_classify(_BINARY)],
        [_binary_cfg(156, 8)],
    ),
    "m16-binary-paraphrase": CaseScript(
        _analysis(goal="Bật trọng số 128..1 cho tổng 89", prescribed=_P_BINW),
        [_classify(_BINARY)],
        [_binary_cfg(89, 8)],
    ),
    # graph_traversal — packet_routing
    "m16-routing-explicit": CaseScript(
        _analysis(goal="Đường đi gói tin qua các chặng"),
        [_classify("network.packet_routing")],
        [_net_cfg(
            [{"id": "pc", "type": "client"}, {"id": "sw", "type": "switch"},
             {"id": "r1", "type": "router"}, {"id": "isp", "type": "isp"}, {"id": "srv", "type": "server"}],
            [["pc", "sw"], ["sw", "r1"], ["r1", "isp"], ["isp", "srv"]], "pc", "srv",
        )],
    ),
    "m16-routing-paraphrase": CaseScript(
        _analysis(goal="Dữ liệu đi qua từng thiết bị"),
        [_classify("network.packet_routing")],
        [_net_cfg(
            [{"id": "cl", "type": "client"}, {"id": "r1", "type": "router"},
             {"id": "r2", "type": "router"}, {"id": "srv", "type": "server"}],
            [["cl", "r1"], ["r1", "r2"], ["r2", "srv"]], "cl", "srv",
        )],
    ),
    # layered_pdu_transform — encapsulation
    "m16-encap-explicit": CaseScript(
        _analysis(goal="Đóng gói qua các tầng TCP/IP"),
        [_classify("network.protocol_encapsulation")],
        [_encap_cfg("Dữ liệu ứng dụng")],
    ),
    "m16-encap-paraphrase": CaseScript(
        _analysis(goal="Mỗi tầng bọc thêm thông tin"),
        [_classify("network.protocol_encapsulation")],
        [_encap_cfg("Tin nhắn")],
    ),
    # structural_progressive_representation — generic reveal + move
    "m16-generic-reveal": CaseScript(
        _analysis(
            goal="Dựng tam giác ABC từng bước", ownership="provided",
            scene_construction="step_by_step", relation_roles=["relational"], process_roles=["temporal"],
        ),
        [_classify(_GENERIC)],
        [_TRIANGLE_REVEAL],
    ),
    "m16-generic-move": CaseScript(
        _analysis(
            goal="Robot đi qua các trạm", ownership="provided",
            scene_construction="step_by_step", process_roles=["movement", "temporal"],
        ),
        [_classify(_GENERIC)],
        [_MOVING_PATH],
    ),

    # ══════════════ §2 — valid_boundary (8/8 family) ══════════════
    "m16-vb-scan-optional": CaseScript(
        _analysis(goal="Tìm nhiệt độ thấp nhất (cực tiểu trùng, không nhãn)"),
        [_classify("algorithm.find_min")],
        [_algo_cfg([22, 19, 25, 19, 30], summary="Tìm giá trị nhỏ nhất")],
    ),
    "m16-vb-binsearch-absent": CaseScript(
        _analysis(goal="Tìm 17 (vắng mặt) bằng chia đôi"),
        [_classify("algorithm.binary_search")],
        [_algo_cfg([2, 5, 9, 14, 21, 30], target=17, summary="Tìm kiếm nhị phân")],
    ),
    # input CHƯA sắp → validator normalize (auto-sort), vẫn ok
    "m16-vb-binsearch-unsorted": CaseScript(
        _analysis(goal="Tìm 38 bằng chia đôi trên dãy chưa sắp"),
        [_classify("algorithm.binary_search")],
        [_algo_cfg([27, 4, 51, 13, 38, 9], target=38, summary="Tìm kiếm nhị phân")],
    ),
    "m16-vb-sort-duplicates": CaseScript(
        _analysis(goal="Sắp xếp dãy có phần tử trùng", prescribed=_P_ADJ),
        [_classify(_TOKEN)],
        [_sort_spec("bubble", [5, 3, 5, 2, 3])],
    ),
    # anti-merge: AND 3 đầu vào → generic (KHÔNG and_gate)
    "m16-vb-and3-generic": CaseScript(
        _analysis(
            goal="Đèn sáng khi cả BA công tắc bật", ownership="rule_derivable",
            entity_roles=["logical"], interaction_needs=["interactive"],
        ),
        [_classify(_GENERIC)],
        [_AND3_GATE],
    ),
    "m16-vb-binary-zero": CaseScript(
        _analysis(goal="Biểu diễn 0 nhị phân", prescribed=_P_BINW),
        [_classify(_BINARY)],
        [_binary_cfg(0, 8)],
    ),
    "m16-vb-binary-255": CaseScript(
        _analysis(goal="Biểu diễn 255 nhị phân", prescribed=_P_BINW),
        [_classify(_BINARY)],
        [_binary_cfg(255, 8)],
    ),
    # contract-error control: attempt1 giữ 300 (validator 0–255 từ chối) → attempt2 hợp lệ
    "m16-vb-binary-overrange": CaseScript(
        _analysis(goal="Biểu diễn 300 nhị phân (vượt phạm vi)", prescribed=_P_BINW),
        [_classify(_BINARY)],
        [_binary_cfg(300, 8), _binary_cfg(255, 8)],
    ),
    "m16-vb-routing-multipath": CaseScript(
        _analysis(goal="Chọn đường khi có hai router song song"),
        [_classify("network.packet_routing")],
        [_net_cfg(
            [{"id": "cl", "type": "client"}, {"id": "r1", "type": "router"},
             {"id": "r2", "type": "router"}, {"id": "srv", "type": "server"}],
            [["cl", "r1"], ["cl", "r2"], ["r1", "srv"], ["r2", "srv"]], "cl", "srv",
        )],
    ),
    "m16-vb-decapsulation": CaseScript(
        _analysis(goal="Tháo gói ở máy nhận"),
        [_classify("network.protocol_encapsulation")],
        [_encap_cfg("Gói tin nhận")],
    ),
    "m16-vb-web-static": CaseScript(
        _analysis(
            goal="Hiển thị cấu trúc trang web (tĩnh)", ownership="provided",
            scene_construction="prebuilt", entity_roles=["structural", "textual"],
        ),
        [_classify(_GENERIC)],
        [_WEB_STATIC],
    ),

    # ══════════════ §3 — near_miss_gap (group unsupported) ══════════════
    # comparison_sort partition (quicksort) → mechanism gate tầng 1
    "m16-nm-sort-partition": CaseScript(
        _analysis(goal="Sắp xếp bằng chia quanh mốc + đệ quy", ownership="algorithmic", prescribed=_P_PARTITION),
        [_classify(_TOKEN)],
    ),
    # single_pass_scan — vòng lặp biến tự do (không dãy) → computation gate (algorithmic + gap role)
    "m16-nm-freevar-loop": CaseScript(
        _analysis(
            goal="Mô phỏng x nhân đôi tới khi vượt 100", ownership="algorithmic",
            process_roles=["arbitrary_algorithm"],
        ),
        [_classify(_GENERIC)],
    ),
    # interval_elimination — nội suy (không mechanism-exposed) → computation gate (algorithmic)
    "m16-nm-interpolation": CaseScript(
        _analysis(goal="Tìm 47 bằng đoán vị trí theo tỉ lệ", ownership="algorithmic"),
        [_classify(_GENERIC)],
    ),
    # boolean_composition — ngưỡng k-of-n (numeric_threshold role gap, KHÔNG algorithmic)
    "m16-nm-threshold-kofn": CaseScript(
        _analysis(
            goal="Đèn sáng khi ít nhất 2/4 cảm biến", ownership="rule_derivable",
            process_roles=["numeric_threshold"],
        ),
        [_classify(_GENERIC)],
    ),
    # positional_representation — hex, đường (A): classify binary → direct ownership gate
    "m16-nm-hex-gap": CaseScript(
        _analysis(goal="Đổi 2026 sang thập lục phân", ownership="rule_derivable", prescribed=_P_NONBIN),
        [_classify(_BINARY)],
    ),
    # graph_traversal — Dijkstra (không mechanism-exposed) → computation gate (algorithmic)
    "m16-nm-weighted-shortest": CaseScript(
        _analysis(goal="Đường ngắn nhất theo tổng độ dài", ownership="algorithmic"),
        [_classify(_GENERIC)],
    ),
    # layered_pdu_transform — TCP handshake → classify unsupported thẳng
    "m16-nm-tcp-handshake": CaseScript(
        _analysis(goal="Bắt tay ba bước TCP", ownership="rule_derivable"),
        [_classify(None, status="unsupported", reason=_TCP_ADVANCED_REASON)],
    ),

    # ══════════════ §4 — cross_family_recovery ══════════════
    # (a) recovery-SUCCESS: classify1 generic (family mismatch) → reclassify → binary → ok
    "m16-cr-positional-recover": CaseScript(
        _analysis(goal="Biểu diễn 45 bằng công tắc trọng số", ownership="provided", prescribed=_P_BINW),
        [_classify(_GENERIC), _classify(_BINARY)],
        [_binary_cfg(45, 6)],
    ),
    # (b) recovery-FAILURE: classify1 generic, reclassify vẫn generic → fail-closed mismatch
    "m16-cr-positional-fail": CaseScript(
        _analysis(goal="Biểu diễn 68 hệ cơ số 5", ownership="rule_derivable", prescribed=_P_NONBIN),
        [_classify(_GENERIC), _classify(_GENERIC)],
    ),

    # ══════════════ §5 — authority_control ══════════════
    # (a) computation-LEAK control: classify generic + algorithmic → computation gate
    "m16-ac-computation-leak": CaseScript(
        _analysis(goal="Vẽ sơ đồ trạm rồi TÍNH đường ngắn nhất có trọng số", ownership="algorithmic"),
        [_classify(_GENERIC)],
    ),
    # (b) representation ĐỐI CHỨNG: chỉ vẽ theo mô tả cho sẵn → generic ok
    "m16-ac-representation-ok": CaseScript(
        _analysis(
            goal="Vẽ sơ đồ các trạm, hiện dần từng trạm", ownership="provided",
            scene_construction="step_by_step", relation_roles=["relational"], process_roles=["temporal"],
        ),
        [_classify(_GENERIC)],
        [_STATION_REVEAL],
    ),
}


# ── provider factory (async fake call_gemini) — DÙNG CHUNG test + Task 6 ──
def build_scripted_provider(script: CaseScript):
    """Trả (fake_call_gemini, counts). Dispatch theo marker user_text như
    `tests/test_pipeline_mechanism_consistency.py::_mock`:
    - "DANH MỤC MÔ PHỎNG" (catalog_text) → classify (đếm lượt → classify_seq[i];
      reclassify lượt 2 vẫn chứa marker này nên CHECK classify TRƯỚC simulate —
      extra_note reclassify có chứa cụm "simulation_id đã chọn").
    - "simulation_id đã chọn" → simulate attempt kế tiếp.
    - còn lại → analysis.
    counts giúp assert budget call (analyze==1, classify≤2, simulate≤len)."""
    counts = {"analyze": 0, "classify": 0, "simulate": 0}
    idx = {"c": 0, "s": 0}
    analysis_json = _j(script.analysis)
    classify_json = [_j(c) for c in script.classify_seq]
    simulate_seq = list(script.simulate_seq)

    async def fake(api_key, system_prompt, user_text, response_schema=None, temperature=0.2, image=None):
        if "DANH MỤC MÔ PHỎNG" in user_text:
            counts["classify"] += 1
            r = classify_json[min(idx["c"], len(classify_json) - 1)] if classify_json else _j(_classify(None, "unsupported"))
            idx["c"] += 1
            return r
        if "simulation_id đã chọn" in user_text:
            counts["simulate"] += 1
            r = simulate_seq[min(idx["s"], len(simulate_seq) - 1)] if simulate_seq else "{}"
            idx["s"] += 1
            return r
        counts["analyze"] += 1
        return analysis_json

    return fake, counts


__all__ = ["CaseScript", "SCRIPTS", "build_scripted_provider"]
