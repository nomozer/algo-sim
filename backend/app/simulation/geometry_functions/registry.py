# -*- coding: utf-8 -*-
"""THƯ VIỆN HÀM DỰNG HÌNH + HỢP ĐỒNG AI → LỜI GỌI HÀM (run `text-to-geometry-functions`, mở rộng ở `ai-function-route`).

AI đọc đề và chỉ được CHỌN lời gọi trong `REGISTRY`; mỗi lời gọi kèm `source.quotes` — các đoạn nguyên văn của đề mà nó
dựa vào (một dữ kiện có thể trải trên nhiều câu). Lược đồ đóng (`extra="forbid"`): không ô nào nhận toạ độ, không hàm
tự do, không mã. Engine tất định (`engine.py`) mới là thứ chuẩn hoá quan hệ, dựng, chọn bố cục và kiểm.

─── CỔNG NGUỒN (`kiem_nguon`) — NĂM TẦNG, TẤT ĐỊNH ───────────────────────────
1. VỊ TRÍ — mỗi quote nằm trong đề (so bỏ qua khoảng trắng: `SA⊥(ABC)` ≡ `SA ⊥ (ABC)`)      QUOTE_NOT_IN_SOURCE
   nhãn điểm phải là nhãn của đề                                                          UNKNOWN_LABEL
2. VAI TRÒ MỆNH ĐỀ — lời gọi khẳng định (mọi hàm trừ `ask_*`/`unsupported`) phải là TIỀN ĐỀ:
   nằm sau "chứng minh/CMR/chứng tỏ" (chưa có "biết") ⇒ điều phải chứng minh               GOAL_CLAUSE_NOT_PREMISE
   nằm sau "nếu" mà chưa tới "thì" ⇒ giả thiết điều kiện                                  CONDITIONAL_CLAUSE
3. PHẠM VI PHỦ ĐỊNH — dấu phủ định trong quote HOẶC ngay trước nó trong cùng mệnh đề        NEGATED_CLAUSE
4. VỊ TỪ + THAM CHIẾU — từ định nghĩa của CẤU TRÚC câu (`cues`; mỗi cấu trúc là một hàm riêng: "vuông góc với (ABC)",
   "là đường cao của hình chóp", "hình chiếu vuông góc … là", không phải danh sách đồng nghĩa của một hàm)  PREDICATE_NOT_IN_QUOTE
   mặt phẳng được nhắc (`(ABC)`, `ABCD`, hoặc "đáy")                                      PLANE_NOT_IN_QUOTE
   điểm/đoạn đóng vai riêng (đường thẳng, ảnh hình chiếu, chân) được nhắc NGOÀI nhóm mặt phẳng   ROLE_NOT_IN_QUOTE
5. GIÁ TRỊ — số neo theo NHÃN ĐOẠN khi quote có nhãn ấy (`AB = 3, BC = 4`: BC ↔ 4); không có nhãn thì quote phải có
   đúng MỘT số                                                            AMBIGUOUS_VALUE_QUOTE / UNGROUNDED_VALUE

Từ khoá là điều kiện CẦN, không đủ: cổng chặn lời gọi mà đoạn trích không nói tới; nó không hiểu câu thay mô hình. Quan
hệ tương đương (đường cao ⇒ ⊥ mặt đáy tại chân; hình chiếu ⇒ ⊥; ⊥ hai đường cắt nhau ⇒ ⊥ mặt) được CHUẨN HOÁ trong
engine kèm tiền điều kiện hình học, không ở đây.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator

REGISTRY_VERSION = "geometry-functions/3"


class TuChoi(Exception):
    """Từ chối CÓ MÃ. `calls` = id lời gọi liên quan (rỗng khi không quy được về lời gọi nào)."""

    def __init__(self, code: str, reason: str, calls: tuple[str, ...] = (), data: dict | None = None) -> None:
        super().__init__(f"{code}: {reason}")
        self.code, self.reason, self.calls, self.data = code, reason, tuple(calls), dict(data or {})


# ── chuẩn hoá ký hiệu ───────────────────────────────────────────────────────
def chuan_hoa(s: str) -> str:
    s = unicodedata.normalize("NFC", s).replace("’", "'").replace("′", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", s).strip()


def _nhan(v: Any) -> Any:
    return chuan_hoa(v) if isinstance(v, str) else v


Label = Annotated[str, BeforeValidator(_nhan), Field(pattern=r"^[A-Z][0-9]*'?$", description="nhãn một điểm của đề, vd S, A, A'")]
SolidName = Annotated[str, BeforeValidator(_nhan),
                      Field(pattern=r"^(?:[A-Z][0-9]*'?)+\.(?:[A-Z][0-9]*'?)+$", description="ký hiệu khối, vd S.ABC hoặc ABC.A'B'C'")]
ExactNumber = Annotated[str, BeforeValidator(_nhan),
                        Field(pattern=r"^(?:\d+(?:[.,]\d+)?(?:/\d+)?a?(?:√\d+)?(?:/\d+)?|a(?:√\d+)?(?:/\d+)?|√\d+(?:/\d+)?)$",
                              description="độ dài CHÉP từ đề: số dương (4, 2/3, √3, 3√3/4) hoặc theo ký hiệu a (a, 2a, a√3, a√3/2)")]
Seg = Annotated[list[Label], Field(min_length=2, max_length=2)]
Poly = Annotated[list[Label], Field(min_length=3)]

#: Một số chính xác trong văn bản: hệ số · (a) · √căn / mẫu. Không dính chữ/nhãn hai bên (`A1`, `bằng` không tính).
_SO = re.compile(r"(?<![\w'])(?P<he>\d+(?:[.,]\d+)?(?:/\d+)?)?(?P<sym>a)?(?:√(?P<can>\d+))?(?:/(?P<mau>\d+))?(?![\w'])")


def _doc(m: re.Match) -> tuple[Fraction, bool] | None:
    if not (m["he"] or m["sym"] or m["can"]):
        return None
    he = Fraction((m["he"] or "1").replace(",", ".")) / int(m["mau"] or 1)
    return he * he * int(m["can"] or 1), bool(m["sym"])


def doc_so(s: str) -> tuple[Fraction, bool]:
    """Số chính xác (dạng `ExactNumber`) → (hệ số², có ký hiệu a). Không float: `1,5` đọc thành 3/2."""
    m = _SO.fullmatch(chuan_hoa(s))
    if not m or (r := _doc(m)) is None:
        raise TuChoi("SCHEMA_INVALID", f"không phải số chính xác: {s!r}")
    return r


def binh_phuong(s: str) -> Fraction:
    """Hệ số² của một độ dài (với độ dài ký hiệu: hệ số² theo đơn vị a)."""
    return doc_so(s)[0]


def so_trong(quote: str) -> list[tuple[int, Fraction, bool]]:
    """(vị trí, giá trị², có a) của các số trong một đoạn đề; chữ số dính nhãn (A1) không tính."""
    return [(m.start(), *r) for m in _SO.finditer(chuan_hoa(quote)) if (r := _doc(m)) is not None]


# ── đối số có kiểu của từng hàm ─────────────────────────────────────────────
class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegularPolygonArgs(_Args):
    vertices: Poly = Field(..., description="các đỉnh theo thứ tự vòng quanh")
    side: ExactNumber | None = Field(None, description="cạnh, nếu đề nêu")


class RectangleArgs(_Args):
    vertices: Annotated[list[Label], Field(min_length=4, max_length=4)] = Field(..., description="bốn đỉnh theo vòng")


class RightAngleArgs(_Args):
    vertex: Label = Field(..., description="đỉnh góc vuông")
    rays: Seg = Field(..., description="hai điểm trên hai cạnh góc vuông")


class SegmentLengthArgs(_Args):
    segment: Seg
    value: ExactNumber


class PerpendicularLinePlaneArgs(_Args):
    line: Seg = Field(..., description="hai điểm của đường thẳng, vd [S, A]")
    plane: Poly = Field(..., description="các điểm của mặt phẳng, vd [A, B, C]")


class AltitudeArgs(_Args):
    apex: Label = Field(..., description="đỉnh khối")
    foot: Label = Field(..., description="chân đường cao, điểm trên mặt đáy")
    solid: SolidName


class OrthogonalProjectionArgs(_Args):
    point: Label = Field(..., description="điểm được chiếu")
    plane: Poly = Field(..., description="mặt phẳng chiếu lên")
    image: Label = Field(..., description="hình chiếu (ảnh) của điểm")


class ProjectionLineArgs(_Args):
    point: Label
    line: Seg
    image: Label


class IntersectionLinesArgs(_Args):
    point: Label
    line1: Seg
    line2: Seg


class IntersectionPlaneArgs(_Args):
    point: Label
    line: Seg
    plane: Poly


class PerpendicularLinesArgs(_Args):
    line1: Seg
    line2: Seg


class EqualLengthArgs(_Args):
    segment_a: Seg
    segment_b: Seg


class MidpointArgs(_Args):
    point: Label = Field(..., description="tên trung điểm")
    segment: Seg


class CentroidArgs(_Args):
    point: Label = Field(..., description="tên trọng tâm")
    polygon: Poly


class PyramidArgs(_Args):
    apex: Label
    base: Poly = Field(..., description="đáy theo thứ tự vòng quanh")


class PrismArgs(_Args):
    base: Poly
    top: Poly = Field(..., description="đáy trên, cùng thứ tự với đáy dưới (A ↔ A')")
    right: bool = Field(..., description="lăng trụ ĐỨNG (đề nói đứng/đều)")


class FacePerpendicularBaseArgs(_Args):
    face: Annotated[list[Label], Field(min_length=3, max_length=3)] = Field(..., description="mặt bên, vd [S, A, B]")
    base: Poly = Field(..., description="mặt đáy")


class HeightArgs(_Args):
    solid: SolidName
    value: ExactNumber


class AskVolumeArgs(_Args):
    solid: SolidName


class AskLengthArgs(_Args):
    segment: Seg


class AskDistancePointPlaneArgs(_Args):
    point: Label
    plane: Annotated[list[Label], Field(min_length=3, max_length=3)]


class AskDistanceLinesArgs(_Args):
    line1: Seg
    line2: Seg


class AskAngleLinePlaneArgs(_Args):
    line: Seg
    plane: Poly


class AskAnglePlanePlaneArgs(_Args):
    plane1: Poly
    plane2: Poly


class AskAreaArgs(_Args):
    polygon: Poly


class SectionArgs(_Args):
    solid: SolidName
    plane: Poly = Field(..., description="mặt phẳng cắt: ba điểm đã có tên, không thẳng hàng")


class IntersectionLineArgs(_Args):
    plane1: Poly = Field(..., description="mặt phẳng 1: ba điểm đã có tên")
    plane2: Poly = Field(..., description="mặt phẳng 2: ba điểm đã có tên")


class UnsupportedArgs(_Args):
    reason: str = Field(..., min_length=1, description="vì sao mệnh đề không ánh xạ được vào thư viện")


@dataclass(frozen=True)
class FunctionSpec:
    name: str
    args: type[_Args]
    kind: Literal["fact", "construct", "ask", "escape"]
    description: str
    #: Mỗi nhóm phải có ít nhất một từ (không phân biệt hoa thường) trong các quote; `re:` = biểu thức chính quy.
    keywords: tuple[tuple[str, ...], ...] = ()
    #: Ô số phải neo vào quote.
    value_fields: tuple[str, ...] = ()
    #: Ô là MẶT PHẲNG phải được nhắc trong quote (nhóm nhãn trùng tập điểm, hoặc "đáy").
    plane_fields: tuple[str, ...] = ()
    #: Ô là ĐOẠN/ĐƯỜNG phải được nhắc (hai nhãn liền nhau trong một từ, vd `SA`).
    segment_fields: tuple[str, ...] = ()
    #: Ô là ĐIỂM đóng vai riêng phải được nhắc ngoài nhóm mặt phẳng.
    point_fields: tuple[str, ...] = ()


_VUONG = ("vuông", "⊥")
_F = FunctionSpec
REGISTRY: dict[str, FunctionSpec] = {s.name: s for s in (
    _F("regular_polygon", RegularPolygonArgs, "fact", "Đa giác đều (tam giác đều, hình vuông, lục giác đều) với các đỉnh "
       "đã nêu; cạnh nếu đề nêu.", (("đều", "hình vuông", "lập phương"),), ("side",)),
    # "hình hộp chữ nhật" có đáy là hình chữ nhật — từ định nghĩa là "chữ nhật", không bắt buộc "hình chữ nhật" liền nhau.
    _F("rectangle", RectangleArgs, "fact", "Hình chữ nhật với bốn đỉnh đã nêu.", (("chữ nhật",),)),
    _F("right_angle", RightAngleArgs, "fact", "Góc vuông tại một đỉnh (tam giác vuông tại B ⇒ đỉnh B, hai điểm A, C).",
       (("vuông",),)),
    # Không bắt nhãn đoạn: "cạnh bên bằng 5" (chóp đều) hợp lệ với SA đại diện; số vẫn căn theo nhãn KHI quote có nhãn.
    _F("segment_length", SegmentLengthArgs, "fact", "Độ dài một đoạn thẳng do đề cho.", (), ("value",)),
    _F("perpendicular_line_plane", PerpendicularLinePlaneArgs, "fact", "Đường thẳng vuông góc với mặt phẳng (SA ⊥ (ABC), "
       "SA vuông góc với mặt phẳng đáy).", (_VUONG,), plane_fields=("plane",), segment_fields=("line",)),
    _F("altitude", AltitudeArgs, "fact", "Đề nói một đoạn LÀ ĐƯỜNG CAO của khối (SA là đường cao của hình chóp S.ABC).",
       (("đường cao",), ("chóp", "tứ diện")), point_fields=("foot",)),
    _F("orthogonal_projection", OrthogonalProjectionArgs, "fact", "Đề nói hình chiếu vuông góc của một điểm lên một mặt "
       "phẳng là một điểm.", (("hình chiếu",),), plane_fields=("plane",), point_fields=("image",)),
    _F("orthogonal_projection_line", ProjectionLineArgs, "construct", "Dựng ảnh hình chiếu vuông góc của điểm lên đường thẳng.",
       (("hình chiếu",),), segment_fields=("line",), point_fields=("image",)),
    _F("intersect_line_line", IntersectionLinesArgs, "construct", "Dựng giao điểm DUY NHẤT của hai đường thẳng; không phải đoạn hữu hạn.",
       (("giao điểm",),), segment_fields=("line1", "line2"), point_fields=("point",)),
    _F("intersect_line_plane", IntersectionPlaneArgs, "construct", "Dựng giao điểm DUY NHẤT của đường thẳng và mặt phẳng.",
       (("giao điểm",),), plane_fields=("plane",), segment_fields=("line",), point_fields=("point",)),
    _F("perpendicular_lines", PerpendicularLinesArgs, "fact", "Hai đường thẳng vuông góc (SA ⊥ AB). Một lời gọi cho MỖI cặp.",
       (_VUONG,), segment_fields=("line1", "line2")),
    _F("equal_length", EqualLengthArgs, "fact", "Hai đoạn bằng nhau (SA = AB).", (("=", "bằng"),),
       segment_fields=("segment_a", "segment_b")),
    _F("height", HeightArgs, "fact", "Chiều cao của một khối do đề cho.", (("cao",),), ("value",)),
    _F("face_perpendicular_base", FacePerpendicularBaseArgs, "fact", "Mặt bên (một đỉnh ngoài đáy + một cạnh đáy) vuông "
       "góc với mặt đáy.", (_VUONG,), plane_fields=("base", "face")),
    _F("midpoint", MidpointArgs, "construct", "Gọi một điểm là trung điểm của một đoạn.", (("trung điểm",),)),
    _F("centroid", CentroidArgs, "construct", "Gọi một điểm là trọng tâm của một đa giác.", (("trọng tâm",),)),
    _F("pyramid", PyramidArgs, "construct", "Khối chóp với đỉnh và đáy đã nêu.", (("chóp", "tứ diện"),)),
    _F("regular_pyramid", PyramidArgs, "construct", "Khối chóp ĐỀU: đáy đa giác đều, chân đường cao tại tâm đáy.",
       (("chóp", "tứ diện"), ("đều",))),
    _F("prism", PrismArgs, "construct", "Khối lăng trụ với hai đáy tương ứng; `right` khi đề nói lăng trụ đứng/đều.",
       (("lăng trụ", "hình hộp", "lập phương"),)),
    _F("ask_volume", AskVolumeArgs, "ask", "Đề hỏi thể tích một khối.", (("thể tích", r"re:(?<![\w'])V(?![\w'])"),)),
    _F("ask_length", AskLengthArgs, "ask", "Đề hỏi độ dài một đoạn.", (("độ dài", "tính", "tìm"),)),
    _F("ask_distance_point_plane", AskDistancePointPlaneArgs, "ask", "Đề hỏi khoảng cách từ một điểm tới một mặt phẳng.",
       (("khoảng cách",),)),
    _F("ask_distance_lines", AskDistanceLinesArgs, "ask", "Đề hỏi khoảng cách giữa hai đường thẳng (chéo nhau).",
       (("khoảng cách",),)),
    _F("ask_angle_line_plane", AskAngleLinePlaneArgs, "ask", "Đề hỏi góc giữa đường thẳng và mặt phẳng (trả cos²).",
       (("góc",),)),
    _F("ask_angle_plane_plane", AskAnglePlanePlaneArgs, "ask", "Đề hỏi góc giữa hai mặt phẳng (trả cos²).", (("góc",),)),
    _F("ask_area", AskAreaArgs, "ask", "Đề hỏi diện tích một đa giác.", (("diện tích",),)),
    # Slice 1 (run `hybrid-section-slice`): cửa vào cho phép dựng engine chung ĐÃ có (`construct_section`, `intersect_plane_plane`).
    _F("section", SectionArgs, "construct", "Dựng THIẾT DIỆN của một khối với mặt phẳng qua ba điểm đã có tên.",
       (("thiết diện",),), plane_fields=("plane",)),
    _F("intersection_line", IntersectionLineArgs, "construct", "Dựng GIAO TUYẾN của hai mặt phẳng, mỗi mặt qua ba điểm đã có tên.",
       (("giao tuyến",),), plane_fields=("plane1", "plane2")),
    _F("ask_section_area", SectionArgs, "ask", "Đề hỏi diện tích thiết diện của một khối cắt bởi một mặt phẳng.",
       (("diện tích",), ("thiết diện",)), plane_fields=("plane",)),
    _F("unsupported", UnsupportedArgs, "escape", "Mệnh đề không ánh xạ được vào thư viện — engine sẽ từ chối trung thực."),
)}

#: Dấu phủ định — xét trong quote VÀ phần mệnh đề đứng ngay trước nó.
PHU_DINH = ("không phải", "không là", "không vuông góc", "không ⊥", "không đều", "không song song", "chưa chắc")
#: Mở đầu điều PHẢI CHỨNG MINH / PHẢI LÀM (S1 thêm: chỉ ra, giải thích, kiểm chứng, tìm điều kiện — nhóm A phần dư).
_MUC_TIEU = ("chứng minh", "cmr", "chứng tỏ", "chỉ ra", "giải thích", "kiểm chứng", "tìm điều kiện",
             # review S1, I5
             "kiểm tra", "suy ra", "xác minh", "vì sao", "tại sao", "lập luận")
#: Không khẳng định (S1, nhóm A): phủ định mạnh, tình thái, phủ định mệnh đề — đọc trong quote và phần trước nó của mệnh đề.
_KHONG_KHANG_DINH = re.compile(r"(?<!\w)(?:không hề|chẳng|không nhất thiết|không đúng là|có thể(?!\s+tích)"
                               r"|không bao giờ|không thể|chưa|không còn|đâu có)(?!\w)",
                               re.IGNORECASE)
#: Tuyển ("… hoặc …"): một vế của phép tuyển không phải dữ kiện — đọc trong CẢ mệnh đề.
_TUYEN = re.compile(r"(?<!\w)hoặc(?!\w)", re.IGNORECASE)
#: Câu tự phủ nhận điều nó nêu ("… là sai", "… vô lí") — đọc trong CẢ câu (review S1, I5).
_SAI = re.compile(r"(?<!\w)(?:là\s+(?:điều\s+)?(?:sai|không đúng)|vô lí|vô lý)(?!\w)", re.IGNORECASE)
#: Điều kiện đặt SAU điều được nêu, trong cùng mệnh đề ("SA ⊥ (ABCD) khi M trùng S") — review S1, I5.
_DIEU_KIEN_SAU = re.compile(r"(?<!\w)(?:khi(?!\s+(?:đó|cắt|dựng|quay|chiếu))|nếu|với điều kiện|trừ khi)(?!\w)", re.IGNORECASE)


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quote: str | None = Field(None, min_length=1, description="một đoạn NGUYÊN VĂN của đề")
    quotes: list[str] | None = Field(None, min_length=1, description="các đoạn NGUYÊN VĂN của đề (một dữ kiện có thể trải nhiều câu)")

    @model_validator(mode="after")
    def _co_quote(self) -> "Source":
        if not (self.quote or self.quotes) or any(not q.strip() for q in self.quotes or []):
            raise ValueError("lời gọi phải chép ít nhất một đoạn nguyên văn của đề")
        return self

    def tat_ca(self) -> tuple[str, ...]:
        return tuple(chuan_hoa(q) for q in ([self.quote] if self.quote else []) + list(self.quotes or []))


class FunctionCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., min_length=1)
    fn: str
    args: dict[str, Any]
    source: Source
    depends_on: list[str] = Field(default_factory=list, description="id các lời gọi mà lời gọi này cần (khai báo của AI; engine tự kiểm)")


@dataclass(frozen=True)
class LoiGoi:
    """Một lời gọi ĐÃ kiểm lược đồ."""

    id: str
    fn: str
    args: _Args
    quotes: tuple[str, ...]
    depends_on: tuple[str, ...] = ()

    @property
    def spec(self) -> FunctionSpec:
        return REGISTRY[self.fn]

    @property
    def quote(self) -> str:
        return " … ".join(self.quotes)


def doc_ke_hoach(raw: Any) -> tuple[LoiGoi, ...]:
    """`{"calls": [...]}` → lời gọi có kiểu. Hàm lạ, ô lạ, kiểu sai ⇒ SCHEMA_INVALID; phụ thuộc treo / vòng ⇒ mã riêng."""
    try:
        calls = [FunctionCall.model_validate(c) for c in (raw or {}).get("calls") or []]
    except (ValidationError, AttributeError) as e:
        raise TuChoi("SCHEMA_INVALID", f"lời gọi sai lược đồ: {e}") from None
    if not calls:
        raise TuChoi("SCHEMA_INVALID", "kế hoạch rỗng")
    if len({c.id for c in calls}) != len(calls):
        raise TuChoi("DUPLICATE_CALL_ID", "id lời gọi trùng")
    ra = []
    for c in calls:
        if c.fn not in REGISTRY:
            raise TuChoi("SCHEMA_INVALID", f"hàm {c.fn!r} không có trong thư viện", (c.id,))
        try:
            a = REGISTRY[c.fn].args.model_validate(c.args)
        except ValidationError as e:
            raise TuChoi("SCHEMA_INVALID", f"{c.id} ({c.fn}): {e.errors()[0]['msg']}", (c.id,)) from None
        ra.append(LoiGoi(c.id, c.fn, a, c.source.tat_ca(), tuple(c.depends_on)))
    _kiem_phu_thuoc(ra)
    return tuple(ra)


def _kiem_phu_thuoc(calls: list[LoiGoi]) -> None:
    ids = {c.id for c in calls}
    canh = {c.id: c.depends_on for c in calls}
    for c in calls:
        if treo := sorted(set(c.depends_on) - ids):
            raise TuChoi("DANGLING_DEPENDENCY", f"{c.id} phụ thuộc lời gọi không tồn tại {treo}", (c.id,))
    trang: dict[str, int] = {}

    def tham(u: str) -> None:
        trang[u] = 1
        for v in canh[u]:
            if trang.get(v) == 1:
                raise TuChoi("DEPENDENCY_CYCLE", f"phụ thuộc vòng qua {u} → {v}", (u, v))
            if v not in trang:
                tham(v)
        trang[u] = 2

    for u in sorted(ids):
        if u not in trang:
            tham(u)


# ── nhãn điểm ───────────────────────────────────────────────────────────────
_TU = re.compile(r"[\w'.]+")


def _tu_nhan(s: str) -> list[tuple[int, int, list[list[str]]]]:
    """Các từ toàn chữ HOA trong `s`: (đầu, cuối, phần nhãn theo dấu chấm) — `S.ABC` → [[S], [A, B, C]]."""
    ra = []
    for m in _TU.finditer(s):
        w = m.group(0).strip(".")
        if w and any(ch.isalpha() for ch in w) and all(not ch.isalpha() or "A" <= ch <= "Z" for ch in w):
            ra.append((m.start(), m.end(), [re.findall(r"[A-Z][0-9]*'?", p) for p in w.split(".") if p]))
    return ra


def nhan_cua_de(text: str) -> set[str]:
    """Nhãn điểm có trong đề: từ chỉ gồm chữ HOA (S.ABC, (ABC), SA, A'B'C'), tách thành từng nhãn."""
    return {n for _a, _b, phan in _tu_nhan(chuan_hoa(text)) for p in phan for n in p}


def nhan_cua_loi_goi(c: LoiGoi) -> set[str]:
    ra: set[str] = set()
    for v in c.args.model_dump().values():
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, str) and re.fullmatch(r"(?:[A-Z][0-9]*'?)+(?:\.(?:[A-Z][0-9]*'?)+)?", x):
                ra.update(re.findall(r"[A-Z][0-9]*'?", x))
    return ra


