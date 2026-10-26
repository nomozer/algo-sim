# -*- coding: utf-8 -*-
"""ENGINE TẤT ĐỊNH của đường text → function calls → dựng → kiểm → Scene3D (run `text-to-geometry-functions`).

    lời gọi có kiểu (registry.doc_ke_hoach) → cổng nguồn (registry.kiem_nguon)
      → giải phụ thuộc + chọn BỐ CỤC (khung affine hữu tỉ + metric Gram G, `geometry.metric`)
      → kiểm lại MỌI dữ kiện trên bố cục (mâu thuẫn ⇒ INCONSISTENT_FACTS; dữ kiện engine đã dùng mà sai ⇒
        ENGINE_SELF_CHECK_FAILED)
      → IR `SemanticProgramSpec` HIỆN CÓ qua bộ tạo câu lệnh dùng chung `semantic_program.ir_builders`
      → `SemanticProgramInterpreter` + kernel HIỆN CÓ dưới `metric.using(G)` → `build_scene3d` HIỆN CÓ + `chart_metric`.

─── BỐ CỤC: VÌ SAO KHUNG AFFINE ─────────────────────────────────────────────
Tam giác đều / lục giác đều cạnh hữu tỉ không có toạ độ Euclid trong ℚ³ (pilot G05: mô hình viết `sqrt(3)` và bị
`IR_NOT_EXACT_RATIONAL`). Engine đặt đáy trong một khung affine chuẩn của hình (tam giác: (0,0),(1,0),(0,1); lục giác:
u, u+v, v, −u, −u−v, −v) và lấy ĐỘ DÀI từ ma trận Gram 2×2 dẫn xuất từ dữ kiện đề. Trục thứ ba e₃ vuông góc đáy theo
metric (G₁₃ = G₂₃ = 0), |e₃|² = h² ⇒ đỉnh ngoài đáy luôn ở z = 1, kể cả khi h vô tỉ. Bố cục là lựa chọn của engine
(`LAYOUT_DERIVED`), không mang độ dài nào — độ dài chỉ đến từ dữ kiện có nguồn.

─── CHÂN ĐƯỜNG CAO KHÔNG SUY ĐOÁN ───────────────────────────────────────────
Một điểm ngoài đáy chỉ được đặt khi CÓ lời gọi xác định chân: `perpendicular_line_plane` với một đầu nằm trong đáy
(chân = chính đầu ấy), hoặc `regular_pyramid` (chân = tâm đáy đều, theo định nghĩa). Không có ⇒ UNDERDETERMINED_POINT.
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass, field
from fractions import Fraction
from itertools import combinations
from math import isqrt
from typing import Any

from app.simulation.geometry import metric as _metric
from app.simulation.geometry.exact import GeometryError, Line3, Plane3, Vec3
from app.simulation.geometry import kernel as K
from app.simulation.geometry.predicates import parallel_planes, point_on_line, point_on_plane, parallel_line_plane, line_in_plane
from app.simulation.semantic_program import ir_builders as P

from .registry import MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG, LoiGoi, TuChoi, binh_phuong, doc_ke_hoach, doc_so, kiem_nguon, nhan_cua_de, nhom_mat_nguon
from .registry import DINH_CAT_CANH, _cum_hoi

#: /6 (run `goal-directed-function-composition`): `ask_angle_lines` IR + independent line–line Gram verifier.
#: /7 (run `geometry-capability-expansion`): ratio points, right-angle-chain base, prism lateral vector, ⊥-line plane check.
#: /8 (run `composite-geometry`): determined derived bases, per-solid formation, independent volume certificates.
#: /9 (run `volume-reasoning`): exact volume ratio (`ask_volume_ratio`) and residual volume (`ask_residual_volume`) certificates.
#: /10 (run `typedfactnext-planner-bridge`): section vertices verified on their edge segment (0 < t ≤ 1, `kiem_dinh_cat`).
#: /11 (run `hybrid-contract-v2`, owner D5/D6): section closure certificate (`chung_chi_khep_kin` = exact `cross_section`),
#: declared-boundary verification; IR canonicalization limited to engine-owned names.
ENGINE_VERSION = "geometry-function-engine/12"
Z = Fraction(0)
V3 = tuple[Fraction, Fraction, Fraction]


def ir_name(label: str) -> str:
    """Nhãn đề → tên máy của IR (`A'` → `A_prime`)."""
    return label.replace("'", "_prime")


# ── primitive bố cục: đa giác đều trong khung affine ────────────────────────
def regular_polygon_chart(k: int, side_sq: Fraction):
    """(đỉnh khung 2D theo vòng, Gram 2×2) của đa giác đều k cạnh, cạnh² = side_sq. Chỉ k ∈ {3, 4, 6}: với k khác,
    cos(2π/k) vô tỉ ⇒ không có Gram hữu tỉ ⇒ từ chối có mã thay vì xấp xỉ."""
    o, h = Fraction(1), Fraction(1, 2)
    if k == 3:
        return ((Z, Z), (o, Z), (Z, o)), ((side_sq, side_sq * h), (side_sq * h, side_sq))
    if k == 4:
        return ((Z, Z), (o, Z), (o, o), (Z, o)), ((side_sq, Z), (Z, side_sq))
    if k == 6:
        return (((o, Z), (o, o), (Z, o), (-o, Z), (-o, -o), (Z, -o)),
                ((side_sq, -side_sq * h), (-side_sq * h, side_sq)))
    raise TuChoi("UNSUPPORTED_REGULAR_POLYGON",
                 f"đa giác đều {k} cạnh không có khung hữu tỉ chính xác (chỉ 3, 4, 6)")


def _sqrt_q(x: Fraction) -> Fraction | None:
    if x < 0:
        return None
    a, b = isqrt(x.numerator), isqrt(x.denominator)
    return Fraction(a, b) if a * a == x.numerator and b * b == x.denominator else None


@dataclass
class KetQuaTuyen:
    """Kết cục của đường mới. `REFUSED` luôn có `code` + `reason`; `SERVED` luôn có `scene3d` + `answers`."""

    status: str
    code: str | None = None
    reason: str | None = None
    failed_calls: tuple[str, ...] = ()
    answers: dict[str, str] = field(default_factory=dict)
    scene3d: dict[str, Any] | None = None
    trace: list[dict[str, Any]] = field(default_factory=list)
    program: dict[str, Any] | None = None
    points: dict[str, V3] = field(default_factory=dict)
    metric: list[list[str]] | None = None
    kernel_check: bool | None = None
    calls: list[dict[str, Any]] = field(default_factory=list)
    #: Chương trình ĐÃ bổ sung dựng hình + kết quả thực thi + metric — đầu vào của tầng bày cảnh.
    spec: Any = None
    exec_result: Any = None
    chart_metric: Any = None
    #: Đáp số chính xác có cấu trúc: {"coef": hệ số, "dim": bậc theo a (0 khi đề dùng số), "unit": "a" | None}.
    answer_exact: dict[str, dict[str, Any]] = field(default_factory=dict)
    #: "a" khi mọi độ dài đề cho theo a (bố cục dựng ở a = 1, đơn vị — không phải dữ kiện); None khi đề dùng số.
    length_unit: str | None = None
    #: Chẩn đoán của adapter AI (số lời gọi, usage, lời gọi trùng đã bỏ…) — rỗng khi lời gọi đến từ fixture.
    ai: dict[str, Any] = field(default_factory=dict)
    #: Dữ liệu có cấu trúc của lời từ chối (vd điểm chưa xác định) — để tầng trên chẩn đoán mà không phân tích câu chữ.
    details: dict[str, Any] = field(default_factory=dict)
    #: Chẩn đoán của planner nhánh B (lời gọi sinh ra, mục tiêu chứng minh đã kiểm…) — rỗng ở nhánh A.
    planner: dict[str, Any] = field(default_factory=dict)
    #: Kiểm một lời gọi (dict) trên hình ĐÃ dựng: True/False, None = không kiểm được. Chỉ có khi SERVED.
    checker: Any = field(default=None, repr=False, compare=False)
    #: Hợp đồng CHỈ mang tô-pô khối đề đã khai (`hop_dong_to_po_da_khai`) — cùng một giá trị cho bổ sung dựng hình và bày cảnh.
    declared_topology: Any = None
    #: Route-D `/4` envelope (run `hybrid-contract-v2`, `app/ai/adapter4_route.py`); None on every other route.
    route_d: dict[str, Any] | None = None
    #: Tên IR mà ĐỀ hỏi (CONTRACT-BE-1): biến đáp số của mỗi lời hỏi đã qua cổng nguồn + toán hạng phép đo của nó, trừ điểm
    #: phụ tươi do planner dựng. Cùng nghĩa `targets` mà tuyến LLM_ONLY đọc từ nghĩa vụ của `RequestContract`.
    targets: tuple[str, ...] = ()


def hop_dong_to_po_da_khai(calls: tuple[LoiGoi, ...]) -> Any:
    """Tô-pô khối ĐỀ ĐÃ KHAI → `RequestContract(solid_topology=…)`, thẩm quyền ① của `formation.lop_khoi`.

    Khi câu nguồn viết ký hiệu chấm khớp lời gọi: chóp `S.ABC` (đỉnh + đáy), lăng trụ
    `ABC.A'B'C'` (đáy + đáy trên, ′ ’ ≡ ').
    "Tứ diện ABCD" không nêu đỉnh — đỉnh trong lời gọi là lựa chọn của mô hình/planner ⇒ None, không bịa tô-pô.
    Nhiều khối trả map theo tập đỉnh IR; thiếu tô-pô trả None. Không đoán đỉnh từ bảng mặt của tứ diện.
    """
    from app.simulation.semantic_program.request_contract import PyramidTopologySpec, RequestContract

    from app.simulation.semantic_program.request_contract import PrismTopologySpec

    khoi = [c for c in calls if c.fn in ("pyramid", "regular_pyramid", "prism")]   # the calls `thu_khoi` builds solids from
    if len(khoi) != 1:
        # Internal per-solid contracts, never a provider/schema extension. Formation resolves by exact vertex identity.
        result = {}
        for c in khoi:
            contract = hop_dong_to_po_da_khai((c,))
            if contract is None:
                continue
            key = frozenset(map(ir_name, _labels(c)))
            if key in result and result[key] != contract:
                raise TuChoi("AMBIGUOUS_REFERENCE", "cùng tập đỉnh nhận hai tô-pô khối khác nhau", (c.id,))
            result[key] = contract
        return result or None
    a, nhan = khoi[0].args, r"A-Za-z0-9'′"
    phay = lambda s: s.replace("′", "'").replace("’", "'")    # A′, A’ and A' are the same source name
    dau = list(a.base) if khoi[0].fn == "prism" else [a.apex]
    sau = list(a.top) if khoi[0].fn == "prism" else list(a.base)
    ky_hieu = "".join(map(re.escape, map(phay, dau))) + r"\s*\.\s*" + "".join(map(re.escape, map(phay, sau)))
    if not any(re.search(rf"(?<![{nhan}]){ky_hieu}(?![{nhan}])", phay(q)) for q in khoi[0].quotes):
        return None
    if khoi[0].fn == "prism":     # pedagogical-construction-sequencing: base / top face / lateral edges, source-declared
        return RequestContract(solid_topology=PrismTopologySpec(
            base_cycle=tuple(a.base), top_cycle=tuple(a.top), correspondence=tuple(zip(a.base, a.top)),
            lateral_structure="right" if a.right else None))           # review C3: an oblique prism is not declared right
    return RequestContract(solid_topology=PyramidTopologySpec(apex=a.apex, base_cycle=tuple(a.base)))


def thu_tu_su_pham(khoi_diem: list[tuple[str, list[dict[str, Any]]]], dinh_khoi: set[str]
                   ) -> tuple[list[tuple[str, list[dict[str, Any]]]], list[tuple[str, list[dict[str, Any]]]]]:
    """Point blocks `(name, statements)` in dependency order → (blocks the solids need, the rest), each in its original
    order. A block is needed when it is a solid vertex or (transitively) read by a needed block — a topological split, no
    statement is changed, so the kernel computes the same values (run `pedagogical-construction-sequencing`)."""
    ten = {t for t, _ in khoi_diem}

    def doc(x: Any) -> set[str]:
        if isinstance(x, str):
            return {x} & ten
        if isinstance(x, dict):
            return set().union(*map(doc, x.values())) if x else set()
        if isinstance(x, list):
            return set().union(*map(doc, x)) if x else set()
        return set()

    can = set(dinh_khoi) & ten
    for t, l in reversed(khoi_diem):               # reads only point to earlier blocks ⇒ one backward pass closes
        if t in can:
            can |= doc(l) - {t}
    return [b for b in khoi_diem if b[0] in can], [b for b in khoi_diem if b[0] not in can]


#: Fields of an IR statement that are never a reference to another variable (run `hybrid-contract-v2`, P1).
_KHONG_THAM_CHIEU = frozenset({"kind", "label", "target_var"})


def gop_doi_tuong_trung(khai: list[dict[str, Any]], lenh: list[dict[str, Any]], so_huu: set[str] | frozenset[str]
                        ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """IR canonicalization (run `backend-hybrid-contract-unification`), on the FINAL statement order: an engine-OWNED line
    / plane (`so_huu`: names `bien_dich` itself created for an operand, never a source name nor a labelled object) whose
    construction (IR kind + operand names) repeats one already in the program IS that object — the repeat is dropped and
    every later reference goes to the first. The kernel builds the same object from the same named operands, so values
    are unchanged; only declarations shrink. References are rewritten only in reference fields (`_KHONG_THAM_CHIEU`)."""
    dau: dict[tuple, str] = {}
    doi: dict[str, str] = {}

    def ve(x: Any, khoa_cha: str = "") -> Any:
        if isinstance(x, str):
            return x if khoa_cha in _KHONG_THAM_CHIEU else doi.get(x, x)
        if isinstance(x, dict):
            return {k: ve(v, k) for k, v in x.items()}
        if isinstance(x, list):
            return [ve(v, khoa_cha) for v in x]
        return x

    giu = []
    for st in lenh:
        st = ve(st) if doi else st
        if st["kind"] in ("construct_line", "construct_plane"):
            khoa = (st["kind"], st.get("through_a"), st.get("through_b"), tuple(st.get("through") or ()))
            if khoa in dau and st["target_var"] in so_huu and "label" not in st:
                doi[st["target_var"]] = dau[khoa]
                continue
            dau.setdefault(khoa, st["target_var"])
        giu.append(st)
    return [d for d in khai if d["name"] not in doi], giu


@dataclass
class _Khoi:
    name: str
    kind: str                  # pyramid | prism
    base: tuple[str, ...]
    apex: str | None = None
    top: tuple[str, ...] = ()
    right: bool = False
    regular: bool = False
    call: str = ""


def _key(c: LoiGoi) -> tuple:
    """Thứ tự CHÍNH TẮC của lời gọi — theo nội dung, không theo thứ tự AI liệt kê."""
    return (c.fn, json.dumps(c.args.model_dump(), ensure_ascii=False, sort_keys=True), c.id)


class _Dung:
    def __init__(self, calls: tuple[LoiGoi, ...], text: str, ky_hieu: str | None = None) -> None:
        self.calls = tuple(sorted(calls, key=_key))
        self.ky_hieu = ky_hieu
        self.centroids: dict[str, tuple[str, ...]] = {}
        self.text_labels = nhan_cua_de(text)
        self.pts: dict[str, V3] = {}
        self.G2: tuple | None = None
        self.h2: Fraction | None = None
        self.trace: list[dict[str, Any]] = []
        self.dung: set[str] = set()             # id lời gọi engine ĐÃ DÙNG để dựng bố cục
        self.khoi: dict[str, _Khoi] = {}
        self.tam: str | None = None
        self.midpoints: dict[str, tuple[str, str]] = {}
        self.divisions: dict[str, tuple[str, str, Fraction]] = {}   # P = (1 − t)A + tB (`divide_segment`)
        self.constructions: dict[str, LoiGoi] = {}
        self.lines: dict[str, Line3] = {}       # existing entity store: verified source-bound line results
        self.line_refs = {c.args.line_ref for c in calls if c.fn=='orthogonal_projection_line' and c.args.line_ref}
        self.line_aliases = {}
        if self.line_refs:
            groups={}
            for c in self.of('intersection_line'):
                key=tuple(sorted((tuple(sorted(c.args.plane1)),tuple(sorted(c.args.plane2)))))
                groups.setdefault(key,[]).append(c.id)
            self.line_aliases={cid:min(ids) for ids in groups.values() for cid in ids}
        self.sections: list[str] = []           # biến IR của thiết diện đã dựng (kiểm khép kín sau khi thực thi)
        self.mat_phu: list[dict] = []           # mặt phẳng dẫn xuất đã khai (`MAT_SONG_SONG`), kiểm ở `kiem_mat_cat`
        self.ten_mat_phu: dict[str, str | None] = {}   # tên đề đặt cho mỗi mặt dẫn xuất — do `kiem_nguon` trả về

    def of(self, *fns: str) -> list[LoiGoi]:
        return [c for c in self.calls if c.fn in fns]

    # ── khối ────────────────────────────────────────────────────────────────
    def thu_khoi(self) -> None:
        for c in self.of("pyramid", "regular_pyramid", "prism"):
            a = c.args
            if c.fn == "prism":
                if len(a.base) != len(a.top):
                    raise TuChoi("SCHEMA_INVALID", f"{c.id}: hai đáy lăng trụ khác số đỉnh", (c.id,))
                k = _Khoi("".join(a.base) + "." + "".join(a.top), "prism", tuple(a.base), top=tuple(a.top),
                          right=a.right, call=c.id)
            else:
                k = _Khoi(a.apex + "." + "".join(a.base), "pyramid", tuple(a.base), apex=a.apex,
                          regular=c.fn == "regular_pyramid", call=c.id)
            cu = self.khoi.get(k.name)
            if cu:
                cu.regular = cu.regular or k.regular
            else:
                self.khoi[k.name] = k
        if not self.khoi:
            raise TuChoi("NO_SOLID", "bản này chỉ dựng khối chóp / lăng trụ; kế hoạch không có khối nào")
        for c in self.of("height", "ask_volume"):
            if c.args.solid not in self.khoi:
                raise TuChoi("UNKNOWN_SOLID", f"{c.id}: khối {c.args.solid} chưa được dựng bằng lời gọi nào", (c.id,))
        for c in self.of("ask_volume_ratio"):
            for s in (c.args.numerator_solid, c.args.denominator_solid):
                if s not in self.khoi:
                    raise TuChoi("UNKNOWN_SOLID", f"{c.id}: khối {s} chưa được dựng bằng lời gọi nào", (c.id,))
        for c in self.of("ask_residual_volume"):
            for s in (c.args.original_solid, *c.args.subtracted_solids):
                if s not in self.khoi:
                    raise TuChoi("UNKNOWN_SOLID", f"{c.id}: khối {s} chưa được dựng bằng lời gọi nào", (c.id,))
            if len(set(c.args.subtracted_solids)) != len(c.args.subtracted_solids):
                raise TuChoi("INCONSISTENT_FACTS", f"{c.id}: danh sách khối bị cắt bỏ lặp khối", (c.id,))
        self.root = next(iter(self.khoi.values()))
        self.composite = len({frozenset(k.base) for k in self.khoi.values()}) != 1 or len(self.khoi) > 1
        if self.composite:
            # A new base is admitted only as a derived object in the SAME chart. Never lay out an independent base.
            outputs = {c.args.point for c in self.of("midpoint", "centroid", "divide_segment", "intersect_line_line",
                                                    "intersect_line_plane")}
            outputs |= {c.args.image for c in self.of("orthogonal_projection", "orthogonal_projection_line", "translate_point")}
            roots = [k for k in self.khoi.values() if not (set(k.base) | set(k.top) | {k.apex}) & outputs]
            if not roots or len({frozenset(k.base) for k in roots}) != 1:
                raise TuChoi("UNSUPPORTED_MULTIPLE_BASES", "cần một đáy gốc; các đáy khác phải dùng đỉnh đã dựng duy nhất")
            self.root = roots[0]
            if any(k.kind != "pyramid" for k in self.khoi.values() if k not in roots):
                raise TuChoi("UNSUPPORTED_MULTIPLE_BASES", "khối có đáy dẫn xuất hiện chỉ hỗ trợ hình chóp")

    # ── độ dài ──────────────────────────────────────────────────────────────
    def _lop_bang(self, s: frozenset) -> list[tuple[frozenset, tuple[str, ...]]]:
        """Các đoạn bằng `s` qua chuỗi `equal_length` (kèm id lời gọi của chuỗi)."""
        lop, hang = {s: ()}, [s]
        while hang:
            u = hang.pop()
            for c in self.of("equal_length"):
                a, b = frozenset(c.args.segment_a), frozenset(c.args.segment_b)
                for p, q in ((a, b), (b, a)):
                    if p == u and q not in lop:
                        lop[q] = lop[u] + (c.id,)
                        hang.append(q)
        return sorted(lop.items(), key=lambda kv: sorted(kv[0]))

    def do_dai(self, x: str, y: str, _suy: bool = True) -> list[tuple[Fraction, tuple[str, ...]]]:
        """Độ dài² của đoạn xy từ MỌI nguồn tất định: `segment_length`, lớp `equal_length`, hình đã dựng (hai đầu đã
        đặt), cạnh khác của một đa giác đều chứa xy (cả `side` của nó). Hai nguồn lệch ⇒ INCONSISTENT_FACTS NGAY —
        mâu thuẫn của đề, không để lọt thành lỗi tự kiểm của engine."""
        ra: list[tuple[Fraction, tuple[str, ...]]] = []
        for s, chuoi in self._lop_bang(frozenset((x, y))):
            ra += [(binh_phuong(c.args.value), (c.id, *chuoi)) for c in self.of("segment_length")
                   if frozenset(c.args.segment) == s]
            a, b = sorted(s)
            if a in self.pts and b in self.pts:
                ra.append((self.d2(a, b), chuoi))
        if _suy:
            for c in self.of("regular_polygon"):
                v, n = c.args.vertices, len(c.args.vertices)
                canh = [frozenset((v[i], v[(i + 1) % n])) for i in range(n)]
                if frozenset((x, y)) not in canh:
                    continue
                if c.args.side is not None:
                    ra.append((binh_phuong(c.args.side), (c.id,)))
                for e in canh:
                    if e != frozenset((x, y)):
                        ra += [(d, (c.id, *ids)) for d, ids in self.do_dai(*sorted(e), _suy=False)]
        if len({d for d, _ in ra}) > 1:
            raise TuChoi("INCONSISTENT_FACTS", f"đoạn {x}{y} nhận hai độ dài khác nhau từ các dữ kiện",
                         tuple(sorted({i for _, ids in ra for i in ids})))
        return ra

    # ── đáy ─────────────────────────────────────────────────────────────────
    def bo_cuc_day(self) -> None:
        dat = frozenset(self.root.base)
        reg = [c for c in self.of("regular_polygon") if frozenset(c.args.vertices) == dat]
        rect = [c for c in self.of("rectangle") if frozenset(c.args.vertices) == dat]
        if reg:
            c = reg[0]
            vong = tuple(c.args.vertices)
            if c.args.side is not None:
                s2, dung = binh_phuong(c.args.side), {c.id}
            else:
                ung = sorted((d, ids) for i in range(len(vong)) for d, ids in self.do_dai(vong[i], vong[(i + 1) % len(vong)]))
                if not ung:
                    raise TuChoi("MISSING_DIMENSION", "đa giác đều đáy chưa có độ dài cạnh", (c.id,))
                s2, dung = ung[0][0], {c.id, *ung[0][1]}
            khung, G2 = regular_polygon_chart(len(vong), s2)
            luat = "regular_polygon_chart"
        elif rect:
            c = rect[0]
            vong = tuple(c.args.vertices)
            a = self.do_dai(vong[0], vong[1]) or self.do_dai(vong[2], vong[3])
            b = self.do_dai(vong[1], vong[2]) or self.do_dai(vong[3], vong[0])
            if not a or not b:
                raise TuChoi("MISSING_DIMENSION", "hình chữ nhật đáy thiếu một cạnh", (c.id,))
            khung = ((Z, Z), (Fraction(1), Z), (Fraction(1), Fraction(1)), (Z, Fraction(1)))
            G2, dung, luat = ((a[0][0], Z), (Z, b[0][0])), {c.id, *a[0][1], *b[0][1]}, "rectangle_chart"
        elif len(dat) == 3:
            vong = self.root.base
            khung, G2, dung = self._tam_giac(vong)
            luat = "triangle_by_sides"
        elif (chuoi := self._chuoi_goc_vuong(self.root.base)) is not None:
            vong, khung, G2, dung = chuoi
            luat = "right_angle_chain_chart"
        else:
            raise TuChoi("UNSUPPORTED_BASE_SHAPE",
                         f"đáy {len(dat)} đỉnh không có lời gọi xác định hình (đa giác đều / hình chữ nhật)")
        if not (G2[0][0] > 0 and G2[0][0] * G2[1][1] - G2[0][1] * G2[1][0] > 0):
            raise TuChoi("INCONSISTENT_FACTS", "các độ dài đáy không tạo thành một đa giác (vi phạm bất đẳng thức tam giác)",
                         tuple(sorted(dung)))
        self.G2, self.dung = G2, self.dung | dung
        for v, (x, y) in zip(vong, khung):
            self._dat(v, (x, y, Z), luat, dung)

    def _chuoi_goc_vuong(self, vong: tuple[str, ...]):
        """Quadrilateral base with right angles at two CONSECUTIVE vertices Vi, Vj (right trapezoid), each angle between the
        polygon's own two sides there. Both legs ViVp, VjVn are ⊥ ViVj, hence parallel, and on the SAME side of ViVj (any
        other side makes ABCD self-intersecting). Chart: Vi origin, e1 = ViVj, e2 = ViVp, G2 = diag(|ViVj|², |ViVp|²),
        Vn = Vj + (|VjVn| / |ViVp|)·e2 — exact only when that ratio is rational. Missing length ⇒ MISSING_DIMENSION; the
        fourth side, if given, is checked later like every fact. None when no such pair exists (not this shape)."""
        if len(vong) != 4:
            return None
        goc = {(c.args.vertex, frozenset(c.args.rays)): c.id for c in self.of("right_angle")}   # several per vertex allowed
        for i in range(4):
            vi, vj, vp, vn = vong[i], vong[(i + 1) % 4], vong[(i - 1) % 4], vong[(i + 2) % 4]
            gi, gj = goc.get((vi, frozenset((vp, vj)))), goc.get((vj, frozenset((vi, vn))))
            if not (gi and gj):
                continue
            ab, ad, bc = self.do_dai(vi, vj), self.do_dai(vi, vp), self.do_dai(vj, vn)
            if thieu := [s for s, l in ((vi + vj, ab), (vi + vp, ad), (vj + vn, bc)) if not l]:
                raise TuChoi("MISSING_DIMENSION", f"đáy có góc vuông tại {vi}, {vj} nhưng chưa biết {thieu}", (gi, gj))
            r = _sqrt_q(sorted(bc)[0][0] / sorted(ad)[0][0])
            if r is None:
                raise TuChoi("UNSUPPORTED_IRRATIONAL_LAYOUT", f"{vj}{vn} : {vi}{vp} vô tỉ — chưa dựng đáy chính xác trong ℚ",
                             (gi, gj))
            o = Fraction(1)
            dat = {vi: (Z, Z), vj: (o, Z), vp: (Z, o), vn: (o, r)}
            dung = {gi, gj, *sorted(ab)[0][1], *sorted(ad)[0][1], *sorted(bc)[0][1]}
            return vong, tuple(dat[v] for v in vong), ((sorted(ab)[0][0], Z), (Z, sorted(ad)[0][0])), dung
        return None

    def _tam_giac(self, vong: tuple[str, ...]):
        """Ba cạnh² từ độ dài + góc vuông (Pythagore khi biết hai trong ba). Gram từ định lý cos (hữu tỉ)."""
        canh = {frozenset(p): None for p in ((vong[0], vong[1]), (vong[0], vong[2]), (vong[1], vong[2]))}
        dung: set[str] = set()
        for e in canh:
            if l := sorted(self.do_dai(*sorted(e))):
                canh[e] = l[0][0]
                dung |= set(l[0][1])
        for c in self.of("right_angle"):
            V, (X, Y) = c.args.vertex, c.args.rays
            if {V, X, Y} != set(vong):
                continue
            l1, l2, hy = frozenset((V, X)), frozenset((V, Y)), frozenset((X, Y))
            if canh[hy] is None and canh[l1] is not None and canh[l2] is not None:
                canh[hy] = canh[l1] + canh[l2]
                dung.add(c.id)
            elif canh[hy] is not None and (canh[l1] is None) != (canh[l2] is None):
                biet = l1 if canh[l1] is not None else l2
                con = canh[hy] - canh[biet]
                if con <= 0:
                    raise TuChoi("INCONSISTENT_FACTS", "cạnh huyền không dài hơn cạnh góc vuông", (c.id,))
                canh[l2 if biet == l1 else l1] = con
                dung.add(c.id)
        if any(v is None for v in canh.values()):
            raise TuChoi("MISSING_DIMENSION", "đáy tam giác chưa xác định đủ ba cạnh")
        d01, d02, d12 = (canh[frozenset((vong[0], vong[1]))], canh[frozenset((vong[0], vong[2]))],
                         canh[frozenset((vong[1], vong[2]))])
        m = (d01 + d02 - d12) / 2
        o = Fraction(1)
        return ((Z, Z), (o, Z), (Z, o)), ((d01, m), (m, d02)), dung

    # ── đặt điểm ────────────────────────────────────────────────────────────
    def _dat(self, ten: str, xyz: V3, luat: str, calls: set[str] | tuple, nguon: str = "LAYOUT_DERIVED") -> None:
        self.pts[ten] = xyz
        self.trace.append({"step": "place_point", "object": ten, "rule": luat, "calls": sorted(calls),
                           "provenance": nguon})

    def g(self, u: V3, v: V3) -> Fraction:
        G2, h2 = self.G2, self.h2 or Fraction(1)
        return (u[0] * (G2[0][0] * v[0] + G2[0][1] * v[1]) + u[1] * (G2[1][0] * v[0] + G2[1][1] * v[1])
                + u[2] * h2 * v[2])

    def d2(self, a: str, b: str) -> Fraction:
        u = tuple(self.pts[b][i] - self.pts[a][i] for i in range(3))
        return self.g(u, u)

    def trong_day(self, ten: str) -> bool:
        return ten in self.pts and self.pts[ten][2] == 0

    def _chieu_cao(self, dinh: str, chan: str, khoi_ten: list[str]) -> tuple[Fraction, set[str]]:
        """h² của đỉnh `dinh` có chân `chan` trong đáy — (a) độ dài đoạn đỉnh–chân, (b) chiều cao khối, (c) độ dài
        đỉnh tới một điểm khác trong đáy (Pythagore trong G). Thiếu cả ba ⇒ MISSING_DIMENSION."""
        if l := sorted(self.do_dai(dinh, chan)):
            return l[0][0], set(l[0][1])
        if h := sorted((binh_phuong(c.args.value), c.id) for c in self.of("height") if c.args.solid in khoi_ten):
            return h[0][0], {h[0][1]}
        for x in sorted(p for p in self.pts if self.trong_day(p) and p != chan):
            if l := sorted(self.do_dai(dinh, x)):
                u = tuple(self.pts[x][i] - self.pts[chan][i] for i in range(3))
                h2 = l[0][0] - self.g(u, u)
                if h2 <= 0:
                    raise TuChoi("INCONSISTENT_FACTS", f"{dinh}{x} không dài hơn khoảng cách từ chân {chan} tới {x}",
                                 tuple(l[0][1]))
                return h2, set(l[0][1])
        raise TuChoi("MISSING_DIMENSION", f"chưa có dữ kiện cho chiều cao của {dinh}")

    def _dat_ngoai_day(self, ten: str, chan: str | tuple, h2: Fraction, luat: str, calls: set[str]) -> None:
        """Đặt `ten` trên đường vuông góc đáy tại chân (`chan` = tên điểm đáy, hoặc toạ độ khung (x, y) dẫn xuất)."""
        if self.h2 is None:
            self.h2 = h2
            z = Fraction(1)
        elif (z := _sqrt_q(h2 / self.h2)) is None:
            raise TuChoi("UNSUPPORTED_MULTIPLE_HEIGHTS", "hai độ cao độc lập có tỉ số vô tỉ — chưa dựng chính xác được")
        f = self.pts[chan] if isinstance(chan, str) else chan
        self.dung |= calls
        self._dat(ten, (f[0], f[1], z), luat, calls)

    def giai_phu_thuoc(self) -> None:
        """Đặt mọi điểm còn lại theo thứ tự PHỤ THUỘC: mỗi vòng đặt MỘT điểm có luật áp được (ưu tiên cố định, thứ
        tự chính tắc), rồi bắt đầu lại — trace vì thế là một thứ tự topo hợp lệ và không đổi khi AI xáo lời gọi."""
        while True:
            if not self._mot_buoc():
                break
        can = set()
        for k in self.khoi.values():
            can |= set(k.base) | set(k.top) | ({k.apex} if k.apex else set())
        for c in self.calls:
            if c.spec.kind in ("fact", "ask", "construct") and c.fn != "height":
                can |= {x for x in _labels(c)}
        if thieu := sorted(can - set(self.pts)):
            raise TuChoi("UNDERDETERMINED_POINT",
                         f"không lời gọi nào xác định vị trí của {thieu} (thiếu quan hệ vuông góc / trung điểm / khối đều)",
                         data={"points": thieu})

    def _mot_buoc(self) -> bool:
        for c in self.of('intersection_line'):
            if c.id in self.line_refs and c.id not in self.lines and set(c.args.plane1+c.args.plane2) <= self.pts.keys():
                try:
                    with _metric.using(self.metric()):
                        planes = (self._plane(c.args.plane1),self._plane(c.args.plane2))
                        line = K.intersect_plane_plane(*planes)
                        verified = all(p.signed_eval(line.point)==0 and p.normal.dot(line.direction)==0 for p in planes)
                        if not verified:
                            raise TuChoi('ENGINE_SELF_CHECK_FAILED','giao tuyến không thuộc hai mặt',(c.id,))
                        self.lines[c.id]=line
                except GeometryError as e:
                    raise TuChoi(e.code,str(e),(c.id,)) from None
                sources = sorted(cid for cid,canonical in self.line_aliases.items() if canonical==c.id) or [c.id]
                self.trace.append({'step':'resolve_line','object':f'gt_{c.id}','producer':c.fn,'calls':sources,
                                   'dependencies':list(dict.fromkeys(c.args.plane1+c.args.plane2)),
                                   'provenance':'DERIVED','relation_verified':verified})
                return True
        for c in self.of("intersect_line_line", "intersect_line_plane", "orthogonal_projection_line", "orthogonal_projection",
                         "translate_point"):
            a = c.args
            p = a.point if c.fn.startswith("intersect") else a.image
            if c.fn in ("orthogonal_projection", "translate_point") and a.point == a.image:
                raise TuChoi("PRECONDITION_FAILED", f"{c.id}: ảnh trùng tên điểm đầu vào", (c.id,))
            if (p not in self.pts and all(v in self.pts for v in self._construction_dependencies(c))
                    and (not getattr(a,'line_ref',None) or a.line_ref in self.lines)):
                xyz = self._construct(c)
                self.constructions[p] = c
                self._dat(p, xyz, c.fn, {c.id}, "DERIVED")
                self.trace[-1].update(producer=c.fn, dependencies=list(self._construction_dependencies(c)),
                                      relation_verified=self._construction_relation(c))
                if getattr(a,'line_ref',None):
                    self.trace[-1]['dependencies'].append(f'gt_{a.line_ref}')
                    self.trace[-1]['result_binding'] = a.line_ref
                if not self.trace[-1]["relation_verified"]:
                    raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"{c.id}: quan hệ dựng không được thỏa", (c.id,))
                self.dung.add(c.id)
                return True
        for c in self.of("divide_segment"):
            p, (a, b), t = c.args.point, c.args.segment, Fraction(c.args.ratio)
            if p not in self.pts and a in self.pts and b in self.pts:
                self.divisions[p] = (a, b, t)
                self._dat(p, tuple((1 - t) * self.pts[a][i] + t * self.pts[b][i] for i in range(3)), f"divide_segment_t={t}",
                          {c.id}, "DERIVED")
                self.dung.add(c.id)
                return True
        for c in self.of("midpoint"):
            p, (a, b) = c.args.point, c.args.segment
            if p not in self.pts and a in self.pts and b in self.pts:
                self.midpoints[p] = (a, b)
                self._dat(p, tuple((self.pts[a][i] + self.pts[b][i]) / 2 for i in range(3)), "midpoint", {c.id},
                          "DERIVED")
                self.dung.add(c.id)
                return True
        for k in sorted(self.khoi.values(), key=lambda k: k.name):
            if k.kind == "pyramid" and k.regular and k.apex not in self.pts:
                if frozenset(k.base) != frozenset(self.root.base):
                    continue  # Derived solids consume known vertices; they never seed another chart or choose an apex.
                reg = [c for c in self.of("regular_polygon") if frozenset(c.args.vertices) == frozenset(k.base)]
                if not reg:
                    raise TuChoi("REGULAR_PYRAMID_NEEDS_REGULAR_BASE", f"chóp đều {k.name} nhưng đáy chưa được khai là đa giác đều",
                                 (k.call,))
                if self.tam is None:
                    self.tam = next(t for t in ("O", "I", "O1", "O2") if t not in self.text_labels and t not in self.pts)
                    n = len(k.base)
                    self._dat(self.tam, tuple(sum(self.pts[v][i] for v in k.base) / n for i in range(3)),
                              "center_of_regular_base", {k.call, reg[0].id}, "DERIVED")
                h2, cs = self._chieu_cao(k.apex, self.tam, [k.name])
                self._dat_ngoai_day(k.apex, self.tam, h2, "apex_over_center", {k.call, reg[0].id} | cs)
                return True
        for c in self.of("centroid"):
            p, da = c.args.point, c.args.polygon
            if len(da) != 3:
                raise TuChoi("UNSUPPORTED_CENTROID", f"{c.id}: bản này dựng trọng tâm TAM GIÁC", (c.id,))
            if p not in self.pts and all(v in self.pts for v in da):
                self.centroids[p] = tuple(da)
                self._dat(p, tuple(sum(self.pts[v][i] for v in da) / 3 for i in range(3)), "centroid_of_triangle", {c.id},
                          "DERIVED")
                self.dung.add(c.id)
                return True
        for c, (a, b), mp, luat, chan_khai in self._rang_buoc_vuong():
            if c.fn == "orthogonal_projection" and (c.args.point in self.pts or c.args.image not in self.pts):
                continue  # forward construction waits for all plane operands; never infer its input
            if not (set(mp) <= set(self.pts) and all(self.trong_day(v) for v in mp)):
                if set(mp) <= set(self.pts) or not (set(mp) & set(self.pts)):
                    continue
                raise TuChoi("UNSUPPORTED_PLANE", f"{c.id}: mặt phẳng {sorted(mp)} không phải mặt đáy đã dựng", (c.id,))
            if chan_khai is not None:                          # đường cao / hình chiếu: CHÂN do chính lời gọi nêu
                chan, dinh = chan_khai, (a if b == chan_khai else b)
                if chan not in self.pts or dinh in self.pts:
                    continue                                   # chân chưa dựng ⇒ đợi; đỉnh đã có ⇒ chỉ còn kiểm
                if not self.trong_day(chan):
                    raise TuChoi("FOOT_NOT_IN_PLANE", f"{c.id}: chân {chan} không nằm trên mặt {''.join(mp)}", (c.id,))
            else:
                chan, dinh = ((a, b) if self.trong_day(a) and b not in self.pts else
                              (b, a) if self.trong_day(b) and a not in self.pts else (None, None))
                if chan is None:
                    if a in self.pts and b in self.pts:
                        continue                               # đã dựng ⇒ chỉ còn là dữ kiện để kiểm
                    if (a in self.pts and not self.trong_day(a)) or (b in self.pts and not self.trong_day(b)):
                        raise TuChoi("FOOT_NOT_DETERMINED", f"{c.id}: không đầu nào của {a}{b} nằm trên mặt đáy", (c.id,))
                    continue                                   # chân chưa dựng (vd trung điểm chưa có) ⇒ đợi
            ten_khoi = [k.name for k in self.khoi.values() if k.apex == dinh and frozenset(k.base) == frozenset(self.root.base)]
            h2, cs = self._chieu_cao(dinh, chan, ten_khoi)
            self._dat_ngoai_day(dinh, chan, h2, luat + chan, {c.id} | cs)
            return True
        if self._hai_duong_cat_nhau():
            return True
        if self._mat_ben_vuong_goc_day():
            return True
        for k in sorted(self.khoi.values(), key=lambda k: k.name):
            if k.kind == "prism" and k.right and any(t not in self.pts for t in k.top) and all(b in self.pts for b in k.base):
                h2, cs = self._chieu_cao_lang_tru(k)
                for i, (b, t) in enumerate(zip(k.base, k.top)):
                    if i == 0:
                        self._dat_ngoai_day(t, b, h2, "right_prism_translate", {k.call} | cs)
                    else:
                        f = self.pts[b]
                        self._dat(t, (f[0], f[1], self.pts[k.top[0]][2]), "right_prism_translate", {k.call} | cs)
                return True
        # Any prism (oblique included): once the base is placed and ONE top vertex is fixed by the facts (projection, an
        # edge), every other top vertex is its base vertex + that same lateral vector — the definition of a prism, exact in
        # ℚ³. The prism fact check (`_dung_khong`: one vector for all pairs) still verifies a top vertex placed otherwise.
        for k in sorted(self.khoi.values(), key=lambda k: k.name):
            if k.kind != "prism" or not all(b in self.pts for b in k.base):
                continue
            biet = [(b, t) for b, t in zip(k.base, k.top) if t in self.pts]
            if biet and len(biet) < len(k.top):
                b0, t0 = biet[0]
                v = tuple(self.pts[t0][i] - self.pts[b0][i] for i in range(3))
                if v[2] == 0:
                    raise TuChoi("INCONSISTENT_FACTS", f"{k.name}: đỉnh {t0} nằm trên mặt đáy — lăng trụ suy biến", (k.call,))
                b, t = next((b, t) for b, t in zip(k.base, k.top) if t not in self.pts)
                self._dat(t, tuple(self.pts[b][i] + v[i] for i in range(3)), f"prism_lateral_vector_{b0}{t0}", {k.call},
                          "DERIVED")
                return True
        return False

    def _rang_buoc_vuong(self):
        """CHUẨN HOÁ ba cách nói về một đường vuông góc mặt phẳng thành MỘT ràng buộc (lời gọi, đường, mặt, luật, chân):
        `perpendicular_line_plane` (chân = đầu mút nằm trên mặt); `altitude` (TIỀN ĐIỀU KIỆN: đỉnh là đỉnh của chính khối
        chóp được nêu, mặt = đáy khối ấy, chân = `foot` phải nằm trên đáy); `orthogonal_projection` (TIỀN ĐIỀU KIỆN: ảnh ≠
        điểm, ảnh nằm trên mặt). Tiền điều kiện hỏng ⇒ từ chối có mã — không suy diễn quan hệ khi ngữ cảnh không chứng minh."""
        for c in self.of("perpendicular_line_plane"):
            yield c, tuple(c.args.line), list(c.args.plane), "perpendicular_foot_at_", None
        for c in self.of("altitude"):
            k = self.khoi.get(c.args.solid)
            if k is None:
                raise TuChoi("UNKNOWN_SOLID", f"{c.id}: khối {c.args.solid} chưa được dựng bằng lời gọi nào", (c.id,))
            if k.kind != "pyramid" or k.apex != c.args.apex or c.args.foot == c.args.apex:
                raise TuChoi("PRECONDITION_FAILED", f"{c.id}: đường cao phải hạ từ ĐỈNH của khối chóp {k.name}", (c.id,))
            yield c, (c.args.apex, c.args.foot), list(k.base), "altitude_normalized_to_perpendicular_foot_at_", c.args.foot
        for c in self.of("orthogonal_projection"):
            if c.args.point == c.args.image:
                raise TuChoi("PRECONDITION_FAILED", f"{c.id}: hình chiếu trùng chính điểm — không xác định đường vuông góc", (c.id,))
            yield (c, (c.args.point, c.args.image), list(c.args.plane),
                   "orthogonal_projection_normalized_to_perpendicular_foot_at_", c.args.image)

    def _hai_duong_cat_nhau(self) -> bool:
        """ĐỊNH LÝ: PQ ⊥ hai đường (không song song) nằm trong đáy và Q thuộc đáy ⇒ PQ ⊥ đáy, chân Q. Một đường vuông
        góc thôi KHÔNG đủ — đỉnh để nguyên chưa xác định."""
        dau = {x for c in self.of("perpendicular_lines") for l in (c.args.line1, c.args.line2) for x in l}
        for p in sorted(dau - set(self.pts)):
            theo_chan: dict[str, list] = {}
            for c in self.of("perpendicular_lines"):
                for L, M in ((c.args.line1, c.args.line2), (c.args.line2, c.args.line1)):
                    if p in L and L[0] != L[1]:
                        q = L[1] if L[0] == p else L[0]
                        if self.trong_day(q) and all(self.trong_day(m) for m in M):
                            theo_chan.setdefault(q, []).append(
                                (tuple(self.pts[M[1]][i] - self.pts[M[0]][i] for i in range(2)), c.id))
            for q, ds in sorted(theo_chan.items()):
                for (d1, c1), (d2, c2) in combinations(ds, 2):
                    if d1[0] * d2[1] - d1[1] * d2[0] != 0:
                        h2, cs = self._chieu_cao(p, q, [k.name for k in self.khoi.values()
                                                        if k.apex == p and frozenset(k.base) == frozenset(self.root.base)])
                        self._dat_ngoai_day(p, q, h2, "line_perpendicular_to_two_intersecting_lines_foot_at_" + q,
                                            {c1, c2} | cs)
                        return True
        return False

    def _mat_ben_vuong_goc_day(self) -> bool:
        """(SAB) ⊥ đáy, A, B trên đáy: S nằm trong mặt phẳng qua AB vuông góc đáy. Chân F = hình chiếu của S lên AB —
        DẪN XUẤT từ SA², SB², AB² (t = (SA² − SB² + AB²)/2AB²), KHÔNG giả định là trung điểm; h² = SA² − t²AB²."""
        for c in self.of("face_perpendicular_base"):
            k = self.root                      # the sole root base, not whichever solid sorts first (review 2)
            if frozenset(c.args.base) != frozenset(k.base):
                raise TuChoi("UNSUPPORTED_PLANE", f"{c.id}: mặt {''.join(c.args.base)} không phải mặt đáy đã dựng", (c.id,))
            ngoai = [v for v in c.args.face if v not in k.base]
            if len(ngoai) != 1:
                raise TuChoi("PRECONDITION_FAILED", f"{c.id}: mặt bên phải gồm đúng một đỉnh ngoài đáy và một cạnh đáy", (c.id,))
            s = ngoai[0]
            A, B = [v for v in c.args.face if v != s]
            if s in self.pts or not (self.trong_day(A) and self.trong_day(B)):
                continue
            la, lb = sorted(self.do_dai(s, A)), sorted(self.do_dai(s, B))
            if not la or not lb:
                raise TuChoi("MISSING_DIMENSION", f"{c.id}: mặt ({s}{A}{B}) ⊥ đáy nhưng chưa biết {s}{A} và {s}{B}", (c.id,))
            ab2 = self.d2(A, B)
            t = (la[0][0] - lb[0][0] + ab2) / (2 * ab2)
            h2 = la[0][0] - t * t * ab2
            if h2 <= 0:
                raise TuChoi("INCONSISTENT_FACTS", f"{c.id}: tam giác {s}{A}{B} suy biến với các độ dài đã cho",
                             (c.id, *la[0][1], *lb[0][1]))
            chan = tuple(self.pts[A][i] + t * (self.pts[B][i] - self.pts[A][i]) for i in range(2))
            self._dat_ngoai_day(s, chan, h2, f"face_perpendicular_base_foot_on_{A}{B}_t={t}",
                                {c.id, *la[0][1], *lb[0][1]})
            return True
        return False

    def _chieu_cao_lang_tru(self, k: _Khoi) -> tuple[Fraction, set[str]]:
        if h := sorted((binh_phuong(c.args.value), c.id) for c in self.of("height") if c.args.solid == k.name):
            return h[0][0], {h[0][1]}
        for b, t in sorted(zip(k.base, k.top)):
            if l := sorted(self.do_dai(b, t)):
                return l[0][0], set(l[0][1])
        raise TuChoi("MISSING_DIMENSION", f"lăng trụ {k.name} chưa có chiều cao hay cạnh bên", (k.call,))

    # ── kiểm lại MỌI dữ kiện trên bố cục ────────────────────────────────────
    def _construction_dependencies(self, c: LoiGoi) -> tuple[str, ...]:
        a = c.args
        if c.fn == "intersect_line_line":
            pts = a.line1 + a.line2
        elif c.fn == "intersect_line_plane":
            pts = a.line + a.plane
        elif c.fn == "orthogonal_projection_line":
            pts = [a.point] + (a.line or [])
        elif c.fn == "translate_point":
            pts = [a.point] + a.vector
        else:
            pts = [a.point] + a.plane
        return tuple(dict.fromkeys(pts))

    def _line(self, labels) -> Line3:
        return Line3.through(*(Vec3(*self.pts[p]) for p in labels))

    def kiem_mat_viet(self, nhom: list[list[str]]) -> None:
        """Nhóm nhãn mặt phẳng nguồn phải không suy biến và đồng phẳng trên hình đã dựng (chính xác).
        Cùng `_cung_mat`, phép kiểm này không cho rút gọn một nhóm nguồn sai thành mặt ba nhãn."""
        # Các nhãn dư trong lời gọi cũng phải thuộc cùng mặt, kể cả hàm góc chỉ phát ba nhãn đầu vào IR.
        nhom = [*nhom, *(g for c in self.calls for key in ("plane", "plane1", "plane2")
                         if (g := getattr(c.args, key, None)) is not None)]
        for g in nhom:
            if any(p not in self.pts for p in g):
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"({''.join(g)}) có nhãn chưa được dựng — không kiểm được là một mặt phẳng")
            v = [Vec3(*self.pts[p]) for p in g]
            ba = next(((a, b, c) for a, b, c in combinations(v, 3) if not (b - a).cross(c - a).is_zero()), None)
            if ba is None or any(Plane3.through(*ba).signed_eval(p) != 0 for p in v):
                raise TuChoi("SOURCE_OBJECT_MISMATCH", f"({''.join(g)}) không phải một mặt phẳng của hình — "
                             "không đọc nó thành mặt ba nhãn")

    def _plane(self, labels) -> Plane3:
        plane = Plane3.through(*(Vec3(*self.pts[p]) for p in labels[:3]))
        if any(plane.signed_eval(Vec3(*self.pts[p])) != 0 for p in labels[3:]):
            raise GeometryError("NON_COPLANAR_POINTS", "các điểm không cùng nằm trong một mặt phẳng")
        return plane

    def _construction_objects(self, c: LoiGoi):
        a = c.args
        if c.fn == "intersect_line_line":
            x, y = self._line(a.line1), self._line(a.line2)
            # Kernel's historic parallel code also covers skew; classify exactly here.
            if (y.point - x.point).dot(x.direction.cross(y.direction)) != 0:
                raise GeometryError("SKEW_NO_INTERSECTION", "hai đường chéo nhau không có giao điểm")
            return x, y
        if c.fn == "intersect_line_plane":
            return self._line(a.line), self._plane(a.plane)
        if c.fn == "translate_point":
            return Vec3(*self.pts[a.point]), Vec3(*self.pts[a.vector[1]]) - Vec3(*self.pts[a.vector[0]])
        return Vec3(*self.pts[a.point]), ((self.lines[a.line_ref] if a.line_ref else self._line(a.line))
                                        if c.fn.endswith("_line") else self._plane(a.plane))

    def _construct(self, c: LoiGoi) -> V3:
        try:
            with _metric.using(self.metric()):
                x, y = self._construction_objects(c)
                fn = {"intersect_line_line": K.intersect_line_line, "intersect_line_plane": K.intersect_line_plane,
                      "orthogonal_projection_line": K.project_point_onto_line,
                      "orthogonal_projection": K.project_point_onto_plane, "translate_point": K.translate}[c.fn]
                p = fn(x, y)
                return p.x, p.y, p.z
        except GeometryError as e:
            raise TuChoi(e.code, str(e), (c.id,)) from None

    def _construction_relation(self, c: LoiGoi) -> bool:
        """Independent incidence/orthogonality checks, not equality to a repeated kernel call."""
        try:
            with _metric.using(self.metric()):
                x, y = self._construction_objects(c)
                a = c.args
                p = Vec3(*self.pts[a.point if c.fn.startswith("intersect") else a.image])
                if c.fn == "translate_point":               # hình bình hành: X + B = M + A (không lặp lại phép cộng vectơ)
                    m, u, v = (self.pts[a.point], self.pts[a.vector[0]], self.pts[a.vector[1]])
                    return all(self.pts[a.image][i] + u[i] == m[i] + v[i] for i in range(3))
                if c.fn == "intersect_line_line":
                    return (not x.direction.cross(y.direction).is_zero() and point_on_line(p, x) and point_on_line(p, y))
                if c.fn == "intersect_line_plane":
                    return x.direction.dot(y.normal) != 0 and point_on_line(p, x) and y.signed_eval(p) == 0
                if c.fn.endswith("_line"):
                    return point_on_line(p, y) and _metric.dot(x - p, y.direction) == 0
                d = x - p
                return y.signed_eval(p) == 0 and all(self.g((d.x, d.y, d.z), self._vec(a.plane[0], v)) == 0 for v in a.plane[1:])
        except GeometryError as e:
            raise TuChoi(e.code, str(e), (c.id,)) from None

    def kiem(self) -> None:
        # Establish a real, coplanar base before any Gram distance divides by its area.
        for k in self.khoi.values():
            try:
                self._plane(k.base)
            except GeometryError as e:
                raise TuChoi(e.code, str(e), (k.call,)) from None
        hong = [c for c in self.calls if not self._dung_khong(c)]
        tu_hong = [c for c in hong if c.id in self.dung]
        if tu_hong:
            raise TuChoi("ENGINE_SELF_CHECK_FAILED", "bố cục engine vi phạm chính dữ kiện nó đã dùng: "
                         + "; ".join(f"{c.id} {c.quote!r}" for c in tu_hong), tuple(c.id for c in tu_hong))
        if hong:
            raise TuChoi("INCONSISTENT_FACTS", "dữ kiện mâu thuẫn với phần còn lại của đề: "
                         + "; ".join(f"{c.id} {c.quote!r}" for c in hong), tuple(c.id for c in hong))
        self.volume_certificates = {}
        self.ratio_certificates: dict[str, Fraction] = {}
        self.residual_certificates: dict[str, Fraction] = {}
        if self.composite or self.of("ask_volume_ratio", "ask_residual_volume"):
            from app.simulation.geometry.section import Polyhedron, kiem_mat_phang_don
            for k in self.khoi.values():
                if k.kind == "pyramid":
                    labels = [k.apex, *k.base]
                    faces = P.construct_pyramid("solid", k.apex, k.base)["faces"]
                    rule = "gram_base_area_squared_times_height_squared_over_9"
                else:
                    labels = [*k.base, *k.top]
                    faces = P.construct_prism("solid", k.base, k.top, tuple((b, t) for b, t in zip(k.base, k.top)))["faces"]
                    rule = "gram_base_area_squared_times_height_squared"
                try:
                    kiem_mat_phang_don(Polyhedron(tuple(Vec3(*self.pts[p]) for p in labels),
                                                 tuple(tuple(labels.index(p) for p in face) for face in faces)))
                except GeometryError as e:
                    raise TuChoi(e.code, str(e), (k.call,)) from None
                v2 = self._the_tich2_khoi(k)
                if v2 <= 0:
                    raise TuChoi("DEGENERATE_SOLID", f"khối {k.name} có thể tích bằng 0 (suy biến)", (k.call,))
                self.volume_certificates[k.name] = v2
                self.trace.append({"step": "verify_solid", "object": k.name, "rule": rule,
                                   "calls": [k.call], "provenance": "DERIVED", "volume_squared": str(v2),
                                   "dependencies": labels, "base_coplanar": True})
            for c in self.of("ask_volume_ratio"):
                num_s, den_s = c.args.numerator_solid, c.args.denominator_solid
                if num_s == den_s:
                    raise TuChoi("UNSUPPORTED_VOLUME_RATIO", f"{c.id}: tỉ số thể tích cần hai khối phân biệt", (c.id,))
                v2_num, v2_den = self.volume_certificates[num_s], self.volume_certificates[den_s]
                ratio = _sqrt_q(v2_num / v2_den)
                if ratio is None or ratio <= 0:
                    raise TuChoi("UNSUPPORTED_VOLUME_RATIO", f"{c.id}: tỉ số thể tích giữa {num_s} và {den_s} không hữu tỉ dương", (c.id,))
                self.ratio_certificates[c.id] = ratio
                self.trace.append({
                    "step": "certify_volume_ratio", "object": c.id, "rule": "exact_gram_volume_ratio_certificate",
                    "calls": [c.id, self.khoi[num_s].call, self.khoi[den_s].call], "provenance": "DERIVED",
                    "numerator_solid": num_s, "denominator_solid": den_s,
                    "numerator_volume_squared": str(v2_num), "denominator_volume_squared": str(v2_den),
                    "ratio": str(ratio),
                })
            for c in self.of("ask_residual_volume"):
                self._kiem_phan_con_lai(c)

    def _the_tich2_chop(self, k: _Khoi) -> Fraction:
        """Independent of the interpreter's oriented boundary-volume sum: Gram base area × altitude / 3, squared."""
        u, v = self._vec(k.base[0], k.base[1]), self._vec(k.base[0], k.base[2])
        i, j = next((i, j) for i, j in combinations(range(3), 2) if u[i] * v[j] != u[j] * v[i])
        proj = sum(self.pts[a][i] * self.pts[b][j] - self.pts[a][j] * self.pts[b][i]
                   for a, b in zip(k.base, (*k.base[1:], k.base[0])))
        scale = proj / (u[i] * v[j] - u[j] * v[i])
        area2 = (self.g(u, u) * self.g(v, v) - self.g(u, v) ** 2) * scale ** 2 / 4
        return (area2 * self._kc2_mat(k.apex, k.base[:3]) / 9 if k.kind == "pyramid"
                else area2 * self._kc2_mat(k.top[0], k.base[:3]))

    def _the_tich2_khoi(self, k: _Khoi) -> Fraction:
        """Exact Gram-metric volume squared for a pyramid (`S_base² · h² / 9`) or prism (`S_base² · h²`), independent of IR execution."""
        return self._the_tich2_chop(k)

    def _mat_ngoai_khoi(self, k: _Khoi):
        labels = [k.apex, *k.base] if k.kind == "pyramid" else [*k.base, *k.top]
        faces = (P.construct_pyramid("solid", k.apex, k.base)["faces"] if k.kind == "pyramid"
                 else P.construct_prism("solid", k.base, k.top, tuple((b, t) for b, t in zip(k.base, k.top)))["faces"])
        planes: list[tuple[V3, Fraction]] = []
        edges: set[tuple[str, str]] = set()
        for face in faces:
            for i in range(len(face)):
                a_e, b_e = face[i], face[(i + 1) % len(face)]
                if (b_e, a_e) not in edges:
                    edges.add((a_e, b_e))
            u, v = self._vec(face[0], face[1]), self._vec(face[0], face[2])
            n = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            p0 = self.pts[face[0]]
            d = n[0] * p0[0] + n[1] * p0[1] + n[2] * p0[2]
            off = [n[0] * self.pts[x][0] + n[1] * self.pts[x][1] + n[2] * self.pts[x][2] - d for x in labels if x not in face]
            if not off or any(val == 0 for val in off) or ({val > 0 for val in off} == {True, False}):
                raise TuChoi("DEGENERATE_SOLID", f"khối {k.name} có mặt không lồi hoặc suy biến", (k.call,))
            if off[0] > 0:
                n, d = (-n[0], -n[1], -n[2]), -d
            planes.append((n, d))
        return labels, faces, planes, tuple(edges)

    def _kiem_phan_con_lai(self, c: LoiGoi) -> None:
        orig = self.khoi[c.args.original_solid]
        subs = [self.khoi[s] for s in c.args.subtracted_solids]
        _, _, orig_planes, _ = self._mat_ngoai_khoi(orig)
        v2_orig = self.volume_certificates[orig.name]
        sub_data = [self._mat_ngoai_khoi(sk) for sk in subs]
        sum_r = Fraction(0)
        for sk, (s_labels, s_faces, _s_planes, _s_edges) in zip(subs, sub_data):
            if sk.name == orig.name:
                raise TuChoi("NON_POSITIVE_RESIDUAL_VOLUME", f"{c.id}: không thể cắt bỏ chính khối gốc {orig.name}", (c.id,))
            for v_lb in s_labels:
                pt = self.pts[v_lb]
                if any(n[0] * pt[0] + n[1] * pt[1] + n[2] * pt[2] - d > 0 for n, d in orig_planes):
                    raise TuChoi("RESIDUAL_CONTAINMENT_UNPROVED",
                                 f"{c.id}: đỉnh {v_lb} của khối {sk.name} nằm ngoài khối gốc {orig.name}", (c.id,))
            if not any(
                all(n[0] * self.pts[v_lb][0] + n[1] * self.pts[v_lb][1] + n[2] * self.pts[v_lb][2] - d == 0 for v_lb in sf)
                for sf in s_faces for n, d in orig_planes
            ):
                raise TuChoi("RESIDUAL_CONTAINMENT_UNPROVED",
                             f"{c.id}: khối cắt bỏ {sk.name} không chung mặt biên với khối gốc {orig.name}", (c.id,))
            r_i = _sqrt_q(self.volume_certificates[sk.name] / v2_orig)
            if r_i is None or r_i <= 0:
                raise TuChoi("RESIDUAL_CONTAINMENT_UNPROVED",
                             f"{c.id}: tỉ lệ thể tích khối cắt bỏ {sk.name} không hữu tỉ dương", (c.id,))
            sum_r += r_i
        for i in range(len(subs)):
            la, _, pa, ea = sub_data[i]
            pts_a = [self.pts[x] for x in la]
            for j in range(i + 1, len(subs)):
                lb, _, pb, eb = sub_data[j]
                pts_b = [self.pts[x] for x in lb]
                sep = (
                    any(all(n[0] * p[0] + n[1] * p[1] + n[2] * p[2] - d >= 0 for p in pts_b) for n, d in pa)
                    or any(all(n[0] * p[0] + n[1] * p[1] + n[2] * p[2] - d >= 0 for p in pts_a) for n, d in pb)
                )
                if not sep:
                    for u1, u2 in ea:
                        du = self._vec(u1, u2)
                        p0 = self.pts[u1]
                        for v1, v2 in eb:
                            dv = self._vec(v1, v2)
                            n = (du[1] * dv[2] - du[2] * dv[1], du[2] * dv[0] - du[0] * dv[2], du[0] * dv[1] - du[1] * dv[0])
                            if n == (Z, Z, Z):
                                continue
                            d = n[0] * p0[0] + n[1] * p0[1] + n[2] * p0[2]
                            va = [n[0] * p[0] + n[1] * p[1] + n[2] * p[2] - d for p in pts_a]
                            vb = [n[0] * p[0] + n[1] * p[1] + n[2] * p[2] - d for p in pts_b]
                            if (all(x <= 0 for x in va) and all(y >= 0 for y in vb)) or (all(x >= 0 for x in va) and all(y <= 0 for y in vb)):
                                sep = True
                                break
                        if sep:
                            break
                if not sep:
                    raise TuChoi("OVERLAPPING_SUBTRACTED_SOLIDS",
                                 f"{c.id}: hai khối cắt bỏ {subs[i].name} và {subs[j].name} có phần trong giao nhau", (c.id,))
        rem_frac = Fraction(1) - sum_r
        if rem_frac <= 0:
            raise TuChoi("NON_POSITIVE_RESIDUAL_VOLUME",
                         f"{c.id}: tổng thể tích cắt bỏ không nhỏ hơn thể tích khối gốc {orig.name}", (c.id,))
        v2_res = rem_frac * rem_frac * v2_orig
        self.residual_certificates[c.id] = v2_res
        self.trace.append({
            "step": "certify_residual_volume", "object": c.id,
            "rule": "exact_halfspace_containment_and_sat_disjointness_certificate",
            "calls": [c.id, orig.call, *(sk.call for sk in subs)], "provenance": "DERIVED",
            "original_solid": orig.name, "subtracted_solids": [sk.name for sk in subs],
            "containment_verified": True, "shared_boundary_verified": True,
            "disjoint_interiors_verified": True, "positive_residual_verified": True,
            "residual_fraction": str(rem_frac), "residual_volume_squared": str(v2_res),
        })

    def _vec(self, a: str, b: str) -> V3:
        return tuple(self.pts[b][i] - self.pts[a][i] for i in range(3))

    def _kc2_mat(self, p: str, mp: tuple[str, ...]) -> Fraction:
        """Khoảng cách² từ p tới mặt (mp[0], mp[1], mp[2]) theo G: det Gram(u,v,w) / det Gram(u,v)."""
        u, v, w = self._vec(mp[0], mp[1]), self._vec(mp[0], mp[2]), self._vec(mp[0], p)
        M = [[self.g(x, y) for y in (u, v, w)] for x in (u, v, w)]
        d3 = (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1]) - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
              + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))
        return d3 / (M[0][0] * M[1][1] - M[0][1] * M[1][0])

    def _canh_da_giac_deu(self, v) -> Fraction | None:
        """Exact Gram check: equal sides and equal distance to the vertex centroid ⇒ regular polygon; side² or None."""
        n = len(v)
        canh = {self.d2(v[i], v[(i + 1) % n]) for i in range(n)}
        O = tuple(sum(self.pts[x][i] for x in v) / n for i in range(3))
        r = {self.g(*(tuple(self.pts[x][i] - O[i] for i in range(3)),) * 2) for x in v}
        if len(canh) != 1 or len(r) != 1 or canh == {Z}:
            return None
        # Planar too: a regular tetrahedron's SABC has equal sides and centroid distances but is skew (review 2).
        u, w = self._vec(v[0], v[1]), self._vec(v[0], v[2])
        if self.g(u, u) * self.g(w, w) - self.g(u, w) ** 2 == 0 or any(self._kc2_mat(x, v[:3]) != 0 for x in v[3:]):
            return None
        return next(iter(canh))

    def _dung_khong(self, c: LoiGoi) -> bool:
        a = c.args
        if c.fn in ("intersect_line_line", "intersect_line_plane", "orthogonal_projection_line", "translate_point"):
            return self._construction_relation(c)
        if c.fn == "orthogonal_projection" and c.args.point in self.pts:
            return self._construction_relation(c)
        if c.fn == "segment_length":
            return self.d2(*a.segment) == binh_phuong(a.value)
        if c.fn == "regular_polygon":
            canh = self._canh_da_giac_deu(a.vertices)
            return canh is not None and (a.side is None or canh == binh_phuong(a.side))
        if c.fn == "rectangle":
            v = a.vertices
            return all(self.g(self._vec(v[i], v[(i + 1) % 4]), self._vec(v[i], v[(i - 1) % 4])) == 0 for i in range(4))
        if c.fn == "right_angle":
            return self.g(self._vec(a.vertex, a.rays[0]), self._vec(a.vertex, a.rays[1])) == 0
        if c.fn == "perpendicular_line_plane":
            d, mp = self._vec(*a.line), a.plane
            return all(self.g(d, self._vec(mp[0], x)) == 0 for x in mp[1:])
        if c.fn == "midpoint":
            p, (x, y) = a.point, a.segment
            return all(2 * self.pts[p][i] == self.pts[x][i] + self.pts[y][i] for i in range(3))
        if c.fn == "centroid":
            return all(3 * self.pts[a.point][i] == sum(self.pts[v][i] for v in a.polygon) for i in range(3))
        if c.fn == "divide_segment":
            t, (x, y) = Fraction(a.ratio), a.segment
            return all(self.pts[a.point][i] == (1 - t) * self.pts[x][i] + t * self.pts[y][i] for i in range(3))
        if c.fn == "equal_length":
            return self.d2(*a.segment_a) == self.d2(*a.segment_b)
        if c.fn == "perpendicular_lines":
            return self.g(self._vec(*a.line1), self._vec(*a.line2)) == 0
        if c.fn in ("altitude", "orthogonal_projection"):
            if c.fn == "altitude":
                k = self.khoi[a.solid]
                dinh, chan, mp = a.apex, a.foot, k.base
            else:
                dinh, chan, mp = a.point, a.image, a.plane
            d = self._vec(chan, dinh)
            return (self._kc2_mat(chan, mp[:3]) == 0 and self._kc2_mat(dinh, mp[:3]) > 0
                    and all(self.g(d, self._vec(mp[0], x)) == 0 for x in mp[1:]))
        if c.fn == "face_perpendicular_base":
            def phap(m):                                     # covector của mặt (tích có hướng trong khung)
                u, v = self._vec(m[0], m[1]), self._vec(m[0], m[2])
                return Vec3(u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
            n1, n2 = phap(a.face), phap(a.base)
            return self.metric().vector(n2).dot(n1) == 0     # hai mặt ⊥ ⇔ n₁ᵀ G⁻¹ n₂ = 0
        if c.fn == "height":
            k = self.khoi[a.solid]
            dinh = k.apex if k.kind == "pyramid" else k.top[0]
            return self._kc2_mat(dinh, k.base[:3]) == binh_phuong(a.value)
        if c.fn in ("pyramid", "regular_pyramid"):
            k = self.khoi[a.apex + "." + "".join(a.base)]
            ok = self._kc2_mat(k.apex, k.base[:3]) > 0
            if c.fn == "regular_pyramid":
                # Regular = REGULAR base + equal lateral edges (⇒ foot at the base centre). Equal lateral edges alone
                # only put the foot at a circumcentre: a non-square rectangle passes that test (review blocker).
                ok = (ok and self._canh_da_giac_deu(k.base) is not None
                      and len({self.d2(k.apex, b) for b in k.base}) == 1)
            return ok
        if c.fn == "prism":
            vec = {self._vec(b, t) for b, t in zip(a.base, a.top)}
            ok = len(vec) == 1 and next(iter(vec))[2] != 0
            if a.right:
                d = next(iter(vec))
                ok = ok and all(self.g(d, self._vec(a.base[0], x)) == 0 for x in a.base[1:])
            return ok
        return True                                             # ask_* / unsupported: không phải dữ kiện

    # ── IR ──────────────────────────────────────────────────────────────────
    def bien_dich(self) -> tuple[dict[str, Any], dict[str, str]]:
        self.emitted_lines: set[str] = set()
        so_huu: set[str] = set()                 # operand lines / planes this compiler names itself (`gop_doi_tuong_trung`)
        khai: list[dict[str, Any]] = []
        lenh: list[dict[str, Any]] = []
        khoi_diem: list[tuple[str, list[dict[str, Any]], list[dict[str, Any]]]] = []
        for s in self.trace:
            if s["step"] != "place_point":
                continue
            t = s["object"]
            lenh, khai = [], []          # one block per point: its statements + declarations (moved as a unit)
            khoi_diem.append((ir_name(t), lenh, khai))
            if t in self.constructions:
                c = self.constructions[t]
                a = c.args
                prefix = "derived_" + ir_name(t)
                def line(suffix, labels):
                    name = prefix + suffix
                    lenh.append(P.construct_line(name, *map(ir_name, labels)))
                    khai.append(P.memory_declaration(name, "line3"))
                    so_huu.add(name)
                    return name
                def plane(labels):
                    name = prefix + "_plane"
                    lenh.append({"kind": "construct_plane", "target_var": name, "through": list(map(ir_name, labels[:3]))})
                    khai.append(P.memory_declaration(name, "plane3"))
                    so_huu.add(name)
                    return name
                if c.fn == "intersect_line_line":
                    expr = {"kind": c.fn, "line_a": line("_line1", a.line1), "line_b": line("_line2", a.line2)}
                elif c.fn == "intersect_line_plane":
                    expr = {"kind": c.fn, "line": line("_line", a.line), "plane": plane(a.plane)}
                elif c.fn == "translate_point":               # IR's own expression: vector_from_points, then translate
                    vec = prefix + "_vec"
                    lenh.append({"kind": "assign", "target_var": vec, "expr": {
                        "kind": "vector_from_points", "from_point": ir_name(a.vector[0]), "to_point": ir_name(a.vector[1])}})
                    khai.append(P.memory_declaration(vec, "vector3"))
                    expr = {"kind": "translate", "point": ir_name(a.point), "vector": vec}
                else:
                    if c.fn.endswith('_line') and a.line_ref:
                        producer = next(c for c in self.calls if c.id==a.line_ref)
                        target = self._emit_intersection(producer,khai,lenh)
                    else:
                        target = line("_line", a.line) if c.fn.endswith("_line") else plane(a.plane)
                    expr = {"kind": "project_onto", "point": ir_name(a.point), "target": target}
                lenh.append({"kind": "construct_point", "target_var": ir_name(t), "label": t, "expr": expr})
                khai.append(P.memory_declaration(ir_name(t), "point3"))
            elif t in self.midpoints:
                a, b = self.midpoints[t]
                lenh.append({"kind": "construct_point", "target_var": ir_name(t), "label": t,
                             "expr": {"kind": "midpoint", "a": ir_name(a), "b": ir_name(b)}})
                khai.append(P.memory_declaration(ir_name(t), "point3"))
            elif t in self.divisions:                        # the IR's own expression, exact ratio
                a, b, r = self.divisions[t]
                lenh.append({"kind": "construct_point", "target_var": ir_name(t), "label": t,
                             "expr": {"kind": "divide_segment", "a": ir_name(a), "b": ir_name(b), "ratio": str(r)}})
                khai.append(P.memory_declaration(ir_name(t), "point3"))
            elif t in self.centroids:                        # trọng tâm = chia đoạn từ đỉnh tới trung điểm cạnh đối, 2/3
                a, b, c3 = self.centroids[t]
                m = ir_name(t) + "_mid_" + ir_name(b) + ir_name(c3)
                lenh.append({"kind": "construct_point", "target_var": m,
                             "expr": {"kind": "midpoint", "a": ir_name(b), "b": ir_name(c3)}})
                lenh.append({"kind": "construct_point", "target_var": ir_name(t), "label": t,
                             "expr": {"kind": "divide_segment", "a": ir_name(a), "b": m, "ratio": "2/3"}})
                khai += [P.memory_declaration(m, "point3"), P.memory_declaration(ir_name(t), "point3")]
            else:
                lenh.append(P.declare_point(ir_name(t), self.pts[t], t))
                khai.append(P.memory_declaration(ir_name(t), "point3", provenance="LAYOUT_DERIVED"))
        # Learner order (run `pedagogical-construction-sequencing`): the points a solid needs, then the solid, then the
        # auxiliary points — a topological split of the same statements, values unchanged.
        # The height foot of a pyramid belongs to the solid's formation (base → height → lateral edges): ask the formation
        # authority itself which points it would accept as the foot, with the same declared topology it receives.
        from app.simulation.semantic_program.formation import _chan_ung_vien
        tat_ca, to_po = [st for _, l, _ in khoi_diem for st in l], hop_dong_to_po_da_khai(self.calls)
        khai_cua = {t: k for t, _, k in khoi_diem}
        lenh, khai = [], []
        sau = [(t, l) for t, l, _ in khoi_diem]
        point_order = {t: i for i, (t, _, _) in enumerate(khoi_diem)}
        # Original solid first; each later solid consumes only its own transitive point prerequisites.
        solid_order = sorted(self.khoi.values(), key=lambda k: (
            max(point_order[ir_name(x)] for x in (*k.base, *k.top, *([k.apex] if k.apex else []))), k.name))
        for k in solid_order:
            dinh = {ir_name(x) for x in (*k.base, *k.top, *([k.apex] if k.apex else []))}
            if k.apex:
                dinh |= set(_chan_ung_vien(tat_ca, to_po, ir_name(k.apex), tuple(map(ir_name, k.base))))
            truoc, sau = thu_tu_su_pham(sau, dinh)
            lenh += [st for _, l in truoc for st in l]
            khai += [d for t, _ in truoc for d in khai_cua[t]]
            ten = "khoi_" + ir_name(k.name.replace(".", "_"))
            st = (P.construct_pyramid(ten, ir_name(k.apex), tuple(map(ir_name, k.base)), k.name) if k.kind == "pyramid"
                  else {**P.construct_prism(ten, tuple(map(ir_name, k.base)), tuple(map(ir_name, k.top)),
                                            tuple((ir_name(b), ir_name(t)) for b, t in zip(k.base, k.top))), "label": k.name})
            lenh.append(st)
            khai.append(P.memory_declaration(ten, "solid"))
            self.trace.append({"step": "construct_solid", "object": k.name, "rule": k.kind, "calls": [k.call],
                               "provenance": "DERIVED"})
        lenh += [st for _, l in sau for st in l]
        khai += [d for t, _ in sau for d in khai_cua[t]]
        td = self._bien_dich_mat_cat(khai, lenh)
        hoi: dict[str, str] = {}
        for c in self.of(*BAC_DAI_LUONG):
            kq, a = f"kq_{c.id}", c.args
            if c.fn == "ask_volume":
                lenh.append(P.measure_quantity(kq, "volume", "khoi_" + ir_name(a.solid.replace(".", "_"))))
            elif c.fn == "ask_length":
                lenh.append(P.measure_quantity(kq, "distance", ir_name(a.segment[0]), ir_name(a.segment[1])))
            elif c.fn == "ask_distance_point_plane":
                mp = f"mp_{c.id}"
                lenh.append({"kind": "construct_plane", "target_var": mp, "through": [ir_name(x) for x in a.plane]})
                khai.append(P.memory_declaration(mp, "plane3"))
                lenh.append(P.measure_quantity(kq, "distance", ir_name(a.point), mp))
            elif c.fn == "ask_angle_line_plane":
                dt, mp = f"dt_{c.id}", f"mp_{c.id}"
                lenh.append(P.construct_line(dt, ir_name(a.line[0]), ir_name(a.line[1])))
                lenh.append({"kind": "construct_plane", "target_var": mp, "through": [ir_name(x) for x in a.plane[:3]]})
                khai += [P.memory_declaration(dt, "line3"), P.memory_declaration(mp, "plane3")]
                lenh.append(P.measure_quantity(kq, "angle_cos_sq", dt, mp))
            elif c.fn == "ask_angle_plane_plane":
                m1, m2 = f"mp1_{c.id}", f"mp2_{c.id}"
                for m, mp in ((m1, a.plane1), (m2, a.plane2)):
                    lenh.append({"kind": "construct_plane", "target_var": m, "through": [ir_name(x) for x in mp[:3]]})
                    khai.append(P.memory_declaration(m, "plane3"))
                lenh.append(P.measure_quantity(kq, "angle_cos_sq", m1, m2))
            elif c.fn in ("ask_distance_lines", "ask_angle_lines"):
                d1, d2 = f"dt1_{c.id}", f"dt2_{c.id}"
                for d, ln in ((d1, a.line1), (d2, a.line2)):
                    lenh.append(P.construct_line(d, ir_name(ln[0]), ir_name(ln[1])))
                    khai.append(P.memory_declaration(d, "line3"))
                lenh.append(P.measure_quantity(kq, "distance" if c.fn == "ask_distance_lines" else "angle_cos_sq", d1, d2))
            elif c.fn == "ask_section_area":
                lenh.append(P.measure_quantity(kq, "area", td[self._khoa_mat_cat(c)]))
            elif c.fn == "ask_volume_ratio":
                v_num, v_den = f"v_tu_{c.id}", f"v_mau_{c.id}"
                s_num = "khoi_" + ir_name(a.numerator_solid.replace(".", "_"))
                s_den = "khoi_" + ir_name(a.denominator_solid.replace(".", "_"))
                lenh.append({**P.measure_quantity(v_num, "volume", s_num), "label": f"Thể tích khối {a.numerator_solid}"})
                lenh.append({**P.measure_quantity(v_den, "volume", s_den), "label": f"Thể tích khối {a.denominator_solid}"})
                khai += [P.memory_declaration(v_num, P.KIEU_DAI_LUONG), P.memory_declaration(v_den, P.KIEU_DAI_LUONG)]
                ratio = self.ratio_certificates[c.id]
                p_num, q_den = ratio.numerator, ratio.denominator
                cross = {"kind": "arith", "op": "-", "left": {"kind": "arith", "op": "*", "left": {"kind": "literal", "value": q_den}, "right": {"kind": "var", "name": v_num}}, "right": {"kind": "arith", "op": "*", "left": {"kind": "literal", "value": p_num}, "right": {"kind": "var", "name": v_den}}}
                expr = {"kind": "arith", "op": "+", "left": cross, "right": {"kind": "literal", "value": str(ratio)}}
                lenh.append({"kind": "assign", "target_var": kq, "expr": expr, "label": f"Tỉ số thể tích V({a.numerator_solid}) / V({a.denominator_solid})"})
            elif c.fn == "ask_residual_volume":
                v_orig = f"v_goc_{c.id}"
                s_orig = "khoi_" + ir_name(a.original_solid.replace(".", "_"))
                lenh.append({**P.measure_quantity(v_orig, "volume", s_orig), "label": f"Thể tích khối gốc {a.original_solid}"})
                khai.append(P.memory_declaration(v_orig, P.KIEU_DAI_LUONG))
                expr: dict[str, Any] = {"kind": "var", "name": v_orig}
                for idx, sub_s in enumerate(a.subtracted_solids, 1):
                    v_sub = f"v_cat_{c.id}_{idx}"
                    s_sub = "khoi_" + ir_name(sub_s.replace(".", "_"))
                    lenh.append({**P.measure_quantity(v_sub, "volume", s_sub), "label": f"Thể tích khối cắt bỏ {sub_s}"})
                    khai.append(P.memory_declaration(v_sub, P.KIEU_DAI_LUONG))
                    expr = {"kind": "arith", "op": "-", "left": expr, "right": {"kind": "var", "name": v_sub}}
                lenh.append({"kind": "assign", "target_var": kq, "expr": expr, "label": f"Thể tích phần còn lại của {a.original_solid}"})
            else:
                dg = f"dg_{c.id}"
                lenh.append(P.construct_polygon(dg, tuple(map(ir_name, a.polygon))))
                khai.append(P.memory_declaration(dg, "polygon3"))
                lenh.append(P.measure_quantity(kq, "area", dg))
            khai.append(P.memory_declaration(kq, P.KIEU_DAI_LUONG))
            hoi[c.id] = kq
            self.trace.append({"step": "measure", "object": c.fn, "rule": c.fn, "calls": [c.id], "provenance": "DERIVED"})
        khai, lenh = gop_doi_tuong_trung(khai, lenh, so_huu)
        return {"title": "Dựng hình từ lời gọi hàm có nguồn", "memory_declarations": khai, "statements": lenh}, hoi

    def kiem_mat_cat(self) -> None:
        """Tiền điều kiện của thiết diện / giao tuyến / tam giác / góc đường–mặt trên hình ĐÃ dựng — từ chối có mã thay vì để
        kernel ném lúc thực thi: mặt cắt/tam giác qua ba điểm thẳng hàng hay không cùng mặt ⇒ mã của kernel; hai mặt song song
        (hay trùng) ⇒ PARALLEL_PLANES."""
        cur_id: tuple[str, ...] = ()
        try:
            with _metric.using(self.metric()):
                for d in self.mat_phu:
                    cur_id = tuple(d["constructs"]) + tuple(d["targets"])
                    self._kiem_mat_phu(d)
                for c in (*self.of("section"), *self.of("ask_section_area")):
                    cur_id = (c.id,)
                    self._plane(c.args.plane)
                for c in self.of("ask_area"):
                    cur_id = (c.id,)
                    self._plane(c.args.polygon)
                for c in self.of("ask_angle_line_plane"):
                    cur_id = (c.id,)
                    self._line(c.args.line)
                    self._plane(c.args.plane[:3])
                for c in self.of("ask_angle_lines"):              # a line through two coincident points ⇒ kernel code
                    cur_id = (c.id,)
                    self._line(c.args.line1)
                    self._line(c.args.line2)
                for c in self.of("intersection_line"):
                    cur_id = (c.id,)
                    p1, p2 = self._plane(c.args.plane1), self._plane(c.args.plane2)
                    if p1.normal.cross(p2.normal).is_zero():
                        raise TuChoi("PARALLEL_PLANES", f"{c.id}: hai mặt phẳng song song hoặc trùng nhau — không có giao tuyến",
                                     (c.id,))
        except GeometryError as e:
            raise TuChoi(e.code, str(e), cur_id or tuple(c.id for c in self.of("section", "ask_section_area", "intersection_line", "ask_area", "ask_angle_line_plane")))

    def kiem_dinh_cat(self, d: dict) -> None:
        """Postconditions of a `DINH_CAT_CANH` certificate on the built figure (run `typedfactnext-planner-bridge`): every
        vertex lies on its edge's LINE and on the derived plane, the edge IS a lateral edge of the solid and not parallel to
        the plane (unique cut), and the vertex lies on the SEGMENT oriented from the apex (pyramid, 0 < t ≤ 1) or from the base
        (prism, 0 ≤ t ≤ 1) — exact, chart coordinates (incidence is affine);
        a derived pyramid's base vertices are pairwise distinct. Reused points are checked like constructed ones."""
        ids = tuple(d.get("constructs") or ()) + ((d["derived"]["call"],) if d.get("derived") else ())
        k = self.khoi.get(d.get("solid"))
        if k is None:
            raise TuChoi("UNKNOWN_SOLID", "đỉnh thiết diện: khối bị cắt không có trên hình", ids)
        # lateral edges ORIENTED from the apex (pyramid) or the base vertex (prism): t is measured from that end
        canh = {frozenset(e): e for e in ([(k.apex, b) for b in k.base] if k.apex else list(zip(k.base, k.top)))}
        with _metric.using(self.metric()):
            mat = self._plane(d["plane"])
            for v in d["vertices"]:
                if frozenset(v["edge"]) not in canh:
                    raise TuChoi("SECTION_VERTEX_OFF_EDGE", f"{''.join(v['edge'])} không phải cạnh bên của {k.name}", ids)
                (u, w), x = canh[frozenset(v["edge"])], v["label"]
                pu, pw, px = (Vec3(*self.pts[n]) for n in (u, w, x))
                huong = pw - pu
                if huong.dot(mat.normal) == 0:
                    raise TuChoi("LINE_PARALLEL_TO_PLANE", f"cạnh {u}{w} song song (hoặc nằm trong) mặt cắt — không có giao duy "
                                 "nhất", ids)
                if not point_on_line(px, Line3(pu, huong)) or mat.signed_eval(px) != 0:
                    raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"{x} không là giao của {u}{w} với mặt cắt", ids)
                i = next(j for j in range(3) if (huong.x, huong.y, huong.z)[j] != 0)
                t = ((px.x, px.y, px.z)[i] - (pu.x, pu.y, pu.z)[i]) / (huong.x, huong.y, huong.z)[i]
                # a pyramid's lateral edge starts at the apex: the cut may meet the base vertex, never the apex; a prism's
                # lateral edge has no apex, either endpoint may be met
                if not (0 < t <= 1 if k.apex else 0 <= t <= 1):
                    raise TuChoi("SECTION_VERTEX_OFF_EDGE", f"mặt cắt gặp đường {u}{w} ngoài cạnh (t = {t})", ids)
                self.trace.append({"step": "certify_section_vertex", "object": x, "edge": [u, w], "t": str(t),
                                   "choice": v["choice"], "rule": d["rule"], "relation_verified": True,
                                   "provenance": "DERIVED", "binding": "AUXILIARY"})
            if d.get("derived"):
                base = d["derived"]["base"]
                if len({self.pts[n] for n in base}) != len(base):
                    raise TuChoi("DEGENERATE_DERIVED_SECTION", "hai đỉnh thiết diện trùng nhau", ids)
        # Closure certificate (run `hybrid-contract-v2`): the polygon a derived solid stands on, and any author-declared
        # boundary, must BE the exact cross-section — same vertices, same cyclic order (rotation / reversal allowed).
        tren = {frozenset(v["edge"]): v["label"] for v in d["vertices"]}
        vong = None
        if d.get("declared_boundary") is not None:
            vong = [tren.get(frozenset(e)) for e in d["declared_boundary"]]
            if None in vong:
                raise TuChoi("SECTION_BOUNDARY_INCOMPLETE", "biên khai báo đi qua cạnh không có đỉnh thiết diện", ids)
            self.chung_chi_khep_kin(k.name, d["plane"], vong, ids)
        if d.get("derived"):
            vong = list(d["derived"]["base"])
            self.chung_chi_khep_kin(k.name, d["plane"], vong, ids)
        if vong is not None:
            d["closure"] = {"boundary": vong, "verified": True,
                            "rule": "boundary == cross_section(solid, plane) up to rotation/reversal; vertices 0 < t ≤ 1"}
            self.trace.append({"step": "certify_section_closure", "object": "".join(vong), "rule": d["rule"],
                               "relation_verified": True, "provenance": "DERIVED", "binding": "AUXILIARY"})

    def chung_chi_khep_kin(self, ten_khoi: str, mat: list[str], vong: list[str], ids: tuple = ()) -> None:
        """THE section-closure authority (run `hybrid-contract-v2`; Adapter /3 calls it too): the cycle `vong` of built
        points is exactly `section.cross_section(solid, plane through mat[:3])` up to rotation / reversal. Incidence only,
        exact Fractions, chart coordinates (affine-invariant). Anything else ⇒ `SECTION_BOUNDARY_INCOMPLETE`."""
        from app.simulation.geometry.section import Polyhedron, cross_section, same_section_cycle
        k = self.khoi[ten_khoi]
        if k.kind == "pyramid":
            dinh, mat_khoi = [k.apex, *k.base], P.construct_pyramid("solid", k.apex, k.base)["faces"]
        else:
            dinh = [*k.base, *k.top]
            mat_khoi = P.construct_prism("solid", k.base, k.top, tuple(zip(k.base, k.top)))["faces"]
        try:
            with _metric.using(self.metric()):
                that = cross_section(Polyhedron(tuple(Vec3(*self.pts[p]) for p in dinh),
                                                tuple(tuple(dinh.index(p) for p in f) for f in mat_khoi)),
                                     self._plane(mat[:3])).polygon
        except GeometryError as e:
            raise TuChoi(e.code, str(e), ids) from None
        if not same_section_cycle([Vec3(*self.pts[p]) for p in vong], that):
            raise TuChoi("SECTION_BOUNDARY_INCOMPLETE", f"chu trình {''.join(vong)} ({len(vong)} đỉnh) không phải thiết diện "
                         f"thật của {ten_khoi} ({len(that)} đỉnh) theo đúng thứ tự vòng", ids)

    def _kiem_mat_vuong_duong(self, d: dict) -> None:
        """Postconditions of the plane through p ⊥ d (`MAT_VUONG_DUONG`), independent of how it was assembled: both
        auxiliary directions ⊥ d in the chart Gram metric, independent (a plane), and the same plane as the kernel's own
        `plane_through_point_perpendicular_to(p, d)` — the operation the IR's `PlanePerpendicularToLineExpr` evaluates."""
        p, (x1, x2), (a, b) = d["point"], d["labels"], d["perpendicular_to"]
        ids = tuple(d["constructs"]) + tuple(d["targets"])
        dv = self._vec(a, b)
        if self.g(dv, dv) == 0:
            raise TuChoi("DEGENERATE_LINE", "hai đầu mút của đường trùng tọa độ đã xác minh", ids)
        u1, u2 = self._vec(p, x1), self._vec(p, x2)
        if self.g(u1, dv) != 0 or self.g(u2, dv) != 0:
            raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"phương phụ của mặt qua {p} không vuông góc {a}{b}", ids)
        mat = self._plane([p, x1, x2])                     # independent directions, else the kernel's own code
        ref = K.plane_through_point_perpendicular_to(Vec3(*self.pts[p]), self._line([a, b]))
        if not all(ref.signed_eval(Vec3(*self.pts[x])) == 0 for x in (p, x1, x2)) or not mat.normal.cross(ref.normal).is_zero():
            raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"mặt dẫn xuất qua {p} khác mặt qua {p} vuông góc {a}{b} của kernel", ids)

    def _kiem_mat_phu(self, d: dict) -> None:
        """Postconditions of a derived plane, independent of how the planner built it. It passes through the point by
        construction (built through it); checked here: parallel to the reference plane (normals, `predicates.parallel_planes`),
        not that plane, and not a face of the solid it cuts (a boundary plane is not a cutting section — no silent M4)."""
        vuong, two = d["rule"] == MAT_VUONG_DUONG, d["rule"] == MAT_HAI_DUONG
        p, q, (x1, x2), ids = d["point"], d.get("parallel_to"), d["labels"], tuple(d["constructs"]) + tuple(d["targets"])
        if vuong:                                          # ⊥ certificate first; the face check below is shared
            self._kiem_mat_vuong_duong(d)
        if two:
            if any(self.pts[a] == self.pts[b] for a,b in d['lines']):
                raise TuChoi('DEGENERATE_LINE', 'hai đầu mút của đường trùng tọa độ đã xác minh', ids)
            lines = [self._line(v) for v in d['lines']]
            if lines[0].direction.cross(lines[1].direction).is_zero():
                raise TuChoi('PLANE_NOT_UNIQUE', 'hai đường có phương phụ thuộc; mặt qua điểm không duy nhất', ids)
        mat = self._plane([p, x1, x2])
        if not point_on_plane(Vec3(*self.pts[p]),mat):
            raise TuChoi('ENGINE_SELF_CHECK_FAILED','mặt dẫn xuất không qua điểm đã xác minh',ids)
        if two:
            for line in lines:
                if line_in_plane(line,mat):
                    raise TuChoi('LINE_CONTAINED_IN_PLANE','đường nằm trong mặt phẳng, không song song nghiêm ngặt',ids)
                if not parallel_line_plane(line,mat):
                    raise TuChoi('ENGINE_SELF_CHECK_FAILED','mặt dẫn xuất không song song với cả hai đường',ids)
        elif not vuong:
            goc=self._plane(q)
            if not parallel_planes(mat, goc):
                raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"mặt dẫn xuất qua {p} không song song ({''.join(q)})", ids)
            if goc.signed_eval(Vec3(*self.pts[p])) == 0:
                raise TuChoi("DERIVED_PLANE_IS_REFERENCE", f"{p} nằm trên ({''.join(q)}): mặt qua {p} song song với nó là chính "
                             "nó — không có mặt cắt mới", ids)
        for c in self.of(*{"section", "ask_section_area"}):
            if c.id not in ids:
                continue
            k = self.khoi[c.args.solid]
            dinh = list(dict.fromkeys([*k.base, *k.top, *([k.apex] if k.apex else [])]))
            dau = [mat.signed_eval(Vec3(*self.pts[v])) for v in dinh]
            if sum(x == 0 for x in dau) >= 3 and not ({x > 0 for x in dau if x != 0} == {True, False}):
                raise TuChoi("SECTION_PLANE_IS_FACE", f"{c.id}: mặt dẫn xuất chứa một mặt biên của {k.name} — mặt biên không "
                             "phải thiết diện cắt xuyên", ids)
        ten = (f"({d['plane_name']})" if two else f"({p} ⊥ {''.join(d['perpendicular_to'])})" if vuong
               else f"({p} ∥ {''.join(q)})")
        self.trace.append({"step": "construct_plane", "object": ten, "rule": d['rule'],
                           "calls": list(d["constructs"]), "dependencies": [p, x1, x2], "relation_verified": True,
                           "provenance": "DERIVED", "binding": "AUXILIARY"})

    def _khoa_mat_cat(self, c: LoiGoi) -> tuple:
        """Một thiết diện = (khối, MẶT PHẲNG) — mặt so bằng phương trình chuẩn hoá trên hình đã dựng, nên (MAB) và (NAB) cùng
        một mặt là một thiết diện (review 2, M2). Pháp tuyến chia cho thành phần khác 0 đầu tiên; hệ số tự do d = n·điểm."""
        with _metric.using(self.metric()):
            mp = self._plane(c.args.plane)
        n = (mp.normal.x, mp.normal.y, mp.normal.z)
        k = next(x for x in n if x != 0)
        n = tuple(Fraction(x) / k for x in n)
        return c.args.solid, n, sum(a * Fraction(b) for a, b in zip(n, (mp.point.x, mp.point.y, mp.point.z)))

    def _bien_dich_mat_cat(self, khai: list, lenh: list) -> dict[tuple, str]:
        """Thiết diện và giao tuyến → câu lệnh IR SẴN CÓ (`construct_section`, `intersect_plane_plane`). Một thiết diện (khối,
        mặt) chỉ dựng MỘT lần dù được yêu cầu dựng và hỏi diện tích; trả {khoá: biến thiết diện}."""
        td: dict[tuple, str] = {}
        vet: dict[tuple, dict] = {}
        for c in (*self.of("section"), *self.of("ask_section_area")):
            if (khoa := self._khoa_mat_cat(c)) in td:
                vet[khoa]["calls"].append(c.id)                 # cùng thiết diện: một đối tượng, vết ghi mọi lời gọi (M3)
                continue
            ten, mp = f"td_{c.id}", f"mp_td_{c.id}"
            # A derived plane is named by its verified relation, never by the planner's auxiliary labels.
            dan = next((d for d in self.mat_phu if c.id in d["targets"]), None)
            nhan_mat = (f"({self.ten_mat_phu.get(dan['constructs'][0]) or 'α'})" if dan
                        else "(" + "".join(c.args.plane) + ")")
            lenh.append({"kind": "construct_plane", "target_var": mp, "through": [ir_name(x) for x in c.args.plane[:3]],
                         "label": nhan_mat})
            lenh.append({"kind": "construct_section", "target_var": ten, "solid": "khoi_" + ir_name(c.args.solid.replace(".", "_")),
                         "plane": mp, "label": "thiết diện"})
            khai += [P.memory_declaration(mp, "plane3"), P.memory_declaration(ten, "section")]
            td[khoa] = ten
            self.sections.append(ten)
            vet[khoa] = {"step": "construct_section", "object": ten, "rule": c.fn, "calls": [c.id], "provenance": "DERIVED"}
            self.trace.append(vet[khoa])
        for c in self.of("intersection_line"):
            self._emit_intersection(c,khai,lenh)
        return td

    def _emit_intersection(self, c, declarations, statements):
        """Emit the existing line IR once, inside the first consumer's dependency block."""
        if c.id in self.line_aliases:
            c=next(p for p in self.calls if p.id==self.line_aliases[c.id])
        name = f'gt_{c.id}'
        if c.id in self.emitted_lines:
            return name
        self.emitted_lines.add(c.id)
        m1, m2 = f'mp1_gt_{c.id}', f'mp2_gt_{c.id}'
        for m, labels in ((m1,c.args.plane1),(m2,c.args.plane2)):
            statements.append({'kind':'construct_plane','target_var':m,'through':[ir_name(p) for p in labels[:3]],
                               'label':'('+''.join(labels)+')'})
            declarations.append(P.memory_declaration(m,'plane3'))
        statements.append({'kind':'assign','target_var':name,'expr':{'kind':'intersect_plane_plane','plane_a':m1,'plane_b':m2}})
        declarations.append(P.memory_declaration(name,'line3'))
        if c.id not in self.lines:
            self.trace.append({'step':'construct_line','object':name,'rule':c.fn,'calls':[c.id],'provenance':'DERIVED'})
        return name

    def kiem_mo_ta(self, d: dict) -> None:
        """`effect-chain` (planner): the unnamed point IS what the source describes, checked on the built figure by a
        predicate keyed by the DESCRIPTION — not by whichever function the planner's contract chose to construct it."""
        op, ask = d.get("operand") or {}, (d.get("ask"),)
        dung = _MO_TA.get(op.get("descriptor"))
        if dung is None:
            raise TuChoi("UNSUPPORTED_CAPABILITY", f"không có vị từ kiểm cho mô tả {op.get('descriptor')!r}", ask)
        x, pts = op.get("label"), op.get("points") or []
        if x not in self.pts or any(p not in self.pts for p in pts) or not dung(self.pts[x], [self.pts[p] for p in pts]):
            raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"điểm {x} không phải {op.get('descriptor')} của {''.join(pts)}", ask)

    def _dt2_tam_giac(self, p: str, q: str, r: str) -> Fraction:
        """Squared area of triangle (p, q, r) directly from Gram determinant: (g(u,u)·g(v,v) - g(u,v)²) / 4."""
        u, v = self._vec(p, q), self._vec(p, r)
        det = self.g(u, u) * self.g(v, v) - self.g(u, v) ** 2
        if det <= 0:
            raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"ba đỉnh {p}, {q}, {r} thẳng hàng — định thức Gram suy biến")
        return det / 4

    def _goc_duong_mat_cos2(self, line: tuple[str, ...], plane: tuple[str, ...]) -> Fraction:
        """Line–plane angle cos²(θ) = 1 - sin²(θ) directly from Gram determinants of (u, v, w), independent of kernel covectors."""
        u, v, w = self._vec(plane[0], plane[1]), self._vec(plane[0], plane[2]), self._vec(line[0], line[1])
        ww = self.g(w, w)
        if ww == 0:
            raise TuChoi("DEGENERATE_LINE", "đường thẳng suy biến (hai đầu mút trùng nhau)")
        M = [[self.g(x, y) for y in (u, v, w)] for x in (u, v, w)]
        det2 = M[0][0] * M[1][1] - M[0][1] * M[1][0]
        if det2 == 0:
            raise TuChoi("ENGINE_SELF_CHECK_FAILED", "ba điểm xác định mặt phẳng thẳng hàng — định thức Gram suy biến")
        d3 = (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1]) - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
              + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))
        sin2 = d3 / (ww * det2)
        return Fraction(1) - sin2

    def _goc_hai_duong_cos2(self, line1: tuple[str, ...], line2: tuple[str, ...]) -> Fraction:
        """Line–line angle cos²(θ) = ⟨u,v⟩²_G / (⟨u,u⟩_G ⟨v,v⟩_G) from the chart Gram metric, independent of the kernel."""
        u, v = self._vec(*line1), self._vec(*line2)
        uu, vv = self.g(u, u), self.g(v, v)
        if uu == 0 or vv == 0:
            raise TuChoi("DEGENERATE_LINE", "đường thẳng suy biến (hai đầu mút trùng nhau)")
        return self.g(u, v) ** 2 / (uu * vv)

    def _kc2_goc_hai_duong(self, d: dict) -> Fraction:
        return self._goc_hai_duong_cos2((d["operand"]["label"], d["target"]["point"]), tuple(d["target"]["line"]))

    def _kc2_khoang_cach(self, d: dict) -> Fraction:
        p, t = d["operand"]["label"], d["target"]
        if "plane" in t:
            return self._kc2_mat(p, tuple(t["plane"][:3]))
        if "line" in t:
            o, u = self.pts[t["line"][0]], self._vec(*t["line"])
        else:
            line = self.lines[t["line_ref"]]
            o, u = (line.point.x, line.point.y, line.point.z), (line.direction.x, line.direction.y, line.direction.z)
        w = tuple(self.pts[p][i] - o[i] for i in range(3))
        return self.g(w, w) - self.g(w, u) ** 2 / self.g(u, u)

    def _kc2_do_dai(self, d: dict) -> Fraction:
        w = self._vec(d["operand"]["label"], d["target"]["point"])
        return self.g(w, w)

    def _kc2_dien_tich(self, d: dict) -> Fraction:
        q, r = d["target"]["points"]
        return self._dt2_tam_giac(d["operand"]["label"], q, r)

    def _kc2_goc_duong_mat(self, d: dict) -> Fraction:
        p, t = d["operand"]["label"], d["target"]
        return self._goc_duong_mat_cos2((p, t["point"]), tuple(t["plane"][:3]))

    def kc2_dich(self, d: dict) -> Fraction:
        """Direct Gram-metric target verifier dispatched by `_KIEM_DICH` from the certified goal contract —
        independent of the chain whose measurement answered the question."""
        from .registry import GOAL_VERIFIER_TARGET

        # the verifier is the one whose target the certificate carries (one table with the gate); otherwise a distance
        verifier = next((v for v, keys in GOAL_VERIFIER_TARGET.items() if keys == frozenset(d["target"])), "distance")
        ask_call = next((c for c in self.calls if c.id == d.get("ask")), None)
        if ask_call is not None and d.get("chain"):
            from .registry import planning_contract
            ans_entry = d["chain"][-1]
            contract = planning_contract(ask_call.spec, ans_entry.get("effect"))
            if contract is None or contract.verifier != verifier or contract.verifier not in _KIEM_DICH:
                raise TuChoi("ENGINE_SELF_CHECK_FAILED", "verifier của hợp đồng mục tiêu không khớp bộ kiểm độc lập",
                             (ask_call.id,))
        fn = _KIEM_DICH.get(verifier)
        if fn is None:
            raise TuChoi("ENGINE_SELF_CHECK_FAILED", f"không có bộ kiểm độc lập cho {verifier!r}", (d.get("ask", ""),))
        return fn(self, d)

    def metric(self) -> _metric.Metric:
        G2, h2 = self.G2, self.h2 or Fraction(1)
        try:
            return _metric.Metric(((G2[0][0], G2[0][1], Z), (G2[1][0], G2[1][1], Z), (Z, Z, h2)))
        except GeometryError as e:
            # The type enforces SPD. `kiem_mat_cat` already maps it inside its handler, but goal checkers call
            # `metric()` after serving, outside any handler: refuse with the code here, once, for every caller.
            raise TuChoi(e.code, f"khung toạ độ không có hình Euclid: {e}") from None


