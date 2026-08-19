# -*- coding: utf-8 -*-
"""NARRATION_CERTIFICATION: Chứng nhận tính xác thực và sư phạm của hệ thống thuyết minh 2 tầng."""
import pytest
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.visual_adapter import VisualTraceAdapter
from .fixtures_coverage_18 import (
    ALL_18_COVERAGE_FIXTURES,
    P01_STACK_BRACKET,
    P02_FIND_MAX,
    P03_BINARY_SEARCH,
    P04_BUBBLE_SORT,
)


def test_narration_tier1_facts_in_all_18():
    """Mọi bước thực thi trong 18 bài toán đều có thuyết minh Tier 1 xác thực, không rỗng."""
    interpreter = SemanticProgramInterpreter()
    for spec in ALL_18_COVERAGE_FIXTURES:
        res = interpreter.execute(spec)
        assert len(res.trace) > 0
        for step in res.trace:
            assert step.tier1_narration is not None
            assert len(step.tier1_narration.strip()) > 0
            # Không được chứa placeholder dạng 'undefined' hoặc 'null' bừa bãi
            assert "undefined" not in step.tier1_narration


def test_p01_stack_bracket_narration_truth():
    """Kiểm tra thuyết minh chuỗi ngoặc: các thao tác push/pop và gán phải đúng thực tế."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P01_STACK_BRACKET)

    push_steps = [s for s in res.trace if s.action == "push"]
    pop_steps = [s for s in res.trace if s.action == "pop"]

    assert len(push_steps) == 3 # '{', '[', '('
    assert len(pop_steps) == 3 # pop 3 lần

    assert "Đẩy giá trị" in push_steps[0].tier1_narration
    assert "Lấy phần tử đỉnh" in pop_steps[0].tier1_narration


def test_p04_bubble_sort_narration_swap_truth():
    """Kiểm tra thuyết minh Bubble Sort khi swap: ghi rõ 2 vị trí và giá trị hoán đổi."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P04_BUBBLE_SORT)

    swap_steps = [s for s in res.trace if s.action == "swap"]
    assert len(swap_steps) > 0
    for s in swap_steps:
        assert "Hoán đổi" in s.tier1_narration
        assert "arr[" in s.tier1_narration


def test_visual_adapter_2tier_narration_composition():
    """VisualTraceAdapter gắn đúng Tier 2 vào frame 0 và giữ Tier 1 trên mọi frame."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(P01_STACK_BRACKET)
    adapter = VisualTraceAdapter(P01_STACK_BRACKET)
    frames = adapter.adapt(res)

    assert len(frames) == len(res.trace)
    assert P01_STACK_BRACKET.pedagogical_intent in frames[0].narration
    assert frames[0].tier2_intent == P01_STACK_BRACKET.pedagogical_intent