# ── vị trí quote trong đề (bỏ qua khoảng trắng) ──────────────────────────────
def _vi_tri(de: str, q: str) -> tuple[int, int] | None:
    """Vị trí [đầu, cuối) của `q` trong `de`, so sau khi BỎ mọi khoảng trắng (cách gõ ký hiệu khác nhau vẫn khớp)."""
    goc = [i for i, ch in enumerate(de) if not ch.isspace()]
    nen = "".join(de[i] for i in goc)
    qn = "".join(ch for ch in q if not ch.isspace())
    k = nen.find(qn) if qn else -1
    return None if k < 0 else (goc[k], goc[k + len(qn) - 1] + 1)


def _cau_chua(de: str, vt: int) -> int:
    """Đầu câu chứa vị trí `vt` (câu tách bởi . ! ? theo sau là khoảng trắng — `S.ABC` không tách)."""
    dau = 0
    for m in re.finditer(r"[.!?]\s+", de):
        if m.end() <= vt:
            dau = m.end()
    return dau


def _phu_dinh(de: str, vt: int, q: str) -> bool:
    """Phủ định trong quote, hoặc ngay trước nó trong CÙNG mệnh đề (cắt ở , ; :)."""
    truoc = de[_cau_chua(de, vt):vt]
    duoi = re.split(r"[,;:]", truoc)[-1]
    ma, mb = _bien_menh_de(de, vt)
    ca, cb = _bien_cau(de, vt)
    return (any(p in (duoi + q).lower() for p in PHU_DINH) or bool(_KHONG_KHANG_DINH.search(duoi + q))
            or bool(_TUYEN.search(de[ma:mb])) or bool(_SAI.search(de[ca:cb])))


