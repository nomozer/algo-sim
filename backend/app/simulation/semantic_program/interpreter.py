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
    IfStmt,
    WhileStmt,
    ForRangeStmt,
    BreakStmt,
    ReturnStmt,
    LiteralExpr,
    VarRefExpr,
    BinaryArithExpr,
    UnaryArithExpr,
    CompareCond,
    LogicCond,
    NotCond,
)
from .validator import validate_semantic_program

DEFAULT_MAX_STEPS = 300

from .geometry_exec import (  # noqa: E402
    GEOMETRY_TYPES,
    ke_thiet_dien,
    build_initial,
    chuan_hoa_dai_luong,
    exec_construct_line,
    exec_construct_segment,
    exec_construct_plane,
    exec_construct_plane_from_equation,
    exec_construct_polygon,
    exec_construct_point,
    exec_construct_curved_solid,
    exec_construct_section,
    exec_construct_solid,
    eval_geometry_expr,
)


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


#: Biểu thức/thao tác không có nhánh thực thi (fail-closed). Giá trị giữ nguyên chuỗi cũ để telemetry cũ còn đọc được;
#: (/13) các mã container (EMPTY_CONTAINER / INDEX_OUT_OF_RANGE / UNDECLARED_CONTAINER) đã gỡ cùng thao tác container.
ERR_SAI_KIEU = "CONTAINER_TYPE_MISMATCH"


