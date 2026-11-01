# -*- coding: utf-8 -*-
"""NHÁNH B (thực nghiệm, run `hybrid-compiler-selection`): DỮ KIỆN CÓ KIỂU → PLANNER chọn và kết hợp hàm của REGISTRY.

    AI: trích dữ kiện (đối tượng, quan hệ, giá trị, vai trò mệnh đề, phủ định, nguồn) — KHÔNG chọn hàm
    planner (module này): kiểm dữ kiện → chọn hàm theo LOẠI + KIỂU toán hạng → mở rộng định nghĩa → lời gọi `{"calls": [...]}`
    sau đó: ĐÚNG đường của nhánh A — lược đồ → cổng nguồn → engine → IR → kernel → Scene3D (`app/ai/function_route.run_fact_route`)

Interface của module: `lap_ke_hoach(raw) -> KeHoach` (lời gọi, mục tiêu chứng minh, mệnh đề phủ định cần kiểm, trace) hoặc
`TuChoi` có mã. Không dựng hình, không tính toán hình học: phần ấy thuộc engine; planner chỉ quyết ĐỊNH GỌI GÌ.

─── VÌ SAO KHÔNG CÓ HỌ BÀI ─────────────────────────────────────────────────────
Mỗi loại dữ kiện có MỘT luật ánh xạ (bảng `_LUAT`), cộng mở rộng định nghĩa cho từ ngữ hình học chuẩn ("chóp đều", "lập phương",
"hình hộp chữ nhật", "tứ diện đều"). Không có luật nào nhìn vào tổ hợp dữ kiện để nhận dạng "dạng bài".

─── DỪNG VÀ GIỚI HẠN ─────────────────────────────────────────────────────────
Các dữ kiện tường minh vẫn ánh xạ một lần. Mục tiêu khoảng cách điểm–đường, và khoảng cách từ một điểm KHÔNG TÊN do đề mô tả
("trung điểm của SC") tới mặt / đường / giao tuyến, phân giải typed needs từ `PlanningContract` của Registry (`_EffectResolver`):
producer tìm theo hiệu ứng + kiểu toán hạng, lời gọi viết từ khuôn của contract — một hàm có contract được dùng mà planner
không cần nhánh riêng cho nó. Ngân sách hữu hạn, tái sử dụng producer đã khai; không tìm hình bằng số, suy tiền đề hoặc lấy
mẫu đáp số. Quá ngân sách ⇒ `PLAN_TOO_LARGE`, không phục vụ một phần.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, ValidationError, WithJsonSchema
from pydantic.json_schema import SkipJsonSchema

from .registry import AUXILIARY_RULES, DINH_CAT_CANH, MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG, ExactNumber, Label, TuChoi, chuan_hoa
from .registry import nhan_cua_de, nhan_phu_da_dung
from .registry import POINT_PRODUCERS, REGISTRY, doc_ke_hoach, goal_slots, parse_descriptor_inputs, planning_contract, planning_contracts, render_call, same_call

#: /8 (run `goal-directed-function-composition`): goal entry by typed slots (`_toan_hang_muc_tieu`), line partner operand.
#: /9 (run `geometry-capability-expansion`): `divide_segment` point_def, plane through a point ⊥ a line (`MAT_VUONG_DUONG`).
#: /10 (run `source-gate-hardening`): a `line_ref` producer may name a face by ≥ 3 distinct labels ((ABCD)).
#: /12 (run `typedfactnext-planner-bridge`): provider-hidden bridge fields; section vertices on stated cut edges (reuse /
#: named / fresh), derived pyramid over the section, solid operands by fact id.
#: /13 (run `hybrid-contract-v2`, owner D5/D6): section vertices through the Registry `Meet` contract (no hard-coded
#: producer); `/2`-only derived vertices on unstated lateral edges where a closed boundary is required; declared boundary.
#: /14 (run `hybrid-v2-backend-generalization`): a > 3-label question plane is handed to the engine in full
#: (`KeHoach.named_planes`, keyed by call id) instead of being cut to its first three labels.
#: /16 (run `hybrid-v2-planner-generalization`): `MAT_VUONG_DUONG` anchors on prisms (two layers: base/top), not only pyramids.
#: /17 (run `hybrid-v2-holdout-failure-repair`): M1 Greek/Latin `PlaneName` alignment, M2 single-solid height/altitude resolution,
#: M5 bounded section-area question binding (`diện tích của nó` and grounded named section polygons).
#: /18 (run `hybrid-v2-w3-f1-cross-sentence-plane-grounding`): propagate declared `plane_name` on all derived plane relations
#: (`MAT_SONG_SONG`, `MAT_VUONG_DUONG`, `MAT_HAI_DUONG`) and distinguish unasked section-area goals (`NOT_ASKED_IN_SOURCE`).
#: /21 (run `hybrid-master-backend-replacement`): a curved section carries the named point on the axis (`through_point`).
#: /22 (run `hybrid-master-backend-replacement`): composite geometry relations (`inscribed_in`, `sphere_tangent_plane`,
#: multi-sphere & axial-host composites) and explicit `composition_classification`.
#: /23 (run `hybrid-master-backend-replacement`): generalized unhinted `Point` descriptor resolution across goals and
#: auxiliary planes (`parse_descriptor_inputs`, `_EffectResolver.point`), premise-line `MAT_VUONG_DUONG` anchors, and
#: 3-way `search_telemetry` + `SEARCH_EXHAUSTED` budget telemetry.
#: /24 (run `hybrid-master-backend-replacement`, C16): `search_telemetry` classifies by step PROVENANCE recorded at emission
#: (`source_defined_steps` / `registered_decomposition_steps` / `search_generated_steps`); building a point the source
#: describes is no longer "discovered" (`route-b-composition-relabel.json`, `r1-composition-relabel.json`).
PLANNER_VERSION = "geometry-fact-planner/24"
PlaneName = Annotated[
    str,
    BeforeValidator(lambda v: chuan_hoa(v) if isinstance(v, str) else v),
    Field(pattern=r"^(?:[A-Z][0-9]*'?|[α-ω]'?)$", description="nhãn một điểm của đề, vd S, A, A'"),
]
#: Nhãn điểm phụ: chuỗi H, H1, H2, …; nhãn đầu tiên không có trong đề lẫn dữ kiện (Label của Registry không cho namespace
#: riêng mà không đổi bề mặt nhà cung cấp của A ⇒ "dành riêng" = chọn tươi + cổng kiểm `AUXILIARY_LABEL_COLLISION`).
def _nhan_tuoi(stem: str) -> tuple[str, ...]:
    return (stem, *(f"{stem}{i}" for i in range(1, 100)))


_NHAN_PHU = _nhan_tuoi("H")
MAX_CALLS = 64
#: Bound of the goal-directed decomposition `MAT_SONG_SONG`: derived planes per problem (each costs two auxiliary points).
MAX_DERIVED_PLANES = 4
MAX_EFFECT_DEPTH = 3
MAX_EFFECT_NEEDS = 32
MAX_EFFECT_CANDIDATES = 8
MAX_RESULT_LINES = 4
MAX_RESULT_FEET = 8

#: Point kinds the frozen `flat` provider surface offers (485d3834…). The planner accepts more (`TypedFact.point_kind`).
FLAT_POINT_KINDS = ("midpoint", "centroid", "intersect_line_line", "intersect_line_plane")
FLAT_QUANTITIES = ("volume", "area", "length", "distance", "angle")

FactKind = Literal["solid", "polygon_shape", "right_angle", "length", "equal_lengths", "perpendicular", "altitude",
                   "projection", "point_def", "section", "intersection_line", "question", "unsupported"]


class TypedFact(BaseModel):
    """MỘT dữ kiện có kiểu. Phẳng (một đối tượng, các ô theo `kind`) để lược đồ structured output của provider diễn đạt được."""

    model_config = ConfigDict(extra="forbid")
    id: str = Field(..., min_length=1)
    kind: FactKind
    role: Literal["premise", "prove", "condition", "question"] = Field(
        ..., description="premise = đề cho; prove = điều phải chứng minh; condition = trong 'nếu … thì'; question = đề hỏi")
    negated: bool = Field(False, description="mệnh đề bị phủ định trong đề")
    ambiguous: bool = Field(False, description="AI không chắc cách hiểu ⇒ planner từ chối, không đoán")
    quotes: Annotated[list[str], Field(min_length=1)] = Field(..., description="đoạn NGUYÊN VĂN của đề làm căn cứ")
    solid: str | None = Field(None, description="ký hiệu khối như đề viết: S.ABC, ABC.A'B'C', ABCD (tứ diện)")
    solid_type: Literal["pyramid", "prism", "tetrahedron", "cube", "cuboid"] | None = None
    regular: bool | None = Field(None, description="đề nói khối ĐỀU")
    right: bool | None = Field(None, description="đề nói lăng trụ ĐỨNG")
    points: list[Label] | None = Field(None, description="đỉnh đa giác / đoạn / mặt phẳng tuỳ loại")
    shape: Literal["equilateral_triangle", "square", "regular_hexagon", "regular_polygon", "rectangle", "triangle"] | None = None
    at: Label | None = Field(None, description="đỉnh góc vuông · ảnh hình chiếu")
    point: Label | None = None
    # The planner also accepts `divide_segment` (Wave 2B); the provider schema stays the frozen `flat` surface (owner
    # decision): a live `flat` extraction cannot emit it until that surface is re-measured (`FLAT_POINT_KINDS`).
    point_kind: Annotated[Literal["midpoint", "centroid", "intersect_line_line", "intersect_line_plane", "divide_segment",
                                  "orthogonal_projection", "orthogonal_projection_line"],
                          WithJsonSchema({"enum": list(FLAT_POINT_KINDS), "type": "string"})] | None = None
    value: ExactNumber | None = None
    measure: Literal["segment", "base_edge", "lateral_edge", "height", "edge"] | None = Field(
        None, description="độ dài này là của gì: một đoạn có tên, cạnh đáy, cạnh bên, chiều cao, mọi cạnh (lập phương, tứ diện đều)")
    points_a: list[Label] | None = Field(None, description="toán hạng 1: 1 điểm, 2 điểm = đường thẳng, ≥3 = mặt phẳng")
    points_b: list[Label] | None = Field(None, description="toán hạng 2")
    line_ref: str | None = Field(None, min_length=1, description="ID dữ kiện intersection_line có nguồn, cho distance/projection; không phải nhãn điểm hay chương trình")
    # the provider's flat quantities, plus the bridge-only ones (ratio / residual; curved lateral area and radius, /19)
    quantity: Annotated[Literal[*FLAT_QUANTITIES, "volume_ratio", "residual_volume", "lateral_area", "radius"],
                        WithJsonSchema({"enum": list(FLAT_QUANTITIES), "type": "string"})] | None = None
    plane_relation: Literal["parallel", "perpendicular", "parallel_two_lines"] | None = Field(
        None, description="thiết diện / diện tích thiết diện với mặt cắt cho bằng QUAN HỆ: mặt qua `point`, song song "
        "(parallel) hay vuông góc (perpendicular) với mặt `points_b`; khi đó không có `points`")
    plane_name: PlaneName | None = Field(None, description="tên mặt phẳng cắt trong đề; bắt buộc cho parallel_two_lines")
    reason: str | None = None
    # Internal only (run `typedfactnext-planner-bridge`): absent from every provider schema (`SkipJsonSchema`, frozen
    # fingerprints unchanged) and refused when a provider response carries them (`INTERNAL_FACT_FIELDS`). Written by the
    # TypedFactNext bridge: the edges a relation-plane section is stated to cut, the names the source gives those cuts
    # (aligned; None = unnamed), and the section a derived pyramid "khối chóp đỉnh S cắt bởi (α)" stands on.
    cut_edges: SkipJsonSchema[list[list[Label]] | None] = None
    cut_points: SkipJsonSchema[list[Label | None] | None] = None
    plane_ref: SkipJsonSchema[str | None] = None
    # Operands of a volume ratio / residual question as solid FACT ids (declared or derived), in the ordered roles the
    # question's quantity defines: (numerator, denominator) / (original, subtracted…).
    solid_refs: SkipJsonSchema[list[str] | None] = None
    # Internal only, written by the `typed-fact-next/2` bridge (run `hybrid-contract-v2`): `derive_cuts` lets the planner
    # derive the vertex on a lateral edge the source does not state (D6) where a closed boundary is required;
    # `boundary_edges` is an author-declared boundary (cyclic edges) the engine must verify, never trust.
    derive_cuts: SkipJsonSchema[bool | None] = None
    boundary_edges: SkipJsonSchema[list[list[Label]] | None] = None
    # Internal only (curved slice, planner /19): a solid of revolution's declaration — kind, centre / top / rim labels and
    # the stated radius / height — as the `typed-fact-next/2` bridge read it from one `SolidSpec`.
    curved: SkipJsonSchema[dict[str, Any] | None] = None
    # Internal only (planner /20): a section / the small cone / a goal of THE solid of revolution, as the bridge read it.
    curved_part: SkipJsonSchema[dict[str, Any] | None] = None


#: TypedFact fields only the deterministic bridge writes; a provider response carrying one is refused.
INTERNAL_FACT_FIELDS = ("cut_edges", "cut_points", "plane_ref", "solid_refs", "derive_cuts", "boundary_edges", "curved",
                        "curved_part")


@dataclass
class KeHoach:
    calls: list[dict[str, Any]] = field(default_factory=list)
    goals: list[dict[str, Any]] = field(default_factory=list)       # điều phải chứng minh: kiểm SAU khi dựng
    negated: list[dict[str, Any]] = field(default_factory=list)     # mệnh đề phủ định: phải SAI trên hình
    trace: list[dict[str, Any]] = field(default_factory=list)
    auxiliary: list[dict[str, Any]] = field(default_factory=list)  # điểm phụ do luật phân rã mục tiêu đưa vào (`_phan_ra`)
    taken: set[str] = field(default_factory=set)                    # nhãn của đề + của dữ kiện: điểm phụ không được trùng
    fact_ids: set[str] = field(default_factory=set)                 # id lời gọi điểm phụ không được trùng id dữ kiện
    heights: dict[str, str] = field(default_factory=dict)           # khối → id dữ kiện chiều cao (chẩn đoán tính duy nhất)
    volume_asks: dict[str, str] = field(default_factory=dict)       # id câu hỏi thể tích → khối
    solids: dict[str, "_Khoi"] = field(default_factory=dict)
    curved_solids: dict[str, TypedFact] = field(default_factory=dict)
    derived_planes: dict[tuple, dict] = field(default_factory=dict)  # (khối, điểm, mặt tham chiếu) → khai báo `MAT_SONG_SONG`
    # A question plane named by > 3 labels whose function slot takes three, `{"call": id, "labels": [...]}`: the engine
    # checks every label (`kiem_mat_viet`), measures through a non-collinear triple of them (`chon_ba_mat`) and shows the
    # full name — the call keeps the registry's three-label contract, nothing is dropped unchecked (review I-1).
    named_planes: list[dict[str, Any]] = field(default_factory=list)
    composition_classification: str = "SCHEMA_TRANSLATION"
    search_telemetry: dict[str, Any] = field(default_factory=dict)
    #: call id → source_defined (builds a point the source describes) | registered (a declared rule's step) |
    #: search_generated (a producer the effect search chose for a need neither describes); untagged planner calls are
    #: steps of a declared decomposition (`_mat_qua_diem`, `_mat_vuong_duong`, `_dinh_cat_canh`, curved composites)
    step_provenance: dict[str, str] = field(default_factory=dict)
    resolver: Any = field(default=None, repr=False)  # ephemeral view of existing calls; no geometry/semantic state


@dataclass
class _Khoi:
    ky_hieu: str                 # như đề viết
    ten: str                     # tên khối của engine (S.ABC · ABC.A'B'C' · D.ABC cho tứ diện ABCD)
    loai: str
    day: list[str]
    dinh: str | None = None
    tren: list[str] = field(default_factory=list)
    deu: bool = False
    dung: bool = False
    fact: str = ""
    quotes: list[str] = field(default_factory=list)
    kieu: str = ""               # solid_type như AI trích (tetrahedron · cube · cuboid · pyramid · prism)


def _nhan(s: str) -> list[str]:
    import re

    return re.findall(r"[A-Z][0-9]*'?", s)


def _doc_khoi(f: TypedFact) -> _Khoi:
    kh = _doc_khoi_tho(f)
    kh.kieu = f.solid_type or ""
    if f.negated:                    # "không phải là hình chóp đều S.ABC": khối vẫn có, tính ĐỀU bị phủ định ⇒ không dùng
        kh.deu = False
    return kh


def _doc_khoi_tho(f: TypedFact) -> _Khoi:
    s, t = (f.solid or "").replace("’", "'"), f.solid_type
    if t == "tetrahedron":
        p = _nhan(s)
        if len(p) != 4:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id}: tứ diện cần đúng 4 đỉnh", (f.id,))
        return _Khoi(s, f"{p[3]}.{''.join(p[:3])}", "pyramid", p[:3], dinh=p[3], deu=bool(f.regular), fact=f.id,
                     quotes=list(f.quotes))
    if "." not in s:
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: ký hiệu khối {s!r} không đọc được", (f.id,))
    a, b = s.split(".", 1)
    if t == "pyramid":
        if len(_nhan(a)) != 1:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id}: chóp phải có một đỉnh", (f.id,))
        return _Khoi(s, s, "pyramid", _nhan(b), dinh=_nhan(a)[0], deu=bool(f.regular), fact=f.id, quotes=list(f.quotes))
    day, tren = _nhan(a), _nhan(b)
    if len(day) != len(tren):
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: hai đáy lăng trụ khác số đỉnh", (f.id,))
    return _Khoi(s, s, t or "prism", day, tren=tren, deu=bool(f.regular),
                 dung=bool(f.right) or bool(f.regular) or t in ("cube", "cuboid"), fact=f.id, quotes=list(f.quotes))


_CAN = {"solid": ("solid", "solid_type"), "polygon_shape": ("points", "shape"), "right_angle": ("at", "points"),
        "length": ("value", "measure"), "equal_lengths": ("points_a", "points_b"), "perpendicular": ("points_a", "points_b"),
        "altitude": ("points",), "projection": ("point", "points", "at"), "point_def": ("point", "point_kind", "points"),
        "section": ("solid", "points"), "intersection_line": ("points_a", "points_b"),
        "question": ("quantity",), "unsupported": ("reason",)}
_DA_GIAC_DEU = {"equilateral_triangle": 3, "square": 4, "regular_hexagon": 6, "regular_polygon": None}


def doc_du_kien(raw: Any) -> list[TypedFact]:
    try:
        facts = [TypedFact.model_validate(f) for f in (raw or {}).get("facts") or []]
    except (ValidationError, AttributeError) as e:
        raise TuChoi("SCHEMA_INVALID", f"dữ kiện sai lược đồ: {e}") from None
    if not facts:
        raise TuChoi("SCHEMA_INVALID", "không có dữ kiện nào")
    if len({f.id for f in facts}) != len(facts):
        raise TuChoi("SCHEMA_INVALID", "id dữ kiện trùng")
    for f in facts:
        required = _CAN[f.kind]
        if f.kind == "question" and f.point_kind is not None and f.plane_relation is None:
            _doc_toan_hang_mo_ta(f)
        if f.line_ref is not None:
            if f.kind == "question" and f.quantity == "distance" and (len(f.points_a or []) == 1 or f.point_kind):
                if (f.points and not f.point_kind) or f.points_b or f.plane_relation:
                    raise TuChoi("SCHEMA_INVALID", f"{f.id}: line_ref thay cho toán hạng đường", (f.id,))
            elif f.kind == "projection" and not f.points and not f.points_a and not f.points_b:
                required = ("point", "at", "line_ref")
            else:
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: line_ref chỉ cho distance / projection", (f.id,))
        if f.curved is not None:                        # a solid of revolution: kind + centre, never a polyhedral type
            from app.simulation.geometry.curved import LOAI_TU_NGUON

            if (f.kind != "solid" or f.solid_type is not None or f.curved.get("kind") not in LOAI_TU_NGUON):
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: khối tròn xoay cần loại (trụ, nón, cầu)", (f.id,))
            required = ("solid",)
        if f.curved_part is not None:                   # a part / relation of a solid of revolution: owner + its own fields
            if f.curved_part.get("role") not in ("section", "derived", "ask", "tangent_plane") or f.points or f.solid_type:
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: phần của khối tròn xoay không hợp lệ", (f.id,))
            if f.curved_part.get("role") == "tangent_plane":
                pl = f.curved_part.get("plane") or []
                if len(pl) < 3 or len(set(pl)) != len(pl):
                    raise TuChoi("FACT_INCOMPLETE", f"{f.id}: mặt tiếp xúc cần ít nhất ba nhãn phân biệt", (f.id,))
            required = ("solid",)
        if f.kind == "point_def":
            if f.point_kind not in ("midpoint", "centroid", "intersect_line_line", "intersect_line_plane", "divide_segment"):
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: point_def không hỗ trợ point_kind={f.point_kind!r}", (f.id,))
            if f.point_kind in ("intersect_line_line", "intersect_line_plane"):
                required = ("point", "point_kind", "points_a", "points_b")
            elif f.point_kind == "divide_segment":       # the ratio t = AP/AB rides on `value`
                required = ("point", "point_kind", "points", "value")
        if f.plane_relation is not None:                # mặt cắt cho bằng quan hệ: điểm đi qua + mặt tham chiếu, không ba điểm
            if f.kind not in ("section", "question") or (f.points and f.point_kind is None) or (f.point and f.point_kind is not None):
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: plane_relation chỉ cho thiết diện, và thay cho `points`", (f.id,))
            if f.point_kind is not None:
                required = ("solid", "point_kind", "points", "points_b") + (("quantity",) if f.kind == "question" else ())
                dcs = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.descriptor == f.point_kind]
                if not dcs:
                    raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: không hàm nào của thư viện dựng được {f.point_kind}", (f.id,))
                if not any(parse_descriptor_inputs(c, f.points or ()) is not None for c in dcs):
                    raise TuChoi("FACT_INCOMPLETE", f"{f.id}: toán hạng của {f.point_kind} không hợp lệ", (f.id,))
            else:
                required = ("solid", "point", "points_b") + (("quantity",) if f.kind == "question" else ())
            if f.plane_relation == "parallel_two_lines":
                required += ("points_a", "plane_name")
                for line in (f.points_a, f.points_b):
                    if line is None or len(line) != 2:
                        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: mỗi đường cần đúng hai điểm đã định danh", (f.id,))
                    if len(set(line)) != 2:
                        raise TuChoi("DEGENERATE_LINE", f"{f.id}: hai đầu mút đường trùng nhau", (f.id,))
        if f.cut_edges is not None or f.cut_points is not None or f.derive_cuts or f.boundary_edges is not None:
            # an empty stated list is meaningful only with `derive_cuts` (`/2`); `/1` never writes one
            if (f.kind != "section" or f.plane_relation is None or f.cut_edges is None
                    or (not f.cut_edges and not f.derive_cuts)):
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: cạnh bị cắt chỉ cho thiết diện của mặt cho bằng quan hệ", (f.id,))
            vong = [frozenset(e) for e in f.boundary_edges or ()]
            if f.boundary_edges is not None and (len(vong) < 3 or len(set(vong)) != len(vong)
                                                 or any(len(e) != 2 for e in vong)):
                raise TuChoi("FACT_INCOMPLETE", f"{f.id}: biên khai báo là chu trình ≥ 3 cạnh phân biệt", (f.id,))
            canh = [frozenset(e) for e in f.cut_edges]
            if any(len(e) != 2 or len(set(e)) != 2 for e in f.cut_edges) or len(set(canh)) != len(canh):
                raise TuChoi("FACT_INCOMPLETE", f"{f.id}: mỗi cạnh bị cắt là hai đỉnh phân biệt, không lặp", (f.id,))
            ten = [p for p in f.cut_points or () if p]
            if f.cut_points is not None and (len(f.cut_points) != len(f.cut_edges) or len(set(ten)) != len(ten)):
                raise TuChoi("FACT_INCOMPLETE", f"{f.id}: tên giao điểm khớp từng cạnh bị cắt, không trùng", (f.id,))
        if f.plane_ref is not None:
            if f.kind != "solid" or f.solid_type != "pyramid" or f.solid or f.points:
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: plane_ref chỉ cho khối chóp dựng trên thiết diện (đỉnh ở `point`)",
                             (f.id,))
            required = ("point", "solid_type", "plane_ref")
        if f.solid_refs is not None:
            so = {"volume_ratio": (2, 2), "residual_volume": (2, 3)}.get(f.quantity or "")
            if (f.kind != "question" or so is None or not so[0] <= len(f.solid_refs) <= so[1]
                    or len(set(f.solid_refs)) != len(f.solid_refs) or f.solid or f.points or f.points_a or f.points_b):
                raise TuChoi("SCHEMA_INVALID", f"{f.id}: solid_refs chỉ cho tỉ số / thể tích còn lại, thay cho toán hạng điểm",
                             (f.id,))
        if thieu := [k for k in required if getattr(f, k) in (None, [])]:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id} ({f.kind}) thiếu {thieu}", (f.id,))
    by_id = {f.id: f for f in facts}
    for f in facts:
        if f.plane_ref is None:
            continue
        sec = by_id.get(f.plane_ref)
        if sec is None:
            raise TuChoi("UNKNOWN_DERIVED_REFERENCE", f"{f.id}: thiết diện {f.plane_ref!r} không tồn tại", (f.id,))
        if sec.kind != "section" or not (sec.cut_edges or (sec.cut_edges is not None and sec.derive_cuts)):
            raise TuChoi("DERIVED_REFERENCE_TYPE_MISMATCH", f"{f.id}: {sec.id} không phải thiết diện có cạnh bị cắt",
                         (f.id, sec.id))
        for obj in (f, sec):
            if obj.role in ("prove", "condition") or obj.negated:
                raise TuChoi("UNSUPPORTED_CAPABILITY", "khối dựng trên thiết diện chỉ từ giả thiết / yêu cầu khẳng định",
                             (obj.id,))
    for f in facts:
        if f.line_ref is None:
            continue
        producer = by_id.get(f.line_ref)
        if producer is None:
            raise TuChoi("UNKNOWN_DERIVED_REFERENCE", f"{f.id}: producer {f.line_ref!r} không tồn tại", (f.id,))
        if producer.kind != "intersection_line":
            raise TuChoi("DERIVED_REFERENCE_TYPE_MISMATCH", f"{f.id}: producer không sinh đường", (f.id, producer.id))
        for obj in (f, producer):
            if obj.role == "prove":
                raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", "reference không dùng mục tiêu chứng minh", (obj.id,))
            if obj.role == "condition":
                raise TuChoi("CONDITIONAL_CLAUSE", "reference không dùng điều kiện", (obj.id,))
            if obj.negated:
                raise TuChoi("NEGATED_CLAUSE", "reference không dùng phủ định", (obj.id,))
        # SG-6: a face may be named by all its vertices ((ABCD)); coplanarity is the engine's check (NON_COPLANAR_POINTS)
        if any(len(p or []) < 3 or len(set(p or [])) != len(p or []) for p in (producer.points_a, producer.points_b)):
            raise TuChoi("FACT_INCOMPLETE", "reference cần hai mặt, mỗi mặt ít nhất ba nhãn phân biệt", (producer.id,))
    return facts


def _doi_tac(contract) -> bool:
    """A goal contract whose measured object is a LINE through the described point and one named point (its partner,
    `points_a`), measured against a line or plane target — the only place a described question carries `points_a`."""
    kinds = [k for _s, k in goal_slots(contract)]
    return kinds[:2] == ["Point", "Point"] and any(k in ("Line", "Plane") for k in kinds[2:])


def _toan_hang_muc_tieu(f: TypedFact, contract) -> tuple | None:
    """Typed operands of a question on a DESCRIBED point for ONE goal contract, or None when the fact does not fill its
    slots. The described point fills the first slot; `points_a` (its named partner on a line, one label) the next Point
    slot; `points_b` the rest — one label per Point slot, exactly two labels for a Line slot, ≥ 3 for a Plane slot. Each
    list fills only the slots of its own operand: a position is never guessed inside a list."""
    dcs = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.descriptor == f.point_kind]
    parsed = next((r for c in dcs if (r := parse_descriptor_inputs(c, f.points or ())) is not None), None)
    if parsed is None:
        return None
    kinds = [k for _s, k in goal_slots(contract)]
    head = [("desc", f.point_kind, parsed[0])] + list(f.points_a or [])
    if len(head) >= len(kinds) or any(k != "Point" for k in kinds[:len(head)]):
        return None
    rest, b = kinds[len(head):], list(f.points_b or [])
    if len(set(b)) != len(b) or (f.points_a and not _doi_tac(contract)):
        return None
    if all(k == "Point" for k in rest):
        return (*head, *b) if len(b) == len(rest) else None
    if rest == ["Line"]:
        return (*head, ("named", tuple(sorted(b)))) if len(b) == 2 else None
    if rest == ["Plane"]:
        return (*head, tuple(b)) if len(b) >= 3 else None
    return None


def _doc_toan_hang_mo_ta(f: TypedFact) -> None:
    """A question whose first operand is a point the source DESCRIBES but does not name: `point_kind` + `points`, no
    `point`; `points_a` only as the named partner of a line through it. Which descriptions and goals exist, and the
    operands each goal takes, come from Registry contracts (`goal_slots`), not from a planner table."""
    goals = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.goal == f.quantity]
    if f.point or f.plane_relation or (f.points_a and not any(_doi_tac(c) for c in goals)):
        raise TuChoi("SCHEMA_INVALID", f"{f.id}: điểm không tên cần hợp đồng mục tiêu đã hỗ trợ "
                     "(point_kind + points; points_a chỉ là điểm thứ hai của một đường; không point)", (f.id,))
    if f.quantity != "distance" and not goals:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: chưa có hợp đồng mục tiêu cho {f.quantity} với điểm được mô tả", (f.id,))
    contracts = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.descriptor == f.point_kind]
    if not contracts:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: không hàm nào của thư viện dựng được {f.point_kind}", (f.id,))
    pts = f.points or []
    if not any(parse_descriptor_inputs(c, pts) is not None for c in contracts):
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: {f.point_kind} cần toán hạng phân biệt đúng kiểu hợp đồng", (f.id,))
    if goals:
        if f.line_ref or not any(_toan_hang_muc_tieu(f, c) for c in goals):
            raise TuChoi('FACT_INCOMPLETE', f'{f.id}: toán hạng của mục tiêu {f.quantity} không điền đúng ô của hợp đồng '
                         'mục tiêu nào (điểm đích phân biệt, đường hai điểm, mặt ≥ 3 điểm)', (f.id,))
    elif f.line_ref is None and len(set(f.points_b or [])) < 2:
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: thiếu đích của khoảng cách (đường, mặt hay line_ref)", (f.id,))


#: Question quantity on a solid of revolution → its ask (curved slice, planner /19).
_HOI_CONG = {"volume": "ask_curved_volume", "lateral_area": "ask_lateral_area", "area": "ask_surface_area",
             "radius": "ask_radius"}


#: A goal on a part of the solid of revolution → its ask (planner /20).
_HOI_PHAN_CONG = {"area": "ask_curved_section_area", "radius": "ask_curved_section_radius",
                  "volume_ratio": "ask_curved_volume_ratio", "residual_volume": "ask_curved_residual_volume"}


def _ke_hoach_cong(facts: list[TypedFact], k: KeHoach) -> KeHoach:
    """Standalone solid of revolution, or one axial host (`cylinder`/`cone`) with ≥ 1 anchored spheres (`circumscribes` /
    `inscribed_in`). Unanchored multi-curved or unsupported mixed facts are refused fail-closed."""
    unanchored = [f for f in facts if f.curved and not f.curved.get("circumscribes") and not f.curved.get("inscribed_in")]
    anchored = [f for f in facts if f.curved and (f.curved.get("circumscribes") or f.curved.get("inscribed_in"))]
    if len(unanchored) != 1:
        raise TuChoi("CURVED_RELATION_UNSUPPORTED", "chỉ hỗ trợ một khối tròn xoay gốc trên tuyến này",
                     tuple(f.id for f in facts if f.curved))
    s = unanchored[0]
    cv = s.curved

    def phat(fid: str, fn: str, args: dict, quotes: list[str], luat: str) -> None:
        k.calls.append({"id": fid, "fn": fn, "args": args, "source": {"quotes": list(dict.fromkeys(quotes))}})
        k.trace.append({"fact": fid, "rule": luat, "fn": fn, "call": fid})

    phat(s.id, "curved_solid", {"kind": cv["kind"], "solid": s.solid, "center": cv["center"], "top": cv.get("top"),
                                "rim": cv.get("rim"), "radius": cv.get("radius"), "height": cv.get("height")},
         s.quotes, f"solid({cv['kind']})→curved_solid")
    from app.simulation.geometry import curved as CV

    known_curved = {s.solid: s}
    host_kc = CV.KHOI_CONG[CV.LOAI_TU_NGUON[cv["kind"]]]
    for af in anchored:
        acv = af.curved
        akind = "circumscribes" if acv.get("circumscribes") else "inscribed_in"
        anch_kc = CV.KHOI_CONG[CV.LOAI_TU_NGUON[acv["kind"]]]
        if not host_kc.co_truc or anch_kc.co_truc or acv.get(akind) != s.solid:
            raise TuChoi("CURVED_RELATION_UNSUPPORTED", f"{af.id}: quan hệ {akind} chưa hỗ trợ cho {acv['kind']} trên {cv['kind']}",
                         (af.id,))
        if af.solid in known_curved:
            raise TuChoi("AMBIGUOUS_REFERENCE", f"{af.id}: ký hiệu khối cong {af.solid!r} bị trùng", (af.id,))
        known_curved[af.solid] = af
        phat(af.id, "curved_solid",
             {"kind": acv["kind"], "solid": af.solid, "center": acv.get("center"), "top": acv.get("top"),
              "rim": acv.get("rim"), "radius": acv.get("radius"), "height": acv.get("height"),
              akind: s.solid},
             af.quotes, f"solid({acv['kind']},{akind}={s.solid})→curved_solid")
    if anchored:
        k.composition_classification = "BOUNDED_RULE_COMPOSITION"
    for f in facts:
        if f is s or f in anchored:
            continue
        cp = f.curved_part or {}
        if cp.get("role") == "section" and not anchored:
            phat(f.id, "curved_section", {"solid": s.solid, "section": f.id, "kind": cp["kind"], "plane": cp.get("plane"),
                                          "distance": cp.get("distance"), "ratio": cp.get("ratio"),
                                          "point": cp.get("point")},
                 f.quotes, f"section({cp['kind']})→curved_section")
            k.composition_classification = "BOUNDED_RULE_COMPOSITION"
        elif cp.get("role") == "derived" and not anchored:
            phat(f.id, "curved_subsolid", {"solid": s.solid, "section": cp["section"], "derived": cp["derived"],
                                           "apex": cp["apex"]}, f.quotes, "derived_solid→curved_subsolid")
            k.composition_classification = "BOUNDED_RULE_COMPOSITION"
        elif cp.get("role") == "ask" and f.quantity in _HOI_PHAN_CONG and not anchored:
            fn = _HOI_PHAN_CONG[f.quantity]
            args = ({"solid": s.solid, "section": cp["section"]} if "section" in cp
                    else {"first": cp["pair"][0], "second": cp["pair"][1]})
            phat(f.id, fn, args, f.quotes, f"question({f.quantity})→{fn}")
        elif f.kind == "length" and f.measure == "segment" and f.points and f.value:
            phat(f.id, "segment_length", {"segment": f.points, "value": f.value}, f.quotes, "length(segment)→segment_length")
        elif f.kind == "question" and f.quantity in _HOI_CONG and f.solid in known_curved:
            phat(f.id, _HOI_CONG[f.quantity], {"solid": f.solid}, f.quotes, f"question({f.quantity})→{_HOI_CONG[f.quantity]}")
        else:
            raise TuChoi("CURVED_RELATION_UNSUPPORTED", f"{f.id}: dữ kiện {f.kind} chưa có quan hệ đã chứng nhận với khối "
                         "tròn xoay trên planner", (f.id,))
    k.search_telemetry = {
        "classification": (
            "REGISTERED_DECOMPOSITION"
            if k.composition_classification == "BOUNDED_RULE_COMPOSITION"
            else "SOURCE_EXPLICIT_SEQUENCE"
        ),
        "explored_states": 0,
        "candidate_evaluations": 0,
        "search_depth": 0,
        "reused_intermediates": 0,
        **_nguon_goc_buoc(k),
        "selected_functions": [c["fn"] for c in k.calls],
        "available_effects": sorted({pc.effect.kind for sp in REGISTRY.values() for pc in planning_contracts(sp)}),
        "search_budget": {
            "max_depth": MAX_EFFECT_DEPTH,
            "max_needs": MAX_EFFECT_NEEDS,
            "max_candidates": MAX_EFFECT_CANDIDATES,
            "max_fresh_points": MAX_RESULT_FEET,
            "max_calls": MAX_CALLS,
        },
    }
    return k


def lap_ke_hoach(raw: Any, problem_text: str = "") -> KeHoach:
    """Dữ kiện có kiểu → kế hoạch lời gọi. Từ chối (`TuChoi`) khi dữ kiện mơ hồ, có điều kiện, thiếu ô, hay không ánh xạ được.
    `problem_text` chỉ dùng để chọn nhãn điểm phụ không trùng đề (cổng nguồn kiểm lại độc lập)."""
    facts = doc_du_kien(raw)
    k = KeHoach()
    k.fact_ids = {f.id for f in facts}
    k.taken = (nhan_cua_de(problem_text) | nhan_phu_da_dung(problem_text) | {
        n for f in facts for v in (f.points, f.points_a, f.points_b, [f.at, f.point], _nhan(f.solid or ""),
                                   (f.curved_part or {}).get("plane"), [(f.curved_part or {}).get("point")])
        for n in (v or []) if n
    } | ({f.curved.get("center") for f in facts if f.curved} - {None}))
    if mo := [f.id for f in facts if f.ambiguous]:
        raise TuChoi("AMBIGUOUS_FACT", f"AI đánh dấu mơ hồ: {mo} — không đoán cách hiểu", tuple(mo))
    if dk := [f.id for f in facts if f.role == "condition"]:
        raise TuChoi("CONDITIONAL_CLAUSE", f"dữ kiện trong mệnh đề điều kiện {dk} — không phải giả thiết vô điều kiện", tuple(dk))
    has_poly = any(f.kind == "solid" and f.curved is None and f.role != "question" and f.plane_ref is None for f in facts)
    if not has_poly and any(f.curved for f in facts):
        return _ke_hoach_cong(facts, k)
    if any(f.curved and not f.curved.get("circumscribes") and not f.curved.get("inscribed_in") for f in facts):
        return _ke_hoach_cong(facts, k)
    for f in facts:
        if f.curved and (f.curved.get("circumscribes") or f.curved.get("inscribed_in")):
            if f.solid in k.curved_solids:
                raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: ký hiệu khối cong {f.solid!r} bị trùng", (f.id,))
            k.curved_solids[f.solid] = f
            continue
        if f.kind == "solid" and f.role != "question" and f.plane_ref is None:
            kh = _doc_khoi(f)
            k.solids[kh.ky_hieu] = kh
    ten = {s: kh.ten for s, kh in k.solids.items()} | {kh.ten: kh.ten for kh in k.solids.values()}
    deu: dict[frozenset, dict] = {}                                     # đáy → lời gọi regular_polygon (để gắn cạnh)

    def phat(fid: str, fn: str, args: dict, quotes: list[str], luat: str, dich: str = "calls") -> dict:
        c = {"id": fid, "fn": fn, "args": args, "source": {"quotes": list(dict.fromkeys(quotes))}}
        getattr(k, dich).append(c) if dich == "calls" else None
        k.trace.append({"fact": fid.split("_")[0], "rule": luat, "fn": fn, "call": fid})
        return c

    def khoi_cua(s: str | None, f: TypedFact) -> _Khoi:
        if not s and (f.kind == "altitude" or (f.kind == "length" and f.measure == "height")):
            if len(k.solids) == 1:
                return next(iter(k.solids.values()))
            if len(k.solids) > 1:
                raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: không nêu khối trong bài có nhiều khối", (f.id,))
        kh = k.solids.get(s or "") or next((x for x in k.solids.values() if x.ten == s), None)
        if kh is None:
            raise TuChoi("UNKNOWN_SOLID", f"{f.id}: khối {s!r} không có trong dữ kiện", (f.id,))
        return kh

    k.resolver = _EffectResolver(facts, k, phat, problem_text)

    # ── khối + mở rộng định nghĩa ───────────────────────────────────────────
    for kh in k.solids.values():
        if kh.loai == "pyramid":
            phat(kh.fact, "regular_pyramid" if kh.deu else "pyramid", {"apex": kh.dinh, "base": kh.day}, kh.quotes,
                 "solid→" + ("regular_pyramid (định nghĩa chóp đều)" if kh.deu else "pyramid"))
            if kh.deu:
                deu[frozenset(kh.day)] = phat(kh.fact + "_day", "regular_polygon", {"vertices": kh.day}, kh.quotes,
                                              "chóp đều ⇒ đáy đa giác đều")
        else:
            phat(kh.fact, "prism", {"base": kh.day, "top": kh.tren, "right": kh.dung}, kh.quotes,
                 f"solid({kh.loai})→prism (right={kh.dung})")
            if kh.deu or kh.loai == "cube":
                if kh.loai == "cube" and len(kh.day) != 4:
                    raise TuChoi("FACT_INCOMPLETE", f"{kh.fact}: lập phương cần đáy 4 đỉnh", (kh.fact,))
                deu[frozenset(kh.day)] = phat(kh.fact + "_day", "regular_polygon", {"vertices": kh.day}, kh.quotes,
                                              "lăng trụ đều / lập phương ⇒ đáy đa giác đều")
            elif kh.loai == "cuboid":
                phat(kh.fact + "_day", "rectangle", {"vertices": kh.day}, kh.quotes, "hình hộp chữ nhật ⇒ đáy hình chữ nhật")
    for sf in k.curved_solids.values():
        cv = sf.curved
        anchor_kind = "circumscribes" if cv.get("circumscribes") else "inscribed_in"
        poly_kh = khoi_cua(cv[anchor_kind], sf)
        phat(sf.id, "curved_solid",
             {"kind": cv["kind"], "solid": sf.solid, "center": cv.get("center"), "top": cv.get("top"),
              "rim": cv.get("rim"), "radius": cv.get("radius"), "height": cv.get("height"),
              anchor_kind: poly_kh.ten},
             sf.quotes, f"solid({cv['kind']},{anchor_kind}={poly_kh.ten})→curved_solid")

    # Bind all explicit producers before resolving goals, independently of provider order.
    def anh_xa(f: TypedFact) -> None:
        if f.kind == "solid" and (f.role != "question" or f.plane_ref is not None):
            return
        if f.role == "prove":
            c = _anh_xa(f, k, ten, deu, khoi_cua, lambda *a, **kw: phat(*a, **kw, dich="goals"))
            k.goals.append({"fact": f.id, "call": c})
            return
        if f.negated:
            c = _anh_xa(f, k, ten, deu, khoi_cua, lambda *a, **kw: phat(*a, **kw, dich="negated"))
            k.negated.append({"fact": f.id, "call": c})
            return
        _anh_xa(f, k, ten, deu, khoi_cua, phat)

    thu_tu = sorted(facts, key=lambda f: f.id)
    for f in thu_tu:
        if f.kind != "question":
            anh_xa(f)
    for f in thu_tu:                                      # derived pyramids stand on the sections just planned, and
        if f.plane_ref is not None:                       # questions may name them by their vertices
            _khoi_tren_thiet_dien(f, k, phat, khoi_cua)
    for f in thu_tu:
        if f.kind == "question":
            anh_xa(f)
    for f in facts:
        if f.kind == "length" and f.measure == "height" and f.role == "premise" and not f.negated:
            k.heights[khoi_cua(f.solid, f).ten] = f.id
    if len(k.calls) > MAX_CALLS:
        raise TuChoi("PLAN_TOO_LARGE", f"kế hoạch {len(k.calls)} lời gọi > trần {MAX_CALLS}")
    # Lời gọi y hệt (cùng hàm, cùng đối số) từ hai dữ kiện: giữ MỘT. Đa giác/khối gộp nguồn (từ khoá có thể ở quote kia);
    # độ dài giữ quote của lời gọi đầu (gộp có thể đưa hai số vào cùng một lời gọi). Câu hỏi không bao giờ gộp.
    gon: dict[str, dict] = {}
    for c in k.calls:
        # Referenced line declarations retain their IDs/quotes for Registry validation; Engine coalesces verified aliases.
        khoa = (c['id'] if c['fn'].startswith('ask_')
                or c['fn']=='intersection_line' and k.resolver.aliases.get(c['id'],c['id']) in k.resolver.lines else
                c['fn'] + json.dumps(c['args'],sort_keys=True,ensure_ascii=False))
        if khoa not in gon:
            gon[khoa] = c
        elif c["fn"] not in ("segment_length", "height"):
            gon[khoa]["source"]["quotes"] = list(dict.fromkeys(gon[khoa]["source"]["quotes"] + c["source"]["quotes"]))
    k.calls = list(gon.values())
    for c in k.calls:
        if c['fn']=='orthogonal_projection_line' and c['args'].get('line_ref') and c['id'] in k.fact_ids:
            k.auxiliary.append({'rule':'result-line-reference', 'consumer':c['id'], 'line_ref':c['args']['line_ref']})
            k.resolver.used = True
    for alias, canonical in k.resolver.aliases.items():
        if alias!=canonical and canonical in k.resolver.lines:
            k.auxiliary.append({'rule':'result-line-alias','producer':alias,'canonical':canonical,'line_ref':canonical})
    _sap_xep_phu_thuoc_loi_goi(k)
    if k.resolver.used:
        _bind_result_dependencies(k)
    k.composition_classification = (
        "GENERALIZED_PRIMITIVE_COMPOSITION"
        if k.resolver.used
        else "BOUNDED_RULE_COMPOSITION"
        if (k.derived_planes or k.curved_solids or len(k.solids) > 1 or any(c["fn"] == "sphere_tangent_plane" for c in k.calls))
        else "SCHEMA_TRANSLATION"
    )
    # C16: DISCOVERED only with a step the effect search chose for a need the source does not describe and no declared
    # rule supplies — before /24, building the point a question describes ("effect-chain", "point_chain") counted
    steps = _nguon_goc_buoc(k)
    has_registered_decomp = (
        bool(steps["registered_decomposition_steps"])
        or any(d.get("rule") != "effect-chain" for d in k.auxiliary)
        or bool(k.derived_planes)
        or bool(k.curved_solids)
        or len(k.solids) > 1
        or any(c["fn"] == "sphere_tangent_plane" for c in k.calls)
    )
    k.search_telemetry = {
        "classification": (
            "DISCOVERED_FUNCTION_COMPOSITION"
            if steps["search_generated_steps"]
            else "REGISTERED_DECOMPOSITION"
            if has_registered_decomp
            else "SOURCE_EXPLICIT_SEQUENCE"
        ),
        "explored_states": k.resolver.needs,
        "candidate_evaluations": k.resolver.candidates,
        "search_depth": k.resolver.depth_max,
        "reused_intermediates": k.resolver.reused,
        **steps,
        "selected_functions": [c["fn"] for c in k.calls],
        "available_effects": sorted({pc.effect.kind for s in REGISTRY.values() for pc in planning_contracts(s)}),
        "search_budget": {
            "max_depth": MAX_EFFECT_DEPTH,
            "max_needs": MAX_EFFECT_NEEDS,
            "max_candidates": MAX_EFFECT_CANDIDATES,
            "max_fresh_points": MAX_RESULT_FEET,
            "max_calls": MAX_CALLS,
        },
    }
    return k


_NON_POINT_ARG_KEYS = frozenset({
    "line_ref", "solid", "numerator_solid", "denominator_solid",
    "original_solid", "subtracted_solids", "value", "side", "reason", "right",
    "circumscribes", "inscribed_in", "kind", "radius", "height",
})


def _diem_cua_loi_goi(c: dict[str, Any]) -> list[str]:
    a = c.get("args") or {}
    pts: list[str] = []
    for key, val in a.items():
        if key in _NON_POINT_ARG_KEYS:
            continue
        if isinstance(val, list):
            pts.extend(x for x in val if isinstance(x, str))
        elif isinstance(val, str):
            pts.append(val)
    return pts


def _sap_xep_phu_thuoc_loi_goi(k: KeHoach) -> None:
    """Dependency-aware topological ordering over `k.calls` (`GAP-C1` / `ISSUE-RESEARCH-HYBRID-AUXILIARY-BEFORE-SOLID`).

    Builds an explicit directed dependency graph `prereq_id -> call_id`:
    - Data dependencies (`direct_deps`) from derived point producers (`midpoint`, `centroid`, `intersect_*`,
      `orthogonal_projection_line`, `translate_point`, and forward `orthogonal_projection`), `intersection_line`
      `line_ref` producers, sub-solids (`M.ABC`), and `section -> ask_section_area`.
    - Pedagogical foundation tiers (`Tier 0` root solid declarations -> `Tier 1` base foundation -> `Tier 2` apex-foot
      point constructors -> `Tier 3` apex/solid metric & perpendicularity premises -> `Tier 4` auxiliary point/line/
      section/sub-solid constructions -> `Tier 5` `ask_*` / `unsupported` queries).
    - Fail-closed rejection on dangling dependencies (`DANGLING_DEPENDENCY`) and cycles (`DEPENDENCY_CYCLE`).
    - Preserves `k.calls` in its exact original order whenever no dependency edge is violated.
    """
    import heapq

    calls = k.calls
    if not calls:
        return
    by_id = {c["id"]: c for c in calls}
    idx_of = {c["id"]: i for i, c in enumerate(calls)}

    raw_point_outputs: set[str] = set()
    for c in calls:
        fn, a = c["fn"], c.get("args") or {}
        if fn in POINT_PRODUCERS and isinstance(a.get("point"), str):
            raw_point_outputs.add(a["point"])
        elif fn in ("orthogonal_projection", "orthogonal_projection_line", "translate_point") and isinstance(a.get("image"), str):
            raw_point_outputs.add(a["image"])

    solids_list = list(k.solids.values())
    if solids_list:
        unproduced_solids = [
            kh
            for kh in solids_list
            if not ((set(kh.day) | ({kh.dinh} if kh.dinh else set()) | set(kh.tren)) & raw_point_outputs)
        ]
        root_solids = unproduced_solids if unproduced_solids else [solids_list[0]]
    else:
        root_solids = []

    base_vertices = {v for kh in root_solids for v in kh.day}
    apex_vertices = {kh.dinh for kh in root_solids if kh.dinh} | {v for kh in root_solids for v in kh.tren}
    solid_vertices = base_vertices | apex_vertices
    root_solid_call_ids = {kh.fact for kh in root_solids}

    explicit_point_producers: dict[str, list[str]] = {}
    for c in calls:
        fn, a = c["fn"], c.get("args") or {}
        if fn in POINT_PRODUCERS and isinstance(a.get("point"), str):
            pt = a["point"]
            if pt not in solid_vertices:
                explicit_point_producers.setdefault(pt, []).append(c["id"])
        elif fn in ("orthogonal_projection_line", "translate_point") and isinstance(a.get("image"), str):
            pt = a["image"]
            if pt not in solid_vertices:
                explicit_point_producers.setdefault(pt, []).append(c["id"])

    point_producers: dict[str, list[str]] = {p: list(ids) for p, ids in explicit_point_producers.items()}
    produced_point_of_call: dict[str, str] = {
        cid: pt for pt, cids in explicit_point_producers.items() for cid in cids
    }
    for c in calls:
        fn, a = c["fn"], c.get("args") or {}
        if fn == "orthogonal_projection" and isinstance(a.get("image"), str):
            pt = a["image"]
            is_apex_foot_proj = (
                a.get("point") in apex_vertices
                and set(a.get("plane") or ()) <= base_vertices
                and (pt in base_vertices or pt in explicit_point_producers)
            )
            if not is_apex_foot_proj and pt not in solid_vertices:
                point_producers.setdefault(pt, []).append(c["id"])
                produced_point_of_call[c["id"]] = pt
        elif fn == "curved_solid" and isinstance(a.get("center"), str):
            pt = a["center"]
            if pt not in solid_vertices and pt not in explicit_point_producers:
                point_producers.setdefault(pt, []).append(c["id"])
                produced_point_of_call[c["id"]] = pt
        elif fn == "sphere_tangent_plane" and isinstance(a.get("point"), str):
            pt = a["point"]
            if pt not in solid_vertices and pt not in explicit_point_producers:
                point_producers.setdefault(pt, []).append(c["id"])
                produced_point_of_call[c["id"]] = pt

    direct_deps: dict[str, set[str]] = {c["id"]: set() for c in calls}
    consumed_points_of_call: dict[str, list[str]] = {}
    for c in calls:
        cid, fn, a = c["id"], c["fn"], c.get("args") or {}
        out_pt = produced_point_of_call.get(cid)
        pts = [p for p in _diem_cua_loi_goi(c) if p != out_pt]
        consumed_points_of_call[cid] = pts
        for pt in pts:
            for p_cid in point_producers.get(pt, ()):
                if p_cid != cid:
                    direct_deps[cid].add(p_cid)
        if a.get("line_ref"):
            ref = a["line_ref"]
            if ref not in by_id:
                raise TuChoi("DANGLING_DEPENDENCY", f"{cid} phụ thuộc lời gọi không tồn tại {[ref]}", (cid,))
            direct_deps[cid].add(ref)
        for dep_id in c.get("depends_on") or ():
            if dep_id not in by_id:
                raise TuChoi("DANGLING_DEPENDENCY", f"{cid} phụ thuộc lời gọi không tồn tại {[dep_id]}", (cid,))
            direct_deps[cid].add(dep_id)

    for kh in k.solids.values():
        if kh.fact in by_id and kh.fact not in root_solid_call_ids:
            for v in calls:
                va = v.get("args") or {}
                v_solids = {
                    x for x in (va.get("solid"), va.get("numerator_solid"), va.get("denominator_solid"), va.get("original_solid"))
                    if isinstance(x, str)
                } | {x for x in (va.get("subtracted_solids") or ()) if isinstance(x, str)}
                if v["id"] != kh.fact and kh.ten in v_solids:
                    direct_deps[v["id"]].add(kh.fact)

    for u in calls:
        if u["fn"] == "curved_solid":
            ua = u.get("args") or {}
            u_solid = ua.get("solid")
            host_ten = ua.get("circumscribes") or ua.get("inscribed_in")
            if host_ten:
                for kh in k.solids.values():
                    if kh.ten == host_ten and kh.fact in by_id and kh.fact != u["id"]:
                        direct_deps[u["id"]].add(kh.fact)
            for v in calls:
                if v["fn"] in (*_HOI_CONG.values(), "sphere_tangent_plane") and (v.get("args") or {}).get("solid") == u_solid:
                    direct_deps[v["id"]].add(u["id"])
        if u["fn"] == "section":
            u_solid = (u.get("args") or {}).get("solid")
            u_plane = frozenset((u.get("args") or {}).get("plane") or ())
            for v in calls:
                if (
                    v["fn"] == "ask_section_area"
                    and (v.get("args") or {}).get("solid") == u_solid
                    and frozenset((v.get("args") or {}).get("plane") or ()) == u_plane
                ):
                    direct_deps[v["id"]].add(u["id"])

    # Determine goal-reachable calls (ask_*, section, sphere_tangent_plane, explicit line_ref / depends_on)
    goal_roots = [
        c["id"]
        for c in calls
        if c["fn"].startswith("ask_")
        or c["fn"] in ("section", "sphere_tangent_plane")
        or bool(c.get("depends_on"))
        or bool((c.get("args") or {}).get("line_ref"))
    ]
    reachable_from_goals: set[str] = set(goal_roots) if goal_roots else set(by_id)
    if k.resolver.used:
        reachable_from_goals = set(by_id)
    else:
        r_queue = list(reachable_from_goals)
        while r_queue:
            curr = r_queue.pop()
            for prereq in direct_deps.get(curr, ()):
                if prereq not in reachable_from_goals:
                    reachable_from_goals.add(prereq)
                    r_queue.append(prereq)

    # Cycle detection on direct_deps (fail-closed on goal-reachable or explicit cycles)
    state: dict[str, int] = {}
    back_edges_to_drop: list[tuple[str, str]] = []

    def _visit(u_id: str) -> None:
        state[u_id] = 1
        for v_id in sorted(direct_deps[u_id]):
            if state.get(v_id) == 1:
                if u_id in reachable_from_goals or v_id in reachable_from_goals:
                    raise TuChoi("DEPENDENCY_CYCLE", f"phụ thuộc vòng qua {u_id} → {v_id}", (u_id, v_id))
                back_edges_to_drop.append((u_id, v_id))
            elif v_id not in state:
                _visit(v_id)
        state[u_id] = 2

    for cid in [c["id"] for c in calls]:
        if cid not in state:
            _visit(cid)

    for u_id, v_id in back_edges_to_drop:
        direct_deps[u_id].discard(v_id)

    # Identify derived points that serve as the foot of a root solid's apex
    apex_foot_points: set[str] = set()
    for c in calls:
        cid, fn, a = c["id"], c["fn"], c.get("args") or {}
        if fn == "perpendicular_line_plane":
            line_pts = set(a.get("line") or ())
            plane_pts = set(a.get("plane") or ())
            if (line_pts & apex_vertices) and plane_pts <= base_vertices:
                apex_foot_points |= (line_pts - apex_vertices) & set(point_producers)
        elif fn == "altitude" and a.get("apex") in apex_vertices and a.get("foot") in point_producers:
            apex_foot_points.add(a["foot"])
        elif fn == "orthogonal_projection" and cid not in produced_point_of_call and a.get("image") in point_producers:
            apex_foot_points.add(a["image"])

    # Close apex_foot_points transitively over point_producers
    queue = list(apex_foot_points)
    while queue:
        pt = queue.pop()
        for p_cid in point_producers.get(pt, ()):
            for in_pt in consumed_points_of_call.get(p_cid, ()):
                if in_pt in point_producers and in_pt not in apex_foot_points:
                    apex_foot_points.add(in_pt)
                    queue.append(in_pt)

    apex_foot_calls = {p_cid for pt in apex_foot_points for p_cid in point_producers.get(pt, ())}

    tier_of: dict[str, int] = {}
    for c in calls:
        cid, fn = c["id"], c["fn"]
        pts = set(_diem_cua_loi_goi(c))
        if fn in ("pyramid", "regular_pyramid", "prism") and cid in root_solid_call_ids and not direct_deps[cid]:
            tier_of[cid] = 0
        elif fn.startswith("ask_") or fn == "unsupported":
            tier_of[cid] = 5
        elif cid in apex_foot_calls:
            tier_of[cid] = 2
        elif (
            fn in ("regular_polygon", "rectangle", "right_angle", "segment_length", "equal_length")
            and pts
            and pts <= base_vertices
            and not direct_deps[cid]
        ):
            tier_of[cid] = 1
        elif (
            cid not in produced_point_of_call
            and fn
            in (
                "regular_polygon",
                "rectangle",
                "right_angle",
                "perpendicular_line_plane",
                "altitude",
                "orthogonal_projection",
                "perpendicular_lines",
                "face_perpendicular_base",
                "height",
                "segment_length",
                "equal_length",
                "parallel_lines",
                "parallel_planes",
            )
            and pts <= (solid_vertices | apex_foot_points)
            and not direct_deps[cid]
        ):
            tier_of[cid] = 3
        else:
            tier_of[cid] = 4

    tiers: dict[int, list[str]] = {t: [] for t in range(6)}
    for c in calls:
        tiers[tier_of[c["id"]]].append(c["id"])

    ordering_deps: dict[str, set[str]] = {cid: set(deps) for cid, deps in direct_deps.items()}
    for cid in calls:
        u_id = cid["id"]
        t = tier_of[u_id]
        if t >= 1:
            ordering_deps[u_id].update(tiers[0])
        if t >= 2:
            ordering_deps[u_id].update(tiers[1])
        if t >= 3:
            ordering_deps[u_id].update(tiers[2])
        if t >= 4:
            ordering_deps[u_id].update(tiers[3])
        if t >= 5:
            ordering_deps[u_id].update(tiers[4])
        ordering_deps[u_id].discard(u_id)

    # Preserve exact original order if all prerequisites already precede their dependents
    if all(idx_of[prereq] < idx_of[cid] for cid, deps in ordering_deps.items() for prereq in deps):
        return

    in_degree = {cid: len(ordering_deps[cid]) for cid in by_id}
    dependents: dict[str, list[str]] = {cid: [] for cid in by_id}
    for cid, deps in ordering_deps.items():
        for prereq in deps:
            dependents[prereq].append(cid)

    heap: list[tuple[int, int, str]] = [
        (tier_of[cid], idx_of[cid], cid) for cid, deg in in_degree.items() if deg == 0
    ]
    heapq.heapify(heap)
    ordered_ids: list[str] = []
    while heap:
        _t, _i, u_id = heapq.heappop(heap)
        ordered_ids.append(u_id)
        for v_id in dependents[u_id]:
            in_degree[v_id] -= 1
            if in_degree[v_id] == 0:
                heapq.heappush(heap, (tier_of[v_id], idx_of[v_id], v_id))

    if len(ordered_ids) != len(calls):
        rem = sorted(cid for cid, deg in in_degree.items() if deg > 0)
        raise TuChoi("DEPENDENCY_CYCLE", f"phụ thuộc vòng trong kế hoạch lời gọi {rem}", tuple(rem[:2]))

    k.calls = [by_id[cid] for cid in ordered_ids]


def _toan_hang(p: list[str] | None) -> str:
    return "point" if len(p or []) == 1 else "line" if len(p or []) == 2 else "plane"


def _anh_xa(f: TypedFact, k: KeHoach, ten: dict, deu: dict, khoi_cua, phat) -> dict | None:
    """MỘT dữ kiện → lời gọi. Chọn hàm theo `kind` + KIỂU toán hạng; vai trò độ dài ("cạnh bên") giải theo khối."""
    q = list(f.quotes)
    if f.kind == "unsupported":
        return phat(f.id, "unsupported", {"reason": f.reason}, q, "unsupported")
    if f.kind == "polygon_shape":
        if f.shape in _DA_GIAC_DEU:
            n = _DA_GIAC_DEU[f.shape]
            if n and len(f.points) != n:
                raise TuChoi("FACT_INCOMPLETE", f"{f.id}: {f.shape} cần {n} đỉnh", (f.id,))
            if (cu := deu.get(frozenset(f.points))) is not None:       # đáy đã được khai đều qua khối: gắn cạnh + nguồn
                cu["source"]["quotes"] = list(dict.fromkeys(cu["source"]["quotes"] + q))
                if f.value:
                    cu["args"]["side"] = f.value
                return cu
            c = phat(f.id, "regular_polygon", {"vertices": f.points, **({"side": f.value} if f.value else {})}, q,
                     f"polygon_shape({f.shape})→regular_polygon")
            deu[frozenset(f.points)] = c
            return c
        if f.shape == "rectangle":
            return phat(f.id, "rectangle", {"vertices": f.points}, q, "polygon_shape(rectangle)→rectangle")
        return None                                                    # "tam giác ABC": chỉ đặt tên, không ràng buộc
    if f.kind == "right_angle":
        return phat(f.id, "right_angle", {"vertex": f.at, "rays": f.points}, q, "right_angle")
    if f.kind == "equal_lengths":
        return phat(f.id, "equal_length", {"segment_a": f.points_a, "segment_b": f.points_b}, q, "equal_lengths→equal_length")
    if f.kind == "length":
        return _do_dai(f, q, deu, khoi_cua, phat)
    if f.kind == "perpendicular":
        ta, tb = _toan_hang(f.points_a), _toan_hang(f.points_b)
        a, b = (f.points_a, f.points_b) if (ta, tb) != ("plane", "line") else (f.points_b, f.points_a)
        ta, tb = _toan_hang(a), _toan_hang(b)
        if (ta, tb) == ("line", "plane"):
            return phat(f.id, "perpendicular_line_plane", {"line": a, "plane": b}, q, "perpendicular(line, plane)")
        if (ta, tb) == ("line", "line"):
            return phat(f.id, "perpendicular_lines", {"line1": a, "line2": b}, q, "perpendicular(line, line)")
        if (ta, tb) == ("plane", "plane"):
            for mat, day in ((a, b), (b, a)):
                kh = next((x for x in k.solids.values() if frozenset(x.day) == frozenset(day)), None)
                if kh is not None and len(mat) == 3 and len([v for v in mat if v not in kh.day]) == 1:
                    return phat(f.id, "face_perpendicular_base", {"face": mat, "base": day}, q,
                                "perpendicular(face, base)→face_perpendicular_base")
            raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: hai mặt phẳng vuông góc mà không mặt nào là (mặt bên, đáy) — "
                         "chưa có phép dựng", (f.id,))
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: vuông góc giữa {ta} và {tb}", (f.id,))
    if f.kind == "altitude":
        pass
        kh = khoi_cua(f.solid, f)
        x, y = f.points
        dinh, chan = (x, y) if x == kh.dinh else (y, x)
        return phat(f.id, "altitude", {"apex": dinh, "foot": chan, "solid": kh.ten}, q, "altitude")
    if f.curved_part and f.curved_part.get("role") == "tangent_plane":
        if f.solid not in k.curved_solids:
            raise TuChoi("UNKNOWN_SOLID", f"{f.id}: mặt cầu {f.solid!r} không có trong dữ kiện", (f.id,))
        cp = f.curved_part
        return phat(f.id, "sphere_tangent_plane",
                    {"solid": f.solid, "plane": cp["plane"], **({"point": cp["point"]} if cp.get("point") else {})},
                    q, "tangent_to→sphere_tangent_plane")
    if f.kind == "projection":
        if f.line_ref:
            ref = k.resolver.aliases.get(f.line_ref,f.line_ref)
            k.resolver.used = True
            k.resolver.lines.add(ref)
            if len(k.resolver.lines)>MAX_RESULT_LINES:
                raise TuChoi('PLAN_TOO_LARGE','quá trần line results')
            return phat(f.id, "orthogonal_projection_line", {"point": f.point, "line_ref": ref, "image": f.at}, q,
                        "projection(point, result line)")
        if len(f.points) == 2:
            return phat(f.id, "orthogonal_projection_line", {"point": f.point, "line": f.points, "image": f.at}, q, "projection(point, line)")
        return phat(f.id, "orthogonal_projection", {"point": f.point, "plane": f.points, "image": f.at}, q, "projection")
    if f.kind == "point_def":
        if f.point_kind == "intersect_line_line":
            return phat(f.id, f.point_kind, {"point": f.point, "line1": f.points_a, "line2": f.points_b}, q, "point_def(line–line)")
        if f.point_kind == "intersect_line_plane":
            return phat(f.id, f.point_kind, {"point": f.point, "line": f.points_a, "plane": f.points_b}, q, "point_def(line–plane)")
        if f.point_kind == "divide_segment":
            return phat(f.id, "divide_segment", {"point": f.point, "segment": f.points, "ratio": _ty_so(f)}, q,
                        "point_def(divide_segment)")
        if f.point_kind in ("midpoint", "centroid"):
            fn = f.point_kind
            args = {"point": f.point, ("segment" if fn == "midpoint" else "polygon"): f.points}
            return phat(f.id, fn, args, q, f"point_def({f.point_kind})")
        raise TuChoi("SCHEMA_INVALID", f"{f.id}: point_def không hỗ trợ point_kind={f.point_kind!r}", (f.id,))
    if f.kind == "section" and f.plane_relation:                     # mục tiêu: thiết diện với một mặt DỰNG từ quan hệ
        c = _mat_qua_diem(f, q, k, phat, khoi_cua(f.solid, f).ten, "section")
        if f.cut_edges or (f.cut_edges is not None and f.derive_cuts):      # `/2`: no stated cut, vertices derived (D6)
            _dinh_cat_canh(f, k, phat, khoi_cua(f.solid, f))
        return c
    if f.kind == "section":                                         # dựng thiết diện: khối × mặt phẳng qua ba điểm có tên
        return phat(f.id, "section", {"solid": khoi_cua(f.solid, f).ten, "plane": f.points}, q, "section(solid, plane)")
    if f.kind == "intersection_line":
        return phat(f.id, "intersection_line", {"plane1": f.points_a, "plane2": f.points_b}, q, "intersection_line(plane, plane)")
    if f.kind == "question":
        return _cau_hoi(f, q, k, khoi_cua, phat)
    raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: loại dữ kiện {f.kind} chưa có luật", (f.id,))


def _ty_so(f: TypedFact) -> str:
    """The fact's ratio t = AP/AB as an exact "p/q": rational, strictly between 0 and 1, on two distinct endpoints."""
    from fractions import Fraction

    if len(f.points or []) != 2 or len(set(f.points)) != 2:
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: điểm chia cần đúng hai đầu mút phân biệt", (f.id,))
    try:
        t = Fraction(str(f.value).replace(",", "."))
    except (ValueError, ZeroDivisionError):
        raise TuChoi("INVALID_RATIO", f"{f.id}: tỉ số {f.value!r} không phải số hữu tỉ", (f.id,)) from None
    if not 0 < t < 1:
        raise TuChoi("INVALID_RATIO", f"{f.id}: tỉ số AP/AB = {t} phải nằm giữa 0 và 1 (điểm trong đoạn)", (f.id,))
    return f"{t.numerator}/{t.denominator}"


