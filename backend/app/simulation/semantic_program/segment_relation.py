# -*- coding: utf-8 -*-
"""QUAN HỆ CHIA ĐOẠN đọc từ ĐỀ, phát thành `SourceInvariant` có cấu trúc.

    `SEGMENT_RELATION_CONSISTENCY_VERIFICATION`, 2026-09-06 — bản đầu.
    `SEGMENT_RELATION_COVERAGE_HARDENING`,      2026-09-06 — hai pha.

─── LỖ NÓ BỊT, ĐO ĐƯỢC BẰNG QUOTA THẬT ─────────────────────────────────

Lượt `DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB`, ca `r3` arm A. Đề: *"đoạn EF dài
10; P nằm trên đoạn EF sao cho FP = 4·PE"*. Mô hình viết
`divide_segment(E, F, 1/4)` ⇒ `P = (5/2,0,0)`, và hệ trả **`served`** với
`PF = 15/2`.

Mọi cổng đều làm đúng việc của nó, và đó mới là chỗ đáng sợ: kernel thi hành
đúng chương trình đã nhận, `check_distance` tính lại đúng khoảng cách tới
điểm **đã dựng**, grounding thấy `source_fact_id` nên cho qua.

`source_fact_id` chứng minh **nguồn được viện có tồn tại**. Nó không, và
không thể, chứng minh **hình dựng ra thoả nội dung của nguồn ấy**.

─── VÌ SAO PHẢI TÁCH HAI PHA (bản 2026-09-06 chiều) ────────────────────

Bản đầu gộp neo và quan hệ vào **một** mẫu: *"Điểm M nằm trên đoạn AB **sao
cho** <quan hệ>"*. Nó đọc được `r1`–`r4` và **không đọc được `e4`**, dù `e4`
là ca có thật, đã chạy bằng quota thật:

    "… mặt phẳng vuông góc với PQ **cắt PQ tại điểm T** sao cho **PT bằng 20**
     …, chiều cao **PQ bằng 28**"

Ba thứ lệch cùng lúc: neo là **dạng cắt** chứ không phải *"nằm trên"*; từ nối
là **"bằng"** chứ không phải `=`; và độ dài cả đoạn nằm ở **một câu khác**
(*"chiều cao PQ bằng 28"*). Gộp một mẫu thì mỗi lối nói mới lại phải thêm một
mẫu — đúng thứ *"bảng liệt kê tay sẽ lặng lẽ bỏ sót lớp mới"* mà kho này đã
dọn ba lần.

Nên tách:

    ① NEO      → bộ ba (A, B, M): "M nằm trên/thuộc AB" · "cắt AB tại M"
                 · "M là trung điểm AB"
    ② QUAN HỆ  → tìm trên TOÀN BỘ đề + mọi `InputFact`, chỉ nhận mảnh nói về
                 đúng hai đoạn con của bộ ba ấy
    ③ ĐỘ DÀI   → |AB| tìm cùng cách, khi quan hệ là độ dài một nhánh

Nhờ ②–③ mà các mảnh dữ kiện **nằm rời nhau** vẫn ghép được, và luật ghép là
*"cùng xác định một bộ ba"* chứ không phải *"cùng một câu"*.

─── VÌ SAO ĐỌC TỪ ĐỀ, KHÔNG ĐỌC TỪ LỜI KHAI CỦA MÔ HÌNH ────────────────

Doctrine đã đăng ký ở `SourceInvariant`: *"toán hạng lấy từ chỗ khác: chính
câu văn của đề"*. Một cổng gác cửa mà đọc chuỗi do LLM tự đặt tên thì nó gác
chính thứ nó phải nghi ngờ.

─── BỎ SÓT THÌ ĐƯỢC, ĐOÁN BỪA THÌ KHÔNG ────────────────────────────────

Ba kết cục, và chúng **không được gộp**:

    COVERED       phát được bất biến ⇒ checker phán trên hình
    NOT_CHECKABLE thấy bộ ba + mảnh quan hệ + nguồn, nhưng KHÔNG tính được
                  `t` ⇒ **chặn `served`**: hệ chưa chứng minh được gì
    NOT_EXTRACTED không đủ tín hiệu để nói có quan hệ chia đoạn ⇒ im lặng,
                  giữ nguyên hành vi cũ

Gộp `NOT_EXTRACTED` vào *"đã kiểm"* là tự cho điểm; gộp nó vào *"vi phạm"* là
kết tội oan. Cả hai đều tệ hơn việc nói thẳng ra là chưa biết.
"""
from __future__ import annotations

import re
from fractions import Fraction
from typing import Optional

from .scale_normalization import SourceInvariant

