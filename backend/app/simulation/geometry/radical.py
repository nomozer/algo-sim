# -*- coding: utf-8 -*-
"""MIỀN SỐ CHÍNH XÁC MỞ RỘNG — `a·π^m·√b`, `a ∈ ℚ`, `b` nguyên dương phi chính phương.

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

    b = 1 VÀ m = 0 ⇒ về `Fraction` (giá trị hữu tỉ thì không giữ dạng căn)
    a = 0        ⇒ về `Fraction(0)`, kể cả khi `m = 1`
    b > 0        ⇒ căn âm không thuộc miền, từ chối chứ không trả `None` lặng
    b phi chính phương ⇒ `√8` tự rút thành `2√2` LÚC DỰNG, không lúc so
    m ∈ {0, 1}   ⇒ ngoài miền thì từ chối — xem `PI_EXPONENT_DOMAIN`

⚠️ Điều kiện về `Fraction` là **`b = 1` VÀ `m = 0`**, không phải `b = 1` một
mình: `2π` có `b = 1` mà không hữu tỉ. Luật cũ là ca riêng `m = 0` của luật này.

─── π ĐI VÀO ĐÂU, VÀ KHÔNG ĐI VÀO ĐÂU ─────────────────────────────────────

π thuộc **đại lượng ĐO ĐƯỢC**, không thuộc **toạ độ**. `Vec3` vẫn là ℚ³ và
`hf()` vẫn từ chối mọi thứ không phải hữu tỉ — mở miền số ở đây **không** mở
miền toạ độ, và hai thứ ấy phải giữ tách bạch: toạ độ vô tỉ làm hỏng mọi phép
so bằng của kernel, còn một đại lượng vô tỉ thì chỉ là một đáp số bình thường.

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
    "PI_EXPONENT_DOMAIN",
    "radical",
    "multiply",
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

#: MIỀN SỐ MŨ π — cố ý chỉ `{0, 1}`, không phải "mọi số nguyên".
#:
#: Đây là một quyết định đo được, không phải một giới hạn tạm. Kiểm mọi đại
#: lượng cong của chương trình THPT (`CURVED_GEOMETRY_FOUNDATION_DESIGN §8b`):
#:
#:     V cầu   (4/3)πR³   S cầu  4πR²    V trụ  πr²h   S_xq trụ  2πrh
#:     V nón   (1/3)πr²h  S_xq nón πrl
#:
#: **Không** đại lượng nào có `mu = 2`, và không phép đo nào của IR chia cho một
#: đại lượng chứa π (thứ duy nhất sinh `mu` âm). Mở rộng miền "cho đủ" thì
#: `π² · thứ gì đó` trở nên biểu diễn được mà không có phép đo nào sinh ra nó —
#: tức mở một cửa chỉ dùng để đi nhầm.
#:
#: Ra ngoài miền ⇒ **từ chối**, không cắt xén, không xấp xỉ.
PI_EXPONENT_DOMAIN = (0, 1)


@dataclass(frozen=True)
class Radical:
    """`he · π^mu · √can`. **Dựng qua `radical()`**, đừng gọi thẳng constructor.

    Constructor không chuẩn hoá — cố ý, để `radical()` là cửa duy nhất và mọi
    `Radical` tồn tại đều đã chính tắc. `frozen=True` cho `__eq__`/`__hash__`
    theo trường, mà điều đó chỉ đúng *vì* mọi thể hiện đều chính tắc.

    `mu` mặc định `0` nên `Radical(he, can)` vẫn dựng đúng số cũ, và mọi
    `Radical` sinh trước bản này so BẰNG với bản sinh sau — miền số không hề
    tách làm hai.
    """

    he: Fraction
    can: int
    #: Số mũ của π. Miền: `PI_EXPONENT_DOMAIN` — xem hằng số ấy để biết vì sao
    #: nó không phải "mọi số nguyên".
    mu: int = 0

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


def radical(he: Fraction | int, can: int, mu: int = 0) -> ExactNumber:
    """Dựng `he·π^mu·√can` ĐÃ CHÍNH TẮC. Trả `Fraction` khi kết quả hữu tỉ.

    Đây là cửa duy nhất vào `Radical`. Lối ra hữu tỉ — hệ số 0, hoặc phần vô tỉ
    biến mất hoàn toàn — đều trả `Fraction`, nên trong hệ **không tồn tại**
    `0·√2` hay `3·√1` hay `2·√4`.

    ─── BẤT BIẾN CHÍNH TẮC ĐÃ TỔNG QUÁT HOÁ ────────────────────────────────

    Luật cũ là *"`can == 1` ⇒ về `Fraction`"*. Luật ấy **sai** khi có π: `2π`
    có `can == 1` mà **không** hữu tỉ, nên trả `Fraction(2)` là nói dối về giá
    trị. Luật đúng, và nó bao luật cũ:

        về `Fraction` ⇔ GIÁ TRỊ hữu tỉ ⇔ `can == 1` **và** `mu == 0`

    Nên `Radical` tồn tại đúng khi số ấy vô tỉ trong miền này. Vẫn một cách
    viết cho một số: `π√4` → `2π`, `0·π·√5` → `0`.
    """
    he = Fraction(he)
    if mu not in PI_EXPONENT_DOMAIN:
        raise RadicalDomainError(
            f"số mũ π = {mu} nằm ngoài miền {PI_EXPONENT_DOMAIN} — miền số này "
            "cố ý không nhận luỹ thừa π khác 0 hoặc 1"
        )
    if can <= 0:
        raise RadicalDomainError(f"căn thức phải là số nguyên dương, nhận {can}")
    if can > MAX_RADICAND:
        raise RadicalDomainError(
            f"căn thức {can} vượt trần {MAX_RADICAND} — từ chối thay vì treo"
        )
    if he == 0:
        # `0·π·√5 = 0`. Số mũ π không cứu được một hệ số bằng 0, nên nhánh này
        # đứng TRƯỚC mọi phép xét `mu` — nếu không, hệ có hai cách viết số 0.
        return Fraction(0)
    k, m = _tach_binh_phuong(can)
    if m == 1 and mu == 0:
        return he * k
    return Radical(he * k, m, mu)


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
    """`x²` — hữu tỉ, và **chỉ** trong phần miền không có π.

    `check_distance` so `d² == khai²` chứ không so `d == khai`, nên bộ chấm đi
    hết trong miền hữu tỉ kể cả khi đáp số là căn thức. Tính chất ấy có sẵn từ
    trước wave này — nó là lý do bộ chấm không phải viết lại.

    ⚠️ `(π√5)² = 5π²` có `mu = 2`, **ngoài** `PI_EXPONENT_DOMAIN`, và cũng
    không phải `Fraction`. Nên hàm này **từ chối** thay vì trả một `Fraction`
    đúng-về-hệ-số mà sai-về-giá-trị. Một bộ chấm so hai số sai như nhau sẽ nói
    PASS, và đó là kiểu hỏng đắt nhất.
    """
    if isinstance(x, Radical):
        if x.mu != 0:
            raise RadicalDomainError(
                f"bình phương của {display(x)} chứa π² — ngoài miền số này. "
                "Đại lượng chứa π không đi qua đường so bình phương."
            )
        return x.he * x.he * x.can
    return Fraction(x) * Fraction(x)


def negate(x: ExactNumber) -> ExactNumber:
    if isinstance(x, Radical):
        return Radical(-x.he, x.can, x.mu)
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
        return radical(x.he * Fraction(k), x.can, x.mu)
    return Fraction(x) * Fraction(k)


def divided_by_rational(x: ExactNumber, k: Fraction | int) -> ExactNumber:
    """Chia cho một số HỮU TỈ. Cố ý không có `divide(a, b)` tổng quát.

    Miền chia rộng hơn không có người dùng: không phép đo nào của IR chia một
    đại lượng cho một đại lượng khác. Và chia cho một số chứa π sinh `mu = -1`,
    ngoài `PI_EXPONENT_DOMAIN` — tức thêm phép ấy là thêm một cửa mà mọi lối đi
    qua đều bị từ chối. Số mũ π đi qua đây **không đổi**, vì `k` hữu tỉ.
    """
    k = Fraction(k)
    if k == 0:
        raise RadicalDomainError("chia cho 0")
    return times_rational(x, Fraction(1) / k)


def multiply(a: ExactNumber, b: ExactNumber) -> ExactNumber:
    """Tích — đại số CHÍNH XÁC trên cả ba thành phần, rồi chuẩn hoá lại.

        (h₁·π^m₁·√c₁) · (h₂·π^m₂·√c₂) = (h₁h₂)·π^(m₁+m₂)·√(c₁c₂)

    Căn thức nhân vào nhau rồi `radical()` rút bình phương, nên `√5·√5` về đúng
    `5` chứ không đọng lại `√25`. Số mũ π **cộng**, và tổng ra ngoài
    `PI_EXPONENT_DOMAIN` thì `radical()` từ chối — `π · π` không có phép đo nào
    sinh ra, nên từ chối ở đây là chặn một đường không ai đi, không phải cắt
    một năng lực.

    Không khai triển đa thức. Đây là tích của HAI đơn thức, và miền số chỉ có
    đơn thức.
    """
    ha = a.he if isinstance(a, Radical) else Fraction(a)
    hb = b.he if isinstance(b, Radical) else Fraction(b)
    ca = a.can if isinstance(a, Radical) else 1
    cb = b.can if isinstance(b, Radical) else 1
    ma = a.mu if isinstance(a, Radical) else 0
    mb = b.mu if isinstance(b, Radical) else 0
    if ha == 0 or hb == 0:
        return Fraction(0)
    return radical(ha * hb, ca * cb, ma + mb)


def add(a: ExactNumber, b: ExactNumber) -> ExactNumber:
    """Tổng — CHỈ khi kết quả còn nằm trong miền `a·√b`.

    Ba trường hợp cộng được: hai số hữu tỉ · một toán hạng bằng 0 · hai căn
    **cùng căn thức VÀ cùng số mũ π**. Ngoài ra `√2 + √3` **từ chối**, không
    xấp xỉ, không âm thầm dựng một cây biểu thức.

    Vì sao từ chối thay vì mở rộng miền: mở tổng tuỳ ý biến module này thành
    một CAS, và một CAS nửa vời sai ở chỗ không ai kiểm. Hình học hiện tại
    không cần tổng ấy — mỗi khoảng cách là MỘT phép căn của MỘT phân số.

    ─── π KHÔNG NỚI LUẬT NÀY, NÓ THÊM MỘT CHIỀU ────────────────────────────

        π√5 + 2π√5  →  3π√5      cùng căn, cùng mũ
        π√5 + π     →  TỪ CHỐI   căn 5 ≠ căn 1
        π   + 1     →  TỪ CHỐI   mũ 1 ≠ mũ 0

    Hệ quả thật, khai thẳng: `S_tp` của nón `= πrl + πr²` **không** viết được
    trong miền này. Đó **không** phải một giới hạn mới — nó đúng là giới hạn
    `√2 + √3` mà kho đã cố ý chọn, chỉ lộ ra ở một chỗ khác.
    """
    if sign(a) == 0:
        return b
    if sign(b) == 0:
        return a
    ra, rb = isinstance(a, Radical), isinstance(b, Radical)
    if not ra and not rb:
        return Fraction(a) + Fraction(b)
    if ra and rb and a.can == b.can and a.mu == b.mu:
        return radical(a.he + b.he, a.can, a.mu)
    raise RadicalDomainError(
        f"tổng {display(a)} + {display(b)} không viết được dưới dạng "
        "a·π^m·√b — miền số này cố ý không nhận tổng các hạng tử khác căn "
        "thức hoặc khác số mũ π"
    )


# ── SERIALIZATION: CẤU TRÚC, không phải chuỗi hiển thị ────────────────────
def to_json(x: ExactNumber) -> dict[str, Any]:
    """Dạng máy đọc được. Bộ chấm và frontend đều cần CẤU TRÚC, không cần chữ.

    Chuỗi `"3√2/5"` là **dẫn xuất** của cấu trúc này, không phải nguồn: đọc
    ngược một chuỗi có ký tự toán học là mời sai sót vào đúng chỗ không được
    phép sai.

    ─── `pi` CHỈ XUẤT HIỆN KHI KHÁC 0 — có chủ đích ────────────────────────

    Phát `"pi": 0` cho mọi số cũ sẽ đổi **byte** của mọi payload đang tồn tại
    (fixture, envelope đã cache, artifact đánh giá) mà **không** đổi một giá
    trị toán học nào. Bỏ trường khi `mu == 0` giữ chúng giống hệt từng byte,
    nên `OLD_EXACT_PAYLOADS` không đổi cả về nghĩa lẫn về dây.

    Mặc định *"vắng ⇒ `mu = 0`"* thuộc về **hợp đồng này**, và `from_json`
    ngay dưới là nơi nó được viết ra. Phía đọc không tự nghĩ ra nó.
    """
    if isinstance(x, Radical):
        d: dict[str, Any] = {
            "kind": "radical", "coefficient": str(x.he), "radicand": x.can,
        }
        if x.mu:
            d["pi"] = x.mu
        return d
    return {"kind": "rational", "value": str(Fraction(x))}


def from_json(d: Any) -> ExactNumber:
    """Nghịch đảo của `to_json`. Dữ liệu lạ ⇒ từ chối, không đoán.

    `pi` vắng ⇒ `mu = 0`: đó là hợp đồng, không phải suy đoán — mọi payload
    sinh trước bản này đều là số không chứa π, nên đọc chúng như `mu = 0` là
    đọc đúng, không phải đọc rộng lượng.
    """
    if not isinstance(d, dict):
        raise RadicalDomainError(f"không phải số chính xác: {d!r}")
    loai = d.get("kind")
    if loai == "rational":
        return Fraction(str(d["value"]))
    if loai == "radical":
        return radical(Fraction(str(d["coefficient"])), int(d["radicand"]),
                       int(d.get("pi", 0)))
    raise RadicalDomainError(f"kind không hợp lệ: {loai!r}")


#: Văn phạm HẸP cho giá trị mong đợi viết bằng chữ (`§9`).
#:
#: Dạng: `[-][k][*]​[π][sqrt(n)|√n][/m]` — phải có **ít nhất một** trong `π`
#: hoặc căn, nếu không thì chuỗi ấy là một phân số thường và đi lối `Fraction`
#: y như trước. Không eval, không parser biểu thức tổng quát — một `eval` ở đây
#: là một lỗ thực thi mã, và một parser tổng quát là một CAS đi cửa sau.
#:
#: ─── VÌ SAO π ĐƯỢC MỞ (2026-09-03, `VOLUME_VERIFICATION_BRIDGE`) ──────────
#:
#: Bản trước CỐ Ý đóng, và ghi rõ tiền đề:
#:
#:     "không tập đo nào có đại lượng chứa π — vì chưa phép đo nào sinh ra π
#:      (`CURVED_TYPES_ADDED = 0`)"
#:
#: Tiền đề ấy **chết từ Phase 2**: `volume(curved_solid)`, `lateral_area` và
#: `area(circle3)` sinh ra π ở mọi ca. Không ai soát lại lời chú thích khi điều
#: kiện của nó đổi — **đúng một hình lỗi với `check_volume`** mà wave này đi
#: dọn, chỉ khác chỗ đứng.
#:
#: Hậu quả đo được: `params["value"]` là ô STRING (`analyze_contract`), nên đáp
#: số mong đợi của MỌI bài khối cong (`288π`, `15π`, `12π`) rơi vào nhánh
#: `Fraction(s)`, ném, trả `None` — và `None` ở đây nghĩa là *"không có gì để
#: so"*. Tức cổng C₂ **fail OPEN**: nó không thể mâu thuẫn với đáp số đề, dù có
#: sai thế nào. Đường CẤU TRÚC (`from_json`) chở π đầy đủ, nhưng `analyze`
#: không đi được đường ấy — nó chỉ phát chuỗi.
#:
#: Văn phạm này nay đọc đúng thứ `display()` viết ra, và `test_pi_exact_domain`
#: khoá vòng tròn `display → parse_exact → display`.
_MAU_CAN = re.compile(
    r"""^\s*
    (?P<dau>-)?\s*                          # dấu âm trần, vd `-sqrt(3)`
    (?:(?P<k>-?\d+(?:/\d+)?)\s*\*?\s*)?     # hệ số nhân, tuỳ chọn (`288π` viết liền)
    (?P<pi>π|pi)?\s*                        # thừa số π, tuỳ chọn
    (?:(?:sqrt|√)\s*\(?\s*(?P<n>\d+)\s*\)?)?    # sqrt(n) hoặc √n, tuỳ chọn
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
    # Không có π lẫn căn ⇒ chuỗi ấy là phân số thường; để nguyên cho nhánh
    # `Fraction` bên dưới, đúng như trước khi π được mở. Nhánh này chỉ nhận
    # thứ mà `Fraction` KHÔNG đọc nổi.
    if m is not None and (m.group("pi") or m.group("n")):
        try:
            he = Fraction(m.group("k")) if m.group("k") else Fraction(1)
            if m.group("m"):
                he /= Fraction(int(m.group("m")))
            if m.group("dau"):
                he = -he
            return radical(he, int(m.group("n") or 1),
                           1 if m.group("pi") else 0)
        except (RadicalDomainError, ValueError, ZeroDivisionError):
            return None
    try:
        return Fraction(s)
    except (ValueError, ZeroDivisionError):
        return None


