# -*- coding: utf-8 -*-
"""SEMANTIC_PROGRAM_CONTRACT_V1: Hợp đồng biểu diễn chương trình ngữ nghĩa đóng.

Mục tiêu:
- Tách biệt 100% logic thuật toán (Semantic Core) khỏi logic trình bày (Visual Trace Adapter).
- Ngữ pháp biểu thức (ValueExpr, ConditionExpr) và câu lệnh (SemanticStatement) đóng hoàn toàn.
- Hệ thống kiểu tĩnh kiểm tra nghiêm ngặt (Static Type System), 0 magic functions.
"""
from __future__ import annotations
import json
from typing import Annotated, Any, Literal, Optional, Union
from pydantic import BaseModel, Field, Discriminator, Tag

SPEC_VERSION: Literal["1.0"] = "1.0"

# ── 1. Kiểu dữ liệu bộ nhớ (Memory Types) ──────────────────────────────────
ScalarType = Literal["int", "str", "bool", "float"]
ContainerType = Literal[
    "array", "stack", "queue", "matrix", "map", "set", "tree_node", "graph"
]
MemoryType = Literal[
    "int", "str", "bool", "float",
    "array", "stack", "queue", "matrix", "map", "set", "tree_node", "graph",
    "node_ref", "null"
]

class MemoryDeclaration(BaseModel):
    name: str = Field(..., description="Tên định danh biến/container trong bộ nhớ")
    type: MemoryType = Field(..., description="Kiểu dữ liệu ngữ nghĩa")
    initial_value: Any = Field(None, description="Giá trị khởi tạo ban đầu")
    element_type: Optional[MemoryType] = Field(None, description="Kiểu phần tử nếu là array/stack/queue/set")
    key_type: Optional[ScalarType] = Field(None, description="Kiểu khóa nếu là map")
    val_type: Optional[MemoryType] = Field(None, description="Kiểu giá trị nếu là map")


# ── 2. Biểu thức giá trị đóng (Closed Value Expressions) ────────────────────
class LiteralExpr(BaseModel):
    kind: Literal["literal"] = "literal"
    value: Union[int, str, bool, float, None] = Field(..., description="Giá trị nguyên thủy")

class VarRefExpr(BaseModel):
    kind: Literal["var"] = "var"
    name: str = Field(..., description="Tên biến tham chiếu")

class IndexRefExpr(BaseModel):
    kind: Literal["index"] = "index"
    container: str = Field(..., description="Tên container (array/matrix)")
    index: ValueExpr = Field(..., description="Chỉ số hoặc chỉ số dòng")
    second_index: Optional[ValueExpr] = Field(None, description="Chỉ số cột nếu là ma trận 2D")

class FieldRefExpr(BaseModel):
    kind: Literal["field"] = "field"
    target: ValueExpr = Field(..., description="Biểu thức trả về node_ref hoặc record")
    field: Literal["left", "right", "val", "data"] = Field(..., description="Tên trường truy xuất")

class BinaryArithExpr(BaseModel):
    kind: Literal["arith"] = "arith"
    op: Literal["+", "-", "*", "//", "%"] = Field(..., description="Toán tử số học")
    left: ValueExpr = Field(..., description="Vế trái")
    right: ValueExpr = Field(..., description="Vế phải")

class UnaryArithExpr(BaseModel):
    kind: Literal["unary"] = "unary"
    op: Literal["-"] = Field(..., description="Toán tử đảo dấu")
    expr: ValueExpr = Field(..., description="Biểu thức con")

class LengthExpr(BaseModel):
    kind: Literal["length"] = "length"
    container: str = Field(..., description="Tên container cần lấy kích thước")

class PeekExpr(BaseModel):
    kind: Literal["peek"] = "peek"
    container: str = Field(..., description="Tên stack hoặc queue cần nhìn phần tử đầu")