#: Ký hiệu ĐIỂM: chữ hoa + chỉ số + phẩy tuỳ chọn. Cùng quy ước
#: `_MAU_DOAN_THANG` của `scale_normalization` — không dựng quy ước thứ hai.
_D = r"[A-Z]\d*['′]?"
_SO = r"\d+(?:\s*/\s*\d+)?"

#: `kind` của bất biến này. Một chuỗi, một chỗ khai, một checker.
KIND = "segment_division"
#: Thấy quan hệ nhưng KHÔNG giải được — trạng thái CHẶN, xem docstring.
KIND_CHUA_GIAI = "segment_division_unresolved"


def _chuan(s: str) -> str:
    """Chuẩn hoá lối viết, KHÔNG chuẩn hoá ngữ nghĩa.

    `bằng` → `=` · `·×*` → `*` · gộp khoảng trắng. Ba phép này chỉ đổi CÁCH
    VIẾT của cùng một quan hệ; không phép nào suy ra thêm thông tin.
    """
    s = re.sub(r"\s+", " ", s or "")
    s = re.sub(r"(?<![A-Za-zÀ-ỹ])bằng(?![A-Za-zÀ-ỹ])", "=", s, flags=re.I)
    return s.replace("·", "*").replace("×", "*")


# ── ① NEO: ba lối nói xác định một bộ ba (A, B, M) ─────────────────────────
#: *"Điểm P nằm trên đoạn EF"* · *"P thuộc EF"*
_NEO_TREN = re.compile(
    rf"(?:[ĐđDd]iểm\s+)?(?P<M>{_D})\s+(?:nằm\s+)?(?:thuộc|trên|nằm\s+trên)\s+"
    rf"(?:đoạn\s+(?:thẳng\s+)?)?(?P<A>{_D})(?P<B>{_D})(?![A-Za-z0-9])")
#: *"mặt phẳng … cắt PQ tại điểm T"* · *"đường thẳng d cắt AB tại M"*
_NEO_CAT = re.compile(
    rf"cắt\s+(?:đoạn\s+(?:thẳng\s+)?)?(?P<A>{_D})(?P<B>{_D})\s+tại\s+"
    rf"(?:điểm\s+)?(?P<M>{_D})(?![A-Za-z0-9])")
#: *"I là trung điểm của GH"*
_NEO_TRUNG_DIEM = re.compile(
    rf"(?:[ĐđDd]iểm\s+)?(?P<M>{_D})\s+là\s+trung\s+điểm\s+(?:của\s+)?"
    rf"(?:đoạn\s+(?:thẳng\s+)?)?(?P<A>{_D})(?P<B>{_D})(?![A-Za-z0-9])")

# ── ② QUAN HỆ giữa hai đoạn con ────────────────────────────────────────────
_QH_TI_SO = re.compile(
    rf"(?P<s1>{_D}{_D})\s*:\s*(?P<s2>{_D}{_D})\s*=\s*"
    rf"(?P<m>\d+)\s*:\s*(?P<n>\d+)")
_QH_BOI = re.compile(
    rf"(?P<s1>{_D}{_D})\s*=\s*(?P<k>{_SO})\s*\*?\s*(?P<s2>{_D}{_D})"
    rf"(?![A-Za-z0-9])")
_QH_DO_DAI = re.compile(
    rf"(?P<s1>{_D}{_D})\s*=\s*(?P<v>{_SO})(?![0-9/]|\s*[:*]|\s*{_D}{_D})")

# ── ③ ĐỘ DÀI cả đoạn ───────────────────────────────────────────────────────
_DO_DAI_CO = re.compile(
    rf"(?:đoạn\s+(?:thẳng\s+)?)?(?P<A>{_D})(?P<B>{_D})\s+có\s+độ\s+dài\s+"
    rf"(?P<v>{_SO})")


def _phan(s: str) -> Optional[Fraction]:
    try:
        return Fraction(str(s).replace(" ", ""))
    except (ValueError, ZeroDivisionError):
        return None


def _tach(seg: str) -> Optional[tuple[str, str]]:
    m = re.fullmatch(rf"({_D})({_D})", seg)
    return (m.group(1), m.group(2)) if m else None


def _phia(seg: str, M: str, A: str, B: str) -> Optional[str]:
    """Nhánh nào của phép chia: `"A"` (đầu A) hay `"B"` (đầu B)?

    Đoạn con hợp lệ phải gồm ĐÚNG `M` và một trong hai đầu mút. `"AB"` (cả
    đoạn) hay `"AX"` (điểm lạ) đều trả `None` — từ chối, không chọn bừa.
    """
    hai = _tach(seg)
    if hai is None or M not in hai:
        return None
    con = hai[0] if hai[1] == M else hai[1]
    return "A" if con == A else ("B" if con == B else None)


