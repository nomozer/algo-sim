# -*- coding: utf-8 -*-
"""M17-Lite W0 — fixture audit authenticity: kịch bản per-target + control.

DATA THUẦN (không import pytest, không network). Mỗi AI-reachable target khai
một ``TargetFixture`` gồm đề bài VI + kịch bản provider cho 3–4 archetype
(direct / paraphrase / changed_input / boundary). Control fixture gồm:
near-miss (mỗi cơ chế INTENTIONAL_GAP đúng MỘT case), leak-control,
refusal-control, và 2 case regression duyệt cây (honest + adversarial probe).

Tái dùng builder của ``m16_offline_scripts`` (import tên "_private" CÓ CHỦ
ĐÍCH — đó là nguồn duy nhất về SHAPE kịch bản đúng schema production đã
live-proven; copy lại = tạo nguồn sự thật thứ hai, vi phạm anti-pattern #1;
module m16 giữ nguyên 0 diff). Case matrix KHÔNG hard-code theo test ID:
``authenticity_matrix.build_audit_cases`` duyệt CATALOG thật — target mới
thiếu fixture sẽ đỏ ở lock, không lặng lẽ bị bỏ qua.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.evaluation.m16_offline_scripts import (  # noqa: F401 — tái dùng có chủ đích
    CaseScript,
    build_scripted_provider,
    _algo_cfg,
    _analysis,
    _AND3_GATE,
    _binary_cfg,
    _classify,
    _encap_cfg,
    _j,
    _logic_cfg,
    _MOVING_PATH,
    _net_cfg,
    _scan_cfg,
    _sort_spec,
    _STATION_REVEAL,
    _TRIANGLE_REVEAL,
)

_TOKEN = "algorithm.comparison_sort"
_GENERIC = "generic.rule_scene"
_BINARY = "binary.decimal_to_binary"

# bề mặt analyze-exposed THẬT (bare legacy sorting + positional namespaced)
_P_ADJ = "adjacent_compare_swap"
_P_SHIFT = "shift_into_sorted_prefix"
_P_SELECT = "select_extreme_repeated"
_P_PARTITION = "partition_recursive"
_P_OTHER = "other_unspecified"
_P_BINW = "positional_representation.binary_positional_weights"
_P_NONBIN = "positional_representation.non_binary_base"

OK_ARCHETYPES = ("direct", "paraphrase", "changed_input", "boundary")


def _baseconv_cfg(source: int, target: int, value: str) -> str:
    """Config binary.base_conversion (M17 W1) — đúng schema validator BE."""
    return _j({"sourceBase": source, "targetBase": target, "inputValue": value})


def _booldag_cfg(inputs: list, gates: list, output: str) -> str:
    """Config logic.boolean_dag (M17 W1) — đúng schema validator BE."""
    return _j({"inputs": inputs, "gates": gates, "output": output})


def _traverse_cfg(nodes: list, edges: list, start: str, variant: str,
                  goal: str | None = None, directed: bool = False) -> str:
    """Config network.graph_traversal (M17 W1) — đúng schema validator BE."""
    cfg: dict = {
        "nodes": [{"id": n} for n in nodes],
        "edges": edges,
        "start": start,
        "variant": variant,
        "directed": directed,
    }
    if goal is not None:
        cfg["goal"] = goal
    return _j(cfg)


@dataclass(frozen=True)
class TargetFixture:
    """Kịch bản audit cho MỘT target: archetype → (đề VI, CaseScript).
    ``expected_route`` mặc định = chính sim_id (sorting: concrete id sau
    selector resolve — vẫn chính sim_id vì audit gắn fixture theo target)."""

    prompts: dict[str, str]
    scripts: dict[str, CaseScript]


@dataclass(frozen=True)
class ControlFixture:
    """Case kiểm soát: near-miss gap / leak-control / refusal / probe."""

    case_id: str
    kind: str  # "near_miss" | "leak_control" | "refusal_control" | "leak_probe"
    prompt: str
    script: CaseScript
    mechanism: str | None = None
    expected_status: str = "unsupported"
    note: str = ""


# ══════════════ fixture per-target (14 AI-reachable) ══════════════
TARGET_FIXTURES: dict[str, TargetFixture] = {
    "algorithm.find_max": TargetFixture(
        prompts={
            "direct": "Cho dãy số 12, 7, 25, 9, 18. Tìm phần tử lớn nhất.",
            "paraphrase": "Bốn bạn có chiều cao 165, 172, 158, 180 cm. Ai cao nhất?",
            "changed_input": "Cho dãy 4, 9, 1, 16, 7, 3. Giá trị lớn nhất là bao nhiêu?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm phần tử lớn nhất"),
                [_classify("algorithm.find_max")],
                [_algo_cfg([12, 7, 25, 9, 18], summary="Tìm giá trị lớn nhất")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Tìm người cao nhất"),
                [_classify("algorithm.find_max")],
                [_algo_cfg([165, 172, 158, 180], summary="Tìm giá trị lớn nhất")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm giá trị lớn nhất của dãy khác"),
                [_classify("algorithm.find_max")],
                [_algo_cfg([4, 9, 1, 16, 7, 3], summary="Tìm giá trị lớn nhất")],
            ),
        },
    ),
    "algorithm.find_min": TargetFixture(
        prompts={
            "direct": "Cho dãy 45, 12, 78, 6, 33. Tìm phần tử nhỏ nhất.",
            "paraphrase": "Nhiệt độ các ngày là 18, 15, 21, 12, 19 độ. Ngày nào lạnh nhất?",
            "changed_input": "Cho dãy 7, 3, 11, 2, 9, 5. Số nhỏ nhất là số nào?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm phần tử nhỏ nhất"),
                [_classify("algorithm.find_min")],
                [_algo_cfg([45, 12, 78, 6, 33], summary="Tìm giá trị nhỏ nhất")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Tìm ngày lạnh nhất"),
                [_classify("algorithm.find_min")],
                [_algo_cfg([18, 15, 21, 12, 19], summary="Tìm giá trị nhỏ nhất")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm giá trị nhỏ nhất của dãy khác"),
                [_classify("algorithm.find_min")],
                [_algo_cfg([7, 3, 11, 2, 9, 5], summary="Tìm giá trị nhỏ nhất")],
            ),
        },
    ),
    "algorithm.sum_if": TargetFixture(
        prompts={
            "direct": "Cho dãy 6, 11, 4, 9, 15, 3. Tính tổng các số lớn hơn 5.",
            "paraphrase": "Các khoản chi 20, 50, 10, 80, 35 nghìn. Cộng những khoản từ 30 nghìn trở lên.",
            "changed_input": "Cho dãy 2, 14, 8, 5, 20. Tổng các số lớn hơn 7 là bao nhiêu?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tính tổng các số lớn hơn 5"),
                [_classify("algorithm.sum_if")],
                [_algo_cfg([6, 11, 4, 9, 15, 3], condition={"op": ">", "value": 5}, summary="Tổng theo điều kiện")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Cộng dồn các khoản lớn"),
                [_classify("algorithm.sum_if")],
                [_algo_cfg([20, 50, 10, 80, 35], condition={"op": ">=", "value": 30}, summary="Tổng theo điều kiện")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tổng các số lớn hơn 7"),
                [_classify("algorithm.sum_if")],
                [_algo_cfg([2, 14, 8, 5, 20], condition={"op": ">", "value": 7}, summary="Tổng theo điều kiện")],
            ),
        },
    ),
    "algorithm.count_if": TargetFixture(
        prompts={
            "direct": "Điểm của lớp: 6, 8.5, 7, 9, 5.5, 8. Đếm số bạn đạt từ 8 trở lên.",
            "paraphrase": "Nhiệt độ tủ ghi 3, 6, 2, 8, 5, 7. Bao nhiêu lần tủ vượt 4 độ?",
            "changed_input": "Cho dãy 10, 3, 12, 7, 15, 2. Đếm các số nhỏ hơn 8.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Đếm số bạn đạt từ 8 trở lên"),
                [_classify("algorithm.count_if")],
                [_algo_cfg([6, 8.5, 7, 9, 5.5, 8], condition={"op": ">=", "value": 8}, summary="Đếm theo điều kiện")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Đếm số lần tủ quá ấm"),
                [_classify("algorithm.count_if")],
                [_algo_cfg([3, 6, 2, 8, 5, 7], condition={"op": ">", "value": 4}, summary="Đếm theo điều kiện")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Đếm các số nhỏ hơn 8"),
                [_classify("algorithm.count_if")],
                [_algo_cfg([10, 3, 12, 7, 15, 2], condition={"op": "<", "value": 8}, summary="Đếm theo điều kiện")],
            ),
        },
    ),
    "algorithm.linear_search": TargetFixture(
        prompts={
            "direct": "Cho danh sách 305, 118, 227, 194, 260. Tìm xem 194 có trong danh sách không.",
            "paraphrase": "Duyệt lần lượt các mã 71, 34, 90, 12, 58 để tìm mã 90.",
            "changed_input": "Tìm số 42 trong dãy 15, 42, 8, 23, 4 bằng cách xét từng phần tử.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm 194 trong danh sách"),
                [_classify("algorithm.linear_search")],
                [_algo_cfg([305, 118, 227, 194, 260], target=194, summary="Tìm kiếm tuần tự")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Tìm mã 90"),
                [_classify("algorithm.linear_search")],
                [_algo_cfg([71, 34, 90, 12, 58], target=90, summary="Tìm kiếm tuần tự")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm 42 bằng duyệt tuần tự"),
                [_classify("algorithm.linear_search")],
                [_algo_cfg([15, 42, 8, 23, 4], target=42, summary="Tìm kiếm tuần tự")],
            ),
        },
    ),
    "algorithm.binary_search": TargetFixture(
        prompts={
            "direct": "Dãy đã sắp 3, 8, 15, 22, 30, 41, 55. Tìm 30 bằng tìm kiếm nhị phân.",
            "paraphrase": "Tìm 203 trong dãy tăng dần 101, 145, 178, 203, 256 bằng cách xét phần tử giữa.",
            "changed_input": "Dãy 2, 5, 9, 14, 21, 30 đã sắp xếp. Dùng chia đôi để tìm 17.",
            "boundary": "Cho dãy CHƯA sắp 27, 4, 51, 13, 38, 9. Tìm 38 bằng tìm kiếm nhị phân.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm 30 bằng chia đôi"),
                [_classify("algorithm.binary_search")],
                [_algo_cfg([3, 8, 15, 22, 30, 41, 55], target=30, summary="Tìm kiếm nhị phân")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Tìm 203 bằng cách xét phần tử giữa"),
                [_classify("algorithm.binary_search")],
                [_algo_cfg([101, 145, 178, 203, 256], target=203, summary="Tìm kiếm nhị phân")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm 17 (vắng mặt) bằng chia đôi"),
                [_classify("algorithm.binary_search")],
                [_algo_cfg([2, 5, 9, 14, 21, 30], target=17, summary="Tìm kiếm nhị phân")],
            ),
            # M15 policy: input chưa sắp → normalize-not-refuse (validator tự sắp)
            "boundary": CaseScript(
                _analysis(goal="Tìm 38 bằng chia đôi trên dãy chưa sắp"),
                [_classify("algorithm.binary_search")],
                [_algo_cfg([27, 4, 51, 13, 38, 9], target=38, summary="Tìm kiếm nhị phân")],
            ),
        },
    ),
    "algorithm.bubble_sort": TargetFixture(
        prompts={
            "direct": "Sắp xếp dãy 9, 4, 7, 2, 6 tăng dần bằng thuật toán nổi bọt.",
            "paraphrase": "Sắp xếp 8, 3, 6, 1 bằng cách so sánh và đổi chỗ hai phần tử kề nhau.",
            "changed_input": "Dùng nổi bọt sắp xếp dãy 5, 1, 4, 2, 8 theo thứ tự tăng.",
            "boundary": "Sắp xếp dãy có phần tử trùng 5, 3, 5, 2, 3 bằng nổi bọt.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Sắp xếp tăng dần bằng nổi bọt", prescribed=_P_ADJ),
                [_classify(_TOKEN)],
                [_sort_spec("bubble", [9, 4, 7, 2, 6])],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Sắp xếp bằng đổi chỗ cặp kề", prescribed=_P_ADJ),
                [_classify(_TOKEN)],
                [_sort_spec("bubble", [8, 3, 6, 1])],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Sắp xếp dãy khác bằng nổi bọt", prescribed=_P_ADJ),
                [_classify(_TOKEN)],
                [_sort_spec("bubble", [5, 1, 4, 2, 8])],
            ),
            "boundary": CaseScript(
                _analysis(goal="Sắp xếp dãy có phần tử trùng", prescribed=_P_ADJ),
                [_classify(_TOKEN)],
                [_sort_spec("bubble", [5, 3, 5, 2, 3])],
            ),
        },
    ),
    "algorithm.insertion_sort": TargetFixture(
        prompts={
            "direct": "Sắp xếp dãy 7, 2, 9, 4, 5 bằng thuật toán sắp xếp chèn.",
            "paraphrase": "Chèn từng lá bài 6, 2, 8, 3, 5 vào phần đã sắp xếp bên trái.",
            "changed_input": "Dùng sắp xếp chèn cho dãy 10, 6, 3, 8, 1.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Sắp xếp tăng dần bằng chèn", prescribed=_P_SHIFT),
                [_classify(_TOKEN)],
                [_sort_spec("insertion", [7, 2, 9, 4, 5])],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Chèn từng lá bài vào phần đã sắp", prescribed=_P_SHIFT),
                [_classify(_TOKEN)],
                [_sort_spec("insertion", [6, 2, 8, 3, 5])],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Sắp xếp chèn dãy khác", prescribed=_P_SHIFT),
                [_classify(_TOKEN)],
                [_sort_spec("insertion", [10, 6, 3, 8, 1])],
            ),
        },
    ),
    # M17 W1 — Selection Sort (route qua token comparison_sort, variant "selection")
    "algorithm.selection_sort": TargetFixture(
        prompts={
            "direct": "Sắp xếp dãy 9, 2, 7, 4 bằng thuật toán sắp xếp chọn (selection sort).",
            "paraphrase": "Sắp xếp 6, 1, 8, 3, 5 bằng cách mỗi lượt tìm phần tử nhỏ nhất còn lại rồi đưa lên đầu.",
            "changed_input": "Dùng sắp xếp chọn cho dãy 12, 5, 9, 3 theo thứ tự giảm dần.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Sắp xếp bằng chọn cực trị lặp", prescribed=_P_SELECT),
                [_classify(_TOKEN)],
                [_sort_spec("selection", [9, 2, 7, 4])],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Mỗi lượt tìm phần tử nhỏ nhất đưa lên đầu", prescribed=_P_SELECT),
                [_classify(_TOKEN)],
                [_sort_spec("selection", [6, 1, 8, 3, 5])],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Sắp xếp chọn giảm dần", prescribed=_P_SELECT),
                [_classify(_TOKEN)],
                [_sort_spec("selection", [12, 5, 9, 3], order="desc")],
            ),
        },
    ),
    "algorithm.scan": TargetFixture(
        prompts={
            "direct": "Nhiệt độ 7 ngày: 31, 33, 30, 36, 32, 38, 29. Tìm ngày ĐẦU TIÊN vượt 35 độ.",
            "paraphrase": "Áp suất các bình: 12, 15, 11, 18, 14, 20. Dừng ở bình đầu tiên đạt từ 18 bar.",
            "changed_input": "Cho dãy 5, 9, 4, 12, 7. Tìm phần tử đầu tiên lớn hơn 10.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Tìm ngày đầu tiên vượt 35 độ"),
                [_classify("algorithm.scan")],
                [_scan_cfg([31, 33, 30, 36, 32, 38, 29], 35, op=">")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Dừng ở bình đầu tiên ≥ 18 bar"),
                [_classify("algorithm.scan")],
                [_scan_cfg([12, 15, 11, 18, 14, 20], 18, op=">=")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm phần tử đầu tiên lớn hơn 10"),
                [_classify("algorithm.scan")],
                [_scan_cfg([5, 9, 4, 12, 7], 10, op=">")],
            ),
        },
    ),
    "logic.and_gate": TargetFixture(
        prompts={
            "direct": "Mô phỏng cổng AND hai đầu vào, cả hai đang bật.",
            "paraphrase": "Đèn chỉ sáng khi cả hai công tắc cùng đóng — hiện tại một công tắc mở.",
            "changed_input": "Cổng AND với đầu vào A tắt, B bật. Đầu ra là gì?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Cổng AND hai đầu vào"),
                [_classify("logic.and_gate")],
                [_logic_cfg(1, 1)],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Đầu ra 1 chỉ khi cả hai vào 1"),
                [_classify("logic.and_gate")],
                [_logic_cfg(1, 0)],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Cổng AND với A=0, B=1"),
                [_classify("logic.and_gate")],
                [_logic_cfg(0, 1)],
            ),
        },
    ),
    # M17 W1 — mạch logic nhiều cổng (boolean DAG + truth table)
    "logic.boolean_dag": TargetFixture(
        prompts={
            "direct": "Mạch logic: đèn sáng khi (A VÀ B) HOẶC (KHÔNG C). Mô phỏng mạch và bảng chân trị.",
            "paraphrase": "Chuông reo khi đúng MỘT trong hai công tắc bật (XOR). Dựng mạch logic.",
            "changed_input": "Cho biểu thức logic A ∧ ¬B. Lập bảng chân trị bằng mạch cổng.",
            "boundary": "Mạch 4 đầu vào: (A VÀ B) HOẶC (C VÀ D) — bảng chân trị đủ 16 hàng.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Mạch (A AND B) OR (NOT C)", ownership="rule_derivable",
                          entity_roles=["logical"]),
                [_classify("logic.boolean_dag")],
                [_booldag_cfg(
                    [{"id": "A", "value": 1}, {"id": "B", "value": 0}, {"id": "C", "value": 1}],
                    [{"id": "g1", "op": "AND", "inputs": ["A", "B"]},
                     {"id": "g2", "op": "NOT", "inputs": ["C"]},
                     {"id": "g3", "op": "OR", "inputs": ["g1", "g2"]}],
                    "g3",
                )],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Chuông reo khi đúng một công tắc bật (XOR)", ownership="rule_derivable",
                          entity_roles=["logical"]),
                [_classify("logic.boolean_dag")],
                [_booldag_cfg(
                    [{"id": "x", "value": 0}, {"id": "y", "value": 0}],
                    [{"id": "g", "op": "XOR", "inputs": ["x", "y"]}],
                    "g",
                )],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Bảng chân trị của A ∧ ¬B", ownership="rule_derivable",
                          entity_roles=["logical"]),
                [_classify("logic.boolean_dag")],
                [_booldag_cfg(
                    [{"id": "A", "value": 0}, {"id": "B", "value": 0}],
                    [{"id": "n", "op": "NOT", "inputs": ["B"]},
                     {"id": "g", "op": "AND", "inputs": ["A", "n"]}],
                    "g",
                )],
            ),
            "boundary": CaseScript(
                _analysis(goal="Mạch 4 đầu vào — bảng chân trị 16 hàng", ownership="rule_derivable",
                          entity_roles=["logical"]),
                [_classify("logic.boolean_dag")],
                [_booldag_cfg(
                    [{"id": "A", "value": 0}, {"id": "B", "value": 0},
                     {"id": "C", "value": 0}, {"id": "D", "value": 0}],
                    [{"id": "g1", "op": "AND", "inputs": ["A", "B"]},
                     {"id": "g2", "op": "AND", "inputs": ["C", "D"]},
                     {"id": "g3", "op": "OR", "inputs": ["g1", "g2"]}],
                    "g3",
                )],
            ),
        },
    ),
    "binary.decimal_to_binary": TargetFixture(
        prompts={
            "direct": "Biểu diễn số 156 trong hệ nhị phân 8 bit.",
            "paraphrase": "Bật các công tắc trọng số 128..1 để tổng bằng 89.",
            "changed_input": "Đổi số 37 sang nhị phân 8 bit.",
            "boundary": "Biểu diễn 300 trong 8 bit nhị phân (vượt phạm vi biểu diễn).",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Biểu diễn 156 nhị phân", prescribed=_P_BINW),
                [_classify(_BINARY)],
                [_binary_cfg(156, 8)],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Bật trọng số 128..1 cho tổng 89", prescribed=_P_BINW),
                [_classify(_BINARY)],
                [_binary_cfg(89, 8)],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Đổi 37 sang nhị phân", prescribed=_P_BINW),
                [_classify(_BINARY)],
                [_binary_cfg(37, 8)],
            ),
            # contract-error retry: attempt1 giữ 300 (validator từ chối) → attempt2 hợp lệ
            "boundary": CaseScript(
                _analysis(goal="Biểu diễn 300 nhị phân (vượt phạm vi)", prescribed=_P_BINW),
                [_classify(_BINARY)],
                [_binary_cfg(300, 8), _binary_cfg(255, 8)],
            ),
        },
    ),
    # M17 W1 — base conversion tổng quát (gap hex/octal flip → owned)
    "binary.base_conversion": TargetFixture(
        prompts={
            "direct": "Đổi số 2026 sang hệ thập lục phân.",
            "paraphrase": "Số bát phân 755 bằng bao nhiêu trong hệ thập phân?",
            "changed_input": "Đổi số thập lục phân 9C sang hệ nhị phân.",
            "boundary": "Đổi 45 sang nhị phân (LLM khai nhầm cùng cơ số ở lượt đầu — validator từ chối, retry).",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Đổi 2026 sang thập lục phân", ownership="rule_derivable", prescribed=_P_NONBIN),
                [_classify("binary.base_conversion")],
                [_baseconv_cfg(10, 16, "2026")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Giá trị thập phân của số bát phân 755", ownership="rule_derivable", prescribed=_P_NONBIN),
                [_classify("binary.base_conversion")],
                [_baseconv_cfg(8, 10, "755")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Đổi 9C (hex) sang nhị phân", ownership="rule_derivable", prescribed=_P_NONBIN),
                [_classify("binary.base_conversion")],
                [_baseconv_cfg(16, 2, "9C")],
            ),
            # contract-retry: attempt1 cùng cơ số (validator từ chối) → attempt2 hợp lệ
            "boundary": CaseScript(
                _analysis(goal="Đổi 45 sang nhị phân", ownership="rule_derivable", prescribed=_P_NONBIN),
                [_classify("binary.base_conversion")],
                [_baseconv_cfg(10, 10, "45"), _baseconv_cfg(10, 2, "45")],
            ),
        },
    ),
    "network.packet_routing": TargetFixture(
        prompts={
            "direct": "Gói tin đi từ máy tính qua switch, router, ISP tới máy chủ. Mô phỏng đường đi.",
            "paraphrase": "Dữ liệu truyền lần lượt qua từng thiết bị mạng từ máy khách tới máy chủ.",
            "changed_input": "Mạng có hai router song song giữa máy khách và máy chủ. Gói tin chọn đường nào?",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Đường đi gói tin qua các chặng"),
                [_classify("network.packet_routing")],
                [_net_cfg(
                    [{"id": "pc", "type": "client"}, {"id": "sw", "type": "switch"},
                     {"id": "r1", "type": "router"}, {"id": "isp", "type": "isp"},
                     {"id": "srv", "type": "server"}],
                    [["pc", "sw"], ["sw", "r1"], ["r1", "isp"], ["isp", "srv"]], "pc", "srv",
                )],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Dữ liệu đi qua từng thiết bị"),
                [_classify("network.packet_routing")],
                [_net_cfg(
                    [{"id": "cl", "type": "client"}, {"id": "r1", "type": "router"},
                     {"id": "r2", "type": "router"}, {"id": "srv", "type": "server"}],
                    [["cl", "r1"], ["r1", "r2"], ["r2", "srv"]], "cl", "srv",
                )],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Chọn đường khi có hai router song song"),
                [_classify("network.packet_routing")],
                [_net_cfg(
                    [{"id": "cl", "type": "client"}, {"id": "r1", "type": "router"},
                     {"id": "r2", "type": "router"}, {"id": "srv", "type": "server"}],
                    [["cl", "r1"], ["cl", "r2"], ["r1", "srv"], ["r2", "srv"]], "cl", "srv",
                )],
            ),
        },
    ),
    # M17 W1 — duyệt đồ thị BFS/DFS (packet_routing giữ là application variant)
    "network.graph_traversal": TargetFixture(
        prompts={
            "direct": "Duyệt đồ thị 5 đỉnh A,B,C,D,E (A-B, A-C, B-D, C-D, D-E) theo chiều rộng (BFS) từ A.",
            "paraphrase": "Đi thăm các đỉnh của đồ thị bắt đầu từ A, ưu tiên đi SÂU hết một nhánh rồi mới quay lại (DFS).",
            "changed_input": "Tìm đường từ A đến E trong đồ thị (A-B, B-C, C-E, A-D) bằng BFS.",
            "boundary": "Đồ thị hai phần rời: (A-B) và (X-Y). Duyệt BFS từ A tìm Y.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Duyệt đồ thị theo BFS từ A", process_roles=["temporal"]),
                [_classify("network.graph_traversal")],
                [_traverse_cfg(
                    ["A", "B", "C", "D", "E"],
                    [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"], ["D", "E"]],
                    "A", "bfs",
                )],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Duyệt đồ thị theo chiều sâu từ A", process_roles=["temporal"]),
                [_classify("network.graph_traversal")],
                [_traverse_cfg(
                    ["A", "B", "C", "D", "E"],
                    [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"], ["D", "E"]],
                    "A", "dfs",
                )],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tìm đường A→E bằng BFS", process_roles=["temporal"]),
                [_classify("network.graph_traversal")],
                [_traverse_cfg(
                    ["A", "B", "C", "D", "E"],
                    [["A", "B"], ["B", "C"], ["C", "E"], ["A", "D"]],
                    "A", "bfs", goal="E",
                )],
            ),
            # unreachable = kết quả hợp lệ (không phải lỗi)
            "boundary": CaseScript(
                _analysis(goal="Tìm Y từ A trong đồ thị rời", process_roles=["temporal"]),
                [_classify("network.graph_traversal")],
                [_traverse_cfg(
                    ["A", "B", "X", "Y"],
                    [["A", "B"], ["X", "Y"]],
                    "A", "bfs", goal="Y",
                )],
            ),
        },
    ),
    "network.protocol_encapsulation": TargetFixture(
        prompts={
            "direct": "Mô phỏng quá trình đóng gói dữ liệu qua các tầng TCP/IP khi gửi một trang web.",
            "paraphrase": "Mỗi tầng mạng bọc thêm phần đầu vào tin nhắn trước khi truyền đi.",
            "changed_input": "Máy nhận tháo từng lớp gói tin như thế nào? Mô phỏng quá trình mở gói.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(goal="Đóng gói qua các tầng TCP/IP"),
                [_classify("network.protocol_encapsulation")],
                [_encap_cfg("Dữ liệu ứng dụng")],
            ),
            "paraphrase": CaseScript(
                _analysis(goal="Mỗi tầng bọc thêm thông tin"),
                [_classify("network.protocol_encapsulation")],
                [_encap_cfg("Tin nhắn")],
            ),
            "changed_input": CaseScript(
                _analysis(goal="Tháo gói ở máy nhận"),
                [_classify("network.protocol_encapsulation")],
                [_encap_cfg("Gói tin nhận")],
            ),
        },
    ),
    "generic.rule_scene": TargetFixture(
        prompts={
            "direct": "Dựng tam giác ABC từng bước: vẽ AB, thêm C, nối AC và BC.",
            "paraphrase": "Vẽ sơ đồ ba trạm theo mô tả, hiện dần từng trạm một.",
            "changed_input": "Robot đi qua các trạm A→B→C→D→E, mỗi bước một trạm.",
            "boundary": "Đèn chỉ sáng khi CẢ BA công tắc cùng bật. Mô phỏng mạch.",
        },
        scripts={
            "direct": CaseScript(
                _analysis(
                    goal="Dựng tam giác ABC từng bước", ownership="provided",
                    scene_construction="step_by_step", relation_roles=["relational"],
                    process_roles=["temporal"],
                ),
                [_classify(_GENERIC)],
                [_TRIANGLE_REVEAL],
            ),
            "paraphrase": CaseScript(
                _analysis(
                    goal="Vẽ sơ đồ các trạm, hiện dần từng trạm", ownership="provided",
                    scene_construction="step_by_step", relation_roles=["relational"],
                    process_roles=["temporal"],
                ),
                [_classify(_GENERIC)],
                [_STATION_REVEAL],
            ),
            "changed_input": CaseScript(
                _analysis(
                    goal="Robot đi qua các trạm", ownership="provided",
                    scene_construction="step_by_step", process_roles=["movement", "temporal"],
                ),
                [_classify(_GENERIC)],
                [_MOVING_PATH],
            ),
            # computation membership (boolean composed_rule_dag) — AND 3 đầu vào
            "boundary": CaseScript(
                _analysis(
                    goal="Đèn sáng khi cả BA công tắc bật", ownership="rule_derivable",
                    entity_roles=["logical"], interaction_needs=["interactive"],
                ),
                [_classify(_GENERIC)],
                [_AND3_GATE],
            ),
        },
    ),
}


# ══════════════ near-miss per cơ chế INTENTIONAL_GAP (dedupe theo mechanism) ══
# M17 W1: near-miss select_extreme_repeated ĐÃ flip thành ok-case của target
# algorithm.selection_sort (xem TARGET_FIXTURES) — không còn ở đây.
NEAR_MISS_FIXTURES: dict[str, ControlFixture] = {
    "comparison_sort.partition_recursive": ControlFixture(
        case_id="aud-nm-quick-sort",
        kind="near_miss",
        prompt="Sắp xếp dãy 8, 3, 6, 1, 9 bằng cách chọn mốc rồi CHIA dãy quanh mốc và đệ quy (quick sort).",
        script=CaseScript(
            _analysis(goal="Sắp xếp bằng chia quanh mốc + đệ quy", ownership="algorithmic", prescribed=_P_PARTITION),
            [_classify(_TOKEN)],
        ),
        mechanism="comparison_sort.partition_recursive",
        note="Quick sort giữ gap (contract không biểu diễn partition) — không ép.",
    ),
    "comparison_sort.other_unspecified": ControlFixture(
        case_id="aud-nm-sort-unspecified",
        kind="near_miss",
        prompt="Sắp xếp dãy 5, 8, 1 bằng một thuật toán tự chọn hiệu quả nhất.",
        script=CaseScript(
            _analysis(goal="Sắp xếp bằng thuật toán không nêu cơ chế", ownership="algorithmic", prescribed=_P_OTHER),
            [_classify(_TOKEN)],
        ),
        mechanism="comparison_sort.other_unspecified",
        note="Cơ chế không xác định — từ chối trung thực thay vì đoán biến thể.",
    ),
    # M17 W1: near-miss non_binary_base ĐÃ flip thành ok-case của target
    # binary.base_conversion (xem TARGET_FIXTURES) — không còn ở đây.
}


# ══════════════ leak / refusal control + regression duyệt cây ══════════════
# Config adversarial: cây nhị phân bị "ép phẳng" thành điểm + đoạn nối + vật
# di chuyển — ĐÚNG kiểu leak mà M17 mô tả (Điểm 1/Điểm 2/Đoạn nối/Vật di chuyển).
_TREE_AS_POINTS = _j(
    {
        "dsl_version": "1.0",
        "title": "Duyệt các điểm theo thứ tự",
        "objects": [
            {"id": "p1", "type": "node", "label": "Điểm 1"},
            {"id": "p2", "type": "node", "label": "Điểm 2"},
            {"id": "p3", "type": "node", "label": "Điểm 3"},
            {"id": "p4", "type": "node", "label": "Điểm 4"},
            {"id": "e12", "type": "edge", "from": "p1", "to": "p2"},
            {"id": "e13", "type": "edge", "from": "p1", "to": "p3"},
            {"id": "e24", "type": "edge", "from": "p2", "to": "p4"},
            {"id": "vat", "type": "moving_entity", "label": "Vật di chuyển"},
        ],
        "rules": [],
        "interactions": [],
        "processes": [
            {"type": "move_along_path", "entity": "vat", "path": ["p1", "p2", "p4", "p3"]}
        ],
    }
)

CONTROL_FIXTURES: tuple[ControlFixture, ...] = (
    ControlFixture(
        case_id="aud-leak-dijkstra",
        kind="leak_control",
        prompt="Vẽ sơ đồ các trạm rồi TÍNH đường đi ngắn nhất theo tổng độ dài các cạnh.",
        script=CaseScript(
            _analysis(goal="Vẽ sơ đồ trạm rồi TÍNH đường ngắn nhất có trọng số", ownership="algorithmic"),
            [_classify(_GENERIC)],
        ),
        note="Kết quả thuật toán không engine nào sở hữu → computation gate (bất biến #21).",
    ),
    ControlFixture(
        case_id="aud-regression-tree-honest",
        kind="leak_control",
        prompt="Mô phỏng thuật toán duyệt cây nhị phân theo thứ tự trước (preorder) trên cây gốc A.",
        script=CaseScript(
            _analysis(goal="Duyệt cây nhị phân theo thứ tự trước", ownership="algorithmic"),
            [_classify(_GENERIC)],
        ),
        note="REGRESSION M17: tree_traversal chưa có → phải capability_gap, không dựng điểm/đoạn nối.",
    ),
    ControlFixture(
        case_id="aud-regression-tree-adversarial",
        kind="leak_probe",
        prompt="Cho cây nhị phân gốc 1, con trái 2, con phải 3, nút 2 có con trái 4. Mô phỏng duyệt cây theo thứ tự trước.",
        script=CaseScript(
            _analysis(
                goal="Vật di chuyển qua các điểm của cây theo thứ tự duyệt",
                ownership="provided", scene_construction="step_by_step",
                relation_roles=["relational"], process_roles=["movement", "temporal"],
            ),
            [_classify(_GENERIC)],
            [_TREE_AS_POINTS],
        ),
        expected_status="probe",  # PROBE: ghi nhận hành vi thật, ledger phân loại
        note=(
            "ADVERSARIAL PROBE: analyze khai man ownership=provided (thứ tự duyệt "
            "THẬT RA là kết quả thuật toán). Đo xem gate hiện tại có chặn được khi "
            "tín hiệu cấu trúc bị khai sai — kết quả vào generic_leak_ledger."
        ),
    ),
    ControlFixture(
        case_id="aud-refusal-tcp-handshake",
        kind="refusal_control",
        prompt="Mô phỏng bắt tay ba bước TCP giữa máy khách và máy chủ.",
        script=CaseScript(
            _analysis(goal="Bắt tay ba bước TCP", ownership="rule_derivable"),
            [_classify(None, status="unsupported",
                       reason="Bắt tay ba bước / máy trạng thái giao thức vượt năng lực v1 — trả unsupported trung thực.")],
        ),
        note="Advanced-TCP từ chối trung thực ở classify (khoá cur-t12-tcp-advanced).",
    ),
    ControlFixture(
        case_id="aud-control-representation-ok",
        kind="refusal_control",
        prompt="Vẽ sơ đồ ba trạm nối tiếp nhau, hiện dần từng trạm theo mô tả cho sẵn.",
        script=CaseScript(
            _analysis(
                goal="Vẽ sơ đồ các trạm, hiện dần từng trạm", ownership="provided",
                scene_construction="step_by_step", relation_roles=["relational"],
                process_roles=["temporal"],
            ),
            [_classify(_GENERIC)],
            [_STATION_REVEAL],
        ),
        expected_status="ok",
        note="ĐỐI CHỨNG chống chặn oan: biểu diễn khai báo thuần túy PHẢI được generic nhận.",
    ),
)
