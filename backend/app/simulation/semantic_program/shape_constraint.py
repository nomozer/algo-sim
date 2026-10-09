# -*- coding: utf-8 -*-
"""Đọc RÀNG BUỘC HÌNH DẠNG đề nêu tường minh — từ vựng ĐÓNG (W15, quyết định U1).

Cùng họ với `point_coordinate` / `plane_equation` / `segment_relation`: server đọc
CÂU ĐỀ và phát ràng buộc do server sở hữu, gắn đúng định danh thực thể. Chỉ dùng để
XÁC NHẬN tiền đề của chứng chỉ giả định (`assumption_gate`) và kiểm phản ví dụ —
không bao giờ đi vào fact graph, không bao giờ nâng một fact của mô hình thành GIVEN.

─── VÌ SAO TỪ VỰNG ĐÓNG ───────────────────────────────────────────────────

Lối viết ngoài từ vựng không phát gì; ở cổng, thiếu tiền đề ⇒ `UNDETERMINED` (từ
chối). Đoán nghĩa một câu lạ là đặt phép đoán vào giữa đường gác cửa — đúng thứ
`point_coordinate` đã từ chối làm với thập phân dấu phẩy. Bảng từ vựng, thứ tự
`entities` và ví dụ: `docs/architecture/ASSUMPTION_CERTIFICATE_AMENDMENT.md` §2.1;
khoá: `tests/geometry/test_shape_constraint.py`.

─── ĐỌC TRÊN ĐỀ GỐC ───────────────────────────────────────────────────────

`span` trỏ vào CHÍNH chuỗi đề, nên chỉ chuẩn hoá thứ giữ nguyên độ dài (`′`/`’` →
`'`). `segment_relation._chuan` đổi `bằng` → `=` (đổi độ dài) nên không dùng ở đây;
các mẫu tự nhận cả `bằng` lẫn `=`.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from ..geometry.radical import ExactNumber
from .segment_relation import _D as _E
from .segment_relation import _HET_DO_DAI, _SO_DO_DAI as _SO
from .segment_relation import MAU_DO_DAI, _chuan
from .segment_relation import _phan_do_dai as _phan
from .source_entities import dinh_danh_thuc_the


@dataclass(frozen=True)
class RangBuoc:
    """Một ràng buộc hình dạng server đọc được từ đề."""

    kind: str
    entities: tuple[str, ...]
    value: ExactNumber | None          # §18.3: số đo của đề có thể là căn `k√n`
    span: tuple[int, int]


_TRUOC = r"(?<![A-Za-z0-9'])"
_HET_CHU = r"(?![A-Za-zÀ-ỹ])"

_KHOI_CHOP = re.compile(
    rf"(?:[Hh]ình|[Kk]hối)\s+chóp(?:\s+(?:tam|tứ|ngũ|lục)\s+giác(?:\s+đều)?|\s+đều)?\s+"
    rf"(?P<dinh>{_E})\.(?P<day>(?:{_E}){{3,}})(?![A-Za-z0-9'])")
#: c0-whole-solid-reader — chóp tứ/tam giác ĐỀU gọi tên đỉnh và đáy bằng lời: `… có đỉnh (là) S và|, (mặt) đáy (là)
#: ABCD`. Cùng nhóm `dinh`/`day` với `_KHOI_CHOP`: đọc như ký hiệu `S.ABCD`. Không "đều" ⇒ không đọc (ngoài từ vựng).
_KHOI_CHOP_DINH_DAY = re.compile(
    rf"(?:[Hh]ình|[Kk]hối)\s+chóp\s+(?:tam|tứ)\s+giác\s+đều\s*,?\s+có\s+đỉnh\s+(?:là\s+)?(?P<dinh>{_E})\s*(?:,|và)\s*"
    rf"(?:có\s+)?(?:mặt\s+)?đáy\s+(?:là\s+)?(?P<day>(?:{_E}){{3,}})(?![A-Za-z0-9'])")
#: Loại chóp đều trong một ký hiệu khối: `chóp đều` (số đỉnh đáy quyết định) hoặc `chóp tứ/tam giác đều`.
_CHOP_DEU = re.compile(r"chóp\s+(?:(?P<g>tam|tứ|ngũ|lục)\s+giác\s+)?đều")
#: Khẳng định đứng ngay sau "không phải (là)" là PHỦ ĐỊNH — không phải tiền đề.
_PHU_DINH = re.compile(r"không\s+phải(?:\s+là)?\s*$")


#: Đuôi của danh từ khối không tên `hình/khối chóp` khi đó là chóp tứ/tam giác ĐỀU.
_CHOP_DEU_KHONG_TEN = re.compile(r"\s+(?P<g>tam|tứ)\s+giác\s+đều(?![A-Za-zÀ-ỹ])")
_TEN_DIEM = re.compile(rf"(?<![a-zà-ỹ])({_E})(?![a-zà-ỹ])")
_TEN_DIEM_TOA_DO = re.compile(rf"(?<![a-zà-ỹ])({_E})\s*\(")


def ten_diem_khong_toa_do(problem_text: str | None) -> set[str]:
    """Điểm đề GỌI TÊN mà không cho toạ độ. Rỗng ⇔ cách đặt tên đỉnh của một khối không tên không mang nghĩa nào
    đề chưa cố định (không tên điểm nào, hoặc mọi điểm có toạ độ) — điều kiện duy nhất để gắn khối ấy."""
    de = problem_text or ""
    return set(_TEN_DIEM.findall(de)) - set(_TEN_DIEM_TOA_DO.findall(de))


def _cac_chop(de: str) -> list[re.Match]:
    """Mọi ký hiệu chóp có tên đỉnh/đáy (`S.ABCD` hoặc `có đỉnh S và đáy ABCD`), theo vị trí trong đề."""
    return sorted([*_KHOI_CHOP.finditer(de), *_KHOI_CHOP_DINH_DAY.finditer(de)], key=lambda m: m.start())
_KHOI_LANG_TRU = re.compile(
    rf"(?P<noun>(?:[Hh]ình|[Kk]hối)\s+(?:lăng\s+trụ(?:\s+(?:đứng|xiên))?(?:\s+(?:tam|tứ)\s+giác"
    rf"(?:\s+đều)?)?|hộp(?:\s+chữ\s+nhật)?|lập\s+phương)|[Ll]ăng\s+trụ(?:\s+(?:đứng|xiên))?)\s+"
    rf"(?P<day>(?:{_E}){{3,}})\.(?P<tren>(?:{_E}){{3,}})(?![A-Za-z0-9'])")
_CANH_LAP_PHUONG = re.compile(
    rf"\s*,?\s*(?:có\s+)?(?:độ\s+dài\s+)?cạnh\s+(?:bằng\s+|=\s*|là\s+)?(?P<so>{_SO}){_HET_DO_DAI}")
#: §18.1 — tứ diện ABCD (đỉnh = ký hiệu đầu, đáy = ba ký hiệu sau); `đều` ⇒ mọi cạnh bằng nhau.
_KHOI_TU_DIEN = re.compile(
    rf"(?:(?:[Hh]ình|[Kk]hối)\s+)?[Tt]ứ\s+diện(?P<deu>\s+đều)?\s+(?P<ten>(?:{_E}){{4}})(?![A-Za-z0-9'])")
#: §18.1 — "có tất cả các cạnh (đều) bằng a" của khối chóp tam giác đều duy nhất ⇒ tứ diện đều.
_TAT_CA_CANH = re.compile(
    rf"(?:có\s+)?(?:tất\s+cả\s+các|mọi)\s+cạnh\s+(?:đều\s+)?(?:bằng|=|là)?\s*(?P<so>{_SO}){_HET_DO_DAI}")
#: §18.1 — tâm của đáy TAM GIÁC đề gọi tên: `G là trọng tâm (của) (tam giác (đều)) ABC` · `O là tâm (của) (mặt) đáy`
#: · `O là tâm (của) tam giác (đều) ABC`.
_TAM_TAM_GIAC = re.compile(
    rf"(?<![A-Za-z0-9'])(?P<o>{_E})\s+là\s+(?:trọng\s+tâm|tâm)\s+(?:của\s+)?(?:(?:mặt\s+)?đáy(?![A-Za-zÀ-ỹ])"
    rf"|(?:tam\s+giác(?:\s+đều)?\s+)?(?P<ten>(?:{_E}){{3}})(?![A-Za-z0-9']))")
#: Danh từ khối, để đếm khối của PHẦN DỮ KIỆN (đề cắt tại chữ `Tính` đầu tiên).
_DANH_TU_KHOI = re.compile(
    rf"(?:[Hh]ình|[Kk]hối)\s+(?:lăng\s+trụ(?:\s+(?:đứng|xiên))?|hộp(?:\s+chữ\s+nhật)?|lập\s+phương"
    rf"|chóp|trụ|nón|cầu){_HET_CHU}|[Mm]ặt\s+cầu{_HET_CHU}")
#: Đỉnh góc vuông: `tại X` · `ở đỉnh X` · `ở X` · `đỉnh X` (U4 · G1: lối viết thường gặp).
_TAI = r"(?:tại|ở\s+đỉnh|ở|đỉnh)"
_DAY = re.compile(
    rf"[Đđ]áy\s+(?:(?P<ten>(?:{_E}){{3,}})\s+)?là\s+(?:một\s+)?(?P<loai>hình\s+chữ\s+nhật|hình\s+vuông"
    rf"|hình\s+bình\s+hành|hình\s+thoi|tam\s+giác\s+đều|tam\s+giác\s+vuông(?:\s+cân)?\s+{_TAI}\s+(?P<tai>{_E}))"
    rf"(?:\s+cạnh\s+(?:bằng\s+|=\s*)?(?P<canh>{_SO}){_HET_DO_DAI})?(?![\d/])")
#: §20.1 — `đáy (ABCD)? là hình thang vuông tại P và Q`: góc vuông tại hai đỉnh KỀ của đáy tứ giác.
_HINH_THANG_VUONG = re.compile(
    rf"[Đđ]áy\s+(?:(?P<ten>(?:{_E}){{4}})\s+)?là\s+(?:một\s+)?hình\s+thang\s+vuông\s+{_TAI}\s+(?P<p>{_E})"
    rf"\s*(?:,|và)\s*(?P<q>{_E})(?![A-Za-z0-9'])")
#: Tam giác CÓ TÊN vuông tại một đỉnh của nó — `tam giác ABC vuông tại A`, `đáy ABC vuông tại A`.
_TAM_GIAC_VUONG = re.compile(
    rf"(?:[Tt]am\s+giác|[Đđ]áy)\s+(?P<t>(?:{_E}){{3}})\s+vuông(?:\s+cân)?\s+{_TAI}\s+(?P<tai>{_E})")
_VUONG_GOC_MAT = re.compile(
    rf"{_TRUOC}(?P<p>{_E})(?P<q>{_E})\s*(?:vuông\s+góc\s+với|⊥)\s*(?:(?:mặt\s+phẳng|mp)\s*)?"
    rf"(?:\((?P<mp>(?:{_E}){{3,}})\)|(?P<day>mặt\s+đáy|đáy){_HET_CHU})")
_VUONG_GOC_DUONG = re.compile(
    rf"{_TRUOC}(?P<p>{_E})(?P<q>{_E})\s*(?:vuông\s+góc\s+với|⊥)\s*(?P<r>{_E})(?P<t>{_E})(?![A-Za-z0-9'(])")
_GOC_90 = re.compile(
    rf"[Gg]óc\s+(?P<y>{_E})(?P<x>{_E})(?P<z>{_E})\s*(?:=|bằng)\s*90\s*(?:°|º|độ)")
_CHIEU_CAO = re.compile(
    rf"chiều\s+cao(?:\s+của\s+(?:hình|khối)\s+[^\s,.]+(?:\s+[^\s,.]+)?)?\s*(?:bằng|=|là)?\s*"
    rf"(?P<so>{_SO}){_HET_DO_DAI}")
#: regular-square-pyramid-w01 — số đo của chóp tứ giác ĐỀU duy nhất: cạnh đáy, cạnh bên, trung đoạn (đường
#: cao của mặt bên). Chỉ gắn khi đề nêu đúng một khối và khối ấy là chóp tứ giác đều.
_CANH_DAY = re.compile(rf"cạnh\s+đáy\s*(?:bằng|=|là)?\s*(?P<so>{_SO}){_HET_DO_DAI}")
_CANH_BEN = re.compile(rf"cạnh\s+bên\s*(?:bằng|=|là)?\s*(?P<so>{_SO}){_HET_DO_DAI}")
_TRUNG_DOAN = re.compile(
    rf"(?:trung\s+đoạn|đường\s+cao\s+(?:của\s+)?(?:mỗi\s+)?mặt\s+bên)\s*(?:bằng|=|là)?\s*(?P<so>{_SO}){_HET_DO_DAI}")
#: Tâm đáy được ĐỀ gọi tên: `O là tâm (của) (mặt) đáy` · `O là tâm (của) hình vuông ABCD` · `O là giao điểm
#: (của) AC và BD` (hai đường chéo của đáy). Phát `base_centre(O, *đáy)` chỉ khi khớp đáy của chóp đều duy nhất.
_TAM_DAY = re.compile(
    rf"{_TRUOC}(?P<o>{_E})\s+là\s+(?:tâm\s+(?:của\s+)?(?:(?:mặt\s+)?đáy|hình\s+vuông\s+(?P<ten>(?:{_E}){{4}}))"
    rf"|giao\s+điểm\s+(?:của\s+)?(?:hai\s+đường\s+chéo\s+)?(?P<p>{_E})(?P<q>{_E})\s+(?:và|với)\s+(?P<r>{_E})"
    rf"(?P<t>{_E}))(?![A-Za-z0-9'])")
_TINH = re.compile(rf"(?<![A-Za-zÀ-ỹ])Tính{_HET_CHU}")
#: Một ký hiệu khối có chấm mà các mẫu trên không đọc được (vd `ABC.DE`).
_KY_HIEU_KHOI_LOI = re.compile(rf"\s+(?:{_E})+\.(?:{_E})+")

_KIEU_LANG_TRU = (("lập phương", "cube"), ("hộp chữ nhật", "cuboid"), ("đứng", "right_prism"),
                  ("xiên", "oblique_prism"))
_KIEU_DAY = {"hình chữ nhật": "base_rectangle", "hình vuông": "base_square",
             "hình bình hành": "base_parallelogram", "hình thoi": "base_rhombus", "tam giác đều": "base_equilateral"}
#: Số đo của đáy đọc được thành value (cạnh): đáy vuông, đáy tam giác đều (§18.1).
_DAY_CO_CANH = frozenset({"base_square", "base_equilateral"})


def _ten(chuoi: str) -> tuple[str, ...]:
    return tuple(dinh_danh_thuc_the(t)[0] for t in re.findall(_E, chuoi))


def _gon(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def _kieu(noun: str) -> str | None:
    noun = _gon(noun)
    return next((k for tu, k in _KIEU_LANG_TRU if tu in noun), None)


def _khoi_cua_du_kien(du_kien: str):
    """→ (entities, đáy) của khối DUY NHẤT phần dữ kiện nhắc tới; `((), ())` nếu đó là một
    khối không tên; `None` nếu không có hoặc hơn một khối (khi ấy "đáy"/"chiều cao" không gắn)."""
    co_ten: dict[tuple, tuple] = {}
    dau_ky_hieu = set()
    for m in _cac_chop(du_kien):
        ent = _ten(m.group("dinh")) + _ten(m.group("day"))
        co_ten.setdefault(ent, ent[1:])
        dau_ky_hieu.add(m.start())
    for m in _KHOI_LANG_TRU.finditer(du_kien):
        day, tren = _ten(m.group("day")), _ten(m.group("tren"))
        if len(day) == len(tren):
            co_ten.setdefault(day + tren, day)
            dau_ky_hieu.add(m.start())
    for m in _KHOI_TU_DIEN.finditer(du_kien):
        if m.group("deu"):                     # §18.1: chỉ tứ diện đều là khối của bộ đọc
            ent = _ten(m.group("ten"))
            co_ten.setdefault(ent, ent[1:])
            dau_ky_hieu.add(m.start())
    khong_ten = [m for m in _DANH_TU_KHOI.finditer(du_kien) if m.start() not in dau_ky_hieu]
    if any(_KY_HIEU_KHOI_LOI.match(du_kien, m.end()) for m in khong_ten):
        return None                            # ký hiệu khối có mà không đọc được (vd `ABC.DE`)
    if len(co_ten) == 1 and not khong_ten:
        ((ent, day),) = co_ten.items()
        return ent, day, None
    if not co_ten and len(khong_ten) == 1:
        return (), (), khong_ten[0]
    return None


def doc_rang_buoc(problem_text: str | None) -> tuple[RangBuoc, ...]:
    """Mọi ràng buộc hình dạng đề nêu theo từ vựng đóng. Không đọc InputFact."""
    de = (problem_text or "").replace("′", "'").replace("’", "'")
    if not de.strip():
        return ()
    ra: list[RangBuoc] = []

    def phat(kind: str, ent, value, a: int, b: int) -> None:
        r = RangBuoc(kind, tuple(ent), value, (a, b))
        if r not in ra:
            ra.append(r)

    # ── ký hiệu khối ─────────────────────────────────────────────────────
    for m in _cac_chop(de):
        ent = _ten(m.group("dinh")) + _ten(m.group("day"))
        phat("pyramid", ent, None, m.start(), m.end())
        # Chóp tứ giác ĐỀU: đáy vuông và chân đường cao ở tâm đáy (khuôn T7); chóp tam giác ĐỀU: đáy đều, chân ở
        # trọng tâm (T8, §18). `chóp đều`: số đỉnh đáy quyết định. Ngũ/lục giác đều chưa đọc; phủ định không đọc.
        deu = _CHOP_DEU.search(m.group(0))
        if deu is None or _PHU_DINH.search(de, 0, m.start()):
            continue
        if len(ent) == 5 and deu.group("g") in (None, "tứ"):
            phat("regular_square_pyramid", ent, None, m.start(), m.end())
            phat("base_square", ent[1:], None, m.start(), m.end())
        if len(ent) == 4 and deu.group("g") in (None, "tam"):
            phat("regular_triangular_pyramid", ent, None, m.start(), m.end())
            phat("base_equilateral", ent[1:], None, m.start(), m.end())
    for m in _KHOI_TU_DIEN.finditer(de):
        # CHỈ tứ diện ĐỀU (đính chính §18.1 trước khi đo): "tứ diện ABCD" trơn vẫn không phát gì — đưa mọi tứ diện vào
        # vùng đa diện sẽ từ chối các đề tứ diện vuông/ngoại tiếp đang phục vụ (quyết định U3: cổng chỉ từ chối trong
        # vùng có chứng chỉ). Giới hạn ghi ở OPEN_ISSUES.
        if not m.group("deu"):
            continue
        ent = _ten(m.group("ten"))             # mọi cạnh bằng nhau: chóp tam giác đều có cạnh bên = cạnh đáy
        for kind in ("pyramid", "regular_tetrahedron", "regular_triangular_pyramid"):
            phat(kind, ent, None, m.start(), m.end())
        phat("base_equilateral", ent[1:], None, m.start(), m.end())
        if c := _CANH_LAP_PHUONG.match(de, m.end()):
            phat("edge_all", ent, _phan(c.group("so")), m.start(), c.end())
    for m in _KHOI_LANG_TRU.finditer(de):
        day, tren = _ten(m.group("day")), _ten(m.group("tren"))
        if len(day) != len(tren):
            continue
        phat("prism", day + tren, None, m.start(), m.end())
        kieu = _kieu(m.group("noun"))
        if kieu:
            phat(kieu, day + tren, None, m.start(), m.end())
        if kieu == "cube" and (c := _CANH_LAP_PHUONG.match(de, m.end())):
            phat("cube_edge", day + tren, _phan(c.group("so")), m.start(), c.end())

    # ── khối duy nhất của phần dữ kiện: chỉ khi ấy "đáy"/"chiều cao" mới gắn ──
    du_kien = de[:t.start()] if (t := _TINH.search(de)) else de
    khoi = _khoi_cua_du_kien(du_kien)
    if khoi is not None and khoi[2] is not None and _kieu(khoi[2].group(0)) == "right_prism":
        phat("right_prism", (), None, khoi[2].start(), khoi[2].end())
    # unnamed-regular-pyramid-grounding: chóp ĐỀU không tên duy nhất ⇒ khẳng định `()`; cổng gắn nó (hoặc không).
    if khoi is not None and khoi[2] is not None and (g := _CHOP_DEU_KHONG_TEN.match(du_kien, khoi[2].end())) \
            and not _PHU_DINH.search(de, 0, khoi[2].start()):
        a, b = khoi[2].start(), g.end()
        tu = g.group("g") == "tứ"
        phat("regular_square_pyramid" if tu else "regular_triangular_pyramid", (), None, a, b)
        phat("base_square" if tu else "base_equilateral", (), None, a, b)

    # ── đáy: loại đáy, tam giác vuông ────────────────────────────────────
    for m in _DAY.finditer(de):
        if m.group("ten"):
            ten = _ten(m.group("ten"))
            if khoi is not None and khoi[0] and set(ten) != set(khoi[1]):
                continue                       # tên đáy khác đáy của khối đã nêu
            day = khoi[1] if (khoi is not None and khoi[0]) else ten
        elif khoi is None:
            continue
        else:
            day = khoi[1]                      # () cho khối không tên
        loai = _gon(m.group("loai"))
        if loai.startswith("tam giác vuông"):
            tai = dinh_danh_thuc_the(m.group("tai"))[0]
            if len(day) == 3 and tai in day:
                phat("right_triangle", (tai, *[d for d in day if d != tai]), None, m.start(), m.end())
            continue
        kind = _KIEU_DAY[loai]
        if kind == "base_equilateral" and len(day) != 3:
            continue                           # "tam giác đều" chỉ gắn đáy ba đỉnh có tên
        if day or kind == "base_square":
            canh = _phan(m.group("canh")) if (kind in _DAY_CO_CANH and m.group("canh")) else None
            phat(kind, day, canh, m.start(), m.end())
    for m in _HINH_THANG_VUONG.finditer(de):
        if khoi is None or not khoi[0] or len(khoi[1]) != 4 or (
                m.group("ten") and set(_ten(m.group("ten"))) != set(khoi[1])):
            continue
        day = khoi[1]
        p, q = (dinh_danh_thuc_the(m.group(k))[0] for k in ("p", "q"))
        if p not in day or q not in day or (day.index(p) - day.index(q)) % 4 not in (1, 3):
            continue                           # hai góc vuông của hình thang vuông nằm ở hai đỉnh KỀ
        for v in (p, q):
            i = day.index(v)
            phat("line_perp_line", (v, day[i - 1], v, day[(i + 1) % 4]), None, m.start(), m.end())
    for m in _TAM_GIAC_VUONG.finditer(de):
        tg = _ten(m.group("t"))
        tai = dinh_danh_thuc_the(m.group("tai"))[0]
        if tai in tg:
            phat("right_triangle", (tai, *[d for d in tg if d != tai]), None, m.start(), m.end())

    # ── vuông góc ────────────────────────────────────────────────────────
    for m in _VUONG_GOC_MAT.finditer(de):
        if m.group("mp"):
            mat = _ten(m.group("mp"))
        elif khoi is not None and khoi[0]:
            mat = khoi[1]
        else:
            continue
        phat("line_perp_plane", _ten(m.group("p")) + _ten(m.group("q")) + mat, None, m.start(), m.end())
    for m in _VUONG_GOC_DUONG.finditer(de):
        phat("line_perp_line", _ten(m.group("p") + m.group("q") + m.group("r") + m.group("t")), None,
             m.start(), m.end())
    for m in _GOC_90.finditer(de):
        x, y, z = (dinh_danh_thuc_the(m.group(k))[0] for k in ("x", "y", "z"))
        phat("line_perp_line", (x, y, x, z), None, m.start(), m.end())

    # ── chiều cao của khối duy nhất ──────────────────────────────────────
    if khoi is not None:
        for m in _CHIEU_CAO.finditer(du_kien):
            phat("height", khoi[0], _phan(m.group("so")), m.start(), m.end())
    # ── số đo của chóp tứ giác đều duy nhất ──────────────────────────────
    if khoi is not None and any(r.kind == "regular_square_pyramid" and r.entities == khoi[0] for r in ra):
        for m in _CANH_DAY.finditer(du_kien):
            phat("base_square", khoi[1], _phan(m.group("so")), m.start(), m.end())
        for mau, kind in ((_CANH_BEN, "lateral_edge"), (_TRUNG_DOAN, "apothem")):
            for m in mau.finditer(du_kien):
                phat(kind, khoi[0], _phan(m.group("so")), m.start(), m.end())
        d4 = khoi[1]                           # () cho chóp không tên: không đường chéo nào gọi tên được
        cheo = {frozenset({d4[0], d4[2]}), frozenset({d4[1], d4[3]})} if len(d4) == 4 else set()
        for m in _TAM_DAY.finditer(du_kien):
            if m.group("p"):
                if {frozenset(_ten(m.group("p") + m.group("q"))), frozenset(_ten(m.group("r") + m.group("t")))} != cheo:
                    continue
            elif m.group("ten") and set(_ten(m.group("ten"))) != set(khoi[1]):
                continue
            phat("base_centre", _ten(m.group("o")) + khoi[1], None, m.start(), m.end())
    # ── §18.1: số đo của chóp tam giác đều duy nhất (tứ diện đều là một trường hợp) ──
    if khoi is not None and any(r.kind == "regular_triangular_pyramid" and r.entities == khoi[0] for r in ra):
        for m in _CANH_DAY.finditer(du_kien):
            phat("base_equilateral", khoi[1], _phan(m.group("so")), m.start(), m.end())
        for m in _CANH_BEN.finditer(du_kien):
            phat("lateral_edge", khoi[0], _phan(m.group("so")), m.start(), m.end())
        for m in _TAT_CA_CANH.finditer(du_kien):
            phat("regular_tetrahedron", khoi[0], None, m.start(), m.end())
            phat("edge_all", khoi[0], _phan(m.group("so")), m.start(), m.end())
        for m in _TAM_TAM_GIAC.finditer(du_kien):
            if m.group("ten") and set(_ten(m.group("ten"))) != set(khoi[1]):
                continue
            phat("base_centre", _ten(m.group("o")) + khoi[1], None, m.start(), m.end())
    return tuple(ra)


# ── W16 · §14.2 — mệnh đề MỤC TIÊU: quan hệ phải chứng minh không bao giờ là tiền đề ─────

#: Mở đầu một yêu cầu chứng minh / kiểm tra / câu hỏi — ranh giới chữ, không phân biệt hoa
#: thường. `Tính` KHÔNG ở đây: mệnh đề hỏi giá trị có thể mang `biết <giả thiết>`.
_MUC_TIEU = re.compile(r"(?<![^\W\d_])(?:chứng\s+minh|chứng\s+tỏ|cmr|kiểm\s+tra|hỏi)(?![^\W\d_])", re.I)
#: Hết mệnh đề: `? ! ;`, xuống dòng, dấu chấm kết câu (không phải chấm của `S.ABC`), hoặc `, biết`
#: — `Chứng minh X, biết Y`: Y là giả thiết (W17 §15.2, đính chính Task 3).
_HET_MENH_DE = re.compile(r"[?!;\n]|\.(?=\s|$)|,\s*biết(?![^\W\d_])")
#: Ranh giới đứng trước một câu hỏi `…?`.
_TRUOC_CAU_HOI = re.compile(r"[?!;,:\n]|\.(?=\s)")
#: Mệnh đề mở bằng `biết` sau dấu phẩy là GIẢ THIẾT, kể cả khi câu kết bằng `?` (W17, tự rà soát
#: cuối: "… bằng bao nhiêu, biết SA = 5?" từng che chính `biết SA = 5`).
_MO_BIET = re.compile(r"\s*biết(?![^\W\d_])", re.I)


def _nfc_theo_cum(de: str) -> tuple[str, list[int]]:
    """Bản NFC của `de` + chỉ số GỐC của từng ký tự (thêm một phần tử cuối = `len(de)`): đề
    gõ ở dạng tổ hợp (NFD) vẫn khớp từ khoá, và span trả về vẫn cắt đúng đề gốc."""
    ra, vi, i = [], [], 0
    while i < len(de):
        j = i + 1
        while j < len(de) and unicodedata.combining(de[j]):
            j += 1
        for x in unicodedata.normalize("NFC", de[i:j]):
            ra.append(x)
            vi.append(i)
        i = j
    return "".join(ra), vi + [len(de)]


def khoang_muc_tieu(problem_text: str | None) -> tuple[tuple[int, int], ...]:
    """Span `[đầu, cuối)` (trên đề gốc) của các mệnh đề MỤC TIÊU: từ một từ khoá tới hết mệnh
    đề, và câu kết bằng `?` tính từ ranh giới đứng trước nó. Giả thiết đứng TRƯỚC yêu cầu
    trong cùng câu không thuộc span."""
    nfc, vi = _nfc_theo_cum(problem_text or "")
    khoang = []
    for m in _MUC_TIEU.finditer(nfc):
        h = _HET_MENH_DE.search(nfc, m.end())
        khoang.append([m.start(), h.start() if h else len(nfc)])
    for q in re.finditer(r"\?", nfc):
        ranh = list(_TRUOC_CAU_HOI.finditer(nfc, 0, q.start()))
        cuoi = q.start()
        # `…, biết Y?`: câu hỏi là mệnh đề TRƯỚC dấu phẩy ấy, Y là giả thiết.
        while ranh and nfc[ranh[-1].start()] == "," and _MO_BIET.match(nfc, ranh[-1].end()):
            cuoi = ranh.pop().start()
        dau = ranh[-1].end() if ranh else 0
        while dau < cuoi and nfc[dau].isspace():
            dau += 1
        khoang.append([dau, cuoi])
    gop: list[list[int]] = []
    for a, b in sorted(khoang):
        if gop and a <= gop[-1][1]:
            gop[-1][1] = max(gop[-1][1], b)
        elif b > a:
            gop.append([a, b])
    return tuple((vi[a], vi[b]) for a, b in gop)


def che_muc_tieu(problem_text: str | None) -> str:
    """Đề với mọi span mục tiêu thay bằng khoảng trắng — CÙNG độ dài, nên span của mọi bộ
    đọc chạy trên nó vẫn trỏ đúng đề gốc. Chứng chỉ chỉ đọc tiền đề từ bản này (§14.2)."""
    con = list(problem_text or "")
    for a, b in khoang_muc_tieu(problem_text):
        con[a:b] = " " * (b - a)
    return "".join(con)


def neu_khoi_da_dien(problem_text: str | None) -> bool:
    """Đề nêu một khối ĐA DIỆN theo từ vựng đóng: ký hiệu chóp/lăng trụ, lăng trụ đứng không tên duy
    nhất, hoặc chóp đều không tên duy nhất (§25: kể cả khi cổng KHÔNG gắn được — đề gọi tên điểm thiếu toạ độ — để
    cổng chặn thay vì phục vụ một cách đặt tên đỉnh đề chưa cố định). Quyết định U3 (W15): route chỉ TỪ CHỐI theo cổng
    giả định trong vùng này — nơi lỗ W12/W14 đã đo và có chứng chỉ C0/C1; ngoài vùng cổng chỉ ghi trạng thái."""
    return any(r.kind in ("pyramid", "prism") or (r.kind == "right_prism" and not r.entities)
               or (r.kind in ("regular_square_pyramid", "regular_triangular_pyramid") and not r.entities)
               for r in doc_rang_buoc(problem_text))


# ── W17 · §15.1 — QUAN HỆ CẮT: mặt phẳng nào cắt khối nào theo thiết diện nào ─────────────

@dataclass(frozen=True)
class QuanHeCat:
    """Một câu cắt của đề (§15.1). `mat_phang`: tên trong ngoặc (`α`, `P'`, `MNP`) hoặc None
    (mặt phẳng viết bằng phương trình ngay trong câu — `khoa_mat_phang` trỏ vào cụm ấy);
    `khoi`: đỉnh của ký hiệu khối viết trong câu, `()` nếu câu không ghi; `thiet_dien`: tên
    hoặc None."""

    mat_phang: str | None
    khoi: tuple[str, ...]
    thiet_dien: str | None
    khoa_mat_phang: tuple[int, int]
    span: tuple[int, int]


_KY_PT = r"[0-9xyz+\-−–*/ ]"
_PT = rf"{_KY_PT}*={_KY_PT}*"
_SONG_SONG = r"(?:\s*,?\s*song\s+song\s+với\s+(?:(?:mặt\s+phẳng|mp)\s*)?(?:\([^\s()]{1,6}\)|(?:mặt\s+)?đáy))?"


def _mp(k: int) -> str:
    """Mặt phẳng: `Mặt phẳng [(X)] (đi) qua (ba điểm) A, C và B'` (danh tính là BA điểm, tên bỏ
    qua); `(X)` [`: <pt>` | `có phương trình (là) <pt>`], có hoặc không có `Mặt phẳng` đứng
    trước; hoặc `Mặt phẳng <pt>` (không tên)."""
    return (rf"(?P<mp{k}>(?:[Mm]ặt\s+phẳng|[Mm]p)(?:\s*\([^\s()]{{1,6}}\))?\s+(?:đi\s+)?qua\s+(?:(?:ba|các)\s+điểm\s+)?"
            rf"(?P<qua{k}>{_E}\s*,\s*{_E}(?:\s*,\s*|\s+và\s+){_E})(?![A-Za-z0-9'])"
            rf"|(?:(?:[Mm]ặt\s+phẳng|[Mm]p)\s*)?\((?P<ten{k}>[^\s()]{{1,6}})\)"
            rf"(?:\s*(?::|có\s+phương\s+trình(?:\s+là)?)\s*{_PT})?|(?:[Mm]ặt\s+phẳng|[Mm]p)\s+{_PT})")


def _khoi(k: int) -> str:
    return (rf"(?:[Kk]hối|[Hh]ình)\s+(?:chóp(?:\s+(?:tam|tứ|ngũ|lục)\s+giác(?:\s+đều)?)?"
            rf"|lăng\s+trụ(?:\s+(?:đứng|xiên))?(?:\s+(?:tam|tứ)\s+giác(?:\s+đều)?)?|hộp(?:\s+chữ\s+nhật)?"
            rf"|lập\s+phương)(?:\s+(?P<kh{k}>(?:{_E})+\.(?:{_E})+))?(?![A-Za-z0-9'])")


def _td(k: int) -> str:
    return rf"(?:\s*\((?P<td{k}>[^\s()]{{1,4}})\))?"


#: Mặt phẳng đứng ngay sau `với` là TÂN NGỮ ("song song/vuông góc với (X)"), không phải mặt phẳng
#: cắt — W17, tự rà soát cuối: "(Q) qua M và song song với (ABCD) cắt …" từng đọc thành (ABCD) cắt.
_TAN_NGU_VOI = re.compile(r"(?<![^\W\d_])với\s*(?:(?:mặt\s+phẳng|mp)\s*)?$", re.I)

#: Ba dạng ĐÓNG: chủ động, `thiết diện (T) của <khối> cắt bởi (X)`, `cắt <khối> bởi (X) (ta) được thiết diện (T)`.
_CAU_CAT = tuple(re.compile(m) for m in (
    rf"{_mp(1)}{_SONG_SONG}\s*,?\s*cắt\s+{_khoi(1)}\s+theo\s+(?:một\s+)?thiết\s+diện{_td(1)}",
    rf"[Tt]hiết\s+diện{_td(2)}\s+của\s+{_khoi(2)}\s+(?:khi\s+)?(?:bị\s+)?cắt\s+bởi\s+{_mp(2)}",
    rf"[Cc]ắt\s+{_khoi(3)}\s+bởi\s+{_mp(3)}\s*,?\s*(?:(?:ta\s+)?(?:thu\s+)?được\s+)?(?:một\s+)?thiết\s+diện{_td(3)}",
))


def doc_quan_he_cat(problem_text: str | None) -> tuple[QuanHeCat, ...]:
    """Mọi câu cắt đề nêu theo từ vựng đóng §15.1, đọc trên đề đã che mệnh đề mục tiêu (§14.2):
    một quan hệ phải chứng minh không bao giờ là quan hệ của phép dựng. Ngoài từ vựng ⇒ không phát."""
    de = che_muc_tieu(problem_text).replace("′", "'").replace("’", "'")
    ra: list[QuanHeCat] = []
    for k, mau in enumerate(_CAU_CAT, 1):
        for m in mau.finditer(de):
            if _TAN_NGU_VOI.search(de, max(0, m.start(f"mp{k}") - 40), m.start(f"mp{k}")):
                continue
            kh, qua = m.group(f"kh{k}"), m.group(f"qua{k}")
            ten = "".join(re.findall(_E, qua)) if qua else m.group(f"ten{k}")
            q = QuanHeCat(ten, _ten(kh.replace(".", "")) if kh else (),
                          m.group(f"td{k}"), (m.start(f"mp{k}"), m.end(f"mp{k}")), (m.start(), m.end()))
            if q not in ra:
                ra.append(q)
    return tuple(sorted(ra, key=lambda q: q.span))


#: Từ được phép còn lại khi phần dữ kiện đã đọc trọn — không từ nào mang số đo.
_TU_NOI = frozenset({"cho", "có", "và", "cạnh", "bên"})
#: Thông tin mà một span ĐÃ NUỐT nhưng không phát: tính đều của khối, tính cân của tam giác.
_TU_BI_BO = re.compile(rf"(?<![A-Za-zÀ-ỹ])(?:đều|cân){_HET_CHU}", re.I)


def phan_chua_doc(problem_text: str | None) -> tuple[str, ...]:
    """Mảnh của phần dữ kiện (trước `Tính`) mà không bộ đọc nào đọc TRỌN; rỗng ⇔ đọc trọn.

    `assumption_gate` (§7, đính chính Task 6) chỉ kết luận DEPENDENT — "đề không cho kích
    thước này" — khi phần dữ kiện đọc trọn: một câu ngoài từ vựng (góc, `SA = AB`, độ dài
    có căn…) có thể chính là câu cho kích thước ấy. Đã đọc = span của `doc_rang_buoc` + câu
    độ dài số (`segment_relation.MAU_DO_DAI`); còn lại chỉ được là từ nối `_TU_NOI`.
    """
    de = (problem_text or "").replace("′", "'").replace("’", "'")
    du_kien = de[:t.start()] if (t := _TINH.search(de)) else de
    con = list(du_kien)
    rb = doc_rang_buoc(problem_text)
    for r in rb:
        con[r.span[0]:r.span[1]] = " " * len(con[r.span[0]:r.span[1]])
    sot = MAU_DO_DAI.sub(" ", _chuan("".join(con)))
    ra = [t for t in re.findall(r"[^\W\d_]+|\d+|[^\w\s]", sot) if t.lower() not in _TU_NOI and t not in ",.;:"]
    # "đều" của chóp tứ giác đều (T7), chóp tam giác đều / tứ diện đều / đáy tam giác đều / "tất cả các cạnh đều"
    # (T8, §18.1) ĐÃ được đọc; mọi "đều"/"cân" khác vẫn là chữ bị nuốt.
    deu = [r.span for r in rb if r.kind in _KIND_DOC_DEU]
    ra += [m.group(0) for m in _TU_BI_BO.finditer(du_kien) if not any(a <= m.start() < b for a, b in deu)]
    ra += [m.group("canh") for m in _DAY.finditer(du_kien)
           if m.group("canh") and _KIEU_DAY.get(_gon(m.group("loai"))) not in _DAY_CO_CANH]
    return tuple(ra)


def _bang_nhau(do_dai: dict, cap: list[tuple[str, str]]) -> bool:
    """Mọi đoạn trong `cap` có độ dài nguồn và cùng một giá trị (`do_dai`: khoá frozenset định danh thực thể)."""
    gt = [do_dai.get(frozenset(p)) for p in cap]
    return None not in gt and len(set(gt)) == 1


def la_chop_tam_giac_deu(rb: tuple[RangBuoc, ...], apex: str, day: tuple, do_dai: dict) -> bool:
    """§18.2 — chóp tam giác đều: đề NÓI (`regular_triangular_pyramid`/`regular_tetrahedron`), hoặc SUY từ độ dài
    nguồn: đáy đều (`base_equilateral` hay ba cạnh đáy bằng nhau) VÀ ba cạnh bên bằng nhau (chân cách đều ba đỉnh
    đáy ⇒ tâm ngoại tiếp = trọng tâm của đáy đều). Ba cạnh bên bằng nhau MỘT MÌNH không đủ. Một thẩm quyền cho
    chứng chỉ T8 (`assumption_gate`) và chân đường cao của bước dựng (`formation._tam_day_deu`)."""
    if len(day) != 3:
        return False
    if any(r.kind in ("regular_triangular_pyramid", "regular_tetrahedron") and r.entities[:1] == (apex,)
           and set(r.entities[1:]) == set(day) for r in rb):
        return True
    a, b, c = day
    day_deu = (any(r.kind == "base_equilateral" and set(r.entities) == set(day) for r in rb)
               or _bang_nhau(do_dai, [(a, b), (b, c), (c, a)]))
    return day_deu and _bang_nhau(do_dai, [(apex, v) for v in day])


#: Ràng buộc mà span của nó đã đọc chữ "đều" (luật đọc trọn §7).
_KIND_DOC_DEU = frozenset({"regular_square_pyramid", "regular_triangular_pyramid", "regular_tetrahedron",
                           "base_equilateral", "edge_all"})