def _do_dai(f: TypedFact, q: list[str], deu: dict, khoi_cua, phat) -> dict:
    m = f.measure
    if m == "segment":
        if not f.points or len(f.points) != 2:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id}: độ dài đoạn cần hai điểm", (f.id,))
        return phat(f.id, "segment_length", {"segment": f.points, "value": f.value}, q, "length(segment)")
    kh = khoi_cua(f.solid, f)
    if m == "height":
        return phat(f.id, "height", {"solid": kh.ten, "value": f.value}, q, "length(height)→height")

    def canh_day() -> dict:
        reg = deu.get(frozenset(kh.day))
        if reg is None:
            raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: 'cạnh đáy' của đáy không đều — không biết là cạnh nào", (f.id,))
        reg["args"]["side"] = f.value
        reg["source"]["quotes"] = list(dict.fromkeys(reg["source"]["quotes"] + q))
        return reg

    def canh_ben(fid: str, qs: list[str], luat: str) -> dict:
        if kh.loai == "pyramid":
            if not kh.deu:
                raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: 'cạnh bên' của chóp không đều — các cạnh bên không chắc bằng nhau",
                             (f.id,))
            return phat(fid, "segment_length", {"segment": [kh.dinh, kh.day[0]], "value": f.value}, qs, luat)
        return phat(fid, "segment_length", {"segment": [kh.day[0], kh.tren[0]], "value": f.value}, qs, luat)

    if m == "base_edge":
        k_ = canh_day()
        return k_
    if m == "lateral_edge":
        return canh_ben(f.id, q, "length(lateral_edge)→segment_length (mọi cạnh bên bằng nhau)")
    if m == "edge":
        dung_moi_canh = kh.kieu == "cube" or (kh.kieu == "tetrahedron" and kh.deu)
        if not dung_moi_canh:
            raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: 'cạnh' chỉ xác định khi mọi cạnh bằng nhau (lập phương, tứ diện đều)",
                         (f.id,))
        canh_day()
        return canh_ben(f.id, list(dict.fromkeys(kh.quotes + q)), "length(edge)→cạnh đáy + cạnh bên (định nghĩa)")
    raise TuChoi("FACT_INCOMPLETE", f"{f.id}: measure {m!r}", (f.id,))


