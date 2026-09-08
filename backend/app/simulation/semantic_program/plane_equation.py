# -*- coding: utf-8 -*-
"""Đọc PHƯƠNG TRÌNH MẶT PHẲNG từ câu văn của đề, phát `SourceInvariant`.

─── VÌ SAO TẦNG NÀY PHẢI TỒN TẠI ──────────────────────────────────────────

`construct_plane_from_equation` nhận bốn hệ số là **hằng viết thẳng trong câu
lệnh**. Grounding chỉ soi `memory_declarations`, nên bốn con số ấy đi qua nó mà
không bị hỏi câu nào — và bốn con số ấy xác định một VỊ TRÍ trong không gian,
tức đúng thứ ranh giới R0 sinh ra để canh.

Nên phép gác không nằm ở `source_fact_id` của mô hình (một chuỗi mô hình tự
đặt) mà ở đây: **server tự đọc phương trình từ đề**, rồi
`check_source_invariants` so nó với mặt phẳng có thật trong trạng thái cuối.
Đó nguyên văn lập luận mà `check_source_invariants` đã dựng cho
`segment_length`: *"cổng chạy trên dữ liệu server tự phát, nên không có đường
nào để một chương trình tránh bị kiểm bằng cách im lặng."*

─── NGƯỠNG HẸP, VÀ HẸP Ở ĐÂU ──────────────────────────────────────────────

Chỉ phương trình TUYẾN TÍNH Cartesian theo `x, y, z`, hệ số hữu tỉ. Không
tham số, không mũ, không lượng giác. Một chuỗi không đọc trọn ⇒ **không đoán
một nửa**.

Và không chỉ cần một dấu `=`: phải có **cụm chỉ mặt phẳng** ngay trước nó
(*"mặt phẳng"*, *"mp"*). Thiếu ràng buộc ấy thì `2x + 3 = 7` trong một bài bất
kỳ cũng thành một mặt phẳng, và tầng này sẽ đi kiểm một vật đề không nói tới.
"""
from __future__ import annotations

import re
import unicodedata
from fractions import Fraction
from typing import Optional

from .scale_normalization import SourceInvariant

#: `kind` của bất biến. Một chuỗi, một chỗ khai, một checker.
KIND = "plane_equation"
#: Thấy đề nêu một mặt phẳng bằng phương trình nhưng KHÔNG giải được hệ số.
#:
#: Trạng thái CHẶN, cùng khuôn `segment_relation.KIND_CHUA_GIAI` và cùng lý
#: do: *"tôi thấy đề ràng buộc vật này, và tôi KHÔNG chứng minh được hình dựng
#: thoả nó"*. Đi tiếp là phục vụ một mặt phẳng chưa được chứng minh.
KIND_CHUA_GIAI = "plane_equation_unresolved"

#: Cụm nói rằng thứ sắp tới là một MẶT PHẲNG. Không có nó thì không phát gì.
_CUM_MAT_PHANG = re.compile(r"mat\s*phang|\bmp\b|\bmp\.")

#: Bao nhiêu ký tự trước dấu `=` được soi để tìm cụm ấy. Đủ cho
#: *"Mặt phẳng (α): 2x - z + 10"*, không đủ để với sang câu trước.
_CUA_SO = 48

#: Ký tự được phép nằm TRONG một phương trình. `.` và `,` KHÔNG có mặt: chúng
#: là dấu câu, và nuốt chúng sẽ kéo *"… = 0."* thành *"0."* rồi hỏng ở tầng
#: dưới với một thông báo không nói được vì sao.
_TRONG_PT = "0123456789xyz+-*/ \t"

