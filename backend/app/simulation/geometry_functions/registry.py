# -*- coding: utf-8 -*-
"""THƯ VIỆN HÀM DỰNG HÌNH + HỢP ĐỒNG AI → LỜI GỌI HÀM (run `text-to-geometry-functions`).

AI đọc đề và chỉ được CHỌN lời gọi trong `REGISTRY`, mỗi lời gọi kèm `source.quote` — đoạn nguyên văn của đề mà nó
dựa vào. Lược đồ đóng (`extra="forbid"`): không ô nào nhận toạ độ, không hàm tự do, không mã. Engine tất định
(`engine.py`) mới là thứ dựng, chọn bố cục và kiểm.

`kiem_nguon` là cổng nguồn TẤT ĐỊNH, chạy trước mọi phép dựng:
  · quote phải nằm nguyên văn trong đề (QUOTE_NOT_IN_SOURCE);
  · mọi nhãn điểm phải là nhãn có trong đề (UNKNOWN_LABEL);
  · quote mang phủ định ⇒ không được làm dữ kiện (NEGATED_CLAUSE);
  · quote phải chứa từ khoá của vị từ hàm khai (PREDICATE_NOT_IN_QUOTE) — AI không thể khai "vuông góc" từ "SA = 3";
  · ô số phải bằng ĐÚNG số duy nhất trong quote (AMBIGUOUS_VALUE_QUOTE / UNGROUNDED_VALUE) — AI không tự thêm số.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from fractions import Fraction
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError

REGISTRY_VERSION = "geometry-functions/1"


class TuChoi(Exception):
    """Từ chối CÓ MÃ. `calls` = id lời gọi liên quan (rỗng khi không quy được về lời gọi nào)."""

    def __init__(self, code: str, reason: str, calls: tuple[str, ...] = ()) -> None:
        super().__init__(f"{code}: {reason}")
        self.code, self.reason, self.calls = code, reason, tuple(calls)


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
                        Field(pattern=r"^(?:\d+(?:[.,]\d+)?(?:/\d+)?|(?:\d+(?:/\d+)?)?√\d+(?:/\d+)?)$",
                              description="số dương CHÉP từ đề, vd 4, 2/3, √3, 2√3, 3√3/4")]
Seg = Annotated[list[Label], Field(min_length=2, max_length=2)]
Poly = Annotated[list[Label], Field(min_length=3)]

_SO = re.compile(r"(?<![A-Za-z0-9'])(?:(?P<he>\d+(?:[.,]\d+)?(?:/\d+)?)?√(?P<can>\d+)(?:/(?P<mau>\d+))?"
                 r"|(?P<so>\d+(?:[.,]\d+)?)(?:/(?P<mau2>\d+))?)")


def binh_phuong(s: str) -> Fraction:
    """Số chính xác (dạng `ExactNumber`) → giá trị². Không float: `1,5` đọc thành 3/2."""
    m = _SO.fullmatch(chuan_hoa(s))
    if not m:
        raise TuChoi("SCHEMA_INVALID", f"không phải số chính xác: {s!r}")
    if m["can"]:
        he = Fraction((m["he"] or "1").replace(",", ".")) / int(m["mau"] or 1)
        return he * he * int(m["can"])
    v = Fraction(m["so"].replace(",", ".")) / int(m["mau2"] or 1)
    return v * v


def so_trong(quote: str) -> list[Fraction]:
    """Các số (dạng bình phương) xuất hiện trong một đoạn đề; chữ số dính nhãn (A1) không tính."""
    return [binh_phuong(m.group(0)) for m in _SO.finditer(chuan_hoa(quote))]


# ── đối số có kiểu của từng hàm ─────────────────────────────────────────────
class _Args(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegularPolygonArgs(_Args):
    vertices: Poly = Field(..., description="các đỉnh theo thứ tự vòng quanh")
    side: ExactNumber | None = Field(None, description="cạnh, nếu cùng mệnh đề nêu")


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


class MidpointArgs(_Args):
    point: Label = Field(..., description="tên trung điểm")
    segment: Seg


class PyramidArgs(_Args):
    apex: Label
    base: Poly = Field(..., description="đáy theo thứ tự vòng quanh")


class PrismArgs(_Args):
    base: Poly
    top: Poly = Field(..., description="đáy trên, cùng thứ tự với đáy dưới (A ↔ A')")
    right: bool = Field(..., description="lăng trụ ĐỨNG (đề nói đứng/đều)")


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


class AskAngleLinePlaneArgs(_Args):
    line: Seg
    plane: Poly


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
    #: Mỗi nhóm phải có ít nhất một từ (không phân biệt hoa thường) trong quote.
    keywords: tuple[tuple[str, ...], ...] = ()
    #: Ô số phải neo vào quote.
    value_fields: tuple[str, ...] = ()


_F = FunctionSpec
REGISTRY: dict[str, FunctionSpec] = {s.name: s for s in (
    _F("regular_polygon", RegularPolygonArgs, "fact", "Đa giác đều (tam giác đều, hình vuông, lục giác đều) với các đỉnh "
       "đã nêu; cạnh nếu cùng mệnh đề cho.", (("đều", "hình vuông"),), ("side",)),
    _F("rectangle", RectangleArgs, "fact", "Hình chữ nhật với bốn đỉnh đã nêu.", (("hình chữ nhật",),)),
    _F("right_angle", RightAngleArgs, "fact", "Góc vuông tại một đỉnh (tam giác vuông tại B ⇒ đỉnh B, hai điểm A, C).",
       (("vuông",),)),
    _F("segment_length", SegmentLengthArgs, "fact", "Độ dài một đoạn thẳng do đề cho.", (), ("value",)),
    _F("perpendicular_line_plane", PerpendicularLinePlaneArgs, "fact", "Đường thẳng vuông góc với mặt phẳng (SA ⊥ (ABC)).",
       (("vuông góc", "⊥"),)),
    _F("midpoint", MidpointArgs, "construct", "Gọi một điểm là trung điểm của một đoạn.", (("trung điểm",),)),
    _F("pyramid", PyramidArgs, "construct", "Khối chóp với đỉnh và đáy đã nêu.", (("chóp", "tứ diện"),)),
    _F("regular_pyramid", PyramidArgs, "construct", "Khối chóp ĐỀU: đáy đa giác đều, chân đường cao tại tâm đáy.",
       (("chóp", "tứ diện"), ("đều",))),
    _F("prism", PrismArgs, "construct", "Khối lăng trụ với hai đáy tương ứng; `right` khi đề nói lăng trụ đứng/đều.",
       (("lăng trụ", "hình hộp"),)),
    _F("height", HeightArgs, "fact", "Chiều cao của một khối do đề cho.", (("cao",),), ("value",)),
    _F("ask_volume", AskVolumeArgs, "ask", "Đề hỏi thể tích một khối.", (("thể tích",),)),
    _F("ask_length", AskLengthArgs, "ask", "Đề hỏi độ dài một đoạn.", (("độ dài", "tính", "tìm"),)),
    _F("ask_distance_point_plane", AskDistancePointPlaneArgs, "ask", "Đề hỏi khoảng cách từ một điểm tới một mặt phẳng.",
       (("khoảng cách",),)),
    _F("ask_angle_line_plane", AskAngleLinePlaneArgs, "ask", "Đề hỏi góc giữa đường thẳng và mặt phẳng (trả cos²).",
       (("góc",),)),
    _F("ask_area", AskAreaArgs, "ask", "Đề hỏi diện tích một đa giác.", (("diện tích",),)),
    _F("unsupported", UnsupportedArgs, "escape", "Mệnh đề không ánh xạ được vào thư viện — engine sẽ từ chối trung thực."),
)}

#: Dấu hiệu phủ định trong một mệnh đề — mệnh đề phủ định KHÔNG được làm dữ kiện dương.
PHU_DINH = ("không phải", "không là", "không vuông góc", "không đều", "không song song", "chưa chắc")


class Source(BaseModel):
    model_config = ConfigDict(extra="forbid")
    quote: str = Field(..., min_length=1, description="đoạn NGUYÊN VĂN của đề mà lời gọi dựa vào")


class FunctionCall(BaseModel):
    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., min_length=1)
    fn: str
    args: dict[str, Any]
    source: Source


@dataclass(frozen=True)
class LoiGoi:
    """Một lời gọi ĐÃ kiểm lược đồ."""

    id: str
    fn: str
    args: _Args
    quote: str

    @property
    def spec(self) -> FunctionSpec:
        return REGISTRY[self.fn]


def doc_ke_hoach(raw: Any) -> tuple[LoiGoi, ...]:
    """`{"calls": [...]}` → lời gọi có kiểu. Hàm lạ, ô lạ, kiểu sai ⇒ SCHEMA_INVALID."""
    try:
        calls = [FunctionCall.model_validate(c) for c in (raw or {}).get("calls") or []]
    except (ValidationError, AttributeError) as e:
        raise TuChoi("SCHEMA_INVALID", f"lời gọi sai lược đồ: {e}") from None
    if not calls:
        raise TuChoi("SCHEMA_INVALID", "kế hoạch rỗng")
    if len({c.id for c in calls}) != len(calls):
        raise TuChoi("SCHEMA_INVALID", "id lời gọi trùng")
    ra = []
    for c in calls:
        if c.fn not in REGISTRY:
            raise TuChoi("SCHEMA_INVALID", f"hàm {c.fn!r} không có trong thư viện", (c.id,))
        try:
            a = REGISTRY[c.fn].args.model_validate(c.args)
        except ValidationError as e:
            raise TuChoi("SCHEMA_INVALID", f"{c.id} ({c.fn}): {e.errors()[0]['msg']}", (c.id,)) from None
        ra.append(LoiGoi(c.id, c.fn, a, chuan_hoa(c.source.quote)))
    return tuple(ra)


def nhan_cua_de(text: str) -> set[str]:
    """Nhãn điểm có trong đề: từ chỉ gồm chữ HOA (S.ABC, (ABC), SA, A'B'C'), tách thành từng nhãn."""
    ra: set[str] = set()
    for w in re.findall(r"[\w'.]+", chuan_hoa(text)):
        if any(ch.isalpha() for ch in w) and all(not ch.isalpha() or "A" <= ch <= "Z" for ch in w):
            ra.update(re.findall(r"[A-Z][0-9]*'?", w))
    return ra


def nhan_cua_loi_goi(c: LoiGoi) -> set[str]:
    ra: set[str] = set()
    for v in c.args.model_dump().values():
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, str) and re.fullmatch(r"(?:[A-Z][0-9]*'?)+(?:\.(?:[A-Z][0-9]*'?)+)?", x):
                ra.update(re.findall(r"[A-Z][0-9]*'?", x))
    return ra