_DIEN_TICH_THIET_DIEN = re.compile(r"diện tích\s+(?:của\s+)?thiết diện", re.IGNORECASE)
_DIEN_TICH_DA_GIAC = re.compile(r"(?i:diện tích)\s+(?:(?i:của)\s+)?(?:(?i:tam giác|tứ giác|hình|đa giác|mặt|đáy)|[A-Z])")
_DIEN_TICH_NO = re.compile(r"diện tích\s+(?:của\s+)?nó(?![\w'])", re.IGNORECASE)
_DIEN_TICH_TEN_TD = re.compile(
    r"diện tích\s+(?:của\s+)?(?P<loai>tam\s+giác|tứ\s+giác|đa\s+giác)\s+(?P<poly>(?-i:[A-Z][0-9]*'?){3,})(?![\w'])",
    re.IGNORECASE,
)
_DANH_TU_CANH_TRANH_TD = re.compile(
    r"(?<!\w)(?:tam\s+giác|tứ\s+giác|đa\s+giác|hình\s+vuông|hình\s+chữ\s+nhật|hình\s+thoi|hình\s+thang|mặt\s+bên|mặt\s+đáy|đáy)(?!\w)",
    re.IGNORECASE,
)


def _khoi_tu_toan_hang(pts: list[str] | None, k: KeHoach, f: TypedFact, khoi_cua) -> _Khoi:
    if not pts or len(pts) < 4 or len(set(pts)) != len(pts):
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: toán hạng khối cần ít nhất 4 đỉnh phân biệt", (f.id,))
    cands = [f"{pts[0]}.{''.join(pts[1:])}", "".join(pts)]
    if len(pts) >= 6 and len(pts) % 2 == 0:
        half = len(pts) // 2
        cands.insert(1, f"{''.join(pts[:half])}.{''.join(pts[half:])}")
    for sym in cands:
        kh = k.solids.get(sym) or next((x for x in k.solids.values() if x.ten == sym), None)
        if kh is not None:
            return kh
    for kh in k.solids.values():
        if kh.loai == "pyramid" and kh.dinh == pts[0] and len(kh.day) == len(pts) - 1 and set(kh.day) == set(pts[1:]):
            return kh
    if len(pts) == 4:
        tets = [
            kh for kh in k.solids.values()
            if kh.loai == "pyramid" and len(kh.day) == 3 and ({kh.dinh} | set(kh.day)) == set(pts)
        ]
        if len(tets) == 1:
            return tets[0]
    raise TuChoi("UNKNOWN_SOLID", f"{f.id}: khối từ các đỉnh {pts} không có trong dữ kiện", (f.id,))