class MapGetExpr(BaseModel):
    kind: Literal["map_get"] = "map_get"
    container: str = Field(..., description="Tên map")
    key: ValueExpr = Field(..., description="Khóa cần tra cứu")
    default: Optional[ValueExpr] = Field(None, description="Giá trị mặc định nếu không tìm thấy khóa")

class NeighborsExpr(BaseModel):
    kind: Literal["neighbors"] = "neighbors"
    graph: str = Field(..., description="Tên graph")
    node: ValueExpr = Field(..., description="Đỉnh cần lấy danh sách kề")

ValueExpr = Annotated[
    Union[
        Annotated[LiteralExpr, Tag("literal")],
        Annotated[VarRefExpr, Tag("var")],
        Annotated[IndexRefExpr, Tag("index")],
        Annotated[FieldRefExpr, Tag("field")],
        Annotated[BinaryArithExpr, Tag("arith")],
        Annotated[UnaryArithExpr, Tag("unary")],
        Annotated[LengthExpr, Tag("length")],
        Annotated[PeekExpr, Tag("peek")],
        Annotated[MapGetExpr, Tag("map_get")],
        Annotated[NeighborsExpr, Tag("neighbors")],
    ],
    Discriminator("kind"),
]

# Rebuild models for recursive references
IndexRefExpr.model_rebuild()
FieldRefExpr.model_rebuild()
BinaryArithExpr.model_rebuild()
UnaryArithExpr.model_rebuild()
MapGetExpr.model_rebuild()
NeighborsExpr.model_rebuild()


# ── 3. Biểu thức điều kiện đóng (Closed Condition Expressions) ──────────────
class CompareCond(BaseModel):
    kind: Literal["compare"] = "compare"
    op: Literal["==", "!=", "<", "<=", ">", ">="] = Field(..., description="Toán tử so sánh")
    left: ValueExpr = Field(..., description="Vế trái")
    right: ValueExpr = Field(..., description="Vế phải")

class LogicCond(BaseModel):
    kind: Literal["logic"] = "logic"
    op: Literal["and", "or"] = Field(..., description="Toán tử logic")
    left: ConditionExpr = Field(..., description="Điều kiện trái")
    right: ConditionExpr = Field(..., description="Điều kiện phải")

class NotCond(BaseModel):
    kind: Literal["not"] = "not"
    expr: ConditionExpr = Field(..., description="Điều kiện phủ định")

class IsEmptyCond(BaseModel):
    kind: Literal["is_empty"] = "is_empty"
    container: str = Field(..., description="Tên container kiểm tra rỗng")

class ContainsCond(BaseModel):
    kind: Literal["contains"] = "contains"
    container: str = Field(..., description="Tên container/set/map")
    item: ValueExpr = Field(..., description="Phần tử hoặc khóa cần kiểm tra tồn tại")

class IsNullCond(BaseModel):
    kind: Literal["is_null"] = "is_null"
    expr: ValueExpr = Field(..., description="Biểu thức kiểm tra null")

ConditionExpr = Annotated[
    Union[
        Annotated[CompareCond, Tag("compare")],
        Annotated[LogicCond, Tag("logic")],
        Annotated[NotCond, Tag("not")],
        Annotated[IsEmptyCond, Tag("is_empty")],
        Annotated[ContainsCond, Tag("contains")],
        Annotated[IsNullCond, Tag("is_null")],
    ],
    Discriminator("kind"),
]

LogicCond.model_rebuild()
NotCond.model_rebuild()


# ── 4. Câu lệnh thuần ngữ nghĩa (Closed Semantic Statements) ───────────────
class AssignStmt(BaseModel):
    kind: Literal["assign"] = "assign"
    target_var: str = Field(..., description="Tên biến nhận kết quả")
    expr: ValueExpr = Field(..., description="Biểu thức giá trị gán vào")

class WriteIndexStmt(BaseModel):
    kind: Literal["write_index"] = "write_index"
    container: str = Field(..., description="Tên container (array/matrix)")
    index: ValueExpr = Field(..., description="Chỉ số hoặc chỉ số dòng")
    second_index: Optional[ValueExpr] = Field(None, description="Chỉ số cột nếu là ma trận 2D")
    val: ValueExpr = Field(..., description="Giá trị ghi vào")