def _co_tu(quotes: tuple[str, ...], nhom: tuple[str, ...]) -> bool:
    for k in nhom:
        if k.startswith("re:"):
            if any(re.search(k[3:], q) for q in quotes):
                return True
        elif any(k in q.lower() for q in quotes):
            return True
    return False


_LAP_PHUONG = re.compile(r"(?<!\w)(?:(?:hình|khối)\s+)?lập\s+phương(?!\w|\s+hóa\b)", re.IGNORECASE)
_HOP_CHU_NHAT = re.compile(r"(?<!\w)(?:(?:hình|khối)\s+)?hộp\s+chữ\s+nhật(?!\w)", re.IGNORECASE)
_CHU_NHAT = re.compile(r"(?<!\w)chữ\s+nhật(?!\w|\s+hóa\b)", re.IGNORECASE)


def _cung_da_giac(a: list[str], b: list[str]) -> bool:
    """Hai nhóm nhãn gọi đúng cùng một đa giác; thứ tự đọc quanh mặt không mang nghĩa source-grounding."""
    return len(a) == len(b) and set(a) == set(b)


def _mat_cua_khoi_sau_cum(q: str, cum: re.Pattern[str], vertices: list[str]) -> bool:
    """`hình/khối <loại> ABCD.EFGH`: chỉ token nhãn đầu tiên sau cụm loại mới là tên của khối ấy."""
    for m in cum.finditer(q):
        token = next((phan for dau, _cuoi, phan in _tu_nhan(q)
                      if dau >= m.end() and not q[m.end():dau].strip()), None)
        if token and any(_cung_da_giac(p, vertices) for p in token):
            return True
    return False


def _co_doi_tuong_hinh(c: LoiGoi, de: str = "") -> bool:
    """Bind hai cue định nghĩa mới (`lập phương`, `chữ nhật`) vào đúng đa giác, không mượn keyword của đối tượng khác."""
    vertices = list(c.args.vertices)
    if c.fn == "regular_polygon":
        for q in c.quotes:
            if _mat_cua_khoi_sau_cum(q, _LAP_PHUONG, vertices):
                return True
            for dau, cuoi, phan in _tu_nhan(q):
                if any(_cung_da_giac(p, vertices) for p in phan):
                    if re.match(r"\s+(?:là\s+)?(?:(?:tam|tứ|ngũ|lục|đa)\s+giác\s+)?đều\b|\s+(?:là\s+)?hình\s+vuông\b",
                                q[cuoi:], re.IGNORECASE):
                        return True
                    if re.search(r"(?:(?:tam|tứ|ngũ|lục|đa)\s+giác\s+đều|hình\s+vuông)\s*$",
                                 q[:dau], re.IGNORECASE):
                        return True
                # Every triangular face of the explicitly named regular tetrahedron is regular.
                if len(vertices) == 3 and len(phan) == 1 and len(phan[0]) == 4 and set(vertices) <= set(phan[0]):
                    if re.search(r"\btứ\s+diện\s+đều\s*$", q[:dau], re.IGNORECASE):
                        return True
            # Legacy multi-sentence "đáy là tam giác đều": resolve only a unique explicitly named base in the source.
            if re.fullmatch(r"đáy\s+(?:là\s+)?(?:tam|tứ|ngũ|lục|đa)\s+giác\s+đều", q.strip(), re.IGNORECASE):
                bases = {tuple(p[1]) for dau, _cuoi, p in _tu_nhan(de) if len(p) == 2 and
                         re.search(r"(?:chóp|lăng\s+trụ)\s*$", de[:dau], re.IGNORECASE)}
                if len(bases) == 1 and _cung_da_giac(list(next(iter(bases))), vertices):
                    return True
        return False
    if c.fn != "rectangle":
        return True
    for q in c.quotes:
        if _mat_cua_khoi_sau_cum(q, _HOP_CHU_NHAT, vertices):
            return True
        for dau, cuoi, phan in _tu_nhan(q):
            if not any(_cung_da_giac(p, vertices) for p in phan):
                continue
            # `ABCD là hình chữ nhật` / `hình chữ nhật ABCD`; giới hạn tại đúng token nhãn, không nhìn cả quote.
            if re.match(r"\s+(?:là\s+)?hình\s+chữ\s+nhật(?!\w)", q[cuoi:], re.IGNORECASE):
                return True
            if re.search(r"(?<!\w)hình\s+chữ\s+nhật\s*$", q[:dau], re.IGNORECASE):
                return True
    return False


def _co_mat(quotes: tuple[str, ...], mp: list[str], cho_day: bool = True) -> bool:
    """Mặt phẳng được nhắc: nhóm nhãn trùng tập điểm (`(ABC)`, `SAB`), hoặc — với mặt ĐÁY — chữ "đáy"."""
    if cho_day and any("đáy" in q.lower() for q in quotes):
        return True
    return any(set(p) == set(mp) for q in quotes for _a, _b, phan in _tu_nhan(q) for p in phan if len(p) >= 3)


def _co_doan(quotes: tuple[str, ...], seg: list[str]) -> bool:
    x, y = seg
    return any(any((p[i], p[i + 1]) in ((x, y), (y, x)) for i in range(len(p) - 1))
               for q in quotes for _a, _b, phan in _tu_nhan(q) for p in phan)


def _co_diem_rieng(quotes: tuple[str, ...], ten: str, mp: list[str] | None) -> bool:
    return any(ten in p and not (mp and set(p) == set(mp)) and len(p) <= 2
               for q in quotes for _a, _b, phan in _tu_nhan(q) for p in phan)


#: Phép BẰNG giữa nhãn đoạn và số (S1, run `hybrid-semantic-hardening`, nhóm B của phần dư): chỉ "=", "bằng", "là", "dài",
#: "có độ dài (bằng)" — không "≥ > ≈ ≠", "không bằng", "xấp xỉ", "tối đa", "lớn hơn".
_NOI_BANG = re.compile(r"\s*(?:=\s*(?-i:[A-Z][0-9]*'?[A-Z][0-9]*'?)\s*)*"           # chuỗi bằng "SA = SB = 3"
                       r"(?:(?:có\s+)?độ dài(?:\s+(?:=|bằng|là))?|=|bằng|là|dài)\s*", re.IGNORECASE)
#: Sau số, tới hết mệnh đề: chỉ đơn vị, rồi kết mệnh đề hay "và" — không "lần", "hoặc", "là sai", "khi …".
_DUOI_BANG = re.compile(r"\s*(?:(?:cm|dm|mm|m|đvđd)(?![\w'])|đơn vị(?:\s+độ dài)?(?!\w)|\((?:cm|dm|mm|m|đvđd|đơn vị[^()]*)\))?"
                        r"\s*(?:[.?!](?=\s|$)|[,;:)]|$|và(?!\w))", re.IGNORECASE)


def _gia_tri_la_phep_bang(de: str, vts: list[tuple[int, int]], seg: list[str]) -> bool:
    """Số neo sau nhãn đoạn `seg` (trong một quote) được nối với nhãn bằng một phép BẰNG và không bị bổ nghĩa sau nó — đọc
    trên ĐỀ, vì đuôi "hoặc SA = 4" / "là sai" / "khi M trùng S" thường nằm ngoài quote."""
    for dau, cuoi in vts:
        for a, b, phan in _tu_nhan(de[dau:cuoi]):
            if not any((p[i], p[i + 1]) in ((seg[0], seg[1]), (seg[1], seg[0])) for p in phan for i in range(len(p) - 1)):
                continue
            so = next((m for m in _SO.finditer(de, dau + b, cuoi) if _doc(m) is not None), None)
            if so and _NOI_BANG.fullmatch(de[dau + b:so.start()]) and _DUOI_BANG.match(de[so.end():]):
                return True
    return False


def _so_neo(quotes: tuple[str, ...], seg: list[str] | None) -> list[tuple[Fraction, bool]]:
    """Số căn theo nhãn đoạn: số ĐẦU TIÊN đứng sau nhãn `seg` trong mỗi quote có nhãn ấy."""
    if not seg:
        return []
    ra = []
    for q in quotes:
        qn = chuan_hoa(q)
        so = so_trong(qn)
        for dau, cuoi, phan in _tu_nhan(qn):
            if any((p[i], p[i + 1]) in ((seg[0], seg[1]), (seg[1], seg[0])) for p in phan for i in range(len(p) - 1)):
                sau = [(v, s) for vt, v, s in so if vt >= cuoi]
                if sau:
                    ra.append(sau[0])
                    break
    return ra