class SemanticTraceStep(BaseModel):
    step_index: int = Field(..., description="Chỉ số bước thực thi (0-indexed)")
    action: str = Field(..., description="Hành động ngữ nghĩa (assign, push, pop, compare, swap...)")
    target: Optional[str] = Field(None, description="Tên đối tượng hoặc biến mục tiêu")
    details: dict[str, Any] = Field(default_factory=dict, description="Chi tiết thao tác (chỉ số, giá trị, toán hạng)")
    memory_snapshot: dict[str, Any] = Field(..., description="Bản chụp toàn bộ bộ nhớ sau bước này")
    tier1_narration: str = Field(..., description="Thuyết minh sự thật thực thi (Tier 1)")
    semantic_kind: str = Field(
        ...,
        description="GEOMETRY_CONSTRUCTION | MEASUREMENT | EXPLANATION | FINAL_RESULT",
    )


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
        self._compiler_geometry = any(
            getattr(d, "provenance", None) == "LAYOUT_DERIVED"
            for d in spec.memory_declarations
        )
        self._kieu_khai = {d.name: d.type for d in spec.memory_declarations}
        self._last_solid_vertex_count = 0
        self._last_solid_is_pyramid = False

        # Chương trình này có phải chương trình HÌNH HỌC không — quyết một
        # lần, không hỏi lại từng khai báo. Một chương trình hình học luôn khai
        # ít nhất một vật hình học; chương trình Tin học thì không khai cái nào.
        mien_hinh_hoc = any(d.type in GEOMETRY_TYPES
                            for d in spec.memory_declarations)

        for decl in spec.memory_declarations:
            # Kiểu HÌNH HỌC dựng thành đối tượng của kernel ngay từ đây, thay
            # vì để nguyên JSON. Để nguyên thì mỗi phép dựng lại phải tự đoán
            # hình dạng, và chỗ đoán ấy là nơi lỗi kiểu lọt qua im lặng.
            if decl.type in GEOMETRY_TYPES:
                self.memory[decl.name] = build_initial(
                    decl.type, copy.deepcopy(decl.initial_value), decl.name
                )
            else:
                # VÔ HƯỚNG mang dữ kiện đề (`IA = 6`, `R = 13`) được đưa về
                # miền số CHÍNH XÁC ngay tại đây — cùng biên mà kiểu hình học
                # đi qua `build_initial`. Không làm ở đây thì `6` nằm trong bộ
                # nhớ dưới dạng chuỗi, và CẢ HAI người đọc miền hình học
                # (`build_scene`, `learner_surface`) đều không nhận ra nó là
                # một đại lượng — xem `chuan_hoa_dai_luong`.
                #
                # Kiểu KHAI không đổi; đây là biểu diễn runtime. Đọc không được
                # thì giữ nguyên, nên chuỗi vô nghĩa vẫn fail-closed như cũ.
                self.memory[decl.name] = chuan_hoa_dai_luong(
                    decl.type, copy.deepcopy(decl.initial_value),
                    mien_hinh_hoc=mien_hinh_hoc,
                )

        # Lưu snapshot ban đầu bước 0
        init_narration = (
            "Khởi tạo các điểm theo cấu trúc hình và bố trí tất định."
            if mien_hinh_hoc and self._compiler_geometry
            else "Khởi tạo mô phỏng và nạp trạng thái ban đầu của bộ nhớ."
        )
        self._record_step(
            action="init",
            target="system",
            details={},
            narration=init_narration,
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
            narration = self._mo_ta_phep_gan(stmt, val)

            self._record_step(
                action="assign",
                target=stmt.target_var,
                details={"value": val},
                narration=narration,
            )

        # ── DỰNG HÌNH ────────────────────────────────────────────────────
        # Ba nhánh này KHÔNG tự tính toạ độ. Chúng đọc tên, gọi `geometry_exec`,
        # và `geometry_exec` gọi kernel. Mọi `GeometryError` để nguyên cho nó
        # bay lên — kernel đã phân biệt "song song nên không giao" với "nằm
        # trong nên giao vô số điểm", nuốt ở đây là xoá mất phân biệt ấy.
        elif stmt.kind == "construct_point":
            p, ke = exec_construct_point(stmt, self.memory)
            self.memory[stmt.target_var] = p
            self._record_step(
                action="construct_point", target=stmt.target_var,
                details={"label": stmt.label, "toa_do": [str(p.x), str(p.y), str(p.z)]},
                narration=ke,
            )

        elif stmt.kind == "construct_line":
            ln, ke = exec_construct_line(stmt, self.memory)
            self.memory[stmt.target_var] = ln
            self._record_step(
                action="construct_line", target=stmt.target_var,
                details={"label": stmt.label,
                         "qua": [stmt.through_a, stmt.through_b]},
                narration=ke,
            )

        elif stmt.kind == "construct_segment":
            val, ke = exec_construct_segment(stmt, self.memory)
            self.memory[stmt.target_var] = val
            objects = [it["name"] for it in stmt.items] if stmt.items else [stmt.target_var]
            qua = (
                [[it["endpoint_a"], it["endpoint_b"]] for it in stmt.items]
                if stmt.items
                else [stmt.endpoint_a, stmt.endpoint_b]
            )
            self._record_step(
                action="construct_segment",
                target=stmt.target_var,
                details={
                    "label": stmt.label,
                    "objects": objects,
                    "qua": qua,
                },
                narration=ke,
            )

        elif stmt.kind == "construct_plane":
            pl, ke = exec_construct_plane(stmt, self.memory)
            self.memory[stmt.target_var] = pl
            self._record_step(
                action="construct_plane", target=stmt.target_var,
                details={"label": stmt.label, "qua": list(stmt.through)},
                narration=ke,
            )

        elif stmt.kind == "construct_plane_from_equation":
            pl, ke = exec_construct_plane_from_equation(stmt, self.memory)
            self.memory[stmt.target_var] = pl
            # `action` DÙNG LẠI `construct_plane`: hai câu lệnh sinh ra cùng
            # một loại vật, và `action` là thứ Scene3D đọc để biết vẽ gì. Phát
            # một action thứ hai cho cùng một vật là bắt mọi tầng hiển thị mọc
            # thêm một nhánh, rồi hai nhánh trôi khỏi nhau. Cách dựng nằm ở
            # `details`, nơi nó thuộc về.
            self._record_step(
                action="construct_plane", target=stmt.target_var,
                details={"label": stmt.label,
                         "phuong_trinh": {t: str(getattr(stmt, t))
                                          for t in ("a", "b", "c", "d")}},
                narration=ke,
            )

        elif stmt.kind == "construct_polygon":
            dg, ke = exec_construct_polygon(stmt, self.memory)
            self.memory[stmt.target_var] = dg
            self._record_step(
                action="construct_polygon", target=stmt.target_var,
                details={"label": stmt.label, "dinh": list(stmt.vertices)},
                narration=ke,
            )

        elif stmt.kind == "construct_curved_solid":
            kh, ke = exec_construct_curved_solid(stmt, self.memory)
            self.memory[stmt.target_var] = kh
            self._record_step(
                action="construct_curved_solid", target=stmt.target_var,
                details={"label": stmt.label, "loai": stmt.curved_kind,
                         "neo": [t for t in (stmt.anchor, stmt.apex_or_top,
                                             stmt.rim_point, stmt.radius)
                                 if t]},
                narration=ke,
            )

        elif stmt.kind == "construct_solid":
            kh, ke = exec_construct_solid(stmt, self.memory)
            self.memory[stmt.target_var] = kh
            self._last_solid_vertex_count = len(stmt.vertices)
            self._last_solid_is_pyramid = len(stmt.faces) == len(stmt.vertices)
            self._record_step(
                action="construct_solid", target=stmt.target_var,
                details={"label": stmt.label, "dinh": list(stmt.vertices),
                         "so_mat": len(stmt.faces)},
                narration=ke,
            )

        elif stmt.kind == "construct_section":
            sec, ke_list = exec_construct_section(stmt, self.memory)
            self.memory[stmt.target_var] = sec
            # MỘT câu lệnh IR → NHIỀU bước timeline. Thứ tự cạnh do kernel
            # quyết, và chính nó là dãy thao tác học sinh làm trên giấy.
            for i, (st, ke) in enumerate(zip(sec.steps, ke_list)):
                self._record_step(
                    action="section_edge", target=stmt.target_var,
                    details={"canh": i, "mat": st.face_index,
                             "a": [str(st.a.x), str(st.a.y), str(st.a.z)],
                             "b": [str(st.b.x), str(st.b.y), str(st.b.z)],
                             "khoi": stmt.solid, "mat_phang": stmt.plane,
                             "thiet_dien": stmt.target_var},
                    narration=ke,
                )
            # BƯỚC KHÉP — dãy `section_edge` kể *vẽ từng cạnh thế nào* nhưng
            # không bước nào nói **kết quả là gì**: không bước nào mang tên
            # khối, tên mặt phẳng, hay số đỉnh. Bước này nói.
            #
            # Đặt SAU cùng chứ không phải trước, vì chỉ tới đây kernel mới trả
            # về số đỉnh. Gọi một đa giác là "tứ giác" trước khi đếm là để
            # tầng kể chuyện tự kết luận hình học — đúng thứ R0 cấm.
            self._record_step(
                action="construct_section", target=stmt.target_var,
                details={"khoi": stmt.solid, "mat_phang": stmt.plane,
                         "so_dinh": len(sec.polygon),
                         "chu_trinh": [[str(v.x), str(v.y), str(v.z)]
                                       for v in sec.polygon],
                         "mat_sinh_canh": [s.face_index for s in sec.steps]},
                # W4 · yêu cầu 6: tên qua `ke_thiet_dien` — không tên biến IR, không lặp danh từ.
                # Mặt phẳng được gọi theo NHÃN câu lệnh đã dựng nó ("Mặt phẳng (α): z = 3"), không theo tên biến.
                narration=ke_thiet_dien(stmt.label or stmt.target_var, stmt.solid,
                                        next((b.details.get("label") for b in reversed(self.trace)
                                              if b.target == stmt.plane and b.details.get("label")), stmt.plane),
                                        len(sec.polygon)),
                # Khép thiết diện là một bước DỰNG. Kết luận của bài (đáp số)
                # do tầng cảnh xác định từ mục tiêu của đề (w10); gắn
                # FINAL_RESULT ở đây từng đẩy "kết luận" lên TRƯỚC các bước đo.
                semantic_kind="GEOMETRY_CONSTRUCTION",
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
        elif isinstance(expr, BinaryArithExpr):
            l = self._eval_value(expr.left)
            r = self._eval_value(expr.right)
            from fractions import Fraction
            from ..geometry.radical import Radical, add as _rad_add, multiply as _rad_mul, negate as _rad_neg, parse_exact as _parse_exact
            if isinstance(l, (Fraction, Radical)) and isinstance(r, str):
                rp = _parse_exact(r)
                if rp is not None:
                    r = rp
            elif isinstance(r, (Fraction, Radical)) and isinstance(l, str):
                lp = _parse_exact(l)
                if lp is not None:
                    l = lp
            if isinstance(l, Radical) or isinstance(r, Radical):
                if expr.op == "+":
                    if isinstance(l, str) or isinstance(r, str):
                        return str(l) + str(r)
                    return _rad_add(l, r)
                elif expr.op == "-":
                    return _rad_add(l, _rad_neg(r))
                elif expr.op == "*":
                    return _rad_mul(l, r)
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
            from ..geometry.radical import Radical, negate as _rad_neg
            if expr.op == "-" and isinstance(v, Radical):
                return _rad_neg(v)
            return -v if expr.op == "-" else v

        # ── BIỂU THỨC HÌNH HỌC trong `assign` ────────────────────────────
        #
        # Trước Wave 2, nhánh này KHÔNG tồn tại và hàm rơi thẳng xuống
        # `return None` bên dưới. Biểu thức hình học vì thế chỉ chạy được qua
        # `construct_point`; đặt cùng biểu thức ấy vào một `assign` thì
        # `ValueExpr` NHẬN (nó nằm trong union), validator NHẬN, interpreter
        # trả `None`, và biến mang `None` đi tiếp — không một tầng nào kêu.
        #
        # Đo được ngay khi viết `test_geo_09_DI_TRON_DUONG`: `V` ra `None`,
        # C₁b báo *"witness không được hiện thực hoá"*, và lời chẩn đoán ấy chỉ
        # đúng một nửa — witness KHÔNG được hiện thực hoá vì phép tính không hề
        # chạy, chứ không phải vì nhánh chết.
        from .validator import _BIEU_THUC_HINH_HOC

        if getattr(expr, "kind", None) in _BIEU_THUC_HINH_HOC:
            return eval_geometry_expr(expr.kind, expr, self.memory)

        # FAIL-CLOSED thay cho `return None`. Một `kind` chưa ai xử lý là LỖI
        # HỢP ĐỒNG — thêm biểu thức vào union mà quên nhánh ở đây. Trả `None`
        # biến lỗi ấy thành một giá trị hợp lệ chạy tiếp, và nó chỉ lộ ra ở
        # cách xa chỗ hỏng.
        raise SemanticExecutionError(
            ERR_SAI_KIEU,
            f"biểu thức '{getattr(expr, 'kind', type(expr).__name__)}' chưa "
            "có nhánh thực thi",
        )

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
        return False

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

    def _ten_hien_thi_nhanh(self, oid: Optional[str]) -> str:
        """Resolve a clean learner-facing reference for an IR identifier without snake_case leaks."""
        if not oid:
            return "đối tượng"
        for step in reversed(self.trace):
            if step.target == oid:
                lbl = (step.details or {}).get("label")
                if isinstance(lbl, str) and lbl.strip() and "_" not in lbl:
                    return lbl.strip().replace("'", "′")
        from .display_names import MO_TA_KIEU, ky_hieu_dai_luong
        from .source_entities import dinh_danh_thuc_the

        kieu = self._kieu_khai.get(oid)
        if kieu in ("point3", "line3", "segment3", "solid", "polygon3") or oid.endswith("_prime"):
            _, sym = dinh_danh_thuc_the(oid)
            if sym and "_" not in sym:
                return sym
        if "_" not in oid:
            return ky_hieu_dai_luong(oid) or oid
        return MO_TA_KIEU.get(kieu or "", "đối tượng").lower()

    def _mo_ta_phep_gan(self, stmt: AssignStmt, val: Any) -> str:
        """Format learner- and engine-safe narration for any AssignStmt regardless of compiler mode."""
        from ..geometry import Line3, Plane3
        from ..geometry.curved import Circle3, CurvedSolid, Ellipse3
        from ..geometry.section import Polyhedron, Section
        from .display_names import MO_TA_KIEU, ky_hieu_dai_luong
        from .geometry_exec import phan_loai_quan_he_do
        from .source_entities import dinh_danh_thuc_the

        expr_kind = getattr(stmt.expr, "kind", None)
        if expr_kind == "measure":
            qty = getattr(stmt.expr, "quantity", "")
            of_id = getattr(stmt.expr, "of", "")
            wrt_id = getattr(stmt.expr, "wrt", None)
            sym_a = self._ten_hien_thi_nhanh(of_id)
            sym_b = self._ten_hien_thi_nhanh(wrt_id) if wrt_id else ""
            obj_a = self.memory.get(of_id)
            obj_b = self.memory.get(wrt_id) if wrt_id else None
            rel = phan_loai_quan_he_do(qty, val, obj_a, obj_b)

            if qty == "angle_cos_sq":
                rel_text = {
                    "perpendicular_lines": f" Do cos² = 0 nên hai đường thẳng {sym_a} và {sym_b} vuông góc với nhau.",
                    "perpendicular_planes": f" Do cos² = 0 nên hai mặt phẳng {sym_a} và {sym_b} vuông góc với nhau.",
                    "perpendicular_line_plane": f" Do cos² = 0 nên {sym_a} vuông góc với {sym_b}.",
                    "parallel_lines": f" Do cos² = 1 nên hai đường thẳng {sym_a} và {sym_b} song song hoặc trùng nhau.",
                    "parallel_planes": f" Do cos² = 1 nên hai mặt phẳng {sym_a} và {sym_b} song song hoặc trùng nhau.",
                    "parallel_line_plane": f" Do cos² = 1 nên {sym_a} song song hoặc nằm trong {sym_b}.",
                }.get(rel or "", "")
                return f"Tính cos² góc giữa {sym_a} và {sym_b}: cos²({sym_a}, {sym_b}) = {val}.{rel_text}"
            if qty == "angle_cos":
                rel_text = {
                    "orthogonal_vectors": "; do cos = 0 nên hai vectơ vuông góc",
                    "same_direction_vectors": "; do cos = 1 nên hai vectơ cùng hướng",
                    "opposite_direction_vectors": "; do cos = -1 nên hai vectơ ngược hướng",
                }.get(rel or "", "")
                return f"Tính cosin góc giữa hai vectơ {sym_a} và {sym_b}: cos({sym_a}, {sym_b}) = {val}{rel_text}."
            if qty == "distance":
                meaning = {
                    "coincident_points": " (hai điểm trùng nhau)",
                    "point_on_line": " (điểm nằm trên đường thẳng)",
                    "point_on_plane": " (điểm nằm trên mặt phẳng)",
                    "coplanar_intersecting_or_coincident_lines": " (hai đường thẳng đồng phẳng cắt nhau hoặc trùng nhau)",
                    "line_intersects_or_in_plane": " (đường thẳng cắt hoặc nằm trong mặt phẳng)",
                    "intersecting_or_coincident_planes": " (hai mặt phẳng cắt nhau hoặc trùng nhau)",
                }.get(rel or "", "")
                return f"Xác định khoảng cách giữa {sym_a} và {sym_b} bằng {val}{meaning}."
            if qty == "area":
                return f"Tính diện tích {sym_a}: {val}."
            if qty == "volume":
                dimension_values = {
                    value for name, value in self.memory.items()
                    if name.endswith("_length") and value is not None
                }
                if self._last_solid_vertex_count == 8 and len(dimension_values) == 1:
                    return f"Tính thể tích V = a³ = {val}."
                return f"Tính thể tích {sym_a}: {val}."
            if qty == "radius":
                return f"Tính bán kính của {sym_a}: {val}."
            if qty == "lateral_area":
                return f"Tính diện tích xung quanh của {sym_a}: {val}."

        if expr_kind == "vector_from_points":
            return "Lấy vectơ {}{}.".format(*(dinh_danh_thuc_the(p)[1] for p in (
                stmt.expr.from_point, stmt.expr.to_point)))

        if expr_kind == "var":
            target_symbol = ky_hieu_dai_luong(stmt.target_var)
            source_symbol = ky_hieu_dai_luong(getattr(stmt.expr, "name", ""))
            if target_symbol and source_symbol:
                if stmt.target_var.endswith("_length"):
                    return f"Suy ra {target_symbol} = {source_symbol} = {val}."
                if stmt.target_var == "V":
                    return f"Kết luận {target_symbol} = {val}."

        runtime_type_map = (
            (Circle3, "circle3"),
            (Ellipse3, "ellipse3"),
            (Line3, "line3"),
            (Plane3, "plane3"),
            (Polyhedron, "solid"),
            (Section, "section"),
            (CurvedSolid, "curved_solid"),
        )
        declared_type = self._kieu_khai.get(stmt.target_var)
        detected_type = declared_type if declared_type in GEOMETRY_TYPES else next(
            (name for cls, name in runtime_type_map if isinstance(val, cls)),
            None,
        )
        if detected_type is not None:
            # A geometric object is NAMED, never printed: `str()` of a kernel value is Python repr.
            target_symbol = self._ten_hien_thi_nhanh(stmt.target_var)
            noun = MO_TA_KIEU[detected_type].lower()
            clean_lbl = str(getattr(stmt, "label", "") or "").strip()
            if clean_lbl and "_" not in clean_lbl:
                return f"Dựng {clean_lbl}." if not clean_lbl.lower().startswith(noun) else f"Dựng {clean_lbl[:1].lower() + clean_lbl[1:]}."
            return f"Dựng {noun} {target_symbol}." if target_symbol and target_symbol != noun else f"Dựng {noun} cần dùng."

        lbl = str(getattr(stmt, "label", "") or "").strip()
        if lbl and "_" not in lbl:
            return f"Tính {lbl[:1].lower() + lbl[1:]}: {val}."
        target_symbol = ky_hieu_dai_luong(stmt.target_var)
        if target_symbol and "_" not in stmt.target_var:
            return f"Tính giá trị {target_symbol} = {val}."
        return f"Tính giá trị đại lượng: {val}."

    def _record_step(
        self,
        action: str,
        target: Optional[str],
        details: dict[str, Any],
        narration: str,
        semantic_kind: str | None = None,
    ) -> None:
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
            semantic_kind=semantic_kind or self._semantic_kind(action),
        )
        self.trace.append(step)
        self.step_counter += 1

    @staticmethod
    def _semantic_kind(action: str) -> str:
        if action.startswith("construct_") or action == "section_edge":
            return "GEOMETRY_CONSTRUCTION"
        if action == "assign":
            return "MEASUREMENT"
        return "EXPLANATION"
