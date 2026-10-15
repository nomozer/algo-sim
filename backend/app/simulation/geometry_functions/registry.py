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
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator

REGISTRY_VERSION = "geometry-functions/4"


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
    line: Seg | None = None
    line_ref: str | None = Field(None, min_length=1, description="ID của producer giao tuyến đã kiểm nguồn; không phải nhãn điểm")
    image: Label

    @model_validator(mode="after")
    def _one_line(self):
        if (self.line is None) == (self.line_ref is None):
            raise ValueError("cần đúng một trong line và line_ref")
        return self


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


class TranslatePointArgs(_Args):
    point: Label = Field(..., description="điểm gốc")
    vector: Seg = Field(..., description="vectơ tịnh tiến: từ điểm thứ nhất tới điểm thứ hai")
    image: Label = Field(..., description="ảnh (điểm phụ)")


@dataclass(frozen=True)
class PlanningTerm:
    """Internal typed role slots; not an expression language or provider program."""
    kind: Literal["Point", "Plane", "Line", "Foot", "AnswerDistance"]
    operands: tuple[str, ...]


@dataclass(frozen=True)
class PlanningContract:
    inputs: tuple[PlanningTerm, ...]
    effect: PlanningTerm
    source_policy: Literal["declared_intersection", "projection_foot", "distance_witness"]
    verifier: str


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
    #: Only the deterministic planner may emit it, inside a declared decomposition (`AUXILIARY_RULES`); never offered to
    #: the provider (route A), refused anywhere else.
    auxiliary_only: bool = False
    planning: PlanningContract | None = None  # internal; function_declarations never serializes it


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
       (("hình chiếu",),), segment_fields=("line",), point_fields=("image",),
       planning=PlanningContract((PlanningTerm("Point", ("P",)), PlanningTerm("Line", ("L",))),
                                 PlanningTerm("Foot", ("F", "P", "L")), "projection_foot", "_construction_relation")),
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
    _F("ask_length", AskLengthArgs, "ask", "Đề hỏi độ dài một đoạn.", (("độ dài", "tính", "tìm"),),
       planning=PlanningContract((PlanningTerm("Point", ("P",)), PlanningTerm("Foot", ("F", "P", "L"))),
                                 PlanningTerm("AnswerDistance", ("P", "L")), "distance_witness", "distance")),
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
       (("giao tuyến",),), plane_fields=("plane1", "plane2"),
       planning=PlanningContract((PlanningTerm("Plane", ("A",)), PlanningTerm("Plane", ("B",))),
                                 PlanningTerm("Line", ("L",)), "declared_intersection", "intersect_plane_plane")),
    _F("ask_section_area", SectionArgs, "ask", "Đề hỏi diện tích thiết diện của một khối cắt bởi một mặt phẳng.",
       (("diện tích",), ("thiết diện",)), plane_fields=("plane",)),
    _F("unsupported", UnsupportedArgs, "escape", "Mệnh đề không ánh xạ được vào thư viện — engine sẽ từ chối trung thực."),
    # Goal-directed slice (run `goal-directed-section-planning`): the plane through M parallel to (Q) is the plane through M
    # and two translates of M along directions of (Q) — the IR's own expression (`PlanePerpendicularToLineExpr` note).
    _F("translate_point", TranslatePointArgs, "construct", "Điểm phụ: ảnh của một điểm qua phép tịnh tiến theo vectơ hai "
       "điểm đã có.", auxiliary_only=True),
)}
#: The functions offered to the provider of route A — the library minus planner-only auxiliaries.
PROVIDER_FUNCTIONS = tuple(n for n, s in REGISTRY.items() if not s.auxiliary_only)

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
    for key, v in c.args.model_dump().items():
        if key == "line_ref":                         # opaque producer ID, never a geometric point label
            continue
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
#: Plane through a verified point parallel to a named plane, then the section by it (`planner._mat_qua_diem`): two translates
#: of the point along two directions of the reference plane span the plane; the section takes the three points.
MAT_SONG_SONG = "section(plane through point ∥ plane)"
MAT_HAI_DUONG = "section(plane through point strictly parallel to two lines)"
AUXILIARY_RULES = {"distance(point,line)": ("orthogonal_projection_line", "ask_length"),
                   MAT_SONG_SONG: ("translate_point", "section"), MAT_HAI_DUONG: ("translate_point", "section")}
#: "khoảng cách từ S đến (đường thẳng) BD": điểm và đường gắn vai trong CÙNG một cụm; cách nói khác ⇒ từ chối, không đoán.
_KHOANG_CACH_DIEM_DUONG = re.compile(
    r"khoảng cách\s+từ\s+(?:điểm\s+)?([A-Z][0-9]*'?)\s+(?:đến|tới)\s+(?:đường thẳng\s+)?([A-Z][0-9]*'?)([A-Z][0-9]*'?)(?![\w'])",
    re.IGNORECASE)
#: Câu hỏi khoảng cách điểm–đường: không gán giá trị ngay sau đường thẳng ("bằng 4", "không bằng 3", "khác 3"; "bằng bao nhiêu" vẫn là câu hỏi).
_GAN_GIA_TRI = re.compile(r"\s*(?:(?:\w+\s+)?(?:(?:bằng|là|khác)(?!\w)|[=≠])\s*(?!bao\s+nhiêu|\?)\S|(?:đổi|thay|cộng|trừ|nhân|chia|[+\-*/])\b)", re.IGNORECASE)
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


def _kiem_phu(phu: tuple[dict, ...], calls: tuple[LoiGoi, ...], de: str, nhan: set[str],
              ten_mat_phu: dict | None = None, don_vi_de: set[str] = frozenset()) -> set[str]:
    """Điểm phụ do planner khai: đúng luật, nhãn không trùng đề, hai lời gọi đúng hình dạng luật, câu hỏi nguồn có thật,
    không điều kiện/chứng minh/phủ định, và gắn đúng điểm + đường. Trả id các lời gọi đã kiểm (bỏ qua ở vòng thường).
    Nhãn phụ ở bất kỳ lời gọi nào KHÁC vẫn rơi vào `UNKNOWN_LABEL` của vòng thường."""
    theo_id = {c.id: c for c in calls}
    da: set[str] = _kiem_result_binding(phu, calls, de, nhan, don_vi_de)
    chiem = nhan | nhan_phu_da_dung(de)
    nhan_da_khai: set = set()
    for d in phu:
        if d.get('effect_binding') or d.get('rule') in ('result-line-reference','result-line-alias'):
            continue  # same source authority validated actual producer/consumer/goal above
        x, luat = d.get("label"), d.get("rule")
        if luat not in AUXILIARY_RULES:
            raise TuChoi("AUXILIARY_RULE_MISMATCH", f"điểm phụ {x}: luật {luat!r} không có trong bảng phân rã")
        if luat in (MAT_SONG_SONG, MAT_HAI_DUONG):
            da |= _kiem_mat_song_song(d, theo_id, de, nhan, chiem, nhan_da_khai, calls, ten_mat_phu, don_vi_de)
            continue
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
            # Đề là thẩm quyền, quote chỉ định vị: cụm và mọi bổ ngữ quanh nó đọc trên đề GỐC (quote khác khoảng trắng hay bỏ
            # bổ ngữ không che được "bình phương / hai lần …"), theo cùng văn phạm đóng của câu hỏi thường (`_hoi_dung_cum`).
            for m in _KHOANG_CACH_DIEM_DUONG.finditer(de):
                if vt[0] <= m.start() and m.end() <= vt[1] and m[1] == p and [m[2], m[3]] in (dt, dt[::-1]):
                    vai.append(_vai_tro_tai(de, m.start()))
                    # The rest of the sentence (before the governing verb) is read by the question-context gate.
                    hoi_that.append(_hoi_dung_cum(de, m.start(), m.end()) and not _GAN_GIA_TRI.match(de[m.end():]))
                    if _hoi_dung_cum(de, m.start(), m.end()) and not _kiem_don_vi_hoi("ask_length", de, m.start(), m.end(), don_vi_de, calls):
                        raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                                     f"{hoi.id}: đơn vị yêu cầu không khớp chính sách đơn vị của dữ kiện hoặc loại đại lượng", ids)
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