# ── HIỂN THỊ ──────────────────────────────────────────────────────────────
def display(x: ExactNumber) -> str:
    """Chuỗi cho người đọc: `√2`, `3√2`, `3√2/5`, `-√3/2`, `π`, `2π`, `π√5`,
    `4π√3/3`.

    Quy ước bám cách viết SGK và **không đổi** khi thêm π: hệ số trước, rồi
    `π`, rồi dấu căn, mẫu số cuối; `1` và `-1` không viết ra. Đây là DẪN XUẤT —
    nguồn là `to_json`.

    `√` giữ nguyên chứ không đổi sang LaTeX: kho đã có một quy ước hiển thị và
    một quy ước là đủ. `π` là chữ cái Hy Lạp thường, cùng cách viết SGK dùng.
    """
    if not isinstance(x, Radical):
        f = Fraction(x)
        return str(f.numerator) if f.denominator == 1 else f"{f.numerator}/{f.denominator}"
    tu, mau = x.he.numerator, x.he.denominator
    dau = "-" if tu < 0 else ""
    tu = abs(tu)
    # Hệ số `1` chỉ được ẩn khi còn thứ khác đứng sau nó — mà ở đây luôn còn,
    # vì `Radical` tồn tại chỉ khi `can > 1` hoặc `mu > 0` (xem `radical()`).
    he = "" if tu == 1 else str(tu)
    pi = "π" if x.mu else ""
    can = f"√{x.can}" if x.can != 1 else ""
    goc = f"{dau}{he}{pi}{can}"
    return goc if mau == 1 else f"{goc}/{mau}"
