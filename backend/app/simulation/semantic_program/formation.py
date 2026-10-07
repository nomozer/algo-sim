# -*- coding: utf-8 -*-
"""DỰNG HÌNH THEO LỚP — một thẩm quyền: từ vựng vai trò, kế hoạch theo lớp, bước
BỔ SUNG dựng hình cho MỌI chương trình (compiler lẫn LLM — S4) và vai trò của từng
vật trong cảnh (preregistration W13 §2).

Chỉ đọc dữ liệu CÓ KIỂU: bảng mặt của `construct_solid` (`solid_faces`), tô-pô và
quan hệ `perpendicular_line_plane` của hợp đồng, nhà sản xuất `project_onto` của
chương trình, ràng buộc hình dạng có kiểu của `shape_constraint` (chóp tứ giác đều —
regular-square-pyramid-w02). Không đọc nhãn, mã họ, tiêu đề, câu chữ đề hay tên `*_length`; không
phép hình học — mọi điều kiện là tổ hợp trên TÊN đỉnh. Không THỰC THI chương trình:
bước bổ sung chạy trước mọi cổng, kể cả với chương trình không chạy nổi. Khoá:
`test_planner_khong_re_nhanh_theo_ho`, `test_vai_tro_bat_bien_khi_doi_ten_may`.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from fractions import Fraction
from typing import Any

from pydantic import ValidationError

from .contract import SemanticProgramSpec
from .ir_static_check import kiem_tinh
from .segment_relation import do_dai_trong_de
from .shape_constraint import che_muc_tieu, doc_rang_buoc, la_chop_tam_giac_deu
from .solid_faces import phan_loai_bang_mat
from .source_entities import dinh_danh_thuc_the

LOP_CHOP, LOP_LANG_TRU, LOP_THIET_DIEN = "PYRAMID_LIKE", "PRISM_LIKE", "SECTION"
DUNG_KHAI = "DECLARE_ENTITIES"              # theo sự kiện INIT (scene3d)
DUNG_DAY = "CONSTRUCT_BASE"
DUNG_CAO = "CONSTRUCT_HEIGHT"
DUNG_DAY_TREN = "CONSTRUCT_TRANSLATED_FACE"
DUNG_BIEN_BEN = "CONSTRUCT_LATERAL_BOUNDARY"
KHEP_KHOI = "CLOSE_SOLID"
DUNG_MAT_CAT = "CONSTRUCT_CUTTING_OBJECT"
DUNG_GIAO = "CONSTRUCT_INTERSECTION"        # theo sự kiện EXTEND (scene3d)
KHEP_THIET_DIEN = "CLOSE_SECTION"           # theo sự kiện hoàn tất (scene3d)
DUNG_PHU = "CONSTRUCT_AUXILIARY_GEOMETRY"
VAI_TRO = frozenset({DUNG_KHAI, DUNG_DAY, DUNG_CAO, DUNG_DAY_TREN, DUNG_BIEN_BEN,
                     KHEP_KHOI, DUNG_MAT_CAT, DUNG_GIAO, KHEP_THIET_DIEN, DUNG_PHU})
#: Độ phủ tối thiểu theo lớp (§2.3); thứ tự là kế hoạch. Chóp có chân đường cao dùng
#: được thì thêm `DUNG_CAO` ngay sau đáy (`yeu_cau`).
TOI_THIEU = {LOP_CHOP: (DUNG_DAY, DUNG_BIEN_BEN, KHEP_KHOI),
             LOP_LANG_TRU: (DUNG_DAY, DUNG_DAY_TREN, DUNG_BIEN_BEN, KHEP_KHOI),
             LOP_THIET_DIEN: (DUNG_MAT_CAT, DUNG_GIAO, KHEP_THIET_DIEN)}

#: Thẩm quyền đã phân loại được khối (thứ tự ưu tiên của `lop_khoi`).
NGUON_PHAN_LOAI = ("CONTRACT", "TYPED_RELATION", "FACE_TABLE")
MO_HO, KHONG_HO_TRO = "AMBIGUOUS_TOPOLOGY", "UNSUPPORTED_TOPOLOGY"
LECH_HOP_DONG, HONG = "TOPOLOGY_CONTRACT_MISMATCH", "MALFORMED_TOPOLOGY"
#: Trạng thái bước bổ sung của một khối đã phân loại.
DA_DU, DA_DOI, DO_DANG = "COMPLETED", "LATE_OBJECT_MOVED", "PARTIAL_LATE_OBJECT"
TU_CHOI_DAU_RA = "COMPLETION_REJECTED_INVALID_OUTPUT"


@dataclass(frozen=True)
class KetQuaHoanThien:
    spec: SemanticProgramSpec
    #: `(tên khối, trạng thái)` theo thứ tự câu lệnh — nguồn phân loại thất bại
    #: (`MO_HO`…) hoặc trạng thái bổ sung (`DA_DU`, `DA_DOI`, `DO_DANG`).
    trang_thai_theo_khoi: tuple[tuple[str, str], ...]
    sha_goc: str
    sha_hoan_thien: str

    @property
    def hong(self) -> tuple[str, ...]:
        """Khối có bảng mặt hỏng — route từ chối có cấu trúc, không gửi sửa."""
        return tuple(k for k, t in self.trang_thai_theo_khoi if t == HONG)


def _sha(spec: SemanticProgramSpec) -> str:
    return hashlib.sha256(json.dumps(spec.model_dump(mode="json"), sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _id(ten: Any) -> str:
    """Tên đề (`A'`) hoặc tên IR (`A_prime`) → định danh thực thể (`A_prime`)."""
    return dinh_danh_thuc_the(str(ten))[0]


def _ky(ten: str) -> str:
    """Định danh thực thể → ký hiệu học sinh (`A_prime` → `A′`)."""
    return dinh_danh_thuc_the(ten)[1]


def _dinh_nghia(x: Any) -> set[str]:
    """Mọi tên một câu lệnh (kể cả thân lồng, mục nhóm) gán giá trị."""
    ra: set[str] = set()
    if isinstance(x, dict):
        if isinstance(x.get("target_var"), str):
            ra.add(x["target_var"])
        for it in x.get("items") or ():
            if isinstance(it, dict):
                ra.add(it.get("name") or it.get("target_var"))
        for v in x.values():
            if isinstance(v, (dict, list)):
                ra |= _dinh_nghia(v)
    elif isinstance(x, list):
        for v in x:
            ra |= _dinh_nghia(v)
    ra.discard(None)
    return ra


def _la(x: Any) -> set[str]:
    if isinstance(x, str):
        return {x}
    if isinstance(x, (dict, list)):
        return set().union(*map(_la, x.values() if isinstance(x, dict) else x))
    return set()


def _da_co(khai: list[dict[str, Any]], truoc: list[dict[str, Any]]) -> set[str]:
    """Tên ĐÃ có giá trị trước một vị trí: khai báo có giá trị đầu + câu lệnh đứng trước."""
    ra = {d["name"] for d in khai if d.get("initial_value") is not None}
    for s in truoc:
        ra |= _dinh_nghia(s)
    return ra


def _ten_trong(lien_he: Any) -> list[str]:
    return [_id(x) for x in (lien_he or ())]


# ── Phân loại khối ───────────────────────────────────────────────────────────

def _hop_le(vertex_ids: list[str], faces: list[list[int]]) -> bool:
    n = len(vertex_ids)
    return (len(set(vertex_ids)) == n and bool(faces) and all(
        len(f) >= 3 and len(set(f)) == len(f)
        and all(isinstance(i, int) and not isinstance(i, bool) and 0 <= i < n for i in f)
        for f in faces))


def _chan_ung_vien(cau: list[dict[str, Any]], contract: Any, apex: str, day: tuple) -> list[str]:
    """Chân đường cao từ `apex` xuống đáy — chỉ từ dữ kiện CÓ KIỂU, theo thứ tự gặp.

    ① hợp đồng: `perpendicular_line_plane`, đường {apex, F}, mặt ≥ 3 điểm ⊆ đáy;
    ② chương trình: F = `project_onto(point=apex, target=P)`, P dựng qua ≥ 3 điểm ⊆ đáy.
    """
    dat, ra = set(day), []
    for r in getattr(contract, "geometric_relations", None) or ():
        duong, mat = _ten_trong(r.line), set(_ten_trong(r.plane))
        if (r.kind == "perpendicular_line_plane" and len(duong) == 2 and apex in duong
                and len(mat) >= 3 and mat <= dat):
            ra += [p for p in duong if p != apex]
    mat_qua = {s["target_var"]: set(s.get("through") or ()) for s in cau
               if s.get("kind") == "construct_plane"}
    for s in cau:
        e = s.get("expr") if s.get("kind") == "construct_point" else None
        if (isinstance(e, dict) and e.get("kind") == "project_onto" and e.get("point") == apex
                and len(mat_qua.get(e.get("target"), ())) >= 3 and mat_qua[e["target"]] <= dat):
            ra.append(s["target_var"])
    ra += _tam_day_deu(cau, contract, apex, day)
    return ra


def _tam_day_deu(cau: list[dict[str, Any]], contract: Any, apex: str, day: tuple) -> list[str]:
    """③ (regular-square-pyramid-w02) chóp tứ giác ĐỀU — ràng buộc có kiểu `regular_square_pyramid` đọc từ PHẦN
    TIỀN ĐỀ của đề (mục tiêu "chứng minh … đều" bị che) cùng đỉnh và cùng tập đỉnh đáy — chân đường cao là TÂM đáy:
    điểm chương trình dựng bằng giao hai đường chéo đáy (`intersect_line_line` trên hai `construct_line` qua hai cặp
    đỉnh đối) hoặc trung điểm một đường chéo. Chỉ tổ hợp trên tên; đỉnh có thật ở trên tâm không là việc của chứng
    chỉ T7 và cổng gắn phép dựng trên route — sai thì bài bị từ chối, đoạn dựng thêm không bao giờ được phục vụ."""
    de = che_muc_tieu(getattr(contract, "problem_text", None))
    if len(day) == 3:
        # §18.4 (regular-triangular-pyramid-w01): chóp tam giác đều ⇒ chân đường cao là TRỌNG TÂM đáy — điểm chương
        # trình dựng bằng giao hai trung tuyến hoặc chia trung tuyến 2/3 (`phep_trong_tam`), theo tên.
        do_dai = {frozenset(map(_id, k)): v for k, v in do_dai_trong_de(de).items()}
        if not la_chop_tam_giac_deu(doc_rang_buoc(de), _id(apex), tuple(map(_id, day)), do_dai):
            return []
        return [p for p, tam_giac in phep_trong_tam(cau).items() if tam_giac == frozenset(day)]
    if len(day) != 4:
        return []
    deu = any(r.kind == "regular_square_pyramid" and r.entities[0] == apex and set(r.entities[1:]) == set(day)
              for r in doc_rang_buoc(de))
    if not deu:
        return []
    cheo = {frozenset((day[0], day[2])), frozenset((day[1], day[3]))}
    duong = {s["target_var"]: frozenset((s.get("through_a"), s.get("through_b"))) for s in cau
             if s.get("kind") == "construct_line"}
    ra = []
    for s in cau:
        e = s.get("expr") if s.get("kind") == "construct_point" else None
        if not isinstance(e, dict):
            continue
        if ((e.get("kind") == "intersect_line_line"
             and {duong.get(e.get("line_a")), duong.get(e.get("line_b"))} == cheo)
                or (e.get("kind") == "midpoint" and frozenset((e.get("a"), e.get("b"))) in cheo)):
            ra.append(s["target_var"])
    return ra


def _ti_so(r: Any) -> Fraction | None:
    try:
        return Fraction(str(r).replace(" ", ""))
    except (ValueError, ZeroDivisionError):
        return None


def phep_trong_tam(cau: Any) -> dict[str, frozenset[str]]:
    """§18.4 — điểm mà chương trình dựng thành TRỌNG TÂM của một tam giác, nhận theo TÊN phép dựng (không toạ độ):
    `intersect_line_line` của hai TRUNG TUYẾN (đường qua một đỉnh và một điểm `midpoint` của hai đỉnh kia, hai đỉnh
    khác nhau), hoặc `divide_segment(đỉnh, trung điểm cạnh đối, 2/3)` (`(trung điểm, đỉnh, 1/3)`). → tên điểm → ba đỉnh.
    Một thẩm quyền cho chân đường cao (`_tam_day_deu`) và binding trọng tâm (`construction_binding`)."""
    cau = list(cau)

    def bieu_thuc(s: dict) -> dict | None:
        e = s.get("expr") if s.get("kind") in ("construct_point", "assign") else None
        return e if isinstance(e, dict) else None

    trung = {s["target_var"]: frozenset((e.get("a"), e.get("b"))) for s in cau if (e := bieu_thuc(s))
             and (e.get("kind") == "midpoint" or (e.get("kind") == "divide_segment"
                                                  and _ti_so(e.get("ratio")) == Fraction(1, 2)))}

    def tam_giac(dinh: Any, m: Any) -> frozenset[str] | None:
        cap = trung.get(m)
        return cap | {dinh} if cap is not None and len(cap) == 2 and dinh not in cap else None

    trung_tuyen: dict[str, tuple[frozenset[str], str]] = {}
    for s in cau:
        if s.get("kind") == "construct_line":
            a, b = s.get("through_a"), s.get("through_b")
            if t := tam_giac(a, b):
                trung_tuyen[s["target_var"]] = (t, a)
            elif t := tam_giac(b, a):
                trung_tuyen[s["target_var"]] = (t, b)
    ra: dict[str, frozenset[str]] = {}
    for s in cau:
        e = bieu_thuc(s)
        if e is None:
            continue
        if e.get("kind") == "intersect_line_line":
            x, y = trung_tuyen.get(e.get("line_a")), trung_tuyen.get(e.get("line_b"))
            if x and y and x[0] == y[0] and x[1] != y[1]:
                ra[s["target_var"]] = x[0]
        elif e.get("kind") == "divide_segment":
            t = _ti_so(e.get("ratio"))
            tg = (tam_giac(e.get("a"), e.get("b")) if t == Fraction(2, 3)
                  else tam_giac(e.get("b"), e.get("a")) if t == Fraction(1, 3) else None)
            if tg:
                ra[s["target_var"]] = tg
    return ra


def chan_duong_cao(cau: list[dict[str, Any]], contract: Any, apex: str, day: tuple,
                   da_co: set[str] | None = None) -> str | None:
    """Chân đường cao DÙNG ĐƯỢC: ứng viên đầu tiên đã có giá trị trước khối (`da_co`)."""
    return next((f for f in _chan_ung_vien(cau, contract, apex, day)
                 if da_co is None or f in da_co), None)


def _quan_he_day_lang_tru(contract: Any, day: tuple, tren: tuple) -> bool:
    """Quan hệ có kiểu chỉ ra ĐÁY lăng trụ: cạnh bên ⊥ một mặt ≥ 3 điểm ⊆ đáy."""
    ben = [{u, w} for u, w in zip(day, tren)]
    for r in getattr(contract, "geometric_relations", None) or ():
        mat = set(_ten_trong(r.plane))
        if (r.kind == "perpendicular_line_plane" and set(_ten_trong(r.line)) in ben
                and len(mat) >= 3 and mat <= set(day)):
            return True
    return False


def _khop_hop_dong(c: tuple, topo: Any) -> tuple | None:
    """Cách đọc `c` khớp tô-pô hợp đồng ⇒ cách đọc theo THỨ TỰ của hợp đồng."""
    lop, apex, day, tren = c
    base = tuple(_ten_trong(topo.base_cycle))
    if getattr(topo, "apex", None):
        if lop == LOP_CHOP and apex == _id(topo.apex) and set(day) == set(base):
            return (lop, apex, base, ())
        return None
    doi = {_id(a): _id(b) for a, b in getattr(topo, "correspondence", None) or ()}
    if (lop == LOP_LANG_TRU and set(day) == set(base)
            and set(tren) == set(_ten_trong(getattr(topo, "top_cycle", None)))
            and all(doi.get(u) == w for u, w in zip(day, tren))):
        return (lop, None, base, tuple(doi[b] for b in base))
    return None


def _chuan_vong(c: tuple, thu_tu: list[str]) -> tuple:
    """Chu trình đáy đọc từ BẢNG MẶT có chiều tuỳ cách mô hình liệt kê mặt. Chuẩn
    hoá: bắt đầu ở đỉnh khai sớm nhất, đi về phía láng giềng khai sớm hơn (`ABCDE`,
    không `EDCBA`); đáy trên đi theo tương ứng. Chỉ đổi THỨ TỰ đọc, không đổi tập đỉnh."""
    lop, apex, day, tren = c
    vi = {v: i for i, v in enumerate(thu_tu)}
    k = min(range(len(day)), key=lambda i: vi[day[i]])
    xoay = tuple(day[k:]) + tuple(day[:k])
    nguoc = (xoay[0],) + tuple(reversed(xoay[1:]))
    moi = xoay if vi[xoay[1]] <= vi[nguoc[1]] else nguoc
    doi = dict(zip(day, tren))
    return (lop, apex, moi, tuple(doi[v] for v in moi) if tren else ())


def lop_khoi(vertex_ids: list[str], faces: list[list[int]], contract: Any = None,
             cau: list[dict[str, Any]] = ()) -> tuple[str, str | None, str | None, tuple, tuple]:
    """→ (nguồn | trạng thái, lớp, đỉnh chóp, chu trình đáy, chu trình đáy trên).

    Thứ tự thẩm quyền — KHÔNG BAO GIỜ chọn theo thứ tự đỉnh/mặt:
      ① `contract.solid_topology` khi cùng tập đỉnh với khối: khớp một cách đọc bảng
         mặt → "CONTRACT" (theo thứ tự của hợp đồng); không khớp → `LECH_HOP_DONG`;
      ② quan hệ CÓ KIỂU chỉ ra đúng một cách đọc (chân đường cao của chóp, cạnh bên
         vuông góc đáy của lăng trụ) → "TYPED_RELATION";
      ③ bảng mặt chỉ có MỘT cách đọc → "FACE_TABLE"; nhiều cách (tứ diện, lăng trụ
         không biết đáy, lập phương) → `MO_HO`; không cách nào → `KHONG_HO_TRO`.
    Bảng mặt hỏng (chỉ số ngoài miền, mặt < 3 đỉnh, đỉnh lặp) → `HONG`.
    """
    vertex_ids = list(vertex_ids)
    if not _hop_le(vertex_ids, faces):
        return HONG, None, None, (), ()
    cach = []
    for loai, a, b in phan_loai_bang_mat(len(vertex_ids), [list(f) for f in faces]):
        ten_a, ten_b = tuple(vertex_ids[i] for i in a), tuple(vertex_ids[i] for i in b)
        cach.append((LOP_CHOP, ten_a[0], ten_b, ()) if loai == "pyramid"
                    else (LOP_LANG_TRU, None, ten_a, ten_b))
    if not cach:
        return KHONG_HO_TRO, None, None, (), ()
    topo = getattr(contract, "solid_topology", None)
    if topo is not None:
        dinh_topo = set(_ten_trong(topo.base_cycle)) | set(_ten_trong(getattr(topo, "top_cycle", None)))
        if getattr(topo, "apex", None):
            dinh_topo.add(_id(topo.apex))
        if dinh_topo == set(vertex_ids):
            khop = [k for k in (_khop_hop_dong(c, topo) for c in cach) if k is not None]
            return ("CONTRACT", *khop[0]) if khop else (LECH_HOP_DONG, None, None, (), ())
    qh = [c for c in cach if (_chan_ung_vien(cau, contract, c[1], c[2]) if c[0] == LOP_CHOP
                              else _quan_he_day_lang_tru(contract, c[2], c[3]))]
    if len(qh) == 1:
        return ("TYPED_RELATION", *_chuan_vong(qh[0], vertex_ids))
    if len(qh) > 1:
        return MO_HO, None, None, (), ()
    return (("FACE_TABLE", *_chuan_vong(cach[0], vertex_ids)) if len(cach) == 1
            else (MO_HO, None, None, (), ()))


def ke_hoach(lop: str, apex: str | None, day: tuple, tren: tuple,
             chan: str | None) -> list[tuple[str, str, tuple[str, ...]]]:
    """[(vai trò, "polygon"|"segment", tên đỉnh)] theo §2.3, đúng thứ tự dựng."""
    buoc = [(DUNG_DAY, "polygon", tuple(day))]
    if lop == LOP_CHOP:
        if chan is not None:
            buoc.append((DUNG_CAO, "segment", (apex, chan)))
        i = day.index(chan) if chan in day else -1   # cạnh bên bắt đầu NGAY SAU chân
        buoc += [(DUNG_BIEN_BEN, "segment", (apex, x))
                 for x in tuple(day[i + 1:]) + tuple(day[:i + 1]) if x != chan]
    else:
        buoc.append((DUNG_DAY_TREN, "polygon", tuple(tren)))
        buoc += [(DUNG_BIEN_BEN, "segment", (u, w)) for u, w in zip(day, tren)]
    return buoc


def yeu_cau(lop: str, chan: str | None) -> list[str]:
    """Vai trò bắt buộc của một khối, theo thứ tự kế hoạch."""
    if lop == LOP_CHOP and chan is not None:
        return [DUNG_DAY, DUNG_CAO, DUNG_BIEN_BEN, KHEP_KHOI]
    return list(TOI_THIEU[lop])


# ── Bước bổ sung ─────────────────────────────────────────────────────────────

def _vi_tri(cau: list[dict[str, Any]], ten: str) -> int | None:
    return next((i for i, s in enumerate(cau) if s.get("target_var") == ten
                 and s.get("kind") == "construct_solid"), None)


def _co_vat(s: dict[str, Any], loai: str, dinh: frozenset) -> bool:
    """Câu lệnh cấp ngoài dựng vật `loai` có đúng tập đỉnh `dinh`."""
    if loai == "polygon":
        return s.get("kind") == "construct_polygon" and frozenset(s.get("vertices") or ()) == dinh
    if s.get("kind") != "construct_segment":
        return False
    cap = [(s.get("endpoint_a"), s.get("endpoint_b"))] + [
        (it.get("endpoint_a"), it.get("endpoint_b")) for it in s.get("items") or ()]
    return any(frozenset(c) == dinh for c in cap)


def _doi_duoc(cau: list[dict[str, Any]], khai: list[dict[str, Any]], i: int, j: int) -> bool:
    """Câu lệnh `j` (sau khối `i`) dời nguyên vẹn lên ngay trước khối được không:
    mọi toán hạng đã có trước khối, và không câu nào ở giữa định nghĩa lại toán
    hạng của nó hay đọc thứ nó dựng."""
    biet = {d["name"] for d in khai} | _dinh_nghia(cau)
    L = cau[j]
    dung = _dinh_nghia(L)
    toan_hang = (_la(L) & biet) - dung
    if not toan_hang <= _da_co(khai, cau[:i]):
        return False
    return all(not (_dinh_nghia(s) & toan_hang) and not (_la(s) & dung) for s in cau[i:j])


def _ten_moi(goc: str, dung: set[str]) -> str:
    ten, k = goc, 1
    while ten in dung:
        k += 1
        ten = f"{goc}_{k}"
    dung.add(ten)
    return ten


def _phat(thieu: list[tuple[str, str, tuple]], lop: str, dung: set[str]
          ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Câu lệnh + khai báo cho các vật còn thiếu, theo thứ tự kế hoạch; mọi cạnh bên
    thiếu đi chung MỘT câu lệnh nhóm (một bước dựng)."""
    cau, khai = [], []
    ben = [d for v, _l, d in thieu if v == DUNG_BIEN_BEN]
    for vai, loai, dinh in thieu:
        ky = "".join(_ky(x) for x in dinh)
        if loai == "polygon":
            ten = _ten_moi("day_" + "".join(dinh), dung)
            nhan = {DUNG_DAY: "Đáy dưới " if lop == LOP_LANG_TRU else "Đáy ",
                    DUNG_DAY_TREN: "Đáy trên "}[vai] + ky
            cau.append({"kind": "construct_polygon", "target_var": ten, "vertices": list(dinh),
                        "label": nhan})
            khai.append({"name": ten, "type": "polygon3"})
        elif vai == DUNG_CAO:
            ten = _ten_moi("chieu_cao_" + "".join(dinh), dung)
            cau.append({"kind": "construct_segment", "target_var": ten, "endpoint_a": dinh[0],
                        "endpoint_b": dinh[1], "label": "Chiều cao " + ky})
            khai.append({"name": ten, "type": "segment3"})
    if ben:
        muc = []
        for u, w in ben:
            ten = _ten_moi(f"canh_ben_{u}_{w}", dung)
            muc.append({"name": ten, "endpoint_a": u, "endpoint_b": w,
                        "label": "Cạnh bên " + _ky(u) + _ky(w)})
            khai.append({"name": ten, "type": "segment3"})
        cau.append({"kind": "construct_segment", "target_var": _ten_moi("canh_ben", dung), "items": muc,
                    "label": "Các cạnh bên " + ", ".join(_ky(u) + _ky(w) for u, w in ben)})
    return cau, khai