def _kiem_result_binding(phu, calls, de, nhan, don_vi_de: set[str] = frozenset()):
    """Validate proposed effects against real calls and closed source spans. No client promise is truth."""
    by_id = {c.id:c for c in calls}
    accepted = set()
    registered = {d.get('consumer') for d in phu if d.get('rule') == 'result-line-reference'}
    registered |= {d.get('construct') for d in phu if d.get('effect_binding') and d.get('line_ref')}
    for c in calls:
        if getattr(c.args,'line_ref',None) and c.id not in registered:
            raise TuChoi('RESULT_BINDING_UNVERIFIED', 'line_ref chỉ qua chứng chỉ của Planner', (c.id,))

    def source_role(c, q, pos):
        if _vi_tri(de,q) is None:
            raise TuChoi('QUOTE_NOT_IN_SOURCE','quote reference không có trong đề',(c.id,))
        vt = _vi_tri(de,q)[0]
        role = _vai_tro_tai(de,vt+pos)
        if role == 'GOAL':
            raise TuChoi('GOAL_CLAUSE_NOT_PREMISE','reference nằm trong mục tiêu chứng minh',(c.id,))
        if role == 'CONDITIONAL':
            raise TuChoi('CONDITIONAL_CLAUSE','reference có điều kiện',(c.id,))
        if _phu_dinh(de,vt,q):
            raise TuChoi('NEGATED_CLAUSE','reference có phủ định',(c.id,))
        return vt

    def producer(ref):
        c = by_id.get(ref)
        if c is None:
            raise TuChoi('UNKNOWN_DERIVED_REFERENCE','không có producer',(ref,))
        if c.fn != 'intersection_line':
            raise TuChoi('DERIVED_REFERENCE_TYPE_MISMATCH','producer không sinh giao tuyến',(ref,))
        if any(len(p)!=3 or len(set(p))!=3 for p in (c.args.plane1,c.args.plane2)):
            raise TuChoi('FACT_INCOMPLETE','reference cần hai mặt ba nhãn phân biệt',(ref,))
        if nhan_cua_loi_goi(c)-nhan:
            raise TuChoi('UNKNOWN_LABEL','mặt producer có nhãn ngoài nguồn',(ref,))
        producer_form = (rf'(?:(?i:tìm|dựng|xác định)\s+|(?i:gọi)\s+[A-Za-z][A-Za-z0-9]*\s+(?i:là)\s+)'
                         rf'(?i:giao tuyến của)\s*{_MAT_TOAN_HANG}\s*(?i:và)\s*{_MAT_TOAN_HANG}[.\s]*')
        for q in c.quotes:
            m = re.search(r'(?i:giao tuyến)',q)
            vt = source_role(c,q,m.start() if m else 0)
            if not re.fullmatch(producer_form,q):
                raise TuChoi('SOURCE_OBJECT_MISMATCH','producer chưa có định nghĩa/yêu cầu dựng nguyên tử',(ref,))
            if not re.fullmatch(producer_form,de[slice(*_bien_cau(de,vt))].strip()):
                raise TuChoi('SOURCE_PREMISE_UNREAD','câu producer có phần ngoài quote chưa được đọc',(ref,))
            for match in _GIAO_TUYEN.finditer(q):
                planes = [_nhan_cum(next((match[i] for i in group if match[i]),''))
                          for group in ((1,2,3),(4,5,6))]
                if any(len(p)!=3 or len(set(p))!=3 for p in planes):
                    raise TuChoi('SOURCE_OBJECT_MISMATCH','mặt nguồn cần đúng ba nhãn phân biệt',(ref,))
            if not mat_cat_dung_nguon(replace(c,quotes=(q,)),calls):
                raise TuChoi('SOURCE_OBJECT_MISMATCH','hai mặt producer không khớp nguồn',(ref,))
        accepted.add(ref)
        return c

    def matches_planes(m, c):
        labels = [_nhan_cum(m.group(i)) for i in ('a','b')]
        if any(len(p)!=3 or len(set(p))!=3 for p in labels):
            return False
        planes = list(map(frozenset,labels))
        return set(planes)=={frozenset(c.args.plane1),frozenset(c.args.plane2)}

    plane_pattern = rf'(?P<a>{_MAT_TOAN_HANG})\s*(?i:và)\s*(?P<b>{_MAT_TOAN_HANG})'
    derived = re.compile(rf'(?i:khoảng cách\s+từ\s+(?:điểm\s+)?)' + rf'(?P<p>{_P1})'
                         + rf'\s*(?i:đến|tới)\s*(?i:giao tuyến của)\s*{plane_pattern}')
    seen_fresh = {}
    for d in phu:
        if d.get('rule')=='result-line-alias':
            a,b=producer(d.get('producer')),producer(d.get('canonical'))
            if {frozenset(a.args.plane1),frozenset(a.args.plane2)} != {frozenset(b.args.plane1),frozenset(b.args.plane2)}:
                raise TuChoi('AUXILIARY_RULE_MISMATCH','hai producer alias không cùng mặt nguồn')
            continue
        if d.get('rule') == 'result-line-reference':
            c = by_id.get(d.get('consumer'))
            if not c or c.fn!='orthogonal_projection_line' or c.args.line_ref!=d.get('line_ref'):
                raise TuChoi('AUXILIARY_RULE_MISMATCH','projection reference không khớp lời gọi')
            g = producer(c.args.line_ref)
            for q in c.quotes:
                vt = source_role(c,q,0)
                pattern = (rf'(?i:gọi)\s*(?P<f>{_P1})\s*(?i:là hình chiếu vuông góc của)\s*(?P<p>{_P1})'
                           rf'\s*(?i:lên)\s*(?i:giao tuyến của)\s*{plane_pattern}[.\s]*')
                m = re.fullmatch(pattern,q)
                if not m or m['f']!=c.args.image or m['p']!=c.args.point or not matches_planes(m,g):
                    raise TuChoi('SOURCE_OBJECT_MISMATCH','projection reference không khớp nguồn',(c.id,))
                if not re.fullmatch(pattern,de[slice(*_bien_cau(de,vt))].strip()):
                    raise TuChoi('SOURCE_PREMISE_UNREAD','câu hình chiếu có phần ngoài quote chưa được đọc',(c.id,))
            accepted.add(c.id)
            continue
        if not d.get('effect_binding'):
            continue
        foot, ask = by_id.get(d.get('construct')), by_id.get(d.get('ask'))
        p, x, ref, line = d.get('point'), d.get('label'), d.get('line_ref'), d.get('line') or []
        if not (d.get('rule')=='distance(point,line)' and foot and ask and foot.fn=='orthogonal_projection_line'
                and ask.fn=='ask_length' and foot.args.point==p and foot.args.image==x
                and foot.args.line_ref==ref and (foot.args.line or []) in (line,line[::-1]) and ask.args.segment==[p,x]
                and ask.quotes==tuple(d.get('quotes') or ())):
            raise TuChoi('AUXILIARY_RULE_MISMATCH','effect/calls/goal không khớp')
        for fn, kind, verifier in ((foot.fn,'Foot','_construction_relation'),(ask.fn,'AnswerDistance','distance')):
            contract = REGISTRY[fn].planning
            if not contract or contract.effect.kind!=kind or contract.verifier!=verifier:
                raise TuChoi('AUXILIARY_RULE_MISMATCH','contract không có verifier hợp lệ')
        if {p,*line}-nhan:
            raise TuChoi('UNKNOWN_LABEL','toán hạng khoảng cách ngoài nguồn',(ask.id,))
        if d.get('fresh'):
            if x in nhan | nhan_phu_da_dung(de):
                raise TuChoi('AUXILIARY_LABEL_COLLISION','chân phụ ghi đè nhãn nguồn',(foot.id,))
            if x in seen_fresh and seen_fresh[x]!=foot.id:
                raise TuChoi('AUXILIARY_RULE_MISMATCH','hai producer cho một chân phụ')
            seen_fresh[x]=foot.id
            if not foot.quotes or not set(foot.quotes).issubset({q for e in phu if e.get('construct')==foot.id
                                                             for q in e.get('quotes') or ()}):
                raise TuChoi('AUXILIARY_RULE_MISMATCH','chân phụ mất nguồn mục tiêu')
            accepted.add(foot.id)
        elif x not in nhan:
            raise TuChoi('UNKNOWN_LABEL','chân tái sử dụng không có trong nguồn',(foot.id,))
        g = producer(ref) if ref else None
        for q in ask.quotes:
            if ref:
                m = derived.search(q)
                if m and _GAN_GIA_TRI.match(q[m.end():]):
                    raise TuChoi('NOT_ASKED_IN_SOURCE','mục tiêu đã gán giá trị',(ask.id,))
                vt = source_role(ask,q,m.start() if m else 0)
                if not m or m['p']!=p or not matches_planes(m,g):
                    raise TuChoi('SOURCE_OBJECT_MISMATCH','điểm/hai mặt của mục tiêu không khớp nguồn',(ask.id,))
                if not _duoc_hoi(de,vt+m.start(),vt+m.end()):
                    raise TuChoi('NOT_ASKED_IN_SOURCE','nguồn không hỏi khoảng cách này',(ask.id,))
                ask_form = r'(?i:(?:tính|tìm)\s+)?'+derived.pattern+r'[.?\s]*'
                if not re.fullmatch(ask_form,q) or not re.fullmatch(ask_form,de[slice(*_bien_cau(de,vt+m.start()))].strip()):
                    raise TuChoi('SOURCE_PREMISE_UNREAD','quote mục tiêu có phần chưa được đọc',(ask.id,))
            else:
                # The source is the authority, the quote only locates: never read the quote spliced into the source
                # (an extra space in the quote can invent a sentence boundary the source does not have).
                span=_vi_tri(de,q)
                if span is None:
                    raise TuChoi('QUOTE_NOT_IN_SOURCE','quote mục tiêu không có trong đề',(ask.id,))
                matches=[m for m in _KHOANG_CACH_DIEM_DUONG.finditer(de) if span[0]<=m.start() and m.end()<=span[1]
                         and m[1]==p and [m[2],m[3]] in (line,line[::-1])]
                if not matches:
                    raise TuChoi('SOURCE_OBJECT_MISMATCH','mục tiêu điểm/đường không khớp',(ask.id,))
                for m in matches:
                    source_role(ask,q,m.start()-span[0])
                    if not _hoi_dung_cum(de,m.start(),m.end()) or _GAN_GIA_TRI.match(de[m.end():]):
                        raise TuChoi('NOT_ASKED_IN_SOURCE','nguồn không hỏi khoảng cách này',(ask.id,))
                    if not _kiem_don_vi_hoi("ask_length", de, m.start(), m.end(), don_vi_de, calls):
                        raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                                     f"{ask.id}: đơn vị yêu cầu không khớp chính sách đơn vị của dữ kiện hoặc loại đại lượng",
                                     (ask.id,))
        accepted.add(ask.id)
    return accepted


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
    patterns = (*(mau for ds in _CUM_HOI.values() for mau, _b in ds), _KHOANG_CACH_DIEM_DUONG,
                _KHOANG_CACH_GIAO_TUYEN, _CUM_HOI_THIET_DIEN_PHU)
    cum = sorted(((m.start(), m.end()) for mau in patterns for m in mau.finditer(s)
                  if m.end() > m.start() and not re.match(r"số\s+đo\b", m.group(), re.IGNORECASE)),
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
    return _vung_hoi(de, a, b) is not None


def _vung_hoi(de: str, a: int, b: int) -> tuple[int, int] | None:
    """Vùng `_hoi_dung_cum` đã ĐỌC cho cụm `de[a:b]`: từ động từ hỏi chi phối (không có thì đầu mệnh đề) tới hết phần đuôi
    đóng — hay None khi cụm không được hỏi nguyên vẹn. Cổng ngữ cảnh câu hỏi dùng nó để biết chữ nào của câu đã có người đọc."""
    if not _duoc_hoi(de, a, b):
        return None
    c0, c1 = _bien_cau(de, a)
    truoc = de[c0:a]
    moc = [m.end() for m in _DUNG_GAN.finditer(truoc)]
    dong_tu = list(_DONG_TU_HOI.finditer(truoc, moc[-1] if moc else 0))
    tu = c0 + dong_tu[-1].start() if dong_tu else _bien_menh_de(de, a)[0]
    giua = truoc[dong_tu[-1].end():] if dong_tu else de[tu:a]
    sau = _SAU_HOP_LE.match(_bo_cum(de[b:c1]))
    return (tu, b + sau.end()) if _GIUA_HOP_LE.fullmatch(_bo_cum(giua)) and sau else None


def _kiem_cau_hoi(c: LoiGoi, de: str, vts: list[tuple[int, int]], calls: tuple[LoiGoi, ...],
                  don_vi_de: set[str] | None = None) -> None:
    """Câu hỏi `ask_*` chỉ được trả lời khi đề HỎI đúng đối tượng ấy: có CỤM gọi đúng toán hạng của lời gọi (`_cum_hoi`),
    cụm ấy được hỏi nguyên vẹn (`_hoi_dung_cum`), và vai trò mệnh đề đọc TẠI cụm được hỏi không là điều phải chứng minh /
    điều kiện. Nhãn của đối tượng nhắc lại trong một vế chứng minh ("Chứng minh SC ⊥ BD và tính SC") không chặn câu hỏi."""
    if don_vi_de is None:
        don_vi_de = _don_vi_met_cua_de(de)
    cum = [m for dau, cuoi in vts for m in _cum_hoi(c, de, dau, cuoi, calls)]
    if not cum:
        raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: {c.quote!r} không gọi tên đúng đối tượng của {c.fn} "
                     f"{c.args.model_dump()} — không trả lời câu hỏi về đối tượng khác", (c.id,))
    hoi = [(p, h) for p, h in cum if _hoi_dung_cum(de, p, h)]
    if not hoi:
        raise TuChoi("NOT_ASKED_IN_SOURCE", f"{c.id}: {c.quote!r} không hỏi đối tượng này nguyên vẹn (không có từ hỏi gắn với "
                     "nó, đã gán giá trị, hay bị bổ nghĩa / đặt điều kiện) — không trả lời điều đề không hỏi", (c.id,))
    if not all(_kiem_don_vi_hoi(c.fn, de, p, h, don_vi_de, calls) for p, h in hoi):
        raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                     f"{c.id}: đơn vị yêu cầu trong câu hỏi không khớp chính sách đơn vị của dữ kiện hoặc loại đại lượng", (c.id,))
    vai = {_vai_tro_tai(de, p) for p, _h in hoi}
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


def kiem_nguon(calls: tuple[LoiGoi, ...], text: str, auxiliary: tuple[dict, ...] = (),
               read_quotes: tuple[str, ...] = ()) -> dict[str, str | None]:
    """Cổng nguồn tất định — xem docstring module. Ném `TuChoi` ở lời gọi đầu tiên hỏng (theo thứ tự id).
    `auxiliary`: điểm phụ planner nhánh B khai (`AUXILIARY_RULES`); nhánh A không truyền ⇒ mọi nhãn phải có trong đề.
    Returns the name the source gave each bound derived plane (first construct id → "P", or None when unnamed)."""
    de = chuan_hoa(text)
    nhan = nhan_cua_de(de)
    don_vi_de = _don_vi_met_cua_de(de)
    if len(don_vi_de) > 1:
        raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED", "đơn vị độ dài trong đề không đồng nhất; chưa hỗ trợ đổi đơn vị")
    ten_mat_phu: dict[str, str | None] = {}              # derived plane (first construct id) → name the source gave it
    phu = _kiem_phu(tuple(auxiliary), calls, de, nhan, ten_mat_phu, don_vi_de)
    if any(d.get('rule') == MAT_HAI_DUONG or d.get('line_ref') for d in auxiliary):
        _kiem_nguon_dong(calls, de, phu, read_quotes)
    if lac := sorted(c.id for c in calls if c.spec.auxiliary_only and c.id not in phu):
        raise TuChoi("AUXILIARY_ONLY_FUNCTION", f"{lac}: chỉ planner sinh hàm này, trong một phân rã đã khai", tuple(lac))
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

    _kiem_du_kien_cau_hoi(calls, de, read_quotes, phu, don_vi_de)
    return ten_mat_phu


