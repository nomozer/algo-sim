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
    "node_ref", "null",
    # ── MIỀN HÌNH HỌC KHÔNG GIAN (2026-08-24, Bước 3 của MIGRATION_PLAN) ────
    # Sáu kiểu, đóng như phần trên. Chúng chở ĐỐI TƯỢNG, không chở TOẠ ĐỘ KẾT
    # QUẢ: `point3` khai được `A(0,0,0)` mà đề cho, nhưng giao điểm của hai
    # đường thì phải do `construct_point` gọi kernel tính ra. Đó là ranh giới
    # R0 ở miền này — LLM khai dữ kiện, engine tính hệ quả.
    "point3", "vector3", "line3", "plane3", "polygon3", "solid",
]


def tu_choi_ten_nghia_vu_lam_kieu(v: Any) -> Any:
    """Chặn NHẦM LẪN HAI TAXONOMY, và chặn bằng một thông điệp DẠY LẠI.

    ⚠️ CỐ Ý KHÔNG mang tiền tố `canonical_`. Bốn hàm `canonical_*` ở file này
    đều là **biên CHUẨN HOÁ** — chúng nhận một cách viết lệch rồi trả về dạng
    chuẩn, và mỗi cái có một lớp trong `coercion_stats.LOP_HOP_LE` để đếm xem
    model lệch bao nhiêu. Hàm này KHÔNG chuẩn hoá gì: nó từ chối. Đặt tên
    `canonical_memory_type` (bản nháp đầu đã đặt thế) làm `test_coercion_stats`
    đỏ ngay, và đỏ ĐÚNG — nó buộc phải khai một lớp coercion mà không lượt nào
    đếm được, vì không có phép ép kiểu nào xảy ra.

    ─── ĐO ĐƯỢC Ở PHASE 5 (2026-08-24), 3/10 bài ───────────────────────────

    Mô hình khai `{"name": "V", "type": "volume"}` — lấy tên một **NGHĨA VỤ**
    làm **KIỂU BỘ NHỚ**. Cũng thế với `angle`, `perpendicular`, `distance`.

    Nhìn từ phía nó, nhầm lẫn ấy HỢP LÝ: thẻ văn phạm liệt kê các kiểu, prompt
    liệt kê các nghĩa vụ, và cả hai đều là "danh sách tên hợp lệ". Không chỗ
    nào nói hai danh sách ấy sống ở hai không gian tên khác nhau.

    ─── VÌ SAO TỪ CHỐI CHỨ KHÔNG ĐỔI TÊN NGHĨA VỤ ──────────────────────────

    Đổi `volume` → `compute_volume` chỉ **dời đích va chạm**: mô hình vẫn có
    thể viết `type: "compute_volume"`, và ta mất luôn tính tương thích với
    `oracle_result` của tập DEV vốn khoá theo đúng tên nghĩa vụ. Từ chối tại
    biên thì đóng hẳn, và không dataset nào phải đổi.

    ─── VÌ SAO KHÔNG ÉP KIỂU (coerce) ──────────────────────────────────────

    `volume` → `float` nghe tiện, nhưng đó là ĐOÁN: `perpendicular` phải thành
    `bool`, `distance` thành `float`, `angle` thì tuỳ. Mỗi lần đoán đúng là một
    lần che mất việc mô hình đang hiểu sai cấu trúc. Vòng sửa ≤3 lượt đọc được
    thông điệp này và tự sửa — đó là đường phục hồi, và nó lộ thiên.
    """
    if isinstance(v, str):
        from .obligations import OBLIGATION_KINDS

        if v in OBLIGATION_KINDS:
            raise ValueError(
                f"'{v}' là tên một NGHĨA VỤ, không phải một KIỂU BỘ NHỚ. Hai "
                f"danh sách này tách biệt. Nghĩa vụ được khai ở lượt đọc đề, "
                f"không khai trong `memory_declarations`. Ở đây hãy dùng kiểu "
                f"của ĐỐI TƯỢNG: một số đo là `float`, một quan hệ đúng/sai là "
                f"`bool`, một điểm là `point3`, một khối là `solid`."
            )
    return v


#: Kiểu bộ nhớ, kèm bộ chặn nhầm-taxonomy ở ngay biên.
CheckedMemoryType = Annotated[
    MemoryType, BeforeValidator(tu_choi_ten_nghia_vu_lam_kieu)
]