#: Independent Gram-metric verifiers keyed by goal contract `verifier` kind.
_KIEM_DICH = {
    "distance": _Dung._kc2_khoang_cach,
    "length": _Dung._kc2_do_dai,
    "area": _Dung._kc2_dien_tich,
    "angle_line_plane": _Dung._kc2_goc_duong_mat,
    "angle_lines": _Dung._kc2_goc_hai_duong,
}


#: Bậc theo độ dài của mỗi đại lượng được hỏi — đáp số với độ dài ký hiệu a là (hệ số tại a = 1) · a^bậc.
BAC_DAI_LUONG = {"ask_volume": 3, "ask_length": 1, "ask_distance_point_plane": 1, "ask_angle_line_plane": 0,
                 "ask_area": 2, "ask_angle_plane_plane": 0, "ask_distance_lines": 1, "ask_section_area": 2,
                 "ask_angle_lines": 0, "ask_volume_ratio": 0, "ask_residual_volume": 3}


#: Definitions of the unnamed points a planner `effect-chain` may introduce (affine: valid in chart coordinates). A
#: description without a predicate here is not served, whatever contract proposes it.
_MO_TA = {
    "midpoint": lambda x, ps: len(ps) == 2 and all(2 * x[i] == ps[0][i] + ps[1][i] for i in range(3)),
    "centroid": lambda x, ps: len(ps) == 3 and all(3 * x[i] == sum(p[i] for p in ps) for i in range(3)),
}


