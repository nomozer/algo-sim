# -*- coding: utf-8 -*-
"""MIỀN SỐ CHÍNH XÁC MỞ RỘNG — `a·√b` với `a ∈ ℚ`, `b` nguyên dương phi chính phương.

─── LỖ NÓ BỊT ─────────────────────────────────────────────────────────────

Kernel hình học tính **bình phương** khoảng cách chính xác trên `Fraction`, rồi
`geometry_exec` lấy căn. Trước module này, căn không hữu tỉ ⇒ `GEOMETRY_
IRRATIONAL_RESULT`: hệ từ chối trả lời. Nhưng `√2`, `√3`, `3√2/4` là **đáp số
bình thường của hình học THPT** — từ chối chúng nghĩa là từ chối phần lớn bài
khoảng cách, đúng lúc phép tính đã xong và chỉ còn thiếu một cách VIẾT kết quả.

Vấn đề chưa bao giờ là tính được hay không. Nó là biểu diễn.

─── VÌ SAO MỘT MIỀN HẸP, KHÔNG PHẢI MỘT CAS ───────────────────────────────

`a·√b` đóng dưới đúng những phép mà hình học cần: nhân/chia hữu tỉ, đổi dấu,
bình phương, so bằng. Nó KHÔNG đóng dưới phép cộng hai căn khác căn thức —
`√2 + √3` không viết được dưới dạng `a·√b`. Đó là ranh giới thật của miền, và
module này **fail closed** ở đó thay vì lặng lẽ mở rộng: mở tổng tuỳ ý là bước
đầu tiên của một CAS, và một CAS nửa vời sẽ trả lời sai ở chỗ không ai kiểm.

Hình học hiện tại không cần tổng ấy: mỗi khoảng cách là **một** phép căn của
**một** phân số, không phải một tổng nhiều căn.

─── BẤT BIẾN CHÍNH TẮC ────────────────────────────────────────────────────

Một số có ĐÚNG MỘT cách viết. `√8` và `2√2` phải là cùng một đối tượng, nếu
không phép so bằng của bộ chấm sẽ nói dối:

    b = 1        ⇒ về `Fraction` (không bao giờ giữ `a·√1`)
    a = 0        ⇒ về `Fraction(0)`
    b > 0        ⇒ căn âm không thuộc miền, từ chối chứ không trả `None` lặng
    b phi chính phương ⇒ `√8` tự rút thành `2√2` LÚC DỰNG, không lúc so

Hằng số `Radical` chỉ nên dựng qua `radical()`. Gọi thẳng constructor bỏ qua
chuẩn hoá, và hai biểu diễn của cùng một số là cách chắc chắn nhất để một bộ
chấm chính xác trở thành một bộ chấm gần đúng.

─── KHÔNG FLOAT, TUYỆT ĐỐI ────────────────────────────────────────────────

Không `math.sqrt`, không `**0.5`, không so sánh với epsilon. Chính phương kiểm
bằng `math.isqrt` rồi **nhân ngược lại** — `isqrt` là số học nguyên, còn
`int(x**0.5)**2 == x` là một phép so gần đúng đội lốt phép so bằng, và nó sai
với số lớn.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Union

__all__ = [
    "Radical",
    "ExactNumber",
    "RadicalDomainError",
    "MAX_RADICAND",
    "radical",
    "sqrt_rational",
    "square",
    "negate",
    "sign",
    "times_rational",
    "divided_by_rational",
    "add",
    "is_exact_number",
    "to_json",
    "from_json",
    "parse_exact",
    "display",
]


class RadicalDomainError(ValueError):
    """Phép toán vượt khỏi miền `a·√b`. **Fail closed** — không xấp xỉ.

    Là `ValueError` chứ không phải `GeometryError`: đây là lỗi của MIỀN SỐ, một
    tầng dưới hình học. `geometry_exec` bắt và dịch sang mã lỗi hình học khi
    cần — tầng dưới không được biết tên mã lỗi của tầng trên.
    """


#: Trần cho căn thức trước khi rút gọn (`§19`).
#:
#: Phân tích thừa số chạy tới `isqrt(n)`, nên `n` lớn là `n` chậm. Toạ độ hình
#: học THPT nhỏ (đơn vị, nửa đơn vị, phần ba), và `p·q` của chúng ở xa dưới trần
#: này. Đặt trần là chọn **từ chối rõ ràng** thay vì treo — một lượt đo treo
#: trông giống hệt một lượt đo hỏng, và tốn nhiều thời gian hơn để phát hiện.
MAX_RADICAND = 10**12


@dataclass(frozen=True)
class Radical:
    """`he · √can`. **Dựng qua `radical()`**, đừng gọi thẳng constructor.

    Constructor không chuẩn hoá — cố ý, để `radical()` là cửa duy nhất và mọi
    `Radical` tồn tại đều đã chính tắc. `frozen=True` cho `__eq__`/`__hash__`
    theo trường, mà điều đó chỉ đúng *vì* mọi thể hiện đều chính tắc.
    """

    he: Fraction
    can: int

    def __str__(self) -> str:  # pragma: no cover — tiện gỡ lỗi, không phải bề mặt
        return display(self)


#: Số chính xác: hữu tỉ HOẶC căn thức. Đây là **thẩm quyền duy nhất** của union
#: này — module khác import từ đây, không tự khai lại `Fraction | Radical`.
ExactNumber = Union[Fraction, Radical]


def is_exact_number(x: Any) -> bool:
    """`x` có thuộc miền số chính xác không? `bool` bị loại tường minh.

    `bool` là subclass của `int` trong Python, nên `True` sẽ lọt thành `1` nếu
    không chặn. Một cờ đúng/sai trôi vào chỗ một số đo là loại lỗi im lặng nhất.
    """
    if isinstance(x, bool):
        return False
    return isinstance(x, (int, Fraction, Radical))


# ── DỰNG + CHUẨN HOÁ ──────────────────────────────────────────────────────
def _tach_binh_phuong(n: int) -> tuple[int, int]:
    """`n = k² · m` với `m` phi chính phương. Trả `(k, m)`.

    Chia thử tới `isqrt(n)`, rút hết mọi thừa số bình phương. Không cần sàng
    nguyên tố: `n` ở đây nhỏ (xem `MAX_RADICAND`), và một cài đặt đọc hiểu được
    đáng giá hơn vài micro giây ở tầng này.
    """
    if n <= 0:
        raise RadicalDomainError(f"căn thức phải dương, nhận {n}")
    # Đường tắt cho chính phương toàn phần — ca thường gặp nhất (`√4`, `√36`,
    # `√(p·q)` khi `p·q` chính phương). `isqrt` là SỐ HỌC NGUYÊN, và phép nhân
    # ngược lại là thứ biến nó thành một phép so BẰNG: `int(n**0.5)**2 == n`
    # trông giống hệt nhưng đi qua float và sai với `n` lớn.
    r = math.isqrt(n)
    if r * r == n:
        return r, 1
    k, m = 1, n
    d = 2
    while d * d <= m:
        while m % (d * d) == 0:
            m //= d * d
            k *= d
        d += 1
    return k, m


def radical(he: Fraction | int, can: int) -> ExactNumber:
    """Dựng `he·√can` ĐÃ CHÍNH TẮC. Trả `Fraction` khi kết quả hữu tỉ.

    Đây là cửa duy nhất vào `Radical`. Ba lối ra hữu tỉ — hệ số 0, căn 1, và
    căn chính phương — đều trả `Fraction`, nên trong hệ **không tồn tại**
    `0·√2` hay `3·√1` hay `2·√4`.
    """
    he = Fraction(he)
    if can <= 0:
        raise RadicalDomainError(f"căn thức phải là số nguyên dương, nhận {can}")
    if can > MAX_RADICAND:
        raise RadicalDomainError(
            f"căn thức {can} vượt trần {MAX_RADICAND} — từ chối thay vì treo"
        )
    if he == 0:
        return Fraction(0)
    k, m = _tach_binh_phuong(can)
    if m == 1:
        return he * k
    return Radical(he * k, m)


def sqrt_rational(x: Fraction | int) -> ExactNumber:
    """`√x` CHÍNH XÁC cho `x ≥ 0` hữu tỉ. Luôn biểu diễn được.

    ─── VÌ SAO KHÔNG BAO GIỜ THẤT BẠI ──────────────────────────────────────

    `√(p/q) = √(p·q) / q` — nhân tử và mẫu với `q` đưa toàn bộ phần vô tỉ về
    **một số nguyên**, rồi rút bình phương ra khỏi số nguyên ấy. Mọi số hữu tỉ
    không âm đều cho kết quả dạng `a·√b`, nên hàm này không có nhánh "không
    biểu diễn được". Đó chính là lý do `GEOMETRY_IRRATIONAL_RESULT` biến mất
    khỏi đường khoảng cách.

    Cách làm THẲNG (căn tử, căn mẫu riêng) thì hỏng: `√(3/4)` cần `√3/2`, mà
    `√3` không rút ra khỏi tử được nếu chỉ nhìn tử một mình.
    """
    x = Fraction(x)
    if x < 0:
        raise RadicalDomainError(f"không lấy căn số âm: {x}")
    if x == 0:
        return Fraction(0)
    p, q = x.numerator, x.denominator
    return radical(Fraction(1, q), p * q)


# ── PHÉP TOÁN (chỉ những phép hình học thật sự cần) ───────────────────────
def square(x: ExactNumber) -> Fraction:
    """`x²` — LUÔN hữu tỉ. Đây là phép giữ bộ chấm chính xác mà không cần căn.

    `check_distance` so `d² == khai²` chứ không so `d == khai`, nên bộ chấm đi
    hết trong miền hữu tỉ kể cả khi đáp số là căn thức. Tính chất ấy có sẵn từ
    trước wave này — nó là lý do bộ chấm không phải viết lại.
    """
    if isinstance(x, Radical):
        return x.he * x.he * x.can
    return Fraction(x) * Fraction(x)


def negate(x: ExactNumber) -> ExactNumber:
    if isinstance(x, Radical):
        return Radical(-x.he, x.can)
    return -Fraction(x)


def sign(x: ExactNumber) -> int:
    """`-1 | 0 | 1`. Chính xác — `√b > 0` luôn, nên dấu là dấu của hệ số."""
    if isinstance(x, Radical):
        he = x.he
        return (he > 0) - (he < 0)
    f = Fraction(x)
    return (f > 0) - (f < 0)


def times_rational(x: ExactNumber, k: Fraction | int) -> ExactNumber:
    if isinstance(x, Radical):
        return radical(x.he * Fraction(k), x.can)
    return Fraction(x) * Fraction(k)


def divided_by_rational(x: ExactNumber, k: Fraction | int) -> ExactNumber:
    k = Fraction(k)
    if k == 0:
        raise RadicalDomainError("chia cho 0")
    return times_rational(x, Fraction(1) / k)


def add(a: ExactNumber, b: ExactNumber) -> ExactNumber:
    """Tổng — CHỈ khi kết quả còn nằm trong miền `a·√b`.

    Ba trường hợp cộng được: hai số hữu tỉ · một toán hạng bằng 0 · hai căn
    **cùng căn thức**. Ngoài ra `√2 + √3` **từ chối**, không xấp xỉ, không âm
    thầm dựng một cây biểu thức.

    Vì sao từ chối thay vì mở rộng miền: mở tổng tuỳ ý biến module này thành
    một CAS, và một CAS nửa vời sai ở chỗ không ai kiểm. Hình học hiện tại
    không cần tổng ấy — mỗi khoảng cách là MỘT phép căn của MỘT phân số.
    """
    if sign(a) == 0:
        return b
    if sign(b) == 0:
        return a
    ra, rb = isinstance(a, Radical), isinstance(b, Radical)
    if not ra and not rb:
        return Fraction(a) + Fraction(b)
    if ra and rb and a.can == b.can:
        return radical(a.he + b.he, a.can)
    raise RadicalDomainError(
        f"tổng {display(a)} + {display(b)} không viết được dưới dạng a·√b — "
        "miền số này cố ý không nhận tổng nhiều căn thức khác nhau"
    )


# ── SERIALIZATION: CẤU TRÚC, không phải chuỗi hiển thị ────────────────────
def to_json(x: ExactNumber) -> dict[str, Any]:
    """Dạng máy đọc được. Bộ chấm và frontend đều cần CẤU TRÚC, không cần chữ.

    Chuỗi `"3√2/5"` là **dẫn xuất** của cấu trúc này, không phải nguồn: đọc
    ngược một chuỗi có ký tự toán học là mời sai sót vào đúng chỗ không được
    phép sai.
    """
    if isinstance(x, Radical):
        return {"kind": "radical", "coefficient": str(x.he), "radicand": x.can}
    return {"kind": "rational", "value": str(Fraction(x))}


def from_json(d: Any) -> ExactNumber:
    """Nghịch đảo của `to_json`. Dữ liệu lạ ⇒ từ chối, không đoán."""
    if not isinstance(d, dict):
        raise RadicalDomainError(f"không phải số chính xác: {d!r}")
    loai = d.get("kind")
    if loai == "rational":
        return Fraction(str(d["value"]))
    if loai == "radical":
        return radical(Fraction(str(d["coefficient"])), int(d["radicand"]))
    raise RadicalDomainError(f"kind không hợp lệ: {loai!r}")


#: Văn phạm HẸP cho giá trị mong đợi viết bằng chữ (`§9`).
#:
#: Chỉ bốn dạng: `sqrt(n)` · `k*sqrt(n)` · `sqrt(n)/m` · `k*sqrt(n)/m`. Không
#: eval, không parser biểu thức tổng quát — một `eval` ở đây là một lỗ thực thi
#: mã, và một parser tổng quát là một CAS đi cửa sau.
_MAU_CAN = re.compile(
    r"""^\s*
    (?P<dau>-)?\s*                          # dấu âm trần, vd `-sqrt(3)`
    (?:(?P<k>-?\d+(?:/\d+)?)\s*\*\s*)?      # hệ số nhân, tuỳ chọn
    (?:sqrt|√)\s*\(?\s*(?P<n>\d+)\s*\)?     # sqrt(n) hoặc √n
    (?:\s*/\s*(?P<m>\d+))?                  # mẫu số, tuỳ chọn
    \s*$""",
    re.VERBOSE | re.IGNORECASE,
)


def parse_exact(raw: Any) -> ExactNumber | None:
    """Chuỗi/số → `ExactNumber`. Không đọc được ⇒ `None`, KHÔNG phải 0.

    Nhầm "không biết" thành "bằng 0" biến một nghĩa vụ không kiểm được thành
    một nghĩa vụ kiểm sai — và nó sẽ PASS những bài đáng lẽ FAIL.
    """
    if raw is None:
        return None
    if isinstance(raw, Radical):
        return raw
    if isinstance(raw, bool):
        return None
    if isinstance(raw, (int, Fraction)):
        return Fraction(raw)
    if isinstance(raw, dict):
        try:
            return from_json(raw)
        except (RadicalDomainError, KeyError, ValueError):
            return None
    s = str(raw).strip()
    m = _MAU_CAN.match(s)
    if m is not None:
        try:
            he = Fraction(m.group("k")) if m.group("k") else Fraction(1)
            if m.group("m"):
                he /= Fraction(int(m.group("m")))
            if m.group("dau"):
                he = -he
            return radical(he, int(m.group("n")))
        except (RadicalDomainError, ValueError, ZeroDivisionError):
            return None
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        return None


# ── HIỂN THỊ ──────────────────────────────────────────────────────────────
def display(x: ExactNumber) -> str:
    """Chuỗi cho người đọc: `√2`, `3√2`, `3√2/5`, `-√3/2`.

    Quy ước bám cách viết SGK: hệ số trước dấu căn, mẫu số cuối, `1` và `-1`
    không viết ra. Đây là DẪN XUẤT — nguồn là `to_json`.
    """
    if not isinstance(x, Radical):
        f = Fraction(x)
        return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
    tu, mau = x.he.numerator, x.he.denominator
    dau = "-" if tu < 0 else ""
    tu = abs(tu)
    he = "" if tu == 1 else str(tu)
    goc = f"{dau}{he}√{x.can}"
    return goc if mau == 1 else f"{goc}/{mau}"
