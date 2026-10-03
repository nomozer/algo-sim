# -*- coding: utf-8 -*-
"""Chứng chỉ giả định (W15) — đáp số không được phụ thuộc kích thước đề KHÔNG cho.

Thẩm quyền đăng ký: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` (viết TRƯỚC
module này). Mã khác văn bản ấy là lỗi của mã.

Ba trạng thái, một chiều:
  PROVEN_SAFE    chỉ từ chứng chỉ C0 (mọi literal trên lát cắt ghim bởi bất biến ĐỀ của
                 CÙNG thực thể) hoặc C1 (khuôn T1–T6 khớp ràng buộc server đọc từ đề, đủ
                 kích thước bắt buộc, đỉnh khuôn thoả chính xác, chạy lại trên hiện thực
                 chính tắc của khuôn cho đúng từng giá trị);
  DEPENDENT_…    chỉ từ một phép co giãn HỢP LỆ theo đúng một kích thước bắt buộc mà đề
                 không cho, làm đổi một giá trị người học thấy;
  UNDETERMINED   mọi trường hợp còn lại.
Tiền đề chỉ là ràng buộc server đọc từ câu đề (`shape_constraint`, các bộ phát bất biến
gọi KHÔNG kèm hợp đồng) — chú thích của mô hình không bao giờ là tiền đề.
"""
from __future__ import annotations

import copy
import functools
import re
import typing
from collections import Counter
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any, Callable

from ..geometry.exact import Vec3
from ..geometry.radical import is_exact_number
from .contract import SemanticProgramSpec
from .domain_profile import geometry_symbol_key
from .formation import _dinh_nghia, hoan_thien_dung_hinh
from .grounding_gate import bang_chung_doan
from .interpreter import SemanticProgramInterpreter
from .pipeline_adapter import DEFAULT_EXECUTION_BUDGET
from .plane_equation import bat_bien_mat_phang
from .point_coordinate import bat_bien_toa_do
from .postconditions import check_postconditions, check_source_invariants
from .segment_relation import bat_bien_chia_doan, bat_bien_do_dai
from .shape_constraint import RangBuoc, doc_rang_buoc, phan_chua_doc
from .solid_faces import phan_loai_bang_mat
from .source_entities import dinh_danh_thuc_the

PROVEN_SAFE = "PROVEN_SAFE"
DEPENDENT = "DEPENDENT_ON_UNSTATED_ASSUMPTION"
UNDETERMINED = "UNDETERMINED"
NOT_APPLICABLE = "NOT_APPLICABLE_NO_NUMERIC_ANSWER"
MA_PHU_THUOC = "ASSUMPTION_DETERMINES_ANSWER"
MA_CHUA_CHUNG_MINH = "ASSUMPTION_INVARIANCE_UNPROVEN"
#: Detail khi một tên trên lát cắt có nhiều định nghĩa với tới (ghi đè, bí danh, khôi phục) —
#: lỗi toàn vẹn của chương trình: route từ chối nó ở MỌI vùng (quyết định U5).
MA_NHIEU_DINH_NGHIA = "CLOSURE_MULTIPLE_DEFINITIONS"

#: Số lượt chạy lại interpreter được phép (chương trình tham chiếu C1 + phản ví dụ). Hết
#: ngân sách ⇒ không kết luận — không bao giờ là an toàn. Đọc lúc chạy (test vá được).
NGAN_SACH_CHAY_LAI = 24

# ── bảng toán hạng: kind IR → trường mang TÊN hoặc biểu thức con ───────────────

TOAN_HANG: dict[str, tuple[str, ...]] = {
    "measure": ("of", "wrt"),
    "assign": ("target_var", "expr"),
    "declare_point": ("target_var",),
    "construct_point": ("target_var", "expr"),
    "construct_line": ("target_var", "through_a", "through_b"),
    "construct_segment": ("target_var", "endpoint_a", "endpoint_b", "items"),
    "construct_plane": ("target_var", "through"),
    "construct_plane_from_equation": ("target_var",),
    "construct_polygon": ("target_var", "vertices"),
    "construct_solid": ("target_var", "vertices", "faces"),
    "construct_section": ("target_var", "solid", "plane"),
    "construct_curved_solid": ("target_var", "anchor", "apex_or_top", "rim_point", "radius", "height"),
    "var": ("name",),
    "arith": ("left", "right"),
    "unary": ("expr",),
    "literal": (),
    "midpoint": ("a", "b"),
    "divide_segment": ("a", "b"),
    "translate": ("point", "vector"),
    "vector_from_points": ("from_point", "to_point"),
    "project_onto": ("point", "target"),
    "intersect_line_line": ("line_a", "line_b"),
    "intersect_line_plane": ("line", "plane"),
    "intersect_plane_plane": ("plane_a", "plane_b"),
    "intersect_plane_curved": ("solid", "plane"),
    "intersect_plane_curved_ellipse": ("solid", "plane"),
    "plane_perpendicular_to_line": ("point", "line"),
}
#: Trường KHÔNG mang tên: literal (vai trò kiểm ở §4) hoặc từ mô tả phép.
KHONG_TOAN_HANG: dict[str, tuple[str, ...]] = {
    "literal": ("value",), "divide_segment": ("ratio",), "declare_point": ("at",),
    "construct_plane_from_equation": ("a", "b", "c", "d"), "measure": ("quantity",),
    "arith": ("op",), "unary": ("op",), "construct_curved_solid": ("curved_kind",),
}
_META = frozenset({"label", "model_assumption", "source_fact_id", "provenance"})
#: Cấu trúc dữ liệu và luồng điều khiển: ngoài phạm vi chứng chỉ ⇒ UNDETERMINED.
KHONG_HO_TRO = frozenset({
    "if", "while", "for_range", "for_each", "break", "return", "push", "pop", "enqueue", "dequeue",
    "set_insert", "set_remove", "map_set", "map_get", "write_index", "swap", "index", "length",
    "peek", "neighbors", "contains", "is_empty", "is_null", "compare", "logic", "not", "field"})
#: Kind được phép trên lát cắt C1 — phép dựng không phụ thuộc khung (§6.3).
KHUNG_TU_DO = frozenset({
    "assign", "declare_point", "construct_point", "construct_line", "construct_segment",
    "construct_plane", "construct_polygon", "construct_solid", "construct_section", "measure",
    "var", "arith", "unary", "literal", "midpoint", "divide_segment", "translate",
    "vector_from_points", "project_onto", "intersect_line_line", "intersect_line_plane",
    "intersect_plane_plane", "plane_perpendicular_to_line"})
PHEP_DO_C1 = frozenset({"volume", "area", "distance"})
_PHEP_TOAN_C1 = frozenset({"+", "-", "*"})
#: Bước con của MỘT câu lệnh: hành động → hành động khép nó (cùng `target`).
BUOC_CON = {"section_edge": "construct_section"}