#: Luật PHÂN RÃ MỤC TIÊU của planner nhánh B (run `hybrid-goal-decomposition`, design option B slice 1): mục tiêu không có hàm
#: `ask_*` riêng → (hàm dựng ĐIỂM PHỤ, hàm hỏi) SẴN CÓ. Điểm phụ không có trong đề và không bao giờ là giả thiết: nguồn của
#: nó là chính câu hỏi; cổng chỉ nhận nó khi planner khai báo đúng luật (`_kiem_phu`). Nhánh A không khai báo được gì.
AUXILIARY_RULES = {"distance(point,line)": ("orthogonal_projection_line", "ask_length")}
#: "khoảng cách từ S đến (đường thẳng) BD": điểm và đường gắn vai trong CÙNG một cụm; cách nói khác ⇒ từ chối, không đoán.
_KHOANG_CACH_DIEM_DUONG = re.compile(
    r"khoảng cách\s+từ\s+(?:điểm\s+)?([A-Z][0-9]*'?)\s+(?:đến|tới)\s+(?:đường thẳng\s+)?([A-Z][0-9]*'?)([A-Z][0-9]*'?)(?![\w'])",
    re.IGNORECASE)
#: Câu hỏi khoảng cách điểm–đường: không gán giá trị ngay sau đường thẳng ("bằng 4", "không bằng 3", "khác 3"; "bằng bao nhiêu" vẫn là câu hỏi).
_GAN_GIA_TRI = re.compile(r"\s*(?:\w+\s+)?(?:bằng|=|là|khác|≠)\s*(?!bao\s+nhiêu|\?)\S", re.IGNORECASE)
_CHI_SO_DUOI = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")


def nhan_phu_da_dung(text: str, chu: str = "H") -> set[str]:
    """Nhãn chuỗi điểm phụ (`chu`, `chu`1, …) mà đề CÓ THỂ đang dùng — bảo thủ hơn `nhan_cua_de`: chữ `chu` đứng riêng hay
    dính chữ khác (ΔSHD, điểmH), kèm chỉ số thường / `_1` / chỉ số dưới `₁`. Bỏ qua khi nó mở đầu một từ thường (Hình, Hai)."""
    de, ra = chuan_hoa(text), set()
    for m in re.finditer(re.escape(chu), de):
        sau = de[m.end():]
        if sau[:1].islower():
            continue
        ra.add(chu)
        if n := re.match(r"_?([0-9₀-₉]+)", sau):
            ra.add(chu + n[1].translate(_CHI_SO_DUOI))
    return ra


def _kiem_phu(phu: tuple[dict, ...], calls: tuple[LoiGoi, ...], de: str, nhan: set[str]) -> set[str]:
    """Điểm phụ do planner khai: đúng luật, nhãn không trùng đề, hai lời gọi đúng hình dạng luật, câu hỏi nguồn có thật,
    không điều kiện/chứng minh/phủ định, và gắn đúng điểm + đường. Trả id các lời gọi đã kiểm (bỏ qua ở vòng thường).
    Nhãn phụ ở bất kỳ lời gọi nào KHÁC vẫn rơi vào `UNKNOWN_LABEL` của vòng thường."""
    theo_id = {c.id: c for c in calls}
    da: set[str] = set()
    chiem = nhan | nhan_phu_da_dung(de)
    nhan_da_khai: set = set()
    for d in phu:
        x, luat = d.get("label"), d.get("rule")
        if luat not in AUXILIARY_RULES:
            raise TuChoi("AUXILIARY_RULE_MISMATCH", f"điểm phụ {x}: luật {luat!r} không có trong bảng phân rã")
        if x in nhan_da_khai:
            raise TuChoi("AUXILIARY_RULE_MISMATCH", f"điểm phụ {x} được khai hai lần")
        nhan_da_khai.add(x)
        if x in chiem:
            raise TuChoi("AUXILIARY_LABEL_COLLISION", f"điểm phụ {x} trùng một nhãn của đề")
        dung, hoi = theo_id.get(d.get("construct")), theo_id.get(d.get("ask"))
        fn_dung, fn_hoi = AUXILIARY_RULES[luat]
        p, dt, qs = d.get("point"), list(d.get("line") or []), tuple(d.get("quotes") or ())
        if not (dung and hoi and dung.fn == fn_dung and hoi.fn == fn_hoi and dung.args.image == x
                and dung.args.point == p and dung.args.line == dt and hoi.args.segment == [p, x]
                and dung.quotes == hoi.quotes == qs and qs):
            raise TuChoi("AUXILIARY_RULE_MISMATCH", f"điểm phụ {x}: lời gọi không khớp luật {luat}",
                         tuple(i for i in (d.get("construct"), d.get("ask")) if i))
        ids = (dung.id, hoi.id)
        if lac := sorted(({p} | set(dt)) - nhan):
            raise TuChoi("UNKNOWN_LABEL", f"{hoi.id}: nhãn {lac} không có trong đề", ids)
        # Mỗi cụm "khoảng cách từ P đến XY" khớp: vai trò mệnh đề TẠI cụm (quote có thể tự mang "Nếu"), và câu chứa nó có HỎI.
        vai: list[str | None] = []
        hoi_that: list[bool] = []
        for q in qs:
            if (vt := _vi_tri(de, q)) is None:
                raise TuChoi("QUOTE_NOT_IN_SOURCE", f"{hoi.id}: đoạn {q!r} không có nguyên văn trong đề", ids)
            if _phu_dinh(de, vt[0], q):
                raise TuChoi("NEGATED_CLAUSE", f"{hoi.id}: {q!r} mang phủ định", ids)
            qn = chuan_hoa(q)
            s = de[:vt[0]] + qn + de[vt[1]:]                     # đề với quote ở dạng chuẩn hoá — vị trí nhất quán
            for m in _KHOANG_CACH_DIEM_DUONG.finditer(qn):
                if m[1] == p and [m[2], m[3]] in (dt, dt[::-1]):
                    dau, sau = vt[0] + m.start(), vt[0] + m.end()
                    vai.append(_vai_tro_tai(s, dau))                   # cùng bộ phân tích với câu hỏi thường
                    hoi_that.append(_duoc_hoi(s, dau, sau) and not _GAN_GIA_TRI.match(s[sau:]))
        if not vai:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{hoi.id}: câu hỏi không nói 'khoảng cách từ {p} đến {''.join(dt)}'", ids)
        if "GOAL" in vai:
            raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{hoi.id}: câu hỏi nằm trong điều phải chứng minh", ids)
        if "CONDITIONAL" in vai:
            raise TuChoi("CONDITIONAL_CLAUSE", f"{hoi.id}: câu hỏi nằm trong mệnh đề 'nếu … thì'", ids)
        if not all(hoi_that):
            raise TuChoi("NOT_ASKED_IN_SOURCE", f"{hoi.id}: câu chứa 'khoảng cách từ {p} đến {''.join(dt)}' không hỏi nó "
                         "(không có từ hỏi, hoặc đã gán giá trị) — không trả lời điều đề không hỏi", ids)
        da |= set(ids)
    return da


# ── MỘT bộ phân tích mệnh đề cho tiền đề, câu hỏi thường và điểm phụ (review 2, run `hybrid-slice-review`) ────────────
#: Mở đầu mệnh đề ĐIỀU KIỆN. "Khi đó" là tiền đề (nối câu), không phải điều kiện.
#: "khi" + động từ dựng ("khi cắt bởi", "khi dựng", "khi quay") là lời dẫn phép dựng, không phải điều kiện.
_DIEU_KIEN = re.compile(r"(?<!\w)(?:nếu|giả sử|giả thiết rằng|trong trường hợp|với điều kiện|trừ khi"
                        r"|khi(?!\s+(?:đó|cắt|dựng|quay|chiếu))"
                        # S1, nhóm A: giả định / tường thuật — không phải dữ kiện của đề
                        r"|hễ|xét trường hợp|cho rằng|muốn|khẳng định|nói rằng|nghĩ rằng"
                        r"|giả định|coi như|cho là|theo bạn)(?!\w)", re.IGNORECASE)
_THI = re.compile(r"(?<!\w)thì(?!\w)", re.IGNORECASE)
#: Mệnh đề HỎI một quan hệ có/không — không bao giờ là dữ kiện.
_HOI_QUAN_HE = re.compile(r"(?<!\w)(?:phải chăng|có phải|kiểm tra xem|hay không|hay chưa)(?!\w)|(?<!câu )(?<!\w)hỏi(?!\w)"
                          r"|(?<!\w)không\s*\?", re.IGNORECASE)
#: Động từ hỏi đứng TRƯỚC đối tượng trong cùng mệnh đề …
_DONG_TU_HOI = re.compile(r"(?<!\w)(?:tính|tìm|xác định)(?!\w)|(?<!câu )(?<!\w)hỏi(?!\w)", re.IGNORECASE)
#: … hoặc "bao nhiêu / mấy / ?" đứng SAU nó.
_HOI_SAU = re.compile(r"bao\s+nhiêu|(?<!\w)mấy(?!\w)|\?", re.IGNORECASE)
#: Câu hỏi CÓ/KHÔNG về đối tượng ("V có vượt quá 5 không?") hỏi một quan hệ, không hỏi giá trị — trừ khi có "bao nhiêu / mấy".
_CO_KHONG = re.compile(r"(?<!\w)(?:phải chăng|có phải|hay không|hay chưa|phải không)(?!\w)|(?<!\w)(?:không|chưa)\s*\?",
                       re.IGNORECASE)
#: Đối tượng bị GÁN giá trị: một từ nối gán theo sau là một số ("bằng 4", "= √17", "là 3", "có giá trị 4"). Một số đứng riêng
#: ("làm tròn đến 2 chữ số") không phải phép gán.
_GIA_TRI = re.compile(r"(?<!\w)(?:bằng|là|khác|có giá trị)(?!\w)\s*(?:\d|√|π)|[=≠]\s*(?:\d|√|π)", re.IGNORECASE)
#: Phần giải thích dữ kiện đi kèm câu hỏi ("biết SA = 3", "có SA = 3", "với a = 2") không phải gán cho đối tượng hỏi.
_DUNG_GAN = re.compile(r"(?<!\w)(?:biết|với|cho|khi|nếu|trong đó|có(?!\s+(?:giá\s+trị|bằng|là|lớn|nhỏ|vượt|khác)))(?!\w)",
                       re.IGNORECASE)
#: Giữa động từ hỏi và đối tượng (hay ngay sau đối tượng): đối tượng KHÔNG còn là tân ngữ được hỏi — nó là tham chiếu
#: ("theo", "tỉ số giữa … và …"), điều kiện cực trị ("sao cho … nhỏ nhất"), hay chú thích ("ở đây", "trong đó", "gấp").
_CHAN_TAN_NGU = re.compile(r"(?<!\w)(?:theo|tỉ số|tỷ số|tổng|hiệu|sao cho|ở đây|trong đó|gấp|lớn hơn|nhỏ hơn|bé hơn"
                           r"|lớn nhất|nhỏ nhất|bé nhất)(?!\w)", re.IGNORECASE)


def _bien_cau(de: str, p: int) -> tuple[int, int]:
    het = re.search(r"[.!?](?=\s|$)", de[p:])
    return _cau_chua(de, p), p + het.end() if het else len(de)


def _bien_menh_de(de: str, p: int) -> tuple[int, int]:
    """Mệnh đề chứa `p`: phần câu giữa hai dấu , ; : gần nhất."""
    a, b = _bien_cau(de, p)
    truoc = [m.end() for m in re.finditer(r"[,;:]", de[a:p])]
    sau = re.search(r"[,;:]", de[p:b])
    return a + (truoc[-1] if truoc else 0), p + sau.start() if sau else b


