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
from pydantic import BaseModel, BeforeValidator, Field, Discriminator, Tag, field_validator

from .coercion_stats import (
    LOP_CONDITION_BOOL,
    LOP_CONST_INT,
    LOP_CONTAINER_REF,
    LOP_SPEC_VERSION,
    ghi_coercion,
)

SPEC_VERSION: Literal["1.0"] = "1.0"


def canonical_spec_version(v: Any) -> Any:
    """BIÊN CHUẨN HOÁ `spec_version` — JSON number `1.0` và chuỗi `"1.0"` là hai
    cách viết CÙNG MỘT phiên bản.

    Vì sao tồn tại: trên SEALED `7e5df014…` (OFFICIAL Task 12), **17/40 case**
    chết với đúng một lỗi — LLM phát `"spec_version": 1.0` (float), contract đòi
    `Literal["1.0"]` (str), Pydantic vứt CẢ chương trình trước khi xét bất kỳ
    tầng ngữ nghĩa nào. Đó là fail-closed nhầm tầng: một khác biệt serialization
    che mất năng lực ngữ nghĩa của chương trình.

    Hàm này KHÔNG nới phiên bản. Nó chỉ gộp các cách viết của **1.0**; mọi số
    khác được trả về dạng chuỗi để `Literal` từ chối, và để thông báo lỗi vẫn
    nêu đúng giá trị LLM đã phát (người sửa prompt cần thấy con số đó).

    `bool` phải chặn tường minh: trong Python `True` là subclass của `int`, nên
    không có nhánh này thì `float(True) == 1.0` sẽ biến `true` thành phiên bản
    hợp lệ.
    """
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        if float(v) == 1.0:
            ghi_coercion(LOP_SPEC_VERSION)
            return SPEC_VERSION
        return str(v)
    return v

def canonical_container_name(v: Any) -> Any:
    """BIÊN CHUẨN HOÁ THAM CHIẾU CONTAINER — `{"kind":"var","name":X}` ⇒ `X`.

    Vì sao tồn tại: probe E2E sản phẩm (2026-08-23) cho thấy đề "kiểm tra chuỗi
    ngoặc bằng ngăn xếp" đi hết tới `stage_semantic_program`, dựng đúng nghĩa vụ
    `membership(chuoi_ngoac, witness=is_valid)`, rồi chết với **4 lỗi cùng một
    lớp**: LLM viết `container: {"kind":"var","name":"stack"}` còn schema đòi
    `container: "stack"`. Hai cách viết CÙNG MỘT tham chiếu. Lớp lỗi này cũng có
    trong SEALED `7e5df014…`, đứng ngay sau `spec_version` về số case bị giết.

    RANH GIỚI — chỉ nhận `var`. Mọi biểu thức khác (`index`, `arith`, `length`,
    `map_get`…) vẫn bị từ chối: container là một TÊN, không phải biểu thức cần
    tính. Nới tới mức nhận biểu thức thì interpreter phải đánh giá nó để biết
    đang thao tác trên vùng nhớ nào — một ngữ nghĩa khác hẳn, không thuộc phạm vi
    bản vá này.
    """
    if isinstance(v, dict):
        if v.get("kind") == "var":
            ten = v.get("name")
            if isinstance(ten, str) and ten:
                ghi_coercion(LOP_CONTAINER_REF)
                return ten
        # TỪ CHỐI CÓ DẠY, không để Pydantic nói "Input should be a valid string".
        #
        # Vì sao thông báo phải nằm ở ĐÂY chứ không ở prompt hay thẻ văn phạm:
        # cả hai bề mặt ấy đều có ngân sách byte (`test_prompt_size_guard`,
        # `test_grammar_card`) và cả hai guard nói cùng một câu — luật nào mã
        # hoá được thì để validator giữ. Luật này mã hoá được trọn vẹn, nên viết
        # nó thành văn xuôi ở nơi khác là trả giá hai lần: tốn ngân sách, mà vẫn
        # chỉ là GỢI Ý. Ở đây nó là RÀNG BUỘC, và câu chữ đi thẳng vào telemetry
        # (§5) nơi người sửa thật sự đọc nó.
        raise ValueError(
            f"`container` nhận TÊN một mục trong memory_declarations, không "
            f"nhận biểu thức (nhận kind={v.get('kind')!r}). Cần một tập/bảng "
            f"hằng thì khai nó thành một mục có initial_value rồi gọi bằng tên."
        )
    return v


