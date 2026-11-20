# -*- coding: utf-8 -*-
"""Lớp TRẠNG THÁI MÔ PHỎNG — giữa interpreter và renderer. **0 API call.**

    Semantic Program → Interpreter → **Simulation State** → Renderer 3D

VÌ SAO TỒN TẠI: `memory_snapshot` chứa `Vec3`/`Plane3`/`Polyhedron` dưới dạng
**đối tượng Python**. Renderer không đọc được. File này chiếu chúng sang JSON.

─── LUẬT SỐ MỘT: CHIẾU, KHÔNG TÍNH ──────────────────────────────────────────

Không một dòng nào ở đây làm hình học. Không `cross`, không `dot`, không dựng
điểm. Mọi giá trị đến từ thứ kernel đã tính; file này chỉ **sắp lại**. Một phép
tính hình học lọt vào đây là dựng engine thứ hai — và hai engine thì sẽ lệch,
lệch câm.

Hệ quả cụ thể của luật ấy, và nó định hình toàn bộ thiết kế: `Line3` là đường
**vô hạn** (điểm + vector chỉ phương), `Plane3` là `n·x = d` — cũng **vô hạn**.
Muốn vẽ thì phải có biên hữu hạn, và biên ấy **không có trong kernel**.

Cách giải KHÔNG phải tính biên ở đây. Cách giải là **chở PROVENANCE**: đường
thẳng mang tên hai điểm sinh ra nó, mặt phẳng mang tên ba điểm sinh ra nó. Toạ
độ của những điểm ấy đã có sẵn trong cảnh, nên renderer dựng được biên mà lớp
này không phải tính gì.

Và đó cũng là điều đúng với đề tài: cảnh không mô tả *"hình trông thế nào"* mà
mô tả *"hình được tạo ra thế nào"*.

─── LUẬT SỐ HAI: KHÔNG FLOAT ────────────────────────────────────────────────

Toạ độ xuất dạng **chuỗi phân số** (`"1/2"`), không phải `0.5`. Kernel dựng bằng
`Fraction` để mọi vị ngữ so **bằng đúng**, không epsilon — đó là thứ làm hệ này
khác một bộ vẽ hình. Hoá float ở biên JSON là vứt bỏ đúng thứ ấy, ở đúng chỗ
không ai nhìn thấy.

Renderer hoá float ở **bước cuối cùng trước khi đặt vào buffer**, không sớm hơn.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Any

from ..geometry import Line3, Plane3, Segment3, Vec3
from ..geometry.curved import Circle3, CurvedSolid, Ellipse3
from ..geometry.radical import Radical, display, to_json
from ..geometry.section import Polyhedron, Section
from .construction_binding import AUXILIARY, MATCHED, doi_chieu_phep_dung
from .contract import SemanticProgramSpec
from .display_names import ky_hieu_dai_luong, ten_hien_thi
from .formation import gan_vai_tro_dung
from .geometry_exec import (
    la_dai_luong_do,
    la_doi_tuong_hinh_hoc,
    phan_loai_quan_he_do,
)
from .hoisting import TIEN_TO_TAM
from .quantity_annotations import chieu_cao_the_tich, doan_tren_canh, gan_so_do
from .shape_constraint import doc_quan_he_cat
from .source_entities import ky_hieu_toan, ten_mat_phang_nguon
from .transport import TransportTypeError, is_json_native

#: Câu lệnh dựng → tên các trường mang TÊN đối tượng nó ĐỌC.
#:
#: Viết tay, cùng lý do `validator._BIEU_THUC_HINH_HOC` viết tay: đây là chỗ duy
#: nhất nói *"trường nào chở provenance"*, và dẫn xuất tự động sẽ nuốt luôn
#: `faces` (một bảng chỉ số, không phải tên).
_NGUON_CUA_PHEP_DUNG: dict[str, tuple[str, ...]] = {
    "construct_line": ("through_a", "through_b"),
    "construct_segment": ("endpoint_a", "endpoint_b"),
    "construct_plane": ("through",),
    # RỖNG CÓ CHỦ ĐÍCH — không phải chỗ quên. Hệ số là HẰNG của câu lệnh, nên
    # mặt phẳng này không phụ thuộc vật nào; xuất xứ của nó là **dữ kiện
    # phương trình trong đề**, và thứ kiểm điều đó là `SourceInvariant
    # kind="plane_equation"`, không phải đồ thị phụ thuộc. Có mặt ở bảng để
    # câu khẳng định ấy đọc được, thay vì phải suy từ một dòng vắng.
    "construct_plane_from_equation": (),
    "construct_solid": ("vertices",),
    "construct_polygon": ("vertices",),
    "construct_section": ("solid", "plane"),
    # `radius` là TÊN một đại lượng — nó là nguồn thật của khối, nên phải
    # có mặt ở đây, nếu không `depends` của quả cầu mất mắt xích bán kính.
    #
    # `height` vào cùng lý do, và nó bị bỏ sót từ 2026-09-04 tới 2026-09-07
    # (`CURVED_SCALAR_AXIS_SCALE_REPAIR`). Hậu quả đo được: một hình trụ khai
    # `height = h` với `h = measure(distance, O, O′)` mất mắt xích chiều cao,
    # nên bao đóng phụ thuộc của elip **không** về được `O`/`O′` — tức cây
    # thành phần nói dối học sinh về việc hình ấy dựng từ đâu.
    "construct_curved_solid": ("anchor", "apex_or_top", "rim_point", "radius",
                               "height"),
}


def _so(v: Any) -> str:
    """`Fraction` → chuỗi phân số. `"1/2"`, không phải `0.5`.

    `str(Fraction(2, 1))` cho `"2"`, `str(Fraction(1, 2))` cho `"1/2"` — cả hai
    đều đọc ngược lại được bằng `Fraction(s)`, nên chuỗi này là biểu diễn **không
    mất mát**, không phải một cách hiển thị.

    ⚠️ CHỈ dùng cho TOẠ ĐỘ, nơi giá trị luôn hữu tỉ (`Vec3` sống trong ℚ³). Đại
    lượng đo được có thể là căn thức và đi đường khác — `_dai_luong()`.
    """
    return str(v) if isinstance(v, Fraction) else str(Fraction(v))


def _dai_luong(v: Any) -> dict[str, Any]:
    """Đại lượng đo được → CẤU TRÚC máy đọc được, kèm chuỗi hiển thị.

    ─── VÌ SAO KHÔNG CHỈ MỘT CHUỖI ─────────────────────────────────────────

    `"3√2/5"` đọc được bằng mắt và **không** đọc được bằng máy: bộ chấm cần so
    bằng chính xác, frontend cần định dạng theo ngữ cảnh. Đọc ngược một chuỗi
    có ký tự toán học là mời sai sót vào đúng chỗ không được phép sai.

    Nên phát cả hai, và nói rõ cái nào là nguồn: `exact` là NGUỒN, `display` là
    DẪN XUẤT. Frontend cũ (envelope lưu trước wave này) chỉ đọc `value`, nên
    trường ấy giữ nguyên tên và vẫn là chuỗi — thêm trường, không đổi trường.
    """
    return {
        "value": display(v),
        "exact": to_json(v),
    }


def _xyz(p: Vec3) -> list[str]:
    return [_so(p.x), _so(p.y), _so(p.z)]


# ══ 1. ĐỒ THỊ PHỤ THUỘC — API mỏng, KHÔNG dùng để thẩm định ══════════════
def dependency_graph(spec: SemanticProgramSpec) -> dict[str, list[str]]:
    """Mỗi đối tượng phụ thuộc vào những đối tượng nào.

    ─── VÌ SAO CÓ HÀM NÀY ──────────────────────────────────────────────────

    `coverage_gate._phu_thuoc` **đã tính đồ thị này rồi VỨT ĐI** sau khi C₁a
    dùng xong. Không cần tính mới — cần thôi vứt.

    Nhưng `_phu_thuoc`/`_producers` là **chi tiết cài đặt private** của một cổng
    thẩm định. Gọi thẳng chúng từ tầng mô phỏng là buộc hai thứ không liên quan
    vào nhau: một bản vá C₁a sau này sẽ lặng lẽ đổi hình dạng cảnh 3D. Hàm mỏng
    này là chỗ ranh giới ấy được ghi ra.

    ⚠️ **KHÔNG dùng cho thẩm định.** C₁a có bản riêng và bản đó mới là cổng. Đồ
    thị ở đây phục vụ *tô sáng*, *mô phỏng thay đổi*, *tương tác* — nếu ai đó
    dùng nó để gác cửa thì tầng trình bày trở thành tầng thẩm định, và một thay
    đổi thẩm mỹ sẽ đổi được phán quyết.

    ─── TẬP LỌC LÀ `bang_ky_hieu`, KHÔNG PHẢI `memory_declarations` ────────

    Phép lọc tồn tại để chặn **tên ma**: một cạnh trỏ tới cái tên không có
    trong chương trình làm renderer tô sáng một vật không tồn tại. Bất biến ấy
    giữ nguyên. Cái sai là **tập** dùng để kiểm nó.

    `memory_declarations` trả lời *"chương trình KHAI những gì"*, còn câu cần
    hỏi là *"chương trình CÓ những vật nào"* — và `construct_*` ghi thẳng
    `memory[target_var]`, không đòi khai báo. Đúng cái lỗ mà
    `OBLIGATION_BINDING_CONTRACT` (2026-09-04) đã bịt cho cổng phủ bằng
    `bang_ky_hieu`; hàm này là **consumer thứ ba** của cùng câu hỏi, và nó bị
    bỏ sót ở wave đó.

    Đo được trên ca `circumsphere` (`probe-contract-waves-2`): 8 vật dựng ra mà
    mô hình không khai đều bị lọc mất, nên **mọi cạnh trỏ tới một vật DẪN XUẤT
    đều biến mất** — `D` mất `A_prime`, `M` mất `D`, `circumsphere` mất `M`,
    `R` mất `circumsphere`. Hậu quả ở bề mặt học sinh: bấm vào đáp số `R` thì
    `dependencyClosure` trả về **rỗng** — không sáng một vật nào, trong khi
    chuỗi dựng thật có 10 vật.

    Hụt cạnh còn nhiễm sang bộ đo: `scripts/analyze_construction_dependency.py`
    đọc chính đồ thị này, nên `do_sau_max` bị đo hụt (xem
    `docs/GEOMETRIC_DEPENDENCY_VISIBILITY_BRIDGE.md`).
    """
    from .coverage_gate import _phu_thuoc
    from .ir_static_check import bang_ky_hieu

    tho = _phu_thuoc(spec.statements, frozenset())
    co_that = set(bang_ky_hieu(spec))

    # Hợp nhất với nguồn xuất xứ từ _provenance (bao gồm quan hệ nhân quả đo lường và gán biến)
    prov = _provenance(spec)
    for ten, info in prov.items():
        if ten in co_that:
            srcs = set(tho.get(ten, set()))
            for s in info.get("sources", []):
                if s in co_that:
                    srcs.add(s)
            tho[ten] = srcs

    return {
        ten: sorted(n for n in nguon if n in co_that)
        for ten, nguon in sorted(tho.items())
    }


def _provenance(spec: SemanticProgramSpec) -> dict[str, dict[str, Any]]:
    """`target_var` → phép dựng sinh ra nó, kèm TÊN các đối tượng nguồn.

    Đi trên `statements`, không trên bộ nhớ: bộ nhớ chỉ có **giá trị cuối**, còn
    câu hỏi của đề tài là *"nó được tạo ra thế nào"*.
    """
    ra: dict[str, dict[str, Any]] = {}

    from .validator import _BIEU_THUC_HINH_HOC

    def di(stmts) -> None:
        for st in stmts or ():
            kind = getattr(st, "kind", None)
            tv = getattr(st, "target_var", None)
            if kind == "construct_point" and tv:
                # `construct_point` KHÔNG có trường tên ở câu lệnh — nguồn nằm
                # trong BIỂU THỨC (`midpoint.a/b`, `project_onto.point/target`…).
                # Bỏ sót nhánh này thì mọi điểm dựng ra đều `producer: null`, tức
                # cảnh mất đúng thứ đề tài muốn kể: *nó được tạo ra thế nào*.
                #
                # Bảng tên trường nhập từ `validator` — MỘT nguồn sự thật, và
                # bảng ấy cố ý không gồm `ratio` (một phân số, không phải tên).
                e = getattr(st, "expr", None)
                truong = _BIEU_THUC_HINH_HOC.get(getattr(e, "kind", None), ())
                nguon = [x for x in (getattr(e, f, None) for f in truong)
                         if isinstance(x, str)]
                ra[tv] = {"producer": f"construct_point.{getattr(e, 'kind', '?')}",
                          "sources": nguon, "label": getattr(st, "label", None)}
            elif kind in _NGUON_CUA_PHEP_DUNG and tv:
                if kind == "construct_segment" and getattr(st, "items", None):
                    for it in st.items:
                        ra[it["name"]] = {
                            "producer": "construct_segment",
                            "sources": [it["endpoint_a"], it["endpoint_b"]],
                            "label": it.get("label"),
                        }
                    ra[tv] = {
                        "producer": "construct_segment",
                        "sources": [it["name"] for it in st.items],
                        "label": getattr(st, "label", None),
                    }
                else:
                    nguon: list[str] = []
                    for f in _NGUON_CUA_PHEP_DUNG[kind]:
                        v = getattr(st, f, None)
                        if isinstance(v, str):
                            nguon.append(v)
                        elif isinstance(v, list):
                            nguon += [x for x in v if isinstance(x, str)]
                    # Khối cong mang LOẠI vào khoá xuất xứ — `construct_curved_
                    # solid.ball` — đúng khuôn `construct_point.<kind biểu thức>`.
                    # Nhờ vậy tầng đặt tên gọi được *"Khối cầu"* / *"Hình nón"* mà
                    # không phải mở lại câu lệnh, và không dựng bảng loại thứ hai.
                    if kind == "construct_curved_solid":
                        kind = f"{kind}.{getattr(st, 'curved_kind', '?')}"
                    ra[tv] = {"producer": kind, "sources": nguon,
                              "label": getattr(st, "label", None)}
            elif kind == "assign" and tv:
                e = getattr(st, "expr", None)
                ek = getattr(e, "kind", None)
                if ek == "measure":
                    nguon = [x for x in (getattr(e, "of", None),
                                         getattr(e, "wrt", None))
                             if isinstance(x, str)]
                    # Bổ sung quan hệ nhân quả sư phạm cho diện tích và thể tích
                    q = getattr(e, "quantity", "")
                    of_name = getattr(e, "of", "")
                    mem_map = {d.name: d for d in (spec.memory_declarations or ())}
                    if q == "area":
                        polygon_vertices = _construction_vertices(
                            spec, of_name, "construct_polygon"
                        )
                        for d_name, d in mem_map.items():
                            if (
                                d_name.endswith("_length")
                                and _length_joins_vertices(d_name, polygon_vertices)
                                and d_name not in nguon
                            ):
                                nguon.append(d_name)
                    elif q == "volume":
                        base_vertices: list[str] = []
                        for other_tv, other_info in ra.items():
                            if other_info.get("producer") == "measure.area":
                                if other_tv not in nguon:
                                    nguon.append(other_tv)
                                polygon = next(
                                    (src for src in other_info.get("sources", [])
                                     if _construction_vertices(
                                         spec, src, "construct_polygon"
                                     )),
                                    None,
                                )
                                if polygon:
                                    base_vertices = _construction_vertices(
                                        spec, polygon, "construct_polygon"
                                    )
                        solid_vertices = _construction_vertices(
                            spec, of_name, "construct_solid"
                        )
                        for d_name, d in mem_map.items():
                            if not d_name.endswith("_length"):
                                continue
                            is_base_edge = _length_joins_vertices(
                                d_name, base_vertices
                            )
                            is_solid_edge = _length_joins_vertices(
                                d_name, solid_vertices
                            )
                            if is_solid_edge and not is_base_edge and d_name not in nguon:
                                nguon.append(d_name)
                        # Chiều cao ĐO được (regular-square-pyramid-w01): khoảng cách từ một đỉnh của khối
                        # NGOÀI đáy tới mặt phẳng dựng qua các đỉnh của đáy — đúng định nghĩa chiều cao, không
                        # đoán theo tên. Chân đường cao không phải đỉnh của khối (vd tâm O của chóp đều), nên
                        # luật cạnh `*_length` ở trên không bao giờ thấy nó.
                        mat_day = {
                            getattr(s, "target_var", None)
                            for s in spec.statements or ()
                            if getattr(s, "kind", None) == "construct_plane"
                            and base_vertices
                            and set(getattr(s, "through", None) or ()) <= set(base_vertices)
                        }
                        dinh_ngoai = set(solid_vertices) - set(base_vertices)
                        for other_tv, other_info in ra.items():
                            src = other_info.get("sources", [])
                            if (other_info.get("producer") == "measure.distance" and len(src) == 2
                                    and src[0] in dinh_ngoai and src[1] in mat_day and other_tv not in nguon):
                                nguon.append(other_tv)
                    ra[tv] = {"producer": f"measure.{e.quantity}",
                              "sources": nguon, "label": None}
                elif ek == "var":
                    var_name = getattr(e, "name", None)
                    nguon = [var_name] if isinstance(var_name, str) else []
                    ra[tv] = {"producer": "assign", "sources": nguon,
                              "label": getattr(st, "label", None)}
                elif ek in ("arith", "unary"):
                    def _thu_bien(bieu_thuc: Any) -> list[str]:
                        loai_bt = getattr(bieu_thuc, "kind", None)
                        if loai_bt == "var":
                            ten_b = getattr(bieu_thuc, "name", None)
                            return [ten_b] if isinstance(ten_b, str) else []
                        if loai_bt in ("arith", "unary"):
                            ket_qua: list[str] = []
                            for truong_con in ("left", "right", "expr"):
                                con = getattr(bieu_thuc, truong_con, None)
                                if con is not None:
                                    for b in _thu_bien(con):
                                        if b not in ket_qua:
                                            ket_qua.append(b)
                            return ket_qua
                        return []
                    bien_con = _thu_bien(e)
                    prod_gan = "assign"
                    if ek == "arith" and len(bien_con) >= 2 and all(ra.get(b, {}).get("producer") == "measure.volume" for b in bien_con):
                        if getattr(e, "op", None) == "-":
                            prod_gan = "assign.residual_volume"
                        elif getattr(e, "op", None) == "+":
                            prod_gan = "assign.volume_ratio"
                    ra[tv] = {"producer": prod_gan, "sources": bien_con,
                              "label": getattr(st, "label", None)}
                elif ek in _BIEU_THUC_HINH_HOC:
                    # ─── VECTƠ VÀ ĐƯỜNG CŨNG LÀ VẬT DỰNG RA ──────────────
                    #
                    # `assign` sinh ra ĐIỂM đã được chuẩn hoá thành
                    # `construct_point` ở tầng hợp đồng, nên nhánh trên lo. Còn
                    # `vector_from_points` (→ vector3) và `intersect_plane_
                    # plane` (→ line3) thì KHÔNG viết lại được: IR không có
                    # `construct_vector`, và `construct_line` nhận hai TÊN
                    # ĐIỂM chứ không nhận biểu thức. `assign` là lối duy nhất
                    # cho chúng.
                    #
                    # Thiếu nhánh này thì chúng mang `producer: null`, và cảnh
                    # 3D thôi kể *nó được tạo ra thế nào* — mất đúng đóng góp
                    # của đề tài, ở đúng những vật mà một bài vectơ xoay quanh.
                    # Đo được ở bảng sự thật `audit_assign_binding.py`.
                    truong = _BIEU_THUC_HINH_HOC.get(ek, ())
                    nguon = [x for x in (getattr(e, f, None) for f in truong)
                             if isinstance(x, str)]
                    ra[tv] = {"producer": ek, "sources": nguon,
                              "label": getattr(st, "label", None)}
            for attr in ("body", "then_body", "else_body"):
                sub = getattr(st, attr, None)
                if sub:
                    di(sub)

    di(spec.statements)
    return ra


def _construction_vertices(
    spec: SemanticProgramSpec, target: str, kind: str
) -> list[str]:
    """Đọc danh sách đỉnh đã khai của một phép dựng, không suy từ toạ độ."""
    for statement in spec.statements or ():
        if (
            getattr(statement, "kind", None) == kind
            and getattr(statement, "target_var", None) == target
        ):
            return [v for v in (getattr(statement, "vertices", None) or [])
                    if isinstance(v, str)]
    return []


def _length_joins_vertices(name: str, vertices: list[str]) -> bool:
    """Đại lượng độ dài có gọi đúng một cạnh giữa hai đỉnh đã khai không.

    Dùng ký hiệu toán do ``source_entities`` sở hữu, không bóc tên family hay
    giả định đỉnh chỉ dài một ký tự. Vì vậy ``AA_prime_length`` khớp cạnh
    ``A``–``A_prime`` theo ``AA′`` giống như ``AD_length`` khớp ``A``–``D``.
    """
    symbol = ky_hieu_dai_luong(name)
    if not symbol:
        return False
    labels = [(v, ky_hieu_toan(v)) for v in vertices]
    labels = [(v, label.replace("'", "′")) for v, label in labels if label]
    return any(
        symbol in (a + b, b + a)
        for i, (_, a) in enumerate(labels)
        for _, b in labels[i + 1:]
    )


_NON_VISUAL_CARRIERS = frozenset({"vector3", "quantity"})


def _unwrap_visible_sources(
    sources: list[str],
    object_types: dict[str, str],
    dependencies: dict[str, list[str]],
    *,
    exclude_id: str | None = None,
) -> list[str]:
    """Khai triển các nguồn trung gian không hiển thị (`vector3`, `quantity`) về vật hiển thị."""
    seen_expand: set[str] = set()
    out: list[str] = []

    def _visit(sid: str) -> None:
        if sid == exclude_id:
            return
        stype = object_types.get(sid)
        if stype in _NON_VISUAL_CARRIERS:
            if sid in seen_expand:
                return
            seen_expand.add(sid)
            sub_deps = dependencies.get(sid) or []
            for sub in sub_deps:
                _visit(sub)
            # Run `scene3d-causal-pedagogical-integrity`: a carrier with no dependency is SOURCE DATA (the radius R the
            # problem gives, a given vector) — a number, never a drawn prerequisite. It stays in `computational_depends`.
            return
        if sid not in out:
            out.append(sid)

    for src in sources:
        _visit(src)
    return out


def typed_dependency_graph(
    spec: SemanticProgramSpec,
    scene: dict[str, Any],
    dependencies: dict[str, list[str]],
) -> dict[str, list[dict[str, Any]]]:
    """Gắn loại provenance cho từng cạnh phụ thuộc của Scene3D.

    Đây là metadata trình bày additive. Đồ thị ``dependencies`` cũ vẫn giữ
    nguyên để payload cũ và interaction hiện hữu tiếp tục hoạt động.
    """
    provenance = _provenance(spec)
    object_types = {o["id"]: o["type"] for o in scene.get("objects", [])}
    relation_by_type = {
        "solid": "structural",
        "polygon3": "structural",
        "section": "structural",
        "curved_solid": "structural",
        "circle3": "structural",
        "ellipse3": "structural",
        "point3": "topological",
        "segment3": "topological",
        "line3": "topological",
        "plane3": "topological",
        "vector3": "topological",
        "quantity": "numerical",
    }
    result: dict[str, list[dict[str, Any]]] = {}
    for target, sources in dependencies.items():
        producer = str(provenance.get(target, {}).get("producer") or "")
        edges: list[dict[str, Any]] = []
        for source in sources:
            source_type = object_types.get(source)
            relation = relation_by_type.get(source_type or "", "layout")
            if producer.startswith("measure.") and source_type == "quantity":
                relation = "numerical"
            elif producer == "measure.volume" and source_type == "solid":
                relation = "structural"
            edge: dict[str, Any] = {"source_id": source, "relation": relation}
            if source_type in _NON_VISUAL_CARRIERS:
                edge["is_non_visual_carrier"] = True
                if source_type == "vector3":
                    edge["resolved_visible_sources"] = _unwrap_visible_sources(
                        dependencies.get(source) or [source],
                        object_types,
                        dependencies,
                        exclude_id=source,
                    )
            edges.append(edge)
        result[target] = edges
    return result


# ══ 2. GEOMETRY SCENE — chiếu bộ nhớ ═════════════════════════════════════
#: Lớp runtime → (kiểu ngữ nghĩa MẶC ĐỊNH, các kiểu KHAI mà lớp ấy chở được).
#:
#: ─── VÌ SAO KHÔNG CÒN LÀ MỘT CHUỖI `isinstance` THUẦN ─────────────────────
#:
#: `vector3` và `point3` **cùng là `Vec3`** ở runtime, nên phân loại bằng lớp
#: runtime làm mọi vectơ đi qua cảnh dưới lốt một điểm — rồi frontend phải đọc
#: `producer == "vector_from_points"` để đoán ngược, tức tầng trình bày suy lại
#: một mệnh đề ngữ nghĩa (`GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT §19`).
#:
#: Nay **kiểu KHAI là thẩm quyền**; lớp runtime chỉ quyết *đọc trường nào ra*.
#: Vế thứ hai của mỗi mục là tập kiểu khai lớp ấy chở được — khai ngoài tập thì
#: khai và giá trị mâu thuẫn nhau, và ở đó mặc định thắng: cảnh phải mô tả thứ
#: bộ nhớ THẬT SỰ đang giữ, không mô tả thứ chương trình nói là nó giữ.
_KHAI_TUONG_THICH: dict[str, tuple[str, ...]] = {
    "point3": ("point3", "vector3"),
    "line3": ("line3",),
    "segment3": ("segment3",),
    "plane3": ("plane3",),
    "solid": ("solid",),
    "section": ("section",),
    "polygon3": ("polygon3",),
    "circle3": ("circle3",),
    "curved_solid": ("curved_solid",),
}


def _loai_ngu_nghia(mac_dinh: str, kieu_khai: str | None) -> str:
    """Kiểu KHAI thắng khi nó tương thích với thứ bộ nhớ đang giữ."""
    hop = _KHAI_TUONG_THICH.get(mac_dinh, ())
    return kieu_khai if kieu_khai in hop else mac_dinh


def _than_hinh_hoc(gt: Any) -> tuple[str, dict[str, Any]] | None:
    """Giá trị hình học → (kiểu mặc định theo lớp runtime, các trường của cảnh).

    `None` ⇒ không phải đối tượng hình học. **Chỉ trích xuất, không phân loại
    ngữ nghĩa** — việc phân loại nay thuộc `_loai_ngu_nghia`.

    `vertex_ids` để `None`: nó là danh sách TÊN theo VỊ TRÍ, chỉ nơi gọi mới
    biết (`sources` của vật). Bỏ trống ở đây rồi điền ở đó, thay vì chở thêm
    một tham số qua một hàm thuần tuý đọc giá trị.
    """
    if isinstance(gt, Vec3):
        return "point3", {"xyz": _xyz(gt)}
    if isinstance(gt, Line3):
        # KHÔNG có `segment`: `Line3` vô hạn, và cắt nó thành một đoạn là quyết
        # định TRÌNH BÀY. `sources` đã chở tên hai điểm sinh ra nó, nên renderer
        # dựng đoạn được mà lớp này không tính gì.
        return "line3", {"point": _xyz(gt.point),
                         "direction": _xyz(gt.direction)}
    if isinstance(gt, Segment3):
        return "segment3", {
            "point_a": _xyz(gt.a),
            "point_b": _xyz(gt.b),
            "endpoints": [_xyz(gt.a), _xyz(gt.b)],
            "endpoint_ids": None,
        }
    if isinstance(gt, Plane3):
        # Cùng lý do: không có `boundary`. `sources` chở ba điểm định nghĩa.
        return "plane3", {"point": _xyz(gt.point), "normal": _xyz(gt.normal)}
    if isinstance(gt, Polyhedron):
        # `vertex_ids` THEO VỊ TRÍ, không sắp xếp — `faces` là bảng CHỈ SỐ vào
        # `vertices`, nên không có dãy tên cùng thứ tự thì mặt thứ `i` không nói
        # được nó gồm những ĐIỂM NÀO. `depends` không thay được: `dependency_
        # graph` sắp thứ tự chữ và làm mất đúng tính chất ấy.
        return "solid", {"vertices": [_xyz(v) for v in gt.vertices],
                         "vertex_ids": None,
                         "faces": [list(f) for f in gt.faces]}
    if isinstance(gt, Section):
        return "section", {"polygon": [_xyz(v) for v in gt.polygon],
                           "closed": gt.is_closed,
                           "steps": [{"face_index": s.face_index,
                                      "a": _xyz(s.a), "b": _xyz(s.b)}
                                     for s in gt.steps],
                           "vertex_sources": [
                               {
                                   "kind": source.kind,
                                   "solid_vertex_index": source.solid_vertex_index,
                                   "solid_edge_vertex_indices": list(
                                       source.solid_edge_vertex_indices
                                   ) if source.solid_edge_vertex_indices else None,
                               }
                               for source in gt.vertex_sources
                           ]}
    if isinstance(gt, Circle3):
        # `radius_sq`, KHÔNG phải `radius`: bán kính có thể vô tỉ, bình phương
        # thì không. Chở số chính xác qua dây rồi để renderer lấy căn ở biên
        # hiển thị — cùng quy ước mà `distance_sq` đã dùng từ đầu.
        return "circle3", {"center": _xyz(gt.center),
                           "normal": _xyz(gt.normal),
                           "radius_sq": _so(gt.radius_sq)}
    if isinstance(gt, Ellipse3):
        # Cùng quy ước `radius_sq` của đường tròn, nhân đôi: HAI bán trục, mỗi
        # cái chở BÌNH PHƯƠNG. Kèm hai PHƯƠNG trục — thiếu chúng thì renderer
        # không biết elip xoay thế nào trong mặt phẳng của nó, và sẽ phải đoán
        # từ `normal`, tức tự quyết một dữ kiện hình học.
        #
        # Hai phương ở ℚ³ và **chưa chuẩn hoá độ dài**: chuẩn hoá đá chúng ra
        # khỏi ℚ³. Renderer chuẩn hoá ở biên hiển thị, cùng chỗ nó lấy căn.
        return "ellipse3", {"center": _xyz(gt.center),
                            "normal": _xyz(gt.normal),
                            "major_dir": _xyz(gt.major_dir),
                            "minor_dir": _xyz(gt.minor_dir),
                            "semi_major_sq": _so(gt.semi_major_sq),
                            "semi_minor_sq": _so(gt.semi_minor_sq)}
    if isinstance(gt, CurvedSolid):
        # ⚠️ **BA ĐIỂM NEO, KHÔNG ĐỈNH LƯỚI.** Payload cố ý không có `vertices`
        # lẫn `faces`, và đó là toàn bộ cơ chế giữ lưới ra khỏi ngữ nghĩa:
        # renderer chia lưới để VẼ, nhưng không có chỗ nào để một đỉnh nội suy
        # đi ngược lên checker hay phép đo. So sánh với `solid` — đỉnh đa diện
        # **là** ngữ nghĩa nên nó chở đỉnh; khối cong thì không.
        return "curved_solid", {
            "curved_kind": gt.kind,
            "anchor": _xyz(gt.anchor),
            "apex_or_top": _xyz(gt.apex_or_top) if gt.apex_or_top else None,
            "rim_point": _xyz(gt.rim_point) if gt.rim_point else None,
            # `radius_sq` và `height_sq` — BÌNH PHƯƠNG, hữu tỉ, chính xác.
            # Gửi chúng đi để renderer khỏi phải tự đo khoảng cách giữa hai
            # điểm: một phép `distanceTo` ở tầng vẽ là tầng vẽ đang làm hình
            # học, đúng thứ ranh giới R0 cấm (`scene3d.test.tsx` khoá).
            "radius_sq": _so(gt.radius_sq),
            "height_sq": _so(gt.height_sq),
        }
    if la_doi_tuong_hinh_hoc(gt) and isinstance(gt, tuple):
        # `polygon3` sống dưới dạng tuple các đỉnh — không có lớp riêng.
        return "polygon3", {"vertices": [_xyz(v) for v in gt],
                            "vertex_ids": None}
    return None


def build_scene(
    spec: SemanticProgramSpec, memory: dict[str, Any], *, prefer_declared_plane_names: bool = False,
    source_text: str | None = None,
) -> dict[str, Any]:
    """Bộ nhớ + chương trình → cảnh hình học JSON.

    Chỉ nhặt đối tượng HÌNH HỌC. Biến `int`/`array`/`map` của miền Tin học không
    thuộc cảnh 3D, và nhét chúng vào là mời renderer đoán xem phải vẽ gì.

    Đối tượng khai mà chưa dựng (`initial_value: null`, câu lệnh chưa chạy tới)
    có mặt trong `memory` với giá trị `None` — bỏ qua, không dựng một ô rỗng.
    """
    from .coverage_gate import _producers

    tao_ra = _producers(spec.statements)
    prov = _provenance(spec)
    kieu = {d.name: d.type for d in spec.memory_declarations}
    mem_map = {d.name: d for d in (spec.memory_declarations or ())}

    # ── LƯỢT 1: kiểu ngữ nghĩa + phần thân hình học ──────────────────────
    #
    # Tách khỏi lượt ráp vì TÊN HIỂN THỊ của một vật cần ký hiệu của các toán
    # hạng, nên phải biết trọn bảng trước khi đặt tên cho bất cứ vật nào.
    tho: list[tuple[str, str, dict[str, Any]]] = []
    for ten, gt in memory.items():
        than = _than_hinh_hoc(gt)
        if than is None:
            if not la_dai_luong_do(gt, kieu.get(ten)):
                continue
            lbl = getattr(mem_map.get(ten), "label", None)
            if lbl:
                if ten not in prov:
                    prov[ten] = {"producer": None, "sources": [], "label": lbl}
                elif not prov[ten].get("label"):
                    prov[ten]["label"] = lbl
            # ĐẠI LƯỢNG đo được (`measure`) — không vẽ được, nhưng phải HIỆN
            # LÊN: nó là câu trả lời của bài. Bỏ nó khỏi cảnh thì mô phỏng chạy
            # xong mà học sinh không thấy đáp số.
            tho.append((ten, "quantity", _dai_luong(gt)))
            continue
        mac_dinh, noi_dung = than
        kieu_khai = kieu.get(ten) or (
            "vector3" if prov.get(ten, {}).get("producer") == "vector_from_points" else None
        )
        tho.append((ten, _loai_ngu_nghia(mac_dinh, kieu_khai), noi_dung))

    # ── LƯỢT 2: TÊN HIỂN THỊ, do tầng ngữ nghĩa quyết ────────────────────
    #
    # Khối mang bảng mặt + toạ độ để tầng tên gọi được LOẠI khối (chóp, lăng
    # trụ, hộp, lập phương) từ topology; thiết diện mang tên các điểm trùng
    # đỉnh của nó để được gọi bằng chu trình. Không suy gì từ tên bài.
    diem_co_ten = {
        ten: memory[ten]
        for ten, loai, _ in tho
        if loai == "point3" and isinstance(memory.get(ten), Vec3)
    }

    def _hinh(ten: str, loai: str) -> dict[str, Any]:
        gt = memory.get(ten)
        if loai == "solid" and isinstance(gt, Polyhedron):
            return {"solid": {"vertices": list(gt.vertices),
                              "faces": [list(f) for f in gt.faces]}}
        if loai == "section" and isinstance(gt, Section):
            ten_dinh = [next((n for n, v in diem_co_ten.items() if v == p), None)
                        for p in gt.polygon]
            if all(ten_dinh) and len(set(ten_dinh)) == len(ten_dinh):
                ten_dinh_clean = [n for n in ten_dinh if n is not None]
                # Align cycle start/orientation if section label explicitly specifies one
                lbl_hint = str(prov.get(ten, {}).get("label") or ten)
                syms = [ky_hieu_dai_luong(n) or n.replace("'", "′") for n in ten_dinh_clean]
                ten_dinh_clean, _ = _can_chinh_chu_trinh_dinh(
                    ten_dinh_clean, syms, lbl_hint, _ten_mat_cat(ten, prov, memory))
                return {"section_vertex_names": ten_dinh_clean}
        if loai == "plane3" and isinstance(gt, Plane3):
            # Điểm có tên nằm TRÊN mặt phẳng (chính xác) — để tên khai `(ABCD)` được kiểm, không rút thầm thành `(ABC)`.
            return {"points_on_plane": [n for n, v in diem_co_ten.items() if gt.signed_eval(v) == 0]}
        return {}

    hien_thi = ten_hien_thi({
        ten: {"type": loai, "producer": prov.get(ten, {}).get("producer"),
              "sources": prov.get(ten, {}).get("sources", []),
              "label": prov.get(ten, {}).get("label"), **_hinh(ten, loai)}
        for ten, loai, _ in tho
    }, prefer_declared_plane_names=prefer_declared_plane_names,
        source_plane_names=ten_mat_phang_nguon(source_text))

    objects: list[dict[str, Any]] = []
    for ten, loai, noi_dung in tho:
        p = prov.get(ten, {})
        ht = hien_thi[ten]
        chung = {
            "id": ten,
            # ⚠️ KHÔNG còn `or ten`. Rơi về `id` là cách `khoang_cach_hs` lên
            # tới màn hình học sinh (`GEOMETRY_ARCHITECTURE_EXPRESSIVENESS_AUDIT
            # §5`). `display_names.ten_hien_thi` luôn trả một câu đọc được, kể
            # cả khi mô hình không đặt tên và phép dựng không có công thức gọi.
            "label": ht["label"],
            # KÝ HIỆU NGẮN in cạnh vật trên khung 3D. `None` là câu trả lời hợp
            # lệ — khung không in gì cho vật ấy, và đó tốt hơn một ký hiệu bịa.
            "notation": ht["notation"],
            # CÁCH GỌI NGẮN khi vật này bị nhắc trong câu của vật khác, và
            # VAI TRÒ (*"nó là gì"*). Cả hai do tầng ngữ nghĩa quyết — trước
            # 2026-09-03 vai trò được dựng ở **frontend** bằng một bảng
            # `producer → tiếng Việt` thứ hai, tức một thẩm quyền đặt tên thứ
            # hai nằm sai tầng.
            "reference": ht["reference"],
            "role": ht["role"],
            # FREE vs DERIVED — DẪN XUẤT, không khai. Một cờ khai được là một cờ
            # khai sai được, và ở đây khai sai nghĩa là một điểm dẫn xuất tự
            # nhận mình tự do rồi được phép kéo.
            "origin": "derived" if ten in tao_ra else "free",
            # VẬT DO SERVER DỰNG — ràng buộc trung gian mà `hoisting` sinh ra
            # khi mô hình lồng một phép dựng vào một ô TÊN.
            #
            # Cờ nằm ở ĐÂY chứ không ở `scene3d`, và đó là ranh giới kiến trúc
            # chứ không phải sở thích: `scene3d` nhận `dict`, trả `dict`, và
            # `test_scene3d_KHONG_nhap_gi_tu_tang_hinh_hoc` khoá cho nó không
            # nhập gì cả. Tầng này vốn đã biết tên và xuất xứ, nên nó là nơi
            # duy nhất trả lời được câu *"tên này do ai đặt"* mà không phá gì.
            "synthetic": ten.startswith(TIEN_TO_TAM),
            "producer": p.get("producer"),
            "sources": p.get("sources", []),
            # Tên trình bày `(α)` do `display_names` gán (không phải tên của đề): lời kể nói "Gọi (α) là …".
            **({"notation_assigned": True} if ht.get("notation_assigned") else {}),
        }
        # `vertex_ids` THEO VỊ TRÍ chỉ biết được ở đây (cần `sources` của vật),
        # nên `_than_hinh_hoc` để lại ô trống và lượt này điền.
        if "vertex_ids" in noi_dung and noi_dung["vertex_ids"] is None:
            noi_dung = {**noi_dung, "vertex_ids": list(p.get("sources", []))}
        if "endpoint_ids" in noi_dung and noi_dung["endpoint_ids"] is None:
            noi_dung = {**noi_dung, "endpoint_ids": list(p.get("sources", []))}
        objects.append({**chung, "type": loai, **noi_dung})

    return {"objects": objects}


# ══ 3. TIMELINE — tận dụng trace, không dựng mới ═════════════════════════
def build_timeline(
    spec: SemanticProgramSpec, exec_result: Any
) -> list[dict[str, Any]]:
    """`SemanticTraceStep[]` → dãy bước mô phỏng.

    KHÔNG tạo timeline mới. `trace` đã mang `step_index`, `action`, `target`,
    `details`, `tier1_narration` — đủ cả năm thứ một bước cần.

    Bất biến #31 (`frame k ⇔ trace[k]`) áp thẳng: **một mục cho đúng một bước**,
    không gộp, không cắt. `construct_section` đã sinh một bước cho MỖI CẠNH kèm
    `face_index`, nên bài "dựng thiết diện" có timeline đúng như học sinh làm
    trên giấy mà không phải thêm gì.
    """
    prov = _provenance(spec)
    return [
        {
            "step_index": s.step_index,
            "action": s.action,
            "created": s.target,
            "depends_on": prov.get(s.target, {}).get("sources", []),
            "explanation": s.tier1_narration,
            # Trường learner-facing mới đi song song với ``explanation`` để
            # payload cũ vẫn đọc được. Scene3D sẽ kiểm lại động theo toàn bộ
            # internal ids trước khi cho chuỗi này ra UI.
            "learner_text": s.tier1_narration,
            "semantic_kind": s.semantic_kind,
            "details": _json_an_toan(s.details),
        }
        for s in exec_result.trace
    ]


def _json_an_toan(x: Any) -> Any:
    """`Fraction` trong `details` → chuỗi phân số.

    ĐO ĐƯỢC khi viết test 5B: `assign` từ `measure` ghi `{"value": Fraction(2,3)}`
    vào `details`, và `json.dumps` VỠ — sau khi cả lượt đo đã chạy xong. Một
    artifact không ghi ra được là một lượt đo mất trắng.

    Chuyển sang chuỗi phân số chứ không sang float, cùng lý do với toạ độ: đó là
    biểu diễn **không mất mát**, đọc ngược lại được bằng `Fraction(s)`.
    """
    if isinstance(x, Radical):
        # CẤU TRÚC, không phải chuỗi: `details` là dữ liệu, và một `"3√2/5"`
        # trong đó không đọc ngược lại được.
        return to_json(x)
    if isinstance(x, Fraction):
        return str(x)
    if isinstance(x, dict):
        return {k: _json_an_toan(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_json_an_toan(v) for v in x]
    # Giá trị HÌNH HỌC (`Plane3`, `Circle3`, `Ellipse3`…) đi cùng khuôn với vật
    # của cảnh — `_than_hinh_hoc` là thẩm quyền, không dựng bản thứ hai. Từ
    # 50a31e0b `details` ra tới envelope qua `scene3d.events`, nên một giá trị
    # thô lọt ở đây là HTTP 500 ở `main.py`, không còn là chuyện nội bộ.
    than = _than_hinh_hoc(x)
    if than is not None:
        kieu, truong = than
        return {"kind": kieu, **truong}
    if not is_json_native(x):
        raise TransportTypeError(x)
    return x


def _nhan_du_kien_tu_fact(objects: list[dict[str, Any]], spec: SemanticProgramSpec, contract: Any) -> None:
    """Dữ kiện đề cho KHÔNG có ký hiệu (`cạnh đáy bằng 4` — không tên đoạn) mang NHÃN của InputFact mà khai
    báo GIVEN trích dẫn (regular-square-pyramid-w01). Khai báo bộ nhớ không có ô nhãn, nên trước bản này học
    sinh đọc "đại lượng = 4". Chỉ đổi TÊN hiển thị; giá trị, ký hiệu và chứng chỉ không đổi."""
    nhan_fact = {f.fact_id: (f.label or "").strip() for f in (getattr(contract, "input_facts", None) or ())}
    khai = {d.name: d for d in spec.memory_declarations or ()}
    for o in objects:
        d = khai.get(o["id"])
        nhan = nhan_fact.get(getattr(d, "source_fact_id", None) or "")
        # W2: nhãn kiểu TOKEN MÁY (gạch dưới, camelCase) không lên bề mặt học sinh — giữ tên do tầng đặt tên dựng.
        if (o.get("type") != "quantity" or o.get("notation") or getattr(d, "provenance", None) != "GIVEN"
                or not nhan or "_" in nhan or re.fullmatch(r"[a-z]+[A-Z]\w*", nhan)):
            continue
        o["label"] = o["reference"] = nhan[0].upper() + nhan[1:]


# ══ 4. SIMULATION STATE ══════════════════════════════════════════════════
def build_simulation_state(
    spec: SemanticProgramSpec, exec_result: Any, contract: Any = None, *, prefer_declared_plane_names: bool = False,
    common_perpendicular_witness: bool = False,
) -> dict[str, Any]:
    """Cảnh + đồ thị phụ thuộc + timeline. Đầu vào DUY NHẤT của renderer.

    `free_objects` là thứ Phase 5E sẽ cho kéo. Nó dẫn xuất từ `_producers`, nên
    một điểm dẫn xuất **không thể** tự nhận mình tự do — và luật *"kéo M thì bị
    từ chối vì M sinh ra từ A, B"* rơi ra từ dữ liệu, không phải từ một danh
    sách ai đó phải nhớ cập nhật.
    """
    # Đề nguyên văn (`RequestContract.problem_text`) là nguồn DUY NHẤT để một tên mặt phẳng khai được coi là của đề.
    de = getattr(contract, "problem_text", None)
    scene = build_scene(spec, exec_result.final_memory, prefer_declared_plane_names=prefer_declared_plane_names,
                        source_text=de if isinstance(de, str) else None)
    _nhan_du_kien_tu_fact(scene["objects"], spec, contract)
    # Vai trò dựng hình gắn ở PRODUCER (W14): tô-pô + quan hệ có kiểu, một thẩm
    # quyền với bước bổ sung. `scene3d` chỉ chở và hợp theo bước.
    gan_vai_tro_dung(scene["objects"], spec, contract)
    _ky_hieu_dien_tich_thiet_dien(scene["objects"], contract)
    _canh_song_song_thiet_dien(scene["objects"])
    _vet_giao_tuyen_thiet_dien(scene["objects"])
    # W17 §15.4: chủ thể của từng đại lượng — tầng ngữ nghĩa quyết (toán hạng phép đo, hoặc đoạn
    # đề gọi tên kiểm bằng khoảng cách chính xác); lớp chiếu này chỉ chở.
    so_do, chan_doan_so_do = gan_so_do(spec, exec_result.final_memory, contract, scene["objects"],
                                       duong_vuong_goc_chung=common_perpendicular_witness)
    chieu_cao = chieu_cao_the_tich(scene["objects"], exec_result.final_memory, so_do)
    dependencies = dependency_graph(spec)
    prov = _provenance(spec)
    _gan_measured_quantity(scene["objects"], exec_result.final_memory)
    _gan_lineage_va_tien_quyet(scene["objects"], dependencies)
    _gan_chu_trinh_canh_thiet_dien(scene["objects"], exec_result.final_memory, prov)
    targets = sorted(_muc_tieu(contract))
    unused_aux_ids = _tim_phu_tro_du_thua(
        scene["objects"], dependencies, exec_result.final_memory, targets
    )
    return {
        "scene": scene,
        "dependencies": dependencies,
        "dependency_edges": typed_dependency_graph(spec, scene, dependencies),
        "free_objects": sorted(
            o["id"] for o in scene["objects"] if o["origin"] == "free"
        ),
        "timeline": build_timeline(spec, exec_result),
        # ── DỮ LIỆU CHO TƯƠNG TÁC (đọc bởi `scene3d`) ────────────────────────
        #
        # Tính ở ĐÂY chứ không ở `scene3d` vì cả hai cần `spec`, mà `scene3d`
        # chỉ nhận `state` — và mở cửa cho nó nhận thêm `spec` là để tầng trình
        # bày nhìn thẳng vào chương trình, đúng hướng phụ thuộc không được đảo.
        #
        # `targets`: vật mà đề BẢO chứng minh/tính. Nhóm hiển thị `target` dẫn
        # xuất từ đây, nên học sinh phân biệt được *"cái phải chứng minh"* với
        # *"cái dựng ra để chứng minh"* — thứ nhìn hình vẽ phẳng không thấy.
        "targets": targets,
        "unused_auxiliary_ids": unused_aux_ids,
        "provenance": _xuat_xu_hien_thi(spec, contract),
        "annotations": so_do,
        "annotation_diagnostics": chan_doan_so_do,
        "volume_heights": chieu_cao,
        # regular-square-pyramid-w04: đoạn nằm TRÊN cạnh khối (kiểm chính xác ở `quantity_annotations`) — tầng cảnh
        # chỉ tra id cạnh chuẩn, để cạnh ấy là owner nét duy nhất.
        "segments_on_edges": doan_tren_canh(scene["objects"], exec_result.final_memory),
        "khai": "Trạng thái TRUNG GIAN cho renderer. Mọi số là chuỗi phân số "
                "CHÍNH XÁC; hoá float là việc của renderer, ở bước cuối cùng.",
    }


def _can_chinh_chu_trinh_dinh(
    ids: list[str],
    syms: list[str],
    label_hint: str,
    prefix_hint: str = "",
) -> tuple[list[str], list[str]]:
    """Xoay/đảo chu trình đỉnh thiết diện khi nhãn nguồn nêu đúng một hoán vị vòng.

    Không nhãn nào nêu cả chu trình ⇒ đọc chu trình bắt đầu bằng tên mặt phẳng cắt (`prefix_hint`, vd `(MNP)` ⇒
    `MNPQ` chứ không `NMQP`) khi các đỉnh ấy liên tiếp trên chu trình. Chỉ xoay/đảo — cùng một đa giác, cùng tập cạnh.
    """
    if len(ids) < 3 or len(ids) != len(syms):
        return ids, syms
    norm_syms = [s.replace("'", "′") for s in syms]
    rev_ids = list(reversed(ids))
    rev_syms = list(reversed(syms))
    norm_rev = list(reversed(norm_syms))
    cac_vong = ((ids, syms, norm_syms), (rev_ids, rev_syms, norm_rev))

    def _tim(tokens: list[str], khop) -> tuple[list[str], list[str]] | None:
        for tok in tokens:
            for base_ids, base_syms, base_norm in cac_vong:
                for idx in range(len(base_norm)):
                    if khop(base_norm[idx:] + base_norm[:idx], tok):
                        return base_ids[idx:] + base_ids[:idx], base_syms[idx:] + base_syms[:idx]
        return None

    def _tach(text: str) -> list[str]:
        return re.findall(r"[A-Za-z0-9'′]+", (text or "").replace("'", "′"))

    ca_vong = _tim(_tach(label_hint), lambda rot, tok: "".join(rot) == tok)
    if ca_vong is not None:
        return ca_vong
    dau_vong = _tim(
        _tach(prefix_hint),
        lambda rot, tok: any("".join(rot[:k]) == tok for k in range(2, len(rot))),
    )
    return dau_vong if dau_vong is not None else (ids, syms)


def _ten_mat_cat(ten: str, prov: dict[str, dict[str, Any]], memory: dict[str, Any]) -> str:
    """Nhãn nguồn của (các) mặt phẳng cắt mà thiết diện `ten` dựa vào — gợi ý thứ tự đọc chu trình đỉnh."""
    return " ".join(
        str((prov.get(s) or {}).get("label") or "")
        for s in (prov.get(ten) or {}).get("sources", [])
        if isinstance(memory.get(s), Plane3)
    )


def _gan_measured_quantity(
    objects: list[dict[str, Any]],
    memory: dict[str, Any],
) -> None:
    """Gắn metadata `measured_quantity` có cấu trúc cho mọi đại lượng `measure.*`."""
    by_id = {o["id"]: o for o in objects}
    for o in objects:
        if o.get("type") != "quantity":
            continue
        producer = str(o.get("producer") or "")
        if not producer.startswith("measure."):
            continue
        qty_kind = producer.split(".", 1)[1]
        sources = list(o.get("sources") or [])
        subject_labels: list[str] = []
        subject_types: list[str] = []
        for sid in sources:
            subj = by_id.get(sid) or {}
            subject_labels.append(str(subj.get("reference") or subj.get("label") or sid))
            subject_types.append(str(subj.get("type") or ""))
        obj_a = memory.get(sources[0]) if len(sources) >= 1 else None
        obj_b = memory.get(sources[1]) if len(sources) >= 2 else None
        certified_relation = phan_loai_quan_he_do(qty_kind, memory.get(o["id"]), obj_a, obj_b)
        o["measured_quantity"] = {
            "quantity_kind": qty_kind,
            "producer": producer,
            "subject_ids": sources,
            "subject_labels": subject_labels,
            "subject_types": subject_types,
            "value": o.get("value"),
            "exact": o.get("exact"),
            "certified_relation": certified_relation,
        }


def _gan_lineage_va_tien_quyet(
    objects: list[dict[str, Any]],
    dependencies: dict[str, list[str]],
) -> None:
    """Tách `computational_depends`, `visible_prerequisites` và `construction_lineage` trên từng vật."""
    object_types = {str(o["id"]): str(o.get("type") or "") for o in objects if o.get("id")}
    for o in objects:
        oid = str(o["id"])
        comp_deps = list(dependencies.get(oid, []))
        vis_deps = _unwrap_visible_sources(comp_deps, object_types, dependencies, exclude_id=oid)
        o["computational_depends"] = comp_deps
        o["visible_prerequisites"] = vis_deps
        if o.get("origin") == "derived" and o.get("type") != "quantity":
            prod = str(o.get("producer") or "")
            sources = list(o.get("sources") or [])
            if prod in (
                "construct_point.intersect_line_line",
                "construct_point.intersect_lines",
                "construct_point.line_line_intersection",
            ):
                o["construction_lineage"] = {
                    "mode": "euclidean_coplanar_intersection",
                    "coplanar_lines": sources,
                }
            elif prod == "construct_point.intersect_line_plane":
                o["construction_lineage"] = {
                    "mode": "algebraic_line_plane_intersection",
                    "line_id": sources[0] if len(sources) > 0 else None,
                    "plane_id": sources[1] if len(sources) > 1 else None,
                    "pedagogical_limitation": (
                        "Giao điểm được tính trực tiếp từ phương trình đường thẳng và mặt phẳng "
                        "(chưa tách bước dựng đường phụ đồng phẳng trung gian)."
                    ),
                }
            elif prod == "construct_point.translate":
                o["construction_lineage"] = {
                    "mode": "vector_translation",
                    "base_point_id": sources[0] if len(sources) > 0 else None,
                    "vector_id": sources[1] if len(sources) > 1 else None,
                    "visible_prerequisites": list(vis_deps),
                }
            else:
                o["construction_lineage"] = {
                    "mode": "direct_euclidean_primitive",
                    "producer": prod or None,
                }


def _gan_chu_trinh_canh_thiet_dien(
    objects: list[dict[str, Any]],
    memory: dict[str, Any],
    prov: dict[str, dict[str, Any]],
) -> None:
    """Phát chu trình đỉnh và cạnh biên chuẩn cho thiết diện mà mọi đỉnh đã được đặt tên rõ."""
    named_pts = [
        o for o in objects if o.get("type") == "point3" and o.get("notation")
    ]
    unnamed_pts = [
        memory.get(o["id"])
        for o in objects
        if o.get("type") == "point3" and not o.get("notation") and isinstance(memory.get(o["id"]), Vec3)
    ]
    for sec in objects:
        if sec.get("type") != "section" or not sec.get("notation"):
            continue
        gt = memory.get(sec["id"])
        if not isinstance(gt, Section) or len(gt.polygon) < 3:
            continue
        if any(any(up == pt for up in unnamed_pts) for pt in gt.polygon):
            continue
        matched = [
            next((p for p in named_pts if memory.get(p["id"]) == pt), None)
            for pt in gt.polygon
        ]
        if any(m is None for m in matched):
            continue
        ids = [str(m["id"]) for m in matched if m is not None]
        if len(set(ids)) != len(ids):
            continue
        syms = [str(m.get("notation") or m["id"]) for m in matched if m is not None]
        hint = f"{sec.get('notation') or ''} {(prov.get(sec['id']) or {}).get('label') or ''} {sec['id']}"
        goc = list(ids)
        ids, syms = _can_chinh_chu_trinh_dinh(ids, syms, hint, _ten_mat_cat(sec["id"], prov, memory))
        n = len(syms)
        # `ordered_vertex_ids[i]` IS `polygon[i]` and `vertex_sources[i]` for every consumer that pairs them by index
        # (frontend edge/right-angle wording). Re-aligning the names without the coordinates read `SA ⊥ SC tại S`
        # off the diagonal section (SAC) whose right angle is at A — permute all three together.
        thu_tu = [goc.index(i) for i in ids]
        for khoa in ("polygon", "vertex_sources"):
            ds = sec.get(khoa)
            if isinstance(ds, list) and len(ds) == n:
                sec[khoa] = [ds[k] for k in thu_tu]
        sec["ordered_vertex_ids"] = ids
        sec["ordered_vertex_symbols"] = syms
        sec["ordered_boundary_edges"] = [f"{syms[i]}{syms[(i + 1) % n]}" for i in range(n)]


def _tim_phu_tro_du_thua(
    objects: list[dict[str, Any]],
    dependencies: dict[str, list[str]],
    memory: dict[str, Any],
    targets: list[str],
) -> list[str]:
    """Đánh dấu các vật dựng phụ không đi tới mục tiêu, đại lượng, khối hay đỉnh thiết diện nào."""
    sinks: set[str] = set(targets)
    has_terminal = bool(targets)
    section_vertices: list[Vec3] = []
    for o in objects:
        otype = o.get("type")
        if otype in (
            "quantity",
            "section",
            "solid",
            "curved_solid",
            "polygon3",
            "segment3",
            "circle3",
            "ellipse3",
            "sphere3",
            "plane3",
        ):
            sinks.add(o["id"])
            if otype in ("quantity", "section"):
                has_terminal = True
        if otype == "section":
            gt = memory.get(o["id"])
            if isinstance(gt, Section):
                section_vertices.extend(gt.polygon)
    if section_vertices:
        for o in objects:
            if o.get("type") == "point3":
                pt = memory.get(o["id"])
                if isinstance(pt, Vec3) and any(pt == sv for sv in section_vertices):
                    sinks.add(o["id"])
    if not has_terminal:
        derived_ids = [o["id"] for o in objects if o.get("origin") == "derived"]
        if derived_ids:
            sinks.add(derived_ids[-1])

    reachable: set[str] = set()
    stack = list(sinks)
    while stack:
        cur = stack.pop()
        if cur in reachable:
            continue
        reachable.add(cur)
        for dep in dependencies.get(cur) or ():
            if dep not in reachable:
                stack.append(dep)

    unused: list[str] = []
    for o in objects:
        if (
            o.get("origin") == "derived"
            and o.get("type") in ("point3", "line3", "vector3")
            and o["id"] not in reachable
        ):
            o["is_unused_auxiliary"] = True
            unused.append(o["id"])
    return unused


def _canh_song_song_thiet_dien(objects: list[dict[str, Any]]) -> None:
    """W4 · dữ kiện hình học cho «Vì sao» của từng cạnh thiết diện, kiểm CHÍNH XÁC (hữu tỉ, khung affine — song song
    và thuộc là bất biến affine, pháp tuyến `Plane3` là đối vectơ): cạnh XY của chính mặt chứa cạnh thiết diện cùng
    phương với nó và X ngoài mặt phẳng cắt ⇒ XY ∥ (α), XY ⊂ mặt ⇒ giao tuyến ∥ XY. Không tin `face_index` mù (review
    M1): cạnh phải nằm trong mặt phẳng của mặt ấy, mặt phẳng và không song song với (α). Toạ độ vô tỉ ⇒ bỏ qua."""
    by_id = {o["id"]: o for o in objects}
    for sec in objects:
        if sec.get("type") != "section":
            continue
        nguon = [by_id.get(x) for x in sec.get("sources") or []]
        solid = next((o for o in nguon if o and o.get("type") == "solid"), None)
        plane = next((o for o in nguon if o and o.get("type") == "plane3"), None)
        if solid is None or plane is None:
            continue
        try:
            q = lambda v: tuple(Fraction(str(x)) for x in v)                     # noqa: E731
            verts = [q(v) for v in solid["vertices"]]
            p0, n = q(plane["point"]), q(plane["normal"])
            buoc = [(st, q(st["a"]), q(st["b"])) for st in sec.get("steps") or []]
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
        hieu = lambda u, v: tuple(x - y for x, y in zip(u, v))                   # noqa: E731
        cheo = lambda u, v: (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])  # noqa: E731
        vo = lambda u, v: sum(x * y for x, y in zip(u, v))                         # noqa: E731
        for st, a, b in buoc:
            mat = st.get("face_index")
            face = solid["faces"][mat] if isinstance(mat, int) and 0 <= mat < len(solid["faces"]) else None
            if not face or len(face) < 3:
                continue
            pts = [verts[i] for i in face]
            d, nm = hieu(b, a), cheo(hieu(pts[1], pts[0]), hieu(pts[2], pts[0]))
            if (not any(d) or not any(nm) or not any(cheo(nm, n)) or vo(n, hieu(a, p0)) or vo(n, hieu(b, p0))
                    or any(vo(nm, hieu(x, pts[0])) for x in (*pts, a, b))):
                continue
            for i in range(len(face)):
                x, y = pts[i], pts[(i + 1) % len(face)]
                if any(cheo(d, hieu(y, x))) or not vo(n, hieu(x, p0)):
                    continue
                st["parallel_face_edge"] = [face[i], face[(i + 1) % len(face)]]
                break


def _vet_giao_tuyen_thiet_dien(objects: list[dict[str, Any]]) -> None:
    """Run `scene3d-causal-pedagogical-integrity` (GEO-BE-V9415-001) — the TRACE METHOD of the textbook, exactly.

    A section edge with no parallel reason (`parallel_face_edge`) is explained by how its endpoints are FOUND: points of
    the cutting plane Π known so far start as the named points of Π on the solid's face planes; a face plane holding two
    known points carries the trace through them, and that trace meets each edge LINE of the face (two coplanar lines) in
    a new point of Π, which lies on both faces of that edge — a section vertex on the segment, or an auxiliary point on
    the extended edge. A face with one known point whose plane is parallel to a known trace carries the parallel through
    it. Everything is affine incidence over ℚ (no metric). A step gets `trace_derivation` only when both endpoints are
    derived and lie on the trace of its own face; otherwise nothing is claimed."""
    by_id = {o["id"]: o for o in objects}
    q = lambda v: tuple(Fraction(str(x)) for x in v)                                       # noqa: E731
    hieu = lambda u, v: tuple(x - y for x, y in zip(u, v))                                 # noqa: E731
    cheo = lambda u, v: (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])  # noqa: E731
    vo = lambda u, v: sum(x * y for x, y in zip(u, v))                                     # noqa: E731

    def giao(p, d, r, e):                                   # p + s·d = r + t·e, coplanar, not parallel ⇒ (point, t)
        w = cheo(d, e)
        k = max(range(3), key=lambda i: abs(w[i]))
        if w[k] == 0:
            return None
        rp = hieu(r, p)
        s = cheo(rp, e)[k] / w[k]
        t = cheo(rp, d)[k] / w[k]
        x = tuple(pi + s * di for pi, di in zip(p, d))
        return x if tuple(ri + t * ei for ri, ei in zip(r, e)) == x else None, t

    for sec in objects:
        if sec.get("type") != "section" or not sec.get("steps"):
            continue
        nguon = [by_id.get(x) for x in sec.get("sources") or []]
        solid = next((o for o in nguon if o and o.get("type") == "solid"), None)
        plane = next((o for o in nguon if o and o.get("type") == "plane3"), None)
        if solid is None or plane is None:
            continue
        try:
            verts = [q(v) for v in solid["vertices"]]
            p0, n = q(plane["point"]), q(plane["normal"])
            faces = [list(f) for f in solid["faces"]]
            named = [(o["id"], q(o["xyz"])) for o in objects if o.get("type") == "point3" and o.get("xyz")]
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue
        nm = [cheo(hieu(verts[f[1]], verts[f[0]]), hieu(verts[f[2]], verts[f[0]])) if len(f) >= 3 else (0, 0, 0) for f in faces]
        tren_mat = lambda x, i: any(nm[i]) and vo(nm[i], hieu(x, verts[faces[i][0]])) == 0   # noqa: E731
        trong_pi = lambda x: vo(n, hieu(x, p0)) == 0                                         # noqa: E731
        known: list[dict[str, Any]] = []                     # {xyz, ref, faces, depth}
        for vid, x in named:
            mats = {i for i in range(len(faces)) if tren_mat(x, i)}
            if trong_pi(x) and mats and all(k["xyz"] != x for k in known):
                vi = next((j for j, v in enumerate(verts) if v == x), None)
                known.append({"xyz": x, "ref": {"vertex": vi} if vi is not None else {"id": vid}, "faces": mats, "depth": 0})
        for j, v in enumerate(verts):
            if trong_pi(v) and all(k["xyz"] != v for k in known):
                known.append({"xyz": v, "ref": {"vertex": j}, "faces": {i for i, f in enumerate(faces) if j in f}, "depth": 0})
        derivations: list[dict[str, Any]] = []
        traces: dict[int, dict[str, Any]] = {}
        # Rounds (breadth first): a round only uses points and traces known when it starts, so every point is reached by
        # the SHORTEST chain of coplanar intersections — the textbook construction, not whichever face came first.
        for _ in range(2 * len(faces) + 2):
            snap, tr_snap, moi = list(known), dict(traces), False
            for i, f in enumerate(faces):
                if i in traces or not any(nm[i]) or not any(cheo(nm[i], n)):
                    continue
                pts = [k for k in snap if i in k["faces"]]
                cap = sorted(((max(u["depth"], w["depth"]), u["depth"] + w["depth"], iu, iw, u, w)
                              for iu, u in enumerate(pts) for iw, w in enumerate(pts) if iu < iw and u["xyz"] != w["xyz"]),
                             key=lambda c: c[:4])
                if cap:
                    _d, _s, _i, _j, u, w = cap[0]
                    tr = {"through": [u["ref"], w["ref"]], "point": u["xyz"], "dir": hieu(w["xyz"], u["xyz"]), "depth": _d}
                elif len(pts) == 1:
                    ss = next((g for g, t in sorted(tr_snap.items(), key=lambda gt: gt[1]["depth"]) if vo(nm[i], t["dir"]) == 0), None)
                    if ss is None:
                        continue
                    tr = {"through": [pts[0]["ref"]], "parallel_to_trace_of": ss, "point": pts[0]["xyz"],
                          "dir": tr_snap[ss]["dir"], "depth": max(pts[0]["depth"], tr_snap[ss]["depth"])}
                else:
                    continue
                traces[i] = tr
                moi = True
                for e in range(len(f)):
                    x0, x1 = f[e], f[(e + 1) % len(f)]
                    kq = giao(tr["point"], tr["dir"], verts[x0], hieu(verts[x1], verts[x0]))
                    if kq is None or kq[0] is None:
                        continue
                    x, t = kq
                    if not (trong_pi(x) and tren_mat(x, i)) or any(k["xyz"] == x for k in known):
                        continue
                    derivations.append({"xyz": [str(c) for c in x], "face": i, "trace": tr["through"],
                                        **({"parallel_to_trace_of": tr["parallel_to_trace_of"]} if "parallel_to_trace_of" in tr else {}),
                                        "edge": sorted((x0, x1)), "on_edge_segment": bool(0 <= t <= 1)})
                    known.append({"xyz": x, "ref": {"derived": len(derivations) - 1}, "depth": tr["depth"] + 1,
                                  "faces": {g for g, ff in enumerate(faces) if x0 in ff and x1 in ff}})
            if not moi:
                break
        at = {k["xyz"]: k["ref"] for k in known}
        for st in sec["steps"]:
            mat = st.get("face_index")
            if st.get("parallel_face_edge") or mat not in traces:
                continue
            try:
                a, b = q(st["a"]), q(st["b"])
            except (KeyError, TypeError, ValueError):
                continue
            tr = traces[mat]
            if a not in at or b not in at or any(cheo(hieu(x, tr["point"]), tr["dir"]) != (0, 0, 0) for x in (a, b)):
                continue
            need: list[int] = []

            def can(ref):
                if "derived" in ref and ref["derived"] not in need:
                    d = derivations[ref["derived"]]
                    for r in d["trace"]:
                        can(r)
                    if "parallel_to_trace_of" in d:
                        for r in traces[d["parallel_to_trace_of"]]["through"]:
                            can(r)
                    need.append(ref["derived"])
            for r in (*tr["through"], at[a], at[b]):
                can(r)
            st["trace_derivation"] = {"face": mat, "through": tr["through"],
                                      **({"parallel_to_trace_of": tr["parallel_to_trace_of"]} if "parallel_to_trace_of" in tr else {}),
                                      "endpoints": [at[a], at[b]],
                                      "derivations": [{**derivations[k], "index": k} for k in sorted(need)],
                                      "verified_exact": True}


def _ky_hieu_dien_tich_thiet_dien(objects: list[dict[str, Any]], contract: Any) -> None:
    """W18 §16.6 — nhãn ngắn trên hình là `ký hiệu = giá trị`. Diện tích của một thiết diện mà ĐỀ đặt tên
    (`… theo thiết diện (T)`, đọc bằng `doc_quan_he_cat`, không từ nhãn mô hình) có ký hiệu `S(T)`: tên
    biến thiết diện trùng tên đề đặt, hoặc đề có đúng một tên và cảnh có đúng một thiết diện."""
    ten_de = {q.thiet_dien for q in doc_quan_he_cat(getattr(contract, "problem_text", "") or "") if q.thiet_dien}
    thiet_dien = [o["id"] for o in objects if o["type"] == "section"]
    for o in objects:
        nguon = o.get("sources") or []
        if (o["type"] != "quantity" or o.get("notation") or o.get("producer") != "measure.area"
                or len(nguon) != 1 or nguon[0] not in thiet_dien):
            continue
        ten = ky_hieu_toan(nguon[0])
        ten = ten if ten in ten_de else (next(iter(ten_de)) if len(ten_de) == 1 == len(thiet_dien) else None)
        if ten:
            o["notation"] = o["reference"] = f"S({ten})"


def _muc_tieu(contract: Any) -> set[str]:
    """Tên vật mà NGHĨA VỤ CỦA ĐỀ nhắc tới.

    Đọc từ `RequestContract`, KHÔNG từ `SemanticProgramSpec` — spec không có
    trường `obligations`, và nếu có thì đó cũng là nghĩa vụ do chương trình tự
    khai. Nhóm `target` phải nói *"đề bảo chứng minh cái này"*, không phải
    *"chương trình tự nhận nó chứng minh cái này"*.

    `None` (đường gọi cũ, test dựng state bằng tay) ⇒ không có mục tiêu nào,
    và nhóm `target` đơn giản là vắng mặt. Không đoán.
    """
    ra: set[str] = set()
    for ob in (getattr(contract, "obligations", None) or ()):
        for t in (getattr(ob, "container", None), getattr(ob, "witness", None)):
            if isinstance(t, str) and t:
                ra.add(t)
        for v in (getattr(ob, "params", None) or {}).values():
            if isinstance(v, str) and v:
                ra.add(v)
    return ra


def _xuat_xu_hien_thi(spec: SemanticProgramSpec, contract: Any = None) -> dict[str, dict[str, Any]]:
    """`id → xuất xứ NGẮN` cho ô soi. Không chép prompt vào từng đối tượng.

    Ba mẩu, mỗi mẩu trả lời một câu học sinh thật sự hỏi:
    `fact_id` *"dữ kiện nào của đề"* · `assumption` *"chỗ này do ai chọn"* ·
    `instruction` *"câu lệnh nào dựng ra"*. W18 §16.3 thêm `binding` cho điểm dựng: `TEXT_RELATION`
    (dựng đúng quan hệ đề nêu) hay `AUXILIARY` (điểm phụ của hệ, không bao giờ là dữ kiện).
    """
    prov = _provenance(spec)
    ra: dict[str, dict[str, Any]] = {}
    for d in (spec.memory_declarations or ()):
        m = {"fact_id": getattr(d, "source_fact_id", None),
             "assumption": getattr(d, "model_assumption", None),
             "provenance": getattr(d, "provenance", None)}
        if any(m.values()):
            ra[d.name] = {k: v for k, v in m.items() if v}
    for ten, p in prov.items():
        ra.setdefault(ten, {})["instruction"] = p.get("producer")
    if contract is not None:
        try:
            dc = doi_chieu_phep_dung(contract, spec)
        except Exception:  # noqa: BLE001 — một nhãn xuất xứ hỏng không được làm mất cả cảnh
            dc = None
        for ten, tt in (dc.trang_thai.items() if dc else ()):
            nguon = {MATCHED: "TEXT_RELATION", AUXILIARY: "AUXILIARY"}.get(tt)
            for x in ({ten} | {a for a, g in dc.bi_danh.items() if g == ten}) if nguon else ():
                ra.setdefault(x, {})["binding"] = nguon
    return ra