def _hoi_dien_tich_thiet_dien_phu(f: TypedFact, q: list[str], k: KeHoach, khoi_cua) -> bool:
    """M5 bounded section-area question binding for `f.plane_relation`:
    1. Anaphoric `diện tích (của )?nó` when there is a unique derived section in the problem and no competing polygon/face
       noun phrase intervenes between the section antecedent (`thiết diện`) and `diện tích (của )?nó`.
    2. Named section polygon `diện tích (của )?(tam giác|tứ giác|đa giác) <POLY>` when `<POLY>` has distinct vertex labels
       matching the shape noun vertex count (`tam giác` = 3, `tứ giác` = 4) and `set(<POLY>)` equals the grounded section
       vertex set `{through_point, *stated_cut_points}` (or `<POLY>` is explicitly declared as `thiết diện <POLY>`).
    """
    txt = chuan_hoa(k.resolver.text) if k.resolver and k.resolver.text else chuan_hoa(" ".join(q))
    if any(_DIEN_TICH_NO.search(x) for x in q):
        if len(k.derived_planes) > 1:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{f.id}: 'diện tích của nó' mơ hồ khi có nhiều thiết diện", (f.id,))
        m_no = _DIEN_TICH_NO.search(txt)
        if m_no is None:
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{f.id}: không tìm thấy cụm 'diện tích của nó' trong nguồn", (f.id,))
        tds = list(re.finditer(r"thiết\s+diện(?:\s+(?-i:[A-Z][0-9]*'?){3,})?", txt[:m_no.start()], re.IGNORECASE))
        if len(tds) != 1 or _DANH_TU_CANH_TRANH_TD.search(txt[tds[-1].end():m_no.start()]):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{f.id}: 'diện tích của nó' không gắn duy nhất với thiết diện", (f.id,))
        return True
    m_ten = next((m for x in q for m in _DIEN_TICH_TEN_TD.finditer(x)), None)
    if m_ten is not None:
        pts = re.findall(r"[A-Z][0-9]*'?", m_ten["poly"])
        loai = re.sub(r"\s+", " ", m_ten["loai"].lower())
        if (len(pts) != len(set(pts))
                or (loai == "tam giác" and len(pts) != 3)
                or (loai == "tứ giác" and len(pts) != 4)):
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{f.id}: số đỉnh của {m_ten['poly']} không khớp {loai}", (f.id,))
        solid_ten = khoi_cua(f.solid, f).ten
        cat = next((x for x in k.auxiliary if x.get("rule") == DINH_CAT_CANH and x.get("solid") == solid_ten
                    and x.get("point") == f.point), None)
        if cat is not None and cat.get("stated_points") and all(cat["stated_points"]):
            if set(pts) != {f.point, *cat["stated_points"]}:
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{f.id}: đa giác {m_ten['poly']} không khớp các đỉnh thiết diện đã nêu", (f.id,))
            return True
        if f.point in pts and re.search(
                rf"thiết\s+diện(?:\s+là)?(?:\s+(?:tam\s+giác|tứ\s+giác|đa\s+giác))?\s+(?-i:{re.escape(m_ten['poly'])})(?![\w'])",
                txt, re.IGNORECASE):
            return True
        raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{f.id}: đa giác {m_ten['poly']} không phải thiết diện đã xác thực", (f.id,))
    return False