#: Tên container. Nhận cả tên trần lẫn tham chiếu biến, nội bộ luôn là chuỗi.
ContainerName = Annotated[str, BeforeValidator(canonical_container_name)]


def canonical_const_int(v: Any) -> Any:
    """BIÊN CHUẨN HOÁ HẰNG NGUYÊN — `{"kind":"literal","value":1}` ⇒ `1`.

    Vì sao tồn tại: trên SEALED `7e5df014…`, hai case (`T10-C5-062`,
    `T10-C5-071`) chết với đúng một lỗi — LLM viết
    `for_range.step: {"kind":"literal","value":1}` còn schema đòi `int` trần.
    `start`/`end` là `ValueExpr` nên NHẬN dạng bọc, riêng `step` thì không: mô
    hình viết cả ba cùng một kiểu là hành vi nhất quán, chỉ hợp đồng là không
    nhất quán. Cùng lớp lỗi với `spec_version` và `container` — sai CÁCH VIẾT,
    không sai thuật toán.

    RANH GIỚI: chỉ gỡ `literal` mang số nguyên. `var`/`arith` vẫn bị từ chối —
    bước nhảy phải là HẰNG thì vòng lặp mới có biên tất định; nhận biểu thức là
    đổi ngữ nghĩa của `for_range`, không thuộc phạm vi một phép chuẩn hoá.
    """
    if isinstance(v, dict):
        if v.get("kind") == "literal" and isinstance(v.get("value"), int) and not isinstance(v.get("value"), bool):
            ghi_coercion(LOP_CONST_INT)
            return v["value"]
        raise ValueError(
            f"`step` phải là HẰNG nguyên, không phải biểu thức (nhận "
            f"kind={v.get('kind')!r}). Bước nhảy không hằng thì vòng lặp không "
            f"còn biên tất định."
        )
    return v


#: Bước nhảy vòng lặp. Nhận cả số trần lẫn hằng đã bọc, nội bộ luôn là `int`.
ConstInt = Annotated[int, BeforeValidator(canonical_const_int)]


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
    source_fact_id: Optional[str] = Field(
        None,
        description=(
            "ID mục dữ liệu trong RequestContract mà initial_value lấy từ đó. "
            "BẮT BUỘC khi initial_value mang nghĩa dữ liệu ĐỀ CHO. Ghim ĐÚNG MỤC "
            "NÀO — khớp theo giá trị đơn thuần dễ trùng ngẫu nhiên."
        ),
    )


# ── 2. Biểu thức giá trị đóng (Closed Value Expressions) ────────────────────
class LiteralExpr(BaseModel):
    kind: Literal["literal"] = "literal"
    value: Union[int, str, bool, float, list, dict, None] = Field(..., description="Giá trị nguyên thủy hoặc cấu trúc literal")

class VarRefExpr(BaseModel):
    kind: Literal["var"] = "var"
    name: str = Field(..., description="Tên biến tham chiếu")

class IndexRefExpr(BaseModel):
    kind: Literal["index"] = "index"
    container: ContainerName = Field(..., description="Tên container (array/matrix)")
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
    container: ContainerName = Field(..., description="Tên container cần lấy kích thước")

class PeekExpr(BaseModel):
    kind: Literal["peek"] = "peek"
    container: ContainerName = Field(..., description="Tên stack hoặc queue cần nhìn phần tử đầu")

class MapGetExpr(BaseModel):
    kind: Literal["map_get"] = "map_get"
    container: ContainerName = Field(..., description="Tên map")
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
    container: ContainerName = Field(..., description="Tên container kiểm tra rỗng")

class ContainsCond(BaseModel):
    kind: Literal["contains"] = "contains"
    container: ContainerName = Field(..., description="Tên container/set/map")
    item: ValueExpr = Field(..., description="Phần tử hoặc khóa cần kiểm tra tồn tại")

class IsNullCond(BaseModel):
    kind: Literal["is_null"] = "is_null"
    expr: ValueExpr = Field(..., description="Biểu thức kiểm tra null")

