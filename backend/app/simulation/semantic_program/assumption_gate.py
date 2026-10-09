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
from math import isqrt
from typing import Any, Callable

from ..geometry import metric as _metric
from ..geometry.exact import GeometryError, Vec3
from ..geometry.kernel import polygon_from_right_angle_chain, right_angle_chain_start
from ..geometry.radical import ExactNumber, is_exact_number, parse_exact, sqrt_rational, square
from .contract import SemanticProgramSpec
from .domain_profile import geometry_symbol_key
from .formation import _dinh_nghia, hoan_thien_dung_hinh
from .grounding_gate import bang_chung_doan
from .interpreter import SemanticProgramInterpreter
from .pipeline_adapter import DEFAULT_EXECUTION_BUDGET
from .plane_equation import (MatPhangDe, bat_bien_mat_phang, doc_mat_phang_de, so_lan_nhac_mat_phang,
                             ten_mat_phang_cua_bien, tuong_duong)
from .point_coordinate import bat_bien_toa_do
from .postconditions import check_postconditions, check_source_invariants
from .segment_relation import _D, bat_bien_chia_doan, bat_bien_do_dai
from .shape_constraint import (QuanHeCat, RangBuoc, che_muc_tieu, doc_quan_he_cat, doc_rang_buoc, khoang_muc_tieu,
                               la_chop_tam_giac_deu, phan_chua_doc, ten_diem_khong_toa_do)
from .solid_faces import phan_loai_bang_mat
from .source_entities import dinh_danh_thuc_the

PROVEN_SAFE = "PROVEN_SAFE"
DEPENDENT = "DEPENDENT_ON_UNSTATED_ASSUMPTION"
UNDETERMINED = "UNDETERMINED"
NOT_APPLICABLE = "NOT_APPLICABLE_NO_NUMERIC_ANSWER"
MA_PHU_THUOC = "ASSUMPTION_DETERMINES_ANSWER"
MA_CHUA_CHUNG_MINH = "ASSUMPTION_INVARIANCE_UNPROVEN"
#: §21: toạ độ ĐỀ CHO trái một quan hệ hình dạng ĐỀ NÓI — đề tự mâu thuẫn.
MA_DE_MAU_THUAN = "SOURCE_SHAPE_CONTRADICTS_COORDINATES"
#: §15.1 (W17): câu cắt của đề ĐỌC ĐƯỢC mà phép dựng thiết diện trên lát cắt lệch nó (mặt phẳng,
#: khối hoặc thiết diện) — đề đủ và đúng, lỗi ở chương trình.
MA_LECH_PHEP_DUNG = "CONSTRUCTION_NOT_TEXT_BOUND"
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
    kw.setdefault("reason_code", {DEPENDENT: MA_PHU_THUOC, UNDETERMINED: MA_CHUA_CHUNG_MINH}.get(status))
    return KetQuaGiaDinh(status=status, details=tuple(details), **kw)


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
        """Có câu lệnh nào TỚI VÀ GỒM `s` đọc `n` không — `X = trung điểm(X, N)` đọc chính
        literal nó ghi đè (đánh giá cuối W15); không đọc được câu lệnh ⇒ coi như có."""
        for t in self.cau_lenh:
            doc = _Doc("", _LatCat())
            try:
                doc.nut(t)
            except _Loi:
                return True
            if n in doc.ten:
                return True
            if t is s:
                return False
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


def gan_mat_phang(bien: str, mp_de: tuple[MatPhangDe, ...], duy_nhat: bool) -> tuple[MatPhangDe | None, str]:
    """Mặt phẳng ĐỀ mà biến mặt phẳng-từ-phương-trình `bien` gắn được, hoặc None + lý do (§14.1).

    Biến mang tên (`ten_mat_phang_cua_bien`) ⇒ đúng một phương trình đề mang tên ấy. Biến không
    tên ⇒ chỉ khi `duy_nhat` (đề nhắc mặt phẳng đúng một lần VÀ chương trình dựng đúng một mặt
    phẳng từ phương trình) và đề có đúng một phương trình. Trùng bộ số không bao giờ là căn cứ.
    """
    ten = ten_mat_phang_cua_bien(bien)
    if ten:
        khop = [m for m in mp_de if m.ten in ten]
        if len(khop) == 1:
            return khop[0], f"bound by name to ({khop[0].ten})"
        nhan = "/".join(f"({t})" for t in sorted(ten))
        return None, f"no single text equation for {nhan}" if not khop else f"several text equations for {nhan}"
    if duy_nhat and len(mp_de) == 1:
        return mp_de[0], "bound as the only plane of the text and of the program"
    return None, "unnamed program plane and the text plane is not unique"


def _gia_tri_fact(contract: Any, fid: str | None) -> tuple[str, ...]:
    f = next((f for f in getattr(contract, "input_facts", ()) or () if f.fact_id == fid), None) if fid else None
    return tuple(str(v) for v in (f.values if f is not None else ()) if str(v).strip())


def _nhan_mp(m: MatPhangDe, de: str) -> str:
    return f"({m.ten})" if m.ten else de[m.span[0]:m.span[1]].strip()


def danh_tinh_mat_phang(bien: str, fid: str | None, contract: Any, de: str, mp_de: tuple[MatPhangDe, ...],
                        duy_nhat: bool) -> tuple[MatPhangDe | None, str]:
    """§15.1 — mặt phẳng ĐỀ của biến mặt phẳng-từ-phương-trình `bien`. Theo NGUỒN trước: `fid` là
    `source_fact_id` của KHAI BÁO biến (IR nâng ô ấy từ câu lệnh về khai báo); giá trị nguyên văn
    của fact xuất hiện đúng một lần trong `de` và chứa đúng một phương trình đọc trọn ⇒ mặt phẳng
    ấy (đổi tên biến máy không đổi danh tính). Không có nguồn dùng được ⇒ luật W16 `gan_mat_phang`.
    Tên biến chỉ mặt phẳng KHÁC nguồn ⇒ không có danh tính."""
    ung = set()
    for v in _gia_tri_fact(contract, fid):
        vi_tri = [m.start() for m in re.finditer(re.escape(v), de)]
        if len(vi_tri) == 1:
            trong = [m for m in mp_de if vi_tri[0] <= m.span[0] and m.span[1] <= vi_tri[0] + len(v)]
            ung.update(trong[:1] if len(trong) == 1 else ())
    if len(ung) != 1:
        return gan_mat_phang(bien, mp_de, duy_nhat)
    (nguon,) = ung
    ten = ten_mat_phang_cua_bien(bien)
    if ten and nguon.ten not in ten:
        return None, f"name says {'/'.join(f'({t})' for t in sorted(ten))}, source says {_nhan_mp(nguon, de)}"
    return nguon, f"bound by source to {_nhan_mp(nguon, de)}"


def _vai_tro(lit: tuple, de: str, inv: tuple, khuon: set[str] | None,
             mp: dict[str, tuple[MatPhangDe | None, str]] | None = None) -> str | None:
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
        m, _ly_do = (mp or {}).get(lit[1], (None, ""))
        try:
            return "SOURCE_DATUM" if m is not None and tuong_duong([_F(c) for c in lit[2]], m.he_so) else None
        except (ValueError, TypeError, ZeroDivisionError):
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
    gia_tri: ExactNumber | None      # §18.3: kích thước có thể là căn (T8)
    keo: tuple            # ("phap_tuyen", X, (p, q, r)) | ("canh", X, Y) | ("vi_tu", X) | ("vi_tu_mat", X, (p, q, r))


@dataclass
class _Khuon:
    loai: str
    dinh: tuple[str, ...]
    rang_buoc: list[tuple[str, Callable[[dict], bool]]]
    kich_thuoc: list[_KichThuoc]
    tien_de: list[RangBuoc]
    #: Hiện thực CHÍNH TẮC của khuôn từ các kích thước bắt buộc (cùng thứ tự `kich_thuoc`); `None` ⇔ không có.
    chinh_tac: Callable[[list[ExactNumber]], dict[str, Vec3] | None]
    #: §18.2: khung chính tắc nhận kích thước CĂN (T8). Khuôn khác dựng khung trục toạ độ: kích thước vô tỉ ⇒
    #: `TEMPLATE_NOT_REPRESENTABLE`, không bao giờ một toạ độ vô tỉ.
    can: bool = False


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


def _can_huu_ti(q: Fraction) -> Fraction | None:
    """√q trong ℚ, hoặc None."""
    if q < 0:
        return None
    a, b = isqrt(q.numerator), isqrt(q.denominator)
    return Fraction(a, b) if a * a == q.numerator and b * b == q.denominator else None