def _canh_da_dung(cau: list[dict[str, Any]]) -> set[frozenset]:
    """Cặp đầu mút của mọi đoạn các câu lệnh cấp ngoài đưa lên hình: đoạn (kể cả mục nhóm), cạnh vòng của đa giác,
    cạnh vòng của mặt khối."""
    ra: set[frozenset] = set()
    for s in cau:
        if s.get("kind") == "construct_segment":
            ra |= {frozenset((c.get("endpoint_a"), c.get("endpoint_b")))
                   for c in [s, *(s.get("items") or ())] if c.get("endpoint_a")}
        vong = ([s.get("vertices") or []] if s.get("kind") == "construct_polygon"
                else s.get("faces") or [] if s.get("kind") == "construct_solid" else [])
        for v in vong:
            ra |= {frozenset((a, v[(i + 1) % len(v)])) for i, a in enumerate(v)}
    return ra


def _doan_duoc_hoi(cau: list[dict[str, Any]], khai: list[dict[str, Any]], contract: Any,
                   dung: set[str]) -> bool:
    """regular-square-pyramid-w03 · H-W2-2: witness của một nghĩa vụ là khoảng cách giữa HAI ĐIỂM mà chưa đoạn nào
    nối chúng trước phép đo ⇒ dựng đoạn ấy ngay trước phép đo, để đáp số "độ dài đoạn SH" có chỗ bám trên hình (luật
    nhãn W2 · A). Khoảng cách tới đường/mặt giữ nhân chứng W18, không thêm gì."""
    diem = ({s["target_var"] for s in cau if s.get("kind") in ("declare_point", "construct_point")}
            | {k["name"] for k in khai if k.get("type") == "point3"})
    them = False
    for w in [o.witness for o in getattr(contract, "obligations", None) or () if o.witness]:
        j = next((i for i, s in enumerate(cau) if s.get("kind") == "assign" and s.get("target_var") == w), None)
        e = (cau[j].get("expr") or {}) if j is not None else {}
        p, q = e.get("of"), e.get("wrt")
        if not (e.get("kind") == "measure" and e.get("quantity") == "distance" and p != q and {p, q} <= diem):
            continue
        if frozenset((p, q)) in _canh_da_dung(cau[:j]):
            continue
        # Tên theo thứ tự đề viết ("đoạn AK" ⇒ AK dù chương trình đo d(K, A)).
        van = str(getattr(contract, "problem_text", "") or "").lower()
        if ("đoạn " + _ky(q) + _ky(p)).lower() in van and ("đoạn " + _ky(p) + _ky(q)).lower() not in van:
            p, q = q, p
        ten = _ten_moi(f"doan_{p}{q}", dung)
        cau.insert(j, {"kind": "construct_segment", "target_var": ten, "endpoint_a": p, "endpoint_b": q,
                       "label": "Đoạn " + _ky(p) + _ky(q)})
        khai.append({"name": ten, "type": "segment3"})
        them = True
    return them


