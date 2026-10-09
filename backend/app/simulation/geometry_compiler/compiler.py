# -*- coding: utf-8 -*-
"""PRIMITIVE COMPILER — `GeometryFactGraph` → `SemanticProgramSpec`. 0 lượt gọi model.

`GEOMETRY_FACT_GRAPH_AND_PRIMITIVE_COMPILER_VERTICAL_SLICE` (2026-09-20).

Lát cắt dọc ĐẦU TIÊN: một họ bài (hình chóp có đáy là tam giác vuông, cạnh bên
vuông góc với đáy, hỏi thể tích) được dựng thành chương trình, cảnh, quá trình
dựng và đáp số **mà không gọi synthesis**.

─── KHÔNG PHẢI SPATIAL LAYOUT SOLVER ───────────────────────────────────────

Bố cục ở đây là một **canonical construction** cho đúng họ ấy: đỉnh vuông của
đáy ở gốc, hai cạnh góc vuông theo hai trục độc lập, đỉnh chóp theo pháp tuyến.
Độ dài lấy THẲNG từ FactGraph. Không số nào viết cứng. Đừng gọi nó là solver.

─── MỌI TOẠ ĐỘ LÀ `LAYOUT_DERIVED` ─────────────────────────────────────────

Compiler CHỌN hệ toạ độ; đề không cho. Fact toạ độ vì thế mang `DERIVED` và nút
mang `LAYOUT_DERIVED`. Ghi chúng thành `GIVEN` là biến lựa chọn trình bày thành
lời khai về đề — `test` bắt đúng điều đó.

─── KHÔNG ĐI VÒNG QUA CỔNG NÀO ─────────────────────────────────────────────

Chương trình sinh ra đi qua `validator.validate_semantic_program` y như chương
trình do mô hình viết. Mã nội bộ KHÔNG được miễn kiểm, và compiler KHÔNG tự sửa
đầu ra sau khi validator từ chối — nó trả trạng thái để caller quyết.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from ..geometry.radical import sqrt_rational
from . import primitives as P
from .fact_graph import Fact, GeometryFactGraph, MauThuanFact, kiem_mau_thuan

COMPILER_VERSION = "geometry-primitive-compiler/1"

#: Họ bài lát cắt này hỗ trợ.
SUPPORTED_FAMILY = "right_triangle_base_pyramid_volume"
SUPPORTED_FAMILY_PRISM = "right_triangle_base_right_prism_volume"
SUPPORTED_FAMILY_RECT_PYRAMID = "rectangular_base_pyramid_volume"
SUPPORTED_FAMILY_CUBOID = "rectangular_cuboid_volume"
SUPPORTED_FAMILY_CUBE = "cube_volume"
SUPPORTED_FAMILY_SQUARE_PRISM = "right_square_prism_volume"
#: G04 — lăng trụ XIÊN: đáy tam giác vuông hoặc chữ nhật/vuông, chân đường cao hạ từ một đỉnh đáy trên
#: rơi vào một đỉnh đáy dưới (quan hệ `line ⟂ plane` CÓ CẤU TRÚC), chiều cao hữu tỉ.
SUPPORTED_FAMILY_OBLIQUE_PRISM = "oblique_prism_volume"
SUPPORTED_FAMILIES = (
    SUPPORTED_FAMILY,
    SUPPORTED_FAMILY_PRISM,
    SUPPORTED_FAMILY_RECT_PYRAMID,
    SUPPORTED_FAMILY_CUBOID,
    SUPPORTED_FAMILY_CUBE,
    SUPPORTED_FAMILY_SQUARE_PRISM,
    SUPPORTED_FAMILY_OBLIQUE_PRISM,
)

TRANG_THAI_ELIGIBILITY: tuple[str, ...] = (
    "SUPPORTED",
    "UNSUPPORTED_MISSING_FACT",
    "UNSUPPORTED_EXTRA_OBLIGATION",
    "UNSUPPORTED_SYMBOLIC_LENGTH",
    #: Dữ kiện đủ và nhất quán nhưng toạ độ cần căn (chiều cao √ từ cạnh bên) — ngoài miền ℚ³ của bố cục.
    "UNSUPPORTED_IRRATIONAL_LAYOUT",
    #: Đề CÓ THỂ nói rõ *"SA vuông góc với (ABC)"* bằng câu chữ — nhưng không ai
    #: khai nó thành quan hệ CÓ CẤU TRÚC. Đây là phán quyết cố ý của `/2`, không
    #: phải một lỗ hổng: tầng dựng không đọc câu chữ.
    "UNSUPPORTED_STRUCTURED_RELATION_MISSING",
    "INVALID_CONFLICT",
    "INVALID_NON_POSITIVE_LENGTH",
)

TRANG_THAI_COMPILE: tuple[str, ...] = ("COMPILED", "NOT_ELIGIBLE", "PROGRAM_REJECTED")


@dataclass(frozen=True)
class RangBuocHo:
    """Các vai đã phân xử được của họ bài — TÊN, không phải số."""

    dinh_vuong: str
    chan_1: str
    chan_2: str
    dinh_chop: str
    len_1: Fraction
    len_2: Fraction
    len_cao: Fraction
    witness: str
    container: str
    source_fact_ids: tuple[str, ...]


@dataclass(frozen=True)
class RangBuocPrism:
    """Các vai đã phân xử được của họ lăng trụ đứng đáy tam giác vuông."""

    family_id: str
    base_cycle: tuple[str, ...]
    top_cycle: tuple[str, ...]
    correspondence: tuple[tuple[str, str], ...]
    dinh_vuong_day: str
    chan_1: str
    chan_2: str
    dinh_vuong_top: str
    chan_1_top: str
    chan_2_top: str
    len_1: Fraction
    len_2: Fraction
    len_cao: Fraction
    witness: str
    container: str
    source_fact_ids: tuple[str, ...]


@dataclass(frozen=True)
class RangBuocRectPyramid:
    """Các vai đã phân xử được của họ chóp đáy chữ nhật/vuông."""

    family_id: str
    variant: str  # "rectangle" | "square"
    apex: str
    foot: str
    base_cycle: tuple[str, ...]
    adj_1: str
    adj_2: str
    opposite: str
    len_adj1: Fraction
    len_adj2: Fraction
    len_height: Fraction
    witness: str
    container: str
    source_fact_ids: tuple[str, ...]


@dataclass(frozen=True)
class RangBuocCuboid:
    """Ràng buộc cho họ lăng trụ đứng tứ giác (cuboid, cube, right square prism)."""

    family_id: str
    solid_subkind: str  # "cuboid" | "cube" | "right_square_prism"
    base_shape: str     # "rectangle" | "square"
    base_cycle: tuple[str, ...]
    top_cycle: tuple[str, ...]
    correspondence: tuple[tuple[str, str], ...]
    base_cycle_ids: tuple[str, ...]
    top_cycle_ids: tuple[str, ...]
    correspondence_ids: tuple[tuple[str, str], ...]
    display_labels: dict[str, str]
    origin_pt: str
    adj_1: str
    adj_2: str
    opposite: str
    origin_top: str
    len_adj1: Fraction
    len_adj2: Fraction
    len_height: Fraction
    witness: str
    container: str
    source_fact_ids: tuple[str, ...]
    source_grounding: str | None = None


@dataclass(frozen=True)
class RangBuocObliquePrism:
    """Lăng trụ xiên: bố cục đáy (ℚ³), đỉnh neo T trên pháp tuyến tại chân F, cạnh bên = vectơ B0→T."""

    family_id: str
    base_cycle: tuple[str, ...]
    top_cycle: tuple[str, ...]
    correspondence: tuple[tuple[str, str], ...]
    display_labels: dict[str, str]
    #: Toạ độ LAYOUT_DERIVED của đáy, theo thứ tự `base_cycle`.
    base_coords: tuple[tuple[Fraction, Fraction, Fraction], ...]
    #: Hai đoạn đáy ĐỀ CHO mà bố cục dùng (để khai độ dài + nối bước dựng về nguồn).
    base_segments: tuple[tuple[str, str], ...]
    anchor_top: str
    anchor_base: str
    foot: str
    height: Fraction
    #: Đoạn mang số đo dựng chiều cao: (T, F) khi đề cho chiều cao, (B0, T) khi suy từ cạnh bên.
    height_segment: tuple[str, str]
    witness: str
    container: str
    foot_source_fact_id: str | None
    source_fact_ids: tuple[str, ...]


@dataclass(frozen=True)
class KetQuaEligibility:
    status: str
    binding: (RangBuocHo | RangBuocPrism | RangBuocRectPyramid | RangBuocCuboid
              | RangBuocObliquePrism | None) = None
    reason_code: str | None = None
    diagnostics: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class BuocDung:
    """Một bước của quá trình dựng — sinh bằng TEMPLATE tất định, không LLM."""

    index: int
    primitive_id: str
    mo_ta: str
    source_fact_ids: tuple[str, ...] = ()
    derived_fact_ids: tuple[str, ...] = ()
    scene_object_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class KetQuaBienDich:
    status: str
    program: dict[str, Any] | None
    primitive_calls: tuple[P.LoiGoiPrimitive, ...] = field(default_factory=tuple)
    construction_steps: tuple[BuocDung, ...] = field(default_factory=tuple)
    derived_fact_ids: tuple[str, ...] = field(default_factory=tuple)
    compiler_version: str = COMPILER_VERSION
    elapsed_ms: float = 0.0
    reason_code: str | None = None
    #: TỪ VỰNG ĐÓNG — không chở nguyên văn đề, chương trình hay toạ độ.
    diagnostics: tuple[str, ...] = field(default_factory=tuple)


def _danh_gia_eligibility_prism(
    graph: GeometryFactGraph,
    topo: Any,
    ob: Fact,
) -> KetQuaEligibility:
    """Đánh giá tính hợp lệ cho họ lăng trụ đứng đáy tam giác vuông."""
    base_cycle = tuple(str(x) for x in topo.base_cycle)
    top_cycle = tuple(str(x) for x in topo.top_cycle)
    correspondence = tuple((str(u), str(v)) for u, v in topo.correspondence)
    corr_dict = dict(correspondence)

    if len(base_cycle) != 3:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "BASE_NOT_TRIANGLE")

    base_set = set(base_cycle)

    # 1. Đáy vuông: perpendicular_lines giữa 2 cạnh của tam giác đáy
    goc = [f for f in graph.fact_theo_loai("perpendicular_lines") if f.status == "GIVEN"]
    if not goc:
        return KetQuaEligibility(
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
            "BASE_PERPENDICULAR_RELATION_MISSING", ("perpendicular_lines",)
        )

    goc_day: list[tuple[str, str, str, Fact]] = []
    for f in goc:
        if len(f.args) != 4:
            continue
        d1, d2 = set(f.args[:2]), set(f.args[2:])
        if d1 <= base_set and d2 <= base_set:
            chung = d1 & d2
            if len(chung) == 1:
                dv = next(iter(chung))
                chans = sorted((d1 | d2) - {dv})
                if len(chans) == 2:
                    goc_day.append((dv, chans[0], chans[1], f))

    if not goc_day:
        return KetQuaEligibility(
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
            "BASE_PERPENDICULAR_RELATION_MISSING", ("perpendicular_lines",)
        )
    if len(goc_day) > 1:
        return KetQuaEligibility(
            "INVALID_CONFLICT", None, "STRUCTURED_RELATION_CONTRADICTION",
            ("MULTIPLE_RIGHT_ANGLE_VERTICES_IN_TRIANGLE",)
        )

    dinh_vuong, chan_1, chan_2, fact_goc_day = goc_day[0]

    # 2. Cạnh bên vuông góc đáy: perpendicular_line_plane
    lp = [f for f in graph.fact_theo_loai("perpendicular_line_plane") if f.status == "GIVEN"]
    if not lp:
        return KetQuaEligibility(
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING",
            ("LINE_PLANE_RELATION_MISSING", "perpendicular_line_plane")
        )

    valid_lp = []
    for f in lp:
        if len(f.args) < 5:
            continue
        duong, mat = set(f.args[:2]), set(f.args[2:])
        if mat == base_set:
            u_in_base = duong & base_set
            u_in_top = duong - base_set
            if len(u_in_base) == 1 and len(u_in_top) == 1:
                ub = next(iter(u_in_base))
                ut = next(iter(u_in_top))
                if corr_dict.get(ub) == ut:
                    valid_lp.append((f, ub, ut))

    if not valid_lp:
        return KetQuaEligibility(
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING",
            ("LINE_PLANE_RELATION_MISSING", "perpendicular_line_plane")
        )

    fact_lp, lp_base_pt, lp_top_pt = valid_lp[0]

    # 3. Độ dài cần thiết:
    f_len1 = graph.do_dai(dinh_vuong, chan_1)
    f_len2 = graph.do_dai(dinh_vuong, chan_2)
    f_height = None
    for u in (dinh_vuong, chan_1, chan_2):
        fh = graph.do_dai(u, corr_dict[u])
        if fh is not None:
            f_height = fh
            break

    if f_height is None:
        missing_elem = f"{dinh_vuong}{corr_dict[dinh_vuong]}"
        return KetQuaEligibility(
            "UNSUPPORTED_MISSING_FACT", None,
            "REQUIRED_FACT_MISSING",
            ("REQUIRED_LENGTH_MISSING", missing_elem)
        )
    if f_len1 is None:
        missing_elem = f"{dinh_vuong}{chan_1}"
        return KetQuaEligibility(
            "UNSUPPORTED_MISSING_FACT", None,
            "REQUIRED_FACT_MISSING",
            ("REQUIRED_LENGTH_MISSING", missing_elem)
        )
    if f_len2 is None:
        missing_elem = f"{dinh_vuong}{chan_2}"
        return KetQuaEligibility(
            "UNSUPPORTED_MISSING_FACT", None,
            "REQUIRED_FACT_MISSING",
            ("REQUIRED_LENGTH_MISSING", missing_elem)
        )

    # 4. Kiểm tra giá trị hữu tỉ dương
    gia_tri: dict[str, Fraction] = {}
    for k, f in (("canh_1", f_len1), ("canh_2", f_len2), ("cao", f_height)):
        try:
            gia_tri[k] = Fraction(str(f.value))
        except (ValueError, ZeroDivisionError, TypeError):
            return KetQuaEligibility("UNSUPPORTED_SYMBOLIC_LENGTH", None,
                                     "SYMBOLIC_LENGTH", (k,))
    khong_duong = sorted(k for k, v in gia_tri.items() if v <= 0)
    if khong_duong:
        return KetQuaEligibility("INVALID_NON_POSITIVE_LENGTH", None,
                                 "NON_POSITIVE_LENGTH", tuple(khong_duong))

    src_ids = tuple(sorted(
        {f.source_fact_id for f in (f_len1, f_len2, f_height) if f.source_fact_id}
        | ({fact_goc_day.source_fact_id} if fact_goc_day.source_fact_id else set())
        | ({fact_lp.source_fact_id} if fact_lp.source_fact_id else set())
    ))

    binding = RangBuocPrism(
        family_id="right_triangle_base_right_prism_volume",
        base_cycle=base_cycle,
        top_cycle=top_cycle,
        correspondence=correspondence,
        dinh_vuong_day=dinh_vuong,
        chan_1=chan_1,
        chan_2=chan_2,
        dinh_vuong_top=corr_dict[dinh_vuong],
        chan_1_top=corr_dict[chan_1],
        chan_2_top=corr_dict[chan_2],
        len_1=gia_tri["canh_1"],
        len_2=gia_tri["canh_2"],
        len_cao=gia_tri["cao"],
        witness=str(ob.value or "the_tich_lang_tru"),
        container=str(ob.args[1]),
        source_fact_ids=src_ids,
    )
    return KetQuaEligibility("SUPPORTED", binding)


def _danh_gia_eligibility_rectangular_pyramid(
    graph: GeometryFactGraph,
    topo: Any,
    ob: Fact,
) -> KetQuaEligibility:
    """Đánh giá tính hợp lệ cho họ chóp đáy chữ nhật/vuông."""
    base_cycle = tuple(str(x) for x in topo.base_cycle)
    if len(base_cycle) != 4:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "BASE_NOT_QUADRILATERAL")
    if len(set(base_cycle)) != 4:
        return KetQuaEligibility("INVALID_CONFLICT", None, "DUPLICATE_VERTICES")

    apex = str(topo.apex)
    if apex in set(base_cycle):
        return KetQuaEligibility("INVALID_CONFLICT", None, "APEX_IN_BASE")

    base_set = set(base_cycle)

    # 1. Cạnh bên vuông góc đáy: perpendicular_line_plane
    lp = [f for f in graph.fact_theo_loai("perpendicular_line_plane") if f.status == "GIVEN"]
    if not lp:
        return KetQuaEligibility(
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
            "LINE_PLANE_RELATION_MISSING", ("perpendicular_line_plane",)
        )

    valid_lp: list[tuple[Fact, str]] = []
    for f in lp:
        if len(f.args) < 5:
            continue
        duong, mat = set(f.args[:2]), set(f.args[2:])
        if mat <= base_set and len(mat) >= 3:
            u_in_base = duong & base_set
            u_in_top = duong - base_set
            if len(u_in_base) == 1 and len(u_in_top) == 1:
                foot = next(iter(u_in_base))
                top_pt = next(iter(u_in_top))
                if top_pt == apex:
                    valid_lp.append((f, foot))

    if not valid_lp:
        return KetQuaEligibility(
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
            "LINE_PLANE_RELATION_MISSING", ("perpendicular_line_plane",)
        )

    fact_lp, foot = valid_lp[0]
    idx = [i for i, pt in enumerate(base_cycle) if pt == foot][0]
    adj_1 = base_cycle[(idx + 1) % 4]
    opp = base_cycle[(idx + 2) % 4]
    adj_2 = base_cycle[(idx - 1) % 4]

    # 2. Đáy vuông / hình chữ nhật:
    base_shape = getattr(topo, "base_shape", None)
    if base_shape is not None and base_shape not in ("rectangle", "square"):
        return KetQuaEligibility(
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
            "BASE_NOT_RECTANGLE", (base_shape,)
        )

    goc = [f for f in graph.fact_theo_loai("perpendicular_lines") if f.status == "GIVEN"]
    valid_goc_day: list[Fact] = []
    for f in goc:
        if len(f.args) != 4:
            continue
        d1, d2 = set(f.args[:2]), set(f.args[2:])
        if d1 <= base_set and d2 <= base_set:
            chung = d1 & d2
            if len(chung) == 1:
                c = next(iter(chung))
                ends = (d1 | d2) - {c}
                c_idx = [i for i, pt in enumerate(base_cycle) if pt == c][0]
                nbrs = {base_cycle[(c_idx + 1) % 4], base_cycle[(c_idx - 1) % 4]}
                if ends == nbrs:
                    valid_goc_day.append(f)
            elif len(chung) == 0:
                return KetQuaEligibility(
                    "INVALID_CONFLICT", None, "OPPOSITE_EDGES_PERPENDICULAR"
                )

    if base_shape is None and not valid_goc_day:
        return KetQuaEligibility(
            "UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
            "BASE_PERPENDICULAR_RELATION_MISSING", ("perpendicular_lines",)
        )

    variant = "square" if base_shape == "square" else "rectangle"

    # 3. Độ dài cần thiết:
    f_height = graph.do_dai(foot, apex)
    if f_height is None:
        return KetQuaEligibility(
            "UNSUPPORTED_MISSING_FACT", None,
            "REQUIRED_FACT_MISSING",
            ("REQUIRED_LENGTH_MISSING", f"{apex}{foot}")
        )

    f_len1 = graph.do_dai(foot, adj_1) or graph.do_dai(opp, adj_2)
    f_len2 = graph.do_dai(foot, adj_2) or graph.do_dai(opp, adj_1)

    f_b1 = graph.do_dai(foot, adj_1)
    f_o1 = graph.do_dai(opp, adj_2)
    if f_b1 is not None and f_o1 is not None:
        try:
            if Fraction(str(f_b1.value)) != Fraction(str(f_o1.value)):
                return KetQuaEligibility("INVALID_CONFLICT", None, "RECTANGLE_OPPOSITE_EDGES_UNEQUAL")
        except (ValueError, ZeroDivisionError, TypeError):
            pass

    f_b2 = graph.do_dai(foot, adj_2)
    f_o2 = graph.do_dai(opp, adj_1)
    if f_b2 is not None and f_o2 is not None:
        try:
            if Fraction(str(f_b2.value)) != Fraction(str(f_o2.value)):
                return KetQuaEligibility("INVALID_CONFLICT", None, "RECTANGLE_OPPOSITE_EDGES_UNEQUAL")
        except (ValueError, ZeroDivisionError, TypeError):
            pass

    if variant == "square":
        if f_len1 is None and f_len2 is not None:
            f_len1 = f_len2
        elif f_len2 is None and f_len1 is not None:
            f_len2 = f_len1
        elif f_len1 is None and f_len2 is None:
            return KetQuaEligibility(
                "UNSUPPORTED_MISSING_FACT", None,
                "REQUIRED_FACT_MISSING",
                ("REQUIRED_LENGTH_MISSING", f"{foot}{adj_1}")
            )
        else:
            try:
                if Fraction(str(f_len1.value)) != Fraction(str(f_len2.value)):
                    return KetQuaEligibility("INVALID_CONFLICT", None, "SQUARE_SIDES_UNEQUAL")
            except (ValueError, ZeroDivisionError, TypeError):
                pass
    else:
        if f_len1 is None:
            return KetQuaEligibility(
                "UNSUPPORTED_MISSING_FACT", None,
                "REQUIRED_FACT_MISSING",
                ("REQUIRED_LENGTH_MISSING", f"{foot}{adj_1}")
            )
        if f_len2 is None:
            return KetQuaEligibility(
                "UNSUPPORTED_MISSING_FACT", None,
                "REQUIRED_FACT_MISSING",
                ("REQUIRED_LENGTH_MISSING", f"{foot}{adj_2}")
            )

    # 4. Kiểm tra giá trị hữu tỉ dương
    gia_tri: dict[str, Fraction] = {}
    for k, f in (("canh_1", f_len1), ("canh_2", f_len2), ("cao", f_height)):
        try:
            gia_tri[k] = Fraction(str(f.value))
        except (ValueError, ZeroDivisionError, TypeError):
            return KetQuaEligibility("UNSUPPORTED_SYMBOLIC_LENGTH", None,
                                     "SYMBOLIC_LENGTH", (k,))
    khong_duong = sorted(k for k, v in gia_tri.items() if v <= 0)
    if khong_duong:
        return KetQuaEligibility("INVALID_NON_POSITIVE_LENGTH", None,
                                 "NON_POSITIVE_LENGTH", tuple(khong_duong))

    src_ids = tuple(sorted(
        {f.source_fact_id for f in (f_len1, f_len2, f_height) if f and f.source_fact_id}
        | ({fact_lp.source_fact_id} if fact_lp.source_fact_id else set())
        | {f.source_fact_id for f in valid_goc_day if f.source_fact_id}
    ))

    binding = RangBuocRectPyramid(
        family_id=SUPPORTED_FAMILY_RECT_PYRAMID,
        variant=variant,
        apex=apex,
        foot=foot,
        base_cycle=base_cycle,
        adj_1=adj_1,
        adj_2=adj_2,
        opposite=opp,
        len_adj1=gia_tri["canh_1"],
        len_adj2=gia_tri["canh_2"],
        len_height=gia_tri["cao"],
        witness=str(ob.value or "the_tich_khoi"),
        container=str(ob.args[1]),
        source_fact_ids=src_ids,
    )
    return KetQuaEligibility("SUPPORTED", binding)


def _danh_gia_eligibility_cuboid_prism(
    graph: GeometryFactGraph,
    topo: Any,
    ob: Fact,
) -> KetQuaEligibility:
    """Đánh giá tính hợp lệ cho họ lăng trụ đứng tứ giác (cuboid, cube, right square prism)."""
    base_cycle = tuple(str(x) for x in getattr(topo, "base_cycle", ()))
    top_cycle = tuple(str(x) for x in getattr(topo, "top_cycle", ()))
    correspondence = tuple((str(u), str(v)) for u, v in getattr(topo, "correspondence", ()))

    if len(base_cycle) != 4:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "BASE_NOT_QUADRILATERAL")
    if len(top_cycle) != 4:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "TOP_NOT_QUADRILATERAL")
    if len(set(base_cycle)) != 4 or len(set(top_cycle)) != 4:
        return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("REPEATED_TOPOLOGY_VERTEX",))
    if set(base_cycle) & set(top_cycle):
        return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("INTERSECTING_BASE_TOP_VERTICES",))

    corr_dict = dict(correspondence)
    if len(corr_dict) != 4 or set(corr_dict.keys()) != set(base_cycle) or set(corr_dict.values()) != set(top_cycle):
        return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("MALFORMED_BASE_TOP_CORRESPONDENCE",))

    # Lateral structure: must be right prism
    lat_struct = getattr(topo, "lateral_structure", "right") or "right"
    if lat_struct == "oblique":
        return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("OBLIQUE_LATERAL_EDGE_FOR_CUBOID",))
    if lat_struct != "right":
        return KetQuaEligibility("UNSUPPORTED_STRUCTURED_RELATION_MISSING", None, "LATERAL_STRUCTURE_NOT_RIGHT")

    base_set = set(base_cycle)

    # Check perpendicular_line_plane in graph if given
    lp = [f for f in graph.fact_theo_loai("perpendicular_line_plane") if f.status == "GIVEN"]
    for f in lp:
        if len(f.args) >= 5:
            duong, mat = set(f.args[:2]), set(f.args[2:])
            if mat <= base_set and len(mat) >= 3:
                u_in_base = duong & base_set
                u_in_top = duong - base_set
                if len(u_in_base) == 1 and len(u_in_top) == 1:
                    ub = next(iter(u_in_base))
                    ut = next(iter(u_in_top))
                    if corr_dict.get(ub) != ut:
                        return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("LINE_PLANE_RELATION_CONTRADICTION",))

    # Semantic classification & source grounding
    subkind = getattr(topo, "solid_subkind", None)
    base_shape = getattr(topo, "base_shape", None)
    grounding = getattr(topo, "source_grounding", None)

    if base_shape is not None and base_shape not in ("rectangle", "square"):
        return KetQuaEligibility("UNSUPPORTED_STRUCTURED_RELATION_MISSING", None, "BASE_NOT_RECTANGULAR", (base_shape,))

    # Perpendicular lines in base
    goc = [f for f in graph.fact_theo_loai("perpendicular_lines") if f.status == "GIVEN"]
    valid_goc_day: list[Fact] = []
    for f in goc:
        if len(f.args) != 4:
            continue
        d1, d2 = set(f.args[:2]), set(f.args[2:])
        if d1 <= base_set and d2 <= base_set:
            chung = d1 & d2
            if len(chung) == 1:
                valid_goc_day.append(f)
            elif len(chung) == 0:
                return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("OPPOSITE_EDGES_PERPENDICULAR",))

    if base_shape is None and not valid_goc_day and subkind not in ("cube", "cuboid"):
        return KetQuaEligibility("UNSUPPORTED_STRUCTURED_RELATION_MISSING", None, "BASE_PERPENDICULAR_RELATION_MISSING", ("perpendicular_lines",))

    # Cube validation: must have grounded text
    if subkind == "cube":
        if getattr(topo, "grounding_status", "VALID") == "MISSING":
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "UNSUPPORTED_SEMANTIC_GROUNDING_MISSING", (getattr(topo, "grounding_detail", "CUBE_GROUNDING_MISSING"),))
        if getattr(topo, "grounding_status", "VALID") == "INVALID":
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "UNSUPPORTED_SEMANTIC_GROUNDING_MISSING", (getattr(topo, "grounding_detail", "CUBE_GROUNDING_INVALID"),))
        family_id = SUPPORTED_FAMILY_CUBE
        base_shape = "square"
    elif subkind == "cuboid":
        if getattr(topo, "grounding_status", "VALID") == "INVALID":
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "UNSUPPORTED_SEMANTIC_GROUNDING_MISSING", (getattr(topo, "grounding_detail", "CUBOID_GROUNDING_INVALID"),))
        family_id = SUPPORTED_FAMILY_CUBOID
        base_shape = base_shape or "rectangle"
    elif subkind == "right_square_prism" or (base_shape == "square" and subkind is None):
        subkind = "right_square_prism"
        family_id = SUPPORTED_FAMILY_SQUARE_PRISM
        base_shape = "square"
    else:
        subkind = "cuboid"
        family_id = SUPPORTED_FAMILY_CUBOID
        base_shape = base_shape or "rectangle"

    v0, v1, v2, v3 = base_cycle[0], base_cycle[1], base_cycle[2], base_cycle[3]

    f_01 = graph.do_dai(v0, v1)
    f_23 = graph.do_dai(v2, v3)
    if f_01 is not None and f_23 is not None:
        try:
            if Fraction(str(f_01.value)) != Fraction(str(f_23.value)):
                return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("RECTANGLE_OPPOSITE_EDGES_UNEQUAL",))
        except (ValueError, ZeroDivisionError, TypeError):
            pass
    f_len1 = f_01 or f_23

    f_03 = graph.do_dai(v0, v3)
    f_12 = graph.do_dai(v1, v2)
    if f_03 is not None and f_12 is not None:
        try:
            if Fraction(str(f_03.value)) != Fraction(str(f_12.value)):
                return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("RECTANGLE_OPPOSITE_EDGES_UNEQUAL",))
        except (ValueError, ZeroDivisionError, TypeError):
            pass
    f_len2 = f_03 or f_12

    lat_facts = [graph.do_dai(u, corr_dict[u]) for u in base_cycle]
    valid_lat_facts = [f for f in lat_facts if f is not None]
    if len(valid_lat_facts) > 1:
        try:
            lat_vals = [Fraction(str(f.value)) for f in valid_lat_facts]
            if len(set(lat_vals)) > 1:
                return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("LATERAL_EDGES_UNEQUAL",))
        except (ValueError, ZeroDivisionError, TypeError):
            pass
    f_height = valid_lat_facts[0] if valid_lat_facts else None

    if subkind == "cube":
        all_edge_facts = [f for f in (f_01, f_23, f_03, f_12, *valid_lat_facts) if f is not None]
        if not all_edge_facts:
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "REQUIRED_FACT_MISSING", ("REQUIRED_LENGTH_MISSING", f"{v0}{v1}"))
        cube_vals = []
        for f in all_edge_facts:
            try:
                cube_vals.append(Fraction(str(f.value)))
            except (ValueError, ZeroDivisionError, TypeError):
                return KetQuaEligibility("UNSUPPORTED_SYMBOLIC_LENGTH", None, "SYMBOLIC_LENGTH")
        if any(v <= 0 for v in cube_vals):
            return KetQuaEligibility("INVALID_NON_POSITIVE_LENGTH", None, "NON_POSITIVE_LENGTH")
        if len(set(cube_vals)) > 1:
            return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("CUBE_EDGES_UNEQUAL",))
        c_val = cube_vals[0]
        len_1 = c_val
        len_2 = c_val
        len_cao = c_val
        f_len1 = f_len1 or all_edge_facts[0]
        f_len2 = f_len2 or all_edge_facts[0]
        f_height = f_height or all_edge_facts[0]

    elif subkind == "right_square_prism":
        if f_len1 and f_len2:
            try:
                if Fraction(str(f_len1.value)) != Fraction(str(f_len2.value)):
                    return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("SQUARE_SIDES_UNEQUAL",))
            except (ValueError, ZeroDivisionError, TypeError):
                pass
        elif f_len1 is None and f_len2 is not None:
            f_len1 = f_len2
        elif f_len2 is None and f_len1 is not None:
            f_len2 = f_len1
        elif f_len1 is None and f_len2 is None:
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "REQUIRED_FACT_MISSING", ("REQUIRED_LENGTH_MISSING", f"{v0}{v1}"))

        if f_height is None:
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "REQUIRED_FACT_MISSING", ("REQUIRED_LENGTH_MISSING", f"{v0}{corr_dict[v0]}"))

        try:
            len_1 = Fraction(str(f_len1.value))
            len_2 = len_1
            len_cao = Fraction(str(f_height.value))
        except (ValueError, ZeroDivisionError, TypeError):
            return KetQuaEligibility("UNSUPPORTED_SYMBOLIC_LENGTH", None, "SYMBOLIC_LENGTH")

    else:
        # Cuboid
        if f_height is None:
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "REQUIRED_FACT_MISSING", ("REQUIRED_LENGTH_MISSING", f"{v0}{corr_dict[v0]}"))
        if f_len1 is None:
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "REQUIRED_FACT_MISSING", ("REQUIRED_LENGTH_MISSING", f"{v0}{v1}"))
        if f_len2 is None:
            if base_shape == "square":
                f_len2 = f_len1
            else:
                return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "REQUIRED_FACT_MISSING", ("REQUIRED_LENGTH_MISSING", f"{v0}{v3}"))

        try:
            len_1 = Fraction(str(f_len1.value))
            len_2 = Fraction(str(f_len2.value))
            len_cao = Fraction(str(f_height.value))
        except (ValueError, ZeroDivisionError, TypeError):
            return KetQuaEligibility("UNSUPPORTED_SYMBOLIC_LENGTH", None, "SYMBOLIC_LENGTH")

    khong_duong = [k for k, v in [("len_1", len_1), ("len_2", len_2), ("len_cao", len_cao)] if v <= 0]
    if khong_duong:
        return KetQuaEligibility("INVALID_NON_POSITIVE_LENGTH", None, "NON_POSITIVE_LENGTH", tuple(khong_duong))

    display_labels = getattr(topo, "display_labels", {})
    base_ids = base_cycle
    top_ids = top_cycle
    corr_ids = correspondence

    src_ids = tuple(sorted(
        {f.source_fact_id for f in (f_len1, f_len2, f_height, *valid_lat_facts) if f and f.source_fact_id}
        | {f.source_fact_id for f in valid_goc_day if f.source_fact_id}
        | {f.source_fact_id for f in lp if f.source_fact_id}
    ))

    binding = RangBuocCuboid(
        family_id=family_id,
        solid_subkind=subkind,
        base_shape=base_shape,
        base_cycle=base_cycle,
        top_cycle=top_cycle,
        correspondence=correspondence,
        base_cycle_ids=base_ids,
        top_cycle_ids=top_ids,
        correspondence_ids=corr_ids,
        display_labels=display_labels,
        origin_pt=base_ids[0],
        adj_1=base_ids[1],
        adj_2=base_ids[3],
        opposite=base_ids[2],
        origin_top=corr_dict[base_cycle[0]],
        len_adj1=len_1,
        len_adj2=len_2,
        len_height=len_cao,
        witness=str(ob.value or "the_tich_khoi"),
        container=str(ob.args[1]),
        source_fact_ids=src_ids,
        source_grounding=grounding,
    )
    return KetQuaEligibility("SUPPORTED", binding)


def _gia_tri(f: Fact) -> Fraction | None:
    try:
        return Fraction(str(f.value))
    except (ValueError, ZeroDivisionError, TypeError):
        return None


def _co_chan_lech(graph: GeometryFactGraph, topo: Any) -> bool:
    """Đề cho `T F ⊥ (đáy)` với F ≠ đỉnh tương ứng của T — tự nó là lăng trụ XIÊN, kể cả khi `lateral_structure`
    vắng (hợp đồng điền mặc định `right` khi analyze không khai)."""
    doi = {str(v): str(u) for u, v in topo.correspondence}
    day = {str(x) for x in topo.base_cycle}
    for f in graph.fact_theo_loai("perpendicular_line_plane"):
        if f.status == "GIVEN" and len(f.args) == 5 and set(f.args[2:]) <= day:
            t, F = f.args[:2] if f.args[0] in doi else f.args[1::-1]
            if t in doi and F in day and doi[t] != F:
                return True
    return False


def _danh_gia_eligibility_oblique_prism(
    graph: GeometryFactGraph,
    topo: Any,
    ob: Fact,
) -> KetQuaEligibility:
    """G04 — lăng trụ xiên. Bố cục đáy + một chân đường cao là đỉnh đáy; mọi số đo lấy từ FactGraph."""
    base = tuple(str(x) for x in topo.base_cycle)
    top = tuple(str(x) for x in topo.top_cycle)
    corr = tuple((str(u), str(v)) for u, v in topo.correspondence)
    try:
        P.construct_prism("_", base, top, corr)  # cùng một phép kiểm tô-pô với câu lệnh sẽ sinh
    except ValueError:
        return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT",
                                 ("MALFORMED_PRISM_TOPOLOGY",))
    n = len(base)
    if n not in (3, 4):
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "BASE_POLYGON_NOT_SUPPORTED", (str(n),))
    tuong_ung = dict(corr)
    nguoc = {v: u for u, v in corr}
    tap_day = set(base)
    Z = Fraction(0)

    # ── 1 · BỐ CỤC ĐÁY (ℚ³) ──────────────────────────────────────────────
    goc = [f for f in graph.fact_theo_loai("perpendicular_lines") if f.status == "GIVEN"
           and len(f.args) == 4 and set(f.args) <= tap_day and len(set(f.args[:2]) & set(f.args[2:])) == 1]
    if n == 3:
        if not goc:
            return KetQuaEligibility("UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
                                     "BASE_PERPENDICULAR_RELATION_MISSING", ("perpendicular_lines",))
        dv = next(iter(set(goc[0].args[:2]) & set(goc[0].args[2:])))
        c1, c2 = next((base[(i + 1) % 3], base[(i + 2) % 3]) for i, u in enumerate(base) if u == dv)
        f1, f2 = graph.do_dai(dv, c1), graph.do_dai(dv, c2)
        thieu = [f"{dv}{c}" for c, f in ((c1, f1), (c2, f2)) if f is None]
        if thieu:
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "REQUIRED_FACT_MISSING",
                                     ("REQUIRED_LENGTH_MISSING", *thieu))
        a, b = _gia_tri(f1), _gia_tri(f2)
        doan_day = ((dv, c1), (dv, c2))
        toa = {dv: (Z, Z, Z), c1: (a, Z, Z), c2: (Z, b, Z)} if a is not None and b is not None else {}
        nguon_day = [f1, f2, goc[0]]
    else:
        shape = getattr(topo, "base_shape", None)
        if shape not in ("rectangle", "square"):
            return KetQuaEligibility("UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
                                     "BASE_NOT_RECTANGULAR", (str(shape),))
        v0, v1, v2, v3 = base
        ngang = [f for f in (graph.do_dai(v0, v1), graph.do_dai(v2, v3)) if f is not None]
        doc = [f for f in (graph.do_dai(v0, v3), graph.do_dai(v1, v2)) if f is not None]
        if shape == "square":
            ngang = doc = ngang + doc
        for nhom in (ngang, doc):
            if len({_gia_tri(f) for f in nhom}) > 1:
                return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT",
                                         ("RECTANGLE_OPPOSITE_EDGES_UNEQUAL",))
        if not ngang or not doc:
            return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "REQUIRED_FACT_MISSING",
                                     ("REQUIRED_LENGTH_MISSING", f"{v0}{v1}" if not ngang else f"{v0}{v3}"))
        a, b = _gia_tri(ngang[0]), _gia_tri(doc[0])
        doan_day = (tuple(ngang[0].args), tuple(doc[0].args))
        toa = ({v0: (Z, Z, Z), v1: (a, Z, Z), v2: (a, b, Z), v3: (Z, b, Z)}
               if a is not None and b is not None else {})
        nguon_day = [ngang[0], doc[0], *goc]
    if not toa:
        return KetQuaEligibility("UNSUPPORTED_SYMBOLIC_LENGTH", None, "SYMBOLIC_LENGTH", ("base",))
    if a <= 0 or b <= 0:
        return KetQuaEligibility("INVALID_NON_POSITIVE_LENGTH", None, "NON_POSITIVE_LENGTH", ("base",))

    # ── 2 · CHÂN ĐƯỜNG CAO: `T F ⟂ (đáy)`, T đỉnh đáy trên, F đỉnh đáy dưới ──
    #
    # Cạnh bên của CHÍNH T (F = B0) vuông góc đáy là lăng trụ ĐỨNG — mâu thuẫn với `oblique`.
    chan: list[tuple[Fact, str, str]] = []
    for f in graph.fact_theo_loai("perpendicular_line_plane"):
        if f.status != "GIVEN" or len(f.args) != 5 or not set(f.args[2:]) <= tap_day:
            continue
        duong = set(f.args[:2])
        t, F = duong & set(top), duong & tap_day
        if len(t) != 1 or len(F) != 1:
            continue
        t, F = next(iter(t)), next(iter(F))
        if tuong_ung[F] == t:
            return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT",
                                     ("RIGHT_LATERAL_EDGE_FOR_OBLIQUE_PRISM",))
        chan.append((f, t, F))
    if not chan:
        # Đề không định được phương cạnh bên bằng đỉnh có tên (góc nghiêng, chân là trung điểm/trọng tâm
        # chưa có quan hệ có cấu trúc): không dựng được mà không giả định.
        return KetQuaEligibility("UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
                                 "OBLIQUE_FOOT_NOT_LOCATED", ("perpendicular_line_plane",))
    if len({(t, F) for _, t, F in chan}) > 1:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "OBLIQUE_FOOT_NOT_UNIQUE")
    fact_chan, T, F = chan[0]
    B0 = nguoc[T]

    # ── 3 · CHIỀU CAO: đề cho TF, hoặc suy từ cạnh bên (Pythagore, PHẢI hữu tỉ) ──
    canh_ben = [f for u, v in corr if (f := graph.do_dai(u, v)) is not None]
    gt_ben = {_gia_tri(f) for f in canh_ben}
    if None in gt_ben:
        return KetQuaEligibility("UNSUPPORTED_SYMBOLIC_LENGTH", None, "SYMBOLIC_LENGTH", ("lateral",))
    if len(gt_ben) > 1:
        return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT", ("LATERAL_EDGES_UNEQUAL",))
    lech = sum(((x - y) ** 2 for x, y in zip(toa[B0], toa[F])), Fraction(0))
    f_cao = graph.do_dai(T, F)
    if f_cao is not None:
        h = _gia_tri(f_cao)
        if h is None:
            return KetQuaEligibility("UNSUPPORTED_SYMBOLIC_LENGTH", None, "SYMBOLIC_LENGTH", ("height",))
        if h <= 0:
            return KetQuaEligibility("INVALID_NON_POSITIVE_LENGTH", None, "NON_POSITIVE_LENGTH", ("height",))
        if canh_ben and next(iter(gt_ben)) ** 2 != h * h + lech:
            return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT",
                                     ("LATERAL_EDGE_HEIGHT_MISMATCH",))
        doan_cao = (T, F)
    elif canh_ben:
        L = next(iter(gt_ben))
        if L <= 0:
            return KetQuaEligibility("INVALID_NON_POSITIVE_LENGTH", None, "NON_POSITIVE_LENGTH", ("lateral",))
        h2 = L * L - lech
        if h2 <= 0:
            return KetQuaEligibility("INVALID_CONFLICT", None, "INVALID_CONFLICT",
                                     ("LATERAL_EDGE_NOT_LONGER_THAN_FOOT_OFFSET",))
        h = sqrt_rational(h2)
        if not isinstance(h, Fraction):
            return KetQuaEligibility("UNSUPPORTED_IRRATIONAL_LAYOUT", None, "IRRATIONAL_HEIGHT", ("height",))
        f_cao = canh_ben[0]
        doan_cao = tuple(f_cao.args)
    else:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None, "REQUIRED_FACT_MISSING",
                                 ("REQUIRED_LENGTH_MISSING", f"{T}{F}"))

    return KetQuaEligibility("SUPPORTED", RangBuocObliquePrism(
        family_id=SUPPORTED_FAMILY_OBLIQUE_PRISM,
        base_cycle=base, top_cycle=top, correspondence=corr,
        display_labels=dict(getattr(topo, "display_labels", {}) or {}),
        base_coords=tuple(toa[u] for u in base),
        base_segments=doan_day,
        anchor_top=T, anchor_base=B0, foot=F, height=h, height_segment=doan_cao,
        witness=str(ob.value or "the_tich_lang_tru"), container=str(ob.args[1]),
        foot_source_fact_id=fact_chan.source_fact_id,
        source_fact_ids=tuple(sorted({f.source_fact_id for f in (*nguon_day, fact_chan, f_cao, *canh_ben)
                                      if f.source_fact_id}))))


# ══ ELIGIBILITY ═════════════════════════════════════════════════════════════
def danh_gia_eligibility(graph: GeometryFactGraph) -> KetQuaEligibility:
    """Graph này có thuộc họ lát cắt hỗ trợ không. KHÔNG sinh chương trình một phần."""
    # ── FAIL CLOSED với graph mâu thuẫn ──────────────────────────────────
    #
    # `dung_graph` đã kiểm, nhưng `GeometryFactGraph` dựng được trực tiếp. Không có
    # dòng này, vòng chọn góc vuông đáy bên dưới lấy góc ĐẦU TIÊN khớp chân đường
    # cao và lặng lẽ bỏ góc vuông ở đỉnh kia — đúng cách N04 từng đi lọt. Gọi
    # CHÍNH `kiem_mau_thuan`, không chép luật: một thẩm quyền.
    try:
        kiem_mau_thuan(graph.facts)
    except MauThuanFact as e:
        return KetQuaEligibility("INVALID_CONFLICT", None, e.ma,
                                 e.chan_doan or (e.rule_id or e.ma,))
    yeu_cau = graph.fact_theo_loai("requested_operation")
    do_the_tich = [f for f in yeu_cau if f.args and f.args[0] == "volume"]
    khac = [f for f in yeu_cau if f.args and f.args[0] != "volume"]
    if khac:
        return KetQuaEligibility("UNSUPPORTED_EXTRA_OBLIGATION", None,
                                 "EXTRA_OBLIGATION",
                                 tuple(sorted({f.args[0] for f in khac})))
    if len(do_the_tich) != 1:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None,
                                 "VOLUME_OBLIGATION_NOT_UNIQUE")

    # ── PRISM & RECTANGULAR PYRAMID FAMILY DISPATCH ───────────────────────
    if getattr(graph, "solid_topology", None) is not None:
        topo = graph.solid_topology
        if getattr(topo, "solid_kind", None) == "prism":
            # Một khối chuyên biệt (hộp, lập phương…) khai `oblique` vẫn đi nhánh của nó để bị từ chối mâu thuẫn.
            if getattr(topo, "solid_subkind", None) is None and (
                    getattr(topo, "lateral_structure", None) == "oblique" or _co_chan_lech(graph, topo)):
                return _danh_gia_eligibility_oblique_prism(graph, topo, do_the_tich[0])
            base_cycle = getattr(topo, "base_cycle", ())
            if len(base_cycle) == 4:
                return _danh_gia_eligibility_cuboid_prism(graph, topo, do_the_tich[0])
            return _danh_gia_eligibility_prism(graph, topo, do_the_tich[0])
        if getattr(topo, "solid_kind", None) == "pyramid":
            return _danh_gia_eligibility_rectangular_pyramid(graph, topo, do_the_tich[0])

    # ── ĐƯỜNG CAO: `line ⟂ plane`, ĐỀ CHO (không nhận fact suy ra) ────────
    #
    # Đọc quan hệ đường–mặt TRƯỚC, vì chính nó phân xử được cả hai vai: chân
    # đường cao (đầu mút nằm trong mặt phẳng) và đỉnh chóp (đầu mút không nằm).
    # Bản `/1` đi ngược — tìm góc vuông trước rồi mới dò đỉnh chóp — và phải
    # đoán `dinh_chop` bằng cách lấy "đầu kia" của một fact `perpendicular` có
    # args phẳng, tức tin vào thứ tự args.
    lp = [f for f in graph.fact_theo_loai("perpendicular_line_plane")
          if f.status == "GIVEN"]
    if not lp:
        return KetQuaEligibility("UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
                                 "LINE_PLANE_RELATION_MISSING",
                                 ("perpendicular_line_plane",))
    if len(lp) != 1:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None,
                                 "LINE_PLANE_RELATION_NOT_UNIQUE")
    duong, mat = tuple(lp[0].args[:2]), tuple(lp[0].args[2:])
    if len(mat) != 3:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None,
                                 "PLANE_ARITY_UNEXPECTED")
    trong = [t for t in duong if t in mat]
    ngoai = [t for t in duong if t not in mat]
    if len(trong) != 1 or len(ngoai) != 1:
        # Đường nằm hẳn trong mặt, hoặc rời hẳn mặt: không phải đường cao của
        # một hình chóp có chân trên đáy.
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None,
                                 "LINE_PLANE_INCIDENCE_UNEXPECTED")
    dinh_vuong, dinh_chop = trong[0], ngoai[0]

    # ── ĐÁY VUÔNG: `line ⟂ line` CHUNG ĐỈNH, ĐỀ CHO ───────────────────────
    #
    # Chỉ nhận fact `GIVEN`: `SA ⟂ AB` và `SA ⟂ AC` được suy ra từ chính quan hệ
    # đường–mặt ở trên, và nhận chúng ở đây là lấy hệ quả của một dữ kiện làm
    # dữ kiện thứ hai — tam giác đáy sẽ "vuông" mà không ai nói thế.
    goc = [f for f in graph.fact_theo_loai("perpendicular_lines")
           if f.status == "GIVEN"]
    if not goc:
        return KetQuaEligibility("UNSUPPORTED_STRUCTURED_RELATION_MISSING", None,
                                 "BASE_PERPENDICULAR_RELATION_MISSING",
                                 ("perpendicular_lines",))
    chan: list[str] = []
    for f in goc:
        if len(f.args) != 4:
            continue
        d1, d2 = tuple(f.args[:2]), tuple(f.args[2:])
        chung = set(d1) & set(d2)
        if chung != {dinh_vuong}:
            continue  # góc vuông ở một đỉnh khác — không phải đáy của khối này
        chan = sorted((set(d1) | set(d2)) - {dinh_vuong})
        break
    if len(chan) != 2:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None,
                                 "BASE_RIGHT_ANGLE_VERTEX_MISMATCH")
    chan_1, chan_2 = chan

    # Ba đỉnh của đáy phải ĐÚNG là mặt phẳng mà cạnh bên vuông góc. Thiếu phép
    # kiểm này thì một quan hệ hợp lệ nhưng nói về MỘT MẶT KHÁC vẫn đi lọt.
    if set(mat) != {dinh_vuong, chan_1, chan_2}:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None,
                                 "BASE_PLANE_MISMATCH")
    vg = lp

    def _len(x: str, y: str) -> Fact | None:
        return graph.do_dai(x, y)

    can = {"canh_1": _len(dinh_vuong, chan_1),
           "canh_2": _len(dinh_vuong, chan_2),
           "cao": _len(dinh_vuong, dinh_chop)}
    thieu = sorted(k for k, v in can.items() if v is None)
    if thieu:
        return KetQuaEligibility("UNSUPPORTED_MISSING_FACT", None,
                                 "REQUIRED_LENGTH_MISSING", tuple(thieu))

    gia_tri: dict[str, Fraction] = {}
    for k, f in can.items():
        try:
            gia_tri[k] = Fraction(str(f.value))
        except (ValueError, ZeroDivisionError, TypeError):
            return KetQuaEligibility("UNSUPPORTED_SYMBOLIC_LENGTH", None,
                                     "SYMBOLIC_LENGTH", (k,))
    khong_duong = sorted(k for k, v in gia_tri.items() if v <= 0)
    if khong_duong:
        return KetQuaEligibility("INVALID_NON_POSITIVE_LENGTH", None,
                                 "NON_POSITIVE_LENGTH", tuple(khong_duong))

    ob = do_the_tich[0]
    return KetQuaEligibility("SUPPORTED", RangBuocHo(
        dinh_vuong=dinh_vuong, chan_1=chan_1, chan_2=chan_2, dinh_chop=dinh_chop,
        len_1=gia_tri["canh_1"], len_2=gia_tri["canh_2"], len_cao=gia_tri["cao"],
        witness=str(ob.value or "the_tich"), container=str(ob.args[1]),
        source_fact_ids=tuple(sorted(
            {f.source_fact_id for f in can.values() if f.source_fact_id}
            | {g.source_fact_id for g in (*goc, *vg) if g.source_fact_id}))))


# ══ COMPILER ════════════════════════════════════════════════════════════════
def _khai_do_dai_de_cho(graph: GeometryFactGraph,
                        cap: tuple[tuple[str, str], ...]) -> list[dict[str, Any]]:
    """Độ dài ĐỀ CHO thành đại lượng `<đầu><cuối>_length` trong bộ nhớ.

    Thiếu chúng thì cảnh không nối được chiều cao vào thể tích (`_provenance`
    nối theo tên `*_length`), nên thẻ công thức mất và dòng "Dựa trên" thiếu
    chiều cao (review w10). Nhãn xuất xứ và nguồn CHÉP từ FactGraph — compiler
    không tự gán `GIVEN` cho thứ nó chọn.
    """
    ra = []
    for dau, cuoi in cap:
        f = graph.do_dai(dau, cuoi)
        if f is not None:
            ra.append(P.memory_declaration(
                f"{dau}{cuoi}_length", P.KIEU_DAI_LUONG, provenance=f.status,
                source_fact_id=f.source_fact_id, initial_value=P._so(Fraction(str(f.value)))))
    return ra


def bien_dich(graph: GeometryFactGraph) -> KetQuaBienDich:
    """FactGraph → chương trình ngữ nghĩa + quá trình dựng. TẤT ĐỊNH."""
    t0 = time.perf_counter()
    el = danh_gia_eligibility(graph)
    if el.status != "SUPPORTED" or el.binding is None:
        return KetQuaBienDich(
            "NOT_ELIGIBLE", None, reason_code=el.reason_code or el.status,
            diagnostics=el.diagnostics,
            elapsed_ms=(time.perf_counter() - t0) * 1000)

    b = el.binding
    if isinstance(b, RangBuocPrism):
        return _bien_dich_prism(graph, b, t0)
    if isinstance(b, RangBuocRectPyramid):
        return _bien_dich_rectangular_pyramid(graph, b, t0)
    if isinstance(b, RangBuocCuboid):
        return _bien_dich_cuboid(graph, b, t0)
    if isinstance(b, RangBuocObliquePrism):
        return _bien_dich_oblique_prism(graph, b, t0)

    Z = Fraction(0)
    # ── BỐ CỤC CHÍNH TẮC (LAYOUT_DERIVED) ────────────────────────────────
    #
    # Đỉnh vuông ở gốc; hai cạnh góc vuông theo hai trục độc lập; đỉnh chóp
    # theo pháp tuyến của mặt phẳng đáy. Không hằng số nào viết cứng — cả ba
    # độ dài lấy từ FactGraph.
    toa_do = {
        b.dinh_vuong: (Z, Z, Z),
        b.chan_1: (b.len_1, Z, Z),
        b.chan_2: (Z, b.len_2, Z),
        b.dinh_chop: (Z, Z, b.len_cao),
    }

    ten_day = f"day_{b.dinh_vuong}{b.chan_1}{b.chan_2}"
    ten_khoi = b.container
    ten_dt = f"dien_tich_{ten_day}"
    goi: list[P.LoiGoiPrimitive] = []
    buoc: list[BuocDung] = []
    stmts: list[dict[str, Any]] = []
    khai: list[dict[str, Any]] = []
    dan_xuat: list[str] = []

    def them(prim: str, st: dict[str, Any], mo_ta: str,
             src: tuple[str, ...] = (), der: tuple[str, ...] = (),
             obj: tuple[str, ...] = ()) -> None:
        stmts.append(st)
        goi.append(P.LoiGoiPrimitive(prim, len(st), src, der))
        buoc.append(BuocDung(len(buoc) + 1, prim, mo_ta, src, der, obj))
        dan_xuat.extend(der)

    def _src(*pts: str) -> tuple[str, ...]:
        f = graph.do_dai(*pts) if len(pts) == 2 else None
        return (f.source_fact_id,) if f and f.source_fact_id else ()

    # 1 · đỉnh vuông của đáy
    them("declare_point", P.declare_point(b.dinh_vuong, toa_do[b.dinh_vuong]),
         "Đặt đỉnh vuông của tam giác đáy làm gốc toạ độ.",
         der=(f"layout_{b.dinh_vuong}",), obj=(b.dinh_vuong,))
    # 2 · cạnh góc vuông thứ nhất
    them("declare_point", P.declare_point(b.chan_1, toa_do[b.chan_1]),
         "Dựng cạnh góc vuông thứ nhất theo độ dài đề cho.",
         _src(b.dinh_vuong, b.chan_1), (f"layout_{b.chan_1}",), (b.chan_1,))
    # 3 · cạnh góc vuông thứ hai, vuông góc với cạnh thứ nhất
    them("declare_point", P.declare_point(b.chan_2, toa_do[b.chan_2]),
         "Dựng cạnh góc vuông thứ hai, vuông góc với cạnh thứ nhất.",
         _src(b.dinh_vuong, b.chan_2), (f"layout_{b.chan_2}",), (b.chan_2,))
    # 3b · ghi nhận hai cạnh đáy đã dựng (bước KỂ, không sinh câu lệnh mới —
    # cạnh là hệ quả của hai đầu mút, IR không có câu lệnh `construct_segment`)
    for ten_dau, ten_cuoi, nhan in ((b.dinh_vuong, b.chan_1, "thứ nhất"),
                                    (b.dinh_vuong, b.chan_2, "thứ hai")):
        buoc.append(BuocDung(
            len(buoc) + 1, "construct_triangle",
            f"Xác định cạnh góc vuông {nhan} của tam giác đáy.",
            _src(ten_dau, ten_cuoi), (), (ten_dau, ten_cuoi)))
    # 4 · hoàn thiện tam giác đáy
    them("construct_triangle",
         P.construct_triangle(ten_day, (b.dinh_vuong, b.chan_1, b.chan_2),
                              "Tam giác đáy"),
         "Hoàn thiện tam giác đáy từ ba đỉnh vừa dựng.",
         der=(f"derived_{ten_day}",), obj=(ten_day,))
    # 5 + 6 · đỉnh chóp theo pháp tuyến của đáy. Đường cao và các cạnh bên do bước
    # bổ sung dựng hình theo lớp (`semantic_program.formation`) dựng — W14.
    them("declare_point", P.declare_point(b.dinh_chop, toa_do[b.dinh_chop]),
         "Đặt đỉnh chóp theo độ dài cạnh bên đề cho.",
         _src(b.dinh_vuong, b.dinh_chop), (f"layout_{b.dinh_chop}",), (b.dinh_chop,))
    # 7 · nối đỉnh với các đỉnh đáy
    them("construct_pyramid",
         P.construct_pyramid(ten_khoi, b.dinh_chop,
                             (b.dinh_vuong, b.chan_1, b.chan_2), "Khối chóp"),
         "Nối đỉnh chóp với các đỉnh đáy để tạo khối.",
         der=(f"derived_{ten_khoi}",), obj=(ten_khoi,))
    # 8 · diện tích đáy
    them("measure_quantity", P.measure_quantity(ten_dt, "area", ten_day),
         "Tính diện tích tam giác đáy.", der=(f"derived_{ten_dt}",))
    # 9 · thể tích khối chóp
    ten_tt = f"the_tich_{ten_khoi}"
    them("measure_quantity", P.measure_quantity(ten_tt, "volume", ten_khoi),
         "Tính thể tích khối chóp.", der=(f"derived_{ten_tt}",))
    # 10 · ghi kết quả vào final_memory
    them("assign_final_memory", P.assign_final_memory(b.witness, ten_tt),
         "Ghi thể tích vào biến mà đề yêu cầu.", der=(b.witness,))

    # ⚠️ TOẠ ĐỘ DO BỐ CỤC CHỌN ĐI QUA `model_assumption`, KHÔNG qua
    # `source_fact_id`. Đề KHÔNG cho toạ độ; gắn một `source_fact_id` vào đây
    # là khai rằng đề đã cho con số ấy — đúng thứ cổng grounding tồn tại để
    # chặn. `model_assumption` là kênh hợp lệ cho *cách đặt* một vật đề đã nêu.
    ly_do = {
        b.dinh_vuong: "đặt đỉnh vuông của tam giác đáy tại gốc toạ độ",
        b.chan_1: "đặt cạnh góc vuông thứ nhất dọc trục thứ nhất",
        b.chan_2: "đặt cạnh góc vuông thứ hai dọc trục thứ hai",
        b.dinh_chop: "đặt đỉnh chóp trên pháp tuyến của mặt phẳng đáy tại đỉnh vuông",
    }
    khai.extend(_khai_do_dai_de_cho(graph, (
        (b.dinh_vuong, b.chan_1), (b.dinh_vuong, b.chan_2), (b.dinh_chop, b.dinh_vuong))))
    for t in (b.dinh_vuong, b.chan_1, b.chan_2, b.dinh_chop):
        khai.append(P.memory_declaration(t, "point3", ly_do[t]))
    khai.append(P.memory_declaration(ten_day, "polygon3"))
    khai.append(P.memory_declaration(ten_khoi, "solid"))
    for t in (ten_dt, ten_tt, b.witness):
        khai.append(P.memory_declaration(t, P.KIEU_DAI_LUONG))

    program = {
        "title": "Thể tích khối chóp có đáy là tam giác vuông",
        "memory_declarations": khai,
        "statements": stmts,
    }
    return KetQuaBienDich(
        "COMPILED", program, tuple(goi), tuple(buoc), tuple(dan_xuat),
        elapsed_ms=(time.perf_counter() - t0) * 1000)


def _bien_dich_prism(
    graph: GeometryFactGraph,
    b: RangBuocPrism,
    t0: float,
) -> KetQuaBienDich:
    """Biên dịch FactGraph sang chương trình ngữ nghĩa cho họ lăng trụ đứng đáy tam giác vuông."""
    Z = Fraction(0)
    toa_do = {
        b.dinh_vuong_day: (Z, Z, Z),
        b.chan_1: (b.len_1, Z, Z),
        b.chan_2: (Z, b.len_2, Z),
        b.dinh_vuong_top: (Z, Z, b.len_cao),
        b.chan_1_top: (b.len_1, Z, b.len_cao),
        b.chan_2_top: (Z, b.len_2, b.len_cao),
    }

    ten_day = f"day_{b.dinh_vuong_day}{b.chan_1}{b.chan_2}"
    ten_khoi = b.container
    ten_dt = f"dien_tich_{ten_day}"
    goi: list[P.LoiGoiPrimitive] = []
    buoc: list[BuocDung] = []
    stmts: list[dict[str, Any]] = []
    khai: list[dict[str, Any]] = []
    dan_xuat: list[str] = []

    def them(prim: str, st: dict[str, Any], mo_ta: str,
             src: tuple[str, ...] = (), der: tuple[str, ...] = (),
             obj: tuple[str, ...] = ()) -> None:
        stmts.append(st)
        goi.append(P.LoiGoiPrimitive(prim, len(st), src, der))
        buoc.append(BuocDung(len(buoc) + 1, prim, mo_ta, src, der, obj))
        dan_xuat.extend(der)

    def _src(*pts: str) -> tuple[str, ...]:
        f = graph.do_dai(*pts) if len(pts) == 2 else None
        return (f.source_fact_id,) if f and f.source_fact_id else ()

    # 1 · Đỉnh vuông đáy dưới tại gốc toạ độ
    them("declare_point", P.declare_point(b.dinh_vuong_day, toa_do[b.dinh_vuong_day]),
         "Đặt đỉnh vuông của tam giác đáy dưới làm gốc toạ độ.",
         der=(f"layout_{b.dinh_vuong_day}",), obj=(b.dinh_vuong_day,))
    # 2 · Cạnh góc vuông thứ nhất đáy dưới
    them("declare_point", P.declare_point(b.chan_1, toa_do[b.chan_1]),
         "Dựng cạnh góc vuông thứ nhất của đáy dưới theo độ dài đề cho.",
         _src(b.dinh_vuong_day, b.chan_1), (f"layout_{b.chan_1}",), (b.chan_1,))
    # 3 · Cạnh góc vuông thứ hai đáy dưới
    them("declare_point", P.declare_point(b.chan_2, toa_do[b.chan_2]),
         "Dựng cạnh góc vuông thứ hai của đáy dưới, vuông góc với cạnh thứ nhất.",
         _src(b.dinh_vuong_day, b.chan_2), (f"layout_{b.chan_2}",), (b.chan_2,))
    # 4 · Hoàn thiện tam giác đáy dưới
    them("construct_triangle",
         P.construct_triangle(ten_day, (b.dinh_vuong_day, b.chan_1, b.chan_2), "Tam giác đáy dưới"),
         "Hoàn thiện tam giác đáy dưới từ ba đỉnh vừa dựng.",
         der=(f"derived_{ten_day}",), obj=(ten_day,))
    # 5 · Các đỉnh đáy trên theo chiều cao
    for pt_top, pt_base, desc in (
        (b.dinh_vuong_top, b.dinh_vuong_day, "đỉnh tương ứng với đỉnh vuông đáy dưới"),
        (b.chan_1_top, b.chan_1, "đỉnh tương ứng với cạnh thứ nhất đáy dưới"),
        (b.chan_2_top, b.chan_2, "đỉnh tương ứng với cạnh thứ hai đáy dưới"),
    ):
        them("declare_point", P.declare_point(pt_top, toa_do[pt_top]),
             f"Dựng {desc} theo chiều cao lăng trụ.",
             _src(pt_base, pt_top), (f"layout_{pt_top}",), (pt_top,))
    # 6 · Khối lăng trụ
    them("construct_prism",
         P.construct_prism(ten_khoi, b.base_cycle, b.top_cycle, b.correspondence),
         "Dựng khối lăng trụ đứng từ hai đáy và các cặp đỉnh tương ứng.",
         der=(f"derived_{ten_khoi}",), obj=(ten_khoi,))
    # 7 · Diện tích đáy dưới
    them("measure_quantity", P.measure_quantity(ten_dt, "area", ten_day),
         "Tính diện tích tam giác đáy dưới.", der=(f"derived_{ten_dt}",))
    # 8 · Thể tích khối lăng trụ
    ten_tt = f"the_tich_{ten_khoi}"
    them("measure_quantity", P.measure_quantity(ten_tt, "volume", ten_khoi),
         "Tính thể tích khối lăng trụ.", der=(f"derived_{ten_tt}",))
    # 9 · Ghi kết quả vào biến witness
    them("assign_final_memory", P.assign_final_memory(b.witness, ten_tt),
         "Ghi thể tích vào biến mà đề yêu cầu.", der=(b.witness,))

    # Chiều cao là cạnh bên ĐỀ CHO — cùng thứ tự dò với eligibility.
    tuong_ung = dict(b.correspondence)
    day_cao = next(u for u in (b.dinh_vuong_day, b.chan_1, b.chan_2)
                   if graph.do_dai(u, tuong_ung[u]) is not None)
    khai.extend(_khai_do_dai_de_cho(graph, (
        (b.dinh_vuong_day, b.chan_1), (b.dinh_vuong_day, b.chan_2),
        (day_cao, tuong_ung[day_cao]))))
    # Khai báo bộ nhớ với provenance="LAYOUT_DERIVED"
    for pt in (b.dinh_vuong_day, b.chan_1, b.chan_2, b.dinh_vuong_top, b.chan_1_top, b.chan_2_top):
        khai.append(P.memory_declaration(pt, "point3", provenance="LAYOUT_DERIVED"))
    khai.append(P.memory_declaration(ten_day, "polygon3"))
    khai.append(P.memory_declaration(ten_khoi, "solid"))
    seen_mem = set()
    for t in (ten_dt, ten_tt, b.witness):
        if t not in seen_mem:
            khai.append(P.memory_declaration(t, P.KIEU_DAI_LUONG))
            seen_mem.add(t)

    program = {
        "title": "Thể tích khối lăng trụ đứng có đáy là tam giác vuông",
        "memory_declarations": khai,
        "statements": stmts,
    }
    return KetQuaBienDich(
        "COMPILED", program, tuple(goi), tuple(buoc), tuple(dan_xuat),
        elapsed_ms=(time.perf_counter() - t0) * 1000)


def _bien_dich_rectangular_pyramid(
    graph: GeometryFactGraph,
    b: RangBuocRectPyramid,
    t0: float,
) -> KetQuaBienDich:
    """Biên dịch FactGraph sang chương trình ngữ nghĩa cho họ chóp đáy chữ nhật/vuông."""
    Z = Fraction(0)
    toa_do = {
        b.foot: (Z, Z, Z),
        b.adj_1: (b.len_adj1, Z, Z),
        b.adj_2: (Z, b.len_adj2, Z),
        b.opposite: (b.len_adj1, b.len_adj2, Z),
        b.apex: (Z, Z, b.len_height),
    }

    ten_day = f"day_{''.join(b.base_cycle)}"
    ten_khoi = b.container
    ten_dt = f"dien_tich_{ten_day}"
    ten_tt = f"the_tich_{ten_khoi}"

    goi: list[P.LoiGoiPrimitive] = []
    buoc: list[BuocDung] = []
    stmts: list[dict[str, Any]] = []
    khai: list[dict[str, Any]] = []
    dan_xuat: list[str] = []

    def them(prim: str, st: dict[str, Any], mo_ta: str,
             src: tuple[str, ...] = (), der: tuple[str, ...] = (),
             obj: tuple[str, ...] = ()) -> None:
        stmts.append(st)
        goi.append(P.LoiGoiPrimitive(prim, len(st), src, der))
        buoc.append(BuocDung(len(buoc) + 1, prim, mo_ta, src, der, obj))
        dan_xuat.extend(der)

    def _src(*pts: str) -> tuple[str, ...]:
        f = graph.do_dai(*pts) if len(pts) == 2 else None
        return (f.source_fact_id,) if f and f.source_fact_id else ()

    # 1 · Đỉnh đáy ở chân cạnh bên vuông góc, tại gốc toạ độ
    them("declare_point", P.declare_point(b.foot, toa_do[b.foot]),
         f"Đặt đỉnh {b.foot} của đáy làm gốc toạ độ.",
         der=(f"layout_{b.foot}",), obj=(b.foot,))
    # 2 · Cạnh thứ nhất của đáy dọc trục X
    them("declare_point", P.declare_point(b.adj_1, toa_do[b.adj_1]),
         "Dựng cạnh thứ nhất của đáy theo độ dài đề cho.",
         _src(b.foot, b.adj_1), (f"layout_{b.adj_1}",), (b.adj_1,))
    # 3 · Cạnh thứ hai của đáy dọc trục Y
    them("declare_point", P.declare_point(b.adj_2, toa_do[b.adj_2]),
         "Dựng cạnh thứ hai của đáy vuông góc với cạnh thứ nhất.",
         _src(b.foot, b.adj_2), (f"layout_{b.adj_2}",), (b.adj_2,))
    # 4 · Đỉnh đối diện của đáy
    them("declare_point", P.declare_point(b.opposite, toa_do[b.opposite]),
         "Dựng đỉnh thứ tư của đáy hình chữ nhật/vuông từ hai cạnh đã dựng.",
         (), (f"layout_{b.opposite}",), (b.opposite,))
    # 5 · Đỉnh chóp trên trục Z
    them("declare_point", P.declare_point(b.apex, toa_do[b.apex]),
         "Đặt đỉnh chóp theo chiều cao đề cho.",
         _src(b.foot, b.apex), (f"layout_{b.apex}",), (b.apex,))
    # 6 · Dựng mặt đáy (phép đo diện tích cần nó). Đường cao và các cạnh bên do
    # bước bổ sung dựng hình theo lớp (`semantic_program.formation`) dựng — W14.
    them("construct_polygon",
         P.construct_polygon(ten_day, b.base_cycle, f"Đáy {''.join(b.base_cycle)}"),
         f"Dựng mặt phẳng đáy {''.join(b.base_cycle)} từ 4 đỉnh đã có.",
         der=(f"derived_{ten_day}",), obj=(ten_day,))
    # 7 · Khối chóp
    them("construct_pyramid",
         P.construct_pyramid(ten_khoi, b.apex, b.base_cycle, f"{b.apex}.{''.join(b.base_cycle)}"),
         "Hoàn thiện khối chóp từ đỉnh và các mặt bên.",
         der=(f"derived_{ten_khoi}",), obj=(ten_khoi,))
    # 8 · Diện tích mặt đáy
    them("measure_quantity", P.measure_quantity(ten_dt, "area", ten_day),
         "Tính diện tích mặt đáy.", der=(f"derived_{ten_dt}",))
    # 9 · Thể tích khối chóp
    them("measure_quantity", P.measure_quantity(ten_tt, "volume", ten_khoi),
         "Tính thể tích khối chóp.", der=(f"derived_{ten_tt}",))
    # 10 · Ghi kết quả vào biến witness
    them("assign_final_memory", P.assign_final_memory(b.witness, ten_tt),
         "Ghi thể tích vào biến mà đề yêu cầu.", der=(b.witness,))

    # Khai báo bộ nhớ: Dữ kiện độ dài đề cho (GIVEN)
    f_len1 = graph.do_dai(b.foot, b.adj_1)
    f_len2 = graph.do_dai(b.foot, b.adj_2)
    f_height = graph.do_dai(b.foot, b.apex)
    src_len1 = f_len1.source_fact_id if f_len1 and f_len1.source_fact_id else None
    src_len2 = f_len2.source_fact_id if f_len2 and f_len2.source_fact_id else None
    src_height = f_height.source_fact_id if f_height and f_height.source_fact_id else None

    name_len1 = f"{b.foot}{b.adj_1}_length"
    name_len2 = f"{b.foot}{b.adj_2}_length"
    name_height = f"{b.apex}{b.foot}_length"

    label_len1 = f"{b.foot}{b.adj_1}"
    label_len2 = f"{b.foot}{b.adj_2}"
    label_height = f"{b.apex}{b.foot}"

    prov_len1 = f_len1.status if f_len1 else None
    prov_len2 = f_len2.status if f_len2 else None
    prov_height = f_height.status if f_height else None

    khai.append(P.memory_declaration(name_len1, P.KIEU_DAI_LUONG, provenance=prov_len1,
                                     source_fact_id=src_len1, initial_value=P._so(b.len_adj1)))
    if b.variant == "rectangle" or (f_len2 is not None and name_len2 != name_len1):
        khai.append(P.memory_declaration(name_len2, P.KIEU_DAI_LUONG, provenance=prov_len2,
                                         source_fact_id=src_len2, initial_value=P._so(b.len_adj2)))
    khai.append(P.memory_declaration(name_height, P.KIEU_DAI_LUONG, provenance=prov_height,
                                     source_fact_id=src_height, initial_value=P._so(b.len_height)))

    # Khai báo toạ độ các đỉnh (LAYOUT_DERIVED)
    for pt in (b.foot, b.adj_1, b.adj_2, b.opposite, b.apex):
        khai.append(P.memory_declaration(pt, "point3", provenance="LAYOUT_DERIVED"))

    # Khai báo các đối tượng hình học dựng ra
    khai.append(P.memory_declaration(ten_day, "polygon3"))
    khai.append(P.memory_declaration(ten_khoi, "solid"))

    seen_mem = {b.foot, b.adj_1, b.adj_2, b.opposite, b.apex, ten_day,
                ten_khoi, name_len1, name_len2, name_height}
    for t in (ten_dt, ten_tt, b.witness):
        if t not in seen_mem:
            khai.append(P.memory_declaration(t, P.KIEU_DAI_LUONG))
            seen_mem.add(t)

    title = (
        "Thể tích khối chóp có đáy là hình vuông"
        if b.variant == "square"
        else "Thể tích khối chóp có đáy là hình chữ nhật"
    )
    program = {
        "title": title,
        "memory_declarations": khai,
        "statements": stmts,
    }
    return KetQuaBienDich(
        "COMPILED", program, tuple(goi), tuple(buoc), tuple(dan_xuat),
        elapsed_ms=(time.perf_counter() - t0) * 1000)


def _bien_dich_cuboid(
    graph: GeometryFactGraph,
    b: RangBuocCuboid,
    t0: float,
) -> KetQuaBienDich:
    """Biên dịch FactGraph sang chương trình ngữ nghĩa cho cuboid/cube/right square prism."""
    Z = Fraction(0)
    toa_do: dict[str, tuple[Fraction, Fraction, Fraction]] = {
        b.origin_pt: (Z, Z, Z),
        b.adj_1: (b.len_adj1, Z, Z),
        b.opposite: (b.len_adj1, b.len_adj2, Z),
        b.adj_2: (Z, b.len_adj2, Z),
    }
    corr_map = dict(b.correspondence_ids)
    for base_id in (b.origin_pt, b.adj_1, b.opposite, b.adj_2):
        top_id = corr_map[base_id]
        bx, by, _ = toa_do[base_id]
        toa_do[top_id] = (bx, by, b.len_height)

    ten_day_duoi = f"day_{''.join(b.base_cycle_ids)}"
    ten_khoi = b.container
    ten_dt = f"dien_tich_{ten_day_duoi}"
    ten_cao = f"chieu_cao_{b.origin_pt}{b.origin_top}"
    ten_tt = f"the_tich_{ten_khoi}"

    goi: list[P.LoiGoiPrimitive] = []
    buoc: list[BuocDung] = []
    stmts: list[dict[str, Any]] = []
    khai: list[dict[str, Any]] = []
    dan_xuat: list[str] = []

    def them(prim: str, st: dict[str, Any], mo_ta: str,
             src: tuple[str, ...] = (), der: tuple[str, ...] = (),
             obj: tuple[str, ...] = ()) -> None:
        stmts.append(st)
        goi.append(P.LoiGoiPrimitive(prim, len(st), src, der))
        buoc.append(BuocDung(len(buoc) + 1, prim, mo_ta, src, der, obj))
        dan_xuat.extend(der)

    def _src(*pts: str) -> tuple[str, ...]:
        f = graph.do_dai(pts[0], pts[1]) if len(pts) == 2 else None
        return (f.source_fact_id,) if f and f.source_fact_id else ()

    # Dimension memories mirror the actual evidence graph.  A dimension that is
    # known only through the classified solid (equal cube edges, square-base
    # edges, or equal lateral edges) is computed by an assignment; it must not
    # masquerade as another GIVEN fact merely because the numeric values match.
    v0, v1, v2, v3 = b.base_cycle_ids
    direct_len1 = graph.do_dai(v0, v1)
    direct_len2 = graph.do_dai(v0, v3)
    direct_height = graph.do_dai(v0, corr_map[v0])
    opposite_len1 = graph.do_dai(v2, v3)
    opposite_len2 = graph.do_dai(v1, v2)
    lateral_facts = tuple(
        f for u, v in b.correspondence_ids
        if (f := graph.do_dai(u, v)) is not None
    )

    name_len1 = f"{v0}{v1}_length"
    name_len2 = f"{v0}{v3}_length"
    name_height = f"{v0}{corr_map[v0]}_length"
    dimension_specs = (
        (name_len1, (v0, v1), b.len_adj1, direct_len1,
         direct_len1 or opposite_len1),
        (name_len2, (v0, v3), b.len_adj2, direct_len2,
         direct_len2 or opposite_len2),
        (name_height, (v0, corr_map[v0]), b.len_height, direct_height,
         direct_height or (lateral_facts[0] if lateral_facts else None)),
    )

    all_dimension_facts = tuple(
        f for f in (
            direct_len1, opposite_len1, direct_len2, opposite_len2,
            *lateral_facts,
        ) if f is not None
    )
    common_cube_fact = all_dimension_facts[0] if all_dimension_facts else None
    base_square_fact = (
        direct_len1 or opposite_len1 or direct_len2 or opposite_len2
    )

    declared_dimensions: set[str] = set()
    derived_dimensions: list[tuple[str, str, str | None, str, str]] = []

    def _segment_memory(fact: Any) -> tuple[str, str]:
        a, z = fact.args
        symbol = f"{b.display_labels.get(a, a)}{b.display_labels.get(z, z)}"
        return f"{a}{z}_length", symbol

    def _declare_given_dimension(name: str, fact: Any, value: Fraction) -> None:
        if name in declared_dimensions:
            return
        khai.append(P.memory_declaration(
            name,
            P.KIEU_DAI_LUONG,
            provenance=fact.status,
            source_fact_id=fact.source_fact_id,
            initial_value=P._so(value),
        ))
        declared_dimensions.add(name)

    for index, (target, endpoints, value, direct_fact, selected_fact) in enumerate(dimension_specs):
        if direct_fact is not None:
            _declare_given_dimension(target, direct_fact, value)
            continue

        if b.solid_subkind == "cube":
            selected_fact = selected_fact or common_cube_fact
        elif index < 2 and (
            b.solid_subkind == "right_square_prism" or b.base_shape == "square"
        ):
            selected_fact = selected_fact or base_square_fact

        # Eligibility has already proved that every required dimension has a
        # concrete source. Keep this guard fail-closed if that invariant changes.
        if selected_fact is None:
            raise ValueError(f"Missing proven source for cuboid dimension {target}")

        source_name, source_symbol = _segment_memory(selected_fact)
        if source_name not in declared_dimensions:
            _declare_given_dimension(
                source_name, selected_fact, Fraction(str(selected_fact.value))
            )
        khai.append(P.memory_declaration(target, P.KIEU_DAI_LUONG))
        declared_dimensions.add(target)
        target_symbol = "".join(b.display_labels.get(p, p) for p in endpoints)
        derived_dimensions.append((
            target,
            source_name,
            selected_fact.source_fact_id,
            target_symbol,
            source_symbol,
        ))

    for target, source, source_fact_id, target_symbol, source_symbol in derived_dimensions:
        them(
            "assign_final_memory",
            P.assign_final_memory(target, source),
            f"Suy ra {target_symbol} = {source_symbol} từ phân loại hình học đã được kiểm chứng.",
            (source_fact_id,) if source_fact_id else (),
            (f"derived_{target}",),
        )

    # 1 · Đỉnh gốc đáy dưới tại (0,0,0)
    lbl_0 = b.display_labels.get(b.origin_pt, b.origin_pt)
    them("declare_point", P.declare_point(b.origin_pt, toa_do[b.origin_pt], nhan=lbl_0),
         f"Đặt đỉnh {lbl_0} của mặt đáy dưới làm gốc toạ độ.",
         der=(f"layout_{b.origin_pt}",), obj=(b.origin_pt,))

    # 2 · Cạnh thứ nhất của đáy dưới dọc trục X
    lbl_1 = b.display_labels.get(b.adj_1, b.adj_1)
    them("declare_point", P.declare_point(b.adj_1, toa_do[b.adj_1], nhan=lbl_1),
         f"Dựng đỉnh {lbl_1} theo độ dài cạnh thứ nhất của đáy.",
         _src(b.origin_pt, b.adj_1), (f"layout_{b.adj_1}",), (b.adj_1,))

    # 3 · Cạnh thứ hai của đáy dưới dọc trục Y
    lbl_2 = b.display_labels.get(b.adj_2, b.adj_2)
    them("declare_point", P.declare_point(b.adj_2, toa_do[b.adj_2], nhan=lbl_2),
         f"Dựng đỉnh {lbl_2} theo độ dài cạnh thứ hai của đáy vuông góc với cạnh thứ nhất.",
         _src(b.origin_pt, b.adj_2), (f"layout_{b.adj_2}",), (b.adj_2,))

    # 4 · Đỉnh thứ tư của đáy dưới
    lbl_opp = b.display_labels.get(b.opposite, b.opposite)
    them("declare_point", P.declare_point(b.opposite, toa_do[b.opposite], nhan=lbl_opp),
         f"Dựng đỉnh {lbl_opp} hoàn thiện mặt đáy dưới.",
         (), (f"layout_{b.opposite}",), (b.opposite,))

    # 5 · Các đỉnh đáy trên theo chiều cao
    for base_id in (b.origin_pt, b.adj_1, b.opposite, b.adj_2):
        top_id = corr_map[base_id]
        lbl_top = b.display_labels.get(top_id, top_id)
        lbl_b = b.display_labels.get(base_id, base_id)
        them("declare_point", P.declare_point(top_id, toa_do[top_id], nhan=lbl_top),
             f"Dựng đỉnh {lbl_top} tương ứng với đỉnh {lbl_b} đáy dưới theo chiều cao.",
             _src(base_id, top_id), (f"layout_{top_id}",), (top_id,))

    # 6 · Dựng mặt đáy dưới (phép đo diện tích cần nó). Đáy trên và các cạnh bên do
    # bước bổ sung dựng hình theo lớp (`semantic_program.formation`) dựng — W14.
    base_lbls = "".join(b.display_labels.get(u, u) for u in b.base_cycle_ids)
    them("construct_polygon",
         P.construct_polygon(ten_day_duoi, b.base_cycle_ids, nhan=f"đáy dưới {base_lbls}"),
         f"Dựng đáy dưới {base_lbls}.",
         der=(f"derived_{ten_day_duoi}",), obj=(ten_day_duoi,))

    # 7 · Dựng khối lăng trụ / hình hộp (construct_prism)
    top_lbls = "".join(b.display_labels.get(u, u) for u in b.top_cycle_ids)
    if b.family_id == SUPPORTED_FAMILY_CUBE:
        solid_label = f"Hình lập phương {base_lbls}.{top_lbls}"
    elif b.family_id == SUPPORTED_FAMILY_SQUARE_PRISM:
        solid_label = f"Lăng trụ đứng đáy vuông {base_lbls}.{top_lbls}"
    else:
        solid_label = f"Hình hộp chữ nhật {base_lbls}.{top_lbls}"

    _prism_stmt = P.construct_prism(ten_khoi, b.base_cycle_ids, b.top_cycle_ids, b.correspondence_ids)
    _prism_stmt["label"] = solid_label
    them("construct_prism",
         _prism_stmt,
         f"Dựng {solid_label} từ 8 đỉnh và 6 mặt.",
         der=(f"derived_{ten_khoi}",), obj=(ten_khoi,))

    # 8 · Diện tích mặt đáy
    them("measure_quantity", P.measure_quantity(ten_dt, "area", ten_day_duoi),
         f"Tính diện tích đáy S_{base_lbls}.", der=(f"derived_{ten_dt}",))

    # 9 · Chiều cao
    h_lu = b.display_labels.get(b.origin_pt, b.origin_pt)
    h_lv = b.display_labels.get(b.origin_top, b.origin_top)
    them("measure_quantity", P.measure_quantity(ten_cao, "distance", b.origin_pt, wrt=b.origin_top),
         f"Xác định chiều cao {h_lu}{h_lv}.", der=(f"derived_{ten_cao}",))

    # 10 · Thể tích khối
    them("measure_quantity", P.measure_quantity(ten_tt, "volume", ten_khoi),
         "Tính thể tích V.", der=(f"derived_{ten_tt}",))

    # 11 · Gán đáp số cuối vào witness
    them("assign_final_memory", P.assign_final_memory(b.witness, ten_tt),
         "Ghi thể tích vào biến mà đề yêu cầu.", der=(b.witness,))

    for pt_id in (*b.base_cycle_ids, *b.top_cycle_ids):
        khai.append(P.memory_declaration(pt_id, "point3", provenance="LAYOUT_DERIVED"))

    khai.append(P.memory_declaration(ten_day_duoi, "polygon3"))
    khai.append(P.memory_declaration(ten_khoi, "solid"))

    seen_mem = {*declared_dimensions, *b.base_cycle_ids, *b.top_cycle_ids, ten_day_duoi,
                ten_khoi, name_len1, name_len2, name_height}
    for t in (ten_dt, ten_cao, ten_tt, b.witness):
        if t not in seen_mem:
            khai.append(P.memory_declaration(t, P.KIEU_DAI_LUONG))
            seen_mem.add(t)

    title = (
        "Thể tích khối lập phương"
        if b.family_id == SUPPORTED_FAMILY_CUBE
        else "Thể tích khối lăng trụ đứng có đáy là hình vuông"
        if b.family_id == SUPPORTED_FAMILY_SQUARE_PRISM
        else "Thể tích khối hộp chữ nhật"
    )

    program = {
        "title": title,
        "memory_declarations": khai,
        "statements": stmts,
    }
    return KetQuaBienDich(
        "COMPILED", program, tuple(goi), tuple(buoc), tuple(dan_xuat),
        elapsed_ms=(time.perf_counter() - t0) * 1000)




def _bien_dich_oblique_prism(
    graph: GeometryFactGraph,
    b: RangBuocObliquePrism,
    t0: float,
) -> KetQuaBienDich:
    """G04 — đáy và đỉnh neo do bố cục đặt; đáy trên là ẢNH TỊNH TIẾN của đáy dưới, do KERNEL tính."""
    nhan = lambda u: b.display_labels.get(u, u)  # noqa: E731
    ky = lambda *us: "".join(nhan(u) for u in us)  # noqa: E731
    tuong_ung = dict(b.correspondence)
    T, B0, F = b.anchor_top, b.anchor_base, b.foot
    toa_day = dict(zip(b.base_cycle, b.base_coords))
    fx, fy, fz = toa_day[F]

    ten_day = f"day_{''.join(b.base_cycle)}"
    ten_mat = f"mat_day_{''.join(b.base_cycle)}"
    ten_vec = f"vec_{B0}{T}"
    ten_khoi = b.container
    ten_dt = f"dien_tich_{ten_day}"
    ten_cao = f"chieu_cao_{T}"
    ten_tt = f"the_tich_{ten_khoi}"
    goi: list[P.LoiGoiPrimitive] = []
    buoc: list[BuocDung] = []
    stmts: list[dict[str, Any]] = []
    khai: list[dict[str, Any]] = []
    dan_xuat: list[str] = []

    def them(prim: str, st: dict[str, Any], mo_ta: str,
             src: tuple[str, ...] = (), der: tuple[str, ...] = (),
             obj: tuple[str, ...] = ()) -> None:
        stmts.append(st)
        goi.append(P.LoiGoiPrimitive(prim, len(st), src, der))
        buoc.append(BuocDung(len(buoc) + 1, prim, mo_ta, src, der, obj))
        dan_xuat.extend(der)

    def _src(*doan: tuple[str, str]) -> tuple[str, ...]:
        return tuple(sorted({f.source_fact_id for d in doan
                             if (f := graph.do_dai(*d)) is not None and f.source_fact_id}))

    # 1 · Đáy dưới theo bố cục chính tắc (ℚ³)
    for u in b.base_cycle:
        canh = tuple(d for d in b.base_segments if u in d and toa_day[u] != (0, 0, 0))
        them("declare_point", P.declare_point(u, toa_day[u], nhan=nhan(u)),
             f"Đặt đỉnh {nhan(u)} của đáy dưới" + (" theo độ dài cạnh đề cho." if canh else " làm gốc toạ độ."
                                                   if toa_day[u] == (0, 0, 0) else "."),
             _src(*canh), (f"layout_{u}",), (u,))
    them("construct_polygon", P.construct_polygon(ten_day, b.base_cycle, nhan=f"đáy {ky(*b.base_cycle)}"),
         f"Dựng đáy dưới {ky(*b.base_cycle)}.", der=(f"derived_{ten_day}",), obj=(ten_day,))
    # 2 · Đỉnh neo trên pháp tuyến của đáy tại chân F (quan hệ ⟂ ĐỀ CHO)
    them("declare_point", P.declare_point(T, (fx, fy, fz + b.height), nhan=nhan(T)),
         f"Dựng {nhan(T)} trên đường thẳng vuông góc với đáy tại {nhan(F)} "
         f"({ky(T, F)} ⊥ đáy), cách đáy đúng chiều cao.",
         tuple(sorted({*_src(b.height_segment), *((b.foot_source_fact_id,) if b.foot_source_fact_id else ())})),
         (f"layout_{T}",), (T,))
    # 3 · Cạnh bên: vectơ B0→T, và các đỉnh đáy trên là ảnh tịnh tiến — kernel tính
    them("vector_from_points", P.vector_from_points(ten_vec, B0, T),
         f"Lấy vectơ cạnh bên {ky(B0, T)}.", der=(f"derived_{ten_vec}",))
    for u in b.base_cycle:
        if u == B0:
            continue
        v = tuong_ung[u]
        them("translate_point", P.translate_point(v, u, ten_vec, nhan=nhan(v)),
             f"Tịnh tiến {nhan(u)} theo vectơ {ky(B0, T)} được {nhan(v)} "
             f"(cạnh bên {ky(u, v)} song song và bằng {ky(B0, T)}).",
             der=(f"derived_{v}",), obj=(v,))
    # 4 · Khối
    khoi = P.construct_prism(ten_khoi, b.base_cycle, b.top_cycle, b.correspondence)
    khoi["label"] = f"Lăng trụ xiên {ky(*b.base_cycle)}.{ky(*b.top_cycle)}"
    them("construct_prism", khoi, f"Dựng {khoi['label']} từ hai đáy và các cạnh bên.",
         der=(f"derived_{ten_khoi}",), obj=(ten_khoi,))
    # 5 · Đo — diện tích đáy, chiều cao (khoảng cách đỉnh neo tới MẶT PHẲNG đáy), thể tích
    them("measure_quantity", P.measure_quantity(ten_dt, "area", ten_day),
         f"Tính diện tích đáy S_{ky(*b.base_cycle)}.", der=(f"derived_{ten_dt}",))
    them("construct_plane", {"kind": "construct_plane", "target_var": ten_mat,
                             "through": list(b.base_cycle[:3]), "label": f"({ky(*b.base_cycle[:3])})"},
         "Mặt phẳng đáy để đo chiều cao.", der=(f"derived_{ten_mat}",), obj=(ten_mat,))
    them("measure_quantity", P.measure_quantity(ten_cao, "distance", T, wrt=ten_mat),
         f"Chiều cao lăng trụ = khoảng cách từ {nhan(T)} tới mặt phẳng đáy.", der=(f"derived_{ten_cao}",))
    them("measure_quantity", P.measure_quantity(ten_tt, "volume", ten_khoi),
         "Tính thể tích V.", der=(f"derived_{ten_tt}",))
    them("assign_final_memory", P.assign_final_memory(b.witness, ten_tt),
         "Ghi thể tích vào biến mà đề yêu cầu.", der=(b.witness,))

    khai.extend(_khai_do_dai_de_cho(graph, tuple(dict.fromkeys((*b.base_segments, b.height_segment)))))
    for u in (*b.base_cycle, T):
        khai.append(P.memory_declaration(u, "point3", provenance="LAYOUT_DERIVED"))
    khai.append(P.memory_declaration(ten_day, "polygon3"))
    khai.append(P.memory_declaration(ten_khoi, "solid"))
    for t in dict.fromkeys((ten_dt, ten_cao, ten_tt, b.witness)):
        khai.append(P.memory_declaration(t, P.KIEU_DAI_LUONG))

    program = {
        "title": "Thể tích khối lăng trụ xiên",
        "memory_declarations": khai,
        "statements": stmts,
    }
    return KetQuaBienDich(
        "COMPILED", program, tuple(goi), tuple(buoc), tuple(dan_xuat),
        elapsed_ms=(time.perf_counter() - t0) * 1000)
