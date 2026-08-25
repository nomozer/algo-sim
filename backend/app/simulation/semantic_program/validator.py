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

#: NÂNG 4 → 6 (2026-08-23), có lý do đo được — không phải nới cho dễ thở.
#:
#: IR **không có `elif`**: mỗi nhánh "ngược lại, nếu…" phải viết thành
#: `else_body: [if …]`, tức mỗi bậc của một dây else-if ĂN MỘT TẦNG lồng. Với
#: trần 4, một dây ba bậc là hết chỗ trước khi thân vòng lặp kịp làm gì.
#:
#: Probe E2E (route `serve`, API thật) trên đề ghép ngoặc bằng ngăn xếp — bài
#: ngăn xếp kinh điển của TH11-KHMT — dừng ở `Độ sâu lồng lệnh (5) vượt quá
#: giới hạn tối đa (4)` sau khi MỌI lỗi ký pháp đã hết. Cấu trúc tối thiểu của
#: nó là: duyệt ký tự → nếu ngoặc mở → ngược lại → nếu ngăn xếp rỗng → ngược
#: lại → so khớp đỉnh. Năm tầng là mức SÀN của bài, không phải chương trình
#: viết luộm thuộm.
#:
#: 6 chứ không phải 5: chừa đúng một tầng cho `while`/`for` bọc ngoài, thứ mà
#: bài sắp xếp lồng hai vòng cần tới. Trần vẫn tồn tại — nó chặn chương trình
#: bệnh lý, và `MAX_STATEMENTS` mới là thứ chặn kích thước.
#:
#: NÂNG 6 → 8 (2026-08-24). CÙNG một bài, CÙNG một nguyên nhân cấu trúc, chỉ là
#: lần trước chưa đếm hết: ghép ngoặc không dừng ở *"ngăn xếp rỗng chưa"* mà còn
#: phải so **CẶP** ngoặc — `(` với `)`, `[` với `]`, `{` với `}`. Không có
#: `elif` thì mỗi cặp là thêm một tầng, nên dây so cặp một mình đã ăn hết phần
#: trần mà bản 4 → 6 vừa chừa ra. Lượt `serve` thật (telemetry `6b1ee593`,
#: 2026-08-24) chết ở *"Độ sâu lồng lệnh (7) vượt quá giới hạn tối đa (6)"*.
#:
#: VÌ SAO KHÔNG PHẢI "nới cho qua một ca": trần này chặn theo **hình dạng cú
#: pháp**, mà hình dạng ấy bị thổi lên bởi một thiếu sót đã biết của IR (không
#: `elif`) chứ không phải bởi độ phức tạp thật của bài. Mọi bài có một dây
#: "ngược lại, nếu…" từ ba nhánh trở lên đều chạm cùng bức tường này — đó là
#: một LỚP, không phải một ca.
#:
#: 8 chứ không phải 7: 7 vừa đúng cái quan sát được, và đặt trần bằng đúng quan
#: sát cuối cùng là cách bản 4 → 6 đã sai một lần rồi. Một tầng dự phòng cho
#: dây bốn nhánh.
#:
#: ⚠️ Đây là bản vá HÌNH DẠNG, không phải bản vá ngữ nghĩa. Cách sửa THẬT là cho
#: IR một `elif` để dây else-if không còn ăn tầng — việc đó đổi schema nên phải
#: chờ sau lượt đo #2. Ghi ở `RUN2_PROTOCOL §7b`.
MAX_NESTING_DEPTH = 8

#: Biểu thức hình học → tên các trường mang TÊN ĐỐI TƯỢNG. Bảng này DẪN XUẤT
#: được từ contract, nhưng viết tay ở đây có chủ đích: nó là chỗ duy nhất nói
#: "trường nào là tham chiếu", và dẫn xuất tự động sẽ nuốt luôn `ratio` — một
#: chuỗi phân số, KHÔNG phải tên đối tượng. Thêm biểu thức hình học mà quên
#: dòng ở đây thì validator trả "không được hỗ trợ" và ĐỎ ngay, không im lặng.
from .geometry_exec import GEOMETRY_TYPES

