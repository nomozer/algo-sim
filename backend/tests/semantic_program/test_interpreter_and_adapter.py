# -*- coding: utf-8 -*-
"""Test suite kiểm thử thực thi tất định (Interpreter) và Bộ tiếp hợp trực quan (VisualTraceAdapter)."""
import pytest
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter
from .fixtures_coverage_18 import (
    ALL_18_COVERAGE_FIXTURES,
    P01_STACK_BRACKET,
    P02_FIND_MAX,
    P03_BINARY_SEARCH,
    P04_BUBBLE_SORT,
    P05_SELECTION_SORT,
    P06_INSERTION_SORT,
    P07_TWO_SUM_SORTED,
    P08_PALINDROME,
    P09_GRAPH_BFS,
    P10_REVERSE_STRING_STACK,
    P13_DECIMAL_TO_BINARY,
)


def test_interpreter_executes_all_18_fixtures_successfully():
    """Tất cả 18 bài toán đại diện phải thực thi thành công (completed/returned) và không bị crash."""
    interpreter = SemanticProgramInterpreter(max_steps=300)

    for idx, spec in enumerate(ALL_18_COVERAGE_FIXTURES, 1):
        res = interpreter.execute(spec)
        assert res.status in ("completed", "returned"), f"Bài #{idx:02d} '{spec.title}' bị lỗi thực thi: status={res.status}"
        assert res.total_steps > 1, f"Bài #{idx:02d} không sinh đủ bước thực thi."
        assert len(res.trace) == res.total_steps


def test_p01_stack_bracket_valid_execution():
    """Kiểm tra thực thi thuật toán chuỗi ngoặc {[()]} -> HỢP LỆ."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P01_STACK_BRACKET)

    assert res.final_memory["result"] == "HỢP LỆ"
    assert len(res.final_memory["stack"]) == 0

    # Chuyển qua VisualTraceAdapter
    adapter = VisualTraceAdapter(P01_STACK_BRACKET)
    frames = adapter.adapt(res)
    assert len(frames) == res.total_steps
    assert frames[0].tier2_intent is not None
    # Kiểm tra không có dummy 0 trong các frame
    for f in frames:
        for obj in f.objects:
            if obj["type"] == "array_strip":
                assert obj["items"] == ["{", "[", "(", ")", "]", "}"]


def test_p02_find_max_execution():
    """Kiểm tra tìm phần tử lớn nhất trong [12, 45, 67, 23, 89, 34] -> max=89, idx=4."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P02_FIND_MAX)

    assert res.final_memory["max_val"] == 89
    assert res.final_memory["max_idx"] == 4


def test_p03_binary_search_execution():
    """Kiểm tra tìm kiếm nhị phân phần tử 23 trong mảng đã sắp -> found_idx=5."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P03_BINARY_SEARCH)

    assert res.final_memory["found_idx"] == 5


def test_p04_bubble_sort_execution():
    """Kiểm tra sắp xếp nổi bọt [5, 1, 4, 2, 8] -> [1, 2, 4, 5, 8]."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P04_BUBBLE_SORT)

    assert res.final_memory["arr"] == [1, 2, 4, 5, 8]


def test_p05_selection_sort_execution():
    """Kiểm tra sắp xếp chọn [64, 25, 12, 22, 11] -> [11, 12, 22, 25, 64]."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P05_SELECTION_SORT)

    assert res.final_memory["arr"] == [11, 12, 22, 25, 64]


def test_p06_insertion_sort_execution():
    """Kiểm tra sắp xếp chèn [12, 11, 13, 5, 6] -> [5, 6, 11, 12, 13]."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P06_INSERTION_SORT)

    assert res.final_memory["arr"] == [5, 6, 11, 12, 13]


def test_p07_two_sum_sorted_execution():
    """Kiểm tra Two Sum tìm tổng 10 trong [1, 2, 3, 4, 6, 8, 11] (2 + 8 = 10)."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P07_TWO_SUM_SORTED)

    assert res.final_memory["found"] is True
    assert res.final_memory["curr_sum"] == 10


def test_p08_palindrome_execution():
    """Kiểm tra chuỗi đối xứng 'radar' -> is_pal=True."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P08_PALINDROME)

    assert res.final_memory["is_pal"] is True


def test_p09_graph_bfs_execution():
    """Kiểm tra duyệt đồ thị BFS từ đỉnh 1 -> thứ tự duyệt đủ 5 đỉnh."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P09_GRAPH_BFS)

    order = res.final_memory["order"]
    assert len(order) == 5
    assert order[0] == "1"
    assert set(order) == {"1", "2", "3", "4", "5"}


def test_p10_reverse_string_stack_execution():
    """Kiểm tra đảo ngược chuỗi HELLO -> OLLEH."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P10_REVERSE_STRING_STACK)

    assert res.final_memory["output_chars"] == ["O", "L", "L", "E", "H"]


def test_p13_decimal_to_binary_execution():
    """Kiểm tra đổi 13 sang nhị phân -> 1101 (danh sách bit [1, 1, 0, 1])."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P13_DECIMAL_TO_BINARY)

    assert res.final_memory["binary_digits"] == [1, 1, 0, 1]


def test_visual_adapter_pointers_and_bindings():
    """VisualTraceAdapter phản ánh đúng con trỏ và cập nhật hộp giá trị."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P02_FIND_MAX)

    adapter = VisualTraceAdapter(P02_FIND_MAX)
    frames = adapter.adapt(res)

    # Cuối cùng ptr_max phải trỏ vào target_index 4
    last_frame = frames[-1]
    ptr_max = next(obj for obj in last_frame.objects if obj.get("id") == "ptr_max")
    assert ptr_max["target_index"] == 4

    max_box = next(obj for obj in last_frame.objects if obj.get("id") == "max_box")
    assert max_box["value"] == 89
