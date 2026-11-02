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

import contextvars
import functools
import re
import unicodedata
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, model_validator

#: /7 (run `goal-directed-function-composition`): `ask_angle_lines`, the `centroid` producer contract, angle goal contracts.
#: /8 (run `geometry-capability-expansion`): `divide_segment` + ratio grammar, `MAT_VUONG_DUONG`, `POINT_PRODUCERS`.
#: /9 (run `source-gate-hardening`): atomic segment labels, role-bound values, shape values keep their parameter, shared goal
#: wording tokens, request lists in one sentence, line_ref faces of ≥ 3 labels and the intersection named in the question.
#: /10 (run `composite-geometry`): explicit shared-face membership in two declared pyramid topologies.
#: /12 (run `typedfactnext-planner-bridge`): a ratio point owns the coefficient its equation read; the definition grammar
#: reads "M thuộc cạnh SA sao cho …"; `DINH_CAT_CANH` cut-clause / derived-pyramid certificate.
#: /13 (run `hybrid-contract-v2`, owner D3/D5/D6): `intersect_line_plane` planning contract (effect `Meet`); `derived_fresh`
#: section vertices; closed definition / cut-clause alternatives (see `_QUA_SONG_SONG`, `_cum_cat_canh`).
#: /15 (run `hybrid-v2-planner-generalization`): bare "chóp" / "lăng trụ" / "tứ diện" in section phrases (`_TU_KHOI`); a
#: section reference bound to a derived plane must name the cut solid (`_cum_goi_khoi`).
#: /16 (run `hybrid-v2-planner-premerge-review`): a kind word written WITHOUT a solid symbol must be true of the solid the
#: gate validated — a specific class ("tứ diện", "hộp", "lập phương", "đứng", "tam giác" …) is checked, not only the coarse
#: pyramid-/prism-like split (`_loai_cum_dung`).
#: /18 (run `hybrid-v2-holdout-failure-repair`): M1–M5 Source Gate parity (`MAT_HAI_DUONG` / `_kiem_nguon_dong`, SG-3 plural
#: quantifiers, section wording & 4-vertex coplanar solid planes, compound premise coverage, bounded section-area question binding).
#: /20 (run `hybrid-v2-w3-f1-cross-sentence-plane-grounding`): W3-F1 cross-sentence plane definition grounding, `đồng thời`
#: plane-relation connector, `cả hai` two-line quantifier, cut-clause + compound area request tails, and plane-name identity checks.
#: /22 (run `hybrid-master-backend-replacement`): "H, K lần lượt là hình chiếu … của A trên SB, SC" — ordered respectively
#: lists for point–line projections (LLM_ONLY W18 parity; midpoints/centroids already read them).
#: /23 (same run): curved solids on /4 — `curved_solid` with role-bound radius/height, and the planner-only asks
#: `ask_curved_volume` / `ask_lateral_area` / `ask_surface_area` / `ask_radius` (route A's provider surface unchanged).
#: /24 (same run): curved sections (parallel to the base, through the axis), the small cone, its ratio and remaining
#: volume — planner-only functions; route A provider surface unchanged.
#: /25 (same run): base-centre wordings ("tâm đáy O", "tâm đáy dưới/trên", "hai đáy có tâm", "đường tròn đáy tâm O",
#: segment-written dimensions) and the general apex ratio k ("SM/SO = k", "OM/OS = k" converted by the gate, "theo tỉ lệ k
#: tính từ đỉnh S"); an unread curved clause refuses `CURVED_WORDING_UNSUPPORTED` (CAPABILITY, not SOURCE_UNVERIFIED).
#: /26 (same run): certified `inscribed_in` spheres on polyhedra and axial curved hosts, `sphere_tangent_plane` tangency
#: facts with optional named contact points, and multi-curved question disambiguation (`(S1)`/`(S2)`, `ngoại tiếp` vs `nội tiếp`).
#: /29 (thirteenth continuation, SL-3): student shorthand "k/c" (khoảng cách) as a whole token wherever the ask grammar
#: reads that word, and "đt" (đường thẳng) before a line's two labels; no function, contract or provider surface changed.
REGISTRY_VERSION = "geometry-functions/31"


class TuChoi(Exception):
    """Từ chối CÓ MÃ. `calls` = id lời gọi liên quan (rỗng khi không quy được về lời gọi nào)."""

    def __init__(self, code: str, reason: str, calls: tuple[str, ...] = (), data: dict | None = None) -> None:
        super().__init__(f"{code}: {reason}")
        self.code, self.reason, self.calls, self.data = code, reason, tuple(calls), dict(data or {})


# ── chuẩn hoá ký hiệu ───────────────────────────────────────────────────────
def chuan_hoa(s: str) -> str:
    s = unicodedata.normalize("NFC", s).replace("’", "'").replace("′", "'").replace("‘", "'")
    return re.sub(r"\s+", " ", s).strip()


#: SL-3 (thirteenth continuation): the student abbreviation "k/c" of "khoảng cách", as a whole token, wherever the ask
#: grammar reads that word (never in `chuan_hoa`: source text is not rewritten). "mp" (mặt phẳng) was already read where a
#: plane's labels follow; "đt" (đường thẳng) is read only before a line's two labels (`_doan_cum`). A bare abbreviation
#: names nothing: every pattern that accepts one still requires the object's labels.
_KC = r"(?:khoảng cách|(?<![\w/])k/c(?![\w/]))"


def _nhan(v: Any) -> Any:
    return chuan_hoa(v) if isinstance(v, str) else v


SOLID_NAME_PATTERN = r"^(?:[A-Z][0-9]*'?)+\.(?:[A-Z][0-9]*'?)+$"
Label = Annotated[str, BeforeValidator(_nhan), Field(pattern=r"^[A-Z][0-9]*'?$", description="nhãn một điểm của đề, vd S, A, A'")]
SolidName = Annotated[str, BeforeValidator(_nhan),
                      Field(pattern=SOLID_NAME_PATTERN, description="ký hiệu khối, vd S.ABC hoặc ABC.A'B'C'")]
#: Exported for provider response schemas (Schema-Contract v3), so the model is told the same value grammar the validator checks.
NUMBER_PATTERN = r"^(?:\d+(?:[.,]\d+)?(?:/\d+)?a?(?:√\d+)?(?:/\d+)?|a(?:√\d+)?(?:/\d+)?|√\d+(?:/\d+)?)$"
ExactNumber = Annotated[str, BeforeValidator(_nhan),
                        Field(pattern=NUMBER_PATTERN,
                              description="độ dài CHÉP từ đề: số dương (4, 2/3, √3, 3√3/4) hoặc theo ký hiệu a (a, 2a, a√3, a√3/2)")]
Seg = Annotated[list[Label], Field(min_length=2, max_length=2)]
Poly = Annotated[list[Label], Field(min_length=3)]

#: Một số chính xác trong văn bản: hệ số · (a) · √căn / mẫu. Không dính chữ/nhãn hai bên (`A1`, `bằng` không tính).
_SO = re.compile(r"(?<![\w'])(?P<he>\d+(?:[.,]\d+)?(?:/\d+)?)?(?P<sym>a)?(?:√(?P<can>\d+))?(?:/(?P<mau>\d+))?(?![\w'])")


def _doc(m: re.Match) -> tuple[Fraction, bool] | None:
    if not (m["he"] or m["sym"] or m["can"]):
        return None
    try:
        he = Fraction((m["he"] or "1").replace(",", ".")) / int(m["mau"] or 1)
    except ZeroDivisionError:            # "1/0" matches the grammar but is no number: refuse (doc_so), never crash
        return None
    return he * he * int(m["can"] or 1), bool(m["sym"])


def doc_so(s: str) -> tuple[Fraction, bool]:
    """Số chính xác (dạng `ExactNumber`) → (hệ số², có ký hiệu a). Không float: `1,5` đọc thành 3/2."""
    m = _SO.fullmatch(chuan_hoa(s))
    if not m or (r := _doc(m)) is None:
        raise TuChoi("SCHEMA_INVALID", f"không phải số chính xác: {s!r}")
    if r[0] == 0:
        # Văn phạm nhận `0`, `√0`, `0/5`, `0a`; mọi trường dùng bộ đọc này là ĐỘ DÀI (`ExactNumber`: "số dương"). Để lọt
        # xuống engine thì chiều cao 0 bị bố cục thay bằng 1 rồi mới bị tự kiểm bắt, trả nhầm mã lỗi nội bộ
        # (run `hybrid-pre-main-hardening`). Mã chung với tuyến C và thông điệp người học.
        raise TuChoi("NON_POSITIVE_LENGTH", f"độ dài bằng 0 ({s!r}): hình suy biến, không dựng hay tính được")
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


class DivideSegmentArgs(_Args):
    point: Label = Field(..., description="tên điểm chia")
    segment: Seg = Field(..., description="hai đầu mút CÓ THỨ TỰ [A, B]")
    ratio: Annotated[str, Field(pattern=r"^\d+/\d+$")] = Field(..., description="t = AP/AB, hữu tỉ, 0 < t < 1")

    @model_validator(mode="after")
    def _trong_doan(self):
        try:
            t = Fraction(self.ratio)
        except ZeroDivisionError:
            raise ValueError("divide_segment: tỉ số có mẫu 0") from None
        if not 0 < t < 1 or len(set(self.segment)) != 2:
            raise ValueError("divide_segment: cần hai đầu mút phân biệt và 0 < t < 1")
        return self


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


#: A curved solid's notation as the source writes it: "O.O'" (two base centres), "S.O" (apex.centre) or "O" (sphere centre).
#: The ONE grammar of a curved notation the planner can express (the bridge refuses any other as a capability gap).
CURVED_NAME_PATTERN = r"^(?:\([A-Z][0-9]*'?\)|[A-Z][0-9]*'?(?:\.[A-Z][0-9]*'?)?)$"
_HOST_SOLID_BODY = r"(?:(?:[A-Z][0-9]*'?)+\.(?:[A-Z][0-9]*'?)+|\([A-Z][0-9]*'?\)|[A-Z][0-9]*'?(?:\.[A-Z][0-9]*'?)?)"
CIRCUMSCRIBED_NAME_PATTERN = rf"^(?:\(\)|\((?:out|in):{_HOST_SOLID_BODY}\)|\([A-Z][0-9]*'?\)|\((?:[A-Z][0-9]*'?)+\.(?:[A-Z][0-9]*'?)+\)|[A-Z][0-9]*'?)$"
CurvedName = Annotated[str, BeforeValidator(_nhan), Field(pattern=CURVED_NAME_PATTERN)]
CircumscribedOrCurvedName = Annotated[
    str,
    BeforeValidator(_nhan),
    Field(pattern=rf"(?:{CURVED_NAME_PATTERN})|(?:{CIRCUMSCRIBED_NAME_PATTERN})"),
]
HostSolidName = Annotated[
    str,
    BeforeValidator(_nhan),
    Field(pattern=rf"(?:{SOLID_NAME_PATTERN})|(?:{CURVED_NAME_PATTERN})"),
]


class CurvedSolidArgs(_Args):
    """Run `hybrid-master-backend-replacement` (curved & composite slice): one solid of revolution in its canonical pose, or
    an axisless curved solid anchored to a declared host solid (`circumscribes` / `inscribed_in`)."""
    kind: Literal["cylinder", "cone", "sphere"]
    solid: CircumscribedOrCurvedName
    center: Label | None = Field(None, description="tâm (đáy / mặt cầu) nếu đề đặt tên")
    top: Label | None = Field(None, description="tâm đáy trên (trụ) hoặc đỉnh (nón)")
    rim: Label | None = Field(None, description="một điểm trên đường tròn đáy / mặt cầu")
    radius: ExactNumber | None = None
    height: ExactNumber | None = None
    circumscribes: HostSolidName | None = Field(None, description="khối chủ được mặt cầu ngoại tiếp, nếu có")
    inscribed_in: HostSolidName | None = Field(None, description="khối chủ có mặt cầu nội tiếp, nếu có")

    @model_validator(mode="after")
    def _check_notation_for_mode(self) -> CurvedSolidArgs:
        if self.circumscribes is not None and self.inscribed_in is not None:
            raise ValueError("curved_solid: không thể đồng thời khai báo circumscribes và inscribed_in")
        pat = (
            CIRCUMSCRIBED_NAME_PATTERN
            if (self.circumscribes is not None or self.inscribed_in is not None)
            else CURVED_NAME_PATTERN
        )
        if not re.fullmatch(pat, self.solid):
            raise ValueError(f"curved_solid: ký hiệu {self.solid!r} không hợp lệ")
        return self


class SphereTangentPlaneArgs(_Args):
    """Certified tangency between a declared sphere and a plane, optionally naming the unique contact point."""
    solid: CircumscribedOrCurvedName
    plane: Poly = Field(..., description="các điểm xác định mặt phẳng tiếp xúc")
    point: Label | None = Field(None, description="tiếp điểm nếu đề đặt tên")


class AskCurvedArgs(_Args):
    solid: CircumscribedOrCurvedName


class CurvedSectionArgs(_Args):
    """A plane section of THE solid of revolution (registry /24): parallel to the base at a stated distance from it, or
    through the midpoint of the axis (`ratio` = distance from the apex / height), or through the axis."""
    solid: CurvedName
    section: Annotated[str, Field(min_length=1)]
    kind: Literal["parallel_to_base_at_distance", "parallel_to_base_at_ratio", "axial_section", "at_distance_from_center",
                  "through_center"]
    plane: Annotated[str, Field(min_length=1)] | None = None
    distance: ExactNumber | None = None
    ratio: Annotated[str, Field(pattern=r"^\d+/\d+$")] | None = None
    point: Label | None = Field(None, description="điểm trên trục mà mặt phẳng đi qua, nếu đề đặt tên (registry /25)")


class CurvedSubsolidArgs(_Args):
    """The small cone a plane parallel to the base cuts off at the apex (registry /24)."""
    solid: CurvedName
    section: Annotated[str, Field(min_length=1)]
    derived: Annotated[str, Field(min_length=1)]
    apex: Label


class AskCurvedSectionArgs(_Args):
    solid: CurvedName
    section: Annotated[str, Field(min_length=1)]


class AskCurvedPairArgs(_Args):
    """Two solids by their ids, in the ORDER the question states them (numerator, denominator) / (original, cut)."""
    first: Annotated[str, Field(min_length=1)]
    second: Annotated[str, Field(min_length=1)]


class AskVolumeArgs(_Args):
    solid: SolidName


class AskVolumeRatioArgs(_Args):
    numerator_solid: SolidName
    denominator_solid: SolidName

    @model_validator(mode="after")
    def _check_distinct_solids(self) -> AskVolumeRatioArgs:
        if self.numerator_solid == self.denominator_solid:
            raise ValueError("ask_volume_ratio: numerator_solid và denominator_solid phải phân biệt")
        return self


class AskResidualVolumeArgs(_Args):
    original_solid: SolidName
    subtracted_solids: Annotated[list[SolidName], Field(min_length=1, max_length=2)]


class AskLengthArgs(_Args):
    segment: Seg


class AskDistancePointPlaneArgs(_Args):
    point: Label
    plane: Annotated[list[Label], Field(min_length=3, max_length=3)]


class AskDistanceLinesArgs(_Args):
    line1: Seg
    line2: Seg


class AskDistanceLinePlaneArgs(_Args):
    line: Seg
    plane: Poly


class AskDistancePlanesArgs(_Args):
    plane1: Poly
    plane2: Poly


class AskAngleLinePlaneArgs(_Args):
    line: Seg
    plane: Poly


class AskAngleLinesArgs(_Args):
    line1: Seg
    line2: Seg


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
    kind: Literal["Point", "Plane", "Line", "Foot", "AnswerDistance", "AnswerLength", "AnswerArea", "AnswerAngleLinePlane",
                  "AnswerAngleLines", "Meet", "Normal", "PerpLine", "PerpDir"]
    operands: tuple[str, ...]


@dataclass(frozen=True)
class PlanningContract:
    """What ONE Registry function gives the planner: typed input needs → one effect. `call` writes the call from the slot
    bindings (argument → slot, or a tuple of slots for a list argument); `fresh` is the label stem when the effect is a point
    the source does not name; a `descriptor` contract realizes an unnamed point the source describes ("trung điểm của SC"),
    named in the source by `phrase` (operands in group `ops`, `{P}` = one point label). Never serialized to a provider."""
    inputs: tuple[PlanningTerm, ...]
    effect: PlanningTerm
    source_policy: Literal["declared_intersection", "projection_foot", "distance_witness", "derived_point", "distance_answer",
                           "goal_answer", "section_vertex", "normal_witness", "locus_witness", "point_definition"]
    verifier: str
    call: tuple[tuple[str, str | tuple[str, ...]], ...] = ()
    fresh: str | None = None
    descriptor: str | None = None
    phrase: str | tuple[str, ...] | None = None   # a goal contract may list several closed wordings (`_cac_cau`)
    goal: str | None = None  # semantic quantity accepted at goal entry; internal, never a provider field
    #: C18: input slots the planner binds itself (no need operand fills them) — a point of the need's plane `W`.
    free: tuple[str, ...] = ()
    #: C18: preconditions the planner can decide from STRUCTURE (no coordinates): ("off_line", P, L) = point P not on line
    #: L. A precondition it cannot decide is left to the engine, which checks every construction exactly.
    requires: tuple[tuple[str, str, str], ...] = ()
    #: C18: the two slots spanning the LINE this effect stands for (a locus line through P and its witness X).
    line: tuple[str, str] | None = None


def render_call(contract: PlanningContract, env: dict[str, Any]) -> dict[str, Any]:
    """Call arguments from a contract's `call` template and slot bindings — the ONE writer shared by the planner (emission)
    and the gate (re-check). A line slot is written `line` (named, two labels) or `line_ref` (verified result)."""
    args: dict[str, Any] = {}
    for arg, slot in contract.call:
        if isinstance(slot, tuple):
            args[arg] = [env[s] for s in slot]
            continue
        v = env[slot]
        if isinstance(v, (list, tuple)) and len(v) == 2 and v[0] in ("named", "result"):
            args[arg + "_ref" if v[0] == "result" else arg] = v[1] if v[0] == "result" else list(v[1])
        elif isinstance(v, tuple) and v and v[0] == "desc":
            args[arg] = v
        else:
            args[arg] = list(v) if isinstance(v, (list, tuple)) else v
    return args


def same_call(contract: PlanningContract, a: dict[str, Any], b: dict[str, Any]) -> bool:
    """Equal arguments up to what carries no order: a line or plane written from ONE slot (BD = DB), a pair of lines in
    line–line intersection, and a description's flat operands (midpoint of SC = midpoint of CS)."""
    if a.keys() != b.keys():
        return False
    if {"line1", "line2"} <= a.keys() and contract.descriptor:
        la = {tuple(sorted(a["line1"])), tuple(sorted(a["line2"]))}
        lb = {tuple(sorted(b["line1"])), tuple(sorted(b["line2"]))}
        return la == lb and all(a[k] == b[k] for k in a if k not in ("line1", "line2"))
    ordered = set() if contract.descriptor else {arg for arg, slot in contract.call if isinstance(slot, tuple)}
    norm = lambda k, x: sorted(x) if isinstance(x, list) and k not in ordered and all(isinstance(i, str) for i in x) else x  # noqa: E731
    return all(norm(k, a[k]) == norm(k, b[k]) for k in a)


def parse_descriptor_inputs(
    contract: PlanningContract, raw_points: list[str] | tuple[str, ...],
) -> tuple[tuple[Any, ...], list[list[str]]] | None:
    """Parse flat `TypedFact.points` against a descriptor contract's typed `inputs` slots (`Point` / `Line` / `Plane`)."""
    pts = list(raw_points)
    kinds = [t.kind for t in contract.inputs]
    if not kinds:
        return None
    if all(k == "Point" for k in kinds):
        if len(pts) != len(kinds) or len(set(pts)) != len(pts):
            return None
        return tuple(sorted(pts)), []
    i = 0
    out: list[Any] = []
    extra_planes: list[list[str]] = []
    for idx, k in enumerate(kinds):
        if k == "Point":
            if i >= len(pts):
                return None
            out.append(pts[i])
            i += 1
        elif k == "Line":
            if i + 2 > len(pts):
                return None
            seg = pts[i:i + 2]
            i += 2
            if len(set(seg)) != 2:
                return None
            out.append(("named", tuple(sorted(seg))))
        elif k == "Plane":
            if idx != len(kinds) - 1:
                return None
            pl = pts[i:]
            i = len(pts)
            if len(pl) < 3 or len(set(pl)) != len(pl):
                return None
            if len(pl) > 3:
                extra_planes.append(list(pl))
            out.append(tuple(pl))
        else:
            return None
    if i != len(pts):
        return None
    if kinds == ["Line", "Line"]:
        if out[0] == out[1]:
            return None
        out = sorted(out)
    elif kinds[0] == "Point" and len(kinds) == 2:
        ref_pts = out[1][1] if kinds[1] == "Line" else out[1]
        if out[0] in ref_pts:
            return None
    return tuple(out), extra_planes


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
    planning_extra: tuple[PlanningContract, ...] = ()  # another mathematical meaning of the same function
    #: False: the planner (route B) may emit it from typed facts, but it is not offered to the provider of route A —
    #: a new function does not widen the route A model surface without its own decision (Wave 2A, P3.4).
    provider_offered: bool = True


def planning_contracts(spec: FunctionSpec) -> tuple[PlanningContract, ...]:
    return ((spec.planning,) if spec.planning else ()) + spec.planning_extra


def goal_slots(contract: PlanningContract) -> tuple[tuple[str, str], ...]:
    """(slot, kind) of a contract's effect operands, kinds read from its typed inputs — one reader for the planner (which
    fills them from a fact) and the gate (which re-binds them to the source)."""
    kinds = {t.operands[0]: t.kind for t in contract.inputs}
    return tuple((s, kinds.get(s, "")) for s in contract.effect.operands)


def goal_target_keys(contract: PlanningContract) -> frozenset[str]:
    """Certificate target keys of a goal contract, from the kinds of its slots after the measured point: one point →
    `point`, several → `points`, a plane → `plane`, a line → `line`."""
    rest = [k for _s, k in goal_slots(contract)[1:]]
    n = rest.count("Point")
    return frozenset(({"point"} if n == 1 else {"points"} if n > 1 else set())
                     | ({"plane"} if "Plane" in rest else set()) | ({"line"} if "Line" in rest else set()))


#: The target a goal verifier measures (independent check in the engine): the gate refuses a contract whose declared
#: verifier does not measure the target its slots describe (a lying `verifier`), the engine dispatches on it.
GOAL_VERIFIER_TARGET = {"length": frozenset({"point"}), "area": frozenset({"points"}),
                        "angle_line_plane": frozenset({"point", "plane"}), "angle_lines": frozenset({"point", "line"})}


def planning_contract(spec: FunctionSpec, effect: str | None = None, descriptor: str | None = None) -> PlanningContract | None:
    """Certificate selects a mathematical effect, never an unchecked index into catalog data."""
    if effect is None and descriptor is None:
        return spec.planning
    matches = [c for c in planning_contracts(spec)
               if (effect is None or c.effect.kind == effect)
               and (descriptor is None or c.descriptor == descriptor)]
    return matches[0] if len(matches) == 1 else None


_VUONG = ("vuông", "⊥")
#: "hộp chữ nhật" names a cuboid with or without "hình"/"khối" (same pattern as `_HOP_CHU_NHAT`); bare "hộp" does not.
_HOP_CHU_NHAT_KW = r"re:(?i)(?<!\w)hộp\s+chữ\s+nhật(?!\w)"
#: "AB dài bao nhiêu" asks a length; "dài 3" assigns one and "dài hơn … bao nhiêu" compares, so neither matches.
#: Same wording as the question grammar accepts (no "dài là/bằng bao nhiêu" the ask grammar would reject anyway).
_DAI_BAO_NHIEU_KW = r"re:(?i)(?<!\w)dài\s+bao\s+nhiêu(?!\w)"
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
       "phẳng là một điểm.", (("hình chiếu", "chân đường cao", "hạ đường cao", "kẻ đường cao"),),
       plane_fields=("plane",), point_fields=("image",),
       planning=PlanningContract(
           (PlanningTerm("Point", ("P",)), PlanningTerm("Plane", ("Q",))),
           PlanningTerm("Point", ("H",)), "derived_point", "orthogonal_projection",
           call=(("point", "P"), ("plane", "Q"), ("image", "H")), fresh="H", descriptor="orthogonal_projection",
           phrase=(r"hình chiếu(?:\s+vuông góc)?\s+của\s+(?:(?:điểm|đỉnh)\s+)?(?P<op_p>{P})(?![\w'])\s+"
                   r"(?:lên|trên)\s+(?:(?:mặt phẳng|mp|mặt bên|mặt đáy)\s*)?\(?(?P<op_q>(?:{P}){3,})(?![\w'])\)?")),
       # C17: a NORMAL direction of a plane Q — Z − H for any point Z off Q, H its foot on Q. The planner chooses Z.
       planning_extra=(PlanningContract(
           (PlanningTerm("Point", ("Z",)), PlanningTerm("Plane", ("Q",))), PlanningTerm("Normal", ("Q",)), "normal_witness",
           "orthogonal_projection", call=(("point", "Z"), ("plane", "Q"), ("image", "H")), fresh="H"),)),
    _F("orthogonal_projection_line", ProjectionLineArgs, "construct", "Dựng ảnh hình chiếu vuông góc của điểm lên đường thẳng.",
       (("hình chiếu",),), segment_fields=("line",), point_fields=("image",),
       planning=PlanningContract((PlanningTerm("Point", ("P",)), PlanningTerm("Line", ("L",))),
                                 PlanningTerm("Foot", ("F", "P", "L")), "projection_foot", "_construction_relation",
                                 call=(("point", "P"), ("line", "L"), ("image", "F")), fresh="H"),
       planning_extra=(PlanningContract(
           (PlanningTerm("Point", ("P",)), PlanningTerm("Line", ("L",))),
           PlanningTerm("Point", ("H",)), "derived_point", "orthogonal_projection_line",
           call=(("point", "P"), ("line", "L"), ("image", "H")), fresh="H", descriptor="orthogonal_projection_line",
           phrase=(r"hình chiếu(?:\s+vuông góc)?\s+của\s+(?:(?:điểm|đỉnh)\s+)?(?P<op_p>{P})(?![\w'])\s+"
                   r"(?:lên|trên)\s+(?:(?:đường thẳng|đt|đoạn thẳng|đoạn|cạnh(?:\s+bên|\s+đáy)?)\s+)?"
                   r"(?<![\w'.(])(?P<op_l>(?:{P}){2})(?![\w'])")),
           # C18 locus contracts (a local fact each, no goal named): in a plane W holding P and L, the line through P ⊥ L
           # is P and its foot on L (only when P is off L); and Z − foot(Z, L) is a direction ⊥ L for any point Z of W off L.
           PlanningContract((PlanningTerm("Point", ("P",)), PlanningTerm("Line", ("L",))),
                            PlanningTerm("PerpLine", ("X", "P", "L", "W")), "locus_witness", "_construction_relation",
                            call=(("point", "P"), ("line", "L"), ("image", "X")), fresh="H",
                            requires=(("off_line", "P", "L"),), line=("P", "X")),
           PlanningContract((PlanningTerm("Point", ("Z",)), PlanningTerm("Line", ("L",))),
                            PlanningTerm("PerpDir", ("U", "Z", "L", "W")), "locus_witness", "_construction_relation",
                            call=(("point", "Z"), ("line", "L"), ("image", "U")), fresh="H", free=("Z",),
                            requires=(("off_line", "Z", "L"),)))),
    _F("intersect_line_line", IntersectionLinesArgs, "construct", "Dựng giao điểm DUY NHẤT của hai đường thẳng; không phải đoạn hữu hạn.",
       (("giao điểm",),), segment_fields=("line1", "line2"), point_fields=("point",),
       planning=PlanningContract(
           (PlanningTerm("Line", ("L1",)), PlanningTerm("Line", ("L2",))),
           PlanningTerm("Point", ("I",)), "derived_point", "intersect_line_line",
           call=(("point", "I"), ("line1", "L1"), ("line2", "L2")), fresh="I", descriptor="intersect_line_line",
           phrase=(r"giao điểm\s+(?:của\s+)?(?:hai\s+(?:đường thẳng|đt|đường chéo|cạnh|đoạn(?:\s+thẳng)?)\s+)?"
                   r"(?<![\w'.(])(?P<op_l1>(?:{P}){2})(?![\w'])\s*(?:,\s*|\s+(?:và|với)\s+)"
                   r"(?:(?:đường thẳng|đt|đường chéo|cạnh|đoạn(?:\s+thẳng)?)\s+)?(?<![\w'.(])(?P<op_l2>(?:{P}){2})(?![\w'])"))),
    _F("intersect_line_plane", IntersectionPlaneArgs, "construct", "Dựng giao điểm DUY NHẤT của đường thẳng và mặt phẳng.",
       (("giao điểm",),), plane_fields=("plane",), segment_fields=("line",), point_fields=("point",),
       # Section vertex (run `hybrid-contract-v2`): effect `Meet` X = L ∩ Q; only `planner._dinh_cat_canh` asks for it
       # (no goal / descriptor, so no other search can select it); the engine checks uniqueness and 0 < t ≤ 1.
       planning=PlanningContract((PlanningTerm("Line", ("L",)), PlanningTerm("Plane", ("Q",))),
                                 PlanningTerm("Meet", ("X", "L", "Q")), "section_vertex", "_construction_relation",
                                 call=(("point", "X"), ("line", "L"), ("plane", "Q")), fresh="I"),
       planning_extra=(PlanningContract(
           (PlanningTerm("Line", ("L",)), PlanningTerm("Plane", ("Q",))),
           PlanningTerm("Point", ("I",)), "derived_point", "intersect_line_plane",
           call=(("point", "I"), ("line", "L"), ("plane", "Q")), fresh="I", descriptor="intersect_line_plane",
           phrase=(r"giao điểm\s+(?:của\s+)?(?:(?:đường thẳng|đt|đường chéo|cạnh(?:\s+bên|\s+đáy)?|đoạn(?:\s+thẳng)?)\s+)?"
                   r"(?<![\w'.(])(?P<op_l>(?:{P}){2})(?![\w'])\s+(?:và|với)\s+"
                   r"(?:(?:mặt phẳng|mp|mặt bên|mặt đáy)\s*)?\(?(?P<op_q>(?:{P}){3,})(?![\w'])\)?")),)),
    _F("perpendicular_lines", PerpendicularLinesArgs, "fact", "Hai đường thẳng vuông góc (SA ⊥ AB). Một lời gọi cho MỖI cặp.",
       (_VUONG,), segment_fields=("line1", "line2")),
    _F("equal_length", EqualLengthArgs, "fact", "Hai đoạn bằng nhau (SA = AB).", (("=", "bằng"),),
       segment_fields=("segment_a", "segment_b")),
    _F("height", HeightArgs, "fact", "Chiều cao của một khối do đề cho.", (("cao",),), ("value",)),
    _F("face_perpendicular_base", FacePerpendicularBaseArgs, "fact", "Mặt bên (một đỉnh ngoài đáy + một cạnh đáy) vuông "
       "góc với mặt đáy.", (_VUONG,), plane_fields=("base", "face")),
    _F("midpoint", MidpointArgs, "construct", "Gọi một điểm là trung điểm của một đoạn.", (("trung điểm",),),
       planning=PlanningContract((PlanningTerm("Point", ("A",)), PlanningTerm("Point", ("B",))), PlanningTerm("Point", ("M",)),
                                 "derived_point", "midpoint", call=(("point", "M"), ("segment", ("A", "B"))), fresh="M",
                                 descriptor="midpoint",
                                 phrase=r"trung điểm\s+(?:của\s+)?(?:(?:đoạn thẳng|đoạn|cạnh)\s+)?(?P<ops>{P}{P})(?![\w'])")),
    # Wave 2A: the existing function gains ONE producer contract (data only) — the planner then composes it with every goal
    # contract, as the experimental arm `measure_function_discovery.experimental_centroid_contract` first showed.
    _F("centroid", CentroidArgs, "construct", "Gọi một điểm là trọng tâm của một đa giác.", (("trọng tâm",),),
       planning=PlanningContract((PlanningTerm("Point", ("A",)), PlanningTerm("Point", ("B",)), PlanningTerm("Point", ("C",))),
                                 PlanningTerm("Point", ("G",)), "derived_point", "centroid",
                                 call=(("point", "G"), ("polygon", ("A", "B", "C"))), fresh="G", descriptor="centroid",
                                 phrase=r"trọng tâm\s+(?:của\s+)?(?:(?:tam giác|Δ)\s*)?(?P<ops>{P}{P}{P})(?![\w'])")),
    # Wave 2B: the point P = (1 − t)A + tB of segment [A, B], t = AP/AB — the IR's own `divide_segment` expression. Route B
    # only; the source must state the ratio in a closed equation the gate solves for t (`_ty_so_dung_nguon`).
    _F("divide_segment", DivideSegmentArgs, "construct", "Gọi một điểm chia đoạn theo tỉ số đề nêu (t = AP/AB).",
       (("sao cho", "thỏa mãn", "với"),), provider_offered=False),
    _F("pyramid", PyramidArgs, "construct", "Khối chóp với đỉnh và đáy đã nêu.", (("chóp", "tứ diện"),)),
    _F("regular_pyramid", PyramidArgs, "construct", "Khối chóp ĐỀU: đáy đa giác đều, chân đường cao tại tâm đáy.",
       (("chóp", "tứ diện"), ("đều",))),
    _F("prism", PrismArgs, "construct", "Khối lăng trụ với hai đáy tương ứng; `right` khi đề nói lăng trụ đứng/đều.",
       (("lăng trụ", "hình hộp", "lập phương", _HOP_CHU_NHAT_KW),)),
    _F("ask_volume", AskVolumeArgs, "ask", "Đề hỏi thể tích một khối.", (("thể tích", r"re:(?<![\w'])V(?![\w'])"),)),
    _F("ask_length", AskLengthArgs, "ask", "Đề hỏi độ dài một đoạn.", (("độ dài", "tính", "tìm", _DAI_BAO_NHIEU_KW),),
       planning=PlanningContract((PlanningTerm("Point", ("P",)), PlanningTerm("Foot", ("F", "P", "L"))),
                                 PlanningTerm("AnswerDistance", ("P", "L")), "distance_witness", "distance",
                                 call=(("segment", ("P", "F")),)),
       planning_extra=(PlanningContract((PlanningTerm("Point", ("P",)), PlanningTerm("Point", ("Q",))),
                                 PlanningTerm("AnswerLength", ("P", "Q")), "goal_answer", "length",
                                 call=(("segment", ("P", "Q")),), goal="length",
                                 # the segment joining two points has no order: both closed wordings (M3)
                                 phrase=(r"độ dài\s+(?:của\s+)?đoạn(?:\s+thẳng)?\s+nối\s+(?:{D}){J}{N}(?P<t>{P})(?![\w'])",
                                         r"độ dài\s+(?:của\s+)?đoạn(?:\s+thẳng)?\s+nối\s+{N}(?P<t>{P}){J}(?:{D})")),)),
    _F("ask_distance_point_plane", AskDistancePointPlaneArgs, "ask", "Đề hỏi khoảng cách từ một điểm tới một mặt phẳng.",
       (("khoảng cách", r"re:(?i)(?<![\w/])k/c(?![\w/])"),),
       planning=PlanningContract((PlanningTerm("Point", ("P",)), PlanningTerm("Plane", ("Q",))),
                                 PlanningTerm("AnswerDistance", ("P", "Q")), "distance_answer", "distance",
                                 call=(("point", "P"), ("plane", "Q")))),
    _F("ask_distance_lines", AskDistanceLinesArgs, "ask", "Đề hỏi khoảng cách giữa hai đường thẳng (chéo nhau).",
       (("khoảng cách", r"re:(?i)(?<![\w/])k/c(?![\w/])"),)),
    # Run `hybrid-v2-nl-certificates-e2e`: kernel/IR already measure `distance(line3, plane3)` and `distance(plane3, plane3)`
    # exactly (`measure.distance_sq_line_plane` / `distance_sq_planes`); these expose them to route B / `/4` only.
    _F("ask_distance_line_plane", AskDistanceLinePlaneArgs, "ask", "Đề hỏi khoảng cách giữa một đường thẳng và một mặt phẳng.",
       (("khoảng cách", r"re:(?i)(?<![\w/])k/c(?![\w/])"),), provider_offered=False),
    _F("ask_distance_planes", AskDistancePlanesArgs, "ask", "Đề hỏi khoảng cách giữa hai mặt phẳng.",
       (("khoảng cách", r"re:(?i)(?<![\w/])k/c(?![\w/])"),), provider_offered=False),
    # Goal contracts of the angle asks (Wave 2A): the line is (described point P, named point Q), the target `{M}` a plane /
    # `{L}` a line, in closed wordings (both orders of "nối … với …"). Named angles keep their direct rule (`_cau_hoi`).
    _F("ask_angle_line_plane", AskAngleLinePlaneArgs, "ask", "Đề hỏi góc giữa đường thẳng và mặt phẳng (trả cos²).",
       (("góc",),),
       planning=PlanningContract(
           (PlanningTerm("Point", ("P",)), PlanningTerm("Point", ("Q",)), PlanningTerm("Plane", ("R",))),
           PlanningTerm("AnswerAngleLinePlane", ("P", "Q", "R")), "goal_answer", "angle_line_plane",
           call=(("line", ("P", "Q")), ("plane", "R")), goal="angle",
           phrase=(r"góc\s+(?:giữa|tạo bởi|hợp bởi)\s+(?:đường thẳng|đt|đoạn thẳng|đoạn)\s+nối\s+{N}(?P<t>{P})"
                   r"{J}(?:{D})\s+(?:và|với)\s+{M}",
                   r"góc\s+(?:giữa|tạo bởi|hợp bởi)\s+(?:đường thẳng|đt|đoạn thẳng|đoạn)\s+nối\s+(?:{D}){J}"
                   r"{N}(?P<t>{P})\s+(?:và|với)\s+{M}"))),
    _F("ask_angle_plane_plane", AskAnglePlanePlaneArgs, "ask", "Đề hỏi góc giữa hai mặt phẳng (trả cos²).", (("góc",),)),
    # Wave 2A primitive: kernel/IR already measure `angle_cos_sq(line3, line3)`; this exposes it to route B only.
    _F("ask_angle_lines", AskAngleLinesArgs, "ask", "Đề hỏi góc giữa hai đường thẳng (trả cos²).", (("góc",),),
       provider_offered=False,
       planning=PlanningContract(
           (PlanningTerm("Point", ("P",)), PlanningTerm("Point", ("Q",)), PlanningTerm("Line", ("L",))),
           PlanningTerm("AnswerAngleLines", ("P", "Q", "L")), "goal_answer", "angle_lines",
           call=(("line1", ("P", "Q")), ("line2", "L")), goal="angle",
           phrase=(r"góc\s+(?:giữa|tạo bởi|hợp bởi)\s+(?:đường thẳng|đt|đoạn thẳng|đoạn)\s+nối\s+{N}(?P<t>{P})"
                   r"{J}(?:{D})\s+(?:và|với)\s+{L}",
                   r"góc\s+(?:giữa|tạo bởi|hợp bởi)\s+(?:đường thẳng|đt|đoạn thẳng|đoạn)\s+nối\s+(?:{D}){J}"
                   r"{N}(?P<t>{P})\s+(?:và|với)\s+{L}"))),
    _F("ask_area", AskAreaArgs, "ask", "Đề hỏi diện tích một đa giác.", (("diện tích",),),
       planning=PlanningContract(
           (PlanningTerm("Point", ("P",)), PlanningTerm("Point", ("Q",)), PlanningTerm("Point", ("R",))),
           PlanningTerm("AnswerArea", ("P", "Q", "R")), "goal_answer", "area",
           call=(("polygon", ("P", "Q", "R")),), goal="area",
           phrase=(
               r"diện tích\s+(?:của\s+)?tam giác\s+(?:tạo bởi|có\s+(?:ba\s+)?đỉnh(?:\s+là)?|qua)\s+(?:{D}){K}(?:hai\s+(?:điểm|đỉnh)\s+)?{N}(?P<t1>{P})\s*(?:,\s*|\s+và\s+){N}(?P<t2>{P})(?![\w'])",
               r"diện tích\s+(?:của\s+)?tam giác\s+(?:tạo bởi|có\s+(?:ba\s+)?đỉnh(?:\s+là)?|qua)\s+(?:hai\s+(?:điểm|đỉnh)\s+)?{N}(?P<t1>{P})\s*(?:,\s*|\s+và\s+){N}(?P<t2>{P}){K}(?:{D})",
           ))),
    # Slice 1 (run `hybrid-section-slice`): cửa vào cho phép dựng engine chung ĐÃ có (`construct_section`, `intersect_plane_plane`).
    _F("section", SectionArgs, "construct", "Dựng THIẾT DIỆN của một khối với mặt phẳng qua ba điểm đã có tên.",
       (("thiết diện",),), plane_fields=("plane",)),
    _F("intersection_line", IntersectionLineArgs, "construct", "Dựng GIAO TUYẾN của hai mặt phẳng, mỗi mặt qua ba điểm đã có tên.",
       (("giao tuyến",),), plane_fields=("plane1", "plane2"),
       planning=PlanningContract((PlanningTerm("Plane", ("A",)), PlanningTerm("Plane", ("B",))),
                                 PlanningTerm("Line", ("L",)), "declared_intersection", "intersect_plane_plane")),
    _F("ask_section_area", SectionArgs, "ask", "Đề hỏi diện tích thiết diện của một khối cắt bởi một mặt phẳng.",
       (("diện tích",), ("thiết diện",)), plane_fields=("plane",)),
    _F("ask_volume_ratio", AskVolumeRatioArgs, "ask", "Đề hỏi tỉ số thể tích có hướng giữa hai khối đã dựng.",
       (("tỉ số", "tỷ số", "thể tích", "re:V\\s*(?:\\(|_)"),), provider_offered=False),
    _F("ask_residual_volume", AskResidualVolumeArgs, "ask", "Đề hỏi thể tích phần còn lại của khối gốc sau khi cắt bỏ các khối con đã dựng.",
       (("thể tích",), ("còn lại",)), provider_offered=False),
    # Curved slice (registry /23, /26): planner-only, not offered to route A's provider (model surface unchanged).
    _F("curved_solid", CurvedSolidArgs, "construct", "Khối tròn xoay (trụ, nón, cầu) với tâm, bán kính, chiều cao đề nêu.",
       (("trụ", "nón", "cầu"),), provider_offered=False),
    _F("sphere_tangent_plane", SphereTangentPlaneArgs, "fact",
       "Mặt cầu tiếp xúc với một mặt phẳng (có thể nêu tiếp điểm).",
       (("tiếp xúc", "tiếp điểm"), ("mặt phẳng", "mp", "mặt đáy", "đáy")),
       plane_fields=("plane",), provider_offered=False),
    _F("ask_curved_volume", AskCurvedArgs, "ask", "Đề hỏi thể tích khối trụ / khối nón / khối cầu.", (("thể tích",),),
       provider_offered=False),
    _F("ask_lateral_area", AskCurvedArgs, "ask", "Đề hỏi diện tích xung quanh của hình trụ / hình nón.",
       (("diện tích",), ("xung quanh",)), provider_offered=False),
    _F("ask_surface_area", AskCurvedArgs, "ask", "Đề hỏi diện tích toàn phần của hình trụ / hình nón, hay diện tích mặt cầu.",
       (("diện tích",), ("toàn phần", "mặt cầu")), provider_offered=False),
    _F("ask_radius", AskCurvedArgs, "ask", "Đề hỏi bán kính của khối tròn xoay.", (("bán kính",),), provider_offered=False),
    # Curved sections and the cone ratio (registry /24): planner-only, route A's provider surface unchanged.
    _F("curved_section", CurvedSectionArgs, "construct", "Thiết diện của khối tròn xoay bởi mặt phẳng song song đáy, qua trục, hay (mặt cầu) cách tâm d.",
       (("mặt phẳng", "thiết diện"),), provider_offered=False),
    _F("curved_subsolid", CurvedSubsolidArgs, "construct", "Khối nón nhỏ mà mặt phẳng song song đáy cắt ra ở phía đỉnh.",
       (("nón",),), provider_offered=False),
    _F("ask_curved_section_area", AskCurvedSectionArgs, "ask", "Đề hỏi diện tích thiết diện của khối tròn xoay.",
       (("diện tích",), ("thiết diện", "giao tuyến")), provider_offered=False),
    _F("ask_curved_section_radius", AskCurvedSectionArgs, "ask", "Đề hỏi bán kính đường tròn thiết diện.",
       (("bán kính",), ("thiết diện", "giao tuyến")), provider_offered=False),
    _F("ask_curved_volume_ratio", AskCurvedPairArgs, "ask", "Đề hỏi tỉ số thể tích của hai khối nón theo thứ tự đề nêu.",
       (("tỉ số", "tỷ số"), ("thể tích",)), provider_offered=False),
    _F("ask_curved_residual_volume", AskCurvedPairArgs, "ask", "Đề hỏi thể tích phần còn lại (khối nón cụt).",
       (("thể tích",),), provider_offered=False),
    _F("unsupported", UnsupportedArgs, "escape", "Mệnh đề không ánh xạ được vào thư viện — engine sẽ từ chối trung thực."),
    # Goal-directed slice (run `goal-directed-section-planning`): the plane through M parallel to (Q) is the plane through M
    # and two translates of M along directions of (Q) — the IR's own expression (`PlanePerpendicularToLineExpr` note).
    _F("translate_point", TranslatePointArgs, "construct", "Điểm phụ: ảnh của một điểm qua phép tịnh tiến theo vectơ hai "
       "điểm đã có.", auxiliary_only=True,
       # C18 locus contract: P translated along a direction ⊥ L (of W) spans, with P, the line of W through P ⊥ L.
       planning_extra=(PlanningContract((PlanningTerm("Point", ("P",)), PlanningTerm("PerpDir", ("U", "Z", "L", "W"))),
                                        PlanningTerm("PerpLine", ("X", "P", "L", "W")), "locus_witness",
                                        "_construction_relation", call=(("point", "P"), ("vector", ("U", "Z")), ("image", "X")),
                                        fresh="H", line=("P", "X")),)),
)}
#: The functions offered to the provider of route A — the library minus planner-only auxiliaries.
PROVIDER_FUNCTIONS = tuple(n for n, s in REGISTRY.items() if not s.auxiliary_only and s.provider_offered)
#: Construct functions whose output point is `args.point` — the ONE list the planner's dependency views read.
POINT_PRODUCERS = ("midpoint", "centroid", "divide_segment", "intersect_line_line", "intersect_line_plane")


@dataclass(frozen=True)
class Locus:
    """One locus of a point's definition, as a typed need `PerpLine`: the line of the triangle's plane through `through`
    perpendicular to `perp`. `through` is a definition slot, or ("midpoint", slot, slot) — the point the locus names."""
    through: str | tuple[str, str, str]
    perp: tuple[str, str]


@dataclass(frozen=True)
class PointDefinition:
    """C18: a point the source names by a PROPERTY, as the textbook defines it — the common point of loci ("trực tâm là
    giao điểm của ba đường cao"). No Registry function builds it: `contract` says only what the source names (descriptor,
    phrase, operands A, B, C → Point X, no call); the planner must compose its construction from function contracts, and
    the engine checks the definition itself on the built figure (`engine._MO_TA`), every locus included."""
    contract: PlanningContract
    loci: tuple[Locus, ...]


def _dinh_nghia(descriptor: str, phrase: str, loci: tuple[Locus, ...]) -> PointDefinition:
    return PointDefinition(PlanningContract(
        (PlanningTerm("Point", ("A",)), PlanningTerm("Point", ("B",)), PlanningTerm("Point", ("C",))),
        PlanningTerm("Point", ("X",)), "point_definition", descriptor, fresh="I", descriptor=descriptor, phrase=phrase), loci)


POINT_DEFINITIONS: dict[str, PointDefinition] = {
    # the three altitudes: through a vertex, ⊥ the opposite side
    "orthocenter": _dinh_nghia("orthocenter", r"trực tâm\s+(?:của\s+)?(?:(?:tam giác|Δ)\s*)?(?P<ops>{P}{P}{P})(?![\w'])",
                               (Locus("A", ("B", "C")), Locus("B", ("C", "A")), Locus("C", ("A", "B")))),
    # the three perpendicular bisectors: through a side's midpoint, ⊥ that side
    "circumcenter": _dinh_nghia("circumcenter", r"tâm\s+(?:của\s+)?đường tròn ngoại tiếp\s+(?:(?:tam giác|Δ)\s*)?"
                                r"(?P<ops>{P}{P}{P})(?![\w'])",
                                (Locus(("midpoint", "A", "B"), ("A", "B")), Locus(("midpoint", "B", "C"), ("B", "C")),
                                 Locus(("midpoint", "C", "A"), ("C", "A")))),
}


def descriptor_contracts(kind: str | None) -> list[PlanningContract]:
    """Every contract that realizes the description `kind`: a function's descriptor contract, or a definition's (C18)."""
    out = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.descriptor == kind]
    return out + ([POINT_DEFINITIONS[kind].contract] if kind in POINT_DEFINITIONS else [])

#: Dấu phủ định — xét trong quote VÀ phần mệnh đề đứng ngay trước nó.
PHU_DINH = ("không phải", "không là", "không vuông góc", "không ⊥", "không đều", "không song song", "không đi qua", "không qua", "chưa chắc")
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
_DIEU_KIEN_SAU = re.compile(r"(?<!\w)(?:khi(?!\s+(?:đó|cắt|đã\s+cắt|bỏ|loại\s+bỏ|lấy\s+đi|dựng|quay|chiếu))|nếu|với điều kiện|trừ khi)(?!\w)", re.IGNORECASE)


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


_CURVED_SOLID_ARG_FNS = frozenset({
    "curved_solid", "sphere_tangent_plane",
    "ask_curved_volume", "ask_lateral_area", "ask_surface_area", "ask_radius",
})


def nhan_cua_loi_goi(c: LoiGoi) -> set[str]:
    ra: set[str] = set()
    for key, v in c.args.model_dump().items():
        if key in ("line_ref", "section", "derived", "first", "second"):   # opaque object IDs, never point labels
            continue
        if key == "solid" and c.fn in _CURVED_SOLID_ARG_FNS:
            continue
        if key in ("circumscribes", "inscribed_in") and isinstance(v, str) and "." not in v:
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
#: A rightness cue that NAMES the prism (the solid label must follow it, see `_mat_cua_khoi_sau_cum`): "lăng trụ (tứ giác) đứng",
#: "hình hộp đứng", "lăng trụ tam giác đều", "hộp chữ nhật", "lập phương". An adverb "đều" or a box mentioned elsewhere is not one.
_DUNG_KHOI = re.compile(r"(?<!\w)(?:(?:hình|khối)\s+)?(?:lăng\s+trụ|hộp)(?:\s+(?:tam|tứ|ngũ|lục|đa)\s+giác)?\s+(?:đứng|đều)"
                        r"(?:\s+(?:tam|tứ|ngũ|lục|đa)\s+giác)?(?!\w)|(?<!\w)(?:(?:hình|khối)\s+)?(?:hộp\s+chữ\s+nhật|lập\s+phương)(?!\w)",
                        re.IGNORECASE)
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


def _khoi_dung(c: LoiGoi) -> bool:
    """A right-prism cue that names THIS prism: `<cue> ABCD.A'B'C'D'` or `ABCD.A'B'C'D' là (một) <cue>`."""
    wanted = list(zip(c.args.base, c.args.top))
    for q in c.quotes:
        for dau, cuoi, phan in _tu_nhan(q):
            if len(phan) != 2 or any(len(p) != len(wanted) for p in phan):
                continue
            # Both faces AND their vertex correspondence identify a prism; a shared base alone does not.
            pairs = list(zip(*phan))
            if not any(order[i:] + order[:i] == wanted for order in
                       (pairs, pairs[::-1], [(b, a) for a, b in pairs], [(b, a) for a, b in pairs[::-1]])
                       for i in range(len(pairs))):
                continue
            if (any(m.end() <= dau and not q[m.end():dau].strip() for m in _DUNG_KHOI.finditer(q))
                    or re.match(r"\s+là\s+(?:một\s+)?(?:" + _DUNG_KHOI.pattern + ")", q[cuoi:], re.IGNORECASE)
                    or (re.search(r"(?<!\w)(?:(?:hình|khối)\s+)?(?:lăng\s+trụ|hộp)(?:\s+(?:tam|tứ|ngũ|lục|đa)\s+giác)?\s*$",
                                  q[:dau], re.IGNORECASE)
                        and re.match(r"\s+(?:đứng|đều(?!\s*(?:bằng|là|thuộc|nằm|vuông\s+góc|song\s+song|cắt|đi\s+qua|=))|chữ\s+nhật)(?!\w)",
                                     q[cuoi:], re.IGNORECASE))):
                return True
    return False


#: Shape nouns that fix a vertex count (independent review of 81e91ebb: "Hình vuông ABC cạnh 2", "Đáy ABCD là tam giác đều
#: cạnh 2" were served as an equilateral triangle / a square — a self-contradictory premise hidden by the gate).
_DA_GIAC_SO = re.compile(r"(?<!\w)(?:(?P<t>tam|tứ|ngũ|lục)\s+giác|hình\s+vuông)(?!\w)", re.IGNORECASE)
_SO_DINH = {"tam": 3, "tứ": 4, "ngũ": 5, "lục": 6}


def _so_dinh_khop(cum: str, n: int) -> bool:
    """Every count-bearing shape noun in `cum` names an n-gon."""
    return all((_SO_DINH[m["t"].lower()] if m["t"] else 4) == n for m in _DA_GIAC_SO.finditer(cum))


def _co_doi_tuong_hinh(c: LoiGoi, de: str = "") -> bool:
    """Bind hai cue định nghĩa mới (`lập phương`, `chữ nhật`) vào đúng đa giác, không mượn keyword của đối tượng khác."""
    vertices = list(c.args.vertices)
    if c.fn == "regular_polygon":
        # review of b6a9fcc6: EVERY mention is checked before the polygon is accepted ("Đáy ABC đều cạnh 2, và đáy ABC là
        # hình vuông"); a cube's faces are squares; the legacy "đáy là … giác đều" names its count too
        n, ok = len(vertices), False
        for q in c.quotes:
            if _mat_cua_khoi_sau_cum(q, _LAP_PHUONG, vertices):
                if n != 4:
                    return False
                ok = True
            for dau, cuoi, phan in _tu_nhan(q):
                if any(_cung_da_giac(p, vertices) for p in phan):
                    # the shape noun written right before or after the polygon must name as many vertices as it has
                    truoc = re.search(rf"(?:{_DA_GIAC_SO.pattern})(?:\s+đều)?\s*$", q[:dau], re.IGNORECASE)
                    sau = re.match(rf"\s+(?:là\s+(?:một\s+)?)?(?:{_DA_GIAC_SO.pattern})", q[cuoi:], re.IGNORECASE)
                    if not all(_so_dinh_khop(t.group(), n) for t in (truoc, sau) if t):
                        return False
                    if re.match(r"\s+(?:là\s+)?(?:(?:tam|tứ|ngũ|lục|đa)\s+giác\s+)?đều\b|\s+(?:là\s+)?hình\s+vuông\b",
                                q[cuoi:], re.IGNORECASE):
                        ok = True
                    if re.search(r"(?:(?:tam|tứ|ngũ|lục|đa)\s+giác\s+đều|hình\s+vuông)\s*$",
                                 q[:dau], re.IGNORECASE):
                        ok = True
                # Every triangular face of the explicitly named regular tetrahedron is regular.
                if n == 3 and len(phan) == 1 and len(phan[0]) == 4 and set(vertices) <= set(phan[0]):
                    if (re.search(r"\btứ\s+diện\s+đều\s*$", q[:dau], re.IGNORECASE)
                            or (re.search(r"\btứ\s+diện\s*$", q[:dau], re.IGNORECASE)
                                and re.match(r"\s+đều(?!\s*(?:bằng|là|thuộc|nằm|vuông\s+góc|song\s+song|cắt|đi\s+qua|=))\b",
                                             q[cuoi:], re.IGNORECASE))):
                        ok = True
                if len(phan) == 2 and _cung_da_giac(phan[1 if len(phan[0]) == 1 else 0], vertices):
                    m_day = re.match(
                        r"\s*(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?đáy\s+(?:là\s+(?:một\s+)?)?"
                        r"(?P<sh>(?:(?:tam|tứ|ngũ|lục|đa)\s+giác\s+)?đều|hình\s+vuông)\b",
                        q[cuoi:],
                        re.IGNORECASE,
                    )
                    if m_day:
                        if not _so_dinh_khop(m_day["sh"], n):
                            return False
                        ok = True
            # Legacy multi-sentence "đáy là tam giác đều": resolve only a unique explicitly named base in the source.
            if re.fullmatch(r"đáy\s+(?:là\s+)?(?:tam|tứ|ngũ|lục|đa)\s+giác\s+đều", q.strip(), re.IGNORECASE):
                if not _so_dinh_khop(q, n):
                    return False
                bases = {tuple(p[1]) for dau, _cuoi, p in _tu_nhan(de) if len(p) == 2 and
                         re.search(r"(?:chóp|lăng\s+trụ)\s*$", de[:dau], re.IGNORECASE)}
                if len(bases) == 1 and _cung_da_giac(list(next(iter(bases))), vertices):
                    ok = True
        return ok
    if c.fn != "rectangle":
        return True
    for q in c.quotes:
        if _mat_cua_khoi_sau_cum(q, _HOP_CHU_NHAT, vertices):
            return True
        for dau, cuoi, phan in _tu_nhan(q):
            if len(phan) == 2 and _cung_da_giac(phan[1 if len(phan[0]) == 1 else 0], vertices):
                if re.match(r"\s*(?:có\s+)?(?:chung\s+)?(?:mặt\s+)?đáy\s+(?:là\s+(?:một\s+)?)?hình\s+chữ\s+nhật(?!\w)",
                            q[cuoi:], re.IGNORECASE):
                    return True
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


def _la_doan(phan: list[list[str]], seg: list[str]) -> bool:
    """The word IS the segment label — exactly two point labels, no dot (`BC`, `A'B'`, `CB`). Two consecutive labels
    inside a polygon or solid name (`BC` in `ABCD`, `S.ABCD`) are not a segment the source names (SG-1)."""
    return len(phan) == 1 and phan[0] in (list(seg), list(seg)[::-1])


def _co_doan(quotes: tuple[str, ...], seg: list[str]) -> bool:
    return any(_la_doan(phan, seg) for q in quotes for _a, _b, phan in _tu_nhan(q))


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
            if not _la_doan(phan, seg):
                continue
            so = next((m for m in _SO.finditer(de, dau + b, cuoi) if _doc(m) is not None), None)
            if so and _NOI_BANG.fullmatch(de[dau + b:so.start()]) and _DUOI_BANG.match(de[so.end():]):
                return True
    return False


#: SG-1/SG-3 (rewritten after two review rounds): a measure's number is bound to a ROLE only inside a sentence that parses
#: COMPLETELY in a closed clause grammar about one solid and its base. Any other object, qualifier or wording that carries a
#: number or a role noun leaves the sentence unparsed and its numbers unbound — the value is then refused. No owner is ever
#: inferred from free prose (the review found "SAB là tam giác cân có chiều cao…", "khối hộp có chiều cao…", "của mặt bên").
_L1 = r"(?-i:[A-Z][0-9]*'?)"
_NHAN = rf"{_L1}+"


def _so_nhom(g: str) -> str:
    """The number grammar with group names of its own (one per clause) and an optional length unit."""
    # never empty, and case-sensitive: the parameter is "a", never the label "A" (the clauses are case-insensitive)
    return (f"(?P<{g}>(?=[0-9√]|(?-i:a)(?![\\w']))(?-i:" + _SO.pattern.replace("(?P<", f"(?P<{g}_") + "))"
            r"(?:\s*(?:cm|dm|mm|m|đvđd)(?![\w']))?"
            r"(?:\s*\((?:đơn\s+vị[^()]*|cm|dm|mm|m|đvđd)\))?")


_AT_TRI_2D = rf"(?:\s+(?:tại|ở)\s+{_L1})?"
_AT_TRAP_2D = rf"(?:\s+(?:tại|ở)\s+{_L1}(?:\s*(?:và|,\s*(?!{_L1}\s+(?:là|thuộc|nằm|trên|có|=|⊥|//)))\s*{_L1})?)?"
_DEU_CUOI_2D = r"đều(?!\s*(?:bằng|là|thuộc|nằm|vuông\s+góc|song\s+song|cắt|đi\s+qua|=))"
#: Canonical 2D polygon shape-noun fragments shared by sentence role-binding (`_HINH`) and PE-2 invariant extraction (`_HEAD_2D`/`_PRED_2D`).
_DANH_TU_DA_GIAC_2D = (
    r"hình\s+vuông",
    r"hình\s+chữ\s+nhật",
    r"hình\s+thoi",
    r"hình\s+bình\s+hành",
    rf"lục\s+giác\s+{_DEU_CUOI_2D}",
    rf"tứ\s+giác\s+{_DEU_CUOI_2D}",
)
_HINH = (
    rf"(?:tam\s+giác(?:\s+(?:{_DEU_CUOI_2D}|vuông\s+cân|vuông(?!\s+góc\b)|cân|nhọn|tù))?{_AT_TRI_2D}|"
    + "|".join(_DANH_TU_DA_GIAC_2D)
    + rf"|hình\s+thang(?:\s+(?:vuông|cân))?{_AT_TRAP_2D})"
)
#: SL-1 (tenth continuation, `student-language-probe.json`): a learner asks to SEE a figure ("Vẽ / Dựng / Mô phỏng / Cho
#: mình xem hình chóp …"). The verb states no geometry: it opens a solid clause exactly like "Cho", or forms a request
#: that only mentions objects the validated calls already build (`_doc_yeu_cau_mo_phong`). It never adds a fact.
_DONG_TU_MO_PHONG = (r"(?:(?:(?:em|bạn)\s+)?hãy\s+)?(?:vẽ|dựng|mô\s+phỏng|minh\s+ho[ạa]|biểu\s+diễn|hiển\s+thị"
                     r"|cho\s+(?:mình|em|tôi|tớ)\s+xem)(?:\s+giúp(?:\s+(?:mình|em|tôi|tớ))?|\s+lại)?(?!\w)")
_C_KHOI = re.compile(rf"(?:(?:cho|xét|{_DONG_TU_MO_PHONG})\s+)?(?:một\s+)?(?:(?:hình|khối)\s+)?(?P<kn>chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)"
                     rf"(?P<km>(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|ngũ\s+giác|lục\s+giác|chữ\s+nhật))*)"
                     rf"\s+(?P<k>{_NHAN}(?:\.{_NHAN})?)(?![\w'])"
                     rf"(?P<km2>(?:\s+(?:đứng|xiên|{_DEU_CUOI_2D}|chữ\s+nhật))*)(?![\w'])", re.IGNORECASE)


def _km_khoi(m: re.Match[str]) -> str:
    return re.sub(r"\s+", " ", f"{m['km'] or ''} {m.groupdict().get('km2') or ''}".lower()).strip()
_C_DAY = re.compile(rf"(?:(?:có|với)\s+)?(?:(?:mặt|tứ\s+giác|tam\s+giác)\s+)?đáy(?:\s+(?P<d>{_NHAN}))?\s+(?:là\s+(?:một\s+)?{_HINH}(?:\s+(?P<d2>{_NHAN}))?(?:\s+vuông(?:\s+cân)?\s+(?:tại|ở)\s+{_L1})?|đều|vuông(?:\s+cân)?\s+(?:tại|ở)\s+{_L1})(?![\w'])"
                    rf"(?:(?:\s*,\s*|\s+)(?:(?:và|với)\s+)?(?:có\s+)?(?:(?:các|mọi|mỗi)\s+)?(?:độ\s+dài\s+)?cạnh\s*(?:(?:bằng|=|là)\s*)?{_so_nhom('ds')})?", re.IGNORECASE)
_C_VAI = re.compile(rf"(?:(?:có|với)\s+)?(?:(?:các|mọi|mỗi)\s+)?(?:độ\s+dài\s+(?:(?:các|mọi|mỗi)\s+)?)?(?P<vai>cạnh\s+đáy|cạnh\s+bên|chiều\s+cao|đường\s+cao|cạnh)(?:\s+(?:của\s+(?:(?:hình|khối)\s+)?|(?:hình|khối)\s+|(?=tứ\s+diện))"
                    rf"(?P<qn>chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)(?:\s+(?P<ql>{_NHAN}(?:\.{_NHAN})?))?)?"
                    rf"\s*(?:(?:có\s+)?độ\s+dài\s*)?(?:(?:=|bằng|là)\s*)?{_so_nhom('vs')}", re.IGNORECASE)
#: "của <solid>" names the role's owner: its noun must be the bound solid's kind, its label (if any) the bound solid's
_LOAI_KHOI = {"chóp": ("pyramid", "regular_pyramid"), "tứ diện": ("pyramid", "regular_pyramid"), "lăng trụ": ("prism",),
              "hộp": ("prism",), "hộp chữ nhật": ("prism",), "lập phương": ("prism",)}
#: Number-free clauses of the grammar: "SA là đường cao của hình chóp" (altitude statement).
_C_DCAO = re.compile(rf"{_L1}{_L1}\s+là\s+đường\s+cao(?:\s+của\s+(?:(?:hình|khối)\s+)?(?:chóp|lăng\s+trụ)(?:\s+{_NHAN}(?:\.{_NHAN})?)?)?"
                     rf"(?![\w'])(?=\s*(?:[,;.]|và\s|$))", re.IGNORECASE)
#: Number-free CLOSED point definition (review round 4: no word-list exemption): "(gọi) X là trung điểm / tâm / trọng tâm /
#: giao điểm / hình chiếu (vuông góc) … của <labelled object>", "X là điểm (di động) trên/thuộc cạnh XY" — the whole clause.
_DOI_TUONG_NHAN = (rf"(?:(?:cạnh|đoạn(?:\s+thẳng)?|đường\s+thẳng|tam\s+giác|hình\s+vuông|hình\s+chữ\s+nhật|mặt\s+phẳng|"
                   rf"mặt\s+đáy|đáy|mp)\s*)?\(?{_NHAN}\)?")
_C_DIEM = re.compile(rf"(?:gọi\s+)?{_L1}\s+là\s+(?:(?:trung\s+điểm|tâm|trọng\s+tâm)\s+(?:của\s+)?{_DOI_TUONG_NHAN}"
                     rf"|giao\s+điểm\s+(?:của\s+)?{_DOI_TUONG_NHAN}\s+(?:và|với)\s+{_DOI_TUONG_NHAN}"
                     rf"|điểm(?:\s+di\s+động)?\s+(?:nằm\s+)?(?:trên|thuộc)\s+{_DOI_TUONG_NHAN})"
                     rf"(?![\w'])(?=\s*(?:[,;.]|và\s|$))", re.IGNORECASE)
#: A projection may be read as the foot of a height stated in the same sentence: kept readable, but a subject change.
_C_CHIEU = re.compile(rf"(?:(?:gọi\s+)?{_L1}\s+(?:là|trùng\s+với)\s+hình\s+chiếu(?:\s+vuông\s+góc)?\s+của\s+{_L1}\s+(?:lên|trên)\s+{_DOI_TUONG_NHAN}"
                      rf"|hình\s+chiếu(?:\s+vuông\s+góc)?\s+của\s+{_L1}\s+(?:lên|trên)\s+{_DOI_TUONG_NHAN}\s+(?:là|trùng\s+với)\s+(?:(?:điểm|đỉnh|trung\s+điểm|trọng\s+tâm)\s+)?{_L1}(?:\s+của\s+{_DOI_TUONG_NHAN})?)"
                      rf"(?![\w'])(?=\s*(?:[,;.]|và\s|$))", re.IGNORECASE)
_C_DOAN = re.compile(rf"(?:(?:có|với)\s+)?(?:(?:các\s+)?kích\s+thước\s+)?(?:độ\s+dài\s+(?:của\s+)?)?(?:(?P<sv>cạnh\s+bên|chiều\s+cao|đường\s+cao)\s+|(?:cạnh|đoạn(?:\s+thẳng)?|đường\s+chéo|số\s+đo)\s+)?"
                     rf"(?P<seg>{_L1}{_L1})(?![\w'])"
                     rf"(?:\s*=\s*{_L1}{_L1}(?![\w']))*\s*(?:=|bằng|(?:có\s+)?độ\s+dài(?:\s+bằng)?)\s*{_so_nhom('ss')}",
                     re.IGNORECASE)
_C_VUONG = re.compile(rf"(?:(?:có|với|biết)\s+)?(?:(?:cạnh\s+bên|cạnh|đường\s+thẳng)\s+)?{_L1}{_L1}\s*(?:vuông\s+góc(?:\s+với)?|vuông|⊥)\s*"
                      rf"(?:mặt\s+phẳng\s+|mp\s*)?(?:\({_NHAN}\)|{_L1}{_L1}\s+và\s+{_L1}{_L1}(?![\w'])(?!\s*(?:=|bằng))|{_NHAN}(?![\w'])"
                      rf"|(?:mặt\s+(?:phẳng\s+)?)?đáy(?!\w))", re.IGNORECASE)
#: "cạnh CD" (a named edge) continues its clause; only a role "cạnh" ("… cạnh 2", "… cạnh bên") opens a new one
_C_NOI = re.compile(rf"\s*[,;]\s*(?:và\s+)?|\s+và\s+|\s+(?=biết\s|th[ỏo]a\s+mãn\s|với\s+(?:(?:mặt|tứ\s+giác|tam\s+giác)\s+)?đáy(?!\w)|có\s|với\s+(?:(?:(?:các|mọi|mỗi)\s+)?(?:cạnh|chiều\s+cao|đường\s+cao|độ\s+dài|đoạn(?:\s+thẳng)?|đường\s+chéo|kích\s+thước)(?!\w)|{_L1}{_L1}(?![\w']))"
                    rf"|(?:(?:các|mọi|mỗi)\s+)?cạnh\s+(?!{_L1}{_L1}(?![\w'])))", re.IGNORECASE)
#: Number-free CLOSED premise clauses (review round 4): a face ⊥ a face, the shape of a named triangle/face (optionally
#: lying in a plane ⊥ the base), equal named segments. They bind nothing; they only keep their sentence parseable.
_MAT_NHAN = rf"(?:(?:mặt\s+bên|mặt\s+phẳng|mặt|mp)\s*\(?{_L1}{_L1}{_NHAN}\)?|\({_L1}{_L1}{_NHAN}\))"
_MAT_DICH = rf"(?:mặt\s+phẳng\s+|mặt\s+|mp\s*)?(?:\({_NHAN}\)|{_NHAN}(?![\w'])|đáy(?!\w))"
_C_MAT = re.compile(rf"(?:{_MAT_NHAN}\s+(?:và\s+)?(?:nằm\s+trong\s+mặt\s+phẳng\s+)?vuông\s+góc\s+với\s+{_MAT_DICH}"
                    rf"|(?:(?:mặt\s+bên|tam\s+giác)\s+)?{_L1}{_L1}{_NHAN}\s+(?:là\s+(?:một\s+)?)?(?:tam\s+giác\s+)?"
                    rf"(?:đều|vuông(?:\s+cân)?(?:\s+tại\s+{_L1})?|cân(?:\s+tại\s+{_L1})?)(?![\w'])"
                    rf"(?:\s+(?:và\s+)?(?:nằm\s+)?trong\s+mặt\s+phẳng\s+vuông\s+góc\s+với\s+{_MAT_DICH})?"
                    rf"|{_L1}{_L1}(?:\s*=\s*{_L1}{_L1})+(?![\w'])(?!\s*=))"
                    rf"(?=\s*(?:[,;.]|và\s|$))", re.IGNORECASE)
_C_DAU = re.compile(r"\s*(?:trong\s+không\s+gian\s*,\s*)?(?:(?:biết(?:\s+rằng)?|th[ỏo]a\s+mãn)\s+)?", re.IGNORECASE)
_C_HET = re.compile(r"\s*[.;]?\s*")
_C_HOI = re.compile(r"(?:hãy\s+)?(?:tính|tìm|xác\s+định|hỏi)(?!\w)", re.IGNORECASE)
#: A named polygon with its side ("Tam giác ABC đều cạnh 2"): the side belongs to THAT polygon (labelled binding); like any
#: other-object clause it changes the subject for unlabelled roles of the sentence.
_C_DAGIAC = re.compile(rf"(?:tam\s+giác|hình\s+vuông|lục\s+giác)\s+(?P<p>{_L1}{_L1}{_NHAN})(?![\w'])\s+(?:là\s+(?:một\s+)?"
                       rf"(?:tam\s+giác\s+|hình\s+vuông\s+|lục\s+giác\s+)?)?(?:đều\s+)?(?:có\s+)?cạnh\s*(?:(?:bằng|=|là)\s*)?"
                       rf"{_so_nhom('ps')}", re.IGNORECASE)
_DANH_VAI = re.compile(r"(?<!\w)(?:cạnh|chiều\s+cao|đường\s+cao)(?!\w)", re.IGNORECASE)
_KHOI_FN = ("pyramid", "regular_pyramid", "prism")


def _vai_doan_ok(m: re.Match, khoi: LoiGoi | None, calls: tuple[LoiGoi, ...]) -> bool:
    """W4 review B1: a role prefix of a labelled length ("chiều cao XY", "cạnh bên XY") is a CLAIM about XY. It is read
    only when the bound solid and its validated calls prove it — height: XY ⊥ the base (the `dcao` predicate) or a lateral
    edge of a RIGHT prism; lateral edge: apex–base vertex / base vertex–its top vertex. Unproved ⇒ the clause is unread."""
    vai_tro = re.sub(r"\s+", " ", (m["sv"] or "").lower())
    if not vai_tro:
        return True
    seg = re.findall(r"[A-Z][0-9]*'?", m["seg"])
    if khoi is None or len(set(seg)) != 2:
        return False
    if khoi.fn in ("pyramid", "regular_pyramid"):
        canh_ben = khoi.args.apex in seg and set(seg) - {khoi.args.apex} <= set(khoi.args.base)
    else:
        canh_ben = any({b, t} == set(seg) for b, t in zip(khoi.args.base, getattr(khoi.args, "top", None) or []))
    if vai_tro == "cạnh bên":
        return canh_ben
    base = set(khoi.args.base)
    return (khoi.fn == "prism" and bool(getattr(khoi.args, "right", False)) and canh_ben) or any(
        (d.fn == "perpendicular_line_plane" and set(d.args.line) == set(seg) and set(d.args.plane) <= base)
        or (d.fn == "altitude" and {d.args.apex, d.args.foot} == set(seg))
        or (d.fn == "orthogonal_projection" and {d.args.point, d.args.image} == set(seg) and set(d.args.plane) <= base)
        for d in calls)


def _nhan_khoi(k: LoiGoi) -> set[str]:
    return {*([k.args.apex] if k.fn in ("pyramid", "regular_pyramid") else []), *k.args.base, *(getattr(k.args, "top", None) or [])}


#: One object a simulation request may show (SL-1): the figure, a declared polyhedron by its GENERIC kind word (and its
#: own notation), or built points — the scene draws exactly these. A specific class word ("lập phương", "hộp", "tứ diện")
#: is a claim the gate does not verify here, a segment / line / plane is not drawn, and a shape noun ("hình vuông ABCD")
#: is a claim: none is a mention (independent review, BLOCKERs 1–2).
_VAT_MO_PHONG = re.compile(rf"(?:(?:hình|khối)\s+(?P<kn>chóp|lăng\s+trụ)(?:\s+(?P<k>{_NHAN}\.{_NHAN}))?(?!\s*(?:đều|đứng|xiên))"
                           rf"|(?P<hinh>hình(?:\s+vẽ)?)"
                           rf"|(?:các\s+)?(?P<vai>điểm|đỉnh)\s+(?P<d>{_L1}(?:\s*,\s*{_L1})*))"
                           rf"(?:\s+(?:này|đó|đã\s+cho|trên))?(?![\w'])", re.IGNORECASE)
_NOI_VAT_MO_PHONG = re.compile(r"\s*,\s*(?:và\s+)?|\s+và\s+|\s+cùng\s+(?:với\s+)?", re.IGNORECASE)
_MO_YEU_CAU_MO_PHONG = re.compile(rf"\s*(?:(?:không|chưa)\s+cần\s+)?{_DONG_TU_MO_PHONG}\s+", re.IGNORECASE)
#: … then the question of the same sentence ("Vẽ hình rồi tính …", "Không cần vẽ hình, tính …").
_SAU_MO_PHONG_HOI = re.compile(r"(?:\s*,\s*|\s+)(?:(?:rồi|và|sau\s+đó|đồng\s+thời)\s+)?(?=(?:hãy\s+)?(?:tính|tìm|xác\s+định)(?!\w))",
                               re.IGNORECASE)


def _doc_yeu_cau_mo_phong(de: str, a: int, b: int, calls: tuple[LoiGoi, ...]) -> int | None:
    """End of the simulation request opening `de[a:b]` (SL-1), else None: `b` when it is the whole segment, or the start of
    the question that follows it in the same sentence. Every mention must be an object the validated calls build — the
    figure, a declared solid of that kind and notation, labels some call uses — so the request reads no new content."""
    khoi = [k for k in calls if k.fn in _KHOI_FN]
    dung = {n for c in calls for n in nhan_cua_loi_goi(c)}
    if not khoi or (m := _MO_YEU_CAU_MO_PHONG.match(de, a, b)) is None:
        return None
    p = m.end()
    while True:
        v = _VAT_MO_PHONG.match(de, p, b)
        if v is None:
            return None
        if v["kn"]:
            loai = _LOAI_KHOI[re.sub(r"\s+", " ", v["kn"].lower())]
            nhan = set(re.findall(r"[A-Z][0-9]*'?", v["k"] or ""))
            if not any(k.fn in loai and (not nhan or nhan == _nhan_khoi(k)) for k in khoi):
                return None
        elif v["d"]:
            diem = set(re.findall(r"[A-Z][0-9]*'?", v["d"]))
            # "đỉnh" claims a solid vertex; "điểm" any point a validated call builds (drawn in the scene)
            if not diem <= (set().union(*map(_nhan_khoi, khoi)) if v["vai"].lower() == "đỉnh" else dung):
                return None
        p = v.end()
        if _C_HET.fullmatch(de, p, b):
            return b
        if (q := _SAU_MO_PHONG_HOI.match(de, p, b)) is not None:
            return q.end()
        if (j := _NOI_VAT_MO_PHONG.match(de, p, b)) is None:
            return None
        p = j.end()


def _phan_tich_cau(s: str) -> list[tuple[str, re.Match | None]] | None:
    """Clauses of sentence `s` when ALL of it parses, else None. A clause outside the grammar is tolerated only when it
    carries no number; it is recorded as opaque ("mo") and its whole sentence then binds no role (`_lien_ket_cau`)."""
    p, out = _C_DAU.match(s).end(), []
    while True:
        # the request part of the sentence ("…, SA = 3, tính độ dài SC.") ends its premises; it binds nothing, and a request
        # carrying a number (a local given or a changed value) leaves the sentence unread
        if q := _C_HOI.match(s, p):
            return out if not any(_doc(x) is not None for x in _SO.finditer(s, q.end())) else None
        for kind, rx in (("khoi", _C_KHOI), ("day", _C_DAY), ("dagiac", _C_DAGIAC), ("dcao", _C_DCAO), ("diem", _C_DIEM),
                         ("chieu", _C_CHIEU), ("mat", _C_MAT), ("vuong", _C_VUONG), ("doan", _C_DOAN), ("vai", _C_VAI)):
            if m := rx.match(s, p):
                out.append((kind, m))
                p = m.end()
                break
        else:
            j = _C_NOI.search(s, p)
            seg = s[p:j.start()] if j else s[p:].rstrip(" .;")
            if not seg.strip() or any(_doc(x) is not None for x in _SO.finditer(seg)):
                return None
            out.append(("mo", None))
            p += len(seg)
        if _C_HET.fullmatch(s, p):
            return out
        j = _C_NOI.match(s, p)
        if j is None or j.end() == p:
            return None
        p = _C_DAU.match(s, j.end()).end()


def _khop_ky_hieu_khoi(k: LoiGoi, k_str: str) -> bool:
    """Match solid call `k` against notation `k_str` preserving apex/base vs base/top partition on dotted notation."""
    if "." in k_str:
        p0, p1 = (re.findall(r"[A-Z][0-9]*'?", x) for x in k_str.split(".", 1))
        if k.fn in ("pyramid", "regular_pyramid"):
            return [k.args.apex] == p0 and _cung_da_giac(list(k.args.base), p1)
        if k.fn == "prism":
            b, t = list(k.args.base), list(k.args.top)
            return (
                len(p0) == len(p1) == len(b)
                and ((_cung_da_giac(b, p0) and _cung_da_giac(t, p1)) or (_cung_da_giac(b, p1) and _cung_da_giac(t, p0)))
                and {frozenset(e) for e in zip(b, t)} == {frozenset(e) for e in zip(p0, p1)}
            )
        return False
    return _nhan_khoi(k) == set(re.findall(r"[A-Z][0-9]*'?", k_str))


def _lien_ket_cau(de: str, a: int, b: int, calls: tuple[LoiGoi, ...]) -> dict[int, tuple]:
    """number start (in `de`) → its binding, for the numbers of `de[a:b]`, read from the parse of each sentence they lie in:
    ("side", base labels) · ("vai", role, solid call, every-edge-equal) · ("seg", segment). Unparsed ⇒ no entry."""
    out: dict[int, tuple] = {}
    khoi_goi = [k for k in calls if k.fn in _KHOI_FN]
    p = a
    while p < b:
        x, y = _bien_cau(de, p)
        cau = _phan_tich_cau(de[x:y])
        # reviews round 3–4: an opaque clause may re-attribute ANY role of its sentence, before or after it ("…, đường cao
        # bằng 5, H là chân của nó trên cạnh AB", "…cạnh 3, nhưng đó là cạnh của tam giác khác"): a sentence with any
        # opaque clause binds nothing. No exemption list — point definitions are closed grammar clauses (`_C_DIEM`).
        if cau is not None and not any(kind == "mo" for kind, _m in cau) and _so_dinh_cau_khop(cau, khoi_goi):
            khoi, moi = (khoi_goi[0] if len(khoi_goi) == 1 else None), False
            # review round 5: a face / triangle / altitude / projection clause changes the subject — a role anywhere in the
            # sentence ("mặt bên SAB là tam giác cân và có chiều cao bằng 5") may be ITS role, and its shape premise is
            # encoded by no call: no unlabelled role of such a sentence is bound. A plain point definition (midpoint,
            # centre, centroid, intersection, point on an object) names no height or side and changes nothing.
            mo = any(kind in ("chieu", "mat", "dcao", "dagiac") for kind, _m in cau)
            # review round 6 (N1/N2): "G là trọng tâm của tam giác SAB và có đường cao bằng 5" — a "có/với <role>" right
            # after a point definition may predicate that definition's object: the sentence's roles are not bound.
            mo = mo or any(k0 == "diem" and k1 == "vai" and re.match(r"(?:có|với)\s", m1.group(), re.IGNORECASE)
                           for (k0, _m0), (k1, m1) in zip(cau, cau[1:]))
            for kind, m in cau:
                if kind == "khoi":
                    khop = [k for k in khoi_goi if _khop_ky_hieu_khoi(k, m["k"])]
                    khoi = khop[0] if len(khop) == 1 else None
                    tu = re.sub(r"\s+", " ", m["kn"].lower())
                    moi = tu == "lập phương" or tu == "tứ diện" and "đều" in _km_khoi(m)
                elif kind == "dagiac":
                    nhan = re.findall(r"[A-Z][0-9]*'?", m["p"])
                    if _so_dinh_khop(m.group(), len(nhan)):              # "Hình vuông ABC cạnh 2" binds nothing
                        out[x + m.start("ps")] = ("side", frozenset(nhan))
                elif kind == "day" and m["ds"] and (m["d"] or m["d2"] or not mo):
                    day = m["d"] or m["d2"]
                    nhan = re.findall(r"[A-Z][0-9]*'?", day) if day else (list(khoi.args.base) if khoi else [])
                    if not nhan or _so_dinh_khop(m.group(), len(nhan)):  # "Đáy ABCD là tam giác đều cạnh 2" binds nothing
                        out[x + m.start("ds")] = ("side", frozenset(nhan))
                elif kind == "doan" and _vai_doan_ok(m, khoi, calls):
                    out[x + m.start("ss")] = ("seg", frozenset(re.findall(r"[A-Z][0-9]*'?", m["seg"])))
                elif kind == "vai" and not mo and _cua_khop(m, khoi, calls):
                    out[x + m.start("vs")] = ("vai", re.sub(r"\s+", " ", m["vai"].lower()), khoi, moi)
        p = y + 1 if y > p else b
    return out


def _so_dinh_cau_khop(cau: list[tuple[str, re.Match | None]], khoi_goi: list[LoiGoi]) -> bool:
    """Review of 08bad12f: every count-bearing shape noun of the sentence's solid / base / named-polygon clauses names as
    many vertices as its polygon — the labelled one, or for an unlabelled "(mặt) đáy là …" the bound solid's base ("hình
    chóp tam giác đều S.ABC có cạnh đáy bằng 2, đáy là hình vuông"). A contradicting or unresolvable count: no binding."""
    khoi = khoi_goi[0] if len(khoi_goi) == 1 else None
    for kind, m in cau:
        if kind == "khoi":
            khop = [k for k in khoi_goi if _khop_ky_hieu_khoi(k, m["k"])]
            khoi = khop[0] if len(khop) == 1 else None
            km_m = _km_khoi(m)
            if _DA_GIAC_SO.search(km_m) and (khoi is None or not _so_dinh_khop(km_m, len(khoi.args.base))):
                return False
        elif kind in ("day", "dagiac") and _DA_GIAC_SO.search(m.group()):
            nhan = m["p"] if kind == "dagiac" else (m["d"] or m["d2"])
            n = len(re.findall(r"[A-Z][0-9]*'?", nhan)) if nhan else (len(khoi.args.base) if khoi else 0)
            if not _so_dinh_khop(m.group(), n):
                return False
    return True


#: A count-bearing shape noun, spelled freely ("hình tứ giác", "tứ-giác", "hình vuông").
_DEM_LOI = r"(?:hình\s+)?(?:tam|tứ|ngũ|lục)[\s-]+giác|hình\s+vuông"
_DEM_RX = re.compile(rf"(?<!\w)(?i:{_DEM_LOI})(?!\w)")
_KHOI_DEM = re.compile(rf"(?<!\w)(?i:(?:(?:hình|khối)\s+)?(?P<kn>chóp|lăng\s+trụ))"
                       rf"(?P<km>(?i:\s+(?:đứng|đều|xiên|{_DEM_LOI})(?!\w))*)\s+(?P<k>{_NHAN}(?:\.{_NHAN})?)(?![\w'])")
_KHOI_4 = re.compile(rf"(?i:hộp|lập\s+phương)(?:\s+(?i:chữ\s+nhật))?\s+{_NHAN}\.{_NHAN}(?![\w'])")
_TU_DIEN = re.compile(rf"(?i:tứ\s+diện)(?:\s+(?i:đều))?\s+{_NHAN}(?![\w'])")
#: a polygon label right after the noun, past its modifiers; a sentence-final period ends it, "ABC.A'B'C'" is a solid
_DEM_SAU_NHAN = re.compile(rf"(?i:\s+(?:đều|vuông|cân|nhọn|tù)(?!\w))*\s+(?:(?P<tri>[Δ∆△])\s*)?\(?(?P<p>{_L1}{_L1}{_NHAN}?)\)?(?![\w']|\.\w)")
_NHAN_LA = re.compile(rf"(?<![\w'.])(?:(?P<tri>[Δ∆△])\s*)?\(?(?P<p>{_L1}{_L1}{_NHAN}?)\)?\s+(?i:là\s+(?:(?:một|các|những)\s+)?)$")
#: base clause right before the noun: "(hai) (mặt) đáy (ABCD) (là (một|hai))"
_DAY_TRUOC = re.compile(rf"(?<!\w)(?i:(?:hai\s+)?(?:mặt\s+)?đáy)(?:\s+\(?{_NHAN}\)?)?\s+(?i:(?:là\s+(?:(?:một|hai)\s+)?)?)$")
#: base named right after the noun (or its label): "tam giác đáy", "hình vuông SABC làm đáy", "… là đáy"
_DAY_SAU = re.compile(r"(?i:(?:\s+(?:làm|là)(?:\s+mặt)?)?\s+đáy)(?!\w)")
#: the solid's top / bottom face: "mặt dưới (của nó) là", "phần dưới cùng là một"
_MAT_TREN_DUOI = re.compile(r"(?i:(?<!\w)(?:mặt|phần)\s+(?:trên|dưới)(?:\s+cùng)?(?:\s+của\s+[^.;,]{1,30}?)?\s+là\s+(?:một\s+)?)$")
#: a face predicate: "(mỗi|các|ba) mặt (bên) (của …) (đều) là|tạo với đáy (một|các|ba …)"
_MAT_TRUOC = re.compile(r"(?<!\w)(?i:mặt)(?!\s+(?i:phẳng|đáy|trên|dưới|cầu)(?!\w))(?P<ben>\s+(?i:bên)(?!\s+(?i:dưới|trên|trong|ngoài|cạnh|phải|trái|phía)(?!\w)))?(?!\w)[^.;]{0,40}?"
                        r"\s(?i:(?:đều\s+)?(?:là|tạo\s+với\s+đáy)\s+(?:(?:các|những|một|hai|ba|bốn|mỗi)\s+)?)$")
#: "…, và (cũng) là <noun>": the same subject as the sentence's previous noun
_NOI_TRUOC = re.compile(r"(?i:(?:\s+và|,)\s+(?:cũng\s+)?là\s+(?:một\s+)?)$")
#: a plane section is any polygon: "thiết diện là (một)", "cắt … theo (thiết diện là) (một)"
_THIET_DIEN = re.compile(r"(?i:(?<!\w)(?:thiết\s+diện(?:\s+là)?|theo(?:\s+thiết\s+diện(?:\s+là)?)?)\s+(?:một\s+)?)$")
#: a solid noun right before the noun, without the solid's label after it ("S.ABC là hình chóp tứ giác")
_KHOI_TRUOC = re.compile(r"(?i:(?<!\w)(?:chóp|lăng\s+trụ)(?:\s+(?:đứng|đều|xiên))*\s+)$")
#: a polygon given by its points ("tam giác tạo bởi …", "tam giác có ba đỉnh là …") names no polygon of the solid
_MO_TA_DINH = re.compile(r"(?i:\s+(?:tạo\s+bởi|có\s+(?:ba\s+|bốn\s+|các\s+)?đỉnh))(?!\w)")
#: the request part of a sentence asks about an object, it states no premise polygon
_HOI_TRUOC = re.compile(r"(?i)(?<!\w)(?:tính|tìm|xác\s+định|hỏi)(?!\w)")
_CAU = re.compile(r"[.;!?](?=\s|$)")
_VE_KHOI = re.compile(r"(?i)(?<!\w)(?:đáy|chóp|lăng\s+trụ|hộp|lập\s+phương|tứ\s+diện|khối)(?!\w)")


def _so_cua_dem(noun: str) -> int:
    t = re.search(r"(?i)(?<!\w)(tam|tứ|ngũ|lục)(?=[\s-]+giác)", noun)
    return _SO_DINH[t.group(1).lower()] if t else 4


def _kiem_so_dinh_nguon(de: str, calls: tuple[LoiGoi, ...] = ()) -> None:
    """Source-level, FAIL-CLOSED vertex-count gate (reviews of the T3 fix, rounds 1-7). Every count-bearing shape noun of
    the text must be positively attributed and agree with what it names: the solid name it is part of ("hình chóp tam
    giác đều S.ABC"); a polygon label right after it ("trọng tâm tam giác vuông cân ABC."); a label it predicates ("ABCD
    là hình vuông"); the base ("(mặt) đáy (ABCD) là …", "tam giác đáy", "… làm đáy", "mặt dưới là …", "… là hình chóp
    tứ giác") — which must ALSO agree with the base of the solid(s) the text names; a face ("mặt bên … là": 3 for a
    pyramid, 4 for a prism; "các mặt … là": tetrahedron 3, box/cube 4); the previous noun of its sentence ("…, và là
    …"). A plane section ("thiết diện là …", "cắt … theo …") is any polygon. A noun attributed to nothing is refused
    whenever the text names a solid (or the sentence speaks of one)."""
    def dem(lb: str) -> int:
        return len(re.findall(r"[A-Z][0-9]*'?", lb))
    def mot(xs: set[int]) -> int | None:
        # the owner is the DECLARED solid (review of c7b79cce: a sub-solid merely named in the text must not defer the
        # check). Several declared solids: the multi-solid gate downstream owns that refusal (`UNSUPPORTED_MULTIPLE_BASES`)
        # — deferred, never passed: None. No owner at all in a text that names a solid: refused.
        if len(xs) == 1:
            return next(iter(xs))
        if len(khoi_goi) > 1:
            return None
        raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{de[max(0, m.start() - 30):m.end() + 12]!r}: không xác định được đa giác "
                                               "nào của khối mà hình này gọi tên")
    so_day, ben, mat = set(), set(), set()
    da_xet: set[int] = set()
    for m in _KHOI_DEM.finditer(de):
        dau, _, sau = m["k"].partition(".")
        lang = "lăng" in m["kn"].lower()
        n = dem(dau) if lang else (dem(sau) if sau else dem(dau) - 1)
        so_day.add(n)
        ben.add(4 if lang else 3)
        for d in _DEM_RX.finditer(m["km"]):
            da_xet.add(m.start("km") + d.start())
            if _so_cua_dem(d.group()) != n:
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{m.group()!r}: tên khối nêu số đỉnh đáy khác nhãn của nó")
    for _ in _KHOI_4.finditer(de):
        so_day.add(4), mat.add(4)
    for _ in _TU_DIEN.finditer(de):
        so_day.add(3), mat.add(3)
    co_khoi = bool(so_day)
    khoi_goi = [c for c in calls if c.fn in _KHOI_FN]
    if khoi_goi:                                   # ownership from the declared solids, not from names in the text
        so_day = {len(c.args.base) for c in khoi_goi}
        ben = {3 if c.fn in ("pyramid", "regular_pyramid") else 4 for c in khoi_goi}
    truoc_do: dict[int, list[int]] = {}            # sentence start → the previous noun's attributions
    for m in _DEM_RX.finditer(de):
        if m.start() in da_xet:
            continue
        cs = max((k.end() for k in _CAU.finditer(de, 0, m.start())), default=0)
        truoc = de[cs:m.start()]
        doan = de[max(0, m.start() - 30):m.end() + 12]
        can, sau = [], m.end()                     # every vertex count this noun is attributed to
        if x := _DEM_SAU_NHAN.match(de, m.end()):
            can += [dem(x["p"]), *([3] if x["tri"] else [])]
            sau = x.end()
        elif x := _NHAN_LA.search(truoc):
            can += [dem(x["p"]), *([3] if x["tri"] else [])]
        if (_DAY_TRUOC.search(truoc) or _KHOI_TRUOC.search(truoc) or _MAT_TREN_DUOI.search(truoc)
                or _DAY_SAU.match(de, sau)):
            if (n := mot(so_day)) is not None:
                can.append(n)
            elif can and not set(can) <= so_day and so_day:
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{doan!r}: đáy có nhãn không khớp đáy của khối nào được nêu")
            elif not can:
                continue                           # base of an unresolved solid: deferred (see `mot`)
        elif not can and (x := _MAT_TRUOC.search(truoc)):
            # a lateral face ("mặt bên"), or a face of a solid whose faces are all alike (tetrahedron, box, cube); any
            # other "mặt … là" ("mặt nằm dưới", "mặt chứa A, B, C") is a face this gate cannot identify: refused
            if not x["ben"] and not mat:
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{doan!r}: không xác định được mặt nào của khối")
            if (n := mot(ben if x["ben"] else mat)) is None:
                continue
            can.append(n)
        elif not can and _NOI_TRUOC.search(truoc) and truoc_do.get(cs):
            can += truoc_do[cs]
        elif not can and _THIET_DIEN.search(truoc):
            truoc_do[cs] = []
            continue
        if not can:
            if _MO_TA_DINH.match(de, sau) or _HOI_TRUOC.search(truoc):
                truoc_do[cs] = []
                continue
            het = next((k.start() for k in _CAU.finditer(de, m.end())), len(de))
            if co_khoi or _VE_KHOI.search(truoc + de[m.start():het]):
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{doan!r}: tên hình không gắn được với đa giác nào của khối")
            continue
        if any(_so_cua_dem(m.group()) != n for n in can):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{doan!r}: hình nêu số đỉnh khác đa giác nó gọi tên")
        truoc_do[cs] = can


def _ten_khoi_goi(k: LoiGoi) -> str:
    return (
        f"{k.args.apex}.{''.join(k.args.base)}"
        if k.fn in ("pyramid", "regular_pyramid")
        else f"{''.join(k.args.base)}.{''.join(k.args.top)}"
    )


def _cua_khop(m: re.Match, khoi: LoiGoi | None, calls: tuple[LoiGoi, ...] | None = None) -> bool:
    """A role clause's "của <solid>" / "<solid>" names the bound solid itself: its exact class, and its label when written."""
    if not m["qn"]:
        return True
    if khoi is None or (m["ql"] and not _khop_ky_hieu_khoi(khoi, m["ql"])):
        return False
    return _loai_cum_dung(m["qn"], _ten_khoi_goi(khoi), calls=calls)


def _canh_cua(v) -> set[frozenset]:
    v = list(v)
    return {frozenset((x, v[(i + 1) % len(v)])) for i, x in enumerate(v)}


def _lien_ket_khop(c: LoiGoi, bd: tuple, calls: tuple[LoiGoi, ...]) -> bool:
    """A parsed binding fills THIS call's value slot: the height of its own solid; a side of its own regular polygon; an
    unnamed segment by its structural role only where every segment of that role is equal."""
    deu = {frozenset(d.args.vertices) for d in calls if d.fn == "regular_polygon"}
    if bd[0] == "vai":
        _t, vai, k, moi = bd
        if k is None:
            return False
        base = frozenset(k.args.base)
        if c.fn == "height":
            return vai in ("chiều cao", "đường cao") and _nhan_khoi(k) == set(re.findall(r"[A-Z][0-9]*'?", c.args.solid))
        if c.fn == "regular_polygon":
            return frozenset(c.args.vertices) == base and (vai == "cạnh đáy" or vai == "cạnh" and moi)
        if c.fn == "segment_length":
            s = frozenset(c.args.segment)
            ben = ({frozenset((k.args.apex, x)) for x in k.args.base} if k.fn != "prism"
                   else {frozenset(p) for p in zip(k.args.base, k.args.top)})
            return (vai == "cạnh bên" and s in ben and k.fn in ("regular_pyramid", "prism")
                    or vai == "cạnh đáy" and s in _canh_cua(k.args.base) and base in deu
                    or vai == "cạnh" and moi and s in ben | _canh_cua(k.args.base))
        return False
    if bd[0] == "side":
        poly = bd[1]
        if c.fn == "regular_polygon":
            return frozenset(c.args.vertices) == poly
        if c.fn == "segment_length":
            return poly in deu and any(frozenset(c.args.segment) in _canh_cua(d.args.vertices) for d in calls
                                       if d.fn == "regular_polygon" and frozenset(d.args.vertices) == poly)
    return False


def _so_theo_vai_tro(c: LoiGoi, calls: tuple[LoiGoi, ...], de: str) -> list[tuple[Fraction, bool]]:
    """Values the quotes give THIS call's role slot (height, regular-polygon side, unnamed segment) through a parsed
    sentence (`_lien_ket_cau`) — the only source of such a value."""
    own = []
    for q in c.quotes:
        if (vt := _vi_tri(de, q)) is None:
            return []
        lk = _lien_ket_cau(de, *vt, calls)
        own += [_doc(m) for m in _SO.finditer(de, *vt) if _doc(m) is not None and m.start() in lk
                and _lien_ket_khop(c, lk[m.start()], calls)]
    return own


def _so_neo(quotes: tuple[str, ...], seg: list[str] | None) -> list[tuple[Fraction, bool]]:
    """Số căn theo nhãn đoạn: số ĐẦU TIÊN đứng sau nhãn `seg` (nguyên một từ, `_la_doan`) trong mỗi quote có nhãn ấy."""
    if not seg:
        return []
    ra = []
    for q in quotes:
        qn = chuan_hoa(q)
        so = so_trong(qn)
        for dau, cuoi, phan in _tu_nhan(qn):
            if _la_doan(phan, seg):
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
#: Plane through a point ⊥ a line d (run `geometry-capability-expansion`): two translates of the point along Z − F(Z), F(Z) the
#: foot of a solid vertex Z on d — existing primitives only (`orthogonal_projection_line`, `translate_point`).
MAT_VUONG_DUONG = "section(plane through point perpendicular to a line)"
#: Run `typedfactnext-planner-bridge`: the vertices of a derived plane's section on the edges the source says it cuts
#: ("(α) … cắt SB, SC (lần lượt tại N, P)") — one `intersect_line_plane` per stated edge (the plane's own through-point
#: reused on its edge), and optionally the pyramid "khối chóp đỉnh S cắt bởi (α)" over the closed lateral-edge cycle.
DINH_CAT_CANH = "section vertices on the stated cut edges of a derived plane"
#: C17: a plane the source defines by RELATIONS ("(P) đi qua M, N và vuông góc với (ABCD)", "(P) chứa AB và song song với
#: SC"). The entry names the functions a witness may use, not a call sequence: the planner chooses, per constraint, a
#: producer by contract (a `Normal` need: a stated line ⊥ Q, or the foot of a chosen point on Q) and the engine proves the
#: plane exists and is unique from ALL the stated constraints.
MAT_RANG_BUOC = "section(plane defined by stated constraints)"
#: C18 (review MAJOR-1/2): a point named by a property is built from its DECLARED definition (`POINT_DEFINITIONS`: the
#: loci, the meet) — a registered decomposition by the C17 standard, whatever contract realizes each locus. The entry
#: names the functions such a plan may use, not a call sequence.
DINH_NGHIA_DIEM = "point(defined by a property: the common point of its loci)"
AUXILIARY_RULES = {DINH_NGHIA_DIEM: ("midpoint", "orthogonal_projection_line", "translate_point", "intersect_line_line"),"distance(point,line)": ("orthogonal_projection_line", "ask_length"),
                   MAT_SONG_SONG: ("translate_point", "section"), MAT_HAI_DUONG: ("translate_point", "section"),
                   MAT_VUONG_DUONG: ("orthogonal_projection_line", "translate_point", "section"),
                   DINH_CAT_CANH: ("intersect_line_plane", "pyramid"),
                   MAT_RANG_BUOC: ("orthogonal_projection", "translate_point", "section")}
#: "khoảng cách từ S đến (đường thẳng) BD": điểm và đường gắn vai trong CÙNG một cụm; cách nói khác ⇒ từ chối, không đoán.
_KHOANG_CACH_DIEM_DUONG = re.compile(
    _KC + r"\s+từ\s+(?:điểm\s+)?([A-Z][0-9]*'?)\s+(?:đến|tới)\s+(?:(?:đường thẳng|đt)\s+)?([A-Z][0-9]*'?)([A-Z][0-9]*'?)(?![\w'])",
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
              ten_mat_phu: dict | None = None, don_vi_de: set[str] = frozenset(),
              buoc: list[tuple[int, int]] | None = None) -> set[str]:
    """Điểm phụ do planner khai: đúng luật, nhãn không trùng đề, hai lời gọi đúng hình dạng luật, câu hỏi nguồn có thật,
    không điều kiện/chứng minh/phủ định, và gắn đúng điểm + đường. Trả id các lời gọi đã kiểm (bỏ qua ở vòng thường).
    Nhãn phụ ở bất kỳ lời gọi nào KHÁC vẫn rơi vào `UNKNOWN_LABEL` của vòng thường."""
    theo_id = {c.id: c for c in calls}
    plane_pts: dict[int, tuple[PlanningContract, dict]] = {}
    da: set[str] = _kiem_result_binding(phu, calls, de, nhan, don_vi_de, buoc, plane_pts)
    chiem = nhan | nhan_phu_da_dung(de)
    nhan_da_khai: set = set()
    cat_doc: dict = {}                                    # plane goal → its declared cut clause was read in the source
    cat_canh: list[dict] = []                             # `DINH_CAT_CANH`: checked after every plane they stand on
    khoi_dan_xuat = frozenset(d["derived"].get("call") for d in phu if d.get("rule") == DINH_CAT_CANH
                              and isinstance(d.get("derived"), dict))
    for d in phu:
        if d.get('effect_binding') or d.get('rule') in ('result-line-reference','result-line-alias'):
            continue  # same source authority validated actual producer/consumer/goal above
        x, luat = d.get("label"), d.get("rule")
        if luat not in AUXILIARY_RULES:
            raise TuChoi("AUXILIARY_RULE_MISMATCH", f"điểm phụ {x}: luật {luat!r} không có trong bảng phân rã")
        if luat in (MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG):
            da |= _kiem_mat_song_song(d, theo_id, de, nhan, chiem, nhan_da_khai, calls, ten_mat_phu, don_vi_de, buoc,
                                      cat_doc, khoi_dan_xuat, plane_pts.get(id(d)))
            continue
        if luat == MAT_RANG_BUOC:
            da |= _kiem_mat_rang_buoc(d, theo_id, de, nhan, chiem, nhan_da_khai, calls, ten_mat_phu, buoc)
            continue
        if luat == DINH_CAT_CANH:
            cat_canh.append(d)
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
                    if hoi_that[-1] and buoc is not None:     # the span this certificate answers (M1 request coverage)
                        buoc.append((m.start(), m.end()))
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
    mats = [d for d in phu if d.get("rule") in (MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG)]
    for d in cat_canh:
        da |= _kiem_dinh_cat(d, mats, theo_id, de, nhan, chiem, nhan_da_khai, calls, ten_mat_phu, cat_doc, buoc)
    if cat_canh:
        # Every cut clause the SOURCE writes, in any sentence, must be exactly a declared one: a second clause naming other
        # edges or other names ("Dựng thiết diện … bởi (α) cắt BC, CA lần lượt tại N, P") contradicts the bound cut and is
        # never read as covered (review round 1, BLOCKER 1).
        mau = [r for d in mats if (r := _cum_cat_canh(d.get("cut"))) is not None]
        if lac := [m[0] for m in _CAT_CANH_CHUNG.finditer(de) if not any(r.fullmatch(de, m.start(), m.end()) for r in mau)]:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"đề có mệnh đề cắt khác mệnh đề đã gắn với mặt cắt: {lac}",
                         tuple(c for d in cat_canh for c in d.get("constructs") or ()))
    return da


def _mat_nhan_hop_le(p: list[str] | tuple[str, ...]) -> bool:
    """A plane operand written by its labels: at least three, pairwise distinct (SG-6: a four-vertex face such as (ABCD)
    is a plane; whether its vertices are coplanar is checked on the built figure, `NON_COPLANAR_POINTS`)."""
    return len(p) >= 3 and len(set(p)) == len(p)


def _khop_mo_ta_nguon(dc: PlanningContract, denv: dict[str, Any], m: re.Match, khoi: dict[str, frozenset]) -> bool:
    """Role-exact match of a source regex match `m` against a descriptor contract's bound `denv` slots."""
    gi = m.re.groupindex
    if "ops" in gi:
        ops = [denv.get(t.operands[0]) for t in dc.inputs]
        return sorted(_nhan_cum(m["ops"])) == sorted(ops)
    if "op_p" in gi and m["op_p"] != denv.get("P"):
        return False
    if "op_l" in gi:
        ln = denv.get("L")
        if not (isinstance(ln, (list, tuple)) and len(ln) == 2 and ln[0] == "named"):
            return False
        if sorted(_nhan_cum(m["op_l"])) != sorted(ln[1]):
            return False
    if "op_q" in gi:
        pl = denv.get("Q")
        if not isinstance(pl, (list, tuple)) or not _cung_mat(frozenset(_nhan_cum(m["op_q"])), list(pl)):
            return False
    if "op_l1" in gi and "op_l2" in gi:
        l1, l2 = denv.get("L1"), denv.get("L2")
        if not (isinstance(l1, (list, tuple)) and isinstance(l2, (list, tuple)) and l1[0] == "named" and l2[0] == "named"):
            return False
        said = {frozenset(_nhan_cum(m["op_l1"])), frozenset(_nhan_cum(m["op_l2"]))}
        want = {frozenset(l1[1]), frozenset(l2[1])}
        if said != want:
            return False
    return True


def _kiem_chung_chi_mo_ta(dc: PlanningContract, denv: dict[str, Any], op: dict[str, Any], nhan: set[str], err_ids: tuple[str, ...]) -> None:
    """Verify descriptor `denv` slots against `op['points']` and source label set `nhan`."""
    parsed = parse_descriptor_inputs(dc, op.get("points") or ())
    if parsed is None:
        raise TuChoi("AUXILIARY_RULE_MISMATCH", "toán hạng mô tả không khớp chứng chỉ", err_ids)
    expected_slots, _extra = parsed
    got_slots = tuple(
        tuple(tuple(x) if isinstance(x, list) else x for x in v) if isinstance(v, (list, tuple)) else v
        for v in (denv.get(t.operands[0]) for t in dc.inputs)
    )
    if got_slots != expected_slots:
        raise TuChoi("AUXILIARY_RULE_MISMATCH", "toán hạng mô tả không khớp chứng chỉ", err_ids)
    if set(op.get("points") or ()) - nhan:
        raise TuChoi("UNKNOWN_LABEL", "toán hạng của điểm được mô tả không có trong nguồn", err_ids)


def _dinh_nghia_trong_chuoi(d: dict[str, Any], got: list, p: Any, err_ids: tuple[str, ...]) -> tuple[PlanningContract, dict]:
    """C18: the measured point is a DEFINED point (`POINT_DEFINITIONS`): it must be the output of the chain's meet of two
    lines, each line the locus of THIS definition — through the locus point (a slot, or the chain's midpoint of the two
    slots it names) and a point a `PerpLine` contract of the chain built ⊥ the locus side. Re-derived from the bound slots,
    never trusted; the engine then checks the definition itself on the figure."""
    defn = POINT_DEFINITIONS[(d.get('operand') or {}).get('descriptor')]
    dd = d.get('definition') or {}
    denv = dd.get('env') or {}
    slots = [t.operands[0] for t in defn.contract.inputs]
    meet = next((g for g in got if g[2].id == dd.get('call')), None)
    if (dd.get('descriptor') != defn.contract.descriptor or set(denv) != {*slots, 'X'} or denv.get('X') != p
            or meet is None or meet[0].effect.kind != 'Point' or [t.kind for t in meet[0].inputs] != ['Line', 'Line']
            or meet[1].get(meet[0].effect.operands[0]) != p):
        raise TuChoi('AUXILIARY_RULE_MISMATCH', 'điểm được định nghĩa không là giao điểm của chuỗi', err_ids)
    mids = {tuple(sorted(e[t.operands[0]] for t in c.inputs)): e[c.effect.operands[0]] for c, e, _c, _f in got
            if c.descriptor == 'midpoint'}
    perp = {(e.get('P'), tuple(sorted(e['L'][1]))): e.get('X') for c, e, _c, _f in got
            if c.effect.kind == 'PerpLine' and isinstance(e.get('L'), (list, tuple)) and len(e['L']) == 2}

    def locus_line(lc: Locus) -> frozenset | None:
        qua = (denv[lc.through] if isinstance(lc.through, str)
               else mids.get(tuple(sorted(denv[s] for s in lc.through[1:]))))
        x = perp.get((qua, tuple(sorted(denv[s] for s in lc.perp))))
        return frozenset((qua, x)) if qua and x else None
    loci = {locus_line(lc) for lc in defn.loci} - {None}
    lines = [frozenset(meet[1].get(t.operands[0])[1]) for t in meet[0].inputs]
    if len(set(lines)) != 2 or not set(lines) <= loci:
        raise TuChoi('AUXILIARY_RULE_MISMATCH', 'giao điểm không phải của hai quỹ tích của định nghĩa', err_ids)
    return defn.contract, denv


def _kiem_result_binding(phu, calls, de, nhan, don_vi_de: set[str] = frozenset(), buoc=None, plane_pts=None):
    """Validate proposed effects against real calls and closed source spans. No client promise is truth. `buoc` collects
    the exact source spans of the descriptor ask phrases an `effect-chain` certificate bound (read by the coverage gate)."""
    by_id = {c.id:c for c in calls}
    accepted = set()
    registered = {d.get('consumer') for d in phu if d.get('rule') == 'result-line-reference'}
    registered |= {d.get('construct') for d in phu if d.get('effect_binding') and d.get('line_ref')}
    # Malformed parts are skipped here and refused by `chain` below (a coded AUXILIARY_RULE_MISMATCH, never an exception).
    chains = [d for d in phu if d.get('rule') == 'effect-chain' and isinstance(d.get('chain'), list)]
    plane_chains = [d for d in phu if d.get('rule') in (MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG) and isinstance(d.get('point_chain'), list)]
    registered |= {e.get('call') for d in chains for e in d['chain'] if isinstance(e, dict)}
    registered |= {e.get('call') for d in plane_chains for e in d['point_chain'] if isinstance(e, dict)}
    # A planner-written call may serve several goals; its quotes must come from the goals whose chains contain it.
    chain_quotes: dict[str, set[str]] = {}
    for d in chains:
        for e in d['chain']:
            if isinstance(e, dict):
                chain_quotes.setdefault(e.get('call'), set()).update(
                    chuan_hoa(q) for q in d.get('quotes') or () if isinstance(q, str))
    for d in plane_chains:
        for e in d['point_chain']:
            if isinstance(e, dict):
                chain_quotes.setdefault(e.get('call'), set()).update(
                    chuan_hoa(q) for q in d.get('quotes') or () if isinstance(q, str))
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
        if any(not _mat_nhan_hop_le(p) for p in (c.args.plane1,c.args.plane2)):
            raise TuChoi('FACT_INCOMPLETE','reference cần hai mặt, mỗi mặt ít nhất ba nhãn phân biệt',(ref,))
        if nhan_cua_loi_goi(c)-nhan:
            raise TuChoi('UNKNOWN_LABEL','mặt producer có nhãn ngoài nguồn',(ref,))
        producer_form = (rf'(?:(?i:tìm|dựng|xác định)\s+|(?i:gọi)\s+[A-Za-z][A-Za-z0-9]*\s+(?i:là)\s+)'
                         rf'(?i:giao tuyến của)\s*{_MAT_TOAN_HANG}\s*(?i:và)\s*{_MAT_TOAN_HANG}[.\s]*')
        # SG-6: the intersection named only as the TARGET of a distance question ("Tính khoảng cách từ A đến giao tuyến của
        # (SCD) và (ABCD).") — accepted only when that very sentence is the quote of an ask that reads it through this
        # `line_ref`; the ask's own `derived` binding below checks the point and both planes.
        # The point is a label or a point the Registry's own descriptor contracts describe ("trọng tâm của tam giác SAB").
        desc = [re.sub(r"\(\?P<[^>]+>", "(?:", p.phrase).replace('{P}', _P1)
                for s in REGISTRY.values() for p in planning_contracts(s) if p.descriptor and isinstance(p.phrase, str)]
        inline_form = (rf'(?:(?i:tính|tìm|xác định)\s+)?(?i:{_KC}\s+từ\s+)(?:(?i:điểm\s+)?{_P1}|'
                       + '|'.join(f'(?i:{d})' for d in desc) + rf')\s*(?i:đến|tới)\s*'
                       rf'(?i:giao tuyến của)\s*{_MAT_TOAN_HANG}\s*(?i:và)\s*{_MAT_TOAN_HANG}\s*[.?]?\s*')
        consumers = {chuan_hoa(x) for d in calls if getattr(d.args, 'line_ref', None) == ref for x in d.quotes}
        for q in c.quotes:
            m = re.search(r'(?i:giao tuyến)',q)
            vt = source_role(c,q,m.start() if m else 0)
            form = (inline_form if re.fullmatch(inline_form, q) and chuan_hoa(q) in consumers else producer_form)
            if not re.fullmatch(form,q):
                raise TuChoi('SOURCE_OBJECT_MISMATCH','producer chưa có định nghĩa/yêu cầu dựng nguyên tử',(ref,))
            if not re.fullmatch(form,de[slice(*_bien_cau(de,vt))].strip()):
                raise TuChoi('SOURCE_PREMISE_UNREAD','câu producer có phần ngoài quote chưa được đọc',(ref,))
            for match in _GIAO_TUYEN.finditer(q):
                planes = [_nhan_cum(next((match[i] for i in group if match[i]),''))
                          for group in ((1,2,3),(4,5,6))]
                if any(not _mat_nhan_hop_le(p) for p in planes):
                    raise TuChoi('SOURCE_OBJECT_MISMATCH','mặt nguồn cần ít nhất ba nhãn phân biệt',(ref,))
            if not mat_cat_dung_nguon(replace(c,quotes=(q,)),calls):
                raise TuChoi('SOURCE_OBJECT_MISMATCH','hai mặt producer không khớp nguồn',(ref,))
        accepted.add(ref)
        return c

    def matches_planes(m, c):
        labels = [_nhan_cum(m.group(i)) for i in ('a','b')]
        if any(not _mat_nhan_hop_le(p) for p in labels):
            return False
        planes = list(map(frozenset,labels))
        return set(planes)=={frozenset(c.args.plane1),frozenset(c.args.plane2)}

    plane_pattern = rf'(?P<a>{_MAT_TOAN_HANG})\s*(?i:và)\s*(?P<b>{_MAT_TOAN_HANG})'
    derived = re.compile(rf'(?i:{_KC}\s+từ\s+(?:điểm\s+)?)' + rf'(?P<p>{_P1})'
                         + rf'\s*(?i:đến|tới)\s*(?i:giao tuyến của)\s*{plane_pattern}')
    seen_fresh = {}
    khoi = _khoi_cua_loi_goi(calls)

    def term(v):                       # JSON slot value → hashable term (lists → tuples, nested)
        return tuple(term(x) for x in v) if isinstance(v, (list, tuple)) else v

    def values(t, env):
        return tuple(term(env.get(s)) for s in t.operands)

    def chain(d):
        """Generic `effect-chain` certificate: a derivation tree over Registry contracts, re-checked edge by edge against
        the real calls and the source. Nothing in it is trusted: every call is re-written from its contract template."""
        qs = tuple(chuan_hoa(q) for q in d.get('quotes') or ())
        ask = by_id.get(d.get('ask'))
        if not qs or not d.get('chain') or ask is None or d.get('goal') != ask.id:
            raise TuChoi('AUXILIARY_RULE_MISMATCH', 'chuỗi hiệu ứng thiếu mục tiêu hoặc nguồn')
        got = []
        for e in d['chain']:
            c, spec = by_id.get(e.get('call')), REGISTRY.get(e.get('fn') or '')
            contract, env = (planning_contract(spec, e.get('effect'), e.get('descriptor')) if spec else None), e.get('env') or {}
            if c is None or contract is None or c.fn != spec.name:
                raise TuChoi('AUXILIARY_RULE_MISMATCH', 'phần tử chuỗi không khớp lời gọi có contract')
            if contract.call:
                try:
                    ok = same_call(contract, render_call(contract, env), c.args.model_dump(exclude_none=True))
                except (KeyError, TypeError):
                    ok = False
                if not ok:
                    raise TuChoi('AUXILIARY_RULE_MISMATCH', 'lời gọi không phải lời gọi mà contract viết ra', (c.id,))
            elif contract.source_policy != 'declared_intersection' or values(contract.effect, env) != (('result', c.id),):
                raise TuChoi('AUXILIARY_RULE_MISMATCH', 'producer không có khuôn lời gọi', (c.id,))
            got.append((contract, env, c, bool(e.get('fresh'))))
        if [g[2].id for g in got if g[0].effect.kind.startswith('Answer')] != [ask.id] or got[-1][2].id != ask.id:
            raise TuChoi('AUXILIARY_RULE_MISMATCH', 'chuỗi phải kết bằng đúng một lời hỏi của mục tiêu', (ask.id,))
        labels = [env.get(contract.effect.operands[0]) for contract, env, _c, fresh in got if fresh and contract.fresh]
        if d.get('labels') != labels or len(set(labels)) != len(labels):
            raise TuChoi('AUXILIARY_RULE_MISMATCH', 'nhãn phụ không đúng các đầu ra tươi của chuỗi', (ask.id,))
        produced = {(g[0].effect.kind, values(g[0].effect, g[1])) for g in got}
        # C18: in a DEFINED point's chain only, a point an earlier call built (a foot, a translate) may span a later line
        built = ({env.get(contract.effect.operands[0]) for contract, env, _c, fresh in got if fresh and contract.fresh}
                 if (d.get('operand') or {}).get('descriptor') in POINT_DEFINITIONS else set())
        for contract, env, c, fresh in got:
            for t in contract.inputs:                    # every input: a source leaf, or produced inside this chain
                v = values(t, env)
                if t.kind == 'Point' and isinstance(v[0], str):
                    if v[0] not in nhan and ('Point', v) not in produced:
                        raise TuChoi('UNKNOWN_LABEL', 'toán hạng điểm ngoài nguồn và không do chuỗi dựng', (c.id,))
                elif t.kind == 'Plane':
                    if not v[0] or set(v[0]) - nhan:
                        raise TuChoi('UNKNOWN_LABEL', 'mặt phẳng có nhãn ngoài nguồn', (c.id,))
                elif t.kind == 'Line' and v[0] and v[0][0] == 'named':
                    if set(v[0][1]) - nhan - built:
                        raise TuChoi('UNKNOWN_LABEL', 'đường thẳng có nhãn ngoài nguồn', (c.id,))
                elif t.kind == 'Line' and v[0] and v[0][0] == 'result':
                    producer(v[0][1])
                elif (t.kind, v) not in produced:
                    raise TuChoi('AUXILIARY_RULE_MISMATCH', f'đầu vào {t.kind} không có producer trong chuỗi', (c.id,))
            if contract.fresh:
                x = env.get(contract.effect.operands[0])
                if fresh:
                    if not isinstance(x, str) or x in nhan | nhan_phu_da_dung(de, contract.fresh):
                        raise TuChoi('AUXILIARY_LABEL_COLLISION', 'điểm tươi trùng một nhãn của nguồn', (c.id,))
                    if seen_fresh.setdefault(x, c.id) != c.id:
                        raise TuChoi('AUXILIARY_RULE_MISMATCH', 'hai lời gọi cho một điểm tươi', (c.id,))
                    if not c.quotes or not set(c.quotes) <= chain_quotes.get(c.id, set()):
                        raise TuChoi('AUXILIARY_RULE_MISMATCH', 'điểm tươi mất nguồn mục tiêu', (c.id,))
                    accepted.add(c.id)
                elif x not in nhan:
                    raise TuChoi('UNKNOWN_LABEL', 'điểm tái dùng không có trong nguồn', (c.id,))
        if ask.quotes != qs:
            raise TuChoi('AUXILIARY_RULE_MISMATCH', 'lời hỏi không mang quote của mục tiêu', (ask.id,))
        # the goal: the asked quantity binds the DESCRIBED point and the declared target
        ans = got[-1]
        eff_vals = values(ans[0].effect, ans[1])
        p, rest = eff_vals[0], eff_vals[1:]
        op, target = d.get('operand') or {}, d.get('target') or {}
        if op.get('descriptor') in POINT_DEFINITIONS:
            dc, denv = _dinh_nghia_trong_chuoi(d, got, p, (ask.id,))
        else:
            desc = [g for g in got if g[0].descriptor and g[0].descriptor == op.get('descriptor')
                    and values(g[0].effect, g[1]) == (p,)]
            if not desc:
                raise TuChoi('AUXILIARY_RULE_MISMATCH', 'mục tiêu không đo từ điểm được mô tả', (ask.id,))
            dc, denv = desc[0][0], desc[0][1]
        if op.get('label') != p:
            raise TuChoi('AUXILIARY_RULE_MISMATCH', 'mục tiêu không đo từ điểm được mô tả', (ask.id,))
        _kiem_chung_chi_mo_ta(dc, denv, op, nhan, (ask.id,))
        goal_kind = ans[0].goal
        slots = goal_slots(ans[0])[1:]
        if goal_kind is not None:            # target re-read slot by slot from the contract's typed inputs (one reader)
            pts = list(target.get('points') or ([target['point']] if 'point' in target else []))
            want = tuple(pts.pop(0) if k == 'Point' else term(target['plane']) if k == 'Plane'
                         else ('named', tuple(sorted(target['line']))) for _s, k in slots)
            if pts:
                raise TuChoi('AUXILIARY_RULE_MISMATCH', 'đích của mục tiêu không khớp chứng chỉ', (ask.id,))
        else:
            want = ((('result', target['line_ref']),) if 'line_ref' in target
                    else (('named', tuple(sorted(target['line']))),) if 'line' in target else (term(target.get('plane')),))
        if rest != want:
            raise TuChoi('AUXILIARY_RULE_MISMATCH', 'đích của mục tiêu không khớp chứng chỉ', (ask.id,))
        if goal_kind is not None:
            keys = goal_target_keys(ans[0])
            pts = [v for (_s, k), v in zip(slots, rest) if k == 'Point']
            if (set(target) != keys or GOAL_VERIFIER_TARGET.get(ans[0].verifier) != keys
                    or not all(isinstance(v, str) for v in pts) or len(set(pts)) != len(pts) or set(pts) - nhan
                    or any(k == 'Plane' and (len(v) < 3 or set(v) - nhan) for (_s, k), v in zip(slots, rest))
                    or any(k == 'Line' and (v[0] != 'named' or len(set(v[1])) != 2 or set(v[1]) - nhan)
                           for (_s, k), v in zip(slots, rest))
                    or any(k not in ('Point', 'Plane', 'Line') for _s, k in slots)):
                raise TuChoi('AUXILIARY_RULE_MISMATCH', 'đích của mục tiêu không đúng kiểu hợp đồng, hoặc không có nguồn',
                             (ask.id,))
        elif len(rest) != 1 or ans[0].verifier != 'distance' or ans[0].effect.kind != 'AnswerDistance':
            raise TuChoi('AUXILIARY_RULE_MISMATCH', 'loại mục tiêu không hợp lệ trong chứng chỉ chuỗi', (ask.id,))
        x = rest[0]
        g = producer(x[1]) if goal_kind is None and x[0] == 'result' else None
        # a goal contract may declare several closed wordings (operand orders): each is one exact pattern (M3)
        patterns = (tuple(_mau_muc_tieu_mo_ta(p, dc.phrase or '') for p in _cac_cau(ans[0].phrase)) if goal_kind else
                    (_mau_khoang_cach_mo_ta(dc.phrase or ''),))

        def binds(m):
            if not _khop_mo_ta_nguon(dc, denv, m, khoi):
                return False
            if goal_kind is not None:        # wording groups by slot kind: t / t1,t2 points, m plane, l line
                pts = [v for (_s, k), v in zip(slots, rest) if k == 'Point']
                said = [m['t']] if len(pts) == 1 else [m['t1'], m['t2']] if len(pts) == 2 else []
                return (len(pts) <= 2 and sorted(said) == sorted(pts) and len(set(said)) == len(said)
                        and all(_cung_mat(_mat_cua(m, 'm', khoi), list(v)) if k == 'Plane'
                                else sorted(_nhan_cum(m['l'])) == sorted(v[1]) if k == 'Line' else True
                                for (_s, k), v in zip(slots, rest)))
            if x[0] == 'result':
                return bool(m['a'] and m['b']) and matches_planes(m, g)
            if x[0] == 'named':
                return bool(m['l']) and sorted(_nhan_cum(m['l'])) == list(x[1])
            return bool(m['mp'] or m['mb'] or m['md']) and _cung_mat(_mat_cua(m, 'm', khoi), list(x))

        for q in ask.quotes:
            span = _vi_tri(de, q)
            if span is None:
                raise TuChoi('QUOTE_NOT_IN_SOURCE', 'quote mục tiêu không có trong đề', (ask.id,))
            found = [m for pattern in patterns for m in pattern.finditer(de)
                     if span[0] <= m.start() and m.end() <= span[1] and binds(m)]
            if not found:
                raise TuChoi('SOURCE_OBJECT_MISMATCH', 'nguồn không hỏi khoảng cách từ đúng điểm được mô tả tới đúng đích',
                             (ask.id,))
            for m in found:
                source_role(ask, q, m.start() - span[0])
                if not _hoi_dung_cum(de, m.start(), m.end()) or _GAN_GIA_TRI.match(de[m.end():]):
                    raise TuChoi('NOT_ASKED_IN_SOURCE', 'nguồn không hỏi khoảng cách này', (ask.id,))
                if not _kiem_don_vi_hoi(ask.fn, de, m.start(), m.end(), don_vi_de, calls):
                    raise TuChoi('QUESTION_CONTEXT_UNSUPPORTED', 'đơn vị yêu cầu không khớp chính sách đơn vị', (ask.id,))
                # A length goal is read like every other ask: the shared grammar above (`_hoi_dung_cum`: "Tính …",
                # "… bằng bao nhiêu?") and request coverage (M1) for a dropped second ask — not one bare sentence form (M3).
                if goal_kind is None and x[0] == 'result':  # complete sentence, no silently dropped target or second ask
                    form = re.compile(r'(?:(?:tính|tìm)\s+)?(?:' + m.re.pattern + r')[.?\s]*', re.IGNORECASE)
                    if not form.fullmatch(q) or not form.fullmatch(de[slice(*_bien_cau(de, m.start()))].strip()):
                        raise TuChoi('SOURCE_PREMISE_UNREAD', 'câu mục tiêu có phần chưa được đọc', (ask.id,))
                if buoc is not None:
                    buoc.append((m.start(), m.end()))
        accepted.add(ask.id)

    def plane_point_chain(d):
        qs = tuple(chuan_hoa(q) for q in d.get('quotes') or ())
        p_chain = d.get('point_chain')
        op = d.get('point_operand') or {}
        err_ids = tuple(i for i in (*(d.get('constructs') or ()), *(d.get('targets') or ())) if i)
        if not qs or not isinstance(p_chain, list) or not p_chain or not op:
            raise TuChoi('AUXILIARY_RULE_MISMATCH', 'chuỗi điểm của mặt phụ thiếu thông tin', err_ids)
        got = []
        for e in p_chain:
            c, spec = by_id.get(e.get('call')), REGISTRY.get(e.get('fn') or '')
            contract, env = (planning_contract(spec, e.get('effect'), e.get('descriptor')) if spec else None), e.get('env') or {}
            if c is None or contract is None or c.fn != spec.name or not contract.call:
                raise TuChoi('AUXILIARY_RULE_MISMATCH', 'phần tử chuỗi điểm mặt phụ không khớp contract', err_ids)
            if not same_call(contract, render_call(contract, env), c.args.model_dump(exclude_none=True)):
                raise TuChoi('AUXILIARY_RULE_MISMATCH', 'lời gọi điểm mặt phụ không khớp contract', (c.id,))
            got.append((contract, env, c, bool(e.get('fresh'))))
        produced = {(g[0].effect.kind, values(g[0].effect, g[1])) for g in got}
        for contract, env, c, fresh in got:
            for t in contract.inputs:
                v = values(t, env)
                if t.kind == 'Point' and isinstance(v[0], str):
                    if v[0] not in nhan and ('Point', v) not in produced:
                        raise TuChoi('UNKNOWN_LABEL', 'toán hạng điểm mặt phụ ngoài nguồn', (c.id,))
                elif t.kind == 'Plane' and (not v[0] or set(v[0]) - nhan):
                    raise TuChoi('UNKNOWN_LABEL', 'mặt phẳng tham chiếu có nhãn ngoài nguồn', (c.id,))
                elif t.kind == 'Line' and v[0] and v[0][0] == 'named' and (set(v[0][1]) - nhan):
                    raise TuChoi('UNKNOWN_LABEL', 'đường thẳng tham chiếu có nhãn ngoài nguồn', (c.id,))
            if contract.fresh:
                x = env.get(contract.effect.operands[0])
                if fresh:
                    if not isinstance(x, str) or x in nhan | nhan_phu_da_dung(de, contract.fresh):
                        raise TuChoi('AUXILIARY_LABEL_COLLISION', 'điểm tươi mặt phụ trùng nhãn nguồn', (c.id,))
                    if seen_fresh.setdefault(x, c.id) != c.id:
                        raise TuChoi('AUXILIARY_RULE_MISMATCH', 'hai lời gọi cho một điểm tươi', (c.id,))
                    if not c.quotes or not set(c.quotes) <= chain_quotes.get(c.id, set()):
                        raise TuChoi('AUXILIARY_RULE_MISMATCH', 'điểm tươi mặt phụ mất nguồn mục tiêu', (c.id,))
                    accepted.add(c.id)
                elif x not in nhan:
                    raise TuChoi('UNKNOWN_LABEL', 'điểm tái dùng không có trong nguồn', (c.id,))
        dc, denv, _c_last, _fr_last = got[-1]
        p_out = values(dc.effect, denv)[0]
        if not dc.descriptor or dc.descriptor != op.get('descriptor') or op.get('label') != p_out or d.get('point') != p_out:
            raise TuChoi('AUXILIARY_RULE_MISMATCH', 'điểm đi qua của mặt phụ không khớp chứng chỉ mô tả', err_ids)
        _kiem_chung_chi_mo_ta(dc, denv, op, nhan, err_ids)
        if plane_pts is not None:
            plane_pts[id(d)] = (dc, denv)

    for d in phu:
        if d.get('rule') == 'effect-chain':
            try:
                chain(d)
            except (AttributeError, KeyError, TypeError, ValueError, IndexError):
                raise TuChoi('AUXILIARY_RULE_MISMATCH', 'chứng chỉ chuỗi hiệu ứng dị dạng') from None
            continue
        if d.get('rule') in (MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG) and d.get('point_chain') is not None:
            try:
                plane_point_chain(d)
            except (AttributeError, KeyError, TypeError, ValueError, IndexError):
                raise TuChoi('AUXILIARY_RULE_MISMATCH', 'chứng chỉ điểm mặt phụ dị dạng') from None
            continue
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
                if buoc is not None and (span := _vi_tri(de, q)) is not None:
                    buoc += [(x.start(), x.end()) for x in derived.finditer(de, *span)]
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
                    if buoc is not None:
                        buoc.append((m.start(), m.end()))
        accepted.add(ask.id)
    return accepted


# ── MỘT bộ phân tích mệnh đề cho tiền đề, câu hỏi thường và điểm phụ (review 2, run `hybrid-slice-review`) ────────────
#: Mở đầu mệnh đề ĐIỀU KIỆN. "Khi đó" là tiền đề (nối câu), không phải điều kiện.
#: "khi" + động từ dựng ("khi cắt bởi", "khi dựng", "khi quay") là lời dẫn phép dựng, không phải điều kiện.
_DIEU_KIEN = re.compile(r"(?<!\w)(?:nếu|giả sử|giả thiết rằng|trong trường hợp|với điều kiện|trừ khi"
                        r"|khi(?!\s+(?:đó|(?:bị\s+|đã\s+)?cắt|bỏ|loại\s+bỏ|lấy\s+đi|dựng|quay|chiếu))"
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
_CHAN_TAN_NGU = re.compile(r"(?<!\w)(?:theo(?!\s+[a-z](?![\w']))|tỉ số|tỷ số|tổng|hiệu|sao cho|ở đây|trong đó|gấp|lớn hơn|nhỏ hơn|bé hơn"
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
    # Given markers are read OUTSIDE the listed object phrases (`_bo_cum`, length-preserving): the "với" of
    # "đoạn nối M với S" is part of an object, not "với <dữ kiện>" (review N-1, run goal-directed-function-composition).
    moc_du_kien = [m.end() for m in _DUNG_GAN.finditer(_bo_cum(truoc))]
    dong_tu = list(_DONG_TU_HOI.finditer(truoc[moc_du_kien[-1] if moc_du_kien else 0:]))
    # Động từ hỏi chỉ chi phối đối tượng khi giữa chúng không có từ chặn tân ngữ (second re-verification, N2).
    qua_dong_tu = bool(dong_tu) and not _CHAN_TAN_NGU.search(_bo_cum(truoc)[(moc_du_kien[-1] if moc_du_kien else 0) + dong_tu[-1].end():])
    qua_hoi_sau = bool(_HOI_SAU.search(gan)) and not _CHAN_TAN_NGU.search(gan) and not _CHAN_TAN_NGU.search(_bo_cum(de[ma:p]))

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
    cum = sorted(((m.start(), m.end()) for mau in _mau_hoi_tat_ca() for m in mau.finditer(s)
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
    moc = [m.end() for m in _DUNG_GAN.finditer(_bo_cum(truoc))]      # same reading as `_duoc_hoi`
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
        moc += [dau + m.start() for m in re.finditer(r"[A-Z][0-9]*'?\s+(?:là|trùng\s+với)\s+(?:giao điểm|hình chiếu)|[Hh]ình chiếu", doan)]
    return moc


def _kiem_mat_chung(de: str, calls: tuple[LoiGoi, ...]) -> None:
    """A declared common face must be the SAME named face in both declared pyramids, not just a coplanar triangle."""
    solids = {c.args.apex + "." + "".join(c.args.base): c for c in calls if c.fn in ("pyramid", "regular_pyramid")}
    pattern = (rf"Hai\s+hình\s+chóp\s+(?P<a>{_NHAN}\.{_NHAN})\s+và\s+(?P<b>{_NHAN}\.{_NHAN})"
               rf"\s+có\s+mặt\s+chung\s+\(?(?P<f>{_NHAN})\)?\s*[.!?]?")
    for token in re.finditer(r"mặt\s+chung", de, re.IGNORECASE):
        start, end = _bien_cau(de, token.start())
        match = re.fullmatch(pattern, de[start:end].strip(), re.IGNORECASE)
        if not match or match["a"] == match["b"] or any(match[x] not in solids for x in ("a", "b")):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", "quan hệ mặt chung cần hai khối chóp và một mặt được khai tường minh")
        face = re.findall(r"[A-Z][0-9]*'?", match["f"])
        if len(face) != len(set(face)):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", "mặt chung lặp tên đỉnh")
        for name in (match["a"], match["b"]):
            c = solids[name]
            a = c.args
            faces = {frozenset(a.base), *(frozenset((a.apex, p, q)) for p, q in zip(a.base, a.base[1:] + a.base[:1]))}
            if frozenset(face) not in faces:
                raise TuChoi("INCONSISTENT_FACTS", "mặt chung không thuộc bảng mặt của cả hai khối", (c.id,))


def kiem_nguon(calls: tuple[LoiGoi, ...], text: str, auxiliary: tuple[dict, ...] = (),
               read_quotes: tuple[str, ...] = ()) -> dict[str, str | None]:
    """See `_kiem_nguon`; `_GOI_NGUON` holds THIS run's calls and is reset afterwards (run `hybrid-v2-planner-premerge-review`)."""
    token, tok_de = _GOI_NGUON.set(tuple(calls)), _DE_NGUON.set(text)
    try:
        return _kiem_nguon(calls, text, auxiliary, read_quotes)
    finally:
        _GOI_NGUON.reset(token)
        _DE_NGUON.reset(tok_de)


def _kiem_nguon(calls: tuple[LoiGoi, ...], text: str, auxiliary: tuple[dict, ...] = (),
                read_quotes: tuple[str, ...] = ()) -> dict[str, str | None]:
    """Cổng nguồn tất định — xem docstring module. Ném `TuChoi` ở lời gọi đầu tiên hỏng (theo thứ tự id).
    `auxiliary`: điểm phụ planner nhánh B khai (`AUXILIARY_RULES`); nhánh A không truyền ⇒ mọi nhãn phải có trong đề.
    Returns the name the source gave each bound derived plane (first construct id → "P", or None when unnamed)."""
    _KHOI_MO_TA.set({})
    de = chuan_hoa(text)
    nhan = nhan_cua_de(de)
    don_vi_de = _don_vi_met_cua_de(de)
    if len(don_vi_de) > 1:
        raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED", "đơn vị độ dài trong đề không đồng nhất; chưa hỗ trợ đổi đơn vị")
    _kiem_so_dinh_nguon(de, calls)
    _kiem_mat_chung(de, calls)
    ten_mat_phu: dict[str, str | None] = {}              # derived plane (first construct id) → name the source gave it
    buoc: list[tuple[int, int]] = []                     # descriptor ask phrases an `effect-chain` certificate bound
    phu = _kiem_phu(tuple(auxiliary), calls, de, nhan, ten_mat_phu, don_vi_de, buoc)
    # Derived pyramids validated above (run `hybrid-contract-v2`): a volume question may name one by description
    # ("khối chóp đỉnh S cắt bởi (α)"), and its fresh vertex labels — never in the source — are not "unknown" there.
    mo_ta: dict[tuple[str, str], str] = {}
    nhan_dan_xuat: set[str] = set()
    for d in auxiliary:
        if d.get("rule") != DINH_CAT_CANH or not isinstance(d.get("derived"), dict):
            continue
        mat = next((x for x in auxiliary if x.get("goal") == d.get("plane_goal") and x.get("constructs")
                    and x.get("rule") in (MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG)), None)
        if mat is not None and (ten := ten_mat_phu.get(mat["constructs"][0])):
            kd = d["derived"]
            mo_ta[(kd["apex"], ten)] = f"{kd['apex']}.{''.join(kd['base'])}"
            nhan_dan_xuat |= set(d.get("labels") or ())
    _KHOI_MO_TA.set(mo_ta)
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
        mien = (
            nhan_dan_xuat
            if c.fn in ("ask_volume_ratio", "ask_residual_volume")
            and any(re.search(_khoi_ro_cum("m"), de[dau:_c], re.I) for dau, _c in vts)
            else set()
        )
        if lac := sorted(nhan_cua_loi_goi(c) - nhan - mien):
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
                if "QUESTION" in roles and not (
                    c.fn == "curved_solid"
                    and (
                        (c.args.circumscribes is not None and _CAU_CONG_NGOAI_TIEP[2].fullmatch(chuan_hoa(q)) is not None)
                        or (c.args.inscribed_in is not None and _CAU_CONG_NOI_TIEP[2].fullmatch(chuan_hoa(q)) is not None)
                    )
                    and _duoc_hoi(de, dau, _c)
                ):
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
        # A bare "hình hộp" (parallelepiped) may be oblique: rightness needs a cue naming THIS prism (its label right after).
        if c.fn == "prism" and c.args.right and not _khoi_dung(c):
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
        if c.fn in ("intersect_line_line", "intersect_line_plane", "orthogonal_projection_line", "midpoint", "centroid",
                    "right_angle", "divide_segment"):
            if not construction_source_bound(c, de):
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: vai trò điểm và toán hạng dựng không khớp nguồn", (c.id,))
        if c.fn in ("curved_section", "curved_subsolid") and (ma := _phan_cong_dung_nguon(c, calls, de)):
            raise TuChoi(ma, f"{c.id}: {c.quote!r} không nêu đúng {'thiết diện' if c.fn == 'curved_section' else 'khối nón nhỏ'} "
                         "này của khối tròn xoay", (c.id,))
        if c.fn == "curved_solid" and (ma := _khoi_cong_dung_nguon(c, calls)):
            raise TuChoi(ma, f"{c.id}: {c.quote!r} không nêu đúng khối tròn xoay này (vai trò điểm, ký hiệu, hay bán kính / "
                         "chiều cao của chính mệnh đề vai trò)", (c.id,))
        if c.fn == "sphere_tangent_plane" and (ma := _tiep_xuc_mat_dung_nguon(c, calls)):
            raise TuChoi(ma, f"{c.id}: {c.quote!r} không nêu đúng quan hệ tiếp xúc mặt cầu - mặt phẳng", (c.id,))
        if c.fn in ("section", "ask_section_area", "intersection_line") and not mat_cat_dung_nguon(c, calls):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: mặt phẳng / khối của {c.fn} không phải cái mà {c.quote!r} gọi tên",
                         (c.id,))
        if c.fn == "orthogonal_projection" and (c.args.point != c.args.image or
                _co_tu(c.quotes, ("chân đường cao", "hạ đường cao", "kẻ đường cao"))):
            if not construction_source_bound(c, de):
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: vai trò ảnh và điểm chiếu không khớp nguồn", (c.id,))
            # A nondegenerate prism has disjoint parallel bases, even before its top coordinates can be placed.
            if any(k.fn == 'prism' and ((set(c.args.plane) == set(k.args.base) and c.args.image in k.args.top)
                    or (set(c.args.plane) == set(k.args.top) and c.args.image in k.args.base)) for k in calls):
                raise TuChoi('INCONSISTENT_FACTS', f'{c.id}: chân chiếu thuộc mặt đối diện của lăng trụ, không nằm trên mặt nhận chiếu', (c.id,))
        for f in c.spec.value_fields:
            if (v := getattr(c.args, f)) is None:
                continue
            gt = doc_so(v)
            seg = getattr(c.args, "segment", None)
            # A role slot — a height, a regular polygon's side, a segment the quote does not name (SG-1/SG-3, reviewed
            # twice) — takes its value ONLY from a sentence that parses in the closed clause grammar about its own solid.
            if c.fn in ("height", "regular_polygon") or seg and not _co_doan(c.quotes, seg):
                own = _so_theo_vai_tro(c, calls, de)
                if len(own) != 1 and len([x for q in c.quotes for x in so_trong(q)]) > 1:
                    raise TuChoi("AMBIGUOUS_VALUE_QUOTE", f"{c.id}: quote nhiều số mà không số nào gắn duy nhất với vai trò "
                                 "của ô này", (c.id,))
                if own != [gt]:
                    raise TuChoi("UNGROUNDED_VALUE", f"{c.id}: {c.quote!r} không gắn {v} với vai trò của ô này trong một câu "
                                 "đọc trọn", (c.id,))
                continue
            neo = _so_neo(c.quotes, seg)
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

    _kiem_du_kien_cau_hoi(calls, de, read_quotes, phu, don_vi_de, tuple(buoc))
    return ten_mat_phu


def _kiem_du_kien_cau_hoi(calls: tuple[LoiGoi, ...], de: str, read_quotes: tuple[str, ...] = (),
                          phu: set[str] = frozenset(), don_vi_de: set[str] | None = None,
                          buoc: tuple[tuple[int, int], ...] = ()) -> None:
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

    request_verb_raw = re.compile(_DONG_TU_HOI.pattern + r"|(?<!\w)dựng(?!\w)", re.I)

    def _la_mo_khoi_mo_phong(pos: int) -> bool:
        cs, ce = _bien_cau(de, pos)
        gd_s = _GIAN_DAN.match(de, cs, ce)
        a_s = gd_s.end() if gd_s else cs
        return bool(
            (mp_s := _MO_PHONG_MO_KHOI.match(de, a_s, ce))
            and mp_s.start() <= pos < mp_s.end()
            and (mk_s := _C_KHOI.match(de, mp_s.end(), ce))
            and re.match(r"\s*,?\s*(?:có|với|biết|th[ỏo]a\s+mãn)(?!\w)", de[mk_s.end():ce], re.IGNORECASE)
            and any(set(re.findall(r"[A-Z][0-9]*'?", mk_s["k"])) == _nhan_khoi(k) for k in calls if k.fn in _KHOI_FN)
        )

    def _req_verbs(a: int = 0, b: int | None = None) -> list[re.Match[str]]:
        end_b = len(de) if b is None else b
        return [m for m in request_verb_raw.finditer(de, a, end_b) if not _la_mo_khoi_mo_phong(m.start())]
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
        def rb_khop(assertion) -> bool:
            from ..semantic_program.source_entities import dinh_danh_thuc_the
            if assertion.kind in ("cuboid", "cube", "cube_edge"):
                want_fn = "rectangle" if assertion.kind == "cuboid" else "regular_polygon"
                return any(
                    c.fn == "prism" and c.args.right
                    and tuple(dinh_danh_thuc_the(n)[0] for n in c.args.base + c.args.top) == assertion.entities
                    and any(
                        d.fn == want_fn and d.args.vertices == c.args.base
                        and (assertion.kind == "cuboid" or assertion.value is None or _canh_khop(assertion, d.args.side, de))
                        for d in calls
                    )
                    for c in calls
                )
            return any(_rang_buoc_cuc_bo_khop(assertion, c, de) for c in calls)

        if de[a:b].strip(" ,;:.?!"):
            # Extraction may omit an original shape fact while keeping a local replacement. Preserve source authority.
            for original in rb:
                if (_vai_tro_tai(de, original.span[0]) in ("GOAL", "CONDITIONAL", "QUESTION")
                        or _phu_dinh(de, original.span[0], de[slice(*original.span)])):
                    continue
                if not rb_khop(original):
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
            if not rb_khop(r):
                raise TuChoi("QUESTION_LOCAL_GIVEN_UNVERIFIED",
                             f"dữ kiện {r.kind} trong câu hỏi chưa có giả thiết tương ứng đã xác thực")
            x, y = _span_rang_buoc(r, de)
            y = min(y, b)
            residue[x - a:y - a] = " " * (y - x)
            found = True
        for x, y in phep_dung_spans:
            if max(a, x) < min(b, y):
                ox, oy = max(a, x), min(b, y)
                residue[ox - a:oy - a] = " " * (oy - ox)
                found = True
        return "".join(residue), found

    phep_dung_spans: list[tuple[int, int]] = []
    questions = {_bien_cau(de, m.start()) for m in _req_verbs()} | {_bien_cau(de, a) for a, _b in buoc}
    for c in calls:
        if c.spec.kind == "ask":
            for q in c.quotes:
                if (vt := _vi_tri(de, q)) is not None:
                    questions |= {_bien_cau(de, p) for p, h in _cum_hoi(c, de, *vt, calls) if _hoi_dung_cum(de, p, h)}
                    questions |= {_bien_cau(de, m.start()) for pattern in _mau_hoi_tat_ca()
                                  for m in pattern.finditer(de, *vt) if _hoi_dung_cum(de, m.start(), m.end())}
    request_contexts = set(questions)
    construction_contexts = {_bien_cau(de, vt[0]) for c in calls
                             if (c.spec.kind == "construct" and c.fn not in ("pyramid", "regular_pyramid", "prism", "curved_solid", "curved_section", "curved_subsolid"))
                             or c.fn == "orthogonal_projection" for q in c.quotes
                             if (vt := _vi_tri(de, q)) is not None}
    solid_contexts = {_bien_cau(de, vt[0]) for c in calls
                      if c.fn in ("pyramid", "regular_pyramid", "prism", "curved_solid", "curved_section", "curved_subsolid") for q in c.quotes
                      if (vt := _vi_tri(de, q)) is not None}
    construction_contexts -= solid_contexts - request_contexts
    for c in calls:
        if c.fn in ("section", "intersection_line"):
            for q in c.quotes:
                if (vt := _vi_tri(de, q)) is not None:
                    cau = _bien_cau(de, vt[0])
                    s_cau = de[cau[0]:cau[1]]
                    if (re.search(r"thiết\s+diện|giao\s+tuyến", s_cau, re.IGNORECASE)
                            or _req_verbs(*cau) or _HOI_SAU.search(s_cau)):
                        request_contexts.add(cau)
                    else:
                        construction_contexts.add(cau)
    # Derived construction clauses already have their own binding gate. Context applies regardless of request wording.
    questions |= construction_contexts | request_contexts
    first_request = min((a for a, _b in request_contexts), default=min((a for a, _b in construction_contexts), default=len(de)))
    # A sentence that asks ("?", "bao nhiêu", "mấy") opens the request region even without a request verb.
    first_request = min([first_request, *(_bien_cau(de, m.start())[0] for m in _HOI_SAU.finditer(de))])
    questions |= {_bien_cau(de, p) for p in (0, *(m.end() for m in re.finditer(r"[.!?]\s+", de)))
                  if first_request <= p < len(de)}
    # Everything before the first request is premise text: it must be read too (run `source-grounding-completeness`).
    _kiem_vung_tien_de(calls, de, first_request, read_quotes, don_vi_de, phu)
    dung = {n for c in calls for n in nhan_cua_loi_goi(c)}
    khoi = _khoi_cua_loi_goi(calls)
    # M1 request coverage (run `hybrid-semantic-grounding-reliability`): an object phrase is ANSWERED only where a
    # validated call binds it — an `ask_*` call's own binder, or a span an auxiliary / effect-chain certificate bound.
    tra_loi = [s for c in calls if c.spec.kind == "ask" and c.id not in phu for s in _cum_hoi(c, de, 0, len(de), calls)]
    tra_loi += list(buoc)

    def khong_tra_loi(spans) -> list[str]:
        return [de[a:b] for a, b in spans if not any(x <= a and b <= y for x, y in tra_loi)]
    for start, end in sorted(questions):
        # SL-1: a request to show built objects asks nothing; before a question of its own sentence it is read whole
        gd_mp = _GIAN_DAN.match(de, start, end)
        if (het_mp := _doc_yeu_cau_mo_phong(de, gd_mp.end() if gd_mp else start, end, calls)) == end:
            continue
        phrases = [(m.start(), m.end()) for fn, rules in _CUM_HOI.items() for pattern, _bind in rules
                   for m in pattern.finditer(de, start, end)
                   if _hoi_dung_cum(de, m.start(), m.end())
                   and _kiem_don_vi_hoi(fn, de, m.start(), m.end(), don_vi_de, calls)]
        phrases += [(m.start(), m.end()) for pattern in (
            _KHOANG_CACH_DIEM_DUONG, _KHOANG_CACH_GIAO_TUYEN, _CUM_HOI_THIET_DIEN_PHU)
                    for m in pattern.finditer(de, start, end) if _hoi_dung_cum(de, m.start(), m.end())]
        # A descriptor ask phrase is read only where an `effect-chain` certificate bound exactly that phrase.
        phrases += [(a, b) for a, b in buoc if start <= a and b <= end and _hoi_dung_cum(de, a, b)]
        if _DIEU_KIEN.search(de, start, end):
            raise TuChoi("CONDITIONAL_CLAUSE", "ngữ cảnh câu hỏi có giả thiết điều kiện; chưa hỗ trợ thay phạm vi")
        # An object the sentence ASKS (listed after the same verb, after "sau đó", in its own sentence …) that no call
        # answers would be dropped silently while the rest is served: refuse, whatever the joining words.
        if bo := khong_tra_loi((a, b) for a, b in _cum_lon_nhat(de, start, end) if _hoi_dung_cum(de, a, b)):
            raise TuChoi("REQUEST_NOT_ANSWERED", f"đề còn yêu cầu {bo} mà không lời gọi nào trả lời — không trả lời một "
                         "phần rồi coi như xong")
        masked = list(de[start:end])
        # A validated construction definition is read as a whole: its own words ("sao cho" of a ratio point) are not
        # given markers opening an unread fragment (run `geometry-capability-expansion`).
        phep_dung_spans = _doc_phep_dung_cau_hoi(de, start, end, calls, dung, khoi, phu)
        if het_mp is not None:
            phep_dung_spans.append((start, het_mp))
        phep_dung_spans += [(a, b) for a, b in buoc if start <= a and b <= end and not _hoi_dung_cum(de, a, b)]
        # a curved section / derived cone quote is read WHOLE by its closed grammar (the gate refused it otherwise), so its
        # words — "tính từ đỉnh S" included, which is no request — are read (registry /25)
        phep_dung_spans += [vt for c in calls if c.fn in ("curved_section", "curved_subsolid") for q in c.quotes
                            if (vt := _vi_tri(de, q)) is not None and start <= vt[0] and vt[1] <= end]
        phep_dung_spans += [vt for c in calls if (
                                (c.fn == "curved_solid" and (c.args.circumscribes is not None or c.args.inscribed_in is not None))
                                or c.fn == "sphere_tangent_plane"
                            ) for q in c.quotes
                            if (vt := _vi_tri(de, q)) is not None and start <= vt[0] and vt[1] <= end
                            and not _req_verbs(start, end) and not _HOI_SAU.search(de, start, end)]
        for a, b in (*phrases, *phep_dung_spans):
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
        stops = sorted({a for a, _b in phrases} | {m.start() for m in _req_verbs(start, end)} | {end})
        fragments = [(start + m.start(), a, next(p for p in stops if p >= a)) for m, a in zip(dan, markers)]
        first = min(stops)
        a_hoi = start if het_mp is None else het_mp
        prefix = de[a_hoi:first]
        gd = _GIAN_DAN.match(de, start, first)
        a0 = gd.end() if gd else start
        is_note = bool(_GHI_CHU.fullmatch(de, a0, end)
                       and not re.search(r"(?<![a-zA-Z\^])\d+(?![\d\s]*chữ số)", de[a0:end], re.I))
        if (not is_note and not phrases and not _req_verbs(start, end)
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
        discourse =(_GIUA_HOP_LE.fullmatch(prefix) or re.fullmatch(r"\s*khi đó\s*,?\s*", prefix, re.I) or bool(muc_spans))
        if not is_note and start < first < end and not markers and not discourse and _tu_nhan(prefix):
            fragments.append((a_hoi, a_hoi, first))
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
        vung_da_che = (*phrases, *phep_dung_spans)
        for m in _req_verbs(start, end):
            if any(b > m.end() for _a, b in vung_da_che):
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
                # "… rồi suy ra thể tích …" asks that quantity too (M1): it must be answered, not read as a remark.
                if suy_ra_cum and (bo := khong_tra_loi(_cum_lon_nhat(de, mo_f.end(), end_goal))):
                    raise TuChoi("REQUEST_NOT_ANSWERED", f"đề còn yêu cầu suy ra {bo} mà không lời gọi nào trả lời")
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
        # PE-1 (review round 1, pre-existing): a sentence that REQUESTS something ("tìm / tính / xác định …") is read whole
        # even when no ask call exists — "Tìm giao điểm của SC và (ABD)." otherwise served a figure and dropped the request
        # A validated section / intersection line answers its own anaphoric request ("… theo một thiết diện. Xác định thiết
        # diện đó."): only that closed phrase is read, never what a broad model quote also covers (review round 2).
        # matched on the source (a request verb inside it, "vừa dựng", is already blanked in `du`) and only for the noun
        # whose own call exists: "thiết diện" ↔ section, "giao tuyến" ↔ intersection line (review round 3)
        fns = {c.fn for c in calls}
        for m in _HOI_CHI_DUNG.finditer(de, start, end):
            if {"thiết diện": "section", "giao tuyến": "intersection_line"}[re.sub(r"\s+", " ", m["n"].lower())] in fns:
                du = du[:m.start() - start] + " " * (m.end() - m.start()) + du[m.end() - start:]
        co_dung_hop_le = (
            (start, end) in construction_contexts
            or bool(phep_dung_spans)
            or any(
                c.fn in ("section", "intersection_line")
                and any((vt := _vi_tri(de, q)) is not None and start <= vt[0] and vt[1] <= end for q in c.quotes)
                for c in calls
            )
        )
        if ((phrases or _DONG_TU_HOI.search(de, start, end)
             or (bool(_req_verbs(start, end)) and not co_dung_hop_le)
             or (any(c.spec.kind == "ask" for c in calls) and start >= first_request))
                and not _DAN_CAU_HOI.fullmatch(du)):
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
            verbs = _req_verbs(_bien_menh_de(de, p)[0], p)
            # a re-request only when the object is the verb's DIRECT object ("tính lại SC"), not named inside another
            # object ("tính góc giữa SC và (ABCD)", "khoảng cách từ A đến SC") — same connector grammar as the ask gate
            if verbs and _GIUA_HOP_LE.fullmatch(re.sub(r"(?<!\w)lại(?!\w)", " ", _bo_cum(de[verbs[-1].end():p]),
                                                       flags=re.IGNORECASE)):
                raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                             f"{c.id}: đối tượng được yêu cầu lại sau lần hỏi đầu — phạm vi giả thiết đã đổi; chưa hỗ trợ", (c.id,))


#: Premise text a call need not quote: lead-ins and connectors between quoted claims (closed).
_NOI_TIEN_DE = re.compile(r"[\s,;:.()\-–]*(?:(?:cho|gọi|biết|rằng|có|và|với|trong đó|là|của|hãy|xét|thiết\s+lập|ta|đồng thời|lần lượt"
                          r"|theo thứ tự|tại|thì|đơn vị|cm|dm|mm|m|đvđd)(?!\w)[\s,;:.()\-–]*)*", re.IGNORECASE)
#: Exam scaffolding at the start of a premise segment ("Bài 3.", "Câu 2:", "a)", "1)", "Câu a:", "(1 điểm)").
_GIAN_DAN = re.compile(r"\s*(?:(?:bài tập|bài|câu|ví dụ)\s*(?:\d+|[a-d])\s*[.:)]|(?:\d+|[a-d])\s*\)"
                       r"|\(\s*\d+(?:[.,]\d+)?\s*điểm\s*\))\s*", re.IGNORECASE)
#: Sentence-initial indefinite article directly before a solid noun ("Một hộp chữ nhật …"); "một" anywhere else (a number,
#: "một nửa", "một cạnh") stays premise content.
_MAO_TU_KHOI = re.compile(r"\s*một\s+(?=(?:hình|khối|hộp|lăng\s+trụ|chóp|tứ\s+diện)(?!\w))", re.IGNORECASE)
#: Sentence-initial simulation verb directly before a solid noun (SL-1): a lead-in like "Cho", never premise content.
_MO_PHONG_MO_KHOI = re.compile(rf"\s*{_DONG_TU_MO_PHONG}\s+(?=(?:một\s+)?(?:(?:hình|khối)\s+)?(?:chóp|lăng\s+trụ|hộp|lập\s+phương"
                               r"|tứ\s+diện)(?!\w))", re.IGNORECASE)
#: Nouns that only NAME an object next to its label; ROLE nouns also state a role and are accepted only when that role
#: matches a validated call (`_vai_tro_doi_tuong_khop`) — "đường cao SB" is a claim, not a name.
_DANH_TU_TRUNG_TINH = r"mặt phẳng|đường thẳng|đoạn thẳng|đoạn|cạnh|mặt|điểm|độ dài|(?:các\s+)?kích\s+thước|hình chóp|khối chóp"
_DANH_TU_VAI_TRO = r"cạnh bên|cạnh đáy|mặt đáy|mặt bên|đáy|chiều cao|đường cao|đỉnh|tam giác"
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
        elif r == "tam giác":
            ok = len(nhan) == 3 and len(s) == 3
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
                       don_vi_de: set[str] | None = None, phu_ids: set[str] = frozenset()) -> None:
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
        if c.fn == "curved_solid":       # its dimensions are role-bound (`_kich_thuoc_cong_dung_nguon`), so they back numbers too
            gt = [(f, doc_so(v)) for f in _VAI_CONG if (v := getattr(c.args, f, None))]
        if c.fn == "curved_section":       # the closed section grammar reads its distance / ratio AS WRITTEN (OM/OS = 1/4)
            dmc = _doc_mat_cat(" ".join(chuan_hoa(q) for q in c.quotes))     # not `doc`: that name is the read-mask here
            gt = [(f"{v}{i}", doc_so(m["v"] if v in ("distance", "center_distance") else m["k"]))
                  for i, (v, m) in enumerate(dmc[1] if dmc else []) if v in ("distance", "axis_point", "axis_ratio",
                                                                                   "center_distance")]
        for q in c.quotes:
            if (vt := _vi_tri(de, q)) is None or vt[0] >= het:
                continue
            rang += [(vt[0], vt[1], v, (ci, f)) for f, v in gt]
            if c.fn == "divide_segment":
                # A ratio point carries no value field: it owns the ONE coefficient its solved equation read ("SM = 1/3 SA").
                rang += [(m.start("k"), m.end("k"), doc_so(m["k"]), (ci, "ratio"))
                         for m in _ty_so_khop(c, de, *vt) if m["k"]][:1]
            nhip = [vt]
            if c.id in phu_ids and c.fn in ("translate_point", "orthogonal_projection_line", "orthogonal_projection",
                                           "midpoint", "centroid", "intersect_line_line", "section", "ask_section_area",
                                           "intersect_line_plane"):
                nhip = []
                for m in _CUM_DUNG_MAT_PHU.finditer(de, *vt):
                    mend = m.end()
                    if m_day := re.match(rf"\s*\((?P<n>{_NHOM_NHAN})\)", de[mend:vt[1]]):
                        mend += m_day.end()
                    nhip.append((m.start(), mend))
                for pat in (_CUM_DUNG_THIET_DIEN_PHU, *_CAT_BOI, _GIAO_TUYEN, _CUM_TEN_THIET_DIEN):
                    for m in pat.finditer(de, *vt):
                        nhip.append((m.start(), m.end()))
                for m in _CAT_CANH_CHUNG.finditer(de, *vt):
                    chu = _CHU_NGU_CAT.search(de, vt[0], m.start())
                    nhip.append((chu.start() if chu else m.start(), m.end()))
            elif re.search(r"[.!?;]\s", de[vt[0]:vt[1]].rstrip()):
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
        if _doc_yeu_cau_mo_phong(de, a0, b, calls) == b:
            continue                                     # only asks to show built objects (SL-1)
        # only before the solid's own attributes ("… có / với / biết …"): a bare mention list is the reader's job above, so
        # "Cho mình xem hình chóp S.ABCD và đường thẳng SC" is not read as object names (review round 1)
        if ((mp := _MO_PHONG_MO_KHOI.match(de, a0, b)) and (mk := _C_KHOI.match(de, mp.end(), b))
                and re.match(r"\s*,?\s*(?:có|với|biết|th[ỏo]a\s+mãn)(?!\w)", de[mk.end():b], re.IGNORECASE)
                and any(set(re.findall(r"[A-Z][0-9]*'?", mk["k"])) == _nhan_khoi(k) for k in calls if k.fn in _KHOI_FN)):
            a0 = mp.end()                                # "Vẽ hình chóp S.ABCD có …" reads like "Cho hình chóp …"
        if mt := _MAO_TU_KHOI.match(de, a0, b):
            a0 = mt.end()
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
        for m_day in re.finditer(r"(?<!\w)(?:mặt\s+)?đáy(?=\s+là\b)", de[a0:b], re.IGNORECASE):
            if (verts := _chu_cua_day(de, a0 + m_day.start())) is not None and set(verts) <= dung and _vai_tro_doi_tuong_khop("đáy", verts, calls):
                ten |= set(range(a0 + m_day.start(), a0 + m_day.end()))
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


def _gia_tri_rang_buoc(r: Any, de: str) -> tuple[Fraction, bool] | None:
    """SG-2: the shape reader keeps a measure's coefficient, not its parameter (`cạnh 2a` → value 2, span ending before
    `a`). The parameter is read back from the SAME source token the reader consumed — the number starting inside its span
    with that coefficient — so `2` and `2a` never compare equal and neither is silently promoted to the other."""
    toks = _token_rang_buoc(r, de)
    return _doc(toks[-1]) if toks else None


#: "… hình vuông cạnh a": the side right after a regular-base span the reader left without a value (no coefficient).
_CANH_SAU_DAY = re.compile(r"\s*,?\s*(?:có\s+)?(?:độ\s+dài\s+)?cạnh\s*(?:(?:bằng|=|là)\s*)?", re.IGNORECASE)
_DAY_CO_CANH = ("base_square", "base_equilateral", "base_regular_hexagon")


def _token_rang_buoc(r: Any, de: str) -> list[re.Match]:
    """Source number tokens of a shape assertion's measure: those starting inside its span with the coefficient the reader
    kept, or — when the reader kept no value of a regular base — the side written right after the span ("cạnh a")."""
    from ..geometry.radical import display

    if r.value is None:
        m = _CANH_SAU_DAY.match(de, r.span[1]) if r.kind in _DAY_CO_CANH else None
        s = _SO.match(de, m.end()) if m else None
        return [s] if s and _doc(s) is not None else []
    want, (a, b) = doc_so(display(r.value))[0], r.span
    return [m for m in _SO.finditer(de, a) if m.start() < b and (x := _doc(m)) is not None and x[0] == want]


def _canh_khop(r: Any, side: str | None, de: str) -> bool:
    """The call's side equals the measure the source states for this assertion — (value², parameter) both — or the
    source states none. A measure the reader kept but whose token is not found never matches (fail closed)."""
    gv = _gia_tri_rang_buoc(r, de)
    if gv is None and r.value is None:
        return True
    return side is not None and gv is not None and gv == doc_so(side)


def _span_rang_buoc(r: Any, de: str) -> tuple[int, int]:
    """The assertion's source span through the end of its value token (`cạnh 2a` includes the `a` the reader stops before)."""
    toks = _token_rang_buoc(r, de)
    return r.span[0], max(r.span[1], toks[-1].end() if toks else 0)


def _rang_buoc_cuc_bo_khop(r: Any, c: LoiGoi, de: str) -> bool:
    """Reuse source-reader predicates; calls remain the only construction assumptions, engine checks them afterwards."""
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
    if r.kind == "right_triangle" and c.fn == "right_angle":     # (vertex, other two): the right angle at that vertex
        return ids([a.vertex]) == e[:1] and set(ids(a.rays)) == set(e[1:])
    if r.kind == "line_perp_line" and c.fn in ("perpendicular_lines", "right_angle"):
        pair = (a.line1, a.line2) if c.fn == "perpendicular_lines" else ([a.vertex, a.rays[0]], [a.vertex, a.rays[1]])
        return {frozenset(ids(x)) for x in pair} == {frozenset(e[:2]), frozenset(e[2:])}
    if r.kind in ("base_square", "base_equilateral", "base_regular_hexagon") and c.fn == "regular_polygon":
        n = {"base_square": 4, "base_equilateral": 3, "base_regular_hexagon": 6}[r.kind]
        return (len(a.vertices) == n and _cung_da_giac(list(ids(a.vertices)), list(e))
                and _canh_khop(r, a.side, de))
    if r.kind == "base_rectangle" and c.fn == "rectangle":
        return _cung_da_giac(list(ids(a.vertices)), list(e))
    if r.kind == "height" and c.fn == "curved_solid":   # registry /23: the role-bound height of THE solid of revolution,
        # stated inside its own (gate-validated) quote — never a height elsewhere with an equal value (review B3)
        return (not e and a.height is not None and r.value is not None and doc_so(a.height)[0] == Fraction(r.value) ** 2
                and any((vt := _vi_tri(de, q)) is not None and vt[0] <= r.span[0] and r.span[1] <= vt[1] for q in c.quotes))
    return False


#: Một mặt phẳng toán hạng như đề viết: nhóm ≥ 3 nhãn (có hoặc không ngoặc, "mặt phẳng"), hay "(mặt) đáy".
#: Nhãn phân biệt hoa thường dù cả mẫu không phân biệt: "qua" không phải một mặt phẳng.
_NHOM_NHAN = r"(?-i:[A-Z][0-9]*'?(?:[A-Z][0-9]*'?){2,})"
_MAT_TOAN_HANG = (r"(?:(?:hai|2|các)\s+mặt phẳng\s+)?(?:(?:mặt phẳng|mp|mặt bên|mặt đáy)\s*)?"
                  r"(?:\((" + _NHOM_NHAN + r")\)|(" + _NHOM_NHAN + r")|(?:mặt\s+)?(đáy))(?![\w'])")
#: Cụm vai trò gọi tên MẶT CẮT của một thiết diện. "song song với …" / "vuông góc với …" là phép dựng khác — không gắn.
#: Từ loại khối; "chóp" / "lăng trụ" / "tứ diện" cũng viết trần như `_MO_KHOI_DUNG` (run `hybrid-v2-planner-generalization`).
_TU_KHOI = r"(?:(?:hình|khối)\s+(?:chóp|lăng trụ|lập phương|hộp|tứ diện)|chóp|lăng trụ|tứ diện)"
#: Cụm danh từ khối đứng giữa "thiết diện của" và "với (P)": "hình chóp S.ABCD", "khối lăng trụ đứng ABC.A'B'C'"…
_KHOI_NGU = (rf"(?:{_TU_KHOI}(?:\s+(?:đứng|đều|tam giác|tứ giác|chữ nhật|lục giác))*\s+)?"
             r"(?:(?-i:[A-Z][0-9]*'?(?:[A-Z][0-9]*'?)*(?:\.[A-Z][0-9]*'?(?:[A-Z][0-9]*'?)*)?)\s+)?")
#: Đầu mệnh đề (đầu đề, sau . ; : ,) — "(P) cắt …" chỉ khi (P) là CHỦ NGỮ của mệnh đề (second re-verification, N1).
_DAU_MENH_DE = r"(?:^|(?<=[.;:,])|(?<=[.;:,]\s))\s*"
_CAT_BOI = [re.compile(p, re.IGNORECASE) for p in (
    r"(?:(?:khi\s+(?:bị\s+)?|bị\s+)?(?:cắt bởi|tạo bởi))\s+" + _MAT_TOAN_HANG,
    r"thiết diện\s+(?:của\s+|(?:được\s+)?tạo bởi\s+)?" + _KHOI_NGU + r"(?:với|và)\s+" + _MAT_TOAN_HANG,
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
_NOI_DU_KIEN_CUC_BO = re.compile(r"[\s,;:.?!]*(?:(?:biết|rằng|với|cho|trong đó|có|và|cạnh\s+bên|cạnh\s+đáy|cạnh|độ dài|đoạn thẳng)(?!\w)[\s,;:.?!]*)*",
                                 re.IGNORECASE)


def _mat_cum(n: str) -> str:
    return (rf"(?:(?:hai|2|các)\s+mặt phẳng\s+)?(?:(?:mặt phẳng|mp|mặt bên|mặt đáy)\s*)?"
            rf"(?:\((?P<{n}p>{_NHOM_NHAN})\)|(?<![\w'.])(?P<{n}b>{_NHOM_NHAN})|(?:mặt\s+)?(?P<{n}d>đáy))(?![\w'])")


def _doan_cum(n: str) -> str:
    return rf"(?:(?:các\s+)?(?:đường thẳng|đt|đoạn thẳng|đoạn|cạnh bên|cạnh đáy|cạnh|đường chéo)\s+)?(?<![\w'.])(?P<{n}>{_P1}{_P1})(?![\w'])"


def _khoi_cum(n: str) -> str:
    # ký hiệu khối: "S.ABCD", "ABCD.A'B'C'D'"; tứ diện viết liền bốn nhãn "ABCD" (`{n}t`)
    return (rf"(?:\s+(?P<{n}k>{_TU_KHOI})"
            rf"(?:\s+(?:đứng|đều|tam giác|tứ giác|chữ nhật|lục giác))*)?"
            rf"(?:\s+(?:(?P<{n}s>{_P1}+\.{_P1}+)|(?P<{n}t>{_P1}{{4}}))(?![\w']))?")


def _nhan_cum(s: str | None) -> list[str]:
    return re.findall(r"[A-Z][0-9]*'?", s or "")


def _mat_cua(m: re.Match, n: str, khoi: dict) -> frozenset | None:
    if nhom := m[n + "p"] or m[n + "b"]:
        return frozenset(_nhan_cum(nhom))
    return next(iter(khoi.values())) if m[n + "d"] and len(khoi) == 1 else None    # "đáy": đáy của khối duy nhất


_MAT_VIET = re.compile(rf"\((?P<p>{_NHOM_NHAN})\)|(?<!\w)(?:mặt phẳng|mp)\s+(?P<b>{_NHOM_NHAN})(?![\w'])", re.IGNORECASE)


def nhom_mat_nguon(text: str) -> list[list[str]]:
    """Giữ trọn nhóm nhãn mặt phẳng, dùng cùng văn phạm toán hạng với cổng buộc nguồn.

    Engine kiểm cả tính không suy biến: ba nhãn thẳng hàng không định danh một mặt phẳng.
    """
    de = chuan_hoa(text)
    groups = [m["p"] or m["b"] for m in _MAT_VIET.finditer(de)]
    for pattern in _mau_hoi_tat_ca():
        for m in pattern.finditer(de):
            groups += [s for k, s in m.groupdict().items() if k in ("mp", "mb", "ap", "ab", "bp", "bb", "a", "b") and s]
    for pattern in (*_CAT_BOI, _GIAO_TUYEN):
        groups += [s for m in pattern.finditer(de) for s in m.groups() if s]
    ra = []
    for group in groups:
        nhan = _nhan_cum(group)
        if len(set(nhan)) >= 3 and nhan not in ra:
            ra.append(nhan)
    return ra


def _cung_mat(tap: frozenset | None, diem: list[str]) -> bool:
    """Một nhóm định nghĩa phải chứa trọn nhóm kia; engine còn kiểm chúng không suy biến và đồng phẳng.

    Chỉ chung ba nhãn là thiếu: ba điểm ấy có thể thẳng hàng và nằm trên hai mặt khác nhau.
    """
    target = set(diem)
    return tap is not None and len(tap & target) >= 3 and (tap <= target or target <= tap)


def _chi_mot_khoi_3d(khoi: dict, calls: tuple | None = None) -> bool:
    cs = _GOI_NGUON.get() if calls is None else calls
    return len(khoi) == 1 and not any(c.fn == "curved_solid" for c in cs)


def _khoi_khop(m: re.Match, n: str, solid: str, khoi: dict) -> bool:
    """Khối của cụm: ký hiệu (nếu có) đúng là khối của lời gọi; không ký hiệu thì đề chỉ có MỘT khối; từ loại khối (chóp /
    lăng trụ …) phải đúng loại — "khối lập phương" không gọi một hình chóp."""
    if (sym := m[n + "s"]) and sym != solid:
        return False
    if (tu := m[n + "t"]) and set(_nhan_cum(tu)) != set(_nhan_cum(solid)):
        return False
    if not sym and not tu and (len(khoi) != 1 if m[n + "k"] else not _chi_mot_khoi_3d(khoi)):
        return False
    # từ loại xét cả khi có hay không có ký hiệu (run `hybrid-v2-source-kind-consistency`)
    if (kw := m[n + "k"]) and not _loai_cum_dung(
            m.string[m.start(n + "k"):m.end()], solid):
        return False
    return True


#: Calls of the `kiem_nguon` call in progress (set there, like `_KHOI_MO_TA`): lets a question's kind word be checked
#: against the solid the gate validated. Empty outside the gate — a specific class then cannot be verified and refuses.
_GOI_NGUON: contextvars.ContextVar[tuple] = contextvars.ContextVar("_GOI_NGUON", default=())
#: THIS run's source text, beside `_GOI_NGUON`, for binders that must re-ground another call (review 7 round 2, R2-M2).
_DE_NGUON: contextvars.ContextVar[str] = contextvars.ContextVar("_DE_NGUON", default="")
_TU_LOAI = re.compile(r"(?P<kn>chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)"
                      r"(?P<km>(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|ngũ\s+giác|lục\s+giác|chữ\s+nhật))*)",
                      re.IGNORECASE)
_SO_DINH_TU = {"tam giác": 3, "tứ giác": 4, "ngũ giác": 5, "lục giác": 6}


def _loai_cum_dung(cum: str, solid: str, calls: tuple | None = None) -> bool:
    """The kind words of a solid phrase written without its symbol are TRUE of `solid` (run
    `hybrid-v2-planner-premerge-review`). Generic class ("chóp", "lăng trụ") keeps the pyramid-/prism-like test; a
    specific class is accepted only when the gate's validated calls establish it, never from the letters alone:
    "tứ diện" = pyramid on a triangle; "tam/tứ/ngũ/lục giác" = base vertex count; "đứng" = right prism, "xiên" = not;
    "hộp" = prism on a 4-gon with a rectangle/square base or defined as a box by the source; "chữ nhật" = right prism on a
    rectangle/square; "lập phương" / "tứ diện đều" = the source's own validated definition of that solid says so (the gate
    reads no lengths); "đều" = regular base (+ regular pyramid / right prism), as in `_cau_tien_de_dong_hop_le`."""
    m = _TU_LOAI.search(cum)
    if not m:
        return True
    tu, km = re.sub(r"\s+", " ", m["kn"].lower()), re.sub(r"\s+", " ", m["km"].lower())
    if bool(re.search(r"chóp|tứ diện", tu)) != (len(_nhan_cum(solid.split(".")[0])) == 1):
        return False                                     # coarse class (unchanged from /15)
    if tu in ("chóp", "lăng trụ") and not km:
        return True                                      # generic class word: nothing more to verify
    calls = _GOI_NGUON.get() if calls is None else calls
    khop = [x for x in calls if x.fn in _KHOI_FN and _khop_ky_hieu_khoi(x, solid)]
    k = khop[0] if len(khop) == 1 else None
    if k is None or k.fn not in _LOAI_KHOI.get(tu, ()):
        return False                                     # specific class, solid not validated here: cannot verify
    day, lang_tru = list(k.args.base), k.fn == "prism"
    right = lang_tru and bool(k.args.right)
    hinh = {
        d.fn
        for d in calls
        if d.fn in ("rectangle", "regular_polygon")
        and (_cung_da_giac(list(d.args.vertices), day) or (lang_tru and _cung_da_giac(list(d.args.vertices), list(k.args.top))))
    }
    dn = [(re.sub(r"\s+", " ", x["kn"].lower()), _km_khoi(x)) for q in k.quotes
          for x in _C_KHOI.finditer(chuan_hoa(q)) if _khop_ky_hieu_khoi(k, x["k"])]
    if tu == "tứ diện" and len(day) != 3:
        return False
    if tu in ("hộp", "hộp chữ nhật", "lập phương") and len(day) != 4:
        return False
    if tu == "hộp" and not hinh and not any(d in ("hộp", "hộp chữ nhật", "lập phương") for d, _x in dn):
        return False
    if (tu == "hộp chữ nhật" or "chữ nhật" in km) and not (right and hinh):
        return False
    if tu == "lập phương" and not (right and bool(hinh) and any(d == "lập phương" for d, _x in dn)):
        return False
    if "đứng" in km and not right or "xiên" in km and not (lang_tru and not right):
        return False
    if (n := next((v for w, v in _SO_DINH_TU.items() if w in km), None)) and n != len(day):
        return False
    if "đều" in km:
        if tu == "tứ diện":
            return k.fn == "regular_pyramid" and any(d == "tứ diện" and "đều" in x for d, x in dn)
        if "regular_polygon" not in hinh or (tu == "chóp" and k.fn != "regular_pyramid") or (lang_tru and not right):
            return False
    return True


@dataclass(frozen=True)
class KhangDinhLoaiHinh:
    """Premise-level shape-kind assertion extracted from source text for exact geometric certification in `engine.kiem`."""

    kind: str
    vertices: tuple[str, ...]
    top: tuple[str, ...] = ()
    apex: str | None = None
    at: tuple[str, ...] = ()
    side: str | None = None
    quote: str = ""


_PRED_2D = (
    rf"(?:tam\s+giác\s+(?:{_DEU_CUOI_2D}|vuông\s+cân{_AT_TRI_2D}|vuông(?!\s+góc\b){_AT_TRI_2D}|cân{_AT_TRI_2D}|nhọn|tù{_AT_TRI_2D})"
    + "|" + "|".join(_DANH_TU_DA_GIAC_2D)
    + rf"|hình\s+thang(?:\s+(?:vuông{_AT_TRAP_2D}|cân))?"
    rf"|vuông\s+cân{_AT_TRI_2D}|vuông(?!\s+góc\b){_AT_TRAP_2D}|cân{_AT_TRI_2D}|nhọn|tù{_AT_TRI_2D}|{_DEU_CUOI_2D})(?![\w'])"
)
_HEAD_2D = (
    rf"(?:tam\s+giác\s+(?:{_DEU_CUOI_2D}|vuông\s+cân|vuông(?!\s+góc\b)|cân|nhọn|tù)"
    + "|" + "|".join(_DANH_TU_DA_GIAC_2D)
    + r"|hình\s+thang(?:\s+(?:vuông|cân))?)"
)
_KD_KHOI_TRUOC = re.compile(rf"(?<!\w){_C_KHOI.pattern}", re.IGNORECASE)
_KD_KHOI_SAU = re.compile(
    rf"(?<![\w'.])(?P<k>{_NHAN}(?:\.{_NHAN})?)(?![\w'.])\s+là\s+(?:một\s+)?(?:(?:hình|khối)\s+)?"
    rf"(?P<kn>chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)"
    rf"(?P<km>(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|ngũ\s+giác|lục\s+giác|chữ\s+nhật))*)(?!\w)",
    re.IGNORECASE,
)
_KD_2D_SAU = re.compile(
    rf"(?:(?<!\w)(?P<role>mặt\s+bên|mặt\s+đáy|mặt|đáy|tam\s+giác|tứ\s+giác|lục\s+giác|đa\s+giác|hình\s+thang)\s+)?"
    rf"(?<![A-Za-z0-9_'À-ỹ.])(?:[Δ∆△]\s*)?\(?(?P<poly>{_L1}{{3,}})\)?(?![\w'.])\s+"
    rf"(?:(?P<la>là\s+(?:một\s+)?)|(?=(?:đều|vuông\s+cân|vuông(?!\s+góc\b)|cân|nhọn|tù)(?!\w)))(?P<pred>{_PRED_2D})",
    re.IGNORECASE,
)
_KD_2D_TRUOC = re.compile(
    rf"(?<!\w)(?P<pred>{_HEAD_2D})\s+(?:[Δ∆△]\s*)?\(?(?P<poly>{_L1}{{3,}})\)?(?![\w'.])"
    rf"(?P<tail>(?:\s+(?:vuông\s+cân\s+|vuông(?!\s+góc\b)\s+|cân\s+|tù\s+)?(?:tại|ở)\s+{_L1}(?:\s*(?:và|,\s*(?!{_L1}\s+(?:là|thuộc|nằm|trên|có|=|⊥|//)))\s*{_L1})?)?)",
    re.IGNORECASE,
)
_KD_2D_DAY = re.compile(
    rf"(?<!\w)(?P<role>(?:mặt|tứ\s+giác|tam\s+giác|lục\s+giác|đa\s+giác)\s+)?đáy\s+"
    rf"(?:(?P<la>là\s+(?:một\s+)?)|(?=(?:đều|vuông\s+cân|vuông(?!\s+góc\b)|cân|nhọn|tù)(?!\w)))(?P<pred>{_PRED_2D})"
    rf"(?!\s+\(?{_L1}{{3,}}\)?(?![\w'.]))",
    re.IGNORECASE,
)
_KD_AT_RE = re.compile(
    rf"(?:tại|ở)\s+(?P<u1>{_L1})(?:\s*(?:và|,\s*(?!{_L1}\s+(?:là|thuộc|nằm|trên|có|=|⊥|//)))\s*(?P<u2>{_L1}))?(?![\w'])",
    re.IGNORECASE,
)


def _la_khang_dinh_tien_de(de: str, a: int, b: int) -> bool:
    if (
        _vai_tro_tai(de, a) in ("GOAL", "CONDITIONAL", "QUESTION")
        or _vai_tro_tai(de, max(a, b - 1)) in ("GOAL", "CONDITIONAL", "QUESTION")
        or _phu_dinh(de, a, de[a:b])
    ):
        return False
    cs, _ce = _bien_cau(de, a)
    truoc = de[cs:a]
    if _THIET_DIEN.search(truoc):
        return False
    reqs = [m.end() for rx in (_DONG_TU_HOI, _MO_MUC_TIEU) for m in rx.finditer(truoc)]
    if reqs and not re.search(r"(?<!\w)(?:biết|với|cho|trong\s+đó)(?!\w)", _bo_cum(truoc)[max(reqs):], re.IGNORECASE):
        return False
    return True


def _canh_ngay_sau_hinh(de: str, pos: int) -> tuple[str | None, int]:
    m_c = _CANH_SAU_DAY.match(de, pos)
    if m_c and (s_m := _SO.match(de, m_c.end())) and _doc(s_m) is not None and _DUOI_BANG.match(de[s_m.end():]):
        return s_m.group().strip(), s_m.end()
    return None, pos


def _phan_loai_hinh_2d(pred: str, n_verts: int, role: str = "") -> tuple[str, tuple[str, ...]] | None:
    at_m = _KD_AT_RE.search(pred)
    at = tuple(x for x in ((at_m["u1"], at_m["u2"]) if at_m else ()) if x)
    s = re.sub(r"\s+", " ", pred.lower()).strip()
    r = re.sub(r"\s+", " ", role.lower()).strip()
    if "hình thang vuông" in s or ("hình thang" in r and "vuông" in s):
        return ("right_trapezoid", at)
    if "hình thang cân" in s or ("hình thang" in r and "cân" in s and "vuông" not in s):
        return ("isosceles_trapezoid", ())
    if "hình thang" in s:
        return ("trapezoid", ())
    if "hình bình hành" in s:
        return ("parallelogram", ())
    if "hình chữ nhật" in s and "hộp" not in s:
        return ("rectangle", ())
    if "hình vuông" in s or ("tứ giác" in s and "đều" in s) or ("tứ giác" in r and "đều" in s):
        return ("square", ())
    if "hình thoi" in s:
        return ("rhombus", ())
    if "lục giác đều" in s or ("lục giác" in r and "đều" in s):
        return ("regular_hexagon", ())
    if "vuông cân" in s:
        return ("right_isosceles_triangle", at[:1])
    if "vuông" in s and "hình vuông" not in s and "thang" not in s:
        return ("right_triangle", at[:1])
    if "cân" in s and "thang" not in s:
        return ("isosceles_triangle", at[:1])
    if "nhọn" in s:
        return ("acute_triangle", ())
    if "tù" in s:
        return ("obtuse_triangle", at[:1])
    if "đều" in s:
        if "tam giác" in s or "tam giác" in r or n_verts == 3:
            return ("equilateral_triangle", ())
        if n_verts == 4:
            return ("square", ())
        if n_verts == 6:
            return ("regular_hexagon", ())
    return None


def _gop_day_khoi(bs: list[tuple[str, ...]]) -> list[tuple[str, ...]]:
    out: list[tuple[str, ...]] = []
    for b in bs:
        if not b:
            if () not in out:
                out.append(())
        elif not any(x and _cung_da_giac(list(x), list(b)) for x in out):
            out.append(b)
    return out


def _day_khoi_cho_menh_de(de: str, pos: int, khoi_calls: list[LoiGoi]) -> tuple[str, ...] | None:
    """Resolve the owner base polygon of an unlabelled `đáy là <shape>` clause at `pos`.

    Resolves from prose solid mentions directly (never short-circuiting on `len(khoi_calls) == 1`), returning `()`
    when ownership across distinct bases is genuinely ambiguous, or `None` when no solid exists in prose or `khoi_calls`.
    """
    mentions: list[tuple[int, int, tuple[str, ...]]] = []
    seen_spans: set[tuple[int, int]] = set()
    for d, cuoi, p in _tu_nhan(de):
        if len(p) == 2 and ((len(p[0]) == 1 and len(p[1]) >= 3) or (len(p[0]) == len(p[1]) >= 3)):
            if _la_khang_dinh_tien_de(de, d, cuoi):
                seen_spans.add((d, cuoi))
                mentions.append((d, cuoi, tuple(p[1] if len(p[0]) == 1 else p[0])))
    for rx in (_KD_KHOI_TRUOC, _KD_KHOI_SAU):
        for mk in rx.finditer(de):
            if "." in mk["k"] or re.sub(r"\s+", " ", mk["kn"].lower()) != "tứ diện":
                continue
            a_k, b_k = mk.start("k"), mk.end("k")
            if (a_k, b_k) in seen_spans or len(_nhan_cum(mk["k"])) != 4 or not _la_khang_dinh_tien_de(de, mk.start(), mk.end()):
                continue
            seen_spans.add((a_k, b_k))
            cand = _gop_day_khoi([tuple(k.args.base) for k in khoi_calls if _khop_ky_hieu_khoi(k, mk["k"])])
            mentions.append((a_k, b_k, cand[0] if len(cand) == 1 and cand[0] else ()))
    mentions.sort(key=lambda x: (x[0], -x[1]))

    cs, _ce = _bien_cau(de, pos)
    sent = [(a, b, base) for a, b, base in mentions if cs <= a and b <= pos]
    if sent:
        coord_rx = re.compile(
            r"\s*(?:,|và|hoặc|cùng)(?:\s+(?:(?:hình|khối)\s+)?(?:chóp|lăng\s+trụ|hộp(?:\s+chữ\s+nhật)?|lập\s+phương|tứ\s+diện)"
            r"(?:\s+(?:đứng|đều|xiên|tam\s+giác|tứ\s+giác|ngũ\s+giác|lục\s+giác|chữ\s+nhật))*)?\s*",
            re.IGNORECASE,
        )
        b_last = sent[-1][1]
        if re.fullmatch(
            r"(?:\s+(?:đứng|đều|xiên|chữ\s+nhật))*\s*(?:(?:có|với)\s+)?(?:chung\s+)?",
            de[b_last:pos],
            re.IGNORECASE,
        ):
            chain = [sent[-1][2]]
            i = len(sent) - 1
            while i > 0 and coord_rx.fullmatch(de[sent[i - 1][1]:sent[i][0]]):
                chain.append(sent[i - 1][2])
                i -= 1
            cb = _gop_day_khoi(chain)
            return cb[0] if len(cb) == 1 and cb[0] else ()
        sb = _gop_day_khoi([base for _a, _b, base in sent])
        return sb[0] if len(sb) == 1 and sb[0] else ()

    prior = _gop_day_khoi([base for _a, b, base in mentions if b <= cs])
    if prior:
        return prior[0] if len(prior) == 1 and prior[0] else ()

    all_b = _gop_day_khoi([base for _a, _b, base in mentions] + [tuple(k.args.base) for k in khoi_calls])
    if not all_b:
        return None
    return all_b[0] if len(all_b) == 1 and all_b[0] else ()


def doc_khang_dinh_loai_hinh(text: str, calls: tuple[LoiGoi, ...] = ()) -> tuple[KhangDinhLoaiHinh, ...]:
    """Extract premise-level solid and 2D polygon shape-kind assertions for deterministic certification."""
    de = chuan_hoa(text)
    out: list[KhangDinhLoaiHinh] = []
    seen: set[tuple] = set()

    def push(item: KhangDinhLoaiHinh) -> None:
        key = (item.kind, item.vertices, item.top, item.apex, item.at, item.side)
        if key not in seen:
            seen.add(key)
            out.append(item)

    for rx in (_KD_KHOI_TRUOC, _KD_KHOI_SAU):
        for m in rx.finditer(de):
            if not _la_khang_dinh_tien_de(de, m.start(), m.end()):
                continue
            tu = re.sub(r"\s+", " ", m["kn"].lower())
            km = _km_khoi(m)
            k_str = m["k"]
            if "." in k_str:
                parts = [_nhan_cum(p) for p in k_str.split(".")]
                if len(parts) != 2 or not all(parts):
                    continue
            else:
                vs = _nhan_cum(k_str)
                if tu != "tứ diện" or len(vs) != 4:
                    continue
                parts = [vs[:1], vs[1:]]
            side, end_pos = _canh_ngay_sau_hinh(de, m.end()) if (tu == "lập phương" or (tu == "tứ diện" and "đều" in km)) else (None, m.end())
            q = de[m.start():end_pos].strip()
            if tu == "lập phương":
                push(KhangDinhLoaiHinh("cube", tuple(parts[0]), top=tuple(parts[1]), side=side, quote=q))
            elif tu == "hộp chữ nhật" or (tu in ("hộp", "lăng trụ") and "chữ nhật" in km):
                push(KhangDinhLoaiHinh("cuboid", tuple(parts[0]), top=tuple(parts[1]), quote=q))
            elif tu in ("lăng trụ", "hộp") and "đều" in km and len(parts[0]) == len(parts[1]) >= 3:
                if tu == "hộp":
                    push(KhangDinhLoaiHinh("right_parallelepiped", tuple(parts[0]), top=tuple(parts[1]), quote=q))
                push(KhangDinhLoaiHinh("regular_prism", tuple(parts[0]), top=tuple(parts[1]), quote=q))
            elif tu == "hộp" and "đứng" in km:
                push(KhangDinhLoaiHinh("right_parallelepiped", tuple(parts[0]), top=tuple(parts[1]), quote=q))
            elif tu == "hộp":
                push(KhangDinhLoaiHinh("parallelepiped", tuple(parts[0]), top=tuple(parts[1]), quote=q))
                if "xiên" in km:
                    push(KhangDinhLoaiHinh("oblique_prism", tuple(parts[0]), top=tuple(parts[1]), quote=q))
            elif tu == "lăng trụ" and "đứng" in km and len(parts[0]) == len(parts[1]) >= 3:
                push(KhangDinhLoaiHinh("right_prism", tuple(parts[0]), top=tuple(parts[1]), quote=q))
            elif tu == "lăng trụ" and "xiên" in km and len(parts[0]) == len(parts[1]) >= 3:
                push(KhangDinhLoaiHinh("oblique_prism", tuple(parts[0]), top=tuple(parts[1]), quote=q))
            elif tu == "chóp" and "đều" in km and len(parts[0]) == 1 and len(parts[1]) >= 3:
                push(KhangDinhLoaiHinh("regular_pyramid", tuple(parts[1]), apex=parts[0][0], quote=q))
            elif tu == "tứ diện" and "đều" in km and len(parts[0]) + len(parts[1]) == 4:
                push(KhangDinhLoaiHinh("regular_tetrahedron", tuple(parts[0] + parts[1]), side=side, quote=q))

    for m in _KD_2D_SAU.finditer(de):
        if not (m["la"] or m["role"] or _KD_AT_RE.search(m["pred"])):
            continue
        if not _la_khang_dinh_tien_de(de, m.start(), m.end()):
            continue
        vs = tuple(_nhan_cum(m["poly"]))
        if len(set(vs)) != len(vs) or len(vs) < 3:
            continue
        cls = _phan_loai_hinh_2d(m["pred"], len(vs), m["role"] or "")
        if cls is None:
            continue
        kind, at = cls
        side, end_pos = _canh_ngay_sau_hinh(de, m.end()) if kind in ("equilateral_triangle", "square", "rhombus", "regular_hexagon") else (None, m.end())
        push(KhangDinhLoaiHinh(kind, vs, at=at, side=side, quote=de[m.start():end_pos].strip()))

    for m in _KD_2D_TRUOC.finditer(de):
        if not _la_khang_dinh_tien_de(de, m.start(), m.end()):
            continue
        vs = tuple(_nhan_cum(m["poly"]))
        if len(set(vs)) != len(vs) or len(vs) < 3:
            continue
        cls = _phan_loai_hinh_2d(m["pred"] + (m["tail"] or ""), len(vs))
        if cls is None:
            continue
        kind, at = cls
        side, end_pos = _canh_ngay_sau_hinh(de, m.end()) if kind in ("equilateral_triangle", "square", "rhombus", "regular_hexagon") else (None, m.end())
        push(KhangDinhLoaiHinh(kind, vs, at=at, side=side, quote=de[m.start():end_pos].strip()))

    khoi_calls = [c for c in calls if c.fn in _KHOI_FN]
    for m in _KD_2D_DAY.finditer(de):
        if not _la_khang_dinh_tien_de(de, m.start(), m.end()):
            continue
        base_vs = _day_khoi_cho_menh_de(de, m.start(), khoi_calls)
        if base_vs is None:
            continue
        if not base_vs:
            push(KhangDinhLoaiHinh("ambiguous_base", (), quote=de[m.start():m.end()].strip()))
            continue
        cls = _phan_loai_hinh_2d(m["pred"], len(base_vs), m["role"] or "")
        if cls is None:
            continue
        kind, at = cls
        side, end_pos = _canh_ngay_sau_hinh(de, m.end()) if kind in ("equilateral_triangle", "square", "rhombus", "regular_hexagon") else (None, m.end())
        push(KhangDinhLoaiHinh(kind, base_vs, at=at, side=side, quote=de[m.start():end_pos].strip()))

    return tuple(out)


def _cum(mau: str):
    return re.compile(mau, re.IGNORECASE)


def _hai_mat(m, a, khoi):
    return ((_cung_mat(_mat_cua(m, "a", khoi), a.plane1) and _cung_mat(_mat_cua(m, "b", khoi), a.plane2))
            or (_cung_mat(_mat_cua(m, "a", khoi), a.plane2) and _cung_mat(_mat_cua(m, "b", khoi), a.plane1)))


def _khoi_thiet_dien(m, a, khoi):
    co = [n for n in ("k", "j") if m[n + "k"] or m[n + "s"] or m[n + "t"]]
    return all(_khoi_khop(m, n, a.solid, khoi) for n in co) and (bool(co) or _chi_mot_khoi_3d(khoi))


_MOT_KHOI_RO = (
    rf"(?:(?:(?:hình|khối)(?:\s+(?:chóp|lăng trụ|lập phương|hộp|tứ diện|đa diện))?|tứ diện)"
    rf"(?:\s+(?:đứng|đều|tam giác|tứ giác|chữ nhật|lục giác))*\s+)?"
    rf"(?:{_P1}+\.{_P1}+|{_P1}{{4}})(?![\w'])"
)
_SO_LUONG_KHOI = {"hai": 2, "ba": 3, "bốn": 4}
_PHAN_CON_LAI = (
    r"thể\s+tích(?:\s+của)?\s+(?:phần|khối(?:\s+đa\s+diện|\s+chóp|\s+lăng\s+trụ)?|hình(?:\s+đa\s+diện|\s+chóp|\s+lăng\s+trụ)?)"
    r"\s+còn\s+lại"
)
_SAU_CAT_BO = r"(?:sau\s+khi|khi)(?:\s+đã)?\s+(?:cắt\s+bỏ|bỏ\s+đi|bỏ|loại\s+bỏ|lấy\s+đi)"


def _khoi_ro_cum(n: str) -> str:
    return (
        rf"(?:(?:(?P<{n}k>(?:(?:hình|khối)(?:\s+(?:chóp|lăng trụ|lập phương|hộp|tứ diện|đa diện))?|tứ diện)(?:\s+(?:đứng|đều|tam giác|tứ giác|chữ nhật|lục giác))*)\s+)?"

        rf"(?P<{n}s>{_P1}+\.{_P1}+|{_P1}{{4}})(?![\w'])"
        # a derived pyramid named by DESCRIPTION — apex + the plane that cut it (run `hybrid-contract-v2`, D3); resolved
        # only to a pyramid the gate validated on that plane (`_KHOI_MO_TA`), never by guessing
        rf"|(?:khối|hình)\s+chóp\s+(?:đỉnh\s+)?(?P<{n}da>{_P1})(?![\w'])\s+(?:được\s+)?(?:cắt(?:\s+ra)?|tạo)\s+bởi\s+"
        rf"(?:(?:mặt phẳng|mp)\s*)?\((?P<{n}dm>{_P1}|[α-ω]'?)\))"
    )


#: Derived pyramids the gate validated in THIS `kiem_nguon` call: (apex, source plane name) → solid name. Set and reset
#: by `kiem_nguon` itself (run `hybrid-contract-v2`), empty everywhere else.
_KHOI_MO_TA: contextvars.ContextVar[dict[tuple[str, str], str]] = contextvars.ContextVar("_KHOI_MO_TA", default={})


def _v_ky_hieu_cum(n: str) -> str:
    return (
        rf"(?-i:V)\s*(?:\(\s*(?P<{n}v>{_P1}+\.{_P1}+|{_P1}{{4}})\s*\)"
        rf"|_\s*\{{\s*(?P<{n}u>{_P1}+\.{_P1}+|{_P1}{{4}})\s*\}}"
        rf"|_\s*(?P<{n}w>{_P1}+\.{_P1}+|{_P1}{{4}}))(?![\w'])"
    )


def _sym_khoi(m: re.Match, n: str) -> str | None:
    gd = m.groupdict()
    if gd.get(n + "da"):
        return _KHOI_MO_TA.get().get((gd[n + "da"], gd[n + "dm"])) or "?"      # a description no pyramid answers: "?"
    return next((gd[n + k] for k in ("s", "v", "u", "w") if gd.get(n + k)), None)


def _ten_khoi_khop(sym: str | None, solid: str, khoi: dict, kw: str | None = None) -> bool:
    if not sym or (kw and not _loai_cum_dung(kw, solid)):
        return False
    if "." in sym:
        if sym == solid:
            return True
        if "." in solid:
            sa, sb = _nhan_cum(sym.split(".")[0]), _nhan_cum(sym.split(".")[1])
            ta, tb = _nhan_cum(solid.split(".")[0]), _nhan_cum(solid.split(".")[1])
            return (len(sa) == len(ta) == 1 and sa == ta and len(sb) == len(tb) and _cung_da_giac(sb, tb)) or (len(sa) == len(ta) >= 3 and len(sb) == len(tb) >= 3 and ((sa == ta and sb == tb) or (sa == tb and sb == ta)))
        return False
    pts, s_pts = _nhan_cum(sym), _nhan_cum(solid)
    return len(pts) == 4 and len(s_pts) == 4 and set(pts) == set(s_pts)


def _ds_khoi_ro_cum(n: str) -> str:
    return (
        rf"(?P<{n}>(?:(?P<{n}q>các|hai|ba|bốn|\d+)\s+)?"
        rf"{_MOT_KHOI_RO}(?:\s*(?:,|\bvà\b)\s*{_MOT_KHOI_RO})*)"
        rf"(?!\s*(?:,|\bvà\b)\s*{_MOT_KHOI_RO})"
    )


def _ds_khoi_khop(m: re.Match, n: str, solids: list[str], khoi: dict) -> bool:
    gd = m.groupdict()
    raw = gd.get(n) or ""
    items = [(x["k"], x["s"]) for x in re.finditer(_khoi_ro_cum(""), raw, re.I) if x["s"]]
    toks = [t for _kw, t in items]
    if not toks or len(toks) != len(solids) or len(set(toks)) != len(toks) or len(set(solids)) != len(solids):
        return False
    if q := (gd.get(n + "q") or "").lower():
        if q.isdigit() and int(q) != len(toks):
            return False
        if q in _SO_LUONG_KHOI and _SO_LUONG_KHOI[q] != len(toks):
            return False
        if q == "các" and len(toks) < 2:
            return False
    used: set[int] = set()
    for kw, t in items:
        idx = next((i for i, s in enumerate(solids) if i not in used and _ten_khoi_khop(t, s, khoi, kw)), None)
        if idx is None:
            return False
        used.add(idx)
    return len(used) == len(solids)


#: hàm → [(cụm, buộc(m, args, khối của đề))].
#: Curved slice (registry /23): the kind word a question uses for a solid of revolution.
_KIEU_CONG = {"trụ": "cylinder", "nón": "cone", "cầu": "sphere"}
#: How a question names one of the two cones of a cut (registry /24): the small cone at the apex, or the original cone.
_VAI_KHOI_NON = r"khối\s+nón\s+(?:nhỏ|ban\s+đầu|đã\s+cho|lớn)"
def _host_cum(n: str) -> str:
    """Host solid phrase for `ngoại tiếp` / `nội tiếp`: either an axial cylinder/cone or a non-empty polyhedron phrase."""
    return (
        rf"(?:\s+(?:hình|khối)\s+(?P<{n}ck>trụ|nón)(?:\s+tròn\s+xoay)?"
        rf"(?:\s+(?P<{n}cs>(?-i:\([A-Z][0-9]*'?\)|[A-Z][0-9]*'?(?:\.[A-Z][0-9]*'?)?))(?![\w'])(?!\.[A-Z]))?"
        rf"|(?:(?:\s+(?P<{n}k>{_TU_KHOI})(?:\s+(?:đứng|đều|tam giác|tứ giác|chữ nhật|lục giác))*)?"
        rf"(?:\s+(?:(?P<{n}s>{_P1}+\.{_P1}+)|(?P<{n}t>{_P1}{{4}}))(?![\w']))?"
        rf"(?({n}k)|(?({n}s)|(?({n}t)|(?!))))))"
    )


def _host_khop(m: re.Match, n: str, host_solid: str, calls: tuple[LoiGoi, ...], khoi_map: dict) -> bool:
    gd = m.groupdict()
    if gd.get(n + "ck"):
        want_kind = _KIEU_CONG[gd[n + "ck"].lower()]
        hosts = [k for k in calls if k.fn == "curved_solid" and k.args.kind == want_kind]
        if gd.get(n + "cs"):
            return any(k.args.solid == host_solid == gd[n + "cs"] for k in hosts)
        return len(hosts) == 1 and hosts[0].args.solid == host_solid
    has_p = bool(gd.get(n + "k") or gd.get(n + "s") or gd.get(n + "t"))
    return has_p and _khoi_khop(m, n, host_solid, khoi_map)


_KHOI_CONG_CUM = (
    r"(?:\s+của)?\s+(?:khối|hình|mặt)\s+(?P<kieu>trụ|nón|cầu)(?:\s+tròn\s+xoay)?"
    r"(?:\s+(?-i:(?P<ten>\([A-Z][0-9]*'?\)|[A-Z][0-9]*'?(?:\.[A-Z][0-9]*'?)?))(?![\w'])(?!\.[A-Z]))?"
    rf"(?:\s+(?:có\s+)?tâm\s+(?:là\s+)?(?P<tam>{_P1})(?![\w']))?"
    rf"(?P<nt>\s+ngoại\s+tiếp{_host_cum('pk')}(?:\s+đã\s+cho)?)?"
)
_KHOI_CONG_NOI_TIEP_CUM = (
    r"(?:\s+của)?\s+(?:khối|hình|mặt)\s+(?P<kieu>trụ|nón|cầu)(?:\s+tròn\s+xoay)?"
    r"(?:\s+(?-i:(?P<ten>\([A-Z][0-9]*'?\)|[A-Z][0-9]*'?(?:\.[A-Z][0-9]*'?)?))(?![\w'])(?!\.[A-Z]))?"
    rf"(?:\s+(?:có\s+)?tâm\s+(?:là\s+)?(?P<tam>{_P1})(?![\w']))?"
    rf"(?P<it>\s+(?:nội\s+tiếp|tiếp\s+xúc\s+với\s+tất\s+cả\s+các\s+mặt\s+của){_host_cum('pk')}(?:\s+đã\s+cho)?)"
)


def _cong_khop(m: re.Match, a: Any, khoi: dict | None = None, *, noi_tiep_rule: bool = False) -> bool:
    """The question names a uniquely disambiguated declared curved solid: by kind, symbol `(S1)`/`(S2)`, center, or relation."""
    calls = _GOI_NGUON.get()
    cong = [k for k in calls if k.fn == "curved_solid"]
    kieu_want = _KIEU_CONG[m["kieu"].lower()]
    same_kind = [k for k in cong if k.args.kind == kieu_want]
    targets = [k for k in same_kind if k.args.solid == a.solid]
    if len(targets) != 1:
        return False
    ca = targets[0].args
    gd = m.groupdict()
    khoi_map = _khoi_cua_loi_goi(calls) if khoi is None else khoi
    if noi_tiep_rule:
        if ca.inscribed_in is None or gd.get("tam") not in (None, ca.center) or m["ten"] not in (None, a.solid):
            return False
        if not _host_khop(m, "pk", ca.inscribed_in, calls, khoi_map):
            return False
        if m["ten"] is None and gd.get("tam") is None:
            return len([k for k in same_kind if k.args.inscribed_in == ca.inscribed_in]) == 1
        return True
    if gd.get("nt") is not None:
        if ca.circumscribes is None or gd.get("tam") not in (None, ca.center) or m["ten"] not in (None, a.solid):
            return False
        if not _host_khop(m, "pk", ca.circumscribes, calls, khoi_map):
            return False
        if m["ten"] is None and gd.get("tam") is None:
            return len([k for k in same_kind if k.args.circumscribes == ca.circumscribes]) == 1
        return True
    if ca.circumscribes is None and ca.inscribed_in is None:
        if gd.get("tam") is not None or m["ten"] not in (None, a.solid):
            return False
        return True if m["ten"] is not None else len(same_kind) == 1
    if gd.get("tam") not in (None, ca.center) or m["ten"] not in (None, a.solid):
        return False
    if m["ten"] is not None:
        return True
    if gd.get("tam") is not None:
        return len([k for k in same_kind if k.args.center == ca.center]) == 1
    return len(same_kind) == 1


_CUM_HOI = {
    "ask_curved_volume": [
        (_cum(rf"thể tích{_KHOI_CONG_CUM}"), lambda m, a, k: _cong_khop(m, a, k)),
        (_cum(rf"thể tích{_KHOI_CONG_NOI_TIEP_CUM}"), lambda m, a, k: _cong_khop(m, a, k, noi_tiep_rule=True)),
    ],
    "ask_lateral_area": [(_cum(rf"diện tích\s+xung\s+quanh{_KHOI_CONG_CUM}"), lambda m, a, k: _cong_khop(m, a, k))],
    "ask_surface_area": [
        (_cum(rf"diện tích(?:\s+toàn\s+phần)?{_KHOI_CONG_CUM}"), lambda m, a, k: _cong_khop(m, a, k)),
        (_cum(rf"diện tích(?:\s+toàn\s+phần)?{_KHOI_CONG_NOI_TIEP_CUM}"), lambda m, a, k: _cong_khop(m, a, k, noi_tiep_rule=True)),
    ],
    "ask_radius": [
        (_cum(rf"bán\s+kính(?:\s+đáy)?{_KHOI_CONG_CUM}"), lambda m, a, k: _cong_khop(m, a, k)),
        (_cum(rf"bán\s+kính(?:\s+đáy)?{_KHOI_CONG_NOI_TIEP_CUM}"), lambda m, a, k: _cong_khop(m, a, k, noi_tiep_rule=True)),
    ],
    "ask_curved_section_area": [(_cum(r"diện\s+tích\s+(?:của\s+)?(?:thiết\s+diện|(?:hình|đường)\s+tròn\s+giao\s+tuyến)"
                                      r"(?:\s+(?:đó|này))?(?![\w])"),
                                 lambda m, a, k: _mat_cat_khop(a))],
    "ask_curved_section_radius": [(_cum(r"bán\s+kính\s+(?:của\s+)?(?:đường\s+tròn\s+)?(?:thiết\s+diện|giao\s+tuyến)"
                                        r"(?:\s+(?:đó|này))?(?![\w])"),
                                   lambda m, a, k: _mat_cat_khop(a))],
    "ask_curved_volume_ratio": [(_cum(rf"tỉ\s+số\s+(?:giữa\s+)?thể\s+tích\s+(?:của\s+)?(?P<a>{_VAI_KHOI_NON})\s+(?:và|với)\s+"
                                      rf"(?P<b>{_VAI_KHOI_NON})(?![\w])"),
                                 lambda m, a, k: _cap_khoi_khop(m, a, ratio=True))],
    "ask_curved_residual_volume": [(_cum(r"thể\s+tích\s+(?:của\s+)?(?:khối\s+nón\s+cụt|phần\s+còn\s+lại(?:\s+của\s+(?:hình|khối)\s+nón)?)(?![\w])"),
                                    lambda m, a, k: _cap_khoi_khop(None, a, ratio=False))],
    "ask_volume": [
        (_cum(rf"thể tích(?:\s+của)?(?:\s+(?-i:V)(?:\s+của)?)?{_khoi_cum('k')}(?!\s+(?:(?-i:V)\s+)?(?:của\s+)?(?:khối|hình|mặt)\s+(?:trụ|nón|cầu))"),
         lambda m, a, k: _khoi_khop(m, "k", a.solid, k)),
        (_cum(r"(?<![\w'])(?-i:V)(?![\w'])"), lambda m, a, k: _chi_mot_khoi_3d(k) and a.solid in k and not _V_DINH_NGHIA.search(m.string)
         and not m.string[m.end():].lstrip().startswith("("))],
    "ask_length": [
        (_cum(rf"(?:độ dài(?:\s+của)?\s+)?{_doan_cum('s')}"), lambda m, a, k: set(_nhan_cum(m["s"])) == set(a.segment))],
    "ask_distance_point_plane": [
        (_cum(rf"{_KC}\s+(?:từ\s+)?(?:(?:điểm|đỉnh)\s+)?(?<![\w'.])(?P<p>{_P1})(?![\w'])\s+(?:đến|tới)\s+{_mat_cum('m')}"),
         lambda m, a, k: m["p"] == a.point and _cung_mat(_mat_cua(m, "m", k), a.plane))],
    "ask_distance_lines": [
        (_cum(rf"{_KC}\s+giữa\s+(?:hai\s+đường thẳng(?:\s+chéo nhau)?\s+)?{_doan_cum('a')}\s+(?:và|với)\s+{_doan_cum('b')}"),
         lambda m, a, k: {frozenset(_nhan_cum(m["a"])), frozenset(_nhan_cum(m["b"]))} == {frozenset(a.line1), frozenset(a.line2)})],
    # a line (exactly two labels) and a plane group, or two plane groups: disjoint from `ask_distance_lines` (two labels each)
    # and `ask_distance_point_plane` (one label before "đến")
    "ask_distance_line_plane": [
        (_cum(rf"{_KC}\s+(?:giữa|từ)\s+{_doan_cum('l')}\s+(?:và|với|đến|tới)\s+{_mat_cum('m')}"),
         lambda m, a, k: set(_nhan_cum(m["l"])) == set(a.line) and _cung_mat(_mat_cua(m, "m", k), a.plane)),
        (_cum(rf"{_KC}\s+giữa\s+{_mat_cum('m')}\s+(?:và|với)\s+{_doan_cum('l')}"),
         lambda m, a, k: set(_nhan_cum(m["l"])) == set(a.line) and _cung_mat(_mat_cua(m, "m", k), a.plane))],
    "ask_distance_planes": [
        (_cum(rf"{_KC}\s+(?:giữa|từ)\s+(?:hai\s+mặt phẳng\s+)?{_mat_cum('a')}\s+(?:và|với|đến|tới)\s+{_mat_cum('b')}"), _hai_mat)],
    "ask_angle_line_plane": [
        (_cum(rf"(?:số đo\s+(?:của\s+)?)?góc\s+(?:giữa|tạo bởi|hợp bởi)\s+{_doan_cum('l')}\s+(?:và|với)\s+{_mat_cum('m')}"),
         lambda m, a, k: set(_nhan_cum(m["l"])) == set(a.line) and _cung_mat(_mat_cua(m, "m", k), a.plane))],
    "ask_angle_plane_plane": [
        (_cum(rf"(?:số đo\s+(?:của\s+)?)?góc\s+(?:giữa|tạo bởi|hợp bởi)\s+{_mat_cum('a')}\s+(?:và|với)\s+{_mat_cum('b')}"), _hai_mat)],
    # two named lines: each operand exactly two labels (`_doan_cum`), never a plane group — disjoint from the two above
    "ask_angle_lines": [
        (_cum(rf"(?:số đo\s+(?:của\s+)?)?góc\s+(?:giữa|tạo bởi|hợp bởi)\s+(?:hai\s+đường thẳng\s+)?{_doan_cum('a')}"
              rf"\s+(?:và|với)\s+{_doan_cum('b')}"),
         lambda m, a, k: {frozenset(_nhan_cum(m["a"])), frozenset(_nhan_cum(m["b"]))} == {frozenset(a.line1), frozenset(a.line2)})],
    "ask_area": [
        (_cum(rf"diện tích(?:\s+của)?\s+(?:(?:tam giác|tứ giác|hình vuông|hình chữ nhật|hình thoi|hình bình hành|hình thang"
              rf"|đa giác|mặt bên|mặt đáy|đáy|mặt)\s+)?(?:\((?P<gp>{_NHOM_NHAN})\)|(?<![\w'.])(?P<gb>{_NHOM_NHAN})"
              rf"|Δ\s*(?P<gd>{_NHOM_NHAN}))(?![\w'])"),                    # "ΔSAC": Δ là chữ, nên nhánh riêng
         lambda m, a, k: set(_nhan_cum(m["gp"] or m["gb"] or m["gd"])) == set(a.polygon)),
        (_cum(r"diện tích(?:\s+của)?\s+(?:mặt\s+)?đáy(?![\w'])"),
         lambda m, a, k: len(k) == 1 and set(next(iter(k.values()))) == set(a.polygon))],
    "ask_section_area": [
        (_cum(rf"diện tích(?:\s+của)?\s+thiết diện(?:(?:\s+của|\s+(?:được\s+)?tạo bởi){_khoi_cum('k')})?\s+(?:(?:khi\s+(?:bị\s+)?|bị\s+)?(?:cắt bởi|tạo bởi)|với|và|do)\s+{_mat_cum('m')}"
              rf"(?:\s+(?:của|và|cắt){_khoi_cum('j')})?"),
         lambda m, a, k: _cung_mat(_mat_cua(m, "m", k), a.plane) and _khoi_thiet_dien(m, a, k)),
        # "Mặt phẳng (P) cắt hình chóp … theo một thiết diện. Tính diện tích thiết diện đó.": thiết diện đã được gọi tên
        # trước trong đề, và đề chỉ gọi tên ĐÚNG MỘT mặt cắt — chính mặt của lời gọi (review S1, I1).
        (_cum(r"diện tích(?:\s+của)?\s+thiết diện\s+(?:đó|này|trên)(?!\w)"),
         lambda m, a, k: {frozenset(_nhan_cum(x[1] or x[2])) for mau in _CAT_BOI for x in mau.finditer(m.string)
                          if x[1] or x[2]} == {frozenset(a.plane)})],
    "ask_volume_ratio": [
        (_cum(rf"(?:tỉ|tỷ)\s+số(?:\s+giữa)?(?:\s+thể\s+tích)?(?:\s+(?:của|giữa))?"
              rf"(?:\s+(?:hai|2)\s+(?P<hk>(?:(?:hình|khối)(?:\s+(?:chóp|lăng trụ|lập phương|hộp|tứ diện|đa diện))?|(?:chóp|lăng trụ|lập phương|hộp|tứ diện|đa diện))(?:\s+(?:đứng|đều|tam giác|tứ giác|chữ nhật|lục giác))*))?"

              rf"\s+(?:{_v_ky_hieu_cum('x')}|{_khoi_ro_cum('x')})"
              rf"\s+(?:và|với|trên|so\s+với|chia(?:\s+cho)?)"
              rf"(?:\s+thể\s+tích(?:\s+của)?)?"
              rf"\s+(?:{_v_ky_hieu_cum('y')}|{_khoi_ro_cum('y')})"
              rf"(?:\s*,?\s*(?:tức\s+là\s+)?{_v_ky_hieu_cum('c')}\s*/\s*{_v_ky_hieu_cum('d')})?"),
         lambda m, a, k: (
             _ten_khoi_khop(_sym_khoi(m, "x"), a.numerator_solid, k, m.groupdict().get("xk") or m.groupdict().get("hk"))
             and _ten_khoi_khop(_sym_khoi(m, "y"), a.denominator_solid, k, m.groupdict().get("yk") or m.groupdict().get("hk"))
             and (not _sym_khoi(m, "c") or (
                 _ten_khoi_khop(_sym_khoi(m, "c"), a.numerator_solid, k)
                 and _ten_khoi_khop(_sym_khoi(m, "d"), a.denominator_solid, k)
             ))
         )),
        (_cum(rf"(?:(?:tỉ|tỷ)\s+số(?:\s+thể\s+tích)?(?:\s+(?:của|giữa))?\s+)?"
              rf"{_v_ky_hieu_cum('x')}\s*/\s*{_v_ky_hieu_cum('y')}"),
         lambda m, a, k: (
             _ten_khoi_khop(_sym_khoi(m, "x"), a.numerator_solid, k, m.groupdict().get("xk") or m.groupdict().get("hk"))
             and _ten_khoi_khop(_sym_khoi(m, "y"), a.denominator_solid, k, m.groupdict().get("yk") or m.groupdict().get("hk"))
         )),
    ],
    "ask_residual_volume": [
        (_cum(rf"{_PHAN_CON_LAI}\s+của\s+{_khoi_ro_cum('o')}\s+{_SAU_CAT_BO}\s+{_ds_khoi_ro_cum('s')}"),
         lambda m, a, k: (
             _ten_khoi_khop(_sym_khoi(m, "o"), a.original_solid, k, m.groupdict().get("ok"))
             and _ds_khoi_khop(m, "s", a.subtracted_solids, k)
         )),
        (_cum(rf"{_PHAN_CON_LAI}\s+{_SAU_CAT_BO}\s+{_ds_khoi_ro_cum('s')}\s+(?:khỏi|từ|của|ở|trong)\s+{_khoi_ro_cum('o')}"),
         lambda m, a, k: (
             _ten_khoi_khop(_sym_khoi(m, "o"), a.original_solid, k, m.groupdict().get("ok"))
             and _ds_khoi_khop(m, "s", a.subtracted_solids, k)
         )),
    ],
}
#: Distance target after "đến/tới": a source result line (groups a, b), a named plane (`_mat_cum`), or a named line (l).
_DICH_KHOANG_CACH = (rf"(?:(?i:giao tuyến của)\s*(?P<a>{_MAT_TOAN_HANG})\s*(?i:và)\s*(?P<b>{_MAT_TOAN_HANG})"
                     rf"|{_mat_cum('m')}|(?:(?i:đường thẳng|đt)\s+)?(?<![\w'.])(?P<l>{_P1}{_P1})(?![\w']))")


@functools.lru_cache(maxsize=None)
def _mau_khoang_cach_mo_ta(phrase: str) -> re.Pattern[str]:
    """Closed ask phrase "khoảng cách từ ‹unnamed point, as the contract's `phrase` names it› đến ‹target›"."""
    return re.compile(_KC + r"\s+từ\s+(?:" + phrase.replace("{P}", _P1) + r")\s+(?:đến|tới)\s+" + _DICH_KHOANG_CACH,
                      re.IGNORECASE)


#: SG-4: closed tokens shared by every goal `phrase`, so the same wording choices hold for every contract — `{N}` the optional
#: class noun before a NAMED point ("điểm S", "đỉnh S"), `{J}` the joiner of "nối X với/và Y", `{K}` the joiner between the
#: described point and the named points of a triangle ("…, hai điểm S, A" / "… với hai điểm S, A" / "… cùng với …").
_TEN_LOAI_DIEM = r"(?:(?:điểm|đỉnh)\s+)?"
_NOI_HAI_DIEM = r"\s+(?:với|và)\s+"
_NOI_DANH_SACH = r"(?:\s*,\s*|\s+(?:và|với|cùng(?:\s+với)?)\s+)"


@functools.lru_cache(maxsize=None)
def _mau_muc_tieu_mo_ta(goal_phrase: str, descriptor_phrase: str) -> re.Pattern[str]:
    """Goal wording with its slot groups: `{D}` the described point, `{P}` a label, `{M}` a plane (group m, the ask
    grammar's own `_mat_cum`), `{L}` a line (group l, `_doan_cum`)."""
    return re.compile(goal_phrase.replace('{D}', descriptor_phrase).replace('{N}', _TEN_LOAI_DIEM)
                      .replace('{J}', _NOI_HAI_DIEM).replace('{K}', _NOI_DANH_SACH).replace('{P}', _P1)
                      .replace('{M}', _mat_cum('m')).replace('{L}', _doan_cum('l')), re.IGNORECASE)


def _cac_cau(phrase: str | tuple[str, ...] | None) -> tuple[str, ...]:
    """A contract `phrase`: one closed wording, or a tuple of closed wordings (e.g. both operand orders)."""
    return phrase if isinstance(phrase, tuple) else (phrase,) if phrase else ()


@functools.lru_cache(maxsize=None)
def _mau_hoi_dong(desc: tuple[str, ...], goals: tuple[str, ...]) -> tuple[re.Pattern[str], ...]:
    return (*(mau for ds in _CUM_HOI.values() for mau, _b in ds), _KHOANG_CACH_DIEM_DUONG, _KHOANG_CACH_GIAO_TUYEN,
            _CUM_HOI_THIET_DIEN_PHU, *(_mau_khoang_cach_mo_ta(d) for d in desc),
            *(_mau_muc_tieu_mo_ta(g, d) for g in goals for d in desc))


def _mau_hoi_tat_ca() -> tuple[re.Pattern[str], ...]:
    """EVERY object phrase a request can name — the per-function ask grammar, the auxiliary distance phrases and the
    contract phrases of unnamed points (Registry data). One inventory for request coverage (M1): no wording list."""
    ct = [p for s in REGISTRY.values() for p in planning_contracts(s)]
    desc = tuple(p.phrase for p in ct if p.descriptor and isinstance(p.phrase, str))
    goals = tuple(g for p in ct if p.goal for g in _cac_cau(p.phrase))
    return _mau_hoi_dong(desc, goals)


def _cum_lon_nhat(de: str, a: int, b: int) -> list[tuple[int, int]]:
    """Object phrases in `de[a:b]` not contained in a longer one ("SC" inside "khoảng cách từ trung điểm của SC đến …")."""
    cum = {(m.start(), m.end()) for mau in _mau_hoi_tat_ca() for m in mau.finditer(de, a, b) if m.end() > m.start()}
    return sorted(x for x in cum if not any(y != x and y[0] <= x[0] and x[1] <= y[1] for y in cum))


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
_GIUA_HOP_LE = re.compile(r"[\s,:]*(?:(?:(?:và|cùng|lần lượt|hãy|các)(?!\w)|theo\s+[a-z](?![\w']))[\s,:]*)*", re.IGNORECASE)
#: Phần còn lại của một câu hỏi sau khi mọi vùng đã đọc được xoá: chỉ dấu câu, từ nối, lời mở đầu câu và đánh mục.
_DAN_CAU_HOI = re.compile(
    r"[\s,;:.?!]*(?:(?:\(?(?:[a-z]|\d{1,2})\)|(?:câu|ý|phần)\s+(?:[a-z]|\d{1,2})|hơn nữa|ngoài ra|khi đó|từ đó|sau đó|tiếp theo|tiếp đó"
    r"|rồi|do đó|vậy|cuối cùng|và|cùng|hãy|em hãy|các|lần lượt)(?!\w)[\s,;:.?!]*)*", re.IGNORECASE)
#: The anaphoric object of a request a validated section / intersection line answers ("Xác định thiết diện đó.").
_HOI_CHI_DUNG = re.compile(
    r"(?:(?<!\w)(?:xác\s+định|tìm|dựng|vẽ)\s+)?(?<!\w)(?P<n>thiết\s+diện|giao\s+tuyến)\s+"
    r"(?:đó|này|trên|vừa\s+dựng(?:\s+được)?)(?!\w)",
    re.IGNORECASE,
)
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
#: Possessive separators cannot be repartitioned by the outer repetition when an unread suffix fails.
_SAU_HOP_LE = re.compile(
    r"(?:[\s,;:]++|(?:và|cùng)(?!\w)|(?:có\s+)?(?:độ dài\s+)?(?:bằng|là)\s+bao\s+nhiêu|dài\s+bao\s+nhiêu|bao\s+nhiêu"
    # SG-5: the next REQUEST of a list ("… SB và tính độ dài SC", "…, đồng thời tìm …") — its object is another ask
    # phrase, already blanked by `_bo_cum`; any unread object after the verb still fails this closed tail
    r"|(?:đồng\s+thời|hãy|tính|tìm|xác\s+định)(?!\w)"
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
    "ask_distance_line_plane": "length",
    "ask_distance_planes": "length",
    "ask_area": "area",
    "ask_section_area": "area",
    "ask_volume": "volume",
    "ask_volume_ratio": "ratio",
    "ask_residual_volume": "volume",
    "ask_angle_line_plane": "angle",
    "ask_angle_plane_plane": "angle",
    "ask_angle_lines": "angle",
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
    giua_raw = _bo_cum(de[vung[0]:a])
    for m_g in re.finditer(r"theo\s+(?P<sym>[a-z])(?![\w'])", giua_raw, re.IGNORECASE):
        if chieu not in ("length", "area", "volume") or m_g["sym"].lower() != "a" or not _co_tham_so_a(calls):
            return False
    duoi_raw = de[b:vung[1]]
    patterns = _mau_hoi_tat_ca()
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
            if not mm or chieu in ("angle", "ratio"):
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


_NOI_TY_SO = r"(?i:sao\s+cho|thỏa\s+mãn|với)"

#: An operand of an intersection-point definition: a named line / segment / edge, or a plane (labels, a named (P) / (α),
#: the base).
_TOAN_HANG_GIAO = (rf"(?:(?:(?:đường\s+thẳng|đường\s+chéo|đoạn(?:\s+thẳng)?|cạnh(?:\s+bên|\s+đáy)?)\s+)?{_P1}{_P1}(?![\w'])"
                   rf"|(?:mặt\s+phẳng\s*|mp\s*)?\((?:[A-Z][0-9]*'?|[α-ωΑ-Ω][0-9]*'?)\)|{_MAT_TOAN_HANG})")
_CUM_DINH_NGHIA_DIEM = re.compile(
    # ratio point written without "là … điểm" ("Điểm M thuộc cạnh SA sao cho SM = 1/3 SA"): the same optional part as the
    # binding grammar `_TY_SO`, so a clause that grammar validated is read whole (run `typedfactnext-planner-bridge`)
    rf"(?:(?:(?:gọi|lấy|chọn|cho|dựng|vẽ|xác định|tìm)\s+)?(?:điểm\s+)?{_P1}\s+(?:thuộc|nằm\s+trên|trên)\s+"
    rf"(?:(?:cạnh|đoạn\s+thẳng|đoạn)\s+)?{_P1}{_P1}\s*,?\s*{_NOI_TY_SO}\s+{_P1}{_P1}\s*=\s*(?:\d+(?:/\d+)?)?\s*{_P1}{_P1}[.\s]*$)|"
    rf"(?:(?:(?:gọi|lấy|cho|dựng|vẽ|xác định|tìm)\s+)?(?:điểm\s+)?{_P1}\s+(?:là|trùng\s+với)\s+"
    rf"(?:trung điểm(?:\s+của)?(?:\s+(?:đoạn(?:\s+thẳng)?|cạnh(?:\s+bên|\s+đáy)?))?\s+{_P1}{_P1}"
    rf"|trọng tâm(?:\s+của)?(?:\s+(?:tam giác|tứ giác|đa giác|mặt\s+đáy|đáy))?\s+\(?{_NHOM_NHAN}\)?"
    rf"|hình chiếu(?:\s+vuông góc)?\s+của\s+(?:điểm\s+|đỉnh\s+)?{_P1}\s+(?:lên|trên)\s+(?:{_MAT_TOAN_HANG}|(?:đường thẳng\s+|cạnh\s+)?{_P1}{_P1}|{_GIAO_TUYEN.pattern})"
    # two closed operands (review round 2: "[^,.;!?]+" also read "… và tìm giao điểm của SC với (ABD)" as this definition)
    rf"|giao điểm\s+của\s+(?:hai\s+đường(?:\s+thẳng|\s+chéo)?\s+)?{_TOAN_HANG_GIAO}\s+(?:và|với)\s+{_TOAN_HANG_GIAO}"
    # ratio point (`divide_segment`, bound by `_TY_SO`): "M là điểm thuộc cạnh SA sao cho SM = 2MA"
    rf"|(?:một\s+)?điểm\s+(?:thuộc|nằm\s+trên|trên)\s+(?:(?:cạnh|đoạn\s+thẳng|đoạn)\s+)?{_P1}{_P1}\s*,?\s*{_NOI_TY_SO}\s+"
    rf"{_P1}{_P1}\s*=\s*(?:\d+(?:/\d+)?)?\s*{_P1}{_P1})"
    rf"|hình chiếu(?:\s+vuông góc)?\s+của\s+(?:điểm\s+|đỉnh\s+)?{_P1}\s+(?:lên|trên)\s+(?:{_MAT_TOAN_HANG}|(?:đường thẳng\s+|cạnh\s+)?{_P1}{_P1})\s+(?:là|trùng\s+với)\s+(?:(?:điểm|đỉnh|trọng tâm|trung điểm)\s+)?{_P1}(?:\s+của\s+(?:(?:cạnh(?:\s+bên|\s+đáy)?|đoạn(?:\s+thẳng)?|tam\s+giác|đáy)\s+)?(?:{_NHOM_NHAN}|{_P1}{_P1}))?)[.\s]*",
    re.IGNORECASE,
)
_CUM_DUNG_THIET_DIEN = re.compile(
    rf"(?:xác định|tìm|dựng|vẽ)\s+thiết diện(?:(?:\s+của|\s+(?:được\s+)?tạo bởi){_khoi_cum('k')})?\s+"
    rf"(?:(?:khi\s+(?:bị\s+)?|bị\s+)?(?:cắt bởi|tạo bởi)|với|và|do)\s+{_mat_cum('m')}"
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
        if c.fn in ("midpoint", "centroid", "divide_segment", "orthogonal_projection", "orthogonal_projection_line",
                    "intersect_line_line", "intersect_line_plane"):
            for q in c.quotes:
                if (vt := _vi_tri(de, q)) is not None and start <= vt[0] and vt[1] <= end:
                    if (_CUM_DINH_NGHIA_DIEM.fullmatch(de[vt[0]:vt[1]])
                            or c.fn == "divide_segment" and _ty_so_tron_cau(c, de[vt[0]:vt[1]])
                            or c.fn == "orthogonal_projection" and _chan_duong_cao_dung_nguon(c, de[vt[0]:vt[1]])):
                        m_lead = re.search(r"(?<!\w)(?:gọi|lấy|cho)\s+$", de[start:vt[0]], re.IGNORECASE)
                        spans.append((start + m_lead.start() if m_lead else vt[0], vt[1]))
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
            if any(_cung_mat(frozenset(_nhan_cum(m[1] or m[2])), c.args.plane) and _cum_goi_khoi(m[0], c.args.solid, calls) for c in sec_calls):
                spans.append((m.start(), m.end()))
    if any(c.id in phu and c.fn in ("section", "ask_section_area") for c in calls):
        for pat in (_CUM_DUNG_MAT_PHU, _CUM_DUNG_THIET_DIEN_PHU):
            for m in pat.finditer(de, start, end):
                spans.append((m.start(), m.end()))
    if any(c.id in phu and c.fn == _ham_giao_diem() for c in calls):
        # a cut clause whose `DINH_CAT_CANH` certificate the gate validated (exact edges/names checked there); its restated
        # subject "…; (α) cắt …" is read with it when (α) is a plane the source DEFINES (run `hybrid-contract-v2`, D3)
        dinh_nghia = {m["ten"] for mau in (*_ALL_PLANE_DEF_MAU, *_ALL_DESC_PLANE_DEF_MAU) for m in mau.finditer(de)
                      if m["ten"]}
        for m in _CAT_CANH_CHUNG.finditer(de, start, end):
            chu = _CHU_NGU_CAT.search(de, start, m.start())
            spans.append((chu.start() if chu and chu["ten"] in dinh_nghia else m.start(), m.end()))
    # PE-1 (review round 1): an unbuilt projection is read only as the method of an ask OF ITS OWN SENTENCE; alone
    # ("Xác định hình chiếu của S lên (SBC).") it is a request no call answers
    hoi_cung_cau = any(c.spec.kind == "ask" and any((vt := _vi_tri(de, q)) is not None and start <= vt[0] and vt[1] <= end
                                                    for q in c.quotes) for c in calls)
    for m in _CUM_DUNG_HINH_CHIEU.finditer(de, start, end) if hoi_cung_cau else ():
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
#: "chứa M" ≡ "qua M" for ONE point label (run `hybrid-contract-v2`, D3): "chứa SA" is a line and never matches `diem`.
_QUA_CHUA = r"(?:(?:đi\s+)?qua|chứa)\s+(?:(?:điểm|đỉnh|trung\s+điểm|trọng\s+tâm)\s+)?"
_DUOI_DIEM_QUA = rf"(?:\s+của\s+(?:(?:cạnh|đoạn(?:\s+thẳng)?|tam\s+giác)\s+)?(?-i:{_P1}){{2,}}(?![\w']))?"
_NOI_QUAN_HE_MAT = r"\s*,?\s*(?:(?:và(?:\s+đồng\s+thời)?|đồng\s+thời)\s+)?"
_QUA_SONG_SONG = re.compile(
    rf"(?:(?:mặt phẳng|mp)\s*)?(?:\((?P<ten>{_P1}|[α-ω]'?)\)\s*)?(?:là\s+mặt phẳng\s+)?{_QUA_CHUA}"
    rf"(?P<diem>{_P1})(?![\w']){_DUOI_DIEM_QUA}{_NOI_QUAN_HE_MAT}song song\s+(?:với\s+)?" + _MAT_TOAN_HANG, re.IGNORECASE)
#: "Qua M dựng mặt phẳng (α) song song với (ABC)" — point-first order, named plane required (run `hybrid-contract-v2`, D3).
#: Groups: diem (1), ten (2), then the three operand groups of `_MAT_TOAN_HANG` (3, 4, 5).
_DIEM_TRUOC = (rf"{_QUA_CHUA}(?P<diem>{_P1})(?![\w']){_DUOI_DIEM_QUA}\s*,?\s*(?:ta\s+)?(?:dựng|vẽ|kẻ|xét|lấy|gọi|cho|thiết\s+lập)?\s*"
               rf"(?:mặt phẳng|mp)?\s*\((?P<ten>{_P1}|[α-ω]'?)\)\s*(?:là\s+mặt phẳng\s+)?{_NOI_QUAN_HE_MAT}")
_DIEM_TRUOC_SONG_SONG = re.compile(_DIEM_TRUOC + r"song song\s+(?:với\s+)?" + _MAT_TOAN_HANG, re.IGNORECASE)
_DAN_THIET_DIEN = (
    rf"thiết diện\s+(?:(?:của\s+)?{_KHOI_NGU}(?:(?:khi\s+(?:bị\s+)?|bị\s+)?(?:cắt bởi|tạo bởi)|với|bởi)\s+"
    rf"|(?:được\s+)?tạo bởi\s+{_KHOI_NGU}(?:và|với)\s+)"
)
def _td_mat_truoc_khoi(ten_pat: str) -> str:
    return (
        rf"thiết diện\s+(?:được\s+)?(?:cắt bởi|tạo bởi)\s+(?:(?:mặt phẳng|mp)\s*)?\({ten_pat}\)"
        rf"\s+(?:với|và|của)\s+(?:{_TU_KHOI}(?:\s+(?:đứng|đều|tam giác|tứ giác|chữ nhật|lục giác))*)"
        r"(?:\s+(?-i:[A-Z][0-9]*'?(?:[A-Z][0-9]*'?)*(?:\.[A-Z][0-9]*'?(?:[A-Z][0-9]*'?)*)?))?(?![\w'])"
    )
#: The definition sentence ends right after the reference plane (a real sentence end — ";" is not one), or its rest is
#: exactly the section request on the named plane. Anything else ("… và song song với (SBC)", "; (P) vuông góc với SC",
#: "(P) cắt SB tại N") is an unread condition on the plane — refused, not ignored.
_HET_CAU = re.compile(r"[.?!](?=\s|$)")
_TU_THIET_DIEN = len("thiết diện")


_NOI_DS = r"\s*(?:,\s*(?:và\s+)?|\s+và\s+)\s*"


def _cum_cat_canh(cut: dict | None, ten_mat: str | None = None) -> re.Pattern[str] | None:
    """The cut clause a `DINH_CAT_CANH` declaration states, as ONE closed pattern: "cắt (các cạnh) SB, SC (lần lượt tại N,
    P)" — exactly those edges in that order (each edge written either way round), and the names only when every cut is
    named. Run `typedfactnext-planner-bridge`. Run `hybrid-contract-v2` (D3), closed alternatives with the same meaning:
    the per-edge form "cắt SB tại N(, (và) cắt SC tại P)…" (every cut named, the same order), and the clause opened by the
    defined plane restated as subject — "…; (α) cắt …" / "…, (α) cắt …" — only when `ten_mat` is that plane's name."""
    if not cut or not cut.get("edges"):
        return None
    ten = cut.get("points") or [None] * len(cut["edges"])
    if any(ten) and not all(ten):
        return None                                    # "lần lượt tại" names every cut or none

    def canh1(a: str, b: str) -> str:
        return rf"(?-i:(?:{re.escape(a)}{re.escape(b)}|{re.escape(b)}{re.escape(a)}))(?![\w'])"
    canh = _NOI_DS.join(canh1(a, b) for a, b in cut["edges"])
    duoi = (rf"\s+(?:lần\s+lượt|theo\s+thứ\s+tự)\s+tại\s+(?:(?:các\s+)?điểm\s+)?"
            + _NOI_DS.join(rf"(?-i:{re.escape(p)})(?![\w'])" for p in ten)) if all(ten) else ""
    lop = rf"(?:(?:các\s+|hai\s+|ba\s+|bốn\s+)?(?:cạnh|đường thẳng)(?:\s+bên)?\s+)?"
    than = [rf"cắt\s+{lop}{canh}{duoi}"]
    if all(ten):
        tai = [rf"{canh1(a, b)}\s+tại\s+(?:điểm\s+)?(?-i:{re.escape(p)})(?![\w'])" for (a, b), p in zip(cut["edges"], ten)]
        than.append(rf"cắt\s+(?:cạnh(?:\s+bên)?\s+)?{tai[0]}" + "".join(rf"{_NOI_DS}(?:cắt\s+(?:cạnh(?:\s+bên)?\s+)?)?{t}" for t in tai[1:]))
    mo = [r"\s*,?\s*(?:và\s+)?"]
    if ten_mat:
        mo.append(rf"\s*[,;]\s*(?:(?:mặt phẳng|mp)\s*)?\({re.escape(ten_mat)}\)\s+")
    return re.compile(rf"(?:{'|'.join(mo)})(?:{'|'.join(than)})\s*", re.IGNORECASE)


#: The defined plane restated as the subject right before a cut clause: "…; (α) cắt …" (run `hybrid-contract-v2`, D3).
_CHU_NGU_CAT = re.compile(rf"[,;]\s*(?:(?:mặt phẳng|mp)\s*)?\((?P<ten>{_P1}|[α-ω]'?)\)\s+\Z")
#: Any cut clause (question-context coverage of a sentence whose cut certificate the gate already validated). The per-edge
#: form "cắt SB tại N, cắt SC tại P" comes first so it is matched whole (run `hybrid-contract-v2`).
_CAT_TAI = rf"(?-i:{_P1}{_P1})(?![\w'])\s+tại\s+(?:điểm\s+)?(?-i:{_P1})(?![\w'])"
_CAT_CANH_CHUNG = re.compile(
    rf"cắt\s+(?:cạnh(?:\s+bên)?\s+)?{_CAT_TAI}(?:{_NOI_DS}(?:cắt\s+(?:cạnh(?:\s+bên)?\s+)?)?{_CAT_TAI})*"
    rf"|cắt\s+(?:(?:các\s+|hai\s+|ba\s+|bốn\s+)?(?:cạnh|đường thẳng)(?:\s+bên)?\s+)?(?-i:{_P1}{_P1})(?![\w'])"
    rf"(?:{_NOI_DS}(?-i:{_P1}{_P1})(?![\w']))*(?:\s+(?:lần\s+lượt|theo\s+thứ\s+tự)\s+tại\s+(?:(?:các\s+)?điểm\s+)?(?-i:{_P1})(?![\w'])"
    rf"(?:{_NOI_DS}(?-i:{_P1})(?![\w']))*)?", re.IGNORECASE)


def _het_dinh_nghia(s: str, cuoi: int, m: re.Match, cut: dict | None = None,
                    doc_cat: list[tuple[int, int]] | None = None) -> bool:
    """`s`: the SOURCE (with the quote normalised in place); `cuoi`: where the definition ends in it. The rest of the source
    sentence is read, whatever the quote's extent (a quote cut after the operand never hides "… và song song với …").
    A declared cut clause (`cut`, `DINH_CAT_CANH`) may be that rest — read, and its span recorded in `doc_cat`."""
    het = _HET_CAU.search(s, cuoi)
    con = s[cuoi:het.start() if het else len(s)]
    if not con.strip():
        return True
    ten_m = m["ten"] if "ten" in m.re.groupindex else None
    duoi_hoi_gop = r"(?:\s*[,;]?\s*(?:(?:và|rồi|sau đó)\s+)?(?:hãy\s+)?(?:tính|tìm|xác định)\s+diện tích\s+(?:của\s+)?(?:thiết diện(?:\s+(?:đó|này|trên))?|nó))?"
    duoi_td_ten = (
        rf"\s*[,;]?\s*(?:(?:và|rồi|sau đó)\s+)?(?:hãy\s+)?(?:xác định|tìm|tính)(?:\s+diện tích(?:\s+của)?)?\s+"
        rf"(?:{_td_mat_truoc_khoi(re.escape(ten_m))}|{_DAN_THIET_DIEN}(?:(?:mặt phẳng|mp)\s*)?\({re.escape(ten_m)}\)){duoi_hoi_gop}\s*"
    ) if ten_m else None
    if (r := _cum_cat_canh(cut, ten_m)) is not None and (mc := r.match(con)) is not None:
        con_sau = con[mc.end():]
        if not con_sau.strip() or (duoi_td_ten is not None and re.fullmatch(duoi_td_ten, con_sau, re.IGNORECASE)):
            if doc_cat is not None:
                doc_cat.append((cuoi, cuoi + mc.end()))
            return True
    dau_m = s.rfind(m[0], 0, cuoi + 1)
    if dau_m >= 0 and re.search(_DAN_THIET_DIEN + r"$", s[_cau_chua(s, dau_m):dau_m], re.IGNORECASE):
        if re.fullmatch(
            r"\s*[,;]?\s*(?:(?:và|rồi|sau đó)\s+)?(?:hãy\s+)?(?:tính|tìm|xác định)\s+diện tích\s+(?:của\s+)?(?:thiết diện(?:\s+(?:đó|này|trên))?|nó)\s*",
            con, re.IGNORECASE,
        ):
            return True
    return bool(ten_m and duoi_td_ten and re.fullmatch(duoi_td_ten, con, re.IGNORECASE) is not None)
_HOI_DIEN_TICH_THIET_DIEN = re.compile(r"diện tích\s+(?:của\s+)?thiết diện", re.IGNORECASE)
_HOI_DIEN_TICH_NO = re.compile(r"diện tích\s+(?:của\s+)?nó(?![\w'])", re.IGNORECASE)
_DANH_TU_CANH_TRANH_TD = re.compile(
    r"(?<!\w)(?:tam\s+giác|tứ\s+giác|đa\s+giác|hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thang|hình\s+bình\s+hành|hình\s+thoi|mặt\s+bên|mặt\s+đáy|đáy)(?!\w)",
    re.IGNORECASE,
)
_HOI_DIEN_TICH_TEN_TD = re.compile(
    r"diện tích\s+(?:của\s+)?(?P<loai>tam\s+giác|tứ\s+giác|đa\s+giác|hình\s+thang|hình\s+bình\s+hành|hình\s+chữ\s+nhật|hình\s+thoi|hình\s+vuông)\s+(?P<poly>(?-i:[A-Z][0-9]*'?){3,})(?![\w'])",
    re.IGNORECASE,
)
_CUM_TEN_THIET_DIEN = re.compile(
    r"thiết diện(?:\s+là)?(?:\s+(?:tam\s+giác|tứ\s+giác|đa\s+giác))?\s+(?P<poly>(?-i:[A-Z][0-9]*'?){3,})(?![\w'])",
    re.IGNORECASE,
)
#: "thiết diện đó / này / trên" closing the asked object (matched right after the word "thiết diện").
_DAI_TU_THIET_DIEN = re.compile(r"\s+(?:đó|này|trên)(?![\w'])\s*(?:(?:có\s+)?(?:bằng|là)\s+bao\s+nhiêu\s*)?(?:[.?!,;](?=\s|$)|\?|$)",
                                re.IGNORECASE)


def _cum_goi_khoi(cum: str, solid: str, calls: tuple | None = None) -> bool:
    """A matched section reference ("thiết diện của <khối> với (P)" / "(P) cắt <khối> theo thiết diện") names `solid`: a
    written symbol IS it (a tetrahedron by its four labels), else a kind word is its kind (`_khoi_khop`). Needed because
    `_khoi_trong_quote` takes a symbol from ANY merged quote of a shared plane — "diện tích thiết diện của hình chóp T.XYZ
    với (P)" beside "Dựng thiết diện của hình chóp S.ABC với (P)" was served (run `hybrid-v2-planner-generalization`)."""
    m = (re.match(rf"thiết diện\s+(?:được\s+)?(?:cắt bởi|tạo bởi)\s+(?:(?:mặt phẳng|mp)\s*)?\([^)]+\)\s+(?:với|và|của)\s+(.*)$", cum, re.I)
         or re.match(rf"thiết diện\s+(?:của\s+|(?:được\s+)?tạo bởi\s+)?({_KHOI_NGU})", cum, re.I)
         or re.search(r"cắt\s+(.*?)\s+theo", cum, re.I | re.S))
    cum = m[1] if m else ""
    if ky := [phan for _a, _b, phan in _tu_nhan(cum)]:
        return all(".".join(map("".join, p)) == solid if len(p) == 2 else set(p[0]) == set(_nhan_cum(solid)) for p in ky) and _loai_cum_dung(cum, solid, calls)
    return _loai_cum_dung(cum, solid, calls)


def _khoi_trong_quote(c: LoiGoi, khoi: dict[str, frozenset]) -> bool:
    """Solid symbol written in the quote is the call's solid; with no symbol the problem has exactly one solid."""
    ky_hieu = {"".join(phan[0]) + "." + "".join(phan[1]) for q in c.quotes for _a, _b, phan in _tu_nhan(chuan_hoa(q))
               if len(phan) == 2}
    return c.args.solid in ky_hieu if ky_hieu else len(khoi) == 1


def _mat_coplanar_khoi(calls: tuple[LoiGoi, ...], solid: str) -> set[frozenset[str]]:
    """All 4-vertex coplanar faces and diagonal planes of the declared `solid`."""
    out: set[frozenset[str]] = set()
    for c in calls:
        if c.fn in ("pyramid", "regular_pyramid") and f"{c.args.apex}.{''.join(c.args.base)}" == solid:
            if len(c.args.base) == 4:
                out.add(frozenset(c.args.base))
        elif c.fn == "prism" and f"{''.join(c.args.base)}.{''.join(c.args.top)}" == solid:
            b, t = list(c.args.base), list(c.args.top)
            n = len(b)
            if n == 4:
                out.add(frozenset(b))
                out.add(frozenset(t))
                for i in range(4):
                    out.add(frozenset((b[i], b[(i + 1) % 4], t[(i + 2) % 4], t[(i + 3) % 4])))
            for i in range(n):
                j = (i + 1) % n
                out.add(frozenset((b[i], b[j], t[j], t[i])))
                for k in range(i + 2, n):
                    if not (i == 0 and k == n - 1):
                        out.add(frozenset((b[i], b[k], t[k], t[i])))
    return out


@functools.lru_cache(maxsize=None)
def _mau_mat_phu_mo_ta(dc_phrase: str, kind: str) -> tuple[tuple[re.Pattern[str], int], ...]:
    """Closed derived-plane patterns where the through-point is described by a Registry descriptor contract `dc_phrase`."""
    dp = dc_phrase.replace("{P}", _P1)
    qua = rf"(?:(?:đi\s+)?qua|chứa)\s+(?:điểm\s+là\s+)?{dp}"
    dt_pre = (rf"{qua}\s*,?\s*(?:ta\s+)?(?:dựng|vẽ|kẻ|xét|lấy|gọi|cho|thiết\s+lập)?\s*"
              rf"(?:mặt phẳng|mp)?\s*\((?P<ten>{_P1}|[α-ω]'?)\)\s*(?:là\s+mặt phẳng\s+)?{_NOI_QUAN_HE_MAT}")
    if kind == "two_lines":
        tail = (r"song song\s+(?:với\s+)?(?:(?:cả\s+)?(?:hai|các)\s+(?:đường thẳng|cạnh)(?:\s+bên|\s+đáy)?\s+)?"
                rf"(?P<a>{_P1})\s*(?P<b>{_P1})(?![\w'])\s*(?:,\s*|\s+và\s+)\s*(?P<c>{_P1})\s*(?P<d>{_P1})(?![\w'])")
        p1 = re.compile(rf"(?:(?:mặt phẳng|mp)\s*)?\((?P<ten>{_P1}|[α-ω]'?)\)\s*(?:là\s+mặt phẳng\s+)?{qua}{_NOI_QUAN_HE_MAT}" + tail, re.I)
        p2 = re.compile(dt_pre + tail, re.I)
        return ((p1, 0), (p2, 0))
    if kind == "perp_line":
        tail = (r"vuông góc\s+(?:với\s+)?(?:(?:đường thẳng|đường chéo|cạnh bên|cạnh đáy|đoạn thẳng|đoạn|cạnh)\s+)?"
                rf"(?<![\w'.(])(?P<l>{_P1}{_P1})(?![\w'])")
        p1 = re.compile(rf"(?:(?:mặt phẳng|mp)\s*)?(?:\((?P<ten>{_P1}|[α-ω]'?)\)\s*)?(?:là\s+mặt phẳng\s+)?{qua}{_NOI_QUAN_HE_MAT}" + tail, re.I)
        p2 = re.compile(dt_pre + tail, re.I)
        return ((p1, 0), (p2, 0))
    pre1 = rf"(?:(?:mặt phẳng|mp)\s*)?(?:\((?P<ten>{_P1}|[α-ω]'?)\)\s*)?(?:là\s+mặt phẳng\s+)?{qua}{_NOI_QUAN_HE_MAT}song song\s+(?:với\s+)?"
    pre2 = dt_pre + r"song song\s+(?:với\s+)?"
    idx1 = re.compile(pre1, re.I).groups + 1
    idx2 = re.compile(pre2, re.I).groups + 1
    return ((re.compile(pre1 + _MAT_TOAN_HANG, re.I), idx1), (re.compile(pre2 + _MAT_TOAN_HANG, re.I), idx2))


def mat_song_song_dung_nguon(c: LoiGoi, p: str, q: list[str], de: str, calls: tuple[LoiGoi, ...],
                             ten_ra: set[str] | None = None, don_vi_de: set[str] = frozenset(),
                             buoc: list[tuple[int, int]] | None = None, duong: list[str] | None = None,
                             cut: dict | None = None, doc_cat: list[tuple[int, int]] | None = None,
                             khoi_dan_xuat: frozenset[str] = frozenset(),
                             hai_duong: list[list[str]] | None = None, ten_khai: str | None = None,
                             point_desc: tuple[PlanningContract, dict] | None = None) -> bool:
    """Bounded grammar binding a section to a derived plane: the plane through `p` parallel to (q) is defined in the quotes
    (named "(P)" and referred to by a section phrase, or written inside the section phrase), as a premise, not negated.
    Unknown wording is refused, not guessed. `ten_ra` receives the plane names the source gave, once bound. `cut` /
    `doc_cat`: a declared cut clause after the definition is read (`_het_dinh_nghia`). `khoi_dan_xuat`: pyramid calls a
    `DINH_CAT_CANH` certificate builds ON this section — not source solids a bare "thiết diện" could refer to."""
    khoi = _khoi_cua_loi_goi(tuple(x for x in calls if x.id not in khoi_dan_xuat))
    khoi_dan_xuat_ten = {
        f"{x.args.apex}.{''.join(x.args.base)}"
        for x in calls if x.id in khoi_dan_xuat and x.fn in ("pyramid", "regular_pyramid")
    }
    ky_hieu_quote = {
        "".join(phan[0]) + "." + "".join(phan[1])
        for q_str in c.quotes for _a, _b, phan in _tu_nhan(chuan_hoa(q_str)) if len(phan) == 2
    }
    if ky_hieu_quote - ({c.args.solid} | khoi_dan_xuat_ten):
        return False
    if not _khoi_trong_quote(c, khoi):
        return False
    day = khoi.get(c.args.solid)
    mat_4_hop_le = _mat_coplanar_khoi(calls, c.args.solid)
    doan = []                                            # (quote chuẩn hoá, vị trí trong đề, đề với quote chuẩn hoá)
    for quote in c.quotes:
        if (vt := _vi_tri(de, quote)) is None:
            return False
        if _phu_dinh(de, vt[0], quote):
            raise TuChoi("NEGATED_CLAUSE", f"{c.id}: {quote!r} mang phủ định", (c.id,))
        qn = chuan_hoa(quote)
        doan.append((qn, vt[0], de[:vt[0]] + qn + de[vt[1]:]))

    def vai_tro_ok(s: str, pos: int, text: str) -> bool:
        if _phu_dinh(s, pos, text):
            raise TuChoi("NEGATED_CLAUSE", f"{c.id}: mệnh đề mặt phẳng bị phủ định", (c.id,))
        role = _vai_tro_tai(s, pos)
        if role == "CONDITIONAL":
            raise TuChoi("CONDITIONAL_CLAUSE", f"{c.id}: mệnh đề mặt phẳng nằm trong mệnh đề điều kiện/giả sử", (c.id,))
        if role == "GOAL":
            raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{c.id}: mệnh đề mặt phẳng nằm trong mệnh đề mục tiêu", (c.id,))
        return True

    # `duong` given: the plane is defined by a point and a LINE it is ⊥ to (`MAT_VUONG_DUONG`); `hai_duong`: ∥ two lines; else ∥ plane q.
    if point_desc is not None:
        cac_mau_idx = _mau_mat_phu_mo_ta(
            point_desc[0].phrase or "",
            "two_lines" if hai_duong else "perp_line" if duong else "parallel",
        )
    else:
        cac_mau_idx = tuple(
            (pat, 3) for pat in (
                (_QUA_HAI_DUONG, _DIEM_TRUOC_HAI_DUONG) if hai_duong
                else (_QUA_VUONG_DUONG, _DIEM_TRUOC_VUONG_DUONG) if duong
                else (_QUA_SONG_SONG, _DIEM_TRUOC_SONG_SONG)
            )
        )
    cac_mau = tuple(pat for pat, _ in cac_mau_idx)

    def khop(m, mat_idx: int = 3) -> bool:
        if ten_khai is not None and m["ten"] != ten_khai:
            return False
        if point_desc is not None and not _khop_mo_ta_nguon(point_desc[0], point_desc[1], m, khoi):
            return False
        if hai_duong:
            return {frozenset((m["a"], m["b"])), frozenset((m["c"], m["d"]))} == {frozenset(x) for x in hai_duong}
        if duong:
            return frozenset(_nhan_cum(m["l"])) == frozenset(duong)
        tap = _tap_mat(m, mat_idx, day)
        # the source may name the reference face by ALL its vertices ("đáy (ABCD)", "mặt bên (BCC'B')", "(ACC'A')") while the call carries three of them
        return tap == frozenset(q) or (
            tap is not None and len(tap) == 4 and len(q) == 3 and frozenset(q) < tap
            and ((day is not None and tap == frozenset(day)) or tap in mat_4_hop_le)
        )

    ten_mat = set()
    valid_def_spans: set[tuple[int, int]] = set()
    gan: dict[int, int] = {}                             # vị trí (trong đề) của từ "thiết diện" → cuối cụm thiết diện
    for qn, goc, s in doan:
        for mau, mat_idx in cac_mau_idx:
            for m in mau.finditer(qn):
                if (point_desc is None and m["diem"] != p) or not khop(m, mat_idx):
                    continue
                if point_desc is None:
                    dau_diem = m[0][:m.start("diem") - m.start()].lower()
                    if "trung" in dau_diem and not any(d.fn == "midpoint" and d.args.point == p and construction_source_bound(d, de) for d in calls):
                        continue
                    if "trọng" in dau_diem and not any(d.fn == "centroid" and d.args.point == p and construction_source_bound(d, de) for d in calls):
                        continue
                cuoi = goc + m.end()
                if not duong and not hai_duong and m[mat_idx + 2] and day is not None:     # "đáy (ABCD)": the base's own label belongs to the operand
                    nhan_day = re.match(rf"\s*\((?P<n>{_NHOM_NHAN})\)", s[cuoi:])
                    if nhan_day and frozenset(_nhan_cum(nhan_day["n"])) == frozenset(day):
                        cuoi += nhan_day.end()
                if not vai_tro_ok(s, goc + m.start(), m[0]) or not _het_dinh_nghia(s, cuoi, m, cut, doc_cat):
                    return False
                valid_def_spans.add((goc + m.start(), goc + m.end()))
                if m["ten"]:
                    ten_mat.add(m["ten"])
                noi_gop = (re.search(_DAN_THIET_DIEN + r"$", qn[:m.start()], re.IGNORECASE)
                           or re.search(_DAN_THIET_DIEN + r"$", s[_cau_chua(s, goc + m.start()):goc + m.start()], re.IGNORECASE))
                if noi_gop:  # nói gộp trong cụm thiết diện
                    if not _cum_goi_khoi(noi_gop[0], c.args.solid, calls):
                        return False
                    gan[goc + m.start() - len(noi_gop[0])] = cuoi
                elif not m["ten"]:
                    return False                                 # mặt không tên, không nằm trong cụm thiết diện: không gắn được
    if not ten_mat and not gan:
        ung_vien = {ten_khai} if ten_khai else {
            m_ref["ten"]
            for qn, _goc, _s in doan
            for pat in (
                rf"{_DAN_THIET_DIEN}(?:(?:mặt phẳng|mp)\s*)?\((?P<ten>{_P1}|[α-ω]'?)\)",
                _td_mat_truoc_khoi(rf"(?P<ten>{_P1}|[α-ω]'?)"),
                rf"\((?P<ten>{_P1}|[α-ω]'?)\)\s+cắt\s+(?:hình|khối)(?:[^.;]|\.(?=[A-Z]))*?theo\s+(?:một\s+)?thiết diện",
            )
            for m_ref in re.finditer(pat, qn, re.IGNORECASE)
        }
        for ten_u in ung_vien:
            if not ten_u:
                continue
            khop_de = [(m, mat_idx) for mau, mat_idx in cac_mau_idx for m in mau.finditer(de) if m["ten"] == ten_u]
            if len(khop_de) != 1:
                continue
            m, mat_idx = khop_de[0]
            cs, ce = _bien_cau(de, m.start())
            if re.match(r"^\s*(?:hãy\s+)?dựng\b", de[cs:ce], re.IGNORECASE):
                continue
            if (point_desc is None and m["diem"] != p) or not khop(m, mat_idx):
                continue
            if point_desc is None:
                dau_diem = m[0][:m.start("diem") - m.start()].lower()
                if "trung" in dau_diem and not any(d.fn == "midpoint" and d.args.point == p and construction_source_bound(d, de) for d in calls):
                    continue
                if "trọng" in dau_diem and not any(d.fn == "centroid" and d.args.point == p and construction_source_bound(d, de) for d in calls):
                    continue
            cuoi = m.end()
            if not duong and not hai_duong and m[mat_idx + 2] and day is not None:
                nhan_day = re.match(rf"\s*\((?P<n>{_NHOM_NHAN})\)", de[cuoi:])
                if nhan_day and frozenset(_nhan_cum(nhan_day["n"])) == frozenset(day):
                    cuoi += nhan_day.end()
            if not vai_tro_ok(de, m.start(), m[0]) or not _het_dinh_nghia(de, cuoi, m, cut, doc_cat):
                return False
            valid_def_spans.add(m.span())
            ten_mat.add(ten_u)
            doan.append((de[cs:ce], cs, de))
    # A name defined anywhere in the problem for another point or plane makes "(P)" ambiguous.
    if point_desc is None:
        for mau_khac in _ALL_PLANE_DEF_MAU:
            for m in mau_khac.finditer(de):
                if m["ten"] in ten_mat and (mau_khac not in cac_mau or m["diem"] != p or not khop(m, 3)):
                    return False
        for mau_khac in _ALL_DESC_PLANE_DEF_MAU:
            for m in mau_khac.finditer(de):
                if m["ten"] in ten_mat:
                    return False
    else:
        for mau_khac in _ALL_PLANE_DEF_MAU:
            for m in mau_khac.finditer(de):
                if m["ten"] in ten_mat:
                    return False
        for mau_khac in _ALL_DESC_PLANE_DEF_MAU:
            for m in mau_khac.finditer(de):
                if m["ten"] in ten_mat and m.span() not in valid_def_spans:
                    return False
    for ten in ten_mat:
        def_sents = {
            chuan_hoa(de[cs:ce])
            for mau_khac in (*_ALL_PLANE_DEF_MAU, *_ALL_DESC_PLANE_DEF_MAU)
            for m in mau_khac.finditer(de)
            if m["ten"] == ten
            for cs, ce in (_bien_cau(de, m.start()),)
        }
        if len(def_sents) != 1:
            return False
    if hai_duong and ten_khai:
        defs_span = ([m.span() for mau in cac_mau for m in mau.finditer(de) if m["ten"] == ten_khai]
                     if point_desc is not None
                     else [m.span() for mau in (_QUA_HAI_DUONG, _DIEM_TRUOC_HAI_DUONG) for m in mau.finditer(de) if m["ten"] == ten_khai])
        refs_span = [m.span() for pat in (
            rf"{_DAN_THIET_DIEN}(?:(?:mặt phẳng|mp)\s*)?\({re.escape(ten_khai)}\)",
            _td_mat_truoc_khoi(re.escape(ten_khai)),
            rf"\({re.escape(ten_khai)}\)\s+cắt\s+(?:hình|khối)(?:[^.;]|\.(?=[A-Z]))*?theo\s+(?:một\s+)?thiết diện",
        ) for m in re.finditer(pat, de, re.IGNORECASE)]
        cut_subj_span = [
            chu.span() for m_cat in _CAT_CANH_CHUNG.finditer(de)
            if (chu := _CHU_NGU_CAT.search(de, 0, m_cat.start())) and chu["ten"] == ten_khai
        ]
        allowed_spans = defs_span + refs_span + cut_subj_span
        if any(not any(a <= m.start() < b for a, b in allowed_spans) for m in re.finditer(rf"\({re.escape(ten_khai)}\)", de)):
            return False
    for ten in ten_mat:
        mau = [(_td_mat_truoc_khoi(re.escape(ten)), False),
               (rf"{_DAN_THIET_DIEN}(?:(?:mặt phẳng|mp)\s*)?\({re.escape(ten)}\)", False),
               (rf"thiết diện\s*(?:,\s*|\s+và\s+)(?:khối|hình)\s+chóp\s+(?:đỉnh\s+)?(?P<dinh>{_P1})(?![\w'])\s+"
                rf"(?:được\s+)?(?:cắt(?:\s+ra)?|tạo)\s+bởi\s+(?:(?:mặt phẳng|mp)\s*)?\({re.escape(ten)}\)", False),
               (rf"\({re.escape(ten)}\)\s+cắt\s+(?:hình|khối)(?:[^.;]|\.(?=[A-Z]))*?theo\s+(?:một\s+)?thiết diện", True)]
        for qn, goc, s in doan:
            for r, o_cuoi in ((r, o) for x, o in mau for r in re.finditer(x, qn, re.IGNORECASE)):
                if r.groupdict().get("dinh") not in (None, c.args.solid.split(".")[0]):
                    continue
                if not _cum_goi_khoi(r[0], c.args.solid, calls):
                    return False
                if not vai_tro_ok(s, goc + r.start(), r[0]):
                    return False
                k_gan = goc + (r.end() - _TU_THIET_DIEN if o_cuoi else r.start())
                gan[k_gan] = max(gan.get(k_gan, 0), goc + r.end())
    tap_dinh_td = (frozenset((p, *(cut.get("points") or ())))
                   if cut and cut.get("points") and all(cut["points"]) and doc_cat else frozenset())
    if len(tap_dinh_td) >= 3:
        for qn, goc, s in doan:
            for r in _CUM_TEN_THIET_DIEN.finditer(qn):
                pts = _nhan_cum(r["poly"])
                if len(pts) != len(tap_dinh_td) or frozenset(pts) != tap_dinh_td or not _so_dinh_khop(r[0], len(tap_dinh_td)):
                    return False
                if not vai_tro_ok(s, goc + r.start(), r[0]):
                    return False
                gan[goc + r.start()] = goc + r.end()
                if buoc is not None:
                    buoc.append((goc + r.start(), goc + r.end()))
    hoi_ten_td: list[tuple[int, int]] = []
    if len(tap_dinh_td) >= 3:
        for qn, goc, s in doan:
            for h in _HOI_DIEN_TICH_TEN_TD.finditer(qn):
                pts = _nhan_cum(h["poly"])
                loai = re.sub(r"\s+", " ", h["loai"].lower())
                so_dinh_ok = (len(tap_dinh_td) == 3 if loai == "tam giác"
                              else len(tap_dinh_td) >= 3 if loai == "đa giác"
                              else len(tap_dinh_td) == 4)
                if (so_dinh_ok and len(pts) == len(tap_dinh_td) and frozenset(pts) == tap_dinh_td
                        and _hoi_dung_cum(de, goc + h.start(), goc + h.end())
                        and vai_tro_ok(de, goc + h.start(), h[0])):
                    hoi_ten_td.append((goc + h.start(), goc + h.end()))
    thiet_dien = bool(gan) or (bool(hoi_ten_td) and any(
        d.fn == "ask_section_area" and d.args.solid == c.args.solid and d.args.plane == c.args.plane for d in calls))
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
            # a bare "diện tích thiết diện" closing its clause names THE section only when every section the source
            # mentioned before it is the one bound to (P) (run `hybrid-contract-v2`, D3) — otherwise it is ambiguous
            if truoc and all(t in gan for t in truoc) and re.match(r"\s*(?:[.?!;]|$)", de[b:]):
                return b
            return None

        hoi_p = [(a, b_obj) for a, b in hoi if (b_obj := cuoi_cum_p(b)) is not None
                 and _hoi_dung_cum(de, a, b_obj) and _vai_tro_tai(de, a) not in ("GOAL", "CONDITIONAL")]
        for quote in c.quotes:
            if (vt := _vi_tri(de, quote)) is None:
                continue
            for h in _HOI_DIEN_TICH_NO.finditer(chuan_hoa(quote)):
                a, b_obj = vt[0] + h.start(), vt[0] + h.end()
                truoc = [t for t in moi_td if t < a]
                if (len(truoc) == 1 and truoc[0] in gan and gan[truoc[0]] <= a
                        and not _DANH_TU_CANH_TRANH_TD.search(de[gan[truoc[0]]:a])
                        and re.match(r"\s*(?:[.?!,;]|$)", de[b_obj:])
                        and _hoi_dung_cum(de, a, b_obj) and _vai_tro_tai(de, a) not in ("GOAL", "CONDITIONAL")):
                    hoi_p.append((a, b_obj))
        hoi_p.extend(hoi_ten_td)
        if not hoi_p:
            return False
        if not all(_kiem_don_vi_hoi("ask_section_area", de, a, b_obj, don_vi_de, calls) for a, b_obj in hoi_p):
            raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED",
                         f"{c.id}: đơn vị yêu cầu trong câu hỏi không khớp chính sách đơn vị của dữ kiện hoặc loại đại lượng",
                         (c.id,))
        if thiet_dien and buoc is not None:
            buoc.extend(hoi_p)
    if thiet_dien and ten_ra is not None:
        ten_ra |= ten_mat
    return thiet_dien                                    # chỉ đặt True từ một mệnh đề định nghĩa đã khớp (p, q)


def _kiem_mat_song_song(d: dict, theo_id: dict, de: str, nhan: set[str], chiem: set[str], nhan_da_khai: set,
                        calls: tuple[LoiGoi, ...], ten_mat_phu: dict | None = None,
                        don_vi_de: set[str] = frozenset(), buoc: list[tuple[int, int]] | None = None,
                        cat_doc: dict | None = None, khoi_dan_xuat: frozenset[str] = frozenset(),
                        point_desc: tuple[PlanningContract, dict] | None = None) -> set[str]:
    """Declared decomposition `MAT_SONG_SONG`: two fresh labels, two translates of the point along two directions of the
    reference plane, every target section on exactly (point, label₁, label₂), shared quotes, and a source binding.
    `cat_doc[goal]`: whether the declared cut clause (`d["cut"]`) was read after the source definition."""
    xs, p, q = list(d.get("labels") or []), d.get("point"), list(d.get("parallel_to") or [])
    qs = tuple(d.get("quotes") or ())
    ids = tuple(i for i in (*(d.get("constructs") or ()), *(d.get("targets") or ())) if i)
    dung = [theo_id.get(i) for i in d.get("constructs") or ()]
    dich = [theo_id.get(i) for i in d.get("targets") or ()]
    two = d.get("rule") == MAT_HAI_DUONG
    vuong = d.get("rule") == MAT_VUONG_DUONG
    lines = d.get("lines") or []
    duong, chan, moc = list(d.get("perpendicular_to") or []), list(d.get("feet") or []), list(d.get("anchors") or [])
    if d.get("point_chain") is not None and point_desc is None:
        raise TuChoi("AUXILIARY_RULE_MISMATCH", f"mặt phụ qua {p}: chuỗi điểm đi qua chưa được xác thực", ids)
    if vuong:
        if (len(xs) != 2 or len(set(xs + chan)) != 4 or len(chan) != 2 or len(duong) != 2 or len(set(duong)) != 2
                or len(moc) != 2 or len(set(moc)) != 2 or set(moc) & set(duong) or len(dung) != 4 or not dich or not qs):
            raise TuChoi("AUXILIARY_RULE_MISMATCH", f"mặt phụ qua {p}: khai báo không đủ cho luật {MAT_VUONG_DUONG}", ids)
        return _kiem_mat_vuong_duong(d, p, xs, chan, duong, moc, dung, dich, qs, ids, de, nhan, chiem, nhan_da_khai, calls,
                                     ten_mat_phu, don_vi_de, buoc, cat_doc, khoi_dan_xuat, point_desc)
    if (len(xs) != 2 or len(set(xs)) != 2 or (not two and len(q) < 3) or len(dung) != 2 or not dich or not qs
            or two and (len(lines) != 2 or any(len(v) != 2 or len(set(v)) != 2 for v in lines) or not d.get("plane_name"))):
        raise TuChoi("AUXILIARY_RULE_MISMATCH", f"mặt phụ qua {p}: khai báo không đủ cho luật {MAT_SONG_SONG}", ids)
    for nhan_moi in xs:
        if nhan_moi in nhan_da_khai or (point_desc is not None and nhan_moi == p):
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
    need_nhan = {v for line in huong for v in line} if point_desc is not None else ({p} | {v for line in huong for v in line})
    if lac := sorted(need_nhan - nhan):
        raise TuChoi("UNKNOWN_LABEL", f"nhãn {lac} không có trong đề", ids)
    ten_nguon: set[str] = set()
    doc_cat: list[tuple[int, int]] = []
    for c in dich:
        bound = mat_song_song_dung_nguon(
            c, p, q, de, calls, ten_nguon, don_vi_de, buoc, cut=d.get("cut"), doc_cat=doc_cat,
            khoi_dan_xuat=khoi_dan_xuat, hai_duong=lines if two else None, ten_khai=d.get("plane_name"),
            point_desc=point_desc,
        )
        if not bound:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: đề không nói thiết diện của {c.args.solid} với mặt phẳng qua {p} "
                         f"song song ({''.join(q)})", ids)
    if cat_doc is not None and d.get("cut"):
        cat_doc[d.get("goal")] = bool(doc_cat)
    if two:
        ten_nguon.add(d['plane_name'])
    # The engine names the plane by what the source called it, bound here — never by the auxiliary labels.
    if ten_mat_phu is not None:
        ten_mat_phu[ids[0]] = next(iter(ten_nguon)) if len(ten_nguon) == 1 else None
    return set(ids)


def _kiem_mat_vuong_duong(d, p, xs, chan, duong, moc, dung, dich, qs, ids, de, nhan, chiem, nhan_da_khai, calls,
                          ten_mat_phu, don_vi_de, buoc, cat_doc=None, khoi_dan_xuat=frozenset(),
                          point_desc=None) -> set[str]:
    """Declared decomposition `MAT_VUONG_DUONG`: for two solid vertices Zᵢ off the line d, Fᵢ = foot of Zᵢ on d
    (`orthogonal_projection_line`) and Xᵢ = p + Fᵢ→Zᵢ (`translate_point`); every target section on exactly (p, X₁, X₂),
    shared quotes, fresh labels, and a source definition "(P) đi qua p và vuông góc với d". The engine re-checks ⊥ exactly."""
    for nhan_moi in (*xs, *chan):
        if nhan_moi in nhan_da_khai or (point_desc is not None and nhan_moi == p):
            raise TuChoi("AUXILIARY_RULE_MISMATCH", f"điểm phụ {nhan_moi} được khai hai lần", ids)
        nhan_da_khai.add(nhan_moi)
        if nhan_moi in chiem:
            raise TuChoi("AUXILIARY_LABEL_COLLISION", f"điểm phụ {nhan_moi} trùng một nhãn của đề", ids)
    chieu, tinh = dung[:2], dung[2:]
    if not (all(c is not None and c.fn == "orthogonal_projection_line" and c.args.point == z and c.args.line == duong
                and c.args.line_ref is None and c.args.image == f and c.quotes == qs for c, z, f in zip(chieu, moc, chan))
            and all(c is not None and c.fn == "translate_point" and c.args.point == p and c.args.vector == [f, z]
                    and c.args.image == x and c.quotes == qs for c, f, z, x in zip(tinh, chan, moc, xs))
            and all(c is not None and c.fn in ("section", "ask_section_area") and c.args.plane == [p, *xs]
                    and c.quotes == qs for c in dich)):
        raise TuChoi("AUXILIARY_RULE_MISMATCH", f"mặt phụ qua {p}: lời gọi không khớp luật {MAT_VUONG_DUONG}", ids)
    need_nhan = (set(duong) | set(moc)) if point_desc is not None else ({p} | set(duong) | set(moc))
    if lac := sorted(need_nhan - nhan):
        raise TuChoi("UNKNOWN_LABEL", f"nhãn {lac} không có trong đề", ids)
    ten_nguon: set[str] = set()
    doc_cat: list[tuple[int, int]] = []
    for c in dich:
        if not mat_song_song_dung_nguon(c, p, [], de, calls, ten_nguon, don_vi_de, buoc, duong=duong, cut=d.get("cut"),
                                        doc_cat=doc_cat, khoi_dan_xuat=khoi_dan_xuat, ten_khai=d.get("plane_name"),
                                        point_desc=point_desc):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: đề không nói thiết diện của {c.args.solid} với mặt phẳng qua {p} "
                         f"vuông góc {''.join(duong)}", ids)
    if cat_doc is not None and d.get("cut"):
        cat_doc[d.get("goal")] = bool(doc_cat)
    if ten_mat_phu is not None:
        ten_mat_phu[ids[0]] = next(iter(ten_nguon)) if len(ten_nguon) == 1 else None
    return set(ids)


#: C17 closed grammar of a plane the source defines by relations, named "(P)": it contains two points (or the line through
#: them) and is ⊥ a plane, or ∥ a line. Any other wording is refused, never guessed.
_RB_DAU = (rf"(?:(?:mặt phẳng|mp)\s*)?\((?P<ten>{_P1}|[α-ω]'?)\)\s*(?:là\s+mặt phẳng\s+)?(?:(?:đi\s+)?qua|chứa)\s+"
           rf"(?:(?:hai\s+điểm|ba\s+điểm|đường thẳng|đoạn thẳng|cạnh)\s+)?(?P<p1>{_P1})\s*(?:,\s*|\s+và\s+)?(?P<p2>{_P1})(?![\w'])"
           rf"(?:\s*(?:,\s*|\s+và\s+)(?P<p3>{_P1})(?![\w']))?"
           rf"\s*,?\s*(?:(?:và(?:\s+đồng\s+thời)?|đồng\s+thời)\s+)?")
_RB_VUONG_MAT = re.compile(_RB_DAU + rf"vuông góc\s+(?:với\s+)?(?:(?:mặt phẳng|mp|mặt đáy|mặt bên)\s*)?"
                           rf"\((?P<q>{_NHOM_NHAN})\)", re.IGNORECASE)
_RB_SONG_SONG_DUONG = re.compile(_RB_DAU + rf"song song\s+(?:với\s+)?(?:(?:đường thẳng|đoạn thẳng|cạnh)\s+)?"
                                 rf"(?<![\w'.(])(?P<a>{_P1})(?P<b>{_P1})(?![\w'])", re.IGNORECASE)


def _rang_buoc_nguon(de: str) -> list[tuple[str, frozenset, tuple[int, int]]]:
    """Every constrained-plane definition the source writes: (name, its constraint set, span) — read from the TEXT."""
    out = []
    for mau, kind in ((_RB_VUONG_MAT, "perpendicular_to_plane"), (_RB_SONG_SONG_DUONG, "parallel_to_line")):
        for m in mau.finditer(de):
            ref = frozenset(_nhan_cum(m["q"])) if kind == "perpendicular_to_plane" else frozenset((m["a"], m["b"]))
            diem = frozenset(x for x in (m["p1"], m["p2"], m["p3"]) if x)
            out.append((m["ten"], frozenset({("contains_points", diem), (kind, ref)}), m.span()))
    return out


def _kiem_mat_rang_buoc(d: dict, theo_id: dict, de: str, nhan: set[str], chiem: set[str], nhan_da_khai: set[str],
                        calls: tuple[LoiGoi, ...], ten_mat_phu: dict | None,
                        buoc: list[tuple[int, int]] | None = None) -> set[str]:
    """Certificate of `MAT_RANG_BUOC` (C17). The SOURCE grounds the stated constraints (one closed-grammar definition of
    the named plane, not negated, not conditional, not a goal); the CERTIFICATE grounds every witness: a point the plane
    contains, the anchor translated along a stated line, or along a normal of a stated plane — a premise line stated ⊥ to
    it, or Z − H with H written by a function whose CONTRACT has a `Normal` effect. Nothing here proves geometry: the
    engine proves the plane exists, is unique and satisfies every constraint."""
    ids = tuple(d.get("constructs") or ()) + tuple(d.get("targets") or ())
    p, cs, chung, qs = d.get("point"), d.get("constraints") or [], d.get("witnesses") or [], tuple(d.get("quotes") or ())
    ten = d.get("plane_name")
    sai = lambda why: TuChoi("AUXILIARY_RULE_MISMATCH", f"mặt cho bằng ràng buộc ({ten}): {why}", ids)  # noqa: E731
    diem = list(dict.fromkeys(x for c in cs if c.get("kind") == "contains_points" for x in c.get("points") or ()))
    if not ten or not diem or p != diem[0] or not qs or not d.get("targets"):
        raise sai("khai báo không đủ")
    tap_rb = frozenset((c["kind"], frozenset(c["points"])) for c in cs if c["kind"] != "contains_points") | {
        ("contains_points", frozenset(diem))}
    khop = [sp for t, r, sp in _rang_buoc_nguon(de) if t == ten and r == tap_rb]
    if len(khop) != 1:
        raise TuChoi("SOURCE_OBJECT_MISMATCH", f"đề không định nghĩa đúng một mặt ({ten}) bằng các ràng buộc đã khai", ids)
    vt = khop[0][0]
    de_n = de
    if _phu_dinh(de_n, vt, de_n[vt:khop[0][1]]):
        raise TuChoi("NEGATED_CLAUSE", f"mệnh đề định nghĩa ({ten}) mang phủ định", ids)
    vai = _vai_tro_tai(de_n, vt)
    if vai == "CONDITIONAL":
        raise TuChoi("CONDITIONAL_CLAUSE", f"mệnh đề định nghĩa ({ten}) nằm trong mệnh đề điều kiện", ids)
    if vai == "GOAL":
        raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"mệnh đề định nghĩa ({ten}) nằm trong mệnh đề mục tiêu", ids)
    if lac := sorted({x for c in cs for x in c["points"]} - nhan):
        raise TuChoi("UNKNOWN_LABEL", f"nhãn {lac} không có trong đề", ids)
    tu_do = []
    for w in chung:
        tu_do += [w.get("label")] + ([w["foot"]] if w.get("foot") else [])
    for phu in tu_do:
        if not phu or phu in nhan_da_khai or phu == p:
            raise sai(f"điểm phụ {phu} được khai hai lần")
        nhan_da_khai.add(phu)
        if phu in chiem:
            raise TuChoi("AUXILIARY_LABEL_COLLISION", f"điểm phụ {phu} trùng một nhãn của đề", ids)
    dung = list(d.get("constructs") or ())
    for w in chung:
        i = w.get("constraint")
        if not isinstance(i, int) or not 0 <= i < len(cs) or cs[i]["kind"] == "contains_points":
            raise sai("điểm chứng không gắn với một ràng buộc phương")
        c, t = cs[i], theo_id.get(w.get("translate"))
        if (t is None or t.fn != "translate_point" or t.args.point != p or t.args.vector != w.get("vector")
                or t.args.image != w["label"] or t.quotes != qs):
            raise sai(f"điểm chứng {w.get('label')} không là ảnh tịnh tiến của {p}")
        if c["kind"] == "parallel_to_line":
            if w.get("producer") != "stated_line" or list(w["vector"]) != list(c["points"]):
                raise sai("phương song song không phải đường đã nêu")
        elif w.get("producer") == "premise":
            pc = theo_id.get(w.get("fact"))
            if (pc is None or pc.fn != "perpendicular_line_plane" or frozenset(pc.args.line) != frozenset(w["vector"])
                    or not (frozenset(c["points"]) <= frozenset(pc.args.plane) or frozenset(pc.args.plane) <= frozenset(c["points"]))):
                raise sai("pháp tuyến không phải đường đề cho vuông góc với mặt")
        else:
            h = theo_id.get(w.get("call"))
            spec = REGISTRY.get(h.fn) if h is not None else None
            if (spec is None or not any(pc.effect.kind == "Normal" for pc in planning_contracts(spec))
                    or h.args.point != w.get("point") or frozenset(h.args.plane) != frozenset(c["points"])
                    or h.args.image != w.get("foot") or list(w["vector"]) != [w.get("foot"), w.get("point")]
                    or h.quotes != qs or w.get("call") not in dung):
                raise sai("pháp tuyến không do một hàm có hợp đồng Normal dựng")
    mat = [p, *diem[1:], *(w["label"] for w in chung)]
    if list(d.get("plane") or ()) != mat or {w["translate"] for w in chung} | {w["call"] for w in chung if w.get("call")} != set(dung):
        raise sai("lời gọi không khớp các điểm chứng")
    doc: list[tuple[int, int]] = [khop[0]]              # spans this certificate READS: definition, section phrase, ask
    for tid in d["targets"]:
        c = theo_id.get(tid)
        if c is None or c.fn not in ("section", "ask_section_area") or c.args.plane != mat or c.quotes != qs:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{tid}: thiết diện không gọi đúng mặt ({ten})", ids)
        cum, hoi = [], []
        for quote in c.quotes:
            if (vt := _vi_tri(de, quote)) is None:
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{tid}: quote không có trong đề", ids)
            qn = chuan_hoa(quote)
            cum += [(vt[0] + r.start(), vt[0] + r.end()) for r in re.finditer(
                rf"{_DAN_THIET_DIEN}(?:(?:mặt phẳng|mp)\s*)?\({re.escape(ten)}\)", qn, re.IGNORECASE)]
            for h in _HOI_DIEN_TICH_THIET_DIEN.finditer(qn):  # "diện tích thiết diện (đó)": THE section bound to (P)
                a, b = vt[0] + h.start(), vt[0] + h.end()
                ana = re.match(r"\s+(?:đó|này|trên)(?![\w'])", de[b:], re.IGNORECASE)
                truoc = [t.start() for t in re.finditer("thiết diện", de[:b - _TU_THIET_DIEN], re.IGNORECASE)]
                b_obj = b + ana.end() if ana else b if re.match(r"\s*(?:[.?!;]|$)", de[b:]) else None
                if (b_obj is not None and truoc and any(x <= truoc[-1] < y for x, y in cum)
                        and _hoi_dung_cum(de, a, b_obj) and _vai_tro_tai(de, a) not in ("GOAL", "CONDITIONAL")):
                    hoi.append((a, b_obj))
        if not cum:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{tid}: đề không gọi thiết diện cắt bởi ({ten})", ids)
        if c.fn == "ask_section_area":
            if not hoi:
                raise TuChoi("NOT_ASKED_IN_SOURCE", f"{tid}: nguồn không hỏi diện tích thiết diện cắt bởi ({ten})", ids)
            if not all(_kiem_don_vi_hoi("ask_section_area", de, a, b, set(), calls) for a, b in hoi):
                raise TuChoi("QUESTION_CONTEXT_UNSUPPORTED", f"{tid}: đơn vị yêu cầu không khớp", ids)
        doc += cum + hoi
    if buoc is not None:
        buoc.extend(doc)
    if ten_mat_phu is not None:
        ten_mat_phu[ids[0]] = ten
    return set(ids)


#: Negation / exclusion anywhere in the sentence that requests the derived pyramid (review rounds 1–3).
_LOAI_TRU_YEU_CAU = re.compile(r"(?<!\w)(?:không|chẳng|chưa|đừng|khỏi|miễn|bỏ\s+qua|thay\s+vì|thay\s+cho|(?:ngoại\s+)?trừ)"
                               r"(?!\w)", re.IGNORECASE)

#: Closed positive lead-ins of the derived pyramid phrase within its clause: nothing (after "và" / "rồi" / ","), a request
#: verb, or the ratio / residual question openers that name it as an operand. Anything else is refused, never guessed.
_MO_KHOI_TREN_THIET_DIEN = re.compile(
    r"\s*(?:(?:hãy\s+)?(?:dựng|vẽ|xác\s+định|xét)(?:\s+(?:thêm|tiếp|cả|luôn))?\s*"
    r"|(?:(?:hãy\s+)?(?:tính|tìm|xác\s+định)\s+)?(?:tỉ|tỷ)\s+số\s+thể\s+tích\s+(?:của\s+|giữa\s+)?(?:hai\s+)?"
    r"|(?:hãy\s+)?(?:tính|tìm)\s+thể\s+tích\s+(?:của\s+)?phần\s+còn\s+lại\s+của\s+(?:khối|hình)\s+chóp\s+"
    r"(?-i:[A-Z][0-9]*'?\.(?:[A-Z][0-9]*'?)+)\s+sau\s+khi\s+cắt\s+(?:bỏ|đi)\s+)?", re.IGNORECASE)


def _canh_ben_khoi(calls: tuple[LoiGoi, ...], ten: str) -> tuple[str | None, list[tuple[str, str]]] | None:
    """(apex, lateral edges in base order) of the validated solid named `ten`; None when no such solid call."""
    for c in calls:
        if c.fn in ("pyramid", "regular_pyramid") and f"{c.args.apex}.{''.join(c.args.base)}" == ten:
            return c.args.apex, [(c.args.apex, b) for b in c.args.base]
        if c.fn == "prism" and f"{''.join(c.args.base)}.{''.join(c.args.top)}" == ten:
            return None, list(zip(c.args.base, c.args.top))
    return None


def _ham_giao_diem() -> str | None:
    """Name of the ONE Registry function whose planning contract meets a line with a plane (effect `Meet`), else None."""
    ten = [s.name for s in REGISTRY.values() for c in planning_contracts(s) if c.effect.kind == "Meet"]
    return ten[0] if len(ten) == 1 else None


def _kiem_dinh_cat(d: dict, mats: list[dict], theo_id: dict, de: str, nhan: set[str], chiem: set[str],
                   nhan_da_khai: set, calls: tuple[LoiGoi, ...], ten_mat_phu: dict | None, cat_doc: dict,
                   buoc: list[tuple[int, int]] | None) -> set[str]:
    """Declared `DINH_CAT_CANH` (run `typedfactnext-planner-bridge`): the cut certificate stands on a validated derived
    plane whose source definition is followed by THIS cut clause; each stated edge is a lateral edge of the cut solid; each
    vertex is either a call `intersect_line_plane(label, edge, plane)` sharing the plane's quotes — its label the name the
    source gives that cut, or fresh — or the plane's own through-point whose validated producer lies on that edge. A derived
    pyramid "khối chóp đỉnh S cắt bởi (α)" / "khối chóp S.MNP" covers every lateral edge, bound in closed wording. Only
    refuses; the engine checks every vertex on the built figure (0 < t ≤ 1).
    Run `hybrid-contract-v2` (D6): a `derived_fresh` vertex — on a lateral edge the source does NOT state, with a fresh
    label — is admitted only for a `/2` certificate (`derive`) whose section must close (a derived pyramid stands on it,
    or the author's declared boundary passes through that edge). It is never a source fact; the engine certifies closure."""
    ids = tuple(d.get("constructs") or ()) + ((d["derived"].get("call"),) if isinstance(d.get("derived"), dict) else ())
    mat = next((x for x in mats if x.get("goal") == d.get("plane_goal")), None)
    stated, ten = d.get("stated_edges") or [], d.get("stated_points") or []
    phai_khep = bool(d.get("derive")) and (isinstance(d.get("derived"), dict) or bool(d.get("declared_boundary")))
    bien = {frozenset(e) for e in d.get("declared_boundary") or ()}
    giao = _ham_giao_diem()
    if (mat is None or [mat.get("point"), *(mat.get("labels") or [])] != d.get("plane") or (not stated and not phai_khep)
            or mat.get("cut") != {"edges": stated, "points": ten} or tuple(d.get("quotes") or ()) != tuple(mat.get("quotes") or ())):
        raise TuChoi("AUXILIARY_RULE_MISMATCH", "đỉnh thiết diện: khai báo không đứng trên một mặt dẫn xuất đã kiểm", ids)
    if giao is None:
        raise TuChoi("UNSUPPORTED_CAPABILITY", "thư viện không có hàm dựng giao điểm đường–mặt cho đỉnh thiết diện", ids)
    if stated and not cat_doc.get(d.get("plane_goal")):
        raise TuChoi("SOURCE_OBJECT_MISMATCH", "đề không nêu mặt phẳng cắt các cạnh "
                     f"{', '.join(''.join(e) for e in stated)} ngay sau định nghĩa của nó", ids)
    khoi = _canh_ben_khoi(calls, d.get("solid"))
    if khoi is None:
        raise TuChoi("UNKNOWN_SOLID", f"đỉnh thiết diện: khối {d.get('solid')!r} không có lời gọi đã kiểm", ids)
    dinh, canh = khoi
    tap_canh = {frozenset(e) for e in canh}
    if any(frozenset(e) not in tap_canh for e in stated):
        raise TuChoi("SOURCE_OBJECT_MISMATCH", "cạnh đề nói bị cắt không phải cạnh bên của khối", ids)
    ten_canh = {frozenset(e): p for e, p in zip(stated, ten)}
    plane, qs = list(d["plane"]), tuple(d["quotes"])
    goi = {c for c in d.get("constructs") or ()}
    da_goi: set[str] = set()
    tren: dict[frozenset, str] = {}
    for v in d.get("vertices") or []:
        e, x, loai, cid = frozenset(v.get("edge") or ()), v.get("label"), v.get("choice"), v.get("call")
        if e not in tap_canh or e in tren or not isinstance(x, str):
            raise TuChoi("AUXILIARY_RULE_MISMATCH", "đỉnh thiết diện: cạnh lặp hoặc không phải cạnh bên", ids)
        if loai in ("named_intersection", "fresh_intersection", "derived_fresh"):
            c = theo_id.get(cid)
            if not (cid in goi and c is not None and c.fn == giao and c.args.point == x
                    and frozenset(c.args.line) == e and c.args.plane == plane and c.quotes == qs):
                raise TuChoi("AUXILIARY_RULE_MISMATCH", f"đỉnh thiết diện {x}: lời gọi không khớp luật {DINH_CAT_CANH}", ids)
            if loai == "named_intersection" and (x not in nhan or ten_canh.get(e) != x):
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"giao điểm {x} không phải tên đề đặt cho giao trên {''.join(sorted(e))}", ids)
            if loai == "derived_fresh":
                if e in ten_canh or not phai_khep or not (isinstance(d.get("derived"), dict) or e in bien):
                    raise TuChoi("AUXILIARY_RULE_MISMATCH", f"đỉnh dẫn xuất trên {''.join(sorted(e))}: cạnh đã được nêu, hoặc "
                                 "thiết diện không cần khép kín", ids)
                if x in nhan or x in chiem or x in nhan_da_khai or x not in (d.get("labels") or []):
                    raise TuChoi("AUXILIARY_LABEL_COLLISION", f"điểm dẫn xuất {x} trùng nhãn của đề hoặc đã khai", ids)
                nhan_da_khai.add(x)
            if loai == "fresh_intersection":
                if e not in ten_canh:                      # a fresh cut only on an edge the source states is cut
                    raise TuChoi("AUXILIARY_RULE_MISMATCH", f"giao mới trên {''.join(sorted(e))}: cạnh không được nêu là bị cắt",
                                 ids)
                if ten_canh[e]:
                    raise TuChoi("AUXILIARY_RULE_MISMATCH", f"đề đặt tên giao trên {''.join(sorted(e))}; không dùng nhãn phụ", ids)
                if x in chiem or x in nhan_da_khai or x not in (d.get("labels") or []):
                    raise TuChoi("AUXILIARY_LABEL_COLLISION", f"điểm phụ {x} trùng nhãn của đề hoặc đã khai", ids)
                nhan_da_khai.add(x)
            da_goi.add(cid)
        elif loai == "reuse_through_point":
            p = theo_id.get(v.get("producer")) if v.get("producer") else None
            if x != mat.get("point") or (p is None and x not in e) or (p is not None and not (
                    p.fn in ("midpoint", "divide_segment") and p.args.point == x and frozenset(p.args.segment) == e)):
                raise TuChoi("AUXILIARY_RULE_MISMATCH", f"đỉnh {x}: điểm qua của mặt không nằm trên {''.join(sorted(e))}", ids)
            if e in ten_canh and ten_canh[e] not in (None, x):
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"đề gọi giao trên {''.join(sorted(e))} là {ten_canh[e]}, không phải {x}", ids)
        elif loai == "reuse_intersection":
            c = theo_id.get(cid)
            if not (c is not None and c.fn == giao and c.args.point == x and frozenset(c.args.line) == e
                    and c.args.plane == plane):
                raise TuChoi("AUXILIARY_RULE_MISMATCH", f"đỉnh {x}: không có giao điểm đã dựng để dùng lại", ids)
        else:
            raise TuChoi("AUXILIARY_RULE_MISMATCH", f"đỉnh thiết diện: lựa chọn {loai!r} không có trong luật", ids)
        tren[e] = x
    if da_goi != goi or any(frozenset(e) not in tren for e in stated):
        raise TuChoi("AUXILIARY_RULE_MISMATCH", "đỉnh thiết diện: cạnh đề nói bị cắt chưa có đỉnh, hoặc lời gọi thừa", ids)
    kd = d.get("derived")
    if kd is None:
        return set(goi)
    c = theo_id.get(kd.get("call")) if isinstance(kd, dict) else None
    vong = [tren.get(frozenset(e)) for e in canh]
    if (c is None or dinh is None or c.fn != "pyramid" or c.args.apex != dinh or None in vong or c.args.base != vong
            or list(c.quotes) != list(kd.get("quotes") or ()) or len(set(vong)) < 3):
        raise TuChoi("AUXILIARY_RULE_MISMATCH", "khối trên thiết diện: lời gọi không phủ đúng mọi cạnh bên", (c.id,) if c else ids)
    ten_mat = (ten_mat_phu or {}).get((mat.get("constructs") or [None])[0])
    # named form: the derived pyramid's own symbol in a "(hai) khối chóp X(, Y) và Z" list — order is bound by the ask
    cum = [rf"(?:khối|hình)\s+chóp\s+(?:(?-i:[A-Z][0-9]*'?\.(?:[A-Z][0-9]*'?)+)\s*(?:,\s*|\s+và\s+))*"
           rf"(?-i:{re.escape(dinh)}\.{''.join(map(re.escape, vong))})(?![\w'])"] if set(vong) <= nhan else []
    if ten_mat:
        cum.append(rf"(?:khối|hình)\s+chóp\s+(?:đỉnh\s+)?(?-i:{re.escape(dinh)})\s+(?:được\s+)?(?:cắt(?:\s+ra)?\s+bởi|tạo\s+bởi|"
                   rf"giới\s+hạn\s+bởi)\s+(?:(?:mặt phẳng|mp)\s*)?\({re.escape(ten_mat)}\)")
        # the apex named AFTER the plane: "khối chóp cắt bởi (α) chứa đỉnh S" (run `hybrid-contract-v2`, D3)
        cum.append(rf"(?:khối|hình)\s+chóp\s+(?:được\s+)?(?:cắt(?:\s+ra)?\s+bởi|tạo\s+bởi)\s+(?:(?:mặt phẳng|mp)\s*)?"
                   rf"\({re.escape(ten_mat)}\)\s+(?:và\s+)?chứa\s+(?:đỉnh\s+)?(?-i:{re.escape(dinh)})(?![\w'])")
    khop = []
    for q in c.quotes:
        if (vt := _vi_tri(de, q)) is None:
            raise TuChoi("QUOTE_NOT_IN_SOURCE", f"{c.id}: đoạn {q!r} không có nguyên văn trong đề", (c.id,))
        for m in (m for r in cum for m in re.finditer(r, de[:vt[1]], re.IGNORECASE) if m.start() >= vt[0]):
            if _vai_tro_tai(de, m.start()) in ("GOAL", "CONDITIONAL") or _phu_dinh(de, m.start(), m[0]):
                raise TuChoi("UNSUPPORTED_CAPABILITY", f"{c.id}: khối trên thiết diện nằm trong điều kiện / chứng minh / phủ định",
                             (c.id,))
            # The clause leading to the phrase must be a CLOSED positive lead-in (a request verb, a ratio / residual question
            # opener, or nothing after a connector): "nhưng không dựng", "thay vì", "trừ" … are never read as a request
            # (review rounds 1–2; an open negation blacklist cannot be complete).
            dau = _cau_chua(de, m.start())
            menh_de = re.split(r"[,;:]|(?<!\w)(?:và|nhưng|rồi)(?!\w)", de[dau:m.start()], flags=re.IGNORECASE)[-1]
            # A negation may govern a list ("không dựng mặt đáy và khối chóp …", review round 3) or follow ("… hay
            # không?"): any negation / exclusion word in the whole sentence refuses (fail-closed).
            het = re.search(r"[.!?](?:\s|$)", de[m.end():])
            cau = de[dau:m.end() + (het.end() if het else len(de) - m.end())]
            if _LOAI_TRU_YEU_CAU.search(cau):
                raise TuChoi("NEGATED_CLAUSE", f"{c.id}: câu yêu cầu khối chóp trên thiết diện có từ phủ định / loại trừ",
                             (c.id,))
            if not _MO_KHOI_TREN_THIET_DIEN.fullmatch(menh_de):
                raise TuChoi("NEGATED_CLAUSE", f"{c.id}: mệnh đề trước khối chóp trên thiết diện không phải một yêu cầu "
                             f"khẳng định đã biết ({menh_de.strip()!r})", (c.id,))
            pure_build = bool(re.fullmatch(r"\s*(?:(?:hãy\s+)?(?:dựng|vẽ|xác\s+định|xét)(?:\s+(?:thêm|tiếp|cả|luôn))?\s*)?",
                                           menh_de, re.IGNORECASE))
            khop.append((m.start() - len(menh_de) if pure_build else m.start(), m.end()))
    if not khop:
        raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{c.id}: đề không gọi khối chóp đỉnh {dinh} trên thiết diện bởi mặt này", (c.id,))
    if buoc is not None:                                   # the request phrase is answered by this certified construction
        buoc.extend(khop)
    return set(goi) | {c.id}


_QUA_HAI_DUONG = re.compile(
    rf"(?:(?:mặt phẳng|mp)\s*)?\((?P<ten>{_P1}|[α-ω]'?)\)\s*(?:là\s+mặt phẳng\s+)?{_QUA_CHUA}"
    rf"(?P<diem>{_P1})(?![\w']){_DUOI_DIEM_QUA}{_NOI_QUAN_HE_MAT}song song\s+(?:với\s+)?"
    rf"(?:(?:cả\s+)?(?:hai|các)\s+(?:đường thẳng|cạnh)(?:\s+bên|\s+đáy)?\s+)?"
    rf"(?P<a>{_P1})\s*(?P<b>{_P1})(?![\w'])\s*(?:,\s*|\s+và\s+)\s*(?P<c>{_P1})\s*(?P<d>{_P1})(?![\w'])", re.I)
_DIEM_TRUOC_HAI_DUONG = re.compile(
    _DIEM_TRUOC + r"song song\s+(?:với\s+)?"
    rf"(?:(?:cả\s+)?(?:hai|các)\s+(?:đường thẳng|cạnh)(?:\s+bên|\s+đáy)?\s+)?"
    rf"(?P<a>{_P1})\s*(?P<b>{_P1})(?![\w'])\s*(?:,\s*|\s+và\s+)\s*(?P<c>{_P1})\s*(?P<d>{_P1})(?![\w'])", re.I)
_QUA_SONG_SONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _QUA_SONG_SONG.pattern)
_DIEM_TRUOC_SONG_SONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _DIEM_TRUOC_SONG_SONG.pattern)
#: "(P) đi qua A và vuông góc với SC" — a plane fixed by a verified point and a LINE (two labels; a plane after "vuông góc"
#: is not unique and never reaches here). Groups: ten, diem, l.
_QUA_VUONG_DUONG = re.compile(
    rf"(?:(?:mặt phẳng|mp)\s*)?(?:\((?P<ten>{_P1}|[α-ω]'?)\)\s*)?(?:là\s+mặt phẳng\s+)?{_QUA_CHUA}"
    rf"(?P<diem>{_P1})(?![\w']){_DUOI_DIEM_QUA}{_NOI_QUAN_HE_MAT}vuông góc\s+(?:với\s+)?"
    rf"(?:(?:đường thẳng|đường chéo|cạnh bên|cạnh đáy|đoạn thẳng|đoạn|cạnh)\s+)?"
    rf"(?<![\w'.(])(?P<l>{_P1}{_P1})(?![\w'])", re.IGNORECASE)
_DIEM_TRUOC_VUONG_DUONG = re.compile(
    _DIEM_TRUOC + rf"vuông góc\s+(?:với\s+)?(?:(?:đường thẳng|đường chéo|cạnh bên|cạnh đáy|đoạn thẳng|đoạn|cạnh)\s+)?"
    rf"(?<![\w'.(])(?P<l>{_P1}{_P1})(?![\w'])",
    re.IGNORECASE)
_DESC_DIEM_PHU_ANON = "|".join(
    re.sub(r"\(\?P<[^>]+>", "(?:", p.phrase).replace("{P}", _P1)
    for s in REGISTRY.values()
    for p in planning_contracts(s)
    if p.descriptor and isinstance(p.phrase, str)
)
_QUA_MO_TA_ANON = rf"(?:(?:đi\s+)?qua|chứa)\s+(?:điểm\s+là\s+)?(?:{_DESC_DIEM_PHU_ANON})"
_DT_MO_TA_PRE_TEN = (
    rf"{_QUA_MO_TA_ANON}\s*,?\s*(?:ta\s+)?(?:dựng|vẽ|kẻ|xét|lấy|gọi|cho|thiết\s+lập)?\s*"
    rf"(?:mặt phẳng|mp)?\s*\((?P<ten>{_P1}|[α-ω]'?)\)\s*(?:là\s+mặt phẳng\s+)?{_NOI_QUAN_HE_MAT}"
)
_TAIL_HAI_DUONG_ANON = (
    r"song song\s+(?:với\s+)?(?:(?:cả\s+)?(?:hai|các)\s+(?:đường thẳng|cạnh)(?:\s+bên|\s+đáy)?\s+)?"
    rf"{_P1}\s*{_P1}(?![\w'])\s*(?:,\s*|\s+và\s+)\s*{_P1}\s*{_P1}(?![\w'])"
)
_TAIL_VUONG_DUONG_ANON = (
    r"vuông góc\s+(?:với\s+)?(?:(?:đường thẳng|đường chéo|cạnh bên|cạnh đáy|đoạn thẳng|đoạn|cạnh)\s+)?"
    rf"(?<![\w'.(]){_P1}{_P1}(?![\w'])"
)
_TAIL_SONG_SONG_ANON = r"song song\s+(?:với\s+)?" + re.sub(r"(?<!\\)\((?!\?)", "(?:", _MAT_TOAN_HANG)
_ALL_DESC_PLANE_DEF_MAU = (
    re.compile(rf"(?:(?:mặt phẳng|mp)\s*)?(?:\((?P<ten>{_P1}|[α-ω]'?)\)\s*)?(?:là\s+mặt phẳng\s+)?{_QUA_MO_TA_ANON}{_NOI_QUAN_HE_MAT}(?:{_TAIL_SONG_SONG_ANON}|{_TAIL_VUONG_DUONG_ANON}|{_TAIL_HAI_DUONG_ANON})", re.I),
    re.compile(_DT_MO_TA_PRE_TEN + rf"(?:{_TAIL_SONG_SONG_ANON}|{_TAIL_VUONG_DUONG_ANON}|{_TAIL_HAI_DUONG_ANON})", re.I),
)
_QUA_DESC_SONG_SONG_ANON = rf"(?:(?:mặt phẳng|mp)\s*)?(?:\((?:{_P1}|[α-ω]'?)\)\s*)?(?:là\s+mặt phẳng\s+)?{_QUA_MO_TA_ANON}{_NOI_QUAN_HE_MAT}{_TAIL_SONG_SONG_ANON}"
_DT_DESC_SONG_SONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _DT_MO_TA_PRE_TEN) + _TAIL_SONG_SONG_ANON
_QUA_DESC_VUONG_DUONG_ANON = rf"(?:(?:mặt phẳng|mp)\s*)?(?:\((?:{_P1}|[α-ω]'?)\)\s*)?(?:là\s+mặt phẳng\s+)?{_QUA_MO_TA_ANON}{_NOI_QUAN_HE_MAT}{_TAIL_VUONG_DUONG_ANON}"
_DT_DESC_VUONG_DUONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _DT_MO_TA_PRE_TEN) + _TAIL_VUONG_DUONG_ANON
_QUA_DESC_HAI_DUONG_ANON = rf"(?:(?:mặt phẳng|mp)\s*)?\((?:{_P1}|[α-ω]'?)\)\s*(?:là\s+mặt phẳng\s+)?{_QUA_MO_TA_ANON}{_NOI_QUAN_HE_MAT}{_TAIL_HAI_DUONG_ANON}"
_DT_DESC_HAI_DUONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _DT_MO_TA_PRE_TEN) + _TAIL_HAI_DUONG_ANON
_ALL_PLANE_DEF_MAU = (
    _QUA_SONG_SONG,
    _DIEM_TRUOC_SONG_SONG,
    _QUA_VUONG_DUONG,
    _DIEM_TRUOC_VUONG_DUONG,
    _QUA_HAI_DUONG,
    _DIEM_TRUOC_HAI_DUONG,
)
_QUA_VUONG_DUONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _QUA_VUONG_DUONG.pattern) + "|" + _QUA_DESC_VUONG_DUONG_ANON
_DIEM_TRUOC_VUONG_DUONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _DIEM_TRUOC_VUONG_DUONG.pattern) + "|" + _DT_DESC_VUONG_DUONG_ANON
_QUA_HAI_DUONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _QUA_HAI_DUONG.pattern) + "|" + _QUA_DESC_HAI_DUONG_ANON
_DIEM_TRUOC_HAI_DUONG_ANON = re.sub(r"\(\?P<[^>]+>", "(?:", _DIEM_TRUOC_HAI_DUONG.pattern) + "|" + _DT_DESC_HAI_DUONG_ANON
_QUA_SONG_SONG_ANON = _QUA_SONG_SONG_ANON + "|" + _QUA_DESC_SONG_SONG_ANON
_DIEM_TRUOC_SONG_SONG_ANON = _DIEM_TRUOC_SONG_SONG_ANON + "|" + _DT_DESC_SONG_SONG_ANON
_KHOANG_CACH_GIAO_TUYEN = re.compile(
    rf"{_KC}\s+từ\s+(?:(?:điểm|đỉnh)\s+)?(?P<p>{_P1})(?![\w'])\s*(?:đến|tới)\s*"
    rf"giao tuyến\s+(?:của\s+)?(?P<a>{_MAT_TOAN_HANG})\s*(?:và|với)\s*(?P<b>{_MAT_TOAN_HANG})",
    re.IGNORECASE,
)
_CUM_HOI_THIET_DIEN_PHU = re.compile(
    rf"diện tích(?:\s+của)?\s+(?:{_td_mat_truoc_khoi(f'(?:{_P1}|[α-ω]\x27?)')}|{_DAN_THIET_DIEN}(?:{_QUA_SONG_SONG_ANON}|{_QUA_VUONG_DUONG_ANON}|{_QUA_HAI_DUONG_ANON}|(?:(?:mặt phẳng|mp)\s*)?\((?:{_P1}|[α-ω]'?)\))"
    rf"|thiết diện(?:\s+(?:là\s+)?(?:tam\s+giác|tứ\s+giác|đa\s+giác))?\s+(?-i:{_P1}){{3,}}(?![\w'])"
    rf"|nó(?![\w']))",
    re.IGNORECASE,
)
_CUM_DUNG_GIAO_TUYEN = re.compile(
    rf"(?:(?:hãy\s+)?(?:tìm|dựng|xác định)\s+|(?:gọi\s+)?[A-Za-z][A-Za-z0-9]*\s+là\s+){_GIAO_TUYEN.pattern}",
    re.IGNORECASE,
)
_CUM_DUNG_MAT_PHU = re.compile(
    rf"(?:(?:hãy\s+)?(?:gọi|cho|dựng|vẽ|kẻ|xét|thiết\s+lập|xác định|tìm)\s+)?(?:{_QUA_SONG_SONG_ANON}|{_DIEM_TRUOC_SONG_SONG_ANON}"
    rf"|{_QUA_HAI_DUONG_ANON}|{_DIEM_TRUOC_HAI_DUONG_ANON}|{_QUA_VUONG_DUONG_ANON}|{_DIEM_TRUOC_VUONG_DUONG_ANON})",
    re.IGNORECASE,
)
#: Optional solid lead-in in a multi-object construction request: "Dựng lăng trụ, thiết diện bởi (α) và tính …".
_MO_KHOI_DUNG = (rf"(?:(?:từng\s+bước\s+)?(?:hình|khối)?\s*(?:chóp(?:\s+(?:tứ|tam)\s+giác)?(?:\s+đều)?"
                 rf"|lăng\s+trụ(?:\s+(?:đứng|đều|tam\s+giác|tứ\s+giác))*|tứ\s+diện(?:\s+đều)?|hình\s+hộp(?:\s+chữ\s+nhật)?|"
                 rf"hình\s+lập\s+phương)(?:\s+{_NHAN}(?:\.{_NHAN})?)?\s*(?:,\s*|\s+và\s+))?")
_CUM_DUNG_THIET_DIEN_PHU = re.compile(
    rf"(?:(?:hãy\s+)?(?:xác định|tìm|dựng|vẽ)\s+{_MO_KHOI_DUNG}(?:{_td_mat_truoc_khoi(f'(?:{_P1}|[α-ω]\x27?)')}|{_DAN_THIET_DIEN}"
    rf"(?:{_QUA_SONG_SONG_ANON}|{_QUA_VUONG_DUONG_ANON}|{_QUA_HAI_DUONG_ANON}|(?:(?:mặt phẳng|mp)\s*)?\((?:{_P1}|[α-ω]'?)\))"
    rf"|thiết diện(?:\s+(?:là\s+)?(?:tam\s+giác|tứ\s+giác|đa\s+giác))?(?:\s+(?-i:{_P1}){{3,}}(?![\w']))?\s*(?:,\s*(?=(?:khối|hình)\s+chóp\b))?)"
    rf"|(?:(?:mặt phẳng|mp)\s*)?\((?:{_P1}|[α-ω]'?)\)\s+cắt\s+(?:hình|khối)(?:[^.;]|\.(?=[A-Z]))*?theo\s+(?:một\s+)?thiết diện)",
    re.IGNORECASE,
)


def _mat_hai_duong_dung_nguon(c: LoiGoi, point: str, lines: list[list[str]], name: str, de: str,
                            calls: tuple[LoiGoi, ...], don_vi_de: set[str] = frozenset(),
                            buoc: list[tuple[int, int]] | None = None) -> bool:
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
            if (symbols and symbols != {c.args.solid}) or not _cum_goi_khoi(m[0], c.args.solid, calls):
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
                if buoc is not None:
                    buoc.append(ask_m.span())
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
    return any(
        _tap_mat(m, 1, day) == frozenset(c.args.plane)
        and (bool(ky_hieu or _TU_LOAI.search(m[0])) or _chi_mot_khoi_3d(khoi, calls))
        and _cum_goi_khoi(m[0], c.args.solid, calls)
        for q in c.quotes for mau in _CAT_BOI for m in mau.finditer(q)
    )


_DIEM = r"[A-Z][0-9]*'?"
_DS_DIEM = rf"(?<![\w']){_DIEM}(?![\w'])(?:\s*(?:,|và)\s*(?<![\w']){_DIEM}(?![\w']))*"
_DOI_TUONG = (r"(?:(?i:cạnh(?:\s+(?:bên|đáy))?|đoạn(?:\s+thẳng)?|tam\s+giác|tứ\s+giác|đa\s+giác"
              r"|hình\s+(?:vuông|chữ\s+nhật|bình\s+hành|thoi)|mặt(?:\s+(?:bên|đáy))?)\s+|Δ\s*)?")
#: Start of a label group: not glued to a word nor to the "." of a solid symbol (the "ABC" of S.ABC is no subject), except
#: right after "Δ" (a letter, so `(?<![\w'.])` alone never matches it).
_DAU_NHAN = r"(?:(?<=Δ)|(?<![\w'.]))"
_DS_NHOM = (rf"{_DOI_TUONG}{_DAU_NHAN}(?:{_DIEM}){{2,}}(?![\w'])"
            rf"(?:\s*(?:,|và)\s*{_DOI_TUONG}{_DAU_NHAN}(?:{_DIEM}){{2,}}(?![\w']))*")
_CUE_DIEM = {"midpoint": r"(?i:trung\s+điểm)", "centroid": r"(?i:trọng\s+tâm)"}
#: Right angle of a named polygon: `ABC (là tam giác) vuông (cân) tại B`, `ABCD là hình thang vuông tại A và D`,
#: `góc ABC vuông`; the angle at X has its rays on X's two cyclic neighbours. An unlabelled `(đáy là) tam giác vuông tại B`
#: is resolved only when its subject is "đáy", by a unique named base of a solid; a face label in parentheses, "(SAB) là
#: tam giác vuông tại A", names that face (re-review C1 residual: a side face's right angle is never the base's).
#: Case-insensitive only for the words: labels stay upper-case, so "tam" or the length symbol "a" is never a label.
_HINH_VUONG_TAI = r"(?i:tam\s+giác|tứ\s+giác|hình\s+thang|hình\s+chữ\s+nhật)"
_VUONG_TAI = re.compile(rf"(?:{_DAU_NHAN}\(?((?:{_DIEM}){{3,}})\)?(?![\w'.])\s+(?:(?i:là)\s+(?:(?i:một)\s+)?)?(?:{_HINH_VUONG_TAI}\s+)?)?"
                        rf"(?i:vuông(?:\s+cân)?\s+(?:tại|ở))\s+({_DIEM}(?:\s*(?:,|(?i:và))\s*{_DIEM})*)(?![\w'])")
#: The base subject right before an unlabelled right polygon, read in the SOURCE up to the clause (a quote may hold only
#: "tam giác vuông tại B"): "đáy (ABC) là (một) tam giác …"; an optional label names the base itself. Whose base it is
#: comes from `_chu_cua_day`, never from "the only named solid".
_DAY_VUONG = re.compile(rf"(?<!\w)(?i:đáy)\s+(?:\(?((?:{_DIEM}){{3,}})\)?(?![\w'.])\s+)?(?:(?i:là)\s+)?(?:(?i:một)\s+)?"
                        rf"{_HINH_VUONG_TAI}\s+$")
_GOC_VUONG = re.compile(rf"(?i:góc)\s+(?<![\w'])((?:{_DIEM}){{3}})(?![\w'])\s+(?i:vuông|=\s*90|bằng\s+90)")


#: The only words allowed between a solid symbol and the unlabelled "đáy" it owns: "S.ABC (có) (chung) (mặt) đáy",
#: or "S.ABC. Đáy" (a closed list: a noun blacklist was open-ended, review rounds 4–5).
_SAU_KHOI_DEN_DAY = re.compile(r"\s*(?:(?i:có)\s+)?(?:(?i:chung)\s+)?(?:(?i:mặt)\s+)?")


def _chu_cua_day(truoc: str, dau_day: int) -> list[str] | None:
    """Base labels of the solid that owns the unlabelled word "đáy" at `dau_day`: the solid symbol directly before it
    (`_SAU_KHOI_DEN_DAY`). Any other wording (another object's base, "vuông góc với đáy", an intervening clause) has no
    certain owner ⇒ None (refused, not guessed)."""
    khoi = [(cuoi, p) for _d, cuoi, p in _tu_nhan(truoc[:dau_day]) if len(p) == 2]
    if not khoi or not _SAU_KHOI_DEN_DAY.fullmatch(truoc, khoi[-1][0], dau_day):
        return None
    p = khoi[-1][1]
    return p[1] if len(p[0]) == 1 else p[0]


def _dinh_nghia_diem_dung_nguon(c: LoiGoi, q: str, de: str) -> bool:
    """Bind a named derived point / right angle to the clause that defines it: `M, N lần lượt là trung điểm SB, SC` pairs
    in order (several names without `lần lượt` are refused), `G là trọng tâm tam giác ABC` / `trọng tâm G của tam giác
    ABC` binds G to exactly {A, B, C}; `tam giác ABC vuông tại B` binds the vertex and the triangle. A label merely
    appearing somewhere in the quote binds nothing."""
    a = c.args
    if c.fn == "right_angle":
        rays = frozenset(a.rays)

        def ke(poly):                      # the two cyclic neighbours of the right vertex in the named polygon
            i = poly.index(a.vertex)
            return frozenset((poly[i - 1], poly[(i + 1) % len(poly)]))
        for m in _GOC_VUONG.finditer(q):
            pts = re.findall(_DIEM, m[1])
            if pts[1] == a.vertex and frozenset((pts[0], pts[2])) == rays:
                return True
        for m in _VUONG_TAI.finditer(q):
            if a.vertex not in re.findall(_DIEM, m[2]):
                continue
            if m[1]:
                poly = re.findall(_DIEM, m[1])
            elif (vt := _vi_tri(de, q)) and (day := _DAY_VUONG.search(truoc := de[:vt[0]] + q[:m.start()])):
                # A labelled base ("đáy ABC là …") names its polygon; only an unlabelled one needs an owner.
                if day[1]:
                    poly = re.findall(_DIEM, day[1])
                elif (poly := _chu_cua_day(truoc, day.start())) is None:
                    continue
            else:
                continue
            if len(set(poly)) == len(poly) and a.vertex in poly and ke(poly) == rays:
                return True
        return False
    obj = a.segment if c.fn == "midpoint" else a.polygon
    cue = _CUE_DIEM[c.fn]
    forward = re.compile(rf"({_DS_DIEM})\s+((?i:lần\s+lượt)\s+)?(?i:là)\s+(?:(?i:các)\s+)?{cue}\s+(?:(?i:của)\s+)?(?:(?i:các)\s+)?({_DS_NHOM})")
    named = re.compile(rf"{cue}\s+(?<![\w'])({_DIEM})(?![\w'])\s+(?:(?i:của)\s+)?({_DS_NHOM})")
    def groups(s):
        return [re.findall(_DIEM, g) for g in re.findall(rf"{_DAU_NHAN}(?:{_DIEM}){{2,}}(?![\w'])", s)]
    for m in forward.finditer(q):
        names, objs = re.findall(_DIEM, m[1]), groups(m[3])
        if len(names) != len(objs) or (len(names) > 1 and not m[2]):
            continue
        for n, o in zip(names, objs):
            if n == a.point and len(o) == len(obj) and set(o) == set(obj):
                return True
    for m in named.finditer(q):
        objs = groups(m[2])
        if m[1] == a.point and len(objs) == 1 and len(objs[0]) == len(obj) and set(objs[0]) == set(obj):
            return True
    return False


#: "M (là điểm) thuộc / nằm trên (cạnh | đoạn (thẳng)) SA sao cho SM = 2MA" — one closed equation between two segments of
#: {X, Y, P}. Labels stay case-sensitive; the coefficient is a positive integer or fraction (absent = 1).
_TY_SO = re.compile(
    r"(?<![\w'])(?:(?P<p>[A-Z][0-9]*'?)(?![\w'])\s+(?:(?i:là)\s+(?:(?i:một)\s+)?(?i:điểm)\s+)?(?i:thuộc|nằm\s+trên|trên)\s+"
    r"(?:(?i:cạnh|đoạn\s+thẳng|đoạn)\s+)?(?P<x>[A-Z][0-9]*'?)(?P<y>[A-Z][0-9]*'?)(?![\w'])"
    r"|(?i:trên)\s+(?i:cạnh|đoạn\s+thẳng|đoạn)\s+(?P<ix>[A-Z][0-9]*'?)(?P<iy>[A-Z][0-9]*'?)(?![\w'])\s*,?\s+"
    rf"(?i:lấy|chọn)\s+(?:(?i:điểm)\s+)?(?P<ip>[A-Z][0-9]*'?)(?![\w']))\s*,?\s*{_NOI_TY_SO}\s+"
    r"(?P<l>(?:[A-Z][0-9]*'?){2})(?![\w'])\s*=\s*(?P<k>\d+(?:/\d+)?)?\s*(?P<r>(?:[A-Z][0-9]*'?){2})(?![\w'])")


def _ty_so_dung_nguon(c: LoiGoi, q: str) -> bool:
    """The ratio the source STATES, solved exactly for t = XP/XY on the segment it names, equals the call's
    (segment, ratio) — read in either direction ([X, Y], t) or ([Y, X], 1 − t): one point, one convention. Segment
    lengths in units of XY: XP = t, PY = 1 − t, XY = 1 (a + b·t); "L = k·R" ⇒ t = (k·a_R − a_L) / (b_L − k·b_R)."""
    return next(_ty_so_khop(c, chuan_hoa(q)), None) is not None


def _ty_so_khop(c: LoiGoi, s: str, pos: int = 0, endpos: int | None = None):
    """The `_TY_SO` matches in `s[pos:endpos]` that solve to the call's (segment, ratio) — `_ty_so_dung_nguon`'s reader,
    also used by premise coverage to own exactly the coefficient the equation read (run `typedfactnext-planner-bridge`)."""
    a = c.args
    for m in _TY_SO.finditer(s, pos, len(s) if endpos is None else endpos):
        p, x, y = m["p"] or m["ip"], m["x"] or m["ix"], m["y"] or m["iy"]
        if p != a.point or len({p, x, y}) != 3:
            continue
        he = {frozenset((x, p)): (Fraction(0), Fraction(1)), frozenset((p, y)): (Fraction(1), Fraction(-1)),
              frozenset((x, y)): (Fraction(1), Fraction(0))}
        doan = [frozenset(re.findall(r"[A-Z][0-9]*'?", m[g])) for g in ("l", "r")]
        if any(d not in he for d in doan):
            continue
        if re.fullmatch(r"\d+/0+", m["k"] or ""):          # "1/0" states no ratio: not this binding
            continue
        (al, bl), (ar, br), k = he[doan[0]], he[doan[1]], Fraction(m["k"] or 1)
        if bl == k * br:
            continue
        t = (k * ar - al) / (bl - k * br)
        if not 0 < t < 1:
            continue
        if (list(a.segment), Fraction(a.ratio)) in (([x, y], t), ([y, x], 1 - t)):
            yield m


def _ty_so_tron_cau(c: LoiGoi, s: str) -> bool:
    """The shared exact ratio reader consumes the whole premise, including its optional point introducer."""
    return any(re.fullmatch(r"\s*(?:(?:gọi|lấy|chọn|cho)\s+)?(?:điểm\s+)?", s[:m.start()], re.I)
               and re.fullmatch(r"[.\s]*", s[m.end():])
               for m in _ty_so_khop(c, s))


def _chan_duong_cao_dung_nguon(c: LoiGoi, q: str) -> bool:
    """An explicit plane altitude binds all three roles; a triangle/line or an unread tail binds nothing."""
    point = rf"(?P<src>{_DIEM})(?![\w'])"
    foot = rf"(?P<foot>{_DIEM})(?![\w'])"
    plane = rf"(?i:mặt\s+phẳng)\s*\((?P<plane>(?:{_DIEM}){{3,}})\)"
    source = rf"(?i:từ)\s+(?:(?i:điểm|đỉnh)\s+)?{point}\s+(?i:xuống|đến)\s+{plane}"
    altitude = rf"(?i:chân\s+đường\s+cao)\s+(?:(?i:hạ|kẻ)\s+)?{source}"
    forms = (rf"{foot}\s+(?i:là|trùng\s+với)\s+{altitude}",
             rf"{altitude}\s+(?i:là|trùng\s+với)\s+(?:(?P<noun>(?i:điểm|đỉnh))\s+)?{foot}",
             rf"(?i:hạ|kẻ)\s+(?i:đường\s+cao)\s+{source}\s+(?i:tại)\s+{foot}")
    for form in forms:
        m = re.fullmatch(rf"\s*(?:(?i:gọi|cho|biết|có)\s+)?{form}[.\s]*", chuan_hoa(q))
        if not m:
            continue
        vertices = re.findall(_DIEM, m['plane'])
        a = c.args
        if (m['src'] != a.point or m['foot'] != a.image or len(set(vertices)) != len(vertices)
                or set(vertices) != set(a.plane)):
            continue
        if (m.groupdict().get('noun') or '').lower() == 'đỉnh':
            owners = [_nhan_khoi(k) for k in _GOI_NGUON.get()
                      if k.fn in _KHOI_FN and {a.point, *vertices} <= _nhan_khoi(k)]
            if len(owners) != 1 or a.image not in owners[0]:
                continue
        return True
    return False


#: Role phrase of a curved dimension, then the value: "bán kính (đáy) (bằng | là | =) 3", "R = 3"; "chiều cao … 5", "h = 5".
_VAI_CONG = {"radius": r"(?:(?i:bán\s+kính)(?:\s+(?i:đáy))?|(?<![\w'])R(?![\w']))",
             "height": r"(?:(?i:chiều\s+cao)|(?<![\w'])h(?![\w']))"}


_L = r"[A-Z][0-9]*'?"
_SO_VB = r"(?P<v>(?:\d+(?:/\d+)?)?a?(?:√\d+)?(?:/\d+)?)(?![\w'√/])"
_KIEU_TU = r"(?:hình|khối|mặt)\s+(?P<k2>trụ|nón|cầu)"
#: The CLOSED clause grammar of a curved declaration (independent review rounds 1–2): the whole quote must parse into these
#: clauses after the kind word — an allowlist, so another solid, circle, plane, sector, triangle or an unread qualifier
#: ("… và gấp đôi bán kính") leaves words unread and binds nothing. Labels stay case-sensitive.
_CAU_CONG = tuple((vai, re.compile(mau, re.IGNORECASE)) for vai, mau in (
    ("pair", rf"tâm\s+(?:của\s+)?(?:hai|các)\s+đáy\s+(?:lần\s+lượt\s+)?là\s+(?-i:(?P<x>{_L}))\s+và\s+(?-i:(?P<y>{_L}))(?![\w'])"),
    ("pair", rf"(?:hai|các)\s+đáy\s+(?:lần\s+lượt\s+)?có\s+tâm\s+(?:(?:lần\s+lượt\s+)?là\s+)?(?-i:(?P<x>{_L}))\s+và\s+"
             rf"(?-i:(?P<y>{_L}))(?![\w'])"),
    # a cylinder's two named bases (registry /25): the lower one is the centre's, the upper one the top's
    ("lower", rf"(?:có\s+)?tâm\s+(?:của\s+)?(?:mặt\s+)?đáy\s+dưới\s+(?:là\s+)?(?-i:(?P<x>{_L}))(?![\w'])"),
    ("upper", rf"(?:có\s+)?tâm\s+(?:của\s+)?(?:mặt\s+)?đáy\s+trên\s+(?:là\s+)?(?-i:(?P<x>{_L}))(?![\w'])"),
    # ONE base named by its centre (registry /25): only a solid with a single base — on a cylinder it is ambiguous
    ("base_center", rf"(?:có\s+)?(?:tâm\s+(?:của\s+)?(?:mặt\s+)?đáy|đáy\s+có\s+tâm|đường\s+tròn\s+đáy\s+(?:có\s+)?tâm)\s+"
                    rf"(?:là\s+)?(?-i:(?P<x>{_L}))(?![\w'])"),
    ("center", rf"đáy\s+(?:là\s+)?(?:một\s+)?đường\s+tròn\s+tâm\s+(?-i:(?P<x>{_L}))(?![\w'])"),
    ("center_s", rf"(?:có\s+)?tâm\s+(?-i:(?P<x>{_L}))(?![\w'])"),
    ("apex", rf"(?:có\s+)?đỉnh\s+(?-i:(?P<x>{_L}))(?![\w'])"),
    ("rim", rf"(?:điểm\s+)?(?-i:(?P<x>{_L}))\s+(?:thuộc|nằm\s+trên|trên)\s+(?:(?P<day>đường\s+tròn\s+đáy)"
            rf"(?:\s+(?P<tang>dưới|trên))?(?:\s+tâm\s+(?-i:(?P<c>{_L}))|\s+\((?-i:(?P<c2>{_L}))\))?|(?P<cau>mặt\s+cầu))(?![\w'])"),
    ("radius", rf"(?:có\s+)?(?:bán\s+kính(?:\s+đáy)?(?:\s+(?-i:R))?|(?-i:R))(?:\s+của\s+{_KIEU_TU})?\s*(?:bằng\s+|là\s+|=\s*)"
               rf"{_SO_VB}"),
    ("height", rf"(?:có\s+)?(?:chiều\s+cao(?:\s+(?-i:h))?|(?-i:h))(?:\s+của\s+{_KIEU_TU})?\s*(?:bằng\s+|là\s+|=\s*){_SO_VB}"),
    # a dimension written as the segment that realises it (registry /25): "chiều cao SO = 15", "bán kính OB = 9"
    ("height_seg", rf"(?:có\s+)?chiều\s+cao\s+(?-i:(?P<p>{_L})(?P<q>{_L}))(?![\w'])\s*(?:bằng\s+|là\s+|=\s*){_SO_VB}"),
    ("radius_seg", rf"(?:có\s+)?bán\s+kính(?:\s+đáy)?\s+(?-i:(?P<p>{_L})(?P<q>{_L}))(?![\w'])\s*(?:bằng\s+|là\s+|=\s*){_SO_VB}"),
))
_MO_CONG = re.compile(rf"\s*(?:(?:cho|xét)\s+)?(?:một\s+)?(?:hình|khối|mặt)\s+(?P<k>trụ|nón|cầu)(?:\s+tròn\s+xoay)?"
                      rf"(?:\s+(?-i:(?P<n>\({_L}\)|{_L}(?:\.{_L})?)))?(?![\w'.])", re.IGNORECASE)
_NOI_CONG = re.compile(r"\s*(?:,\s*)?(?:(?:và|có|với)\s+)?", re.IGNORECASE)


def _doc_cau_cong(s: str) -> list[tuple[str, re.Match]] | None:
    """The quote as (role, match) clauses of `_CAU_CONG`, or None when ANY word is left unread."""
    m = _MO_CONG.match(s)
    if not m:
        return None
    out, pos = [("kind", m)], m.end()
    while True:
        pos = _NOI_CONG.match(s, pos).end()
        if not s[pos:].strip(" .;"):
            return out
        nxt = next(((vai, x) for vai, mau in _CAU_CONG if (x := mau.match(s, pos))), None)
        if nxt is None:
            return None
        out.append(nxt)
        pos = nxt[1].end()


_TEN_CAU_NT = r"(?-i:\([A-Z][0-9]*'?\))"


def _mau_cong_neo(pred_rx: str) -> tuple[re.Pattern, ...]:
    return (
        re.compile(
            rf"\s*(?:(?:cho|xét|gọi|biết(?:\s+rằng)?)\s+)?"
            rf"(?:(?P<n1>{_TEN_CAU_NT})\s+là\s+)?"
            rf"(?:hình|khối|mặt)\s+(?P<k>trụ|nón|cầu)(?:\s+tròn\s+xoay)?"
            rf"(?:\s+(?P<n2>{_TEN_CAU_NT}))?"
            rf"(?:\s+(?:có\s+)?tâm\s+(?:là\s+)?(?P<c>{_P1})(?![\w']))?"
            rf"{pred_rx}\s*[.;!]?\s*",
            re.IGNORECASE,
        ),
        re.compile(
            rf"\s*(?:(?:cho|gọi|biết(?:\s+rằng)?)\s+)?"
            rf"(?P<c>{_P1})(?![\w'])\s+là\s+tâm(?:\s+của)?\s+(?:hình|khối|mặt)\s+(?P<k>trụ|nón|cầu)(?:\s+tròn\s+xoay)?"
            rf"(?:\s+(?P<n2>{_TEN_CAU_NT}))?"
            rf"{pred_rx}\s*[.;!]?\s*",
            re.IGNORECASE,
        ),
        re.compile(
            rf"\s*(?:(?P<qverb>(?:hãy\s+)?(?:tính|tìm|xác\s+định))\s+)?"
            rf"(?:bán\s+kính|diện\s+tích(?:\s+xung\s+quanh|\s+toàn\s+phần)?|thể\s+tích)"
            rf"(?:\s+của)?\s+(?:hình|khối|mặt)\s+(?P<k>trụ|nón|cầu)(?:\s+tròn\s+xoay)?"
            rf"(?:\s+(?P<n2>{_TEN_CAU_NT}))?"
            rf"(?:\s+(?:có\s+)?tâm\s+(?:là\s+)?(?P<c>{_P1})(?![\w']))?"
            rf"{pred_rx}\s*[.;?!]?\s*",
            re.IGNORECASE,
        ),
    )


_CAU_CONG_NGOAI_TIEP = _mau_cong_neo(rf"\s+ngoại\s+tiếp{_host_cum('p')}(?:\s+đã\s+cho)?")
_CAU_CONG_NOI_TIEP = _mau_cong_neo(
    rf"\s+(?:nội\s+tiếp|tiếp\s+xúc\s+với\s+tất\s+cả\s+các\s+mặt\s+của){_host_cum('p')}(?:\s+đã\s+cho)?"
)
_CAU_TIEP_XUC_MAT = (
    re.compile(
        rf"\s*(?:(?:cho|gọi|biết(?:\s+rằng)?|có)\s+)?"
        rf"(?:hình|khối|mặt)\s+cầu(?:\s+(?P<n>{_TEN_CAU_NT}))?"
        rf"(?:\s+(?:có\s+)?tâm\s+(?:là\s+)?(?P<c>{_P1})(?![\w']))?"
        rf"\s+tiếp\s+xúc\s+(?:với\s+)?{_mat_cum('m')}"
        rf"(?:\s+tại(?:\s+(?:điểm|tiếp\s+điểm))?\s+(?P<pt>{_P1})(?![\w']))?\s*[.;!]?\s*",
        re.IGNORECASE,
    ),
    re.compile(
        rf"\s*(?:(?:cho|gọi|biết(?:\s+rằng)?)\s+)?"
        rf"(?P<pt>{_P1})(?![\w'])\s+là\s+tiếp\s+điểm(?:\s+của)?\s+"
        rf"(?:hình|khối|mặt)\s+cầu(?:\s+(?P<n>{_TEN_CAU_NT}))?"
        rf"(?:\s+(?:có\s+)?tâm\s+(?:là\s+)?(?P<c>{_P1})(?![\w']))?"
        rf"\s+(?:với|và)\s+{_mat_cum('m')}\s*[.;!]?\s*",
        re.IGNORECASE,
    ),
)


def _khoi_cong_neo_dung_nguon(
    c: LoiGoi, calls: tuple[LoiGoi, ...], kc: Any, host_solid: str, patterns: tuple[re.Pattern, ...]
) -> str | None:
    """Closed Source Gate binder for an axisless curved solid anchored via `circumscribes` or `inscribed_in`."""
    from ..geometry import curved as CV

    a = c.args
    if kc.co_truc or any(x is not None for x in (a.top, a.rim, a.radius, a.height)):
        return "SOURCE_OBJECT_MISMATCH"
    calls_ctx = calls or _GOI_NGUON.get()
    de_ctx = chuan_hoa(_DE_NGUON.get() or "")
    khoi_map = _khoi_cua_loi_goi(calls_ctx)
    curved_hosts = {
        k.args.solid for k in calls_ctx
        if k.fn == "curved_solid" and CV.KHOI_CONG[CV.LOAI_TU_NGUON[k.args.kind]].co_truc
    }
    if host_solid not in khoi_map and host_solid not in curved_hosts:
        return "UNKNOWN_SOLID"
    matches: list[re.Match] = []
    for q in c.quotes:
        s = chuan_hoa(q)
        m = next((pat.fullmatch(s) for pat in patterns if pat.fullmatch(s) is not None), None)
        if m is None:
            return "CURVED_WORDING_UNSUPPORTED"
        if m.re is patterns[2] and not m.groupdict().get("qverb") and de_ctx:
            vt = _vi_tri(de_ctx, q)
            if vt is None or not _duoc_hoi(de_ctx, vt[0], vt[1]):
                return "CURVED_WORDING_UNSUPPORTED"
        matches.append(m)
    written: set[str] = set()
    centers: set[str] = set()
    for m in matches:
        gd = m.groupdict()
        if _KIEU_CONG[gd["k"].lower()] != a.kind:
            return "SOURCE_OBJECT_MISMATCH"
        if not _host_khop(m, "p", host_solid, calls_ctx, khoi_map):
            return "SOURCE_OBJECT_MISMATCH"
        for key in ("n1", "n2"):
            if gd.get(key):
                written.add(gd[key])
        if gd.get("c"):
            centers.add(gd["c"])
    if len(written) > 1 or len(centers) > 1:
        return "SOURCE_OBJECT_MISMATCH"
    if (a.center is not None and centers != {a.center}) or (a.center is None and centers):
        return "SOURCE_OBJECT_MISMATCH"
    tag = f"({'out' if a.circumscribes is not None else 'in'}:{host_solid})"
    allowed = written if written else ({a.center, "()", f"({host_solid})", tag} if a.center else {"()", f"({host_solid})", tag})
    if a.solid not in allowed:
        return "SOURCE_OBJECT_MISMATCH"
    return None


def _tiep_xuc_mat_dung_nguon(c: LoiGoi, calls: tuple[LoiGoi, ...] = ()) -> str | None:
    """Closed Source Gate binder for `sphere_tangent_plane`."""
    from ..geometry import curved as CV

    calls_ctx = calls or _GOI_NGUON.get()
    khoi_map = _khoi_cua_loi_goi(calls_ctx)
    spheres = [
        k for k in calls_ctx
        if k.fn == "curved_solid" and not CV.KHOI_CONG[CV.LOAI_TU_NGUON[k.args.kind]].co_truc
    ]
    targets = [k for k in spheres if k.args.solid == c.args.solid]
    if len(targets) != 1:
        return "SOURCE_OBJECT_MISMATCH"
    sa = targets[0].args
    for q in c.quotes:
        s = chuan_hoa(q)
        m = next((pat.fullmatch(s) for pat in _CAU_TIEP_XUC_MAT if pat.fullmatch(s) is not None), None)
        if m is None:
            return "CURVED_WORDING_UNSUPPORTED"
        gd = m.groupdict()
        if gd.get("n") and gd["n"] != c.args.solid:
            return "SOURCE_OBJECT_MISMATCH"
        if gd.get("c") and gd["c"] != sa.center:
            return "SOURCE_OBJECT_MISMATCH"
        if not gd.get("n") and not gd.get("c") and len(spheres) != 1:
            return "SOURCE_OBJECT_MISMATCH"
        if not _cung_mat(_mat_cua(m, "m", khoi_map), c.args.plane):
            return "SOURCE_OBJECT_MISMATCH"
        if gd.get("pt") != c.args.point:
            return "SOURCE_OBJECT_MISMATCH"
    return None


def _khoi_cong_dung_nguon(c: LoiGoi, calls: tuple[LoiGoi, ...] = ()) -> str | None:
    """`None` when a `curved_solid` call is EXACTLY what its quote states, else the refusal code (registry /23; independent
    review rounds 1–2). The quote must parse COMPLETELY in the closed grammar `_CAU_CONG` (an allowlist, not a blacklist);
    per-kind facts come from `curved.KHOI_CONG`, never from a kind name.
    • one kind word, of this solid's kind; a notation, when the call carries "(X)" or a label form, must be the one written;
    • every named point is bound by its role clause — centre / top (the base-centre pair, either order), "đáy là đường tròn
      tâm O", "mặt cầu tâm O", "nón đỉnh S", the rim on THE base circle (a cylinder's rim names its own centre) or on the
      sphere; the notation agrees with the roles;
    • each stated dimension is the ONE value of its own role clause."""
    from app.simulation.geometry import curved as CV

    a = c.args
    kc = CV.KHOI_CONG[CV.LOAI_TU_NGUON[a.kind]]
    if a.circumscribes is not None:
        return _khoi_cong_neo_dung_nguon(c, calls, kc, a.circumscribes, _CAU_CONG_NGOAI_TIEP)
    if a.inscribed_in is not None:
        return _khoi_cong_neo_dung_nguon(c, calls, kc, a.inscribed_in, _CAU_CONG_NOI_TIEP)
    apex, two_bases = kc.vai_dinh == "đỉnh", kc.co_truc and kc.vai_dinh != "đỉnh"
    if a.center is not None and a.center == a.top:
        return "SOURCE_OBJECT_MISMATCH"          # one point as both centres / centre and apex: no solid (review 7, minor)
    if any(_doc_mat_cat(s) is not None or _CHIA_NON.fullmatch(s) for s in map(chuan_hoa, c.quotes)):
        return "SOURCE_OBJECT_MISMATCH"          # the solid's quote is a section sentence: a misquote (review 7, M4)
    cau = [_doc_cau_cong(chuan_hoa(q)) for q in c.quotes]
    if any(x is None for x in cau):          # wording the closed grammar does not read: a capability gap, not a
        return "CURVED_WORDING_UNSUPPORTED"   # claim that the source says something else (registered-controls audit)
    vals: dict[str, list] = {"radius": [], "height": []}
    bound: dict[str, set[str]] = {"center": set(), "top": set(), "rim": set()}
    rims: list[dict] = []
    duoi: set[str] = set()                         # centres named as the LOWER base ("tâm đáy dưới")
    for vai, m in (x for q in cau for x in q):
        g = m.groupdict()
        kieu = g.get("k") or g.get("k2")
        if kieu and _KIEU_CONG[kieu.lower()] != a.kind:
            return "SOURCE_OBJECT_MISMATCH"
        if vai == "kind" and g["n"] is not None and g["n"] != a.solid:
            return "SOURCE_OBJECT_MISMATCH"
        if vai == "pair" and two_bases and {g["x"], g["y"]} == {a.center, a.top}:
            bound["center"].add(a.center), bound["top"].add(a.top)
        elif vai in ("lower", "upper") and two_bases:
            bound["center" if vai == "lower" else "top"].add(g["x"])
            duoi |= {g["x"]} if vai == "lower" else set()
        elif vai == "base_center" and kc.co_truc:
            if two_bases:
                return "AMBIGUOUS_REFERENCE"       # "tâm đáy O" of a cylinder: which of its two bases?
            bound["center"].add(g["x"])
        elif vai in ("height_seg", "radius_seg"):
            want = {a.center, a.top} if vai == "height_seg" else {a.center, a.rim}
            if None in want or {g["p"], g["q"]} != want:
                return "SOURCE_OBJECT_MISMATCH"    # a segment that is not this solid's height / radius
            try:
                vals["height" if vai == "height_seg" else "radius"].append(doc_so(g["v"]))
            except TuChoi as e:
                return e.code
        elif vai == "center" and kc.co_truc:
            bound["center"].add(g["x"])
        elif vai == "center_s" and not kc.co_truc:
            bound["center"].add(g["x"])
        elif vai == "apex" and apex:
            bound["top"].add(g["x"])
        elif vai == "rim" and bool(g["day"]) == kc.co_truc:
            rims.append(g)                         # resolved once every clause is read (the lower base may come later)
        elif vai in vals:
            try:
                vals[vai].append(doc_so(g["v"]))
            except TuChoi as e:                    # keep the reader's own code ("bằng 0" ⇒ NON_POSITIVE_LENGTH)
                return e.code
        elif vai != "kind":
            return "SOURCE_OBJECT_MISMATCH"        # a clause of a role this kind does not have
    for g in rims:                                 # a rim lies on THE base whose centre is `center`
        c = g.get("c") or g.get("c2")
        tang = (g.get("tang") or "").lower() or None
        if two_bases:
            ok = (c == a.center and tang in (None, "dưới" if a.center in duoi else None)) or \
                 (c is None and tang == "dưới" and a.center in duoi)
        else:
            ok = tang is None and c in (None, a.center)
        if not ok:
            return "SOURCE_OBJECT_MISMATCH"      # a rim on another circle / the other base (review 7, M2)
        bound["rim"].add(g["x"])
    for f in bound:
        if (v := getattr(a, f)) is not None and bound[f] != {v}:
            return "SOURCE_OBJECT_MISMATCH"
    written = {g for q in cau for vai, m in q if vai == "kind" and (g := m["n"])}
    ten = (f"{a.top}.{a.center}" if apex else f"{a.center}.{a.top}") if kc.co_truc else a.center
    if a.solid != ten and a.solid not in written:
        return "SOURCE_OBJECT_MISMATCH"
    for f in vals:
        if len(set(vals[f])) > 1:
            return "INCONSISTENT_FACTS"            # the source states two different radii / heights of ONE solid
        if (v := getattr(a, f)) is not None and set(vals[f]) != {doc_so(v)}:
            return "UNGROUNDED_VALUE"
    return None


#: A plane's written name: a Latin label or a Greek letter — "(P)", "(α)", "(β)" (review 7: "(α)" was unreadable).
_TEN_MP = rf"(?:\s+\((?-i:(?P<mp>{_L}|[α-ω]))\))?"
#: The CLOSED grammar of a curved section sentence (an allowlist, like `_CAU_CONG`): the whole quote must parse.
_MO_MAT_CAT = (re.compile(rf"\s*(?:(?:cho|gọi)\s+)?(?:một\s+)?mặt\s+phẳng{_TEN_MP}", re.IGNORECASE),
               re.compile(rf"\s*cắt\s+(?:hình|khối|mặt)\s+(?P<k>trụ|nón|cầu)(?:\s+(?-i:(?P<n>{_L}(?:\.{_L})?)))?\s+bởi\s+(?:một\s+)?mặt\s+phẳng"
                          rf"{_TEN_MP}", re.IGNORECASE))
_CAU_MAT_CAT = tuple((vai, re.compile(mau, re.IGNORECASE)) for vai, mau in (
    ("parallel", r"song\s+song\s+với\s+(?:mặt\s+phẳng\s+)?(?:mặt\s+)?đáy(?![\w])"),
    ("distance", rf"cách\s+(?:mặt\s+phẳng\s+)?(?:mặt\s+)?đáy\s+(?:một\s+khoảng\s+)?(?:bằng\s+|là\s+)?{_SO_VB}"),
    ("midpoint", rf"(?:đi\s+)?qua\s+trung\s+điểm\s+(?:của\s+)?(?:đường\s+cao|đoạn(?:\s+thẳng)?)\s+(?-i:(?P<x>{_L})(?P<y>{_L}))(?![\w'])"),
    ("axial", r"(?:đi\s+)?qua\s+trục(?:\s+của\s+(?:hình|khối)\s+(?:trụ|nón))?(?![\w])"),
    # the general apex ratio (registry /25): "cắt (trục) SO tại M sao cho SM/SO = k" / "cắt trục SO theo tỉ lệ k tính từ đỉnh S"
    ("axis_point", rf"cắt\s+(?:trục\s+|đường\s+cao\s+)?(?-i:(?P<x>{_L})(?P<y>{_L}))(?![\w'])\s+tại\s+(?:điểm\s+)?"
                   rf"(?-i:(?P<m>{_L}))(?![\w'])\s+sao\s+cho\s+(?-i:(?P<a1>{_L})(?P<a2>{_L}))\s*/\s*"
                   rf"(?-i:(?P<b1>{_L})(?P<b2>{_L}))\s*=\s*(?P<k>\d+(?:/\d+)?)(?![\w'√/])"),
    ("axis_ratio", rf"cắt\s+(?:trục\s+|đường\s+cao\s+)?(?-i:(?P<x>{_L})(?P<y>{_L}))(?![\w'])\s+theo\s+tỉ\s+(?P<w>lệ|số)\s+"
                   rf"(?P<k>\d+(?:/\d+)?)(?![\w'√/])\s+(?:tính\s+)?từ\s+(?:đỉnh\s+|điểm\s+)?(?-i:(?P<z>{_L}))(?![\w'])"),
    ("cuts", r"cắt\s+(?:hình|khối|mặt)\s+(?P<k2>trụ|nón|cầu)(?:\s+theo\s+(?:một\s+)?(?P<shape>thiết\s+diện|đường\s+tròn|"
             r"hình\s+chữ\s+nhật|tam\s+giác(?:\s+cân)?)(?:\s+giao\s+tuyến)?)?(?![\w])"),
    # a sphere's plane, placed from its centre (seventh continuation): "cách tâm O một khoảng bằng d" / "(đi) qua tâm O"
    ("center_distance", rf"cách\s+tâm(?:\s+(?-i:(?P<c>{_L})))?(?![\w'])\s+(?:một\s+)?(?:khoảng\s+)?(?:bằng\s+|là\s+)?{_SO_VB}"),
    ("through_center", rf"(?:đi\s+)?qua\s+tâm(?:\s+(?-i:(?P<c>{_L})))?(?![\w'])"),
))
#: "Mặt phẳng (P) chia hình nón thành một khối nón nhỏ đỉnh S và một khối nón cụt" — the derived cone, closed form.
_CHIA_NON = re.compile(rf"\s*(?:(?:một\s+)?mặt\s+phẳng{_TEN_MP}\s+)?chia\s+(?:hình|khối)\s+nón(?:\s+(?-i:(?P<n>{_L}(?:\.{_L})?)))?\s+"
                       rf"thành\s+(?:hai\s+phần\s*:?\s*)?(?:một\s+)?khối\s+nón\s+nhỏ(?:\s+đỉnh\s+(?-i:(?P<apex>{_L})))?"
                       rf"\s+và\s+(?:một\s+)?(?:khối\s+nón\s+cụt|phần\s+còn\s+lại)\s*[.;]?\s*", re.IGNORECASE)


def _doc_mat_cat(s: str) -> tuple[re.Match, list[tuple[str, re.Match]]] | None:
    """The section sentence as (opener, [(role, match)]) — None when ANY word is left unread."""
    for mo in _MO_MAT_CAT:
        if (m := mo.match(s)) is None:
            continue
        out, pos = [], m.end()
        while True:
            pos = _NOI_CONG.match(s, pos).end()
            if not s[pos:].strip(" .;"):
                return m, out
            nxt = next(((vai, x) for vai, mau in _CAU_MAT_CAT if (x := mau.match(s, pos))), None)
            if nxt is None:
                break
            out.append(nxt)
            pos = nxt[1].end()
    return None


def _dau_cau(de: str, q: str) -> bool:
    """The quote starts a sentence or clause of the source (review B1): a quote cut mid-sentence ("… (Q) chia hình nón …"
    quoted from "chia") leaves the words before it unread by THIS call."""
    vt = _vi_tri(de, q)
    return vt is not None and re.search(r"(?:^|[.!?;:]\s*)$", de[:vt[0]].rstrip() + (" " if de[:vt[0]].strip() else "")) is not None


def _phan_cong_dung_nguon(c: LoiGoi, calls: tuple[LoiGoi, ...], de: str = "") -> str | None:
    """`None` when a curved section / derived cone call is EXACTLY what its quote states (registry /24), else a code.
    Section: the WHOLE sentence parses (`_doc_mat_cat`); a parallel section states "song song với đáy" and either its ONE
    distance from the BASE ("cách đáy", never "cách đỉnh") or "qua trung điểm của đường cao <apex><centre>" (ratio 1/2); an
    axial section states "qua trục" and nothing parallel; a written plane name and solid kind are this call's. Derived
    cone: "… chia hình nón thành một khối nón nhỏ (đỉnh S) và một khối nón cụt", the apex THE cone's apex, the cutting
    plane THE section's."""
    from app.simulation.geometry import curved as CV

    a = c.args
    solids = [k for k in calls if k.fn == "curved_solid" and k.args.solid == a.solid]
    if len(solids) != 1:
        return "UNKNOWN_SOLID"
    k = solids[0].args
    if de and not all(_dau_cau(de, q) for q in c.quotes):
        return "SOURCE_OBJECT_MISMATCH"
    s = " ".join(chuan_hoa(q) for q in c.quotes)
    if c.fn == "curved_subsolid":
        m = _CHIA_NON.fullmatch(s)
        if m is None:
            return "CURVED_WORDING_UNSUPPORTED"
        sec = next((x for x in calls if x.fn == "curved_section" and x.args.section == a.section), None)
        many = sum(x.fn == "curved_section" for x in calls) > 1
        if m is None or sec is None or a.apex != k.top or m["apex"] not in (None, a.apex) or m["n"] not in (None, a.solid) \
                or m["mp"] not in ((sec.args.plane,) if many else (None, sec.args.plane)):
            return "SOURCE_OBJECT_MISMATCH"      # with two sections, the derived cone must NAME its cutting plane
        return None
    if _doc_cau_cong(s) is not None:
        return "SOURCE_OBJECT_MISMATCH"          # the section's quote IS a solid sentence: a misquote (review 7, M4 / R2-M1)
    doc = _doc_mat_cat(s)
    if doc is None:
        return "CURVED_WORDING_UNSUPPORTED"
    mo, clauses = doc
    vai = [v for v, _m in clauses]
    kinds = [x for x in [mo.groupdict().get("k")] + [m.groupdict().get("k2") for _v, m in clauses] if x]
    kc = CV.KHOI_CONG[CV.LOAI_TU_NGUON[k.kind]]
    shapes = {" ".join(m["shape"].lower().split()) for v, m in clauses if v == "cuts" and m["shape"]}
    hop = ({"thiết diện", "đường tròn"} if a.kind != "axial_section" else
           {"thiết diện", "tam giác", "tam giác cân"} if kc.vai_dinh == "đỉnh" else {"thiết diện", "hình chữ nhật"})
    if (not kinds or any(_KIEU_CONG[x.lower()] != k.kind for x in kinds) or mo["mp"] not in (None, a.plane)
            or len(set(vai)) != len(vai) or (mo.groupdict().get("n") or a.solid) != a.solid or shapes - hop):
        return "SOURCE_OBJECT_MISMATCH"      # a shape word that contradicts the section kind is refused (review M2)
    tam = [(v, m) for v, m in clauses if v in ("center_distance", "through_center")]
    if a.kind in ("at_distance_from_center", "through_center"):
        want = "center_distance" if a.kind == "at_distance_from_center" else "through_center"
        if kc.co_truc or len(tam) != 1 or tam[0][0] != want or tam[0][1]["c"] not in (None, k.center) \
                or set(vai) - {want, "cuts"} or a.ratio is not None or a.point is not None:
            return "SOURCE_OBJECT_MISMATCH"      # the centre of THIS sphere, one placement, nothing about a base or an axis
        if a.kind == "through_center":
            return None if a.distance is None else "UNGROUNDED_VALUE"
        return None if a.distance is not None and doc_so(tam[0][1]["v"]) == doc_so(a.distance) else "UNGROUNDED_VALUE"
    if tam:
        return "SOURCE_OBJECT_MISMATCH"          # "cách tâm" places a sphere's plane, not a base-parallel one
    if a.kind == "axial_section":
        return None if "axial" in vai and not {"parallel", "distance", "midpoint"} & set(vai) else "SOURCE_OBJECT_MISMATCH"
    if "parallel" not in vai or "axial" in vai:
        return "SOURCE_OBJECT_MISMATCH"
    if a.kind == "parallel_to_base_at_distance":
        d = [doc_so(m["v"]) for v, m in clauses if v == "distance"]
        return None if "midpoint" not in vai and a.distance is not None and d == [doc_so(a.distance)] else "UNGROUNDED_VALUE"
    if None in (k.top, k.center) or "distance" in vai:
        return "SOURCE_OBJECT_MISMATCH"
    axis = {k.top, k.center}
    found = []                                      # (ratio from the apex, named point on the axis)
    for v, m in clauses:
        if v == "midpoint" and {m["x"], m["y"]} == axis:
            found.append((Fraction(1, 2), None))
        elif v in ("axis_point", "axis_ratio") and {m["x"], m["y"]} == axis:
            if v == "axis_ratio" and m["w"].lower() == "số":
                return "AMBIGUOUS_REFERENCE"         # "chia theo tỉ số k" reads SM/MO in textbooks (review 7, M5)
            try:
                kk = Fraction(m["k"])
            except ZeroDivisionError:
                return "SCHEMA_INVALID"              # a zero denominator (review 7, M1)
            if v == "axis_point":                   # XM / XY = k: X is the shared endpoint the ratio is measured from
                num, den = (m["a1"], m["a2"]), (m["b1"], m["b2"])
                frm = next((e for e in num if e in den and e in axis), None)
                if frm is None or {*num} != {frm, m["m"]} or {*den} != axis or m["m"] in axis:
                    return "SOURCE_OBJECT_MISMATCH"
                pt = m["m"]
            else:
                frm, pt = m["z"], None
                if frm not in axis:
                    return "SOURCE_OBJECT_MISMATCH"
            found.append((kk if frm == k.top else 1 - kk, pt))     # from the base centre: SI/SO = 1 − OI/OS
        elif v in ("midpoint", "axis_point", "axis_ratio"):
            return "SOURCE_OBJECT_MISMATCH"         # a ratio along a segment that is not THIS solid's axis
    if len(found) != 1:
        return "SOURCE_OBJECT_MISMATCH"
    kk, pt = found[0]
    if a.ratio is None or Fraction(a.ratio) != kk or a.point != pt:
        return "UNGROUNDED_VALUE"                   # the call's ratio / point is not the one the clause states
    return None


def _mat_cat_khop(a: Any) -> bool:
    """The question's "thiết diện" is THE one curved section of this run, of the asked solid."""
    secs = [x for x in _GOI_NGUON.get() if x.fn == "curved_section"]
    if len(secs) > 1 and any(x.args.section == a.section for x in secs):
        for x in secs:                           # an ungrounded section keeps its own source verdict (review 7, M3)
            if (code := _phan_cong_dung_nguon(x, _GOI_NGUON.get(), _DE_NGUON.get())) is not None:
                raise TuChoi(code, f"{x.id}: thiết diện {x.quotes[0]!r} không nêu đúng điều đề viết ({code}); câu hỏi "
                             "về thiết diện không được buộc trước khi mọi thiết diện khớp nguồn", (x.id,))
        # a capability gap, not a wrong object: the bounded binder reads "thiết diện" only when the run has ONE section
        raise TuChoi("CURVED_MULTI_SECTION_UNSUPPORTED", f"đề có {len(secs)} thiết diện của khối tròn xoay; câu hỏi "
                     "'thiết diện' chỉ được buộc khi đề có đúng một thiết diện", tuple(x.id for x in secs))
    return len(secs) == 1 and secs[0].args.section == a.section and secs[0].args.solid == a.solid


def _cap_khoi_khop(m: re.Match | None, a: Any, ratio: bool) -> bool:
    """A ratio question names its two cones IN ORDER ("khối nón nhỏ và khối nón ban đầu" ⇒ small : original), so an
    inverted call binds nothing; a remaining-volume question is (original, small cone). One cut only."""
    sub = [x for x in _GOI_NGUON.get() if x.fn == "curved_subsolid"]
    if len(sub) != 1:
        return False
    goc = next((x.id for x in _GOI_NGUON.get() if x.fn == "curved_solid" and x.args.solid == sub[0].args.solid), None)
    nho = sub[0].args.derived
    if not ratio:
        return (a.first, a.second) == (goc, nho)

    def ten(g: str) -> str | None:
        return nho if re.search(r"nhỏ", g, re.IGNORECASE) else goc      # "ban đầu" / "đã cho" / "lớn" name the original
    return (a.first, a.second) == (ten(m["a"]), ten(m["b"])) and a.first != a.second


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
    if c.fn in ("midpoint", "centroid", "right_angle"):
        return any(_dinh_nghia_diem_dung_nguon(c, q, de) for q in c.quotes)
    if c.fn == "divide_segment":
        return any(_ty_so_dung_nguon(c, q) for q in c.quotes)
    if c.fn == "orthogonal_projection" and _co_tu(c.quotes, ("chân đường cao", "hạ đường cao", "kẻ đường cao")):
        return any(_chan_duong_cao_dung_nguon(c, q) for q in c.quotes)
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
            # "H, K lần lượt là hình chiếu (vuông góc) của A trên SB, SC": ≥ 2 names only with "lần lượt", equal
            # counts, paired IN ORDER — the `_dinh_nghia_diem_dung_nguon` discipline for midpoints (registry /22)
            if c.fn == "orthogonal_projection_line":
                ds = rf"{point}(?:\s*(?:,|và)\s*{point})+"
                for m in re.finditer(rf"(?<![\w'])({ds})\s+lần lượt\s+là\s+(?:các\s+)?hình chiếu\s+(?:vuông góc\s+)?"
                                     rf"của\s+(?:(?:điểm|đỉnh)\s+)?({point})\s+(?:lên|trên)\s+(?:các\s+)?"
                                     rf"(?:(?:đường thẳng|cạnh)\s+)?({token}(?:\s*(?:,|và)\s*{token})+)(?![\w'])", q):
                    names, lines = labels(m[1]), re.findall(token, m[3])
                    if len(names) == len(lines) and m[2] == a.point and any(
                            n == a.image and labels(d) in (target, target[::-1]) for n, d in zip(names, lines)):
                        return True
            patterns = [rf"(?<![\w'])({point})\s+(?:là|trùng\s+với)\s+hình chiếu\s+(?:vuông góc\s+)?của\s+(?:(?:điểm|đỉnh)\s+)?({point})\s+(?:lên|trên)\s+{operand}(?![\w'])",
                        rf"[Hh]ình chiếu\s+(?:vuông góc\s+)?của\s+(?:(?:điểm|đỉnh)\s+)?({point})\s+(?:lên|trên)\s+{operand}\s+(?:là|trùng\s+với)\s+(?:(?P<noun>điểm|đỉnh|trọng tâm|trung điểm)\s+)?({point})(?![\w'])"]
            for i, pattern in enumerate(patterns):
                for m in re.finditer(pattern, q):
                    out, src, dst = m.groups() if i == 0 else (m[4], m[1], m[2])
                    pts = labels(dst)
                    if dst == "đáy" and len(target) >= 3:
                        bases = {tuple(p[1]) for dau, _cuoi, p in _tu_nhan(de) if len(p) == 2 and
                                 re.search(r"(?:chóp|lăng\s+trụ)\s*$", de[:dau], re.IGNORECASE)}
                        if len(bases) == 1 and _cung_da_giac(list(next(iter(bases))), target):
                            pts = target
                    if out == a.image and src == a.point and (pts == target or (len(target) == 2 and pts == target[::-1])):
                        if i == 1 and m["noun"] == "đỉnh":
                            owners = [_nhan_khoi(k) for k in _GOI_NGUON.get()
                                      if k.fn in _KHOI_FN and {src, *pts} <= _nhan_khoi(k)]
                            if len(owners) != 1 or out not in owners[0]:
                                continue
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


def _doc_nhom(s: str | None) -> tuple[Fraction, bool] | None:
    m = _SO.fullmatch(chuan_hoa(s)) if s else None
    return _doc(m) if m else None


def _cau_tien_de_dong_hop_le(s: str, s_start: int, de: str, calls: tuple[LoiGoi, ...], allow_single: bool = False) -> bool:
    """Verify that a compound premise span `s` parses completely in SG-3 (`_phan_tich_cau`) with zero opaque clauses
    and every clause is backed 1-to-1 by a validated call in `calls`."""
    cau = _phan_tich_cau(s)
    khoi_goi = [k for k in calls if k.fn in _KHOI_FN]
    if not cau or (not allow_single and len(cau) < 2) or any(k == "mo" for k, _m in cau) or not any(k != "khoi" for k, _m in cau) or not _so_dinh_cau_khop(cau, khoi_goi):
        return False
    khoi = khoi_goi[0] if len(khoi_goi) == 1 else None
    for kind, m in cau:
        if kind == "khoi":
            khop = [k for k in khoi_goi if _khop_ky_hieu_khoi(k, m["k"])]
            khoi = khop[0] if len(khop) == 1 else None
            tu = re.sub(r"\s+", " ", m["kn"].lower())
            km = _km_khoi(m)
            if khoi is None or khoi.fn not in _LOAI_KHOI.get(tu, ()):
                return False
            if ("đứng" in km or "chữ nhật" in km or "chữ nhật" in tu or tu == "lập phương") and khoi.fn == "prism" and not khoi.args.right:
                return False
            if "đều" in km:
                if tu in ("chóp", "tứ diện") and khoi.fn != "regular_pyramid":
                    return False
                if not any(d.fn == "regular_polygon" and _cung_da_giac(list(d.args.vertices), list(khoi.args.base)) for d in calls):
                    return False
            if ("chữ nhật" in km or "chữ nhật" in tu) and not any(d.fn == "rectangle" and _cung_da_giac(list(d.args.vertices), list(khoi.args.base)) for d in calls):
                return False
            if tu == "lập phương" and not any(d.fn == "regular_polygon" and len(d.args.vertices) == 4 and _cung_da_giac(list(d.args.vertices), list(khoi.args.base)) for d in calls):
                return False
        elif kind == "day":
            day_lbl = m["d"] or m["d2"]
            verts = re.findall(r"[A-Z][0-9]*'?", day_lbl) if day_lbl else (list(khoi.args.base) if khoi else [])
            if khoi is None or not verts or not _cung_da_giac(verts, list(khoi.args.base)):
                return False
            txt = re.sub(r"\s+", " ", m.group().lower())
            if "hình chữ nhật" in txt:
                if m["ds"] is not None or not any(d.fn == "rectangle" and _cung_da_giac(list(d.args.vertices), verts) for d in calls):
                    return False
            elif "hình vuông" in txt or "đều" in txt:
                matches = [d for d in calls if d.fn == "regular_polygon" and _cung_da_giac(list(d.args.vertices), verts)]
                if not matches:
                    return False
                if m["ds"] is not None:
                    want = _doc_nhom(m["ds"])
                    if want is None:
                        return False
                    if any(d.args.side is not None for d in matches) and not any(d.args.side is not None and doc_so(d.args.side) == want for d in matches):
                        raise TuChoi("UNGROUNDED_VALUE", f"{matches[0].id}: cạnh {matches[0].args.side} không phải số đo nguồn nêu cho khối", (matches[0].id,))
                    if not any(d.args.side is not None and doc_so(d.args.side) == want for d in matches) and not any(
                            v == want for seg in _canh_cua(verts) for v, _cid in _nguon_do_dai_cuc_bo(calls, list(seg))):
                        return False
            elif "vuông" in txt and "hình thang" not in txt:
                m_tai = re.search(rf"(?:tại|ở)\s+(?P<v>{_L1})(?![\w'])", m.group(), re.IGNORECASE)
                if m["ds"] is not None or not m_tai or len(verts) != 3 or m_tai["v"] not in verts:
                    return False
                v = m_tai["v"]
                rays = set(verts) - {v}
                if not any(d.fn == "right_angle" and d.args.vertex == v and set(d.args.rays) == rays for d in calls):
                    return False
                if "cân" in txt:
                    r1, r2 = list(rays)
                    s1, s2 = [v, r1], [v, r2]
                    eq_call = any(d.fn == "equal_length" and {frozenset(d.args.segment1), frozenset(d.args.segment2)} == {frozenset(s1), frozenset(s2)} for d in calls)
                    eq_val = bool({val for val, _ in _nguon_do_dai_cuc_bo(calls, s1)} & {val for val, _ in _nguon_do_dai_cuc_bo(calls, s2)})
                    if not (eq_call or eq_val):
                        return False
            else:
                return False
        elif kind == "dagiac":
            verts = re.findall(r"[A-Z][0-9]*'?", m["p"])
            matches = [d for d in calls if d.fn == "regular_polygon" and _cung_da_giac(list(d.args.vertices), verts)]
            want = _doc_nhom(m["ps"])
            if not matches or want is None:
                return False
            if not any(d.args.side is not None and doc_so(d.args.side) == want for d in matches):
                raise TuChoi("UNGROUNDED_VALUE", f"{matches[0].id}: cạnh {matches[0].args.side} không phải số đo nguồn nêu cho đa giác", (matches[0].id,))
        elif kind == "vuong":
            lhs, rhs = re.split(r"(?:vuông\s+góc\s+với|vuông|⊥)\s*", m.group(), maxsplit=1, flags=re.IGNORECASE)
            line = re.findall(r"[A-Z][0-9]*'?", lhs)
            if len(line) != 2:
                return False
            if re.search(r"(?<!\w)đáy(?!\w)", rhs, re.IGNORECASE):
                plane = list(khoi.args.base) if khoi else []
                if not plane or not any(d.fn == "perpendicular_line_plane" and set(d.args.line) == set(line) and _cung_mat(frozenset(plane), list(d.args.plane)) for d in calls):
                    return False
            elif m_two := re.fullmatch(rf"(?:mặt\s+phẳng\s+|mp\s*)?(?P<a>{_L1}{_L1})\s+và\s+(?P<b>{_L1}{_L1})", rhs.strip(), re.IGNORECASE):
                for g in ("a", "b"):
                    pts = re.findall(r"[A-Z][0-9]*'?", m_two[g])
                    if not any((d.fn == "perpendicular_lines" and {frozenset(d.args.line1), frozenset(d.args.line2)} == {frozenset(line), frozenset(pts)})
                               or (d.fn == "right_angle" and {frozenset((d.args.vertex, d.args.rays[0])), frozenset((d.args.vertex, d.args.rays[1]))} == {frozenset(line), frozenset(pts)})
                               for d in calls):
                        return False
            else:
                pts = re.findall(r"[A-Z][0-9]*'?", rhs)
                if len(pts) >= 3:
                    if not any(d.fn == "perpendicular_line_plane" and set(d.args.line) == set(line) and _cung_mat(frozenset(pts), list(d.args.plane)) for d in calls):
                        return False
                elif len(pts) == 2:
                    if not any((d.fn == "perpendicular_lines" and {frozenset(d.args.line1), frozenset(d.args.line2)} == {frozenset(line), frozenset(pts)})
                               or (d.fn == "right_angle" and {frozenset((d.args.vertex, d.args.rays[0])), frozenset((d.args.vertex, d.args.rays[1]))} == {frozenset(line), frozenset(pts)})
                               for d in calls):
                        return False
                else:
                    return False
        elif kind == "doan":
            if not _vai_doan_ok(m, khoi, calls):
                return False
            segs = [p for _x, _y, parts in _tu_nhan(m.group()[:m.start("ss") - m.start()]) for p in parts if len(p) == 2]
            want = _doc_nhom(m["ss"])
            if not segs or want is None:
                return False
            for seg in segs:
                cands = _nguon_do_dai_cuc_bo(calls, seg)
                if not cands:
                    return False
                if not any(v == want for v, _cid in cands):
                    raise TuChoi("UNGROUNDED_VALUE", f"{cands[0][1]}: độ dài {''.join(seg)} không khớp số đo nguồn", (cands[0][1],))
        elif kind == "vai":
            want = _doc_nhom(m["vs"])
            pos = s_start + m.start("vs")
            lk = _lien_ket_cau(de, s_start, s_start + len(s), calls)
            if want is None or pos not in lk:
                return False
            matched = [d for d in calls if _lien_ket_khop(d, lk[pos], calls)]
            vals = [doc_so(getattr(d.args, f)) for d in matched for f in d.spec.value_fields if getattr(d.args, f, None) is not None]
            if not matched or not vals:
                return False
            if want not in vals:
                raise TuChoi("UNGROUNDED_VALUE", f"{matched[0].id}: giá trị vai trò không khớp số đo nguồn", (matched[0].id,))
        elif kind == "diem":
            pt = re.findall(r"[A-Z][0-9]*'?", re.sub(r"^gọi\s+", "", m.group(), flags=re.I))[0]
            if not any(d.fn in ("midpoint", "centroid", "divide_segment", "intersect_line_line", "intersect_line_plane") and getattr(d.args, "point", None) == pt
                       and construction_source_bound(replace(d, quotes=(m.group(),)), de) for d in calls):
                return False
        elif kind == "chieu":
            proj = [d for d in calls if d.fn == "orthogonal_projection"
                    and construction_source_bound(replace(d, quotes=(m.group(),)), de)]
            if not proj:
                return False
            txt_c = re.sub(r"\s+", " ", m.group().lower())
            if "trung điểm" in txt_c and not any(
                    d.fn == "midpoint" and d.args.point == proj[0].args.image
                    and construction_source_bound(replace(d, quotes=(m.group(),)), de) for d in calls):
                return False
            if "trọng tâm" in txt_c and not any(
                    d.fn == "centroid" and d.args.point == proj[0].args.image
                    and construction_source_bound(replace(d, quotes=(m.group(),)), de) for d in calls):
                return False
        elif kind == "dcao":
            seg = re.findall(r"[A-Z][0-9]*'?", m.group())[:2]
            if len(seg) != 2 or khoi is None or not any(
                    (d.fn == "perpendicular_line_plane" and set(d.args.line) == set(seg) and set(d.args.plane) <= set(khoi.args.base))
                    or (d.fn == "altitude" and {d.args.apex, d.args.foot} == set(seg))
                    or (d.fn == "orthogonal_projection" and {d.args.point, d.args.image} == set(seg) and set(d.args.plane) <= set(khoi.args.base))
                    for d in calls):
                return False
        else:
            return False
    return True


def _kiem_nguon_dong(calls, de, phu, read_quotes):
    """Shared closed source subset: refusal only, never a second semantic authority."""
    # New-rule source subset: no proof/inference exemption and no compound quote may hide a second hypothesis.
    # This is a refusal in the SAME source authority, not an inferred fact or another semantic state.
    if read_quotes or _MO_MUC_TIEU.search(de):
        raise TuChoi('SOURCE_PREMISE_UNREAD','lát hai đường chưa nhận mệnh đề chứng minh/suy ra trong nguồn')
    intersection_form = (rf'(?:(?:tìm|dựng|xác định)\s+|gọi\s+[A-Za-z][A-Za-z0-9]*\s+là\s+)'
                         rf'giao tuyến của\s*{_MAT_TOAN_HANG}\s*và\s*{_MAT_TOAN_HANG}[.\s]*')
    # A cube premise expands to prism + square base + edge length, all quoting the one sentence (M4, run
    # `hybrid-semantic-grounding-reliability`; ISSUE-ARCH-LINE-REF-PREMISE-GRAMMAR-CUBE). Values stay bound by the gate.
    cube_form = (rf'(?:cho\s+)?(?:hình|khối)\s+lập phương\s+(?:{_P1})+\.(?:{_P1})+'
                 rf'(?:\s+(?:có\s+)?(?:độ dài\s+)?cạnh\s*(?:bằng|=)?\s*{_SO.pattern})?[.\s]*')
    for c in calls:
        if c.id in phu:
            continue
        for q in c.quotes:
            vt = _vi_tri(de, q)
            if vt:
                cs, ce = _bien_cau(de, vt[0])
                sent_raw = de[cs:ce]
                sent_s = sent_raw.strip()
                sent_start = cs + (len(sent_raw) - len(sent_raw.lstrip()))
                spans = ((q, vt[0]), (sent_s, sent_start))
            else:
                spans = ((q, 0),)
            if c.fn == 'intersection_line':
                if not all(re.fullmatch(intersection_form, s, re.I) for s, _st in spans):
                    raise TuChoi('SOURCE_PREMISE_UNREAD','quote giao tuyến có phần chưa được đọc',(c.id,))
                continue
            sent_ok = (
                vt is not None
                and c.spec.kind != 'ask'
                and not re.search(r'(?<!\w)(?:song|đổi|thay|gấp|nhân đôi|nhân ba)(?!\w)', re.sub(r'(?<!\w)song\s+song(?!\w)', ' ', sent_s, flags=re.I), re.I)
                and _cau_tien_de_dong_hop_le(sent_s, sent_start, de, calls, allow_single=True)
            )
            if sent_ok:
                continue
            for s, s_start in spans:
                if c.fn == 'divide_segment' and _ty_so_tron_cau(c, s):
                    continue
                if (c.fn == 'right_angle'
                        and re.fullmatch(rf'tam giác\s+(?:{_P1}){{3}}\s+vuông\s+tại\s+{_P1}[.\s]*', s, re.I)
                        and construction_source_bound(replace(c, quotes=(s,)), de)):
                    continue
                if c.fn in ('prism', 'regular_polygon', 'segment_length') and re.fullmatch(cube_form, s, re.I):
                    continue
                atomic = re.sub(r'(?<!\w)song\s+song(?!\w)',' ',s,flags=re.I)
                if re.search(r'(?<!\w)(?:song|đổi|thay|gấp|nhân đôi|nhân ba)(?!\w)',atomic,re.I):
                    raise TuChoi('SOURCE_PREMISE_UNREAD','quote tiền đề ghép chưa được đọc độc lập trên lát hai đường',(c.id,))
                if re.search(r'[,;]|(?<!\w)và(?!\w)',atomic,re.I):
                    if c.spec.kind != 'ask' and _cau_tien_de_dong_hop_le(s, s_start, de, calls, allow_single=True):
                        continue
                    raise TuChoi('SOURCE_PREMISE_UNREAD','quote tiền đề ghép chưa được đọc độc lập trên lát hai đường',(c.id,))
                if c.spec.kind != 'ask' and _cau_tien_de_dong_hop_le(s, s_start, de, calls, allow_single=True):
                    continue
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
                        'prism': rf'(?:cho\s+)?(?:hình\s+)?(?:lăng trụ(?:\s+(?:đứng|xiên))?|hình hộp chữ nhật)\s+{solid}[.\s]*',
                        'regular_polygon': rf'(?:đáy\s+{labels}\s+là\s+)?{shape}[.\s]*',
                        'rectangle': rf'(?:cho\s+)?(?:hình hộp chữ nhật\s+{solid}|(?:đáy\s+{labels}\s+là\s+)?hình chữ nhật\s*(?:{labels})?)[.\s]*',
                        'midpoint': rf'(?:gọi\s+)?{_P1}\s+là trung điểm\s+(?:của\s+)?(?:(?:cạnh|đoạn(?:\s+thẳng)?)\s+)?{_P1}{_P1}[.\s]*',
                    }
                    form = atomic_forms.get(c.fn)
                    if not ((form and re.fullmatch(form,s,re.I))
                            or c.fn in ('prism','regular_polygon') and re.fullmatch(prism,s,re.I)
                            or c.fn == 'regular_polygon' and re.fullmatch(reg_pyr,s,re.I)):
                        raise TuChoi('SOURCE_PREMISE_UNREAD','quote tiền đề chưa nằm trọn trong văn phạm lát hai đường',(c.id,))
    from ..semantic_program.shape_constraint import doc_rang_buoc
    from ..semantic_program.source_entities import dinh_danh_thuc_the
    def base_ok(d, c, assertion):
        kind = assertion.kind
        if d.fn != ('rectangle' if kind == 'cuboid' else 'regular_polygon') or d.args.vertices != c.args.base:
            return False
        # cube / cube_edge (M4): square base; the stated edge is the base side — (value², parameter) both compared (SG-2).
        # Same structure, other value: the call's value is not the source's — the value refusal, not an unread premise.
        if kind == 'cuboid' or (assertion.value is None and _gia_tri_rang_buoc(assertion, de) is None):
            return True
        if not _canh_khop(assertion, d.args.side, de):
            raise TuChoi('UNGROUNDED_VALUE', f'{d.id}: cạnh {d.args.side} không phải số đo nguồn nêu cho khối', (d.id,))
        return True
    for assertion in doc_rang_buoc(de):
        prism = assertion.kind in ('cuboid', 'cube', 'cube_edge') and any(
            c.fn == 'prism' and c.args.right
            and tuple(dinh_danh_thuc_the(n)[0] for n in c.args.base+c.args.top)==assertion.entities
            and any(base_ok(d, c, assertion) for d in calls)
            for c in calls)
        if not prism and not any(_rang_buoc_cuc_bo_khop(assertion, c, de) for c in calls):
            raise TuChoi('SOURCE_PREMISE_UNREAD','quan hệ nguồn chưa khớp lời gọi đã xác thực trên lát hai đường')
