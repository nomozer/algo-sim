# -*- coding: utf-8 -*-
"""SEMANTIC_PROGRAM_INTERPRETER: Động cơ thực thi tất định từng bước cho SemanticProgramSpec.

Nguyên tắc:
- Không eval/exec, không chạy mã tùy tiện.
- Thực thi tất định trên AST đóng của SemanticProgramSpec.
- Sinh SemanticTrace gồm từng bước thực thi nguyên tử kèm snapshot trạng thái bộ nhớ và thuyết minh Tier 1.
- Chống lặp vô hạn bằng giới hạn số bước cứng (max_execution_steps).
"""
from __future__ import annotations
import copy
from typing import Any, Optional, Union
from pydantic import BaseModel, Field

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
from .validator import validate_semantic_program

DEFAULT_MAX_STEPS = 300

class SemanticExecutionError(Exception):
    """Vi phạm biên lúc thực thi — KHÔNG bao giờ thành no-op hay `None`.

    Cùng khuôn `GenericEvaluationError` mà M13-SOUNDNESS dựng cho
    `generic_engine`. Lý do giống hệt, chỉ khác chủ sở hữu: fail-closed nhầm
    tầng thì một chương trình sai sinh ra trace TRÔNG HỢP LÝ, và học sinh xem
    một mô phỏng thiếu bước mà không ai nói cho biết là đang thiếu.

    Bốn mã, đủ để người sửa biết nhìn vào đâu mà không phải đọc trace.
    """

    def __init__(self, code: str, detail: str):
        self.code = code
        super().__init__(f"{code}: {detail}")


#: Lấy phần tử ra khỏi một container rỗng.
ERR_RONG = "EMPTY_CONTAINER"
#: Chỉ số ngoài `[0, len)`. Âm KHÔNG phải "đếm từ cuối" — IR không có ngữ nghĩa đó.
ERR_CHI_SO = "INDEX_OUT_OF_RANGE"
#: Tên container không có trong `memory_declarations`.
ERR_KHONG_CO = "UNDECLARED_CONTAINER"
#: Container có thật nhưng sai kiểu cho thao tác đang làm.
ERR_SAI_KIEU = "CONTAINER_TYPE_MISMATCH"


class SemanticTraceStep(BaseModel):
    step_index: int = Field(..., description="Chỉ số bước thực thi (0-indexed)")
    action: str = Field(..., description="Hành động ngữ nghĩa (assign, push, pop, compare, swap...)")
    target: Optional[str] = Field(None, description="Tên đối tượng hoặc biến mục tiêu")
    details: dict[str, Any] = Field(default_factory=dict, description="Chi tiết thao tác (chỉ số, giá trị, toán hạng)")
    memory_snapshot: dict[str, Any] = Field(..., description="Bản chụp toàn bộ bộ nhớ sau bước này")
    tier1_narration: str = Field(..., description="Thuyết minh sự thật thực thi (Tier 1)")


class SemanticExecutionResult(BaseModel):
    status: str = Field(..., description="'completed' | 'limit_reached' | 'returned'")
    total_steps: int = Field(..., description="Tổng số bước thực thi sinh ra")
    final_memory: dict[str, Any] = Field(..., description="Trạng thái bộ nhớ cuối cùng")
    trace: list[SemanticTraceStep] = Field(..., description="Lịch sử thực thi từng bước")
    return_value: Optional[Any] = Field(None, description="Giá trị trả về nếu có lệnh return")