def _khuon_chop_deu(rb, S: str, day: tuple, ent: tuple, do_dai: dict):
    """T7 (regular-square-pyramid-w01) — chóp tứ giác ĐỀU: đáy vuông, chân đường cao ở TÂM đáy.

    Duy nhất sai khác đồng dạng khi biết cạnh đáy s và chiều cao h; h đến trực tiếp (`chiều cao`, hoặc `SO` với O
    là tâm đề gọi tên) hoặc SUY từ trung đoạn m (h² = m² − s²/4) hay cạnh bên l (h² = l² − s²/2). Hai nguồn h khác
    nhau ⇒ mâu thuẫn; h² không là bình phương hữu tỉ ⇒ không có hiện thực toạ độ hữu tỉ (ngoài miền số của toạ độ)."""
    a, b, c, d = day
    s = next((r.value for r in rb if r.kind == "base_square" and set(r.entities) == set(day) and r.value is not None),
             None) or next((do_dai[frozenset(p)] for p in ((a, b), (b, c), (c, d), (d, a)) if frozenset(p) in do_dai),
                           None)
    doc = {k: next((r for r in rb if r.kind == k and r.entities == ent and r.value is not None), None)
           for k in ("height", "apothem", "lateral_edge")}
    tam = {r.entities[0] for r in rb if r.kind == "base_centre" and set(r.entities[1:]) == set(day)}
    so = next((do_dai[frozenset({S, o})] for o in tam if frozenset({S, o}) in do_dai), None)
    # Cạnh bên: cụm "cạnh bên bằng l" HOẶC độ dài server tự đọc từ đề cho đoạn nối đỉnh với một đỉnh đáy (`SA = 3`,
    # "cạnh bên SA = 3") — cùng hạng bằng chứng nguồn với cạnh đáy `AB = s`. Mọi cạnh bên của chóp đều bằng nhau:
    # hai giá trị khác nhau là mâu thuẫn của chính đề (tự rà soát cuối của W1).
    # §18.3: số đo có thể là căn — mọi so sánh/suy luận ở đây đi trên BÌNH PHƯƠNG (hữu tỉ).
    ben = {square(do_dai[frozenset({S, v})]) for v in day if frozenset({S, v}) in do_dai}
    if doc["lateral_edge"] is not None:
        ben.add(square(doc["lateral_edge"].value))
    if len(ben) > 1:
        return "TEMPLATE_CONTRADICTION T7: lateral edges² " + ", ".join(str(x) for x in sorted(ben))
    l2 = next(iter(ben), None)
    s2 = square(s) if s is not None else None
    ung: list[tuple[str, Fraction]] = []
    if doc["height"] is not None:
        ung.append(("height", square(doc["height"].value)))
    if so is not None:
        ung.append(("apex to centre", square(so)))
    if s2 is not None and doc["apothem"] is not None:
        ung.append(("apothem", square(doc["apothem"].value) - s2 / 4))
    if s2 is not None and l2 is not None:
        ung.append(("lateral edge", l2 - s2 / 2))
    if len({v for _, v in ung}) > 1:
        return "TEMPLATE_CONTRADICTION T7: " + ", ".join(f"{k} ⇒ h² = {v}" for k, v in ung)
    h = None
    if ung:
        h2 = ung[0][1]
        if h2 <= 0:
            return f"TEMPLATE_NOT_MATCHED T7: degenerate height (h² = {h2})"
        h = _can_huu_ti(h2)
        if h is None:
            return f"TEMPLATE_NOT_REPRESENTABLE T7: h² = {h2} is not a rational square (no rational coordinates)"

    def tam_day(V):
        return V[a] + (V[c] - V[a]).scale(Fraction(1, 2))

    rbuoc: list = [
        ("base parallelogram", lambda V: V[b] - V[a] == V[c] - V[d]),
        ("base right angle", lambda V: _vuong(V, a, b, d)),
        ("base square", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == (V[d] - V[a]).dot(V[d] - V[a])),
        ("apex above the base centre", lambda V: (V[S] - tam_day(V)).dot(V[b] - V[a]) == 0
         and (V[S] - tam_day(V)).dot(V[d] - V[a]) == 0),
        ("apex off the base", lambda V: V[S] != tam_day(V))]
    if s2 is not None:
        rbuoc.append(("base side", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == s2))
    if h is not None:
        rbuoc.append(("height", lambda V: (V[S] - tam_day(V)).dot(V[S] - tam_day(V)) == h * h))
    if doc["apothem"] is not None:
        m2 = square(doc["apothem"].value)
        rbuoc.append(("apothem", lambda V: (V[S] - V[a] - (V[b] - V[a]).scale(Fraction(1, 2))).dot(
            V[S] - V[a] - (V[b] - V[a]).scale(Fraction(1, 2))) == m2))
    if l2 is not None:
        rbuoc.append(("lateral edge", lambda V: all((V[S] - V[p]).dot(V[S] - V[p]) == l2 for p in day)))
    tien_de = [r for r in rb if r.kind in ("base_square", "base_centre") and set(r.entities) >= set(day)]
    tien_de += [r for r in doc.values() if r is not None]

    def chinh_tac(L: list[Fraction]) -> dict[str, Vec3]:
        day_ct = _chu_nhat_chinh_tac(day, L[0], L[0])
        return {**day_ct, S: _o(L[0] / 2, L[0] / 2, L[1])}

    return _Khuon("T7", (S, *day), rbuoc,
                  [_KichThuoc(_nhan(a, b), [(a, b), (b, c), (c, d), (d, a)], s, ("vi_tu_mat", a, day[:3])),
                   _KichThuoc("chiều cao", [], h, ("phap_tuyen", a, day[:3]))],
                  tien_de, chinh_tac)


def kich_thuoc_t8(rb, S: str, day: tuple, ent: tuple, do_dai: dict) -> tuple | str:
    """Cạnh đáy² b² và chiều cao² h² mà ĐỀ cố định cho chóp tam giác đều / tứ diện đều (`None` = đề không cho), hoặc lý
    do từ chối (mâu thuẫn, chiều cao suy biến). h đến trực tiếp (`chiều cao`, `SG` với G là tâm đề gọi tên) hoặc SUY từ
    cạnh bên l (h² = l² − b²/3) hay tứ diện đều (h² = 2b²/3). Một thẩm quyền: T8 và metric khung (`do_luong_cua`)."""
    a, b, c = day
    tu_dien = any(r.kind == "regular_tetrahedron" and r.entities == ent for r in rb)
    canh = {square(r.value) for r in rb if r.value is not None and (
        (r.kind == "base_equilateral" and set(r.entities) == set(day)) or (r.kind == "edge_all" and r.entities == ent))}
    canh |= {square(do_dai[frozenset(p)]) for p in ((a, b), (b, c), (c, a)) if frozenset(p) in do_dai}
    ben = {square(do_dai[frozenset({S, v})]) for v in day if frozenset({S, v}) in do_dai}
    ben |= {square(r.value) for r in rb if r.value is not None and (
        (r.kind == "lateral_edge" and r.entities == ent) or (r.kind == "edge_all" and r.entities == ent))}
    if tu_dien:                                # mọi cạnh bằng nhau: cạnh bên và cạnh đáy là MỘT lớp
        canh = ben = canh | ben
    if len(canh) > 1:
        return "TEMPLATE_CONTRADICTION T8: base sides² " + ", ".join(str(x) for x in sorted(canh))
    if len(ben) > 1:
        return "TEMPLATE_CONTRADICTION T8: lateral edges² " + ", ".join(str(x) for x in sorted(ben))
    b2, l2 = next(iter(canh), None), next(iter(ben), None)
    tam = {r.entities[0] for r in rb if r.kind == "base_centre" and set(r.entities[1:]) == set(day)}
    ung = [("height", square(r.value)) for r in rb if r.kind == "height" and r.entities == ent and r.value is not None]
    ung += [("apex to centre", square(do_dai[frozenset({S, o})])) for o in tam if frozenset({S, o}) in do_dai]
    if b2 is not None and l2 is not None:
        ung.append(("lateral edge", l2 - b2 / 3))
    if len({v for _, v in ung}) > 1:
        return "TEMPLATE_CONTRADICTION T8: " + ", ".join(f"{k} ⇒ h² = {v}" for k, v in ung)
    h2 = ung[0][1] if ung else None
    if h2 is not None and h2 <= 0:
        return f"TEMPLATE_NOT_MATCHED T8: degenerate height (h² = {h2})"
    return b2, h2, l2


_RANG_BUOC_T8_THE_TICH = frozenset({
    "pyramid", "regular_triangular_pyramid", "base_equilateral",
    "base_centre", "height", "lateral_edge", "edge_all",
})