#: Biểu thức GIÁ TRỊ có thể mang sẵn một giá trị đúng/sai. Chỉ những dạng này
#: mới được gấp thành điều kiện — `arith`/`length`/`neighbors` thì không, vì
#: `2+3` dùng làm điều kiện là lỗi kiểu thật, và im lặng bọc nó thành
#: `2+3 == true` sẽ đẩy lỗi xuống sâu hơn với thông báo khó hiểu hơn.
_DANG_MANG_BOOL = ("var", "field", "index", "map_get", "literal")


def canonical_condition(v: Any) -> Any:
    """BIÊN CHUẨN HOÁ ĐIỀU KIỆN — `hop_le` ⇒ `hop_le == true`.

    Vì sao tồn tại: probe E2E sản phẩm (2026-08-23) trên đề *"kiểm tra chuỗi
    ngoặc bằng ngăn xếp"* cho thấy LLM viết `if hop_le and ...` bằng cách đặt
    thẳng `{"kind":"var","name":"hop_le"}` vào vế của `logic`, trong khi union
    điều kiện chỉ nhận `compare/logic/not/is_empty/contains/is_null`. Cả chương
    trình bị vứt vì một khác biệt KÝ PHÁP: `x` và `x == true` là cùng một mệnh
    đề, và mọi ngôn ngữ lập trình mà học sinh từng thấy đều cho viết cách đầu.

    Cùng họ với `canonical_container_name`: gộp hai cách viết của MỘT tham
    chiếu, KHÔNG nới ngữ nghĩa. Điều kiện sau khi gấp vẫn phải qua kiểm kiểu —
    biến không mang kiểu bool thì vẫn bị từ chối, chỉ khác là bị từ chối ở tầng
    NGỮ NGHĨA với thông báo nói đúng bệnh, thay vì chết ở tầng cú pháp.
    """
    if isinstance(v, dict) and v.get("kind") in _DANG_MANG_BOOL:
        ghi_coercion(LOP_CONDITION_BOOL)
        return {
            "kind": "compare",
            "op": "==",
            "left": v,
            "right": {"kind": "literal", "value": True},
        }
    return v


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
    BeforeValidator(canonical_condition),
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
    container: ContainerName = Field(..., description="Tên container (array/matrix)")
    index: ValueExpr = Field(..., description="Chỉ số hoặc chỉ số dòng")
    second_index: Optional[ValueExpr] = Field(None, description="Chỉ số cột nếu là ma trận 2D")
    val: ValueExpr = Field(..., description="Giá trị ghi vào")

class MapSetStmt(BaseModel):
    kind: Literal["map_set"] = "map_set"
    container: ContainerName = Field(..., description="Tên map")
    key: ValueExpr = Field(..., description="Khóa cần gán")
    val: ValueExpr = Field(..., description="Giá trị gán")

class SwapStmt(BaseModel):
    kind: Literal["swap"] = "swap"
    container: ContainerName = Field(..., description="Tên container hoán đổi (array)")
    idx_a: ValueExpr = Field(..., description="Chỉ số A")
    idx_b: ValueExpr = Field(..., description="Chỉ số B")

class PushStmt(BaseModel):
    kind: Literal["push"] = "push"
    container: ContainerName = Field(..., description="Tên stack hoặc array")
    val: ValueExpr = Field(..., description="Phần tử đẩy vào")

class PopStmt(BaseModel):
    kind: Literal["pop"] = "pop"
    container: ContainerName = Field(..., description="Tên stack")
    dest_var: Optional[str] = Field(None, description="Biến nhận phần tử lấy ra (nếu có)")

class EnqueueStmt(BaseModel):
    kind: Literal["enqueue"] = "enqueue"
    container: ContainerName = Field(..., description="Tên queue")
    val: ValueExpr = Field(..., description="Phần tử thêm vào hàng đợi")

class DequeueStmt(BaseModel):
    kind: Literal["dequeue"] = "dequeue"
    container: ContainerName = Field(..., description="Tên queue")
    dest_var: Optional[str] = Field(None, description="Biến nhận phần tử lấy ra")

class SetInsertStmt(BaseModel):
    kind: Literal["set_insert"] = "set_insert"
    container: ContainerName = Field(..., description="Tên set")
    val: ValueExpr = Field(..., description="Phần tử thêm vào tập hợp")