def hoan_thien_dung_hinh(spec: SemanticProgramSpec, contract: Any = None) -> KetQuaHoanThien:
    """Bổ sung các bước dựng mà lớp hình đòi (đáy, đường cao, đáy trên, cạnh bên)
    ngay TRƯỚC mỗi `construct_solid` cấp ngoài phân loại được; và đoạn mà đề hỏi độ
    dài ngay trước phép đo của nó (`_doan_duoc_hoi`, W3).

    Bản gốc không bao giờ bị sửa; mọi câu lệnh và khai báo gốc giữ nguyên (chỉ phép
    dời an toàn đổi vị trí). Vật dựng SAU khối không bao giờ được tính là đã xong
    trước khi khép: dời được thì dời (`DA_DOI`), không thì để ngỏ (`DO_DANG`) và không
    chèn bản trùng. Tất định, bất biến khi lặp; đầu ra tự thẩm định (lược đồ + tĩnh),
    hỏng thì trả bản gốc với `TU_CHOI_DAU_RA` — một đáp số đúng không bao giờ bị từ
    chối vì bước trình bày.
    """
    sha_goc = _sha(spec)
    d = spec.model_dump(mode="json", exclude_none=True)
    cau, khai = d["statements"], d["memory_declarations"]
    dung = {x["name"] for x in khai} | _dinh_nghia(cau)
    trang_thai: list[tuple[str, str]] = []
    doi = False
    for khoi in [s["target_var"] for s in cau if s.get("kind") == "construct_solid"]:
        s = cau[_vi_tri(cau, khoi)]
        nguon, lop, apex, day, tren = lop_khoi(s.get("vertices") or [], s.get("faces") or [],
                                               contract, cau)
        if nguon not in NGUON_PHAN_LOAI:
            trang_thai.append((khoi, nguon))
            continue
        i = _vi_tri(cau, khoi)
        chan = (chan_duong_cao(cau, contract, apex, day, _da_co(khai, cau[:i]))
                if lop == LOP_CHOP else None)
        tt, thieu = DA_DU, []
        for vai, loai, dinh in ke_hoach(lop, apex, day, tren, chan):
            i = _vi_tri(cau, khoi)
            co = [j for j, x in enumerate(cau) if _co_vat(x, loai, frozenset(dinh))]
            if any(j < i for j in co):
                continue
            if not co:
                thieu.append((vai, loai, dinh))
            elif _doi_duoc(cau, khai, i, co[0]):
                cau.insert(i, cau.pop(co[0]))
                tt, doi = (tt if tt == DO_DANG else DA_DOI), True
            else:
                tt = DO_DANG
        if thieu:
            moi_cau, moi_khai = _phat(thieu, lop, dung)
            i = _vi_tri(cau, khoi)
            cau[i:i] = moi_cau
            khai += moi_khai
            doi = True
        trang_thai.append((khoi, tt))
    doi = _doan_duoc_hoi(cau, khai, contract, dung) or doi
    if not doi or any(t == HONG for _k, t in trang_thai):
        return KetQuaHoanThien(spec, tuple(trang_thai), sha_goc, sha_goc)
    try:
        moi = SemanticProgramSpec.model_validate(d)
    except ValidationError:
        moi = None
    if moi is None or not kiem_tinh(moi).ok:
        bo = tuple((k, TU_CHOI_DAU_RA if t in (DA_DU, DA_DOI, DO_DANG) else t) for k, t in trang_thai)
        return KetQuaHoanThien(spec, bo, sha_goc, sha_goc)
    return KetQuaHoanThien(moi, tuple(trang_thai), sha_goc, _sha(moi))