def _binh_phuong(v: Any) -> Fraction | None:
    from app.simulation.geometry.radical import Radical

    if isinstance(v, Radical):
        return None if getattr(v, "mu", 0) else Fraction(v.he) ** 2 * v.can
    return Fraction(v) ** 2 if isinstance(v, (int, Fraction)) else None


#: Thiết diện suy biến do kernel phát hiện khi thực thi — từ chối bằng chính mã ấy, không gộp vào ENGINE_EXECUTION_FAILED.
_MA_THIET_DIEN_SUY_BIEN = {"PLANE_DOES_NOT_CUT", "PLANE_TOUCHES_VERTEX", "PLANE_TOUCHES_EDGE"}
_MU = {1: "", 2: "²", 3: "³"}


def _labels(c: LoiGoi) -> set[str]:
    from .registry import nhan_cua_loi_goi

    return nhan_cua_loi_goi(c)


def dinh_dang(x: Any) -> str:
    """Số chính xác của kernel → chuỗi hiển thị (`4√3`, `12/5`, `√14`)."""
    from app.simulation.geometry.radical import Radical

    if isinstance(x, Radical):
        he, can = Fraction(x.he), x.can
        pi = "π" if getattr(x, "mu", 0) else ""
        dau = "-" if he < 0 else ""
        he = abs(he)
        tu = "" if he.numerator == 1 else str(he.numerator)
        return f"{dau}{tu}{pi}√{can}" + (f"/{he.denominator}" if he.denominator != 1 else "")
    if isinstance(x, (int, Fraction)):
        return str(Fraction(x))
    raise TypeError(f"không phải số chính xác: {type(x).__name__}")