def _kiem_du_kien_cau_hoi(calls: tuple[LoiGoi, ...], de: str, read_quotes: tuple[str, ...] = (),
                          phu: set[str] = frozenset(), don_vi_de: set[str] | None = None) -> None:
    """Source coverage, not a second fact state: local claims must match validated calls before engine verification.

    Read the whole question context, including text outside the model's quote. Only closed source spans are covered;
    an unread modifier never authorizes using the old figure. No local claim overwrites a premise.
    """
    # An explicit escape is unconditionally refused by the engine before any construction. Preserve OUT_OF_SCOPE.
    if any(c.fn == "unsupported" for c in calls):
        return
    if don_vi_de is None:
        don_vi_de = _don_vi_met_cua_de(de)
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

    def cover(a: int, b: int) -> tuple[str, bool]:
        """Check every length / shape assertion in `de[a:b]` against validated calls; return the span with them blanked."""
        if de[a:b].strip(" ,;:.?!"):
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
            # What a goal or question states is to be shown, never a hypothesis; it stays uncovered.
            if value is None or tail is None or _vai_tro_tai(de, m.start()) in ("GOAL", "QUESTION"):
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
            if not (a <= r.span[0] < r.span[1] <= b) or _vai_tro_tai(de, r.span[0]) in ("GOAL", "QUESTION"):
                continue
            if not any(_rang_buoc_cuc_bo_khop(r, c) for c in calls):
                raise TuChoi("QUESTION_LOCAL_GIVEN_UNVERIFIED",
                             f"dữ kiện {r.kind} trong câu hỏi chưa có giả thiết tương ứng đã xác thực")
            x, y = r.span
            residue[x - a:y - a] = " " * (y - x)
            found = True
        for x, y in phep_dung_spans:
            if a <= x < y <= b:
                residue[x - a:y - a] = " " * (y - x)
                found = True
        return "".join(residue), found

    phep_dung_spans: list[tuple[int, int]] = []
    questions = {_bien_cau(de, m.start()) for m in request_verb.finditer(de)}
    for c in calls:
        if c.spec.kind == "ask":
            for q in c.quotes:
                if (vt := _vi_tri(de, q)) is not None:
                    questions |= {_bien_cau(de, p) for p, h in _cum_hoi(c, de, *vt, calls) if _hoi_dung_cum(de, p, h)}
                    questions |= {_bien_cau(de, m.start()) for pattern in (
                        _KHOANG_CACH_DIEM_DUONG, _KHOANG_CACH_GIAO_TUYEN, _CUM_HOI_THIET_DIEN_PHU)
                                  for m in pattern.finditer(de, *vt) if _hoi_dung_cum(de, m.start(), m.end())}
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
    # A sentence that asks ("?", "bao nhiêu", "mấy") opens the request region even without a request verb.
    first_request = min([first_request, *(_bien_cau(de, m.start())[0] for m in _HOI_SAU.finditer(de))])
    questions |= {_bien_cau(de, p) for p in (0, *(m.end() for m in re.finditer(r"[.!?]\s+", de)))
                  if first_request <= p < len(de)}
    # Everything before the first request is premise text: it must be read too (run `source-grounding-completeness`).
    _kiem_vung_tien_de(calls, de, first_request, read_quotes, don_vi_de)
    dung = {n for c in calls for n in nhan_cua_loi_goi(c)}
    khoi = _khoi_cua_loi_goi(calls)
    for start, end in sorted(questions):
        phrases = [(m.start(), m.end()) for fn, rules in _CUM_HOI.items() for pattern, _bind in rules
                   for m in pattern.finditer(de, start, end)
                   if _hoi_dung_cum(de, m.start(), m.end())
                   and _kiem_don_vi_hoi(fn, de, m.start(), m.end(), don_vi_de, calls)]
        phrases += [(m.start(), m.end()) for pattern in (
            _KHOANG_CACH_DIEM_DUONG, _KHOANG_CACH_GIAO_TUYEN, _CUM_HOI_THIET_DIEN_PHU)
                    for m in pattern.finditer(de, start, end) if _hoi_dung_cum(de, m.start(), m.end())]
        if _DIEU_KIEN.search(de, start, end):
            raise TuChoi("CONDITIONAL_CLAUSE", "ngữ cảnh câu hỏi có giả thiết điều kiện; chưa hỗ trợ thay phạm vi")
        masked = list(de[start:end])
        for a, b in phrases:
            masked[a - start:b - start] = " " * (b - a)
        assertions = [r.span for r in rb] + [m.span() for m in lengths]
        object_ends = [b for _a, b in phrases] + [m.end() for pattern in (*_CAT_BOI, _GIAO_TUYEN)
                                               for m in pattern.finditer(de, start, end)]
        dan = [m for m in _DUNG_GAN.finditer("".join(masked))
               if m.group().lower() not in ("khi", "nếu")
               and not any(a <= start + m.start() < b for a, b in assertions)
               and (m.group().lower() != "với" or any(p <= start + m.start()
                    and not de[p:start + m.start()].strip(" ,;:") for p in (start, *object_ends)))]
        markers = [start + m.end() for m in dan]
        stops = sorted({a for a, _b in phrases} | {m.start() for m in request_verb.finditer(de, start, end)} | {end})
        fragments = [(start + m.start(), a, next(p for p in stops if p >= a)) for m, a in zip(dan, markers)]
        first = min(stops)
        prefix = de[start:first]
        gd = _GIAN_DAN.match(de, start, first)
        a0 = gd.end() if gd else start
        is_note = bool(_GHI_CHU.fullmatch(de, a0, end)
                       and not re.search(r"(?<![a-zA-Z\^])\d+(?![\d\s]*chữ số)", de[a0:end], re.I))
        if (not is_note and not phrases and not request_verb.search(de, start, end)
                and (start, end) not in construction_contexts and not fragments):
            fragments.append((start, start, end))
        muc_spans = _doc_muc_tieu_cau_hoi(de, a0, first, dung)
        for x, y in muc_spans:
            for d in _DO_DAI_CUC_BO.finditer(de, x, y):
                if not _DUOI_BANG.match(de[d.end():]):
                    continue
                v = _doc(d)
                for seg in [p for _x, _y, parts in _tu_nhan(de[d.start():d.start("number")]) for p in parts if len(p) == 2]:
                    if v is not None and (cand := _nguon_do_dai_cuc_bo(calls, seg)) and all(w != v for w, _i in cand):
                        raise TuChoi("INCONSISTENT_FACTS", "điều phải chứng minh nêu một độ dài khác giá trị đã xác thực")
        phep_dung_spans = _doc_phep_dung_cau_hoi(de, start, end, calls, dung, khoi, phu)
        discourse = (_GIUA_HOP_LE.fullmatch(prefix) or re.fullmatch(r"\s*khi đó\s*,?\s*", prefix, re.I) or bool(muc_spans))
        if not is_note and start < first < end and not markers and not discourse and _tu_nhan(prefix):
            fragments.append((start, start, first))
        # Sentence-level reading (run `shared-ask-grammar-safety`): in a sentence that asks an object, every word must be
        # read by something — the asked phrase with its governing verb and closed tail, a covered given fragment, a
        # follow-up read in closed words, a goal clause, or a validated construction. What is left may only be punctuation
        # and closed connectors: a word that changes the asked quantity ("Nhân đôi kết quả, tính …") is unread.
        doc_cau = [False] * (end - start)

        def doc(a: int, b: int) -> None:
            doc_cau[a - start:b - start] = [True] * (b - a)

        if gd:
            doc(start, a0)
        if is_note:
            if not _kiem_ghi_chu(de[a0:end], calls, don_vi_de):
                raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                             "ghi chú về kết quả/đơn vị không khớp chính sách đơn vị hoặc làm tròn")
            doc(a0, end)
        for a, b in phrases:
            doc(*_vung_hoi(de, a, b))
        for m in request_verb.finditer(de, start, end):
            doc(m.start(), m.end())
        for x, y in muc_spans:
            doc(x, y)
        for x, y in phep_dung_spans:
            doc(x, y)
        for tu, a, b in fragments:
            remaining, found = cover(a, b)
            if (not found and remaining.strip(" ,;:.?!")) or not _NOI_DU_KIEN_CUC_BO.fullmatch(remaining):
                raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                             "phần dữ kiện/đổi giả thiết trong câu hỏi chưa được đọc trọn; không dùng mô hình cũ")
            doc(tu, b)
        # The ask grammar accepts a next task after the asked phrase (`_VIEC_KE_TIEP`) and stops reading there. The gate
        # reads it with the same closed obligation as a given fragment: after covering assertions, only given words, a
        # comparison of named objects or a rounding instruction may remain; a goal clause (chứng minh, suy ra …) is not a
        # hypothesis; a method ("bằng cách") only names a formula or theorem. Anything unread is refused, not guessed.
        for m in _VIEC_KE_TIEP_RE.finditer("".join(masked)):
            a = start + m.end()
            if any(x <= start + m.start() < y for x, y in assertions):
                continue
            b = next(p for p in stops if p >= a)
            doc(start + m.start(), a)
            if not de[a:b].strip(" ,;:.?!"):
                continue
            remaining, _found = cover(a, b)
            if any(c.spec.kind == "ask" for c in calls) and re.search(_LAM_TRON, remaining, re.IGNORECASE):
                raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                             "yêu cầu làm tròn kết quả chưa được hỗ trợ; hệ thống chỉ trả biểu thức chính xác")
            if m.group().lower() == "bằng cách":
                ok = _PHUONG_PHAP.fullmatch(remaining)
            elif mo_f := _MO_MUC_TIEU.match(de, a, b):
                # a goal clause covers itself only: its body must be a closed geometric goal, and what follows ";" is read like a follow-up
                cham = de.find(";", a, b)
                end_goal = cham if cham >= 0 else b
                spans = _doc_muc_tieu_cau_hoi(de, a, end_goal, dung)
                body_f = de[mo_f.end():end_goal]
                suy_ra_cum = (
                    "suy ra" in mo_f.group().lower()
                    and bool(re.match(r"\s*(?:thể\s+tích|diện\s+tích|khoảng\s+cách|độ\s+dài|góc)\b", body_f, re.I))
                    and not _bo_cum(body_f).strip(" .?!")
                    and {n for _x, _y, phan in _tu_nhan(body_f) for p in phan for n in p} <= dung
                )
                ok = (((bool(spans) and not de[spans[-1][1]:end_goal].strip(" .?!")) or suy_ra_cum)
                      and (cham < 0 or _SAU_VIEC_KE_TIEP.fullmatch(remaining[cham - a + 1:])))
            else:
                ok = _SAU_VIEC_KE_TIEP.fullmatch(remaining)
            if not ok:
                raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                             "việc kế tiếp trong yêu cầu chưa được đọc trọn (có thể đổi giả thiết); không dùng mô hình cũ")
            doc(a, b)
        # A length asserted after the first request, whatever its wording or position ("… tính lại SC với SA = 5"), is a
        # local claim like any other: it must match a validated call.
        for m in lengths:
            if first < m.start() < end and _vai_tro_tai(de, m.start()) not in ("GOAL", "QUESTION"):
                cover(m.start(), m.end())
        du = "".join(" " if x else ch for x, ch in zip(doc_cau, de[start:end]))
        if (phrases or (any(c.spec.kind == "ask" for c in calls) and start >= first_request)) and not _DAN_CAU_HOI.fullmatch(du):
            raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED", f"câu hỏi có phần chưa được đọc ({du.strip()!r}) — có thể đổi đại "
                         "lượng được hỏi; không trả lời một đại lượng khác")
    # Requesting the same object again in a modified form after it was asked ("Tính SC, … tính lại SC", "SC lần nữa",
    # "SC mới") presupposes a changed scope; the ask grammar rejects that form, so its hypothesis is unread. Refuse. A plain
    # repeated ask ("SC bằng bao nhiêu? Tính độ dài SC.") carries no new hypothesis of its own.
    for c in calls:
        if c.spec.kind != "ask":
            continue
        occurrences = _cum_hoi(c, de, 0, len(de), calls)
        asked = [p for p, h in occurrences if _hoi_dung_cum(de, p, h)]
        for p, h in occurrences:
            if not asked or p <= min(asked) or _hoi_dung_cum(de, p, h) or _vai_tro_tai(de, p) == "GOAL":
                continue
            verbs = list(request_verb.finditer(de, _bien_menh_de(de, p)[0], p))
            # a re-request only when the object is the verb's DIRECT object ("tính lại SC"), not named inside another
            # object ("tính góc giữa SC và (ABCD)", "khoảng cách từ A đến SC") — same connector grammar as the ask gate
            if verbs and _GIUA_HOP_LE.fullmatch(re.sub(r"(?<!\w)lại(?!\w)", " ", _bo_cum(de[verbs[-1].end():p]),
                                                       flags=re.IGNORECASE)):
                raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                             f"{c.id}: đối tượng được yêu cầu lại sau lần hỏi đầu — phạm vi giả thiết đã đổi; chưa hỗ trợ", (c.id,))


#: Premise text a call need not quote: lead-ins and connectors between quoted claims (closed).
_NOI_TIEN_DE = re.compile(r"[\s,;:.()\-–]*(?:(?:cho|gọi|biết|rằng|có|và|với|trong đó|là|của|hãy|xét|ta|đồng thời|lần lượt"
                          r"|theo thứ tự|tại|thì|đơn vị|cm|dm|mm|m|đvđd)(?!\w)[\s,;:.()\-–]*)*", re.IGNORECASE)
#: Exam scaffolding at the start of a premise segment ("Bài 3.", "Câu 2:", "a)", "1)", "Câu a:", "(1 điểm)").
_GIAN_DAN = re.compile(r"\s*(?:(?:bài tập|bài|câu|ví dụ)\s*(?:\d+|[a-d])\s*[.:)]|(?:\d+|[a-d])\s*\)"
                       r"|\(\s*\d+(?:[.,]\d+)?\s*điểm\s*\))\s*", re.IGNORECASE)