# ── Vai trò của vật trong cảnh (producer: `simulation_state`) ───────────────

def gan_vai_tro_dung(objects: list[dict[str, Any]], spec: SemanticProgramSpec,
                     contract: Any = None) -> None:
    """Gắn `formation_roles` cho mọi vật; `shape_class` + `formation_requirements`
    cho khối phân loại được và cho thiết diện. Cùng `lop_khoi`/`chan_duong_cao` với
    bước bổ sung — một thẩm quyền. Khối mơ hồ/không hỗ trợ/lệch hợp đồng không có
    lớp, để bộ kiểm độc lập (harness) đánh trượt nó thay vì đoán."""
    d = spec.model_dump(mode="json", exclude_none=True)
    cau, khai = d["statements"], d["memory_declarations"]
    khoi: list[tuple] = []
    for o in objects:
        if o.get("type") != "solid" or not o.get("vertex_ids") or o.get("faces") is None:
            continue
        nguon, lop, apex, day, tren = lop_khoi(o["vertex_ids"], o["faces"], contract, cau)
        if nguon not in NGUON_PHAN_LOAI:
            continue
        i = _vi_tri(cau, o["id"])
        chan = (chan_duong_cao(cau, contract, apex, day, _da_co(khai, cau[:i]))
                if lop == LOP_CHOP and i is not None else None)
        o["shape_class"] = lop
        o["formation_requirements"] = yeu_cau(lop, chan)
        khoi.append((lop, apex, day, tren, chan))
    mat_cat: set[str] = set()
    for o in objects:
        if o.get("type") == "section":
            o["shape_class"] = LOP_THIET_DIEN
            o["formation_requirements"] = list(TOI_THIEU[LOP_THIET_DIEN])
            mat_cat |= set(o.get("sources") or ())
    for o in objects:
        o["formation_roles"] = sorted(_vai_cua(o, khoi, mat_cat))