class MapSetStmt(BaseModel):
    kind: Literal["map_set"] = "map_set"
    container: str = Field(..., description="Tên map")
    key: ValueExpr = Field(..., description="Khóa cần gán")
    val: ValueExpr = Field(..., description="Giá trị gán")

class SwapStmt(BaseModel):
    kind: Literal["swap"] = "swap"
    container: str = Field(..., description="Tên container hoán đổi (array)")
    idx_a: ValueExpr = Field(..., description="Chỉ số A")
    idx_b: ValueExpr = Field(..., description="Chỉ số B")

class PushStmt(BaseModel):
    kind: Literal["push"] = "push"
    container: str = Field(..., description="Tên stack hoặc array")
    val: ValueExpr = Field(..., description="Phần tử đẩy vào")

class PopStmt(BaseModel):
    kind: Literal["pop"] = "pop"
    container: str = Field(..., description="Tên stack")
    dest_var: Optional[str] = Field(None, description="Biến nhận phần tử lấy ra (nếu có)")

class EnqueueStmt(BaseModel):
    kind: Literal["enqueue"] = "enqueue"
    container: str = Field(..., description="Tên queue")
    val: ValueExpr = Field(..., description="Phần tử thêm vào hàng đợi")

class DequeueStmt(BaseModel):
    kind: Literal["dequeue"] = "dequeue"
    container: str = Field(..., description="Tên queue")
    dest_var: Optional[str] = Field(None, description="Biến nhận phần tử lấy ra")

class SetInsertStmt(BaseModel):
    kind: Literal["set_insert"] = "set_insert"
    container: str = Field(..., description="Tên set")
    val: ValueExpr = Field(..., description="Phần tử thêm vào tập hợp")

class SetRemoveStmt(BaseModel):
    kind: Literal["set_remove"] = "set_remove"
    container: str = Field(..., description="Tên set")
    val: ValueExpr = Field(..., description="Phần tử xóa khỏi tập hợp")

class IfStmt(BaseModel):
    kind: Literal["if"] = "if"
    condition: ConditionExpr = Field(..., description="Điều kiện rẽ nhánh")
    then_body: list[SemanticStatement] = Field(..., description="Khối lệnh khi điều kiện đúng")
    else_body: list[SemanticStatement] = Field(default_factory=list, description="Khối lệnh khi điều kiện sai")

class WhileStmt(BaseModel):
    kind: Literal["while"] = "while"
    condition: ConditionExpr = Field(..., description="Điều kiện lặp")
    max_iterations: int = Field(100, ge=1, le=200, description="Giới hạn số vòng lặp tối đa chống lặp vô hạn")
    body: list[SemanticStatement] = Field(..., description="Thân vòng lặp")

class ForRangeStmt(BaseModel):
    kind: Literal["for_range"] = "for_range"
    loop_var: str = Field(..., description="Biến chạy vòng lặp")
    start: ValueExpr = Field(..., description="Giá trị bắt đầu")
    end: ValueExpr = Field(..., description="Giá trị kết thúc (exclusive)")
    step: int = Field(1, description="Bước nhảy (mặc định 1)")
    body: list[SemanticStatement] = Field(..., description="Thân vòng lặp")

class ForEachStmt(BaseModel):
    kind: Literal["for_each"] = "for_each"
    item_var: str = Field(..., description="Biến nhận từng phần tử")
    container_or_expr: Union[str, ValueExpr] = Field(..., description="Tên container hoặc biểu thức danh sách")
    body: list[SemanticStatement] = Field(..., description="Thân vòng lặp")

class BreakStmt(BaseModel):
    kind: Literal["break"] = "break"

class ReturnStmt(BaseModel):
    kind: Literal["return"] = "return"
    val: Optional[ValueExpr] = Field(None, description="Giá trị trả về (nếu có)")