#: Nouns that only NAME an object next to its label; ROLE nouns also state a role and are accepted only when that role
#: matches a validated call (`_vai_tro_doi_tuong_khop`) — "đường cao SB" is a claim, not a name.
_DANH_TU_TRUNG_TINH = r"mặt phẳng|đường thẳng|đoạn thẳng|đoạn|cạnh|mặt|điểm|độ dài|hình chóp|khối chóp"
_DANH_TU_VAI_TRO = r"cạnh bên|cạnh đáy|mặt đáy|mặt bên|đáy|chiều cao|đường cao|đỉnh"
_TEN_DOI_TUONG = re.compile(rf"(?:(?<![\w'])|(?<=Δ))(?P<danh>(?:(?:{_DANH_TU_VAI_TRO}|{_DANH_TU_TRUNG_TINH})\s+)*)"
                            rf"\(?(?P<nhan>(?-i:[A-Z][0-9]*'?)+(?:\.(?-i:[A-Z][0-9]*'?)+)?)\)?(?![\w'])", re.IGNORECASE)


def _vai_tro_doi_tuong_khop(danh: str, nhan: list[str], calls: tuple[LoiGoi, ...]) -> bool:
    """A role noun next to labels is a claim; accept it only when a validated call already gives that role."""
    vai_tro = [m.group().lower() for m in re.finditer(_DANH_TU_VAI_TRO, danh, re.IGNORECASE)]
    if not vai_tro:
        return True
    khoi = [(c.args.apex, list(c.args.base), []) for c in calls if c.fn in ("pyramid", "regular_pyramid")]
    khoi += [(None, list(c.args.base), list(c.args.top)) for c in calls if c.fn == "prism"]
    s = set(nhan)

    def chu_trinh(v):
        return [{v[i], v[(i + 1) % len(v)]} for i in range(len(v))]
    for r in vai_tro:
        if r == "cạnh bên":
            ok = any(s == {d, b} for d, day, _t in khoi if d for b in day) or any(
                s == {b, t} for _d, day, tren in khoi for b, t in zip(day, tren))
        elif r == "cạnh đáy":
            ok = any(s in chu_trinh(day) for _d, day, _t in khoi)
        elif r in ("đáy", "mặt đáy"):
            ok = any(s == set(day) or (tren and s == set(tren)) for _d, day, tren in khoi)
        elif r == "mặt bên":
            ok = any(d and s == {d} | e for d, day, _t in khoi for e in chu_trinh(day)) or any(
                s == {day[i], day[(i + 1) % len(day)], tren[i], tren[(i + 1) % len(tren)]}
                for _d, day, tren in khoi if tren for i in range(len(day)))
        elif r in ("chiều cao", "đường cao"):
            # a height is stated by a call: line ⊥ base, altitude / projection of the apex, lateral edge of a RIGHT prism,
            # apex → base centre of a REGULAR pyramid (centre named by a centroid or by two long diagonals of the base)
            ok = any(c.fn == "perpendicular_line_plane" and set(c.args.line) == s
                     and any(set(c.args.plane) <= set(day) for _d, day, _t in khoi) for c in calls) or any(
                c.fn == "altitude" and {c.args.apex, c.args.foot} == s for c in calls) or any(
                c.fn == "orthogonal_projection" and {c.args.point, c.args.image} == s and any(
                    d == c.args.point and set(c.args.plane) <= set(day) for d, day, _t in khoi) for c in calls) or any(
                c.fn == "prism" and c.args.right and s in [{b, t} for b, t in zip(c.args.base, c.args.top)]
                for c in calls) or any(
                c.fn == "regular_pyramid" and s in [{c.args.apex, o} for o in _tam_day(c.args.base, calls)] for c in calls)
        else:                                            # đỉnh
            ok = len(s) == 1 and any(s <= ({d} if d else set()) | set(day) | set(tren) for d, day, tren in khoi)
        if not ok:
            return False
    return True