class MemoryDeclaration(BaseModel):
    name: str = Field(..., description="Tên định danh biến/container trong bộ nhớ")
    type: CheckedMemoryType = Field(..., description="Kiểu dữ liệu ngữ nghĩa")
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
    model_assumption: Optional[str] = Field(
        None,
        description=(
            "LÝ DO chọn giá trị này, khi nó là GIẢ THIẾT MÔ HÌNH HOÁ chứ không "
            "phải dữ liệu đề cho — điển hình là toạ độ của một đỉnh khi đặt hệ "
            "trục. Chỉ dùng cho `point3`/`vector3`, và KHÔNG BAO GIỜ cho biến "
            "mang câu trả lời."
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

# ── Biểu thức HÌNH HỌC (Bước 3) ────────────────────────────────────────────
#
# LUẬT CHUNG CỦA CẢ NHÓM, và là chỗ ranh giới R0 dễ vỡ nhất ở miền này:
# mỗi biểu thức chỉ nhận **TÊN đối tượng**, không nhận toạ độ kết quả. LLM được
# nói *"giao tuyến của (SAB) và (SCD)"*; nó KHÔNG được nói *"giao tuyến là MN"*.
# Toạ độ do `geometry/kernel.py` tính, và `geometry/` không import `app.ai`.
class IntersectLinePlaneExpr(BaseModel):
    kind: Literal["intersect_line_plane"] = "intersect_line_plane"
    line: str = Field(..., description="tên đường thẳng")
    plane: str = Field(..., description="tên mặt phẳng")

class IntersectPlanePlaneExpr(BaseModel):
    kind: Literal["intersect_plane_plane"] = "intersect_plane_plane"
    plane_a: str = Field(..., description="tên mặt phẳng 1")
    plane_b: str = Field(..., description="tên mặt phẳng 2")

class MidpointExpr(BaseModel):
    kind: Literal["midpoint"] = "midpoint"
    a: str = Field(..., description="tên điểm đầu")
    b: str = Field(..., description="tên điểm cuối")

class ProjectOntoExpr(BaseModel):
    kind: Literal["project_onto"] = "project_onto"
    point: str = Field(..., description="tên điểm")
    target: str = Field(..., description="tên mặt phẳng/đường chiếu lên")

class MeasureExpr(BaseModel):
    """ĐO một đại lượng — kernel tính, IR chỉ nói *đo cái gì*.

    ─── VÌ SAO THÊM: audit Wave 2 lộ ra một lỗ mà Phase 5 chưa kịp nhìn thấy ──

    Ba nghĩa vụ `distance` · `angle` · `volume` đã nằm trong taxonomy đóng băng
    và có đủ checker. Nhưng IR **không có phép đo nào**, nên chương trình không
    có cách nào đưa một CON SỐ vào witness — và `cham_oracle` đọc đúng chỗ ấy.
    Ba nghĩa vụ đó phủ **4/10 bài DEV**. Chúng trượt schema trước nên lỗ này bị
    che; sửa xong bốn nguyên nhân kia thì chúng vẫn không chấm được.

    Đây KHÔNG phải "thêm primitive vì thiếu": nó là điều kiện để 3/8 nghĩa vụ
    đã có checker thôi làm mã chết.

    ─── R0 GIỮ NGUYÊN ──────────────────────────────────────────────────────

    Trường của nó toàn là **TÊN**. Không có chỗ nào điền được một con số. LLM
    nói *"đo khoảng cách từ S tới (ABCD)"*; giá trị do `geometry/measure.py`
    tính bằng số hữu tỉ chính xác.

    ─── VÌ SAO `angle_cos_sq` CHỨ KHÔNG PHẢI `angle` ───────────────────────

    Góc hình học phần lớn vô tỉ, `cos²` của nó hữu tỉ. Trả về độ là ép một phép
    làm tròn vào giữa chuỗi tất định, và mọi phép so BẰNG phía sau mất nghĩa.
    Tên trường nói thẳng đơn vị để không ai đọc nhầm.
    """
    kind: Literal["measure"] = "measure"
    quantity: Literal["distance", "angle_cos_sq", "volume"] = Field(
        ..., description="đại lượng cần đo"
    )
    of: str = Field(..., description="tên đối tượng thứ nhất (hoặc khối)")
    wrt: Optional[str] = Field(
        None, description="tên đối tượng thứ hai; `volume` không cần"
    )

class DivideSegmentExpr(BaseModel):
    """Điểm chia đoạn theo tỉ lệ — `t=0` là `a`, `t=1` là `b`.

    Có mặt vì dạng đề *"M thuộc AB sao cho AM = 2MB"* rất phổ biến, và vì nó là
    **miền hợp lệ của thao tác kéo** ở Bước 6: kéo M nghĩa là đổi `t`, không
    phải đổi toạ độ tự do.
    """
    kind: Literal["divide_segment"] = "divide_segment"
    a: str = Field(..., description="tên điểm đầu")
    b: str = Field(..., description="tên điểm cuối")
    ratio: str = Field(..., description="phân số, vd 2/3")


ValueExpr = Annotated[
    Union[
        Annotated[LiteralExpr, Tag("literal")],
        Annotated[IntersectLinePlaneExpr, Tag("intersect_line_plane")],
        Annotated[IntersectPlanePlaneExpr, Tag("intersect_plane_plane")],
        Annotated[MidpointExpr, Tag("midpoint")],
        Annotated[ProjectOntoExpr, Tag("project_onto")],
        Annotated[DivideSegmentExpr, Tag("divide_segment")],
        Annotated[MeasureExpr, Tag("measure")],
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

# ── Câu lệnh DỰNG HÌNH (Bước 3) ────────────────────────────────────────────
#
# Mỗi câu lệnh ở đây = **một bước trong timeline** = một khung hình. Đó là lý do
# chúng là *statement* chứ không phải *expression*: biểu thức tính ra giá trị
# nhưng không để lại dấu vết, còn học sinh cần thấy **thứ tự dựng**.
class ConstructPointStmt(BaseModel):
    kind: Literal["construct_point"] = "construct_point"
    target_var: str = Field(..., description="tên điểm dựng ra")
    expr: ValueExpr = Field(..., description="biểu thức hình học")
    label: Optional[str] = Field(None, description="nhãn, vd M")

class ConstructLineStmt(BaseModel):
    kind: Literal["construct_line"] = "construct_line"
    target_var: str = Field(..., description="tên đường dựng ra")
    through_a: str = Field(..., description="tên điểm 1")
    through_b: str = Field(..., description="tên điểm 2")
    label: Optional[str] = None

class ConstructPlaneStmt(BaseModel):
    """Dựng mặt phẳng QUA BA ĐIỂM ĐÃ CÓ — bằng TÊN, không bằng toạ độ.

    ─── VÌ SAO THÊM, ĐO ĐƯỢC Ở PHASE 5 ────────────────────────────────────

    Mô hình bịa `kind: "construct_plane"` ở 2/10 bài. Không phải nó sáng tác:
    một bài hình học bất kỳ đều cần mặt `(SBC)`, và IR **không có từ nào** để
    nói câu đó.

    ─── VÀ VÌ SAO ĐÂY LÀ BỊT LỖ R0, KHÔNG PHẢI THÊM TIỆN NGHI ─────────────

    Trước câu lệnh này, cách duy nhất để có `(SBC)` là khai một
    `memory_declaration` kiểu `plane3` với `initial_value = {"through": [[…],
    […], […]]}` — tức **chép lại toạ độ của S, B, C lần thứ hai**. Hai bản toạ
    độ thì sẽ lệch, lệch câm, và bản thứ hai do LLM viết chứ không do kernel
    tính. Dựng theo tên thì chỉ còn một nguồn.
    """
    kind: Literal["construct_plane"] = "construct_plane"
    target_var: str = Field(..., description="tên mặt phẳng dựng ra")
    through: list[str] = Field(
        ..., min_length=3, max_length=3, description="tên ba điểm không thẳng hàng"
    )
    label: Optional[str] = Field(None, description="nhãn, vd (SBC)")

class ConstructSolidStmt(BaseModel):
    """Dựng khối từ ĐỈNH ĐÃ ĐẶT TÊN + bảng mặt.

    Cùng lý do với `construct_plane`, và thêm một điều: `faces` là **cấu trúc
    tổ hợp** đọc thẳng từ đề (*"hình chóp S.ABCD"* ⇒ một đáy bốn đỉnh, bốn mặt
    bên), KHÔNG phải dữ liệu hình học. LLM sở hữu quan hệ kề; kernel sở hữu
    toạ độ. Ranh giới R0 rơi đúng vào giữa hai thứ đó.

    Chỉ số trong `faces` trỏ vào `vertices` theo VỊ TRÍ, giống hệt cách
    `Polyhedron` của kernel biểu diễn — không đẻ ra một quy ước thứ hai.
    """
    kind: Literal["construct_solid"] = "construct_solid"
    target_var: str = Field(..., description="tên khối dựng ra")
    vertices: list[str] = Field(
        ..., min_length=4, description="tên các đỉnh, theo thứ tự"
    )
    faces: list[list[int]] = Field(
        ..., min_length=4, description="mỗi mặt là danh sách chỉ số đỉnh"
    )
    label: Optional[str] = Field(None, description="nhãn, vd S.ABCD")

class ConstructSectionStmt(BaseModel):
    """Dựng thiết diện — engine đi theo MẶT và sinh ra NHIỀU bước con.

    Một câu lệnh cho ra cả dãy cạnh, vì thứ tự cạnh do kernel quyết chứ không do
    LLM quyết. LLM chỉ nói *"cắt khối này bằng mặt phẳng kia"*.
    """
    kind: Literal["construct_section"] = "construct_section"
    target_var: str = Field(..., description="tên thiết diện")
    solid: str = Field(..., description="tên khối")
    plane: str = Field(..., description="tên mp cắt")
    label: Optional[str] = None


SemanticStatement = Annotated[
    Union[
        Annotated[AssignStmt, Tag("assign")],
        Annotated[ConstructPointStmt, Tag("construct_point")],
        Annotated[ConstructLineStmt, Tag("construct_line")],
        Annotated[ConstructPlaneStmt, Tag("construct_plane")],
        Annotated[ConstructSolidStmt, Tag("construct_solid")],
        Annotated[ConstructSectionStmt, Tag("construct_section")],
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
