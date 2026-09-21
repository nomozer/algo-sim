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
class KetQuaEligibility:
    status: str
    binding: RangBuocHo | None = None
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