def _vai_tro_tai(de: str, p: int) -> str | None:
    """Vai trò mệnh đề TẠI vị trí `p`: `GOAL` (sau chứng minh/CMR/chứng tỏ, chưa có "biết"), `CONDITIONAL` (sau một từ mở
    điều kiện trong câu, hoặc đứng trước "thì" của câu), `QUESTION` (mệnh đề hỏi có/không), hay None (tiền đề)."""
    a, b = _bien_cau(de, p)
    truoc = de[a:p].lower()
    # điểm KẾT của từ mở mục tiêu gần nhất ("tìm điều kiện" tự chứa động từ "tìm" — chỉ xét động từ hỏi SAU nó)
    muc = max(((i + len(m)) for m in _MUC_TIEU if (i := truoc.rfind(m)) >= 0), default=-1)
    # "Chứng minh X và tính Y": Y đứng sau một động từ hỏi riêng — một vế hỏi, không phải điều phải chứng minh.
    if muc >= 0 and "biết" not in truoc[muc:] and not _DONG_TU_HOI.search(truoc[muc:]):
        return "GOAL"
    ma, mb = _bien_menh_de(de, p)
    if _DIEU_KIEN.search(truoc) or _THI.search(de[p:b]) or _DIEU_KIEN_SAU.search(de[p:mb]):
        return "CONDITIONAL"
    # mệnh đề hỏi có/không, hay mọi mệnh đề kết bằng "?" ("Tại sao …?", "Liệu … ?") — S1, nhóm A
    intro = list(_DUNG_GAN.finditer(truoc))
    local_given = (bool(intro) and intro[-1].group().lower() in ("biết", "với", "cho", "trong đó", "có")
                   and bool(_DONG_TU_HOI.search(truoc[:intro[-1].start()]) or _HOI_SAU.search(truoc[:intro[-1].start()]))
                   and not _DONG_TU_HOI.search(truoc[intro[-1].end():]))
    if (_HOI_QUAN_HE.search(de[ma:mb]) or de[ma:mb].rstrip().endswith("?") and not local_given
            or re.search(r"(?<!\w)có(?!\w).*(?<!\w)không\s*[.?!]?\s*$", de[ma:mb], re.IGNORECASE)):
        return "QUESTION"
    return None


def _duoc_hoi(de: str, p: int, het: int) -> bool:
    """Đối tượng ở `de[p:het]` có được HỎI không:
    - một động từ hỏi đứng TRƯỚC nó trong câu, sau dấu hiệu dữ kiện cuối cùng (biết/cho/với …) — liệt kê "Tính V, độ dài SC và
      góc …" chung một động từ; hoặc "bao nhiêu / mấy / ?" đứng SAU nó trong cùng mệnh đề;
    - và ngay sau đối tượng (trước phần "biết/có/với …") không có một giá trị gán cho nó."""
    a, _b = _bien_cau(de, p)
    ma, mb = _bien_menh_de(de, p)
    sau = de[het:mb]
    dung = _DUNG_GAN.search(sau)
    gan = sau[:dung.start()] if dung else sau
    if (so := _GIA_TRI.search(gan)) and not _HOI_SAU.search(gan[:so.start()]):
        return False
    if _CO_KHONG.search(gan) and not re.search(r"bao\s+nhiêu|(?<!\w)mấy(?!\w)", gan, re.IGNORECASE):
        return False
    truoc = de[a:p]
    moc_du_kien = [m.end() for m in _DUNG_GAN.finditer(truoc)]
    dong_tu = list(_DONG_TU_HOI.finditer(truoc[moc_du_kien[-1] if moc_du_kien else 0:]))
    # Động từ hỏi chỉ chi phối đối tượng khi giữa chúng không có từ chặn tân ngữ (second re-verification, N2).
    qua_dong_tu = bool(dong_tu) and not _CHAN_TAN_NGU.search(truoc[(moc_du_kien[-1] if moc_du_kien else 0) + dong_tu[-1].end():])
    qua_hoi_sau = bool(_HOI_SAU.search(gan)) and not _CHAN_TAN_NGU.search(gan) and not _CHAN_TAN_NGU.search(de[ma:p])
    return qua_dong_tu or qua_hoi_sau


def _cum_hoi(c: LoiGoi, de: str, dau: int, cuoi: int, calls: tuple[LoiGoi, ...]) -> list[tuple[int, int]]:
    """CỤM ĐỐI TƯỢNG của câu hỏi trong quote `de[dau:cuoi]` (S1, run `hybrid-semantic-hardening`): cụm theo văn phạm của
    hàm (`_CUM_HOI`) mà toán hạng ĐÚNG là toán hạng của lời gọi — "khoảng cách từ A đến (SBC)" không phải cụm của câu hỏi
    khoảng cách từ S đến (ABCD); "thể tích khối chóp M.ABCD" không phải của khối S.ABCD. (đầu, cuối) trong `de`."""
    khoi = _khoi_cua_loi_goi(calls)
    return [(m.start(), m.end()) for mau, buoc in _CUM_HOI.get(c.fn, ())
            for m in mau.finditer(de, dau, cuoi) if buoc(m, c.args, khoi)]


def _bo_cum(s: str) -> str:
    """Xoá mọi cụm hỏi (của bất kỳ hàm nào) — phần còn lại là chữ NẰM NGOÀI các đối tượng được liệt kê. Cụm dài xoá trước,
    không chồng lấn: "SC" trần không được cắt vỡ cụm "góc giữa SC và (ABC)"."""
    cum = sorted(((m.start(), m.end()) for ds in _CUM_HOI.values() for mau, _b in ds for m in mau.finditer(s) if m.end() > m.start()),
                 key=lambda x: x[0] - x[1])
    bo = [False] * len(s)
    for a, b in cum:
        if not any(bo[a:b]):
            bo[a:b] = [True] * (b - a)
    return "".join(" " if x else ch for ch, x in zip(s, bo))


def _hoi_dung_cum(de: str, a: int, b: int) -> bool:
    """Cụm `de[a:b]` là ĐÚNG đối tượng được hỏi, nguyên vẹn (S1). Ngoài `_duoc_hoi` (có hỏi, không gán giá trị, không phải
    câu có/không), văn phạm ĐÓNG quanh cụm:
    - trước cụm (từ động từ hỏi cuối cùng; không có động từ thì từ đầu mệnh đề) chỉ có từ nối và các cụm hỏi khác — "nửa",
      "bình phương", "hình chiếu của", "giá trị lớn nhất của", "SC +" không lọt;
    - sau cụm tới hết câu chỉ có các cụm hỏi khác, "bằng / là bao nhiêu", "?", "theo a", một ngoặc chú thích, rồi kết câu,
      lời dẫn dữ kiện (biết, với, cho, trong đó) hay việc kế tiếp (rồi, sau đó) — "khi M thay đổi", "song song với CD",
      "lên đáy" không lọt."""
    if not _duoc_hoi(de, a, b):
        return False
    c0, c1 = _bien_cau(de, a)
    truoc = de[c0:a]
    moc = [m.end() for m in _DUNG_GAN.finditer(truoc)]
    dong_tu = list(_DONG_TU_HOI.finditer(truoc, moc[-1] if moc else 0))
    giua = truoc[dong_tu[-1].end():] if dong_tu else de[_bien_menh_de(de, a)[0]:a]
    return bool(_GIUA_HOP_LE.fullmatch(_bo_cum(giua)) and _SAU_HOP_LE.match(_bo_cum(de[b:c1])))


def _kiem_cau_hoi(c: LoiGoi, de: str, vts: list[tuple[int, int]], calls: tuple[LoiGoi, ...]) -> None:
    """Câu hỏi `ask_*` chỉ được trả lời khi đề HỎI đúng đối tượng ấy: có CỤM gọi đúng toán hạng của lời gọi (`_cum_hoi`),
    cụm ấy được hỏi nguyên vẹn (`_hoi_dung_cum`), và vai trò mệnh đề đọc TẠI cụm được hỏi không là điều phải chứng minh /
    điều kiện. Nhãn của đối tượng nhắc lại trong một vế chứng minh ("Chứng minh SC ⊥ BD và tính SC") không chặn câu hỏi."""
    cum = [m for dau, cuoi in vts for m in _cum_hoi(c, de, dau, cuoi, calls)]
    if not cum:
        raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: {c.quote!r} không gọi tên đúng đối tượng của {c.fn} "
                     f"{c.args.model_dump()} — không trả lời câu hỏi về đối tượng khác", (c.id,))
    hoi = [p for p, h in cum if _hoi_dung_cum(de, p, h)]
    if not hoi:
        raise TuChoi("NOT_ASKED_IN_SOURCE", f"{c.id}: {c.quote!r} không hỏi đối tượng này nguyên vẹn (không có từ hỏi gắn với "
                     "nó, đã gán giá trị, hay bị bổ nghĩa / đặt điều kiện) — không trả lời điều đề không hỏi", (c.id,))
    vai = {_vai_tro_tai(de, p) for p in hoi}
    if vai & {None, "QUESTION"}:                       # mệnh đề hỏi ("Hỏi … bằng bao nhiêu?") là đúng chỗ của một câu hỏi
        return
    if "GOAL" in vai:
        raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{c.id}: đối tượng hỏi nằm trong điều phải chứng minh", (c.id,))
    raise TuChoi("CONDITIONAL_CLAUSE", f"{c.id}: đối tượng hỏi nằm trong mệnh đề điều kiện", (c.id,))


def _moc_menh_de(c: LoiGoi, de: str, dau: int, cuoi: int) -> list[int]:
    """Các mốc của lời gọi trong quote `de[dau:cuoi]`: đầu quote, mỗi chỗ có từ khoá vị từ của hàm, mỗi từ nhãn mang nhãn của
    lời gọi, và cụm "X là giao điểm/hình chiếu" của phép dựng. Vai trò mệnh đề đọc tại MỌI mốc."""
    doan, moc = de[dau:cuoi], [dau]
    for nhom in c.spec.keywords:
        for k in nhom:
            mau, co = (k[3:], 0) if k.startswith("re:") else (re.escape(k), re.IGNORECASE)
            moc += [dau + m.start() for m in re.finditer(mau, doan, co)]
    nhan = nhan_cua_loi_goi(c)
    moc += [dau + a for a, _b, phan in _tu_nhan(doan) if any(n in nhan for p in phan for n in p)]
    if c.fn in ("intersect_line_line", "intersect_line_plane", "orthogonal_projection_line", "orthogonal_projection"):
        moc += [dau + m.start() for m in re.finditer(r"[A-Z][0-9]*'?\s+là\s+(?:giao điểm|hình chiếu)|[Hh]ình chiếu", doan)]
    return moc