#: Dấu trừ KHÔNG-ASCII → `-`. Ánh xạ **1 ký tự ↔ 1 ký tự**, cố ý: `_ung_vien`
#: trả về LÁT CẮT của chuỗi gốc, nên một phép chuẩn hoá đổi độ dài sẽ làm mọi
#: chỉ số lệch. `unicodedata.normalize` không dùng được ở đây vì lý do ấy.
#:
#: ─── VÌ SAO CÓ BẢNG NÀY (2026-09-08, `THESIS_FINAL_ACCEPTANCE_RUNNER_ALIGNMENT`)
#:
#: `U+2212 MINUS SIGN` là dấu trừ ĐÚNG của toán học — thứ SGK, Word và một mô
#: hình chép lại đề đã soạn đẹp sẽ phát ra. Trước bản này nó KHÔNG nằm trong
#: `_TRONG_PT`, và hậu quả không phải "không đọc được" mà tệ hơn hẳn:
#:
#:     đề  "Mặt phẳng (α): 2x − z + 12 = 0"
#:     nở trái dừng ở `−`  ⇒  ứng viên `z + 12 = 0`
#:     ⇒ bất biến so `z + 12 = 0` với hình dựng `2x − z + 12 = 0` ⇒ VI PHẠM
#:
#: Tức một chương trình ĐÚNG bị từ chối, và lời từ chối nói về một mặt phẳng
#: đề không hề viết. Đây đúng là ca *"một mặt phẳng SAI được đem đi đối chiếu"*
#: mà docstring `_ung_vien` đã ghi là ca tệ hơn — chỉ khác nguyên nhân.
#:
#: Đo được ở lượt chứng nhận runner với provider stub: ca `p6` đỏ, ca `p7`
#: cùng lỗi nhưng VẪN xanh vì phép cắt cụt của nó tình cờ cho một phương trình
#: tương đương. Một lỗi bật ở một trong hai ca cùng hình dạng.
#:
#: ⚠️ CHỈ họ dấu gạch ngang. `U+00AD SOFT HYPHEN` cố ý KHÔNG có mặt: nó không
#: phải một dấu trừ, và một soft hyphen nằm giữa phương trình là một vấn đề
#: khác, cần một lời từ chối khác.
_DAU_TRU_KHAC = {
    "−": "-",   # MINUS SIGN — dấu trừ toán học
    "–": "-",   # EN DASH
    "—": "-",   # EM DASH
    "‐": "-",   # HYPHEN
    "‑": "-",   # NON-BREAKING HYPHEN
}
_BANG_DAU_TRU = str.maketrans(_DAU_TRU_KHAC)


def chuan_hoa_dau_tru(s: str) -> str:
    """Đưa mọi dấu trừ về `-`. Độ dài KHÔNG đổi, nên chỉ số vẫn dùng được."""
    return s.translate(_BANG_DAU_TRU)

_TU = re.compile(
    r"""\s*(?P<dau>[+-])?\s*
        (?:
            (?:(?P<he>\d+(?:\s*/\s*\d+)?)\s*\*?\s*)?(?P<bien>[xyz])
            (?:\s*/\s*(?P<mau>\d+))?
          | (?P<hang>\d+(?:\s*/\s*\d+)?)
        )""",
    re.X,
)


def _khong_dau(s: str) -> str:
    """Bỏ dấu tiếng Việt, hạ chữ thường — CHỈ để dò cụm, không để đọc số."""
    tach = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in tach if unicodedata.category(c) != "Mn")


def _phan(s: str) -> Optional[Fraction]:
    try:
        return Fraction(s.replace(" ", ""))
    except (ValueError, ZeroDivisionError):
        return None


def doc_ve(ve: str) -> Optional[tuple[Fraction, Fraction, Fraction, Fraction]]:
    """Một VẾ → `(hệ số x, y, z, hằng)`. Đọc không trọn ⇒ `None`, không đoán.

    Quét tuần tự và đòi **tiêu thụ hết chuỗi**: một ký tự thừa nghĩa là mẫu
    chưa hiểu hết câu, và đọc một nửa phương trình còn tệ hơn không đọc.
    """
    he = {"x": Fraction(0), "y": Fraction(0), "z": Fraction(0)}
    hang = Fraction(0)
    vi, thay = 0, False
    while vi < len(ve):
        if ve[vi].isspace():
            vi += 1
            continue
        m = _TU.match(ve, vi)
        if not m or m.end() == vi:
            return None
        # Hạng tử thứ hai trở đi BẮT BUỘC có dấu — `2x 3` không phải tổng, nó
        # là một chuỗi hỏng, và nhận nó là bịa ra một phép cộng đề không viết.
        if thay and not m.group("dau"):
            return None
        dau = Fraction(-1) if m.group("dau") == "-" else Fraction(1)
        if m.group("bien"):
            g = _phan(m.group("he")) if m.group("he") else Fraction(1)
            if g is None:
                return None
            if m.group("mau"):
                mau = _phan(m.group("mau"))
                if not mau:
                    return None
                g /= mau
            he[m.group("bien")] += dau * g
        else:
            g = _phan(m.group("hang"))
            if g is None:
                return None
            hang += dau * g
        vi, thay = m.end(), True
    if not thay:
        return None
    return he["x"], he["y"], he["z"], hang


def doc_phuong_trinh(
    s: str,
) -> Optional[tuple[Fraction, Fraction, Fraction, Fraction]]:
    """`"2x - z = -10"` → `(2, 0, −1, 10)`. Chuyển vế lo ở đây, không ở mẫu.

    Đọc hai vế RỜI rồi trừ. Nhờ vậy `2x − z + 10 = 0` và `2x − z = −10` cho
    cùng một bộ hệ số mà không cần một mẫu riêng cho từng cách chuyển vế.

    Bộ hệ số trả về CHƯA chuẩn hoá dấu hay ước chung: phép so ở
    `check_source_invariants` là so TỈ LỆ, nên chuẩn hoá ở đây chỉ thêm một
    quy ước mà không tầng nào cần.
    """
    s = chuan_hoa_dau_tru(s)
    if s.count("=") != 1:
        return None
    trai, phai = s.split("=")
    t, p = doc_ve(trai), doc_ve(phai)
    if t is None or p is None:
        return None
    a, b, c, d = (t[i] - p[i] for i in range(4))
    if a == 0 and b == 0 and c == 0:
        return None  # `0 = 0` hoặc `3 = 5`: không phải mặt phẳng nào cả
    return a, b, c, d