_BIEU_THUC_HINH_HOC: dict[str, tuple[str, ...]] = {
    "intersect_line_plane": ("line", "plane"),
    "intersect_plane_plane": ("plane_a", "plane_b"),
    "intersect_line_line": ("line_a", "line_b"),
    "midpoint": ("a", "b"),
    "divide_segment": ("a", "b"),
    "project_onto": ("point", "target"),
    # `quantity` cố ý VẮNG MẶT: nó là một enum đóng, không phải tên vùng nhớ.
    # Cùng lý do `ratio` vắng mặt ở `divide_segment`.
    "measure": ("of", "wrt"),
}
#: Trần số khai báo bộ nhớ. 20 → 32 (2026-08-25), và lần này CÓ lý do ghi kèm.
#:
#: Con số 20 đến từ thời chỉ có miền Tin học, nơi một chương trình điển hình khai
#: một dãy, một ngăn xếp, vài biến đếm. Một bài THIẾT DIỆN hình học thì khác về
#: bản chất: mỗi ĐIỂM là một khai báo.
#:
#:     S A B C D          5   đỉnh chóp
#:     M N P Q            4   điểm dựng thêm
#:     khối · 2 mặt phẳng 3
#:     2 đường · thiết diện 3
#:     đại lượng đo       1
#:     ────────────────────────
#:                       16   cho một đề TRUNG BÌNH
#:
#: Đo được ở lượt live 2026-08-25 trên đề học sinh gửi thật: mô hình chạm trần ở
#: lượt thử đầu, sửa được ở lượt hai. Tức trần cũ không CHẶN sai — nó chỉ thu
#: một khoản thuế ~30 giây và một call cho gần như mọi đề hình học cỡ này.
#:
#: 32 không phải "nhân đôi cho chắc": nó là 16 (đề trung bình) × 2, và cái chặn
#: chương trình chạy loạn vốn là ngân sách BƯỚC của interpreter, không phải trần
#: này. Trần này chống *khai* loạn, và một đề hình học cần 33 tên thì gần như
#: chắc chắn là mô hình đang khai lại cùng một điểm dưới nhiều tên.
#: Kiểu mà một giá trị KHÔNG được đến từ `literal`. DẪN từ nguồn, không chép:
#: thêm một kiểu hình học vào kernel là nó tự vào luật này.
_KIEU_HINH_HOC = GEOMETRY_TYPES