def _tam_day(day: list[str], calls: tuple[LoiGoi, ...]) -> set[str]:
    """Points a call names as the centre of a regular base: its centroid, or the meet of two long diagonals."""
    n = len(day)
    cheo = [{day[i], day[i + n // 2]} for i in range(n // 2)] if n % 2 == 0 else []
    return {c.args.point for c in calls if c.fn == "centroid" and set(c.args.polygon) == set(day)} | {
        c.args.point for c in calls if c.fn == "intersect_line_line" and set(c.args.line1) in cheo
        and set(c.args.line2) in cheo and set(c.args.line1) != set(c.args.line2)}


_GHI_CHU_DAU = r"[\s,;:.()!\-–]*(?:(?:lưu ý|chú ý|ghi chú|gợi ý)\s*[:,-]?\s*)?"
_GHI_CHU_TRINH_BAY = re.compile(
    rf"{_GHI_CHU_DAU}(?:hãy\s+)?(?:(?:trình bày|giải|viết|ghi|nêu)\s+(?:lời giải|bài toán)(?:\s+(?:ngắn gọn|đầy đủ|chi tiết|rõ ràng))*"
    r"|vẽ\s+hình(?:\s+(?:minh hoạ|minh họa))?)[\s,;:.()!\-–]*",
    re.IGNORECASE,
)
#: Closed sentence grammar for note / result-instruction sentences (never a bag-of-words Kleene star; verified by `_kiem_ghi_chu`).
_GHI_CHU = re.compile(
    rf"{_GHI_CHU_TRINH_BAY.pattern}"
    rf"|{_GHI_CHU_DAU}(?:(?:hãy\s+)?(?:làm\s+tròn|ghi|viết|nêu|để|lấy)\s+(?:kết\s+quả|đáp\s+số|đến\b)[^.!?;]*"
    rf"|(?:kết\s+quả|đáp\s+số|đơn\s+vị)\b[^.!?;]*)[\s,;:.()!\-–]*",
    re.IGNORECASE,
)


def _kiem_vung_tien_de(calls: tuple[LoiGoi, ...], de: str, het: int, read_quotes: tuple[str, ...] = (),
                       don_vi_de: set[str] | None = None) -> None:
    """Premise source coverage over `de[:het]` (the text before the first request), one obligation per sentence / ";"
    clause. Outside sentence-local quotes of validated calls, only closed connectors and names of objects the calls use
    may remain (a note made only of closed note words and exam scaffolding are exempt); a goal clause is exempt up to
    the gate's own given / condition markers, and a length it asserts may not contradict a validated value; every number
    must sit inside the quote of a call that carries that value. A quote spanning sentences covers only what its call's
    binding grammar reads. `read_quotes` (route-B goals / negated clauses) count only where the gate itself reads a goal
    or a negation — never on the AI's role label. Bounded: a shape / scale claim with no number hidden inside a long
    quote of another call is not detected. Reuses the gate's readers; no second fact state — only refuses."""
    if het <= 0:
        return
    if don_vi_de is None:
        don_vi_de = _don_vi_met_cua_de(de)
    phu = [False] * het                                  # covered by a validated call
    doc = [False] * het                                  # read by the gate as a goal / negated clause
    rang: list[tuple[int, int, tuple, tuple[int, str]]] = []  # range, value, owning call field
    for ci, c in enumerate(calls):
        gt = [(f, doc_so(v)) for f in c.spec.value_fields if (v := getattr(c.args, f, None))]
        for q in c.quotes:
            if (vt := _vi_tri(de, q)) is None or vt[0] >= het:
                continue
            rang += [(vt[0], vt[1], v, (ci, f)) for f, v in gt]
            nhip = [vt]
            if re.search(r"[.!?;]\s", de[vt[0]:vt[1]].rstrip()):
                # a quote spanning sentences covers only what its call's own binding grammar reads in it
                # ("(MAB) cắt hình chóp … theo một thiết diện. Tính diện tích thiết diện đó.")
                nhip = ([(m.start(), m.end()) for mau in (*_CAT_BOI, _GIAO_TUYEN) for m in mau.finditer(de, *vt)]
                        if c.fn in ("section", "ask_section_area", "intersection_line") else [])
            for x, y in nhip:
                phu[x:min(y, het)] = [True] * max(0, min(y, het) - x)
    for q in read_quotes:
        if (vt := _vi_tri(de, q)) is None or vt[0] >= het or re.search(r"[.!?;]\s", de[vt[0]:vt[1]].rstrip()):
            continue
        x, y = vt
        if (mo := _MO_MUC_TIEU.search(de, x, y)) and de[x:mo.start()].strip(" ,;:"):
            x = mo.start()                               # read only from the goal opener on, never what precedes it
        if not (_vai_tro_tai(de, max(x, y - 1)) == "GOAL" or _phu_dinh(de, x, q)):
            continue                                     # a "prove" label on a plain premise reads nothing
        if (k := _ket_muc_tieu(de, x, y)) is not None:
            y = k                                        # read only up to its first given / condition
        doc[x:min(y, het)] = [True] * max(0, min(y, het) - x)
    dung = {n for c in calls for n in nhan_cua_loi_goi(c)}
    da_dung: set[tuple[int, str]] = set()                 # call fields already backing a number, across all their quotes
    dau = 0
    for m in [*re.finditer(r"(?<=[.!?;])\s+", de[:het]), None]:
        cuoi = m.start() if m else het
        a, b = dau, cuoi
        dau = m.end() if m else het
        if not de[a:b].strip():
            continue
        gd = _GIAN_DAN.match(de, a, b)
        a0 = gd.end() if gd else a
        if (_GHI_CHU.fullmatch(de, a0, b) and not _tu_nhan(de[a0:b])
                and not re.search(r"(?<![a-zA-Z\^])\d+(?![\d\s]*chữ số)", de[a0:b], re.I)
                and not re.search(r"(?<!\w)(?:bỏ|thay|đổi|tăng|giảm|phóng|nhân|chia|gấp|nửa|mọi|kích thước|giả thiết)(?!\w)", de[a0:b], re.I)):
            if not _kiem_ghi_chu(de[a0:b], calls, don_vi_de):
                raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                             "ghi chú về kết quả/đơn vị không khớp chính sách đơn vị hoặc làm tròn")
            continue                                     # a validated note in closed sentence structure only
        if _mo_muc_tieu(de, a0, b):
            # a goal is something to show, never a hypothesis — up to the first given / condition marker or clause
            # boundary not opening a chained goal; a length it states may not contradict a validated value ("Suy ra SA = 5")
            k = _ket_muc_tieu(de, a0, b)
            for d in _DO_DAI_CUC_BO.finditer(de, a0, b if k is None else k):
                if not _DUOI_BANG.match(de[d.end():]):
                    continue
                v = _doc(d)
                for seg in [p for _x, _y, parts in _tu_nhan(de[d.start():d.start("number")]) for p in parts if len(p) == 2]:
                    if v is not None and (cand := _nguon_do_dai_cuc_bo(calls, seg)) and all(w != v for w, _i in cand):
                        raise TuChoi("INCONSISTENT_FACTS", "điều phải chứng minh nêu một độ dài khác giá trị đã xác thực")
            if k is None:
                continue
            a0 = k
        ten = set()
        for t in _TEN_DOI_TUONG.finditer(de, a0, b):
            nh = [n for _x, _y, phan in _tu_nhan(t["nhan"]) for p in phan for n in p]
            if set(nh) <= dung and _vai_tro_doi_tuong_khop(t["danh"], nh, calls):
                ten |= set(range(t.start(), t.end()))
        con = "".join(" " if phu[i] or doc[i] or i in ten else de[i] for i in range(a0, b))
        if not _NOI_TIEN_DE.fullmatch(con):
            raise TuChoi("SOURCE_PREMISE_UNREAD", f"tiền đề {de[a0:b].strip()!r} chưa được lời gọi nào đọc — có thể đổi "
                         "hình; không dùng mô hình cũ")
        for p, *v in so_trong(de[a0:b]):
            # each call value backs ONE occurrence inside its own quote ("SA = 3, đổi AB thành 3" has one too many)
            hop = next((r for r in rang if r[0] <= a0 + p < r[1] and r[2] == tuple(v) and r[3] not in da_dung), None)
            if not doc[a0 + p] and hop is None:
                raise TuChoi("SOURCE_PREMISE_UNREAD", f"giá trị trong tiền đề {de[a0:b].strip()!r} không nằm trong quote của "
                             "lời gọi mang giá trị ấy — không dùng mô hình cũ")
            if hop is not None:
                da_dung.add(hop[3])


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
    if r.kind in ('prism','right_prism') and c.fn == 'prism':
        return ids(a.base+a.top) == e and (r.kind == 'prism' or a.right)
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
#: Next task / method after an asked phrase. The ask grammar stops reading here, so the source-coverage gate must read what
#: follows (`_kiem_du_kien_cau_hoi`): one constant, two consumers.
_VIEC_KE_TIEP = r"rồi|sau đó|từ đó|tiếp theo|tiếp đó|bằng cách"
#: A rounding instruction, read whole in closed words ("làm tròn kết quả đến hàng phần trăm"); "làm tròn sau khi …" is not.
_LAM_TRON = (r"(?:kết quả\s+)?làm tròn(?:\s+kết quả)?(?:\s+(?:đến|tới)\s+(?:hàng\s+(?:phần\s+(?:mười|trăm|nghìn)|đơn vị)"
             r"|\d{1,2}\s+chữ\s+số(?:\s+thập\s+phân)?(?:\s+sau\s+dấu\s+phẩy)?"
             r"|chữ\s+số\s+thập\s+phân\s+thứ\s+(?:nhất|hai|ba|\d)"
             r"|0[.,]0*\d))?")
_VIEC_KE_TIEP_RE = re.compile(rf"(?<!\w)(?:{_VIEC_KE_TIEP})(?!\w)", re.IGNORECASE)
#: Where a goal clause ends (premise coverage): the gate's own given / condition / next-task markers (`_DUNG_GAN`,
#: `_DIEU_KIEN`, `_VIEC_KE_TIEP`), contrast and joining words, and the clause boundary — no separate vocabulary.
_KET_MUC_TIEU = re.compile("|".join((_DUNG_GAN.pattern, _DIEU_KIEN.pattern, _VIEC_KE_TIEP_RE.pattern,
                                     r"(?<!\w)(?:đồng thời|trường hợp|lúc|sau khi|mà|nhưng|tuy nhiên"
                                     r"|do|vì|bởi vì|nhờ|còn|ngoài ra)(?!\w)", r"[,;:]")),
                           re.IGNORECASE)
#: Between one goal and the next ("… rồi suy ra …", ", từ đó suy ra …") and before a goal ("Hãy / Em hãy / Từ đó …").
_NOI_MUC_TIEU = re.compile(r"[\s,;:]*(?:(?:và|rồi|từ đó|sau đó|tiếp theo|tiếp đó|đồng thời|do đó|vì vậy|vì thế|nên|ta|hãy"
                           r"|em|vậy)(?!\w)[\s,:]*)*",
                           re.IGNORECASE)


def _mo_muc_tieu(de: str, a: int, b: int) -> re.Match | None:
    """The goal opener of `de[a:b]`, after closed lead-in words only."""
    return _MO_MUC_TIEU.match(de, _NOI_MUC_TIEU.match(de, a, b).end(), b)


def _ket_muc_tieu(de: str, a: int, b: int) -> int | None:
    """Where the goal clause starting at `a` ends: its first `_KET_MUC_TIEU` marker NOT followed by another goal
    (a chained goal is a goal too, read the same way); None when it runs to `b`."""
    while k := _KET_MUC_TIEU.search(de, a, b):
        if not (mo := _mo_muc_tieu(de, k.start(), b)):
            return k.start()
        a = mo.end()
    return None


#: What a follow-up task may contain once its assertions are covered: given words, a comparison of named objects, a
#: rounding instruction. Closed: a change written in any other words ("tăng SA gấp đôi", "thay SA bằng SB") is unread.
_SAU_VIEC_KE_TIEP = re.compile(
    r"[\s,;:.?!]*(?:(?:biết|rằng|với|cho|trong đó|có|và|cạnh|độ dài|đoạn thẳng|so sánh|kết quả|đó|này|nó"
    r"|tô màu|quan sát|xoay|thiết diện|hình|từ|nhiều|góc nhìn|các"                       # trình bày cảnh, không đổi hình
    rf"|{_VIEC_KE_TIEP.replace('|bằng cách', '')}"          # a further connector opens its own follow-up span, read there
    rf"|{_LAM_TRON}|(?-i:[A-Z][0-9]*'?)+)(?![\w'])[\s,;:.?!]*)*",
    re.IGNORECASE)
#: A follow-up that opens with a goal word is something to show, not a hypothesis (same words as `_MUC_TIEU`).
_MO_MUC_TIEU = re.compile(r"[\s,;:]*(?:" + "|".join(map(re.escape, _MUC_TIEU)) + r")(?!\w)(?:\s+rằng(?!\w))?\s*:?", re.IGNORECASE)
#: "bằng cách …": only a named formula / theorem followed by a symbolic expression (ASCII symbols, no words of a change).
_PHUONG_PHAP = re.compile(r"\s*(?:dùng|áp dụng|sử dụng)\s+(?:công thức|định lí|định lý|hệ thức)[\sA-Za-z0-9=+\-*/^().,²³√]*",
                          re.IGNORECASE)
#: Giữa động từ hỏi và cụm (sau khi xoá các cụm hỏi khác): chỉ từ nối.
_GIUA_HOP_LE = re.compile(r"[\s,:]*(?:(?:và|cùng|lần lượt|hãy|các)(?!\w)[\s,:]*)*", re.IGNORECASE)
#: Phần còn lại của một câu hỏi sau khi mọi vùng đã đọc được xoá: chỉ dấu câu, từ nối, lời mở đầu câu và đánh mục.
_DAN_CAU_HOI = re.compile(
    r"[\s,;:.?!]*(?:(?:\(?(?:[a-z]|\d{1,2})\)|(?:câu|ý|phần)\s+(?:[a-z]|\d{1,2})|hơn nữa|ngoài ra|khi đó|từ đó|sau đó|tiếp theo|tiếp đó"
    r"|rồi|do đó|vậy|cuối cùng|và|cùng|hãy|em hãy|các|lần lượt)(?!\w)[\s,;:.?!]*)*", re.IGNORECASE)
_DON_VI_MET = r"(?:cm|dm|mm|(?-i:m))"
_DON_VI = (rf"(?:{_DON_VI_MET}(?:2|\^2|²)|đvdt"
           rf"|{_DON_VI_MET}(?:3|\^3|³)|đvtt"
           rf"|{_DON_VI_MET}|đvđd|độ|radian)")
_LOAI_DON_VI = r"(?:độ dài|diện tích|thể tích|góc)"
#: Lời dặn trong ngoặc — văn phạm ĐÓNG (run `shared-ask-grammar-safety`): chỉ cách làm tròn và đơn vị, nối bằng , ;
#: "(kết quả nhân đôi)", "(đơn vị: một nửa cm)", "(kết quả 3)" đổi hay gán đại lượng được hỏi — không lọt.
_MUC_GHI_CHU = rf"(?:{_LAM_TRON}|đơn vị(?:\s+{_LOAI_DON_VI})?(?:\s*:?\s*{_DON_VI})?|{_DON_VI})"
_GHI_CHU_NGOAC = rf"\(\s*{_MUC_GHI_CHU}(?:\s*[,;]\s*{_MUC_GHI_CHU})*\s*\)"
#: Sau cụm (sau khi xoá các cụm hỏi khác): chỉ những thứ này rồi kết câu / dữ kiện / việc kế tiếp.
_SAU_HOP_LE = re.compile(
    r"(?:[\s,;:]+|(?:và|cùng)(?!\w)|(?:có\s+)?(?:độ dài\s+)?(?:bằng|là)\s+bao\s+nhiêu|dài\s+bao\s+nhiêu|bao\s+nhiêu"
    r"|(?:bằng|là)\s*[?:]"                                                     # đề trắc nghiệm "… bằng?"
    # ngoặc chỉ là LỜI DẶN (làm tròn, đơn vị) — "(sau khi cắt bỏ …)" / "(tính theo đơn vị mới …)" không lọt (review S1)
    rf"|theo\s+(?:{_DON_VI}(?![\w'])|[a-z](?![\w'])|đơn vị(?:\s+{_LOAI_DON_VI})?\s+{_DON_VI}(?![\w']))|{_GHI_CHU_NGOAC}|{_LAM_TRON}(?![\w'])"
    r"|(?:đã cho|đó|này|trên)(?!\w)"
    r"|của\s+(?:hình|khối)\s+(?:chóp|lăng trụ|lập phương|hộp|tứ diện)(?:\s+(?-i:[A-Z][0-9]*'?)+(?:\.(?-i:[A-Z][0-9]*'?)+)?)?)*"
    # kết: dấu câu THẬT (sau nó là khoảng trắng / hết đề — "SC.SA" không kết), dữ kiện, việc kế tiếp, lời dặn làm tròn
    rf"(?:[.?!](?=\s|$)|$|(?:biết|với|cho|trong đó|{_VIEC_KE_TIEP})(?!\w))", re.IGNORECASE)
#: "V" đã được đề định nghĩa ("Gọi V là …", "V = …", "V(S.MAB)") — không buộc mặc nhiên vào khối duy nhất (review S1, I4).
_V_DINH_NGHIA = re.compile(r"(?<![\w'])(?-i:V)\s*(?:là|=|\()", re.IGNORECASE)

_CHIEU_HAM_HOI = {
    "ask_length": "length",
    "ask_distance_point_plane": "length",
    "ask_distance_lines": "length",
    "ask_area": "area",
    "ask_section_area": "area",
    "ask_volume": "volume",
    "ask_angle_line_plane": "angle",
    "ask_angle_plane_plane": "angle",
}
_LOAI_DON_VI_MAP = {
    "độ dài": "length",
    "diện tích": "area",
    "thể tích": "volume",
    "góc": "angle",
}
_DON_VI_MET_GIVEN_RE = re.compile(
    rf"(?:{_SO.pattern}\s*(?:\(\s*(?:đơn vị(?:\s+độ dài)?\s*:?\s*)?)?(?P<u1>{_DON_VI_MET})"
    rf"|đơn vị\s+độ dài\s+là\s+(?P<u2>{_DON_VI_MET}))(?![\w'²³23^])",
    re.IGNORECASE,
)


def _don_vi_met_cua_de(de: str) -> set[str]:
    """Explicit metric length base scales (`cm`, `dm`, `mm`, `m`) stated on given quantities in `de`."""
    return {(m["u1"] or m["u2"]).lower() for m in _DON_VI_MET_GIVEN_RE.finditer(de)}


def _co_tham_so_a(calls: tuple[LoiGoi, ...]) -> bool:
    """True when all value-carrying calls declare symbolic parameter `a` (same authority as `engine._don_vi`)."""
    co_a = [doc_so(v)[1] for c in calls for f in c.spec.value_fields if (v := getattr(c.args, f, None)) is not None]
    return bool(co_a) and all(co_a)


def _phan_loai_don_vi(u: str) -> tuple[str, str | None]:
    u = u.strip().lower()
    if u in ("độ", "radian"):
        return "angle", None
    if u == "đvđd":
        return "length", None
    if u == "đvdt":
        return "area", None
    if u == "đvtt":
        return "volume", None
    m = re.fullmatch(r"(cm|dm|mm|m)(?:(2|\^2|²)|(3|\^3|³))?", u)
    if not m:
        return "unknown", None
    if m[2]:
        return "area", m[1]
    if m[3]:
        return "volume", m[1]
    return "length", m[1]


_GHI_CHU_THANG_DO = re.compile(
    rf"{_GHI_CHU_DAU}đơn\s+vị(?:\s+độ\s+dài)?\s+là\s+(?P<u>{_DON_VI_MET})[\s,;:.()!\-–]*",
    re.IGNORECASE,
)
_GHI_CHU_DON_VI_KET_QUA = re.compile(
    rf"{_GHI_CHU_DAU}(?:(?:kết\s+quả|đáp\s+số)\s+(?:ghi|viết|để|tính)\s+(?:ở|theo)\s+đơn\s+vị\s+(?P<u1>{_LOAI_DON_VI}|{_DON_VI})"
    rf"|đơn\s+vị\s+(?:của\s+)?(?:kết\s+quả|đáp\s+số)\s+là\s+(?P<u2>{_LOAI_DON_VI}|{_DON_VI}))[\s,;:.()!\-–]*",
    re.IGNORECASE,
)


def _kiem_ghi_chu(note: str, calls: tuple[LoiGoi, ...], don_vi_de: set[str]) -> bool:
    """Closed sentence-level validation for note sentences (`_GHI_CHU`): no permissive default return True."""
    if _GHI_CHU_TRINH_BAY.fullmatch(note):
        return True
    if m_scale := _GHI_CHU_THANG_DO.fullmatch(note):
        return not bool(don_vi_de - {m_scale["u"].lower()})
    m_res = _GHI_CHU_DON_VI_KET_QUA.fullmatch(note)
    ask_calls = [c for c in calls if c.spec.kind == "ask"]
    if not m_res or not ask_calls:
        return False
    dims = {_CHIEU_HAM_HOI.get(c.fn) for c in ask_calls}
    if len(dims) != 1:
        return False
    chieu = next(iter(dims))
    if chieu not in ("length", "area", "volume"):
        return False
    tok = re.sub(r"\s+", " ", (m_res["u1"] or m_res["u2"]).strip().lower())
    if tok in _LOAI_DON_VI_MAP:
        return _LOAI_DON_VI_MAP[tok] == chieu
    dim, base = _phan_loai_don_vi(tok)
    return dim == chieu and (base is None or don_vi_de == {base})


def _kiem_don_vi_hoi(fn: str, de: str, a: int, b: int, don_vi_de: set[str],
                     calls: tuple[LoiGoi, ...] = ()) -> bool:
    """Validate unit, parameter, and formatting annotations in the closed tail of asked object `de[a:b]`."""
    chieu = _CHIEU_HAM_HOI.get(fn)
    vung = _vung_hoi(de, a, b)
    if chieu is None or vung is None:
        return True
    if chieu == "angle" and re.match(r"số\s+đo\b", de[a:b], re.IGNORECASE):
        return False
    duoi_raw = de[b:vung[1]]
    patterns = (*(mau for ds in _CUM_HOI.values() for mau, _b in ds), _KHOANG_CACH_DIEM_DUONG,
                _KHOANG_CACH_GIAO_TUYEN, _CUM_HOI_THIET_DIEN_PHU)
    other = sorted((m.start(), m.end()) for mau in patterns for m in mau.finditer(duoi_raw) if m.end() > m.start())
    before_next = duoi_raw[:other[0][0]] if other else duoi_raw
    after_last = duoi_raw[max(y for _x, y in other):] if other else ""
    has_unit_re = re.compile(
        rf"theo\s+(?:{_DON_VI}|[a-z]|đơn vị)\b|{_LAM_TRON}|\(\s*(?:[^()]*\bđơn vị\b|[^()]*\b{_DON_VI}(?![\w']))",
        re.IGNORECASE,
    )
    seg = before_next if (not other or has_unit_re.search(before_next)) else after_last
    if re.search(_LAM_TRON, seg, re.IGNORECASE):
        return False
    bases: set[str] = set()
    for m in re.finditer(
        rf"theo\s+(?:đơn vị(?:\s+(?P<kind>{_LOAI_DON_VI}))?\s+(?P<u>{_DON_VI})|(?P<ub>{_DON_VI})|(?P<sym>[a-z]))(?![\w'])",
        seg,
        re.IGNORECASE,
    ):
        if m["u"]:
            if m["kind"] and _LOAI_DON_VI_MAP.get(re.sub(r"\s+", " ", m["kind"].lower())) != chieu:
                return False
            dim, base = _phan_loai_don_vi(m["u"])
            if dim == "angle" or dim != chieu or (base and (don_vi_de - {base})):
                return False
            if base:
                bases.add(base)
        elif m["ub"]:
            dim, base = _phan_loai_don_vi(m["ub"])
            if dim == "angle" or dim != chieu or not (base and don_vi_de == {base}):
                return False
            bases.add(base)
        elif m["sym"]:
            if m["sym"].lower() != "a" or not _co_tham_so_a(calls) or chieu not in ("length", "area", "volume"):
                return False
    for ngoac in re.finditer(r"\(([^()]*)\)", seg):
        for muc in re.split(r"\s*(?:;|,(?!\d))\s*", ngoac[1].strip()):
            if not muc:
                continue
            if re.fullmatch(_LAM_TRON, muc, re.IGNORECASE):
                return False
            mm = re.fullmatch(rf"đơn vị(?:\s+(?P<kind>{_LOAI_DON_VI}))?(?:\s*:?\s*(?P<u>{_DON_VI}))?|(?P<ub>{_DON_VI})",
                              muc, re.IGNORECASE)
            if not mm or chieu == "angle":
                return False
            if mm["kind"]:
                if _LOAI_DON_VI_MAP.get(re.sub(r"\s+", " ", mm["kind"].lower())) != chieu:
                    return False
            elif not (mm["u"] or mm["ub"]):
                if chieu not in ("length", "area", "volume"):
                    return False
            if tok := (mm["u"] or mm["ub"]):
                dim, base = _phan_loai_don_vi(tok)
                if dim == "angle" or dim != chieu or (base and (don_vi_de - {base})):
                    return False
                if base:
                    bases.add(base)
    return len(don_vi_de | bases) <= 1


_QUAN_HE_BOI_SO = re.compile(
    rf"(?P<lhs>(?:(?:độ dài|cạnh|đoạn(?:\s+thẳng)?)\s+)?{_P1}{_P1})\s+"
    rf"(?:(?:=|bằng|là)\s+(?:gấp\s+(?:đôi|ba)|một\s+nửa|nửa|(?:một|hai|ba|bốn|năm|sáu|\d+)\s+lần|{_SO.pattern}(?:\s+lần)?)\s+"
    rf"|gấp\s+(?:đôi|ba|(?:một|hai|ba|bốn|năm|sáu|\d+)\s+lần)\s+)"
    rf"(?P<rhs>(?:(?:độ dài|cạnh|đoạn(?:\s+thẳng)?)\s+)?{_P1}{_P1})(?![\w'])",
    re.IGNORECASE,
)
_VI_TU_MUC_TIEU = re.compile(
    r"[⊥∥=<>≥≤]|(?<!\w)(?:vuông góc|song song|cắt|trùng|thuộc|nằm trên|đi qua|cách đều|đồng phẳng|chéo nhau"
    r"|cân|đều|vuông|nhọn|tù|bằng|lớn hơn|nhỏ hơn|bé hơn|là)(?!\w)",
    re.IGNORECASE,
)
_THAN_MUC_TIEU_CON = re.compile(
    rf"[\s,.:()⊥∥=<>≥≤Δ]*(?:(?:rằng|là|vuông góc|song song|cắt|trùng|thuộc|nằm trên|đi qua|cách đều|đồng phẳng|chéo nhau"
    rf"|nhau|bằng\s+(?:một|hai|ba|bốn|\d+)\s+cách"
    rf"|cân|đều|vuông|nhọn|tù|tại|với|và|hoặc|của|hai|các|mặt phẳng|mp|đường thẳng|đoạn thẳng|tam giác|tứ giác"
    rf"|hình|khối|chóp|lăng trụ|lập phương|hộp|tứ diện|đáy|cạnh|bên|độ dài|khoảng cách|diện tích|thể tích|góc"
    rf"|bằng|lớn hơn|nhỏ hơn|bé hơn|{_SO.pattern})(?![\w'])[\s,.:()⊥∥=<>≥≤Δ]*)*",
    re.IGNORECASE,
)


def _than_muc_tieu_hop_le(body: str, dung: set[str]) -> bool:
    """Closed geometric goal body: must name at least one geometric object and form a complete relational/property statement."""
    body = body.replace("Δ", " ")
    body = _QUAN_HE_BOI_SO.sub(
        lambda m: f"{m['lhs']} = {m['rhs']}" if set(_nhan_cum(m["lhs"]) + _nhan_cum(m["rhs"])) <= dung else m.group(),
        body,
    )
    if not _VI_TU_MUC_TIEU.search(body) or not (_tu_nhan(body) or _bo_cum(body) != body):
        return False
    if re.search(r"(?:[=<>≥≤⊥∥]|(?<!\w)(?:và|hoặc|với|tại|của|bằng|là|vuông góc|song song|lớn hơn|nhỏ hơn|bé hơn))\s*$",
                 body.strip(" .?!"), re.IGNORECASE):
        return False
    no_cach = re.sub(r"(?<!\w)bằng\s+(?:một|hai|ba|bốn|\d+)\s+cách(?!\w)", " ", body, flags=re.IGNORECASE)
    for m_so in _SO.finditer(no_cach):
        if _doc(m_so) is not None and not re.search(
                r"(?:[=<>≥≤]|(?<!\w)(?:bằng|lớn hơn|nhỏ hơn|bé hơn))\s*$", no_cach[:m_so.start()], re.IGNORECASE):
            return False
    con = list(_bo_cum(body))
    for t in _TEN_DOI_TUONG.finditer("".join(con)):
        nh = [n for _x, _y, phan in _tu_nhan(t["nhan"]) for p in phan for n in p]
        if nh and set(nh) <= dung:
            con[t.start():t.end()] = " " * (t.end() - t.start())
    return bool("".join(con).strip() or body.strip()) and bool(_THAN_MUC_TIEU_CON.fullmatch("".join(con)))


def _doc_muc_tieu_cau_hoi(de: str, a: int, b: int, dung: set[str]) -> list[tuple[int, int]]:
    """Read closed geometric goal clauses starting at `de[a:b]`, stopping at clause boundaries (`_KET_MUC_TIEU`)."""
    mo = _mo_muc_tieu(de, a, b)
    if not mo:
        return []
    spans: list[tuple[int, int]] = []
    cur_start, cur = a, mo.end()
    while True:
        pos = cur
        while (k := _KET_MUC_TIEU.search(de, pos, b)) and k.group().lower() == "với" and re.search(
                r"(?:vuông góc|song song|hợp|tạo|giao|trùng|cùng|so sánh)\s+$", de[cur:k.start()], re.IGNORECASE):
            pos = k.end()
        end_clause = k.start() if k else b
        if not k and (m_va := re.search(r"\s+và\s*$", de[cur:end_clause], re.IGNORECASE)):
            end_clause = cur + m_va.start()
        if not _than_muc_tieu_hop_le(de[cur:end_clause], dung):
            return spans
        spans.append((cur_start, end_clause))
        if not k:
            return spans
        if mo_next := _mo_muc_tieu(de, k.start(), b):
            cur_start, cur = k.start(), mo_next.end()
        elif k.group() == ",":
            cur_start, cur = k.start(), k.end()
        else:
            return spans


_CUM_DINH_NGHIA_DIEM = re.compile(
    rf"(?:(?:(?:gọi|lấy|cho|dựng|vẽ|xác định|tìm)\s+)?(?:điểm\s+)?{_P1}\s+là\s+"
    rf"(?:trung điểm(?:\s+của)?(?:\s+(?:đoạn(?:\s+thẳng)?|cạnh(?:\s+bên|\s+đáy)?))?\s+{_P1}{_P1}"
    rf"|trọng tâm(?:\s+của)?(?:\s+(?:tam giác|tứ giác|đa giác|mặt\s+đáy|đáy))?\s+\(?{_NHOM_NHAN}\)?"
    rf"|hình chiếu(?:\s+vuông góc)?\s+của\s+(?:điểm\s+|đỉnh\s+)?{_P1}\s+(?:lên|trên)\s+(?:{_MAT_TOAN_HANG}|(?:đường thẳng\s+|cạnh\s+)?{_P1}{_P1}|{_GIAO_TUYEN.pattern})"
    rf"|giao điểm\s+của\s+[^,.;!?]+)"
    rf"|hình chiếu(?:\s+vuông góc)?\s+của\s+(?:điểm\s+|đỉnh\s+)?{_P1}\s+(?:lên|trên)\s+(?:{_MAT_TOAN_HANG}|(?:đường thẳng\s+|cạnh\s+)?{_P1}{_P1})\s+là\s+(?:điểm\s+|trọng tâm\s+|trung điểm\s+)?{_P1})[.\s]*",
    re.IGNORECASE,
)
_CUM_DUNG_THIET_DIEN = re.compile(
    rf"(?:xác định|tìm|dựng|vẽ)\s+thiết diện(?:\s+của{_khoi_cum('k')})?\s+"
    rf"(?:(?:khi\s+|bị\s+)?(?:cắt bởi|tạo bởi)|với|do)\s+{_mat_cum('m')}"
    rf"(?:\s+(?:của|và|cắt){_khoi_cum('j')})?",
    re.IGNORECASE,
)
_CUM_DUNG_HINH_CHIEU = re.compile(
    rf"(?:dựng|vẽ|xác định|tìm)\s+hình chiếu(?:\s+vuông góc)?(?:\s+(?P<img>{_P1}))?\s+của\s+"
    rf"(?:(?:điểm|đỉnh)\s+)?(?P<p>{_P1})(?![\w'])\s+(?:lên|trên)\s+(?:{_mat_cum('m')}|{_doan_cum('d')})",
    re.IGNORECASE,
)


def _doc_phep_dung_cau_hoi(de: str, start: int, end: int, calls: tuple[LoiGoi, ...],
                           dung: set[str], khoi: dict[str, frozenset], phu: set[str] = frozenset()) -> list[tuple[int, int]]:
    """Validated construction / point-definition spans in `de[start:end]` that precede or accompany an ask."""
    spans: list[tuple[int, int]] = []
    for c in calls:
        if c.fn in ("midpoint", "centroid", "orthogonal_projection", "orthogonal_projection_line",
                    "intersect_line_line", "intersect_line_plane"):
            for q in c.quotes:
                if (vt := _vi_tri(de, q)) is not None and start <= vt[0] and vt[1] <= end:
                    if _CUM_DINH_NGHIA_DIEM.fullmatch(de[vt[0]:vt[1]]):
                        spans.append(vt)
        elif c.fn == "intersection_line":
            for q in c.quotes:
                if (vt := _vi_tri(de, q)) is not None and start <= vt[0] and vt[1] <= end:
                    for m in _CUM_DUNG_GIAO_TUYEN.finditer(de, vt[0], vt[1]):
                        spans.append((m.start(), m.end()))
    sec_calls = [c for c in calls if c.fn in ("section", "ask_section_area") and mat_cat_dung_nguon(c, calls)]
    if sec_calls:
        for m in _CUM_DUNG_THIET_DIEN.finditer(de, start, end):
            if any(_cung_mat(_mat_cua(m, "m", khoi), c.args.plane) and _khoi_thiet_dien(m, c.args, khoi) for c in sec_calls):
                spans.append((m.start(), m.end()))
        for m in _CAT_BOI[3].finditer(de, start, end):
            if any(_cung_mat(frozenset(_nhan_cum(m[1] or m[2])), c.args.plane) for c in sec_calls):
                spans.append((m.start(), m.end()))
    if any(c.id in phu and c.fn in ("section", "ask_section_area") for c in calls):
        for pat in (_CUM_DUNG_MAT_PHU, _CUM_DUNG_THIET_DIEN_PHU):
            for m in pat.finditer(de, start, end):
                spans.append((m.start(), m.end()))
    for m in _CUM_DUNG_HINH_CHIEU.finditer(de, start, end):
        if m["p"] not in dung or (m["img"] and m["img"] not in dung):
            continue
        mat = _mat_cua(m, "m", khoi)
        if (mat is not None and len(mat) >= 3 and mat <= dung) or (m["d"] and set(_nhan_cum(m["d"])) <= dung):
            spans.append((m.start(), m.end()))
    return spans



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


#: "(P) đi qua M và song song với (ABCD)" — a plane defined by a verified point and a reference plane, possibly unnamed when
#: written inside the section phrase. Groups: ten, diem, then the three operand groups of `_MAT_TOAN_HANG` (3, 4, 5).
_QUA_SONG_SONG = re.compile(
    rf"(?:(?:mặt phẳng|mp)\s*)?(?:\((?P<ten>{_P1}|[α-ω])\)\s*)?(?:là\s+mặt phẳng\s+)?(?:đi\s+)?qua\s+(?:điểm\s+)?"
    rf"(?P<diem>{_P1})(?![\w'])\s*,?\s*(?:và\s+)?song song\s+(?:với\s+)?" + _MAT_TOAN_HANG, re.IGNORECASE)
_DAN_THIET_DIEN = rf"thiết diện\s+(?:của\s+)?{_KHOI_NGU}(?:với|cắt bởi|tạo bởi|bởi)\s+"
#: The definition sentence ends right after the reference plane (a real sentence end — ";" is not one), or its rest is
#: exactly the section request on the named plane. Anything else ("… và song song với (SBC)", "; (P) vuông góc với SC",
#: "(P) cắt SB tại N") is an unread condition on the plane — refused, not ignored.
_HET_CAU = re.compile(r"[.?!](?=\s|$)")
_TU_THIET_DIEN = len("thiết diện")


def _het_dinh_nghia(s: str, cuoi: int, m: re.Match) -> bool:
    """`s`: the SOURCE (with the quote normalised in place); `cuoi`: where the definition ends in it. The rest of the source
    sentence is read, whatever the quote's extent (a quote cut after the operand never hides "… và song song với …")."""
    het = _HET_CAU.search(s, cuoi)
    con = s[cuoi:het.start() if het else len(s)]
    if not con.strip():
        return True
    return bool(m["ten"]) and re.fullmatch(
        rf"\s*[,;]?\s*(?:(?:và|rồi|sau đó)\s+)?(?:hãy\s+)?(?:xác định|tìm|tính)(?:\s+diện tích(?:\s+của)?)?\s+{_DAN_THIET_DIEN}"
        rf"(?:(?:mặt phẳng|mp)\s*)?\({re.escape(m['ten'])}\)\s*", con, re.IGNORECASE) is not None
_HOI_DIEN_TICH_THIET_DIEN = re.compile(r"diện tích\s+(?:của\s+)?thiết diện", re.IGNORECASE)
#: "thiết diện đó / này / trên" closing the asked object (matched right after the word "thiết diện").
_DAI_TU_THIET_DIEN = re.compile(r"\s+(?:đó|này|trên)(?![\w'])\s*(?:(?:có\s+)?(?:bằng|là)\s+bao\s+nhiêu\s*)?(?:[.?!,;](?=\s|$)|\?|$)",
                                re.IGNORECASE)


def _khoi_trong_quote(c: LoiGoi, khoi: dict[str, frozenset]) -> bool:
    """Solid symbol written in the quote is the call's solid; with no symbol the problem has exactly one solid."""
    ky_hieu = {"".join(phan[0]) + "." + "".join(phan[1]) for q in c.quotes for _a, _b, phan in _tu_nhan(chuan_hoa(q))
               if len(phan) == 2}
    return c.args.solid in ky_hieu if ky_hieu else len(khoi) == 1


def mat_song_song_dung_nguon(c: LoiGoi, p: str, q: list[str], de: str, calls: tuple[LoiGoi, ...],
                             ten_ra: set[str] | None = None, don_vi_de: set[str] = frozenset()) -> bool:
    """Bounded grammar binding a section to a derived plane: the plane through `p` parallel to (q) is defined in the quotes
    (named "(P)" and referred to by a section phrase, or written inside the section phrase), as a premise, not negated.
    Unknown wording is refused, not guessed. `ten_ra` receives the plane names the source gave, once bound."""
    khoi = _khoi_cua_loi_goi(calls)
    if not _khoi_trong_quote(c, khoi):
        return False
    day = khoi.get(c.args.solid)
    doan = []                                            # (quote chuẩn hoá, vị trí trong đề, đề với quote chuẩn hoá)
    for quote in c.quotes:
        if (vt := _vi_tri(de, quote)) is None:
            return False
        qn = chuan_hoa(quote)
        doan.append((qn, vt[0], de[:vt[0]] + qn + de[vt[1]:]))

    def vai_tro_ok(s: str, pos: int, text: str) -> bool:
        return _vai_tro_tai(s, pos) not in ("GOAL", "CONDITIONAL") and not _phu_dinh(s, pos, text)

    ten_mat = set()
    gan: dict[int, int] = {}                             # vị trí (trong đề) của từ "thiết diện" → cuối cụm thiết diện
    for qn, goc, s in doan:
        for m in _QUA_SONG_SONG.finditer(qn):
            if m["diem"] != p or _tap_mat(m, 3, day) != frozenset(q):
                continue
            if not vai_tro_ok(s, goc + m.start(), m[0]) or not _het_dinh_nghia(s, goc + m.end(), m):
                return False
            if m["ten"]:
                ten_mat.add(m["ten"])
            if noi_gop := re.search(_DAN_THIET_DIEN + r"$", qn[:m.start()], re.IGNORECASE):  # nói gộp trong cụm thiết diện
                gan[goc + noi_gop.start()] = goc + m.end()
            elif not m["ten"]:
                return False                                 # mặt không tên, không nằm trong cụm thiết diện: không gắn được
    # A name defined anywhere in the problem for another point or plane makes "(P)" ambiguous.
    for m in _QUA_SONG_SONG.finditer(de):
        if m["ten"] in ten_mat and (m["diem"] != p or _tap_mat(m, 3, day) != frozenset(q)):
            return False
    for ten in ten_mat:
        mau = [(rf"{_DAN_THIET_DIEN}(?:(?:mặt phẳng|mp)\s*)?\({re.escape(ten)}\)", False),
               (rf"\({re.escape(ten)}\)\s+cắt\s+(?:hình|khối)(?:[^.;]|\.(?=[A-Z]))*?theo\s+(?:một\s+)?thiết diện", True)]
        for qn, goc, s in doan:
            for r, o_cuoi in ((r, o) for x, o in mau for r in re.finditer(x, qn, re.IGNORECASE)):
                if not vai_tro_ok(s, goc + r.start(), r[0]):
                    return False
                gan[goc + (r.end() - _TU_THIET_DIEN if o_cuoi else r.start())] = goc + r.end()
    thiet_dien = bool(gan)
    if c.fn == "ask_section_area":
        # the asked "diện tích thiết diện" must be the section of (P) itself, not some other section in the quotes
        hoi = [(vt[0] + h.start(), vt[0] + h.end()) for quote in c.quotes if (vt := _vi_tri(de, quote))
               for h in _HOI_DIEN_TICH_THIET_DIEN.finditer(chuan_hoa(quote))]
        moi_td = [t.start() for t in re.finditer("thiết diện", de, re.IGNORECASE)]       # in the SOURCE, not the quotes

        def cuoi_cum_p(b: int) -> int | None:
            if b - _TU_THIET_DIEN in gan:
                return gan[b - _TU_THIET_DIEN]
            # "thiết diện đó / này / trên" refers to the nearest section mentioned before it in the source text: it must be
            # the section bound to (P) — a section the extraction left out of the quotes is still seen here
            truoc = [t for t in moi_td if t < b - _TU_THIET_DIEN]
            # … and the anaphor ENDS the asked object
            m_ana = re.match(r"\s+(?:đó|này|trên)(?![\w'])", de[b:], re.IGNORECASE)
            if m_ana and truoc and truoc[-1] in gan:
                return b + m_ana.end()
            return None

        hoi_p = [(a, b_obj) for a, b in hoi if (b_obj := cuoi_cum_p(b)) is not None
                 and _hoi_dung_cum(de, a, b_obj) and _vai_tro_tai(de, a) not in ("GOAL", "CONDITIONAL")]
        if not hoi_p:
            return False
        if not all(_kiem_don_vi_hoi("ask_section_area", de, a, b_obj, don_vi_de, calls) for a, b_obj in hoi_p):
            raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                         f"{c.id}: đơn vị yêu cầu trong câu hỏi không khớp chính sách đơn vị của dữ kiện hoặc loại đại lượng",
                         (c.id,))
    if thiet_dien and ten_ra is not None:
        ten_ra |= ten_mat
    return thiet_dien                                    # chỉ đặt True từ một mệnh đề định nghĩa đã khớp (p, q)


def _kiem_mat_song_song(d: dict, theo_id: dict, de: str, nhan: set[str], chiem: set[str], nhan_da_khai: set,
                        calls: tuple[LoiGoi, ...], ten_mat_phu: dict | None = None,
                        don_vi_de: set[str] = frozenset()) -> set[str]:
    """Declared decomposition `MAT_SONG_SONG`: two fresh labels, two translates of the point along two directions of the
    reference plane, every target section on exactly (point, label₁, label₂), shared quotes, and a source binding."""
    xs, p, q = list(d.get("labels") or []), d.get("point"), list(d.get("parallel_to") or [])
    qs = tuple(d.get("quotes") or ())
    ids = tuple(i for i in (*(d.get("constructs") or ()), *(d.get("targets") or ())) if i)
    dung = [theo_id.get(i) for i in d.get("constructs") or ()]
    dich = [theo_id.get(i) for i in d.get("targets") or ()]
    two = d.get("rule") == MAT_HAI_DUONG
    lines = d.get("lines") or []
    if (len(xs) != 2 or len(set(xs)) != 2 or (not two and len(q) < 3) or len(dung) != 2 or not dich or not qs
            or two and (len(lines) != 2 or any(len(v) != 2 or len(set(v)) != 2 for v in lines) or not d.get("plane_name"))):
        raise TuChoi("AUXILIARY_RULE_MISMATCH", f"mặt phụ qua {p}: khai báo không đủ cho luật {MAT_SONG_SONG}", ids)
    for nhan_moi in xs:
        if nhan_moi in nhan_da_khai:
            raise TuChoi("AUXILIARY_RULE_MISMATCH", f"điểm phụ {nhan_moi} được khai hai lần", ids)
        nhan_da_khai.add(nhan_moi)
        if nhan_moi in chiem:
            raise TuChoi("AUXILIARY_LABEL_COLLISION", f"điểm phụ {nhan_moi} trùng một nhãn của đề", ids)
    huong = lines if two else ([q[0], q[1]], [q[0], q[2]])
    if not (all(c is not None and c.fn == "translate_point" and c.args.point == p and c.args.vector == v
                and c.args.image == x and c.quotes == qs for c, v, x in zip(dung, huong, xs))
            and all(c is not None and c.fn in ("section", "ask_section_area") and c.args.plane == [p, *xs]
                    and c.quotes == qs for c in dich)):
        raise TuChoi("AUXILIARY_RULE_MISMATCH", f"mặt phụ qua {p}: lời gọi không khớp luật {MAT_SONG_SONG}", ids)
    if lac := sorted(({p} | {v for line in huong for v in line}) - nhan):
        raise TuChoi("UNKNOWN_LABEL", f"nhãn {lac} không có trong đề", ids)
    ten_nguon: set[str] = set()
    for c in dich:
        bound = (_mat_hai_duong_dung_nguon(c, p, lines, d["plane_name"], de, calls, don_vi_de) if two else
                 mat_song_song_dung_nguon(c, p, q, de, calls, ten_nguon, don_vi_de))
        if not bound:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: đề không nói thiết diện của {c.args.solid} với mặt phẳng qua {p} "
                         f"song song ({''.join(q)})", ids)
    if two:
        ten_nguon.add(d['plane_name'])
    # The engine names the plane by what the source called it, bound here — never by the auxiliary labels.
    if ten_mat_phu is not None:
        ten_mat_phu[ids[0]] = next(iter(ten_nguon)) if len(ten_nguon) == 1 else None
    return set(ids)


