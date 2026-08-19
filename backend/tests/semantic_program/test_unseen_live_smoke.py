# -*- coding: utf-8 -*-
"""UNSEEN_LIVE_SMOKE: Kiểm định khả năng tổng quát hóa với 5 bài toán hoàn toàn mới."""
import pytest
from app.simulation.semantic_program.validator import validate_semantic_program
from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
from app.simulation.semantic_program.pipeline_adapter import compile_semantic_program_to_envelope
from .unseen_smoke_fixtures import (
    ALL_5_UNSEEN_FIXTURES,
    UNSEEN_01_VOWEL_COUNT,
    UNSEEN_02_SECOND_LARGEST,
    UNSEEN_03_DECIMAL_TO_HEX,
    UNSEEN_04_REMOVE_DUPLICATES,
    UNSEEN_05_HOT_POTATO,
)


def test_all_5_unseen_problems_validate_cleanly():
    """Tất cả 5 bài toán mới ngoài tập mẫu đều phải vượt qua static validator."""
    assert len(ALL_5_UNSEEN_FIXTURES) == 5
    for spec in ALL_5_UNSEEN_FIXTURES:
        val = validate_semantic_program(spec)
        assert val.ok is True, f"Bài '{spec.title}' bị lỗi validator: {val.error}"


def test_unseen_01_vowel_count_execution():
    """Đếm nguyên âm trong 'helloworld' -> 3 (e, o, o)."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(UNSEEN_01_VOWEL_COUNT)

    assert res.final_memory["vowel_count"] == 3


def test_unseen_02_second_largest_execution():
    """Tìm số lớn thứ nhì trong [10, 40, 20, 50, 30] -> max1=50, max2=40."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(UNSEEN_02_SECOND_LARGEST)

    assert res.final_memory["first_max"] == 50
    assert res.final_memory["second_max"] == 40


def test_unseen_03_decimal_to_hex_execution():
    """Đổi 43 sang Hexadecimal -> ['2', 'B']."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(UNSEEN_03_DECIMAL_TO_HEX)

    assert res.final_memory["hex_digits"] == ["2", "B"]


def test_unseen_04_remove_duplicates_execution():
    """Xóa trùng lặp [1, 1, 2, 2, 3, 4, 4] -> 4 phần tử duy nhất [1, 2, 3, 4]."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(UNSEEN_04_REMOVE_DUPLICATES)

    assert res.final_memory["unique_count"] == 4
    assert res.final_memory["arr"][:4] == [1, 2, 3, 4]


def test_unseen_05_hot_potato_queue_execution():
    """Trò chơi truyền bóng Hot Potato 5 người (An, Bình, Cường, Dũng, Em), k=2."""
    interpreter = SemanticProgramInterpreter()
    res = interpreter.execute(UNSEEN_05_HOT_POTATO)

    assert res.status == "completed"
    assert res.final_memory["winner"] in ["An", "Bình", "Cường", "Dũng", "Em"]
    assert len(res.final_memory["q"]) == 0


def test_all_5_unseen_compile_to_production_envelopes():
    """Tất cả 5 bài toán mới biên dịch thành SimulationEnvelope chuẩn hợp lệ."""
    for spec in ALL_5_UNSEEN_FIXTURES:
        envelope = compile_semantic_program_to_envelope(spec)
        assert envelope["status"] == "ok"
        assert envelope["domain"] == "generic"
        assert len(envelope["config"]["objects"]) > 0
        assert len(envelope["config"]["processes"][0]["steps"]) > 0