class SetRemoveStmt(BaseModel):
    kind: Literal["set_remove"] = "set_remove"
    container: ContainerName = Field(..., description="Tên set")
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
    step: ConstInt = Field(1, description="Bước nhảy (mặc định 1)")
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
        "tree_element", "bit_register", "bar_chart", "graph_view",
        # `map_view` thêm 2026-08-23 — CÙNG LÝ DO với `graph_view`: `map` là một
        # `MemoryType` đã được admit mà hợp đồng thị giác không có cách nào biểu
        # diễn. Cổng bề mặt học sinh phơi ra điều đó trên fixture #18 ("Bảng đếm
        # tần suất ký tự"): chương trình dựng `freq` suốt lượt chạy, còn màn hình
        # không bao giờ có bảng nào — bài mang tên "bảng tần suất" mà không hiện
        # bảng. Mở vì một LỚP TRẠNG THÁI đã admit là hợp lệ; nguồn phát hiện là
        # DEV, không phải một ca SEALED (`test_primitive_set_frozen.py`).
        "map_view",
    ] = Field(..., description="Visual primitive tương ứng trong DSL")
    label: str = Field(..., description="Nhãn hiển thị trên canvas")

    # ── Tham chiếu TRẠNG THÁI cho `graph_view` (2026-08-21) ──────────────────
    #
    # VÌ SAO CÓ HAI TRƯỜNG NÀY: `graph_view` phải tô được đỉnh nào đã thăm và
    # đỉnh nào đang xét, nếu không mô phỏng BFS chỉ còn là một hàng đợi đổi số.
    # Nhưng renderer TUYỆT ĐỐI không được tự suy ra điều đó bằng cách chạy lại
    # BFS/DFS — làm thế là dựng một engine thứ hai trong tầng trình bày, đúng
    # thứ R0 cấm.
    #
    # Cách giữ cả hai: chương trình KHAI BÁO biến nào mang trạng thái ấy, và
    # adapter đọc thẳng từ `memory_snapshot`. Cùng khuôn với
    # `VisualPointerBinding.var_ref` — một liên kết khai báo, không phải suy diễn.
    visited_ref: Optional[str] = Field(
        None,
        description=(
            "Tên biến (set/array) chứa các đỉnh ĐÃ THĂM. Chỉ có nghĩa với "
            "`graph_view`. Không khai thì đồ thị vẽ không tô trạng thái."
        ),
    )
    current_ref: Optional[str] = Field(
        None,
        description=(
            "Tên biến chứa đỉnh ĐANG XÉT. Chỉ có nghĩa với `graph_view`."
        ),
    )

class VisualPointerBinding(BaseModel):
    pointer_id: str = Field(..., description="ID của con trỏ hiển thị")
    var_ref: str = Field(..., description="Tên biến trong Semantic Memory cần theo dõi")
    target_container: ContainerName = Field(..., description="Container mà con trỏ neo vào")
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

    # `mode="before"` = chạy TRƯỚC khi `Literal` kiểm. Nhờ vậy mọi tầng phía dưới
    # (schema, interpreter, checker) chỉ nhìn thấy biểu diễn canonical dạng chuỗi
    # — biên nằm đúng một chỗ, không rải `isinstance` khắp pipeline.
    _canonical_spec_version = field_validator("spec_version", mode="before")(
        canonical_spec_version
    )
    title: str = Field(..., min_length=3, max_length=150, description="Tiêu đề mô phỏng thuật toán")
    description: Optional[str] = Field(None, max_length=1000, description="Mô tả ngắn gọn")
    memory_declarations: list[MemoryDeclaration] = Field(..., description="Khai báo các vùng nhớ và biến")
    statements: list[SemanticStatement] = Field(..., description="Tập các câu lệnh thuật toán")
    visual_bindings: VisualBindings = Field(default_factory=VisualBindings, description="Khai báo liên kết hiển thị trực quan")
    pedagogical_intent: Optional[str] = Field(None, max_length=500, description="Ý đồ sư phạm / tóm tắt cấp cao (Tier 2 narration)")


def generate_json_schema() -> dict[str, Any]:
    """Sinh JSON Schema chuẩn từ Pydantic Contract."""
    return SemanticProgramSpec.model_json_schema()
