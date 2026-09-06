# -*- coding: utf-8 -*-
"""QUAN HỆ CHIA ĐOẠN đọc từ ĐỀ, phát thành `SourceInvariant` có cấu trúc.

    `SEGMENT_RELATION_CONSISTENCY_VERIFICATION`, 2026-09-06.

─── LỖ NÓ BỊT, ĐO ĐƯỢC BẰNG QUOTA THẬT ─────────────────────────────────

Lượt `DIVIDE_SEGMENT_RATIO_AFFORDANCE_AB`, ca `r3` arm A. Đề: *"đoạn EF có độ
dài 10; P nằm trên đoạn EF sao cho FP = 4·PE"*. Mô hình viết
`divide_segment(E, F, 1/4)` ⇒ `P = (5/2, 0, 0)`, tức `PE = 5/2` chứ không phải
`2`. Hệ trả **`served`** với `PF = 15/2`.

Mọi cổng đều làm đúng việc của nó, và đó mới là chỗ đáng sợ:

    kernel        thi hành ĐÚNG chương trình đã nhận
    check_distance tính lại ĐÚNG khoảng cách từ `P` đã dựng tới `F`
    grounding      thấy `P` có `source_fact_id = 'vi_tri_diem'` ⇒ qua

`source_fact_id` chứng minh **nguồn được viện có tồn tại**. Nó không, và
không thể, chứng minh **hình dựng ra thoả nội dung của nguồn ấy**. Giữa hai
câu đó là một lỗ, và lỗ ấy hỏng **IM LẶNG** — học sinh nhận một đáp số sai
được trình bày y như một đáp số đúng.

─── VÌ SAO ĐỌC TỪ ĐỀ, KHÔNG ĐỌC TỪ LỜI KHAI CỦA MÔ HÌNH ────────────────

Doctrine này đã đăng ký ở `SourceInvariant`: *"toán hạng lấy từ chỗ khác:
chính câu văn của đề"*. Một cổng gác cửa mà đọc chuỗi do LLM tự đặt tên thì
nó gác chính thứ nó phải nghi ngờ. `check_source_invariants` cũng đã ghi
thẳng: *"không có đường nào để một chương trình tránh bị kiểm bằng cách im
lặng"*. Module này giữ đúng cả hai.

─── BỎ SÓT THÌ ĐƯỢC, ĐOÁN BỪA THÌ KHÔNG ────────────────────────────────

`bat_bien_nguon` đã đặt ra luật ấy và module này theo: mẫu nào không khớp thì
**không phát bất biến**, chứ không suy. Một bất biến trỏ nhầm vật sẽ kết tội
một chương trình ĐÚNG — hỏng nặng hơn hẳn việc kiểm thiếu một dòng. Hệ quả
phải khai: đề phát biểu bằng lối nói ngoài ba mẫu dưới đây **không được kiểm**,
và ca ấy giữ nguyên hành vi cũ.
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

#: *"Điểm P nằm trên đoạn EF sao cho …"* — neo bắt buộc là cụm **trên đoạn**.
#: Không có neo ấy thì không biết đoạn nào đang bị chia, và đoán ở đó là đoán
#: chính thứ quyết định kết quả.
_MAU_NEO = re.compile(
    rf"[ĐđDd]iểm\s+(?P<M>{_D})\s+(?:nằm\s+)?(?:thuộc|trên|nằm\s+trên)\s+"
    rf"(?:đoạn\s+(?:thẳng\s+)?)?(?P<A>{_D})(?P<B>{_D})\s+sao\s+cho\s+"
    rf"(?P<qh>[^.]+)")

#: *"Điểm I là trung điểm của GH"* — dạng riêng, tỉ lệ hằng.
_MAU_TRUNG_DIEM = re.compile(
    rf"[ĐđDd]iểm\s+(?P<M>{_D})\s+là\s+trung\s+điểm\s+(?:của\s+)?"
    rf"(?:đoạn\s+(?:thẳng\s+)?)?(?P<A>{_D})(?P<B>{_D})")

#: *"đoạn thẳng AB có độ dài 12"* — cần cho dạng ③ (độ dài một nhánh).
_MAU_DO_DAI = re.compile(
    rf"đoạn\s+(?:thẳng\s+)?(?P<A>{_D})(?P<B>{_D})\s+có\s+độ\s+dài\s+"
    rf"(?P<v>{_SO})")

# ── BA DẠNG QUAN HỆ ────────────────────────────────────────────────────────
#: ① `CN : ND = 2 : 3`
_QH_TI_SO = re.compile(
    rf"(?P<s1>{_D}{_D})\s*:\s*(?P<s2>{_D}{_D})\s*=\s*"
    rf"(?P<m>\d+)\s*:\s*(?P<n>\d+)")
#: ② `FP = 4·PE`  (dấu nhân: `·`, `*`, `x`, hoặc không có)
_QH_BOI = re.compile(
    rf"(?P<s1>{_D}{_D})\s*=\s*(?P<k>{_SO})\s*[·*×x]?\s*(?P<s2>{_D}{_D})")
#: ③ `AM = 9`
_QH_DO_DAI = re.compile(rf"(?P<s1>{_D}{_D})\s*=\s*(?P<v>{_SO})\s*$")


def _phan(s: str) -> Fraction:
    return Fraction(s.replace(" ", ""))


def _tach(seg: str) -> Optional[tuple[str, str]]:
    """`"CN"` → `("C", "N")`. Fail-closed khi không tách ra đúng hai ký hiệu."""
    m = re.fullmatch(rf"({_D})({_D})", seg)
    return (m.group(1), m.group(2)) if m else None


def _phia(seg: str, M: str, A: str, B: str) -> Optional[str]:
    """Nhánh nào của phép chia: `"A"` (đầu A) hay `"B"` (đầu B)?

    Đoạn con hợp lệ phải gồm ĐÚNG `M` và một trong hai đầu mút. `"AB"` (cả
    đoạn) hay `"AX"` (điểm lạ) đều trả `None` — và trả `None` là từ chối,
    không phải chọn bừa.
    """
    hai = _tach(seg)
    if hai is None or M not in hai:
        return None
    con = hai[0] if hai[1] == M else hai[1]
    return "A" if con == A else ("B" if con == B else None)


def _t_tu_quan_he(qh: str, M: str, A: str, B: str,
                  do_dai_ab: Optional[Fraction]) -> Optional[Fraction]:
    """Quan hệ (văn bản) → tham số `t` của `M = A + t·(B − A)`.

    Quy đổi **theo hướng `A → B`**, và hướng ấy lấy từ chính cụm *"trên đoạn
    AB"* của đề, không lấy từ chương trình. Nhờ vậy phép kiểm không phụ thuộc
    mô hình chọn viết `divide_segment(A,B,·)` hay `divide_segment(B,A,·)`.

        AM : MB = m : n   ⇒   t = m/(m+n)
    """
    qh = qh.strip()

    if (m := _QH_TI_SO.search(qh)):
        p1, p2 = _phia(m.group("s1"), M, A, B), _phia(m.group("s2"), M, A, B)
        if {p1, p2} != {"A", "B"}:
            return None
        a, b = int(m.group("m")), int(m.group("n"))
        if p1 == "B":                      # `s1` là nhánh B ⇒ đảo cặp
            a, b = b, a
        return Fraction(a, a + b) if a + b else None

    if (m := _QH_BOI.search(qh)):
        p1, p2 = _phia(m.group("s1"), M, A, B), _phia(m.group("s2"), M, A, B)
        if {p1, p2} != {"A", "B"}:
            return None
        k = _phan(m.group("k"))
        if k <= 0:
            return None
        # `s1 = k · s2`. Đặt nhánh A là `a`, nhánh B là `b`.
        a, b = (k, Fraction(1)) if p1 == "A" else (Fraction(1), k)
        return a / (a + b)

    if (m := _QH_DO_DAI.search(qh)):
        if do_dai_ab is None or do_dai_ab <= 0:
            return None
        p1 = _phia(m.group("s1"), M, A, B)
        if p1 is None:
            return None
        v = _phan(m.group("v"))
        if not (0 <= v <= do_dai_ab):
            return None
        return v / do_dai_ab if p1 == "A" else (do_dai_ab - v) / do_dai_ab

    return None


def _do_dai_doan(text: str, A: str, B: str) -> Optional[Fraction]:
    """Độ dài đoạn `AB` nếu đề nói ra — chấp nhận cả hai chiều viết."""
    for m in _MAU_DO_DAI.finditer(text):
        if {m.group("A"), m.group("B")} == {A, B}:
            try:
                return _phan(m.group("v"))
            except (ValueError, ZeroDivisionError):
                return None
    return None


def _fact_id_cho(contract, M: str, A: str, B: str) -> str:
    """Mục dữ kiện nào NÓI VỀ quan hệ này — chỉ để truy vết và giải thích.

    ⚠️ Cổng **không** dùng nó để quyết định có kiểm hay không; đó đúng là lỗ mà
    wave này đóng. Không tìm thấy thì trả chuỗi rỗng và bất biến vẫn được phát.
    """
    can = {M, A, B}
    for f in getattr(contract, "input_facts", ()) or ():
        van = " ".join([str(f.label or "")] + [str(v) for v in (f.values or ())])
        # TÁCH ký hiệu, không so biên chữ: `"EF"` phải đọc ra `{E, F}`. Bản đầu
        # dùng lookbehind `(?<![A-Za-z])` nên chữ THỨ HAI của mọi tên đoạn bị
        # bỏ — `F` trong `"đoạn EF"` không bao giờ khớp, và mọi bất biến đều ra
        # với `source_fact_id` rỗng.
        if can <= set(re.findall(rf"{_D}", van)):
            return f.fact_id
    return ""


def bat_bien_chia_doan(contract, problem_text: str | None) -> tuple:
    """`SourceInvariant(kind="segment_division")` cho mỗi quan hệ đọc được.

    Biểu diễn — **không thêm trường nào** vào `SourceInvariant`; ý nghĩa của
    `points` do `kind` quyết, và khai ở đúng một chỗ (đây):

        points   = (A, B, M)   A→B là HƯỚNG của đề, M là điểm bị ràng buộc
        expected = `t` hữu tỉ chính xác, `M = A + t·(B − A)`
        source_text = nguyên văn câu đã đọc

    Trùng `M` ⇒ **bỏ cả hai**: đề nói hai điều về cùng một điểm mà tầng này chỉ
    đọc được rời rạc thì nó không đủ tư cách phân xử.
    """
    text = problem_text or getattr(contract, "problem_text", "") or ""
    if not text:
        return ()
    ra: list[SourceInvariant] = []
    for m in _MAU_NEO.finditer(text):
        M, A, B = m.group("M"), m.group("A"), m.group("B")
        if len({M, A, B}) != 3:
            continue
        t = _t_tu_quan_he(m.group("qh"), M, A, B, _do_dai_doan(text, A, B))
        if t is None:
            continue
        ra.append(SourceInvariant(
            kind=KIND, points=(A, B, M), expected=str(t),
            source_fact_id=_fact_id_cho(contract, M, A, B),
            scale_symbol="", source_text=m.group(0).strip()))
    for m in _MAU_TRUNG_DIEM.finditer(text):
        M, A, B = m.group("M"), m.group("A"), m.group("B")
        if len({M, A, B}) != 3:
            continue
        ra.append(SourceInvariant(
            kind=KIND, points=(A, B, M), expected="1/2",
            source_fact_id=_fact_id_cho(contract, M, A, B),
            scale_symbol="", source_text=m.group(0).strip()))
    dem: dict[str, int] = {}
    for bt in ra:
        dem[bt.points[2]] = dem.get(bt.points[2], 0) + 1
    return tuple(bt for bt in ra if dem[bt.points[2]] == 1)
