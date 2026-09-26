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
SUPPORTED_FAMILIES = (
    SUPPORTED_FAMILY,
    SUPPORTED_FAMILY_PRISM,
    SUPPORTED_FAMILY_RECT_PYRAMID,
    SUPPORTED_FAMILY_CUBOID,
    SUPPORTED_FAMILY_CUBE,
    SUPPORTED_FAMILY_SQUARE_PRISM,
)

TRANG_THAI_ELIGIBILITY: tuple[str, ...] = (
    "SUPPORTED",
    "UNSUPPORTED_MISSING_FACT",
    "UNSUPPORTED_EXTRA_OBLIGATION",
    "UNSUPPORTED_SYMBOLIC_LENGTH",
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
class KetQuaEligibility:
    status: str
    binding: RangBuocHo | RangBuocPrism | RangBuocRectPyramid | RangBuocCuboid | None = None
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
    # 5 + 6 · đường cao theo pháp tuyến, và đỉnh chóp
    them("declare_point", P.declare_point(b.dinh_chop, toa_do[b.dinh_chop]),
         "Dựng đường cao vuông góc với mặt phẳng đáy rồi đặt đỉnh chóp theo "
         "độ dài đề cho.",
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
    ten_cao = f"chieu_cao_{b.apex}{b.foot}"
    ten_canh_ben = f"canh_ben_{b.apex}{b.opposite}"
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

    # 1 · Chân đường cao tại gốc toạ độ
    them("declare_point", P.declare_point(b.foot, toa_do[b.foot]),
         "Đặt chân đường cao của hình chóp làm gốc toạ độ.",
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
         "Dựng đường cao vuông góc với mặt phẳng đáy rồi đặt đỉnh chóp.",
         _src(b.foot, b.apex), (f"layout_{b.apex}",), (b.apex,))
    # 6 · Dựng mặt đáy
    them("construct_polygon",
         P.construct_polygon(ten_day, b.base_cycle, f"Đáy {''.join(b.base_cycle)}"),
         f"Dựng mặt phẳng đáy {''.join(b.base_cycle)} từ 4 đỉnh đã có.",
         der=(f"derived_{ten_day}",), obj=(ten_day,))
    # 7 · Dựng đường cao (đoạn thẳng hữu hạn SA)
    them("construct_segment",
         P.construct_segment(ten_cao, b.apex, b.foot, f"Chiều cao {b.apex}{b.foot}"),
         f"Dựng đường cao {b.apex}{b.foot} vuông góc với mặt đáy.",
         _src(b.foot, b.apex), (f"derived_{ten_cao}",), (ten_cao,))
    # 8 · Dựng đồng thời các cạnh bên SB, SC, SD
    ten_sb = f"canh_ben_{b.apex}{b.adj_1}"
    ten_sc = f"canh_ben_{b.apex}{b.opposite}"
    ten_sd = f"canh_ben_{b.apex}{b.adj_2}"
    items_canh_ben = [
        {"name": ten_sb, "endpoint_a": b.apex, "endpoint_b": b.adj_1, "label": f"Cạnh bên {b.apex}{b.adj_1}"},
        {"name": ten_sc, "endpoint_a": b.apex, "endpoint_b": b.opposite, "label": f"Cạnh bên {b.apex}{b.opposite}"},
        {"name": ten_sd, "endpoint_a": b.apex, "endpoint_b": b.adj_2, "label": f"Cạnh bên {b.apex}{b.adj_2}"},
    ]
    ten_canh_ben = "canh_ben"
    them("construct_segments_group",
         P.construct_segments_group(ten_canh_ben, items_canh_ben, f"Các cạnh bên {b.apex}{b.adj_1}, {b.apex}{b.opposite}, {b.apex}{b.adj_2}"),
         f"Dựng các cạnh bên {b.apex}{b.adj_1}, {b.apex}{b.opposite}, {b.apex}{b.adj_2} từ đỉnh tới các đỉnh đáy.",
         der=(f"derived_{ten_canh_ben}",), obj=(ten_sb, ten_sc, ten_sd))
    # 9 · Khối chóp
    them("construct_pyramid",
         P.construct_pyramid(ten_khoi, b.apex, b.base_cycle, f"{b.apex}.{''.join(b.base_cycle)}"),
         "Hoàn thiện khối chóp từ đỉnh và các mặt bên.",
         der=(f"derived_{ten_khoi}",), obj=(ten_khoi,))
    # 10 · Diện tích mặt đáy
    them("measure_quantity", P.measure_quantity(ten_dt, "area", ten_day),
         "Tính diện tích mặt đáy.", der=(f"derived_{ten_dt}",))
    # 11 · Thể tích khối chóp
    them("measure_quantity", P.measure_quantity(ten_tt, "volume", ten_khoi),
         "Tính thể tích khối chóp.", der=(f"derived_{ten_tt}",))
    # 12 · Ghi kết quả vào biến witness
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
    khai.append(P.memory_declaration(ten_cao, "segment3"))
    khai.append(P.memory_declaration(ten_sb, "segment3"))
    khai.append(P.memory_declaration(ten_sc, "segment3"))
    khai.append(P.memory_declaration(ten_sd, "segment3"))
    khai.append(P.memory_declaration(ten_khoi, "solid"))

    seen_mem = {b.foot, b.adj_1, b.adj_2, b.opposite, b.apex, ten_day, ten_cao,
                ten_sb, ten_sc, ten_sd, ten_canh_ben,
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
    ten_day_tren = f"day_{''.join(b.top_cycle_ids)}"
    ten_canh_ben = "canh_ben"
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

    # 6 · Dựng mặt đáy dưới
    base_lbls = "".join(b.display_labels.get(u, u) for u in b.base_cycle_ids)
    them("construct_polygon",
         P.construct_polygon(ten_day_duoi, b.base_cycle_ids, nhan=f"Đáy dưới {base_lbls}"),
         f"Dựng mặt phẳng đáy dưới {base_lbls} từ 4 đỉnh đã có.",
         der=(f"derived_{ten_day_duoi}",), obj=(ten_day_duoi,))

    # 7 · Dựng mặt đáy trên
    top_lbls = "".join(b.display_labels.get(u, u) for u in b.top_cycle_ids)
    them("construct_polygon",
         P.construct_polygon(ten_day_tren, b.top_cycle_ids, nhan=f"Đáy trên {top_lbls}"),
         f"Dựng mặt phẳng đáy trên {top_lbls} song song và tương ứng với đáy dưới.",
         der=(f"derived_{ten_day_tren}",), obj=(ten_day_tren,))

    # 8 · Dựng các cạnh bên hữu hạn bằng construct_segments_group
    items_canh_ben = []
    lat_seg_names = []
    for u_id, v_id in b.correspondence_ids:
        seg_name = f"canh_ben_{u_id}_{v_id}"
        lat_seg_names.append(seg_name)
        lu = b.display_labels.get(u_id, u_id)
        lv = b.display_labels.get(v_id, v_id)
        items_canh_ben.append({
            "name": seg_name,
            "endpoint_a": u_id,
            "endpoint_b": v_id,
            "label": f"Cạnh bên {lu}{lv}",
        })
    them("construct_segments_group",
         P.construct_segments_group(ten_canh_ben, items_canh_ben, nhan="Các cạnh bên"),
         "Dựng đồng thời các cạnh bên nối tương ứng các đỉnh của hai đáy.",
         der=(f"derived_{ten_canh_ben}",), obj=tuple(lat_seg_names))

    # 9 · Dựng khối lăng trụ / hình hộp (construct_prism)
    them("construct_prism",
         P.construct_prism(ten_khoi, b.base_cycle_ids, b.top_cycle_ids, b.correspondence_ids),
         "Bao đóng hoàn thiện khối từ hai đáy và các mặt bên.",
         der=(f"derived_{ten_khoi}",), obj=(ten_khoi,))

    # 10 · Diện tích mặt đáy
    them("measure_quantity", P.measure_quantity(ten_dt, "area", ten_day_duoi),
         "Tính diện tích mặt đáy dưới.", der=(f"derived_{ten_dt}",))

    # 11 · Chiều cao
    them("measure_quantity", P.measure_quantity(ten_cao, "distance", b.origin_pt, wrt=b.origin_top),
         "Xác định chiều cao của khối.", der=(f"derived_{ten_cao}",))

    # 12 · Thể tích khối
    them("measure_quantity", P.measure_quantity(ten_tt, "volume", ten_khoi),
         "Tính thể tích khối.", der=(f"derived_{ten_tt}",))

    # 13 · Gán đáp số cuối vào witness
    them("assign_final_memory", P.assign_final_memory(b.witness, ten_tt),
         "Ghi thể tích vào biến mà đề yêu cầu.", der=(b.witness,))

    # Memory declarations
    f_len1 = graph.do_dai(b.origin_pt, b.adj_1)
    f_len2 = graph.do_dai(b.origin_pt, b.adj_2)
    f_h = graph.do_dai(b.origin_pt, b.origin_top)
    prov_len1 = f_len1.status if f_len1 else None
    prov_len2 = f_len2.status if f_len2 else None
    prov_h = f_h.status if f_h else None

    if b.solid_subkind == "cube":
        edge_fact = f_len1 or f_len2 or f_h or next((graph.do_dai(u, v) for u, v in b.correspondence_ids if graph.do_dai(u, v)), None)
        edge_name = f"{b.origin_pt}{b.adj_1}_length"
        edge_src = edge_fact.source_fact_id if edge_fact and edge_fact.source_fact_id else None
        edge_prov = edge_fact.status if edge_fact else None
        khai.append(P.memory_declaration(edge_name, P.KIEU_DAI_LUONG, provenance=edge_prov,
                                         source_fact_id=edge_src, initial_value=P._so(b.len_adj1)))
        name_len2 = f"{b.origin_pt}{b.adj_2}_length"
        name_height = f"{b.origin_pt}{b.origin_top}_length"
        khai.append(P.memory_declaration(name_len2, P.KIEU_DAI_LUONG, provenance=edge_prov,
                                         source_fact_id=edge_src,
                                         initial_value=P._so(b.len_adj2)))
        khai.append(P.memory_declaration(name_height, P.KIEU_DAI_LUONG, provenance=edge_prov,
                                         source_fact_id=edge_src,
                                         initial_value=P._so(b.len_height)))
    else:
        name_len1 = f"{b.origin_pt}{b.adj_1}_length"
        src_1 = f_len1.source_fact_id if f_len1 and f_len1.source_fact_id else None
        khai.append(P.memory_declaration(name_len1, P.KIEU_DAI_LUONG, provenance=prov_len1,
                                         source_fact_id=src_1, initial_value=P._so(b.len_adj1)))
        name_len2 = f"{b.origin_pt}{b.adj_2}_length"
        src_2 = f_len2.source_fact_id if f_len2 and f_len2.source_fact_id else None
        if b.solid_subkind == "right_square_prism" and not src_2:
            khai.append(P.memory_declaration(name_len2, P.KIEU_DAI_LUONG, provenance=prov_len1,
                                             source_fact_id=src_1,
                                             initial_value=P._so(b.len_adj2)))
        else:
            khai.append(P.memory_declaration(name_len2, P.KIEU_DAI_LUONG, provenance=prov_len2,
                                             source_fact_id=src_2, initial_value=P._so(b.len_adj2)))
        name_height = f"{b.origin_pt}{b.origin_top}_length"
        src_h = f_h.source_fact_id if f_h and f_h.source_fact_id else None
        khai.append(P.memory_declaration(name_height, P.KIEU_DAI_LUONG, provenance=prov_h,
                                         source_fact_id=src_h, initial_value=P._so(b.len_height)))

    for pt_id in (*b.base_cycle_ids, *b.top_cycle_ids):
        khai.append(P.memory_declaration(pt_id, "point3", provenance="LAYOUT_DERIVED"))

    khai.append(P.memory_declaration(ten_day_duoi, "polygon3"))
    khai.append(P.memory_declaration(ten_day_tren, "polygon3"))
    for seg_name in lat_seg_names:
        khai.append(P.memory_declaration(seg_name, "segment3"))
    khai.append(P.memory_declaration(ten_khoi, "solid"))

    seen_mem = {*b.base_cycle_ids, *b.top_cycle_ids, ten_day_duoi, ten_day_tren,
                *lat_seg_names, ten_canh_ben, ten_khoi,
                f"{b.origin_pt}{b.adj_1}_length", f"{b.origin_pt}{b.adj_2}_length",
                f"{b.origin_pt}{b.origin_top}_length"}
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


