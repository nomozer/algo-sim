# -*- coding: utf-8 -*-
"""Bộ kiểm tra tĩnh & thẩm định bất biến (Static Invariant & Type Validator) cho SemanticProgram.

Mọi chương trình ngữ nghĩa đều phải qua bộ kiểm tra này trước khi thực thi:
- Không biến mồ côi (undeclared variables).
- Không thao tác sai kiểu (Type Mismatch: e.g. push vào queue, dequeue từ stack, mod trên chuỗi).
- Ràng buộc trực quan (Visual Bindings) nhất quán với bộ nhớ.
- Độ phức tạp có giới hạn tĩnh (Bounded Execution & Nesting Depth).
"""
from __future__ import annotations
from typing import Any, Optional, Set
from pydantic import ValidationError
from .contract import (
    SemanticProgramSpec,
    MemoryDeclaration,
    ValueExpr,
    ConditionExpr,
    SemanticStatement,
    AssignStmt,
    WriteIndexStmt,
    MapSetStmt,
    SwapStmt,
    PushStmt,
    PopStmt,
    EnqueueStmt,
    DequeueStmt,
    SetInsertStmt,
    SetRemoveStmt,
    IfStmt,
    WhileStmt,
    ForRangeStmt,
    ForEachStmt,
    BreakStmt,
    ReturnStmt,
    LiteralExpr,
    VarRefExpr,
    IndexRefExpr,
    FieldRefExpr,
    BinaryArithExpr,
    UnaryArithExpr,
    LengthExpr,
    PeekExpr,
    MapGetExpr,
    NeighborsExpr,
    CompareCond,
    LogicCond,
    NotCond,
    IsEmptyCond,
    ContainsCond,
    IsNullCond,
)

MAX_STATEMENTS = 50
MAX_NESTING_DEPTH = 4
MAX_MEMORY_DECLARATIONS = 20

class ValidationResult:
    def __init__(self, ok: bool, error: Optional[str] = None, spec: Optional[SemanticProgramSpec] = None):
        self.ok = ok
        self.error = error
        self.spec = spec

    def __repr__(self) -> str:
        return f"<ValidationResult ok={self.ok} error={self.error}>"