def kiem_nguon(calls: tuple[LoiGoi, ...], text: str) -> None:
    """Cổng nguồn tất định — xem docstring module. Ném `TuChoi` ở lời gọi đầu tiên hỏng (theo thứ tự id)."""
    de = chuan_hoa(text)
    nhan = nhan_cua_de(de)
    for c in sorted(calls, key=lambda c: c.id):
        q = c.quote
        if q not in de:
            raise TuChoi("QUOTE_NOT_IN_SOURCE", f"{c.id}: đoạn {q!r} không có nguyên văn trong đề", (c.id,))
        if lac := sorted(nhan_cua_loi_goi(c) - nhan):
            raise TuChoi("UNKNOWN_LABEL", f"{c.id}: nhãn {lac} không có trong đề", (c.id,))
        if c.fn == "unsupported":
            continue
        thuong = q.lower()
        if any(p in thuong for p in PHU_DINH):
            raise TuChoi("NEGATED_CLAUSE", f"{c.id}: mệnh đề {q!r} mang phủ định — không làm dữ kiện {c.fn}", (c.id,))
        for nhom in c.spec.keywords:
            if not any(k in thuong for k in nhom):
                raise TuChoi("PREDICATE_NOT_IN_QUOTE", f"{c.id}: {c.fn} cần một trong {list(nhom)} trong {q!r}", (c.id,))
        if c.fn == "prism" and c.args.right and not any(k in thuong for k in ("đứng", "đều", "hình hộp")):
            raise TuChoi("PREDICATE_NOT_IN_QUOTE", f"{c.id}: lăng trụ đứng cần 'đứng'/'đều' trong {q!r}", (c.id,))
        for f in c.spec.value_fields:
            v = getattr(c.args, f)
            if v is None:
                continue
            so = so_trong(q)
            if len(so) != 1:
                raise TuChoi("AMBIGUOUS_VALUE_QUOTE", f"{c.id}: quote cho ô số phải chứa đúng MỘT số, có {len(so)}", (c.id,))
            if binh_phuong(v) != so[0]:
                raise TuChoi("UNGROUNDED_VALUE", f"{c.id}: giá trị {v} không phải số trong {q!r}", (c.id,))


def function_declarations() -> list[dict[str, Any]]:
    """Khai báo hàm cho function calling của mô hình (một mục mỗi hàm): tên, mô tả, lược đồ đối số + `quote`."""
    ra = []
    for s in REGISTRY.values():
        sch = s.args.model_json_schema()
        props = {**sch.get("properties", {}), "quote": {"type": "string", "description": Source.model_fields["quote"].description}}
        ra.append({"name": s.name, "description": s.description,
                   "parameters": {"type": "object", "properties": props,
                                  "required": [*sch.get("required", []), "quote"], **({"$defs": sch["$defs"]} if "$defs" in sch else {})}})
    return ra