def kiem_nguon(calls: tuple[LoiGoi, ...], text: str, auxiliary: tuple[dict, ...] = ()) -> None:
    """Cổng nguồn tất định — xem docstring module. Ném `TuChoi` ở lời gọi đầu tiên hỏng (theo thứ tự id).
    `auxiliary`: điểm phụ planner nhánh B khai (`AUXILIARY_RULES`); nhánh A không truyền ⇒ mọi nhãn phải có trong đề."""
    de = chuan_hoa(text)
    nhan = nhan_cua_de(de)
    phu = _kiem_phu(tuple(auxiliary), calls, de, nhan)
    for c in sorted(calls, key=lambda c: c.id):
        if c.id in phu:
            continue
        vts = []
        for q in c.quotes:
            if (vt := _vi_tri(de, q)) is None:
                raise TuChoi("QUOTE_NOT_IN_SOURCE", f"{c.id}: đoạn {q!r} không có nguyên văn trong đề", (c.id,))
            vts.append(vt)
        if lac := sorted(nhan_cua_loi_goi(c) - nhan):
            raise TuChoi("UNKNOWN_LABEL", f"{c.id}: nhãn {lac} không có trong đề", (c.id,))
        if c.spec.kind == "escape":
            continue
        if c.spec.kind == "ask":
            _kiem_cau_hoi(c, de, vts, calls)
        if c.spec.kind != "ask":
            for (dau, _c), q in zip(vts, c.quotes):
                # A quote may carry its own "Nếu" / "Chứng minh": read the role where the predicate and the call's labels
                # are, not only at the start of the quote (ISSUE-ARCH-GATE-CLAUSE-ROLE-INSIDE-QUOTE).
                roles = {_vai_tro_tai(de, pos) for pos in _moc_menh_de(c, de, dau, _c)}
                if "GOAL" in roles:
                    raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{c.id}: {q!r} là điều phải chứng minh, không phải dữ kiện", (c.id,))
                if "CONDITIONAL" in roles:
                    raise TuChoi("CONDITIONAL_CLAUSE", f"{c.id}: {q!r} nằm trong mệnh đề điều kiện — không phải dữ kiện", (c.id,))
                if "QUESTION" in roles:
                    raise TuChoi("QUESTION_CLAUSE_NOT_PREMISE", f"{c.id}: {q!r} nằm trong một câu hỏi — không phải dữ kiện", (c.id,))
        if any(_phu_dinh(de, dau, q) for (dau, _c), q in zip(vts, c.quotes)):
            raise TuChoi("NEGATED_CLAUSE", f"{c.id}: mệnh đề {c.quote!r} mang phủ định — không làm dữ kiện {c.fn}", (c.id,))
        if c.fn == "regular_polygon":
            if not _co_tu(c.quotes, ("đều", "hình vuông")) and not any(_LAP_PHUONG.search(q) for q in c.quotes):
                raise TuChoi("PREDICATE_NOT_IN_QUOTE", f"{c.id}: regular_polygon thiếu predicate hình đều", (c.id,))
            if not _co_doi_tuong_hinh(c, de):
                raise TuChoi("OBJECT_NOT_IN_QUOTE", f"{c.id}: cụm lập phương không gọi đúng mặt {c.args.vertices}", (c.id,))
        if c.fn == "rectangle":
            if not any(_CHU_NHAT.search(q) for q in c.quotes):
                raise TuChoi("PREDICATE_NOT_IN_QUOTE", f"{c.id}: rectangle thiếu predicate chữ nhật", (c.id,))
            if not _co_doi_tuong_hinh(c):
                raise TuChoi("OBJECT_NOT_IN_QUOTE", f"{c.id}: cụm chữ nhật không gọi đúng đa giác {c.args.vertices}", (c.id,))
        for nhom in c.spec.keywords:
            if not _co_tu(c.quotes, nhom):
                raise TuChoi("PREDICATE_NOT_IN_QUOTE", f"{c.id}: {c.fn} cần một trong {list(nhom)} trong {c.quote!r}", (c.id,))
        if c.fn == "prism" and c.args.right and not _co_tu(c.quotes, ("đứng", "đều", "hình hộp", "lập phương")):
            raise TuChoi("PREDICATE_NOT_IN_QUOTE", f"{c.id}: lăng trụ đứng cần 'đứng'/'đều' trong {c.quote!r}", (c.id,))
        for f in c.spec.plane_fields:
            if not _co_mat(c.quotes, getattr(c.args, f), cho_day=f != "face"):
                raise TuChoi("PLANE_NOT_IN_QUOTE", f"{c.id}: mặt phẳng {getattr(c.args, f)} không được nhắc trong {c.quote!r}", (c.id,))
        for f in c.spec.segment_fields:
            if not _co_doan(c.quotes, getattr(c.args, f)):
                raise TuChoi("ROLE_NOT_IN_QUOTE", f"{c.id}: đoạn {''.join(getattr(c.args, f))} không được nhắc trong {c.quote!r}", (c.id,))
        for f in c.spec.point_fields:
            mp = getattr(c.args, "plane", None)
            if not _co_diem_rieng(c.quotes, getattr(c.args, f), mp):
                raise TuChoi("ROLE_NOT_IN_QUOTE", f"{c.id}: điểm {getattr(c.args, f)} ({f}) không được nhắc trong {c.quote!r}", (c.id,))
        if c.fn in ("intersect_line_line", "intersect_line_plane", "orthogonal_projection_line"):
            if not construction_source_bound(c, de):
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: vai trò điểm và toán hạng dựng không khớp nguồn", (c.id,))
        if c.fn in ("section", "ask_section_area", "intersection_line") and not mat_cat_dung_nguon(c, calls):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: mặt phẳng / khối của {c.fn} không phải cái mà {c.quote!r} gọi tên",
                         (c.id,))
        if c.fn == "orthogonal_projection" and c.args.point != c.args.image:
            if not construction_source_bound(c, de):
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: vai trò ảnh và điểm chiếu không khớp nguồn", (c.id,))
        for f in c.spec.value_fields:
            if (v := getattr(c.args, f)) is None:
                continue
            gt = doc_so(v)
            neo = _so_neo(c.quotes, getattr(c.args, "segment", None))
            if neo:
                if gt not in neo:
                    raise TuChoi("UNGROUNDED_VALUE", f"{c.id}: giá trị {v} không phải số đứng sau nhãn đoạn trong {c.quote!r}", (c.id,))
                if not _gia_tri_la_phep_bang(de, vts, getattr(c.args, "segment")):
                    raise TuChoi("UNGROUNDED_VALUE", f"{c.id}: {c.quote!r} không phát biểu {''.join(c.args.segment)} BẰNG {v} "
                                 "(bất đẳng thức, phủ định, xấp xỉ, bội số, tuyển hay điều kiện) — không làm dữ kiện", (c.id,))
                continue
            so = [(x, s) for q in c.quotes for _vt, x, s in so_trong(q)]
            if len(so) != 1:
                raise TuChoi("AMBIGUOUS_VALUE_QUOTE", f"{c.id}: quote cho ô số phải chứa đúng MỘT số, có {len(so)}", (c.id,))
            if gt != so[0]:
                raise TuChoi("UNGROUNDED_VALUE", f"{c.id}: giá trị {v} không phải số trong {c.quote!r}", (c.id,))

    _kiem_du_kien_cau_hoi(calls, de)


def _kiem_du_kien_cau_hoi(calls: tuple[LoiGoi, ...], de: str) -> None:
    """Source coverage, not a second fact state: local claims must match validated calls before engine verification.

    Read the whole question context, including text outside the model's quote. Only closed source spans are covered;
    an unread modifier never authorizes using the old figure. No local claim overwrites a premise.
    """
    # An explicit escape is unconditionally refused by the engine before any construction. Preserve OUT_OF_SCOPE.
    if any(c.fn == "unsupported" for c in calls):
        return
    from ..semantic_program.shape_constraint import doc_rang_buoc

    request_verb = re.compile(_DONG_TU_HOI.pattern + r"|(?<!\w)dựng(?!\w)", re.I)
    rb = doc_rang_buoc(de)
    lengths = [m for m in _DO_DAI_CUC_BO.finditer(de) if _doc(m) is not None and _DUOI_BANG.match(de[m.end():])]

    def segments(m):
        return [p for _x, _y, parts in _tu_nhan(de[m.start():m.start("number")]) for p in parts if len(p) == 2]

    def unit(m):
        tail = de[m.end():]
        found = re.match(r"\s*\(?\s*(cm|dm|mm|m|đvđd)(?![\w'])", tail, re.I)
        return found[1].lower() if found else ""

    questions = {_bien_cau(de, m.start()) for m in request_verb.finditer(de)}
    for c in calls:
        if c.spec.kind == "ask":
            for q in c.quotes:
                if (vt := _vi_tri(de, q)) is not None:
                    questions |= {_bien_cau(de, p) for p, h in _cum_hoi(c, de, *vt, calls) if _hoi_dung_cum(de, p, h)}
                    questions |= {_bien_cau(de, m.start()) for m in _KHOANG_CACH_DIEM_DUONG.finditer(de, *vt)
                                  if _hoi_dung_cum(de, m.start(), m.end())}
    request_contexts = set(questions)
    construction_contexts = {_bien_cau(de, vt[0]) for c in calls
                             if (c.spec.kind == "construct" and c.fn not in ("pyramid", "regular_pyramid", "prism"))
                             or c.fn == "orthogonal_projection" for q in c.quotes
                             if (vt := _vi_tri(de, q)) is not None}
    # Derived construction clauses already have their own binding gate. Context applies regardless of request wording.
    questions |= construction_contexts
    request_contexts |= {_bien_cau(de, vt[0]) for c in calls if c.fn in ("section", "intersection_line") for q in c.quotes
                         if (vt := _vi_tri(de, q)) is not None}
    first_request = min((a for a, _b in request_contexts), default=min((a for a, _b in construction_contexts), default=len(de)))
    questions |= {_bien_cau(de, p) for p in (0, *(m.end() for m in re.finditer(r"[.!?]\s+", de)))
                  if first_request <= p < len(de)}
    for start, end in sorted(questions):
        phrases = [(m.start(), m.end()) for rules in _CUM_HOI.values() for pattern, _bind in rules
                   for m in pattern.finditer(de, start, end) if _hoi_dung_cum(de, m.start(), m.end())]
        phrases += [(m.start(), m.end()) for m in _KHOANG_CACH_DIEM_DUONG.finditer(de, start, end)
                    if _hoi_dung_cum(de, m.start(), m.end())]
        if _DIEU_KIEN.search(de, start, end):
            raise TuChoi("CONDITIONAL_CLAUSE", "ngữ cảnh câu hỏi có giả thiết điều kiện; chưa hỗ trợ thay phạm vi")
        masked = list(de[start:end])
        for a, b in phrases:
            masked[a - start:b - start] = " " * (b - a)
        assertions = [r.span for r in rb] + [m.span() for m in lengths]
        object_ends = [b for _a, b in phrases] + [m.end() for pattern in (*_CAT_BOI, _GIAO_TUYEN)
                                               for m in pattern.finditer(de, start, end)]
        markers = [start + m.end() for m in _DUNG_GAN.finditer("".join(masked))
                   if m.group().lower() not in ("khi", "nếu")
                   and not any(a <= start + m.start() < b for a, b in assertions)
                   and (m.group().lower() != "với" or any(p <= start + m.start()
                        and not de[p:start + m.start()].strip(" ,;:") for p in (start, *object_ends)))]
        stops = sorted({a for a, _b in phrases} | {m.start() for m in request_verb.finditer(de, start, end)} | {end})
        fragments = [(a, next(p for p in stops if p >= a)) for a in markers]
        if not phrases and not request_verb.search(de, start, end) and (start, end) not in construction_contexts and not fragments:
            fragments.append((start, end))
        first = min(stops)
        prefix = de[start:first]
        discourse = (_GIUA_HOP_LE.fullmatch(prefix) or re.fullmatch(r"\s*khi đó\s*,?\s*", prefix, re.I)
                     or any(word in prefix.lower() for word in _MUC_TIEU))
        if start < first < end and not markers and not discourse and _tu_nhan(prefix):
            fragments.append((start, first))
        for a, b in fragments:
            # Extraction may omit an original shape fact while keeping a local replacement. Preserve source authority.
            for original in rb:
                if (_vai_tro_tai(de, original.span[0]) in ("GOAL", "CONDITIONAL", "QUESTION")
                        or _phu_dinh(de, original.span[0], de[slice(*original.span)])):
                    continue
                if not any(_rang_buoc_cuc_bo_khop(original, c) for c in calls):
                    raise TuChoi("QUESTION_LOCAL_GIVEN_UNVERIFIED", "giả thiết hình dạng gốc chưa được bảo toàn; không thay mô hình")
            residue = list(de[a:b])
            found = False
            for m in _DO_DAI_CUC_BO.finditer(de, a, b):
                value = _doc(m)
                tail = _DUOI_BANG.match(de[m.end():])
                if value is None or tail is None:
                    continue
                for segment in segments(m):
                    candidates = _nguon_do_dai_cuc_bo(calls, segment)
                    for original in lengths:
                        if (_vai_tro_tai(de, original.start()) in ("GOAL", "CONDITIONAL", "QUESTION")
                                or not any(set(p) == set(segment) for p in segments(original))):
                            continue
                        if _doc(original) != value and not any(v == _doc(original) for v, _cid in candidates):
                            raise TuChoi("QUESTION_LOCAL_GIVEN_CONFLICT",
                                         "dữ kiện cục bộ khác dữ kiện gốc của đề; chưa hỗ trợ ghi đè phạm vi giả thiết")
                        if unit(m) and unit(original) != unit(m):
                            raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED", "đơn vị của dữ kiện cục bộ chưa khớp nguồn; chưa đổi đơn vị")
                    if not any(v == value for v, _cid in candidates):
                        code = "QUESTION_LOCAL_GIVEN_CONFLICT" if candidates else "QUESTION_LOCAL_GIVEN_UNVERIFIED"
                        raise TuChoi(code, "dữ kiện độ dài trong câu hỏi chưa khớp giả thiết đã xác thực; không dùng mô hình cũ",
                                     tuple(cid for _v, cid in candidates))
                last = min(b, m.end() + tail.end())
                residue[m.start() - a:last - a] = " " * (last - m.start())
                found = True
            for r in rb:
                if not (a <= r.span[0] < r.span[1] <= b):
                    continue
                if not any(_rang_buoc_cuc_bo_khop(r, c) for c in calls):
                    raise TuChoi("QUESTION_LOCAL_GIVEN_UNVERIFIED",
                                 f"dữ kiện {r.kind} trong câu hỏi chưa có giả thiết tương ứng đã xác thực")
                x, y = r.span
                residue[x - a:y - a] = " " * (y - x)
                found = True
            remaining = "".join(residue)
            if (not found and remaining.strip(" ,;:.?!")) or not _NOI_DU_KIEN_CUC_BO.fullmatch(remaining):
                raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                             "phần dữ kiện/đổi giả thiết trong câu hỏi chưa được đọc trọn; không dùng mô hình cũ")