def _van_ban(contract, problem_text: str | None) -> list[str]:
    """ĐỀ + mọi mảnh chữ của `InputFact`, mỗi mảnh một phần tử.

    Tách phần tử chứ không nối thành một chuỗi: nối lại thì hai câu rời nhau
    có thể dính vào nhau và đẻ ra một quan hệ **không ai viết**.
    """
    ra = [_chuan(problem_text or getattr(contract, "problem_text", "") or "")]
    for f in getattr(contract, "input_facts", ()) or ():
        nhan = _chuan(str(getattr(f, "label", "") or ""))
        ra.append(nhan)
        for v in (getattr(f, "values", ()) or ()):
            ra.append(_chuan(str(v)))
            # ─── GHÉP NHÃN VỚI GIÁ TRỊ — đó CHÍNH LÀ nghĩa của `InputFact` ──
            #
            # Một mục *"Độ dài đoạn AM"* + `9` nói **`AM = 9`**, nhưng nhãn và
            # giá trị nằm ở hai trường, nên chuỗi ấy không tồn tại ở đâu cả và
            # mọi mẫu đều trượt. Dựng lại nó là ĐỌC ĐÚNG hợp đồng, không phải
            # suy thêm: `label` và `values` vốn là hai nửa của một câu.
            #
            # CHỈ với giá trị SỐ. Giá trị văn xuôi (*"P thuộc EF và FP = 4*PE"*)
            # đã tự là một câu; dán nhãn vào trước sẽ đẻ ra một quan hệ lai
            # không ai viết.
            if nhan and re.fullmatch(rf"\s*{_SO}\s*", str(v)):
                ra.append(f"{nhan} = {_chuan(str(v))}")
    return [x for x in ra if x]


def _do_dai_doan(manh: list[str], A: str, B: str) -> Optional[Fraction]:
    """|AB| — chấp nhận `AB = L` và *"đoạn AB có độ dài L"*, cả hai chiều viết."""
    gt: set[Fraction] = set()
    for van in manh:
        for m in _DO_DAI_CO.finditer(van):
            if {m.group("A"), m.group("B")} == {A, B} and (q := _phan(m.group("v"))):
                gt.add(q)
        for seg in (A + B, B + A):
            for m in re.finditer(
                    rf"(?<![A-Za-z0-9]){seg}\s*=\s*({_SO})(?![0-9/]|\s*[:*]|\s*{_D}{_D})",
                    van):
                if (q := _phan(m.group(1))):
                    gt.add(q)
    # Hai độ dài KHÁC nhau cho cùng một đoạn ⇒ không ai phân xử được.
    return gt.pop() if len(gt) == 1 else None


def _ti_le(manh: list[str], M: str, A: str, B: str
           ) -> tuple[Optional[Fraction], bool, str]:
    """→ `(t, co_tin_hieu, manh_quan_he)`.

    `t = None` mà `co_tin_hieu` ⇒ NOT_CHECKABLE. `co_tin_hieu` bật khi thấy một
    mảnh quan hệ nói về đúng hai đoạn con của bộ ba — tức đề CÓ nói về phép
    chia này, dù ta chưa tính ra `t`.

    Trả luôn **nguyên văn mảnh quan hệ** đã dùng: neo (*"cắt PQ tại điểm T"*)
    nói *chia đoạn nào*, mảnh này nói *chia theo tỉ lệ nào*, và thông điệp lỗi
    cần cả hai. Bản trước chỉ giữ neo, nên lời từ chối mất mất chính vế mà học
    sinh phải đọc để biết mình sai ở đâu.
    """
    dai = _do_dai_doan(manh, A, B)
    thay: set[Fraction] = set()
    tin_hieu = False
    nguyen_van: list[str] = []

    for van in manh:
        for m in _QH_TI_SO.finditer(van):
            p1 = _phia(m.group("s1"), M, A, B)
            p2 = _phia(m.group("s2"), M, A, B)
            if {p1, p2} != {"A", "B"}:
                continue
            tin_hieu = True
            nguyen_van.append(m.group(0).strip())
            a, b = int(m.group("m")), int(m.group("n"))
            if p1 == "B":
                a, b = b, a
            if a + b:
                thay.add(Fraction(a, a + b))

        for m in _QH_BOI.finditer(van):
            p1 = _phia(m.group("s1"), M, A, B)
            p2 = _phia(m.group("s2"), M, A, B)
            if {p1, p2} != {"A", "B"}:
                continue
            tin_hieu = True
            nguyen_van.append(m.group(0).strip())
            k = _phan(m.group("k"))
            if k is None or k <= 0:
                continue
            a, b = (k, Fraction(1)) if p1 == "A" else (Fraction(1), k)
            thay.add(a / (a + b))

        for m in _QH_DO_DAI.finditer(van):
            p1 = _phia(m.group("s1"), M, A, B)
            if p1 is None:
                continue
            tin_hieu = True                      # ← có nói về nhánh này
            nguyen_van.append(m.group(0).strip())
            v = _phan(m.group("v"))
            if v is None or dai is None or dai <= 0 or not (0 <= v <= dai):
                continue
            thay.add(v / dai if p1 == "A" else (dai - v) / dai)

    van = "; ".join(dict.fromkeys(nguyen_van))
    if len(thay) == 1:
        return thay.pop(), True, van
    # Không mảnh nào ⇒ chưa đủ tín hiệu. Nhiều `t` khác nhau ⇒ mơ hồ, và mơ hồ
    # KHÔNG phải "chưa thấy": ta đã thấy, chỉ không phân xử được.
    return None, tin_hieu or len(thay) > 1, van