class SemanticProgramInterpreter:
    def __init__(self, max_steps: int = DEFAULT_MAX_STEPS):
        self.max_steps = max_steps
        self.memory: dict[str, Any] = {}
        self.scope_stack: list[dict[str, Any]] = [{}]
        self.trace: list[SemanticTraceStep] = []
        self.step_counter: int = 0
        self.should_break: bool = False
        self.return_value: Optional[Any] = None
        self.status: str = "completed"

    def execute(self, spec: SemanticProgramSpec) -> SemanticExecutionResult:
        # 1. Thẩm định tĩnh trước khi chạy
        val = validate_semantic_program(spec)
        if not val.ok:
            raise ValueError(f"Chương trình không hợp lệ để thực thi: {val.error}")

        # 2. Khởi tạo bộ nhớ từ memory_declarations
        self.memory.clear()
        self.scope_stack = [{}]
        self.trace.clear()
        self.step_counter = 0
        self.should_break = False
        self.return_value = None
        self.status = "completed"

        for decl in spec.memory_declarations:
            self.memory[decl.name] = copy.deepcopy(decl.initial_value)

        # Lưu snapshot ban đầu bước 0
        self._record_step(
            action="init",
            target="system",
            details={},
            narration="Khởi tạo mô phỏng và nạp trạng thái ban đầu của bộ nhớ.",
        )

        # 3. Thực thi danh sách câu lệnh
        self._execute_statements(spec.statements)

        if self.step_counter >= self.max_steps:
            self.status = "limit_reached"

        return SemanticExecutionResult(
            status=self.status,
            total_steps=len(self.trace),
            final_memory=copy.deepcopy(self.memory),
            trace=self.trace,
            return_value=self.return_value,
        )

    def _execute_statements(self, statements: list[SemanticStatement]) -> None:
        for stmt in statements:
            if self.step_counter >= self.max_steps or self.should_break or self.return_value is not None:
                break
            self._execute_single_statement(stmt)

    def _execute_single_statement(self, stmt: SemanticStatement) -> None:
        if isinstance(stmt, AssignStmt):
            val = self._eval_value(stmt.expr)
            self._set_var(stmt.target_var, val)
            self._record_step(
                action="assign",
                target=stmt.target_var,
                details={"value": val},
                narration=f"Gán {stmt.target_var} = {val}.",
            )

        elif isinstance(stmt, WriteIndexStmt):
            idx = self._eval_value(stmt.index)
            val = self._eval_value(stmt.val)
            container = self._lay_day(stmt.container, "write_index", doi_khong_rong=False)
            if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(container):
                raise SemanticExecutionError(
                    ERR_CHI_SO,
                    f"ghi vào {stmt.container}[{idx!r}] ngoài [0, {len(container)})",
                )
            if stmt.second_index is None:
                container[idx] = val
                self._record_step(
                    action="write_index",
                    target=stmt.container,
                    details={"index": idx, "value": val},
                    narration=f"Ghi giá trị {val} vào {stmt.container}[{idx}].",
                )
            else:
                row = container[idx]
                c_idx = self._eval_value(stmt.second_index)
                if not isinstance(row, list):
                    raise SemanticExecutionError(
                        ERR_SAI_KIEU,
                        f"{stmt.container}[{idx}] không phải một hàng để ghi theo cột",
                    )
                if not isinstance(c_idx, int) or isinstance(c_idx, bool) or not 0 <= c_idx < len(row):
                    raise SemanticExecutionError(
                        ERR_CHI_SO,
                        f"ghi vào {stmt.container}[{idx}][{c_idx!r}] ngoài [0, {len(row)})",
                    )
                row[c_idx] = val
                self._record_step(
                    action="write_index",
                    target=stmt.container,
                    details={"row": idx, "col": c_idx, "value": val},
                    narration=f"Ghi giá trị {val} vào {stmt.container}[{idx}][{c_idx}].",
                )

        elif isinstance(stmt, MapSetStmt):
            key = str(self._eval_value(stmt.key))
            val = self._eval_value(stmt.val)
            container = self.memory[stmt.container]
            if isinstance(container, dict):
                container[key] = val
                self._record_step(
                    action="map_set",
                    target=stmt.container,
                    details={"key": key, "value": val},
                    narration=f"Cập nhật {stmt.container}['{key}'] = {val}.",
                )

        elif isinstance(stmt, SwapStmt):
            idx_a = self._eval_value(stmt.idx_a)
            idx_b = self._eval_value(stmt.idx_b)
            container = self.memory[stmt.container]
            if isinstance(container, list) and 0 <= idx_a < len(container) and 0 <= idx_b < len(container):
                val_a = container[idx_a]
                val_b = container[idx_b]
                container[idx_a], container[idx_b] = container[idx_b], container[idx_a]
                self._record_step(
                    action="swap",
                    target=stmt.container,
                    details={"idx_a": idx_a, "idx_b": idx_b, "val_a": val_a, "val_b": val_b},
                    narration=f"Hoán đổi {stmt.container}[{idx_a}] ({val_a}) và {stmt.container}[{idx_b}] ({val_b}).",
                )

        elif isinstance(stmt, PushStmt):
            val = self._eval_value(stmt.val)
            container = self.memory[stmt.container]
            if isinstance(container, list):
                container.append(val)
                self._record_step(
                    action="push",
                    target=stmt.container,
                    details={"value": val},
                    narration=f"Đẩy giá trị '{val}' vào {stmt.container}.",
                )

        elif isinstance(stmt, PopStmt):
            container = self._lay_day(stmt.container, "pop", doi_khong_rong=True)
            top_val = container.pop()
            if stmt.dest_var:
                self._set_var(stmt.dest_var, top_val)
            self._record_step(
                action="pop",
                target=stmt.container,
                details={"popped_value": top_val, "dest_var": stmt.dest_var},
                narration=f"Lấy phần tử đỉnh '{top_val}' ra khỏi {stmt.container}.",
            )

        elif isinstance(stmt, EnqueueStmt):
            val = self._eval_value(stmt.val)
            container = self._lay_day(stmt.container, "enqueue", doi_khong_rong=False)
            container.append(val)
            self._record_step(
                action="enqueue",
                target=stmt.container,
                details={"value": val},
                narration=f"Thêm '{val}' vào cuối hàng đợi {stmt.container}.",
            )

        elif isinstance(stmt, DequeueStmt):
            container = self._lay_day(stmt.container, "dequeue", doi_khong_rong=True)
            front_val = container.pop(0)
            if stmt.dest_var:
                self._set_var(stmt.dest_var, front_val)
            self._record_step(
                action="dequeue",
                target=stmt.container,
                details={"dequeued_value": front_val, "dest_var": stmt.dest_var},
                narration=f"Lấy phần tử đầu '{front_val}' ra khỏi hàng đợi {stmt.container}.",
            )

        elif isinstance(stmt, SetInsertStmt):
            val = self._eval_value(stmt.val)
            container = self.memory[stmt.container]
            if isinstance(container, (set, list)):
                if isinstance(container, list):
                    if val not in container:
                        container.append(val)
                else:
                    container.add(val)
                self._record_step(
                    action="set_insert",
                    target=stmt.container,
                    details={"value": val},
                    narration=f"Thêm phần tử '{val}' vào tập hợp {stmt.container}.",
                )

        elif isinstance(stmt, SetRemoveStmt):
            val = self._eval_value(stmt.val)
            container = self.memory[stmt.container]
            if isinstance(container, list) and val in container:
                container.remove(val)
            elif isinstance(container, set) and val in container:
                container.discard(val)
            self._record_step(
                action="set_remove",
                target=stmt.container,
                details={"value": val},
                narration=f"Xóa phần tử '{val}' khỏi tập hợp {stmt.container}.",
            )

        elif isinstance(stmt, IfStmt):
            cond_val = self._eval_condition(stmt.condition)
            self._record_step(
                action="eval_condition",
                target="if",
                details={"result": cond_val},
                narration=f"Kiểm tra điều kiện: {'ĐÚNG' if cond_val else 'SAI'}.",
            )
            if cond_val:
                self._execute_statements(stmt.then_body)
            elif stmt.else_body:
                self._execute_statements(stmt.else_body)

        elif isinstance(stmt, WhileStmt):
            iterations = 0
            while iterations < stmt.max_iterations and self.step_counter < self.max_steps:
                cond_val = self._eval_condition(stmt.condition)
                if not cond_val:
                    break
                iterations += 1
                self._execute_statements(stmt.body)
                if self.should_break:
                    self.should_break = False
                    break

        elif isinstance(stmt, ForRangeStmt):
            start_val = int(self._eval_value(stmt.start))
            end_val = int(self._eval_value(stmt.end))
            step_val = int(stmt.step)
            for curr_val in range(start_val, end_val, step_val):
                if self.step_counter >= self.max_steps or self.should_break or self.return_value is not None:
                    break
                self._set_var(stmt.loop_var, curr_val)
                self._record_step(
                    action="loop_step",
                    target=stmt.loop_var,
                    details={"value": curr_val},
                    narration=f"Vòng lặp: {stmt.loop_var} = {curr_val}.",
                )
                self._execute_statements(stmt.body)
                if self.should_break:
                    self.should_break = False
                    break

        elif isinstance(stmt, ForEachStmt):
            if isinstance(stmt.container_or_expr, str):
                items = self.memory.get(stmt.container_or_expr, [])
            else:
                items = self._eval_value(stmt.container_or_expr)

            if isinstance(items, (list, tuple, set)):
                for item in list(items):
                    if self.step_counter >= self.max_steps or self.should_break or self.return_value is not None:
                        break
                    self._set_var(stmt.item_var, item)
                    self._record_step(
                        action="foreach_step",
                        target=stmt.item_var,
                        details={"item": item},
                        narration=f"Xét phần tử: {stmt.item_var} = '{item}'.",
                    )
                    self._execute_statements(stmt.body)
                    if self.should_break:
                        self.should_break = False
                        break

        elif isinstance(stmt, BreakStmt):
            self.should_break = True
            self._record_step(
                action="break",
                target="control",
                details={},
                narration="Thực hiện lệnh break: ngắt vòng lặp hiện thời.",
            )

        elif isinstance(stmt, ReturnStmt):
            if stmt.val:
                self.return_value = self._eval_value(stmt.val)
            else:
                self.return_value = True
            self.status = "returned"
            self._record_step(
                action="return",
                target="control",
                details={"return_value": self.return_value},
                narration=f"Kết thúc chương trình với kết quả: {self.return_value}.",
            )

    def _eval_value(self, expr: ValueExpr) -> Any:
        if isinstance(expr, LiteralExpr):
            return expr.value
        elif isinstance(expr, VarRefExpr):
            return self._get_var(expr.name)
        elif isinstance(expr, IndexRefExpr):
            container = self._lay_container(expr.container, "index")
            idx = self._eval_value(expr.index)
            if not isinstance(container, (list, str)):
                raise SemanticExecutionError(
                    ERR_SAI_KIEU,
                    f"index cần dãy/chuỗi nhưng '{expr.container}' là "
                    f"{type(container).__name__}",
                )
            # Chỉ số ÂM là lỗi, không phải "đếm từ cuối". Python cho `a[-1]`;
            # IR thì không khai ngữ nghĩa ấy ở đâu cả, nên nhận nó là âm thầm
            # thêm một luật không ai dạy cho LLM.
            if not isinstance(idx, int) or isinstance(idx, bool) or not 0 <= idx < len(container):
                raise SemanticExecutionError(
                    ERR_CHI_SO,
                    f"{expr.container}[{idx!r}] ngoài [0, {len(container)})",
                )
            if expr.second_index is None:
                return container[idx]

            row = container[idx]
            c_idx = self._eval_value(expr.second_index)
            if not isinstance(row, list):
                raise SemanticExecutionError(
                    ERR_SAI_KIEU,
                    f"{expr.container}[{idx}] không phải một hàng để lấy chỉ số thứ hai",
                )
            if not isinstance(c_idx, int) or isinstance(c_idx, bool) or not 0 <= c_idx < len(row):
                raise SemanticExecutionError(
                    ERR_CHI_SO,
                    f"{expr.container}[{idx}][{c_idx!r}] ngoài [0, {len(row)})",
                )
            return row[c_idx]
        elif isinstance(expr, FieldRefExpr):
            target = self._eval_value(expr.target)
            if isinstance(target, dict):
                return target.get(expr.field, None)
            return getattr(target, expr.field, None)
        elif isinstance(expr, BinaryArithExpr):
            l = self._eval_value(expr.left)
            r = self._eval_value(expr.right)
            if expr.op == "+":
                if isinstance(l, str) or isinstance(r, str):
                    return str(l) + str(r)
                return l + r
            elif expr.op == "-":
                return l - r
            elif expr.op == "*":
                return l * r
            elif expr.op == "//":
                return l // r if r != 0 else 0
            elif expr.op == "%":
                return l % r if r != 0 else 0
            return 0
        elif isinstance(expr, UnaryArithExpr):
            v = self._eval_value(expr.expr)
            return -v if expr.op == "-" else v
        elif isinstance(expr, LengthExpr):
            # `get(..., [])` rồi `else 0` là HAI lớp bịa chồng nhau: tên sai →
            # độ dài 0, kiểu sai → độ dài 0. Cả hai đều đọc như một sự thật.
            c = self._lay_container(expr.container, "length")
            if not isinstance(c, (list, dict, set, str)):
                raise SemanticExecutionError(
                    ERR_SAI_KIEU,
                    f"length không áp dụng cho '{expr.container}' "
                    f"({type(c).__name__})",
                )
            return len(c)
        elif isinstance(expr, PeekExpr):
            # Trả `None` ở đây thì phép so sánh ngay sau đó lặng lẽ SAI, chứ
            # không lặng lẽ dừng — tệ hơn hẳn một lỗi nổ đúng chỗ.
            return self._lay_day(expr.container, "peek", doi_khong_rong=True)[-1]
        elif isinstance(expr, MapGetExpr):
            m = self.memory.get(expr.container, {})
            key = str(self._eval_value(expr.key))
            default_val = self._eval_value(expr.default) if expr.default else None
            if isinstance(m, dict):
                return m.get(key, default_val)
            return default_val
        elif isinstance(expr, NeighborsExpr):
            g = self.memory.get(expr.graph, {})
            node = str(self._eval_value(expr.node))
            if isinstance(g, dict):
                return g.get(node, [])
            return []
        return None

    def _eval_condition(self, cond: ConditionExpr) -> bool:
        if isinstance(cond, CompareCond):
            l = self._eval_value(cond.left)
            r = self._eval_value(cond.right)
            if cond.op == "==":
                return l == r
            elif cond.op == "!=":
                return l != r
            elif cond.op == "<":
                return l < r
            elif cond.op == "<=":
                return l <= r
            elif cond.op == ">":
                return l > r
            elif cond.op == ">=":
                return l >= r
            return False
        elif isinstance(cond, LogicCond):
            l_res = self._eval_condition(cond.left)
            if cond.op == "and":
                return l_res and self._eval_condition(cond.right)
            elif cond.op == "or":
                return l_res or self._eval_condition(cond.right)
            return False
        elif isinstance(cond, NotCond):
            return not self._eval_condition(cond.expr)
        elif isinstance(cond, IsEmptyCond):
            c = self.memory.get(cond.container, [])
            return len(c) == 0 if isinstance(c, (list, dict, set, str)) else True
        elif isinstance(cond, ContainsCond):
            c = self.memory.get(cond.container, None)
            item = self._eval_value(cond.item)
            if isinstance(c, dict):
                return str(item) in c
            elif isinstance(c, (list, set, tuple, str)):
                return item in c
            return False
        elif isinstance(cond, IsNullCond):
            v = self._eval_value(cond.expr)
            return v is None
        return False

    def _lay_container(self, ten: str, thao_tac: str) -> Any:
        """Đọc một container theo TÊN, fail-closed.

        Thay cho `self.memory.get(ten, [])` — mặc định ấy biến một tên viết sai
        thành một dãy rỗng hợp lệ, và chương trình chạy tiếp trên hư không.
        """
        if ten not in self.memory:
            raise SemanticExecutionError(
                ERR_KHONG_CO,
                f"{thao_tac} tham chiếu '{ten}' không có trong memory_declarations",
            )
        return self.memory[ten]

    def _lay_day(self, ten: str, thao_tac: str, doi_khong_rong: bool) -> list:
        """Container dạng DÃY, fail-closed cả kiểu lẫn tính rỗng."""
        c = self._lay_container(ten, thao_tac)
        if not isinstance(c, list):
            raise SemanticExecutionError(
                ERR_SAI_KIEU,
                f"{thao_tac} cần một dãy nhưng '{ten}' là {type(c).__name__}",
            )
        if doi_khong_rong and not c:
            raise SemanticExecutionError(
                ERR_RONG, f"{thao_tac} trên '{ten}' đang RỖNG"
            )
        return c

    def _get_var(self, name: str) -> Any:
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]
        return self.memory.get(name, None)

    def _set_var(self, name: str, val: Any) -> None:
        if name in self.memory:
            self.memory[name] = val
        else:
            self.scope_stack[-1][name] = val

    def _record_step(self, action: str, target: Optional[str], details: dict[str, Any], narration: str) -> None:
        # Chụp toàn bộ bộ nhớ và các biến trong scope
        full_snap = copy.deepcopy(self.memory)
        for scope in self.scope_stack:
            for k, v in scope.items():
                full_snap[k] = copy.deepcopy(v)

        step = SemanticTraceStep(
            step_index=self.step_counter,
            action=action,
            target=target,
            details=copy.deepcopy(details),
            memory_snapshot=full_snap,
            tier1_narration=narration,
        )
        self.trace.append(step)
        self.step_counter += 1