def _nguon_do_dai_cuc_bo(calls: tuple[LoiGoi, ...], segment: list[str]) -> list[tuple[tuple[Fraction, bool], str]]:
    """Direct lengths and canonical polygon sides, the same authorities engine.do_dai uses; no layout inference."""
    values = []
    for c in calls:
        if c.fn == "segment_length" and set(c.args.segment) == set(segment):
            values.append((doc_so(c.args.value), c.id))
        if c.fn == "regular_polygon" and c.args.side is not None:
            vertices = c.args.vertices
            if any(set(segment) == {v, vertices[(i + 1) % len(vertices)]} for i, v in enumerate(vertices)):
                values.append((doc_so(c.args.side), c.id))
    return values


def _rang_buoc_cuc_bo_khop(r: Any, c: LoiGoi) -> bool:
    """Reuse source-reader predicates; calls remain the only construction assumptions, engine checks them afterwards."""
    from ..geometry.radical import display
    from ..semantic_program.source_entities import dinh_danh_thuc_the

    def ids(xs):
        return tuple(dinh_danh_thuc_the(x)[0] for x in xs)
    a, e = c.args, r.entities
    if r.kind == "pyramid" and c.fn in ("pyramid", "regular_pyramid"):
        return ids([a.apex]) == e[:1] and _cung_da_giac(list(ids(a.base)), list(e[1:]))
    if r.kind in ("regular_square_pyramid", "regular_triangular_pyramid", "regular_hexagonal_pyramid") and c.fn == "regular_pyramid":
        return ids([a.apex]) == e[:1] and _cung_da_giac(list(ids(a.base)), list(e[1:]))
    if r.kind == "line_perp_plane" and c.fn == "perpendicular_line_plane":
        return set(ids(a.line)) == set(e[:2]) and _cung_mat(frozenset(e[2:]), list(ids(a.plane)))
    if r.kind == "line_perp_line" and c.fn in ("perpendicular_lines", "right_angle"):
        pair = (a.line1, a.line2) if c.fn == "perpendicular_lines" else ([a.vertex, a.rays[0]], [a.vertex, a.rays[1]])
        return {frozenset(ids(x)) for x in pair} == {frozenset(e[:2]), frozenset(e[2:])}
    if r.kind in ("base_square", "base_equilateral", "base_regular_hexagon") and c.fn == "regular_polygon":
        n = {"base_square": 4, "base_equilateral": 3, "base_regular_hexagon": 6}[r.kind]
        return (len(a.vertices) == n and _cung_da_giac(list(ids(a.vertices)), list(e))
                and (r.value is None or a.side is not None and doc_so(display(r.value)) == doc_so(a.side)))
    if r.kind == "base_rectangle" and c.fn == "rectangle":
        return _cung_da_giac(list(ids(a.vertices)), list(e))
    return False


#: Một mặt phẳng toán hạng như đề viết: nhóm ≥ 3 nhãn (có hoặc không ngoặc, "mặt phẳng"), hay "(mặt) đáy".
#: Nhãn phân biệt hoa thường dù cả mẫu không phân biệt: "qua" không phải một mặt phẳng.
_NHOM_NHAN = r"(?-i:[A-Z][0-9]*'?(?:[A-Z][0-9]*'?){2,})"
_MAT_TOAN_HANG = (r"(?:(?:hai|2|các)\s+mặt phẳng\s+)?(?:(?:mặt phẳng|mp)\s*)?"
                  r"(?:\((" + _NHOM_NHAN + r")\)|(" + _NHOM_NHAN + r")|(?:mặt\s+)?(đáy))(?![\w'])")
#: Cụm vai trò gọi tên MẶT CẮT của một thiết diện. "song song với …" / "vuông góc với …" là phép dựng khác — không gắn.
#: Cụm danh từ khối đứng giữa "thiết diện của" và "với (P)": "hình chóp S.ABCD", "khối lăng trụ đứng ABC.A'B'C'"…
_KHOI_NGU = (r"(?:(?:hình|khối)\s+(?:chóp|lăng trụ|lập phương|hộp|tứ diện)(?:\s+(?:đứng|đều|tam giác|tứ giác|chữ nhật|lục giác))*\s+)?"
             r"(?:(?-i:[A-Z][0-9]*'?(?:[A-Z][0-9]*'?)*(?:\.[A-Z][0-9]*'?(?:[A-Z][0-9]*'?)*)?)\s+)?")
#: Đầu mệnh đề (đầu đề, sau . ; : ,) — "(P) cắt …" chỉ khi (P) là CHỦ NGỮ của mệnh đề (second re-verification, N1).
_DAU_MENH_DE = r"(?:^|(?<=[.;:,])|(?<=[.;:,]\s))\s*"
_CAT_BOI = [re.compile(p, re.IGNORECASE) for p in (
    r"(?:cắt bởi|tạo bởi)\s+" + _MAT_TOAN_HANG,
    r"thiết diện\s+(?:của\s+)?" + _KHOI_NGU + r"với\s+" + _MAT_TOAN_HANG,
    r"(?<!\w)do\s+" + _MAT_TOAN_HANG + r"\s+cắt(?!\w)",
    _DAU_MENH_DE + _MAT_TOAN_HANG + r"\s+cắt\s+(?:hình|khối)(?:[^.;]|\.(?=[A-Z]))*?theo\s+(?:một\s+)?thiết diện",
)]
_GIAO_TUYEN = re.compile(r"giao tuyến\s+(?:của\s+)?" + _MAT_TOAN_HANG + r"\s+(?:và|với)\s+" + _MAT_TOAN_HANG, re.IGNORECASE)

# ── S1: CỤM ĐỐI TƯỢNG của câu hỏi, buộc toán hạng (run `hybrid-semantic-hardening`) ────────────────────────────────────
# Văn phạm ĐÓNG: mỗi hàm `ask_*` một vài cụm danh từ, toán hạng là nhóm có tên (điểm, đoạn, mặt, khối). Cụm không khớp ⇒
# từ chối; không đoán. Nhãn phân biệt hoa thường, phần chữ thì không.
_P1 = r"(?-i:[A-Z][0-9]*'?)"

# Same label, equality and exact-number grammars as the source gate; every segment in a chain needs coverage.
_DO_DAI_CUC_BO = re.compile(rf"(?<![\w']){_P1}{_P1}(?![\w']){_NOI_BANG.pattern}(?P<number>{_SO.pattern})", re.IGNORECASE)
_NOI_DU_KIEN_CUC_BO = re.compile(r"[\s,;:.?!]*(?:(?:biết|rằng|với|cho|trong đó|có|và|cạnh|độ dài|đoạn thẳng)(?!\w)[\s,;:.?!]*)*",
                                 re.IGNORECASE)


def _mat_cum(n: str) -> str:
    return (rf"(?:(?:hai|2|các)\s+mặt phẳng\s+)?(?:(?:mặt phẳng|mp|mặt bên|mặt đáy)\s*)?"
            rf"(?:\((?P<{n}p>{_NHOM_NHAN})\)|(?<![\w'.])(?P<{n}b>{_NHOM_NHAN})|(?:mặt\s+)?(?P<{n}d>đáy))(?![\w'])")


def _doan_cum(n: str) -> str:
    return rf"(?:(?:các\s+)?(?:đường thẳng|đoạn thẳng|đoạn|cạnh bên|cạnh đáy|cạnh|đường chéo)\s+)?(?<![\w'.])(?P<{n}>{_P1}{_P1})(?![\w'])"


def _khoi_cum(n: str) -> str:
    # ký hiệu khối: "S.ABCD", "ABCD.A'B'C'D'"; tứ diện viết liền bốn nhãn "ABCD" (`{n}t`)
    return (rf"(?:\s+(?P<{n}k>(?:hình|khối)\s+(?:chóp|lăng trụ|lập phương|hộp|tứ diện))"
            rf"(?:\s+(?:đứng|đều|tam giác|tứ giác|chữ nhật|lục giác))*)?"
            rf"(?:\s+(?:(?P<{n}s>{_P1}+\.{_P1}+)|(?P<{n}t>{_P1}{{4}}))(?![\w']))?")


def _nhan_cum(s: str | None) -> list[str]:
    return re.findall(r"[A-Z][0-9]*'?", s or "")


def _mat_cua(m: re.Match, n: str, khoi: dict) -> frozenset | None:
    if nhom := m[n + "p"] or m[n + "b"]:
        return frozenset(_nhan_cum(nhom))
    return next(iter(khoi.values())) if m[n + "d"] and len(khoi) == 1 else None    # "đáy": đáy của khối duy nhất


def _cung_mat(tap: frozenset | None, diem: list[str]) -> bool:
    """Cùng một mặt phẳng: chung ít nhất ba điểm có tên — (ABCD) là (ABC); (SBC) không là (ABC)."""
    return tap is not None and len(tap & set(diem)) >= 3


def _khoi_khop(m: re.Match, n: str, solid: str, khoi: dict) -> bool:
    """Khối của cụm: ký hiệu (nếu có) đúng là khối của lời gọi; không ký hiệu thì đề chỉ có MỘT khối; từ loại khối (chóp /
    lăng trụ …) phải đúng loại — "khối lập phương" không gọi một hình chóp."""
    if (sym := m[n + "s"]) and sym != solid:
        return False
    if (tu := m[n + "t"]) and set(_nhan_cum(tu)) != set(_nhan_cum(solid)):
        return False
    if not sym and not tu and len(khoi) != 1:
        return False
    # từ loại chỉ xét khi KHÔNG có ký hiệu: ký hiệu đúng đã định danh khối ("hình chóp ABCD.EFGH" gọi đúng lăng trụ ấy)
    if (kw := m[n + "k"]) and not sym and not tu and \
            bool(re.search(r"chóp|tứ diện", kw, re.IGNORECASE)) != (len(_nhan_cum(solid.split(".")[0])) == 1):
        return False
    return True


def _cum(mau: str):
    return re.compile(mau, re.IGNORECASE)


def _hai_mat(m, a, khoi):
    return ((_cung_mat(_mat_cua(m, "a", khoi), a.plane1) and _cung_mat(_mat_cua(m, "b", khoi), a.plane2))
            or (_cung_mat(_mat_cua(m, "a", khoi), a.plane2) and _cung_mat(_mat_cua(m, "b", khoi), a.plane1)))


def _khoi_thiet_dien(m, a, khoi):
    co = [n for n in ("k", "j") if m[n + "k"] or m[n + "s"] or m[n + "t"]]
    return all(_khoi_khop(m, n, a.solid, khoi) for n in co) and (bool(co) or len(khoi) == 1)


