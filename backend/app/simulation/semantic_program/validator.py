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
import typing

from pydantic import BaseModel, ValidationError
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

#: Biểu thức hình học → tên các trường mang TÊN ĐỐI TƯỢNG.
#:
#: DẪN XUẤT từ `ir_static_check._CHU_KY`, không chép tay. Trước bản này hai bảng
#: khai CÙNG một hợp đồng ở hai chỗ, và chúng đã trôi khỏi nhau một lần có thật:
#: `vector_from_points` vào `_CHU_KY` mà quên `_KIEU_DO`, khiến một chương trình
#: đúng bị từ chối bằng *"cần point3 hoặc line3 … có vector3"* — hệ nói sai, mô
#: hình làm đúng, cả bốn ca live chết vì đó.
#:
#: `measure` thêm tay vì nó KHÔNG cùng khuôn: `quantity` là một enum đóng chứ
#: không phải tên vùng nhớ, nên nó không có mặt trong chữ ký kiểu. Cùng lý do
#: `ratio` của `divide_segment` không có mặt.
from .geometry_exec import GEOMETRY_TYPES
from .ir_static_check import _CHU_KY as _CHU_KY_TINH
from .measure_contract import BANG_PHEP_DO, phep_do

_BIEU_THUC_HINH_HOC: dict[str, tuple[str, ...]] = {
    **{kind: tuple(ten for ten, _ in truong)
       for kind, (truong, _) in _CHU_KY_TINH.items()},
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
    def __init__(self, ok: bool, error: Optional[str] = None, spec: Optional[SemanticProgramSpec] = None,
                 ignored_keys: tuple = ()):
        self.ok = ok
        self.error = error
        self.spec = spec
        #: Khoá lạ KHÔNG mang dữ liệu trong `memory_declarations[]` mà Pydantic (`extra="ignore"`) bỏ qua — được BÁO,
        #: không im lặng. Mỗi mục `{"pointer": "/memory_declarations/<i>/<khoá>", "key": <khoá>}`; không có giá trị.
        self.ignored_keys = ignored_keys

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
        elif stmt.kind in ("construct_point", "construct_line", "construct_segment",
                           "construct_plane",
                           "construct_plane_from_equation",
                           "construct_solid", "construct_section",
                           "construct_polygon", "construct_curved_solid"):
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
            if stmt.kind == "construct_segment" and getattr(stmt, "items", None):
                for it in stmt.items:
                    t_name = it.get("target_var") or it.get("name")
                    if t_name:
                        self.scoped_vars.add(t_name)
            return None

        return f"Toán tử câu lệnh không được hỗ trợ hoặc không hợp lệ: {type(stmt)}"

    @staticmethod
    def _ten_tham_chieu(stmt) -> list[str]:
        """Tên đối tượng mà một câu lệnh dựng ĐỌC (không tính tên nó GHI RA)."""
        if stmt.kind == "construct_line":
            return [stmt.through_a, stmt.through_b]
        if stmt.kind == "construct_segment":
            if getattr(stmt, "items", None):
                res = []
                for it in stmt.items:
                    if it.get("endpoint_a"):
                        res.append(it["endpoint_a"])
                    if it.get("endpoint_b"):
                        res.append(it["endpoint_b"])
                return res
            res = []
            if stmt.endpoint_a:
                res.append(stmt.endpoint_a)
            if stmt.endpoint_b:
                res.append(stmt.endpoint_b)
            return res
        if stmt.kind == "construct_plane":
            return list(stmt.through)
        if stmt.kind in ("construct_solid", "construct_polygon"):
            return list(stmt.vertices)
        if stmt.kind == "construct_section":
            return [stmt.solid, stmt.plane]
        if stmt.kind == "construct_curved_solid":
            # `apex_or_top` VẮNG với khối cầu — lọc `None` ở đây chứ không đẻ
            # một nhánh riêng cho từng loại khối.
            return [t for t in (stmt.anchor, stmt.apex_or_top,
                                stmt.rim_point, stmt.radius) if t]
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
            # `wrt` VẮNG hợp lệ ĐÚNG với `volume`. Với `distance`/`angle_cos_sq`
            # nó là lỗi, và lỗi ấy phải chết Ở ĐÂY chứ không ở kernel.
            #
            # Đo được 2026-08-31 (probe nhị diện, ca «đổi tên đỉnh»): mô hình
            # phát `angle_cos_sq` chỉ có `of`. Schema cho qua (`wrt` là
            # `Optional` vì `volume`), thẩm định tĩnh cho qua, rồi kernel ném
            # `GEOMETRY_OPERAND_TYPE` — và **lỗi runtime KHÔNG được gửi ngược
            # cho mô hình sửa**, chỉ lỗi validator mới được. Nên một sai sót
            # sửa được trong một lượt lại giết cả ca.
            #
            # Đây là luật TỔNG QUÁT của phép đo, không phải bản vá cho nhị diện.
            #
            # ARITY VÀ KIỂU nay đọc từ `measure_contract.BANG_PHEP_DO` — bản
            # trước viết cứng `!= "volume"` ở đây và `== "angle_cos"` ở dưới,
            # tức thẩm quyền kiểu của phép đo nằm rải ba chỗ (thêm kernel) và
            # KHÔNG chỗ nào gửi cho mô hình. Thêm một lượng đo mới thì phải nhớ
            # sửa cả ba; quên một chỗ là im lặng, đúng như `vector3` từng thiếu
            # trong `_KIEU_DO`.
            hd = phep_do(getattr(expr, "quantity", "") or "") \
                if expr.kind == "measure" else None
            if hd and hd.hai_toan_hang and not getattr(expr, "wrt", None):
                mot = [q for q, p in BANG_PHEP_DO.items() if not p.hai_toan_hang]
                return (f"Phép đo '{expr.quantity}' cần HAI đối tượng: thiếu "
                        f"`wrt`. Chỉ {', '.join(mot)} đo trên một đối tượng.")

            # THẨM QUYỀN CỦA HƯỚNG — tĩnh, vì runtime không có nó.
            #
            # `angle_cos` trả một số CÓ DẤU, và dấu là một mệnh đề toán học
            # ("nhị diện này tù"). Nó chỉ được phép đến từ một đối tượng KHAI
            # là có hướng. Ở runtime `vector3` và `point3` cùng là `Vec3`, nên
            # kernel không phân biệt nổi — chỉ chỗ này đọc được kiểu khai.
            #
            # Từ chối `line3` KHÔNG phải hạn chế kỹ thuật: một đường thẳng
            # không có chiều, nên lấy dấu từ nó là để thứ tự hai điểm lúc dựng
            # quyết kết luận. Đó là đúng thứ `angle_cos_sq` tồn tại để tránh.
            # RANH GIỚI TẦNG: chỉ canh thứ TẦNG DƯỚI KHÔNG CANH NỔI.
            #
            # `ir_static` và kernel đều đọc được kiểu, nên `distance` trên một
            # khối hay `volume` trên một điểm là việc của chúng — canh thêm ở
            # đây chỉ chuyển chỗ báo lỗi và làm hai tầng nói cùng một câu.
            #
            # Trừ ĐÚNG MỘT chỗ: `vector3` và `point3` cùng là `Vec3` ở runtime,
            # nên khác biệt "có hướng / không hướng" **chỉ tồn tại ở tầng KHAI**.
            # Đây là tầng duy nhất đọc được `memory_declarations`, nên thẩm
            # quyền của hướng nằm ở đây và không nơi nào khác.
            #
            # Điều kiện suy từ BẢNG, không viết cứng tên `angle_cos`: thêm một
            # phép đo nhận vectơ thì nó tự được canh.
            if hd:
                for truong in ("of", "wrt"):
                    cho = hd.kieu_of if truong == "of" else hd.kieu_wrt
                    if not cho or "vector3" not in cho:
                        continue
                    ten = getattr(expr, truong, None)
                    decl = self.symbols.get(ten) if ten else None
                    if decl is None:
                        return (f"`{hd.quantity}.{truong}` phải trỏ một mục đã "
                                "khai trong memory_declarations.")
                    if hd.kieu_sai(truong, decl.type):
                        goi_y = (hd.goi_y
                                 or f"Phép đo này nhận {' hoặc '.join(cho)}.")
                        return (f"`{hd.quantity}.{truong}` sai kiểu: '{ten}' "
                                f"khai '{decl.type}'. {goi_y}")
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


def _o_gia_tri_tho(model: type) -> Optional[str]:
    """Ô nhận GIÁ TRỊ THÔ của một model — trường khai kiểu `Any`.

    Dẫn xuất, không viết tay: trong `MemoryDeclaration` chỉ `initial_value`
    nhận một giá trị bất kỳ, và tính chất ấy đọc được từ chính annotation. Nhờ
    vậy chẩn đoán bên dưới nêu đúng tên ô kể cả khi ô ấy được đổi tên.
    """
    ds = [n for n, f in model.model_fields.items() if f.annotation is Any]
    return ds[0] if len(ds) == 1 else None


def _la_o_gia_tri(annotation: Any) -> bool:
    """Trường này có phải một Ô GIÁ TRỊ THÔ không? — `Any` hoặc `list[Any]`.

    Đây là phép phân biệt trung tâm của chẩn đoán bên dưới, và nó dẫn xuất từ
    annotation chứ không từ một danh sách tên. `DeclarePointStmt.at` là
    `list[Any]` — nó CHỞ DỮ LIỆU. `label` là `Optional[str]` — nó trang trí.
    Bỏ rơi cái đầu là mất toạ độ; bỏ rơi cái sau là không mất gì.
    """
    if annotation is Any:
        return True
    goc = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    return goc in (list, tuple) and bool(args) and args[0] is Any


def _chu_so_huu_truong(khoa: str) -> tuple[list[str], bool]:
    """`(model nào có trường tên này, có model nào coi nó là ô giá trị không)`.

    Quét hợp đồng, không chép tay. Dùng để nói *"`at` là trường của
    `declare_point`"* thay vì chỉ nói *"khoá lạ"* — một lời từ chối nêu đúng
    chỗ nhầm thì sửa được.
    """
    from . import contract as _C

    ra, la_gt = [], False
    for ten, obj in vars(_C).items():
        if not (isinstance(obj, type) and issubclass(obj, BaseModel)
                and obj is not BaseModel and khoa in obj.model_fields):
            continue
        kind = obj.model_fields.get("kind")
        ra.append(getattr(kind, "default", None) or ten)
        la_gt = la_gt or _la_o_gia_tri(obj.model_fields[khoa].annotation)
    return sorted(set(ra)), la_gt


def _khoa_bi_bo_im_lang(raw_spec: dict) -> Optional[str]:
    """Khoá mô hình gửi trong `memory_declarations[]` mà hợp đồng KHÔNG có.

    ─── VÌ SAO PHẢI BÁO, KHÔNG ĐƯỢC BỎ QUA ────────────────────────────────

    Pydantic mặc định `extra="ignore"`, nên một khoá lạ **biến mất không dấu
    vết**. Đo được ở A/B `ab-v1-20260905T164514Z`, hai ca `e2` và `e6`: mô
    hình gửi toạ độ trong

        {"name": "X", "type": "point3", "at": [0, 0, 0]}

    — `at` là trường của CÂU LỆNH `declare_point`, không phải của
    `memory_declarations[]`. Nó bị bỏ, khai báo còn `initial_value: null`, và
    lỗi cuối cùng mô hình nhận được là

        IR_USE_BEFORE_CONSTRUCTION: 'X' — cần point3, có khai báo nhưng
        chưa có giá trị

    Câu ấy **đúng sự thật và sai chỗ**: mô hình ĐÃ cho toạ độ, chỉ để nhầm ô.
    Nó không có cách nào biết điều đó, nên lượt sửa (nếu có) sẽ đi tìm một
    câu lệnh dựng cho một điểm gốc — thứ không tồn tại.

    ─── VÌ SAO TỪ CHỐI, KHÔNG QUY ĐỔI ─────────────────────────────────────

    Kho có tiền lệ quy đổi (`canonical_geometry_name`,
    `canonical_container_name`) cho các ca **1:1 về tham chiếu**. Ca này khác:
    `declare_point` là một CÂU LỆNH có vị trí trong chương trình và có đường
    xuất xứ riêng, còn `initial_value` là một khai báo. Tự chuyển ô là **chọn
    hộ** giữa hai cách biểu đạt khác nhau — đúng thứ `_nang_declare_point` đã
    học là không được làm. Nên: từ chối, và nói đủ để sửa.

    Khi có CẢ HAI `at` và `initial_value`: vẫn từ chối, và vẫn không chọn hộ —
    lời từ chối nói rõ ô nào là chính tắc và yêu cầu bỏ ô kia.
    """
    return _thong_diep_khoa_la(khoa_la_trong_khai_bao(raw_spec))


#: Mã ổn định của lời từ chối — runner, trace và bộ chấm đọc mã này (SYNTHESIS_MEMORY_DECLARATION_SCHEMA_PROMPT_ALIGNMENT).
MA_KHOA_BI_BO_IM_LANG = "SCHEMA_SILENTLY_DROPPED_KEY"


def _thoat_con_tro(khoa: str) -> str:
    """Thoát một mắt JSON Pointer theo RFC 6901: `~` → `~0`, `/` → `~1`."""
    return khoa.replace("~", "~0").replace("/", "~1")


def khoa_la_trong_khai_bao(raw_spec: Any) -> list[dict]:
    """MỌI khoá mô hình gửi trong `memory_declarations[]` mà `MemoryDeclaration` không có — kèm phán quyết từng khoá.

    Mỗi mục: `pointer` (JSON Pointer RFC 6901) · `key` · `blocking` · `owners` (kind/model có trường tên ấy) ·
    `value_slot` (ô giá trị thô chính tắc) · `has_value` (khai báo đã có giá trị). KHÔNG mang giá trị của khoá.

    ─── CHỈ BÁC KHI CÓ DỮ LIỆU BỊ MẤT ──────────────────────────────────────

    Bản đầu bác MỌI khoá lạ, và nó bác oan: chương trình lịch sử (`gm_03`, `gm_10`, corpus transport) đặt `label`
    trong khai báo — `label` là `Optional[str]`, một chuỗi TRANG TRÍ, bỏ nó không mất gì. Đo được: 3/5 chương trình
    AI sinh trong artifact bị chặn; đo lại 2026-09-15 (bác mọi khoá lạ): 11 test đỏ, gồm replay đóng băng p4/p5.

    Cái hại thật là **toạ độ biến mất**. Nên `blocking` khi:
      · khoá ấy là Ô GIÁ TRỊ THÔ ở model sở hữu nó (`at` là `list[Any]`) — kể cả khi khai báo đã có
        `initial_value`, vì khi ấy có HAI lời khai giá trị cho một vật; hoặc
      · không model nào sở hữu nó, nó MANG giá trị, và khai báo này đang KHÔNG có giá trị nào — tức khoá bịa đã
        nuốt mất dữ kiện.
    Khoá còn lại không bác, nhưng KHÔNG im lặng: `validate_semantic_program` ghi con trỏ vào `ignored_keys`.
    """
    ds = raw_spec.get("memory_declarations") if isinstance(raw_spec, dict) else None
    if not isinstance(ds, list):
        return []
    hop_le = set(MemoryDeclaration.model_fields)
    o_gt = _o_gia_tri_tho(MemoryDeclaration)
    ra: list[dict] = []
    for i, d in enumerate(ds):
        if not isinstance(d, dict):
            continue
        chua_co_gt = d.get(o_gt) is None if o_gt else False
        for k in sorted(set(d) - hop_le):
            chu, la_gt = _chu_so_huu_truong(k)
            ra.append({"pointer": f"/memory_declarations/{i}/{_thoat_con_tro(k)}", "key": k,
                       "blocking": bool(la_gt or (not chu and d.get(k) is not None and chua_co_gt)),
                       "owners": chu, "value_slot": o_gt, "has_value": not chua_co_gt})
    return ra


def _thong_diep_khoa_la(van_de: list[dict]) -> Optional[str]:
    """Lời từ chối NGẮN, máy đọc được: `[MÃ] <con trỏ>: <khoá> …; <việc>. Khoá hợp lệ: <tập khoá>`.

    Không giá trị của khoá, không chương trình, không lược đồ. Tập khoá hợp lệ theo thứ tự `model_fields` — cùng
    nguồn với thẻ văn phạm. Khi có CẢ `at` và `initial_value`: vẫn không chọn hộ, chỉ nói ô nào chính tắc.
    """
    chan = [v for v in van_de if v["blocking"]]
    if not chan:
        return None
    phan = []
    for v in chan:
        k = v["key"]
        chu = (f"`{k}` là trường của {', '.join('`' + c + '`' for c in v['owners'])}" if v["owners"]
               else f"`{k}` không thuộc hợp đồng")
        if v["value_slot"] and v["has_value"]:
            viec = f"khai báo ĐÃ có `{v['value_slot']}`: bỏ `{k}`"
        elif v["value_slot"]:
            viec = f"chuyển giá trị sang `{v['value_slot']}`"
        else:
            viec = f"bỏ `{k}`"
        phan.append(f"{v['pointer']}: {chu}; {viec}")
    return (f"[{MA_KHOA_BI_BO_IM_LANG}] " + "; ".join(phan)
            + ". Khoá hợp lệ: " + ", ".join(MemoryDeclaration.model_fields))


def validate_semantic_program(raw_spec: Any) -> ValidationResult:
    """Thẩm định một đặc tả SemanticProgramSpec."""
    bo_qua: tuple = ()
    if isinstance(raw_spec, dict):
        # TRƯỚC `model_validate`: đây là biên CUỐI CÙNG còn giữ đầu vào thô.
        # Sau nó, khoá lạ đã bị `extra="ignore"` bỏ và không tầng nào biết
        # mô hình từng gửi gì.
        if (lac := _khoa_bi_bo_im_lang(raw_spec)):
            return ValidationResult(
                False, f"Lỗi cú pháp schema SemanticProgramSpec: {lac}")
        bo_qua = tuple({"pointer": v["pointer"], "key": v["key"]}
                       for v in khoa_la_trong_khai_bao(raw_spec) if not v["blocking"])
        try:
            spec = SemanticProgramSpec.model_validate(raw_spec)
        except ValidationError as e:
            return ValidationResult(False, f"Lỗi cú pháp schema SemanticProgramSpec: {e}")
    elif isinstance(raw_spec, SemanticProgramSpec):
        spec = raw_spec
    else:
        return ValidationResult(False, f"Đầu vào phải là dict hoặc SemanticProgramSpec, nhận được: {type(raw_spec)}")

    checker = SemanticTypeChecker(spec)
    kq = checker.check()
    kq.ignored_keys = bo_qua
    return kq
