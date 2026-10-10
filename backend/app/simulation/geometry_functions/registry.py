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
    _F("unsupported", UnsupportedArgs, "escape", "Mệnh đề không ánh xạ được vào thư viện — engine sẽ từ chối trung thực."),
)}

#: Dấu phủ định — xét trong quote VÀ phần mệnh đề đứng ngay trước nó.
PHU_DINH = ("không phải", "không là", "không vuông góc", "không ⊥", "không đều", "không song song", "chưa chắc")
_MUC_TIEU = ("chứng minh", "cmr", "chứng tỏ")


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


def _vai_tro(de: str, vt: int) -> str | None:
    """`GOAL` / `CONDITIONAL` / None (tiền đề) cho đoạn bắt đầu tại `vt`, xét phần câu đứng trước nó."""
    truoc = de[_cau_chua(de, vt):vt].lower()
    muc = max((truoc.rfind(m) for m in _MUC_TIEU), default=-1)
    if muc >= 0 and "biết" not in truoc[muc:]:
        return "GOAL"
    neu = truoc.rfind("nếu")
    if neu >= 0 and re.search(r"(?<!\w)nếu(?!\w)", truoc[neu:]) and "thì" not in truoc[neu:]:
        return "CONDITIONAL"
    return None


def _phu_dinh(de: str, vt: int, q: str) -> bool:
    """Phủ định trong quote, hoặc ngay trước nó trong CÙNG mệnh đề (cắt ở , ; :)."""
    truoc = de[_cau_chua(de, vt):vt]
    duoi = re.split(r"[,;:]", truoc)[-1]
    return any(p in (duoi + q).lower() for p in PHU_DINH)


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


def kiem_nguon(calls: tuple[LoiGoi, ...], text: str) -> None:
    """Cổng nguồn tất định — xem docstring module. Ném `TuChoi` ở lời gọi đầu tiên hỏng (theo thứ tự id)."""
    de = chuan_hoa(text)
    nhan = nhan_cua_de(de)
    for c in sorted(calls, key=lambda c: c.id):
        vts = []
        for q in c.quotes:
            if (vt := _vi_tri(de, q)) is None:
                raise TuChoi("QUOTE_NOT_IN_SOURCE", f"{c.id}: đoạn {q!r} không có nguyên văn trong đề", (c.id,))
            vts.append(vt)
        if lac := sorted(nhan_cua_loi_goi(c) - nhan):
            raise TuChoi("UNKNOWN_LABEL", f"{c.id}: nhãn {lac} không có trong đề", (c.id,))
        if c.spec.kind == "escape":
            continue
        if c.spec.kind != "ask":
            for (dau, _c), q in zip(vts, c.quotes):
                positions = [dau]
                if c.fn in ("intersect_line_line", "intersect_line_plane", "orthogonal_projection_line", "orthogonal_projection"):
                    # A quote may include its own "Nếu" / "Chứng minh" prefix.
                    # Inspect the actual predicate position in the original source,
                    # including an antecedent BEFORE its later "thì".
                    positions += [dau + m.start() for m in re.finditer(
                        r"[A-Z][0-9]*'?\s+là\s+(?:giao điểm|hình chiếu)|[Hh]ình chiếu", de[dau:_c])]
                roles = {_vai_tro(de, pos) for pos in positions}
                if len(positions) > 1 and any(re.search(r"(?<!\w)nếu(?!\w)", de[_cau_chua(de, pos):pos], re.IGNORECASE)
                                              for pos in positions[1:]):
                    roles.add("CONDITIONAL")  # a conditional consequent is not an unconditional premise either
                if "GOAL" in roles:
                    raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{c.id}: {q!r} là điều phải chứng minh, không phải dữ kiện", (c.id,))
                if "CONDITIONAL" in roles:
                    raise TuChoi("CONDITIONAL_CLAUSE", f"{c.id}: {q!r} nằm trong mệnh đề 'nếu … thì' — không phải dữ kiện", (c.id,))
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
                continue
            so = [(x, s) for q in c.quotes for _vt, x, s in so_trong(q)]
            if len(so) != 1:
                raise TuChoi("AMBIGUOUS_VALUE_QUOTE", f"{c.id}: quote cho ô số phải chứa đúng MỘT số, có {len(so)}", (c.id,))
            if gt != so[0]:
                raise TuChoi("UNGROUNDED_VALUE", f"{c.id}: giá trị {v} không phải số trong {c.quote!r}", (c.id,))


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