def _nguon_cho(contract, M: str, A: str, B: str) -> str:
    """Mục dữ kiện nào NÓI VỀ quan hệ này — chỉ để truy vết và giải thích.

    ⚠️ Cổng **không** dùng nó để quyết định có kiểm hay không; đó đúng là lỗ
    mà `SEGMENT_RELATION_CONSISTENCY_VERIFICATION` đã đóng.
    """
    can = {M, A, B}
    tot = ""
    for f in getattr(contract, "input_facts", ()) or ():
        van = " ".join([str(f.label or "")] + [str(v) for v in (f.values or ())])
        ky = set(re.findall(_D, van))
        if can <= ky:
            return f.fact_id
        # Dự phòng: mục chỉ nói về HAI trong ba ký hiệu (vd *"Độ dài đoạn PT"*)
        # vẫn truy vết được, nhưng nhường mục nói đủ ba.
        if not tot and len(can & ky) >= 2:
            tot = f.fact_id
    return tot


def _moc(manh: list[str]) -> list[tuple[str, str, str, bool, str]]:
    """Mọi bộ ba `(A, B, M)` neo được, kèm cờ trung điểm và câu nguyên văn."""
    ra = []
    for van in manh:
        for mau, la_td in ((_NEO_TRUNG_DIEM, True), (_NEO_TREN, False),
                           (_NEO_CAT, False)):
            for m in mau.finditer(van):
                A, B, M = m.group("A"), m.group("B"), m.group("M")
                if len({A, B, M}) == 3:
                    ra.append((A, B, M, la_td, m.group(0).strip()))
    return ra


def bat_bien_chia_doan(contract, problem_text: str | None) -> tuple:
    """`SourceInvariant` cho mỗi quan hệ chia đoạn đọc được từ ĐỀ.

    Biểu diễn — **không thêm trường nào**; ý nghĩa của `points` do `kind`
    quyết và khai ở đúng một chỗ (đây):

        points   = (A, B, M)   A→B là HƯỚNG của đề, M là điểm bị ràng buộc
        expected = `t` hữu tỉ chính xác, `M = A + t·(B − A)`
                   — rỗng khi `kind = KIND_CHUA_GIAI`

    Trùng `M` với hai bộ ba KHÁC nhau ⇒ bỏ cả hai: đề nói hai điều về cùng một
    điểm mà tầng này chỉ đọc rời rạc thì nó không đủ tư cách phân xử.
    """
    manh = _van_ban(contract, problem_text)
    if not manh:
        return ()

    theo_m: dict[str, set[tuple[str, str]]] = {}
    ung_vien: dict[tuple[str, str, str], tuple[Optional[Fraction], bool, str]] = {}
    for A, B, M, la_td, cau in _moc(manh):
        theo_m.setdefault(M, set()).add((A, B))
        khoa = (A, B, M)
        if la_td:
            ung_vien[khoa] = (Fraction(1, 2), True, cau)
            continue
        if khoa in ung_vien and ung_vien[khoa][0] is not None:
            continue
        t, tin_hieu, van = _ti_le(manh, M, A, B)
        # NEO nói *chia đoạn nào*, MẢNH nói *theo tỉ lệ nào* — giữ cả hai.
        mo_ta = f"{cau} — {van}" if van else cau
        cu = ung_vien.get(khoa)
        if cu is None or (cu[0] is None and t is not None):
            ung_vien[khoa] = (t, tin_hieu or (cu[1] if cu else False), mo_ta)

    ra: list[SourceInvariant] = []
    for (A, B, M), (t, tin_hieu, cau) in ung_vien.items():
        if len(theo_m.get(M, ())) != 1:      # cùng M, hai đoạn khác nhau
            continue
        if t is None and not tin_hieu:       # NOT_EXTRACTED — im lặng
            continue
        ra.append(SourceInvariant(
            kind=KIND if t is not None else KIND_CHUA_GIAI,
            points=(A, B, M), expected=str(t) if t is not None else "",
            source_fact_id=_nguon_cho(contract, M, A, B),
            scale_symbol="", source_text=cau))
    return tuple(ra)