@functools.lru_cache(maxsize=1)
def _cac_kieu_ir() -> dict[str, tuple[str, ...]]:
    """kind → các trường (trừ `kind`) của mọi mô hình IR trong `contract.py`."""
    from pydantic import BaseModel

    from . import contract as K

    ra: dict[str, tuple[str, ...]] = {}
    for obj in vars(K).values():
        if isinstance(obj, type) and issubclass(obj, BaseModel) and "kind" in obj.model_fields:
            for v in typing.get_args(obj.model_fields["kind"].annotation):
                if isinstance(v, str):
                    ra[v] = tuple(f for f in obj.model_fields if f != "kind")
    return ra


def kieu_ir_chua_phu() -> list[str]:
    """Kind/trường của lược đồ IR mà `TOAN_HANG` chưa phân loại. Rỗng ⇔ bảng phủ đủ."""
    thieu: list[str] = []
    for kind, fields in _cac_kieu_ir().items():
        if kind in KHONG_HO_TRO:
            continue
        if kind not in TOAN_HANG:
            thieu.append(kind)
            continue
        biet = set(TOAN_HANG[kind]) | set(KHONG_TOAN_HANG.get(kind, ())) | _META
        thieu += [f"{kind}.{f}" for f in fields if f not in biet]
    return sorted(thieu)


# ── kết quả ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class KetQuaGiaDinh:
    status: str
    certificate: str | None = None
    reason_code: str | None = None
    subjects: tuple[str, ...] = ()
    details: tuple[str, ...] = ()
    witness: dict | None = None


def _ket_qua(status: str, details: list[str], **kw: Any) -> KetQuaGiaDinh:
    ma = {DEPENDENT: MA_PHU_THUOC, UNDETERMINED: MA_CHUA_CHUNG_MINH}.get(status)
    return KetQuaGiaDinh(status=status, reason_code=ma, details=tuple(details), **kw)


class _Loi(Exception):
    def __init__(self, ma: str, ten: str = "") -> None:
        super().__init__(f"{ma} {ten}".strip())


def _id(x: Any) -> str:
    return dinh_danh_thuc_the(str(x))[0]


def _khoa(x: Any) -> str:
    """Khoá để so tên phía mô hình/chương trình với thực thể của đề (U4 · G2):
    `domain_profile.geometry_symbol_key` — A′ ≡ A1 ≡ A_prime ≡ Aprime, bốn lối viết đo được ở
    lượt sinh thật; tên không phải ký hiệu giữ định danh thường."""
    return geometry_symbol_key(str(x)) or _id(x)


def _nhan(*ten: str) -> str:
    return "".join(dinh_danh_thuc_the(t)[1] for t in ten)


def _la_so(v: Any) -> bool:
    return is_exact_number(v) or isinstance(v, float)


def _F(x: Any) -> Fraction:
    return Fraction(str(x).replace(" ", ""))


# ── định nghĩa với tới (R3) ──────────────────────────────────────────────────

@dataclass
class _DinhNghia:
    loai: str          # "khai" | "cau_lenh"
    nut: dict
    gia_tri: Any       # giá trị TẠI LÚC định nghĩa


class _ChiMuc:
    """Định nghĩa tĩnh (khai báo có giá trị đầu, câu lệnh) × lần ghi động (trace)."""

    def __init__(self, prog: dict, trace: list) -> None:
        self.tinh: dict[str, list[tuple[str, dict]]] = {}
        for m in prog["memory_declarations"]:
            if m.get("initial_value") is not None:
                self.tinh.setdefault(m["name"], []).append(("khai", m))
        self.cau_lenh = prog["statements"]
        for s in self.cau_lenh:
            for n in _dinh_nghia(s):
                self.tinh.setdefault(n, []).append(("cau_lenh", s))
        self.dong: dict[str, list] = {}
        for st in trace:
            if st.action == "init" or st.action in BUOC_CON or not st.target:
                continue
            self.dong.setdefault(st.target, []).append(st)
        self.dau = trace[0].memory_snapshot if trace and trace[0].action == "init" else {}

    def dinh_nghia(self, n: str) -> _DinhNghia:
        tinh, dong = self.tinh.get(n, []), self.dong.get(n, [])
        if [k for k, _ in tinh] == ["khai", "cau_lenh"] and len(dong) == 1 and not self._doc_truoc(n, tinh[1][1]):
            # U5: literal khai báo bị CHÍNH lệnh dựng ghi đè trước mọi lần đọc thì không với tới
            # ai — lệnh dựng là định nghĩa duy nhất (quy tắc sản phẩm cũ, derived_point B3).
            tinh = tinh[1:]
        if len(tinh) > 1 or len(dong) > 1 or (tinh and tinh[0][0] == "khai" and dong):
            raise _Loi(MA_NHIEU_DINH_NGHIA, n)
        if len(tinh) == 1 and tinh[0][0] == "khai":
            return _DinhNghia("khai", tinh[0][1], self.dau.get(n))
        if len(tinh) == 1 and len(dong) == 1:
            return _DinhNghia("cau_lenh", tinh[0][1], dong[0].memory_snapshot.get(n))
        raise _Loi("CLOSURE_UNRESOLVED_DEFINITION", n)

    def _doc_truoc(self, n: str, s: dict) -> bool:
        """Có câu lệnh nào TRƯỚC `s` đọc `n` không; không đọc được câu lệnh ⇒ coi như có."""
        for t in self.cau_lenh:
            if t is s:
                return False
            doc = _Doc("", _LatCat())
            try:
                doc.nut(t)
            except _Loi:
                return True
            if n in doc.ten:
                return True
        return True

    def ten_theo_khoa(self) -> dict[str, str]:
        """Khoá ký hiệu → tên chương trình; khoá mà hai tên cùng mang (`A` và `A_`) bị bỏ —
        không đoán tên nào là điểm nào."""
        dem = Counter(_khoa(n) for n in self.tinh)
        return {_khoa(n): n for n in self.tinh if dem[_khoa(n)] == 1}


# ── lát cắt ──────────────────────────────────────────────────────────────────

@dataclass
class _LatCat:
    da_xet: set[str] = field(default_factory=set)
    literal: list[tuple] = field(default_factory=list)
    kieu: set[str] = field(default_factory=set)
    phep_do: list[tuple[str, str]] = field(default_factory=list)
    phep_toan: set[str] = field(default_factory=set)