def _kich_thuoc_t8_quyet_dinh_the_tich(rb, do_dai: dict, lc: _LatCat, de: str) -> tuple[str, ...]:
    """Các kích thước T8 còn thiếu mà lát cắt *thực tế* dùng để đo thể tích.

    Đây là nhánh hẹp cho affine-chart gap: quyết định dựa trên dependency slice
    (`measure(volume)`), quan hệ nguồn T8 đã đọc và `kich_thuoc_t8`; không suy từ
    tên họ hình.  Bất kỳ chữ/ràng buộc ngoài vocabulary này hoặc mâu thuẫn kích
    thước đều trả rỗng để đường fail-closed cũ xử lý.
    """
    if not any(phep_do == "volume" for _chu, phep_do in lc.phep_do):
        return ()
    if phan_chua_doc(de) or any(r.kind not in _RANG_BUOC_T8_THE_TICH for r in rb):
        return ()
    khoi = {r.entities for r in rb if r.kind == "pyramid" and len(r.entities) == 4}
    if len(khoi) != 1:
        return ()
    ent = next(iter(khoi))
    S, day = ent[0], ent[1:]
    # Tứ diện đều chỉ thiếu một scale chung; không gộp nó vào lát cắt hai kích
    # thước này khi chưa có hợp đồng nhãn riêng.
    if any(r.kind == "regular_tetrahedron" and r.entities == ent for r in rb):
        return ()
    if not any(r.kind == "regular_triangular_pyramid" and r.entities == ent for r in rb):
        return ()
    kt = kich_thuoc_t8(rb, S, day, ent, do_dai)
    if isinstance(kt, str):
        return ()
    b2, h2, _l2 = kt
    return tuple(([_nhan(day[0], day[1])] if b2 is None else [])
                 + (["chiều cao"] if h2 is None else []))


def _khuon_chop_tam_giac_deu(rb, S: str, day: tuple, ent: tuple, do_dai: dict):
    """T8 (§18.2, exact-dimensions) — chóp đáy tam giác ĐỀU, chân đường cao ở TRỌNG TÂM; tứ diện đều là trường hợp
    cạnh bên = cạnh đáy. Duy nhất sai khác đẳng cự khi biết b và h (`kich_thuoc_t8`); mọi phép so trên BÌNH PHƯƠNG.

    Không còn miền "biểu diễn được": bố cục là KHUNG AFFINE, độ dài theo metric khung (`geometry.metric`) mà
    `do_luong_cua` dẫn xuất từ chính b², h² của đề. Ràng buộc dưới đây đọc metric đang hiệu lực — khung Euclid cũ
    (N1/N3) cho metric đồng nhất, khung khác chỉ thoả khi metric dẫn xuất từ đề đang chạy."""
    kt = kich_thuoc_t8(rb, S, day, ent, do_dai)
    if isinstance(kt, str):
        return kt
    b2, h2, l2 = kt
    a, b, c = day

    def G(V):
        return (V[a] + V[b] + V[c]).scale(Fraction(1, 3))

    def d2(V, p, q):
        return _metric.norm_sq(V[p] - V[q])

    rbuoc: list = [
        ("base equilateral", lambda V: d2(V, a, b) == d2(V, b, c) == d2(V, c, a)),
        ("apex above the centroid", lambda V: _metric.dot(V[S] - G(V), V[b] - V[a]) == 0
         and _metric.dot(V[S] - G(V), V[c] - V[a]) == 0),
        ("apex off the base", lambda V: V[S] != G(V))]
    if b2 is not None:
        rbuoc.append(("base side", lambda V: d2(V, a, b) == b2))
    if h2 is not None:
        rbuoc.append(("height", lambda V: _metric.norm_sq(V[S] - G(V)) == h2))
    if l2 is not None:
        rbuoc.append(("lateral edge", lambda V: all(d2(V, S, p) == l2 for p in day)))
    tien_de = [r for r in rb if (r.kind in ("base_equilateral", "base_centre") and set(r.entities) >= set(day))
               or (r.kind in ("height", "lateral_edge", "edge_all", "regular_tetrahedron") and r.entities == ent)]

    def chinh_tac(L: list[ExactNumber]) -> dict[str, Vec3]:
        """Khung đơn vị — kích thước KHÔNG nằm trong toạ độ; lượt chạy lại dẫn xuất metric riêng từ đề (`_chay`)."""
        return {a: _o(), b: _o(1), c: _o(0, 1), S: _o(Fraction(1, 3), Fraction(1, 3), 1)}

    canh_day = sqrt_rational(b2) if b2 is not None else None
    cao = sqrt_rational(h2) if h2 is not None else None
    return _Khuon("T8", (S, *day), rbuoc,
                  [_KichThuoc(_nhan(a, b), [(a, b), (b, c), (c, a)], canh_day, ("vi_tu_mat", a, day)),
                   _KichThuoc("chiều cao", [], cao, ("phap_tuyen", a, day))],
                  tien_de, chinh_tac, can=True)


def _khuon_chop(rb, S: str, day: tuple, ent: tuple, do_dai: dict | None = None):
    if la_chop_tam_giac_deu(rb, S, day, do_dai or {}):
        return _khuon_chop_tam_giac_deu(rb, S, day, ent, do_dai or {})
    if len(day) == 4 and any(r.kind == "regular_square_pyramid" and r.entities == ent for r in rb):
        return _khuon_chop_deu(rb, S, day, ent, do_dai or {})
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
        rbuoc.append(("height", lambda V: (V[S] - V[X]).dot(V[S] - V[X]) == square(cao)))
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
                rbuoc.append(("base side", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == square(canh_day)))
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


def _khuon_lang_tru_xien(rb, day: tuple, tren: tuple, ent: tuple, rb_kieu: list, do_dai: dict):
    """T9 (§19, oblique-prism) — lăng trụ xiên: chân đường cao hạ từ đỉnh T của đáy trên là một đỉnh F ≠ B₀ của đáy dưới.

    `None` ⇔ đề không nêu quan hệ ấy (luồng T3–T6 tiếp tục như trước). Chiều cao đến trực tiếp (`height`, |TF|) hoặc
    SUY từ cạnh bên l (h² = l² − |B₀F|²); nguồn khác nhau ⇒ mâu thuẫn; h² không là bình phương hữu tỉ ⇒ ngoài ℚ³."""
    k = len(day)
    doi = dict(zip(tren, day))
    chan = {(T, F, r) for r in rb if r.kind == "line_perp_plane" and len(set(r.entities[:2])) == 2
            and set(r.entities[2:]) <= set(day) and len(set(r.entities[2:])) >= 3
            for T, F in (r.entities[:2], r.entities[1::-1]) if T in doi and F in day and doi[T] != F}
    if not chan:
        return None
    if len({(T, F) for T, F, _ in chan}) > 1:
        return "TEMPLATE_NOT_MATCHED T9: more than one foot of a lateral height"
    T, F, r_chan = next(iter(chan))
    B0 = doi[T]
    tien_de = [*rb_kieu, r_chan]
    canh_cua = lambda i, j: [(day[i], day[j]), (tren[i], tren[j])]  # noqa: E731
    rbuoc: list = [(f"translation {day[i]}{tren[i]}", lambda V, i=i: V[tren[i]] - V[day[i]] == V[T] - V[B0])
                   for i in range(k)]
    rbuoc += [("foot of the height", lambda V: all((V[T] - V[F]).dot(V[day[(i + 1) % k]] - V[day[i]]) == 0
                                                   for i in range(k))),
              ("apex off the base", lambda V: V[T] != V[F])]
    if k == 3:
        X, gv = next(((x, g) for x in day if (g := _goc_vuong_tai(rb, day, x))), (None, None))
        if X is None:
            return "TEMPLATE_NOT_MATCHED T9: no right angle on the base"
        Y, Z = [p for p in day if p != X]
        rbuoc.append(("right angle on the base", lambda V: _vuong(V, X, Y, Z)))
        i, j, l = day.index(X), day.index(Y), day.index(Z)
        lop = [_KichThuoc(_nhan(X, Y), canh_cua(i, j), None, ("canh", X, Y)),
               _KichThuoc(_nhan(X, Z), canh_cua(i, l), None, ("canh", X, Z))]
        tien_de.append(gv)

        def day_chinh_tac(L: list) -> dict[str, Vec3]:
            return {X: _o(), Y: _o(L[0]), Z: _o(0, L[1])}
    elif k == 4:
        a, b, c, d = day
        vuong = next((r for r in rb if r.kind == "base_square" and set(r.entities) == set(day)), None)
        cn = next((r for r in rb if r.kind == "base_rectangle" and set(r.entities) == set(day)), None)
        if vuong is None and cn is None:
            return "TEMPLATE_NOT_MATCHED T9: base not stated rectangle/square"
        rbuoc += [("base parallelogram", lambda V: V[b] - V[a] == V[c] - V[d]),
                  ("base right angle", lambda V: _vuong(V, a, b, d))]
        if vuong is not None:
            rbuoc.append(("base square", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == (V[d] - V[a]).dot(V[d] - V[a])))
            if vuong.value is not None:
                rbuoc.append(("base side", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == square(vuong.value)))
            lop = [_KichThuoc(_nhan(a, b), canh_cua(0, 1) + canh_cua(1, 2) + canh_cua(2, 3) + canh_cua(3, 0),
                              vuong.value, ("vi_tu_mat", a, day[:3]))]
        else:
            lop = [_KichThuoc(_nhan(a, b), canh_cua(0, 1) + canh_cua(3, 2), None, ("canh", a, b)),
                   _KichThuoc(_nhan(a, d), canh_cua(0, 3) + canh_cua(1, 2), None, ("canh", a, d))]
        tien_de.append(vuong or cn)

        def day_chinh_tac(L: list) -> dict[str, Vec3]:
            return _chu_nhat_chinh_tac(day, L[0], L[-1])
    else:
        return "TEMPLATE_NOT_MATCHED T9: prism base size"

    # ── chiều cao: mọi nguồn trùng bình phương ────────────────────────────
    ben = {square(do_dai[frozenset(p)]) for p in zip(day, tren) if frozenset(p) in do_dai}
    if len(ben) > 1:
        return "TEMPLATE_CONTRADICTION T9: lateral edges² " + ", ".join(str(x) for x in sorted(ben))
    cao, rb_cao = _do_dai_tu_rb(rb, "height", ent)
    tien_de += rb_cao
    ung: list[tuple[str, Fraction]] = []
    if cao is not None:
        ung.append(("height", square(cao)))
    if frozenset((T, F)) in do_dai:
        ung.append(("foot segment", square(do_dai[frozenset((T, F))])))
    canh_day = [kt.gia_tri if kt.gia_tri is not None else next(
        (do_dai[frozenset(p)] for p in kt.lop if frozenset(p) in do_dai), None) for kt in lop]
    if ben and all(isinstance(x, Fraction) for x in canh_day):
        ct = day_chinh_tac(canh_day)
        ung.append(("lateral edge", next(iter(ben)) - (ct[B0] - ct[F]).dot(ct[B0] - ct[F])))
    if len({v for _, v in ung}) > 1:
        return "TEMPLATE_CONTRADICTION T9: " + ", ".join(f"{n} ⇒ h² = {v}" for n, v in ung)
    h = None
    if ung:
        h2 = ung[0][1]
        if h2 <= 0:
            return f"TEMPLATE_NOT_MATCHED T9: degenerate height (h² = {h2})"
        h = _can_huu_ti(h2)
        if h is None:
            return f"TEMPLATE_NOT_REPRESENTABLE T9: h² = {h2} is not a rational square (no rational coordinates)"
        rbuoc.append(("height", lambda V: (V[T] - V[F]).dot(V[T] - V[F]) == h * h))

    def chinh_tac(L: list) -> dict[str, Vec3]:
        day_ct = day_chinh_tac(L[:-1])
        dinh_T = day_ct[F] + _o(0, 0, L[-1])
        return {**day_ct, **{tren[i]: day_ct[day[i]] + (dinh_T - day_ct[B0]) for i in range(k)}}

    return _Khuon("T9", day + tren, rbuoc, lop + [_KichThuoc(_nhan(T, F), [(T, F)], h, ("phap_tuyen", F, day[:3]))],
                  tien_de, chinh_tac)