#: hàm → [(cụm, buộc(m, args, khối của đề))].
_CUM_HOI = {
    "ask_volume": [
        (_cum(rf"thể tích(?:\s+của)?(?:\s+(?-i:V)(?:\s+của)?)?{_khoi_cum('k')}"), lambda m, a, k: _khoi_khop(m, "k", a.solid, k)),
        (_cum(r"(?<![\w'])(?-i:V)(?![\w'])"), lambda m, a, k: len(k) == 1 and a.solid in k and not _V_DINH_NGHIA.search(m.string)
         and not m.string[m.end():].lstrip().startswith("("))],
    "ask_length": [
        (_cum(rf"(?:độ dài(?:\s+của)?\s+)?{_doan_cum('s')}"), lambda m, a, k: set(_nhan_cum(m["s"])) == set(a.segment))],
    "ask_distance_point_plane": [
        (_cum(rf"khoảng cách\s+(?:từ\s+)?(?:(?:điểm|đỉnh)\s+)?(?<![\w'.])(?P<p>{_P1})(?![\w'])\s+(?:đến|tới)\s+{_mat_cum('m')}"),
         lambda m, a, k: m["p"] == a.point and _cung_mat(_mat_cua(m, "m", k), a.plane))],
    "ask_distance_lines": [
        (_cum(rf"khoảng cách\s+giữa\s+(?:hai\s+đường thẳng(?:\s+chéo nhau)?\s+)?{_doan_cum('a')}\s+(?:và|với)\s+{_doan_cum('b')}"),
         lambda m, a, k: {frozenset(_nhan_cum(m["a"])), frozenset(_nhan_cum(m["b"]))} == {frozenset(a.line1), frozenset(a.line2)})],
    "ask_angle_line_plane": [
        (_cum(rf"(?:số đo\s+(?:của\s+)?)?góc\s+(?:giữa|tạo bởi|hợp bởi)\s+{_doan_cum('l')}\s+(?:và|với)\s+{_mat_cum('m')}"),
         lambda m, a, k: set(_nhan_cum(m["l"])) == set(a.line) and _cung_mat(_mat_cua(m, "m", k), a.plane))],
    "ask_angle_plane_plane": [
        (_cum(rf"(?:số đo\s+(?:của\s+)?)?góc\s+(?:giữa|tạo bởi|hợp bởi)\s+{_mat_cum('a')}\s+(?:và|với)\s+{_mat_cum('b')}"), _hai_mat)],
    "ask_area": [
        (_cum(rf"diện tích(?:\s+của)?\s+(?:(?:tam giác|tứ giác|hình vuông|hình chữ nhật|hình thoi|hình bình hành|hình thang"
              rf"|đa giác|mặt bên|mặt đáy|đáy|mặt)\s+)?(?:\((?P<gp>{_NHOM_NHAN})\)|(?<![\w'.])(?P<gb>{_NHOM_NHAN})"
              rf"|Δ\s*(?P<gd>{_NHOM_NHAN}))(?![\w'])"),                    # "ΔSAC": Δ là chữ, nên nhánh riêng
         lambda m, a, k: set(_nhan_cum(m["gp"] or m["gb"] or m["gd"])) == set(a.polygon)),
        (_cum(r"diện tích(?:\s+của)?\s+(?:mặt\s+)?đáy(?![\w'])"),
         lambda m, a, k: len(k) == 1 and set(next(iter(k.values()))) == set(a.polygon))],
    "ask_section_area": [
        (_cum(rf"diện tích(?:\s+của)?\s+thiết diện(?:\s+của{_khoi_cum('k')})?\s+(?:(?:khi\s+|bị\s+)?(?:cắt bởi|tạo bởi)|với|do)\s+{_mat_cum('m')}"
              rf"(?:\s+(?:của|và|cắt){_khoi_cum('j')})?"),
         lambda m, a, k: _cung_mat(_mat_cua(m, "m", k), a.plane) and _khoi_thiet_dien(m, a, k)),
        # "Mặt phẳng (P) cắt hình chóp … theo một thiết diện. Tính diện tích thiết diện đó.": thiết diện đã được gọi tên
        # trước trong đề, và đề chỉ gọi tên ĐÚNG MỘT mặt cắt — chính mặt của lời gọi (review S1, I1).
        (_cum(r"diện tích(?:\s+của)?\s+thiết diện\s+(?:đó|này|trên)(?!\w)"),
         lambda m, a, k: {frozenset(_nhan_cum(x[1] or x[2])) for mau in _CAT_BOI for x in mau.finditer(m.string)
                          if x[1] or x[2]} == {frozenset(a.plane)})],
}
#: Giữa động từ hỏi và cụm (sau khi xoá các cụm hỏi khác): chỉ từ nối.
_GIUA_HOP_LE = re.compile(r"[\s,:]*(?:(?:và|cùng|lần lượt|hãy|các)(?!\w)[\s,:]*)*", re.IGNORECASE)
#: Sau cụm (sau khi xoá các cụm hỏi khác): chỉ những thứ này rồi kết câu / dữ kiện / việc kế tiếp.
_SAU_HOP_LE = re.compile(
    r"(?:[\s,;:]+|(?:và|cùng)(?!\w)|(?:có\s+)?(?:độ dài\s+)?(?:bằng|là)\s+bao\s+nhiêu|dài\s+bao\s+nhiêu|bao\s+nhiêu"
    r"|(?:bằng|là)\s*[?:]"                                                     # đề trắc nghiệm "… bằng?"
    # ngoặc chỉ là LỜI DẶN (làm tròn, đơn vị) — "(sau khi cắt bỏ …)" / "(tính theo đơn vị mới …)" không lọt (review S1)
    r"|theo\s+(?:[a-z](?![\w'])|độ|radian|đơn vị\s+\w+)|\((?:làm tròn|kết quả|đơn vị|đvđd|cm|dm|mm|m|độ)(?![\w'])[^()]*\)"
    r"|(?:đã cho|đó|này|trên)(?!\w)"
    r"|của\s+(?:hình|khối)\s+(?:chóp|lăng trụ|lập phương|hộp|tứ diện)(?:\s+(?-i:[A-Z][0-9]*'?)+(?:\.(?-i:[A-Z][0-9]*'?)+)?)?)*"
    # kết: dấu câu THẬT (sau nó là khoảng trắng / hết đề — "SC.SA" không kết), dữ kiện, việc kế tiếp, lời dặn làm tròn
    r"(?:[.?!](?=\s|$)|$|(?:biết|với|cho|trong đó|rồi|sau đó|từ đó|bằng cách|(?:kết quả\s+)?làm tròn)(?!\w))", re.IGNORECASE)
#: "V" đã được đề định nghĩa ("Gọi V là …", "V = …", "V(S.MAB)") — không buộc mặc nhiên vào khối duy nhất (review S1, I4).
_V_DINH_NGHIA = re.compile(r"(?<![\w'])(?-i:V)\s*(?:là|=|\()", re.IGNORECASE)


def _khoi_cua_loi_goi(calls: tuple[LoiGoi, ...]) -> dict[str, frozenset]:
    """Khối đề khai → tập nhãn đáy: chóp `apex.base`, lăng trụ `base.top`."""
    ra = {}
    for c in calls:
        if c.fn in ("pyramid", "regular_pyramid"):
            ra[c.args.apex + "." + "".join(c.args.base)] = frozenset(c.args.base)
        elif c.fn == "prism":
            ra["".join(c.args.base) + "." + "".join(c.args.top)] = frozenset(c.args.base)
    return ra


def _tap_mat(m: re.Match, i: int, day: frozenset | None) -> frozenset | None:
    nhom = m[i] or m[i + 1]
    return frozenset(re.findall(r"[A-Z][0-9]*'?", nhom)) if nhom else day


def mat_cat_dung_nguon(c: LoiGoi, calls: tuple[LoiGoi, ...]) -> bool:
    """Thiết diện / diện tích thiết diện / giao tuyến (review 2, run `hybrid-slice-review`): mặt phẳng toán hạng phải đúng là
    mặt mà CỤM vai trò của quote gọi tên — "cắt bởi (MAB)", "giao tuyến của (SAB) và (SCD)". "Đáy" chỉ là đáy của khối đang
    xét. Khối: ký hiệu khối trong quote (nếu có) phải là khối của lời gọi; không có ký hiệu thì đề chỉ được có MỘT khối."""
    khoi = _khoi_cua_loi_goi(calls)
    if c.fn == "intersection_line":
        day = next(iter(khoi.values())) if len(khoi) == 1 else None
        dich = {frozenset(c.args.plane1), frozenset(c.args.plane2)}
        return any({_tap_mat(m, 1, day), _tap_mat(m, 4, day)} == dich for q in c.quotes for m in _GIAO_TUYEN.finditer(q))
    ky_hieu = {"".join(phan[0]) + "." + "".join(phan[1]) for q in c.quotes for _a, _b, phan in _tu_nhan(chuan_hoa(q))
               if len(phan) == 2}
    if (ky_hieu and c.args.solid not in ky_hieu) or (not ky_hieu and len(khoi) != 1):
        return False
    day = khoi.get(c.args.solid)
    return any(_tap_mat(m, 1, day) == frozenset(c.args.plane) for q in c.quotes for mau in _CAT_BOI for m in mau.finditer(q))


def construction_source_bound(c: LoiGoi, de: str = "") -> bool:
    """Bounded construction grammar: bind roles together, never borrow labels across clauses.

    Unknown wording is refused, not semantically guessed. Existing plane-foot
    source checks still run first, retaining their legacy error classifications.
    """
    token = r"[A-Z][0-9]*'?(?:[A-Z][0-9]*'?)*"
    point = r"[A-Z][0-9]*'?"
    operand = rf"(?:đường thẳng\s+|mặt phẳng\s+)?\(?({token}|đáy)\)?"
    a = c.args
    def labels(s):
        return re.findall(point, s)
    for q in c.quotes:
        if c.fn.startswith("intersect_line_"):
            pattern = rf"(?<![\w'])({point})\s+là\s+giao điểm\s+(?:của\s+)?{operand}\s+(?:và|với)\s+{operand}(?![\w'])"
            for m in re.finditer(pattern, q):
                out, x, y = m.groups()
                if c.fn == "intersect_line_line":
                    actual = {frozenset(labels(x)), frozenset(labels(y))}
                    expected = {frozenset(a.line1), frozenset(a.line2)}
                    bound = actual == expected and len(labels(x)) == len(labels(y)) == 2
                else:
                    bound = ((labels(x) in (a.line, a.line[::-1]) and labels(y) == a.plane) or
                             (labels(y) in (a.line, a.line[::-1]) and labels(x) == a.plane))
                if out == a.point and bound:
                    return True
        else:
            target = a.line if c.fn.endswith("_line") else a.plane
            patterns = [rf"(?<![\w'])({point})\s+là\s+hình chiếu\s+(?:vuông góc\s+)?của\s+({point})\s+(?:lên|trên)\s+{operand}(?![\w'])",
                        rf"[Hh]ình chiếu\s+(?:vuông góc\s+)?của\s+({point})\s+(?:lên|trên)\s+{operand}\s+là\s+(?:điểm\s+|trọng tâm\s+|trung điểm\s+)?({point})(?![\w'])"]
            for i, pattern in enumerate(patterns):
                for m in re.finditer(pattern, q):
                    out, src, dst = m.groups() if i == 0 else (m[3], m[1], m[2])
                    pts = labels(dst)
                    if dst == "đáy" and len(target) >= 3:
                        bases = {tuple(p[1]) for dau, _cuoi, p in _tu_nhan(de) if len(p) == 2 and
                                 re.search(r"(?:chóp|lăng\s+trụ)\s*$", de[:dau], re.IGNORECASE)}
                        if len(bases) == 1 and _cung_da_giac(list(next(iter(bases))), target):
                            pts = target
                    if out == a.image and src == a.point and (pts == target or (len(target) == 2 and pts == target[::-1])):
                        return True
    return False


def function_declarations() -> list[dict[str, Any]]:
    """Khai báo hàm (JSON Schema) — một mục mỗi hàm: đối số + `call_id`, `quotes`, `depends_on`. Bản Gemini (tập con
    OpenAPI) dẫn xuất từ đây ở `app/ai/function_calling.py`."""
    ra = []
    for s in REGISTRY.values():
        sch = s.args.model_json_schema()
        props = {**sch.get("properties", {}),
                 "call_id": {"type": "string", "description": "id ngắn, duy nhất trong bài, vd c1"},
                 "quotes": {"type": "array", "items": {"type": "string"}, "minItems": 1,
                            "description": Source.model_fields["quotes"].description},
                 "depends_on": {"type": "array", "items": {"type": "string"},
                                "description": FunctionCall.model_fields["depends_on"].description}}
        ra.append({"name": s.name, "description": s.description,
                   "parameters": {"type": "object", "properties": props,
                                  "required": [*sch.get("required", []), "call_id", "quotes"],
                                  **({"$defs": sch["$defs"]} if "$defs" in sch else {})}})
    return ra