def _cau_hoi(f: TypedFact, q: list[str], k: KeHoach, khoi_cua, phat) -> dict:
    n = f.quantity
    if f.solid in k.curved_solids:
        if f.role == "prove":
            raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{f.id}: đại lượng khối tròn xoay là điều phải chứng minh, chưa hỗ trợ", (f.id,))
        if f.negated:
            raise TuChoi("NEGATED_CLAUSE", f"{f.id}: câu hỏi khối tròn xoay bị phủ định", (f.id,))
        if n not in _HOI_CONG:
            raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: câu hỏi {n!r} chưa hỗ trợ trên khối tròn xoay", (f.id,))
        return phat(f.id, _HOI_CONG[n], {"solid": f.solid}, q, f"question({n})→{_HOI_CONG[n]}")
    # Diện tích THIẾT DIỆN chỉ khi câu hỏi gọi tên đúng đối tượng ấy ("diện tích (của) thiết diện"); "diện tích tam giác MAB"
    # có ô `solid` vẫn là đa giác; một dữ kiện hỏi CẢ HAI là mơ hồ (review 2, I2). Cổng nguồn kiểm lại cụm mặt cắt.
    hoi_td = any(_DIEN_TICH_THIET_DIEN.search(x) for x in q)
    if n == "area" and hoi_td and any(_DIEN_TICH_DA_GIAC.search(x) for x in q):
        raise TuChoi("AMBIGUOUS_FACT", f"{f.id}: một câu hỏi diện tích nêu cả thiết diện lẫn một đa giác — tách hai câu hỏi", (f.id,))
    if n == "area" and f.plane_relation and not hoi_td and not f.negated and f.role == "question":
        hoi_td = _hoi_dien_tich_thiet_dien_phu(f, q, k, khoi_cua)
        if not hoi_td:
            if not any(re.search(r"diện\s+tích", x, re.IGNORECASE) for x in q):
                raise TuChoi("NOT_ASKED_IN_SOURCE", f"{f.id}: nguồn không hỏi diện tích thiết diện", (f.id,))
            raise TuChoi("SOURCE_OBJECT_MISMATCH", f"{f.id}: câu hỏi diện tích không gọi đúng thiết diện đã khai", (f.id,))
    if n == "area" and f.plane_relation and hoi_td and not f.negated and f.role == "question":
        return _mat_qua_diem(f, q, k, phat, khoi_cua(f.solid, f).ten, "ask_section_area")
    if f.plane_relation:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: mặt cho bằng quan hệ chỉ dùng cho thiết diện / diện tích thiết diện",
                     (f.id,))
    if n == "area" and f.solid and len(f.points or []) >= 3 and hoi_td:
        return phat(f.id, "ask_section_area", {"solid": khoi_cua(f.solid, f).ten, "plane": f.points}, q,
                    "question(area of section)")
    entries = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.goal == n]
    if entries and f.role == 'question' and not f.negated:
        if f.point_kind is not None:                  # a described operand: the goal contracts decide which slots it fills
            return k.resolver.goal(f, entries)
        # A NAMED question enters by goal contract only when every slot is a point read from one flat label list (length,
        # area). A goal with a line / plane slot (angles) keeps its direct rule below: all its objects are named, nothing
        # to search, and `points_a`/`points_b` would otherwise be read against the wrong contract (Wave 2A, trap 1).
        flat = [c for c in entries if all(kind == 'Point' for _s, kind in goal_slots(c))]
        if flat and len(f.points or []) <= max(len(c.effect.operands) for c in flat):
            return k.resolver.goal(f, flat)
    if f.point_kind is not None:                       # distance from an unnamed, described point: one typed goal
        if f.role == "prove":
            raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{f.id}: điểm không tên chỉ cho câu hỏi được hỏi", (f.id,))
        if f.negated:
            raise TuChoi("NEGATED_CLAUSE", f"{f.id}: câu hỏi khoảng cách bị phủ định", (f.id,))
        b = list(dict.fromkeys(f.points_b or []))
        if len(b) > 3 and not f.line_ref:
            k.named_planes.append({"call": f.id, "labels": b})
        target = (("result", f.line_ref) if f.line_ref else ("named", tuple(sorted(b))) if len(b) == 2 else tuple(b[:3]))
        dcs = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.descriptor == f.point_kind]
        parsed = next(r for c in dcs if (r := parse_descriptor_inputs(c, f.points or ())) is not None)
        return k.resolver.distance(f, ("desc", f.point_kind, parsed[0]), target)
    if f.line_ref:
        return k.resolver.distance(f, f.points_a[0], ("result", f.line_ref))
    if n == "volume":
        pass

    if f.solid_refs:                                    # operands by solid fact id (declared or derived pyramid)
        theo = {kh.fact: kh for kh in k.solids.values()}
        if lac := [x for x in f.solid_refs if x not in theo]:
            raise TuChoi("UNKNOWN_SOLID", f"{f.id}: {lac} không phải khối đã khai", (f.id,))
        ten = [theo[x].ten for x in f.solid_refs]
        if f.role != "question" or f.negated:
            raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: toán hạng khối chỉ cho câu hỏi khẳng định", (f.id,))
        if n == "volume_ratio":
            return phat(f.id, "ask_volume_ratio", {"numerator_solid": ten[0], "denominator_solid": ten[1]}, q,
                        "question(volume_ratio, solid refs)")
        return phat(f.id, "ask_residual_volume", {"original_solid": ten[0], "subtracted_solids": ten[1:]}, q,
                    "question(residual_volume, solid refs)")
    if n == "volume_ratio" or (n == "volume" and not f.solid and len(f.points_a or []) >= 4 and len(f.points_b or []) >= 4):
        if f.role == "prove":
            raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{f.id}: tỉ số thể tích là điều phải chứng minh, chưa hỗ trợ", (f.id,))
        if f.negated:
            raise TuChoi("NEGATED_CLAUSE", f"{f.id}: câu hỏi tỉ số thể tích bị phủ định", (f.id,))
        kh_a = khoi_cua(f.solid, f) if (f.solid and not f.points_a) else _khoi_tu_toan_hang(f.points_a, k, f, khoi_cua)
        kh_b = _khoi_tu_toan_hang(f.points_b, k, f, khoi_cua)
        if kh_a.ten == kh_b.ten:
            raise TuChoi("UNSUPPORTED_VOLUME_RATIO", f"{f.id}: tỉ số thể tích cần hai khối phân biệt", (f.id,))
        return phat(f.id, "ask_volume_ratio", {"numerator_solid": kh_a.ten, "denominator_solid": kh_b.ten}, q,
                    "question(volume_ratio)")
    if n == "residual_volume" or (n == "volume" and f.solid and (len(f.points_a or []) >= 4 or len(f.points_b or []) >= 4)):
        if f.role == "prove":
            raise TuChoi("GOAL_CLAUSE_NOT_PREMISE", f"{f.id}: thể tích phần còn lại là điều phải chứng minh, chưa hỗ trợ", (f.id,))
        if f.negated:
            raise TuChoi("NEGATED_CLAUSE", f"{f.id}: câu hỏi thể tích phần còn lại bị phủ định", (f.id,))
        kh_orig = khoi_cua(f.solid, f) if f.solid else _khoi_tu_toan_hang(f.points, k, f, khoi_cua)
        sub_lists = [pts for pts in (f.points_a, f.points_b) if pts] or ([f.points] if f.solid and f.points else [])
        if not sub_lists:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id}: thể tích phần còn lại thiếu khối bị cắt bỏ", (f.id,))
        sub_tens = [_khoi_tu_toan_hang(pts, k, f, khoi_cua).ten for pts in sub_lists]
        return phat(f.id, "ask_residual_volume", {"original_solid": kh_orig.ten, "subtracted_solids": sub_tens}, q,
                    "question(residual_volume)")
    if n == "volume":
        kh_v = khoi_cua(f.solid, f)
        k.volume_asks[f.id] = kh_v.ten
        return phat(f.id, "ask_volume", {"solid": kh_v.ten}, q, "question(volume)")
    if n == "area":
        return phat(f.id, "ask_area", {"polygon": f.points}, q, "question(area)")
    if n == "length" or (n == "distance" and _toan_hang(f.points_a) == _toan_hang(f.points_b) == "point"):
        seg = f.points or (f.points_a or []) + (f.points_b or [])
        return phat(f.id, "ask_length", {"segment": seg}, q, "question(length)")
    a, b = f.points_a, f.points_b
    loai = (_toan_hang(a), _toan_hang(b))
    if n == "distance":
        if loai == ("plane", "point"):
            a, b, loai = b, a, ("point", "plane")
        if loai == ("point", "plane"):
            if len(b) > 3:
                k.named_planes.append({"call": f.id, "labels": list(b)})
            return phat(f.id, "ask_distance_point_plane", {"point": a[0], "plane": b[:3]}, q, "question(distance point–plane)")
        if loai == ("line", "line"):
            return phat(f.id, "ask_distance_lines", {"line1": a, "line2": b}, q, "question(distance line–line)")
        if loai == ("plane", "line"):
            a, b, loai = b, a, ("line", "plane")
        if loai == ("line", "plane"):
            return phat(f.id, "ask_distance_line_plane", {"line": a, "plane": b}, q, "question(distance line–plane)")
        if loai == ("plane", "plane"):
            return phat(f.id, "ask_distance_planes", {"plane1": a, "plane2": b}, q, "question(distance plane–plane)")
        if loai in (("point", "line"), ("line", "point")) and f.role == "question" and not f.negated:
            p, dt = (a, b) if loai == ("point", "line") else (b, a)
            return _phan_ra(f, q, k, phat, p[0], dt)
    if n == "angle":
        if loai == ("plane", "line"):
            a, b, loai = b, a, ("line", "plane")
        if loai == ("line", "plane"):
            return phat(f.id, "ask_angle_line_plane", {"line": a, "plane": b}, q, "question(angle line–plane)")
        if loai == ("plane", "plane"):
            return phat(f.id, "ask_angle_plane_plane", {"plane1": a, "plane2": b}, q, "question(angle plane–plane)")
        if loai == ("line", "line"):
            return phat(f.id, "ask_angle_lines", {"line1": a, "line2": b}, q, "question(angle line–line)")
    raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: câu hỏi {n} giữa {loai} chưa có hàm", (f.id,))