def _vuong_tai_dinh(rb, day: tuple, i: int) -> RangBuoc | None:
    """Góc vuông của đáy tại `day[i]`: giữa hai cạnh đáy kề nó (`line_perp_line`), hoặc `right_triangle` (k = 3)."""
    x, ke = day[i], {frozenset((day[i], day[i - 1])), frozenset((day[i], day[(i + 1) % len(day)]))}
    for r in rb:
        if r.kind == "line_perp_line" and {frozenset(r.entities[:2]), frozenset(r.entities[2:])} == ke:
            return r
        if r.kind == "right_triangle" and len(day) == 3 and r.entities[0] == x and set(r.entities) == set(day):
            return r
    return None


def _khuon_day_chuoi(rb, day: tuple, ent: tuple, chop: str | None, tren: tuple | None, rb_kieu: list):
    """T10 (§20) — chóp có cạnh bên SX ⊥ đáy hoặc lăng trụ đứng, đáy LỒI xác định bởi chuỗi k − 2 góc vuông liên tiếp.

    `None` ⇔ khuôn không áp dụng (không chuỗi, không cạnh vuông góc đáy): lý do của khuôn cũ được giữ."""
    k = len(day)
    if k < 3:
        return None
    i0 = right_angle_chain_start(k, lambda i: _vuong_tai_dinh(rb, day, i))
    if i0 is None:
        return None
    duong = [day[(i0 + t) % k] for t in range(k)]
    goc = [_vuong_tai_dinh(rb, day, (i0 + t) % k) for t in range(1, k - 1)]
    vi_tri = {u: j for j, u in enumerate(day)}
    canh_cua = (lambda u, v: [(u, v), (tren[vi_tri[u]], tren[vi_tri[v]])]) if tren else (lambda u, v: [(u, v)])
    lop = [_KichThuoc(_nhan(duong[t], duong[t + 1]), canh_cua(duong[t], duong[t + 1]), None,
                      ("canh", duong[t], duong[t + 1])) for t in range(k - 1)]
    a, b, c = day[:3]
    n = lambda V: (V[b] - V[a]).cross(V[c] - V[a])  # noqa: E731
    rbuoc: list = [
        ("base planar", lambda V: all((V[p] - V[a]).dot(n(V)) == 0 for p in day)),
        ("base convex", lambda V: all((V[day[j]] - V[day[j - 1]]).cross(V[day[(j + 1) % k]] - V[day[j]]).dot(n(V)) > 0
                                      for j in range(k))),
        *((f"right angle at {duong[t]}", lambda V, t=t: _vuong(V, duong[t], duong[t - 1], duong[t + 1]))
          for t in range(1, k - 1))]
    cao, rb_cao = _do_dai_tu_rb(rb, "height", ent)
    if chop is not None:
        chan = [(r, (set(r.entities[:2]) - {chop}).pop()) for r in rb
                if r.kind == "line_perp_plane" and chop in r.entities[:2] and len(set(r.entities[:2])) == 2
                and (set(r.entities[:2]) - {chop}) <= set(day) and set(r.entities[2:]) <= set(day)
                and len(set(r.entities[2:])) >= 3]
        if not chan:
            return None
        r_chan, X = chan[0]
        rbuoc += [("apex edge ⊥ base", lambda V: all((V[chop] - V[X]).dot(V[q] - V[X]) == 0 for q in day if q != X)),
                  ("apex off the base", lambda V: V[chop] != V[X])]
        if cao is not None:
            rbuoc.append(("height", lambda V: (V[chop] - V[X]).dot(V[chop] - V[X]) == square(cao)))
        lop.append(_KichThuoc(_nhan(chop, X), [(chop, X)], cao, ("phap_tuyen", X, day[:3])))
        tien_de = [*rb_kieu, r_chan, *goc, *rb_cao]
        dinh = (chop, *day)
    else:
        rbuoc += [(f"translation {day[j]}{tren[j]}", lambda V, j=j: V[tren[j]] - V[day[j]] == V[tren[0]] - V[day[0]])
                  for j in range(1, k)]
        rbuoc += [("lateral ⊥ base", lambda V: all((V[tren[0]] - V[day[0]]).dot(V[day[(j + 1) % k]] - V[day[j]]) == 0
                                                   for j in range(k))),
                  ("lateral non-zero", lambda V: V[tren[0]] != V[day[0]])]
        if cao is not None:
            rbuoc.append(("height", lambda V: (V[tren[0]] - V[day[0]]).dot(V[tren[0]] - V[day[0]]) == square(cao)))
        lop.append(_KichThuoc(_nhan(day[0], tren[0]), list(zip(day, tren)), cao, ("phap_tuyen", day[0], day[:3])))
        tien_de = [*rb_kieu, *goc, *rb_cao]
        dinh = day + tren

    def chinh_tac(L: list) -> dict[str, Vec3] | None:
        try:
            V = dict(zip(duong, polygon_from_right_angle_chain(L[:-1])))
        except GeometryError:
            return None
        if chop is not None:
            V[chop] = V[X] + _o(0, 0, L[-1])
        else:
            V.update({tren[vi_tri[u]]: V[u] + _o(0, 0, L[-1]) for u in day})
        return V

    return _Khuon("T10", dinh, rbuoc, lop, tien_de, chinh_tac)


def _khuon_lang_tru(rb, day: tuple, tren: tuple, ent: tuple, kieu: set[str], rb_kieu: list, do_dai: dict | None = None):
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
        rbuoc.append(("height", lambda V: (V[tren[0]] - V[day[0]]).dot(V[tren[0]] - V[day[0]]) == square(cao)))
    ben_kt = _KichThuoc(_nhan(day[0], tren[0]), ben, cao, ("phap_tuyen", b0, day[:3]))
    tien_de = [*rb_kieu, *rb_cao]
    canh_cua = lambda i, j: [(day[i], day[j]), (tren[i], tren[j])]  # noqa: E731

    def nap(day_ct: dict[str, Vec3], h: Fraction) -> dict[str, Vec3]:
        return {**day_ct, **{tren[i]: day_ct[day[i]] + _o(0, 0, h) for i in range(k)}}
    if not kieu & {"right_prism", "cuboid", "cube"}:
        xien = _khuon_lang_tru_xien(rb, day, tren, ent, rb_kieu, do_dai or {})
        if xien is not None:
            return xien
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
            rbuoc.append(("cube edge", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == square(canh)))
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
            rbuoc.append(("base side", lambda V: (V[b] - V[a]).dot(V[b] - V[a]) == square(s)))
        canh_day = canh_cua(0, 1) + canh_cua(1, 2) + canh_cua(2, 3) + canh_cua(3, 0)
        return _Khuon("T6", day + tren, rbuoc,
                      [_KichThuoc(_nhan(a, b), canh_day, s, ("vi_tu_mat", a, day[:3])), ben_kt],
                      tien_de + [vuong_day], lambda L: nap(_chu_nhat_chinh_tac(day, L[0], L[0]), L[1]))
    return "TEMPLATE_NOT_MATCHED prism type"