MAX_MEMORY_DECLARATIONS = 32

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
            # `str` ĐƯỢC bind từ 2026-08-23: một chuỗi LÀ dãy ký tự, và
            # `array_strip` vẫn vẽ nó như vẽ một mảng. Trên SEALED `7e5df014…`
            # hai case (`T10-C5-079`, `T11CS-C6-058`) chết chỉ vì luật này —
            # chương trình quét chuỗi hoàn toàn đúng, nhưng khai chuỗi làm
            # container thì bị từ chối, mà không khai thì học sinh không thấy
            # dữ liệu mình đang duyệt. Cùng lớp với `set` (cũng không phải dãy
            # theo nghĩa hẹp) vốn đã được nhận từ trước.
            if decl.type not in ("array", "stack", "queue", "matrix", "tree_node", "graph", "bit_register", "set", "map", "str"):
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
            # ─── R0 Ở MIỀN HÌNH HỌC: GIÁ TRỊ HÌNH HỌC KHÔNG ĐƯỢC LÀ LITERAL ──
            #
            # Prompt đã dạy luật này từ đầu: *"Bạn chỉ khai toạ độ cho các ĐIỂM
            # gốc. Đường, mặt, khối, thiết diện, số đo đều phải đến từ một phép
            # dựng hoặc một phép đo."* Nhưng nó chỉ là một câu trong prompt, và
            # hợp đồng KHÔNG cưỡng chế — nên nó là lời khuyên, không phải luật.
            #
            # Đo được ở lượt smoke 2026-08-25 (bài thể tích): mô hình khai
            # `ABCD` kiểu `polygon3` rồi `assign ABCD = literal(["A","B","C","D"])`.
            # Một biến kiểu hình học giữ một danh sách CHUỖI. Không cổng nào
            # kêu, và lỗi chỉ lộ ra tận `learner_surface` dưới dạng *"ABCD đổi
            # giá trị nhưng không có binding"* — một thông báo nói về TRIỆU
            # CHỨNG ở cách chỗ sai bốn tầng.
            #
            # Bắt ở đây vì `validate_semantic_program` là thứ DUY NHẤT có đường
            # gửi lỗi ngược cho mô hình sửa (≤3 lượt). Bắt lúc chạy thì chỉ được
            # `executable=False`, không sửa được.
            #
            # `initial_value` của KHAI BÁO thì KHÔNG đụng tới: đó là kênh hợp lệ
            # cho điểm gốc và cho dữ kiện đề cho, và P2 đã gác nó.
            if (sym := self.symbols.get(stmt.target_var)) is not None:
                if sym.type in _KIEU_HINH_HOC and stmt.expr.kind == "literal":
                    return (
                        f"'{stmt.target_var}' kiểu {sym.type} không được gán "
                        f"bằng `literal` — giá trị hình học phải đến từ một phép "
                        f"DỰNG (construct_*) hoặc một phép ĐO. Khai toạ độ trực "
                        f"tiếp chỉ hợp lệ ở `initial_value` của điểm gốc."
                    )
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

        # ── DỰNG HÌNH (2026-08-24) ───────────────────────────────────────
        # Thẩm định TĨNH ở đây chỉ hỏi: mọi tên có được khai chưa. Câu hỏi
        # "hai mặt phẳng này có song song không" là câu hỏi ĐỘNG — chỉ trả lời
        # được khi biết toạ độ, và kernel đã fail-closed đúng chỗ ấy. Cố đoán
        # trước ở đây là dựng một tầng hình học thứ hai, và hai tầng thì sẽ
        # lệch nhau.
        elif stmt.kind in ("construct_point", "construct_line", "construct_plane",
                           "construct_solid", "construct_section",
                           "construct_polygon"):
            for ten in self._ten_tham_chieu(stmt):
                if ten not in self.symbols and ten not in self.scoped_vars:
                    return (f"Câu lệnh dựng tham chiếu '{ten}' chưa khai trong "
                            f"memory_declarations và cũng chưa được dựng trước đó.")
            loi = (self._check_value_expr(stmt.expr)
                   if stmt.kind == "construct_point" else None)
            if loi:
                return loi
            # ĐĂNG KÝ đối tượng vừa dựng — cùng luật `assign`. Không đăng ký thì
            # một dây dựng hai bước (`M = trung điểm AB` rồi `d = MS`) bị từ
            # chối oan, mà dây hai bước chính là hình dạng của MỌI bài dựng hình.
            self.scoped_vars.add(stmt.target_var)
            return None

        return f"Toán tử câu lệnh không được hỗ trợ hoặc không hợp lệ: {type(stmt)}"

    @staticmethod
    def _ten_tham_chieu(stmt) -> list[str]:
        """Tên đối tượng mà một câu lệnh dựng ĐỌC (không tính tên nó GHI RA)."""
        if stmt.kind == "construct_line":
            return [stmt.through_a, stmt.through_b]
        if stmt.kind == "construct_plane":
            return list(stmt.through)
        if stmt.kind in ("construct_solid", "construct_polygon"):
            return list(stmt.vertices)
        if stmt.kind == "construct_section":
            return [stmt.solid, stmt.plane]
        return []

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
        # ── BIỂU THỨC HÌNH HỌC (2026-08-24) ──────────────────────────────
        # Mọi trường của năm biểu thức này là TÊN (khoá bởi
        # `test_R0_bieu_thuc_hinh_hoc_chi_nhan_TEN`), nên thẩm định tĩnh gom
        # được về một luật duy nhất: tên phải đã khai. Kiểu và tính khả thi
        # hình học là việc của kernel — nó có toạ độ, còn ở đây thì không.
        elif expr.kind in _BIEU_THUC_HINH_HOC:
            for ten_truong in _BIEU_THUC_HINH_HOC[expr.kind]:
                ten = getattr(expr, ten_truong)
                # `measure.wrt` là `None` với `volume` (một khối không đo "so
                # với" cái gì cả). Ô trống hợp lệ ≠ tên chưa khai.
                if ten is None:
                    continue
                if ten not in self.symbols and ten not in self.scoped_vars:
                    return (f"Biểu thức '{expr.kind}' tham chiếu '{ten}' chưa "
                            f"khai trong memory_declarations.")
            return None

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