#: `x`, `y` hoặc `z` đứng MỘT MÌNH — không dính chữ cái nào hai bên.
#:
#: ⚠️ Phân biệt này không phải chuộng chuẩn mực, nó chặn hai lỗi ĐO ĐƯỢC (xem
#: `_ung_vien`): chữ `y` trong *"đáy"* và chữ `y` trong tham số `my`. Cả hai
#: từng bị đọc thành biến, và một trong hai đẻ ra một mặt phẳng SAI.
_BIEN_DOC_LAP = re.compile(r"(?<![^\W\d_])[xyz](?![^\W\d_])")


def _no_ra(manh: str, i: int) -> tuple[int, int, bool]:
    """Nở hai phía từ dấu `=` theo tập ký tự cho phép, và nói BIÊN CÓ SẠCH KHÔNG.

    Biên bẩn = ký tự chặn lại là một CHỮ CÁI dính liền (không cách). Khi ấy
    phép nở đã cắt ngang một từ, nên nó nuốt luôn cụm chữ cái đó để chuỗi ứng
    viên mang theo thứ làm nó không đọc được — thay vì lặng lẽ trả về một mẩu
    đọc được nhưng SAI.
    """
    t = i
    while t > 0 and manh[t - 1] in _TRONG_PT:
        t -= 1
    while t < i and manh[t].isspace():          # bỏ khoảng trắng đầu
        t += 1
    ban = t > 0 and manh[t - 1].isalpha()
    if ban:                                     # nuốt trọn cụm chữ cái
        while t > 0 and manh[t - 1].isalpha():
            t -= 1

    p = i + 1
    while p < len(manh) and manh[p] in _TRONG_PT:
        p += 1
    while p > i + 1 and manh[p - 1].isspace():  # bỏ khoảng trắng cuối
        p -= 1
    if p < len(manh) and manh[p].isalpha():
        ban = True
        while p < len(manh) and manh[p].isalpha():
            p += 1
    return t, p, ban


def _ung_vien(manh: str) -> list[tuple[str, bool]]:
    """Mọi chuỗi quanh một dấu `=` **có cụm mặt phẳng đứng trước**.

    Trả `(chuỗi, có biến ĐỘC LẬP không)`. Nở ra hai phía từ dấu `=` theo tập
    ký tự cho phép — cách này đọc được phương trình nằm giữa văn xuôi mà không
    phải viết một mẫu cho từng cách đề dẫn dắt nó.

    ─── HAI LỖI ĐO ĐƯỢC BẮT BẢN NÀY PHẢI CANH BIÊN ────────────────────────

    Bản đầu chỉ nở theo tập ký tự, không hỏi biên. Hai ca hỏng, cả hai tìm
    được bằng test trước khi nhập:

      *"Diện tích mặt phẳng đáy = 12"* → nở trái dừng ở `á`, thu được **`y =
      12`** và đọc thành mặt phẳng `y − 12 = 0`. Chữ `y` của **"đáy"**.

      *"(α): 2x + my − z + 10 = 0"* → nở trái dừng ở `m`, thu được `y − z + 10
      = 0` — một phương trình ĐỌC ĐƯỢC nhưng **KHÁC hẳn** phương trình của đề.
      Đây là ca tệ hơn: không phải một cảnh báo thừa, mà một mặt phẳng SAI được
      đem đi đối chiếu.

    Nên biên bẩn ⇒ nuốt luôn cụm chữ cái, để chuỗi mang theo thứ làm nó không
    đọc nổi. Sau đó `bat_bien_mat_phang` mới phân xử: có biến độc lập thì
    CHẶN (đề nói về một mặt phẳng hệ không dựng nổi), không có thì IM LẶNG.
    """
    ra: list[tuple[str, bool]] = []
    # Chuẩn hoá dấu trừ TRƯỚC khi nở: phép nở đi theo `_TRONG_PT`, và một dấu
    # trừ không-ASCII sẽ chặn nó giữa phương trình rồi trả về một mẩu đọc được
    # nhưng SAI. Ánh xạ 1:1 nên `manh[t:p]` vẫn cắt đúng chỗ.
    manh = chuan_hoa_dau_tru(manh)
    phang = _khong_dau(manh)
    for m in re.finditer("=", manh):
        i = m.start()
        if not _CUM_MAT_PHANG.search(phang[max(0, i - _CUA_SO):i]):
            continue
        t, p, _ban = _no_ra(manh, i)
        chuoi = manh[t:p].strip()
        if chuoi.count("=") != 1:
            continue
        ra.append((chuoi, bool(_BIEN_DOC_LAP.search(chuoi))))
    return ra