_QUA_HAI_DUONG = re.compile(
    rf"(?:mặt phẳng|mp)\s*\((?P<ten>{_P1})\)\s*(?:đi\s+)?qua\s+(?:điểm\s+)?(?P<diem>{_P1})(?![\w'])"
    rf"\s*,?\s*(?:và\s+)?song song\s+với\s+(?:hai\s+đường thẳng\s+)?"
    rf"(?P<a>{_P1})\s*(?P<b>{_P1})(?![\w'])\s+và\s+(?P<c>{_P1})\s*(?P<d>{_P1})(?![\w'])", re.I)
_QUA_SONG_SONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _QUA_SONG_SONG.pattern)
_QUA_HAI_DUONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _QUA_HAI_DUONG.pattern)
_KHOANG_CACH_GIAO_TUYEN = re.compile(
    rf"khoảng cách\s+từ\s+(?:(?:điểm|đỉnh)\s+)?(?P<p>{_P1})(?![\w'])\s*(?:đến|tới)\s*"
    rf"giao tuyến\s+(?:của\s+)?(?P<a>{_MAT_TOAN_HANG})\s*(?:và|với)\s*(?P<b>{_MAT_TOAN_HANG})",
    re.IGNORECASE,
)
_CUM_HOI_THIET_DIEN_PHU = re.compile(
    rf"diện tích(?:\s+của)?\s+{_DAN_THIET_DIEN}(?:{_QUA_SONG_SONG_ANON}|(?:(?:mặt phẳng|mp)\s*)?\((?:{_P1}|[α-ω])\))",
    re.IGNORECASE,
)
_CUM_DUNG_GIAO_TUYEN = re.compile(
    rf"(?:(?:hãy\s+)?(?:tìm|dựng|xác định)\s+|(?:gọi\s+)?[A-Za-z][A-Za-z0-9]*\s+là\s+){_GIAO_TUYEN.pattern}",
    re.IGNORECASE,
)
_CUM_DUNG_MAT_PHU = re.compile(
    rf"(?:(?:hãy\s+)?(?:gọi|cho|dựng|vẽ|xác định|tìm)\s+)?(?:{_QUA_SONG_SONG_ANON}|{_QUA_HAI_DUONG_ANON})",
    re.IGNORECASE,
)
_CUM_DUNG_THIET_DIEN_PHU = re.compile(
    rf"(?:(?:hãy\s+)?(?:xác định|tìm|dựng|vẽ)\s+{_DAN_THIET_DIEN}(?:{_QUA_SONG_SONG_ANON}|(?:(?:mặt phẳng|mp)\s*)?\((?:{_P1}|[α-ω])\))"
    rf"|(?:(?:mặt phẳng|mp)\s*)?\((?:{_P1}|[α-ω])\)\s+cắt\s+(?:hình|khối)(?:[^.;]|\.(?=[A-Z]))*?theo\s+(?:một\s+)?thiết diện)",
    re.IGNORECASE,
)