class _Doc:
    """Đọc MỘT câu lệnh định nghĩa: tên được đọc, literal, phép đo, phép toán."""

    def __init__(self, chu: str, lc: _LatCat) -> None:
        self.chu, self.lc = chu, lc
        self.ten: list[str] = []

    def nut(self, x: Any) -> None:
        if isinstance(x, str):
            self.ten.append(x)
        elif isinstance(x, list):
            for v in x:
                self.nut(v)
        elif isinstance(x, dict):
            self._dict(x)

    def _dict(self, x: dict) -> None:
        kind = x.get("kind")
        if kind is None:                                   # mục của construct_segment
            for k, v in x.items():
                if k in ("endpoint_a", "endpoint_b"):
                    self.nut(v)
                elif k not in ("name", "target_var", "label"):
                    raise _Loi("CLOSURE_INCOMPLETE", f"items.{k}")
            return
        if kind in KHONG_HO_TRO:
            raise _Loi("CLOSURE_UNSUPPORTED_KIND", kind)
        if kind not in TOAN_HANG:
            raise _Loi("CLOSURE_INCOMPLETE", kind)
        self.lc.kieu.add(kind)
        for f, v in x.items():
            if f == "kind" or f in _META:
                continue
            if f in KHONG_TOAN_HANG.get(kind, ()):
                self._khong_ten(kind, f, v, x)
            elif f not in TOAN_HANG[kind]:
                raise _Loi("CLOSURE_INCOMPLETE", f"{kind}.{f}")
            elif f != "target_var":
                self.nut(v)

    def _khong_ten(self, kind: str, f: str, v: Any, x: dict) -> None:
        if kind == "literal":
            self.lc.literal.append(("literal", self.chu, v))
        elif kind == "divide_segment":
            self.lc.literal.append(("ti_so", self.chu, x.get("a"), x.get("b"), v))
        elif kind == "declare_point":
            self.lc.literal.append(("diem", self.chu, v))
        elif kind == "construct_plane_from_equation" and f == "a":
            self.lc.literal.append(("mat_phang", self.chu, tuple(x.get(k) for k in "abcd")))
        elif kind == "measure":
            self.lc.phep_do.append((self.chu, v))
        elif kind in ("arith", "unary"):
            self.lc.phep_toan.add(v)


def _lat_cat(goc: list[str], cm: _ChiMuc) -> _LatCat:
    lc = _LatCat()
    ngan = list(goc)
    while ngan:
        n = ngan.pop()
        if n in lc.da_xet:
            continue
        d = cm.dinh_nghia(n)
        lc.da_xet.add(n)
        if d.loai == "khai":
            kieu = d.nut.get("type")
            loai = "diem" if kieu == "point3" else ("vo_huong" if kieu in ("float", "int") else "khai_khac")
            lc.literal.append((loai, n, d.nut.get("initial_value") if loai != "khai_khac" else kieu))
            continue
        doc = _Doc(n, lc)
        doc.nut(d.nut)
        ngan.extend(t for t in doc.ten if t != n)
    return lc


# ── bằng chứng từ đề (§2) ────────────────────────────────────────────────────

def bat_bien_tu_de(problem_text: str) -> tuple:
    """Bốn bộ phát bất biến gọi KHÔNG kèm hợp đồng — `_van_ban(None, …)` chỉ đọc câu đề."""
    return (bat_bien_do_dai(None, problem_text) + bat_bien_chia_doan(None, problem_text)
            + bat_bien_mat_phang(None, problem_text) + bat_bien_toa_do(None, problem_text))


_TEN_DO_DAI = re.compile(r"([A-Z]\d*(?:_prime)?)([A-Z]\d*(?:_prime)?)_length")


def _vai_tro(lit: tuple, de: str, inv: tuple, khuon: set[str] | None) -> str | None:
    loai = lit[0]
    if loai == "diem":
        try:
            xyz = [_F(c) for c in lit[2]]
        except (ValueError, TypeError, ZeroDivisionError):
            return None
        for i in inv:
            if i.kind == "point_coordinate" and [_khoa(p) for p in i.points] == [_khoa(lit[1])]:
                if [_F(c) for c in i.coefficients] == xyz:
                    return "SOURCE_DATUM"
        return "LAYOUT_FRONTIER" if khuon is not None and _khoa(lit[1]) in {_khoa(v) for v in khuon} else None
    if loai == "vo_huong":
        m = _TEN_DO_DAI.fullmatch(lit[1])
        try:
            return "SOURCE_DATUM" if m and bang_chung_doan(de, (m[1], m[2]), _F(lit[2])) else None
        except (ValueError, ZeroDivisionError):
            return None
    if loai == "mat_phang":
        he = [_F(c) for c in lit[2]]
        for i in inv:
            if i.kind == "plane_equation" and i.coefficients:
                g = [_F(c) for c in i.coefficients]
                k = next((g[j] / he[j] for j in range(4) if he[j] != 0), None)
                if k and all(g[j] == k * he[j] for j in range(4)):
                    return "SOURCE_DATUM"
        return None
    if loai == "ti_so":
        _l, m_ten, a, b, t = lit
        for i in inv:
            if i.kind != "segment_division" or len(i.points) != 3 or not i.expected:
                continue
            A, B, M = (_khoa(p) for p in i.points)
            if _khoa(m_ten) != M or {_khoa(a), _khoa(b)} != {A, B}:
                continue
            ky_vong = _F(i.expected) if (_khoa(a), _khoa(b)) == (A, B) else 1 - _F(i.expected)
            try:
                return "SOURCE_DATUM" if _F(t) == ky_vong else None
            except (ValueError, ZeroDivisionError):
                return None
        return None
    return None                                              # literal số học, khai báo khác


# ── bốn trạng thái của quan hệ mô hình (§2.2) ───────────────────────────────

def _vuong_goc_ngam(rb: tuple[RangBuoc, ...]) -> set[frozenset]:
    """Cặp đường vuông góc mà đề NÓI (trực tiếp hoặc qua KIỂU khối/đáy đã nêu)."""
    ra: set[frozenset] = set()

    def cap(a, b, c, d):
        ra.add(frozenset((frozenset((a, b)), frozenset((c, d)))))

    def chu_nhat(v):
        for i in range(len(v)):
            cap(v[i], v[i - 1], v[i], v[(i + 1) % len(v)])

    for x in rb:
        e = x.entities
        if x.kind == "line_perp_line":
            cap(*e)
        elif x.kind == "right_triangle":
            cap(e[0], e[1], e[0], e[2])
        elif x.kind in ("base_rectangle", "base_square") and len(e) == 4:
            chu_nhat(e)
        elif x.kind in ("right_prism", "cuboid", "cube") and e:
            k = len(e) // 2
            for i in range(k):
                for j in ((i + 1) % k, i - 1):
                    cap(e[i], e[k + i], e[i], e[j])
            if x.kind != "right_prism" and k == 4:
                chu_nhat(e[:k])
                chu_nhat(e[k:])
    return ra


