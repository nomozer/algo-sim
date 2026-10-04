# -*- coding: utf-8 -*-
"""W18 §16 — phép dựng ĐIỂM phải gắn với quan hệ của đề bằng DANH TÍNH, không bằng toạ độ.

Lỗ đo được trước bản sửa (`docs/evaluation/geometry/runs/w18-binding-focus/`, 0 lượt gọi): hình chiếu
lên sai đường/mặt phẳng, danh sách "lần lượt" bị tráo đích, đích đổi tên và một điểm trùng toạ độ
nhưng khác danh tính đều được PHỤC VỤ. Bất biến toạ độ (`segment_division`) chỉ hỏi "điểm này nằm
đâu", không hỏi "điểm này là điểm nào của đề".

Ba bước một chiều (thẩm quyền: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §16):
- `doc_quan_he_dung(đề)` — quan hệ trung điểm / hình chiếu đề nêu, từ vựng ĐÓNG (§16.1), đọc trên đề
  đã che mệnh đề mục tiêu (§14.2): điều phải chứng minh không bao giờ là phép dựng.
- danh tính (§16.2) — tên chương trình → ký hiệu điểm của đề qua bí danh, khoá `_khoa`, nhãn, fact
  nguồn và lưới hoà giải C₁a. Module này KHÔNG đọc toạ độ nào: toạ độ hay giá trị bằng nhau không
  bao giờ tạo bí danh.
- `doi_chieu_phep_dung` — trạng thái từng phép dựng điểm (§16.3) và mã từ chối (§16.4).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Any

from .assumption_gate import _gia_tri_fact, _khoa
from .ir_static_check import _CHU_KY, DIEM
from .segment_relation import _D as _E
from .shape_constraint import che_muc_tieu, doc_rang_buoc
from .source_entities import chuan_hoa_ten, dinh_danh_thuc_the, ky_hieu_toan, nhan_hinh_hoc, nhan_suy_ra

MATCHED, MISMATCHED, UNVERIFIED = "MATCHED", "MISMATCHED", "UNVERIFIED"
AUXILIARY, OUT_OF_SCOPE, NOT_REALIZED = "AUXILIARY", "OUT_OF_SCOPE", "NOT_REALIZED"
#: Cùng mã với W17 §15.1 (nguyên nhân CONSTRUCTION); chặng `construction_binding` phân biệt lời.
MA_LECH_PHEP_DUNG = "CONSTRUCTION_NOT_TEXT_BOUND"
MA_CHUA_DOI_CHIEU = "CONSTRUCTION_BINDING_UNVERIFIED"
#: Ba phép dựng điểm trong phạm vi W18 (§16.3).
PHEP_TRONG_PHAM_VI = frozenset({"midpoint", "divide_segment", "project_onto"})
_SINH_DIEM = frozenset(k for k, (_, ra) in _CHU_KY.items() if ra == DIEM)
_MO_HO = object()            # danh tính mơ hồ: các nguồn chỉ hai thực thể khác nhau


@dataclass(frozen=True)
class QuanHeDung:
    """Một quan hệ dựng điểm đề nêu. `dich`: khoá ký hiệu điểm đích. `toan_hang` — trung điểm:
    frozenset hai khoá (KHÔNG thứ tự); hình chiếu: (khoá điểm nguồn, đích nhận) với đích nhận
    `("line"|"plane", frozenset khoá)` hoặc None khi server không ghim được."""

    kind: str
    dich: str
    toan_hang: Any
    nhan_hoc_sinh: str
    span: tuple[int, int]


@dataclass(frozen=True)
class KetQuaDoiChieu:
    """`trang_thai`: đích chương trình → trạng thái (NOT_REALIZED: theo nhãn đích của đề);
    `bi_danh`: bí danh `assign X = var Y` → tên gốc."""

    trang_thai: dict[str, str] = field(default_factory=dict)
    reason_code: str | None = None
    subjects: tuple[str, ...] = ()
    details: tuple[str, ...] = ()
    bi_danh: dict[str, str] = field(default_factory=dict)


# ── §16.1 · bộ đọc ───────────────────────────────────────────────────────────────────────────

_TRUOC = r"(?<![A-Za-z0-9'])"
_SAU = r"(?![A-Za-z0-9'])"
_VA = r"(?:\s*,\s*(?:và\s+)?|\s+và\s+)"
_TRUNG_DIEM = re.compile(
    rf"{_TRUOC}(?P<x>{_E})\s+(?i:là\s+trung\s+điểm\s+(?:của\s+)?(?:(?:đoạn(?:\s+thẳng)?|cạnh)\s+)?)"
    rf"(?P<a>{_E})(?P<b>{_E}){_SAU}")
_LAN_LUOT = re.compile(
    rf"{_TRUOC}(?P<dich>{_E}(?:{_VA}{_E})+)\s+(?i:lần\s+lượt\s+là\s+trung\s+điểm\s+(?:của\s+)?"
    rf"(?:các\s+(?:cạnh|đoạn(?:\s+thẳng)?)\s+)?)(?P<doan>{_E}{_E}(?:{_VA}{_E}{_E})*){_SAU}")
#: Đích nhận: mặt phẳng gọi bằng điểm · mặt đáy (của khối duy nhất, hoặc tên ngay sau) · đường qua hai điểm.
_NHAN = (rf"(?:(?i:(?:mặt\s+phẳng|mp)\s*)?\((?P<mp>(?:{_E}){{3,}})\)"
         rf"|(?P<day>(?i:(?:mặt\s+(?:phẳng\s+)?)?đáy))(?![^\W\d_])(?:\s*\((?P<mpd>(?:{_E}){{3,}})\))?"
         rf"|(?i:(?:đường\s+thẳng|cạnh|đoạn(?:\s+thẳng)?)\s+)?(?P<l1>{_E})(?P<l2>{_E}){_SAU})")
_HINH_CHIEU = tuple(re.compile(m) for m in (
    rf"{_TRUOC}(?P<x>{_E})\s+(?i:là\s+hình\s+chiếu(?:\s+vuông\s+góc)?\s+của)\s+(?P<p>{_E})\s+"
    rf"(?i:lên|trên|xuống)\s+{_NHAN}",
    rf"{_TRUOC}(?P<x>{_E})\s+(?i:là\s+chân\s+đường\s+(?:vuông\s+góc|cao)\s+(?:(?:kẻ|hạ)\s+)?từ)\s+"
    rf"(?P<p>{_E})\s+(?i:xuống|đến|tới|lên)\s+{_NHAN}",
))
#: Vai trò đề nêu mà W18 KHÔNG đọc (§16.3 OUT_OF_SCOPE): tâm, trọng tâm, trực tâm, giao điểm, đối xứng.
_VAI_KHAC = re.compile(
    rf"{_TRUOC}(?P<x>{_E}(?:{_VA}{_E})*)\s+(?i:(?:lần\s+lượt\s+|tương\s+ứng\s+)?là\s+"
    rf"(?:giao\s+điểm|trọng\s+tâm|trực\s+tâm|tâm|điểm\s+đối\s+xứng))(?![^\W\d_])")


def _hien(t: str) -> str:
    return dinh_danh_thuc_the(t)[1]


def _chuan(de: str | None) -> str:
    return che_muc_tieu(de).replace("′", "'").replace("’", "'")


def _day_duy_nhat(de: str) -> tuple[str, ...] | None:
    """Đáy của khối DUY NHẤT đề nêu (chóp: các đỉnh sau dấu chấm; lăng trụ: đáy dưới)."""
    khoi = {(r.kind, r.entities) for r in doc_rang_buoc(de) if r.kind in ("pyramid", "prism")}
    if len(khoi) != 1:
        return None
    ((kind, ent),) = khoi
    return ent[1:] if kind == "pyramid" else ent[:len(ent) // 2]


def doc_quan_he_dung(problem_text: str | None) -> tuple[QuanHeDung, ...]:
    """Mọi quan hệ trung điểm / hình chiếu đề nêu theo từ vựng ĐÓNG §16.1. Một đích được hai câu nói
    khác nhau thì bỏ cả hai (không phân xử); cách nói ngoài từ vựng không cho quan hệ nào."""
    de = _chuan(problem_text)
    ra: list[QuanHeDung] = []

    def trung_diem(x: str, a: str, b: str, span: tuple[int, int]) -> None:
        ra.append(QuanHeDung("midpoint", _khoa(x), frozenset({_khoa(a), _khoa(b)}),
                             f"{_hien(x)} là trung điểm của {_hien(a)}{_hien(b)}", span))

    for m in _TRUNG_DIEM.finditer(de):
        trung_diem(m["x"], m["a"], m["b"], m.span())
    for m in _LAN_LUOT.finditer(de):
        dich, doan = re.findall(_E, m["dich"]), re.findall(rf"({_E})({_E})", m["doan"])
        if len(dich) == len(doan):                    # lệch số lượng ⇒ không ghép
            for x, (a, b) in zip(dich, doan):
                trung_diem(x, a, b, m.span())
    day = _day_duy_nhat(de)
    for mau in _HINH_CHIEU:
        for m in mau.finditer(de):
            if m["mp"] or m["mpd"]:
                ten = re.findall(_E, m["mp"] or m["mpd"])
                nhan, hien = ("plane", frozenset(map(_khoa, ten))), f"({''.join(map(_hien, ten))})"
            elif m["day"]:
                nhan = ("plane", frozenset(map(_khoa, day))) if day else None
                hien = f"({''.join(map(_hien, day))})" if day else "mặt đáy"
            else:
                nhan = ("line", frozenset({_khoa(m["l1"]), _khoa(m["l2"])}))
                hien = _hien(m["l1"]) + _hien(m["l2"])
            ra.append(QuanHeDung("projection", _khoa(m["x"]), (_khoa(m["p"]), nhan),
                                 f"{_hien(m['x'])} là hình chiếu của {_hien(m['p'])} lên {hien}", m.span()))
    loai: dict[str, set] = {}
    for q in ra:
        loai.setdefault(q.dich, set()).add((q.kind, q.toan_hang))
    ket, da = [], set()
    for q in sorted(ra, key=lambda q: q.span):
        if len(loai[q.dich]) == 1 and q.dich not in da:
            da.add(q.dich)
            ket.append(q)
    return tuple(ket)


# ── §16.2 · danh tính ────────────────────────────────────────────────────────────────────────

def _cau_lenh(sts):
    for s in sts or ():
        yield s
        for k in ("body", "then_body", "else_body"):
            yield from _cau_lenh(s.get(k))


class _DanhTinh:
    """Tên chương trình → khoá ký hiệu điểm của đề; None = thực thể KHÔNG có trong đề."""

    def __init__(self, de: str, prog: dict, contract: Any, hoa_giai: dict[str, str]) -> None:
        self.ky_hieu = {_khoa(t): t for t in nhan_hinh_hoc(de)}
        sts = list(_cau_lenh(prog["statements"]))
        self.goc = {s["target_var"]: s["expr"]["name"] for s in sts
                    if s.get("kind") == "assign" and (s.get("expr") or {}).get("kind") == "var"}
        self.dinh: dict[str, list[dict]] = {}
        for s in sts:
            if s.get("target_var"):
                self.dinh.setdefault(s["target_var"], []).append(s)
        self.khai = {m["name"]: m for m in prog["memory_declarations"]}
        self.contract = contract
        self.nguoc: dict[str, set[str]] = {}
        for c, p in (hoa_giai or {}).items():
            self.nguoc.setdefault(p, set()).add(c)

    def goc_cua(self, n: str) -> str:
        da = set()
        while n in self.goc and n not in da:
            da.add(n)
            n = self.goc[n]
        return n

    def nhom(self, n: str) -> set[str]:
        r = self.goc_cua(n)
        return {r} | {x for x in self.goc if self.goc_cua(x) == r}

    def _fact(self, x: str) -> set[str]:
        """Fact nguồn của khai báo nêu ĐÚNG MỘT ký hiệu điểm của đề ⇒ ký hiệu ấy."""
        gt = _gia_tri_fact(self.contract, (self.khai.get(x) or {}).get("source_fact_id"))
        diem = {_khoa(t) for t in nhan_hinh_hoc(" ".join(gt))} & self.ky_hieu.keys()
        return diem if len(diem) == 1 else set()

    def diem(self, n: str) -> Any:
        ung: set[str] = set()
        for x in self.nhom(n):
            nguon = {x} | chuan_hoa_ten(x) | self.nguoc.get(x, set())
            nguon |= {s["label"] for s in self.dinh.get(x, ()) if s.get("label")}
            ung |= {k for v in nguon if (k := _khoa(v)) in self.ky_hieu} | self._fact(x)
        return next(iter(ung)) if len(ung) == 1 else (None if not ung else _MO_HO)

    def nhan(self, n: str) -> tuple[str, frozenset] | None:
        """Đích nhận của chương trình: đường qua hai điểm / mặt phẳng qua các điểm của đề; mặt phẳng
        phương trình, đường dẫn xuất khác, hay qua một điểm ngoài đề ⇒ không ghim (None)."""
        ds = self.dinh.get(self.goc_cua(n), [])
        if len(ds) != 1:
            return None
        s = ds[0]
        if s.get("kind") == "construct_line":
            loai, ten = "line", (s["through_a"], s["through_b"])
        elif s.get("kind") == "construct_plane":
            loai, ten = "plane", tuple(s.get("through") or ())
        else:
            return None
        diem = [self.diem(t) for t in ten]
        return None if any(d is None or d is _MO_HO for d in diem) else (loai, frozenset(diem))

    def nhan_hoc_sinh(self, n: str) -> str:
        k = self.diem(n)
        return _hien(self.ky_hieu[k]) if isinstance(k, str) else (ky_hieu_toan(n) or "một điểm phụ")


# ── §16.3 · trạng thái ───────────────────────────────────────────────────────────────────────

def _ti_so(r: Any) -> Fraction | None:
    try:
        return Fraction(str(r).replace(" ", ""))
    except (ValueError, ZeroDivisionError):
        return None


def _la_trung_diem(e: dict) -> bool:
    """`midpoint`, hoặc `divide_segment` tỉ số 1/2 — cùng một quan hệ (§16.3)."""
    return e["kind"] == "midpoint" or (e["kind"] == "divide_segment" and _ti_so(e.get("ratio")) == Fraction(1, 2))


def _quan_he_ct(e: dict, dt: _DanhTinh) -> tuple[str, Any] | None:
    """Quan hệ chương trình dựng, trong không gian khoá; None ⇒ phép ngoài ba phép §16.3."""
    k = e["kind"]
    if _la_trung_diem(e):
        return "midpoint", frozenset({dt.diem(e["a"]), dt.diem(e["b"])})
    if k == "divide_segment":
        return "division", (dt.diem(e["a"]), dt.diem(e["b"]), _ti_so(e.get("ratio")))
    if k == "project_onto":
        return "projection", (dt.diem(e["point"]), dt.nhan(e["target"]))
    return None


def _cau_ct(dich: str, e: dict, dt: _DanhTinh) -> str:
    L = dt.nhan_hoc_sinh
    if _la_trung_diem(e):
        return f"{dich} là trung điểm của {L(e['a'])}{L(e['b'])}"
    if e["kind"] == "divide_segment":
        return f"{dich} chia đoạn {L(e['a'])}{L(e['b'])} theo tỉ số {e.get('ratio')}"
    if e["kind"] == "project_onto":
        ds = dt.dinh.get(dt.goc_cua(e["target"]), [])
        s = ds[0] if len(ds) == 1 else {}
        nhan = (L(s["through_a"]) + L(s["through_b"]) if s.get("kind") == "construct_line"
                else "(" + "".join(map(L, s["through"])) + ")" if s.get("kind") == "construct_plane"
                else ky_hieu_toan(e["target"]) or "một đối tượng phụ")
        return f"{dich} là hình chiếu của {L(e['point'])} lên {nhan}"
    return f"{dich} dựng bằng {e['kind']}"


def _cung_nhan(a: tuple[str, frozenset], b: tuple[str, frozenset]) -> bool:
    """Đường: cùng cặp điểm. Mặt phẳng: chung ≥ 3 điểm và tập này chứa tập kia (§16.2)."""
    if a[0] != b[0]:
        return False
    if a[0] == "line":
        return a[1] == b[1]
    return len(a[1] & b[1]) >= 3 and (a[1] <= b[1] or b[1] <= a[1])


def _so(R: QuanHeDung, p: tuple[str, Any] | None) -> tuple[str, str]:
    """Quan hệ đề `R` vs quan hệ chương trình `p` (bỏ qua đích)."""
    if p is None:
        return UNVERIFIED, "the text relation is read, the program builds it with another operation"
    kind, th = p
    if _MO_HO in (th if kind == "midpoint" else th[:2] if kind == "division" else th[:1]):
        return UNVERIFIED, "ambiguous identity of an operand"
    if kind != R.kind:
        return MISMATCHED, f"the text states a {R.kind}, the program builds a {kind}"
    if kind == "midpoint":
        return (MATCHED, "same unordered endpoints") if th == R.toan_hang else (MISMATCHED, "other endpoints")
    nguon, nhan = th
    if R.toan_hang[1] is None or nhan is None:
        return UNVERIFIED, "receiver not pinned"
    if nguon != R.toan_hang[0]:
        return MISMATCHED, "other source point"
    return (MATCHED, "same source and receiver") if _cung_nhan(R.toan_hang[1], nhan) else (MISMATCHED, "other receiver")


_THU_TU = {MISMATCHED: 0, UNVERIFIED: 1}


def doi_chieu_phep_dung(contract: Any, spec: Any, ten_da_hoa_giai: dict[str, str] | None = None) -> KetQuaDoiChieu:
    """§16.3/§16.4 — trạng thái của mọi phép dựng điểm (mọi tầng lồng) và mã từ chối:
    `CONSTRUCTION_NOT_TEXT_BOUND` khi có MISMATCHED (chủ thể: cặp [quan hệ đề, quan hệ chương
    trình]), không thì `CONSTRUCTION_BINDING_UNVERIFIED` khi có UNVERIFIED (chủ thể: đích)."""
    de = getattr(contract, "problem_text", "") or ""
    if not de.strip():
        return KetQuaDoiChieu()
    if ten_da_hoa_giai is None:
        from .coverage_gate import check_structural_coverage

        ten_da_hoa_giai = check_structural_coverage(contract, spec).ten_da_hoa_giai
    prog = spec.model_dump(mode="json", exclude_none=True)
    dt = _DanhTinh(de, prog, contract, ten_da_hoa_giai)
    qh = {q.dich: q for q in doc_quan_he_dung(de)}
    gioi_thieu = ({_khoa(t) for t in nhan_suy_ra(de)} & dt.ky_hieu.keys()) | set(qh)
    vai_khac = {_khoa(t) for m in _VAI_KHAC.finditer(_chuan(de)) for t in re.findall(_E, m["x"])}
    dung = [s for s in _cau_lenh(prog["statements"]) if s.get("kind") in ("construct_point", "assign")
            and (s.get("expr") or {}).get("kind") in _SINH_DIEM]
    ten_diem = [m["name"] for m in prog["memory_declarations"] if m.get("type") == "point3"]
    co = {dt.diem(n) for n in ten_diem + [s["target_var"] for s in dung]}

    tt: dict[str, str] = {}
    chi_tiet: list[str] = []
    lech: list[tuple[str, str]] = []
    chua: list[str] = []
    da_thay: set[str] = set()
    for s in dung:
        T, e = s["target_var"], s["expr"]
        x, p = dt.diem(T), _quan_he_ct(e, dt)
        cau = None
        if x is _MO_HO:
            st, ly = UNVERIFIED, "ambiguous identity of the target"
        elif x is not None and x in qh:
            st, ly = _so(qh[x], p)
            cau = qh[x].nhan_hoc_sinh
        elif x is not None:
            st, ly = ((OUT_OF_SCOPE, "text role outside the W18 vocabulary") if x in vai_khac
                      else (UNVERIFIED, "text-introduced point, relation not readable")
                      if x in gioi_thieu and e["kind"] in PHEP_TRONG_PHAM_VI
                      else (OUT_OF_SCOPE, "not a W18 binding target"))
        else:
            thay = [R for R in qh.values() if R.dich not in co and _so(R, p)[0] == MATCHED]
            if thay:
                st, ly = MISMATCHED, "the text relation is built under a name the text does not have"
                cau = thay[0].nhan_hoc_sinh
                da_thay.add(thay[0].dich)
            else:
                st, ly = AUXILIARY, "engine construction, not named by the text"
        dich_hs = dt.nhan_hoc_sinh(T) if isinstance(x, str) else (ky_hieu_toan(T) or "một điểm phụ")
        if st == MISMATCHED and (cap := (cau or "", _cau_ct(dich_hs, e, dt))) not in lech:
            lech.append(cap)
        elif st == UNVERIFIED and dich_hs not in chua:
            chua.append(dich_hs)
        if T not in tt or _THU_TU.get(st, 9) < _THU_TU.get(tt[T], 9):
            tt[T] = st
        chi_tiet.append(f"CONSTRUCTION_BINDING {T}: {st} — {ly}" + (f" (text: {cau})" if cau else ""))
    for R in qh.values():
        if R.dich not in co and R.dich not in da_thay:
            tt.setdefault(_hien(dt.ky_hieu.get(R.dich, R.dich)), NOT_REALIZED)
            chi_tiet.append(f"CONSTRUCTION_BINDING {R.nhan_hoc_sinh}: {NOT_REALIZED}")
    ma, chu_the = ((MA_LECH_PHEP_DUNG, [c for cap in lech for c in cap]) if lech
                   else (MA_CHUA_DOI_CHIEU, chua) if chua else (None, []))
    return KetQuaDoiChieu(tt, ma, tuple(chu_the), tuple(chi_tiet),
                          {a: dt.goc_cua(a) for a in dt.goc})