def _kiem_tren_hinh(dung: "_Dung"):
    """Kiểm MỘT mệnh đề (lời gọi dạng dict, chưa qua cổng nguồn) trên hình đã dựng — dùng cho điều phải chứng minh và mệnh đề
    phủ định của nhánh B. Không dựng thêm gì; điểm/khối chưa có ⇒ None (không kiểm được), không đoán."""
    def kiem(call: dict) -> bool | None:
        try:
            (c,) = doc_ke_hoach({"calls": [call]})
            if c.spec.kind in ("ask", "escape"):            # câu hỏi / mệnh đề ngoài thư viện: không có gì để kiểm
                return None
            return dung._dung_khong(c)
        except (TuChoi, KeyError, ZeroDivisionError):
            return None
    return kiem


def _don_vi(calls: tuple[LoiGoi, ...]) -> str | None:
    """Độ dài ký hiệu: TẤT CẢ độ dài đề cho cùng theo a (đồng bậc 1) ⇒ "a"; tất cả là số ⇒ None; trộn ⇒ từ chối — hình
    khi ấy KHÔNG đồng dạng khi a đổi, nên không có một bố cục chung nào đúng cho mọi a (không gán a một giá trị)."""
    loai = {doc_so(getattr(c.args, f))[1] for c in calls for f in c.spec.value_fields if getattr(c.args, f) is not None}
    if len(loai) > 1:
        raise TuChoi("NON_HOMOGENEOUS_LENGTHS", "đề trộn độ dài theo a với độ dài là số — chưa dựng được một hình chung cho mọi a",
                     tuple(sorted(c.id for c in calls for f in c.spec.value_fields if getattr(c.args, f) is not None)))
    return "a" if loai == {True} else None