def _nhan_khuon(rb: tuple[RangBuoc, ...], cm: _ChiMuc, prog: dict, do_dai: dict | None = None):
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
            k = _khuon_chop(rb, ent[0], ent[1:], ent, do_dai)
            if isinstance(k, _Khuon):
                k.tien_de = rb_kieu + k.tien_de
            elif k.startswith("TEMPLATE_NOT_MATCHED"):      # §20.2: T10 chỉ khi T1/T2 không khớp
                k = _khuon_day_chuoi(rb, ent[1:], ent, ent[0], None, rb_kieu) or k
        else:
            n = len(ent) // 2
            k = _khuon_lang_tru(rb, ent[:n], ent[n:], ent, {r.kind for r in rb_kieu}, rb_kieu, do_dai)
            if isinstance(k, str) and k.startswith("TEMPLATE_NOT_MATCHED") and \
                    "right_prism" in {r.kind for r in rb_kieu}:
                k = _khuon_day_chuoi(rb, ent[:n], ent, None, ent[n:], rb_kieu) or k
        return (k, anh_xa) if isinstance(k, _Khuon) else k
    if co_ten:
        return "TEMPLATE_NOT_MATCHED more than one named solid"
    if any(r.kind in _CHOP_DEU_KHONG_TEN and not r.entities for r in rb):
        # §25: chóp đều không tên mà §24 không gắn được (đề gọi tên điểm thiếu toạ độ / chương trình không đúng một
        # khối) — đề không cố định đỉnh nào là đỉnh chóp; không chứng nhận một cách đặt tên của chương trình.
        return "TEMPLATE_NOT_MATCHED unnamed regular pyramid: its vertices are not fixed by the text"
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
             _metric.norm_sq(V[p] - V[q]) == square(L))
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
                         exec_res, ngan: list[int], budget: int, de: str = "") -> tuple[bool, str]:
    vo_ti = [kt.nhan for kt in khuon.kich_thuoc if not khuon.can and not isinstance(
        kt.gia_tri if kt.gia_tri is not None else next(
            (do_dai[frozenset(c)] for c in kt.lop if frozenset(c) in do_dai), Fraction(0)), Fraction)]
    if vo_ti:                                  # §18.2: khung trục toạ độ không chở được kích thước căn
        return False, f"TEMPLATE_NOT_REPRESENTABLE {khuon.loai}: irrational {vo_ti[0]} (axis-aligned canonical layout)"
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
        res2 = _chay(SemanticProgramSpec.model_validate(d2), budget, de)
    except Exception as e:  # noqa: BLE001
        return False, f"C1_CROSS_CHECK_REFERENCE_FAILED {type(e).__name__}"
    lech = [n for n in phu if res2.final_memory.get(n) != exec_res.final_memory.get(n)]
    if lech:
        return False, f"C1_CROSS_CHECK_DISAGREES {lech[0]}"
    return True, f"C1_CROSS_CHECK_AGREES canonical re-run, {len(phu)} value(s)"


def _chay(sp: SemanticProgramSpec, budget: int = DEFAULT_EXECUTION_BUDGET, de: str = ""):
    """Chạy MỘT chương trình trong metric khung của CHÍNH nó (exact-dimensions): khung chính tắc, khung kéo giãn của
    phản ví dụ hay chương trình ứng viên đều dẫn xuất lại từ đề — không thừa hưởng metric của chương trình khác."""
    with _metric.using(do_luong_cua(de, sp)):
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
        res2 = _chay(sp2, budget, getattr(contract, "problem_text", "") or "")
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


def _hinh_binh_hanh(V, a, b, c, d) -> bool:
    return V[b] - V[a] == V[c] - V[d]


#: §21 — định nghĩa CHÍNH XÁC của các ràng buộc hình dạng kiểm được trên toạ độ (cùng định nghĩa các khuôn dùng).
_KIEM_C0: dict[str, Callable[[dict, tuple, Any], bool]] = {
    "line_perp_line": lambda V, e, _v: (V[e[1]] - V[e[0]]).dot(V[e[3]] - V[e[2]]) == 0,
    "line_perp_plane": lambda V, e, _v: (V[e[1]] - V[e[0]]).cross(
        (V[e[3]] - V[e[2]]).cross(V[e[4]] - V[e[2]])).is_zero() and all(
        (V[e[1]] - V[e[0]]).dot(V[q] - V[e[2]]) == 0 for q in e[2:]),
    "right_triangle": lambda V, e, _v: _vuong(V, e[0], e[1], e[2]),
    "base_parallelogram": lambda V, e, _v: _hinh_binh_hanh(V, *e),
    "base_rectangle": lambda V, e, _v: _hinh_binh_hanh(V, *e) and _vuong(V, e[0], e[1], e[3]),
    "base_rhombus": lambda V, e, _v: _hinh_binh_hanh(V, *e) and (
        (V[e[1]] - V[e[0]]).norm_sq() == (V[e[3]] - V[e[0]]).norm_sq()),
    "base_square": lambda V, e, v: _hinh_binh_hanh(V, *e) and _vuong(V, e[0], e[1], e[3]) and (
        (V[e[1]] - V[e[0]]).norm_sq() == (V[e[3]] - V[e[0]]).norm_sq()) and (
        v is None or (V[e[1]] - V[e[0]]).norm_sq() == square(v)),
    "base_equilateral": lambda V, e, v: len({(V[e[i]] - V[e[i - 1]]).norm_sq() for i in range(3)}) == 1 and (
        v is None or (V[e[1]] - V[e[0]]).norm_sq() == square(v)),
}
_SO_DINH_C0 = {"line_perp_line": 4, "right_triangle": 3, "base_equilateral": 3, "base_parallelogram": 4,
               "base_rectangle": 4, "base_rhombus": 4, "base_square": 4}


# §22 — khẳng định TOÀN KHỐI. Toạ độ của đề là Descartes ⇒ phép Euclid thô trên `Vec3` (như §21), không metric khung.
def _phap_tuyen(V, day) -> Vec3:
    """Vectơ diện tích của đáy (tổng tích có hướng quanh đỉnh đầu) — khác 0 với mọi đa giác phẳng không suy biến."""
    o = V[day[0]]
    n = Vec3.of(0, 0, 0)
    for p, q in zip(day[1:], day[2:]):
        n = n + (V[p] - o).cross(V[q] - o)
    return n


def _tam(V, day) -> Vec3:
    t = Vec3.of(0, 0, 0)
    for p in day:
        t = t + V[p]
    return t.scale(Fraction(1, len(day)))


def _tinh_tien(V, e) -> Vec3 | None:
    """Lăng trụ `day + tren` (tương ứng theo vị trí): vectơ cạnh bên chung v ≠ 0, hoặc None nếu đáy trên không là tịnh tiến."""
    k = len(e) // 2
    v = V[e[k]] - V[e[0]]
    return v if not v.is_zero() and all(V[e[k + i]] - V[e[i]] == v for i in range(k)) else None