def bat_bien_mat_phang(contract, problem_text: str | None) -> tuple:
    """`SourceInvariant(kind="plane_equation")` cho mỗi mặt phẳng đề cho bằng
    phương trình.

    Đặt cạnh `bat_bien_do_dai`/`bat_bien_chia_doan` vì cùng làm MỘT việc: đọc
    câu văn của đề rồi phát một ràng buộc SERVER sở hữu. Khác ở chỗ đọc gì.

    ─── HAI VERDICT, KHÔNG PHẢI MỘT ───────────────────────────────────────

    · đọc trọn  ⇒ `KIND` + `coefficients` — cổng so tỉ lệ trên hình dựng ra;
    · thấy mà không đọc trọn ⇒ `KIND_CHUA_GIAI` — **chặn**. Ca thật: hệ số
      mang tham số (`2x + my - z + 10 = 0`). Hệ không dựng nổi mặt phẳng ấy,
      và phục vụ một hình đoán bừa còn tệ hơn từ chối.

    Chuỗi không có `x`, `y`, `z` nào thì **im lặng bỏ qua**, kể cả khi có cụm
    mặt phẳng đứng trước: *"diện tích mặt phẳng … = 12"* là một câu về ĐỘ LỚN,
    và biến nó thành một mặt phẳng chưa giải được sẽ chặn oan cả một lớp đề.
    """
    from .segment_relation import _van_ban

    manh = _van_ban(contract, problem_text)
    if not manh:
        return ()
    ra: list[SourceInvariant] = []
    da_co: set[tuple[Fraction, ...]] = set()
    for m in manh:
        for chuoi, co_bien in _ung_vien(m):
            if not co_bien:
                continue
            he = doc_phuong_trinh(chuoi)
            if he is None:
                ra.append(SourceInvariant(
                    kind=KIND_CHUA_GIAI, points=(), expected="",
                    coefficients=(), source_fact_id=_nguon(contract, chuoi),
                    scale_symbol="", source_text=chuoi))
                continue
            # Cùng một phương trình xuất hiện ở CẢ đề lẫn mục dữ kiện là
            # chuyện thường — `_van_ban` cố ý tách nhiều mảnh. Phát hai bản
            # của cùng một ràng buộc chỉ nhân đôi mẫu số telemetry.
            chuan = _chuan_hoa(he)
            if chuan in da_co:
                continue
            da_co.add(chuan)
            ra.append(SourceInvariant(
                kind=KIND, points=(), expected="",
                coefficients=tuple(str(x) for x in he),
                source_fact_id=_nguon(contract, chuoi),
                scale_symbol="", source_text=chuoi))
    return tuple(ra)


def _chuan_hoa(he) -> tuple[Fraction, ...]:
    """Đại diện CHÍNH TẮC của một lớp phương trình tỉ lệ — chỉ để khử trùng.

    Chia cho hệ số khác 0 đầu tiên. Không dùng cho phép so của cổng: cổng so
    tỉ lệ bằng định thức con, không qua một dạng chính tắc nào.
    """
    dau = next((x for x in he if x != 0), Fraction(1))
    return tuple(x / dau for x in he)


def _nguon(contract, chuoi: str) -> str:
    """Mục dữ kiện chứa phương trình này — CHỈ để truy vết, không để quyết."""
    gon = chuoi.replace(" ", "")
    for f in getattr(contract, "input_facts", ()) or ():
        van = " ".join([str(getattr(f, "label", "") or "")]
                       + [str(v) for v in (getattr(f, "values", ()) or ())])
        if gon in van.replace(" ", ""):
            return f.fact_id
    return ""


def tuong_duong(u, v) -> bool:
    """Hai bộ bốn hệ số có tỉ lệ với nhau không — CHÍNH XÁC, không dung sai.

    `u ~ λv, λ ≠ 0` ⇔ mọi định thức con 2×2 bằng 0. So bằng nhân chéo nên
    không có phép chia nào, và không cần chọn hệ số nào làm chuẩn.

    Bộ toàn 0 KHÔNG tỉ lệ với gì cả: nó không phải một mặt phẳng, nên trả
    `False` thay vì `True` — `λ` phải khác 0.
    """
    u = [Fraction(x) for x in u]
    v = [Fraction(x) for x in v]
    if all(x == 0 for x in u) or all(x == 0 for x in v):
        return False
    return all(u[i] * v[j] == u[j] * v[i]
               for i in range(4) for j in range(i + 1, 4))
