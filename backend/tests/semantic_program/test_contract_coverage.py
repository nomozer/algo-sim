# -*- coding: utf-8 -*-
"""Test suite kiểm thử tính đầy đủ (Coverage Review) và kiểm tra bất biến kiểu của SemanticProgram."""
import pytest
from app.simulation.semantic_program.validator import validate_semantic_program
from app.simulation.semantic_program.contract import (
    SemanticProgramSpec,
    MemoryDeclaration,
    AssignStmt,
    PushStmt,
    PopStmt,
    EnqueueStmt,
    WriteIndexStmt,
    BreakStmt,
    LiteralExpr,
    VarRefExpr,
    IndexRefExpr,
    BinaryArithExpr,
    CompareCond,
)
from .fixtures_coverage_18 import ALL_18_COVERAGE_FIXTURES

def test_all_18_problems_validate_cleanly():
    """Tất cả 18 bài toán đại diện trong chương trình Tin học THPT phải qua validator 100%."""
    assert len(ALL_18_COVERAGE_FIXTURES) == 18

    for idx, spec in enumerate(ALL_18_COVERAGE_FIXTURES, 1):
        res = validate_semantic_program(spec)
        assert res.ok is True, f"Bài #{idx:02d} '{spec.title}' thất bại khi validate: {res.error}"
        assert res.spec is not None
        assert len(res.spec.memory_declarations) > 0
        assert len(res.spec.statements) > 0


def test_zero_target_specific_operators_in_all_18():
    """Xác nhận không có bất kỳ toán tử đặc thù hay opcode tuỳ tiện nào trong 18 bài."""
    allowed_statement_kinds = {
        "assign", "write_index", "map_set", "swap", "push", "pop",
        "enqueue", "dequeue", "set_insert", "set_remove",
        "if", "while", "for_range", "for_each", "break", "return"
    }

    for spec in ALL_18_COVERAGE_FIXTURES:
        for stmt in spec.statements:
            kind = getattr(stmt, "kind", None)
            assert kind in allowed_statement_kinds, f"Phát hiện toán tử ngoài tập đóng: {kind}"


def test_validator_rejects_undeclared_variable():
    """Validator bắt đúng lỗi biến chưa khai báo/chưa gán."""
    bad_spec = SemanticProgramSpec(
        title="Lỗi biến mồ côi",
        memory_declarations=[
            MemoryDeclaration(name="arr", type="array", initial_value=[1, 2, 3]),
        ],
        statements=[
            AssignStmt(target_var="y", expr=VarRefExpr(name="ghost_var")),
        ],
    )
    res = validate_semantic_program(bad_spec)
    assert res.ok is False
    assert "chưa được khai báo" in res.error


def test_validator_rejects_push_to_non_stack():
    """Validator bắt đúng lỗi thao tác sai kiểu (push vào queue hoặc number)."""
    bad_spec = SemanticProgramSpec(
        title="Lỗi push vào queue",
        memory_declarations=[
            MemoryDeclaration(name="q", type="queue", initial_value=[]),
        ],
        statements=[
            PushStmt(container="q", val=LiteralExpr(value=10)),
        ],
    )
    res = validate_semantic_program(bad_spec)
    assert res.ok is False
    assert "push chỉ hợp lệ trên stack" in res.error


def test_validator_rejects_enqueue_to_stack():
    """Validator bắt đúng lỗi enqueue vào stack."""
    bad_spec = SemanticProgramSpec(
        title="Lỗi enqueue vào stack",
        memory_declarations=[
            MemoryDeclaration(name="s", type="stack", initial_value=[]),
        ],
        statements=[
            EnqueueStmt(container="s", val=LiteralExpr(value=10)),
        ],
    )
    res = validate_semantic_program(bad_spec)
    assert res.ok is False
    assert "enqueue chỉ hợp lệ trên queue" in res.error


def test_validator_rejects_write_index_on_non_indexed_container():
    """Validator bắt đúng lỗi write_index trên kiểu không hỗ trợ (stack/queue)."""
    bad_spec = SemanticProgramSpec(
        title="Lỗi write_index trên stack",
        memory_declarations=[
            MemoryDeclaration(name="s", type="stack", initial_value=[]),
        ],
        statements=[
            WriteIndexStmt(container="s", index=LiteralExpr(value=0), val=LiteralExpr(value=5)),
        ],
    )
    res = validate_semantic_program(bad_spec)
    assert res.ok is False
    assert "write_index chỉ hợp lệ trên array hoặc matrix" in res.error


def test_validator_rejects_break_outside_loop():
    """Validator bắt lỗi 'break' nằm ngoài vòng lặp."""
    bad_spec = SemanticProgramSpec(
        title="Lỗi break ngoài loop",
        memory_declarations=[
            MemoryDeclaration(name="x", type="int", initial_value=0),
        ],
        statements=[
            BreakStmt(),
        ],
    )
    res = validate_semantic_program(bad_spec)
    assert res.ok is False
    assert "Lệnh 'break' chỉ được xuất hiện bên trong vòng lặp" in res.error


def test_validator_rejects_pointer_to_nonexistent_container():
    """Validator bắt lỗi visual pointer trỏ vào container không tồn tại."""
    from app.simulation.semantic_program.contract import VisualBindings, VisualPointerBinding

    bad_spec = SemanticProgramSpec(
        title="Lỗi pointer rác",
        memory_declarations=[
            MemoryDeclaration(name="i", type="int", initial_value=0),
        ],
        statements=[
            AssignStmt(target_var="i", expr=LiteralExpr(value=1)),
        ],
        visual_bindings=VisualBindings(
            pointers=[
                VisualPointerBinding(pointer_id="ptr_i", var_ref="i", target_container="ghost_array", label="i"),
            ]
        ),
    )
    res = validate_semantic_program(bad_spec)
    assert res.ok is False
    assert "target_container 'ghost_array' không tồn tại" in res.error