def _phan_giai_diem_mat_phu(f: TypedFact, k: KeHoach) -> tuple[str, list[dict] | None, dict | None, list[str]]:
    if f.point is not None:
        return f.point, None, None, []
    dcs = [c for s in REGISTRY.values() for c in planning_contracts(s) if c.descriptor == f.point_kind]
    parsed = next(r for c in dcs if (r := parse_descriptor_inputs(c, f.points or ())) is not None)
    m, chain, p_labels = k.resolver.point(f, ("desc", f.point_kind, parsed[0]))
    return m, chain, {"descriptor": f.point_kind, "points": list(f.points or ()), "label": m}, p_labels


def _mat_qua_diem(f: TypedFact, q: list[str], k: KeHoach, phat, khoi: str, fn: str) -> dict:
    """PHÂN RÃ MỤC TIÊU, độ sâu 1 (`MAT_SONG_SONG`): Section(khối, mặt qua M ∥ (Q)).

    Kiểu: Point M × Plane Q (≥ 3 nhãn) → Plane → Section. Phụ thuộc: M và Q đã có tên (cổng nguồn kiểm nhãn và mệnh đề
    định nghĩa) → hai điểm phụ = M tịnh tiến theo hai vectơ chỉ phương của (Q) → thiết diện qua (M, X₁, X₂). Engine kiểm
    hậu điều kiện độc lập (qua M, song song (Q), không trùng (Q), không phải mặt biên). Một mặt dẫn xuất chỉ dựng MỘT lần
    dù được dùng để dựng và để hỏi diện tích. Mặt qua một điểm VUÔNG GÓC với một mặt phẳng không duy nhất ⇒ từ chối."""
    if f.plane_relation == "perpendicular":
        if len(set(f.points_b)) >= 3:                 # ⊥ a PLANE: infinitely many planes through the point
            raise TuChoi("PLANE_NOT_UNIQUE", f"{f.id}: mặt qua {f.point or f.point_kind} vuông góc với ({''.join(f.points_b)}) có vô số — cần "
                         "thêm một ràng buộc để xác định duy nhất", (f.id,))
        if len(set(f.points_b)) != 2:
            raise TuChoi("FACT_INCOMPLETE", f"{f.id}: đường vuông góc với mặt cần đúng hai điểm phân biệt", (f.id,))
        return _mat_vuong_duong(f, q, k, phat, khoi, fn)          # ⊥ a LINE: exactly one plane
    if f.role not in ("premise", "question") or f.negated:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: mặt dựng từ quan hệ chỉ cho thiết diện được yêu cầu", (f.id,))
    two = f.plane_relation == "parallel_two_lines"
    rule = MAT_HAI_DUONG if two else MAT_SONG_SONG
    m, p_chain, p_op, p_labels = _phan_giai_diem_mat_phu(f, k)
    ref = list(dict.fromkeys(f.points_b))
    directions = [list(f.points_a), list(f.points_b)] if two else [[ref[0], ref[1]], [ref[0], ref[2]]] if len(ref) >= 3 else []
    if not two and len(ref) < 3:
        raise TuChoi("FACT_INCOMPLETE", f"{f.id}: mặt tham chiếu cần ít nhất ba điểm", (f.id,))
    if not two and m in ref:
        raise TuChoi("DERIVED_PLANE_IS_REFERENCE", f"{f.id}: {m} thuộc ({''.join(ref)}) — mặt qua {m} song song với nó là chính nó",
                     (f.id,))
    khoa = ((khoi, m, f.plane_name, frozenset(frozenset(v) for v in directions)) if two else (khoi, m, f.plane_name, frozenset(ref)))
    d = k.derived_planes.get(khoa)
    if d is None:
        if len(k.derived_planes) >= MAX_DERIVED_PLANES:
            raise TuChoi("PLAN_TOO_LARGE", f"{f.id}: quá {MAX_DERIVED_PLANES} mặt dẫn xuất", (f.id,))
        xs = [ten for ten in _NHAN_PHU if ten not in k.taken][:2]
        if len(xs) < 2:
            raise TuChoi("PLAN_TOO_LARGE", f"{f.id}: hết nhãn điểm phụ", (f.id,))
        k.taken |= set(xs)
        dung, cids = {c["id"] for c in k.calls}, []
        for i, (x, v) in enumerate(zip(xs, directions), 1):
            cid = next(j for j in (f"{f.id}_plane{i}", *(f"{f.id}_plane{i}_{n}" for n in range(2, 1000)))
                       if j not in k.fact_ids | dung)
            phat(cid, "translate_point", {"point": m, "vector": v, "image": x}, q,
                 f"{rule}→translate_point (điểm phụ {x} = {m} + {v[0]}{v[1]}→)")
            k.trace[-1]["fact"] = f.id
            cids.append(cid)
        d = {"labels": xs, "rule": rule, "goal": f.id, "constructs": cids, "targets": [], "point": m,
             "parallel_to": ref, "solid": khoi, "quotes": list(dict.fromkeys(q)), "provenance": "DERIVED",
             "binding": "AUXILIARY"}
        if p_chain is not None:
            d.update(point_chain=p_chain, point_operand=p_op, point_labels=p_labels)
        if f.plane_name is not None:
            d["plane_name"] = f.plane_name
        if two:
            d.update(lines=directions, plane_name=f.plane_name)
        k.derived_planes[khoa] = d
        k.auxiliary.append(d)
    d["quotes"] = list(dict.fromkeys(d["quotes"] + q))
    c = phat(f.id, fn, {"solid": khoi, "plane": [m, *d["labels"]]}, d["quotes"], f"{rule}→{fn}")
    k.trace[-1]["fact"] = f.id
    d["targets"].append(f.id)
    # a cut certificate on this plane, and its cut calls, share the plane's FINAL quotes (an area question on the same
    # plane mapped after the section grows them — run `hybrid-contract-v2`)
    cat = [x for x in k.auxiliary if x.get("rule") == DINH_CAT_CANH and x.get("plane_goal") == d["goal"]]
    for x in cat:
        x["quotes"] = list(d["quotes"])
    for call in k.calls:                                  # một khai báo, một tập quote cho mọi lời gọi của nó
        if call["id"] in d["constructs"] + d["targets"] + [i for x in cat for i in x["constructs"]]:
            call["source"]["quotes"] = list(d["quotes"])
    k.trace.append({"fact": f.id, "step": "decompose_goal", "rule": rule,
                    "goal": f"Section({khoi}, Plane({m} ∥ ({''.join(ref)})))",
                    "dependencies": ([f"VerifiedPoint {m}", *[f"VerifiedLine {''.join(v)}" for v in directions]] if two else
                                     [f"VerifiedPoint {m}", f"ParallelPlane({m}, {''.join(ref)})", f"{fn}({khoi})"]),
                    "calls": d["constructs"] + [f.id], "auxiliary": d["labels"],
                    "reason": f"mặt qua {m} và hai ảnh tịnh tiến theo " + ', '.join(''.join(v)+'→' for v in directions)
                              + " (IR sẵn có; engine kiểm các quan hệ trên hình đã dựng)",
                    "provenance": "DERIVED", "binding": "AUXILIARY"})
    return c


def _chon_moc_vuong_duong(kh: _Khoi, d: list[str], facts: dict[str, TypedFact], fid: str) -> list[str]:
    tang = [kh.day, [kh.dinh] if kh.loai == "pyramid" else kh.tren]
    solid_verts = {*tang[0], *tang[1]}
    if set(d) <= solid_verts:
        cung = next((i for i, t in enumerate(tang) if set(d) <= set(t) and set(t) - set(d)), None)
        return ([v for v in kh.day if v not in d][:2] if cung is None
                else [next(v for v in tang[cung] if v not in d), tang[1 - cung][0]])
    prem_pts: dict[str, TypedFact] = {}
    perp_faces: list[tuple[set[str], set[str]]] = []
    perp_line_planes: list[tuple[set[str], set[str]]] = []
    for pf in facts.values():
        if pf.role == "premise" and not pf.negated:
            if pf.kind == "point_def" and pf.point:
                prem_pts[pf.point] = pf
            elif pf.kind == "projection" and pf.at:
                prem_pts[pf.at] = pf
            elif pf.kind == "altitude" and pf.points:
                for ap in pf.points:
                    if ap not in solid_verts:
                        prem_pts[ap] = pf
            elif pf.kind == "perpendicular":
                pa, pb = pf.points_a or (), pf.points_b or ()
                if len(pa) >= 3 and len(pb) >= 3:
                    perp_faces.append((set(pa), set(pb)))
                elif len(pa) == 2 and len(pb) >= 3:
                    perp_line_planes.append((set(pa), set(pb)))
                elif len(pb) == 2 and len(pa) >= 3:
                    perp_line_planes.append((set(pb), set(pa)))
    if not set(d) <= (solid_verts | set(prem_pts)):
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{fid}: đường {''.join(d)} phải nối hai điểm đã xác thực của {kh.ten}", (fid,))

    carrier_planes: list[set[str]] = [set(kh.day)]
    if kh.loai == "prism":
        carrier_planes.append(set(kh.tren))
        for i in range(len(kh.day)):
            for j in range(i + 1, len(kh.day)):
                carrier_planes.append({kh.day[i], kh.day[j], kh.tren[j], kh.tren[i]})
    else:
        for i in range(len(kh.day)):
            for j in range(i + 1, len(kh.day)):
                carrier_planes.append({kh.dinh, kh.day[i], kh.day[j]})
    for ln_p, pl_p in perp_line_planes:
        for f_pl in carrier_planes:
            if ln_p <= f_pl:
                perp_faces.append((set(f_pl), set(pl_p)))

    def _layer(pt: str, seen: frozenset[str] = frozenset()) -> int | None:
        if pt in tang[0]:
            return 0
        if pt in tang[1]:
            return 1
        if pt in seen or (pf := prem_pts.get(pt)) is None:
            return None
        nxt = seen | {pt}
        if pf.kind == "altitude":
            return 0
        if pf.kind == "projection":
            ops = set(pf.points or ())
        elif pf.kind == "point_def" and pf.point_kind == "intersect_line_plane":
            ops = set(pf.points_b or ())
        else:
            ops = set(pf.points or ()) | set(pf.points_a or ()) | set(pf.points_b or ())
        if not ops:
            return None
        ls = {_layer(u, nxt) for u in ops}
        return next(iter(ls)) if len(ls) == 1 and None not in ls else None

    carrier_lines: list[set[str]] = []
    for pt, pf in prem_pts.items():
        if pf.kind == "point_def":
            if pf.point_kind in ("midpoint", "divide_segment") and len(pf.points or ()) == 2:
                carrier_lines.append({pt, *pf.points})
            elif pf.point_kind == "centroid" and len(pf.points or ()) >= 3:
                carrier_planes.append({pt, *pf.points})
            elif pf.point_kind == "intersect_line_line":
                if len(pf.points_a or ()) == 2:
                    carrier_lines.append({pt, *pf.points_a})
                if len(pf.points_b or ()) == 2:
                    carrier_lines.append({pt, *pf.points_b})
                if len(pf.points_a or ()) == 2 and len(pf.points_b or ()) == 2:
                    carrier_planes.append({pt, *pf.points_a, *pf.points_b})
            elif pf.point_kind == "intersect_line_plane":
                if len(pf.points_a or ()) == 2:
                    carrier_lines.append({pt, *pf.points_a})
                if len(pf.points_b or ()) >= 3:
                    carrier_planes.append({pt, *pf.points_b})
        elif pf.kind == "projection":
            if len(pf.points or ()) == 2:
                carrier_lines.append({pt, *pf.points})
            elif len(pf.points or ()) >= 3:
                carrier_planes.append({pt, *pf.points})
                if pf.point:
                    pl = set(pf.points)
                    for fa, fb in perp_faces:
                        for face, base_pl in ((fa, fb), (fb, fa)):
                            inter = face & base_pl
                            if pf.point in face and pl <= base_pl and len(inter) == 2:
                                carrier_lines.append({pt, *inter})
        elif pf.kind == "altitude" and pf.points:
            carrier_planes.append({pt, *kh.day})
            ap = next((u for u in pf.points if u != pt), None)
            base_pl = set(kh.day)
            if ap:
                for fa, fb in perp_faces:
                    for face, bpl in ((fa, fb), (fb, fa)):
                        inter = face & bpl
                        if ap in face and bpl == base_pl and len(inter) == 2:
                            carrier_lines.append({pt, *inter})

    changed = True
    while changed:
        changed = False
        for i in range(len(carrier_lines)):
            for j in range(i + 1, len(carrier_lines)):
                if len(carrier_lines[i] & carrier_lines[j]) >= 2:
                    carrier_lines[i] |= carrier_lines[j]
                    carrier_lines.pop(j)
                    changed = True
                    break
            if changed:
                break

    pl_changed = True
    while pl_changed:
        pl_changed = False
        for pl in carrier_planes:
            before_n = len(pl)
            for ln in carrier_lines:
                if len(pl & ln) >= 2:
                    pl |= ln
            for pt, pf in prem_pts.items():
                if pt in pl:
                    continue
                if pf.kind == "point_def":
                    if pf.point_kind in ("midpoint", "divide_segment", "centroid") and pf.points and set(pf.points) <= pl:
                        pl.add(pt)
                    elif pf.point_kind == "intersect_line_plane" and pf.points_b and set(pf.points_b) <= pl:
                        pl.add(pt)
                    elif pf.point_kind == "intersect_line_line" and pf.points_a and pf.points_b and set(pf.points_a) <= pl and set(pf.points_b) <= pl:
                        pl.add(pt)
                elif pf.kind == "projection" and len(pf.points or ()) >= 3 and set(pf.points) <= pl:
                    pl.add(pt)
                elif pf.kind == "altitude" and set(kh.day) <= pl:
                    pl.add(pt)
            if len(pl) != before_n:
                pl_changed = True

    layers = [_layer(x) for x in d]
    if layers[0] is not None and layers[0] == layers[1]:
        li = layers[0]
        collinear: set[str] = set(d)
        for ln in carrier_lines:
            if len(ln & set(d)) >= 2:
                collinear |= ln
        z_same = next((v for v in tang[li] if v not in collinear), next(v for v in tang[li] if v not in d))
        return [z_same, tang[1 - li][0]]
    rel_lines = [ln for ln in carrier_lines if ln & set(d)]
    ordered_verts = [*kh.day, *(v for v in tang[1] if v not in kh.day)]
    on_d = set(d) | {v for ln in carrier_lines if len(ln & set(d)) >= 2 for v in ln}
    cand = [v for v in ordered_verts if v not in on_d]
    if len(cand) < 2:
        cand = [v for v in ordered_verts if v not in d]
    for i, u in enumerate(cand):
        for w in cand[i + 1:]:
            if not any({u, w} <= ln for ln in rel_lines) and not any({*d, u, w} <= pl for pl in carrier_planes):
                return [u, w]
    return cand[:2]