class SemanticTypeChecker:
    def __init__(self, spec: SemanticProgramSpec):
        self.spec = spec
        self.symbols: dict[str, MemoryDeclaration] = {}
        self.scoped_vars: set[str] = set()
        self.in_loop_depth: int = 0
        self.total_statements_count: int = 0

    def check(self) -> ValidationResult:
        # 1. Kiểm tra giới hạn số lượng khai báo bộ nhớ
        if len(self.spec.memory_declarations) > MAX_MEMORY_DECLARATIONS:
            return ValidationResult(False, f"Số lượng khai báo bộ nhớ vượt quá giới hạn ({MAX_MEMORY_DECLARATIONS}).")

        # 2. Xây dựng Symbol Table và kiểm tra trùng lặp
        for decl in self.spec.memory_declarations:
            if decl.name in self.symbols:
                return ValidationResult(False, f"Tên vùng nhớ bị khai báo trùng lặp: '{decl.name}'.")
            self.symbols[decl.name] = decl

        # 3. Kiểm tra tính hợp lệ của Visual Bindings
        for cb in self.spec.visual_bindings.containers:
            if cb.semantic_id not in self.symbols:
                return ValidationResult(False, f"Visual binding container '{cb.semantic_id}' không tồn tại trong memory_declarations.")
            decl = self.symbols[cb.semantic_id]
            if decl.type not in ("array", "stack", "queue", "matrix", "tree_node", "graph", "bit_register", "set", "map"):
                return ValidationResult(False, f"Visual binding container '{cb.semantic_id}' có kiểu '{decl.type}' không phải kiểu container hợp lệ.")

        for pb in self.spec.visual_bindings.pointers:
            if pb.var_ref not in self.symbols and pb.var_ref not in self.scoped_vars:
                # Có thể là loop_var, kiểm tra tạm thời
                pass
            if pb.target_container not in self.symbols:
                return ValidationResult(False, f"Visual binding pointer '{pb.pointer_id}' trỏ vào target_container '{pb.target_container}' không tồn tại.")

        for vb in self.spec.visual_bindings.value_boxes:
            if vb.var_ref not in self.symbols and vb.var_ref not in self.scoped_vars:
                # Sẽ kiểm tra sau khi duyệt toàn bộ biến gán
                pass

        # 4. Kiểm tra cây lệnh (Statements)
        err = self._check_statements(self.spec.statements, depth=1)
        if err:
            return ValidationResult(False, err)

        if self.total_statements_count > MAX_STATEMENTS:
            return ValidationResult(False, f"Tổng số câu lệnh ({self.total_statements_count}) vượt quá giới hạn cho phép ({MAX_STATEMENTS}).")

        return ValidationResult(True, None, self.spec)

    def _check_statements(self, statements: list[SemanticStatement], depth: int) -> Optional[str]:
        if depth > MAX_NESTING_DEPTH:
            return f"Độ sâu lồng lệnh ({depth}) vượt quá giới hạn tối đa ({MAX_NESTING_DEPTH})."

        for stmt in statements:
            self.total_statements_count += 1
            err = self._check_single_statement(stmt, depth)
            if err:
                return err
        return None

    def _check_single_statement(self, stmt: SemanticStatement, depth: int) -> Optional[str]:
        kind = getattr(stmt, "kind", None)
        if not kind:
            return f"Câu lệnh không có trường 'kind': {stmt}"

        if isinstance(stmt, AssignStmt):
            # Biến được gán nếu chưa có trong symbols thì được ghi nhận vào scoped_vars
            err = self._check_value_expr(stmt.expr)
            if err:
                return err
            self.scoped_vars.add(stmt.target_var)
            return None

        elif isinstance(stmt, WriteIndexStmt):
            if stmt.container not in self.symbols:
                return f"write_index tham chiếu container không tồn tại: '{stmt.container}'."
            target_type = self.symbols[stmt.container].type
            if target_type not in ("array", "matrix"):
                return f"write_index chỉ hợp lệ trên array hoặc matrix, không hợp lệ trên '{target_type}'."
            err = self._check_value_expr(stmt.index)
            if err:
                return err
            if stmt.second_index:
                err = self._check_value_expr(stmt.second_index)
                if err:
                    return err
            return self._check_value_expr(stmt.val)

        elif isinstance(stmt, MapSetStmt):
            if stmt.container not in self.symbols:
                return f"map_set tham chiếu container không tồn tại: '{stmt.container}'."
            if self.symbols[stmt.container].type != "map":
                return f"map_set chỉ hợp lệ trên map, không hợp lệ trên '{self.symbols[stmt.container].type}'."
            err = self._check_value_expr(stmt.key)
            if err:
                return err
            return self._check_value_expr(stmt.val)

        elif isinstance(stmt, SwapStmt):
            if stmt.container not in self.symbols:
                return f"swap tham chiếu container không tồn tại: '{stmt.container}'."
            if self.symbols[stmt.container].type not in ("array", "matrix"):
                return f"swap chỉ hợp lệ trên array hoặc matrix."
            err = self._check_value_expr(stmt.idx_a)
            if err:
                return err
            return self._check_value_expr(stmt.idx_b)

        elif isinstance(stmt, PushStmt):
            if stmt.container not in self.symbols:
                return f"push tham chiếu container không tồn tại: '{stmt.container}'."
            c_type = self.symbols[stmt.container].type
            if c_type not in ("stack", "array"):
                return f"push chỉ hợp lệ trên stack hoặc array, không thể push vào '{c_type}'."
            return self._check_value_expr(stmt.val)

        elif isinstance(stmt, PopStmt):
            if stmt.container not in self.symbols:
                return f"pop tham chiếu container không tồn tại: '{stmt.container}'."
            if self.symbols[stmt.container].type != "stack":
                return f"pop chỉ hợp lệ trên stack, không thể pop từ '{self.symbols[stmt.container].type}'."
            if stmt.dest_var:
                self.scoped_vars.add(stmt.dest_var)
            return None

        elif isinstance(stmt, EnqueueStmt):
            if stmt.container not in self.symbols:
                return f"enqueue tham chiếu container không tồn tại: '{stmt.container}'."
            if self.symbols[stmt.container].type != "queue":
                return f"enqueue chỉ hợp lệ trên queue, không thể enqueue vào '{self.symbols[stmt.container].type}'."
            return self._check_value_expr(stmt.val)

        elif isinstance(stmt, DequeueStmt):
            if stmt.container not in self.symbols:
                return f"dequeue tham chiếu container không tồn tại: '{stmt.container}'."
            if self.symbols[stmt.container].type != "queue":
                return f"dequeue chỉ hợp lệ trên queue, không thể dequeue từ '{self.symbols[stmt.container].type}'."
            if stmt.dest_var:
                self.scoped_vars.add(stmt.dest_var)
            return None

        elif isinstance(stmt, SetInsertStmt):
            if stmt.container not in self.symbols:
                return f"set_insert tham chiếu container không tồn tại: '{stmt.container}'."
            if self.symbols[stmt.container].type != "set":
                return f"set_insert chỉ hợp lệ trên set, không hợp lệ trên '{self.symbols[stmt.container].type}'."
            return self._check_value_expr(stmt.val)

        elif isinstance(stmt, SetRemoveStmt):
            if stmt.container not in self.symbols:
                return f"set_remove tham chiếu container không tồn tại: '{stmt.container}'."
            if self.symbols[stmt.container].type != "set":
                return f"set_remove chỉ hợp lệ trên set, không hợp lệ trên '{self.symbols[stmt.container].type}'."
            return self._check_value_expr(stmt.val)

        elif isinstance(stmt, IfStmt):
            err = self._check_condition_expr(stmt.condition)
            if err:
                return err
            err = self._check_statements(stmt.then_body, depth + 1)
            if err:
                return err
            if stmt.else_body:
                return self._check_statements(stmt.else_body, depth + 1)
            return None

        elif isinstance(stmt, WhileStmt):
            err = self._check_condition_expr(stmt.condition)
            if err:
                return err
            self.in_loop_depth += 1
            err = self._check_statements(stmt.body, depth + 1)
            self.in_loop_depth -= 1
            return err

        elif isinstance(stmt, ForRangeStmt):
            err = self._check_value_expr(stmt.start)
            if err:
                return err
            err = self._check_value_expr(stmt.end)
            if err:
                return err
            self.scoped_vars.add(stmt.loop_var)
            self.in_loop_depth += 1
            err = self._check_statements(stmt.body, depth + 1)
            self.in_loop_depth -= 1
            return err

        elif isinstance(stmt, ForEachStmt):
            if isinstance(stmt.container_or_expr, str):
                if stmt.container_or_expr not in self.symbols:
                    return f"for_each tham chiếu container không tồn tại: '{stmt.container_or_expr}'."
            else:
                err = self._check_value_expr(stmt.container_or_expr)
                if err:
                    return err
            self.scoped_vars.add(stmt.item_var)
            self.in_loop_depth += 1
            err = self._check_statements(stmt.body, depth + 1)
            self.in_loop_depth -= 1
            return err

        elif isinstance(stmt, BreakStmt):
            if self.in_loop_depth <= 0:
                return "Lệnh 'break' chỉ được xuất hiện bên trong vòng lặp (while/for_range/for_each)."
            return None

        elif isinstance(stmt, ReturnStmt):
            if stmt.val:
                return self._check_value_expr(stmt.val)
            return None

        return f"Toán tử câu lệnh không được hỗ trợ hoặc không hợp lệ: {type(stmt)}"

    def _check_value_expr(self, expr: ValueExpr) -> Optional[str]:
        if isinstance(expr, LiteralExpr):
            return None
        elif isinstance(expr, VarRefExpr):
            if expr.name not in self.symbols and expr.name not in self.scoped_vars:
                return f"Tham chiếu biến chưa được khai báo hoặc gán: '{expr.name}'."
            return None
        elif isinstance(expr, IndexRefExpr):
            if expr.container not in self.symbols:
                return f"index_ref tham chiếu container không tồn tại: '{expr.container}'."
            c_type = self.symbols[expr.container].type
            if c_type not in ("array", "matrix", "str"):
                return f"index_ref chỉ hợp lệ trên array/matrix/str, không hợp lệ trên '{c_type}'."
            err = self._check_value_expr(expr.index)
            if err:
                return err
            if expr.second_index:
                return self._check_value_expr(expr.second_index)
            return None
        elif isinstance(expr, FieldRefExpr):
            return self._check_value_expr(expr.target)
        elif isinstance(expr, BinaryArithExpr):
            err = self._check_value_expr(expr.left)
            if err:
                return err
            return self._check_value_expr(expr.right)
        elif isinstance(expr, UnaryArithExpr):
            return self._check_value_expr(expr.expr)
        elif isinstance(expr, LengthExpr):
            if expr.container not in self.symbols:
                return f"length tham chiếu container không tồn tại: '{expr.container}'."
            return None
        elif isinstance(expr, PeekExpr):
            if expr.container not in self.symbols:
                return f"peek tham chiếu container không tồn tại: '{expr.container}'."
            c_type = self.symbols[expr.container].type
            if c_type not in ("stack", "queue", "array"):
                return f"peek chỉ hợp lệ trên stack hoặc queue."
            return None
        elif isinstance(expr, MapGetExpr):
            if expr.container not in self.symbols:
                return f"map_get tham chiếu container không tồn tại: '{expr.container}'."
            if self.symbols[expr.container].type != "map":
                return f"map_get chỉ hợp lệ trên map."
            err = self._check_value_expr(expr.key)
            if err:
                return err
            if expr.default:
                return self._check_value_expr(expr.default)
            return None
        elif isinstance(expr, NeighborsExpr):
            if expr.graph not in self.symbols:
                return f"neighbors tham chiếu graph không tồn tại: '{expr.graph}'."
            if self.symbols[expr.graph].type != "graph":
                return f"neighbors chỉ hợp lệ trên graph."
            return self._check_value_expr(expr.node)
        return f"Biểu thức giá trị không được hỗ trợ: {type(expr)}"

    def _check_condition_expr(self, cond: ConditionExpr) -> Optional[str]:
        if isinstance(cond, CompareCond):
            err = self._check_value_expr(cond.left)
            if err:
                return err
            return self._check_value_expr(cond.right)
        elif isinstance(cond, LogicCond):
            err = self._check_condition_expr(cond.left)
            if err:
                return err
            return self._check_condition_expr(cond.right)
        elif isinstance(cond, NotCond):
            return self._check_condition_expr(cond.expr)
        elif isinstance(cond, IsEmptyCond):
            if cond.container not in self.symbols:
                return f"is_empty tham chiếu container không tồn tại: '{cond.container}'."
            return None
        elif isinstance(cond, ContainsCond):
            if cond.container not in self.symbols:
                return f"contains tham chiếu container không tồn tại: '{cond.container}'."
            return self._check_value_expr(cond.item)
        elif isinstance(cond, IsNullCond):
            return self._check_value_expr(cond.expr)
        return f"Biểu thức điều kiện không được hỗ trợ: {type(cond)}"


def validate_semantic_program(raw_spec: Any) -> ValidationResult:
    """Thẩm định một đặc tả SemanticProgramSpec."""
    if isinstance(raw_spec, dict):
        try:
            spec = SemanticProgramSpec.model_validate(raw_spec)
        except ValidationError as e:
            return ValidationResult(False, f"Lỗi cú pháp schema SemanticProgramSpec: {e}")
    elif isinstance(raw_spec, SemanticProgramSpec):
        spec = raw_spec
    else:
        return ValidationResult(False, f"Đầu vào phải là dict hoặc SemanticProgramSpec, nhận được: {type(raw_spec)}")

    checker = SemanticTypeChecker(spec)
    return checker.check()
