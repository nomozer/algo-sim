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
from pydantic import (
    BaseModel, BeforeValidator, Field, Discriminator, Tag, field_validator,
    model_validator,
)

from .coercion_stats import (
    LOP_CONDITION_BOOL,
    LOP_CONST_INT,
    LOP_CONTAINER_REF,
    LOP_FACE_SYMBOL,
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
    # `section` tách khỏi `polygon3` (2026-08-30). Trước đó thiết diện phải
    # khai nhờ kiểu `polygon3`, trong khi `ir_static_check._KIEU_DUNG` đã coi
    # `construct_section` sinh ra kiểu `section` — hai bảng nói hai điều khác
    # nhau về cùng một vật. Một thiết diện KHÔNG phải một đa giác bất kỳ: nó
    # mang khối cha, mặt phẳng cắt và dãy cạnh sinh ra nó, và nghĩa vụ
    # `section_matches` chỉ kiểm được vì biết vật ấy là thiết diện.
    "section",
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

def tu_choi_phep_chia_khong_nguyen(v: Any) -> Any:
    """`/` KHÔNG được ánh xạ sang `//`, và đây là chỗ nói vì sao.

    Cám dỗ: thêm alias `"/" → "//"` cho mô hình khỏi mất một lượt. Nhưng hai
    phép ấy **không 1:1**: `Fraction(1) // 2 == 0` còn `1/2` là `1/2`. Alias sẽ
    biến một chương trình ĐÚNG thành một chương trình SAI CÂM — kết quả sai mà
    không ai kêu, đúng thứ tệ hơn cả việc từ chối.

    Nên: từ chối, nhưng nói ra chỗ đúng để đi. Mô hình với tay sang `/` hầu như
    luôn vì nó đang định TỰ TÍNH toạ độ — cùng gốc với `construct_point` mang
    toạ độ. Tỉ lệ chia đoạn có nhà riêng (`divide_segment.ratio`, nhận chuỗi
    phân số chính xác); toạ độ thì do kernel tính.
    """
    if v == "/":
        raise ValueError(
            "IR không có phép chia thực `/`. Nếu bạn đang chia một ĐOẠN theo tỉ "
            "lệ, dùng `divide_segment` với `ratio` dạng chuỗi phân số (vd "
            '"1/3"). Nếu đang tự tính toạ độ — đừng: engine tính chính xác, bạn '
            "chỉ nói cần dựng gì. `//` là chia LẤY NGUYÊN, không thay được `/`."
        )
    return v


class BinaryArithExpr(BaseModel):
    kind: Literal["arith"] = "arith"
    op: Annotated[
        Literal["+", "-", "*", "//", "%"],
        BeforeValidator(tu_choi_phep_chia_khong_nguyen),
    ] = Field(..., description="Toán tử số học")
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

# THÊM 2026-08-25, sau một lượt live trên đề học sinh gửi thật. Đề hỏi
# *"xác định giao điểm Q = d ∩ AD"* — dạng cực phổ biến của bài thiết diện: dựng
# giao tuyến rồi cắt nó với một cạnh của đáy. Mô hình viết đúng
# `{"kind": "intersect_line_line", "line_a": "d", "line_b": "AD"}` ở CẢ BA lượt
# thử, và cả ba lần hợp đồng từ chối vì không có tag ấy.
#
# `kernel.intersect_line_line` đã tồn tại từ đầu, chính xác trên `Fraction`, và
# NÉM đúng khi hai đường chéo nhau hay song song. Đây thuần tuý là bỏ sót ở
# tầng nối — cùng lớp với lỗ `distance` cho cặp đường–đường ở
# `GEOMETRY_CURRICULUM_COVERAGE §5`, và cũng rẻ như thế.
class IntersectLineLineExpr(BaseModel):
    kind: Literal["intersect_line_line"] = "intersect_line_line"
    line_a: str = Field(..., description="tên đường thẳng 1")
    line_b: str = Field(..., description="tên đường thẳng 2")

class MidpointExpr(BaseModel):
    kind: Literal["midpoint"] = "midpoint"
    a: str = Field(..., description="tên điểm đầu")
    b: str = Field(..., description="tên điểm cuối")

class ProjectOntoExpr(BaseModel):
    kind: Literal["project_onto"] = "project_onto"
    point: str = Field(..., description="tên điểm")
    target: str = Field(..., description="tên mặt phẳng/đường chiếu lên")

class VectorFromPointsExpr(BaseModel):
    """Vectơ CÓ HƯỚNG từ điểm `from_point` tới `to_point`.

    ─── VÌ SAO THÊM: một KIỂU ĐÃ KHAI MÀ KHÔNG CÓ NƠI SINH ─────────────────

    `vector3` nằm sẵn trong `MemoryType` từ đầu, nhưng **không biểu thức nào
    tạo ra nó** — chương trình chỉ khai được bằng `initial_value`, tức chép
    toạ độ tay. Đây không phải "thêm đại số vectơ": không có cộng, nhân vô
    hướng, tích có hướng. Đúng MỘT phép dựng, và nó tồn tại vì một lý do cụ
    thể ở dưới.

    ─── THẨM QUYỀN CỦA HƯỚNG ───────────────────────────────────────────────

    `angle_cos` cần biết chiều. `line3` là đường **vô hướng** theo quy ước —
    lấy dấu từ nó là để một quy ước cài đặt (thứ tự hai điểm lúc dựng) quyết
    một mệnh đề toán học. Nên dấu phải đến từ một đối tượng KHAI là có hướng.

    Ở runtime `vector3` và `point3` cùng là `Vec3`, nên thẩm quyền ấy **tĩnh**:
    validator đọc `memory_declarations` và từ chối `angle_cos` trên toán hạng
    không khai `vector3`. Kernel không phân biệt được hai thứ, và đó chính là
    lý do phép kiểm phải nằm trước kernel.
    """
    kind: Literal["vector_from_points"] = "vector_from_points"
    from_point: str = Field(..., description="tên điểm gốc")
    to_point: str = Field(..., description="tên điểm ngọn")

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
    quantity: Literal["distance", "angle_cos_sq", "angle_cos", "volume"] = Field(
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
        Annotated[IntersectLineLineExpr, Tag("intersect_line_line")],
        Annotated[MidpointExpr, Tag("midpoint")],
        Annotated[ProjectOntoExpr, Tag("project_onto")],
        Annotated[VectorFromPointsExpr, Tag("vector_from_points")],
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

# ── ĐIỂM DẪN XUẤT: chỉ nhận PHÉP DỰNG HÌNH HỌC ───────────────────────────
#
# ─── HAI LOẠI ĐIỂM, VÀ RANH GIỚI GIỮA CHÚNG LÀ MỘT PHẦN CỦA R0 ──────────
#
#   ĐIỂM DỮ KIỆN     khai ở `memory_declarations` với `initial_value`, kèm
#                    `source_fact_id` (đề cho) hoặc `model_assumption` (mô hình
#                    tự chọn hệ trục). Grounding gác kênh này.
#
#   ĐIỂM DẪN XUẤT    sinh ra bởi `construct_point`. Toạ độ của nó phải do
#                    KERNEL tính, không do LLM tính.
#
# ─── VÌ SAO THU HẸP KIỂU, ĐO ĐƯỢC 2 LẦN Ở 2 VÒNG ĐO ĐỘC LẬP ────────────
#
# `expr: ValueExpr` cho phép cả `arith`, `literal`, `index`, `peek`… — biểu thức
# của miền Tin học. `eval_geometry_expr` từ chối chúng, nhưng từ chối ở LÚC CHẠY.
# Hợp đồng nói HỢP LỆ, engine nói KHÔNG, và mô hình tin hợp đồng:
#
#     {"kind":"construct_point","target_var":"C",
#      "expr":{"kind":"arith","op":"+","left":{"var":"B"},"right":{"var":"D"}}}
#
# Nó tự cộng hai điểm để tính đỉnh thứ tư — vừa vi phạm R0 vừa sai công thức
# (đỉnh thứ tư là `B + D − A`, chỉ đúng khi `A` ở gốc). Xuất hiện ở Phase 6.7
# lượt `2-the-tich-lan5` VÀ Phase 6.7.2 lượt `2-the-tich-lan2`: hai vòng đo độc
# lập, hai bản mã khác nhau, cùng một câu lệnh.
#
# Hệ quả nặng hơn cả việc trượt: lỗi nổ ở EXECUTION, tức SAU vòng sửa. Lỗi
# validator được gửi ngược cho mô hình sửa (≤3 lượt); lỗi runtime thì không —
# `thu_that_bai` của cả hai lượt đều RỖNG, không một lần thử lại nào.
#
# Thu hẹp kiểu đẩy phép từ chối lên tận biên PARSE, nơi mô hình còn sửa được.
#
# ─── ĐÓNG THEO BẰNG CHỨNG, KHÔNG THEO SUY ĐOÁN ─────────────────────────
#
# Năm biểu thức dưới đây là **toàn bộ** biểu thức mà kernel trả về một `Point3`.
# Soi 30 chương trình đã sinh: `construct_point` dùng `midpoint` 22 lần và
# `arith` 2 lần, không gì khác. Soi test: dùng đúng năm cái này. Nên thu hẹp
# KHÔNG phá một đường đúng nào.
#
# `intersect_plane_plane` CỐ Ý VẮNG MẶT: nó trả `Line3`, không phải điểm.
# `var` cũng vắng: sao chép một điểm đã có không phải một phép DỰNG.
#
# `vector_from_points` cũng VẮNG, và vắng vì một lý do dễ trượt: ở runtime nó
# trả về `Vec3` — **cùng lớp với điểm**. Nên nếu `construct_point` nhận nó,
# chương trình dựng ra được một "điểm" thật ra là một PHƯƠNG, và không tầng nào
# phía sau phát hiện nổi. Vectơ sinh bằng `assign`, nơi kiểu khai của biến đích
# nói rõ nó là `vector3`.
PointExpr = Annotated[
    Union[
        Annotated[IntersectLinePlaneExpr, Tag("intersect_line_plane")],
        Annotated[IntersectLineLineExpr, Tag("intersect_line_line")],
        Annotated[MidpointExpr, Tag("midpoint")],
        Annotated[ProjectOntoExpr, Tag("project_onto")],
        Annotated[DivideSegmentExpr, Tag("divide_segment")],
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

def tu_choi_toa_do_trong_construct_point(v: Any) -> Any:
    """TỪ CHỐI CÓ DẠY cho `construct_point.expr`, thay một lỗi union câm.

    ─── ĐO ĐƯỢC 2026-08-31, probe nhị diện, HAI LƯỢT LIÊN TIẾP ─────────────

    Mô hình viết `{"kind":"construct_point","expr":{"kind":"literal","value":
    [0,0,0]}}` — nó muốn KHAI một điểm gốc và với tay sang câu lệnh DỰNG. Schema
    từ chối đúng, nhưng bằng câu của Pydantic:

        Input tag 'literal' found using 'kind' does not match any of the
        expected tags: 'intersect_line_plane', …

    Câu ấy nói *cái gì* sai và không nói *phải làm gì*, nên lượt sửa không có
    hướng — và cả lượt tổng hợp đầu tiên mất trắng, lần nào cũng vậy. Thêm một
    dòng vào prompt KHÔNG cứu được (đã thử, vẫn lặp): prompt là gợi ý, còn đây
    là chỗ mô hình thật sự bị chặn, nên đây là chỗ phải nói.

    Cùng khuôn `canonical_container_name`: **không nới hợp đồng**, chỉ đổi lời
    từ chối. `literal`/`var` vẫn bị chặn y như trước.
    """
    if isinstance(v, dict) and v.get("kind") in ("literal", "var"):
        raise ValueError(
            "`construct_point` chỉ dành cho điểm DỰNG RA từ hình đã có "
            "(giao tuyến/giao điểm, trung điểm, chia đoạn, hình chiếu). Điểm "
            "gốc — toạ độ đề cho hoặc do bạn chọn — khai ở "
            "`memory_declarations` với `initial_value`, KHÔNG qua "
            "`construct_point`."
        )
    return v


# ── Câu lệnh DỰNG HÌNH (Bước 3) ────────────────────────────────────────────
#
# Mỗi câu lệnh ở đây = **một bước trong timeline** = một khung hình. Đó là lý do
# chúng là *statement* chứ không phải *expression*: biểu thức tính ra giá trị
# nhưng không để lại dấu vết, còn học sinh cần thấy **thứ tự dựng**.
class DeclarePointStmt(BaseModel):
    """KHAI một điểm GỐC ngay trong dòng chương trình — toạ độ đề cho hoặc bạn chọn.

    ─── VÌ SAO TỒN TẠI: MA SÁT BỀ MẶT, ĐO ĐƯỢC 3/4 CA LIVE ─────────────────

    IR vốn CÓ chỗ khai điểm gốc: `memory_declarations` với `initial_value`.
    Nhưng mô hình viết chương trình theo DÒNG THỜI GIAN, nên nó nói *"đặt A tại
    gốc"* như một BƯỚC, và với tay sang `construct_point` — câu lệnh duy nhất
    trong `statements` có chữ "point". Bị chặn, nó mất trọn lượt tổng hợp đầu
    tiên. Ba trên bốn ca live, lần nào cũng đúng chỗ ấy.

    Đó là ma sát BỀ MẶT, không phải lỗi ngữ nghĩa: chương trình mô hình định
    viết hoàn toàn hợp lệ, chỉ là IR không cho nó nói câu ấy ở chỗ nó đang đứng.

    ─── VÌ SAO KHÔNG ÉP KIỂU ÂM THẦM ──────────────────────────────────────

    Cách rẻ là: thấy `construct_point` mang toạ độ thì lặng lẽ coi như khai báo.
    KHÔNG làm, vì phép ánh xạ ấy **không bảo toàn xuất xứ**: một
    `memory_declaration` mang `model_assumption`/`source_fact_id`, còn
    `construct_point` không có trường nào để chở chúng. Ép kiểu sẽ đẻ ra một
    điểm gốc KHÔNG có xuất xứ — đúng thứ `grounding_gate` sinh ra để chặn.

    Nên đây là một câu lệnh THẬT, mang đủ hai kênh xuất xứ, rồi được NÂNG về
    `memory_declarations` ở biên phân tích. Cơ chế bộ nhớ không đổi một dòng;
    R0 không có cửa nào mới.
    """
    kind: Literal["declare_point"] = "declare_point"
    target_var: str = Field(..., description="tên điểm")
    at: list[Any] = Field(
        ..., min_length=3, max_length=3,
        description="toạ độ [x, y, z] — số nguyên hoặc chuỗi phân số như \"1/2\"",
    )
    model_assumption: Optional[str] = Field(
        None, description="LÝ DO chọn toạ độ này, khi đề không cho toạ độ")
    source_fact_id: Optional[str] = Field(
        None, description="ID dữ kiện đề, khi toạ độ lấy từ đề")
    label: Optional[str] = Field(None, description="nhãn, vd A")


class ConstructPointStmt(BaseModel):
    kind: Literal["construct_point"] = "construct_point"
    target_var: str = Field(..., description="tên điểm dựng ra")
    expr: Annotated[
        PointExpr, BeforeValidator(tu_choi_toa_do_trong_construct_point)
    ] = Field(
        ...,
        description="PHÉP DỰNG sinh ra điểm — toạ độ do kernel tính. Toạ độ đề "
                    "cho hoặc do mình chọn thì khai ở memory_declarations.",
    )
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

def canonical_face_indices(v: Any) -> Any:
    """`faces` khai bằng TÊN ĐỈNH → chỉ số. Biên chuẩn hoá, KHÔNG đụng kernel.

    ─── ĐO ĐƯỢC Ở LƯỢT W4 (`8b4025e`): 3/4 ca trượt schema, CÙNG một trường ───

        statements.N.construct_solid.faces.0.0
          Input should be a valid integer … input_value='S'

    Mô hình viết `[["S","A","B"], …]`. Đó không phải cẩu thả: `faces:
    list[list[int]]` dùng **chỉ số vị trí** vào `vertices` — mã hoá thân thiện
    với máy, **thù địch với người**. Và mô hình vừa được Wave 4 dặn *"giữ nguyên
    ký hiệu điểm, đừng hạ chữ thường"*, nên nó dùng ký hiệu ở mọi chỗ.

    Ở Wave 3 tôi từ chối vá một lỗi hình-dạng-wire tương tự với lý do *"một lần
    là giai thoại"*. Nay là **ba lần, cùng một trường** — ngưỡng đã vượt.

    ─── HAI THỨ HÀM NÀY KHÔNG LÀM ─────────────────────────────────────────

    **KHÔNG nhận toạ độ.** Một mục của `faces` chỉ được là `int` (chỉ số) hoặc
    `str` (tên đỉnh đã khai ở `vertices`). Một `[0,0,0]` lọt vào đây sẽ là LLM
    tiêm toạ độ thẳng vào khối, bỏ qua cả `vertices` lẫn ranh giới R0 — nên nó
    bị từ chối tường minh, không phải bị nuốt.

    **KHÔNG đoán `str` là số.** `"0"` không được hiểu thành chỉ số 0. Chỗ này có
    một cám dỗ hợp lý (mô hình có thể khai `["0","1","2"]`), nhưng bằng chứng
    hiện có là `["S","A","B"]`, và vá theo thứ CHƯA quan sát được là mở rộng hợp
    đồng bằng suy đoán. Tên lạ ⇒ lỗi có liệt kê tên hợp lệ, và vòng sửa ≤3 lượt
    đọc được nó.

    Đồ thị phụ thuộc KHÔNG đổi: `_phu_thuoc` đọc `st.vertices` (danh sách TÊN),
    và hàm này không chạm `vertices`.
    """
    if not isinstance(v, dict):
        return v
    dinh = v.get("vertices")
    mat = v.get("faces")
    if not isinstance(dinh, list) or not isinstance(mat, list):
        return v
    tra = {t: i for i, t in enumerate(dinh) if isinstance(t, str)}

    ra: list[Any] = []
    da_ghi = False
    for f in mat:
        if not isinstance(f, list):
            ra.append(f)
            continue
        moi: list[Any] = []
        for o in f:
            if isinstance(o, str):
                if o not in tra:
                    raise ValueError(
                        f"mặt của khối trỏ tới đỉnh '{o}' chưa khai trong "
                        f"`vertices` (đã khai: {sorted(tra)})"
                    )
                moi.append(tra[o])
                da_ghi = True
            elif isinstance(o, bool) or not isinstance(o, int):
                # Chặn TIÊM TOẠ ĐỘ và mọi hình dạng lạ khác. `bool` tách riêng
                # vì trong Python nó *là* `int`, và `True` lọt vào đây sẽ thành
                # chỉ số 1 một cách âm thầm.
                raise ValueError(
                    f"mặt của khối chỉ nhận TÊN ĐỈNH hoặc chỉ số nguyên, "
                    f"nhận {o!r} ({type(o).__name__}). Toạ độ phải khai ở "
                    f"`memory_declarations`, không khai trong `faces`."
                )
            else:
                moi.append(o)
        if len(set(moi)) != len(moi):
            raise ValueError(
                f"mặt {f!r} lặp lại cùng một đỉnh — mặt suy biến, không dựng "
                "được thành đa giác."
            )
        ra.append(moi)

    if da_ghi:
        ghi_coercion(LOP_FACE_SYMBOL)
    return {**v, "faces": ra}


class ConstructPolygonStmt(BaseModel):
    """Đa giác từ CÁC ĐIỂM ĐÃ ĐẶT TÊN — `đáy ABCD`, `mặt ABC`, `thiết diện`.

    ─── VÌ SAO THÊM, ĐO ĐƯỢC Ở LƯỢT SMOKE 2026-08-26 ──────────────────────

    Đề *"hình chóp S.ABCD có đáy ABCD là hình vuông"* nêu một vật: **đáy**. IR
    không có từ nào cho nó — có `construct_solid(vertices)` cho cả KHỐI, có
    `construct_plane(through)` cho MẶT PHẲNG VÔ HẠN, nhưng không có gì cho một
    **miền phẳng hữu hạn có biên**.

    Nên mô hình phải bịa đường, và nó bịa theo hai cách khác nhau ở hai lượt:

        assign ABCD = literal(["A","B","C","D"])        ← rác trong biến polygon3
        khai `ABCD` type=polygon3 initial_value=["A",…] ← P2 bắt: không có trong đề

    Cả hai đều là **triệu chứng của cùng một khoảng trống**, và cả hai đều làm
    mất Ý NGHĨA QUÁ TRÌNH DỰNG: đáy trở thành một hằng số thay vì một vật được
    dựng ra từ bốn điểm.

    ─── KHÔNG PHẢI MỘT BƯỚC VỀ PHÍA PHẦN MỀM DỰNG HÌNH ────────────────────

    Nó KHÔNG thêm năng lực tính toán nào: `polygon3` đã là một `MemoryType` từ
    Wave 2, kernel đã có mọi thứ cần (`predicates.coplanar`), `RENDER_HINT` đã
    có ô cho nó, và `simulation_state` đã chiếu tuple-các-đỉnh thành cảnh. Câu
    lệnh này chỉ mở ĐƯỜNG KHAI BÁO hợp lệ cho một kiểu đã tồn tại — thứ duy
    nhất còn thiếu là cách nói.

    R0 nguyên vẹn: nhận **TÊN**, không nhận toạ độ. Toạ độ đọc từ bộ nhớ.
    """
    kind: Literal["construct_polygon"] = "construct_polygon"
    target_var: str = Field(..., description="tên đa giác dựng ra")
    vertices: list[str] = Field(
        ..., min_length=3,
        description="tên các đỉnh theo THỨ TỰ VÒNG QUANH, ít nhất 3",
    )
    label: Optional[str] = Field(None, description="nhãn, vd ABCD")


class ConstructSolidStmt(BaseModel):
    """Dựng khối từ ĐỈNH ĐÃ ĐẶT TÊN + bảng mặt.

    Cùng lý do với `construct_plane`, và thêm một điều: `faces` là **cấu trúc
    tổ hợp** đọc thẳng từ đề (*"hình chóp S.ABCD"* ⇒ một đáy bốn đỉnh, bốn mặt
    bên), KHÔNG phải dữ liệu hình học. LLM sở hữu quan hệ kề; kernel sở hữu
    toạ độ. Ranh giới R0 rơi đúng vào giữa hai thứ đó.

    Chỉ số trong `faces` trỏ vào `vertices` theo VỊ TRÍ, giống hệt cách
    `Polyhedron` của kernel biểu diễn — không đẻ ra một quy ước thứ hai.

    Từ Phase 5A, `faces` nhận **cả TÊN ĐỈNH lẫn chỉ số**; biên chuẩn hoá
    `canonical_face_indices` quy về chỉ số TRƯỚC khi Pydantic kiểm kiểu, nên
    kernel vẫn chỉ nhìn thấy `list[list[int]]` như cũ.
    """
    _canonical_faces = model_validator(mode="before")(canonical_face_indices)

    kind: Literal["construct_solid"] = "construct_solid"
    target_var: str = Field(..., description="tên khối dựng ra")
    vertices: list[str] = Field(
        ..., min_length=4, description="tên các đỉnh, theo thứ tự"
    )
    faces: list[list[int]] = Field(
        ..., min_length=4,
        description="mỗi mặt là danh sách TÊN ĐỈNH (vd [\"S\",\"A\",\"B\"]) "
                    "hoặc chỉ số vào `vertices`",
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
        Annotated[DeclarePointStmt, Tag("declare_point")],
        Annotated[ConstructPointStmt, Tag("construct_point")],
        Annotated[ConstructLineStmt, Tag("construct_line")],
        Annotated[ConstructPlaneStmt, Tag("construct_plane")],
        Annotated[ConstructSolidStmt, Tag("construct_solid")],
        Annotated[ConstructPolygonStmt, Tag("construct_polygon")],
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

    @model_validator(mode="before")
    @classmethod
    def _nang_declare_point(cls, data: Any) -> Any:
        """NÂNG `declare_point` từ `statements` về `memory_declarations`.

        Chạy TRƯỚC mọi phép kiểm, nên mọi tầng phía sau — grounding, static
        check, interpreter, checker — chỉ nhìn thấy MỘT cách khai điểm gốc. Cơ
        chế bộ nhớ không đổi một dòng, và không có đường vòng nào quanh R0:
        xuất xứ được chở nguyên vẹn sang khai báo, nên `grounding_gate` vẫn
        hỏi đúng câu nó vẫn hỏi.

        Nâng rồi GỠ khỏi `statements`: giữ lại thì cùng một điểm tồn tại ở hai
        chỗ, và tầng dưới sẽ thấy một câu lệnh không có nghĩa thực thi.
        """
        if not isinstance(data, dict):
            return data
        stmts = data.get("statements")
        if not isinstance(stmts, list):
            return data
        nang, con_lai = [], []
        for st in stmts:
            if isinstance(st, dict) and st.get("kind") == "declare_point":
                nang.append(st)
            else:
                con_lai.append(st)
        if not nang:
            return data

        khai = [dict(d) if isinstance(d, dict) else d
                for d in (data.get("memory_declarations") or [])]
        co_san = {d.get("name") for d in khai if isinstance(d, dict)}
        chi_muc = {d.get("name"): i for i, d in enumerate(khai)
                   if isinstance(d, dict)}
        for st in nang:
            ten = st.get("target_var")
            if ten in co_san:
                # ĐÃ KHAI RỒI — và đây KHÔNG phải mâu thuẫn. Mô hình nói cùng
                # một điều hai lần: một mục trong `memory_declarations` và một
                # `declare_point` cùng tên, cùng toạ độ. Đo được ở 3/4 ca live
                # 2026-08-31, và bản đầu của phép nâng này ĐẺ RA lỗi ấy: nó
                # thêm một khai báo thứ hai rồi để phép kiểm trùng tên bắt.
                # Tự dựng lỗi rồi tự bắt là ma sát ta tự tạo.
                #
                # Gộp: điền vào chỗ TRỐNG của khai báo có sẵn.
                #
                # ⚠️ TOẠ ĐỘ MÂU THUẪN THÌ FAIL CLOSED. Hai lời khai khác nhau
                # về cùng một điểm KHÔNG phải chuyện dư thừa — nó là hai hình
                # khác nhau. Giữ im lặng một trong hai là ta chọn hộ, và chọn
                # sai thì cả bài dựng lên một hình không ai định vẽ. Đây là
                # ranh giới giữa "gộp thứ tương đương" và "đoán".
                cu = khai[chi_muc[ten]]
                moi = st.get("at")
                if (moi is not None and cu.get("initial_value") is not None
                        and cu["initial_value"] != moi):
                    raise ValueError(
                        f"Điểm '{ten}' được khai HAI TOẠ ĐỘ khác nhau: "
                        f"{cu['initial_value']} ở memory_declarations và {moi} "
                        "ở declare_point. Giữ đúng MỘT lời khai."
                    )
                for khoa, gt in (("initial_value", moi),
                                 ("model_assumption", st.get("model_assumption")),
                                 ("source_fact_id", st.get("source_fact_id"))):
                    if gt is not None and cu.get(khoa) is None:
                        cu[khoa] = gt
                continue
            khai.append({
                "name": ten, "type": "point3",
                "initial_value": st.get("at"),
                "model_assumption": st.get("model_assumption"),
                "source_fact_id": st.get("source_fact_id"),
            })
            chi_muc[ten] = len(khai) - 1
            co_san.add(ten)
        return {**data, "memory_declarations": khai, "statements": con_lai}

    @model_validator(mode="before")
    @classmethod
    def _rang_buoc_lan_dau(cls, data: Any) -> Any:
        """RÀNG BUỘC LẦN ĐẦU của `assign` hình học → dạng chuẩn tắc.

        ─── LỖ NÓ BỊT, ĐO ĐƯỢC Ở CLEAN_BASELINE_V1 ────────────────────────

        4/6 chương trình chết ở runtime vì `assign M = midpoint(B,C)` với `M`
        chưa khai. Bảng sự thật (`scripts/audit_assign_binding.py`):

            assign X = midpoint, chưa khai   → giá trị vào SCOPE, provenance None
            assign X = midpoint, đã khai     → memory, provenance None
            construct_point X = midpoint     → memory, provenance ĐẦY ĐỦ

        `_set_var` đưa tên chưa khai vào `scope_stack`, còn kernel hình học chỉ
        đọc `self.memory`. Nên phép tính CHẠY, giá trị ĐÚNG, và câu lệnh kế
        tiếp ném `GEOMETRY_UNDECLARED` — một tiền điều kiện TĨNH bị canh ở tầng
        runtime, nơi vòng sửa không với tới.

        ─── HAI ĐƯỜNG, VÀ VÌ SAO KHÔNG PHẢI MỘT ───────────────────────────

        · RHS sinh ra ĐIỂM  → viết lại thành `construct_point`. Nó là dạng
          chuẩn tắc: memory + provenance có sẵn, 1:1, và bớt một lối cho mô
          hình chọn nhầm.
        · RHS sinh ra vectơ/đường/mặt → **giữ `assign`** và bổ sung khai báo
          với kiểu suy tĩnh. Không viết lại được vì IR không có
          `construct_vector`; `construct_line` nhận hai TÊN ĐIỂM, không nhận
          biểu thức. `assign` là lối DUY NHẤT cho chúng, nên nó phải chạy.

        ─── BA THỨ CỐ Ý KHÔNG LÀM ─────────────────────────────────────────

        **① CHỈ TẦNG NGOÀI CÙNG.** Một `assign` trong `if`/`while` không được
        nâng: nâng nó là khai một tên ở scope ngoài rồi để nó mang `None` khi
        nhánh không chạy — đúng món nợ `RUNTIME_NONE_OPERAND_REACHABLE` mà
        `ir_static_check` đã khai và không được nới. Ca ấy để thẩm định tĩnh
        TỪ CHỐI, nơi mô hình còn sửa được.

        **② KHÔNG đụng giá trị vô hướng.** `assign X = measure(...)` hay
        `literal` vào scope là ĐÚNG và vẫn chạy: chúng không đi qua kernel hình
        học, và `_record_step` chụp cả scope nên bộ chấm vẫn thấy. Sửa thứ
        không hỏng là mở một bề mặt hồi quy cho miền Tin học.

        **③ KHÔNG tự đăng ký toạ độ thô.** Chỉ biểu thức DỰNG mới được nâng.
        `assign X = literal([1,2,3])` vẫn không thành một điểm — nếu không thì
        đây là cửa sau của cổng trung thực năng lực.
        """
        if not isinstance(data, dict):
            return data
        stmts = data.get("statements")
        if not isinstance(stmts, list):
            return data

        from .ir_static_check import _CHU_KY, DIEM

        khai = [dict(d) if isinstance(d, dict) else d
                for d in (data.get("memory_declarations") or [])]
        co_san = {d.get("name") for d in khai if isinstance(d, dict)}
        moi_stmts, doi = [], False
        for st in stmts:
            if not (isinstance(st, dict) and st.get("kind") == "assign"):
                moi_stmts.append(st)
                continue
            e = st.get("expr")
            k = e.get("kind") if isinstance(e, dict) else None
            if k not in _CHU_KY:
                moi_stmts.append(st)
                continue
            ten, kieu = st.get("target_var"), _CHU_KY[k][1]
            if kieu == DIEM:
                moi_stmts.append({"kind": "construct_point", "target_var": ten,
                                  "expr": e,
                                  **({"label": st["label"]}
                                     if st.get("label") else {})})
                doi = True
                continue
            moi_stmts.append(st)
            if ten not in co_san:
                khai.append({"name": ten, "type": kieu})
                co_san.add(ten)
                doi = True
        if not doi:
            return data
        return {**data, "memory_declarations": khai, "statements": moi_stmts}

    @field_validator("description", mode="before")
    @classmethod
    def _cat_mo_ta_dai(cls, v: Any) -> Any:
        """CẮT thay vì TỪ CHỐI — `description` không chạm đúng đắn.

        Đo được ở lượt live 2026-08-31: một chương trình hình học ĐÚNG bị vứt
        vì phần văn xuôi dài 1200 ký tự. `description` đi đúng một chỗ —
        `pipeline_adapter` chép nó vào envelope để hiển thị — và không chạm
        hình học, bộ chấm hay grounding. Bắt cả chương trình chết vì nó là để
        một trường TRÌNH BÀY phủ quyết một trường NGỮ NGHĨA.

        Cắt là phép chuẩn hoá tất định, kiểm được, và không mất gì đáng giá:
        1000 ký tự đã dài hơn mọi mô tả có ích. Ghi `…` để người đọc biết.
        """
        if isinstance(v, str) and len(v) > 1000:
            return v[:999] + "…"
        return v


def generate_json_schema() -> dict[str, Any]:
    """Sinh JSON Schema chuẩn từ Pydantic Contract."""
    return SemanticProgramSpec.model_json_schema()