def _mat_vuong_duong(f: TypedFact, q: list[str], k: KeHoach, phat, khoi: str, fn: str) -> dict:
    """PHÂN RÃ MỤC TIÊU (`MAT_VUONG_DUONG`): Section(khối, mặt qua M ⊥ d) from EXISTING primitives only.

    For a solid vertex Z off d, F = foot of Z on d (`orthogonal_projection_line`) and X = M + F→Z (`translate_point`) lies on
    the plane through M ⊥ d. Two anchors Z₁, Z₂ chosen from the solid's STRUCTURE (no coordinates), the solid seen as two
    layers — base and apex of a pyramid, base and top of a prism: with d inside one layer, a vertex of that layer off d and a
    vertex of the other layer; otherwise (d joins the layers) two base vertices off d — either way d ∪ {Z₁, Z₂} spans space,
    so the two directions are independent (pyramid anchors unchanged from /9). The engine re-checks ⊥ in the Gram metric,
    independence, and against the kernel's `plane_through_point_perpendicular_to`."""
    if f.role not in ("premise", "question") or f.negated:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: mặt dựng từ quan hệ chỉ cho thiết diện được yêu cầu", (f.id,))
    m, p_chain, p_op, p_labels = _phan_giai_diem_mat_phu(f, k)
    d = list(f.points_b)
    kh = next(x for x in k.solids.values() if x.ten == khoi)
    moc = _chon_moc_vuong_duong(kh, d, k.resolver.facts, f.id)
    khoa = (khoi, m, f.plane_name, "perpendicular_line", frozenset(d))
    dd = k.derived_planes.get(khoa)
    if dd is None:
        if len(k.derived_planes) >= MAX_DERIVED_PLANES:
            raise TuChoi("PLAN_TOO_LARGE", f"{f.id}: quá {MAX_DERIVED_PLANES} mặt dẫn xuất", (f.id,))
        nhan = [ten for ten in _NHAN_PHU if ten not in k.taken][:4]
        if len(nhan) < 4:
            raise TuChoi("PLAN_TOO_LARGE", f"{f.id}: hết nhãn điểm phụ", (f.id,))
        k.taken |= set(nhan)
        chan, xs, cids = nhan[:2], nhan[2:], []

        def moi(goc: str) -> str:
            dung = {c["id"] for c in k.calls}
            return next(j for j in (goc, *(f"{goc}_{n}" for n in range(2, 1000))) if j not in k.fact_ids | dung)

        for i, (z, foot) in enumerate(zip(moc, chan), 1):
            cids.append(moi(f"{f.id}_perp{i}_foot"))
            phat(cids[-1], "orthogonal_projection_line", {"point": z, "line": d, "image": foot}, q,
                 f"{MAT_VUONG_DUONG}→orthogonal_projection_line (chân {foot} của {z} trên {''.join(d)})")
            k.trace[-1]["fact"] = f.id
        for i, (z, foot, x) in enumerate(zip(moc, chan, xs), 1):
            cids.append(moi(f"{f.id}_perp{i}"))
            phat(cids[-1], "translate_point", {"point": m, "vector": [foot, z], "image": x}, q,
                 f"{MAT_VUONG_DUONG}→translate_point (điểm phụ {x} = {m} + {foot}{z}→)")
            k.trace[-1]["fact"] = f.id
        dd = {"labels": xs, "feet": chan, "anchors": moc, "rule": MAT_VUONG_DUONG, "goal": f.id, "constructs": cids,
              "targets": [], "point": m, "perpendicular_to": d, "solid": khoi, "quotes": list(dict.fromkeys(q)),
              "provenance": "DERIVED", "binding": "AUXILIARY"}
        if p_chain is not None:
            dd.update(point_chain=p_chain, point_operand=p_op, point_labels=p_labels)
        if f.plane_name is not None:
            dd["plane_name"] = f.plane_name
        k.derived_planes[khoa] = dd
        k.auxiliary.append(dd)
    dd["quotes"] = list(dict.fromkeys(dd["quotes"] + q))
    c = phat(f.id, fn, {"solid": khoi, "plane": [m, *dd["labels"]]}, dd["quotes"], f"{MAT_VUONG_DUONG}→{fn}")
    k.trace[-1]["fact"] = f.id
    dd["targets"].append(f.id)
    cat = [x for x in k.auxiliary if x.get("rule") == DINH_CAT_CANH and x.get("plane_goal") == dd["goal"]]
    for x in cat:
        x["quotes"] = list(dd["quotes"])
    for call in k.calls:
        if call["id"] in dd["constructs"] + dd["targets"] + [i for x in cat for i in x["constructs"]]:
            call["source"]["quotes"] = list(dd["quotes"])
    k.trace.append({"fact": f.id, "step": "decompose_goal", "rule": MAT_VUONG_DUONG,
                    "goal": f"Section({khoi}, Plane({m} ⊥ {''.join(d)}))",
                    "dependencies": [f"VerifiedPoint {m}", f"VerifiedLine {''.join(d)}", *(f"Vertex {z}" for z in dd["anchors"])],
                    "calls": dd["constructs"] + [f.id], "auxiliary": dd["feet"] + dd["labels"],
                    "reason": f"mặt qua {m} và hai điểm {m} + (đỉnh − chân của đỉnh trên {''.join(d)}) (IR sẵn có: project_onto, "
                              "translate; engine kiểm vuông góc chính xác)",
                    "provenance": "DERIVED", "binding": "AUXILIARY"})
    return c


def _canh_ben(kh: _Khoi) -> list[tuple[str, str]]:
    """Lateral edges in base order: apex–base vertex of a pyramid, base–top vertex of a prism (structure, no coordinates)."""
    return [(kh.dinh, b) for b in kh.day] if kh.loai == "pyramid" else list(zip(kh.day, kh.tren))


def _hop_dong_giao_diem() -> tuple[str, Any]:
    """The Registry function (and its planning contract) that realizes a section vertex: a line meeting a plane, effect
    `Meet` (run `hybrid-contract-v2`). Read from the Registry, never named in the planner — without exactly one such
    contract no cut vertex is planned (ablation-tested)."""
    cs = [(s.name, c) for s in REGISTRY.values() for c in planning_contracts(s) if c.effect.kind == "Meet"]
    if len(cs) != 1:
        raise TuChoi("UNSUPPORTED_CAPABILITY", "thư viện không có đúng một hàm dựng giao điểm đường–mặt cho đỉnh thiết diện")
    return cs[0]


def _dinh_cat_canh(f: TypedFact, k: KeHoach, phat, kh: _Khoi) -> dict:
    """Section vertices of a derived plane on the edges the source says it cuts (`DINH_CAT_CANH`, run
    `typedfactnext-planner-bridge`). One typed need SectionVertex(edge, plane) per lateral edge, solved by the cheapest
    candidate whose effect is already established: the plane's own through-point when its validated producer lies on that
    edge, or an identical intersection already planned (cost 0); otherwise a NEW call of the Registry `Meet` producer
    named as the source names it (cost 1) or with a fresh `I…` label (cost 1). An unstated edge takes a cost-0 reuse —
    and, only for a `/2` fact (`derive_cuts`) whose section must close (a derived solid stands on it, or the author declared
    a boundary through that edge), a DERIVED vertex (cost 2, `derived_fresh`, run `hybrid-contract-v2` D6): never named
    with a source label, never stated, checked by the engine (0 < t ≤ 1, closure certificate). The gate binds the cut
    clause; it never asserts a cut the source did not state."""
    fn, hd = _hop_dong_giao_diem()
    d = next((x for x in k.derived_planes.values() if f.id in x["targets"]), None)
    if d is None:
        raise TuChoi("AUXILIARY_RULE_MISMATCH", f"{f.id}: cạnh bị cắt cần một mặt dẫn xuất đã khai", (f.id,))
    stated = [tuple(e) for e in f.cut_edges]
    names = list(f.cut_points) if f.cut_points else [None] * len(stated)
    if d.get("cut") not in (None, {"edges": [list(e) for e in stated], "points": names}):
        raise TuChoi("AMBIGUOUS_FACT", f"{f.id}: hai cách nêu cạnh bị cắt cho cùng một mặt", (f.id,))
    d["cut"] = {"edges": [list(e) for e in stated], "points": names}
    canh = _canh_ben(kh)
    if lac := [e for e in stated if frozenset(e) not in {frozenset(x) for x in canh}]:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: {[''.join(e) for e in lac]} không phải cạnh bên của {kh.ten}", (f.id,))
    plane, p = [d["point"], *d["labels"]], d["point"]
    ten = dict(zip(map(frozenset, stated), names))
    cert = {"rule": DINH_CAT_CANH, "goal": f.id, "plane_goal": d["goal"], "point": p, "plane": plane, "solid": kh.ten,
            "stated_edges": [list(e) for e in stated], "stated_points": names, "vertices": [], "constructs": [],
            "labels": [], "quotes": list(d["quotes"]), "provenance": "DERIVED", "binding": "AUXILIARY"}
    r = k.resolver
    # D6 scope: a vertex is derived only where a closed boundary is REQUIRED — a derived solid stands on this section, or
    # the author's declared boundary passes through that edge (to be verified, not trusted).
    khep = bool(f.derive_cuts) and any(x.plane_ref == f.id for x in r.facts.values())
    if not stated and not khep and f.boundary_edges is None:
        return
    bien = {frozenset(x) for x in f.boundary_edges or ()} if f.derive_cuts else set()
    if f.derive_cuts:
        cert["derive"] = True
    if f.boundary_edges is not None:
        cert["declared_boundary"] = [list(x) for x in f.boundary_edges]
    for u, v in canh:
        e = frozenset((u, v))
        r.needs += 1
        if r.needs > MAX_EFFECT_NEEDS:
            raise TuChoi("PLAN_TOO_LARGE", "quá trần typed needs")
        choices = []                                  # (cost, kind, label, call id, producer id)
        # The through-point's producer is read from the FACTS (its call carries the fact id), so the choice does not depend
        # on the order facts are mapped in.
        tren_canh = next((x for x in r.facts.values() if x.kind == "point_def" and x.role == "premise" and not x.negated
                          and x.point_kind in ("midpoint", "divide_segment") and x.point == p
                          and frozenset(x.points or ()) == e), None)
        if tren_canh is not None:
            choices.append((0, "reuse_through_point", p, None, tren_canh.id))
        if p in e:
            choices.append((0, "reuse_through_point", p, None, None))
        cu = next((c for c in k.calls if c["fn"] == fn and frozenset(c["args"]["line"]) == e
                   and c["args"]["plane"] == plane), None)
        if cu is not None:
            choices.append((0, "reuse_intersection", cu["args"]["point"], cu["id"], None))
        if e in ten:
            choices.append((1, "named_intersection", ten[e], None, None) if ten[e] else (1, "fresh_intersection", None, None, None))
        if not choices and (khep or e in bien):
            choices.append((2, "derived_fresh", None, None, None))
        r.candidates += len(choices)
        if r.candidates > MAX_EFFECT_CANDIDATES * MAX_EFFECT_NEEDS:
            raise TuChoi("PLAN_TOO_LARGE", "quá trần candidate")
        if not choices:
            continue                                  # unstated edge with nothing established on it: no vertex claimed
        cost, kind, label, call_id, producer = min(choices, key=lambda x: (x[0], x[1]))
        if e in ten and ten[e] and label != ten[e]:   # the source names the cut otherwise than the point already there
            raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: giao điểm trên {u}{v} được gọi {ten[e]} nhưng đã là {label}",
                         (f.id,))
        if cost:
            if kind in ("fresh_intersection", "derived_fresh"):
                r.feet += 1
                if r.feet > MAX_RESULT_FEET:
                    raise TuChoi("PLAN_TOO_LARGE", "quá trần điểm tươi")
                if "I" not in r.quet:
                    r.quet.add("I")
                    k.taken |= nhan_phu_da_dung(r.text, "I")
                label = next((n for n in _nhan_tuoi("I") if n not in k.taken), None)
                if label is None:
                    raise TuChoi("PLAN_TOO_LARGE", "hết nhãn điểm phụ")
                k.taken.add(label)
                cert["labels"].append(label)
            dung = {c["id"] for c in k.calls}
            call_id = next(j for j in (f"{f.id}_cut{len(cert['vertices']) + 1}", *(f"{f.id}_cut_{n}" for n in range(2, 1000)))
                           if j not in k.fact_ids | dung)
            phat(call_id, fn, render_call(hd, {"X": label, "L": [u, v], "Q": plane}), d["quotes"],
                 f"{DINH_CAT_CANH}→{fn} ({kind})")
            k.trace[-1]["fact"] = f.id
            cert["constructs"].append(call_id)
        cert["vertices"].append({"edge": [u, v], "label": label, "choice": kind, "call": call_id, "producer": producer,
                                 "stated": e in ten})
        k.trace.append({"fact": f.id, "step": "effect_resolution", "need": f"SectionVertex({u}{v}, plane through {p})",
                        "selection": kind, "cost": cost, "candidates": len(choices), "label": label})
    if missing := [list(e) for e in stated if not any(frozenset(x["edge"]) == frozenset(e) for x in cert["vertices"])]:
        raise TuChoi("AUXILIARY_RULE_MISMATCH", f"{f.id}: cạnh bị cắt {missing} không có đỉnh thiết diện", (f.id,))
    k.auxiliary.append(cert)
    k.trace.append({"fact": f.id, "step": "decompose_goal", "rule": DINH_CAT_CANH, "calls": list(cert["constructs"]),
                    "auxiliary": list(cert["labels"]), "reused": [x["label"] for x in cert["vertices"] if not x["call"]
                                                                 or x["choice"] == "reuse_intersection"],
                    "provenance": "DERIVED", "binding": "AUXILIARY"})
    return cert


def _khoi_tren_thiet_dien(f: TypedFact, k: KeHoach, phat, khoi_cua) -> dict:
    """Derived pyramid "khối chóp đỉnh S cắt bởi (α)": apex = the parent pyramid's apex, base = the section vertices on
    EVERY lateral edge in base order (each established by `_dinh_cat_canh`); an open cycle is refused, never closed by
    guessing. Registered as a solid so later goals (ratio, residual) can name it by its vertices."""
    sec = next((x for x in k.auxiliary if x.get("rule") == DINH_CAT_CANH and x["goal"] == f.plane_ref), None)
    if sec is None:
        raise TuChoi("AUXILIARY_RULE_MISMATCH", f"{f.id}: thiết diện {f.plane_ref} chưa có đỉnh trên cạnh bị cắt", (f.id,))
    kh = next(x for x in k.solids.values() if x.ten == sec["solid"])
    if kh.loai != "pyramid" or kh.dinh != f.point:
        raise TuChoi("UNSUPPORTED_CAPABILITY", f"{f.id}: khối dựng trên thiết diện cần đỉnh {kh.dinh} của chóp {kh.ten}",
                     (f.id,))
    dinh = {frozenset(x["edge"]): x["label"] for x in sec["vertices"]}
    if any(frozenset(e) not in dinh for e in _canh_ben(kh)):
        raise TuChoi("SECTION_NOT_CLOSED_ON_LATERAL_EDGES", f"{f.id}: thiết diện chưa có đỉnh trên mọi cạnh bên của {kh.ten}",
                     (f.id,))
    vong = [dinh[frozenset(e)] for e in _canh_ben(kh)]
    if len(set(vong)) < 3:
        raise TuChoi("DEGENERATE_DERIVED_SECTION", f"{f.id}: thiết diện có ít hơn 3 đỉnh phân biệt", (f.id,))
    ten = f"{kh.dinh}.{''.join(vong)}"
    if ten in k.solids:
        raise TuChoi("AMBIGUOUS_REFERENCE", f"{f.id}: khối {ten} đã được khai", (f.id,))
    phat(f.id, "pyramid", {"apex": kh.dinh, "base": vong}, list(f.quotes), f"{DINH_CAT_CANH}→pyramid (khối trên thiết diện)")
    k.solids[ten] = _Khoi(ten, ten, "pyramid", vong, dinh=kh.dinh, fact=f.id, quotes=list(f.quotes), kieu="pyramid")
    sec["derived"] = {"call": f.id, "apex": kh.dinh, "base": vong, "quotes": list(f.quotes)}
    k.trace.append({"fact": f.id, "step": "decompose_goal", "rule": DINH_CAT_CANH, "goal": f"Pyramid({kh.dinh}, Section)",
                    "dependencies": [sec["goal"], *vong], "calls": [f.id], "provenance": "DERIVED", "binding": "AUXILIARY"})
    return sec


def _phan_ra(f: TypedFact, q: list[str], k: KeHoach, phat, p: str, dt: list[str]) -> dict:
    return k.resolver.distance(f, p, ("named", tuple(sorted(dt))))


@dataclass
class _Choice:
    fn: str | None
    env: dict
    inputs: list["_Choice"] = field(default_factory=list)
    existing: dict | None = None
    cost: int = 0
    contract: Any = None


#: Source policies of contracts that are a declared decomposition's step: the foot of `distance(point,line)`, a section
#: vertex on a stated cut edge (`DINH_CAT_CANH`), a declared intersection line (`registry.AUXILIARY_RULES`).
_RULE_POLICIES = frozenset({"projection_foot", "distance_witness", "section_vertex", "declared_intersection"})


def _nguon_goc_buoc(k: KeHoach) -> dict[str, list[str]]:
    """Planner-made steps by provenance (C16). Untagged ones come from a declared decomposition."""
    own = [c["id"] for c in k.calls if c["id"] not in k.fact_ids]
    tag = {i: k.step_provenance.get(i, "registered") for i in own}
    return {"planner_originated_steps": own,
            "source_defined_steps": [i for i in own if tag[i] == "source_defined"],
            "registered_decomposition_steps": [i for i in own if tag[i] == "registered"],
            "search_generated_steps": [i for i in own if tag[i] == "search_generated"]}


def _loai(v) -> str | None:
    """Kind of a typed-need operand: a point (label, or `("desc", kind, operands)` for an unnamed described point), a line
    (`("named", (X, Y))` / `("result", fact_id)`) or a plane (≥ 3 labels)."""
    if isinstance(v, str) or (isinstance(v, tuple) and v[:1] == ("desc",)):
        return "Point"
    if isinstance(v, tuple) and len(v) == 2 and v[0] in ("named", "result"):
        return "Line"
    if isinstance(v, tuple) and len(v) >= 3 and all(isinstance(x, str) for x in v):
        return "Plane"
    return None