def _mat_hai_duong_dung_nguon(c: LoiGoi, point: str, lines: list[list[str]], name: str, de: str,
                            calls: tuple[LoiGoi, ...], don_vi_de: set[str] = frozenset()) -> bool:
    """Closed named definition and direct section reference; no quote/anaphor may rebind another goal."""
    if not _khoi_trong_quote(c, _khoi_cua_loi_goi(calls)):
        return False
    expected = {frozenset(x) for x in lines}
    definitions = [m for m in _QUA_HAI_DUONG.finditer(de) if m['ten'] == name]
    if not definitions:
        return False
    for m in definitions:
        if (m['diem'] != point or {frozenset((m['a'], m['b'])),frozenset((m['c'],m['d']))} != expected
                or _vai_tro_tai(de,m.start()) in ('GOAL','CONDITIONAL') or _phu_dinh(de,m.start(),m[0])
                or not _het_dinh_nghia(de,m.end(),m)
                or not any((vt:=_vi_tri(de,q)) and vt[0]<=m.start() and vt[1]>=m.end() for q in c.quotes)):
            return False
    pattern = re.compile(_DAN_THIET_DIEN + rf"(?:mặt phẳng\s*)?\({re.escape(name)}\)(?!\w)", re.I)
    references=list(pattern.finditer(de))
    allowed=[m.span() for m in definitions+references]
    if any(not any(a<=m.start()<b for a,b in allowed) for m in re.finditer(rf'\({re.escape(name)}\)',de)):
        return False  # every use/definition of the name belongs to this closed construction or section grammar
    request_ok = False
    ask_pattern = re.compile(rf"diện tích\s+(?:của\s+)?{pattern.pattern}", re.I)
    for q in c.quotes:
        vt = _vi_tri(de,q)
        if vt is None:
            return False
        definition_form = rf'(?:hãy\s+)?(?:(?:dựng|gọi|cho)\s+)?{_QUA_HAI_DUONG.pattern}[.\s]*'
        construct_form = rf'(?:hãy\s+)?(?:xác định|tìm)\s+{pattern.pattern}[.\s]*'
        defined = re.fullmatch(definition_form,q,re.I)
        if defined and (defined['ten'] != name or defined['diem'] != point
                        or {frozenset((defined['a'],defined['b'])),frozenset((defined['c'],defined['d']))} != expected):
            return False
        constructed = re.fullmatch(construct_form,q,re.I)
        ask_m = ask_pattern.search(de, *vt)
        vung_ask = _vung_hoi(de, ask_m.start(), ask_m.end()) if ask_m else None
        asked = bool(ask_m and vung_ask and re.fullmatch(rf"(?:{_GIAN_DAN.pattern})?", de[vt[0]:vung_ask[0]], re.I)
                     and vung_ask[1] == _bien_cau(de, ask_m.start())[1])
        if not (defined or constructed or asked):
            return False  # auxiliary quotes cannot license a hidden premise either
        for m in pattern.finditer(de,*vt):
            if _vai_tro_tai(de,m.start()) in ('GOAL','CONDITIONAL') or _phu_dinh(de,m.start(),m[0]):
                continue
            symbols={''.join(parts[0])+'.'+''.join(parts[1]) for _a,_b,parts in _tu_nhan(m[0]) if len(parts)==2}
            if symbols and symbols != {c.args.solid}:
                continue
            if c.fn == 'section':
                tail=_HET_CAU.search(de,m.end())
                if not de[m.end():tail.start() if tail else len(de)].strip() or asked:
                    request_ok = True
            elif asked and ask_m:
                if not _kiem_don_vi_hoi("ask_section_area", de, ask_m.start(), ask_m.end(), don_vi_de, calls):
                    raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                                 f"{c.id}: đơn vị yêu cầu trong câu hỏi không khớp chính sách đơn vị của dữ kiện hoặc loại đại lượng",
                                 (c.id,))
                request_ok = True
    return request_ok


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
    for s in (REGISTRY[n] for n in PROVIDER_FUNCTIONS):
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