def _vai_cua(o: dict[str, Any], khoi: list[tuple], mat_cat: set[str]) -> set[str]:
    t = o.get("type")
    if t in ("solid", "curved_solid"):
        return {KHEP_KHOI}
    if t == "section":        # vai của thiết diện là vai THEO SỰ KIỆN (giao, khép) — scene3d
        return set()
    dinh = set(o.get("vertex_ids") or o.get("endpoint_ids") or ())
    vai: set[str] = set()
    for lop, apex, day, tren, chan in khoi:
        if t == "polygon3":
            if dinh == set(day):
                vai.add(DUNG_DAY)
            elif tren and dinh == set(tren):
                vai.add(DUNG_DAY_TREN)
        elif t == "segment3" and len(dinh) == 2:
            if chan is not None and dinh == {apex, chan}:
                vai.add(DUNG_CAO)
            if (lop == LOP_CHOP and apex in dinh and dinh - {apex} <= set(day)) or (
                    lop == LOP_LANG_TRU and any(dinh == {u, w} for u, w in zip(day, tren))):
                vai.add(DUNG_BIEN_BEN)
    if t == "plane3" and o.get("id") in mat_cat:
        vai.add(DUNG_MAT_CAT)
    if not vai and o.get("origin") == "derived" and t not in ("quantity", "vector3"):
        vai.add(DUNG_PHU)
    return vai