def _hien_thi_ky_hieu(x: Any, bac: int, ky_hieu: str) -> str:
    """hệ số · a^bậc → `a³√2/3`, `a√21/7`, `16a³`."""
    from app.simulation.geometry.radical import Radical

    he, can = (Fraction(x.he), x.can) if isinstance(x, Radical) else (Fraction(x), 1)
    tu = "" if he.numerator == 1 else str(he.numerator)
    return f"{tu}{ky_hieu}{_MU[bac]}" + (f"√{can}" if can != 1 else "") + (f"/{he.denominator}" if he.denominator != 1 else "")


def dung_tu_loi_goi(problem_text: str, plan: Any, auxiliary: tuple[dict, ...] = (),
                    read_quotes: tuple[str, ...] = ()) -> KetQuaTuyen:
    """Dựng + kiểm + thực thi từ lời gọi hàm. Trả `KetQuaTuyen` CHƯA có cảnh (`scene3d=None`) nhưng có `spec` và
    `exec_result` — bày cảnh là việc của tầng trên (`app/ai/function_route.py`), cùng hướng phụ thuộc với
    `ai/pipeline._dung_scene3d`: không module nào trong `app/simulation` nhập `scene3d`/`simulation_state`."""
    from app.simulation.semantic_program.formation import hoan_thien_dung_hinh
    from app.simulation.semantic_program.interpreter import SemanticProgramInterpreter
    from app.simulation.semantic_program.validator import validate_semantic_program

    dung: _Dung | None = None
    try:
        calls = doc_ke_hoach(plan)
        ten_mat_phu = kiem_nguon(calls, problem_text, auxiliary, read_quotes)
        if esc := [c for c in calls if c.fn == "unsupported"]:
            raise TuChoi("OUT_OF_SCOPE", "; ".join(f"{c.id}: {c.args.reason} ({c.quote!r})" for c in esc),
                         tuple(c.id for c in esc))
        ky_hieu = _don_vi(calls)
        dung = _Dung(calls, problem_text, ky_hieu)
        if ky_hieu:
            dung.trace.append({"step": "choose_unit", "object": ky_hieu, "rule": "symbolic_length_unit",
                               "calls": sorted(c.id for c in calls for f in c.spec.value_fields if getattr(c.args, f)),
                               "provenance": "LAYOUT_DERIVED",
                               "note": f"mọi độ dài đề cho tỉ lệ với {ky_hieu} ⇒ hình đồng dạng với hình tại {ky_hieu} = 1; "
                                       f"dựng ở {ky_hieu} = 1 (đơn vị, không phải dữ kiện), đáp số = hệ số · {ky_hieu}^bậc"})
        dung.thu_khoi()
        dung.bo_cuc_day()
        dung.giai_phu_thuoc()
        phu = {x: d for d in auxiliary for x in (d.get("labels") or ([d['label']] if d.get('label') else []))}
        for s in dung.trace:                             # điểm phụ: DẪN XUẤT, không phải nhãn của đề — ghi rõ ràng buộc
            if s["step"] == "place_point" and s["object"] in phu:
                s.update(binding="AUXILIARY", auxiliary_rule=phu[s["object"]]["rule"], goal=phu[s["object"]]["goal"])
        dung.mat_phu = [d for d in auxiliary if d.get("rule") in (MAT_SONG_SONG, MAT_HAI_DUONG, MAT_VUONG_DUONG)]
        dung.ten_mat_phu = ten_mat_phu
        dung.kiem()
        dung.kiem_mat_cat()
        for d in auxiliary:                              # section vertices on stated cut edges (`DINH_CAT_CANH`)
            if d.get("rule") == DINH_CAT_CANH:
                dung.kiem_dinh_cat(d)
        dung.kiem_mat_viet(nhom_mat_nguon(problem_text))
        chuoi = [d for d in auxiliary if d.get("rule") == "effect-chain"]
        for d in chuoi:
            dung.kiem_mo_ta(d)
        program, hoi = dung.bien_dich()
        from app.simulation.semantic_program.validator import MAX_MEMORY_DECLARATIONS
        if (n := len(program["memory_declarations"])) > MAX_MEMORY_DECLARATIONS:   # a resource budget, typed
            raise TuChoi("IR_MEMORY_BUDGET_EXCEEDED", f"chương trình dựng cần {n} khai báo bộ nhớ > trần "
                         f"{MAX_MEMORY_DECLARATIONS} — không dựng một phần")
        vr = validate_semantic_program(program)
        if not vr.ok:
            raise TuChoi("ENGINE_IR_INVALID", f"IR engine sinh ra không qua thẩm định: {vr.error}")
        to_po = hop_dong_to_po_da_khai(calls)
        spec = hoan_thien_dung_hinh(vr.spec, to_po).spec
        if (len(spec.memory_declarations) > MAX_MEMORY_DECLARATIONS
                and any(d.get("rule") == DINH_CAT_CANH for d in auxiliary)):
            # Section-vertex plans only (run `typedfactnext-planner-bridge`; every other plan keeps main's behaviour): when
            # the teaching expansion ALONE exceeds the IR budget, build the verified program unexpanded — the Adapter /3
            # policy — and say so in the trace. Geometry, checks and answers are those of the verified program.
            dung.trace.append({"step": "formation_budget", "rule": "pedagogical_expansion_skipped",
                               "declarations": len(spec.memory_declarations), "limit": MAX_MEMORY_DECLARATIONS})
            spec = vr.spec
        G = dung.metric()
        try:
            with _metric.using(G):
                ket = SemanticProgramInterpreter().execute(spec)
        except Exception as e:  # noqa: BLE001 — kernel từ chối ⇒ từ chối có mã, không xấp xỉ
            if getattr(e, "code", None) in _MA_THIET_DIEN_SUY_BIEN:     # giữ mã của kernel cho thiết diện suy biến (review 2, M1)
                raise TuChoi(e.code, str(e)) from None
            raise TuChoi("ENGINE_EXECUTION_FAILED", f"{type(e).__name__}: {e}") from None
        fm = ket.final_memory
        for c in dung.of("ask_distance_lines"):
            # B3 gap (review I-2): the question CALLS the two lines skew ("chéo nhau"). Coplanar lines (they meet or are
            # parallel — triple product 0, exact and frame-independent) contradict the problem: refuse, never serve the
            # distance of a configuration the problem says it is not.
            d1, d2 = fm.get(f"dt1_{c.id}"), fm.get(f"dt2_{c.id}")
            noi_cheo = any(re.search(r"chéo\s+nhau", unicodedata.normalize("NFC", q[a:b]).lower())
                           for q in c.quotes for a, b in _cum_hoi(c, q, 0, len(q), calls))
            if noi_cheo and d1 is not None and d2 is not None \
                    and (d2.point - d1.point).dot(d1.direction.cross(d2.direction)) == 0:
                raise TuChoi("SKEW_CLAIM_CONTRADICTED", f"{c.id}: đề gọi hai đường là chéo nhau nhưng chúng đồng phẳng "
                             "(cắt nhau hoặc song song) — không trả khoảng cách cho một cấu hình đề nói là khác", (c.id,))
        for c in dung.of("ask_volume"):
            expected = dung.volume_certificates.get(c.args.solid)
            if expected is not None and _binh_phuong(fm.get(hoi[c.id])) != expected:
                raise TuChoi("ENGINE_SELF_CHECK_FAILED", "thể tích thực thi khác chứng chỉ diện tích Gram × đường cao", (c.id,))
        for c in dung.of("ask_volume_ratio"):
            v_num, v_den = fm.get(f"v_tu_{c.id}"), fm.get(f"v_mau_{c.id}")
            if (_binh_phuong(v_num) != dung.volume_certificates.get(c.args.numerator_solid)
                    or _binh_phuong(v_den) != dung.volume_certificates.get(c.args.denominator_solid)
                    or fm.get(hoi[c.id]) != dung.ratio_certificates.get(c.id)):
                raise TuChoi("ENGINE_SELF_CHECK_FAILED", "tỉ số thể tích thực thi khác chứng chỉ Gram độc lập", (c.id,))
        for c in dung.of("ask_residual_volume"):
            v_orig = fm.get(f"v_goc_{c.id}")
            if (_binh_phuong(v_orig) != dung.volume_certificates.get(c.args.original_solid)
                    or any(_binh_phuong(fm.get(f"v_cat_{c.id}_{idx}")) != dung.volume_certificates.get(sub_s)
                           for idx, sub_s in enumerate(c.args.subtracted_solids, 1))
                    or _binh_phuong(fm.get(hoi[c.id])) != dung.residual_certificates.get(c.id)):
                raise TuChoi("ENGINE_SELF_CHECK_FAILED", "thể tích phần còn lại thực thi khác chứng chỉ Gram độc lập", (c.id,))
        kernel_ok = all((lambda v: v is not None and (v.x, v.y, v.z) == dung.pts[t])(fm.get(ir_name(t)))
                        for t in dung.pts)
        kernel_ok = kernel_ok and all(isinstance(fm.get(f'gt_{ref}'),Line3)
                                     and point_on_line(fm[f'gt_{ref}'].point,line)
                                     and not fm[f'gt_{ref}'].direction.is_zero()
                                     and fm[f'gt_{ref}'].direction.cross(line.direction).is_zero()
                                     for ref,line in dung.lines.items())
        if not kernel_ok:
            raise TuChoi("ENGINE_SELF_CHECK_FAILED", "điểm kernel thực thi khác bố cục engine")
        for d in chuoi:                       # the composed answer is the asked quantity, not just a value of the chain
            with _metric.using(G):
                c_ask = next((c for c in calls if c.id == d["ask"]), None)
                raw_v = fm.get(hoi.get(d["ask"], ""))
                got_v = Fraction(raw_v) if (c_ask and BAC_DAI_LUONG[c_ask.fn] == 0 and isinstance(raw_v, (int, Fraction))) else _binh_phuong(raw_v)
                if got_v != dung.kc2_dich(d):
                    raise TuChoi("ENGINE_SELF_CHECK_FAILED", "đáp số của chuỗi khác đại lượng đích tính trực tiếp",
                                 (d["ask"],))
        for c in dung.of("ask_area"):
            if len(c.args.polygon) == 3 and _binh_phuong(fm.get(hoi.get(c.id, ""))) != dung._dt2_tam_giac(*c.args.polygon):
                raise TuChoi("ENGINE_SELF_CHECK_FAILED", "diện tích tam giác thực thi khác định thức Gram độc lập", (c.id,))
        for c in dung.of("ask_angle_line_plane"):
            if fm.get(hoi.get(c.id, "")) != dung._goc_duong_mat_cos2(tuple(c.args.line), tuple(c.args.plane[:3])):
                raise TuChoi("ENGINE_SELF_CHECK_FAILED", "góc đường–mặt thực thi khác công thức Gram độc lập", (c.id,))
        for c in dung.of("ask_angle_lines"):
            if fm.get(hoi.get(c.id, "")) != dung._goc_hai_duong_cos2(tuple(c.args.line1), tuple(c.args.line2)):
                raise TuChoi("ENGINE_SELF_CHECK_FAILED", "góc hai đường thực thi khác công thức Gram độc lập", (c.id,))
        if hong := [t for t in dung.sections if not fm[t].is_closed]:
            raise TuChoi("SECTION_EMPTY", f"mặt phẳng không cắt khối thành một đa giác ({hong}) — không có thiết diện để dựng")
        tra, chinh_xac = {}, {}
        for cid, kq in hoi.items():
            v = fm.get(kq)
            bac = BAC_DAI_LUONG[next(c.fn for c in calls if c.id == cid)]
            he = dinh_dang(v)
            chinh_xac[cid] = {"coef": he, "dim": bac if ky_hieu else 0, "unit": ky_hieu if bac else None}
            fn_cid = next(c.fn for c in calls if c.id == cid)
            tra[cid] = f"cos²={he}" if fn_cid.startswith("ask_angle_") else (_hien_thi_ky_hieu(v, bac, ky_hieu) if (ky_hieu and bac) else he)
        # CONTRACT-BE-1: what the source asks = each gate-certified ask's answer variable + the operands of its measure,
        # minus the planner's fresh auxiliary points (a foot H is a construction, not something the problem names; the
        # described point of an `effect-chain` IS named by the problem, "trung điểm của SC").
        phu_ir = ({ir_name(x) for x in phu}
                  - {ir_name(d["operand"]["label"]) for d in chuoi if (d.get("operand") or {}).get("label")})
        muc_tieu: set[str] = {ir_name(d["operand"]["label"]) for d in chuoi if (d.get("operand") or {}).get("label")}
        for st in program["statements"]:
            e = st.get("expr") or {}
            if st.get("target_var") in hoi.values() and e.get("kind") == "measure":
                muc_tieu |= {st["target_var"], *(x for x in (e.get("of"), e.get("wrt")) if x and x not in phu_ir)}
            elif st.get("target_var") in hoi.values() and e.get("kind") == "arith":
                muc_tieu.add(st["target_var"])
        for c in dung.of("ask_volume_ratio"):
            muc_tieu |= {
                f"v_tu_{c.id}", f"v_mau_{c.id}",
                "khoi_" + ir_name(c.args.numerator_solid.replace(".", "_")),
                "khoi_" + ir_name(c.args.denominator_solid.replace(".", "_")),
            }
        for c in dung.of("ask_residual_volume"):
            muc_tieu |= {
                f"v_goc_{c.id}", *(f"v_cat_{c.id}_{i}" for i in range(1, len(c.args.subtracted_solids) + 1)),
                "khoi_" + ir_name(c.args.original_solid.replace(".", "_")),
                *("khoi_" + ir_name(s.replace(".", "_")) for s in c.args.subtracted_solids),
            }
        return KetQuaTuyen("SERVED", answers=tra, trace=dung.trace, program=program, points=dict(dung.pts),
                           metric=G.as_json(), kernel_check=True, spec=spec, exec_result=ket, chart_metric=G,
                           targets=tuple(sorted(muc_tieu)),
                           answer_exact=chinh_xac, length_unit=ky_hieu, checker=_kiem_tren_hinh(dung), declared_topology=to_po,
                           calls=[{"id": c.id, "fn": c.fn, "args": c.args.model_dump(), "quotes": list(c.quotes)}
                                  for c in calls])
    except TuChoi as e:
        return KetQuaTuyen("REFUSED", e.code, e.reason, e.calls, trace=dung.trace if dung else [], details=e.data)