def _kiem_nguon_dong(calls, de, phu, read_quotes):
    """Shared closed source subset: refusal only, never a second semantic authority."""
    # New-rule source subset: no proof/inference exemption and no compound quote may hide a second hypothesis.
    # This is a refusal in the SAME source authority, not an inferred fact or another semantic state.
    if read_quotes or _MO_MUC_TIEU.search(de):
        raise TuChoi('SOURCE_PREMISE_UNREAD','lát hai đường chưa nhận mệnh đề chứng minh/suy ra trong nguồn')
    intersection_form = (rf'(?:(?:tìm|dựng|xác định)\s+|gọi\s+[A-Za-z][A-Za-z0-9]*\s+là\s+)'
                         rf'giao tuyến của\s*{_MAT_TOAN_HANG}\s*và\s*{_MAT_TOAN_HANG}[.\s]*')
    for c in calls:
        if c.id in phu:
            continue
        for q in c.quotes:
            vt = _vi_tri(de, q)
            spans = (q, de[slice(*_bien_cau(de, vt[0]))].strip()) if vt else (q,)
            if c.fn == 'intersection_line':
                if not all(re.fullmatch(intersection_form, s, re.I) for s in spans):
                    raise TuChoi('SOURCE_PREMISE_UNREAD','quote giao tuyến có phần chưa được đọc',(c.id,))
                continue
            for s in spans:
                atomic = re.sub(r'(?<!\w)song\s+song(?!\w)',' ',s,flags=re.I)
                if re.search(r'[,;]|(?<!\w)(?:và|song|đổi|thay|gấp|nhân đôi)(?!\w)',atomic,re.I):
                    raise TuChoi('SOURCE_PREMISE_UNREAD','quote tiền đề ghép chưa được đọc độc lập trên lát hai đường',(c.id,))
                # Read the complete accepted span, not just its first keyword/object. These two premise forms carry
                # the geometry/length anchors of this slice; unparsed suffixes never acquire authority from a quote.
                if c.fn == 'perpendicular_line_plane' and not re.fullmatch(
                    rf"(?:cho\s+|biết\s+)?(?:đường thẳng\s+|cạnh bên\s+)?{_P1}\s*{_P1}\s*"
                    rf"(?:vuông góc\s+(?:với\s+)?|⊥\s*){_MAT_TOAN_HANG}[.\s]*",s,re.I):
                    raise TuChoi('SOURCE_PREMISE_UNREAD','quote vuông góc có phần chưa được đọc trên lát hai đường',(c.id,))
                if c.fn == 'segment_length':
                    length=_DO_DAI_CUC_BO.search(s)
                    prefix=s[:length.start()] if length else s
                    if (length is None or not re.fullmatch(r'(?:cho|biết|độ dài|cạnh bên|chiều cao|cạnh|\s)*',prefix,re.I)
                            or not re.fullmatch(r'\s*(?:cm|dm|mm|m|đvđd)?[.\s]*',s[length.end():],re.I)):
                        raise TuChoi('SOURCE_PREMISE_UNREAD','quote độ dài có phần chưa được đọc trên lát hai đường',(c.id,))
                if c.spec.kind != 'ask' and c.fn not in ('perpendicular_line_plane','segment_length'):
                    # Closed syntax only: existing source checks below still bind every operand/value and role.
                    # This guard grants no fact authority; it refuses tails the existing quote anchor cannot read.
                    labels = rf'(?:{_P1})+'
                    solid = rf'{labels}\.{labels}'
                    number = _SO.pattern
                    shape = rf'(?:tam giác đều|hình vuông|lục giác đều)\s*(?:{labels}\s*)?(?:cạnh\s*{number})?'
                    prism = rf'(?:cho\s+)?(?:hình\s+)?lăng trụ đứng\s+{solid}\s+có đáy là\s+{shape}[.\s]*'
                    reg_pyr = rf'(?:cho\s+)?(?:hình|khối) chóp\s+(?:đều|tam giác đều|tứ giác đều)\s+{solid}(?:\s+có\s+cạnh\s+đáy\s*(?:bằng|=)?\s*{number})?[.\s]*'
                    atomic_forms = {
                        'pyramid': rf'(?:cho\s+)?(?:hình|khối) chóp\s+{solid}[.\s]*',
                        'regular_pyramid': reg_pyr,
                        'prism': rf'(?:cho\s+)?(?:hình\s+)?(?:lăng trụ đứng|hình hộp chữ nhật)\s+{solid}[.\s]*',
                        'regular_polygon': rf'(?:đáy\s+{labels}\s+là\s+)?{shape}[.\s]*',
                        'rectangle': rf'(?:cho\s+)?(?:hình hộp chữ nhật\s+{solid}|(?:đáy\s+{labels}\s+là\s+)?hình chữ nhật\s*(?:{labels})?)[.\s]*',
                        'midpoint': rf'(?:gọi\s+)?{_P1}\s+là trung điểm\s+(?:của\s+)?{_P1}{_P1}[.\s]*',
                    }
                    form = atomic_forms.get(c.fn)
                    if not ((form and re.fullmatch(form,s,re.I))
                            or c.fn in ('prism','regular_polygon') and re.fullmatch(prism,s,re.I)
                            or c.fn == 'regular_polygon' and re.fullmatch(reg_pyr,s,re.I)):
                        raise TuChoi('SOURCE_PREMISE_UNREAD','quote tiền đề chưa nằm trọn trong văn phạm lát hai đường',(c.id,))
    from ..semantic_program.shape_constraint import doc_rang_buoc
    from ..semantic_program.source_entities import dinh_danh_thuc_the
    for assertion in doc_rang_buoc(de):
        prism = assertion.kind == 'cuboid' and any(
            c.fn == 'prism' and c.args.right
            and tuple(dinh_danh_thuc_the(n)[0] for n in c.args.base+c.args.top)==assertion.entities
            and any(d.fn == 'rectangle' and d.args.vertices == c.args.base for d in calls)
            for c in calls)
        if not prism and not any(_rang_buoc_cuc_bo_khop(assertion,c) for c in calls):
            raise TuChoi('SOURCE_PREMISE_UNREAD','quan hệ nguồn chưa khớp lời gọi đã xác thực trên lát hai đường')