class _EffectResolver:
    """Bounded backward search over Registry effects. A need (kind + operands) is solved by every contract whose effect has
    that kind and kind-compatible operands — its inputs become sub-needs; a call already in the plan with the same effect
    is reused at cost 0; the cheapest choice wins (ties by function name, never by catalog order). Calls are WRITTEN from
    the winner's contract template (`registry.render_call`), so a function the planner never names can be used once its
    contract is registered. Proposed bindings are NEVER geometric truth: the gate and the engine re-check them."""

    def __init__(self, facts, plan, emit, text=""):
        self.facts = {f.id: f for f in facts}
        self.plan, self.emit, self.text = plan, emit, text
        self.needs = self.candidates = self.feet = self.depth_max = self.reused = 0  # feet: every fresh point (feet, unnamed operands)
        self.trail: list[dict] = []
        self.quet = {"H"}                     # label stems already scanned in the text (`lap_ke_hoach` scans H itself)
        self.lines = set()
        self.used = False
        self.active = set()
        self.memo = {}
        groups = {}
        for f in facts:
            if (f.kind=='intersection_line' and f.role in ('premise','question') and not f.negated
                    and all(len(p or [])==3 and len(set(p))==3 for p in (f.points_a,f.points_b))):
                key=tuple(sorted((tuple(sorted(f.points_a)),tuple(sorted(f.points_b)))))
                groups.setdefault(key,[]).append(f.id)
        self.aliases = {fid:min(ids) for ids in groups.values() for fid in ids}

    def _exhausted(self, msg: str) -> TuChoi:
        return TuChoi("PLAN_TOO_LARGE", msg, data={"outcome": "SEARCH_EXHAUSTED", "explored_states": self.needs,
                                                   "candidate_evaluations": self.candidates, "search_depth": self.depth_max})

    def _resolve(self, kind, operands, depth=0):
        key = (kind, operands)
        if not kind.startswith('Answer') and key in self.memo:
            return self.memo[key]  # available producer binding only; Engine still verifies every given later
        self.needs += 1
        if self.needs > MAX_EFFECT_NEEDS:
            raise self._exhausted("quá trần typed needs")
        if key in self.active:
            raise TuChoi("DEPENDENCY_CYCLE", "typed need phụ thuộc chính nó")
        self.depth_max = max(self.depth_max, depth)
        if kind in ('Point', 'Line', 'Plane') and _loai(operands[0]) != kind:
            raise TuChoi('UNSUPPORTED_CAPABILITY', f'typed need {kind} không khớp kiểu toán hạng')
        if kind == 'Plane' or (kind == 'Point' and isinstance(operands[0], str)):
            if not all(p in self.plan.taken for p in (operands[0] if kind == 'Plane' else operands)):
                raise TuChoi('UNSUPPORTED_CAPABILITY', f'typed need {kind} không khớp kiểu toán hạng')
            return _Choice(None, {})
        if kind == "Line" and operands[0][0] == "named":
            return _Choice(None, {})
        if depth >= MAX_EFFECT_DEPTH:
            raise self._exhausted("quá trần phân rã effect")
        self.active.add(key)
        choices = []
        try:
            contracts = [(s,c) for s in sorted(REGISTRY.values(), key=lambda s: s.name) for c in planning_contracts(s)]
            for spec, contract in contracts:
                if contract.effect.kind != kind or len(contract.effect.operands) != len(operands):
                    continue
                desc = operands[0] if kind == 'Point' else None      # an unnamed point: only producers of its description
                if desc and (contract.descriptor != desc[1] or len(contract.inputs) != len(desc[2])):
                    continue
                typed = {t.operands[0]: t.kind for t in contract.inputs if t.kind in ('Point', 'Line', 'Plane')}
                if any(v is not None and typed.get(s, _loai(v)) != _loai(v) for s, v in zip(contract.effect.operands, operands)):
                    continue  # an operand of the wrong kind is not a candidate; excluded before it is counted
                self.candidates += 1
                if self.candidates > MAX_EFFECT_CANDIDATES:
                    raise self._exhausted("quá trần candidate")
                env = dict(zip(contract.effect.operands, operands))
                if desc:
                    env.update(zip((t.operands[0] for t in contract.inputs), desc[2]))
                existing = None
                if contract.source_policy == "declared_intersection":
                    ref = env["L"][1]
                    producer = self.facts[ref]
                    env.update(A=tuple(producer.points_a), B=tuple(producer.points_b))
                    existing = next((c for c in self.plan.calls if c['id'] == ref and c['fn'] == spec.name), None)
                    if existing is None:
                        continue
                    self.lines.add(ref)
                    if len(self.lines) > MAX_RESULT_LINES:
                        raise self._exhausted("quá trần line results")
                try:
                    children = [self._resolve(term.kind, tuple(env.get(slot) for slot in term.operands), depth+1)
                                for term in contract.inputs]
                except TuChoi as e:
                    if e.code=='UNSUPPORTED_CAPABILITY':
                        continue  # exclude incompatible symbolic candidates; never skip a geometric/source failure
                    raise
                cost = sum(c.cost for c in children)
                if contract.fresh:              # the source (or an earlier goal) may already hold this exact construction
                    out = contract.effect.operands[0]
                    arg = next(a for a, s in contract.call if s == out)
                    check_env = dict(env)
                    can_reuse = True
                    for t_in, child in zip(contract.inputs, children):
                        if child.fn is not None:
                            if child.existing is None:
                                can_reuse = False
                                break
                            check_env.update({s: child.env[c_op] for s, c_op in zip(t_in.operands, child.contract.effect.operands)})
                    if can_reuse and not any(
                        isinstance(v, tuple) and v and v[0] == "desc"
                        for k_slot, v in check_env.items()
                        if k_slot != out
                    ):
                        for c in self.plan.calls:
                            if c['fn'] != spec.name:
                                continue
                            bound = {**check_env, out: c['args'].get(arg)}
                            if same_call(contract, render_call(contract, bound), c['args']):
                                self.candidates += 1
                                if self.candidates > MAX_EFFECT_CANDIDATES:
                                    raise self._exhausted('quá trần available-binding candidates')
                                choices.append(_Choice(spec.name, bound, children, c, cost, contract))
                    cost += 1
                choices.append(_Choice(spec.name, env, children, existing, cost, contract))
            if not choices:
                raise TuChoi("UNSUPPORTED_CAPABILITY", f"không effect nào giải được {kind}")
            selected = min(choices, key=lambda c: (c.cost, c.fn, _nhan_ra(c), c.existing['id'] if c.existing else ''))
            if not kind.startswith('Answer'):
                self.memo[key]=selected
            return selected
        finally:
            self.active.remove(key)

    def _emit(self, choice, fact):
        if choice.fn is None:
            return choice.env
        contract = choice.contract
        env = dict(choice.env)
        for t, child in zip(contract.inputs, choice.inputs):  # an input slot takes its producer's effect, by position
            got = self._emit(child, fact)
            if child.fn is not None:
                env.update({s: got[c] for s, c in zip(t.operands, child.contract.effect.operands)})
        if choice.existing:
            if not contract.effect.kind.startswith('Answer'):
                self.reused += 1
            self._ghi(choice.existing, env, contract)
            return env
        if not contract.call:
            raise TuChoi('UNSUPPORTED_CAPABILITY', 'producer chưa được khai trong nguồn')
        answer = contract.effect.kind.startswith('Answer')
        if contract.fresh:
            self.feet += 1
            if self.feet > MAX_RESULT_FEET:
                raise self._exhausted("quá trần điểm tươi")
            if contract.fresh not in self.quet:
                self.quet.add(contract.fresh)
                self.plan.taken |= nhan_phu_da_dung(self.text, contract.fresh)
            x = next((n for n in _nhan_tuoi(contract.fresh) if n not in self.plan.taken), None)
            if x is None:
                raise self._exhausted("hết nhãn điểm phụ")
            self.plan.taken.add(x)
            env[contract.effect.operands[0]] = x
        cid = fact.id if answer else next(i for i in (f'{fact.id}_aux', *(f'{fact.id}_aux{n}' for n in range(2,1000)))
                                          if i not in self.plan.fact_ids | {c['id'] for c in self.plan.calls})
        call = self.emit(cid, choice.fn, render_call(contract, env), fact.quotes, f'effect({contract.effect.kind})→{choice.fn}')
        self.plan.trace[-1]['fact'] = fact.id
        if not answer:                     # provenance at emission (C16): what put this step in the plan
            self.plan.step_provenance[cid] = ('source_defined' if contract.descriptor
                                              else 'registered' if contract.source_policy in _RULE_POLICIES
                                              else 'search_generated')
        self._ghi(call, env, contract)
        if not answer:
            choice.env.update(env)
            choice.existing, choice.cost = call, 0
        return env

    def _ghi(self, call, env, contract):
        """Trail of the goal being resolved: the calls of its derivation, each with the slot bindings it was written from."""
        if all(e['call'] != call['id'] for e in self.trail):
            self.trail.append({'call': call['id'], 'fn': call['fn'], 'env': json.loads(json.dumps(env)),
                               'fresh': call['id'] not in self.plan.fact_ids})
            if contract is not REGISTRY[call['fn']].planning:
                self.trail[-1]['effect'] = contract.effect.kind
                if contract.descriptor:
                    self.trail[-1]['descriptor'] = contract.descriptor

    def goal(self, fact, entries):
        """Typed semantic entry: quantity + the typed slots its operands fill select ONE contract effect (several ⇒
        ambiguous, none ⇒ incomplete); operands carry no function recipe."""
        if fact.point_kind:
            parsed = [(c, ops) for c in entries if (ops := _toan_hang_muc_tieu(fact, c)) is not None]
            if not parsed:
                raise TuChoi('FACT_INCOMPLETE', 'số toán hạng không khớp hợp đồng mục tiêu', (fact.id,))
            entries, operands = [c for c, _ops in parsed], parsed[0][1]
        else:
            operands = tuple(fact.points or (fact.points_a or []) + (fact.points_b or []))
        kinds = {c.effect.kind for c in entries}
        if len(kinds) != 1:
            raise TuChoi('AMBIGUOUS_FACT', 'mục tiêu có nhiều cách hiểu kiểu', (fact.id,))
        if not any(len(c.effect.operands) == len(operands) for c in entries):
            raise TuChoi('FACT_INCOMPLETE', 'số toán hạng không khớp hợp đồng mục tiêu', (fact.id,))
        self.used, self.trail = True, []
        choice = self._resolve(next(iter(kinds)), operands)
        env = self._emit(choice, fact)
        if fact.point_kind:
            return self._chuoi(fact, operands[0], _dich_muc_tieu(choice.contract, operands), choice, env)
        return next(c for c in self.plan.calls if c['id'] == fact.id)

    def distance(self, fact, point, line):
        self.used = True
        if line[0]=='result':
            line=('result',self.aliases.get(line[1],line[1]))
        self.trail = []
        choice = self._resolve('AnswerDistance', (point,line))
        env = self._emit(choice, fact)
        if not isinstance(point, str):
            return self._chuoi(fact, point, line, choice, env)
        foot = next((c for c in self.plan.calls if c['fn']=='orthogonal_projection_line'
                     and c['args']['point']==point and c['args']['image']==env.get('F')), None)
        if foot is None:                                  # a resolution that wrote no foot is refused, never a crash
            raise TuChoi('AUXILIARY_RULE_MISMATCH', f'{fact.id}: phân giải không viết chân vuông góc', (fact.id,))
        cert = {'label':env['F'], 'rule':'distance(point,line)', 'goal':fact.id, 'construct':foot['id'], 'ask':fact.id,
                'point':point, 'line':list(line[1]) if line[0]=='named' else [],
                'quotes':list(dict.fromkeys(fact.quotes)), 'provenance':'DERIVED', 'binding':'AUXILIARY'}
        # Preserve the old source certificate for a fresh named-line foot; reuse that validator instead of duplicating it.
        if line[0]=='result' or choice.cost==0:
            cert.update(line_ref=line[1] if line[0]=='result' else None,
                        fresh=foot['id'] not in self.plan.fact_ids,effect_binding=True)
        self.plan.auxiliary.append(cert)
        self.plan.trace.append({'fact':fact.id,'step':'decompose_goal','rule':cert['rule'],
                                'calls':[foot['id'],fact.id], 'auxiliary':env['F'],
                                'provenance':'DERIVED','binding':'AUXILIARY'})
        self.plan.trace.append({'fact':fact.id,'step':'effect_resolution','selection':'registry-effects',
                                'new_constructions':choice.cost})
        return next(c for c in self.plan.calls if c['id']==fact.id)

    def point(self, fact, point_term):
        self.used, self.trail = True, []
        choice = self._resolve('Point', (point_term,))
        env = self._emit(choice, fact)
        out = env[choice.contract.effect.operands[0]]
        fresh = [e['env'][pc.effect.operands[0]] for e in self.trail
                 if e['fresh'] and (pc := planning_contract(REGISTRY[e['fn']], e.get('effect'), e.get('descriptor'))) and pc.fresh]
        return out, list(self.trail), fresh

    def _chuoi(self, fact, point, target, choice, env):
        """`effect-chain` certificate of a goal on an unnamed described point: the trail of calls with their bindings, the
        goal (description + target) and the fresh labels. The gate re-writes every call from its contract; the engine checks
        the description and the answer on the built figure."""
        answer = choice.contract
        fresh = [(e, pc) for e in self.trail
                 if e['fresh'] and (pc := planning_contract(REGISTRY[e['fn']], e.get('effect'), e.get('descriptor'))) and pc.fresh]
        cert = {'rule': 'effect-chain', 'effect_binding': True, 'goal': fact.id, 'ask': fact.id,
                'operand': {'descriptor': point[1], 'points': list(fact.points), 'label': env[answer.effect.operands[0]]},
                'target': (target if isinstance(target, dict) else {'point': target} if isinstance(target, str)
                           else {'points': list(target[1])} if target[0] == 'points'
                           else {'line_ref': target[1]} if target[0] == 'result'
                           else {'line': list(target[1])} if target[0] == 'named'
                           else {'plane': list(target)}),
                'chain': self.trail,
                'labels': [e['env'][pc.effect.operands[0]] for e, pc in fresh],
                'quotes': list(dict.fromkeys(fact.quotes)), 'provenance': 'DERIVED', 'binding': 'AUXILIARY'}
        if isinstance(target, tuple) and target[0] == 'result':
            cert['line_ref'] = target[1]
        self.plan.auxiliary.append(cert)
        self.plan.trace.append({'fact': fact.id, 'step': 'decompose_goal', 'rule': cert['rule'],
                                'calls': [e['call'] for e in self.trail], 'auxiliary': cert['labels'],
                                'provenance': 'DERIVED', 'binding': 'AUXILIARY'})
        self.plan.trace.append({'fact': fact.id, 'step': 'effect_resolution', 'selection': 'registry-effects',
                                'new_constructions': len([e for e in self.trail if e['fresh'] and e['call'] != fact.id]),
                                'needs': self.needs, 'candidates': self.candidates, 'depth': self.depth_max})
        return next(c for c in self.plan.calls if c['id'] == fact.id)


def _dich_muc_tieu(contract, operands) -> dict:
    """Certificate target of a goal contract from its typed slots after the measured point (`registry.goal_target_keys`
    names the same keys): one point / several points / a plane / a named line."""
    rest = list(zip((k for _s, k in goal_slots(contract)[1:]), operands[1:]))
    pts = [v for k, v in rest if k == "Point"]
    t: dict = {"point": pts[0]} if len(pts) == 1 else {"points": list(pts)} if pts else {}
    t.update({"plane": list(v) for k, v in rest if k == "Plane"})
    t.update({"line": list(v[1]) for k, v in rest if k == "Line"})
    return t


def _nhan_ra(c: _Choice) -> str:
    """Output label of an available-binding choice (tie-break); '' for a new construction or an answer."""
    contract = c.contract
    x = c.env.get(contract.effect.operands[0]) if contract.fresh else None
    return x if isinstance(x, str) else ''


def _bind_result_dependencies(k):
    """Call edges are a view of the existing producers, not another FactGraph."""
    solid_pts = {v for kh in k.solids.values() for v in (*kh.day, *kh.tren, *([kh.dinh] if kh.dinh else ()))}
    producers = {}
    curved_by_solid = {}
    for c in k.calls:
        a, fn = c['args'], c['fn']
        if fn == 'curved_solid' and isinstance(a.get('solid'), str):
            curved_by_solid[a['solid']] = c['id']
        label = (a.get('image') if fn in ('orthogonal_projection_line','orthogonal_projection','translate_point')
                 else a.get('point') if fn in (*POINT_PRODUCERS, 'sphere_tangent_plane')
                 else a.get('center') if fn == 'curved_solid' and a.get('center') not in solid_pts
                 else None)
        if label:
            producers.setdefault(label, []).append(c['id'])
    for c in k.calls:
        a = c['args']
        points = [x for v in a.values() if isinstance(v,list) for x in v]
        if c['fn'].startswith('orthogonal_projection') or c['fn']=='translate_point' or c['fn'].startswith('ask_'):
            points += [a['point']] if isinstance(a.get('point'), str) else []
        output = (a.get('image')
                  or (a.get('point') if c['fn'] in (*POINT_PRODUCERS, 'sphere_tangent_plane') else None)
                  or (a.get('center') if c['fn'] == 'curved_solid' else None))
        if output:
            points = [x for x in points if x != output]
        deps = {p for x in points for p in producers.get(x,()) if p != c['id']}
        if c['fn'] == 'sphere_tangent_plane' and a.get('solid') in curved_by_solid:
            deps.add(curved_by_solid[a['solid']])
        if a.get('line_ref'):
            deps.add(a['line_ref'])
        c['depends_on'] = sorted(deps)
    doc_ke_hoach({'calls':k.calls})  # existing cycle/dangling/type authority