SemanticStatement = Annotated[
    Union[
        Annotated[AssignStmt, Tag("assign")],
        Annotated[WriteIndexStmt, Tag("write_index")],
        Annotated[MapSetStmt, Tag("map_set")],
        Annotated[SwapStmt, Tag("swap")],
        Annotated[PushStmt, Tag("push")],
        Annotated[PopStmt, Tag("pop")],
        Annotated[EnqueueStmt, Tag("enqueue")],
        Annotated[DequeueStmt, Tag("dequeue")],
        Annotated[SetInsertStmt, Tag("set_insert")],
        Annotated[SetRemoveStmt, Tag("set_remove")],
        Annotated[IfStmt, Tag("if")],
        Annotated[WhileStmt, Tag("while")],
        Annotated[ForRangeStmt, Tag("for_range")],
        Annotated[ForEachStmt, Tag("for_each")],
        Annotated[BreakStmt, Tag("break")],
        Annotated[ReturnStmt, Tag("return")],
    ],
    Discriminator("kind"),
]

IfStmt.model_rebuild()
WhileStmt.model_rebuild()
ForRangeStmt.model_rebuild()
ForEachStmt.model_rebuild()


# ── 5. Tiếp hợp hiển thị trực quan (Visual Bindings 0..N) ───────────────────
class VisualContainerBinding(BaseModel):
    semantic_id: str = Field(..., description="Tên container trong Semantic Memory")
    primitive: Literal[
        "array_strip", "stack_view", "queue_view", "table_grid",
        "tree_element", "bit_register", "bar_chart"
    ] = Field(..., description="Visual primitive tương ứng trong DSL")
    label: str = Field(..., description="Nhãn hiển thị trên canvas")

class VisualPointerBinding(BaseModel):
    pointer_id: str = Field(..., description="ID của con trỏ hiển thị")
    var_ref: str = Field(..., description="Tên biến trong Semantic Memory cần theo dõi")
    target_container: str = Field(..., description="Container mà con trỏ neo vào")
    label: str = Field(..., description="Ký tự nhãn con trỏ (vd: 'i', 'left')")

class VisualValueBoxBinding(BaseModel):
    box_id: str = Field(..., description="ID của hộp giá trị")
    var_ref: str = Field(..., description="Tên biến cần hiển thị")
    label: str = Field(..., description="Nhãn của hộp giá trị (vd: 'Ký tự hiện tại', 'Kết quả')")

class VisualBindings(BaseModel):
    containers: list[VisualContainerBinding] = Field(default_factory=list, description="Danh sách binding container")
    pointers: list[VisualPointerBinding] = Field(default_factory=list, description="Danh sách binding con trỏ")
    value_boxes: list[VisualValueBoxBinding] = Field(default_factory=list, description="Danh sách binding hộp giá trị")


# ── 6. Toàn bộ đặc tả SemanticProgramSpec ──────────────────────────────────
class SemanticProgramSpec(BaseModel):
    spec_version: Literal["1.0"] = SPEC_VERSION
    title: str = Field(..., min_length=3, max_length=150, description="Tiêu đề mô phỏng thuật toán")
    description: Optional[str] = Field(None, max_length=1000, description="Mô tả ngắn gọn")
    memory_declarations: list[MemoryDeclaration] = Field(..., description="Khai báo các vùng nhớ và biến")
    statements: list[SemanticStatement] = Field(..., description="Tập các câu lệnh thuật toán")
    visual_bindings: VisualBindings = Field(default_factory=VisualBindings, description="Khai báo liên kết hiển thị trực quan")
    pedagogical_intent: Optional[str] = Field(None, max_length=500, description="Ý đồ sư phạm / tóm tắt cấp cao (Tier 2 narration)")


def generate_json_schema() -> dict[str, Any]:
    """Sinh JSON Schema chuẩn từ Pydantic Contract."""
    return SemanticProgramSpec.model_json_schema()