def _lang_tru_dung(V, e) -> bool:
    v = _tinh_tien(V, e)
    return v is not None and v.cross(_phap_tuyen(V, e[:len(e) // 2])).is_zero()


def _hop_chu_nhat(V, e) -> bool:
    return _lang_tru_dung(V, e) and _KIEM_C0["base_rectangle"](V, e[:4], None)


def _chop_deu(V, e) -> bool:
    """Đỉnh e[0] trên pháp tuyến tại tâm đáy e[1:], ngoài mặt đáy."""
    n, h = _phap_tuyen(V, e[1:]), V[e[0]] - _tam(V, e[1:])
    return h.cross(n).is_zero() and h.dot(n) != 0


def _chieu_cao_sq(V, e, khoi) -> Fraction | None:
    """Khoảng cách² tới mặt đáy: chóp — từ đỉnh; lăng trụ — từ đỉnh đáy trên. Đáy suy biến ⇒ None (không kiểm)."""
    day, p = (e[1:], e[0]) if khoi == "pyramid" else (e[:len(e) // 2], e[len(e) // 2])
    n = _phap_tuyen(V, day)
    return None if n.is_zero() else (V[p] - V[day[0]]).dot(n) ** 2 / n.norm_sq()


_KIEM_C0.update({
    "right_prism": lambda V, e, _v: _lang_tru_dung(V, e),
    "oblique_prism": lambda V, e, _v: _tinh_tien(V, e) is not None and not _lang_tru_dung(V, e),
    "cuboid": lambda V, e, _v: _hop_chu_nhat(V, e),
    "cube": lambda V, e, _v: _hop_chu_nhat(V, e) and len(
        {(V[e[i]] - V[e[0]]).norm_sq() for i in (1, 3, 4)}) == 1,
    "cube_edge": lambda V, e, v: (V[e[1]] - V[e[0]]).norm_sq() == square(v),
    "regular_square_pyramid": lambda V, e, _v: _KIEM_C0["base_square"](V, e[1:], None) and _chop_deu(V, e),
    "regular_triangular_pyramid": lambda V, e, _v: _KIEM_C0["base_equilateral"](V, e[1:], None) and _chop_deu(V, e),
    "regular_tetrahedron": lambda V, e, _v: len({(V[p] - V[q]).norm_sq() for i, p in enumerate(e)
                                                 for q in e[i + 1:]}) == 1,
    "edge_all": lambda V, e, v: all((V[p] - V[q]).norm_sq() == square(v) for i, p in enumerate(e) for q in e[i + 1:]),
    "lateral_edge": lambda V, e, v: all((V[b] - V[e[0]]).norm_sq() == square(v) for b in e[1:]),
    "apothem": lambda V, e, v: all((V[e[0]] - (V[a] + V[b]).scale(Fraction(1, 2))).norm_sq() == square(v)
                                   for a, b in zip(e[1:], e[2:] + e[1:2])),
    "base_centre": lambda V, e, _v: V[e[0]] == _tam(V, e[1:]),
    "height_pyramid": lambda V, e, v: _chieu_cao_sq(V, e, "pyramid") in (None, square(v)),
    "height_prism": lambda V, e, v: _chieu_cao_sq(V, e, "prism") in (None, square(v)),
})
_SO_DINH_C0.update({"cuboid": 8, "cube": 8, "cube_edge": 8, "regular_square_pyramid": 5,
                    "regular_triangular_pyramid": 4, "regular_tetrahedron": 4, "edge_all": 4, "apothem": 5})
_LANG_TRU_C0 = {"right_prism", "oblique_prism", "height_prism"}
_CHOP_C0 = {"lateral_edge", "base_centre", "height_pyramid"}
_CO_GIA_TRI_C0 = {"cube_edge", "edge_all", "lateral_edge", "apothem", "height_pyramid", "height_prism"}


def _mau_thuan_c0(rb: tuple[RangBuoc, ...], cm: "_ChiMuc", inv: tuple = ()) -> list[RangBuoc]:
    """§21/§22 — ràng buộc hình dạng (cả khẳng định toàn khối) ĐỀ NÓI mà toạ độ đề cho làm sai. Giá trị điểm lấy từ
    chương trình; điểm chương trình không khai thì lấy toạ độ CHÍNH ĐỀ cho (`point_coordinate` đọc trọn) — đề tự mâu
    thuẫn dù chương trình bỏ qua điểm ấy. Điểm không có toạ độ ở cả hai nơi, kind ngoài `_KIEM_C0`, khối không tên hay
    `height` không gắn được với một chóp/lăng trụ có tên, không được kiểm (thiếu mô tả ≠ mâu thuẫn)."""
    ten = cm.ten_theo_khoa()
    toa_de = {_khoa(i.points[0]): Vec3.of(*(Fraction(c) for c in i.coefficients)) for i in inv
              if i.kind == "point_coordinate" and len(i.points) == 1 and len(i.coefficients) == 3}

    def gia_tri(e: str):
        try:
            return cm.dinh_nghia(ten[_khoa(e)]).gia_tri
        except (KeyError, _Loi):
            return toa_de[_khoa(e)]              # KeyError ⇒ không toạ độ nào ⇒ bỏ qua ràng buộc

    khoi = {r.entities: r.kind for r in rb if r.kind in ("pyramid", "prism")}
    sai = []
    for r in rb:
        kind = f"height_{khoi.get(r.entities)}" if r.kind == "height" else r.kind
        kiem, n, so = _KIEM_C0.get(kind), _SO_DINH_C0.get(kind), len(r.entities)
        if kiem is None or (n is not None and so != n) or (r.kind == "line_perp_plane"
                                                           and len(set(r.entities[2:])) < 3):
            continue
        if kind in _LANG_TRU_C0 and (so < 6 or so % 2) or kind in _CHOP_C0 and so < 4 or (
                kind in _CO_GIA_TRI_C0 and r.value is None):
            continue                             # khối không tên (entities = ()) / thiếu số đo ⇒ không kiểm
        try:
            V = {e: gia_tri(e) for e in set(r.entities)}
        except KeyError:
            continue
        if all(isinstance(v, Vec3) for v in V.values()) and not kiem(V, r.entities, r.value):
            sai.append(r)
    return sai


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


# ── §15.1 · phép dựng thiết diện dùng ĐÚNG thực thể đề nói (W17) ───────────────────────────

def _gan_quan_he(s: dict, so_cat: int, qh: tuple[QuanHeCat, ...], contract: Any, khai: dict):
    """Câu cắt của đề mà thiết diện `s` của chương trình gắn được: một câu cắt và một thiết diện
    trên lát cắt; hoặc theo nguồn (fact của khai báo nhắc `(T)`); hoặc theo tên thiết diện."""
    if len(qh) == 1 and so_cat == 1:
        return qh[0], "the only cut of the text and of the slice"
    T = s["target_var"]
    nguon = [v.replace("′", "'").replace("’", "'")
             for v in _gia_tri_fact(contract, (khai.get(T) or {}).get("source_fact_id"))]
    ten = {_khoa(T)} | {_khoa(t) for t in ten_mat_phang_cua_bien(T)}
    for cach, khop in (("by source", lambda q: any(f"({q.thiet_dien})" in v for v in nguon)),
                       ("by name", lambda q: _khoa(q.thiet_dien) in ten)):
        ung = [q for q in qh if q.thiet_dien and khop(q)]
        if len(ung) == 1:
            return ung[0], cach
    return None, ""


def _mp_cua_cau_cat(q: QuanHeCat, mp_de: tuple[MatPhangDe, ...], de: str) -> tuple[Any, str]:
    """Danh tính + nhãn mặt phẳng của câu cắt: phương trình viết trong câu (không tên), mặt phẳng
    gọi qua điểm (`(MNP)` ⇒ tập điểm), hoặc đúng một phương trình đề mang tên ấy; không ⇒ None."""
    if q.mat_phang is None:
        trong = [m for m in mp_de if q.khoa_mat_phang[0] <= m.span[0] and m.span[1] <= q.khoa_mat_phang[1]]
        return (("pt", trong[0].span), _nhan_mp(trong[0], de)) if len(trong) == 1 else (None, "")
    nhan = f"({q.mat_phang})"
    if re.fullmatch(rf"(?:{_D}){{3,}}", q.mat_phang):
        return ("diem", frozenset(_khoa(t) for t in re.findall(_D, q.mat_phang))), nhan
    khop = [m for m in mp_de if m.ten == q.mat_phang]
    return (("pt", khop[0].span) if len(khop) == 1 else None), nhan


def _mp_cua_chuong_trinh(ten: str, cm: _ChiMuc, mp: dict, de: str) -> tuple[Any, str]:
    nut = cm.dinh_nghia(ten).nut
    if nut.get("kind") == "construct_plane_from_equation" and (m := mp.get(ten, (None, ""))[0]) is not None:
        return ("pt", m.span), _nhan_mp(m, de)
    if nut.get("kind") == "construct_plane" and isinstance(nut.get("through"), list):
        return ("diem", frozenset(_khoa(p) for p in nut["through"])), f"({_nhan(*map(str, nut['through']))})"
    return None, ""


def _ky_hieu_khoi(dinh: frozenset | None, rb: tuple[RangBuoc, ...]) -> str | None:
    for r in rb:
        if r.kind in ("pyramid", "prism") and frozenset(_khoa(e) for e in r.entities) == dinh:
            k = 1 if r.kind == "pyramid" else len(r.entities) // 2
            return _nhan(*r.entities[:k]) + "." + _nhan(*r.entities[k:])
    return None


def _kiem_phep_dung(contract: Any, prog: dict, cm: _ChiMuc, lc: _LatCat, de: str,
                    mp_de: tuple[MatPhangDe, ...], mp: dict, rb: tuple[RangBuoc, ...]):
    """§15.1 — mọi `construct_section` trên lát cắt phải gắn với một câu cắt của đề, cắt bằng mặt
    phẳng CÙNG danh tính (trùng phương trình không đủ) và cắt khối có CÙNG tập đỉnh.
    → (details, mã lý do — None khi khớp hết, chủ thể). LỆCH (`CONSTRUCTION_NOT_TEXT_BOUND`) chỉ
    khi cả hai danh tính đều xác định và khác nhau; danh tính mà server không ghim được (mặt phẳng
    có tên mà không phương trình, không tên điểm; khối đề không ghim; thiết diện không câu cắt nào
    gọi) là CHƯA CHỨNG MINH — không bao giờ đổ cho chương trình (W17, tự rà soát cuối)."""
    cat = [nut for n in sorted(lc.da_xet) if (nut := cm.dinh_nghia(n).nut).get("kind") == "construct_section"]
    if not cat:
        return [], None, ()
    qh = doc_quan_he_cat(de)
    if not qh:
        return ([f"OPERATION_BINDING {s['target_var']}: no cut relation read from the text" for s in cat],
                MA_CHUA_CHUNG_MINH, ())
    khai = {m["name"]: m for m in prog["memory_declarations"]}
    khoi_duy_nhat = {frozenset(_khoa(e) for e in r.entities) for r in rb if r.kind in ("pyramid", "prism")}
    ra: list[str] = []
    chu_the: list[str] = []
    sai = chua_ro = False
    for s in cat:
        T = s["target_var"]
        q, cach = _gan_quan_he(s, len(cat), qh, contract, khai)
        if q is None:
            ra.append(f"OPERATION_BINDING {T}: no cut relation of the text names this section — not provable")
            chua_ro = True
            continue
        loi, mo = [], []
        mp_d, nhan_d = _mp_cua_cau_cat(q, mp_de, de)
        mp_c, nhan_c = _mp_cua_chuong_trinh(s["plane"], cm, mp, de)
        if mp_d is None or mp_c is None:
            mo.append(f"the text cuts with {nhan_d or 'a plane'}, the program with {nhan_c or 'a plane'} — "
                      "the server cannot pin "
                      f"{'the text plane' if mp_d is None else 'the program plane'}: not provable")
        elif mp_d != mp_c:
            loi.append(f"the text cuts with {nhan_d}, the program cuts with {nhan_c}")
            chu_the += [x for x in (nhan_d, nhan_c) if x and x not in chu_the]
        khoi_d = frozenset(_khoa(e) for e in q.khoi) if q.khoi else (
            next(iter(khoi_duy_nhat)) if len(khoi_duy_nhat) == 1 else None)
        nut_k = cm.dinh_nghia(s["solid"]).nut
        khoi_c = frozenset(_khoa(v) for v in nut_k["vertices"]) if nut_k.get("kind") == "construct_solid" else None
        if khoi_d is None or khoi_c is None:
            mo.append("the server cannot pin the cut solid of the text or of the program: not provable")
        elif khoi_d != khoi_c:
            nhan_k = [x for x in (_ky_hieu_khoi(khoi_d, rb), _ky_hieu_khoi(khoi_c, rb)) if x]
            loi.append(f"the text cuts {nhan_k[0] if nhan_k else 'another solid'}, the program cuts another solid")
            chu_the += [x for x in nhan_k if x not in chu_the]
        sai, chua_ro = sai or bool(loi), chua_ro or bool(mo)
        ra += ([f"OPERATION_BINDING {T}: {x}" for x in loi + mo] if loi or mo
               else [f"OPERATION_BINDING {T}: matches the text cut @[{q.span[0]},{q.span[1]}] ({cach})"])
    return ra, (MA_LECH_PHEP_DUNG if sai else MA_CHUA_CHUNG_MINH if chua_ro else None), tuple(chu_the)


_CHOP_DEU_KHONG_TEN = {"regular_square_pyramid": 4, "regular_triangular_pyramid": 3}


def _cach_doc_chop_khong_ten(rb: tuple[RangBuoc, ...], de: str, prog: dict) -> list[tuple[str, ...]]:
    """§24 — các cách gắn khẳng định chóp đều KHÔNG TÊN (`()`) vào khối duy nhất của chương trình: mỗi cách đọc chóp
    của bảng mặt (đỉnh, *đáy) có số đỉnh đáy khớp. Chỉ khi đề không gọi tên điểm nào thiếu toạ độ — cách đặt tên đỉnh
    khi ấy không mang nghĩa đề chưa cố định; ràng buộc gắn vào vẫn được KIỂM (khuôn, §22), không được tin."""
    k = {_CHOP_DEU_KHONG_TEN[r.kind] for r in rb if r.kind in _CHOP_DEU_KHONG_TEN and not r.entities}
    khoi = [s for s in prog.get("statements", []) if s.get("kind") == "construct_solid"]
    if len(k) != 1 or len(khoi) != 1 or ten_diem_khong_toa_do(de):
        return []
    dinh = list(khoi[0]["vertices"])
    try:
        mat = [[dinh.index(v) if isinstance(v, str) else v for v in f] for f in khoi[0]["faces"]]
    except ValueError:
        return []
    return [tuple(_id(dinh[i]) for i in (*a, *b)) for loai, a, b in phan_loai_bang_mat(len(dinh), mat)
            if loai == "pyramid" and len(b) in k]


def _gan_chop(rb, ent: tuple[str, ...]) -> tuple[RangBuoc, ...]:
    """Ràng buộc `()` của chóp không tên → thực thể của cách đọc `ent` (như ký hiệu `S.ABCD`), thêm `pyramid(ent)`."""
    def gan(r: RangBuoc) -> RangBuoc:
        if r.kind == "base_centre" and len(r.entities) == 1:
            return RangBuoc(r.kind, r.entities + ent[1:], r.value, r.span)
        if r.entities:
            return r
        return RangBuoc(r.kind, ent[1:] if r.kind.startswith("base_") else ent, r.value, r.span)
    deu = next(r for r in rb if r.kind in _CHOP_DEU_KHONG_TEN and not r.entities)
    return tuple(map(gan, rb)) + (RangBuoc("pyramid", ent, None, deu.span),)


def _doc_de(de: str) -> tuple:
    """Đề → (đề che mệnh đề mục tiêu, ràng buộc, bất biến nguồn, độ dài đề cho CHÍNH XÁC theo cặp đỉnh)."""
    de_gt = che_muc_tieu(de)
    rb = doc_rang_buoc(de_gt)
    inv = bat_bien_tu_de(de_gt)
    # §18.3: độ dài nguồn có thể là căn (`display` của bộ đọc) — đọc lại CHÍNH XÁC, không ép `Fraction`.
    do_dai = {frozenset(_id(p) for p in i.points): v for i in inv
              if i.kind == "segment_length" and len(i.points) == 2 and i.expected
              and (v := parse_exact(i.expected)) is not None}
    return de_gt, rb, inv, do_dai


def do_luong_cua(de: str, prog: Any) -> "_metric.Metric | None":
    """exact-dimensions — metric của KHUNG chương trình, dẫn xuất từ ĐỀ; `None` = khung Euclid (đồng nhất).

    Chỉ khi đề là chóp tam giác đều / tứ diện đều (`la_chop_tam_giac_deu`, thẩm quyền duy nhất) và CỐ ĐỊNH b², h²
    (`kich_thuoc_t8`, cùng thẩm quyền với T8), và chương trình KHAI bốn đỉnh bằng toạ độ khung: sáu độ dài² (ba cạnh
    đáy b², ba cạnh bên b²/3 + h²) xác định DUY NHẤT metric (`geometry.metric.gram_from_lengths`). Toạ độ khung
    không mang độ dài nào — nên bố cục không thể thành giả thiết. Metric đồng nhất (khung Euclid sẵn đúng) ⇒ `None`,
    giữ nguyên từng byte đường cũ. Mọi thứ khác (thiếu kích thước, mâu thuẫn, khung phẳng, đỉnh dựng chứ không khai)
    ⇒ `None`, và các cổng phía sau quyết như trước."""
    if not isinstance(prog, dict):
        prog = prog.model_dump(mode="json", exclude_none=True)
    _gt, rb, _inv, do_dai = _doc_de(de or "")
    if cach := _cach_doc_chop_khong_ten(rb, de or "", prog):
        rb = _gan_chop(rb, cach[0])
    co_ten = {r.entities for r in rb if r.kind == "pyramid" and r.entities}
    if len(co_ten) != 1:
        return None
    ent = next(iter(co_ten))
    S, day = ent[0], ent[1:]
    if len(day) != 3 or not la_chop_tam_giac_deu(rb, S, day, do_dai):
        return None
    kt = kich_thuoc_t8(rb, S, day, ent, do_dai)
    if isinstance(kt, str) or kt[0] is None or kt[1] is None:
        return None
    b2, h2, _l2 = kt
    toa: dict[str, Any] = {}
    for m in prog.get("memory_declarations", []):
        if m.get("type") == "point3" and isinstance(m.get("initial_value"), list):
            toa.setdefault(m["name"], m["initial_value"])
    for s in prog.get("statements", []):
        if s.get("kind") == "declare_point" and isinstance(s.get("at"), list):
            toa.setdefault(s["target_var"], s["at"])
    dem = Counter(_khoa(n) for n in toa)
    theo_khoa = {_khoa(n): n for n in toa if dem[_khoa(n)] == 1}
    try:
        P = tuple(Vec3.of(*[_F(c) for c in toa[theo_khoa[_khoa(e)]]]) for e in (S, *day))
        l2 = b2 / 3 + h2
        m = _metric.gram_from_lengths(P, {(1, 2): b2, (2, 3): b2, (1, 3): b2, (0, 1): l2, (0, 2): l2, (0, 3): l2})
    except (KeyError, TypeError, ValueError, ZeroDivisionError, GeometryError):
        return None
    return None if _metric.is_identity(m) else m


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
    # §14.2: mọi TIỀN ĐỀ đọc từ đề đã che mệnh đề mục tiêu (cùng độ dài, span giữ nguyên);
    # đề gốc chỉ còn dùng để CHẶN phản ví dụ (phần chưa đọc, ràng buộc chưa kiểm).
    muc_tieu = khoang_muc_tieu(de)
    de_gt, rb, inv, do_dai = _doc_de(de)
    cach = _cach_doc_chop_khong_ten(rb, de, prog)
    rb_tho, rb = rb, (_gan_chop(rb, cach[0]) if cach else rb)
    details, bac = _trang_thai_quan_he(contract, rb)
    details = [f"GOAL_CLAUSE @[{a},{b}]" for a, b in muc_tieu] + details
    if bac:
        return _ket_qua(UNDETERMINED, details + ["RELATION_REFUTED_BY_SOURCE"])
    # exact-dimensions follow-up: nếu dependency slice thật sự đo THỂ TÍCH của
    # T8 đã đọc trọn, V = sqrt(3) * b² * h / 12. Vì vậy b/h còn thiếu là một
    # phụ thuộc nguồn có chứng minh giải tích, không phải lỗi chart. Làm trước
    # phép kiểm toạ độ: khi thiếu metric, một affine chart hợp lệ không nhất
    # thiết trông đều trong tích vô hướng Euclid mặc định.
    thieu_t8 = _kich_thuoc_t8_quyet_dinh_the_tich(rb, do_dai, lc, de)
    if thieu_t8:
        return _ket_qua(
            DEPENDENT,
            details + ["T8 ANALYTIC_DEPENDENCY volume = sqrt(3) * base_side^2 * height / 12"]
            + [f"T8 MISSING {nhan}" for nhan in thieu_t8],
            subjects=thieu_t8,
            witness={
                "description": "positive scaling of a missing T8 dimension preserves the read source relations",
                "changes": {nhan: ["t", "2t"] for nhan in thieu_t8},
            },
        )
    # §15.1 (W17): mặt phẳng ĐỀ của từng câu lệnh phương trình — theo nguồn, rồi luật W16 §14.1
    # (theo tên, hoặc duy nhất theo đếm).
    mp_de = doc_mat_phang_de(de_gt)
    pt = [s["target_var"] for s in prog["statements"] if s.get("kind") == "construct_plane_from_equation"]
    duy_nhat = so_lan_nhac_mat_phang(de) == 1 and len(pt) == 1
    khai = {m["name"]: m for m in prog["memory_declarations"]}
    mp = {b: danh_tinh_mat_phang(b, (khai.get(b) or {}).get("source_fact_id"), contract, de_gt, mp_de, duy_nhat)
          for b in pt}

    def an_toan(chi_tiet: list[str], cc: str) -> KetQuaGiaDinh:
        """§15.1: ĐIỀU KIỆN THÊM cho C0/C1 — phép dựng thiết diện trên lát cắt dùng đúng thực thể
        của câu cắt đề nói; không thì không chứng nhận (detail nối thêm)."""
        them, ma, chu_the = _kiem_phep_dung(contract, prog, cm, lc, de, mp_de, mp, rb)
        if ma is None:
            return _ket_qua(PROVEN_SAFE, chi_tiet + them, certificate=cc)
        return _ket_qua(UNDETERMINED, chi_tiet + them, reason_code=ma, subjects=chu_the)

    # C0 — lát cắt ghim bởi nguồn
    khong_vai = [lit for lit in lc.literal if _vai_tro(lit, de_gt, inv, None, mp) != "SOURCE_DATUM"]
    if not khong_vai:
        # §24: chóp không tên mâu thuẫn chỉ khi KHÔNG cách đọc nào của khối thoả khẳng định
        sai = min((_mau_thuan_c0(_gan_chop(rb_tho, e), cm, inv) for e in cach), key=len) if cach else \
            _mau_thuan_c0(rb, cm, inv)
        if sai:
            return _ket_qua(UNDETERMINED, details + [f"C0_SHAPE_CONTRADICTION {r.kind}({','.join(r.entities)})"
                                                     f" @[{r.span[0]},{r.span[1]}]" for r in sai],
                            reason_code=MA_DE_MAU_THUAN,
                            subjects=tuple(dict.fromkeys(de[r.span[0]:r.span[1]] for r in sai)))
        return an_toan(details + [f"C0 {len(lc.literal)} literal(s) pinned by the text"], "C0")
    for lit in khong_vai:
        if lit[0] == "mat_phang":
            m, ly_do = mp.get(lit[1], (None, "no plane statement"))
            details.append(f"PLANE_BINDING {lit[1]}: " + (
                ly_do if m is None else f"{ly_do} @[{m.span[0]},{m.span[1]}], coefficients not proportional"))

    # C1 — cấu hình do đề xác định
    k = _nhan_khuon(rb, cm, prog, do_dai)
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
        # W16 §14.2: ràng buộc đọc được trong mệnh đề mục tiêu không là tiền đề nhưng VẪN chặn,
        # và đề có mục tiêu thì không thử phản ví dụ.
        chua_doc = phan_chua_doc(de)
        da_kiem = {(r.kind, r.entities, r.value) for r in khuon.tien_de}
        doc = doc_rang_buoc(de)
        ngoai = [r for r in (_gan_chop(doc, cach[0]) if cach and any(x.kind in _CHOP_DEU_KHONG_TEN and not x.entities for x in doc)
                           else doc)
                 if (r.kind, r.entities, r.value) not in da_kiem]
        if chua_doc or ngoai or muc_tieu:
            return _ket_qua(UNDETERMINED, details + tien_de + [f"{khuon.loai} MISSING {kt.nhan}" for kt in thieu]
                            + ([f"CE_TEXT_NOT_FULLY_READ {' '.join(chua_doc[:8])}"] if chua_doc else [])
                            + [f"CE_CONSTRAINT_NOT_CHECKED {r.kind}({','.join(r.entities)})" for r in ngoai]
                            + (["CE_GOAL_CLAUSE_PRESENT"] if muc_tieu else []))
        for kt in thieu:
            chung, ly_do = _phan_vi_du(contract, prog, exec_res, ten_da_hoa_giai, khuon, anh_xa, V, kt, do_dai,
                                       inv, de_gt, phu, ngan, execution_budget)
            if chung is not None:
                return _ket_qua(DEPENDENT, details + tien_de + [f"{khuon.loai} MISSING {kt.nhan}", ly_do],
                                subjects=tuple(x.nhan for x in thieu), witness=chung)
            details.append(f"{khuon.loai} MISSING {kt.nhan}: {ly_do}")
        return _ket_qua(UNDETERMINED, details + tien_de)
    loi = [f"NO_ROLE {lit[0]} {lit[1]}" for lit in lc.literal
           if _vai_tro(lit, de_gt, inv, set(khuon.dinh), mp) not in ("SOURCE_DATUM", "LAYOUT_FRONTIER")]
    loi += [f"FRAME_DEPENDENT {x}" for x in sorted(lc.kieu - KHUNG_TU_DO)]
    loi += [f"UNCERTIFIED {chu}: measure {q} outside C1" for chu, q in lc.phep_do if q not in PHEP_DO_C1]
    loi += [f"UNCERTIFIED arithmetic '{op}' outside C1" for op in sorted(lc.phep_toan - _PHEP_TOAN_C1)]
    if loi:
        return _ket_qua(UNDETERMINED, details + tien_de + loi)
    ok, ghi = _doi_chieu_chinh_tac(prog, khuon, anh_xa, do_dai, phu, exec_res, ngan, execution_budget, de)
    if not ok:
        return _ket_qua(UNDETERMINED, details + tien_de + [ghi])
    return an_toan(details + tien_de + [f"C1 {khuon.loai}", ghi], "C1")


def danh_gia_doc_lap(contract: Any, spec: SemanticProgramSpec) -> KetQuaGiaDinh:
    """Cùng bước bổ sung dựng hình + thực thi của route, rồi chứng chỉ (test và census)."""
    from .coverage_gate import check_structural_coverage

    dung = hoan_thien_dung_hinh(spec, contract)
    if dung.hong:
        return _ket_qua(UNDETERMINED, ["FORMATION_REJECTED"])
    de = getattr(contract, "problem_text", "") or ""
    try:
        res = _chay(dung.spec, de=de)
    except Exception as e:  # noqa: BLE001
        return _ket_qua(UNDETERMINED, [f"EXECUTION_FAILED {type(e).__name__}"])
    ten = check_structural_coverage(contract, dung.spec).ten_da_hoa_giai
    with _metric.using(do_luong_cua(de, dung.spec)):
        return kiem_gia_dinh(contract, dung.spec, res, ten)