def _trang_thai_quan_he(contract: Any, rb: tuple[RangBuoc, ...]) -> tuple[list[str], bool]:
    # Tên của hợp đồng (phía mô hình) so với thực thể đề trong CÙNG không gian khoá ký hiệu.
    rb = tuple(RangBuoc(x.kind, tuple(_khoa(e) for e in x.entities), x.value, x.span) for x in rb)
    dong = lambda a, b: frozenset((_khoa(a), _khoa(b)))  # noqa: E731
    ra, bac = [], False
    ngam = _vuong_goc_ngam(rb)
    for r in getattr(contract, "geometric_relations", ()) or ():
        line = list(r.line or ())
        if len(line) != 2:
            continue
        L = dong(*line)
        if r.kind == "perpendicular_lines" and len(r.other_line or ()) == 2:
            K = dong(*r.other_line)
            xac = frozenset((L, K)) in ngam
            chung = L & K
            trai = any(x.kind == "right_triangle" and len(chung) == 1 and set(L | K) == set(x.entities)
                       and next(iter(chung)) != x.entities[0] for x in rb)
        elif r.kind == "perpendicular_line_plane":
            P = {_khoa(p) for p in (r.plane or ())}
            xac = any((x.kind == "line_perp_plane" and dong(*x.entities[:2]) == L and P <= set(x.entities[2:]))
                      or (x.kind in ("right_prism", "cuboid", "cube") and x.entities
                          and _la_canh_ben(x.entities, L) and P <= set(x.entities[:len(x.entities) // 2]))
                      for x in rb)
            trai = any(x.kind == "oblique_prism" and _la_canh_ben(x.entities, L) for x in rb)
        else:
            continue
        trang = ("MODEL_ASSUMPTION" if r.model_assumption else "REFUTED_BY_SOURCE" if trai
                 else "SERVER_CONFIRMED" if xac else "UNCONFIRMED")
        bac = bac or trang == "REFUTED_BY_SOURCE"
        ra.append(f"RELATION {r.kind}({','.join(line)}|{','.join(r.other_line or r.plane or ())}): {trang}")
    return ra, bac


def _la_canh_ben(ent: tuple[str, ...], L: frozenset) -> bool:
    k = len(ent) // 2
    return any(frozenset((ent[i], ent[k + i])) == L for i in range(k))


# ── C1: khuôn (§6) ───────────────────────────────────────────────────────────

@dataclass
class _KichThuoc:
    nhan: str
    lop: list[tuple[str, str]]
    gia_tri: Fraction | None
    keo: tuple            # ("phap_tuyen", X, (p, q, r)) | ("canh", X, Y) | ("vi_tu", X) | ("vi_tu_mat", X, (p, q, r))


@dataclass
class _Khuon:
    loai: str
    dinh: tuple[str, ...]
    rang_buoc: list[tuple[str, Callable[[dict], bool]]]
    kich_thuoc: list[_KichThuoc]
    tien_de: list[RangBuoc]
    #: Hiện thực CHÍNH TẮC của khuôn từ các kích thước bắt buộc (cùng thứ tự `kich_thuoc`).
    chinh_tac: Callable[[list[Fraction]], dict[str, Vec3]]


def _o(x=0, y=0, z=0) -> Vec3:
    return Vec3.of(x, y, z)


def _chu_nhat_chinh_tac(day: tuple, L1: Fraction, L2: Fraction) -> dict[str, Vec3]:
    a, b, c, d = day
    return {a: _o(), b: _o(L1), c: _o(L1, L2), d: _o(0, L2)}


def _vuong(V, x, y, z) -> bool:
    return (V[y] - V[x]).dot(V[z] - V[x]) == 0


def _goc_vuong_tai(rb, day: tuple, x: str) -> RangBuoc | None:
    con = set(day) - {x}
    for r in rb:
        if r.kind == "right_triangle" and r.entities[0] == x and set(r.entities) == set(day):
            return r
        if r.kind == "line_perp_line":
            a, b = set(r.entities[:2]), set(r.entities[2:])
            if x in a and x in b and (a | b) - {x} == con:
                return r
    return None


def _goc_vuong_bat_ky(rb, day: tuple) -> tuple[str, RangBuoc] | None:
    k = len(day)
    for i, x in enumerate(day):
        ke = {day[i - 1], day[(i + 1) % k]}
        for r in rb:
            if r.kind == "line_perp_line":
                a, b = set(r.entities[:2]), set(r.entities[2:])
                if x in a and x in b and (a | b) - {x} == ke:
                    return x, r
    return None


def _do_dai_tu_rb(rb, kind, ent) -> tuple[Fraction | None, list]:
    for r in rb:
        if r.kind == kind and r.entities == ent and r.value is not None:
            return r.value, [r]
    return None, []


def _khuon_chop(rb, S: str, day: tuple, ent: tuple):
    chan = [(r, (set(r.entities[:2]) - {S}).pop()) for r in rb
            if r.kind == "line_perp_plane" and S in r.entities[:2] and len(set(r.entities[:2])) == 2
            and (set(r.entities[:2]) - {S}) <= set(day) and set(r.entities[2:]) <= set(day)
            and len(set(r.entities[2:])) >= 3]
    if not chan:
        return "TEMPLATE_NOT_MATCHED pyramid: no apex edge stated perpendicular to the base"
    r_chan, X = chan[0]
    cao, rb_cao = _do_dai_tu_rb(rb, "height", ent)
    keo_cao = ("phap_tuyen", X, day[:3])
    tien_de = [r_chan, *rb_cao]
    rbuoc: list = [("apex edge ⊥ base", lambda V: all((V[S] - V[X]).dot(V[p] - V[X]) == 0 for p in day if p != X)),
                   ("apex off the base", lambda V: V[S] != V[X])]
    if cao is not None:
        rbuoc.append(("height", lambda V: (V[S] - V[X]).dot(V[S] - V[X]) == cao * cao))
    if len(day) == 3:
        gv = _goc_vuong_tai(rb, day, X)
        if gv is None:
            return "TEMPLATE_NOT_MATCHED T1: no right angle at the foot of the apex edge"
        Y, Z = [p for p in day if p != X]
        rbuoc.append(("right angle at the foot", lambda V: _vuong(V, X, Y, Z)))
        return _Khuon("T1", (S, *day), rbuoc,
                      [_KichThuoc(_nhan(X, Y), [(X, Y)], None, ("canh", X, Y)),
                       _KichThuoc(_nhan(X, Z), [(X, Z)], None, ("canh", X, Z)),
                       _KichThuoc(_nhan(S, X), [(S, X)], cao, keo_cao)], tien_de + [gv],
                      lambda L: {X: _o(), Y: _o(L[0]), Z: _o(0, L[1]), S: _o(0, 0, L[2])})
    if len(day) == 4:
        a, b, c, d = day
        vuong_day = next((r for r in rb if r.kind == "base_square" and set(r.entities) == set(day)), None)
        cn = next((r for r in rb if r.kind == "base_rectangle" and set(r.entities) == set(day)), None)
        gv = None
        if cn is None and vuong_day is None:
            hbh = next((r for r in rb if r.kind in ("base_parallelogram", "base_rhombus")
                        and set(r.entities) == set(day)), None)
            gv = _goc_vuong_bat_ky(rb, day) if hbh else None
            if gv is None:
                return "TEMPLATE_NOT_MATCHED T2: base not stated rectangle/square (or parallelogram + right angle)"
            cn = hbh
            if hbh.kind == "base_rhombus":
                vuong_day = hbh
        rbuoc += [("base parallelogram", lambda V: V[b] - V[a] == V[c] - V[d]),
                  ("base right angle", lambda V: _vuong(V, a, b, d))]
        canh_day = vuong_day.value if vuong_day is not None and vuong_day.kind == "base_square" else None
        if vuong_day is not None:
            rbuoc.append(("base square", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == (V[d] - V[a]).dot(V[d] - V[a])))
            if canh_day is not None:
                rbuoc.append(("base side", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == canh_day * canh_day))
            lop = [_KichThuoc(_nhan(a, b), [(a, b), (b, c), (c, d), (d, a)], canh_day, ("vi_tu_mat", a, day[:3]))]
        else:
            lop = [_KichThuoc(_nhan(a, b), [(a, b), (d, c)], None, ("canh", a, b)),
                   _KichThuoc(_nhan(a, d), [(a, d), (b, c)], None, ("canh", a, d))]
        tien_de += [x for x in (cn, vuong_day, gv[1] if gv else None) if x is not None]

        def chinh_tac(L: list[Fraction]) -> dict[str, Vec3]:
            day_ct = _chu_nhat_chinh_tac(day, L[0], L[0] if len(L) == 2 else L[1])
            return {**day_ct, S: day_ct[X] + _o(0, 0, L[-1])}

        return _Khuon("T2", (S, *day), rbuoc, lop + [_KichThuoc(_nhan(S, X), [(S, X)], cao, keo_cao)], tien_de,
                      chinh_tac)
    return "TEMPLATE_NOT_MATCHED pyramid base size"


def _khuon_lang_tru(rb, day: tuple, tren: tuple, ent: tuple, kieu: set[str], rb_kieu: list):
    k = len(day)
    ben = [(day[i], tren[i]) for i in range(k)]
    cao, rb_cao = _do_dai_tu_rb(rb, "height", ent)
    b0 = day[0]
    rbuoc: list = [(f"translation {day[i]}{tren[i]}", lambda V, i=i: V[tren[i]] - V[day[i]] == V[tren[0]] - V[day[0]])
                   for i in range(1, k)]
    rbuoc += [("lateral ⊥ base", lambda V: all((V[tren[0]] - V[day[0]]).dot(V[day[(i + 1) % k]] - V[day[i]]) == 0
                                               for i in range(k))),
              ("lateral non-zero", lambda V: V[tren[0]] != V[day[0]])]
    if cao is not None:
        rbuoc.append(("height", lambda V: (V[tren[0]] - V[day[0]]).dot(V[tren[0]] - V[day[0]]) == cao * cao))
    ben_kt = _KichThuoc(_nhan(day[0], tren[0]), ben, cao, ("phap_tuyen", b0, day[:3]))
    tien_de = [*rb_kieu, *rb_cao]
    canh_cua = lambda i, j: [(day[i], day[j]), (tren[i], tren[j])]  # noqa: E731

    def nap(day_ct: dict[str, Vec3], h: Fraction) -> dict[str, Vec3]:
        return {**day_ct, **{tren[i]: day_ct[day[i]] + _o(0, 0, h) for i in range(k)}}
    if k == 3 and "right_prism" in kieu:
        X, gv = next(((x, g) for x in day if (g := _goc_vuong_tai(rb, day, x))), (None, None))
        if X is None:
            return "TEMPLATE_NOT_MATCHED T3: no right angle on the base"
        Y, Z = [p for p in day if p != X]
        i, j, l = day.index(X), day.index(Y), day.index(Z)
        rbuoc.append(("right angle on the base", lambda V: _vuong(V, X, Y, Z)))
        return _Khuon("T3", day + tren, rbuoc,
                      [_KichThuoc(_nhan(X, Y), canh_cua(i, j), None, ("canh", X, Y)),
                       _KichThuoc(_nhan(X, Z), canh_cua(i, l), None, ("canh", X, Z)), ben_kt],
                      tien_de + [gv], lambda L: nap({X: _o(), Y: _o(L[0]), Z: _o(0, L[1])}, L[2]))
    if k == 3:
        return "TEMPLATE_NOT_MATCHED T3: the prism is not stated right ('lăng trụ đứng')"
    if k != 4:
        return "TEMPLATE_NOT_MATCHED prism base size"
    a, b, c, d = day
    rbuoc += [("base parallelogram", lambda V: V[b] - V[a] == V[c] - V[d]),
              ("base right angle", lambda V: _vuong(V, a, b, d))]
    vuong_day = next((r for r in rb if r.kind == "base_square" and set(r.entities) == set(day)), None)
    if "cube" in kieu:
        canh, rb_canh = _do_dai_tu_rb(rb, "cube_edge", ent)
        rbuoc.append(("cube edges equal", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == (V[d] - V[a]).dot(V[d] - V[a])
                      == (V[tren[0]] - V[a]).dot(V[tren[0]] - V[a])))
        if canh is not None:
            rbuoc.append(("cube edge", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == canh * canh))
        moi_canh = canh_cua(0, 1) + canh_cua(1, 2) + canh_cua(2, 3) + canh_cua(3, 0) + ben
        return _Khuon("T5", day + tren, rbuoc, [_KichThuoc(_nhan(a, b), moi_canh, canh, ("vi_tu", a))],
                      tien_de + rb_canh, lambda L: nap(_chu_nhat_chinh_tac(day, L[0], L[0]), L[0]))
    if "cuboid" in kieu:
        return _Khuon("T4", day + tren, rbuoc,
                      [_KichThuoc(_nhan(a, b), canh_cua(0, 1) + canh_cua(3, 2), None, ("canh", a, b)),
                       _KichThuoc(_nhan(a, d), canh_cua(0, 3) + canh_cua(1, 2), None, ("canh", a, d)), ben_kt],
                      tien_de, lambda L: nap(_chu_nhat_chinh_tac(day, L[0], L[1]), L[2]))
    if "right_prism" in kieu and vuong_day is not None:
        s = vuong_day.value
        rbuoc.append(("base square", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == (V[d] - V[a]).dot(V[d] - V[a])))
        if s is not None:
            rbuoc.append(("base side", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == s * s))
        canh_day = canh_cua(0, 1) + canh_cua(1, 2) + canh_cua(2, 3) + canh_cua(3, 0)
        return _Khuon("T6", day + tren, rbuoc,
                      [_KichThuoc(_nhan(a, b), canh_day, s, ("vi_tu_mat", a, day[:3])), ben_kt],
                      tien_de + [vuong_day], lambda L: nap(_chu_nhat_chinh_tac(day, L[0], L[0]), L[1]))
    return "TEMPLATE_NOT_MATCHED prism type"


def _nhan_khuon(rb: tuple[RangBuoc, ...], cm: _ChiMuc, prog: dict):
    """Khuôn §6.2 từ ràng buộc ĐỌC ĐƯỢC + ký hiệu khối của đề (hoặc khối không tên → khối
    DUY NHẤT của chương trình). → `(_Khuon, ánh xạ thực thể → tên bộ nhớ)` hoặc lý do."""
    co_ten = {r.entities for r in rb if r.kind in ("pyramid", "prism") and r.entities}
    if len(co_ten) == 1:
        ent = next(iter(co_ten))
        if len({_khoa(e) for e in ent}) != len(set(ent)):
            return "TEMPLATE_NOT_MATCHED two solid vertices share one symbol key"
        theo_khoa = cm.ten_theo_khoa()
        anh_xa = {e: theo_khoa[_khoa(e)] for e in ent if _khoa(e) in theo_khoa}
        rb_kieu: list[RangBuoc] = []                       # ký hiệu + kiểu, mỗi kind một lần
        for r in rb:
            if r.entities == ent and r.kind not in {x.kind for x in rb_kieu}:
                rb_kieu.append(r)
        if any(r.kind == "pyramid" for r in rb_kieu):
            k = _khuon_chop(rb, ent[0], ent[1:], ent)
            if isinstance(k, _Khuon):
                k.tien_de = rb_kieu + k.tien_de
        else:
            n = len(ent) // 2
            k = _khuon_lang_tru(rb, ent[:n], ent[n:], ent, {r.kind for r in rb_kieu}, rb_kieu)
        return (k, anh_xa) if isinstance(k, _Khuon) else k
    if co_ten:
        return "TEMPLATE_NOT_MATCHED more than one named solid"
    khong_ten = [r for r in rb if r.entities == () and r.kind in ("right_prism", "base_square", "height")]
    if not any(r.kind == "right_prism" for r in khong_ten) or not any(r.kind == "base_square" for r in khong_ten):
        return "TEMPLATE_NOT_MATCHED no solid notation"
    khoi = [s for s in prog["statements"] if s.get("kind") == "construct_solid"]
    if len(khoi) != 1:
        return "TEMPLATE_NOT_MATCHED unnamed solid: the program does not build exactly one solid"
    dinh = list(khoi[0]["vertices"])
    mat = [[dinh.index(v) if isinstance(v, str) else v for v in f] for f in khoi[0]["faces"]]
    rb_ao = tuple(RangBuoc(r.kind, tuple(_id(x) for x in r.entities), r.value, r.span) for r in rb)
    for loai, a, b in phan_loai_bang_mat(len(dinh), mat):
        if loai != "prism" or len(a) != 4:
            continue
        day, tren = tuple(_id(dinh[i]) for i in a), tuple(_id(dinh[i]) for i in b)
        gan = tuple(RangBuoc(r.kind, (day if r.kind == "base_square" else day + tren) if r.entities == ()
                             else r.entities, r.value, r.span) for r in rb_ao)
        k = _khuon_lang_tru(gan, day, tren, day + tren, {"right_prism"},
                            [r for r in gan if r.entities == day + tren])
        if isinstance(k, _Khuon):
            anh_xa = {_id(v): v for v in dinh}
            V = _gia_tri_dinh(k.dinh, anh_xa, cm)
            if V is not None and all(f(V) for _n, f in k.rang_buoc):
                k.tien_de = [r for r in rb if r.entities == ()]
                return k, anh_xa
    return "TEMPLATE_NOT_MATCHED unnamed solid: no reading of its face table satisfies the text"


def _gia_tri_dinh(dinh: tuple[str, ...], anh_xa: dict[str, str], cm: _ChiMuc) -> dict | None:
    V = {}
    for e in dinh:
        if e not in anh_xa:
            return None
        v = cm.dinh_nghia(anh_xa[e]).gia_tri
        if not isinstance(v, Vec3):
            return None
        V[e] = v
    return V


def _ap_do_dai(khuon: _Khuon, do_dai: dict[frozenset, Fraction]) -> list:
    """Mọi độ dài đề cho trên một cặp đỉnh khuôn phải thoả chính xác."""
    dinh = set(khuon.dinh)
    return [(f"|{''.join(sorted(c))}| = {L}", lambda V, p=sorted(c)[0], q=sorted(c)[1], L=L:
             (V[p] - V[q]).dot(V[p] - V[q]) == L * L)
            for c, L in do_dai.items() if c <= dinh and len(c) == 2]


def _da_cho(kt: _KichThuoc, do_dai: dict[frozenset, Fraction]) -> bool:
    return kt.gia_tri is not None or any(frozenset(c) in do_dai for c in kt.lop)


# ── đối chiếu độc lập: chạy lại trên một hiện thực CHÍNH TẮC (§6.5, đính chính Task 5) ──
#
# Bản đăng ký ghi "đối chiếu với `compiler.bien_dich`". Không làm được trên đường sản
# phẩm: `test_structured_geometry_relations::test_Y` giữ bất biến *không tệp sản phẩm nào
# ngoài gói compiler tham chiếu gói ấy* (`LLM_ONLY`, compiler CÓ nhưng CHƯA BẬT). Thực chất
# giữ nguyên: một hiện thực THỨ HAI của khuôn, dựng từ kích thước đề cho chứ không từ toạ
# độ ứng viên, phải cho đúng từng giá trị bị phủ. Đối chiếu với compiler chuyển sang census
# (chẩn đoán, không phải sản phẩm).

def _hien_thuc_chinh_tac(khuon: _Khuon, do_dai: dict[frozenset, Fraction]) -> dict[str, Vec3] | None:
    L = []
    for kt in khuon.kich_thuoc:
        v = kt.gia_tri if kt.gia_tri is not None else next(
            (do_dai[frozenset(c)] for c in kt.lop if frozenset(c) in do_dai), None)
        if v is None:
            return None
        L.append(v)
    return khuon.chinh_tac(L)


def _doi_chieu_chinh_tac(prog: dict, khuon: _Khuon, anh_xa: dict[str, str], do_dai: dict, phu: list[str],
                         exec_res, ngan: list[int], budget: int) -> tuple[bool, str]:
    ct = _hien_thuc_chinh_tac(khuon, do_dai)
    if ct is None:
        return False, "C1_CROSS_CHECK_NO_CANONICAL_REALISATION"
    if ngan[0] >= NGAN_SACH_CHAY_LAI:
        return False, "BUDGET_EXHAUSTED (canonical re-run)"
    ngan[0] += 1
    d2 = copy.deepcopy(prog)

    ve_de = {n: e for e, n in anh_xa.items()}

    def moi(ten: str) -> list[str] | None:
        e = ve_de.get(ten)
        if e not in ct:
            return None
        return [str(ct[e].x), str(ct[e].y), str(ct[e].z)]

    for m in d2["memory_declarations"]:
        if m.get("type") == "point3" and isinstance(m.get("initial_value"), list) and (v := moi(m["name"])):
            m["initial_value"] = v
    for s in d2["statements"]:
        if s.get("kind") == "declare_point" and isinstance(s.get("at"), list) and (v := moi(s["target_var"])):
            s["at"] = v
    try:
        res2 = _chay(SemanticProgramSpec.model_validate(d2), budget)
    except Exception as e:  # noqa: BLE001
        return False, f"C1_CROSS_CHECK_REFERENCE_FAILED {type(e).__name__}"
    lech = [n for n in phu if res2.final_memory.get(n) != exec_res.final_memory.get(n)]
    if lech:
        return False, f"C1_CROSS_CHECK_DISAGREES {lech[0]}"
    return True, f"C1_CROSS_CHECK_AGREES canonical re-run, {len(phu)} value(s)"


def _chay(sp: SemanticProgramSpec, budget: int = DEFAULT_EXECUTION_BUDGET):
    return SemanticProgramInterpreter(max_steps=budget).execute(sp)


# ── phản ví dụ (§7) ──────────────────────────────────────────────────────────

def _ham_keo(keo: tuple, V: dict) -> Callable[[Vec3], Vec3]:
    loai, X = keo[0], V[keo[1]]
    if loai == "vi_tu":
        return lambda p: X + (p - X).scale(2)
    if loai == "canh":
        u = V[keo[2]] - X
        return lambda p: p + u.scale((p - X).dot(u) / u.dot(u))
    a, b, c = (V[t] for t in keo[2])
    n = (b - a).cross(c - a)
    if loai == "phap_tuyen":
        return lambda p: p + n.scale((p - X).dot(n) / n.dot(n))
    return lambda p: X + (p - X).scale(2) - n.scale((p - X).dot(n) / n.dot(n))      # "vi_tu_mat"


def _phan_vi_du(contract, prog: dict, exec_res, ten_da_hoa_giai, khuon: _Khuon, anh_xa: dict, V: dict,
                kt: _KichThuoc, do_dai: dict, inv: tuple, de: str, phu: list[str], ngan: list[int],
                budget: int) -> tuple[dict | None, str]:
    f = _ham_keo(kt.keo, V)
    d2 = copy.deepcopy(prog)

    def keo(owner: str, xyz: list) -> list | None:
        if _vai_tro(("diem", owner, xyz), de, inv, None) == "SOURCE_DATUM":
            return None
        q = f(Vec3.of(*[_F(c) for c in xyz]))
        return [str(q.x), str(q.y), str(q.z)]

    doi = 0
    for m in d2["memory_declarations"]:
        if m.get("type") == "point3" and isinstance(m.get("initial_value"), list):
            moi = keo(m["name"], m["initial_value"])
            if moi is not None and moi != [str(_F(c)) for c in m["initial_value"]]:
                m["initial_value"], doi = moi, doi + 1
    for s in d2["statements"]:
        if s.get("kind") == "declare_point" and isinstance(s.get("at"), list):
            moi = keo(s["target_var"], s["at"])
            if moi is not None and moi != [str(_F(c)) for c in s["at"]]:
                s["at"], doi = moi, doi + 1
    if not doi:
        return None, "CE_NOTHING_TO_STRETCH"
    if ngan[0] >= NGAN_SACH_CHAY_LAI:
        return None, "CE_BUDGET_EXHAUSTED"
    ngan[0] += 1
    try:
        sp2 = SemanticProgramSpec.model_validate(d2)
        res2 = _chay(sp2, budget)
        V2 = _gia_tri_dinh(khuon.dinh, anh_xa, _ChiMuc(d2, res2.trace))
    except Exception as e:  # noqa: BLE001 — ngoại lệ: không kết luận, không bao giờ là phản ví dụ
        return None, f"CE_INCONCLUSIVE {type(e).__name__}"
    if res2.status != "completed" or V2 is None:
        return None, "CE_INCONCLUSIVE execution"
    hong = [n for n, g in khuon.rang_buoc + _ap_do_dai(khuon, do_dai) if not g(V2)]
    if hong:
        return None, f"CE_INVALID breaks {hong[0]}"
    for hd in (contract, contract.model_copy(update={"source_invariants": tuple(inv)})):
        if not check_source_invariants(hd, res2, ten_da_hoa_giai=ten_da_hoa_giai).ok:
            return None, "CE_INVALID breaks a text invariant"
    if check_postconditions(contract, sp2, res2, ten_da_hoa_giai=ten_da_hoa_giai).violations:
        return None, "CE_INVALID breaks a postcondition"
    doi_gia = {n: [str(exec_res.final_memory.get(n)), str(res2.final_memory.get(n))] for n in phu
               if res2.final_memory.get(n) != exec_res.final_memory.get(n)}
    if not doi_gia:
        return None, "CE_NO_CHANGE"
    return {"description": f"x2 {kt.keo[0]} anchored at {kt.keo[1]} ({kt.nhan})", "program": d2,
            "changes": doi_gia}, "CE_VALID"


# ── cổng ─────────────────────────────────────────────────────────────────────

def _gia_tri_bi_phu(contract: Any, exec_res, ten_da_hoa_giai) -> list[str]:
    """Mọi giá trị SỐ người học thấy: mọi bước MEASUREMENT + witness của nghĩa vụ (§1)."""
    ra: list[str] = []
    for st in exec_res.trace:
        if st.semantic_kind == "MEASUREMENT" and st.target and _la_so(st.memory_snapshot.get(st.target)):
            ra.append(st.target)
    for o in getattr(contract, "obligations", ()) or ():
        w = (ten_da_hoa_giai or {}).get(o.witness, o.witness) if o.witness else None
        if w and _la_so(exec_res.final_memory.get(w)):
            ra.append(w)
    return list(dict.fromkeys(ra))


def kiem_gia_dinh(contract: Any, spec: SemanticProgramSpec, exec_res, ten_da_hoa_giai=None, *,
                  execution_budget: int = DEFAULT_EXECUTION_BUDGET) -> KetQuaGiaDinh:
    """Chứng chỉ cho chương trình ĐÃ bổ sung dựng hình và ĐÃ chạy (đầu vào của route)."""
    de = getattr(contract, "problem_text", "") or ""
    phu = _gia_tri_bi_phu(contract, exec_res, ten_da_hoa_giai)
    if not phu:
        return KetQuaGiaDinh(NOT_APPLICABLE, details=("NO_NUMERIC_VALUE_SHOWN",))
    prog = spec.model_dump(mode="json", exclude_none=True)
    if any(s.get("kind") in KHONG_HO_TRO for s in prog["statements"]):
        return _ket_qua(UNDETERMINED, ["CLOSURE_UNSUPPORTED_KIND control flow"])
    cm = _ChiMuc(prog, exec_res.trace)
    try:
        lc = _lat_cat(phu, cm)
    except _Loi as e:
        return _ket_qua(UNDETERMINED, [str(e)])
    rb = doc_rang_buoc(de)
    inv = bat_bien_tu_de(de)
    do_dai = {frozenset(_id(p) for p in i.points): _F(i.expected) for i in inv
              if i.kind == "segment_length" and len(i.points) == 2 and i.expected}
    details, bac = _trang_thai_quan_he(contract, rb)
    if bac:
        return _ket_qua(UNDETERMINED, details + ["RELATION_REFUTED_BY_SOURCE"])

    # C0 — lát cắt ghim bởi nguồn
    khong_vai = [lit for lit in lc.literal if _vai_tro(lit, de, inv, None) != "SOURCE_DATUM"]
    if not khong_vai:
        return _ket_qua(PROVEN_SAFE, details + [f"C0 {len(lc.literal)} literal(s) pinned by the text"],
                        certificate="C0")

    # C1 — cấu hình do đề xác định
    k = _nhan_khuon(rb, cm, prog)
    if isinstance(k, str):
        return _ket_qua(UNDETERMINED, details + [k] + [f"NO_ROLE {lit[0]} {lit[1]}" for lit in khong_vai])
    khuon, anh_xa = k
    try:
        V = _gia_tri_dinh(khuon.dinh, anh_xa, cm)
    except _Loi as e:
        return _ket_qua(UNDETERMINED, details + [f"{khuon.loai} {e}"])
    if V is None:
        return _ket_qua(UNDETERMINED, details + [f"{khuon.loai} TEMPLATE_VERTEX_MISSING"])
    hong = [n for n, f in khuon.rang_buoc + _ap_do_dai(khuon, do_dai) if not f(V)]
    if hong:
        return _ket_qua(UNDETERMINED, details + [f"{khuon.loai} TEMPLATE_CONSTRAINT_VIOLATED {hong[0]}"])
    tien_de = list(dict.fromkeys(
        f"PREMISE {r.kind}({','.join(r.entities)})" + (f"={r.value}" if r.value is not None else "")
        + f" @[{r.span[0]},{r.span[1]}]" for r in khuon.tien_de))
    thieu = [kt for kt in khuon.kich_thuoc if not _da_cho(kt, do_dai)]
    ngan = [0]
    if thieu:
        # §7 (đính chính Task 6): phản ví dụ chỉ nói "đề không cho" khi server đã đọc trọn
        # phần dữ kiện VÀ kiểm được mọi ràng buộc đọc được trên nhân chứng (= tiền đề khuôn).
        chua_doc = phan_chua_doc(de)
        da_kiem = {(r.kind, r.entities, r.value) for r in khuon.tien_de}
        ngoai = [r for r in rb if (r.kind, r.entities, r.value) not in da_kiem]
        if chua_doc or ngoai:
            return _ket_qua(UNDETERMINED, details + tien_de + [f"{khuon.loai} MISSING {kt.nhan}" for kt in thieu]
                            + ([f"CE_TEXT_NOT_FULLY_READ {' '.join(chua_doc[:8])}"] if chua_doc else [])
                            + [f"CE_CONSTRAINT_NOT_CHECKED {r.kind}({','.join(r.entities)})" for r in ngoai])
        for kt in thieu:
            chung, ly_do = _phan_vi_du(contract, prog, exec_res, ten_da_hoa_giai, khuon, anh_xa, V, kt, do_dai,
                                       inv, de, phu, ngan, execution_budget)
            if chung is not None:
                return _ket_qua(DEPENDENT, details + tien_de + [f"{khuon.loai} MISSING {kt.nhan}", ly_do],
                                subjects=tuple(x.nhan for x in thieu), witness=chung)
            details.append(f"{khuon.loai} MISSING {kt.nhan}: {ly_do}")
        return _ket_qua(UNDETERMINED, details + tien_de)
    loi = [f"NO_ROLE {lit[0]} {lit[1]}" for lit in lc.literal
           if _vai_tro(lit, de, inv, set(khuon.dinh)) not in ("SOURCE_DATUM", "LAYOUT_FRONTIER")]
    loi += [f"FRAME_DEPENDENT {x}" for x in sorted(lc.kieu - KHUNG_TU_DO)]
    loi += [f"UNCERTIFIED {chu}: measure {q} outside C1" for chu, q in lc.phep_do if q not in PHEP_DO_C1]
    loi += [f"UNCERTIFIED arithmetic '{op}' outside C1" for op in sorted(lc.phep_toan - _PHEP_TOAN_C1)]
    if loi:
        return _ket_qua(UNDETERMINED, details + tien_de + loi)
    ok, ghi = _doi_chieu_chinh_tac(prog, khuon, anh_xa, do_dai, phu, exec_res, ngan, execution_budget)
    if not ok:
        return _ket_qua(UNDETERMINED, details + tien_de + [ghi])
    return _ket_qua(PROVEN_SAFE, details + tien_de + [f"C1 {khuon.loai}", ghi], certificate="C1")


def danh_gia_doc_lap(contract: Any, spec: SemanticProgramSpec) -> KetQuaGiaDinh:
    """Cùng bước bổ sung dựng hình + thực thi của route, rồi chứng chỉ (test và census)."""
    from .coverage_gate import check_structural_coverage

    dung = hoan_thien_dung_hinh(spec, contract)
    if dung.hong:
        return _ket_qua(UNDETERMINED, ["FORMATION_REJECTED"])
    try:
        res = _chay(dung.spec)
    except Exception as e:  # noqa: BLE001
        return _ket_qua(UNDETERMINED, [f"EXECUTION_FAILED {type(e).__name__}"])
    ten = check_structural_coverage(contract, dung.spec).ten_da_hoa_giai
    return kiem_gia_dinh(contract, dung.spec, res, ten)
